# 4. Kafka Consumers: Reading Data from Kafka

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## Kafka Consumer Concepts

| Cue / Question | Notes |
| --- | --- |
| How does a consumer group divide a topic's partitions, and what caps the parallelism? | |
| Eager vs. cooperative (incremental) rebalance — what's the difference, and why does cooperative cut downtime? | |
| What triggers a rebalance, and who coordinates it (group coordinator / consumer leader)? | |
| What problem does static group membership (`group.instance.id`) solve? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Creating a Kafka Consumer

| Cue / Question | Notes |
| --- | --- |
| Which properties are required (`bootstrap.servers`, key/value deserializers)? | |
| What does `group.id` do, and when can it be omitted? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Subscribing to Topics

| Cue / Question | Notes |
| --- | --- |
| `subscribe` (list vs. regex) vs. `assign` — what's the difference, and when use each? | |
| What's the risk of a regex subscription on a large cluster? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## The Poll Loop

| Cue / Question | Notes |
| --- | --- |
| Why is `poll()` the heart of the consumer — what does it do *besides* fetch records (heartbeats, rebalances, coordination)? | |
| What is the poll timeout for? | |
| What happens if you don't poll often enough (`max.poll.interval.ms`)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Thread Safety

| Cue / Question | Notes |
| --- | --- |
| What is the one-consumer-per-thread rule, and what are the patterns for scaling consumption beyond it? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Configuring Consumers

| Cue / Question | Notes |
| --- | --- |
| `fetch.min.bytes` / `fetch.max.wait.ms` — how do they trade latency for efficiency? | |
| `max.partition.fetch.bytes` / `fetch.max.bytes` / `max.poll.records` — how do they bound a single poll? | |
| `session.timeout.ms` vs. `heartbeat.interval.ms` vs. `max.poll.interval.ms` — what does each one detect? | |
| `auto.offset.reset` — `earliest` vs. `latest`, and *when* does it apply? | |
| `enable.auto.commit` — what does it do, and what's the risk? | |
| `partition.assignment.strategy` — Range / RoundRobin / Sticky / Cooperative Sticky trade-offs? | |
| `client.rack` — what does fetching from the closest replica buy you? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Commits and Offsets

| Cue / Question | Notes |
| --- | --- |
| What does "committing an offset" actually mean, and where are offsets stored? | |
| Automatic commit — how can it cause duplicates *or* lost messages? | |
| `commitSync` vs. `commitAsync` — trade-offs, and how do you combine them (sync in `finally`)? | |
| How (and why) do you commit a specific offset partway through a batch? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Rebalance Listeners

| Cue / Question | Notes |
| --- | --- |
| What are `onPartitionsRevoked` / `onPartitionsAssigned` / `onPartitionsLost` for, and what must you do in *revoked*? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Consuming Records with Specific Offsets

| Cue / Question | Notes |
| --- | --- |
| How do `seek` / `seekToBeginning` / `seekToEnd` let you reprocess or skip records? | |
| How can you store offsets *with* results to get exactly-once-ish processing? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## But How Do We Exit?

| Cue / Question | Notes |
| --- | --- |
| How do you cleanly break a poll loop from another thread (`wakeup()`), and what exception signals it? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Deserializers

| Cue / Question | Notes |
| --- | --- |
| Why must deserializers match serializers, and why are custom ones fragile? | |
| How does Avro deserialization reconcile the writer's schema with the reader's schema? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Standalone Consumer: Why and How to Use a Consumer Without a Group

| Cue / Question | Notes |
| --- | --- |
| When would you use `assign()` without a group, and what do you give up (no rebalance, manual partition handling)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw: topic(partitions 0..N) --> consumer group(members) ; poll loop --> process --> commit offset
flowchart LR
```
