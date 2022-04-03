from dataclasses import dataclass, field
import json
from typing import Iterable, List, Type, Union


@dataclass
class Skill:
    '''
    Args:
        api_name: The name of the Skill in the pipeline API.
        is_generator: Whether the Skill is a generator.
        skill_params: Names of the fields of the Skill object that should be passed as parameters to the API.
        label_type: If the Skill generates labels, the type name of the label.
        output_attr: The attribute name of the Skill's output in the Output object.
    '''
    api_name: str = ''
    is_generator: bool = False
    _skill_params: List[str] = field(default_factory=list, repr=False, init=False)
    label_type: str = ''
    output_attr: str = ''


def skillclass(
    cls: Type=None,
    api_name: str='',
    label_type: str='',
    is_generator: bool=False,
    output_attr: str = ''
):
    def wrap(cls) -> cls:
        if not issubclass(cls, Skill):
            print(f'warning: class {cls.__name__} decorated with @skillclass does not inherit Skill')

        def __init__(self, *args, **kwargs):
            cls_init(self, *args, **kwargs)
            Skill.__init__(self, api_name=api_name, label_type=label_type, is_generator=is_generator, output_attr=output_attr)
            self._skill_params = [a for a in self.__dict__ if not (a in Skill.__dict__ or a == '_skill_params')]
        
        cls_init = cls.__init__
        cls.__init__ = __init__
        return cls
    
    return wrap if cls is None else wrap(cls)


class Input:
    def __init__(self, type: str):
        self.type = type

    @classmethod
    def parse(cls, text: str) -> 'Input':
        raise NotImplementedError()

    def get_text(self) -> str:
        raise NotImplementedError()

class Document(Input):
    def __init__(self, text: str):
        super().__init__('article')
        self.text = text

    @classmethod
    def parse(cls, text: str) -> 'Document':
        return cls(text)

    def get_text(self) -> str:
        return self.text

@dataclass
class Utterance:
    speaker: str
    utterance: str

    def __repr__(self) -> str:
        return f'\n\t{self.speaker}: {self.utterance}'

class Conversation(Input):
    def __init__(self, utterances: List[Utterance]=[]):
        super().__init__('conversation')
        self.utterances = utterances

    def get_text(self) -> str:
        return json.dumps(self.utterances, default=lambda o: o.__dict__)

    @classmethod
    def parse(cls, text: str) -> 'Conversation':
        try:
            js = json.loads(text)
            return cls([Utterance(**utterance) for utterance in js])
        except json.JSONDecodeError:
            from oneai.parsing import parse_conversation
            return parse_conversation(text)

    def __repr__(self) -> str:
        return f'oneai.Conversation{repr(self.utterances)}'

@dataclass
class Label:
    type: str = ''
    name: str = ''
    span: List[int] = field(default_factory=lambda: [0, 0])
    value: str = ''

    @classmethod
    def from_json(cls, json): return cls(
        type=json.get('type', ''),
        name=json.get('name', ''),
        span=json.get('span', [0, 0]),
        value=json.get('value', '')
    )

    def __repr__(self) -> str:
        return 'oneai.Label(' + ', '.join(f'{k}={v}' for k, v in self.__dict__.items() if v) + ')'

@dataclass
class Output:
    text: str
    skills: List[Skill] # not a dict since Skills are currently mutable & thus unhashable
    data: List[Union[List[Label], 'Output']]

    def __getitem__(self, name: str) -> Union[List[Label], 'Output']:
        return self.__getattr__(name)

    def __getattr__(self, name: str) -> Union[List[Label], 'Output']:
        for i, skill in enumerate(self.skills):
            if (skill.api_name and skill.api_name == name) or \
                (skill.output_attr and name in skill.output_attr) or \
                (type(skill).__name__ == name):
                return self.data[i]
        raise AttributeError(f'{name} not found in {self}')

    def __dir__(self) -> Iterable[str]:
        return super().__dir__() + [skill.output_attr or skill.api_name for skill in self.skills]

    @classmethod
    def build(
        cls,
        pipeline, 
        raw_output: dict,
        output_index: int=0, 
        skill_index: int=0,
        input_type: type=str
    ) -> 'Output':
        if skill_index == 0 and pipeline.steps[0].is_generator:
            text = raw_output['input_text']
            return cls(
                text=input_type.parse(text) if issubclass(input_type, Input) else text,
                skills=[pipeline.steps[0]],
                data=[cls.build(pipeline, raw_output, output_index, skill_index + 1)]
            )

        text = raw_output['output'][output_index]['text']
        skills = pipeline.steps[skill_index:]
        labels = [Label.from_json(label) for label in raw_output['output'][output_index]['labels']]
        data = []
        for i, skill in enumerate(skills):
            if skill.is_generator:
                data.append(cls.build(pipeline, raw_output, output_index + 1, skill_index + 1 + i))
            else:
                data.append(list(filter(lambda label: label.type == skill.label_type, labels)))
        return cls(text=text, skills=skills, data=data)

    def __repr__(self) -> str:
        result = f'oneai.Output(text={repr(self.text)}'
        for i, skill in enumerate(self.skills):
            result += f', {skill.api_name}={repr(self.data[i])}'
        return result + ')'
