from dataclasses import dataclass

from oneai.classes import Skill, skillclass

@skillclass(name='enhance', iswriting=True)
class EnhanceTranscription(Skill): pass

@skillclass(name='summarize', iswriting=True, param_fields=['min_length', 'max_length'])
@dataclass
class Summarize(Skill):
    min_length: int = 5
    max_length: int = 100

@skillclass(name='emotions')
class EmotionDetection(Skill): pass

@skillclass(name='entities')
class EntityDetection(Skill): pass

@skillclass(name='keywords')
class KeywordDetection(Skill): pass

@skillclass(name='highlights')
class Highlighting(Skill): pass

@skillclass(name='sentences')
class SplitToSentences(Skill): pass
