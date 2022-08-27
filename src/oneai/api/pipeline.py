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
