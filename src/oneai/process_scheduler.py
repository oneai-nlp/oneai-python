import asyncio
from datetime import datetime, timedelta
import io
import logging
from typing import Awaitable, Callable, Iterable, List, Tuple, TYPE_CHECKING

import aiohttp

import oneai
from oneai.api.output import build_output
from oneai.api.pipeline import post_pipeline, post_pipeline_async, get_task_status
from oneai.classes import Input, PipelineInput, Skill, CSVParams
from oneai.exceptions import ServerError, handle_unsuccessful_response, OneAIError
from oneai.output import Output

logger = logging.getLogger("oneai")


def time_format(time: timedelta):
    minutes = f"{time.seconds // 60}m " if time.seconds > 59 else ""
    return minutes + f"{time.seconds % 60}s {time.microseconds // 1000}ms"


STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"


# open a client session and send a request
async def process_single_input(
    input: PipelineInput,
    steps: List[Skill],
    api_key: str,
    multilingual: bool = False,
    csv_params: CSVParams = None,
) -> Awaitable[Output]:
    timeout = aiohttp.ClientTimeout(total=6000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        return await _run_internal(
            session, input, steps, api_key, multilingual, csv_params
        )


async def process_single_input_async(
    input: PipelineInput,
    steps: List[Skill],
    api_key: str,
    interval: int,
    multilingual: bool = False,
    csv_params: CSVParams = None,
    polling: bool = True,
) -> Awaitable[Output]:
    if isinstance(input.text, io.TextIOBase):
        input._make_sync()
    timeout = aiohttp.ClientTimeout(total=6000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        name = f" '{input.text.name}'" if hasattr(input.text, "name") else ""
        logger.debug(f"Uploading input{name}...")
        task_id = (
            await post_pipeline_async(
                session, input, steps, api_key, multilingual, csv_params
            )
        )["task_id"]
        logger.debug(f"Upload of input{name} complete\n")
        return (
            await task_polling(task_id, session, api_key, steps, interval)
            if polling
            else Output(None, steps, task_id=task_id)
        )


async def task_polling(
    task_id: str,
    session: aiohttp.ClientSession,
    api_key: str,
    steps: List[Skill],
    interval: int,
) -> Awaitable[Output]:
    timeout = aiohttp.ClientTimeout(total=6000)
    close = session is None
    if session == None:
        session = aiohttp.ClientSession(timeout=timeout)
    status, response = "", None
    start = datetime.now()
    while status != STATUS_COMPLETED:
        status, response = await process_task_status(task_id, session, api_key, steps)
        if status == STATUS_FAILED:
            raise response
        logger.debug(
            f"Processing input - status {status} - {time_format(datetime.now() - start)}"
        )
        await asyncio.sleep(interval)
    logger.debug(
        f"Processing of input complete - {time_format(datetime.now() - start)} total\n"
    )
    if close:
        await session.close()
    return response


async def process_task_status(
    task_id: str,
    session: aiohttp.ClientSession,
    api_key: str,
    steps: List[Skill],
) -> Awaitable[Tuple[str, Output]]:
    timeout = aiohttp.ClientTimeout(total=6000)
    close = session is None
    if session == None:
        session = aiohttp.ClientSession(timeout=timeout)
    response = await get_task_status(session, task_id, api_key)
    status = response["status"]
    if status == STATUS_FAILED:
        try:
            await handle_unsuccessful_response(response["result"])
        except OneAIError as e:
            return status, e
    elif status == STATUS_COMPLETED:
        return status, build_output(
            steps, response["result"], {"x-oneai-request-id": task_id}
        )
    if close:
        await session.close()
    return status, None


# open a client session with multiple workers and send concurrent requests
async def process_batch(
    batch: Iterable[PipelineInput],
    steps: List[Skill],
    on_output: Callable[[PipelineInput, Output], None],
    on_error: Callable[[PipelineInput, Exception], None],
    api_key: str,
    multilingual: bool = False,
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

    def log_progress(
        time_delta=timedelta(), start=False, end=False
    ):  # todo progress bar for iterables with __len__
        nonlocal successful, failed, time_total

        time_total += time_delta
        if start:
            logger.debug(
                f"Starting batch processing with {oneai.MAX_CONCURRENT_REQUESTS} workers"
            )
        elif end:
            logger.debug(
                "Processed %d inputs - %s/input - %s total - %d successful - %d failed\n"
                % (
                    successful + failed,
                    time_format(
                        time_total
                        / (successful + failed)
                        / oneai.MAX_CONCURRENT_REQUESTS
                    ),
                    time_format(time_total / oneai.MAX_CONCURRENT_REQUESTS),
                    successful,
                    failed,
                )
            )
        else:
            logger.debug(
                "Input %d - %s/input - %s total - %d successful - %d failed"
                % (
                    successful + failed,
                    time_format(time_delta),
                    time_format(time_total / oneai.MAX_CONCURRENT_REQUESTS),
                    successful,
                    failed,
                )
            )

    async def req_worker(session):  # run requests sequentially
        nonlocal successful, failed

        time_start = datetime.now()
        input = next_input()
        while input:
            try:
                output = await _run_internal(
                    session, input, steps, api_key, multilingual
                )
                on_output(input, output)
                successful += 1
            except Exception as e:  # todo: break loop for some error types
                logger.error(f"Input {successful + failed}: {repr(e)}")
                on_error(input, e)
                failed += 1

            time_end = datetime.now()
            log_progress(time_end - time_start)
            time_start = time_end
            input = next_input()

    workers = []
    timeout = aiohttp.ClientTimeout(total=6000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for _ in range(oneai.MAX_CONCURRENT_REQUESTS):
            worker = asyncio.create_task(req_worker(session))
            workers.append(worker)
        log_progress(start=True)
        await asyncio.gather(*workers)
        log_progress(end=True)


async def fetch_url(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as response:
        if response.status != 200:
            raise ServerError(
                50001,
                "Retrieve URL failed",
                f"Failed to retrieve the input from url '{url}'.",
            )
        return Input(await response.text(), type="article", content_type="text/plain")


async def _run_internal(
    session: aiohttp.ClientSession,
    input: Input,
    skills: List[Skill],
    api_key: str,
    multilingual: bool,
    csv_params: CSVParams = None,
) -> Awaitable[Output]:
    if not skills:  # no skills
        return Output(input.text)

    if input.content_type == "text/uri-list":
        input = await fetch_url(session, input.text)
    input._make_sync()  # make input compatible with sync API
    return await post_pipeline(
        session, input, skills, api_key, multilingual, csv_params
    )
