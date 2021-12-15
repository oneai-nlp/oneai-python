from dataclasses import dataclass, field
from typing import List, Type


@dataclass
class Skill:
    name: str = ''
    iswriting: bool = False
    param_fields: List[str] = field(default_factory=list, repr=False)

def skillclass(cls: Type[Skill]=None, name: str='', iswriting: bool=False, param_fields: List[str]=[]):
    def wrap(cls):
        if not Skill.__subclasscheck__(cls):
            print('warning: @skillclass annotated class ' + cls.__name__ + ' doesn\'t override Skill')

        cls_init = cls.__init__
        def skill_init(self, *args, **kwargs) -> None:
            cls_init(self, *args, **kwargs)
            Skill.__init__(self, name=name, iswriting=iswriting, param_fields=param_fields)
        cls.__init__ = skill_init
        return cls
    
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
