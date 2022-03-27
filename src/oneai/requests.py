import asyncio
from typing import Awaitable, Dict, Generator, Iterable, List, Union

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
            print(f'Error: {resp.status} {await resp.text()}')
            raise Exception(f'Error: {resp.status} {await resp.text()}')  # todo error types
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
    batch: Iterable[Union[str, Input]],
    steps: dict,
    api_key: str
) -> Awaitable[Dict[Union[str, Input], List[LabeledText]]]:
    iterator = iter(batch)
    results = dict()

    def next_input():
        try: return next(iterator)
        except StopIteration: return None

    async def req_worker(session):
        input = next_input()
        while input:
            try: results[input] = await _send_request(
                session,
                input,
                steps,
                api_key
            )
            except Exception as e: results[input] = e
            input = next_input()

    timeout = aiohttp.ClientTimeout(total=6000)
    workers = []
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for _ in range(MAX_CONCURRENT_REQUESTS):
            worker = asyncio.create_task(req_worker(session))
            workers.append(worker)
        await asyncio.gather(*workers)
        return results
