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

@skillclass(api_name='article-topics', label_type='topic', output_attr='topics')
class Topics(Skill): pass

@skillclass(api_name='extract-html')
class HTMLExtractArticle(Skill): pass

@skillclass(api_name='html-extract-text')
class HTMLExtractText(Skill): pass

@skillclass(api_name='business-entities', is_generator=True, label_type='business-entity', output_attr='labs', output_attr1='business_entities')
class BusinessEntities(Skill): pass

'''[ { "text_generated_by_step_name": "business-entities", "text_generated_by_step_id": 1, "text": 
"labels": [ { "type": "business-entity", "name": "quantity", "span": [ 1022, 1054 ], "value": "25,000 Barrels plus or minus 10%", "output_spans": [ { "section": 0, "start": 1022, "end": 1054 } ], "input_spans": null, "span_text": "25,000 Barrels plus or minus 10%", "data": { "quantity": "25,000", "modifier": "plus or minus 10 %", "unit": "Barrels", "secondary_unit": "", "is_primary_confidence": 1 } }, { "type": "business-entity", "name": "pricing", "span": [ 1473, 1503 ], "value": "Differential: USD 0.09 per GAL", "output_spans": [ { "section": 0, "start": 1473, "end": 1503 } ], "input_spans": null, "span_text": "Differential: USD 0.09 per GAL", "data": { "amount": "0.09", "currency": "USD", "modifier": "Differential :", "unit": "GAL", "is_primary_confidence": 1 } }, { "type": "business-entity", "name": "pricing", "span": [ 1778, 1808 ], "value": "Differential: USD 0.09 per GAL", "output_spans": [ { "section": 0, "start": 1778, "end": 1808 } ], "input_spans": null, "span_text": "Differential: USD 0.09 per GAL", "data": { "amount": "0.09", "currency": "USD", "modifier": "Differential :", "unit": "GAL", "is_primary_confidence": 0.33333333333333337 } }, { "type": "business-entity", "name": "pricing", "span": [ 1921, 1945 ], "value": "USD USD 0.007 per gallon", "output_spans": [ { "section": 0, "start": 1921, "end": 1945 } ], "input_spans": null, "span_text": "USD USD 0.007 per gallon", "data": { "amount": "0.007", "currency": "USD USD", "modifier": "", "unit": "gallon", "is_primary_confidence": 0.33333333333333337 } } ] } ]'''