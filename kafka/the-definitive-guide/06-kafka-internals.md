# 6. Kafka Internals

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## Cluster Membership

| Cue / Question | Notes |
| --- | --- |
| How does a broker join the cluster (registers an ephemeral ZNode under `/brokers/ids` with its unique `broker.id`)? | |
| What happens when a broker leaves (ephemeral node disappears, watchers fire) — and why does its ID live on (replica assignments keep it; a replacement broker with the same ID inherits its work)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## The Controller

| Cue / Question | Notes |
| --- | --- |
| How is the controller elected (first broker to create the ephemeral `/controller` ZNode wins; others watch it)? | |
| What is the controller responsible for (electing partition leaders when brokers join/leave, persisting state to ZK, pushing LeaderAndIsr/UpdateMetadata to brokers)? | |
| How does the controller epoch prevent split brain (brokers ignore requests carrying an older epoch — zombie fencing)? | |
| Why is ZooKeeper being replaced by KRaft (metadata inconsistencies between ZK and controller pushes; failover/restart time grows with partition count; two systems to secure and operate)? | |
| How does KRaft work (Raft quorum of controllers replicating a metadata event log; active controller = quorum leader; brokers pull metadata deltas instead of receiving pushes)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Replication

| Cue / Question | Notes |
| --- | --- |
| Why is replication called "the heart of Kafka," and what do leader vs follower replicas each do? | |
| What makes a follower "in sync" (fetching the latest messages continuously, within `replica.lag.time.max.ms`), and what happens to out-of-sync replicas? | |
| What is the preferred leader, and why should leadership stay balanced across brokers? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Request Processing

| Cue / Question | Notes |
| --- | --- |
| How does the broker's threading model process a request (acceptor → network/processor threads → request queue → I/O handler threads → response queue)? | |
| How do clients know which broker to talk to (metadata requests, cached routing, refresh on NotLeader errors or `metadata.max.age.ms`)? | |
| What does the leader do with a produce request (validate ACLs/`acks`/leadership, write to the filesystem page cache — no fsync wait, park in purgatory until ISR ack for `acks=all`)? | |
| How are fetch requests served efficiently (offset validity check, zero-copy from page cache to network, `fetch.min.bytes` + `max.wait` batching via purgatory)? | |
| Why do consumers only see "committed" messages (high-water mark — records not yet replicated to all in-sync replicas are withheld)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Physical Storage

| Cue / Question | Notes |
| --- | --- |
| What is Kafka's basic storage unit (the partition replica — a directory of segment files under `log.dirs`; segments split by size/time; the active segment is never deleted)? | |
| What problem does tiered storage solve (local + remote tier; near-unlimited retention, cheaper storage, faster recovery and rebalancing, elasticity)? | |
| How are partitions allocated (round-robin spreading leaders and replicas across brokers and racks; disks chosen by partition count, not size)? | |
| Why is the on-disk format identical to the wire format (zero-copy sends, no recompression), and what does a record batch contain (headers, offsets deltas, timestamps, keys/values)? | |
| What do the two per-segment indexes map (offset → file position; timestamp → offset), and what happens if they're corrupted (rebuilt from the log)? | |
| How does compaction work (cleaner threads, clean vs dirty section, in-memory offset map of latest key offsets, rewrite retaining newest value per key)? | |
| How are deletes handled in a compacted topic (tombstone = null value, retained for `delete.retention.ms` so consumers can see it)? | |
| When does compaction actually run (never on the active segment; dirty ratio threshold — 50% by default; `min/max.compaction.lag.ms` bounds)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw: request path — client --> acceptor --> network threads --> request queue --> I/O threads --> (purgatory) --> response queue --> network threads ; plus leader/follower replication feeding the high-water mark
flowchart LR
```
