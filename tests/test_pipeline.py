import oneai
import pytest

from tests.constants import DOCUMENT, CONVERSATION, URL_INPUT


@pytest.mark.parametrize(
    "pipeline, input, notes",
    [
        (
            oneai.Pipeline([oneai.skills.Keywords()]),
            DOCUMENT,
            "simple document",
        ),
        (
            oneai.Pipeline([oneai.skills.Keywords()]),
            CONVERSATION,
            "simple conversation",
        ),
        (
            oneai.Pipeline([oneai.skills.Summarize(), oneai.skills.Keywords()]),
            DOCUMENT,
            "first Skill generator",
        ),
        (
            oneai.Pipeline(
                [
                    oneai.skills.Emotions(),
                    oneai.skills.Summarize(),
                    oneai.skills.Keywords(),
                ]
            ),
            DOCUMENT,
            "empty labels, then generator",
        ),
        (
            oneai.Pipeline(
                [
                    oneai.skills.Summarize(),
                    oneai.skills.Proofread(),
                    oneai.skills.Anonymize(),
                ]
            ),
            DOCUMENT,
            "multiple generators",
        ),
        (
            oneai.Pipeline(
                [
                    oneai.Skill("summarize", text_attr="custom_summary"),
                ]
            ),
            DOCUMENT,
            "custom Skill only",
        ),
        (
            oneai.Pipeline(
                [
                    oneai.skills.Summarize(),
                    oneai.skills.Names(),
                    oneai.Skill("keywords", labels_attr="custom_keywords"),
                    oneai.skills.Keywords(),
                    oneai.skills.Summarize(),
                ]
            ),
            DOCUMENT,
            "custom Skill, surrounded by core Skills",
        ),
        (
            oneai.Pipeline(
                [
                    oneai.skills.HtmlToArticle(),
                    oneai.skills.Emotions(),
                ]
            ),
            URL_INPUT,
            "URL input",
        ),
    ],
)
def test_pipeline(pipeline: oneai.Pipeline, input: oneai.TextContent, notes: str):
    try:
        pipeline.run(input)
    except Exception as e:
        pytest.fail(f"Pipeline failed on {notes}: {e}")


def test_batch():
    inputs = [
        DOCUMENT,
        CONVERSATION,
        DOCUMENT,
        CONVERSATION,
        URL_INPUT,
    ]
    outputs = oneai.Pipeline(
        [oneai.skills.Names(), oneai.skills.Summarize(), oneai.skills.Keywords()]
    ).run_batch(inputs)

    for input in inputs:
        assert input in outputs
        assert isinstance(
            outputs[input], Exception if input == URL_INPUT else oneai.Output
        )
