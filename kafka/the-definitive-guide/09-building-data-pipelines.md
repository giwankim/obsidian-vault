# 9. Building Data Pipelines

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## Considerations When Building Data Pipelines

| Cue / Question | Notes |
| --- | --- |
| What role does Kafka play in a pipeline (a decoupling buffer between every source and sink — producers and consumers move independently)? | |
| How does Kafka span the timeliness spectrum (same pipeline serves near-real-time consumers and hourly batch consumers)? | |
| What reliability guarantees can a pipeline offer (at-least-once by default; exactly-once with Connect offsets + idempotent/transactional sinks)? | |
| How does Kafka handle high and varying throughput (buffer absorbs bursts; producers and consumers scale independently)? | |
| Why do data formats and schemas matter in a pipeline (Kafka is format-agnostic; converters + schema registry decouple source and sink formats and let schemas evolve)? | |
| ETL vs ELT — what's the trade-off (transform in-flight vs preserve raw data and transform at the target; who owns the transformation)? | |
| What must failure handling cover (bad records, retries, dead-letter queues, replaying history)? | |
| How do pipelines create accidental coupling (ad-hoc one-off pipelines, stripping metadata/schemas, doing so much transformation the sink is chained to the source's choices)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## When to Use Kafka Connect Versus Producer and Consumer

| Cue / Question | Notes |
| --- | --- |
| When do you embed clients directly (you own the application code and can call produce/consume yourself)? | |
| When is Connect the right tool (moving data to/from datastores you didn't write), and what does it give you for free (offset tracking, config management, REST API, schemas, scaling, fault tolerance)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Kafka Connect

| Cue / Question | Notes |
| --- | --- |
| How do standalone and distributed modes differ, and how do you configure connectors in distributed mode (REST API; workers share config/offset/status topics)? | |
| What does the file source/sink example demonstrate, and why isn't it production-grade? | |
| What does the JDBC-source → Elasticsearch-sink example add (installing connector plugins, connector configs, following data through the pipeline)? | |
| What are Single Message Transformations good for (routing, masking, filtering, headers — per-record, stateless), and when should you use Kafka Streams instead (joins, aggregations, anything stateful)? | |
| How do connectors and tasks divide the work (connector decides task count and splits the work; tasks do the actual copying)? | |
| What do workers do (container processes — run connectors/tasks, handle rebalancing, fault tolerance, offset commits)? | |
| Why do converters matter (translate Connect's internal data model ↔ bytes: JSON, Avro; they're what decouples connectors from data formats)? | |
| How does offset management differ for source vs sink connectors (source: logical positions in the source system stored in the offsets topic; sink: Kafka offsets committed like a consumer)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Alternatives to Kafka Connect

| Cue / Question | Notes |
| --- | --- |
| When would ingest frameworks tied to other systems (Flume, Logstash, NiFi, GoldenGate) fit better, and what do you give up vs Connect? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw: source DB --> source connector (tasks, converter) --> Kafka topics --> sink connector (converter, tasks) --> target system ; workers hosting tasks, offsets/config/status topics on the side
flowchart LR
```
