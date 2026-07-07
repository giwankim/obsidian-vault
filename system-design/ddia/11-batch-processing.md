# 11. Batch Processing

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch11.html>
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references)

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions.
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

**Status:** not started

## Batch Processing with Unix Tools

| Cue / Question | Notes |
| --- | --- |
| How does services / batch / stream form a spectrum? (request-response vs. bounded jobs vs. unbounded) | |
| Walk through the log-analysis example: why does `sort | uniq -c` beat an in-memory hash map at scale? (sorting spills to disk gracefully) | |
| What is the **Unix philosophy**, and which design choices enable composition? (uniform byte-stream interface, pipes, stdin/stdout, immutable inputs) | |
| What limits Unix tools to a single machine? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## MapReduce and Distributed Filesystems

| Cue / Question | Notes |
| --- | --- |
| What does a **distributed filesystem** (HDFS-style; today also object storage) provide, and how does replication make cheap disks reliable? | |
| Describe the MapReduce execution flow: **map → shuffle (sort by key) → reduce**. Why "put the computation near the data"? | |
| How do **workflows** chain jobs, and why is materializing intermediate state to files both robust and wasteful? | |
| Compare the join algorithms: **sort-merge join**, **broadcast hash join**, **partitioned hash join** — when does each win? | |
| How do you handle **skew** (linchpin/hot keys) in a distributed join or grouping? | |
| Why did MapReduce tolerate task failures so well, and what environment assumption drove that design? (preemption on shared clusters) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## The Output of Batch Workflows

| Cue / Question | Notes |
| --- | --- |
| What do batch jobs actually produce? (search indexes, key-value stores/ML models, analytics) | |
| Why build databases *as files* inside the job and bulk-load them, instead of writing to a live DB row by row? | |
| How does treating inputs as **immutable** and outputs as replaceable enable fault tolerance and human-error recovery? (rerun the job; roll back the output) | |
| How does this philosophy compare to Unix — and to databases (schema-on-read, storage/compute separation)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Beyond MapReduce

| Cue / Question | Notes |
| --- | --- |
| What do **dataflow engines** (Spark, Flink, Tez) change about execution? (operator DAGs, no forced materialization between stages, memory/pipelining) | |
| How does fault tolerance work without materialized intermediates? (recompute from lineage; determinism matters) | |
| How does **iterative / graph processing** (Pregel model) differ from one-pass dataflow? | |
| Why did high-level declarative APIs (dataframes, SQL-on-everything) win over hand-written MapReduce? (query optimizers come to batch) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Summary (the book's own)

| Cue / Question | Notes |
| --- | --- |
| What's the chapter's core pattern — derived data recomputed from immutable inputs? | |
| Anything the book highlights that the notes above missed? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Sketch a two-job workflow: input files -> map -> shuffle -> reduce -> output files,
%% feeding a second job; mark where a sort-merge join happens and what gets
%% re-run when a task fails.
flowchart LR
```

## Open Questions / Follow-Ups

- [ ]

## Connections

- [[00-ddia-moc]] — chapter map / index.
- [[01-trade-offs-in-data-systems-architecture]] — ETL and the warehouse: batch is how derived data gets built.
- [[04-storage-and-retrieval]] — batch jobs build the very indexes and columnar files described there.
- [[12-stream-processing]] — stream processing is batch with unbounded input; the comparison is that chapter's opening move.
