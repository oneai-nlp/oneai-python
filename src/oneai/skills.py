from dataclasses import dataclass
from warnings import warn
from oneai import scraping

from oneai.classes import Skill, skillclass


@skillclass(
    api_name="enhance",
    is_generator=True,
    label_type="replacement",
    output_attr="enhanced",
    output_attr1="replacements",
)
class TranscriptionEnhancer(Skill):
    """
    Deprecated- use `Proofread` instead

    ## Output Attributes

    `enhanced: Output`
        An `Output` object containing the enhanced conversation, and output of the following `Skill`s
    `enhanced.text: str`
        The enhanced conversation
    `enhanced.replacements: list[Label]`
        A list of `Label` objects, representing changes made to the text

    ## Example

    >>> conversation = oneai.Conversation([...])
    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.TranscriptionEnhancer()
    ... ])
    >>> output = pipeline.run(conversation)
    >>> output.enhanced
    oneai.Output(text='ENHANCED TRANSCRIPTION', replacements=[...])
    """

    def __new__(cls, *args, **kwargs):
        warn(
            "TranscriptionEnhancer Skill is deprecated- use `Proofread` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().__new__(cls, *args, **kwargs)


@skillclass(
    api_name="enhance",
    is_generator=True,
    label_type="replacement",
    output_attr="proofread",
    output_attr1="replacements",
)
class Proofread(Skill):
    """
    Enhances conversations, removing fillers and mistakes. Only works with `Conversation` inputs

    ## Output Attributes

    `proofread: Output`
        An `Output` object containing the enhanced conversation, and output of the following `Skill`s
    `proofread.text: str`
        The enhanced conversation
    `proofread.replacements: list[Label]`
        A list of `Label` objects, representing changes made to the text

    ## Example

    >>> conversation = oneai.Conversation([...])
    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Proofread()
    ... ])
    >>> output = pipeline.run(conversation)
    >>> output.proofread
    oneai.Output(text='PROOFREAD TRANSCRIPTION', replacements=[...])
    """


@skillclass(
    api_name="summarize",
    is_generator=True,
    label_type="origin",
    output_attr="summary",
    output_attr1="origins",
)
@dataclass
class Summarize(Skill):
    """
    Provides a summary of the input

    ##  Attributes

    `min_length: int`
        Minimal desired length (words) of the summary. Omit for automatic length
    `max_length: int`
        Maximal desired length (words) of the summary. Omit for automatic length
    `find_origins: bool, default=False`
        Whether to generate origins of the summary, pointing to the input text

    ## Output Attributes

    `summary: Output`
        An `Output` object containing the generated summary, and output of the following `Skill`s
    `summary.text: str`
        The generated summary
    `summary.origins: list[Label]`
        A list of `Label` objects, mapping words from the summary to the corresponding words in the input text. Only generated if `find_origins=True`

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Summarize(min_length=10, find_origins=True)
    ... ])
    >>> output = pipeline.run('YOUR-TEXT')
    >>> output.summary
    oneai.Output(text='SUMMARY', origins=[...])
    """

    min_length: int = 0
    max_length: int = 0
    find_origins: bool = False


@skillclass(api_name="emotions", label_type="emotion")
class Emotions(Skill):
    """
    Detects emotions in the input. Supported emotions: [`happiness`, `sadness`, `fear`, `surprise`, `anger`]

    ## Output Attributes

    `emotions: list[Label]`
        A list of `Label` objects, with spans of the input that were detected as conveying an emotion

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Emotions()
    ... ])
    >>> output = pipeline.run("I'm not interested. Don't call me again!")
    >>> output.emotions
    [oneai.Label(type=emotion, span=[20, 40], name=anger)]
    """


@skillclass(api_name="entities", label_type="entity")
class Entities(Skill):
    """
    Deprecated- use either `Names` or `Numbers` instead

    ## Output Attributes

    `entities: list[Label]`
        A list of `Label` objects, with detected entities and their type

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Entities()
    ... ])
    >>> output = pipeline.run('Jim bought shares of Acme Corp.')
    >>> output.entities
    [oneai.Label(type=entity, name=PERSON, span=[0, 3], value=Jim), oneai.Label(type=entity, name=ORG, span=[21, 31], value=Acme Corp.)]
    """

    def __new__(cls, *args, **kwargs):
        warn(
            "Entities Skill is deprecated- use either `Names` or `Numbers` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().__new__(cls, *args, **kwargs)


@skillclass(api_name="keywords", label_type="keyword")
class Keywords(Skill):
    """
    Detects keywords in the input

    ## Output Attributes

    `keywords: list[Label]`
        A list of `Label` objects, with detected keywords

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Keywords()
    ... ])
    >>> output = pipeline.run('I love this app, it helps me to organize my tasks')
    >>> output.keywords
    [oneai.Label(type=keyword, span=[12, 15], value=app), oneai.Label(type=keyword, span=[44, 49], value=tasks)]
    """


@skillclass(api_name="highlights", label_type="highlight")
class Highlights(Skill):
    """
    Detects highlights of the input

    ## Output Attributes

    `highlights: list[Label]`
        A list of `Label` objects, with detected highlights

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Highlights()
    ... ])
    >>> output = pipeline.run('YOUR-TEXT')
    >>> output.keywords
    [oneai.Label(value='A-HIGHLIGHT'), ...]
    """


@skillclass(api_name="sentiments", label_type="sentiment")
class Sentiments(Skill):
    """
    Detects sentiments in the input

    ## Output Attributes

    `sentiments: list[Label]`
        A list of `Label` objects, with spans of the input that were detected as having positive or negative sentiment

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Sentiments()
    ... ])
    >>> output = pipeline.run('I love this app, it helps me to organize my tasks')
    >>> output.sentiments
    [oneai.Label(type=sentiment, span=[0, 49], value=POS)]
    """


@skillclass(api_name="article-topics", label_type="topic", output_attr="topics")
class Topics(Skill):
    """
    Detects topics of the input

    ## Output Attributes

    `topics: list[Label]`
        A list of `Label` objects, with extracted topics

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Topics()
    ... ])
    >>> output = pipeline.run('One AI is an NLP platform for developers')
    >>> output.topics
    [oneai.Label(type=topic, value=Machine Learning), oneai.Label(type=topic, value=Artificial Intelligence), ...]
    """


@skillclass(
    api_name="extract-html",
    is_generator=True,
    output_attr="html_article",
    run_custom=scraping.extract_article,
)
class HTMLExtractArticle(Skill):
    """
    Extracts the main text content of an HTML page. Accepts URLs or HTML strings

    ## Output

    Main text content from the HTML page

    ## Example

    >>> resp = requests.get('https://oneai.com/about-us/')
    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.HTMLExtractArticle()
    ... ])
    >>> output = pipeline.run(resp.text)
    >>> output.html_article.text[:100] + '...'
    One AI - About us
    ABOUT ONE AI
    // Bringing human-level language AI to everyday life, one developer a...
    """

    def __new__(cls, *args, **kwargs):
        warn(
            "BusinessEntities Skill is deprecated- use `Pricing` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().__new__(cls, *args, **kwargs)


@skillclass(api_name="html-extract-text", is_generator=True, output_attr="html_text")
class HTMLExtractText(Skill):
    """
    Extracts all text content of an HTML page (including text from control elements). Accepts URLs or HTML strings. Use HTMLExtractArticle to extract the main content only

    ## Output

    Text content from the HTML page

    ## Example

    >>> resp = requests.get('https://oneai.com/about-us/')
    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.HTMLExtractText()
    ... ])
    >>> output = pipeline.run(resp.text)
    >>> output.html_text.text[:100] + '...'
    One AI - About usSkip to main contentAPIStudioSkillsIndustriesPricingResearchAboutAbout UsLeadership...
    """

    def __new__(cls, *args, **kwargs):
        warn(
            "BusinessEntities Skill is deprecated- use `Pricing` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().__new__(cls, *args, **kwargs)


@skillclass(
    api_name="extract-html",
    is_generator=True,
    output_attr="html_article",
    run_custom=scraping.extract_article,
)
class HtmlToArticle(Skill):
    """
    Extracts the main text content of an HTML page. Accepts URLs or HTML strings

    ## Output

    Main text content from the HTML page

    ## Example

    >>> resp = requests.get('https://oneai.com/about-us/')
    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.HtmlToArticle()
    ... ])
    >>> output = pipeline.run(resp.text)
    >>> output.html_article.text[:100] + '...'
    One AI - About us
    ABOUT ONE AI
    // Bringing human-level language AI to everyday life, one developer a...
    """


@skillclass(api_name="html-extract-text", is_generator=True, output_attr="html_text")
class HtmlAllText(Skill):
    """
    Extracts all text content of an HTML page (including text from control elements). Accepts URLs or HTML strings. Use HTMLExtractArticle to extract the main content only

    ## Output

    Text content from the HTML page

    ## Example

    >>> resp = requests.get('https://oneai.com/about-us/')
    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.HtmlAllText()
    ... ])
    >>> output = pipeline.run(resp.text)
    >>> output.html_text.text[:100] + '...'
    One AI - About usSkip to main contentAPIStudioSkillsIndustriesPricingResearchAboutAbout UsLeadership...
    """


@skillclass(
    api_name="business-entities",
    is_generator=True,
    label_type="business-entity",
    output_attr="labs",
    output_attr1="business_entities",
)
class BusinessEntities(Skill):
    """
    ### 'Labs' Skill- this Skill is still in beta and is may produce incorrect results in some cases

    deprecated- use `Pricing` instead.
    Detects business entities (quantities, pricings) in the input

    ## Output Attributes

    `business_entities: list[Label]`
        A list of `Label` objects, with detected business entities and their data

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.BusinessEntities()
    ... ])
    >>> output = pipeline.run('it costs 10 USD per barrel')
    >>> output.business_entities
    [oneai.Label(type=business-entity, name=pricing, data={'amount': 10.0, 'currency': 'USD', 'unit': 'barrel'}, span=[9, 26], value=10 USD per barrel)]
    """

    def __new__(cls, *args, **kwargs):
        warn(
            "BusinessEntities Skill is deprecated- use `Pricing` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().__new__(cls, *args, **kwargs)


@skillclass(
    api_name="action-items", label_type="action-item", output_attr="action_items"
)
class ActionItems(Skill):
    """
    ### 'Labs' Skill- this Skill is still in beta and is may produce incorrect results in some cases

    Detects action items in the input

    ## Output Attributes

    `action_items: list[Label]`
        A list of `Label` objects, with detected action items

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.ActionItems()
    ... ])
    >>> output = pipeline.run("It's been a blast talking to you. Let's schedule another meeting for next Sun.")
    >>> output.action_items
    [oneai.Label(type=action-item, span=[34, 78], value=Let's schedule another meeting for next Sun.)]
    """


@skillclass(
    api_name="anonymize",
    is_generator=True,
    label_type="anonymized",
    output_attr="anonymized",
    output_attr1="anonymizations",
)
class Anonymize(Skill):
    """
    Anonymize texts, removing personal information

    ## Output Attributes

    `anonymized: Output`
        An `Output` object containing the anonymized text, and output of the following `Skill`s
    `anonymized.text: str`
        The anonymized text
    `anonymized.anonymizations: list[Label]`
        A list of `Label` objects, representing anonymized information

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Anonymize()
    ... ])
    >>> output = pipeline.run("hello, I'm Michael, my email is michael@abcde.com")
    >>> output.anonymized.text
    hello, I'm ***, my email is ***
    >>> output.anonymized.anonymizations
    [oneai.Label(type=anonymized, span=[11, 14], value=Michael), oneai.Label(type=anonymized, span=[28, 31], value=michael@abcde.com)]
    """


@skillclass(
    api_name="business-entities",
    is_generator=True,
    label_type="business-entity",
    output_attr="labs",
    output_attr1="pricing",
)
class Pricing(Skill):
    """
    ### 'Labs' Skill- this Skill is still in beta and is may produce incorrect results in some cases

    Detects pricing and quantities in the input

    ## Output Attributes

    `pricing: list[Label]`
        A list of `Label` objects, with detected pricing and their data

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Pricing()
    ... ])
    >>> output = pipeline.run('it costs 10 USD per barrel')
    >>> output.pricing
    [oneai.Label(name=pricing, data={'amount': 10.0, 'currency': 'USD', 'unit': 'barrel'}, span=[9, 26], value=10 USD per barrel)]
    """


@skillclass(api_name="names", label_type="name")
class Names(Skill):
    """
    Detects and classifies names in the input

    ## Output Attributes

    `names: list[Label]`
        A list of `Label` objects, with detected names and their type

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Names()
    ... ])
    >>> output = pipeline.run('Jim bought shares of Acme Corp.')
    >>> output.names
    [oneai.Label(type=entity, name=PERSON, span=[0, 3], value=Jim), oneai.Label(type=entity, name=ORG, span=[21, 31], value=Acme Corp.)]
    """


@skillclass(api_name="numbers", label_type="number")
class Numbers(Skill):
    """
    Detects and classifies numbers and dates in the input

    ## Output Attributes

    `entities: list[Label]`
        A list of `Label` objects, with detected numbers and their type

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Numbers()
    ... ])
    >>> output = pipeline.run('Jim bought shares of Acme Corp.')
    >>> output.numbers
    """


@skillclass(api_name="sentences", label_type="sentence")
class SplitBySentence(Skill):
    """
    Splits input by sentence

    ## Output Attributes

    `sentences: list[Label]`
        A list of `Label` objects, with detected numbers and their type

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Sentences()
    ... ])
    >>> output = pipeline.run('...')
    >>> output.sentences
    """


@skillclass(
    api_name="dialogue-segmentation",
    label_type="dialogue-segment",
    output_attr="segments",
)
class SplitByTopic(Skill):
    """
    Splits input by discussed topics

    ## Output Attributes

    `segments: list[Label]`
        A list of `Label` objects, with generated topic-segments

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.SplitByTopic()
    ... ])
    >>> output = pipeline.run('...')
    >>> output.segments
    """


@skillclass(
    api_name="sales-insights", label_type="sales-insights", output_attr="sales_insights"
)
class SalesInsights(Skill):
    """
    Splits input by discussed topics

    ## Output Attributes

    `sales_insights: list[Label]`
        A list of `Label` objects, with detected sales insights

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.SalesInsights()
    ... ])
    >>> output = pipeline.run('...')
    >>> output.sales_insights
    """
