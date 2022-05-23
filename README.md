<p align="center">
  <a href="https://customer.io">
    <img src="https://studio.oneai.com/static/media/logo-gray.d978e495.svg" height="60">
  </a>
  <p align="center">NLP-as-a-service</p>
</p>

# One AI Python SDK
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
    oneai.skills.Entities(),
    oneai.skills.Summarize(min_length=20),
    oneai.skills.Highlights()
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

Let's say you're interested in extracting keywords *and* emotions from the text.
```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Keywords(),
    oneai.skills.Emotions()
])

my_text = 'analyze this text.'
output = pipeline.run(my_text)
print(output)
```

### Analyzer Skills vs Generator Skills

Skills can do either text analysis, and then their output are labels and spans (labels location in the analyzed text), or they can be generator skills, in which case they transform the input text into an output text.

Here's an example for a pipeline that combines both type of skills. It will extract keywords and emotions from the text, and then summarize it.

```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Keywords(),
    oneai.skills.Emotions(),
    oneai.skills.Summarize()
])

my_text = 'analyze this text.'
output = pipeline.run(my_text)
print(output)
```

### Order is Important

When the pipeline is invoked, it is invoked with an original text you submit. If a generator skill is ran, then all following skills will use its generated text rather then the original text. In this example, for instance, we change the order of the pipeline from the previous example, and the results will be different. Instead of extracting keywords and emotions from the original text, keywords and emotions will be extracted from the generated summary.

```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Summarize(),
    oneai.skills.Keywords(),
    oneai.skills.Emotions()
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
    oneai.skills.Emotions()
])

my_text = 'analyze this text.'
output = pipeline.run(my_text)
print(output)
```

### Output
The structure of the output is dynamic, and corresponds to the Skills used and their order in the pipeline. Each output object contains the input text (which can be the original input or text produced by generator Skills), and a list of labels detected by analyzer Skills, that contain the extracted data.
```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Summarize(max_length=50),
    oneai.skills.Keywords(),
    oneai.skills.Emotions(),
])

my_text = 'analyze this text.'
output = pipeline.run(my_text)

print(output.entities)
print(output.summary.text)
print(output.summary.highlights)
```

### Support

Feel free to submit issues in this repo, contact us at [devrel@oneai.com](mailto:devrel@oneai.com), or chat with us on [Disocrd](https://discord.gg/ArpMha9n8H)

