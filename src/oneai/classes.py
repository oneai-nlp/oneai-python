from datetime import datetime, timedelta
from dateutil import parser as dateutil
import io
import os
from base64 import b64encode
import validators
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    TextIO,
    Tuple,
    Type,
    TypeVar,
    Union,
    Hashable,
)
from warnings import warn


from oneai.exceptions import InputError

if TYPE_CHECKING:
    from oneai.skills import OutputAttrs


@dataclass
class Utterance:
    speaker: str
    utterance: str
    timestamp: Optional[timedelta] = None

    @classmethod
    def from_dict(cls, u: Dict[str, str]) -> "Utterance":
        return cls(
            u["speaker"],
            u["utterance"],
            timestamp_to_timedelta(u.get("timestamp", None)),
        )

    def __repr__(self) -> str:
        return (
            f"\n\t{self.timestamp} {self.speaker}: {self.utterance}"
            if self.timestamp
            else f"\n\t{self.speaker}: {self.utterance}"
        )


TextContent = TypeVar("TextContent", bound=Union[str, List["Utterance"]])
PipelineInput = Union["Input[TextContent]", TextContent, TextIO, BinaryIO]

# extension -> content_type, input_type
CONTENT_TYPES: Dict[str, Tuple[str, str]] = {
    ".json": ("application/json", "conversation"),
    ".txt": ("text/plain", "article"),
    ".srt": ("text/plain", "conversation"),
    ".wav": ("audio/wav", "conversation"),
    ".mp3": ("audio/mpeg", "conversation"),
    ".mp4": ("audio/mpeg", "conversation"),
    ".html": ("text/plain", "article"),
    ".pdf": ("text/pdf", "article"),
}


@dataclass
class Skill:
    """
    A base class for all Language Skills. Use predefined subclasses of this class, or use this class to define your own Skills.

    A Language Skill is a package of trained NLP models. Skills accept text and respond with processed texts and extracted metadata.

    Process texts with Skills using `Pipeline`s

    ### Skill types
    * Generator Skills (`text_attr is not None`) process the input and produce a new text based on it. Examples include `Summarize`, `Proofread`.
    * Analyzer Skills (`text_attr is None`) scan the input and extract structured data. Examples include `Emotions`, `Topics`.

    ## Attributes

    `api_name: str`
        The name of the Skill in the pipeline API.
    `skill_params: List[str]`
        Names of the fields of the Skill object that should be passed as parameters to the API.
    `text_attr: str`
        The attribute name of the Skill's output text in the Output object (Generator Skills only).
    `labels_attr: str`
        The attribute name of the Skill's output labels in the Output object.
    """

    api_name: str = ""
    _skill_params: List[str] = field(default_factory=list, repr=False, init=False)
    text_attr: str = ""
    labels_attr: str = ""

    ### redundant, do not set, for backwards compatibility only ###
    is_generator: bool = field(default=False, repr=False)
    label_type: str = field(default="", repr=False)
    output_attr: str = field(default="", repr=False)
    output_attr1: str = field(default="", repr=False)
    ###############################################################

    def __post_init__(self):
        # backwards compatibility
        if self.labels_attr is None and self.text_attr is None:
            if self.output_attr1:
                self.text_attr = self.output_attr
                self.labels_attr = self.output_attr1
            elif self.is_generator:
                self.text_attr = self.output_attr or self.api_name
            else:
                # only this case is needed when backwards compatibility is removed
                self.labels_attr = self.output_attr or self.api_name

    def asdict(self) -> dict:
        return {
            "skill": self.api_name,
            "params": {
                p: self.__getattribute__(p)
                for p in self._skill_params
                if self.__getattribute__(p)
            },
        }


def skillclass(
    cls: Type = None,
    api_name: str = "",
    text_attr: str = "",
    labels_attr: str = "",
    ### redundant, do not set, for backwards compatibility only ###
    label_type: str = "",
    is_generator: bool = False,
    output_attr: str = "",
    output_attr1: str = "",
    ###############################################################
):
    """
    A decorator for defining a Language Skill class. Decorate subclasses of `Skill` with this to provide default values for instance attributes.
    """

    def wrap(cls) -> cls:
        if not issubclass(cls, Skill):
            warn(
                f"warning: class {cls.__name__} decorated with @skillclass does not inherit Skill",
                stacklevel=2,
            )

        def __init__(self, *args, **kwargs):
            cls_init(self, *args)
            Skill.__init__(
                self,
                api_name=api_name,
                text_attr=text_attr,
                labels_attr=labels_attr,
            )
            self._skill_params = [
                a
                for a in {**self.__dict__, **kwargs}
                if a not in Skill.__dataclass_fields__
            ]
            for param in self._skill_params:
                if param in kwargs:
                    self.__setattr__(param, kwargs[param])

        cls_init = cls.__init__
        cls.__init__ = __init__
        return cls

    return wrap if cls is None else wrap(cls)


class Input(Generic[TextContent]):
    """
    A base class for all input texts, allowing structured representations of inputs.

    ## Attributes

    `text: TextContent`
        Input text. Either `str` or `list[Utterance]` (conversation).
    `type: str`
        A type hint for the API, suggesting which models to use when processing the input.
    `content_type: str`
        The content type of the input.
    `encoding: str`
        The encoding of the input.
    `metadata: dict`
        Optional metadata to be associated with the input in clustering collections.
    `datetime: datetime`
        Optional datetime to be associated with the input in clustering collections.
    """

    def __init__(
        self,
        text: TextContent,
        *,
        type: str = None,
        content_type: str = None,
        encoding: str = None,
        metadata: Dict[str, any] = None,
        datetime: datetime = None,
    ):
        self.text: TextContent = text
        self.type = type
        self.content_type = content_type
        self.encoding = encoding
        self.metadata = metadata
        self.datetime = datetime

    @classmethod
    def wrap(
        cls, text: PipelineInput[TextContent], sync: bool = True
    ) -> "Input[TextContent]":
        if isinstance(text, cls):
            return text
        elif isinstance(text, str):
            if validators.url(text):
                return cls(text, type="article", content_type="text/uri-list")
            else:
                return cls(text, type="article", content_type="text/plain")
        elif isinstance(text, list) and (
            len(text) == 0 or isinstance(text[0], Utterance)
        ):
            return cls(text, type="conversation", content_type="application/json")
        elif isinstance(text, io.IOBase):
            name, mode = text.name, text.mode
            _, ext = os.path.splitext(name)
            if ext not in CONTENT_TYPES:
                raise InputError(
                    message=f"unsupported file extension {ext}",
                    details="see supported files in docs",
                )
            content_type, input_type = CONTENT_TYPES[ext]
            if "b" not in mode:
                return cls(text.read(), type=input_type, content_type=content_type)
            elif sync:
                data = b64encode(text.read()).decode("ascii")
                return cls(
                    data, type=input_type, content_type=content_type, encoding="base64"
                )
            else:
                return cls(text, type=input_type, content_type=content_type)
        else:
            raise ValueError(f"invalid content type {type(text)}")


def timestamp_to_timedelta(timestamp: str) -> timedelta:
    if not timestamp:
        return None
    dt = dateutil.parse(timestamp)
    return timedelta(
        hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond
    )


@dataclass
class Span:
    start: int
    end: int
    section: int = 0
    text: str = None

    @classmethod
    def from_dict(cls, objects: List[dict], text: str) -> "List[Span]":
        return (
            []
            if not objects
            else [
                cls(
                    start=object.get("start", None),
                    end=object.get("end", None),
                    section=object.get("section", None),
                    text=text,
                )
                for object in objects
            ]
        )


@dataclass
class Label:
    """
    Represents a label, marking a part of the input text. Attribute values largely depend on the Skill the labels were produced by.

    ## Attributes

    `type: str`
        Label type, e.g. 'entity', 'topic', 'emotion'.
    `skill: str`
        The name of the Skill that produced the label.
    `name: str`
        Label class name, e.g. 'PERSON', 'happiness', 'POS'.
    `output_spans: list[Span]`
        The spans in the output text that are marked with the label.
    `input_spans: list[Span]`
        The spans in the input text that are relevant to the label. Only appears if the label was produced by a Skill that supports input spans.
    `span_text: str`
        The text of the label.
    `timestamp: str`
        For audio inputs, the timestamp of the start of the label.
    `timestamp_end: str`
        For audio inputs, the timestamp of the end of the label.
    `value: str`
        The value of the label.
    `data: Dict[str, Any]`
        Additional data associated with the label.
    """

    type: str = ""
    skill: str = ""
    name: str = ""
    _span: List[int] = field(default_factory=lambda: [0, 0], repr=False)
    output_spans: List[Span] = field(default_factory=list)
    input_spans: List[Span] = field(default_factory=list)
    span_text: str = ""
    timestamp: timedelta = None
    timestamp_end: timedelta = None
    value: str = ""
    data: dict = field(default_factory=dict)

    @property
    def span(self) -> Span:
        warn(
            "`Label.span` is deprecated, use `Label.output_spans` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._span

    @classmethod
    def from_dict(cls, object: dict) -> "Label":
        return cls(
            type=object.pop("type", ""),
            skill=object.pop("skill", ""),
            name=object.pop("name", ""),
            output_spans=Span.from_dict(
                object.pop("output_spans", []), object.get("span_text", None)
            ),
            input_spans=Span.from_dict(
                object.pop("input_spans", []), object.get("span_text", None)
            ),
            _span=object.pop("span", [0, 0]),
            span_text=object.pop("span_text", ""),
            value=object.pop("value", ""),
            data=object.pop("data", {}),
            timestamp=timestamp_to_timedelta(object.pop("timestamp", "")),
            timestamp_end=timestamp_to_timedelta(object.pop("timestamp_end", "")),
        )

    def __repr__(self) -> str:
        return (
            "oneai.Label("
            + ", ".join(
                f"{k}={repr(v)}"
                for k, v in self.__dict__.items()
                if v and not k.startswith("_")
            )
            + ")"
        )


class Labels(List[Label]):
    """
    Wrapper object for a list of `Label` objects. Provides convenience methods to query labels by attribute.

    ## Properties

    `values: list[str]`
        A list of all values of the labels.
    `names: list[str]`
        A list of all names of the labels.
    `input_spans: list[list[Span]]`
        A list of all input spans of the labels.
    `output_spans: list[list[Span]]`
        A list of all output spans of the labels.
    `span_texts: list[str]`
        A list of all span texts of the labels.
    """

    @property
    def values(self) -> List[Any]:
        return [l.value for l in self]

    @property
    def names(self) -> List[str]:
        return [l.name for l in self]

    @property
    def input_spans(self) -> List[List[Span]]:
        return [l.input_spans for l in self]

    @property
    def output_spans(self) -> List[List[Span]]:
        return [l.output_spans for l in self]

    @property
    def span_texts(self) -> List[str]:
        return [l.span_text for l in self]


class Output(Input[TextContent], OutputAttrs if TYPE_CHECKING else object):
    """
    Represents the output of a pipeline. The structure of the output is dynamic, and corresponds to the Skills used and their order in the pipeline.
    Skill outputs can be accessed as attributes, either with the `api_name` of the corresponding Skill or the `output_attr` field.

    ## Attributes

    `text: TextContent`
        The input text from which this `Output` instance was produced.
    `skills: List[Skill]`
        The Skills used to process `text` and produce this `Output` instance.
    See `OutputAttrs` for the attributes generated by different Skills.
    """

    def __init__(
        self,
        text: TextContent,
        skills: List[Skill] = [],
        data: List[Union[Labels, "Output"]] = [],
    ):
        super().__init__(
            text,
            type="article" if isinstance(text, str) else "conversation",
            content_type="text/plain" if isinstance(text, str) else "application/json",
        )

        self.skills = skills
        for skill, value in zip(skills, data):
            setattr(self, skill.text_attr or skill.labels_attr or skill.api_name, value)

    def __dir__(self) -> Iterable[str]:
        return super().__dir__() + [
            skill.text_attr or skill.labels_attr or skill.api_name
            for skill in self.skills
        ]

    def __repr__(self) -> str:
        result = f"oneai.Output(text={repr(self.text)}"
        for skill in self.skills:
            attr = skill.text_attr or skill.labels_attr or skill.api_name
            result += f", {attr}={repr(getattr(self, attr))}"
        return result + ")"


class BatchResponse:
    def __init__(self):
        self._data: Dict[Input, Output] = {}

    def __setitem__(self, key: Input, value: Output):
        self._data[key] = value

    def __getitem__(self, key: Input) -> Output:
        return (
            self._data[key]
            if isinstance(key, Hashable) and key in self._data
            else next(v for k, v in self._data.items() if k.text == key)
        )
