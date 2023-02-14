from datetime import timedelta
import json
import urllib.parse
from typing import Awaitable, List

import aiohttp
import oneai, oneai.api
from oneai.api.output import build_output
from oneai.classes import Input, Output, Skill
from oneai.exceptions import handle_unsuccessful_response, validate_api_key

endpoint_default = "api/v0/pipeline"
endpoint_async_file = "api/v0/pipeline/async/file"
endpoint_async_tasks = "api/v0/pipeline/async/tasks"


def build_request(
    input: Input, steps: List[Skill], multilingual: bool, include_text: True
):
    def json_default(obj):
        if isinstance(obj, timedelta):
            return str(obj)
        if isinstance(obj, Skill):
            return obj.api_name
        return {k: v for k, v in obj.__dict__.items() if v is not None}

    # use input metadata for clustering
    if hasattr(input, "metadata"):
        for skill in steps:
            if skill.api_name == "clustering":
                skill._skill_params.append("user_metadata")
                skill.user_metadata = input.metadata
                break

    request = {
        "steps": [skill.asdict() for skill in steps],
        "output_type": "json",
        "multilingual": multilingual,
    }
    if include_text:
        request["text"] = input.text
    if isinstance(input, Input):
        if input.type:
            request["input_type"] = input.type
        if hasattr(input, "content_type") and input.content_type:
            request["content_type"] = input.content_type
        if hasattr(input, "encoding") and input.encoding:
            request["encoding"] = input.encoding
    return json.dumps(request, default=json_default)


async def post_pipeline(
    session: aiohttp.ClientSession,
    input: Input,
    steps: List[Skill],
    api_key: str,
    multilingual: bool,
) -> Awaitable[Output]:
    validate_api_key(api_key)

    request = build_request(input, steps, multilingual, True)
    url = f"{oneai.URL}/{endpoint_default}"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "User-Agent": f"python-sdk/{oneai.__version__}/{oneai.api.uuid}",
    }

    if oneai.DEBUG_LOG_REQUESTS:
        oneai.logger.debug(f"POST {url}\n")
        oneai.logger.debug(f"headers={json.dumps(headers, indent=4)}\n")
        oneai.logger.debug(f"data={json.dumps(json.loads(request), indent=4)}\n")

    async with session.post(url, headers=headers, data=request) as response:
        if response.status != 200:
            await handle_unsuccessful_response(response)
        else:
            return build_output(steps, await response.json())


async def post_pipeline_async_file(
    session: aiohttp.ClientSession,
    input: Input,
    steps: List[Skill],
    api_key: str,
    multilingual: bool,
) -> Awaitable[str]:
    validate_api_key(api_key)

    request = build_request(input, steps, multilingual, False)
    url = f"{oneai.URL}/{endpoint_async_file}?pipeline=" + urllib.parse.quote(request)
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "User-Agent": f"python-sdk/{oneai.__version__}/{oneai.api.uuid}",
    }

    if oneai.DEBUG_LOG_REQUESTS:
        oneai.logger.debug(f"POST {url}\n")
        oneai.logger.debug(f"headers={json.dumps(headers, indent=4)}\n")
        oneai.logger.debug(f"data={json.dumps(json.loads(request), indent=4)}\n")

    async with session.post(url, headers=headers, data=input.text) as response:
        if response.status != 200:
            await handle_unsuccessful_response(response)
        else:
            return await response.json()


async def get_task_status(
    session: aiohttp.ClientSession,
    task_id: str,
    api_key: str,
):
    validate_api_key(api_key)

    url = f"{oneai.URL}/{endpoint_async_tasks}/{task_id}"
    headers = {
        "api-key": api_key,
        "User-Agent": f"python-sdk/{oneai.__version__}/{oneai.api.uuid}",
    }

    if oneai.DEBUG_LOG_REQUESTS:
        oneai.logger.debug(f"GET {url}\n")
        oneai.logger.debug(f"headers={json.dumps(headers, indent=4)}\n")

    async with session.get(url, headers=headers) as response:
        if response.status != 200:
            await handle_unsuccessful_response(response)
        else:
            return await response.json()
