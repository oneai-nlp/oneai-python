from dataclasses import dataclass, field
from typing import List, Type


@dataclass
class Skill:
    name: str = ''
    iswriting: bool = False
    param_fields: List[str] = field(default_factory=list, repr=False)

def skillclass(cls: Type=None, name: str='', iswriting: bool=False, param_fields: List[str]=[]):
    def wrap(cls):
        class SkillWrapper(cls, Skill):
            def __init__(self, *args, **kwargs):
                cls.__init__(self, *args, **kwargs)
                Skill.__init__(self, name=name, iswriting=iswriting, param_fields=param_fields)

        return SkillWrapper
    
    return wrap if cls is None else wrap(cls)

@dataclass
class Label:
    type: str
    name: str
    span: List[int]
    value: float

@dataclass
class LabeledText:
    text: str
    labels: List[Label]
