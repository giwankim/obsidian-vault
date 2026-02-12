---
title: "Steve Yegge on AI Agents and the Future of Software Engineering"
source: "https://newsletter.pragmaticengineer.com/p/steve-yegge-on-ai-agents-and-the?utm_source=post-email-title&publication_id=458709&post_id=187563524&utm_campaign=email-post-title&isFreemail=true&r=8x3s&triedRedirect=true&utm_medium=email"
author:
  - "[[Gergely Orosz]]"
published: 2026-02-11
created: 2026-02-12
description: "Steve Yegge on the 8 levels of AI adoption, why big companies may be doomed, and why he and many AI-adopters feel drained from using agents non-stop"
tags:
  - "clippings"
---
### Steve Yegge on the 8 levels of AI adoption, why big companies may be doomed, and why he and many AI-adopters feel drained from using agents non-stop

*Note: apologies for this issue of the newsletter arriving slightly later than usual, I’m currently in San Francisco. Last night, I attended AI Night with WorkOS, and tomorrow I’ll be hosting [The Pragmatic Summit](https://www.pragmaticsummit.com/).*

![](https://substackcdn.com/image/fetch/$s_!6gca!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fbf1479a6-12f4-4060-b5d7-caefa6656db0_1600x506.png)

More than 200 people attended a packed AI Night event, featuring hands-on demos and a fireside chat between WorkOS founder Michael Grinich (in the middle, to the left of me) and myself

*The next podcast episode with Kotlin’s creator, Andrey Breslav, will be out on Thursday instead of tomorrow (Wednesday). Regular scheduling, including [The Pulse](https://newsletter.pragmaticengineer.com/s/the-pulse), resumes next week. We’ll release session recordings from the Pragmatic Summit to paid subscribers first, and later to everyone.*

*Please wish me luck with this event tomorrow, it’s the first ever in-person event by The Pragmatic Engineer, and there’s a full house of 500 attendees. If you’re there, come and say hi!*

---

Steve Yegge has been a software engineer for over 40 years, with stints at GeoWorks, Amazon, Google, and Grab. He’s known for provocative, entertaining blog posts, of which the most famous might be [Stevey’s Google platform rant](https://gist.github.com/chitchcock/1281611).

Steve recently published the book *“Vibe Coding”,* has also built [Gas Town](https://github.com/steveyegge/gastown), an open-source AI agent orchestrator, and created documentation site and community hub [Gas Townhall](https://gastownhall.ai/) around the project. A year ago, we did [a podcast](https://newsletter.pragmaticengineer.com/p/amazon-google-and-vibe-coding-with) focusing on his career, including how he used AI for coding. Last week, Steve and I sat down again in Salt Lake City and explored what’s changed in terms of using LLMs for coding, and also the wider tech industry.

![](https://substackcdn.com/image/fetch/$s_!u5UR!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F7db99a33-23b5-4f42-9fff-0036150bab74_1600x1200.jpeg)

Steve (right) and I in Salt Lake City

In this article, we cover:

1. **LLMs, the end of coding by hand, and the S-curve.** Initially skeptical of LLMs, Steve became a convert after trying out Claude Code. He now argues the industry is headed into a steep exponential curve that shows no signs of stopping.
2. **“50% dial” and deep cuts**. Could big companies cut up to 50% of their staff in order to make way for AI tools? Such a trend might dwarf pandemic-era layoffs.
3. **Eight levels of AI adoption.** A spectrum of AI adoption, from “no AI”, to “building your own orchestrator”. Steve fears engineers stuck at the lower levels will be left behind.
4. **The Dracula effect: the drain of using AI.** Vibe coding at full speed can be physically draining, and Steve argues that employers shouldn’t reasonably expect more than three hours of AI-augmented work from engineers, per day.
5. **Big companies are doomed – but don’t know it.** Innovation at large companies is effectively dead, and the real action will come from small, AI-augmented teams – like when cloud computing shifted the balance of power.
6. **Redundant values in the AI era.** Knowing how to code doesn’t make engineers special any more, but demand for software will keep growing.
7. **Debugging and programming languages.** Agents may not need good debugging tools, and language choices have never mattered less.
8. **Grieving the demise of coding by hand.** Steve endured a grieving process when he realized many skills are obsolete, BUT building software is now more fun than ever.
9. **Predictions.** Steve’s non-coder wife could be the top contributor to their video game, [Wyvern](https://store.steampowered.com/app/1541710/Wyvern/).

Related The Pragmatic Engineer articles featuring Steve:

- [Amazon, Google, and Vibe Coding with Steve Yegge](https://newsletter.pragmaticengineer.com/p/amazon-google-and-vibe-coding-with) (podcast episode in 2025)
- [The full circle of developer productivity with Steve Yegge](https://newsletter.pragmaticengineer.com/p/steve-yegge) (deepdive in 2022)

*For paid subscribers, you can also watch the recording or listen to it via a video. Unfortunately, Steve’s audio is not great – which is also why this interview did not make it to a podcast format – so we’ve added subtitles to the video. See the link at the bottom of the article.*

## 1\. LLMs, the end of coding by hand, and the S-curve

**One thing about you is that you’re pretty pragmatic. You were always into compilers, debugger tools, and worked on hard problems at Amazon and Google. When AI came out, I don’t remember you saying, “this is amazing!” What was your initial reaction to LLMs?**

**Steve:** “I was pretty blown away that they could write fairly coherent Emacs and Lisp functions. The original ChatGPT in December 2022 could already write code in a weird language, right? Not very much of it, and it was janky; but for me, that was the beginning. I’ve had friends who were saying for 20 years, “any minute now, any day now” about AI. But 2022 was the first time that it was like, “okay, I see now.

I was still skeptical when the rumors emerged about Claude Code at the start of last year, that Anthropic had a tool internally that was writing code for them and it was a command line tool. Like many others, my reaction was “no, it’s not!” Then I used it and was like, “oh, I get it. We’re all doomed.” It was then that I wrote [The Death of the Junior Developer](https://sourcegraph.com/blog/the-death-of-the-junior-developer).

So, was I a skeptic? Yes. But did I pay attention to the curves from the very beginning? Also yes. It was at that point that I thought we’re on a curve, this is a ride, and it’s not stopping, so let’s get on board and see where it goes.”

I dived in. I was feeling behind because I didn’t know AI, I didn’t know its fundamentals, or the lingo. I spent a year doing nothing but reading papers and catching up”.

**Your book,** ***‘Vibe Coding’,*** **says on its rear cover: “the days of coding by hand are over”. When did you decide this?**

**Steve:** “It was a year ago \[early 2025\] and that wasn’t even my quote. It’s [Dr. Erik Meijer](https://en.wikipedia.org/wiki/Erik_Meijer_\(computer_scientist\)), the inventor of many things in the programming world, and one of the most important compiler people in the world. He spent his life building technology for developers to be able to write code, and he’s saying developers aren’t going to write code anymore. That’s what caused [Gene Kim](http://www.realgenekim.me/) (author of The Phoenix Project and former CTO of Tripwire) and I to both say that if someone this prolific in the tech world says ‘we’re done writing code’, then what does he see that we don’t?

He sees the curves; it’s that simple. It’s like exponential curves, they get real steep, real fast, and we’re heading into the steep part this year”.

![](https://substackcdn.com/image/fetch/$s_!NJf5!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F84c1fd5c-d230-41f2-af26-6af3b72dc3f2_1524x946.png)

My copy of Vibe Coding written by Gene Kim and Steve. Published mid-2025, it predicts “the days of coding by hand are over” on the rear cover

**One thing about being an engineer is that you can draw curves, but you never know when they end, or if they flatten. What makes you believe that this curve will continue? There’s also the question of how long they will scale for.**

**Steve:** “The world is filled with unbelievers; people who think the S curve goes up and then flattens, and that we’re at the hump stage right now. They have thought that ever since GPT-3.5 came out. They’re like, ‘it’s not going to get any better’, but then GPT-4 comes out and they think that’s as good as it gets. Now Opus 4.5 is out and most people haven’t played with it, and don’t realize what’s there. But that thing is already two months old.

The half-life between models has gone from about four months at the beginning of last year to two months from Anthropic at the beginning of this year, and we’re going to see another model from them soon, which will be so much further up the curve that people will really freak out. All the bugs, all the mistakes they’re complaining about get fed right back in as training, so it doesn’t make them next time. This is what people aren’t understanding.

Also, time continues, and there’s this inevitable collision of curves: there will be societal upheaval. It’s already started and people are justifiably mad. And I’m mad too. I’m mad at Amazon for laying off 16,000 people and blaming AI without an AI strategy. Many of those people are not going to be able to find jobs, by and large, and they’re the first of many to come. Nobody has a plan for this”.

![](https://substackcdn.com/image/fetch/$s_!DaLa!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F02fe07b1-c0cf-4991-bef3-00281d26f6fb_2048x1207.png)

Steve talking how many people will be worried when they see how capable the next model is, compared to the current one

## 2\. The “50% dial” and large cuts

**Why do you think Amazon did those layoffs if they don’t have an AI strategy?**

**Steve:** “People will hate me for saying this, and me saying it doesn’t make it true: it was true already. Every company has a dial \[of the percentage of staff they can lay off\] that they turn from zero to a hundred. It just has a default setting of what percentage of your engineers you need to get rid of in order to pay for the rest of them to have AI – because they’re all starting to spend their own salaries on tokens.

And so, at least for a while, if you want engineers to be as productive as possible, you’re going to have to get rid of half of them to make the other half maximally productive. And as it happens, half your engineers don’t want to prompt anyway and are ready to quit.

So what’s happening is that everybody on average is setting that dial to about 50%, and we’re going to lose around half the engineers from big companies, which is scary”.

**That would be more than during the Covid-19 pandemic and afterwards.**

**Steve:** “It’s going to be way bigger. It’s going to be awful. But at the same time, something else is happening, which is that AI is enabling non-programmers to write code. It’s also enabling engineers who have seen the light and believe the curves are going to continue to go up to actually get together in groups and start to do things that rival the output of big companies that are tripping over themselves.

So, we’ve got this mad rush of innovation coming up, bottom up. And we’ve got knowledge workers being laid off by big companies because clearly big businesses are not the right size anymore.

Even Andy Jassy \[Amazon’s CEO\] is saying they’re going to do the same thing with fewer people. So, does this mean we’re going to have a million times more companies? Is there going to be a massive explosion of software, or are people going to get out of software altogether and do other stuff? I’m very curious about where all this goes”.

## 3\. Eight levels of AI adoption

**Elsewhere, you’ve said something that might trigger many people, that if you use an IDE today, then you’re a bad engineer.**

**Steve:** “Well, you’ve got to be a little provocative! I’m not going to say you’re a *bad* engineer because I know some very good engineers – better than me – who are still at level one or two in my chart. But I feel sorry for people who are good engineers – or who used to be – and they use Cursor, ask it questions sometimes, review its code really carefully, and then check it in. And I’m like: ‘dude, you’re going to get fired \[because you are not keeping up with modern tools\] and you’re one of the best engineers I know!’”

**Tell us about your chart and these eight levels.**

**Steve:** “I drew it on a board in Australia for a big group of people to show what happens, as I saw them all as being at different phases. Some had their IDEs open, some had a big, wide coding agent, and others had a really narrow coding agent. I put them all on a spectrum just to show what’s going on. Here’s the levels:

- **Level 1:** no AI
- **Level 2:** Coding agent in your IDE, permissions turned on
- **Level 3:** Coding agent in IDE, “YOLO mode.” Your trust is going up.
- **Level 4:** you’re starting to not look at the diffs anymore, but at what the agent is doing. You’re not reviewing as much, you’re letting more of it through, and you’re really focused on the conversation with the agent.
- **Level 5:** your approach is: “I just want the agent and I’ll look at the code in my IDE later, but I’m not coding with my IDE”.
- **Level 6:** several agents. You’re bored because your agent’s busy and you want to do something, so you fire up another agent, then another. And you find yourself just multiplexing between them, and you can’t “leave” \[you start to get addicted to using more agents.\]
- **Level 7:** 10+ agents, managed by hand. This is where you typically say “oh gosh, I’ve made a mess! I accidentally texted the wrong agent and didn’t realize. How do I coordinate all these agents? What if Claude Code could run Claude Code?”
- **Level 8:** you build your own orchestrator to coordinate more agents”.

![](https://substackcdn.com/image/fetch/$s_!UdJX!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F3322b1f1-3617-46e1-b210-dc220d55fe05_1600x890.png)

Steve explaining his eight levels of AI usage mental model

## 4\. The Dracula effect: the drain of using AI

**One thing you’ve mentioned is that AI can really “drain” people.**

**Steve:** “There is something happening that we need to start talking about as a community. There’s a vampiric effect with AI, where it gets you excited and you work really hard, and you’re capturing a ton of value.

I find myself napping during the day, and I’m talking to friends at startups and they’re finding themselves napping during the day. We’re starting to get tired and cranky.

Companies are set up to extract value from you, and then pay you for it. The way all companies have always been set up is that they will give you more work until you break. People have to learn the art of pushing back. Let’s say an engineer can be a hundred times more productive, who gets to capture all that value? Well, if the engineer goes to work and works eight hours a day and produces a hundred times as much, the company captures all that value, and that is not a fair exchange.

There’s another group of people who are capturing all the value for themselves. They go in and work for 10 minutes a day and get a hundred times as much done, they don’t tell anyone, and they’ve captured all the value. And that’s not really ideal either, right?

I think that the answer is that each and every one of us has to learn how to say “no” real fast, and get real good at it.

I seriously think founders and company leaders and engineering leaders at all levels, all the way down to line managers, have to be aware of this and realize that you might only get three productive hours out of a person who’s vibe coding at max speed. But they’re still a hundred times as productive as they would be without AI. So, do you let them work for three hours a day? The answer is yes, or your company’s going to break \[because people get burnt out\]”.

## 5\. Big companies are doomed – but don’t know it

**With non-technical people getting into building software, could there be jobs for engineers to take over maintenance? For example, with websites you don’t need an engineer to build one because there’s Wix, WordPress, etc. But there are frontend engineers at big businesses where the website actually matters, and you want all these advanced bells and whistles. Could this be a thing with AI?**

**Steve:** “There are going to be a lot of engineers doing software engineering, and I just think we’re all going to be doing it with AI. I think it’ll be quite some time before companies are comfortable trusting their code to be written and deployed by AI without any human involvement at all. The important point that the naysayers and the skeptics are missing is that AI is *not* coming to replace your job. It’s not a replacement function. It’s an augmentation function. It’s here to make you better at your job. And that’s not a bad thing, actually”.

**Assuming AI makes engineers and teams more efficient, why don’t we see more and better software being produced? Could it be that engineering teams are focusing on building internal tools around AI, not products?**

**Steve:** “I’ll turn it around and ask whether what we’re seeing is innovation dying at large companies? What if we are only going to see innovation in small places? This is kind of what happened when the cloud came out.

Also, look at Meta. It feels like the biggest company in the world right now, but back in the day it was one dude. When a new enabling platform technology substrate appears, you’re going to see innovation at the fringes because of the innovator’s dilemma \[when successful companies fail by ignoring innovation elsewhere\]. Big companies can’t innovate. They’re all running into this problem.

Big companies may have hyper-productive engineers who are producing at a very, very high rate, but the company itself can’t absorb that work. Downstream, they’re just hitting bottlenecks and these engineers are getting shut down and they’re quitting. So, I think what’s happening is that we’re all looking at big companies going, “When are you going to give us something?” And the answer is we’re looking at big, dead companies. We just don’t know they’re dead yet”.

## 6\. Redundant values in the AI era

**What are some beliefs from your earlier career which no longer apply because of AI?**

**Steve:** “‘Engineers are special’. There’s one. Sure, we learned how to do something by hand that computers can do now. Kind of cool, I guess”.

**But what about the “engineer mindset”? It’s not just coding that we do, right?**
