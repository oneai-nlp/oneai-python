from copy import copy
from dataclasses import dataclass, field
import json
from typing import Iterable, List, Tuple, Type, Union

_SkillInput = Type[Union[str, 'Input']]
_SkillOutput = Type[Tuple[Union[str, 'Input'], str]]


@dataclass
class Skill:
    '''
    Args:
        api_name: The name of the Skill in the pipeline API.
        is_generator: Whether the Skill is a generator.
        skill_params: Names of the fields of the Skill object that should be passed as parameters to the API.
        label_type: If the Skill generates labels, the type name of the label.
        output_attr: The attribute name of the Skill's output in the Output object.
        output_attr1: Only for Skills with 2 outputs (text / labels)
    '''
    api_name: str = ''
    is_generator: bool = False
    _skill_params: List[str] = field(default_factory=list, repr=False, init=False)
    # todo: replace all these w/ an output type object + parse conversations from t. enhancer etc.
    label_type: str = ''
    output_attr: str = ''
    output_attr1: str = ''
    

def skillclass(
    cls: Type=None,
    api_name: str='',
    label_type: str='',
    is_generator: bool=False,
    output_attr: str = '',
    output_attr1: str = ''
):
    def wrap(cls) -> cls:
        if not issubclass(cls, Skill):
            print(f'warning: class {cls.__name__} decorated with @skillclass does not inherit Skill')

        def __init__(self, *args, **kwargs):
            cls_init(self, *args, **kwargs)
            Skill.__init__(self, api_name=api_name, label_type=label_type, is_generator=is_generator, output_attr=output_attr, output_attr1=output_attr1)
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
    data: dict = field(default_factory=lambda: dict())

    @classmethod
    def from_json(cls, object): return cls(
        type=object.get('type', ''),
        name=object.get('name', ''),
        span=object.get('span', [0, 0]),
        value=object.get('value', ''),
        data=object.get('data', {})
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
        #####TEMP#HACK########
        if name == 'business_entities' and hasattr(self, 'labs'):
            return self.__getattr__('labs').business_entities
        ######################
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
        input_type: type=str
    ) -> 'Output':
        def get_text(index, input_type):
            # get the input text for this Output object. use index=-1 to get the original input text
            # text can be returned as a simple str or parsed to match a given input type
            text = raw_output['output'][index]['text'] if index >= 0 else raw_output['input_text']
            return input_type.parse(text) if issubclass(input_type, Input) else text

        def split_pipeline(skills, i):
            # split pipeline at a generator Skill
            first, second = skills[:i + 1], skills[i + 1:]
            if hasattr(skills[i], 'output_attr1') and skills[i].output_attr1: 
                # handle skills that create both text and labels
                clone = copy(skills[i])
                clone.is_generator = False
                clone.output_attr = skills[i].output_attr1
                second.insert(0, clone)
            return first, second

        def _build_internal(
            output_index: int, 
            skills: List[Skill],
            input_type: type
        ) -> 'Output':
            text = get_text(output_index, input_type)
            labels = [Label.from_json(label) for label in raw_output['output'][output_index]['labels']]
            data = []
            for i, skill in enumerate(skills):
                if skill.is_generator:
                    skills, next_skills = split_pipeline(skills, i)
                    data.append(_build_internal(output_index + 1, next_skills, str))
                    break
                else:
                    data.append(list(filter(lambda label: label.type == skill.label_type, labels)))
            return cls(text=text, skills=skills, data=data)

        
        generator = raw_output['output'][0].get('text_generated_by_step_id', 0) - 1
        if generator < 0:
            return _build_internal(0, pipeline.steps, input_type)
        else:
            # edge case- first Skill is a generator, or a generator preceded by Skills that didn't generate output
            # in this case the API will skip these Skills,
            # so we need to create filler objects to match the expected structure
            skills, next_skills = split_pipeline(pipeline.steps, generator)
            return cls(
                text=get_text(-1, input_type),
                skills=skills,
                data=[[]] * generator + [_build_internal(0, next_skills, str)]
            )

    def __repr__(self) -> str:
        result = f'oneai.Output(text={repr(self.text)}'
        for i, skill in enumerate(self.skills):
            result += f', {skill.output_attr or skill.api_name}={repr(self.data[i])}'
        return result + ')'
