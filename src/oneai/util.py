import asyncio
import oneai
from typing import List, Optional, Union
from typing_extensions import Literal
from dataclasses import dataclass


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
