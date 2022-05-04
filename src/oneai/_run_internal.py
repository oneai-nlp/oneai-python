import asyncio
from datetime import datetime, timedelta
from inspect import isawaitable
from typing import Awaitable, Dict, Iterable, List, Union

import aiohttp
import oneai

from oneai.api import send_pipeline_request
from oneai.classes import Input, Output, Skill
from oneai.exceptions import OneAIError

# open a client session and send a request
async def _run_single_input(
    input: Union[Input, str], pipeline: oneai.Pipeline, api_key: str
) -> Awaitable[Output]:
    timeout = aiohttp.ClientTimeout(total=6000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        segments = pipeline._split_segments()
        return await _run_segmented_pipeline(session, input, segments, api_key)


# open a client session with multiple workers and send concurrent requests
async def _run_batch(
    batch: Iterable[Union[str, Input]], pipeline: oneai.Pipeline, api_key: str
) -> Awaitable[Dict[Union[str, Input], Output]]:
    iterator = iter(batch)
    results = dict()
    exceptions = 0 # number of exceptions occurred
    time_total = timedelta() # total time spent on all requests
    segments = pipeline._split_segments() # segmented pipeline

    def next_input(): # distribute batch to workers
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

    async def req_worker(session): # run requests sequentially
        nonlocal exceptions 

        time_start = datetime.now()
        input = next_input()
        while input:
            try:
                results[input] = await _run_segmented_pipeline(session, input, segments, api_key)
            except Exception as e: # todo: break loop for some error types
                print(f"\r\033[KInput {len(results)}:", repr(e))
                results[input] = e
                exceptions += 1

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
        return results


# run the pipeline sequentially by segments (either lists of API skills, or a single custom skill)
async def _run_segmented_pipeline(
    session: aiohttp.ClientSession,
    input: Union[Input, str],
    segments: List[Union[Skill, List[Skill]]],
    api_key: str,
) -> Awaitable[Output]:
    if not segments: # no skills
        return Output(input)
    if len(segments) == 1: # single segment
        if isinstance(segments[0], Skill): # single custom skill
            output = segments[0].run_custom(input, session)
            if not isawaitable(output):
                return output
        else: # single API segment
            output = send_pipeline_request(session, input, segments[0], api_key)
        return await output
    
    output = Output(input) # result Output object
    next_input = output # input of the next segment (output of the previous segment)
    for segment in segments:
        if isinstance(segment, Skill): # custom skill
            try:
                new_output = segment.run_custom(next_input, session)
            except Exception as e:
                raise OneAIError(message=f"Error while running Skill {segment.name}: {e}")
            if isawaitable(new_output): # support async custom skills
                new_output = await new_output
            if isinstance(new_output, str): # skill returned a string, construct an Output object for next outputs
                new_output = Output(new_output)
            if segment.is_generator or not isinstance(new_output, Output): # either a new text or labels, set them as an attribute of the existing Output object
                next_input.set(segment, new_output)
            else:
                next_input.merge(new_output) # new_output was produced from same text as next_input, merge them
                new_output = next_input
        else: # API request
            new_output = await send_pipeline_request(session, next_input.text, segment, api_key)
            next_input.merge(new_output)
        while isinstance(new_output, Output): # find the deepest nested Output object (represents the last text generated in the pipeline) to serve as next_input
            next_input = new_output
            new_output = new_output.data[-1] if new_output.data else None
    return output
