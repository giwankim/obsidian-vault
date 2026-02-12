---
title: "What Functional Programmers Get Wrong About Systems"
source: "https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/"
author:
  - "[[Ian Duncan]]"
published: 2026-02-09
created: 2026-02-11
description: "Type systems verify properties of programs. Production correctness is a property of systems. The gap between these is where the interesting failures live."
tags:
  - "clippings"
---
Static types, algebraic data types, making illegal states unrepresentable: the functional programming tradition has developed extraordinary tools for reasoning about *programs*. I have spent over a decade writing Haskell professionally, and I believe in all of it.

But the very effectiveness of these tools creates a particular susceptibility. We sometimes mistake reasoning about programs for reasoning about *systems*. These are not the same activity, and the instincts that make you good at one do not automatically transfer to the other.

This is not a uniquely FP problem. Every programming community treats “the program” as its primary object of study. But FP practitioners are in a distinctive position: our tools for local correctness are powerful enough to foster an unwarranted confidence about system-level properties. The type checker is honest about what it checks. The trouble starts when we forget where its jurisdiction ends. Every language community has its own version of this forgetting; the FP community just has the most sophisticated reason to believe it’s unnecessary.

A caveat before we go further: this essay is grounded in the world of web services, service-oriented architectures, and the distributed systems that inevitably emerge from them. If you’re building video games, CLI tools, or embedded firmware, the version boundaries look different and much of this won’t apply. But if you ship code that talks to other code across a network, and especially if you’ve ever had to deploy a change without taking the whole system down at once, this is for you.

The good news is that the research community has been quietly assembling the tools we need, if you know where to look.

## Your monolith is a distributed system

Before we talk about types, I want to establish something that I find myself arguing repeatedly: **every production system is a distributed system**, including your monolith.

If you have a web application with more than one server, you have a distributed system. If you have background job workers, you have a distributed system. If you have a cron job, you have a distributed system. If you talk to Stripe, or send emails through SendGrid, or enqueue something in Redis, or write to a Postgres replica, then you are (I regret to inform you) operating a distributed system. The word “monolith” describes your deployment artifact. It does not describe your runtime topology.

This matters because the interesting correctness problems in production are almost always *systemic* rather than *local*. They live in the interactions between components running different versions of your code, or operating on different assumptions about the state of the database, or retrying an operation that already partially succeeded somewhere else. These are not problems that any single-program analysis can catch, regardless of how sophisticated your type system is.

Most programming language communities (FP included) tend to treat “the program” as the object of study. We write papers about programs. We verify programs. We optimize programs. But in production, correctness is not a property of a program. It is a property of a system. And once you see this clearly, some of the most cherished practices across our industry start to look like they’re aimed at the wrong altitude.

## The unit of correctness is the set of deployments

Here is the central claim: **the unit of correctness in production is not the program. It is the set of deployments.**

When the Haskell compiler tells you your program is well-typed, it has verified properties of a single artifact. One binary, one version, one coherent snapshot of your types and your logic. This is genuinely valuable. But in production, that artifact is one member of an ensemble. At any given moment, your system might be running:

- The current deploy, serving new requests
- The previous deploy, still draining connections
- Background job workers that are one, two, or three deploys behind
- A database whose schema has been migrated forward
- Serialized data on a Kafka topic or in a job queue, written by a version of the code that no longer exists
- Third-party webhook handlers that will deliver payloads conforming to *their* schema, not yours

Correctness is a property of this entire set simultaneously. The type checker verified one element. It told you nothing about the interactions between elements. And the interactions are where the bugs live.

This is not an original observation. Google discovered it the hard way with their F1 database, which led to one of the most important papers in the schema evolution literature.<sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-1">1</a></sup> Their insight was that if servers can be at most two schema versions apart at any time, then dangerous schema changes can be decomposed into a sequence of intermediate states, each pairwise compatible with its neighbors. They found two subtle bugs in production systems using this framework: bugs that existed precisely because the system had been reasoning about schemas one version at a time.

## Multiple versions are always running

Programming language culture treats a program as a single thing. You write it, you compile it, you deploy it. The old version ceases to exist and the new version takes its place. The type system operates on this model. The module system operates on it. Your mental model of “the code” operates on it.

In production, this is a polite fiction.

In any non-trivial deployment, multiple versions of your code are running simultaneously. A rolling deploy means that for some window (seconds, minutes, sometimes hours) both old and new versions are live, serving the same users, blissfully unaware of each other. A blue-green deploy means both exist and traffic could be routed to either. Canary deploys mean both are serving real users, right now, at the same time.

Consider a sum type:

```haskell
data PaymentStatus

  = Pending

  | Completed

  | Failed
```

You ship a new version that adds a constructor:

```haskell
data PaymentStatus

  = Pending

  | Completed

  | Failed

  | Refunded
```

For the next however-many minutes, old workers will receive messages or database rows containing `Refunded` and they won’t know what to do. If you’re serializing to JSON, the old code sees an unrecognized string and throws a parse error. The type checker didn’t warn you about this, because the type checker only sees one version at a time. This is true regardless of language; the Haskell example just makes the irony sharpest, because the exhaustive pattern match that felt like an ironclad guarantee turns out to be a guarantee about a world that no longer exists.

This is why Protocol Buffers uses numeric field tags rather than field names on the wire, and why Avro requires both the writer’s and reader’s schema to be present at deserialization time.<sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-2">2</a></sup> These aren’t quirks. They are engineering responses to the fundamental reality that producers and consumers will be at different versions. The serialization format is doing the work that the type system cannot: reasoning about compatibility across time.

Rolling Deploy Watch versions coexist

web-1

v1

running

web-2

v1

running

worker-1

v1

running

Erlang/OTP is the one mainstream platform that took this problem seriously at the language level, and it is worth pausing to appreciate what they did. The BEAM VM supports running **exactly two versions of a module simultaneously** during hot upgrades. When you load a new version, processes running the old code continue until they make an external call, at which point they transition. The `code_change/3` callback in OTP’s `gen_server` is an explicit hook for migrating process state between versions: you receive the old state, the old version identifier, and you return the new state. The state migration is a first-class part of the programming model, not an afterthought discovered during an incident.

The two-version limit is the critical design choice. It means the mixed-version state space is bounded: you only ever need to reason about compatibility between adjacent versions, not arbitrary pairs. If you try to load a third version while processes are still running the first, BEAM kills those processes. This is strict, but it makes the problem tractable. Google’s F1 independently arrived at the same constraint for schema migrations. Most modern deployment systems have rediscovered it without naming it; a rolling deploy that completes before the next one starts gives you a two-version window almost by accident, which is perhaps the nicest kind of safety property: the one you get without having to think about it.<sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-3">3</a></sup>

## The migration ratchet

If multiple versions running concurrently is the normal case, the relationship between code and data is what makes it genuinely treacherous.

You can roll code back relatively easily: redeploy the old artifact. You cannot easily roll back `ALTER TABLE ADD COLUMN`, and you absolutely cannot roll back `DROP COLUMN`. The data layer moves forward on a ratchet. The code layer appears to move in both directions, but a rollback creates a combination (old code, new schema) that never existed as a commit in your repository. Nobody compiled it. Nobody tested it. No type checker ever saw it.

I am an always-roll-forward partisan, and this asymmetry is why. A rollback gives you the *feeling* of a safety net, but the state it produces is one you have never verified and are unlikely to have even considered. Better to move forward through the problem with a fix than to retreat into an untested configuration. The expand-and-contract pattern (add the new column as nullable, deploy code that writes to both, backfill, deploy code that reads from the new column, drop the old one) requires a minimum of four deploys to accomplish what *feels* like one change. It is not just a recipe. It is a discipline of only ever occupying states that have been deliberately constructed and tested.

The Migration Ratchet Try rolling back after a schema change

CODE

v1

3 columns

↕ can roll back

reads/writes

SCHEMA

schema v1

id

name

email

→ forward only

Code and schema are aligned at v1.

The research community has a name for the general problem, from an unexpected direction. The Dynamic Software Updating (DSU) literature studies the safety of transitioning between program versions at runtime. Gupta, Jalote, and Barua proved in 1996 that **the general problem of update validity is undecidable**: you cannot build a tool that will tell you, for all possible programs and updates, whether a transition is safe.<sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-4">4</a></sup> This is a sobering result. It does not mean we give up. It means progress has to be domain-specific and heuristic, which is exactly what practical tools like Atlas’s migration linter and `gh-ost` do.

The expand-and-contract pattern itself turns out to be an operational implementation of what the database theory community calls **bidirectional schema transformation**.<sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-5">5</a></sup> The theory was published in 2017. Most of us had been doing it by hand for years before that, arriving at the same structure through trial and error and 3am incident retrospectives. The academy and the industry converged on the same answer from opposite directions, neither aware of the other.

## Message queues are version time capsules

Databases at least let you migrate data in place. Message queues are more patient.

Not all queues are patient in the same way. RabbitMQ and Sidekiq typically process messages within seconds or minutes (sometimes faster than you can alt-tab to the monitoring dashboard); the version window is narrow, roughly the duration of a rolling deploy. If your consumer is one deploy behind for ten minutes, that’s the extent of your compatibility obligation. These systems are forgiving precisely because messages don’t linger. The version problem exists, but it’s bounded by the same two-version window as the deploy itself.

Kafka is a different animal. A Kafka topic with a 30-day retention policy contains messages from 30 days of deploys. If you deploy daily, that’s 30 versions of your serialization format, coexisting on the same topic. A consumer spinning up today needs to be able to deserialize all of them. If you’re using Kafka as an event store with infinite retention (and some teams do) you might have messages from *years* ago, written by code that no longer exists in any branch of your repository, by engineers who no longer work at the company. The messages persist. They are very patient.

This is where the F1/Erlang “two versions apart” assumption breaks down entirely. You aren’t dealing with a bounded version window. You’re dealing with an unbounded archaeological record of every serialization format your system has ever used.

The practical responses are well-known: use a serialization format with strong backward compatibility guarantees (Protobuf’s wire format is explicitly designed to be stable across major versions), enforce compatibility at write time via a schema registry, and have explicit retention policies that bound how far back you need to be compatible. But many teams treat topic retention as a storage cost decision rather than a compatibility decision, and that’s a mistake. **Your retention policy is a version compatibility policy.** Thirty days of retention means “every deploy must be compatible with the serialization format from 30 days ago.” Infinite retention means “every deploy must be compatible with every serialization format, ever.” These are very different engineering constraints, and they should be chosen deliberately.

The same problem appears anywhere you write data that might be read back by a different version of the code: S3 buckets, cached values in Redis, scheduled job payloads. Anywhere you serialize, you leave a fossil record that future versions will need to interpret. The question is just how long the fossils stick around.

Message Queue Time Capsule Adjust retention to see the compatibility window

60d ago now

↑ retention start

Retention:30d

v4

v5

v6

30-day retention = 3 schema versions your consumer must handle.

## Event sourcing: the version problem as a way of life

If message queues are version time capsules, event sourcing systems have taken the version problem and elevated it to a first principle.

The promise of event sourcing appeals to the same instincts that draw people to functional programming: your application state is not a mutable thing in a database. It is the result of a left fold over an ordered sequence of immutable events. The events are facts. They happened. You can derive any view of your data by replaying them through a projection function. State is a pure function of history.

This is a beautiful idea, and it has a terrifying corollary: **every event you have ever written must be interpretable by your current code, forever.**

In a traditional system, you can migrate your data in place. `ALTER TABLE`, backfill, move on. The old representation is gone. In an event-sourced system, the old representation *is the point*. The event log is append-only by definition. You cannot rewrite a `PaymentInitiated` event from 2019 to match your 2026 schema, because that would be lying about what happened. The immutability of the log is the entire value proposition. It means that every version of every event schema your system has ever used is a permanent part of your codebase’s obligations, whether or not anyone *remembers* writing it.

The standard response is **upcasting**: transforming old events into the current schema at read time. When your projection encounters a v1 `PaymentInitiated` event, it runs it through an upcaster that produces something your current code can process. This is Cambria’s edit lenses, arrived at independently by practitioners. It works, and it is also a quiet accumulation of obligations that only grows. Each new event schema version requires a new upcaster. The upcasters compose (v1→v2→v3) but the chain only lengthens. Five years in, your projection pipeline may spend more time upcasting old events than processing new ones. The past grows heavier. The present must carry it.

CQRS compounds this. The whole point of Command Query Responsibility Segregation is that the write model and the read model are different representations, updated at different times, potentially by different versions of the code. These two sides are *always* at different versions during a deploy, and they are *designed* to be. This is a feature, right up until the event schema changes and the read side needs to rebuild its projections from the entire history of the write side, including event formats that predate the current team.

Projection rebuilds are the moment of truth. “Just replay the events” is the event sourcing equivalent of “just run the tests”: true in principle, contingent on everything else being in order. If the projection function can’t handle every event schema that ever existed (including the ones from before the team adopted a schema registry, before the naming conventions were standardized, before someone decided that `amount` meant dollars instead of cents, before the engineer who made that decision left for a FAANG and took the context with them) the rebuild fails, and you discover that your theoretically-rebuildable read model is not, in fact, rebuildable.

There is a deeper issue. When your aggregate’s behavior changes (new business rules, different state transitions, altered validation logic) every aggregate that was built by replaying events under the *old* rules is now suspect. The events are facts about what happened, but the meaning you ascribed to those events was a function of the code that processed them. A `PaymentAuthorized` event that was valid under old business rules may represent a state transition that the new rules would have rejected. The events haven’t changed. What they *mean* has. This is semantic drift at its most consequential, and I’ll return to it shortly.

None of this means event sourcing is wrong. For audit-heavy domains, financial systems, and applications where “what happened” is as important as “what is,” it remains one of the best architectural patterns available. But it is worth understanding what you are signing up for: a permanent, irrevocable contract with every schema version your system will ever produce, extending forward without bound. The version compatibility problem isn’t something that happens to event-sourced systems. It *is* the system.

<svg viewBox="0 0 680 340" xmlns="http://www.w3.org/2000/svg" class="upcaster-svg" data-astro-cid-muiazdm6=""><text x="20" y="20" class="section-label" data-astro-cid-muiazdm6="">EVENT LOG (append-only)</text> <rect x="20" y="32" width="200" height="28" rx="4" class="event-box event-v1" data-astro-cid-muiazdm6=""></rect><circle cx="36" cy="46" r="6" class="dot dot-v1" data-astro-cid-muiazdm6=""></circle><text x="48" y="42" class="event-label label-v1" data-astro-cid-muiazdm6="">v1</text> <text x="48" y="54" class="event-text" data-astro-cid-muiazdm6="">PaymentInitiated { amount: 500 }</text> <rect x="20" y="64" width="200" height="28" rx="4" class="event-box event-v1" data-astro-cid-muiazdm6=""></rect><circle cx="36" cy="78" r="6" class="dot dot-v1" data-astro-cid-muiazdm6=""></circle><text x="48" y="74" class="event-label label-v1" data-astro-cid-muiazdm6="">v1</text> <text x="48" y="86" class="event-text" data-astro-cid-muiazdm6="">PaymentCaptured { amount: 500 }</text> <rect x="20" y="100" width="200" height="28" rx="4" class="event-box event-v2" data-astro-cid-muiazdm6=""></rect><circle cx="36" cy="114" r="6" class="dot dot-v2" data-astro-cid-muiazdm6=""></circle><text x="48" y="110" class="event-label label-v2" data-astro-cid-muiazdm6="">v2</text> <text x="48" y="122" class="event-text" data-astro-cid-muiazdm6="">PaymentInitiated {..., currency }</text> <rect x="20" y="132" width="200" height="28" rx="4" class="event-box event-v2" data-astro-cid-muiazdm6=""></rect><circle cx="36" cy="146" r="6" class="dot dot-v2" data-astro-cid-muiazdm6=""></circle><text x="48" y="142" class="event-label label-v2" data-astro-cid-muiazdm6="">v2</text> <text x="48" y="154" class="event-text" data-astro-cid-muiazdm6="">RefundRequested {..., currency }</text> <rect x="20" y="168" width="200" height="28" rx="4" class="event-box event-v3" data-astro-cid-muiazdm6=""></rect><circle cx="36" cy="182" r="6" class="dot dot-v3" data-astro-cid-muiazdm6=""></circle><text x="48" y="178" class="event-label label-v3" data-astro-cid-muiazdm6="">v3</text> <text x="48" y="190" class="event-text" data-astro-cid-muiazdm6="">PaymentInitiated { amount: {...} }</text> <rect x="20" y="204" width="200" height="28" rx="4" class="event-box event-v4" data-astro-cid-muiazdm6=""></rect><circle cx="36" cy="218" r="6" class="dot dot-v4" data-astro-cid-muiazdm6=""></circle><text x="48" y="214" class="event-label label-v4" data-astro-cid-muiazdm6="">v4</text> <text x="48" y="226" class="event-text" data-astro-cid-muiazdm6="">PaymentInitiated {..., precision }</text> <line x1="10" y1="32" x2="10" y2="232" class="time-arrow" data-astro-cid-muiazdm6=""></line><polygon points="10,236 7,228 13,228" class="arrow-head" data-astro-cid-muiazdm6=""></polygon><text x="10" y="250" text-anchor="middle" class="time-label" data-astro-cid-muiazdm6="">time</text> <line x1="230" y1="130" x2="270" y2="130" class="flow-arrow" data-astro-cid-muiazdm6=""></line><polygon points="274,130 266,126 266,134" class="flow-head" data-astro-cid-muiazdm6=""></polygon><text x="280" y="20" class="section-label" data-astro-cid-muiazdm6="">UPCASTER PIPELINE</text> <rect x="280" y="36" width="100" height="36" rx="4" class="upcaster-box upcaster-v2" data-astro-cid-muiazdm6=""></rect><text x="330" y="52" text-anchor="middle" class="upcaster-label label-v2" data-astro-cid-muiazdm6="">v1 → v2</text> <text x="330" y="64" text-anchor="middle" class="upcaster-detail" data-astro-cid-muiazdm6="">add currency default</text> <line x1="330" y1="72" x2="330" y2="84" class="connector connector-v2" data-astro-cid-muiazdm6=""></line><polygon points="330,88 327,82 333,82" class="connector-head connector-v2" data-astro-cid-muiazdm6=""></polygon><rect x="280" y="88" width="100" height="36" rx="4" class="upcaster-box upcaster-v3" data-astro-cid-muiazdm6=""></rect><text x="330" y="104" text-anchor="middle" class="upcaster-label label-v3" data-astro-cid-muiazdm6="">v2 → v3</text> <text x="330" y="116" text-anchor="middle" class="upcaster-detail" data-astro-cid-muiazdm6="">nest amount object</text> <line x1="330" y1="124" x2="330" y2="136" class="connector connector-v3" data-astro-cid-muiazdm6=""></line><polygon points="330,140 327,134 333,134" class="connector-head connector-v3" data-astro-cid-muiazdm6=""></polygon><rect x="280" y="140" width="100" height="36" rx="4" class="upcaster-box upcaster-v4" data-astro-cid-muiazdm6=""></rect><text x="330" y="156" text-anchor="middle" class="upcaster-label label-v4" data-astro-cid-muiazdm6="">v3 → v4</text> <text x="330" y="168" text-anchor="middle" class="upcaster-detail" data-astro-cid-muiazdm6="">add precision field</text> <line x1="330" y1="176" x2="330" y2="188" class="connector connector-current" data-astro-cid-muiazdm6=""></line><polygon points="330,192 327,186 333,186" class="connector-head connector-current" data-astro-cid-muiazdm6=""></polygon><rect x="280" y="192" width="100" height="30" rx="4" class="current-box" data-astro-cid-muiazdm6=""></rect><text x="330" y="211" text-anchor="middle" class="current-label" data-astro-cid-muiazdm6="">v4 (current)</text> <rect x="280" y="234" width="100" height="36" rx="4" class="future-box" data-astro-cid-muiazdm6=""></rect><text x="330" y="250" text-anchor="middle" class="future-label" data-astro-cid-muiazdm6="">v4 → v5</text><text x="330" y="262" text-anchor="middle" class="future-detail" data-astro-cid-muiazdm6="">???</text><line x1="330" y1="192" x2="330" y2="234" class="future-connector" data-astro-cid-muiazdm6=""></line> <text x="400" y="56" class="annotation annotation-dim" data-astro-cid-muiazdm6="">each new schema</text> <text x="400" y="70" class="annotation annotation-dim" data-astro-cid-muiazdm6="">adds to the chain</text> <text x="400" y="252" class="annotation annotation-warn" data-astro-cid-muiazdm6="">five years in, the pipeline</text> <text x="400" y="266" class="annotation annotation-warn" data-astro-cid-muiazdm6="">may spend more time upcasting</text> <text x="400" y="280" class="annotation annotation-warn" data-astro-cid-muiazdm6="">than processing new events</text> <rect x="20" y="296" rx="4" ry="4" width="640" height="30" class="summary-box" data-astro-cid-muiazdm6=""></rect><text x="340" y="316" text-anchor="middle" class="summary-text" data-astro-cid-muiazdm6="">4 schema versions → 3 upcasters. The events are permanent. The chain only grows.</text></svg>

## Temporal and bitemporal databases: time as a first-class citizen

(To be clear: I’m talking about *temporal databases*, not the Temporal workflow orchestrator or the Temporal JavaScript API. Different things entirely, confusingly named.)

If event sourcing is the application-level response to “we need to know what happened,” temporal databases are the data-level response. Bitemporal databases are the response that takes the problem seriously enough to track *why the answer keeps changing*.

A traditional database gives you the current state, full stop. When you `UPDATE` a row, the previous value is gone. SQL:2011 standardized two flavors of temporal table: *system-versioned* tables (which automatically record when each row version was stored, letting you query any historical point) and *application-time period* tables (which track when a fact was true in the real world). These are genuinely different questions. System time tells you “what did the database contain at time T?” Application time tells you “what was true in the world during period P?”

A **bitemporal database** tracks both axes simultaneously: **valid time** (when a fact was true in the real world) and **transaction time** (when the system recorded it). The distinction matters most when corrections arrive late. Suppose you learn on February 5th that an employee’s address actually changed on January 15th, but the old address was recorded until today. A bitemporal table lets you ask both: “what did we *believe* the address was on January 20th?” (the old one; we hadn’t learned about the change yet) and “what *was* the address on January 20th?” (the new one; the change had already happened). In financial reporting, insurance, healthcare, and regulatory compliance, the difference between “what was true” and “what we knew” has legal consequences.

This is directly relevant to the version problem, because `db.asOf(lastTuesday)` is essentially asking “give me the database as last Tuesday’s code saw it.” It is version-aware querying at the data layer.

**Datomic** is the purest expression of this idea, and not coincidentally, it comes from the functional programming tradition. Rich Hickey designed it around the same insight that motivates persistent data structures: the past is immutable, so treat it as a value. Facts are datoms (entity, attribute, value, transaction, added?) and the database is an accumulation of datoms over time. Nothing is updated; new facts are asserted, old facts are retracted by asserting their negation. Attributes are added but never removed. You cannot drop a column. You cannot rename an attribute. (If you want the old attribute to stop being used, you simply stop writing to it and exercise great discipline in your attribute naming, forever.) This eliminates an entire class of version problems by refusing to permit destructive schema changes: the always-roll-forward philosophy applied to the data model itself.

**XTDB** (formerly Crux) takes bitemporality further, making both valid time and transaction time first-class on every document. You can insert a record with a valid-time range in the past (correcting historical data without pretending you always knew it) and the transaction time records when you made the correction.

What temporal and bitemporal databases get right is that they make the version-of-truth problem explicit in the data model. But here is the recurring theme: **bitemporal databases give you time-travel for data, not for code.** You can reconstruct the database as it appeared to last Tuesday’s deploy. You cannot automatically run last Tuesday’s code against it. The query function interpreting the historical data is whatever version is running *now*. Datomic will show you exactly what the `amount` attribute contained at every point in time. It will not tell you whether `amount` meant cents or dollars at the time it was written.

Bitemporal Database Click a cell, then try different queries

T1

T2

T3

T4

T5

T6

T7

T8

V1

V2

V3

V4

V5

V6

V7

V8

Transaction Time →

↓ Valid Time (when it was true) → Transaction Time (when recorded)

The yellow dot is a late correction: at T6, we learned the V3 value was different. A traditional DB would lose the old value.

Having an immutable, queryable history of your data is strictly better than not having one. But it solves the data half of the problem. The code half (the fact that the function interpreting the data is itself a versioned artifact with its own quiet evolution) remains unsolved by the database alone.

## Semantic drift: the type didn’t change, but the meaning did

I touched on this in the context of event sourcing, but it deserves its own treatment, because it is the version of the version problem that no tool catches.

Everything I’ve described so far (structural schema evolution, sum type changes, serialization compatibility) is at least *detectable*. A field was added or removed. A constructor appeared. A type changed. Schema comparison tools can see these things.

The more insidious problem is when the type stays the same but the meaning changes.

Consider a field called `amount` on a transaction record, typed as `Int`. In version 1, it represents cents. In version 2, someone decides it should represent dollars. The schema hasn’t changed. The type hasn’t changed. No diff tool, no schema registry, no linter will flag this. But every consumer that crosses the version boundary will silently produce wrong answers, wrong by a factor of 100, which is the kind of wrong that makes accountants *very* unhappy and auditors positively incandescent.

This is not a contrived example. Semantic drift happens constantly in more subtle forms: a boolean field whose meaning shifts from “user opted in” to “user did not opt out” (same values, different default assumptions). A status enum where `Completed` starts meaning “payment captured” but gradually comes to mean “payment authorized” as the business process evolves. A timestamp that was always UTC until one service started writing local time. (There is always one service.) The schema is identical across versions. The data is quietly, catastrophically incompatible.

Semantic Drift Toggle versions to see the silent failure

v1: Producer

type Transaction = {
amount :Int
\-- cents
}

writes: amount = 4999

meaning: $49.99

v2: Producer

type Transaction = {
amount :Int
\-- dollars
}

writes: amount = 4999

meaning: $4999.00

Schema diff: no changes detected ✓

v1 consumer reads v1 data: amount = 4999 cents → $49.99 → €42.49 ✓

No type system catches this, and I don’t think any type system *can* catch this in full generality; it would require encoding the intended semantics of every field, not just its representation. Liquid Haskell can express refinement types like `{v : Amount | v > 0}`, which would catch the sign of the value but not the unit. Dependent types in Idris or Agda could, in principle, track units through computation, but only if someone writes the proof obligations, and only within a single version.

What *does* help is treating semantic changes as seriously as structural changes. Document the semantics of your data contracts. Use newtypes that encode units (`Cents` vs `Dollars`, not `Int`). When you change the *interpretation* of a field, treat it as a migration even if the schema doesn’t change, because at the version boundary, it *is* a migration. The discipline is social and documentary as much as it is technical. This may be uncomfortable for communities that prize formal verification, but no amount of type-level machinery will save you if two versions of your code disagree about what a field *means*.

## The diminishing returns of type-level invariants

There is a curve to encoding invariants in the type system, and I think many communities are systematically miscalibrated about where the returns start diminishing. Every language with a sufficiently expressive type system develops its own version of this: Java’s generics rabbit hole, TypeScript’s conditional types labyrinth, Rust’s lifetime annotation thickets. The FP variant is distinctive because the type system is genuinely capable enough to go very far down the curve before the costs become obvious.

On the left side of the curve, the returns are enormous. Newtypes that prevent you from mixing up a `CustomerId` with an `OrderId`. Sum types that model your domain states explicitly. Making illegal states unrepresentable for your core business logic. This is high-value work. I will defend it to anyone, in any language.

But there’s a point where the returns drop while costs keep climbing. Phantom types tracking authorization state. Type-level natural numbers for sized vectors. GADTs enforcing protocol ordering. Effect systems with fine-grained capability tracking. Each is a real technique solving a real problem. Each also increases compile times, produces worse error messages (GHC’s novel-length type errors are a rite of passage, not a selling point), shrinks the pool of engineers who can confidently modify the code, and makes it harder to follow under production pressure.

The cost I want to focus on is the one that rarely gets discussed: **the invariants you most want to enforce are inter-version properties, and the type checker operates on one version at a time.** “This system handles deploy boundaries gracefully.” “This serialization format is forward-compatible.” “This migration is safe to run while the old code is still serving traffic.” These are properties of the relationship between two snapshots of the code. The type checker sees one snapshot. Production is running several.

This is worth stating even for the most powerful type systems we have. Liquid Haskell can prove that *within your code*, a PaymentStatus is always valid after parsing. It cannot prove that a PaymentStatus serialized by last Tuesday’s deploy will parse successfully in today’s code, because last Tuesday’s code is not in scope. Dependent types can prove your serializer and deserializer are inverses; a round-trip property of a *single* version’s codec. The production question is whether *this* version’s deserializer is a left inverse of *last* version’s serializer, and that requires having both versions in scope simultaneously.

The practical response is surprisingly low-tech: keep both versions in scope yourself. Copy the old schema definition into your codebase alongside the new one. Write an explicit parser from the old format to the new. Test it. This is unglamorous, but it has the virtue of being checkable against what is actually running in production right now, rather than against an abstract notion of compatibility. The type checker can verify that your v1-to-v2 migration function is total and well-typed; it just needs you to supply both types. Most teams that do this well arrive at it through painful experience rather than methodology, and end up with a `legacy/` or `compat/` module that quietly grows over time.

<svg viewBox="0 0 680 300" xmlns="http://www.w3.org/2000/svg" class="tb-svg" data-astro-cid-mrd56pta=""><rect x="20" y="20" width="250" height="240" rx="6" class="process-box" data-astro-cid-mrd56pta=""></rect><text x="145" y="40" text-anchor="middle" class="process-label" data-astro-cid-mrd56pta="">Process A (v2)</text> <rect x="35" y="52" width="220" height="68" rx="4" class="type-box" data-astro-cid-mrd56pta=""></rect><text x="45" y="68" class="kw" data-astro-cid-mrd56pta="">data</text> <text x="72" y="68" class="type-name" data-astro-cid-mrd56pta="">PaymentStatus</text> <text x="55" y="82" class="constructor" data-astro-cid-mrd56pta="">= Pending</text> <text x="55" y="94" class="constructor" data-astro-cid-mrd56pta="">| Completed</text> <text x="55" y="106" class="constructor" data-astro-cid-mrd56pta="">| Failed</text> <text x="55" y="118" class="constructor-new" data-astro-cid-mrd56pta="">| Refunded</text> <rect x="35" y="128" width="220" height="44" rx="4" class="type-box" data-astro-cid-mrd56pta=""></rect><text x="45" y="144" class="kw" data-astro-cid-mrd56pta="">newtype</text> <text x="88" y="144" class="type-name" data-astro-cid-mrd56pta="">Amount (u:: Unit)</text> <text x="55" y="158" class="constructor" data-astro-cid-mrd56pta="">= Amount Int</text> <rect x="35" y="180" width="220" height="36" rx="4" class="type-box" data-astro-cid-mrd56pta=""></rect><text x="45" y="196" class="refinement" data-astro-cid-mrd56pta="">{-@ type ValidAmt = {v:Int | v &gt; 0} @-}</text> <text x="45" y="210" class="refinement-label" data-astro-cid-mrd56pta="">Liquid Haskell refinement</text> <rect x="35" y="224" width="220" height="24" rx="4" class="check-box" data-astro-cid-mrd56pta=""></rect><text x="145" y="240" text-anchor="middle" class="check-text" data-astro-cid-mrd56pta="">GHC: all invariants hold ✓</text> <rect x="282" y="80" width="116" height="140" rx="4" class="wire-box" data-astro-cid-mrd56pta=""></rect><text x="340" y="100" text-anchor="middle" class="wire-label" data-astro-cid-mrd56pta="">THE WIRE</text> <text x="340" y="116" text-anchor="middle" class="wire-sublabel" data-astro-cid-mrd56pta="">(JSON / Protobuf / Avro)</text> <text x="340" y="140" text-anchor="middle" class="wire-data" data-astro-cid-mrd56pta="">{"status": "Refunded",</text><text x="340" y="154" text-anchor="middle" class="wire-data" data-astro-cid-mrd56pta=""> "amount": 4999}</text> <text x="340" y="178" text-anchor="middle" class="wire-annotation" data-astro-cid-mrd56pta="">no phantom type</text> <text x="340" y="190" text-anchor="middle" class="wire-annotation" data-astro-cid-mrd56pta="">no refinement</text> <text x="340" y="202" text-anchor="middle" class="wire-annotation" data-astro-cid-mrd56pta="">no unit tag</text> <text x="340" y="214" text-anchor="middle" class="wire-annotation-em" data-astro-cid-mrd56pta="">just bytes</text> <line x1="270" y1="150" x2="282" y2="150" class="flow-arrow" data-astro-cid-mrd56pta=""></line><polygon points="282,150 276,147 276,153" class="flow-head" data-astro-cid-mrd56pta=""></polygon><text x="276" y="140" text-anchor="middle" class="serialize-label" data-astro-cid-mrd56pta="">serialize</text> <line x1="398" y1="150" x2="410" y2="150" class="flow-arrow" data-astro-cid-mrd56pta=""></line><polygon points="410,150 404,147 404,153" class="flow-head" data-astro-cid-mrd56pta=""></polygon><text x="404" y="140" text-anchor="middle" class="serialize-label" data-astro-cid-mrd56pta="">deserialize</text> <rect x="410" y="20" width="250" height="240" rx="6" class="process-box-old" data-astro-cid-mrd56pta=""></rect><text x="535" y="40" text-anchor="middle" class="process-label-old" data-astro-cid-mrd56pta="">Process B (v1)</text> <rect x="425" y="52" width="220" height="56" rx="4" class="type-box" data-astro-cid-mrd56pta=""></rect><text x="435" y="68" class="kw" data-astro-cid-mrd56pta="">data</text> <text x="462" y="68" class="type-name" data-astro-cid-mrd56pta="">PaymentStatus</text> <text x="445" y="82" class="constructor" data-astro-cid-mrd56pta="">= Pending</text> <text x="445" y="94" class="constructor" data-astro-cid-mrd56pta="">| Completed</text> <text x="445" y="106" class="constructor" data-astro-cid-mrd56pta="">| Failed</text> <rect x="425" y="120" width="220" height="36" rx="4" class="error-box" data-astro-cid-mrd56pta=""></rect><text x="435" y="138" class="error-text" data-astro-cid-mrd56pta="">ParseError: unknown</text> <text x="435" y="152" class="error-text" data-astro-cid-mrd56pta="">constructor "Refunded"</text> <rect x="425" y="164" width="220" height="44" rx="4" class="type-box" data-astro-cid-mrd56pta=""></rect><text x="435" y="180" class="kw" data-astro-cid-mrd56pta="">newtype</text> <text x="478" y="180" class="type-name" data-astro-cid-mrd56pta="">Amount</text> <text x="445" y="194" class="constructor" data-astro-cid-mrd56pta="">= Amount Int</text> <text x="575" y="194" class="drift-label" data-astro-cid-mrd56pta="">-- cents?</text><rect x="425" y="224" width="220" height="24" rx="4" class="check-box-old" data-astro-cid-mrd56pta=""></rect> <text x="535" y="240" text-anchor="middle" class="check-text-old" data-astro-cid-mrd56pta="">GHC: all invariants hold ✓</text> <rect x="20" y="272" rx="4" ry="4" width="640" height="24" class="summary-box" data-astro-cid-mrd56pta=""></rect><text x="340" y="288" text-anchor="middle" class="summary-text" data-astro-cid-mrd56pta="">Both processes are well-typed. The type checker verified one at a time. The bug lives between them.</text></svg>

This is also where Ink & Switch’s [Cambria](https://www.inkandswitch.com/cambria/) project offers an interesting alternative model.<sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-6">6</a></sup> Instead of trying to make types enforce version compatibility at compile time, Cambria uses **edit lenses** (composable, reversible schema transformations) to convert data between versions at runtime. You define how version A maps to version B, and Cambria can compose A→B and B→C into A→C. Compatibility is a property of the *transformation between versions*, not of any single version’s types. This is a fundamentally different way of thinking, and it’s one that FP’s own theoretical tradition (the lens and optics literature <sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-7">7</a></sup>) helped create.

## Parse, don’t validate: across versions

Alexis King’s “Parse, Don’t Validate” is one of the most influential ideas in recent FP discourse, and rightfully so. Instead of checking properties of data at runtime and hoping the check was performed before use, parse unstructured input into a structured type that *proves* the invariant holds. Push checks to the boundary, once, and let the types carry the guarantee forward.

This is correct. It is also incomplete, because it considers only one boundary: the edge of your program, within a single version.

In production, data crosses a harder boundary constantly: the boundary between *versions*. A message serialized by deploy N is deserialized by deploy N+1. A database row written by code with three constructors is read by code with four. A GraphQL response shaped by today’s schema is consumed by a mobile client running last month’s code. At these boundaries, you are parsing data structured according to someone else’s types; types that may no longer exist in your codebase.

The discipline of “parse, don’t validate” should extend to this boundary. In some domains, it already does.

A **schema registry** is “parse, don’t validate” applied to the version boundary. In Confluent’s model, every message on a Kafka topic is tagged with a schema ID. The producer registers its schema before writing. The consumer fetches both its own schema and the writer’s schema, and the deserializer uses both to parse the data: resolving missing fields with defaults, skipping unknown fields, failing loudly on incompatible changes. You don’t deserialize and then check if the data looks right. You *parse* through a pair of schemas, and the parse itself guarantees compatibility. The check happens once, at schema registration time, not scattered across every consumer.

GraphQL takes this even further. The schema *is* the API contract, and it’s introspectable by design. Tools like Apollo GraphOS run **operations checks** against your schema: before you deploy a change, they compare it against real client queries collected from production traffic and tell you exactly which clients would break.<sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-parse1">8</a></sup> GraphQL Hive, an open-source schema registry, performs composition checks for federated schemas and can do **conditional breaking change detection**, only flagging a field removal as breaking if that field actually appears in collected operations. GraphQL Inspector diffs two schema versions and classifies every change as breaking, dangerous, or safe.

This is the version-boundary equivalent of “parse, don’t validate.” Instead of deploying and hoping your schema change is backward-compatible, you prove it before deploy. The schema diff is the parse. The compatibility check is the type check. The registry is the type system.

It is worth noting the limits of this approach honestly. Checking against 10,000 recent operations tells you about the clients that are active *now*. It tells you nothing about the mobile app version from eighteen months ago that a user hasn’t updated, which will wake up next Tuesday and send a request shaped like nothing in your recent traffic. It tells you nothing about the Kafka message serialized six months ago that is sitting patiently in a topic with annual retention, waiting to be consumed by your shiny new code. These tools are heuristics, good ones, but heuristics. They cover the common case well and the long tail not at all. For the long tail, you still need explicit version-aware parsing and the discipline of never removing a field you aren’t certain nothing still references.

The same pattern applies to Protobuf via Buf, which enforces 53 rules across four strictness levels; to Avro via the Schema Registry’s seven compatibility modes; and increasingly to database schemas via tools like Atlas, which lints your SQL migrations for destructive changes before they run. Each of these tools is doing the same thing: moving the compatibility check from runtime (where it manifests as an incident) to build time (where it manifests as a failed CI check). This is the same migration from “validate” to “parse” that King describes, applied one level up.

Schema Registry Pick a change, pick a compatibility mode

PROPOSED SCHEMA CHANGE

COMPATIBILITY MODE

New schema can read old data (upgrade consumers first)

Select a schema change to see the compatibility check.

The check happens once, at registration time. Not scattered across every consumer.

## Knowing what’s running changes everything

The schema registry pattern reveals something important: **if you can identify what versions are currently running, and you can assert compatibility between adjacent versions, you can practically achieve multi-version correctness** without waiting for the unified theory.

Think about what you’d need:

First, every boundary artifact (every serialized message, every API response, every database migration) needs to be tagged with version metadata. Schema registries do this for serialization formats. Database migration tools do this for schemas (your migration history *is* a version log). API gateways can tag HTTP traffic. Most systems already have this information; they just don’t connect it.

Second, you need a compatibility function: given version A and version B of some boundary artifact, are they compatible? This is what Confluent’s Schema Registry computes for Avro/Protobuf, what GraphQL Inspector computes for GraphQL schemas, what Buf computes for Protobuf definitions, and what Atlas computes for SQL migrations. Each tool covers one boundary type.

Third (and this is the piece most teams are missing) you need to know what’s actually running. Which code versions are deployed across your web servers, your background workers, your cron jobs? Which schema version is your database at? Which message schemas are in-flight on your Kafka topics?

This is where service meshes become interesting for reasons beyond the usual marketing. Istio and Linkerd sit between your services and observe every request. They know which version of a service is running on which pod. They can split traffic by version for canary deploys, route requests based on headers, and enforce that traffic only flows between declared-compatible versions. Combined with progressive delivery tools like Argo Rollouts or Flagger (which automatically roll back a canary if error rates spike) you get a feedback loop where version incompatibility is detected and mitigated at the network layer.

The limitation is that service meshes only see HTTP/gRPC boundaries between services. They don’t see the database, the message queue, the cron job. They’re one piece of the version inventory, not the whole picture. But they demonstrate that version-aware infrastructure is practical, and they represent the closest thing we have to a runtime system that treats “what versions are running” as a first-class concept.

If you have all three (version tags, compatibility functions, and runtime version inventory) you can answer the question that actually matters before every deploy: **“Is the version I’m about to deploy compatible with every version currently running?”** Not “does it compile?” Not “do the tests pass?” But: “given the actual set of deployments that exist right now, is it safe to add this one?”

Nobody has built the unified tool that answers this across all boundary types simultaneously. (If you are reading this and thinking “that sounds like a startup,” please, by all means.) But the components exist. A deploy pipeline that queries your orchestrator for running image tags, checks your migration history against the schema registry, diffs your GraphQL schema against collected client operations, and runs Buf’s compatibility checks: this is buildable today, with off-the-shelf parts. It is engineering work, not research.

Deploy Compatibility Check Run a deploy check against the ensemble

CURRENTLY RUNNING

Web Servers

v42

Workers

v41

Database

migration #187

Kafka Topics

3 schema versions

GraphQL Schema

hash abc123

Not "does it compile?" Not "do the tests pass?" But: "given what's running, is this safe?"

The reason I find this exciting from a compositional perspective is that the compatibility of a deploy is the conjunction of compatibility across each boundary. Each boundary has its own compatibility function. The whole thing is a product of independent checks. This is *exactly* the kind of structure that FP-trained minds are good at identifying and exploiting. We just need to look up from the type checker and see it.

## What if the old code just kept working?

Everything so far has treated multi-version coexistence as a problem to be managed. A few projects have asked a more radical question: what if it weren’t a problem at all?

**Unison** takes the most principled approach. Code is stored not by name but by a hash of its abstract syntax tree. When you change a function, you produce a new hash, and the old hash still exists, still refers to the old definition, and still works. Dependents of the old version continue using it until you explicitly propagate the update. There is no deploy in the traditional sense. The old function and the new function *coexist by construction*, because they are literally different values in a content-addressed store.

This eliminates a remarkable number of the problems I’ve been describing. Rolling deploys can’t create mixed-version incoherence, because there’s nothing to roll; each caller is pinned to the exact hash it was built against. The version compatibility question becomes “has this caller been updated to reference the new hash?” which is a graph reachability problem, not a temporal coordination problem.

**Dark** pursued a related idea from the infrastructure side: the editor and the runtime were unified, and old HTTP requests in flight continued executing against the code version that existed when they arrived. **Dhall** addresses a narrower but important slice (configuration) where totality and content-addressing provide genuine equality checking across config versions. The pattern across all three is the same: **make code (or configuration) immutable and content-addressed, so that “deploying a new version” doesn’t destroy or alter the old one.** Version coexistence stops being a race condition and becomes a data structure.

There’s a seductive quality to this, because it feels like the *right* answer in some Platonic sense. But it is not a silver bullet.

The most fundamental limitation is the one that haunts this entire essay: **semantic drift doesn’t care about your hashes.** A content-addressed function that computes `amount * exchangeRate` will return the same AST hash forever. If the business meaning of `amount` changes from cents to dollars, the function is structurally identical and semantically wrong. Content-addressing guarantees referential integrity of *code*. It says nothing about the referential integrity of *meaning*, and meaning is where the quiet catastrophes live.

More practically: your code may be immutable, but your database is not. A Unison function pinned to a specific hash still reads from and writes to the same Postgres, the same Kafka topic, the same Redis cluster as every other version. Old code pinned to an old hash will execute faithfully against a database whose schema has migrated out from under it. Content-addressing solves the version problem for pure computation but does nothing for side effects; and production systems are, inconveniently, mostly side effects.

There is also a coherence problem that content-addressing can obscure rather than solve. If service A is pinned to hash-X of a shared library and service B is pinned to hash-Y, and those hashes embed different assumptions about the wire format of messages between them, you have the same version incompatibility as before, just harder to see, because each service is internally consistent. The incoherence lives in the space *between* the hashes, in the implicit contract about what the data means.

<svg viewBox="0 0 660 360" xmlns="http://www.w3.org/2000/svg" class="ca-svg" data-astro-cid-t2wlo5eo=""><text x="20" y="18" class="section-label" data-astro-cid-t2wlo5eo="">CONTENT STORE</text> <rect x="20" y="30" width="180" height="44" rx="4" class="fn-box fn-old" data-astro-cid-t2wlo5eo=""></rect><text x="30" y="48" class="fn-name fn-name-old" data-astro-cid-t2wlo5eo="">calculateTotal</text> <text x="30" y="62" class="fn-hash" data-astro-cid-t2wlo5eo="">#a3f7 <tspan class="fn-tag" data-astro-cid-t2wlo5eo="">old — still exists</tspan></text> <rect x="20" y="82" width="180" height="44" rx="4" class="fn-box fn-new" data-astro-cid-t2wlo5eo=""></rect><text x="30" y="100" class="fn-name fn-name-new" data-astro-cid-t2wlo5eo="">calculateTotal</text> <text x="30" y="114" class="fn-hash fn-hash-new" data-astro-cid-t2wlo5eo="">#b2e1 <tspan class="fn-tag-new" data-astro-cid-t2wlo5eo="">new</tspan></text> <rect x="20" y="148" width="180" height="44" rx="4" class="fn-box fn-pinned" data-astro-cid-t2wlo5eo=""></rect><text x="30" y="166" class="fn-name fn-name-pinned" data-astro-cid-t2wlo5eo="">processPayment</text> <text x="30" y="180" class="fn-hash" data-astro-cid-t2wlo5eo="">#c8d4 · uses calculateTotal <tspan class="fn-ref-old" data-astro-cid-t2wlo5eo="">#a3f7</tspan></text> <rect x="20" y="200" width="180" height="44" rx="4" class="fn-box fn-pinned" data-astro-cid-t2wlo5eo=""></rect><text x="30" y="218" class="fn-name fn-name-pinned" data-astro-cid-t2wlo5eo="">generateReceipt</text> <text x="30" y="232" class="fn-hash" data-astro-cid-t2wlo5eo="">#d1a9 · uses processPayment <tspan class="fn-ref" data-astro-cid-t2wlo5eo="">#c8d4</tspan></text> <line x1="200" y1="170" x2="215" y2="170" class="ref-line" data-astro-cid-t2wlo5eo=""></line><line x1="215" y1="170" x2="215" y2="52" class="ref-line" data-astro-cid-t2wlo5eo=""></line><line x1="215" y1="52" x2="200" y2="52" class="ref-line" data-astro-cid-t2wlo5eo=""></line><polygon points="200,52 206,49 206,55" class="ref-head-old" data-astro-cid-t2wlo5eo=""></polygon><text x="220" y="116" class="pin-label" data-astro-cid-t2wlo5eo="">pinned to old hash.</text><text x="220" y="128" class="pin-label" data-astro-cid-t2wlo5eo="">still works.</text><text x="370" y="18" class="section-label" data-astro-cid-t2wlo5eo="">SIDE EFFECTS (shared, mutable)</text> <rect x="370" y="30" width="160" height="52" rx="4" class="effect-box" data-astro-cid-t2wlo5eo=""></rect><text x="380" y="50" class="effect-icon" data-astro-cid-t2wlo5eo="">⛁</text> <text x="400" y="50" class="effect-name" data-astro-cid-t2wlo5eo="">PostgreSQL</text> <text x="400" y="64" class="effect-detail" data-astro-cid-t2wlo5eo="">schema: migration #187</text> <text x="400" y="76" class="effect-version" data-astro-cid-t2wlo5eo="">NOT pinned to any hash</text> <rect x="370" y="90" width="160" height="52" rx="4" class="effect-box" data-astro-cid-t2wlo5eo=""></rect><text x="380" y="110" class="effect-icon" data-astro-cid-t2wlo5eo="">⇶</text> <text x="400" y="110" class="effect-name" data-astro-cid-t2wlo5eo="">Kafka</text> <text x="400" y="124" class="effect-detail" data-astro-cid-t2wlo5eo="">messages from 30 days of deploys</text> <text x="400" y="136" class="effect-version" data-astro-cid-t2wlo5eo="">NOT pinned to any hash</text> <rect x="370" y="150" width="160" height="44" rx="4" class="effect-box" data-astro-cid-t2wlo5eo=""></rect><text x="380" y="170" class="effect-icon" data-astro-cid-t2wlo5eo="">⟡</text> <text x="400" y="170" class="effect-name" data-astro-cid-t2wlo5eo="">Redis cache</text> <text x="400" y="182" class="effect-detail" data-astro-cid-t2wlo5eo="">written by who-knows-which version</text> <path d="M 200 52 C 280 52, 320 56, 370 56" class="effect-arrow" data-astro-cid-t2wlo5eo=""></path><path d="M 200 104 C 280 104, 320 56, 370 56" class="effect-arrow-new" data-astro-cid-t2wlo5eo=""></path><rect x="370" y="210" width="270" height="62" rx="4" class="tension-box" data-astro-cid-t2wlo5eo=""></rect><text x="380" y="228" class="tension-title" data-astro-cid-t2wlo5eo="">The fundamental limitation</text> <text x="380" y="244" class="tension-text" data-astro-cid-t2wlo5eo="">Code is immutable and content-addressed.</text><text x="380" y="258" class="tension-text" data-astro-cid-t2wlo5eo="">The world it operates on is not.</text><text x="380" y="268" class="tension-text-dim" data-astro-cid-t2wlo5eo="">Old code pinned to #a3f7 executes faithfully against</text> <text x="380" y="278" class="tension-text-dim" data-astro-cid-t2wlo5eo="">a database whose schema has migrated out from under it.</text><rect x="20" y="296" rx="4" ry="4" width="620" height="50" class="summary-box" data-astro-cid-t2wlo5eo=""></rect> <text x="330" y="314" text-anchor="middle" class="summary-text" data-astro-cid-t2wlo5eo="">Each service is internally consistent — pinned to exact hashes. The incoherence lives</text> <text x="330" y="330" text-anchor="middle" class="summary-text" data-astro-cid-t2wlo5eo="">in the space between the hashes: the shared database, the message queue, the cache.</text></svg>

None of these projects has achieved mainstream adoption. The reasons are partly technical and partly gravitational: the existing ecosystem of tools, libraries, deployment infrastructure, and hiring pipelines (good luck findiny any job listings requiring Unison experience just yet) assumes that code lives in files, compiles into artifacts, and deploys by replacing old artifacts with new ones. But the ideas keep resurfacing. Nix and Guix use content-addressing for packages. Docker image layers are content-addressed. Git is a content-addressed store. The insight that “immutable, addressable values are easier to reason about than mutable names” is one that functional programmers should find deeply familiar. It is, after all, the argument for pure functions. We just haven’t applied it consistently to the deployment artifact itself, and when we try, we discover that the hard part was never the code. It was everything the code touches.

## The right tools, pointed at the wrong level

Here’s the thing I find both frustrating and hopeful: the intellectual toolkit for the problems I’ve been describing already exists, scattered across communities that don’t talk to each other enough, or else siloed within megacorporations that don’t share their knowledge / tooling for one reason or another.

The question “what is the space of valid (code version, schema version, data format version) tuples, and can we always reach a safe state from any point in this space?” is a compositional question. It’s a question about algebraic structure, about invariants, about lawful transformations. Let me sketch the most promising connections.

**Gradual typing as a model for version compatibility.** The correspondence runs surprisingly deep. [Siek and Taha’s consistency relation](https://ecee.colorado.edu/~siek/pubs/pubs/2006/siek06:_gradual.pdf) (2006), reflexive and symmetric but not transitive, models compatibility between types of differing precision exactly like compatibility between version types. Max New and Amal Ahmed showed that casts between types of different precision form **embedding-projection pairs**: going from a more-precise type to a less-precise type and back is the identity.<sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-8">9</a></sup> This is the mathematical structure underlying version migration: you can widen data to a more general schema and narrow it back without loss.

**Session types as API versioning.**[Session types](https://doi.org/10.1145/1328438.1328472) model the legal sequences of messages between communicating parties, and their subtyping rules map almost perfectly to API evolution: a server that accepts *more* request types is backward compatible; a server that promises *fewer* response variants is safe. [Recent work](https://doi.org/10.1007/978-3-031-57262-3_5) shows that checking this compatibility for multiparty protocols is decidable in polynomial time. No practical API versioning tool uses this theory yet (Buf’s 53 breaking change rules are ad hoc where they could be principled) but the foundations are ready.

**Multi-language semantics as multi-version semantics.** Amal Ahmed’s group has been working on programs composed from components in different languages with different type systems. Patterson and Ahmed’s [**linking types**](https://doi.org/10.4230/LIPIcs.SNAPL.2017.12) (SNAPL 2017) allow annotating where code can link with components having different capabilities. If you squint, different versions of your code *are* different languages with different type systems, and the deploy boundary is the foreign function interface.<sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-11">10</a></sup>

**Spivak’s categorical data migration.** David Spivak formalized schema evolution using category theory: a database schema is a small category, an instance is a set-valued functor, and a schema morphism induces three adjoint data migration functors (Σ, Δ, Π) that are composable by construction.<sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-12">11</a></sup> Schema migrations form a category where composition is guaranteed to be well-defined; exactly the property you want when reasoning about sequences of migrations across deploys.

## What this means in practice

None of this research will help you at 3am when your deploy is failing and PagerDuty is doing its level best to ruin your night. I know that. But it points to a shift in how we should think about building systems, regardless of language.

**Design for the ensemble, not the snapshot.** When modeling a domain type, ask not just “is this type correct?” but “can this type evolve?” Will adding a constructor break deserialization for old consumers? Will removing a field crash the previous deploy? Apply “parse, don’t validate” at every version boundary, not just at the edge of a single program.

**Make your boundaries explicit and machine-checkable.** Register your schemas. Diff your GraphQL types in CI. Lint your SQL migrations. Every boundary artifact (API schema, message format, database schema, workflow definition) should be versioned and checked for compatibility as part of your deploy pipeline.<sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-13">12</a></sup>

**Invest in the “impure shell.”** The part of your system that handles retries, timeouts, connection management, circuit breaking, graceful shutdown, and error recovery is where your system meets reality. In a well-structured FP application, this logic lives in the outer “impure” layer that often gets less design attention than the pure core. But it is the code that determines whether your system handles version transitions gracefully or falls over. It deserves the same rigor we bring to domain modeling.

**Build toward a deploy-time compatibility check.** The individual tools exist: Atlas for migration safety, Buf for Protobuf compatibility, Apollo GraphOS or GraphQL Hive for schema checks, Temporal for workflow versioning <sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-14">13</a></sup>, `cargo-semver-checks` for library APIs <sup><a href="https://www.iankduncan.com/engineering/2026-02-09-what-functional-programmers-get-wrong-about-systems/#user-content-fn-15">14</a></sup>. What’s missing is the orchestration; a single step in your pipeline that queries what’s running, checks compatibility across every boundary, and gives you a yes or no. This is achievable today with off-the-shelf parts.

**Treat your monolith like what it is.** If you have multiple servers, background workers, cron jobs, or third-party integrations (and you do) you are operating a distributed system. The sooner your team internalizes this, the sooner you start making architectural decisions that account for the reality of your runtime environment rather than the pleasant fiction of a single coherent program.

---

## Closing

The FP community has spent decades building tools for reasoning about programs with extraordinary precision. That work is deeply valuable, fascinating, and makes me a happier coder every day. Every language community would benefit from taking local correctness as seriously as we do. What I’m suggesting is not that we abandon it or minimize its value, but that we lift our gaze to the level where many of the hardest problems actually live, and that we notice, with some honesty, how many of those problems look the same regardless of what language you wrote the program in.

What’s missing is the synthesis. Nobody has built a unified tool that takes your type definitions, your serialization format, your migration history, and your deployment topology and tells you whether a given deploy sequence is safe. In fairness, I don’t think you really can, given the breadth of the problem.

But we don’t have to wait for the theory or some shiny startup to fix it for us. “Parse, don’t validate” gave us the right intuition; we just need to apply it at every version boundary. The tools to check schema compatibility, diff API contracts, and lint database migrations exist today. The missing piece is connecting them to your deployment system so you can answer the question that actually matters: “given everything that’s running right now, is it safe to deploy this?”

The program is not the unit of correctness. The set of deployments is. The type checker’s jurisdiction ends at the boundary of a single artifact, and production is an ensemble of artifacts, each one a different vintage, each one faithful to the types it was compiled against, each one potentially at odds with its neighbors. The tools to reason about that ensemble are closer than you think. They just aren’t the tools you’ve been reaching for.

[^1]: Rae et al., [“Online, Asynchronous Schema Change in F1”](https://doi.org/10.14778/2536222.2536230) (VLDB 2013). The paper defines four-state transitions for index creation (absent → delete-only → write-only → public) where each adjacent pair is safe to coexist. This remains the definitive formal model for multi-version schema correctness in distributed systems.

[^2]: Confluent’s Schema Registry formalizes this into seven compatibility modes: BACKWARD, FORWARD, FULL, and their TRANSITIVE variants. BACKWARD means “you can upgrade consumers first,” FORWARD means “you can upgrade producers first,” FULL means “upgrade in any order.” These map directly to the deployment ordering problem.

[^3]: Kubernetes is converging on the same insight from the infrastructure side. KEP-4330 introduces “emulated version” for two-step upgrades with minor-version rollback, while KEP-4020 adds a mixed-version proxy for safe API routing during upgrades. But neither gives you Erlang’s `code_change/3`, an explicit, programmer-written function for the state transition between versions. That remains the most honest interface to the problem any platform has offered.

[^4]: Gupta, Jalote, and Barua, [“A Formal Framework for On-line Software Version Change”](https://doi.org/10.1109/32.485222) (IEEE TSE, 1996). Stoyle, Hicks, et al. later developed [a type system for DSU](https://www.cs.umd.edu/~mwh/papers/mutatis-journal.pdf) (TOPLAS 2007) that ensures if an update is accepted, the resulting program is type-correct across the version boundary. Hayden et al. ([VSTTE 2012](https://doi.org/10.1007/978-3-642-27705-4_22)) achieved the first automatic verification of DSU correctness using a “merged program” combining old and new versions.

[^5]: The [InVerDa system](https://doi.org/10.1007/s00778-018-0508-7) (Herrmann et al.) formalized this as BiDEL, a Bidirectional Database Evolution Language that extends the PRISM framework’s Schema Modification Operators to be bidirectional and relationally complete. It enables multiple co-existing schema versions within one database where all versions access the same data set; the strongest formal guarantee for multi-version schema coexistence in the literature.

[^6]: Litt, van Hardenberg, and Henry, [“Cambria: Schema Evolution in Distributed Systems with Edit Lenses”](https://doi.org/10.1145/3447865.3457963) (PaPoC 2021). The system integrates with Automerge CRDTs, storing raw writes in the writer’s schema and translating at read time.

[^7]: Foster, Greenwald, Moore, Pierce, and Schmitt’s [seminal work on lenses](https://doi.org/10.1145/1232420.1232424) (POPL 2005, TOPLAS 2007) established the algebraic foundation. Hofmann, Pierce, and Wagner extended it to [symmetric lenses](https://doi.org/10.1145/1926385.1926428) (POPL 2011) where neither direction is privileged, directly modeling bidirectional version migration.

[^8]: Apollo’s operations checks run against up to 10,000 distinct historical operations. GraphQL Hive and GraphQL Inspector provide similar capabilities in the open-source ecosystem, with Hive offering a full schema registry with version history and composition validation for federated graphs.

[^9]: New and Ahmed, [“Graduality from Embedding-Projection Pairs”](https://doi.org/10.1145/3236768) (ICFP 2018). Wadler and Findler’s [blame tracking](https://doi.org/10.1007/978-3-642-00590-9_1) (ESOP 2009) extends this with the Blame Theorem: when casting between types of different precision, failures are attributed to the less-precisely-typed portion. Directly applicable to identifying which side of a version boundary caused an incompatibility.

[^10]: Patterson and Ahmed’s [semantic soundness framework](https://doi.org/10.1145/3519939.3523703) (PLDI 2022) uses a convertibility relation τ\_A ∼ τ\_B between types from different languages, with glue code implementing conversions; directly applicable to cross-version type compatibility.

[^11]: Spivak, [“Functorial Data Migration”](https://doi.org/10.1016/j.ic.2012.05.001) (2012). The categorical framing guarantees that migration composition is associative and has identities, which is more than can be said for most migration frameworks I’ve encountered in the wild.

[^12]: Atlas performs automated destructive change detection with 40+ lint rules, including data-dependent analysis that simulates changes against a temporary dev-database.

[^13]: Temporal deserves special mention here because it has taken the multi-version problem more seriously than most orchestration systems. The earliest mechanism, `patched()`, inserts markers into workflow event history that act as version-aware branch points: new code can take a different path while old executions continue on the original one. This works but scales poorly; every incompatible change requires a new patch call, and the branching logic accumulates. The more interesting approach is **Worker Versioning**, which assigns a Build ID to each worker deployment and lets the Temporal server route workflow tasks to the right worker version. New workflows go to the latest build. Existing workflows continue on the build that started them. This is essentially blue-green deployment at the workflow level: old and new worker pools coexist, each handling the workflows that belong to them, and the server manages the routing. You can drain old workers gradually as their workflows complete, or run them indefinitely if some workflows are long-lived. The version boundary is explicit and managed by the platform rather than by per-function patching in your code. But perhaps the most interesting thing Temporal does is *fail loudly when versions disagree*. If you deploy new workflow code that would produce a different sequence of commands than the original execution recorded in its event history, Temporal raises a **nondeterminism error** and refuses to continue. On one hand, your workflow is stuck and someone’s pager is going off. On the other hand, the system *detected at runtime* that two versions of your code are incompatible, which is more than most systems manage. They simply produce wrong answers in silence. Temporal’s nondeterminism errors are, in a sense, a runtime version-compatibility assertion: the event history *is* the specification of what the workflow was supposed to do, and the new code is being checked against it. It’s not a pleasant experience when it fires, but it is an honest one.

[^14]: Predrag Gruevski’s analysis with `cargo-semver-checks` found that 1 in 6 of the top 1000 Rust crates had violated semver at least once. Elm’s package manager was the first to automate version classification by comparing exposed type signatures between releases.
