from dataclasses import dataclass
from typing import List
from typing_extensions import Literal
from warnings import warn

from oneai.classes import Labels, Skill, Utterance, skillclass, Output


@skillclass(
    api_name="enhance",
    text_attr="proofread",
    labels_attr="replacements",
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

    >>> conversation = [oneai.Utterance(...), ...]
    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Proofread()
    ... ])
    >>> output = pipeline.run(conversation)
    >>> output.proofread
    oneai.Output(text='PROOFREAD TRANSCRIPTION', replacements=[...])
    """


@skillclass(
    api_name="summarize",
    text_attr="summary",
    labels_attr="origins",
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


@skillclass(api_name="emotions")
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


@skillclass(api_name="keywords")
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


@skillclass(api_name="highlights")
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


@skillclass(api_name="sentiments")
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


@skillclass(api_name="article-topics", labels_attr="topics")
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
    api_name="pdf-extract-text",
    text_attr="pdf_text",
)
class PDFExtractText(Skill):
    """
    Extracts the text from PDF files.

    ## Output

    Main text content from the PDF file
    """


@skillclass(
    api_name="extract-html",
    text_attr="html_article",
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


@skillclass(
    api_name="html-extract-text",
    text_attr="html_text",
)
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


@skillclass(api_name="action-items", labels_attr="action_items")
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
    text_attr="anonymized",
    labels_attr="anonymizations",
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
    text_attr="labs",
    labels_attr="pricing",
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
    >>> output.labs.pricing
    [oneai.Label(name=pricing, data={'amount': 10.0, 'currency': 'USD', 'unit': 'barrel'}, span=[9, 26], value=10 USD per barrel)]
    """


@skillclass(api_name="names")
@dataclass
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

    enrichment: bool = False
    amount: Literal["more", "less", "normal"] = None


@skillclass(api_name="numbers")
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


@skillclass(api_name="sentences")
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
    labels_attr="segments",
)
@dataclass
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

    std_ratio: float = 0
    amount: Literal["more", "less", "normal"] = None
    use_discourse_parser: bool = False


@skillclass(api_name="sales-insights", labels_attr="sales_insights")
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


@skillclass(
    api_name="service-email-insights",
    labels_attr="service_insights",
)
class ServiceInsights(Skill):
    """
    Finds spans in the text with Service Insights.

    ## Output Attributes

    `service_insights: list[Label]`
        A list of `Label` objects, with detected service insights

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.ServiceInsights()
    ... ])
    >>> output = pipeline.run('...')
    >>> output.service_insights
    """


@skillclass(
    api_name="service-email-insights",
    labels_attr="email_insights",
)
class EmailInsights(Skill):
    """
    Finds spans in the text with Email Insights.

    ## Output Attributes

    `email_insights: list[Label]`
        A list of `Label` objects, with detected email insights

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.EmailInsights()
    ... ])
    >>> output = pipeline.run('...')
    >>> output.email_insights
    """


@skillclass(api_name="detect-language", labels_attr="language")
class DetectLanguage(Skill):
    """
    Detects language of input

    ## Output Attributes

    `language: list[Label]`
        A list of `Label` objects, containing the detected language

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.DetectLanguage()
    ... ])
    >>> output = pipeline.run('...')
    >>> output.language[0]
    """


@skillclass(api_name="headline")
class Headline(Skill):
    """
    Generates a headline based on input

    ## Output Attributes

    `headline: list[Label]`
        A list of `Label` objects, containing the generated headline

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Headline()
    ... ])
    >>> output = pipeline.run('...')
    >>> output.headline[0]
    """


@skillclass(api_name="subheading")
class Subheading(Skill):
    """
    Generates a subheading based on input

    ## Output Attributes

    `subheading: list[Label]`
        A list of `Label` objects, containing the generated subheading

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Subheading()
    ... ])
    >>> output = pipeline.run('...')
    >>> output.subheading[0]
    """


@skillclass(
    api_name="transcribe",
    text_attr="transcription",
    labels_attr="words",
)
@dataclass
class Transcribe(Skill):
    """
    Transcribes audio files

    ## Output

    Speech-to-text transcription of the audio data

    ## Example

    >>> input = oneai.File('./my_audio_file.wav')
    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Transcribe()
    ... ])
    >>> output = pipeline.run(input)
    >>> str(output.transcription.text)[:20] + ' ...'
    oneai.Conversation([ ...
    """

    speaker_detection: bool = True
    timestamp_per_word: bool = False
    engine: Literal["default", "whisper"] = "default"


@skillclass(api_name="clustering")
@dataclass
class Clustering(Skill):
    """
    Automatically organizes various skill labels in clusters for later analytics

    ## Example

    >>> pipeline = oneai.Pipeline(steps=[
    ...     oneai.skills.Sentiments(),
    ...     oneai.skills.Clustering(),
    ... ])
    >>> pipeline.run(input)
    """

    collection: str = ""
    input_skill: str = ""


class OutputAttrs:
    summary: "Output[str]" = None
    proofread: "Output[List[Utterance]]" = None
    html_article: "Output[str]" = None
    html_text: "Output[str]" = None
    pdf_text: "Output[str]" = None
    transcription: "Output[List[Utterance]]" = None
    anonymized: "Output" = None
    words: Labels = None
    emotions: Labels = None
    names: Labels = None
    numbers: Labels = None
    keywords: Labels = None
    highlights: Labels = None
    sentiments: Labels = None
    topics: Labels = None
    sales_insights: Labels = None
    service_insights: Labels = None
    action_items: Labels = None
    pricing: Labels = None
    replacements: Labels = None
    origins: Labels = None
    segments: Labels = None
    sentences: Labels = None
    anonymizations: Labels = None
    language: Labels = None
    headline: Labels = None
    subheading: Labels = None
