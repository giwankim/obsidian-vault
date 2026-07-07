# 9. The Trouble with Distributed Systems

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch09.html>
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references)

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions.
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

**Status:** not started

## Faults and Partial Failures

| Cue / Question | Notes |
| --- | --- |
| What makes **partial failure** the defining property of distributed systems — and why is it *nondeterministic*? | |
| How do supercomputers and cloud computing handle faults differently, and why does cloud hardware force fault tolerance into software? | |
| Why "build a reliable system from unreliable components" — where does that philosophy come from (TCP over IP, error-correcting codes)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Unreliable Networks

| Cue / Question | Notes |
| --- | --- |
| When you send a request and hear nothing back, what are *all* the things that might have happened? (why you can't tell) | |
| How common are network faults in practice, and what's a **network partition**? | |
| How do you **detect** a faulty node — and why is every mechanism imperfect? | |
| Why can't you pick a "correct" **timeout**? What are **unbounded delays**, and where does queueing happen (switches, OS, GC, virtualization)? | |
| **Synchronous vs. asynchronous networks**: why does the phone network get bounded delay while TCP doesn't? (circuit-switched reserved capacity vs. packet-switched sharing) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Unreliable Clocks

| Cue / Question | Notes |
| --- | --- |
| **Time-of-day vs. monotonic clocks**: what is each for, and which must you use for measuring durations? | |
| How badly do clocks drift, and what does NTP actually achieve? | |
| What goes wrong when you rely on synchronized clocks — e.g. **last-write-wins** across nodes? | |
| How do Spanner-style systems use **clock confidence intervals** (TrueTime) to get ordering from clocks? | |
| **Process pauses**: what can stop a running thread for seconds (GC, VM migration, disk I/O, paging), and why does that break "I'm still the leader" reasoning? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Knowledge, Truth, and Lies

| Cue / Question | Notes |
| --- | --- |
| Why can no node trust its own judgment ("I'm alive, I hold the lock") — and how does the **majority (quorum)** define truth instead? | |
| How do **fencing tokens** protect a resource from a paused ex-leader who still thinks it holds the lock? | |
| What are **Byzantine faults**, and when is Byzantine fault tolerance worth it (and when is it not)? | |
| What is a **system model** (synchronous, partially synchronous, asynchronous × crash-stop, crash-recovery, Byzantine), and why do proofs need one? | |
| Safety vs. liveness: how do the guarantees differ? ("nothing bad ever happens" vs. "something good eventually happens") | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Summary (the book's own)

| Cue / Question | Notes |
| --- | --- |
| What's the chapter's message — networks, clocks, and pauses can all betray you, so design for it? | |
| Anything the book highlights that the notes above missed? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Sketch the classic split-brain timeline: leader pauses (GC), followers elect
%% a new leader, old leader wakes and writes — then add the fencing token
%% that saves the day.
sequenceDiagram
```

## Open Questions / Follow-Ups

- [ ]

## Connections

- [[00-ddia-moc]] — chapter map / index.
- [[02-defining-nonfunctional-requirements]] — unbounded delays and queueing are the mechanism behind tail latency there.
- [[06-replication]] — failover hazards previewed there (split brain, timeouts) get their theory here.
- [[08-transactions]] — the in-doubt coordinator problem is partial failure in miniature.
- [[10-consistency-and-consensus]] — this chapter poses the problems; that one buys back guarantees with consensus.
