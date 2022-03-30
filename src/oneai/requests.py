import asyncio
from datetime import datetime, timedelta
from typing import Awaitable, Dict, Iterable, Union

import aiohttp
import oneai

from oneai.classes import Input
from oneai.exceptions import handle_unsuccessful_response

MAX_CONCURRENT_REQUESTS = 4


async def _send_request(
    session: aiohttp.ClientSession,
    input: Union[Input, str],
    steps: dict,
    api_key: str
) -> Awaitable[Dict]:
    headers = {
        'api-key': api_key,
        'Content-Type': 'application/json'
    }
    request = {
        'text': input.get_text() if isinstance(input, Input) else str(input),
        'steps': steps,
        'input_type': input.type if isinstance(input, Input) else 'article'
    }
    async with session.post(oneai.URL, headers=headers, json=request) as response:
        if response.status != 200: 
            handle_unsuccessful_response(response)
        else:
            return await response.json()


async def send_single_request(
    input: Union[Input, str],
    steps: dict,
    api_key: str
) -> Awaitable[Dict]:
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
) -> Awaitable[Dict[Union[str, Input], Dict]]:
    iterator = iter(batch)
    results = dict()
    exceptions = 0
    time_total = timedelta()

    def next_input():
        try: return next(iterator)
        except StopIteration: return None  # we need to break loop for each worker, so we ignore StopIteration

    def print_progress(time_delta=timedelta(), start=False, end=False): # todo progress bar for iterables with __len__
        nonlocal time_total
        
        def time_format(time: timedelta):
            minutes = f'{time.seconds // 60}m ' if time.seconds > 59 else ''
            return minutes + f'{time.seconds % 60}s {time.microseconds // 1000}ms'

        total = len(results)
        time_total += time_delta
        if start: print(f'Starting processing batch with {MAX_CONCURRENT_REQUESTS} workers', end='\r')
        elif end: print('Processed %d inputs - %s/input - %s total - %d successful - %d failed' % (
            total,
            time_format(time_delta),
            time_format(time_total),
            len(results),
            total - len(results)
        ))
        else: print('Input %d - %s/input - %s total - %d successful - %d failed        ' % (
            total,
            time_format(time_delta),
            time_format(time_total),
            total - exceptions,
            exceptions
        ), end='\r')

    async def req_worker(session):
        nonlocal exceptions

        time_start = datetime.now()
        input = next_input()
        while input:
            try: results[input] = await _send_request(
                session,
                input,
                steps,
                api_key
            )
            except Exception as e:
                print('\r\033[K' + repr(e))
                results[input] = e
                exceptions += 1

            time_end = datetime.now()
            if oneai.PRINT_PROGRESS:
                print_progress(time_end - time_start)
            time_start = time_end
            input = next_input()

    timeout = aiohttp.ClientTimeout(total=6000)
    workers = []
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for _ in range(MAX_CONCURRENT_REQUESTS):
            worker = asyncio.create_task(req_worker(session))
            workers.append(worker)
        print_progress(start=True)
        await asyncio.gather(*workers)
        print_progress(end=True)
        return results
