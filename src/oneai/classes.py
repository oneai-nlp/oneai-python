from dataclasses import dataclass, field
from typing import List, Type


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
    span: List[int] = field(default_factory=lambda: [0, 0])
    value: float = .0

    @classmethod
    def from_json(cls, json): return cls(
        type=json.get('type', ''),
        name=json.get('name', ''),
        span=json.get('span', [0, 0]),
        value=json.get('value', .0)
    )


@dataclass
class LabeledText:
    text: str
    labels: List[Label]

    @classmethod
    def from_json(cls, json: dict): return cls(
        text=json['text'],
        labels=[Label.from_json(l) for l in json['labels']]
    )
