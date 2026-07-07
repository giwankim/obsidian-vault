# 8. Transactions

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch08.html>
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references)

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions.
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

**Status:** not started

## The Meaning of ACID

| Cue / Question | Notes |
| --- | --- |
| What problem do transactions solve for the *application programmer*? (a whole class of partial-failure and concurrency errors collapses into "retry") | |
| **Atomicity**: what does it actually mean here (abortability, *not* concurrency)? | |
| **Consistency**: why is the C "just there to make the acronym work" — whose job is it really? | |
| **Isolation**: what does serializability promise in principle? | |
| **Durability**: what does a durability promise rest on (fsync, WAL, replication) — and can it ever be absolute? | |
| What can go wrong when **retrying** an aborted transaction? (it actually committed but the ack was lost; overload; side effects outside the DB) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Single-Object and Multi-Object Operations

| Cue / Question | Notes |
| --- | --- |
| What do single-object atomicity and isolation give you, and why aren't they "transactions"? | |
| When do you genuinely *need* multi-object transactions? (foreign keys, secondary indexes, denormalized data staying in sync) | |
| Why did many distributed datastores drop multi-object transactions, and what did applications lose? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Weak Isolation Levels

| Cue / Question | Notes |
| --- | --- |
| Why do databases ship weak isolation by default instead of serializability? | |
| **Read committed**: what are *dirty reads* and *dirty writes*, and how are they prevented? | |
| **Snapshot isolation**: what anomaly (read skew / nonrepeatable read) does it fix, and how does **MVCC** implement it? | |
| **Lost updates**: give a concrete example (read-modify-write). Compare fixes: atomic operations, explicit locking (`FOR UPDATE`), automatic detection, compare-and-set. | |
| **Write skew**: how does it generalize lost updates? Walk through the on-call-doctors example. | |
| What are **phantoms**, and why does write skew often hinge on a query whose result another write changes? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Serializability

| Cue / Question | Notes |
| --- | --- |
| **Actual serial execution**: what makes running transactions one-at-a-time feasible today? (in-memory data, stored procedures, short transactions) | |
| **Two-phase locking (2PL)**: how do shared/exclusive locks enforce serializability, and what does it cost? (blocked readers/writers, deadlocks, unstable latencies) | |
| What are **predicate locks** and **index-range locks** for? (locking objects that don't exist yet — phantoms) | |
| **Serializable snapshot isolation (SSI)**: how does *optimistic* concurrency control detect dangerous dependencies instead of blocking? | |
| When does SSI perform well vs. poorly? (abort rate under contention) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Distributed Transactions

| Cue / Question | Notes |
| --- | --- |
| What does **two-phase commit (2PC)** guarantee, and how do prepare/commit phases achieve it? | |
| Why is the **coordinator** a single point of failure — what happens to participants stuck **in doubt**? | |
| What are **XA transactions**, and why are they operationally painful in practice? | |
| How do modern distributed databases do better than XA? (internal consensus-backed commit rather than heterogeneous 2PC) | |
| What is **exactly-once semantics** in this context, and how do idempotence and atomic commit relate? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Summary (the book's own)

| Cue / Question | Notes |
| --- | --- |
| Can you rank the isolation levels and name the anomaly each one eliminates? | |
| Anything the book highlights that the notes above missed? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Sketch the isolation ladder: read committed -> snapshot isolation -> serializable,
%% annotating each rung with the anomaly it kills (dirty read, read skew,
%% lost update, write skew). Or: the 2PC message flow with a coordinator crash.
flowchart TB
```

## Open Questions / Follow-Ups

- [ ]

## Connections

- [[00-ddia-moc]] — chapter map / index.
- [[06-replication]] — "transactions exist so apps don't have to handle replication-lag anomalies themselves."
- [[09-the-trouble-with-distributed-systems]] — why coordinators fail and messages get lost: the failure models behind 2PC's pain.
- [[10-consistency-and-consensus]] — atomic commit is a cousin of consensus; this chapter's 2PC meets Raft there.
