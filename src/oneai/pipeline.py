import asyncio
import oneai

from typing import Awaitable, List, Literal
from oneai.classes import Skill, LabeledText
from oneai.requests import send_batch_request, send_single_request


class Pipeline:
    def __init__(self, steps: List[Skill], input_type: Literal['article', 'transcription']=None, api_key: str=None) -> None:
        self.steps = steps  # todo: validate (based on input_type)
        self.input_type = input_type
        self.api_key = api_key

    def to_json(self) -> dict:
        result = []
        for skill in self.steps:
            result.append({
                'skill': skill.name,
                'params': {
                    p: skill.__getattribute__(p) for p in skill._param_fields
                }
            })
        return result
        
    def run(
        self,
        text: str,
        input_type: Literal['article', 'transcription']=None,
        api_key: str=None
    ) -> List[LabeledText]:
        return asyncio.run(self.run_async(text, input_type, api_key))

    async def run_async(
        self,
        text: str,
        input_type: Literal['article', 'converstion']=None,
        api_key: str=None
    ) -> Awaitable[List[LabeledText]]:
        return await send_single_request(
            text,
            self.to_json(),
            api_key=api_key or self.api_key or oneai.api_key,
            input_type=input_type or self.input_type or 'article'
        )

    def run_batch(
        self,
        batch: List[str],
        input_type: Literal['article', 'converstion']=None,
        api_key: str=None
    ) -> List[List[LabeledText]]:
        return asyncio.run(self.run_batch_async(batch, input_type, api_key))

    async def run_batch_async(
        self,
        batch: List[str],
        input_type: Literal['article', 'converstion']=None,
        api_key: str=None
    ) -> Awaitable[List[List[LabeledText]]]:
        return await send_batch_request(
            batch,
            self.to_json(),
            api_key=api_key or self.api_key or oneai.api_key,
            input_type=input_type or self.input_type or 'article'
        )

    def __repr__(self) -> str:
        return f'oneai.Pipeline({self.steps})'
