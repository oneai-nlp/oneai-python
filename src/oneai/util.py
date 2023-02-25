import asyncio
import oneai
from typing import List, Optional, Union
from typing_extensions import Literal, dataclass_transform
from dataclasses import dataclass


@dataclass_transform()
def skillclass(
    api_name: str = "",
    text_attr: Optional[str] = None,
    labels_attr: Optional[str] = None,
):
    """
    A decorator for defining a Language Skill class. Decorate subclasses of `Skill` with this to provide default values for instance attributes.

    ## Example

    >>> @skillclass(api_name="my-skill", text_attr="my_result")
    ... class MySkill(Skill):
    ...     ratio: float = 0.2
    >>> s = Summarize(ratio=0.5)
    >>> s.ratio
    0.5
    >>> pipeline = Pipeline([s])
    >>> output = pipeline.run("Text to be processed with MySkill")
    >>> output.my_result
    "Result text, processed with MySkill"
    """

    def wrap(cls):
        if not issubclass(cls, Skill):
            warn(
                f"warning: class {cls.__name__} decorated with @skillclass does not inherit Skill",
                stacklevel=2,
            )

        # remove class variables
        classVars = {
            k: getattr(cls, k, None)
            for k in cls.__annotations__
            if k not in Skill.__annotations__
        }
        for k in classVars:
            if hasattr(cls, k):
                delattr(cls, k)

        def __init__(self, **params):
            Skill.__init__(
                self,
                api_name=api_name,
                text_attr=text_attr,
                labels_attr=labels_attr,
                params=params,
            )

            for k, v in classVars.items():
                if k not in params:
                    setattr(self, k, v)

        def __getattr__(self, name):
            return self.params[name]

        def __setattr__(self, name, value):
            if "params" not in self.__dict__:
                return object.__setattr__(self, name, value)
            self.params[name] = value

        cls.__init__ = __init__
        cls.__getattr__ = __getattr__
        cls.__setattr__ = __setattr__
        return cls

    return wrap


@dataclass
class Chapter:
    subheading: str
    text: Union[str, List[oneai.Utterance]]
    summary: str


def span_text(
    input: Union[str, List[oneai.Utterance]], label: oneai.Label
) -> Union[str, List[oneai.Utterance]]:
    if isinstance(input, str):
        return label.span_text
    return [
        oneai.Utterance(
            speaker=input[span.section].speaker,
            utterance=input[span.section].utterance[span.start : span.end],
            timestamp=input[span.section].timestamp,
        )
        for span in label.output_spans
    ]


def generate_chapters(
    input: oneai.PipelineInput,
    amount: Literal["more", "less", "normal"] = None,
    preprocessing: Optional[oneai.Skill] = None,
) -> List[Chapter]:
    output = asyncio.run(
        oneai.Pipeline([oneai.skills.SplitByTopic(amount=amount)]).run_async(input)
        if not preprocessing
        else oneai.Pipeline(
            [preprocessing, oneai.skills.SplitByTopic(amount=amount)]
        ).run_async(input)
    )
    if preprocessing:
        output = output.__getattribute__(preprocessing.output_attr)
    spans = [span_text(output.text, seg) for seg in output.segments]
    summaries = oneai.Pipeline([oneai.skills.Summarize()]).run_batch(spans)
    return [
        Chapter(
            subheading=seg.data["subheading"],
            text=span,
            summary=summaries[span].summary.text,
        )
        for seg, span in zip(output.segments, spans)
    ]
