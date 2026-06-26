---
title: "Running an Engineering Papers Reading Guild at Zalando"
source: "https://engineering.zalando.com/posts/2026/01/running-an-engineering-papers-reading-guild-at-zalando.html"
author:
  - "[[Danilo Veljovic]]"
published: 2026-01-29
created: 2026-03-25
description: "In September 2024, we started an Engineering Papers guild at Zalando to read and discuss research papers together. A year later, we reflect on our journey and share insights on organising and..."
tags:
  - "clippings"
  - "career-growth"
  - "engineering-management"
  - "distributed-systems"
---

> [!summary]
> Zalando engineers share how they built a monthly paper-reading guild from scratch, covering paper selection strategies, format evolution, marketing, and tangible impacts like teams applying DynamoDB internals knowledge to fix production partition issues. Includes a practical blueprint for starting similar groups in your organization.

In September 2024 a friendly message in our internal Java guild chat led to the formation of the Engineering Papers guild born out of sheer curiosity and excitement about reading and discussing papers together.

![Chat screenshot of the initial message that led to the formation of the guild](https://img01.ztat.net/engineering-blog/posts/2026/01/images/conversation.jpg?imwidth=1320)

The Engineering Papers guild at Zalando recently celebrated its first anniversary as we completed one year of monthly in-person meetups - a big feat for the group! Throughout the year we have evolved and improved gradually to make the meetups more engaging and valuable for everyone who attends while learning a lot ourselves on the way. Today, we want to share how the journey has been and celebrate one year of papers, discussions and valuable insights which may come in handy for you if you are deciding to start such a group within your organisation.

## Why we wanted to read academic papers

[This StackOverflow article](https://stackoverflow.blog/2022/12/30/you-should-be-reading-academic-computer-science-papers/) groups reasons to read papers into three categories:

*“surveying history, the future of programming and the map of giants’ shoulders”*

For us, the primary motivation was to peek under the hood of abstraction in software. We work with several tools at work - web frameworks like Node.js, runtimes like JVM, databases like Postgres and DynamoDB, platforms like Kubernetes - all of which abstract a set of features implemented using lower-level primitives and in turn enable developers to build higher levels of abstraction.

Papers from early days of the Internet are special in a way. They often talk about technologies and tools that have become foundations of modern day computing. Take [Time, Clocks and the Ordering of Events in Distributed Systems](https://lamport.azurewebsites.net/pubs/time-clocks.pdf) - a seminal paper in which Lamport shared how we can make sense of time and ordering in distributed systems. Ideas from this paper have influenced for example how multiple replicas in a database system communicate with each other to maintain data consistency.

## Organising an internal paper-reading meetup

At Zalando, *guilds* are communities of interests around a certain topic. We have guilds for many interests ranging from technology-focused topics like Java, Web, Data Engineering, LLMs, SRE to several non-tech groups like pet owners, photography, and music. The obvious next step for us was to create a guild for us: #guild-engineering-papers.

We wanted to run this guild in a sustainable way that keeps people interested and engaged and makes them derive most value from attending the meetings. We had a genuine interest in reading papers, so we would keep reading them even if the guild never existed. The reason to have a guild was to leverage the pool of high quality engineers across Zalando and discuss the papers with them, so that we could learn new techniques and potentially apply them to our daily work.

Of course, running a niche guild in a large company is a challenge and it doesn’t come without its fair share of mistakes. Our plan was simple: take the best papers in the realm of distributed systems, databases and compilers, and discuss them within the group. The discussions would have a driver who would prepare and present (and essentially drive the conversation), and to set the momentum, we as co-organisers would be the drivers as well.

One of the initial papers we selected to cover was the [DynamoDB paper](https://www.usenix.org/system/files/atc22-elhemali.pdf). It was relatively recent and relevant within Zalando where a lot of teams use DynamoDB, and we were confident that we would have high attendance. We created posters, wrote in the global tech channel and announced the topic in the guild channel - all excited to host the meetup. The day arrived and to our surprise we only had one attendee.

Well, we realised the importance of marketing for a meetup. If no one knew about what you are organising, then no one would show up. For next meetups, we put all viable mechanisms to market the event to use - starting from eye-catching colorful posters put up across the office building to the company-wide tech newsletter, all mechanisms were utilized and this worked very well!

![Guild meetup in action](https://img01.ztat.net/engineering-blog/posts/2026/01/images/session-in-action.jpeg?imwidth=1320)

Guild meetup in action

## Evolving the format

As the guild was created out of our sheer interest to read papers, we were quite eager to discuss as many interesting topics as possible in our meetups. We started with two papers in a 90 minute session, taking one per organiser and on a monthly cadence. We soon realised that this was not scalable: we as organisers would have to prepare the presentations in about three weeks for each meetup, and a session would be jam packed with topics related to (usually) two completely different papers.

In the session where we discussed the DynamoDB paper, we also covered the [Raft paper](https://raft.github.io/raft.pdf). It is an extremely interesting read for anyone wanting to understand distributed consensus algorithms and cannot make sense of algorithms like Paxos. In a session with two such information-dense papers, it was hard for the attendees to keep up with the discussion. We soon decided to move to a one-paper-per-session format to ensure that the discussions are rich and focused.

### Selecting papers

**Content sweet spot = Relevance + Interest**

This is usually a tricky topic and you should aim to balance “bringing in value” (a.k.a. *relevance*) and “interests” for the attendees. In one of the sessions we discussed [Overlapping Experiment Infrastructure: More, Better, Faster Experimentation](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/36500.pdf) as it is a foundation for an internal experimentation solution and contained valuable insights for anyone wanting to work with the product by looking under the hood. Along with talking about the particular solution, the paper also generally describes how experimentation systems work which is a great learning.

Similarly, [On Designing and Deploying Internet-Scale Services](https://s3.amazonaws.com/systemsandpapers/papers/hamilton.pdf) is a goldmine for running and maintaining software systems at scale. Ideas shared in this paper were super relevant for everyone who attended and for Zalando.

On the other hand, we also discussed papers like [Prequal](https://arxiv.org/pdf/2312.10172) and [Building a Database on S3](https://people.csail.mit.edu/kraska/pub/sigmod08-s3.pdf) - topics which are purely interesting and can potentially inspire builders at Zalando to apply learnings to their systems.

More recently, as the momentum has set in, we were happy to receive our first community proposal for a paper presentation! One of our regular attendees presented [MLIR: A Compiler Infrastructure for the End of Moore’s Law](https://arxiv.org/pdf/2002.11054) - the paper introducing MLIR, a superset of LLVM-like tooling to work with multiple levels of intermediate representations in compilers. We want to encourage more such voluntary submissions so that the guild becomes community-driven and more diverse with respect to topics.

## Quantifying impact

We see the impact of a meetup like ours materialising in two ways. While investing time into reading academic research papers has a long-term impact, we do want to share the tangible outcomes we realised through our regular meetups.

### System internals and application at work

Our regular attendees shared that with papers like [DynamoDB](https://www.usenix.org/system/files/atc22-elhemali.pdf), they could better understand the underlying implementations and working of systems they used everyday in production. Understanding DynamoDB's internal architecture through the meetup helped a team at Zalando to understand why DynamoDB writes kept failing despite adequate provisioned capacity. They realised their data was concentrated on specific partitions that had exhausted their burst capacity, leading them to redesign their partition key strategy for better load distribution.

Similarly, [Distributed Snapshots: Determining Global States of Distributed Systems](https://lamport.azurewebsites.net/pubs/chandy.pdf) helped a team understand [Apache Flink](https://flink.apache.org/) 's checkpointing mechanisms.

### Engineering culture and exchange of ideas

The guild meetups often see rich technical discussions that bring perspectives from different parts of the organisation as we see participation from departments all around the company. Attendees bring in varying experiences and the guild provides a platform for everyone looking to learn and share.

While discussing [A Simplified Architecture for Fast, Adaptive Compilation and Execution of SQL Queries](https://bigdata.uni-saarland.de/publications/Haffner,%20Dittrich%20-%20A%20Simplified%20Architecture%20for%20Fast,%20Adaptive%20Compilation%20and%20Execution%20of%20SQL%20Queries%20@EDBT2023.pdf), which discusses a LLVM and WebAssembly-based compilation architecture for SQL queries, attendees shared how some engineering teams at Zalando were experimenting with WebAssembly as a cross-platform target. This discussion provided insight for the attendees into how technologies they did not primarily use in their teams could benefit their goals.

## Blueprint for organising this yourself

With our learnings from 2025, we put the following *blueprint* together for anyone who wants to/is interested in running such a group in their organisations/institutions. We believe such a group greatly benefits in building a strong engineering culture and benefits both the attendees and the organisation.

*Fundamentals*:

- **Two or more organisers** - doing this solo will definitely wear you out and affect the quality of the meetup.
- **Interest in reading papers and continuous learning** - for a significant period of time initially you as organisers will have to drive the group, your interest and motivation will push the group through its initial days.

*Choosing what to read*:

- **Combine relevance and interests** - bring in topics that interest you and may also be relevant to the organisation or the attendees. For us, distributed systems, databases and compilers were a good fit.
- **Mix classics with cutting edge research** - a historical perspective enriches ideas about present developments.

*Cadence and logistics*:

- **Start easy, once a month** - With at least two organisers, one session with one paper discussion per month would give enough time for you to prepare if you alternate responsibilities. A paper per session also allows focused discussion.
- **Market your meetup** - We cannot stress this enough. Let people know that you are organising this, you will be pleasantly surprised how many are really interested. Use various channels (chat groups, internal social media, physical posters in office, common newsletters) to share about the next meetup. Having a significant audience creates a nice feedback loop and motivates you to put in the effort.

*Engaging the community*:

- **Use a lot of examples** - breaking down concepts in a paper via examples was a great way for us to share what we learned. E.g., in the Raft paper we went as far as implementing the algorithm in Node.js to see it in action.
- **Ask for feedback** - The group is community-driven and feedback is very important. We tried both formal and informal ways to gather feedback and both were helpful.
- **Create an inclusive environment** - All of us are learning in the group and creating an environment where everyone can discuss and ask questions is crucial. This also encourages community participation and gradually having presenters other than the organisers.
- **In-person meetups make a difference** - In-person gathering helps in enaging with all the attendees better and makes it more like a discussion than a *webinar*. We value seeing each other in person once a month and you may want to try this too if your team setup permits it.

## What’s next

In total, we discussed 13 papers throughout the year in the guild. That’s a significant number, considering this was a self-organised effort! We celebrated the completion of 1 year of the guild with a special anniversary edition which was a more relaxed meetup. We had donuts, discussed some interesting events at scale (Cyber Week flavored) and some popular Internet bugs of the past.

We want to continue organising guild meetups and explore interesting topics in systems and how they can be applied at Zalando. If this post encourages you to pick up a paper to read or organise a similar group, hurray! Happy reading!

---

*Other than the papers mentioned in the post, we discussed the following:*

1. [Local-First Software: You Own Your Data, in spite of the Cloud](https://martin.kleppmann.com/papers/local-first.pdf)
2. [Spanner: Google’s Globally-Distributed Database](https://static.googleusercontent.com/media/research.google.com/en//archive/spanner-osdi2012.pdf)
3. [An Execution Model for Serverless Functions at the Edge](https://sites.cc.gatech.edu/projects/up/publications/iotdi19-AdamHall.pdf)
4. [Google's Chubby: lock service for loosely-coupled distributed systems](https://static.googleusercontent.com/media/research.google.com/en//archive/chubby-osdi06.pdf)

---

*We're hiring! Do you like working in an ever evolving organization such as Zalando? Consider joining our teams as a [Software Engineer](https://jobs.zalando.com/en/jobs?category=Software+Engineering+-+Backend&category=Software+Engineering+-+Data&category=Software+Engineering+-+Frontend&category=Software+Engineering+-+Full+Stack&category=Software+Engineering+-+Leadership&category=Software+Engineering+-+Machine+Learning&category=Software+Engineering+-+Mobile&category=Software+Engineering+-+Principal+Engineering&utm_source=eng_blog&utm_content=running-an-engineering-papers-)!*

---

## Related posts

## Adapting to Change: Returning to Work in a Fast-Moving Tech World

This article discusses the challenges of returning to work in a fast-paced tech environment and how to navigate them. [Read more...](https://engineering.zalando.com/posts/2025/05/adapting-to-change.html)

## Failing to Auto Scale Elasticsearch in Kubernetes

A story of operational failure in large scale Elastisearch installation including the root cause analysis and... [Read more...](https://engineering.zalando.com/posts/2024/06/failing-to-auto-scale-elasticsearch-in-kubernetes.html)

## Hosting an internal Engineering Conference

In August 2023 we hosted our first internal Engineering Conference. This post summarizes the experience and provides... [Read more...](https://engineering.zalando.com/posts/2024/06/hosting-an-internal-engineering-conference.html)
