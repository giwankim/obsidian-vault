# 10. Consistency and Consensus

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch10.html>
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references)

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions.
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

**Status:** not started

## Consistency Guarantees

| Cue / Question | Notes |
| --- | --- |
| Why isn't **eventual consistency** enough for application programmers? (it's a weak, hard-to-test promise) | |
| How is the hierarchy of consistency models like transaction isolation levels — and how is it different? (concurrency anomalies vs. replication/fault anomalies) | |
| What's the plan of the chapter — linearizability, ordering/causality, consensus — and how do they build on each other? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Linearizability

| Cue / Question | Notes |
| --- | --- |
| Define **linearizability** in one sentence. (make the system appear as one copy of the data, operations atomic in real-time order) | |
| How does linearizability differ from **serializability** — and what is *strict serializability*? | |
| Where do you genuinely need it? (locking & leader election, uniqueness constraints, cross-channel dependencies) | |
| Which replication schemes can (and can't) be linearizable? (single-leader maybe, quorums surprisingly not without extra work) | |
| What does the **CAP theorem** actually say — and why is "CA/CP/AP" pigeonholing misleading? | |
| Why do systems drop linearizability even without partitions? (performance — latency, not just fault tolerance) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## ID Generators and Logical Clocks

| Cue / Question | Notes |
| --- | --- |
| Why does causality need an *ordering*, and why is a total real-time order overkill? (causal consistency as the sweet spot) | |
| Why are auto-increment IDs, wall-clock timestamps, and random UUIDs each flawed as event orderings? | |
| How do **Lamport timestamps** produce a total order consistent with causality — and what *can't* they do (uniqueness at write time)? | |
| What are **hybrid logical clocks** / Snowflake-style ID generators, and what do they trade? | |
| Why isn't knowing the order after-the-fact enough for things like uniqueness constraints? (→ you need consensus) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Consensus

| Cue / Question | Notes |
| --- | --- |
| What is **total order broadcast**, and why is it equivalent to repeated consensus? | |
| What properties must consensus satisfy? (uniform agreement, integrity, validity, termination) | |
| How does **Raft** work at a high level — leader election with **terms/epochs**, log replication, quorum overlap between election and commit? | |
| How does consensus-based commit fix what's broken in 2PC? (no single stuck coordinator; majority makes progress) | |
| What do coordination services (**ZooKeeper / etcd**) provide, and how do apps use them? (locks, leader election, membership, service discovery) | |
| What does consensus cost, and when is it not worth it? (majority round-trips, sensitivity to network conditions) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Summary (the book's own)

| Cue / Question | Notes |
| --- | --- |
| Which problems does the chapter show to be *equivalent* to consensus? (linearizable CAS, total order broadcast, locks, uniqueness, membership) | |
| Anything the book highlights that the notes above missed? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Sketch a Raft election + commit: leader with term N, follower quorum,
%% a partition, a new election at term N+1, and why the old leader's
%% unreplicated entries die.
sequenceDiagram
```

## Open Questions / Follow-Ups

- [ ]

## Connections

- [[00-ddia-moc]] — chapter map / index.
- [[06-replication]] — safe failover/leader election is finally solved here.
- [[08-transactions]] — 2PC's stuck-coordinator flaw is repaired by consensus-backed commit.
- [[09-the-trouble-with-distributed-systems]] — consensus is the answer to that chapter's problems, at a price.
- [[12-stream-processing]] — total order broadcast is exactly an append-only log: the bridge to Part III.
