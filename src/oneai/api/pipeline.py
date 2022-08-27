from copy import copy
import json
from typing import Awaitable, List
import aiohttp
import urllib.parse
import oneai, oneai.api

from oneai.classes import Input, Label, Labels, Output, Skill
from oneai.exceptions import handle_unsuccessful_response, validate_api_key

endpoint_default = "api/v0/pipeline"
endpoint_async_file = "api/v0/pipeline/async/file"
endpoint_task = "api/v0/pipeline/async/tasks"


def build_request(input: Input, steps: List[Skill], include_text: True):
    request = {
        "steps": [skill.asdict() for skill in steps],
    }
    if include_text:
        request["text"] = input.raw
    if isinstance(input, Input):
        if input.type:
            request["input_type"] = input.type
        if hasattr(input, "content_type") and input.content_type:
            request["content_type"] = input.content_type
        if hasattr(input, "encoding") and input.encoding:
            request["encoding"] = input.encoding
    return json.dumps(request, default=lambda x: x.__dict__)

async def post_pipeline(
    session: aiohttp.ClientSession,
    input: Input,
    steps: List[Skill],
    api_key: str,
) -> Awaitable[Output]:
    validate_api_key(api_key)

    request = build_request(input, steps, True)
    url = f"{oneai.URL}/{endpoint_default}"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "User-Agent": f"python-sdk/{oneai.__version__}/{oneai.api.uuid}",
    }

    async with session.post(url, headers=headers, data=request) as response:
        if response.status != 200:
            await handle_unsuccessful_response(response)
        elif oneai.DEBUG_RAW_RESPONSES:
            return await response.json()
        else:
            return build_output(steps, await response.json(), input_type=type(input))

async def post_pipeline_async_file(
    session: aiohttp.ClientSession,
    input: Input,
    steps: List[Skill],
    api_key: str,
) -> Awaitable[str]:
    validate_api_key(api_key)

    request = build_request(input, steps, False)
    url = f"{oneai.URL}/{endpoint_async_file}?pipeline=" + urllib.parse.quote(json.dumps(request))
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "User-Agent": f"python-sdk/{oneai.__version__}/{oneai.api.uuid}",
    }

    async with session.post(url, headers=headers, data=input.raw) as response:
        if response.status != 200:
            await handle_unsuccessful_response(response)
        else:
            return await response.json()


def build_output(
    skills: List[Skill], raw_output: dict, input_type: type = str
) -> Output:
    def get_text(index, input_type):
        # get the input text for this Output object. use index=-1 to get the original input text
        # text can be returned as a simple str or parsed to match a given input type
        text = (
            raw_output["output"][index]["text"]
            if index >= 0
            else raw_output["input_text"]
        )
        return input_type.parse(text)

    def split_pipeline(skills: List[Skill], i: int):
        # split pipeline at a generator Skill
        first, second = skills[: i + 1], skills[i + 1 :]
        if hasattr(skills[i], "output_attr1") and skills[i].output_attr1:
            # handle skills that create both text and labels
            clone = copy(skills[i])
            clone.is_generator = False
            clone.output_attr = skills[i].output_attr1
            second = (clone, *second)
        return first, second

    def build_internal(
        output_index: int, skills: List[Skill], input_type: type
    ) -> "Output":
        text = get_text(output_index, input_type).raw
        # temporary fix- if 1st skill is not a generator, use input_text, not output[0].text,
        # since output[0].text is corrupted (not parsable) for conversation inputs
        output_index = max(output_index, 0)
        labels = [
            Label.from_dict(label)
            for label in raw_output["output"][output_index]["labels"]
        ]
        data = []
        for i, skill in enumerate(skills):
            if skill.is_generator:
                skills, next_skills = split_pipeline(skills, i)
                data.append(
                    build_internal(
                        output_index + 1, next_skills, skill.output_type or input_type
                    )
                )
                break
            else:
                data.append(
                    Labels(filter(lambda label: label.type == skill.label_type, labels))
                )
        return Output(text=text, skills=list(skills), data=data)

    generator = raw_output["output"][0].get("text_generated_by_step_id", 0) - 1
    if generator < 0:
        return build_internal(-1, skills, input_type)
    else:
        # edge case- first Skill is a generator, or a generator preceded by Skills that didn't generate output
        # in this case the API will skip these Skills,
        # so we need to create filler objects to match the expected structure
        next_input_type = skills[generator].output_type or input_type
        skills, next_skills = split_pipeline(skills, generator)
        return Output(
            text=get_text(-1, input_type).raw,
            skills=list(skills),
            data=[Labels()] * generator + [build_internal(0, next_skills, next_input_type)],
        )
