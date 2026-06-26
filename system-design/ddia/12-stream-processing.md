# Stream Processing (DDIA 2nd ed., Chapter 12)

> Source: [Designing Data-Intensive Applications, 2nd Edition — Chapter 12: Stream Processing](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch12.html)
> Authors: Martin Kleppmann, Chris Riccomini (O'Reilly, 2nd edition)
> Book site: [dataintensive.net](https://dataintensive.net/)
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references) (per-chapter links to the papers cited in the book)

<!--
Citation convention for these notes:
- Direct quotes in blockquotes, followed by: — ch. 12, "Section Name", p. NNN
- Paraphrased ideas: cite the section name inline, e.g. (ch. 12, "Messaging Systems")
- External papers/posts the book references: link them where mentioned and
  find the canonical link in ept/ddia-references.
-->

**Status:** reading — currently at: _Transmitting Event Streams_

## TL;DR

<!-- Fill in last: 3–5 sentences capturing the chapter's core argument. -->

## Transmitting Event Streams

An *event* is a small, self-contained, immutable object containing the details of something that happened at a point in time.

An event is generated once by a *producer* and potentially processed by multiple *consumers*. Related events are usually grouped together into a *topic* or *stream*.

### Messaging Systems

<!-- What happens when producers outpace consumers? What happens if a node crashes?
     Direct messaging vs. message brokers; ack/redelivery; load balancing vs. fan-out. -->

### Log-Based Message Brokers

<!-- Kafka-style: append-only log, offsets, partitions.
     How this differs from traditional (AMQP/JMS-style) brokers and when to pick which. -->

## Databases and Streams

### Keeping Systems in Sync

<!-- Dual writes and why they're problematic (race conditions, partial failure). -->

### Change Data Capture

<!-- Treating the DB replication log as a stream; log compaction; initial snapshots. -->

### State, Streams, and Immutability

<!-- Event sourcing; state as a fold over the event log; commands vs. events;
     deriving multiple read views from one log; limits of immutability. -->

## Processing Streams

### Uses of Stream Processing

<!-- CEP, stream analytics, materialized views, search on streams. -->

### Reasoning About Time

<!-- Event time vs. processing time; windows (tumbling/hopping/sliding/session);
     straggler events and watermarks; whose clock is it anyway? -->

### Stream Joins

<!-- Stream-stream, stream-table, table-table joins; time-dependence of joins. -->

### Fault Tolerance

<!-- Microbatching, checkpointing, idempotence, exactly-once semantics
     (and what "exactly-once" actually means). -->

## Summary

<!-- The book's own chapter summary — note anything it emphasizes that the notes above missed. -->

## Key Terms

<!-- term — one-line definition (section where defined) -->

## Quotes Worth Keeping

> _quote_
> — ch. 12, "Section Name", p. NNN

## Open Questions / Follow-Ups

- [ ]

## Connections

- [What do you mean by "Event-Driven"?](meaning-of-event-driven.md) — Fowler's four patterns; event sourcing and event-carried state transfer map onto "State, Streams, and Immutability" and CDC.
