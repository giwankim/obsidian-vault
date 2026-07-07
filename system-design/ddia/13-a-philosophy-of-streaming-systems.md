# 13. A Philosophy of Streaming Systems

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch13.html>
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references)

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions.
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

**Status:** not started

## Data Integration

| Cue / Question | Notes |
| --- | --- |
| Why does any nontrivial application end up combining *specialized* tools — and what problem does that create? (keeping copies of the same data in sync) | |
| Why is an ordered **log of events** a better integration backbone than dual writes? (deterministic replay, total order, loose coupling) | |
| Batch vs. stream for deriving data: what do **lambda** and **kappa**-style architectures each propose, and what's the critique of maintaining two codepaths? | |
| Where does total order break down at scale? (ordering across shards/services/datacenters — no global order) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Unbundling Databases

| Cue / Question | Notes |
| --- | --- |
| What does it mean to "unbundle the database" — which internal components (indexes, materialized views, replication, triggers) reappear as separate systems? | |
| How is a stream processor maintaining a **materialized view** just index-building writ large? | |
| *Federation* (unified reads) vs. *unbundling* (unified writes): why is synchronizing writes the hard part? | |
| When is one integrated database enough — when is unbundling worth its complexity? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Designing Applications Around Dataflow

| Cue / Question | Notes |
| --- | --- |
| What does application code look like when the app is a **derivation function** over event streams? (state changes flow in, derived views flow out) | |
| How do stable message ordering and fault-tolerant processing make derived data **maintainable**? (rebuild from the log after bugs) | |
| How can dataflow extend to the client — subscribing to changes instead of polling state? (end-to-end event streams) | |
| Reads as events: what does it mean to route queries through the log too, and what does it cost? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Aiming for Correctness

| Cue / Question | Notes |
| --- | --- |
| Why aren't transactions alone enough for **end-to-end correctness**? (the client's retry after a timeout — exactly-once needs an end-to-end **operation ID**) | |
| What is the **end-to-end argument**, and what does it imply about where to enforce correctness (application, not just infrastructure)? | |
| How can **uniqueness and other constraints** be enforced with logs instead of distributed transactions? (partition by the constrained key; a stream processor decides) | |
| **Timeliness vs. integrity**: why does Kleppmann argue integrity matters far more — and how do loosely-coupled, apology-based real-world processes (compensation) fit in? | |
| How do you maintain integrity **in the face of software bugs**? (immutable events, recompute derived state, audit) | |
| "Trust, but verify" — why audit even without Byzantine actors? (self-validating systems, checking data integrity end to end) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Summary (the book's own)

| Cue / Question | Notes |
| --- | --- |
| What's the philosophy in one line — derive everything from immutable event logs, and enforce correctness end to end? | |
| Anything the book highlights that the notes above missed? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Sketch the log-centric architecture: one event log fanning out to
%% search index, cache, warehouse, and app views — then mark where a bug's
%% bad data gets fixed by replaying the log.
flowchart LR
```

## Open Questions / Follow-Ups

- [ ]

## Connections

- [[00-ddia-moc]] — chapter map / index.
- [[03-data-models-and-query-languages]] — event sourcing and CQRS were the preview; this is the full worldview.
- [[11-batch-processing]] — immutable inputs + recomputation, generalized from jobs to always-on systems.
- [[12-stream-processing]] — the mechanisms (logs, CDC, processors) that this chapter builds a philosophy from.
- [[08-transactions]] — end-to-end operation IDs pick up where exactly-once and idempotence left off.
