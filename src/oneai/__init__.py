import asyncio
from typing import Awaitable, List, Literal
import aiohttp

import oneai.skills as skills
from oneai.classes import *

URL = 'https://api.oneai.com/api/v0/pipeline'

api_key = ''

def process(text: str, skills: List[Skill], inputType: Literal['article', 'transcription']='article') -> List[LabeledText]:
    return asyncio.run(process_async(text, skills, inputType))

async def process_async(text: str, skills: List[Skill], inputType: Literal['article', 'transcription']='article') -> Awaitable[List[LabeledText]]:
    def build_skills(skills: List[Skill]) -> List[dict]:
        result = []
        input = 0
        for id, skill in enumerate(skills):
            result.append({
                'skill': skill.name,
                'input': input,
                'id': id + 1,
                'params': {
                    p: skill.__getattribute__(p) for p in skill._param_fields
                }
            })
            if skill.iswriting: input = id + 1
        return result


    def build_output(output_raw) -> List[LabeledText]: 
        def build_label(label_raw: dict) -> Label: return Label(
            type=label_raw.get('type', ''),
            name=label_raw.get('name', ''),
            span=label_raw.get('span', [0, 0]),
            value=label_raw.get('value', .0)
        )

        return [
            LabeledText(
                text=labeled_text['text'],
                labels=[build_label(label) for label in labeled_text['labels']]
            ) for labeled_text in output_raw
        ]

    ##############################################

    request = {
        'text': text,
        'steps': build_skills(skills),
        'include_intermediates': True,
        'input_type': inputType
    }
    headers = {
        'api-key': api_key,
        'Content-Type': 'application/json'
    }

    timeout = aiohttp.ClientTimeout(total=6000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(URL, headers=headers, json=request) as resp:
            if resp.status != 200:
                raise Exception # todo error types
            else:
                response = await resp.json()
                return build_output(response['output'])
