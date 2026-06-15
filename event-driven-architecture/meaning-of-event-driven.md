---
title: "What do you mean by “Event-Driven”? (my notes)"
source: "https://martinfowler.com/articles/201701-event-driven.html"
author:
  - "[[Martin Fowler]]"
published: 2017-02-07
created: 2026-06-04
description: "My distilled notes on Fowler's four conflated event-driven patterns: Event Notification, Event-Carried State Transfer, Event Sourcing, and CQRS."
tags:
  - "note"
  - "event-driven"
---

# What do you mean by "Event-Driven"?

> Source: [martinfowler.com/articles/201701-event-driven.html](https://martinfowler.com/articles/201701-event-driven.html)
> Authors: Martin Fowler (with the ThoughtWorks event-architecture group)
> Supplementary (long-form video): [The Many Meanings of Event-Driven Architecture — Martin Fowler (GOTO 2017)](https://www.youtube.com/watch?v=STKCRSUsyP0)
> Full clipping of the original article in this vault: [[what-do-you-mean-by-event-driven]]

"Event-Driven" is an overloaded term. People use it to mean at least four distinct patterns that get conflated.

- Event Notification
- Event-Carried State Transfer
- Event-Sourcing
- CQRS

## The Problem: "Event-Driven" Conflates Several Patterns

## 1. Event Notification

This happens when a system sends event messages to notify other systems of a change in its domain. A key element of event notification is that the source system doesn't really care much about the response.

An event need not carry much data on it, often just some id information and a link back to the sender that can be queried for more information.

### Decouples sender from receiver

It implies a low level of coupling between the sender and the receiver.

### "Where did this happen?" traceability problem

It can become problematic, however, if there really is a logical flow that runs over various event notifications. The problem is that it can be hard to see such a flow as it's not explicit in any program text. Often the only way to figure out this flow is from monitoring a live system.

A simple example of this trap is when an event is used as a passive-aggressive command.

## 2. Event-Carried State Transfer

This pattern shows up when you want to update clients of a system in such a way that they don't need to contact the source system in order to do further work.

### Trade-offs

An obvious downside of this pattern is that there's lots of data schlepped around and lots of copies. What we gain is greater resilience. We reduce latency and improve availability, at the cost of increased complexity and eventual consistency.

## 3. Event-Sourcing

<!-- What it is: store the sequence of events as the system of record; current
     state is a derivation.
     - Rebuilding state, audit log, temporal queries
     - Pitfalls: external systems, versioning event schemas, snapshots -->

The core idea of event sourcing is that whenever we make a change to the state of a system, we record that state change as an event, and we can rebuild the system state by reprocessing the events at any time in the future. The event store becomes the principal source of truth, and the system state is purely derived from it.

### Misconceptions

There's no need for event processing to be asynchronous.

Everyone using an event-sourced system should understand and access the event log to determine useful data. Much of the processing in an event-sourced system can be based on a useful working copy. Usually there should be a clear separation between domain processing and deriving a working copy from the event log.

### Snapshots

When working with an event log, it is often useful to build snapshots of the working copy. There is a duality here: we can look at the event log as either a list of changes or a list of states.

### Benefits

The event log provides a strong audit capability (account transactions are an event source for account balances). We can recreate historic states by replaying the event log up to a point. We can explore alternative histories by injecting hypothetical events when replaying. Event sourcing makes it plausible to have non-durable working copies, such as a Memory Image.

### Pitfalls

Replaying events becomes problematic when results depend on interactions with outside systems.

Have to figure out how to deal with changes in the schema of events over time.

## 4. CQRS

Command Query Responsibility Segregation (CQRS) is the notion of having separate data structures for reading and writing information. You can use CQRS without any events present in your design, but commonly people do combine CQRS with the earlier patterns here.

### Justification

In complex domains, a single model to handle both reads and writes gets too complicated, and we can simplify by separating the models. This is particularly appealing when you have different access patterns, such as lots of reads and very few writes.

### Trade-offs

The gain from CQRS has to be balanced against the additional complexity of having separate models.

## Key Distinctions & When to Use Each

The four patterns are *orthogonal*: they solve different problems and can be mixed freely. CQRS isn't inherently about events, and event sourcing doesn't require asynchrony. Fowler's main warning is that trouble usually comes from *conflating* the patterns, not from any one of them. (His anecdote: a project manager blamed event sourcing for a troubled project, while the tech lead pinned the real culprit on asynchronous communication — two independent choices mistaken for one.)

| Pattern | Problem it solves | Reach for it when | Be wary when |
| --- | --- | --- | --- |
| Event Notification | Decouple the source of a change from whoever reacts to it | You want low coupling and don't care about the response | A real logical flow spans many notifications — invisible in the code, traceable only on a live system |
| Event-Carried State Transfer | Let clients do further work without querying the source | Source availability and latency matter more than data freshness | You can't tolerate eventual consistency or the duplicated data |
| Event-Sourcing | A strong audit log plus the ability to rebuild and replay state | You need history, temporal queries, or alternative-history replay | State depends on outside systems, or event schemas will churn over time |
| CQRS | Separate the model for reading from the model for writing | Reads and writes have very different shapes or access patterns | The domain is simple — the extra model is pure overhead |

### Fowler's caution

> All these patterns are good in the right place, and bad when put on the wrong terrain.

He pointedly declines to give a decision procedure, admitting he'd like to write a "definitive treatise" on when each applies but doesn't have the time. He singles out CQRS as the one his colleagues are "deeply wary of using ... finding it often misused." The takeaway: adopt each pattern only where its specific benefit is clear, and never reach for one by default.

## My Takeaways

<!-- Your own notes / how this applies to your work. -->
