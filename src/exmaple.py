import oneai, oneai.skills

text = '''One month after the United States began what has become a troubled rollout of a national COVID vaccination campaign, the effort is finally gathering real steam.
Close to a million doses -- over 951,000, to be more exact -- made their way into the arms of Americans in the past 24 hours, the U.S. Centers for Disease Control and Prevention reported Wednesday. That's the largest number of shots given in one day since the rollout began and a big jump from the previous day, when just under 340,000 doses were given, CBS News reported.
That number is likely to jump quickly after the federal government on Tuesday gave states the OK to vaccinate anyone over 65 and said it would release all the doses of vaccine it has available for distribution. Meanwhile, a number of states have now opened mass vaccination sites in an effort to get larger numbers of people inoculated, CBS News reported.'''

text_convo = '''Prospect  0:00
Hello.

Agent  0:01
Hi, Kiara. This is Almer with Acme. How are you doing?

Prospect  0:05
You're doing good from there. I didn't get it.

Agent  0:09
From Acme. We're a carrot platform I just was following up. It looks like you downloaded our Thank God.

Prospect  0:15
Yeah. Look at it. Luck.

Agent  0:22
Yeah.

Prospect  0:23
But I really didn't get a chance to look at it yet.

Agent  0:27
Yeah, no problem at all I just wanted to call to see, you know, if this is something that you're interested in, we could set up like, you know, 10 minutes for me to answer any questions that you have. Or if you want, we can see if it makes sense to, you know, set up like an actual flower of the product. But I wanted to reach out first and see what would be appropriate.

Prospect  0:49
Yeah, sure. I let me have a look into that. Actually, it sounded interesting to me, because we are also working on carrot soup itself here.

Agent  0:59
Of course, yeah. What are some of the things that you guys are looking for? I know, I mean, carrot soup, just as people become more data mature, you know, it becomes so important for, for companies to understand, you know, volcano behavior of their lands, and being able to eat when there are carrots and things of that nature. So, yeah, I'd be happy to give you guys an overview. You want me to follow up like later this week? and then we can figure out, you know, timing is really like next week.

Prospect  1:28
If you Is it possible for you to call me on Friday by the time and have a look on the whole document which I have downloaded?

Agent  1:36
Yeah. And we can have a more directed conversation for sure. What do you want me to give you a call at 1pm? I'm on pacific time as well.

Prospect  1:44
Yeah, 1pm would be fine. Okay,

Agent  1:46
cool. Sounds good. Well, I'll go ahead and add you on Farmvil. So you can put a name to the face and if anything changes, just let me know. But otherwise, I'll look forward to talking to you again on Friday.

Prospect  1:56
Yeah.

Agent  1:58
Okay, cool. Take care of on the way
'''

if __name__ == '__main__':
    result = oneai.process(text_convo, oneai.skills.EnhanceTranscription())
    print(result)