import asyncio
import io
from datetime import datetime, timedelta
from typing import Awaitable, Callable, Iterable, List

import aiohttp

import oneai
from oneai.api import post_pipeline
from oneai.api.async_api import monitor_task
from oneai.api.pipeline import post_pipeline_async_file
from oneai.classes import Input, Output, PipelineInput, Skill


# open a client session and send a request
async def process_single_input(
    input: PipelineInput, steps: List[Skill], api_key: str, sync: bool
) -> Awaitable[Output]:
    timeout = aiohttp.ClientTimeout(total=6000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        return await _run_internal(session, Input.wrap(input, sync), steps, api_key, sync)


# open a client session with multiple workers and send concurrent requests
async def process_batch(
    batch: Iterable[PipelineInput],
    steps: List[Skill],
    on_output: Callable[[Input, Output], None],
    on_error: Callable[[Input, Exception], None],
    api_key: str,
):
    iterator = iter(batch)
    successful = 0  # total successful responses
    failed = 0  # number of exceptions occurred
    time_total = timedelta()  # total time spent on all requests
    # length = len(batch) if hasattr(batch, "__len__") else 0

    def next_input():  # distribute batch to workers
        try:
            return Input.wrap(next(iterator))
        except StopIteration:
            return None  # we need to break loop for each worker, so we ignore StopIteration

    def print_progress(
        time_delta=timedelta(), start=False, end=False
    ):  # todo progress bar for iterables with __len__
        nonlocal successful, failed, time_total

        def time_format(time: timedelta):
            minutes = f"{time.seconds // 60}m " if time.seconds > 59 else ""
            return minutes + f"{time.seconds % 60}s {time.microseconds // 1000}ms"

        time_total += time_delta
        if start:
            print(
                f"{oneai.__prefix__} Starting processing batch with {oneai.MAX_CONCURRENT_REQUESTS} workers",
                end="\r",
            )
        elif end:
            print(
                "%s Processed %d inputs - %s/input - %s total - %d successful - %d failed"
                % (
                    oneai.__prefix__,
                    successful + failed,
                    time_format(
                        time_total / successful / oneai.MAX_CONCURRENT_REQUESTS
                    ),
                    time_format(time_total / oneai.MAX_CONCURRENT_REQUESTS),
                    successful,
                    failed,
                )
            )
        else:
            print(
                "%s Input %d - %s/input - %s total - %d successful - %d failed        "
                % (
                    oneai.__prefix__,
                    successful + failed,
                    time_format(time_delta),
                    time_format(time_total / oneai.MAX_CONCURRENT_REQUESTS),
                    successful,
                    failed,
                ),
                end="\r",
            )

    async def req_worker(session):  # run requests sequentially
        nonlocal successful, failed

        time_start = datetime.now()
        input = next_input()
        while input:
            try:
                output = await _run_internal(session, input, steps, api_key, True)
                on_output(input, output)
                successful += 1
            except Exception as e:  # todo: break loop for some error types
                print(f"\r\033[KInput {successful + failed}:", repr(e))
                on_error(input, e)
                failed += 1

            time_end = datetime.now()
            if oneai.PRINT_PROGRESS:
                print_progress(time_end - time_start)
            time_start = time_end
            input = next_input()

    workers = []
    timeout = aiohttp.ClientTimeout(total=6000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for _ in range(oneai.MAX_CONCURRENT_REQUESTS):
            worker = asyncio.create_task(req_worker(session))
            workers.append(worker)
        print_progress(start=True)
        await asyncio.gather(*workers)
        print_progress(end=True)


async def _run_internal(
    session: aiohttp.ClientSession,
    input: Input,
    skills: List[Skill],
    api_key: str,
    sync: bool,
) -> Awaitable[Output]:
    if not skills:  # no skills
        return Output(input.text)

    if (not sync) and isinstance(input.text, io.IOBase):
        task_id = (await post_pipeline_async_file(session, input.text, skills, api_key))['task_id']
        output = await monitor_task(session, task_id, oneai.api_key)
    else:
        output = await post_pipeline(session, input, skills, api_key)

    return output
