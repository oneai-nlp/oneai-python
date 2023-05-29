from typing import List
import oneai
import pytest

from tests.constants import DOCUMENT, CONVERSATION, URL_INPUT
from tests.util import hasattrnested


@pytest.mark.parametrize(
    "pipeline, input, attrs, notes",
    [
        (
            oneai.Pipeline([oneai.skills.Keywords()]),
            DOCUMENT,
            ["keywords"],
            "simple document",
        ),
        (
            oneai.Pipeline([oneai.skills.Keywords()]),
            CONVERSATION,
            ["keywords"],
            "simple conversation",
        ),
        (
            oneai.Pipeline([oneai.skills.Summarize(), oneai.skills.Keywords()]),
            DOCUMENT,
            ["summary", "summary.keywords"],
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
            ["emotions", "summary", "summary.keywords"],
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
            ["summary", "summary.proofread", "summary.proofread.anonymized"],
            "multiple generators",
        ),
        (
            oneai.Pipeline(
                [
                    oneai.Skill("summarize", text_attr="custom_summary"),
                ]
            ),
            DOCUMENT,
            ["custom_summary"],
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
            [
                "summary",
                "summary.names",
                "summary.custom_keywords",
                "summary.keywords",
                "summary.summary",
            ],
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
            ["html_article", "html_article.html_labels", "html_article.emotions"],
            "URL input",
        ),
    ],
)
def test_pipeline(
    pipeline: oneai.Pipeline, input: oneai.TextContent, attrs: List[str], notes: str
):
    try:
        output = pipeline.run(input)
        for attr in attrs:
            assert hasattrnested(output, attr)
        assert hasattr(output, "task_id")
        assert output.task_id is not None and output.task_id != ""
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


def test_generate_chapters():
    assert oneai.util.generate_chapters(DOCUMENT, amount="more")


@pytest.mark.asyncio
async def test_async():
    try:
        output = await oneai.Pipeline(
            [oneai.skills.Names(), oneai.skills.Summarize(), oneai.skills.Keywords()]
        ).run_async(DOCUMENT)
        assert hasattr(output, "task_id")
        assert output.task_id is not None and output.task_id != ""
        assert hasattr(output, "text")
        assert hasattr(output, "names")
        assert hasattr(output, "summary")
        assert hasattrnested(output, "summary.keywords")
    except Exception as e:
        pytest.fail(f"Async pipeline failed: {e}")


@pytest.mark.asyncio
async def test_polling_output():
    try:
        task = await oneai.Pipeline(
            [oneai.skills.Names(), oneai.skills.Summarize(), oneai.skills.Keywords()]
        ).run_async(DOCUMENT, polling=False)
        assert hasattr(task, "task_id")
        assert await task.get_status() in ["COMPLETED", "RUNNING"]
        output = await task.await_completion()
        assert output.task_id == task.task_id
        assert hasattr(output, "text")
        assert hasattr(output, "names")
        assert hasattr(output, "summary")
        assert hasattrnested(output, "summary.keywords")
    except Exception as e:
        pytest.fail(f"Async pipeline failed: {e}")


@pytest.mark.asyncio
async def test_polling_pipeline():
    try:
        pipeline = oneai.Pipeline(
            [oneai.skills.Names(), oneai.skills.Summarize(), oneai.skills.Keywords()]
        )
        task = await pipeline.run_async(DOCUMENT, polling=False)
        assert hasattr(task, "task_id")
        output = await pipeline.await_completion(task)
        assert output.task_id == task.task_id
        assert hasattr(output, "text")
        assert hasattr(output, "names")
        assert hasattr(output, "summary")
        assert hasattrnested(output, "summary.keywords")
    except Exception as e:
        pytest.fail(f"Async pipeline failed: {e}")
