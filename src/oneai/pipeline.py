import asyncio, concurrent.futures
import oneai

from typing import Awaitable, Dict, Iterable, List, Union
from oneai.classes import Input, Output, Skill


class Pipeline:
    """
    Language AI pipelines allow invoking and chaining multiple Language Skills to process your input text with a single API call.

    ## Attributes

    `steps: list[Skill]`
        A list of Language Skills to process the input text. The order of the skills in the list determines their input.
    `api_key: str, optional`
        An API key to be used in this pipelines `run` calls. If not provided, the global `oneai.api_key` is used.

    ## Methods

    `run(input, api_key=None) -> Output`
        Runs the pipeline on the input text.
    `run_async(input, api_key=None) -> Awaitable[Output]`
        Runs the pipeline on the input text asynchronously.
    `run_batch(batch, api_key=None) -> Dict[Input, Output]`
        Runs the pipeline on a batch of input texts.
    `run_batch_async(batch, api_key=None) -> Awaitable[Dict[Input, Output]]`
        Runs the pipeline on a batch of input texts asynchronously.

    ## Pipeline Ordering

    The order of the skills in the pipeline determines their input:
    * Skills that are placed after a generator Skill will receive its output as input.
    * If there's no preceding generator Skill, the original input text is used.

    ## Example

    >>> my_text = 'ENTER-YOUR-TEXT-HERE'
    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Topics(),
    ...     oneai.skills.Summarize(min_length=20),
    ...     oneai.skills.Entities()
    ... ])
    >>> output = pipeline.run(my_text)
    >>> output.topics
    [oneai.Label(type=topic, span=[0, 10], name=topic1), ...] # topics from my_text
    >>> output.summary.text
    '...' # summary of my_text
    >>> output.summary.entities
    [oneai.Label(type=entity, span=[0, 10], name=entity1), ...] # entities from the summary
    """

    def __init__(self, steps: List[Skill], api_key: str = None) -> None:
        self.steps = steps  # todo: validate (based on input_type)
        self.api_key = api_key

    def _split_segments(self) -> List[Union[List[Skill], Skill]]:
        if not self.steps:
            return []
        # split into segments of skills, by where these skills should run (custom skills count as a separate segment)
        segments = []
        current_segment = 0
        for i, skill in enumerate(self.steps):
            if skill.run_custom is not None:
                if i - current_segment:
                    segments.append(self.steps[i:current_segment])
                    current_segment = i
                segments.append(skill)
        if i - current_segment:
            segments.append(self.steps[i:current_segment])
        return segments

    def run(
        self, input: Union[str, Input, Iterable[Union[str, Input]]], api_key: str = None
    ) -> Output:
        """
        Runs the pipeline on the input text.

        ## Parameters

        `input: str | Input | Iterable[str | Input]]`
            The input text (or multiple input texts) to be processed.
        `api_key: str, optional`
            An API key to be used in this API call. If not provided, `self.api_key` is used.

        ## Returns

        An `Output` object containing the results of the Skills in the pipeline.

        ## Raises

        `InputError` if the input is is invalid or is of an incompatible type for the pipeline.
        `APIKeyError` if the API key is invalid, expired, or missing quota.
        `ServerError` if an internal server error occured.
        """
        return _async_run_nested(self.run_async(input, api_key))

    async def run_async(
        self, input: Union[str, Input, Iterable[Union[str, Input]]], api_key: str = None
    ) -> Awaitable[Output]:
        """
        Runs the pipeline on the input text asynchronously.

        ## Parameters

        `input: str | Input | Iterable[str | Input]]`
            The input text (or multiple input texts) to be processed.
        `api_key: str, optional`
            An API key to be used in this API call. If not provided, `self.api_key` is used.

        ## Returns

        An Awaitable with an `Output` object containing the results of the Skills in the pipeline.

        ## Raises

        `InputError` if the input is is invalid or is of an incompatible type for the pipeline.
        `APIKeyError` if the API key is invalid, expired, or missing quota.
        `ServerError` if an internal server error occured.
        """
        if isinstance(input, (str, Input)):
            from oneai.requests import send_single_request

            return await send_single_request(
                input,
                self,
                api_key=api_key or self.api_key or oneai.api_key,
            )
        elif isinstance(input, Iterable):
            return await self.run_batch_async(input, api_key)
        else:
            raise TypeError(f"pipeline input must be Input, str or iterable of inputs")

    def run_batch(
        self, batch: Iterable[Union[str, Input]], api_key: str = None
    ) -> Dict[Union[str, Input], Output]:
        """
        Runs the pipeline on a batch of input texts.

        ## Parameters

        `batch: Iterable[str | Input]`
            The input texts to be processed.
        `api_key: str, optional`
            An API key to be used in this API call. If not provided, `self.api_key` is used.

        ## Returns

        A dictionary mapping inputs to the produced `Output` objects, each containing the results of the Skills in the pipeline.

        ## Raises

        `InputError` if the input is is invalid or is of an incompatible type for the pipeline.
        `APIKeyError` if the API key is invalid, expired, or missing quota.
        `ServerError` if an internal server error occured.
        """
        return _async_run_nested(self.run_batch_async(batch, api_key))

    async def run_batch_async(
        self, batch: Iterable[Union[str, Input]], api_key: str = None
    ) -> Awaitable[Dict[Union[str, Input], Output]]:
        """
        Runs the pipeline on a batch of input texts asynchronously.

        ## Parameters

        `batch: Iterable[str | Input]`
            The input texts to be processed.
        `api_key: str, optional`
            An API key to be used in this API call. If not provided, `self.api_key` is used.

        ## Returns

        An Awaitable with a dictionary mapping inputs to the produced `Output` objects, each containing the results of the Skills in the pipeline.

        ## Raises

        `InputError` if the input is is invalid or is of an incompatible type for the pipeline.
        `APIKeyError` if the API key is invalid, expired, or missing quota.
        `ServerError` if an internal server error occured.
        """
        from oneai.requests import send_batch_request

        return await send_batch_request(
            batch, self, api_key=api_key or self.api_key or oneai.api_key
        )

    def __repr__(self) -> str:
        return f"oneai.Pipeline({self.steps})"


# for jupyter environment, to avoid "asyncio.run() cannot be called from a running event loop"
pool = concurrent.futures.ThreadPoolExecutor()


def _async_run_nested(coru):
    try:
        asyncio.get_running_loop()
        return pool.submit(asyncio.run, coru).result()
    except RuntimeError:
        return asyncio.run(coru)
