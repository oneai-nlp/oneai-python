<p align="center">
  <a href="https://customer.io">
    <img src="https://studio.oneai.com/static/media/logo-gray.d978e495.svg" height="60">
  </a>
  <p align="center">NLP-as-a-service</p>
</p>

# One AI Python SDK
OneAI is a NLP as a service platform. Our API enables language comprehension in context, transforming texts from any source into structured data to use in code.

This SDK provides safe and convenient access to OneAI's API from a python environment.

## Documentation
See the [One AI documentation](https://studio.oneai.com/docs?utm_source=open_source&utm_medium=node_sdk_readme)

## Getting started

### Requirements
Python 3.6.1+ (PyPy supported)

### Installation
`pip install oneai`

### Authentication
You will need a valid API key for all requests. Register and create a key for your project [in OneAI Studio](https://studio.oneai.com/?utm_source=open_source&utm_medium=node_sdk_readme). As a security measure we only show the key once, so make sure to keep it somewhere safe.

#### Example
```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Entities(),
    oneai.skills.Summarize(min_length=20),
    oneai.skills.Highlights()
])

my_text = '''analyze this text.'''
output = pipeline.run(my_text)
print(output)
```

## Pipeline API

The pipeline API enables analyzing and transforming text using various skills. A skill is a package of trained NLP models, available via API, which accept text from various language sources as input and respond with processed texts and extracted metadata. Chaining skills together creates a pipeline.

### OneAI Studio

The best way to create a pipeline is to use our [studio](https://studio.oneai.com/?utm_source=open_source&utm_medium=node_sdk_readme) where you can craft a pipeline using an easy graphical interface and then paste the generated code back into your repository. 

### Basic Example

Let's say you're interested in extracting keywords from the text.
```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Keywords(),
])

my_text = '''analyze this text.'''
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
    oneai.skills.Emotions(),
])

my_text = '''analyze this text.'''
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
    oneai.skills.Summarize(),
])

my_text = '''analyze this text.'''
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
    oneai.skills.Emotions(),
])

my_text = '''analyze this text.'''
output = pipeline.run(my_text)
print(output)
```


### Configuring Skills
Many skills are configurable as you can find out in the [docs](https://studio.oneai.com/docs?utm_source=open_source&utm_medium=node_sdk_readme). Let's use the exact same example, this time however, we'll limit the summary length to 50 words.
```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Summarize(max_length=50),
    oneai.skills.Keywords(),
    oneai.skills.Emotions(),
])

my_text = '''analyze this text.'''
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

my_text = '''analyze this text.'''
output = pipeline.run(my_text)

print(output.entities)
print(output.summary.text)
print(output.summary.highlights)
```


#### Detailed Output Example

That said, here's an example that explains the structure of the response.

```json
{
  "input_text": "your input text here",                // input text from request
  "status": "success",                                 // success/failure
  "error": "string",                                   // error message if relevant 
  "output": [                                          // List of output blocks - one   
    {                                                  // for each input/generated text  
      "text_id": "0",                                  // unique output block ID
      "text_generated_by_step_name": "enhance",        // generated by step (0=input)
      "text_generated_by_step_id":"1"
      "text": "the first summary text",
      "Labels":
       [
        {
         "type":"emotion",                             // generated text if relevant
         "name":"happiness",                           // labels from all processing skills for this text input
         "span":[153,172], 
         "value":"0.89"
        }
      ]
    },                                                 // label type (skill)
    {                                                  // label class
      "text_id": "2",                                  // text span where label found
      "text_from": "summary_2",                        // emotion value confidence
      "text_generated_by_step":"3"                     // label type (skill)
      "origin_span": [10,20],                          // label class
      "text": "the second summary text",               // text span where label found
    }                                                  // parsed cardinal number 
  ]
}
```

### Support

Feel free to submit issues in this repo, contact us at [devrel@oneai.com](mailto:devrel@oneai.com), or chat with us on [Disocrd](https://discord.gg/ArpMha9n8H)

