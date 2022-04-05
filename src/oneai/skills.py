from dataclasses import dataclass

from oneai.classes import Skill, skillclass

@skillclass(api_name='enhance', is_generator=True, label_type='replacement', output_attr='enhanced', output_attr1='replacements')
class TranscriptionEnhancer(Skill): pass

@skillclass(api_name='summarize', is_generator=True, label_type='origin', output_attr='summary', output_attr1='origins')
@dataclass
class Summarize(Skill):
    '''
    Provides a summary of the input

    Attributes
    ----------
        min_length : int, default=5
            minimal desired length (words) of the summary 
        max_length : int, default=100
            maximal desired length (words) of the summary 


    Examples
    --------
    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.HTMLExtractArticle(),
    ...     oneai.skills.Summarize(min_length=10)
    ... ])
    >>> pipeline.run('https://www.oneai.com/docs/')
    '''
    min_length: int = 5
    max_length: int = 100
    find_origins: bool = True

@skillclass(api_name='emotions', label_type='emotion')
class Emotions(Skill): pass

@skillclass(api_name='entities', label_type='entity')
class Entities(Skill): pass

@skillclass(api_name='keywords', label_type='keyword')
class Keywords(Skill): pass

@skillclass(api_name='highlights', label_type='highlight')
class Highlights(Skill): pass

@skillclass(api_name='sentiments', label_type='sentiment')
class Sentiments(Skill): pass

@skillclass(api_name='article-topics', label_type='topic', output_attr1='topics')
class Topics(Skill): pass

@skillclass(api_name='extract-html')
class HTMLExtractArticle(Skill): pass

@skillclass(api_name='html-extract-text')
class HTMLExtractText(Skill): pass
