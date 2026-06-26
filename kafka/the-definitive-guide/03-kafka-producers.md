# 3. Kafka Producers: Writing Messages to Kafka

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## Producer Overview

| Cue / Question | Notes |
| --- | --- |
| What are the steps a record takes through the producer (ProducerRecord → serialize → partition → batch → send)? | |
| Where do batches live, and what does the sender (I/O) thread do with them? | |
| How do success, failure, and retries flow back to the caller? | |
| When would you reach for Kafka Connect instead of writing a producer? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Constructing a Kafka Producer

| Cue / Question | Notes |
| --- | --- |
| Which three properties are mandatory (`bootstrap.servers`, `key.serializer`, `value.serializer`)? | |
| Why specify a key serializer even when you only ever send values? | |
| What are the three ways to send a message (fire-and-forget, synchronous, asynchronous)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Sending a Message to Kafka

| Cue / Question | Notes |
| --- | --- |
| Fire-and-forget — what guarantees do you give up? | |
| Synchronous send — how does `.get()` on the returned `Future` work, and what does it cost? | |
| Asynchronous send — how does a `Callback` report completion, and on which thread does it run? | |
| Retriable vs. non-retriable errors — how does the producer treat each? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Configuring Producers

| Cue / Question | Notes |
| --- | --- |
| `acks` — what do `0`, `1`, and `all` mean for the durability vs. latency trade-off? | |
| What stages make up *message delivery time*, and which timeouts bound each (`max.block.ms`, `delivery.timeout.ms`, `request.timeout.ms`, `retries`, `retry.backoff.ms`)? | |
| `linger.ms` and `batch.size` — how do they trade latency for throughput? | |
| `buffer.memory` — what happens when it fills up? | |
| `compression.type` — what are the options and their trade-offs? | |
| `max.in.flight.requests.per.connection` — how does it affect ordering, and how does idempotence change that? | |
| `max.request.size` — what does it cap, and what must stay consistent on the broker? | |
| `enable.idempotence` — what does it guarantee, and which other configs must it agree with? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Serializers

| Cue / Question | Notes |
| --- | --- |
| Why are custom serializers discouraged, and what breaks as schemas evolve? | |
| What does Avro give you, and what is the Schema Registry's role? | |
| When using Avro with Kafka, how are the schema and the data physically separated? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Partitions

| Cue / Question | Notes |
| --- | --- |
| How is a record's partition chosen when the key is `null` vs. non-null? | |
| What does the default partitioner guarantee about same-key records, and what breaks that guarantee? | |
| When and why would you write a custom partitioner? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Headers

| Cue / Question | Notes |
| --- | --- |
| What are record headers for, and why use them instead of encoding metadata in the key or value? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Interceptors

| Cue / Question | Notes |
| --- | --- |
| What can a `ProducerInterceptor` hook into, and what are typical uses (monitoring, lineage) without touching app code? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Quotas and Throttling

| Cue / Question | Notes |
| --- | --- |
| What quota types can a broker enforce (produce, consume, request)? | |
| How does the broker throttle a client that exceeds its quota, and how does the client observe it? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw: ProducerRecord --> serializer --> partitioner --> record batches --> sender thread --> broker (acks back)
flowchart LR
```
