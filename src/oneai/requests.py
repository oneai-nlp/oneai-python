import asyncio
from typing import Awaitable, Generator, List, Union

import aiohttp
import oneai

from oneai.classes import Input, LabeledText

MAX_CONCURRENT_REQUESTS = 4


async def _send_request(
    session: aiohttp.ClientSession,
    input: Union[Input, str],
    steps: dict,
    api_key: str
) -> Awaitable[List[LabeledText]]:
    headers = {
        'api-key': api_key,
        'Content-Type': 'application/json'
    }
    request = {
        'text': input.text if input is Input else str(input),
        'steps': steps,
        'input_type': input.type if input is Input else 'article'
    }
    async with session.post(oneai.URL, headers=headers, json=request) as resp:
        if resp.status != 200:
            raise Exception  # todo error types
        else:
            response = await resp.json()
            return [LabeledText.from_json(output) for output in response['output']]


async def send_single_request(
    input: Union[Input, str],
    steps: dict,
    api_key: str
) -> Awaitable[List[LabeledText]]:
    timeout = aiohttp.ClientTimeout(total=6000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        return await _send_request(
            session,
            input,
            steps,
            api_key
        )


async def send_batch_request(
    batch: List[Union[str, Input]],
    steps: dict,
    api_key: str
) -> Awaitable[List[List[LabeledText]]]:
    size = len(batch)
    results = [None] * size

    async def req_worker(session, task_id):
        for i in range(task_id, size, MAX_CONCURRENT_REQUESTS):
            results[i] = await _send_request(
                session,
                batch[i],
                steps,
                api_key
            )

    timeout = aiohttp.ClientTimeout(total=6000)
    tasks = []
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i in range(min(MAX_CONCURRENT_REQUESTS, size)):
            task = asyncio.create_task(req_worker(session, i))
            tasks.append(task)
        await asyncio.gather(*tasks)
        return results
