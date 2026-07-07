# 5. Encoding and Evolution

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch05.html>
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references)

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions.
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

**Status:** not started

## Formats for Encoding Data

| Cue / Question | Notes |
| --- | --- |
| Why does schema change force **backward** and **forward** compatibility? (rolling upgrades — old and new code, old and new data, coexist) | |
| Define **backward compatibility** vs. **forward compatibility**. Which one is harder, and why? | |
| Why are language-specific serialization formats (e.g. Java serialization, pickle) a bad idea? (lock-in, security, versioning, efficiency) | |
| What are the strengths and pitfalls of **JSON, XML, and CSV**? (numbers vs. strings, no binary strings, optional-schema ambiguity) | |
| What do binary JSON variants (MessagePack, BSON, CBOR…) buy you — and what do they *not* solve? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Protocol Buffers, Avro, and the Merits of Schemas

| Cue / Question | Notes |
| --- | --- |
| How does **Protocol Buffers** encode data using **field tags**, and how do tags enable schema evolution? (add new tag numbers; never reuse or change a tag) | |
| Which schema changes are backward/forward compatible in Protocol Buffers? (adding optional fields, removing fields, datatype changes) | |
| How is **Avro** fundamentally different? (no field tags — the **writer's schema** and **reader's schema** are *resolved* at read time) | |
| How does Avro learn the writer's schema in files vs. databases vs. RPC? (schema registry) | |
| Why is Avro friendlier to **dynamically generated schemas** (e.g. dumping a DB)? | |
| What are the merits of schemas over schemaless JSON? (compactness, documentation that can't drift, compatibility checking, codegen) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Dataflow Through Databases

| Cue / Question | Notes |
| --- | --- |
| In what sense is writing to a database "sending a message to your future self"? | |
| What is the **data outlives code** problem, and how do old rows survive schema migrations? | |
| Why must an *old* version of the code preserve fields it doesn't know about? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Dataflow Through Services: REST and RPC

| Cue / Question | Notes |
| --- | --- |
| How does service-oriented / microservices architecture turn encoding into an *organizational* problem? (independently deployable services) | |
| What are the fundamental problems with making a network call look like a local function call (**RPC**)? (partial failure, latency, retries/idempotence, no pass-by-reference) | |
| How do REST/HTTP APIs and modern RPC frameworks (e.g. **gRPC**) each deal with evolvability? | |
| Who upgrades first — clients or servers — and what does that imply for compatibility? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Durable Execution and Workflows

| Cue / Question | Notes |
| --- | --- |
| What problem do **workflow engines** / **durable execution** frameworks (e.g. Temporal-style) solve? (long-running, multi-step processes that survive crashes) | |
| How does durable execution work — what gets logged, and why must workflow code be **deterministic**? | |
| What new versioning/evolution problem does replaying old workflow histories create? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Event-Driven Architectures

| Cue / Question | Notes |
| --- | --- |
| How does asynchronous message passing differ from RPC and from databases? (broker in the middle, one-way, sender doesn't wait) | |
| What do **message brokers** give you? (buffering, redelivery, decoupling of sender/recipient, fan-out) | |
| What is the **distributed actor** model, and how does it blend messaging with programming model? | |
| How does schema evolution play out when messages linger in a broker? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Summary (the book's own)

| Cue / Question | Notes |
| --- | --- |
| What's the through-line — evolvability via forward/backward-compatible encodings, whatever the dataflow? | |
| Anything the book highlights that the notes above missed? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Sketch a rolling upgrade: old + new service versions running at once,
%% with data flowing via DB, RPC, and a message broker — mark where
%% backward vs. forward compatibility is needed at each arrow.
flowchart LR
```

## Open Questions / Follow-Ups

- [ ]

## Connections

- [[00-ddia-moc]] — chapter map / index.
- [[04-storage-and-retrieval]] — encoding on disk vs. encoding in flight; schema evolution echoes storage formats.
- [[06-replication]] — replication logs are "dataflow through databases" between nodes.
- [[12-stream-processing]] — message brokers and event streams get their full treatment there.
