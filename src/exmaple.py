import oneai

text = '''One month after the United States began what has become a troubled rollout of a national COVID vaccination campaign, the effort is finally gathering real steam.
Close to a million doses -- over 951,000, to be more exact -- made their way into the arms of Americans in the past 24 hours, the U.S. Centers for Disease Control and Prevention reported Wednesday. That's the largest number of shots given in one day since the rollout began and a big jump from the previous day, when just under 340,000 doses were given, CBS News reported.
That number is likely to jump quickly after the federal government on Tuesday gave states the OK to vaccinate anyone over 65 and said it would release all the doses of vaccine it has available for distribution. Meanwhile, a number of states have now opened mass vaccination sites in an effort to get larger numbers of people inoculated, CBS News reported.'''

if __name__ == '__main__':
    oneai.api_key = '510a3615-59ff-4f4c-9d98-2cc30e7408d7'
    pipeline = oneai.Pipeline(steps=[
        oneai.skills.EntityDetection(),
        oneai.skills.Summarize(min_length=20),
        oneai.skills.Highlighting()
    ])
    print(pipeline)
