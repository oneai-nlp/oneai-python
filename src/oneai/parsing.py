import re
import oneai
from oneai.classes import Utterance


def parse_conversation(text: str, strict=False) -> oneai.Conversation:
    # try to parse SRT format (I think this should be done more explicitly)
    srt_regex = re.compile(r'\d+\n\d{1,2}:\d{2}:\d{2}[,.]\d{1,3} --> \d{1,2}:\d{2}:\d{2}[,.]\d{1,3}')
    match = srt_regex.match(text)
    if match:
        data_array = srt_regex.split(text)
        return oneai.Conversation(utterances=[
            Utterance(speaker='SPEAKER', utterance=line.strip().replace('\n', ' '))
            for line in data_array[1:]
        ])

    result = []
    lines = re.split(r"\r?\n", text.strip())
    firstLine = True
    structure = None
    currentLineInfo = None
    waitForTextLine = False
    weak = False
    previousObject = None

    for i, line in enumerate(lines):
        if _isEmptyOrWhitespace(line):
            continue

        if waitForTextLine:
            previousObject["text"] = line.strip()
            previousObject["text_line"] = i
            waitForTextLine = False
            continue

        currentLineInfo = _parseSpeakerLine(line)
        if currentLineInfo is None:
            if firstLine:
                raise ValueError(f"Invalid conversation format at line {i}")
            previousObject["text"] += "\n" + line.strip()
            weak = True
            continue

        if firstLine:
            structure = currentLineInfo
            firstLine = False

        weak |= currentLineInfo["weak"]
        if strict and not _comp(structure, currentLineInfo):
            raise ValueError(
                f"Differing conversation format at line {i}, run with strict=False to ignore"
            )

        if previousObject: result.append(
            Utterance(
                speaker=previousObject["speaker"],
                utterance=previousObject["text"]
            )
        )
        previousObject = {
            "speaker": currentLineInfo["speaker"],
            "text": currentLineInfo["text"],
            "speaker_line": i, # what are these properties for? do I want them in Utterance objects?
            "text_line": i,
            "speaker_length": currentLineInfo["speaker_end"]
        }
        
        waitForTextLine = not bool(currentLineInfo["text"])
    if previousObject and not _isEmptyOrWhitespace(previousObject["text"]):
        result.append(
            Utterance(
                speaker=previousObject["speaker"],
                utterance=previousObject["text"]
            )
        )

    return oneai.Conversation(utterances=result)


def _isEmptyOrWhitespace(text):
    return (not text) or (text.isspace())


def _parseSpeakerLine(text):
    value = {
        "weak": True,
        "preTime": False,
        "speaker": None,
        "speaker_end": None,
        "time": False,
        "separator": False,
        "text": None,
    }

    match = re.match(r"\s*\[?[0-9]+:[0-9]+\]?\s*", text)
    if match:
        text = text[match.end() :]
        value["preTime"] = True
        value["weak"] = False

    # capture STRONG pattern - either timestamp or separator
    matchArea = text[: min(len(text), 35)]
    match = re.search(r"\s{1,10}\[?[0-9]{1,2}:[0-9]{1,2}\]?\s*|\s{0,5}[:|-]", matchArea)

    if not match:  # STRONG not found
        # check if speaker only, in all caps - WEAK PATTERN
        match = re.match(r"[A-Z_-]{3,20}$", matchArea)
        if not match:
            return None  # not a valid format - fail
        else:
            value["speaker"] = match.group(0)
            value["speaker_end"] = len(text)
    else:
        value["weak"] = False
        if match.end() < len(text):
            value["text"] = text[match.end() :].strip()
        value["speaker"] = text[: match.start()]
        value["speaker_end"] = match.end()

        if re.search(r"[:|-]$", match.group(0)):
            value["separator"] = True
        else:
            text = text[match.end() :]
            match = re.match(r"\s*[:|-]", text)
            if match:
                value["separator"] = True
                value["speaker_end"] = match.end()
                value["text"] = (
                    text[match.end() :].strip() if match.end() < len(text) else None
                )
            value["time"] = True
    return value


def _comp(a, b):
    return (
        a["separator"] == b["separator"]
        and a["time"] == b["time"]
        and a["preTime"] == b["preTime"]
        and (a["text"] is None) == (b["text"] is None)
    )
