<p align="left">
  <a href="https://oneai.com?utm_source=open_source&utm_medium=python_sdk_readme">
    <img src="./oneai_logo_light_cropped.svg" height="60">
  </a>
</p>

# Python SDK
One AI is a NLP as a service platform. Our API enables language comprehension in context, transforming texts from any source into structured data to use in code.

This SDK provides safe and convenient access to One AI's API from a Python environment.

## Documentation
See the [documentation](https://studio.oneai.com/docs?utm_source=open_source&utm_medium=python_sdk_readme)

## Getting started

### Requirements
Python 3.6.1+ (PyPy supported)

### Installation
`pip install oneai`

### Authentication
You will need a valid API key for all requests. Register and create a key for your project [in the Studio](https://studio.oneai.com/?utm_source=open_source&utm_medium=python_sdk_readme).

#### Example
```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Names(),
    oneai.skills.Summarize(min_length=20),
    oneai.skills.Keywords()
])

my_text = 'analyze this text.'
output = pipeline.run(my_text)
print(output)
```

## Pipeline API
### Language Skills
A Language Skill is a package of trained NLP models, available via API. Skills accept text as an input in various formats, and respond with processed texts and extracted metadata.

### Pipelines
Language AI pipelines allow invoking and chaining multiple Language Skills to process your input text with a single call. Pipelines are defined by listing the desired Skills.

### Language Studio
The [Language Studio](https://studio.oneai.com/?utm_source=open_source&utm_medium=python_sdk_readme) provides a visual interface to experiment with our APIs and generate calls to use in code. In the Studio you can craft a pipeline and paste the generated code back into your repository. 

### Basic Example

Let's say you're interested in extracting keywords from the text.
```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Keywords()
])

my_text = 'analyze this text.'
output = pipeline.run(my_text)
print(output)
```

### Multi Skills request

Let's say you're interested in extracting keywords *and* sentiments from the text.
```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Keywords(),
    oneai.skills.Sentiments()
])

my_text = 'analyze this text.'
output = pipeline.run(my_text)
print(output)
```

### Analyzer Skills vs Generator Skills

Skills can do either text analysis, and then their output are labels and spans (labels location in the analyzed text), or they can be generator skills, in which case they transform the input text into an output text.

Here's an example for a pipeline that combines both type of skills. It will extract keywords and sentiments from the text, and then summarize it.

```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Keywords(),
    oneai.skills.Sentiments(),
    oneai.skills.Summarize()
])

my_text = 'analyze this text.'
output = pipeline.run(my_text)
print(output)
```

### Order is Important

When the pipeline is invoked, it is invoked with an original text you submit. If a generator skill is ran, then all following skills will use its generated text rather then the original text. In this example, for instance, we change the order of the pipeline from the previous example, and the results will be different. Instead of extracting keywords and sentiments from the original text, keywords and sentiments will be extracted from the generated summary.

```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Summarize(),
    oneai.skills.Keywords(),
    oneai.skills.Sentiments()
])

my_text = 'analyze this text.'
output = pipeline.run(my_text)
print(output)
```


### Configuring Skills
Many skills are configurable as you can find out in the [docs](https://studio.oneai.com/docs?utm_source=open_source&utm_medium=python_sdk_readme). Let's use the exact same example, this time however, we'll limit the summary length to 50 words.
```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Summarize(max_length=50),
    oneai.skills.Keywords(),
    oneai.skills.Sentiments()
])

my_text = 'analyze this text.'
output = pipeline.run(my_text)
print(output)
```

### Output
The structure of the output is dynamic, and corresponds to the Skills used and their order in the pipeline. Each output object contains the input text (which can be the original input or text produced by generator Skills), and a list of labels detected by analyzer Skills, that contain the extracted data. For example:
```python
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Sentiments(),
    oneai.skills.Summarize(max_length=50),
    oneai.skills.Keywords(),
])

my_text = '''Could a voice control microwave be the new norm? The price is unbeatable for a name brand product, an official Amazon brand, so you can trust it at least. Secondly, despite the very low price, if you don't want to use the voice control, you can still use it as a regular microwave.'''
output = pipeline.run(my_text)
```
will generate the following:
```python
oneai.Output(
    text="Could a voice control microwave be the ...",
    sentiments=[ # list of detected sentiments
        oneai.Label(
            type='sentiment',
            output_spans=[ # where the sentiment appears in the text
                Span(
                    start=49,
                    end=97,
                    section=0,
                    text='The price is unbeatable for a name brand product'
                )
            ],
            value='POS' # a positive sentiment
        ),
        ...
    ],
    summary=oneai.Output(
        text='The price is unbeatable for a name brand product, an official Amazon brand, so you can trust it at least. Despite the very low price, you can still use it as a regular microwave.',
        keywords=[ # keyword labels
            oneai.Label(type='keyword', name='price', output_spans=[Span(start=4, end=9, section=0, text='price')], value=0.253), ...
        ]
    )
)
```

### File Uploads
Our API supports the following file extensions:
* `.txt`- text content
* `.json`- conversations in the One AI conversation format
* `.srt`- analyze captions as conversations
* `.wav`- audio files to be transcribed & analyzed
* `.jpg`- detect text in pictures via OCR
Upload a file by passing the the FileIO object to the pipeline
```python
with open('./example.txt', 'r') as inputf:
    pipeline = oneai.Pipeline(steps=[...])
    output = pipeline.run(inputf)
```
For large audio files, use the asyncronous `Pipeline.run_async`
```python
with open('./example.mp3', 'rb') as inputf:
    pipeline = oneai.Pipeline(steps=[oneai.skills.Transcribe(), ...])
    output = await pipeline.run(inputf)
```

### Support

Feel free to submit issues in this repo, contact us at [devrel@oneai.com](mailto:devrel@oneai.com), or chat with us on [Discord](https://discord.gg/ArpMha9n8H)

