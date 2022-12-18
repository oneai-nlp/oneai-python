import re
from typing import List
import oneai
from oneai.classes import Utterance


# v 1.6.1
def parse_conversation(text: str, strict=False) -> List[Utterance]:
    """
    Parse a string with a conversation format into a structured `Utterance` list representing the conversation.

    ## Parameters

    `text: str`
        The text to parse.

    ## Returns

    A list of `Utterance` objects produced from `text`.

    ## Raises

    `ValueError` if `text` is not in a valid conversation format.
    """

    srt_regex = re.compile(
        r"\d+\n\d{1,2}:\d{2}:\d{2}[,.]\d{1,3} --> \d{1,2}:\d{2}:\d{2}[,.]\d{1,3}"
    )
    match = srt_regex.match(text)
    if match:
        data_array = srt_regex.split(text)
        return [
            Utterance(speaker="SPEAKER", utterance=line.strip().replace("\n", " "))
            for line in data_array[1:]
        ]

    result = []
    lines = re.split(r"\r?\n", text.strip())
    firstLine = True
    structure = None
    currentLineInfo = None
    waitForTextLine = False
    # weak = False
    previousObject = None

    for i, line in enumerate(lines):
        if _isEmptyOrWhitespace(line):
            continue

        if waitForTextLine:
            previousObject["text"] = line.strip()
            # previousObject["text_line"] = i
            waitForTextLine = False
            continue

        currentLineInfo = _parseSpeakerLine(line)
        if currentLineInfo is None:
            if firstLine:
                raise ValueError(f"Invalid conversation format at line {i}")
            previousObject["text"] += "\n" + line.strip()
            # weak = True
            continue

        if firstLine:
            structure = currentLineInfo

        # weak |= currentLineInfo["weak"]
        if strict and not _comp(structure, currentLineInfo):
            raise ValueError(
                f"Differing conversation format at line {i}, run with strict=False to ignore"
            )

        firstLine = False

        previousObject = {
            "speaker": currentLineInfo["speaker"],
            "text": currentLineInfo["text"],
            # "speaker_line": i,  # what are these properties for? do I want them in Utterance objects?
            # "text_line": i,
            # "speaker_length": currentLineInfo["speaker_end"],
        }
        if currentLineInfo["timestamp"]:
            previousObject["timestamp"] = currentLineInfo["timestamp"]

        result.append(previousObject)
        waitForTextLine = not currentLineInfo["hasText"]
    if previousObject and _isEmptyOrWhitespace(previousObject["text"]):
        result.pop()

    return [
        Utterance(
            speaker=u["speaker"],
            utterance=u["text"],
            timestamp=u.get("timestamp", None),
        )
        for u in result
    ]


def _isEmptyOrWhitespace(text):
    return (not text) or (text.isspace())


def _parseSpeakerLine(text: str):
    value = {
        "weak": True,
        "preTime": False,
        "speaker": None,
        "speaker_end": None,
        "time": False,
        "timestamp": None,
        "timestamp_full_match_string": None,
        "separator": False,
        "hasText": False,
        "text": None,
    }

    ################################################
    # extracting timestamp from text
    matchArea = text[:40]
    colonPos = matchArea.find(":")
    timestampFound = get_timestamp(matchArea, value)
    signatureEndPos = 0
    if timestampFound:
        if colonPos != -1 and colonPos < value["timestamp_position"]:
            timestampFound = False
            value["time"] = False
            value["timestamp"] = None
        else:
            if value["timestamp_position"] == 0:
                value["preTime"] = True
            text = text.replace(value["timestamp_full_match_string"], "")
            matchArea = matchArea.replace(value["timestamp_full_match_string"], "")
            signatureEndPos = len(value["timestamp_full_match_string"])
    ################################################
    # check if speaker only, in all caps - WEAK PATTERN
    match = (
        re.search(r"^[ A-Za-z_-]{3,20}$", text)
        if timestampFound
        else re.search(r"^[ A-Z_-]{3,20}$", text)
    )
    if match is not None:
        value["weak"] = not timestampFound
        value["speaker"] = match[0].strip()
        # end position for speaker signature area (for highlighting),
        # use match[0].length to include whitespace
        value["speaker_end"] = len(match[0]) + signatureEndPos
        value["hasText"] = False
        return value

    # update colon position after timestamp removal
    if timestampFound:
        colonPos = matchArea.find(":")

    if colonPos == -1 and not timestampFound:
        return None  # failed to find signature

    if colonPos == -1:  # only timestamp
        if len(text) != 0:
            return None  # if text after timestamp, fail
        value["weak"] = True
        value["speaker"] = "Speaker"
        value["speaker_end"] = signatureEndPos
        value["hasText"] = False

    value["separator"] = True

    # if no whitespace after speaker, fail same line text
    textPos = colonPos + 1
    value["hasText"] = textPos < len(text.rstrip()) - 1
    if value["hasText"] and " \t\n\r\v".find(text[textPos]) == -1:
        return None

    value["weak"] = False
    value["text"] = text[textPos:].strip() if value["hasText"] else None
    value["speaker"] = text[:colonPos].strip()
    value["speaker_end"] = signatureEndPos + colonPos
    return value


def _comp(a, b):
    return (
        a["separator"] == b["separator"]
        and a["time"] == b["time"]
        and a["preTime"] == b["preTime"]
        and a["hasText"] == b["hasText"]
    )


def get_timestamp(text, value):
    # match preceding timestamp "[3:07 PM, 3/15/2022] Adam Hanft: Helps"
    match = re.search(r"(^\s*\[?\s*)([0-9:,\sPAM/]{4,23})(\]?)\s*", text)
    if match is not None and (match[3] or match[0].find("/") != -1):
        value["preTime"] = True
        value["weak"] = False
        value["time"] = True
        value["timestamp"] = match[2].strip()
        value["timestamp_position"] = index_of_group(match, 2)
        value["timestamp_full_match_string"] = match[0]
        return True

    #                  optinal      [        timestamp                 ]  \s*
    match = re.search(r"(^\s*)?(\[?)(\d{1,2}:\d{1,2})(:\d{1,2})?(\.\d*)?(\]?\s*)", text)
    if match is not None:
        value["weak"] = False
        value["time"] = True
        value["timestamp_position"] = match.start()
        value["timestamp_full_match_string"] = match[0]
        # capture timestamp without non-captured groups
        value["timestamp"] = text[
            index_of_group(match, 3) : index_of_group(match, 6)
        ].strip()
        return True

    return False


def index_of_group(match: re.Match, group: int):
    ix = match.start()
    for i in range(1, group):
        if match[i]:
            ix += len(match[i])
    return ix
