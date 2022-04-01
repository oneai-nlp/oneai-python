import asyncio
from curses import raw
import oneai

from typing import Awaitable, Dict, Iterable, List, Union
from oneai.classes import Input, Output, Skill
from oneai.requests import send_batch_request, send_single_request


class Pipeline:
    def __init__(self, steps: List[Skill], api_key: str=None) -> None:
        self.steps = steps  # todo: validate (based on input_type)
        self.api_key = api_key

    def to_json(self) -> dict:
        result = []
        for skill in self.steps:
            result.append({
                'skill': skill.api_name,
                'params': {
                    p: skill.__getattribute__(p) for p in skill._skill_params
                }
            })
        return result
        
    def run(
        self,
        input: Union[str, Input],
        api_key: str=None
    ) -> Output:
        return asyncio.run(self.run_async(input, api_key))

    async def run_async(
        self,
        input: Union[str, Input],
        api_key: str=None
    ) -> Awaitable[Output]:
        raw_output = await send_single_request(
            input.get_text() if input is Input else input,
            self.to_json(),
            api_key=api_key or self.api_key or oneai.api_key,
        )
        return Output.build(self, raw_output)

    def run_batch(
        self,
        batch: Iterable[Union[str, Input]],
        api_key: str=None
    ) -> Dict[Union[str, Input], Output]:
        return asyncio.run(self.run_batch_async(batch, api_key))

    async def run_batch_async(
        self,
        batch: Iterable[Union[str, Input]],
        api_key: str=None
    ) -> Awaitable[Dict[Union[str, Input], Output]]:
        raw_output = await send_batch_request(
            batch,
            self.to_json(),
            api_key=api_key or self.api_key or oneai.api_key
        )
        return {
            # todo: this obviously should happen in parallel to the requests
            input: Output.build(self, output) 
                for input, output in raw_output.items()
                if not isinstance(output, Exception)
        }

    def __repr__(self) -> str:
        return f'oneai.Pipeline({self.steps})'
