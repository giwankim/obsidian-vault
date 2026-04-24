---
title: "Multi-agentic Software Development is a Distributed Systems Problem (AGI can't save you from it)"
source: "https://kirancodes.me/posts/log-distributed-llms.html"
author:
  - "[[Kiran Gopinathan]]"
published:
created: 2026-04-18
description:
tags:
  - "clippings"
---

> [!summary]
> Frames multi-agent LLM software development as a distributed consensus problem — agents must independently implement components that refine one consistent interpretation of an underspecified prompt — and argues distributed-systems impossibility results (FLP, Byzantine Generals) apply regardless of model capability: smarter agents can't escape the safety/liveness/fault-tolerance tradeoff, and more than (n−1)/3 misinterpretations makes consensus impossible. The actionable consequence is that external validation (tests, static analysis, verification) converts Byzantine-style misinterpretations into crash failures, which admit the weaker FLP bounds — plus giving agents `ps`-style failure detectors could unlock stronger consensus guarantees.

Recently, I've been thinking a lot about scaffolding and languages for managing systems of LLMs coordinating with each other — new programming languages might be the ideal solution for this area.

We have a rather fun paper in the works developing a fun [choreographic language](https://en.wikipedia.org/wiki/Choreographic_programming) for describing multi-agent workflows — it turns out that choreographies, while being too weak for any practical distributed protocol, are actually quite a concise and elegant formalism for describing the bespoke interactions that arise between agents, especially so if we incorporate game theory. Keep an eye out for that, we'll be sharing it soon!

Now, one annoying piece of feedback that I keep on hearing, even from other verification researchers who should know better, is a sort of *apathy* about the state of affairs, and towards the goals of developing formalisms and languages to manage agents. The common refrain is best summarised as the quote:

> **"The best solution to agentic coordination is to just wait a few months."**

The argument roughly summarises to something like:

1. Current multi-agentic LLM systems are unable to build large-scale software autonomously (*agreed ✅*).
2. This boils down to an issue of coordination (*agreed ✅*).
3. The next generation of models will be smarter (*agreed ✅*).
4. **The next generation of models will not have coordination problems** (⁇ HUH ⁇).

The main implication is that building languages and tooling to describe and manage these systems is a sisyphean task; newer models will inevitably render them obsolete, and the entire effort will be in vain.

As a verification researcher I find this capitulation a little premature and misguided: there's a rich literature of distributed systems literature, *literally about this very problem*, that people are ignoring, and a number of impossibility results that are invariant to model capability. Even if the next models are AGI (lol), the problem of coordination is a *fundamental* one, and smarter agents alone can't escape it.

In this blog post, I want to flesh out this idea, and break down the problem of multi-agent software development into a formal model and establish some connections to some standard distributed systems impossibility results. Distributed consensus is difficult, no matter how AGI your participants are.

### A Formal Model of Software Development

> Claude. Make me an app to track recipes. *Make no mistakes.*

We can model the problem of multi-agent synthesis formally as follows:

Given a prompt $P :=$ " $\textit{An app to track recipes}$ ", we can define the formula $\Phi \left(\right. P \left.\right)$ as the set of software consistent with the prompt:

$$
\Phi \left(\right. P \left.\right) := \left{\right. \phi \left|\right. \phi \text{program} \land \phi \text{is consistent with the prompt} P \left.\right}
$$

The key point here is that a natural language prompt, by its very nature, is *underspecified* — i.e there may be multiple programs that are consistent with the prompt. When we use LLMs to build and write software systems, we're effectively asking the LLMs to select one element amongst many from this set.

Conversely, when we do multi-agentic software development, i.e we spin up several agents, $A_{1} , \hdots , A_{n}$, and ask them to build a piece of software, we're essentially asking them each to produce software components $\phi_{1} , \hdots , \phi_{n}$ such that they all refine one single consistent interpretation of the prompt:

$$
C \left(\right. \phi_{1} , \hdots , \phi_{n} \left.\right) := \exists \phi \in \Phi \left(\right. P \left.\right) , \forall i , \phi_{i} \text{refines} \phi
$$

This in other words, is nothing other than one big distributed consensus problem.

![agentic-coordination.svg](https://kirancodes.me/images/agentic-coordination.svg)

In other words, the user's prompt $P$ first gets sent split, via a plan, into tasks for several agents $a_{1} , \hdots , a_{n}$. Then, these agents work in parallel to implement their respective coding tasks $\phi_{1} , \hdots , \phi_{n}$, and by the end, if the synthesis was successful, we're hoping that the final generated software system $\phi$ composed of each of the individual constructions $\phi := \phi_{1} \left|\right. \left|\right. \hdots \left|\right. \left|\right. \phi_{n}$, satisfies the user's request.

This is inherently a consensus problem as the agents $a_{1} , \hdots , a_{n}$ must work concurrently to produce their software artefacts $\phi_{1} , \hdots , \phi_{n}$, but communicate and agree enough that the final piece of software $\phi_{1} \left|\right. \left|\right. \hdots \left|\right. \left|\right. \phi_{n}$ is well formed and satisfies the request. Design decisions or choices in one $\phi_{i}$ will result in constraints that affect and influence the possible choices of $\phi_{j}$ for other agents. For example, if the agent in charge of implementing network connections $a_{\text{network}}$ chooses a library with a callback-style async API for requests, then whichever agent is responsible for the overall integration $a_{\text{integration}}$ must organise the infrastructure around that choice and so on and so forth. Similar choices in other modules will influence the design spaces of other agents and overall the process proceeds as a joint synthesis problem.

### Is this really a Distributed Consensus Problem?

As we complete our formal model of agentic software development, at this point, I'd like to also take a second to shoot down some obvious rebuttals.

1. **Why is $P$ underspecified (i.e. can't $\parallel \Phi \left(\right. P \left.\right) \parallel = 1$)?** This holds by the very nature of natural language as being ambiguous. As it turns out, we do have a way to give a precise and unambiguous specifications for software. It's called a programming language. Anything else leaves room for the agent to make design decisions. Another way of viewing this is that we could spend some time refining our initial prompt to make it less underspecified, but unless we go all the way to code (at which point, you're not using multiple agents, just one), there's going to be some degree of ambiguity to our prompt.
2. **Is the problem inherently concurrent?** The motivations for throwing multiple agents at a software system are somewhat outside the scope of this post, but as soon as we have made that decision and we have multiple agents working on our tasks, then the problem is inherently concurrent (irrespective of whether they're working in parallel, or interleaved on a single thread), and we have to solve problems of coordination.
3. **Can't we have a single supervisor to dictate choices?** Why not have agents make proposals in parallel and then have some kind of supervisor which manages merging PRs into the shared codebase? Nice try! A git repo is a pretty standard approach to trying to coordinate parallel software development, but you haven't solved the fundamental concurrency problem, at best you've hard-coded yourself into a single choice of concurrency, and not a particularly good one: when one design decision is chosen and merged into the codebase, what happens to work that must be rebased? what if it has conflicts? Some work has to be lost.

The key point that I'm trying to convey here is not that you can't *sometimes* do multi-agentic software development while ignoring the concurrency problem – evidently people have had [some success](https://www.anthropic.com/engineering/building-c-compiler) at software development with agents without pulling out Paxos — but rather that this perspective helps us be prescient about how we are resolving these fundamental concurrency problems with our coordination workflows. Now, if you take me out for a few drinks, maybe I'd go even further to say that if we want multi-agentic software development to truly scale, then these questions **have** to be thought about and answered carefully.

### Impossibility Results for Multi-agentic Software Development

Now we have this formal model of agentic software development, it's time for the payoff of this blog post! Let's draw some connections to distributed systems and try and sketch out some impossibility results.

#### FLP for multi-agentic systems (Safety, Liveness, Fault Tolerance, pick two)

Of course, where else could we start but with FLP, oh my dear FLP. Fischer, Lynch and Paterson's seminal paper ["Impossibility of Distributed Consensus with One Faulty Process"](https://groups.csail.mit.edu/tds/papers/Lynch/jacm85.pdf) establishes a fundamental impossibility result dictating consensus in any asynchronous distributed system (yes! that includes us).

> **FLP Theorem (Fischer et al., 1985):** In *any* distributed system with arbitrary delays on messages and the possibility of at least 1 node crash failure, no deterministic protocol can ensure all non-faulty nodes reach consensus in bounded time.

Before we break down the implications of this theorem, I'd like to take a bit to argue that the assumptions of FLP (asynchronous messages, crash failure) do apply to our protocol:

1. **Asynchronous Messages** - Delivery of messages to LLMs are often asynchronous. LLMs are usually responsible for determining when messages are read, and they can defer this arbitrarily long. However one LLM agent tries to send a message to another, whether that be through a shared file system, through some message passing queue or any other scaffolding, the point when this message will be seen by the other will usually be determined by the other LLM - when it finishes its reasoning trace, or when the programs or tools it is calling have finished. Overall we can't place a bound on message delivery.
2. **Crash failure** - This one requires less justification, but agents are pretty eager to shoot themselves in the foot. Crash failure in this context doesn't just mean something like the process itself dying, but could also be something like the agent running a tool which never terminates (i.e. a bash script with an accidental loop etc.). Other times they might just `pkill` themselves. Overall, agents may crash unannounced.

Now, what does that mean for us? in particular, it means that in any multi-agentic system, irrespective of how smart the agents are, they will never be able to guarantee that they are able to do both at the same time:

- **Be Safe** - i.e produce well formed software satisfying the user's specification.
- **Be Live** - i.e always reach consensus on the final software module.

You may be surprised at the liveness part of this, as agents always seem to make progress and terminate in most workflows, but this doesn't mean that they reach consensus — in fact, a very common pattern that I see is a sort of looping, going back and forth on design decisions where one agent picks one design decision, another one reverts the change, picks another decision, and then they loop.

Another interesting insight from this perspective is the observation that when we have agents running on a shared machine, we might be able to do a little better than the pure crash failure fault model — in particular, running commands like `ps | grep claude` etc. could correspond to something akin to a **failure detector** from which we can obtain stronger bounds on consensus. In particular, the paper ["Unreliable Failure Detectors for Reliable Distributed Systems"](https://www.cs.utexas.edu/~lorenzo/corsi/cs380d/papers/p225-chandra.pdf) by Chandra and Toueg built on top of FLP and proved that consensus *was possible* in the FLP setting **iff** agents were allowed access to a failure detector gadget (possibly unreliable) which reports whether other agents are still alive. If agents correspond to processes, and the process being alive is equivalent to progress (this is not necessarily always the case [^1]), then `ps` might give us something like that. One takeaway from this thus might be to give LLMs a tool to check the liveness of other agents.

#### The Byzantine Generals Problem for Multi-Agentic Software Development

The second impossibility result I'd like to sketch a connection to is a little more subtle, but still useful to think about: Lamport's ["The Byzantine Generals Problem"](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/12/The-Byzantine-Generals-Problem.pdf).

In a distributed system, a **byzantine node** is a modelling notion that corresponds to the worst-case assumption of failure for a participant; while theorems like FLP assume that when a server fails it crashes and stops participating in the protocol, byzantine nodes may do that, or they may do *anything*, that is they may deviate from the protocol in arbitrary ways, such as faking messages from other users, sending messages to participants it was not meant to, or repeating prior messages as a few examples.

Are byzantine failure modes really relevant for multi-agentic software development? While this failure model is a little conservative — surely our agents won't be actively trying to break our system — I think this model is still useful to think about in our setting because byzantine failures seem like a good way to capture the idea of "misinterpretations" of our input prompt. An agent that misunderstands the prompt can, for all intents and purposes, be considered as a byzantine agent in the protocol, actively working against the other participants trying to produce a correct software system. In the presence of such agents, can we still achieve consensus?

> **Byzantine Generals Theorem (Lamport-Shostak-Pease, 1982)**: In any synchronous message-passing system with $f$ Byzantine agents that may deviate from the protocol arbitrarily, agreement among honest processes is achievable only if the total number of processes $n > 3 f + 1$.

So concretely, with this interpretation, if we spin up $n$ agents to implement our software system, if more than $\frac{n - 1}{3}$ agents misunderstand the prompt then consensus is impossible. In the paper Lamport proposes an algorithm for this setting, which at a high level involves collecting votes from all the participants and taking the majority. Ensemble voting in our setting is more of a theoretical construction and a place where our analogy starts to break a little — the space of software implementation is large enough that voting is unlikely to make much progress — but there are still some useful insights we can take from this impossibility result.

The key observation here is that Lamport's result is a hard bound on the maximum number of misinterpretations we can tolerate for software development to actually be possible. This isn't something that will be solved by smarter agents or better LLMs. Our synthesis problem is inherently underspecified, and agents thus may always have misinterpretations. One actionable takeaway from this analysis is that while we can't improve the amount of misinterpretations $f$ we can tolerate, we can increase the likelihood of success by adopting techniques for *reducing* the number of misinterpretations — in particular, external validation mechanisms such as tests, static analysis and verification effectively convert misinterpretations into crash failures — instead of proceeding with a misinterpretation of the natural language description, the agent can crash, or refine its interpretation to match the tests, from which we can reuse the weaker FLP results.

[^1]: This doesn't fully capture whether agents are actually alive and making progress, as a coarse grained process view can not capture failure modes such as agents hanging in an infinite tool call, or agents who have been derailed and have stopped working on the codebase entirely.

[^2]: I haven't spent too much time thinking about the bridge to our setting, but at a high level I'd say that for agentic software development, partition tolerance might not be a requirement.
