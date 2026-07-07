# 6. Replication

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch06.html>
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references)

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions.
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

**Status:** not started

## Single-Leader Replication

| Cue / Question | Notes |
| --- | --- |
| Why replicate at all? (latency/locality, availability, read throughput) | |
| How does **leader-based replication** work — who accepts writes, who serves reads? | |
| **Synchronous vs. asynchronous** replication: what does each guarantee, and why is fully-sync impractical? (semi-synchronous as the compromise) | |
| How do you set up a **new follower** without downtime? (consistent snapshot + log position, catch-up) | |
| What happens on follower failure vs. **leader failure**? Walk through **failover** and its hazards (lost writes, split brain, timeout tuning). | |
| How are replication logs implemented — statement-based, **WAL shipping**, **logical (row-based)** — and what are the trade-offs? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Problems with Replication Lag

| Cue / Question | Notes |
| --- | --- |
| What is **eventual consistency**, and why is "eventually" a weak promise? | |
| **Read-after-write (read-your-writes)** consistency: what anomaly does it prevent, and how can you implement it? | |
| **Monotonic reads**: what anomaly (time moving backwards) does it prevent? | |
| **Consistent prefix reads**: what causality anomaly does it prevent? | |
| Why push these guarantees into the database rather than handle lag in application code — i.e., why do **transactions** exist? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Multi-Leader Replication

| Cue / Question | Notes |
| --- | --- |
| When is multi-leader worth its complexity? (multi-datacenter, **clients with offline operation**, **collaborative editing**) | |
| Why are **write conflicts** the defining problem, and what does conflict *detection* look like when it's asynchronous? | |
| What are the options for **conflict resolution**? (avoidance, last-write-wins, merge, custom logic; on-write vs. on-read) | |
| What are **CRDTs**, and how do they resolve conflicts automatically? | |
| How do replication **topologies** (circular, star, all-to-all) differ, and what ordering problems arise? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Leaderless Replication

| Cue / Question | Notes |
| --- | --- |
| How do Dynamo-style systems accept writes with **no leader at all**? (client/coordinator writes to several replicas) | |
| How do **quorums** work — what must be true of `w + r > n`, and what does it *not* guarantee? | |
| How does data get repaired? (**read repair** and **anti-entropy**) | |
| What are **sloppy quorums** and **hinted handoff**, and what do they trade away? | |
| How are **concurrent writes** detected and handled? (happens-before, **version vectors**, siblings, last-write-wins dangers) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Summary (the book's own)

| Cue / Question | Notes |
| --- | --- |
| Can you place single-leader, multi-leader, and leaderless on one spectrum of consistency vs. availability/flexibility? | |
| Anything the book highlights that the notes above missed? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Sketch the three topologies side by side: single-leader (writes -> leader -> followers),
%% multi-leader (two DCs, conflict arrows), leaderless (client -> n replicas, w/r quorum).
flowchart LR
```

## Open Questions / Follow-Ups

- [ ]

## Connections

- [[00-ddia-moc]] — chapter map / index.
- [[05-encoding-and-evolution]] — replication logs are dataflow through databases; log formats need the same evolvability.
- [[07-sharding]] — replication and sharding compose: each shard is itself replicated.
- [[09-the-trouble-with-distributed-systems]] — failover's hazards (timeouts, split brain) get their full explanation there.
- [[10-consistency-and-consensus]] — electing a leader safely is a consensus problem.
