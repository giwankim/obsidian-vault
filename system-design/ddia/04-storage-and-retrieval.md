# 4. Storage and Retrieval

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch04.html>
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references)

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions.
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

**Status:** not started

## Log-Structured Storage: SSTables and LSM-Trees

| Cue / Question                                                                                                                                | Notes |
| --------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| Why should an application developer care how the storage engine works internally?                                                             |       |
| What's the simplest possible database (append-only log), and why are appends fast but reads slow?                                             |       |
| What is a **hash index**, and what are its limitations? (must fit in memory, no range queries)                                                |       |
| How do **segments** and **compaction** keep an append-only log from growing forever?                                                          |       |
| What is an **SSTable**, and what does keeping keys *sorted* buy you over a hash index? (sparse index, range scans, merge-friendly compaction) |       |
| How does an **LSM-tree** work end to end? (writes → **memtable** → flushed SSTables → background compaction; crash recovery via a log)        |       |
| What are **Bloom filters** for? (cheaply ruling out reads of keys that don't exist)                                                           |       |
| How do **size-tiered** and **leveled** compaction strategies differ?                                                                          |       |

**Summary:**
<!-- 1-2 sentences, your words -->

## B-Trees

| Cue / Question | Notes |
| --- | --- |
| How does a **B-tree** organize data? (fixed-size **pages**, branching factor, key ranges) | |
| What happens on lookup, insert, and page **split**? | |
| How are B-trees made reliable after a crash? (**write-ahead log**, careful page overwrites) | |
| What optimizations exist? (copy-on-write instead of WAL, key abbreviation, sibling pointers for scans) | |
| Why do B-trees overwrite pages in place while LSM-trees never modify files? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Comparing B-Trees and LSM-Trees

| Cue / Question | Notes |
| --- | --- |
| What is **write amplification**, and where does it come from in each structure? | |
| Why are LSM-trees typically better for **write-heavy** workloads? (sequential writes, higher throughput, better compression) | |
| Why are B-trees often better for **reads** and for transactional semantics? (each key in exactly one place → simpler locking) | |
| What are the downsides of compaction? (background load interfering with latency, unbounded disk usage if compaction can't keep up) | |
| Given a workload, how would you actually choose? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Multi-Column, Secondary, Full-Text, and In-Memory Indexes

| Cue / Question | Notes |
| --- | --- |
| How does a **secondary index** differ from a primary index? (non-unique values; postings lists) | |
| Where do the rows actually live — what's the difference between a **heap file**, a **clustered index**, and a **covering index**? | |
| What are **multi-column (concatenated) indexes**, and why does column order matter? Where do they fall short (e.g. geospatial), and what fills the gap (R-trees / space-filling curves)? | |
| How do **full-text search** and fuzzy indexes work at a high level? | |
| Why are **in-memory databases** faster — and why is "they don't read from disk" the *wrong* answer? (avoiding encoding/serialization overhead; durability still via logs/replication) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Data Storage for Analytics

| Cue / Question | Notes |
| --- | --- |
| Why do OLTP storage engines struggle with analytical scans over millions of rows? | |
| What is **column-oriented storage**, and why does it fit analytics? (read only the columns you need) | |
| How does **column compression** work (bitmap encoding, run-length encoding), and why do columns compress so well? | |
| How does **sort order** in column storage help both queries and compression — and how do multiple sort orders (per replica) help? | |
| How do you *write* to column storage when it's optimized for reads? (LSM-style: in-memory buffer → merged column files) | |
| Where do cloud data warehouses, data lakes, and open formats (e.g. Parquet) fit in this picture? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Query Execution, Materialized Views, and Data Cubes

| Cue / Question | Notes |
| --- | --- |
| What's the difference between **query compilation** and **vectorized processing**, and why does either beat row-at-a-time interpretation? | |
| What is a **materialized view**, and how does it differ from a virtual view? | |
| What is a **data cube**, and what's the trade-off of precomputed aggregates? (fast queries vs. inflexibility) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Summary (the book's own)

| Cue / Question | Notes |
| --- | --- |
| What's the chapter's core split — OLTP (log-structured vs. update-in-place) and analytics (columnar)? | |
| Anything the book highlights that the notes above missed? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Sketch the LSM write path (write --> memtable --> SSTable flush --> compaction)
%% next to the B-tree write path (find page --> WAL --> overwrite page / split).
flowchart LR
```

## Open Questions / Follow-Ups

- [ ]

## Connections

- [[00-ddia-moc]] — chapter map / index.
- [[01-trade-offs-in-data-systems-architecture]] — the OLTP vs. OLAP split introduced there dictates the two halves of this chapter.
- [[03-data-models-and-query-languages]] — data models are the interface; this chapter is what's underneath it.
- [[05-encoding-and-evolution]] — how data is laid out in files continues into how it's encoded on the wire.
