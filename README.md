# One AI Python SDK
This SDK provides safe and convenient access to One AI's pipeline API from Python.

One AI is an NLP as a service platform. Our APIs enables language comprehension in context, transforming texts from any source into structured data to use in code.

## Language Studio
The Language Studio provides a visual interface to experiment with our APIs and generate calls to use in code.

Visit the [Langauge Studio](https://studio.oneai.com?utm_source=open_source&utm_medium=python_sdk_readme)

## Documentation
See the [One AI documentation](https://oneai.com/docs)

## Getting started
### Requirements
Python 3.4+ (PyPy supported)

### Installation
`pip install oneai`

### Authentication
Register and create a key for your project [in the Studio](https://studio.oneai.com/settings/api-keys). As a security measure we only show the key once, so make sure to keep it somewhere safe.

Attach your key via the `oneai.api_key` field or by passing it to individual calls. Requests must be authenticated, and will fail without an active token.

### Example
```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Entities(),
    oneai.skills.Summarize(min_length=20),
    oneai.skills.Highlights()
])

my_text = '''One month after the United States began what has become a troubled rollout of a national COVID vaccination campaign, the effort is finally 
gathering real steam. Close to a million doses -- over 951,000, to be more exact -- made their way into the arms of Americans in the past 24 hours, the 
U.S. Centers for Disease Control and Prevention reported Wednesday. That's the largest number of shots given in one day since the rollout began and a big 
jump from the previous day, when just under 340,000 doses were given, CBS News reported. That number is likely to jump quickly after the federal government 
on Tuesday gave states the OK to vaccinate anyone over 65 and said it would release all the doses of vaccine it has available for distribution. Meanwhile, 
a number of states have now opened mass vaccination sites in an effort to get larger numbers of people inoculated, CBS News reported.'''
output = pipeline.run(my_text)
print(output)
```

## Pipeline API
### Language Skills
A Language Skill is a package of trained NLP models, available via API. Skills accept text from various language sources and respond with processed texts and extracted metadata.
### Pipelines
Language AI pipelines allow invoking and chaining multiple Language Skills to process your input text with a single API call. Pipelines can be defined by listing the desired Skills.
```python
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Entities(),
    oneai.skills.Summarize(min_length=20),
    oneai.skills.Highlights()
])
```
### Output
The structure of the output is dynamic, and corresponds to the Skills used and their order in the pipeline. Each output object contains the input text (which can be the original input or text produced by generator Skills), and a list of labels detected by analyzer Skills, that contain the extracted data.
```python
output = pipeline.run(my_text)

print(output.entities)
print(output.summary.text)
print(output.summary.highlights)
```

## Contact
If you need help or are experiencing any issues with the API/SDK, please contact us at [devrel@oneai.com](mailto:devrel@oneai.com).

You're also invited to join our [Discord community](https://discord.gg/ArpMha9n8H).