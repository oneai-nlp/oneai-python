import aiohttp
import asyncio
import oneai

from typing import Awaitable, List, Literal
from oneai.classes import Skill, LabeledText

class Pipeline:
    def __init__(self, steps: List[Skill], input_type: Literal['article', 'transcription']=None, api_key: str=None) -> None:
        self.steps = steps # todo: validate (based on input_type)
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
        request = {
            'text': text,
            'steps': self.to_json(),
            'input_type': input_type or self.input_type or 'article'
        }
        headers = {
            'api-key': api_key or self.api_key or oneai.api_key,
            'Content-Type': 'application/json'
        }

        timeout = aiohttp.ClientTimeout(total=6000)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(oneai.URL, headers=headers, json=request) as resp:
                if resp.status != 200:
                    raise Exception # todo error types
                else:
                    response = await resp.json()
                    return [LabeledText(output['text'], output['labels']) for output in response['output']]

    def __repr__(self) -> str:
        return f'oneai.Pipeline({self.steps})'
