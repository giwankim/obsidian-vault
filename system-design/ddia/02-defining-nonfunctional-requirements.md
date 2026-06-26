# 2. Defining Nonfunctional Requirements

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch02.html>
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references)

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions.
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

**Status:** not started

## Case Study: Social Network Home Timelines

| Cue / Question | Notes |
| --- | --- |
| Why frame nonfunctional requirements through a concrete case study (the social-network timeline)? | |
| What's the difference between **fan-out on write** (precompute each timeline) and **fan-out on read** (assemble at query time)? | |
| What are the read/write cost trade-offs of each approach? | |
| How does **workload skew** (e.g. celebrities with millions of followers) break naive fan-out-on-write, and what hybrid copes with it? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Describing Performance

| Cue / Question | Notes |
| --- | --- |
| What's the difference between **response time**, **latency**, and **service time**? | |
| What is **throughput**, and how does it relate to response time? | |
| Why are **percentiles** (p50 / p95 / p99 / p999) more honest than the **mean** for response times? | |
| What are **tail latencies**, and why do they matter disproportionately (often to the most valuable users)? | |
| What is **tail latency amplification**, and how does **head-of-line blocking** (queueing delay) create it? | |
| How are response-time metrics used in practice (SLOs, SLAs, percentile monitoring)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Reliability and Fault Tolerance

| Cue / Question | Notes |
| --- | --- |
| What's the difference between a **fault** and a **failure**, and what does **fault-tolerant** mean? | |
| What are typical **hardware faults**, and why is hardware redundancy alone no longer enough? | |
| Why are **software faults** (systematic, correlated errors) often more dangerous than hardware faults? | |
| How do **human errors** cause outages, and how do you design systems that tolerate them? | |
| When (if ever) is it acceptable to trade away reliability? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Scalability

| Cue / Question | Notes |
| --- | --- |
| What are **load parameters**, and how do you choose the right ones to describe a system's load? | |
| When load grows, what two distinct questions describe performance? (fixed resources → how does perf degrade vs. how much to add to keep perf constant) | |
| **Scaling up (vertical)** vs **scaling out (horizontal)**: what's the trade-off, and where does **elasticity** fit? | |
| Why is there no generic, one-size-fits-all "scalable architecture"? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Maintainability

| Cue / Question | Notes |
| --- | --- |
| What three design principles make a system maintainable? (operability, simplicity, evolvability) | |
| **Operability**: what makes life easy for the operations team? | |
| **Simplicity**: what is *accidental* complexity, and how do good **abstractions** reduce it? | |
| **Evolvability**: what makes a system easy to change as requirements evolve? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Summary (the book's own)

| Cue / Question | Notes |
| --- | --- |
| How does the chapter connect functional vs. **nonfunctional** requirements? | |
| What through-line ties performance, reliability, scalability, and maintainability together? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Sketch the home-timeline case study: the write path (post tweet --> fan-out)
%% vs the read path (load timeline), and where skew forces a hybrid.
flowchart LR
```

## Open Questions / Follow-Ups

- [ ]

## Connections

- [[00-ddia-moc]] — chapter map / index.
- [[01-trade-offs-in-data-systems-architecture]] — picks up the operational vs. analytical workload framing; shared-nothing architecture recurs in Scalability.
