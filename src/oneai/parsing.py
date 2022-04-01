import re
import oneai


def parse_conversation(text: str, strict=False) -> oneai.Conversation:
    result = []
    lines = re.split(r'\r?\n', text.strip())
    firstLine = True
    structure = None
    currentLineInfo = None
    waitForTextLine = False
    weak = False
    
    for i, line in enumerate(lines):
        if _isEmptyOrWhitespace(line):
            continue

        if waitForTextLine:
            result.append(oneai.Utterance(
                speaker=currentLineInfo['speaker'],
                utterance=line.strip()
            ))
            waitForTextLine = False
            continue
            
        currentLineInfo = _parseSpeakerLine(line)
        if currentLineInfo is None:
            raise ValueError(f'Invalid conversation format at line {i}')
        
        if firstLine:
            structure = currentLineInfo
            firstLine = False

        weak |= currentLineInfo['weak']
        if strict and not _comp(structure, currentLineInfo):
            raise ValueError(f'Differing conversation format at line {i}, run with strict=False to ignore')
        
        if currentLineInfo['text']:
            result.append(oneai.Utterance(
                speaker=currentLineInfo['speaker'],
                utterance=currentLineInfo['text']
            ))
            waitForTextLine = False
        else:
            waitForTextLine = True
    if waitForTextLine:
        raise ValueError('Invalid conversation format: last utterance is empty, at line')
    
    if weak and len(result) <= 3:
        raise ValueError('Weak pattern detected, but conversation is too short')

    return oneai.Conversation(utterances=result)

def _isEmptyOrWhitespace(text):
    return (not text) or (text.isspace())


def _parseSpeakerLine(text):
    value = {
        'weak': True,
        'preTime': False,
        'speaker': None,
        'time': False,
        'separator': False,
        'text': None
    }

    match = re.match(r'\s*\[?[0-9]+:[0-9]+\]?\s*', text)
    if match:
        text = text[match.end():]
        value['preTime'] = True
        value['weak'] = False

    # capture STRONG pattern - either timestamp or separator
    matchArea = text[:min(len(text), 35)]
    match = re.search(r'\s{1,10}\[?[0-9]{1,2}:[0-9]{1,2}\]?\s*|\s{0,5}[:|-]', matchArea)

    if not match: # STRONG not found
        # check if speaker only, in all caps - WEAK PATTERN
        match = re.match(r'[A-Z_-]{3,20}$', matchArea)
        if not match: return None # not a valid format - fail
        else: value['speaker'] = match.group(0)
    else:
        value['weak'] = False
        if match.end() < len(text):
            value['text'] = text[match.end():].strip()
        value['speaker'] = text[:match.start()]

        if re.search(r'[:|-]$', match.group(0)):
            value['separator'] = True
        else:
            text = text[match.end():]
            match = re.match(r'\s*[:|-]', text)
            if match:
                value['separator'] = True
                value['text'] = text[match.end():].strip() if match.end() < len(text) else None
            value['time'] = True
    return value


def _comp(a, b):
    return a['separator'] == b['separator'] and \
            a['time'] == b['time'] and \
            a['preTime'] == b['preTime'] and \
            (a['text'] is None) == (b['text'] is None)
