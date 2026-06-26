# 7. Reliable Data Delivery

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## Reliability Guarantees

| Cue / Question | Notes |
| --- | --- |
| Which guarantees does Kafka actually provide (order within a partition, a committed message survives while ≥1 ISR is alive, consumers read only committed messages)? | |
| What's the difference between a *committed message* and a *committed offset*, and why is it easy to confuse them? | |
| Why is reliability a system-wide trade-off (durability vs. throughput / latency / cost) rather than a single switch? | |

**Summary:**
- Order guarantee of messages in a partition.
	- If message B was written after message A using the same producer in the same partition, then the offset of message B will be higher than message A.
- Produced messages are considered "committed" when they were written to the partition on all its in-sync replicas (but not necessarily flushed to disk).
	- Producers can choose to receive acknowledgments of sent messages when the message was fully committed, when it was written to the leader, or when it was sent over the network.
- Messages that are committed will not be lost as long as least one replica remains alive.
- Consumers can only read messages that are committed.

## Replication

| Cue / Question                                                                        | Notes |
| ------------------------------------------------------------------------------------- | ----- |
| What makes a replica *in-sync* (ISR), and what must it keep doing to stay in the set? |       |
| Why is the **ISR** — not the replication factor — the real determinant of durability? |       |
| What happens to availability and durability when a replica drops out of the ISR?      |       |

**Summary:**
<!-- 1-2 sentences, your words -->

## Broker Configuration

| Cue / Question | Notes |
| --- | --- |
| `replication.factor` / `default.replication.factor` — how do you choose N, and what does RF=3 buy you? | |
| `unclean.leader.election.enable` — what's the availability-vs-durability trade-off of letting an out-of-sync replica become leader? | |
| `min.insync.replicas` — how does it pair with `acks=all` to *refuse* a write rather than risk losing it? | |
| How does broker/rack placement change how many simultaneous failures you can survive? | |
| Why does Kafka lean on the OS page cache instead of fsync-per-message, and what does that imply for durability? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Using Producers in a Reliable System

| Cue / Question | Notes |
| --- | --- |
| `acks=0` / `1` / `all` — what does each acknowledge, and what can be lost under each? | |
| Why can a perfectly configured broker still lose data if the *producer* is misconfigured? | |
| Which errors are retriable (handled by Kafka) vs. which must the app handle itself (serialization, non-retriable broker errors)? | |
| How do producer retries create duplicates, and how does that motivate the idempotent producer (ch. 8)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Using Consumers in a Reliable System

| Cue / Question | Notes |
| --- | --- |
| `group.id`, `auto.offset.reset`, `enable.auto.commit`, `auto.commit.interval.ms` — how does each affect reliable processing? | |
| Why commit offsets only *after* processing, and what's the duplicate-vs-loss trade-off of when you commit? | |
| How do you handle long processing time, retries, and rebalances without losing or double-processing records? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Validating System Reliability

| Cue / Question | Notes |
| --- | --- |
| How do you validate *configuration* before trusting it (e.g. `VerifiableProducer` / `VerifiableConsumer`, Trogdor)? | |
| Which failure scenarios should you deliberately inject (leader election, rolling restart, network partition)? | |
| What do you monitor in *production* to confirm reliability (under-replicated partitions, consumer lag, error rates)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw: producer(acks=all) --> leader --> ISR replication (min.insync.replicas) ; consumer --> process --> commit offset AFTER processing
flowchart LR
```
