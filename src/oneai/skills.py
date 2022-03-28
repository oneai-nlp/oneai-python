from dataclasses import dataclass

from oneai.classes import Skill, skillclass

@skillclass(name='enhance', iswriting=True)
class Proofread(Skill): pass

@skillclass(name='summarize', iswriting=True, param_fields=['min_length', 'max_length'])
@dataclass
class Summarize(Skill):
    min_length: int = 5
    max_length: int = 100

@skillclass(name='emotions')
class Emotions(Skill): pass

@skillclass(name='entities')
class Entities(Skill): pass

@skillclass(name='keywords')
class Keywords(Skill): pass

@skillclass(name='highlights')
class Highlights(Skill): pass

@skillclass(name='sentences')
class Sentencer(Skill): pass

@skillclass(name='sentiment')
class Sentiments(Skill): pass

@skillclass(name='article-topics')
class Topics(Skill): pass

@skillclass(name='extract-html')
class HTMLExtractArticle(Skill): pass

@skillclass(name='html-extract-text')
class HTMLExtractText(Skill): pass
