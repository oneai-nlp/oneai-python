import asyncio
import oneai

from typing import Awaitable, Dict, Iterable, List, Union
from oneai.classes import Input, Output, Skill


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
        input: Union[str, Input, Iterable[Union[str, Input]]],
        api_key: str=None
    ) -> Output:
        return asyncio.run(self.run_async(input, api_key))

    async def run_async(
        self,
        input: Union[str, Input, Iterable[Union[str, Input]]],
        api_key: str=None
    ) -> Awaitable[Output]:
        if isinstance(input, (str, Input)):
            from oneai.requests import send_single_request
            return await send_single_request(
                input,
                self,
                api_key=api_key or self.api_key or oneai.api_key,
            )
        elif isinstance(input, Iterable):
            return await self.run_batch_async(input, api_key)
        else: raise TypeError(f'pipeline input must be Input, str or iterable of inputs')

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
        from oneai.requests import send_batch_request
        return await send_batch_request(
            batch,
            self,
            api_key=api_key or self.api_key or oneai.api_key
        )

    def __repr__(self) -> str:
        return f'oneai.Pipeline({self.steps})'
