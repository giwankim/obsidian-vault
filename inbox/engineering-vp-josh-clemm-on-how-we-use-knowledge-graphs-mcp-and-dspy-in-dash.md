---
title: "Engineering VP Josh Clemm on how we use knowledge graphs, MCP, and DSPy in Dash"
source: "https://dropbox.tech/machine-learning/vp-josh-clemm-knowledge-graphs-mcp-and-dspy-dash"
author:
  - "[[Josh Clemm]]"
published: 2026-01-29
created: 2026-02-19
description: "Engineering VP Josh Clemm deep-dives into how we think about knowledge graphs, indexes, MCP, and prompt optimization using tools like DSPy."
tags:
  - "clippings"
---

> [!summary]
> Dropbox VP Josh Clemm explains how Dash's context engine uses indexed retrieval, knowledge graphs, and cross-app intelligence to power enterprise search and AI answers. He discusses strategies for managing MCP at scale, using LLMs as judges for retrieval quality, and leveraging DSPy for prompt optimization.

![](https://dropbox.tech/cms/content/dam/dropbox/tech-blog/en-us/2026/january/maven/headers/Machine%20Learning-Knowledge%20Graphs%20MCP%20and%20DSPy%20with%20Josh%20Clemm-315x234-dark.png/_jcr_content/renditions/Machine%20Learning-Knowledge%20Graphs%20MCP%20and%20DSPy%20with%20Josh%20Clemm-315x234-dark.webp) ![](https://dropbox.tech/cms/content/dam/dropbox/tech-blog/en-us/2026/january/maven/headers/Machine%20Learning-Knowledge%20Graphs%20MCP%20and%20DSPy%20with%20Josh%20Clemm-1024x250-dark.png/_jcr_content/renditions/Machine%20Learning-Knowledge%20Graphs%20MCP%20and%20DSPy%20with%20Josh%20Clemm-1024x250-dark.webp)

// By Josh Clemm • Jan 28, 2026

*I was recently a guest speaker in Jason Liu’s online course on RAG offered by the education platform Maven. I did some mini deep-dives into what we’ve been doing at Dropbox with knowledge graphs; how we’re thinking about indexes, MCP, and tool calling in general; some of the work we do with LLM as a judge; and how we use prompt optimizers like DSPy. This is an edited and condensed version of my talk. Visit Maven to [watch the full video and hear my Q&A](https://maven.com/p/7d35a7/dropbox-knowledge-graphs-prompt-optimizers-and-mc-ps) with Jason and his students. — Josh Clemm, vice president of engineering for Dropbox Dash*

~ ~ ~

I don't know about you, but I probably have about 50 tabs open right now—and at least another 50 accounts for other SaaS apps. It’s completely overwhelming. It means your content is all over the place, and that makes it very, very hard to find what you're looking for. The good news is we have all these amazing LLMs coming out every day that can tell you about [quantum physics](https://x.com/drewhouston/status/1981440222484451444). But the bad news is they don’t have access to your content. All of your work content is proprietary. It's within your walled garden. It means most LLMs can’t help when it comes to your work.

That’s why we’ve been building [Dropbox Dash](https://dash.dropbox.com/). It doesn't just look at your Dropbox content. It connects to all your third-party apps and brings it into one place, so you can search, get answers, and do the agentic queries that you want to do at work.

Here’s a brief primer on our tech stack and how Dash works.

## The context engine that makes Dash possible

![](https://dropbox.tech/cms/content/dam/dropbox/tech-blog/en-us/2026/january/maven/slides/yHmKaGFo.png/_jcr_content/renditions/yHmKaGFo.webp)

First, we have our **connectors**. This is where we're building custom crawlers and connecting to all these different third-party apps. It’s not easy. Everything has its own rate limit, each has its own unique API quirks, each has its own ACL and permission system, etc. But getting that right is essential and getting all that content in one place is the goal.

Next, we're doing a lot of **content understanding** —and in certain cases, enriching the content itself. So, first we normalize a lot of the different files that come in and get it into a format like markdown. Then, we’re looking at extracting key information. We're going to be looking at titles, metadata, trying to extract links, and generate different embeddings.

For documents, this is fairly straightforward. Just grab the text, extract it, throw it in the index, and you're done. Images require media understanding. CLIP-based models are a good start, but complex images need true multimodal understanding. Then you get to PDFs, which might have text *and*  figures and more. Audio clips need to be transcribed. And then finally you get to videos. What if a client has a video like  [this very famous scene from *Jurassic Park*](https://www.youtube.com/watch?v=E8WaFvwtphY). How would you find this later? There's no dialogue, so you can't really rely on pure transcription. This is where you would need to use a multimodal model and extract certain scenes, generate understanding for each one, and then store that.

After we understand the incoming content, we take it a step further to model all these pieces of information together as a graph. Meetings may have associated documents, associated people, transcripts, or prior notes. Building that cross-app intelligence is essential to providing better context for our users. This is where we're going to start to do the knowledge graph bundle that I'll talk more about later in depth.

From there, all that information (embeddings, chunks, contextual graph representations) flows into our **highly secure data stores**. Today we use both a lexical index—using BM25—and then store everything as dense vectors in a vector store. While this allows us to do hybrid retrieval, we found BM25 was very effective on its own with some relevant signals. It’s an amazing workhorse for building out an index.

Finally, we apply multiple ranking passes on any retrieved results so they are personalized and ACL’d to you.

![](https://dropbox.tech/cms/content/dam/dropbox/tech-blog/en-us/2026/january/maven/slides/NXkT_VUD.png/_jcr_content/renditions/NXkT_VUD.webp)

Altogether, this is what we call our **context engine**. And once you have that, you can introduce APIs on top of it and [build entire products like Dash](https://dropbox.tech/machine-learning/building-dash-rag-multi-step-ai-agents-business-users).

## Why we chose index-based retrieval

Okay, but why build an index? Why did we even go down this route in the first place? Well, there's a bit of a choose-your-fighter kind of mentality in the world right now between federated retrieval and indexed retrieval. The difference is very classic software engineering. Are you going to process everything on the fly? That’s federated retrieval. Or are you going to try to pre-process it all at ingestion time? That's index-based retrieval. And there are pros and cons to each approach.

Federated retrieval is very easy to get up and running. You don't have to worry about storage costs. The data is mostly fresh. You can keep adding more MCP servers and new connectors. But there are some big-time weaknesses here. You're at the mercy of all these different APIs or MCP servers which are going to differ in speed, quality, and ranking. You’re also limited in what you can access. You can access *your* information, but you probably don’t have access to company-wide connectors—meaning you can’t access content that’s shared across the whole company. And you have to do a lot of work on-the-fly in the post-processing. Once the data comes back, you have to merge information and potentially do re-ranking. And if you're using a lot of chatbots today with MCP, you're going to see that token count go up and up. It takes a lot of tokens to reason over this amount of information.

On the flip side, with index-based retrieval, you *do* now have access to those company connectors. And because you have time on your side, you can pre-process that content and create these really interesting enriched data sets that don't exist on their own. You can also do a lot more offline ranking experiments. You can try different methods to improve your recall, and it’s very, very fast. But it's also a ton of work—and a lot of custom work. This is not for the faint of heart. You have to write a lot of custom connectors. As for ingestion time, you're going to have freshness issues if you're not good with understanding rate limits. It can also be extremely expensive to host this information, and then you have to decide how to store it. Am I using a vector database, like classic RAG from many years ago? Am I going the BM25 route? Do I want to do hybrid? Do I want to do a full graph RAG, which is what we ended up going with? There are a lot of decisions you have to make.

![](https://dropbox.tech/cms/content/dam/dropbox/tech-blog/en-us/2026/january/maven/slides/JmCHl8Y4.png/_jcr_content/renditions/JmCHl8Y4.webp)

## Making MCP work at Dropbox scale

Now what about MCP? There was a lot of hype when MCP burst onto the scene about a year ago. Everybody was talking about it: “You don't need any of these APIs anymore, you just add MCP to your agent.” Sounds great, right? But there are some major challenges with how MCP is typically implemented.

MCP tool definitions, in particular, take up [valuable real estate in your context window](https://dropbox.tech/machine-learning/how-dash-uses-context-engineering-for-smarter-ai). We’re noticing quite a bit of degradation in the effectiveness of our chat and agents (very classic context rot). So with Dash, we're trying to cap things to about 100,000 tokens. But those tool definitions do fill up quickly. The results are quite significant, especially if you're doing retrieval. You're getting a lot of content back, and you're immediately going to fill up that context window. It's going to be very problematic. It’s also incredibly slow. So, if you’re using MCP with some agents today, even a simple query can take up to 45 seconds—whereas with the raw index, you're getting all the content coming back very quickly, within seconds.

Here are some of the ways we’ve solved for that:

- We've got our index, and we can wrap that around a tool. Let's call it a super tool. And so instead of 5-10 different retrieval tools, we just have one. This helps a ton with cleaning things up overall.
- Modeling data within knowledge graphs can significantly cut our token usage as well, because you're really just getting the most relevant information for the query.
- Tool results come back with a huge amount of context, so we actually choose to store that locally. We do not put that in the LLM context window.
- Finally, we use a lot of sub-agents for very complex agentic queries, and have a classifier effectively pick the sub-agent with a much more narrow set of tools.

![](https://dropbox.tech/cms/content/dam/dropbox/tech-blog/en-us/2026/january/maven/slides/QmiszUPw.png/_jcr_content/renditions/QmiszUPw.webp)

## Our approach to knowledge graphs

The next question that comes up a lot: are knowledge graphs worth it? Well, let’s look at how a knowledge graph works.

You start by modeling these different relationships across these various apps. For example, say you've got a calendar invite. It might have attachments, meeting minutes, a transcript. Of course, it also has all the attendees, and maybe there's even a Jira project associated. Every app that we connect with has its own concept or definition of people, and so coming up with a canonical ID for who someone is is very, very impactful for us overall. Being able to model something like that is incredibly powerful. You can go view somebody's profile on Dash today, but it also helps a ton in relevance and retrieval.

![](https://dropbox.tech/cms/content/dam/dropbox/tech-blog/en-us/2026/january/maven/slides/sc791hed.png/_jcr_content/renditions/sc791hed.webp)

Say that I want to find all the past [context engineering](https://dropbox.tech/machine-learning/how-dash-uses-context-engineering-for-smarter-ai) talks from Jason. But who *is* Jason? How do you know that? Well, if you have this graph—this people model—you can then go ahead and fetch that and add that to the context, and it's not having to do a ton of different retrieval overall. Fantastic. And we use normalized discounted cumulative gain (NDCG) a lot to score the results to retrieve. But just by doing this people-based result we saw some really nice wins.

The architecture itself is complicated. I won't talk a ton here, but it's important to realize we're not just storing a one-to-one mapping of source doc to end doc. We do want to derive and create more unique characteristics. And the other key insight here is we're not storing these graphs in a graph database. We did experiment with that. The latency and query pattern were a challenge. Trying to figure out that hybrid retrieval was a challenge. And so we ended up building these graphs in a more unique way. We’re staging it more asynchronously, we're building out these relationships, and then we create these knowledge bundles. So again, it's not necessarily a graph, but think of it almost like an embedding—like a summary of that graph. And it becomes these little contexts that contain all this information. And with that context, we actually just send it on through the exact same index pipeline that we have for all the other content. So things will get chunked and things will generate embeddings for both lexical as well as semantic retrieval.

![](https://dropbox.tech/cms/content/dam/dropbox/tech-blog/en-us/2026/january/maven/slides/YxJn9XDG.png/_jcr_content/renditions/YxJn9XDG.webp)

## Using an LLM to judge relevancy

Alright, we've indexed all this content. We've got content understanding. We've done a ton of work on trying to model these relationships. But did the retrieval quality actually improve? How do we know?

Take Google search, for example. You have your 10 blue links, and the audience for those results are humans. If your results are high quality, the humans will tell you by clicking. You can quickly get some amazing signal this way. The model is either working or it isn’t.

In the world of chat, you're still retrieving results, but it's not for the human. It's for this large language model. And so you no longer have those humans to help us out. So what do you do? That's where you want to use [LLMs as a judge](https://dropbox.tech/machine-learning/practical-blueprint-evaluating-conversational-ai-at-scale-dash). Broadly speaking, what you're trying to do is judge how relevant a piece of information is between, say, one and five, and then use that to improve over time.

Humans can still help here. Sometimes they give you thumbs ups and thumbs down on the quality of your results. You can also bring in human evaluators to help you. When we started these experiments, we asked ourselves: How accurate can we get our judge to match what a human will do? And so we had a bunch of our engineers label a ton of documents to see how much of a disagreement there was between the human and the LLM as a judge. The first prompt for our judge wasn’t bad—8% disagreed—but the lower, the better.

Next, we continued to refine the prompt. You know, classic prompt tuning like “provide explanations for what you're doing.” And sure enough, disagreements went down. Then, we just upgraded the model itself to OpenAI’s o3. It's a reasoning model, far more powerful, and guess what? Disagreements with the humans went down further.

Finally, a big problem with using an LLM as a judge in a work context is that it doesn't know things like acronyms. If I were to say, “What is RAG?”—and hopefully it knows what RAG is—what if it hasn’t been trained on that? Sometimes, the judge needs to go get that context. And so, this is a little tongue-in-cheek, but we call this RAG as a judge. It can't just be using pre-computed information. Sometimes it has to go fetch some context itself. And with that, we dropped disagreements even further.

![](https://dropbox.tech/cms/content/dam/dropbox/tech-blog/en-us/2026/january/maven/slides/_6BAuy4w.png/_jcr_content/renditions/_6BAuy4w.webp)

## Prompt optimization with DSPy

There's a growing community around prompt optimizers, and one of the technologies in particular we've been using is DSPy. It helps optimize your prompts. It tries to get the most accurate information based on a set of evals. So by bringing in DSPy, we got even better results overall.

It might be impossible to get to zero disagreements. Even humans—multiple humans—will disagree on the relevance set. But we're going to keep grinding on this. And even if we can't get to zero, we're actually quite pleased with some of the results we're getting with DSPy.

One thing to note: We saw some really interesting emergent behavior happening with DSPy. Instead of simply telling us what the improvements could be, we noticed we could create bullet points with the different disagreements and then have DSPy try to optimize the bullets themselves. So if there were multiple disagreements, it would try to reduce those disagreements overall, and we started to create this really nice flywheel and ended up getting some nice results.

![](https://dropbox.tech/cms/content/dam/dropbox/tech-blog/en-us/2026/january/maven/slides/KKgSMlQW.png/_jcr_content/renditions/KKgSMlQW.webp)

There are some other benefits of DSPy. So first, obviously, is prompt optimization. It helped us quite a bit in our LLM-as-a-judge area. Again, that's a prime place to think about DSPy right now, because LLMs as a judge have very crystal clear rubrics and evals. You know exactly what the outcome should be. You just need to have the ultimate prompt, and it’s really good for that. We're going to start to experiment with DSPy across our entire stack. We have over 30 different prompts today throughout the Dash stack, whether that's in the ingest path, LLMs as a judge, some offline evals, as well as our online agentic platform approach.

The next one is prompt management at scale. I mentioned we've got about 30 prompts overall, and at any given time we might have 5 to 15 different engineers tweaking these prompts and trying to get more improvements. And it's a little silly if you think about it. You've got this text string that you've checked in to your code repository; but then there's an edge case, this chat session didn't work. So you go in and fix it, but then something else breaks, and it becomes a bit of a whack-a-mole. And so it's very powerful to just define things in a more of a programmatic way and let these tools spit out the actual prompt themselves. It just works better at scale.

And the last really great benefit we like is around model switching. So, every model out there is a bit unique. They have their own quirks, and there's always different ways to prompt them. And anytime you bring in a new model, you have to spend a bunch of time optimizing the prompt again. But with DSPy, you just plug the model in, define your goals, and out spits the prompt that works. So you can do this model switching far more rapidly—and this is really beneficial for modern agentic systems, because you just don't have one giant LLM. You're going to have a planning LLM, you're going to have all these smaller sub-agents, and those sub-agents might be very narrowly focused. You probably want to pick a model that's highly tuned to that particular task, so having something like a prompt optimizer is really powerful.

## Make it work, then make it better

To wrap things up, here are some key takeaways:

- We do find the index is superior. It is a lot of work, so don’t approach this lightly. Understand that you have to build up quite a bit of infrastructure and different data pipelines to get this working. Thinking through your data, storage, how you want to index, the retrieval—it's a lot of work, but worth it at scale.
- Cross-app intelligence absolutely does work. You want to create those relationships. You want to be able to bring in the org chart whenever you're adding different prompts. But it also isn't easy. If I knew the exact prompts everybody was going to ask 10 times a day, I would go build a more optimal bundle of that knowledge and store that, so it's very, very fast and accurate. You just don't have that benefit all the time.
- On the MCP side, we highly recommend you limit tool usage. Instead, try to think about super tools. Explore tool selection. Potentially have sub-agents with limits on tool calls. Really guard your context window.
- Investing in effective LLM judges is incredibly important. A lot of times that initial prompt is all people do. They're like, “Alright, good. Done. It's good enough.” But if you can grind that down and get the accuracy to improve, it really lifts all boats—and you're going to see some really nice outcomes across the board.
- Prompt optimizers do work at scale. They work at any scale, but they’re absolutely essential at scale.

My final, overall takeaway is the classic software engineering concept of: make it work, then make it better. A lot of the techniques and things I've described here are things that we've been doing over the last few years with a big engineering team working on this day-in and day-out. If you're just getting started, absolutely invest in those MCP tools and everything on the real-time side. And then, over time, as you start to see what your customers are doing and you start to get some more scale, look for opportunities to optimize overall.

~ ~ ~

*If building innovative products, experiences, and infrastructure excites you, come build the future with us! Visit* [*jobs.dropbox.com*](https://jobs.dropbox.com/) *to see our open roles.*

---

// Copy link

- [![Share on Linkedin](https://dropbox.tech/cms/etc.clientlibs/settings/wcm/designs/dropbox-tech-blog/clientlib-article-content/resources/linkedin.svg)](https://www.linkedin.com/shareArticle?mini=true&url=https://dropbox.tech/machine-learning/vp-josh-clemm-knowledge-graphs-mcp-and-dspy-dash&title=Engineering%20VP%20Josh%20Clemm%20on%20how%20we%20use%20knowledge%20graphs%2C%20MCP%2C%20and%20DSPy%20in%20Dash&source=https://dropbox.tech/machine-learning/vp-josh-clemm-knowledge-graphs-mcp-and-dspy-dash)
