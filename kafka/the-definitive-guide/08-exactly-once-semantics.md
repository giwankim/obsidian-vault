# 8. Exactly-Once Semantics

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## Idempotent Producer

| Cue / Question | Notes |
| --- | --- |
| What duplicate problem does the idempotent producer solve (a retry re-sending a message the broker already wrote)? | |
| How does it work mechanically — producer ID (PID) + per-partition sequence numbers, and broker-side dedup? | |
| What are its limitations (dedups only retries within one producer session, per partition — not cross-session, not multi-partition atomicity)? | |
| How do you enable it (`enable.idempotence=true`), and which configs does it require/imply (`acks=all`, retries > 0, `max.in.flight.requests<=5`)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Transactions

| Cue / Question | Notes |
| --- | --- |
| Which use case do transactions target — the consume-process-produce (read-process-write) loop of stream processing? | |
| What problems do transactions solve (atomic writes across multiple partitions **and** committing consumer offsets atomically with the output)? | |
| How do transactions guarantee exactly-once (`transactional.id`, zombie fencing via epochs, atomic commit, `read_committed` consumers)? | |
| What do transactions **not** solve (side effects to external systems — DB writes, RPCs, emails; only Kafka-to-Kafka)? | |
| How do you use them — `transactional.id`, `initTransactions` / `beginTransaction` / `sendOffsetsToTransaction` / `commitTransaction`, or just `processing.guarantee=exactly_once` in Kafka Streams? | |
| How do transactions work internally — transaction coordinator, transaction log, commit/abort markers, two-phase commit? | |
| What does consumer `isolation.level=read_committed` do, and how does the Last Stable Offset (LSO) hide aborted/in-flight records? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Performance of Transactions

| Cue / Question | Notes |
| --- | --- |
| What overhead do transactions add (coordinator round-trips, markers), and how does transaction/batch size amortize it? | |
| When is the cost justified vs. just using the idempotent producer alone? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw: consume --> process --> produce + sendOffsetsToTransaction, all inside begin/commitTransaction ; coordinator writes commit/abort markers ; read_committed consumer reads up to LSO
flowchart LR
```
