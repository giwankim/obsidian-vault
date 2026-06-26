# 1. Meet Kafka

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## Publish/Subscribe Messaging

| Cue / Question | Notes |
| --- | --- |
| What pain do direct point-to-point connections create as systems grow? | |
| What problem does a single metrics-dashboard example expose? | |
| Why do teams end up with many separate queue systems? | |
| What does a pub/sub message broker fundamentally decouple? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Enter Kafka

| Cue / Question | Notes |
| --- | --- |
| What *is* a message in Kafka? What is the key for? | |
| Why batch messages? What's the trade-off? | |
| What do schemas decouple, and why does that matter? | |
| Topic vs. partition — what's the unit of ordering, and its scope? | |
| What is an offset and who owns it? | |
| How does a consumer group divide a topic's partitions? | |
| Broker vs. cluster vs. controller — what does each do? | |
| What is replication (leader/follower) protecting against? | |
| Why run multiple clusters? What is MirrorMaker for? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Why Kafka?

| Cue / Question | Notes |
| --- | --- |
| How does Kafka support multiple producers cleanly? | |
| How can many consumers read the same stream independently? | |
| Why is disk-based retention a feature, not a bug? | |
| What makes Kafka horizontally scalable? | |
| Where does its high performance / low latency come from? | |
| What do Kafka Connect and Kafka Streams add beyond messaging? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## The Data Ecosystem

| Cue / Question | Notes |
| --- | --- |
| Activity tracking — what's the use case? | |
| Messaging — how is it different from a traditional broker here? | |
| Metrics & logging — why does Kafka fit? | |
| Commit log — what's the insight? | |
| Stream processing — what does it enable? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Kafka's Origin

| Cue / Question | Notes |
| --- | --- |
| What was LinkedIn's original problem? | |
| Why build something new instead of using existing tools? | |
| Open source, commercial engagement, and the name? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw producers --> topic(partitions 0..N) --> consumer group(s)
flowchart LR
```
