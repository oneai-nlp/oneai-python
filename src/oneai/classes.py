from base64 import b64encode
from dataclasses import dataclass, field
import json
import os
from typing import Any, Callable, Iterable, List, Type, Union

import aiohttp

from oneai.exceptions import InputError


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
    `run_custom: (Input, aiohttp.ClientSession) -> str | list[Label] | Output`
        A custom function that will be called locally instead of passing the Skill to the API.
        Can return a string with generated text (when `is_generator=True`), a list of `Label`s (when `is_generator=False`) or an `Output` object for more complex outputs.
        Can use the `aiohttp.ClientSession` to make HTTP requests.
    """

    api_name: str = ""
    is_generator: bool = False
    _skill_params: List[str] = field(default_factory=list, repr=False, init=False)
    # todo: replace all these w/ an output type object + parse conversations from t. enhancer etc.
    label_type: str = ""
    output_attr: str = ""
    output_attr1: str = field(default="", repr=False)
    run_custom: Callable[
        ["Input", aiohttp.ClientSession], Union[str, "Labels", "Output"]
    ] = None

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
    run_custom: Callable[
        ["Input", aiohttp.ClientSession], Union[str, "Labels", "Output"]
    ] = None,
):
    """
    A decorator for defining a Language Skill class. Decorate subclasses of `Skill` with this decorator to provide default values for instance attributes.
    """

    def wrap(cls) -> cls:
        if not issubclass(cls, Skill):
            print(
                f"warning: class {cls.__name__} decorated with @skillclass does not inherit Skill"
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
                run_custom=run_custom,
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


class Input:
    """
    A base class for all input texts, allowing structured representations of inputs.

    ## Attributes

    `type: str`
        A type hint for the API, suggesting which models to use when processing the input.
    `content_type: str`
        The content type of the input.
    `encoding: str`
        The encoding of the input.

    ## Methods

    `get_text() -> str`
        Returns the input as a string. Not implemented by default.
    `parse(text) -> Input`
        A class method. Parse a string into an instance of the Input class. Not implemented by default.
    """

    def __init__(self, type: str, content_type: str = None, encoding: str = None):
        self.type = type
        self.content_type = content_type
        self.encoding = encoding

    @classmethod
    def parse(cls, text: str) -> "Input":
        """
        A class method. Parse a string into an instance of the Input class. Not implemented by default.

        ## Parameters

        `text: str`
            The text to parse.

        ## Returns

        The `Input` instance produced from `text`.
        """
        raise NotImplementedError()

    def get_text(self) -> str:
        """
        Returns the input as a string (used by `repr`). Not implemented by default.

        ## Returns

        `str` representation of this `Input` instance.
        """
        raise NotImplementedError()

    def __repr__(self) -> str:
        return self.get_text()


class Document(Input):
    """
    Represents any text that doesn't have a structured format

    ## Attributes

    `text: str`
        The text of the document.

    ## Methods

    `get_text() -> str`
        Returns the text of the document.
    `parse(text) -> Document`
        A class method. Parse a string into a `Document` instance.
    """

    type = "article"

    def __init__(self, text: str):
        self.text = text

    @classmethod
    def parse(cls, text: str) -> "Document":
        """
        A class method. Parse a string into a `Document` instance.

        ## Parameters

        `text: str`
            The text to parse.

        ## Returns

        The `Document` instance produced from `text`.
        """
        return cls(text)

    def get_text(self) -> str:
        """
        Returns the document as a string.

        ## Returns

        `str` representation of this `Documentation` instance.
        """
        return self.text


@dataclass
class Utterance:
    speaker: str
    utterance: str

    def __repr__(self) -> str:
        return f"\n\t{self.speaker}: {self.utterance}"


class Conversation(Input):
    """
    Represents conversations.

    ## Attributes

    `utterances: List[Utterance]`
        A list of `Utterance` objects, each has `speaker` and `utterance` fields.

    ## Methods

    `get_text() -> str`
        Returns the conversation as a JSON string.
    `parse(text) -> Conversation`
        A class method. Parse a string with a structued conversation format or a conversation JSON string into a `Conversation` instance.
    """

    type = "conversation"

    def __init__(self, utterances: List[Utterance] = []):
        self.utterances = utterances

    def get_text(self) -> str:
        """
        Returns the conversation as a JSON string.

        ## Returns

        `str` representation of this `Conversation` instance.
        """
        return json.dumps(self.utterances, default=lambda o: o.__dict__)

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

            return parse_conversation(text)

    def __str__(self) -> str:
        return f"oneai.Conversation{repr(self.utterances)}"


class File(Input):
    """
    Represents file inputs. Supported file extensions:
    * .txt (text files)
    * .wav (transcribe)
    * .srt (captions)
    * .jpg (OCR)
    * .json (One AI conversation JSON format)

    ## Attributes

    `data: str`
        Encoded file data.
    `type: str`
        An input-type hint for the API, either `Conversation` or `Document`.
    `content_type: str`
        The content type of the file.
    `encoding: str`
        The encoding of the file.

    ## Methods

    `get_text() -> str`
        Returns the encoded file data.
    """

    def __init__(self, file_path: str, type: Union[str, Type[Input]] = None):
        """
        Creates a new `File` input instance

        ## Parameters

        `file_path: str`
            The path of the file to encode. Supported file extensions: [.txt, .wav, .srt, .jpg/.jpeg, .json]
        `type: str` (optional)
            The input-type hint for the API, either `Conversation` or `Document`.
        """
        if type is None or isinstance(type, str):
            super().__init__(type)
        elif issubclass(type, Input):
            super().__init__(type.type)
        else:
            raise ValueError(f"Invalid input type {type}")

        utf8, b64 = "utf8", "b64"
        _, ext = os.path.splitext(file_path)
        if ext == ".json":
            self.content_type = "application/json"
            self.encoding = utf8
        elif ext == ".txt":
            self.content_type = "text/plain"
            self.encoding = utf8
        elif ext == ".srt":
            self.data = Conversation.parse(open(file_path).read()).get_text()
            return
        elif ext in [".jpg", ".jpeg"]:
            self.content_type = "image/jpeg"
            self.encoding = b64
        elif ext == ".wav":
            self.content_type = "audio/wav"
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
            self.data = open(file_path).read()
        else:
            self.data = b64encode(file_path).decode("utf-8")

    def get_text(self) -> str:
        """
        Returns the encoded file data.

        ## Returns

        `str` representation of this `File` instance.
        """

        return self.data

    @classmethod
    def parse(cls, text: str) -> Input:
        """
        A class method. Parse a string into an `Input` instance.

        ## Parameters

        `text: str`
            The text to parse.

        ## Returns

        The `Input` instance produced from `text`.
        """
        try:
            return Conversation.parse(text)
        except:
            return text


@dataclass
class Span:
    start: int
    end: int
    section: int = 0
    text: str = None

    @classmethod
    def from_json(cls, objects: List[dict], text: str) -> "List[Span]":
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
    `value: str`
        The value of the label.
    `data: Dict[str, Any]`
        Additional data associated with the label.
    """

    type: str = ""
    skill: str = ""
    name: str = ""
    span: List[int] = field(default_factory=lambda: [0, 0], repr=False)
    output_spans: List[int] = field(default_factory=list)
    input_spans: List[int] = field(default_factory=list)
    span_text: str = ""
    value: str = ""
    data: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, object: dict) -> "Label":
        return cls(
            type=object.pop("type", ""),
            skill=object.pop("skill", ""),
            name=object.pop("name", ""),
            output_spans=Span.from_json(
                object.pop("output_spans", []), object.get("span_text", None)
            ),
            input_spans=Span.from_json(
                object.pop("input_spans", []), object.get("span_text", None)
            ),
            span=object.pop("span", [0, 0]),
            span_text=object.pop("span_text", ""),
            value=object.pop("value", ""),
            data=object.pop("data", {}),
        )

    def __repr__(self) -> str:
        return (
            "oneai.Label("
            + ", ".join(f"{k}={repr(v)}" for k, v in self.__dict__.items() if v)
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


@dataclass
class Output(Input):
    """
    Represents the output of a pipeline. The structure of the output is dynamic, and corresponds to the Skills used and their order in the pipeline.
    Skill outputs can be accessed as attributes, either with the `api_name` of the corresponding Skill or the `output_attr` field.

    ## Attributes

    `text: str`
        The input text from which this `Output` instance was produced.
    `skills: List[Skill]`
        The Skills used to process `text` and produce this `Output` instance.
    `data: List[List[Label] | Output]`
        Output data produced by `skills`, in the same order. Each element can be:
        * A list of labels, marking data points in `text`, e.g entities.
        * A nested `Output` instance, with a new `text`, e.g summary.
    """

    text: Union[Input, str] = ""
    skills: List[Skill] = field(
        default_factory=list, repr=False
    )  # not a dict since Skills are currently mutable & thus unhashable
    data: List[Union[Labels, "Output"]] = field(default_factory=list, repr=False)

    def __getitem__(self, name: str) -> Union[Labels, "Output"]:
        return self.__getattr__(name)

    def __getattr__(self, name: str) -> Union[Labels, "Output"]:
        #####TEMP#HACK########
        if name in ["business_entities", "pricing"] and hasattr(self, "labs"):
            return getattr(self.__getattr__("labs"), name)
        ######################
        for i, skill in enumerate(self.skills):
            if (
                (skill.api_name and skill.api_name == name)
                or (skill.output_attr and name in skill.output_attr)
                or (type(skill).__name__ == name)
            ):
                return self.data[i]
        raise AttributeError(f"{name} not found in {self}")

    def __dir__(self) -> Iterable[str]:
        return super().__dir__() + [
            skill.output_attr or skill.api_name for skill in self.skills
        ]

    def get_text(self) -> str:
        return self.text if isinstance(self.text, str) else repr(self.text)

    def add(self, skill: Skill, data: Union["Output", Labels]):
        """
        Add data generated by a `Skill` to the output. Data can be a nested `Output` instance or a list of `Label`s.

        ## Parameters

        `skill: Skill`
            The Skill which generated the data.
        `data: Output | list[Label]`
            The data to add to the output.
        """
        self.skills.append(skill)
        self.data.append(data)

    def merge(self, output: "Output") -> "Output":
        """
        Merge data from the given `Output` instance into this one, ignoring input text.

        ## Parameters

        `output: Output`
            The `Output` instance to merge into this one.
        """
        self.skills += output.skills
        self.data += output.data

    def __repr__(self) -> str:
        result = f"oneai.Output(text={repr(self.text)}"
        for i, skill in enumerate(self.skills):
            result += f", {skill.output_attr or skill.api_name}={repr(self.data[i])}"
        return result + ")"
