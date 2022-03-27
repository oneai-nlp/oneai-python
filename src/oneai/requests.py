import asyncio
from typing import Awaitable, Generator, List

import aiohttp
import oneai

from oneai.classes import LabeledText

MAX_CONCURRENT_REQUESTS = 4


async def _send_request(
    session: aiohttp.ClientSession,
    text: str,
    steps: dict,
    input_type: str,
    api_key: str
) -> Awaitable[List[LabeledText]]:
    headers = {
        'api-key': api_key,
        'Content-Type': 'application/json'
    }
    request = {
        'text': text,
        'steps': steps,
        'input_type': input_type
    }
    async with session.post(oneai.URL, headers=headers, json=request) as resp:
        if resp.status != 200:
            raise Exception  # todo error types
        else:
            response = await resp.json()
            return [LabeledText.from_json(output) for output in response['output']]


async def send_single_request(
    text: str,
    steps: dict,
    input_type: str,
    api_key: str
) -> Awaitable[List[LabeledText]]:
    timeout = aiohttp.ClientTimeout(total=6000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        return await _send_request(
            session,
            text,
            steps,
            input_type,
            api_key
        )


async def send_batch_request(
    batch: List[str],
    steps: dict,
    input_type: str,
    api_key: str
) -> Awaitable[List[List[LabeledText]]]:
    size = len(batch)
    results = [None] * size

    async def req_worker(session, task_id):
        for i in range(task_id, size, MAX_CONCURRENT_REQUESTS):
            results[i] = await _send_request(
                session,
                batch[task_id],
                steps,
                input_type,
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
