from datetime import datetime, timedelta
from dateutil import parser as dateutil
import io
import json
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
    ".html": ("text/plain", "article"),
}


@dataclass
class Skill:
    """
    A base class for all Language Skills. Use predefined subclasses of this class, or use this class to define your own Skills.

    A Language Skill is a package of trained NLP models. Skills accept text and respond with processed texts and extracted metadata.

    Process texts with Skills using `Pipeline`s

    ### Skill types
    * Generator Skills (`is_generator=True`) process the input and produce a new text based on it. Examples include `Summarize`, `TranscriptionEnhancer`.
    * Analyzer Skills (`is_generator=False`) scan the input and extract structured data. Examples include `Emotions`, `Topics`.

    ## Attributes

    `api_name: str`
        The name of the Skill in the pipeline API.
    `is_generator: bool`
        Whether the Skill is a generator Skill.
    `skill_params: List[str]`
        Names of the fields of the Skill object that should be passed as parameters to the API.
    `label_type: str`
        If the Skill generates labels, the type name of the label.
    `output_attr: str`
        The attribute name of the Skill's output in the Output object.
    `output_attr1: str`
        Only for Skills with 2 outputs (text / labels)
    """

    api_name: str = ""
    is_generator: bool = False
    _skill_params: List[str] = field(default_factory=list, repr=False, init=False)
    # todo: replace all these w/ an output type object + parse conversations from t. enhancer etc.
    label_type: str = ""
    output_attr: str = ""
    output_attr1: str = field(default="", repr=False)

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
    label_type: str = "",
    is_generator: bool = False,
    output_attr: str = "",
    output_attr1: str = "",
):
    """
    A decorator for defining a Language Skill class. Decorate subclasses of `Skill` with this decorator to provide default values for instance attributes.
    """

    def wrap(cls) -> cls:
        if not issubclass(cls, Skill):
            warn(
                f"warning: class {cls.__name__} decorated with @skillclass does not inherit Skill",
                stacklevel=2,
            )

        def __init__(self, *args, **kwargs):
            cls_init(self, *args, **kwargs)
            Skill.__init__(
                self,
                api_name=api_name,
                label_type=label_type,
                is_generator=is_generator,
                output_attr=output_attr,
                output_attr1=output_attr1,
            )
            self._skill_params = [
                a
                for a in self.__dict__
                if not (a in Skill.__dict__ or a == "_skill_params")
            ]

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


class Document(Input[str]):
    """
    Represents any text that doesn't have a structured format

    ## Attributes

    `text: str`
        The text of the document.
    """

    def __init__(self, text: str):
        super().__init__(text, type="article", content_type="text/plain")


class Conversation(Input[List[Utterance]]):
    """
    Represents conversations.

    ## Attributes

    `text: List[Utterance]`
        A list of `Utterance` objects, each has `speaker` and `utterance` fields.

    ## Methods

    `parse(text) -> Conversation`
        A class method. Parse a string with a structued conversation format or a conversation JSON string into a `Conversation` instance.
    """

    def __init__(self, utterances: List[Utterance] = []):
        super().__init__(
            utterances, type="conversation", content_type="application/json"
        )

    @property
    def utterances(self):
        return self.text

    @utterances.setter
    def utterances(self, value: List[Utterance]):
        self.text = value

    def __getitem__(self, index: int) -> Utterance:
        return self.utterances[index]

    @classmethod
    def parse(cls, text: str) -> "Conversation":
        """
        A class method. Parse a string with a structured conversation format or a conversation JSON string into a `Conversation` instance.

        ## Parameters

        `text: str`
            The text to parse.

        ## Returns

        The `Conversation` instance produced from `text`.

        ## Raises

        `ValueError` if `text` is not in a valid conversation format.
        """
        try:  # try to parse as JSON
            js = json.loads(text)
            return cls([Utterance(**utterance) for utterance in js])
        except json.JSONDecodeError:  # if not JSON, assume it's a structured conversation
            from oneai.parsing import parse_conversation

            return cls(parse_conversation(text))

    def __repr__(self) -> str:
        return f"oneai.Conversation{repr(self.utterances)}"


class File(Input):
    """
    Deprecated. Pass file-like objects directly to `Pipeline.run`

    Represents file inputs. Supported file extensions:
    * .txt (text files)
    * .wav, .mp3 (transcribe)
    * .srt (captions)
    * .jpg (OCR)
    * .json (One AI conversation JSON format)

    ## Attributes

    `text: str`
        Encoded file data.
    `type: str`
        An input-type hint for the API, either `Conversation` or `Document`.
    `content_type: str`
        The content type of the file.
    `encoding: str`
        The encoding of the file.
    """

    def __init__(self, file_path: str, type: Union[str, Type[Input]] = None):
        """
        Creates a new `File` input instance

        ## Parameters

        `file_path: str`
            The path of the file to encode. Supported file extensions: [.txt, .wav, .mp3, .srt, .jpg/.jpeg, .json]
        `type: str` (optional)
            The input-type hint for the API, either `Conversation` or `Document`.
        """
        warn(
            "File class is deprecated- pass file-like objects directly to pipelines instead",
            DeprecationWarning,
            stacklevel=2,
        )
        if type is None or isinstance(type, str):
            super().__init__(type)
        elif issubclass(type, Input):
            super().__init__(type.type)
        else:
            raise ValueError(f"Invalid input type {type}")

        utf8, b64 = "utf8", "base64"
        _, ext = os.path.splitext(file_path)
        if ext == ".json":
            self.content_type = "application/json"
            self.encoding = utf8
        elif ext == ".txt":
            self.content_type = "text/plain"
            self.encoding = utf8
        elif ext == ".srt":
            self.text = Conversation.parse(open(file_path).read()).text
            return
        elif ext in [".jpg", ".jpeg"]:
            self.content_type = "image/jpeg"
            self.encoding = b64
        elif ext == ".wav":
            self.content_type = "audio/wav"
            self.encoding = b64
        elif ext == ".mp3":
            self.content_type = "audio/mp3"
            self.encoding = b64
        elif ext == ".html":
            self.content_type = "text/html"
            self.encoding = utf8
        else:
            raise InputError(
                message=f"unsupported file extension {ext}",
                details="see supported files in docs",
            )

        if self.encoding == utf8:
            self.text = open(file_path, "r").read()
        else:
            self.text = b64encode(open(file_path, "rb").read()).decode("utf-8")


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
    output_spans: List[int] = field(default_factory=list)
    input_spans: List[int] = field(default_factory=list)
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
            setattr(self, skill.output_attr or skill.api_name, value)

    def __dir__(self) -> Iterable[str]:
        return super().__dir__() + [
            skill.output_attr or skill.api_name for skill in self.skills
        ]

    def __repr__(self) -> str:
        result = f"oneai.Output(text={repr(self.text)}"
        for skill in self.skills:
            attr = skill.output_attr or skill.api_name
            result += f", {attr}={repr(getattr(self, attr))}"
        return result + ")"
