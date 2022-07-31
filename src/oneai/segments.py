import asyncio
from datetime import datetime, timedelta
from inspect import isawaitable
from typing import Awaitable, Callable, Dict, Iterable, List, Union

import aiohttp
import oneai

from oneai.api import post_pipeline
from oneai.classes import Input, Output, Skill
from oneai.exceptions import OneAIError


class Segment:
    async def run(
        self,
        input: Union[Input, Output, str],
        api_key: str,
        session: aiohttp.ClientSession,
    ) -> Output:
        """
        Run the pipeline segment and attach the output to the input if possible.

        ## Parameters

        `input: Input | Output | str`
            The input to process, either the original input text (`Input` or `str`) or the output of the previous segment (`Output`).
            If the input is an `Output`, the segment output will be attached to the parameter.
        `api_key: str`
            The API key to use for API segments.
        `session: aiohttp.ClientSession`
            Client session to use in segments.

        ## Returns

        `Output`
            The output of the segment.
        """
        raise NotImplementedError


# open a client session and send a request
async def process_single_input(
    input: Union[Input, str], segments: List[Segment], api_key: str
) -> Awaitable[Output]:
    timeout = aiohttp.ClientTimeout(total=6000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        return await _run_segments(session, input, segments, api_key)


# open a client session with multiple workers and send concurrent requests
async def process_batch(
    batch: Iterable[Union[str, Input]],
    segments: List[Segment],
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
            return next(iterator)
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
                    time_format(time_total / successful / oneai.MAX_CONCURRENT_REQUESTS),
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
                output = await _run_segments(session, input, segments, api_key)
                on_output(input, output)
                successful += 1
            except Exception as e:  # todo: break loop for some error types
                print(f"\r\033[K{oneai.__prefix__} Input {successful + failed}:", repr(e))
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


async def _run_segments(
    session: aiohttp.ClientSession,
    input: Union[Input, str],
    segments: List[Segment],
    api_key: str,
) -> Awaitable[Output]:
    if not segments:  # no skills
        return Output(input)

    output_top = await segments[0].run(input, api_key, session)
    output = output_top
    for segment in segments[1:]:
        while isinstance(
            output, Output
        ):  # find the last output to serve as the next input
            input = output
            output = output.data[-1] if output.data else None
        output = await segment.run(input, api_key, session)
    return output_top


class CustomSegment(Segment):
    def __init__(self, skill: Skill):
        self.skill = skill

    async def run(
        self,
        input: Union[Input, Output, str],
        api_key: str,
        session: aiohttp.ClientSession,
    ) -> Output:
        if not isinstance(input, Output):
            input = Output(input)
        try:
            output = self.skill.run_custom(input, session)
        except Exception as e:
            raise OneAIError(
                message=f"Error while running Skill {self.skill.api_name}: {e}"
            )
        if isawaitable(output):  # support async custom skills
            output = await output
        if isinstance(
            output, (str, Input)
        ):  # skill returned a string, construct an Output object for next segment
            output = Output(output)
        if self.skill.is_generator or not isinstance(
            output, Output
        ):  # either a new text or labels, set them as an attribute of the existing Output object
            input.add(self.skill, output)
        else:  # this is an edge case which should not happen
            input.merge(
                output
            )  # new_output was produced from same text as next_input, merge them
        return input


class APISegment(Segment):
    def __init__(self, skills: List[Skill]):
        self.skills = skills

    async def run(
        self,
        input: Union[Input, Output, str],
        api_key: str,
        session: aiohttp.ClientSession,
    ) -> Output:
        if isinstance(input, Output):
            output = await post_pipeline(session, input.text, self.skills, api_key)
            input.merge(output)
            output = input
        else:
            output = await post_pipeline(session, input, self.skills, api_key)
        return output
