import asyncio
from dataclasses import dataclass, field
from typing import Awaitable, List, Literal, Tuple, Type

import aiohttp
import oneai


@dataclass
class Skill:
    name: str = ''
    iswriting: bool = False
    _param_fields: List[str] = field(default_factory=list, repr=False, init=False)


def skillclass(cls: Type=None, name: str='', iswriting: bool=False, param_fields: List[str]=[]):
    def wrap(cls):
        if not issubclass(cls, Skill):
            print(f'warning: class {cls.__name__} decorated with @skillclass does not inherit Skill')

        def __init__(self, *args, **kwargs):
            cls_init(self, *args, **kwargs)
            Skill.__init__(self, name=name, iswriting=iswriting)
            self._param_fields = param_fields
        
        cls_init = cls.__init__
        cls.__init__ = __init__
        return cls
    
    return wrap if cls is None else wrap(cls)


@dataclass
class Label:
    type: str = ''
    name: str = ''
    span: Tuple[int] = (0, 0)
    value: float = .0


@dataclass
class LabeledText:
    text: str
    labels: List[Label]


class Pipeline:
    def __init__(self, steps: List[Skill], input_type: Literal['article', 'transcription']=None, api_key: str=None) -> None:
        self.steps = steps
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
