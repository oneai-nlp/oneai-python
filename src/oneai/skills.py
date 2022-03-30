from dataclasses import dataclass

from oneai.classes import Skill, skillclass

@skillclass(api_name='enhance', is_generator=True, label_type='replacement', output_name='enhanced_transcription')
class TranscriptionEnhancer(Skill): pass

@skillclass(api_name='summarize', is_generator=True, output_name='summary', param_fields=['min_length', 'max_length'])
@dataclass
class Summarize(Skill):
    min_length: int = 5
    max_length: int = 100

@skillclass(api_name='emotions', label_type='emotion')
class Emotions(Skill): pass

@skillclass(api_name='entities', label_type='entity')
class Entities(Skill): pass

@skillclass(api_name='keywords', label_type='keyword')
class Keywords(Skill): pass

@skillclass(api_name='highlights', label_type='highlight')
class Highlights(Skill): pass

@skillclass(api_name='sentiment', label_type='sentiment')
class Sentiments(Skill): pass

@skillclass(api_name='article-topics', label_type='topic', output_name='topics')
class Topics(Skill): pass

@skillclass(api_name='extract-html')
class HTMLExtractArticle(Skill): pass

@skillclass(api_name='html-extract-text')
class HTMLExtractText(Skill): pass
