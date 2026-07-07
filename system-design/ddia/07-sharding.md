# 7. Sharding

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch07.html>
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references)

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions.
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

**Status:** not started

## Pros and Cons of Sharding

| Cue / Question | Notes |
| --- | --- |
| Why shard? (dataset or write throughput beyond one node; shared-nothing scale-out) | |
| What does sharding cost you? (cross-shard queries and transactions, rebalancing, operational complexity) | |
| How do sharding and **replication** compose? (each shard has its own leader/followers) | |
| When should you *not* shard — what can you do instead? (scale up, read replicas, caching) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Sharding of Key-Value Data

| Cue / Question | Notes |
| --- | --- |
| What's the goal — spread load evenly — and what is **skew** / a **hot spot**? | |
| **Key-range sharding**: what does it enable (range scans) and how does it go wrong (hot ranges, e.g. timestamps)? | |
| **Hash-based sharding**: what does it fix and what does it sacrifice? (even spread vs. losing key adjacency) | |
| What is **consistent hashing**, and what problem does it actually solve? | |
| How do you cope with a single hot key (e.g. a celebrity)? (salting/splitting the key, application-level strategies) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Sharding and Secondary Indexes

| Cue / Question | Notes |
| --- | --- |
| Why do secondary indexes not map neatly onto shards? | |
| **Local (document-partitioned)** indexes: why are writes cheap but reads **scatter/gather**? | |
| **Global (term-partitioned)** indexes: why are reads targeted but writes distributed (and often async)? | |
| Which approach do real systems pick, and why? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Rebalancing Shards

| Cue / Question | Notes |
| --- | --- |
| Why is `hash mod N` a terrible rebalancing strategy? | |
| **Fixed number of shards** (more shards than nodes): how does it work, and what must you get right up front? | |
| **Dynamic sharding** (split/merge like a B-tree): what does it adapt to? | |
| Sharding **proportional to nodes**: how does it differ? | |
| Automatic vs. manual rebalancing — why is fully automatic risky? (rebalancing + failure detection = cascading failure) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Request Routing

| Cue / Question | Notes |
| --- | --- |
| When a client wants key X, how does the request find the right node? (three options: any node forwards, routing tier, shard-aware client) | |
| How do systems keep routing metadata consistent — where does a coordination service (e.g. **ZooKeeper/etcd**) fit? | |
| What happens to routing during a rebalance? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Summary (the book's own)

| Cue / Question | Notes |
| --- | --- |
| Can you connect the three design axes — how keys map to shards, how indexes are sharded, how shards move? | |
| Anything the book highlights that the notes above missed? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Sketch key-range vs hash sharding for the same key space, then add a
%% rebalance: node joins, which shards move, how the router learns about it.
flowchart LR
```

## Open Questions / Follow-Ups

- [ ]

## Connections

- [[00-ddia-moc]] — chapter map / index.
- [[04-storage-and-retrieval]] — secondary indexes from the storage chapter return here with a distribution problem.
- [[06-replication]] — sharding splits the data; replication copies each piece; real systems do both.
- [[10-consistency-and-consensus]] — routing metadata and shard assignment lean on coordination services / consensus.
