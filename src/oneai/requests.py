import asyncio
from datetime import datetime, timedelta
from inspect import isawaitable
from typing import Awaitable, Dict, Iterable, List, Union

import aiohttp
import oneai

from oneai.classes import Input, Output, Skill
from oneai.exceptions import handle_unsuccessful_response


async def _send_request(
    session: aiohttp.ClientSession,
    input: Union[Input, str],
    steps: List[Skill],
    api_key: str,
) -> Awaitable[Output]:
    headers = {"api-key": api_key, "Content-Type": "application/json"}
    request = {
        "text": input.get_text() if isinstance(input, Input) else str(input),
        "steps": [skill.asdict() for skill in steps],
        "input_type": input.type if isinstance(input, Input) else "article",
    }
    async with session.post(oneai.URL, headers=headers, json=request) as response:
        if response.status != 200:
            await handle_unsuccessful_response(response)
        else:
            return Output.build(steps, await response.json(), input_type=type(input))


async def _work_segmented_pipeline(
    session: aiohttp.ClientSession,
    input: Union[Input, str],
    segments: List[Union[Skill, List[Skill]]],
    api_key: str,
) -> Awaitable[Output]:
    output = Output(input)
    next_input = output
    for segment in segments:
        if isinstance(segment, Skill):
            new_output = segment.run_custom(next_input, session)
            if isawaitable(new_output):
                new_output = await new_output
            if isinstance(new_output, str):
                new_output = Output(new_output)
            if segment.is_generator or not isinstance(new_output, Output):
                next_input.attach(segment, new_output)
            else:
                next_input.merge(new_output)
                new_output = next_input
        else:
            new_output = await _send_request(session, next_input.text, segment, api_key)
            next_input.merge(new_output)
        while isinstance(new_output, Output):
            next_input = new_output
            new_output = new_output.data[-1] if new_output.data else None
    return output


async def send_single_request(
    input: Union[Input, str], pipeline: oneai.Pipeline, api_key: str
) -> Awaitable[Output]:
    timeout = aiohttp.ClientTimeout(total=6000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        segments = pipeline._split_segments()
        return await (
            _send_request(session, input, segments[0], api_key)
            if len(segments) <= 1
            else _work_segmented_pipeline(session, input, segments, api_key)
        )


async def send_batch_request(
    batch: Iterable[Union[str, Input]], pipeline: oneai.Pipeline, api_key: str
) -> Awaitable[Dict[Union[str, Input], Output]]:
    iterator = iter(batch)
    results = dict()
    exceptions = 0
    time_total = timedelta()
    segments = pipeline._split_segments()
    is_segmented = len(segments) > 1

    def next_input():
        try:
            return next(iterator)
        except StopIteration:
            return None  # we need to break loop for each worker, so we ignore StopIteration

    def print_progress(
        time_delta=timedelta(), start=False, end=False
    ):  # todo progress bar for iterables with __len__
        nonlocal time_total

        def time_format(time: timedelta):
            minutes = f"{time.seconds // 60}m " if time.seconds > 59 else ""
            return minutes + f"{time.seconds % 60}s {time.microseconds // 1000}ms"

        total = len(results)
        time_total += time_delta
        if start:
            print(
                f"Starting processing batch with {oneai.MAX_CONCURRENT_REQUESTS} workers",
                end="\r",
            )
        elif end:
            print(
                "Processed %d inputs - %s/input - %s total - %d successful - %d failed"
                % (
                    total,
                    time_format(time_delta),
                    time_format(time_total),
                    total - exceptions,
                    exceptions,
                )
            )
        else:
            print(
                "Input %d - %s/input - %s total - %d successful - %d failed        "
                % (
                    total,
                    time_format(time_delta),
                    time_format(time_total),
                    total - exceptions,
                    exceptions,
                ),
                end="\r",
            )

    async def req_worker(session):
        nonlocal exceptions

        time_start = datetime.now()
        input = next_input()
        while input:
            try:
                results[input] = await (
                    _work_segmented_pipeline(session, input, pipeline, api_key)
                    if is_segmented
                    else _send_request(session, input, segments[0], api_key)
                )
            except Exception as e:
                print(f"\r\033[KInput {len(results)}:", repr(e))
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
        for _ in range(oneai.MAX_CONCURRENT_REQUESTS):
            worker = asyncio.create_task(req_worker(session))
            workers.append(worker)
        print_progress(start=True)
        await asyncio.gather(*workers)
        print_progress(end=True)
        return results
