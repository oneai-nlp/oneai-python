import sys
from tests import oneai
from tests.constants import CONVERSATION_PARSING_TESTS, CONVERSATION_LINE_TESTS
import pytest


def comp4Test(a, b):
    if a is None:
        return b is None
    return (
        a["speaker"] == b["speaker"]
        and a["hasText"] == b["hasText"]
        and a["separator"] == b["separator"]
        and a["preTime"] == b["preTime"]
        and a["text"] == b["text"]
        and a["weak"] == b["weak"]
        and (not (a["timestamp"] or b["timestamp"]) or a["timestamp"] == b["timestamp"])
    )


@pytest.mark.parametrize(
    "input, expected",
    [(test["input"], test["output"]) for test in CONVERSATION_LINE_TESTS],
)
def test_conversation_line(input, expected):
    parsedSpeaker = oneai.parsing._parseSpeakerLine(input)
    assert parsedSpeaker or comp4Test(parsedSpeaker, expected)


@pytest.mark.parametrize(
    "input, expected",
    [(test["text"], test["elements"]) for test in CONVERSATION_PARSING_TESTS],
)
def test_conversation_parsing(input, expected):
    try:
        parsed = oneai.parsing.parse_conversation(input)
        assert parsed is not None and parsed != []
        assert len(parsed) == expected
    except Exception as e:
        assert not expected, repr(e)
