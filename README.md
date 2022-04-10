# One AI Python SDK
This SDK provides safe and convenient access to One AI's pipeline API from Python.

One AI is an NLP as a service platform. Our APIs enables language comprehension in context, transforming texts from any source into structured data to use in code.

## Documentation
See the [One AI documentation](https://oneai.com/docs)

## Installation
`pip install oneai`

## Example
```python
import oneai

oneai.api_key = '<YOUR-API-KEY>'
pipeline = oneai.Pipeline(steps=[
    oneai.skills.Entities(),
    oneai.skills.Summarize(min_length=20),
    oneai.skills.Highlights()
])

my_text = '''One month after the United States began what has become a troubled rollout of a national COVID vaccination campaign, the effort is finally gathering real steam. Close to a million doses -- over 951,000, to be more exact -- made their way into the arms of Americans in the past 24 hours, the U.S. Centers for Disease Control and Prevention reported Wednesday. That's the largest number of shots given in one day since the rollout began and a big jump from the previous day, when just under 340,000 doses were given, CBS News reported. That number is likely to jump quickly after the federal government on Tuesday gave states the OK to vaccinate anyone over 65 and said it would release all the doses of vaccine it has available for distribution. Meanwhile, a number of states have now opened mass vaccination sites in an effort to get larger numbers of people inoculated, CBS News reported.'''
results = pipeline.run(my_text)
print(results)
```
