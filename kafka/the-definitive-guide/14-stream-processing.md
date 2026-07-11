# 14. Stream Processing

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## What Is Stream Processing?

| Cue / Question | Notes |
| --- | --- |
| What defines a data stream (unbounded, ordered, replayable sequence of immutable events)? | |
| Where does stream processing sit between request-response and batch (continuous, non-blocking; trades a bit of latency for a lot of context)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Stream Processing Concepts

| Cue / Question | Notes |
| --- | --- |
| What is a topology (DAG of source processors → transforms → sink processors)? | |
| Which notions of time exist (event time vs log-append time vs processing time), and why does event time usually win? | |
| Why does state make stream processing hard (local vs external state; recovery; memory), and how is local state made durable (changelog topics)? | |
| Explain the stream-table duality (table = latest-value snapshot; stream = changelog; materialize a stream into a table, capture a table's changes into a stream). | |
| Which window types exist (tumbling, hopping, sliding, session), and what do window size, advance, and grace period control? | |
| How does Kafka Streams achieve exactly-once (`processing.guarantee=exactly_once` riding on transactions)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Stream Processing Design Patterns

| Cue / Question | Notes |
| --- | --- |
| Single-event processing — when is stateless map/filter enough, and why is it trivially scalable and recoverable? | |
| Processing with local state — why must aggregations be per-key and partition-scoped, and what backs the state up? | |
| Multiphase processing — why does grouping by a *different* key force a repartition topic (like a shuffle/map-reduce phase)? | |
| Stream-table join — how do you enrich a stream without hammering the external DB (CDC the table into a local, changelog-backed store)? | |
| Streaming (stream-stream) join — why does it need a time window, and how are both sides matched (same key, co-partitioned, buffered by window)? | |
| Out-of-sequence events — how are stragglers handled (event stays in its event-time window, grace period, updating already-emitted results)? | |
| Reprocessing — what are the two variants (run a new app version alongside on a new `application.id` vs reset the existing app's state and offsets)? | |
| What do interactive queries add (read the stream processor's state stores directly instead of a downstream table)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Kafka Streams by Example

| Cue / Question | Notes |
| --- | --- |
| Word count — which DSL pieces does it exercise (flatMapValues/groupBy/count, a repartition, a changelog-backed KTable)? | |
| Stock market statistics — what does it add (windowed aggregations over event time, custom serdes)? | |
| ClickStream enrichment — what does it demonstrate (stream-table join for profiles + windowed stream-stream join for searches vs clicks)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Kafka Streams: Architecture Overview

| Cue / Question | Notes |
| --- | --- |
| How does the DSL become execution (topology → tasks, one task per input partition — the unit of parallelism)? | |
| How do you scale (more threads per instance, more instances in the same consumer group; repartition topics split the topology into independent sub-topologies)? | |
| How do you test a topology (`TopologyTestDriver`, plus real end-to-end tests)? | |
| How does Streams survive failures (offsets + changelog topics restore state, standby replicas cut recovery time, consumer-group rebalance reassigns tasks — static membership/cooperative rebalancing reduce churn)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Stream Processing Use Cases

| Cue / Question | Notes |
| --- | --- |
| Which use cases fit stream processing well (customer-service event propagation, IoT, fraud detection — where minutes-not-milliseconds context matters)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## How to Choose a Stream Processing Framework

| Cue / Question | Notes |
| --- | --- |
| How does the application type steer the choice (ingest → maybe Connect instead; millisecond latency → maybe not streams; async microservices vs near-real-time analytics)? | |
| Beyond features, what actually decides it (operability, maturity and community, how well it integrates with your Kafka estate)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw: source topic partitions --> tasks (local state store + changelog topic) --> repartition topic --> downstream tasks --> sink topic ; instances/threads hosting tasks via one consumer group
flowchart LR
```
