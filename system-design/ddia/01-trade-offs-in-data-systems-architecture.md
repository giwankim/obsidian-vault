# 1. Trade-offs in Data Systems Architecture

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch01.html>
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references)

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions.
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

**Status:** in progress

## Introduction

| Cue / Question | Notes |
| --- | --- |
| What makes an application *data-intensive* (vs. compute-intensive)? | Storing & processing large data volumes, managing changes to data, ensuring consistency in the face of failures and concurrency, and keeping services highly available. |
| What are data-intensive applications built from? | Standard building blocks: databases, caches, search indexes, and batch/stream processors. |
| Why isn't there one database that fits every job? | Many database systems exist with different characteristics, each suitable for different purposes. |
| What is this book actually for? | A guide to help you decide which technologies to use and how to combine them. |
| What's the core challenge of data systems? | Different people need to do very different things with the same data. |

**Summary:**
<!-- 1-2 sentences, your words -->

## Operational vs. Analytical Systems

| Cue / Question | Notes |
| --- | --- |
| What distinguishes **OLTP** (transaction processing) from **OLAP** (analytics)? Think access patterns, who runs the queries, and freshness needs. | |
| What is a **data warehouse**, and how does the **ETL / ELT** pipeline feed it from operational systems? | |
| How do a **data lake** and a **lakehouse** differ from a classic warehouse? | |
| What's the difference between a **system of record** and **derived data**? | |
| What are **star** and **snowflake** schemas, and why are they used for analytics? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Cloud vs. Self-Hosting

| Cue / Question | Notes |
| --- | --- |
| What are the pros and cons of using cloud services? | |
| What does **separation of storage and compute** mean, and why does it matter? | |
| How do operations change in the cloud era (SaaS, managed services)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Distributed vs. Single-Node Systems

| Cue / Question | Notes |
| --- | --- |
| Why (and why not) distribute? Weigh scale against complexity. | |
| What problems are unique to distributed systems (partial failure, the network)? | |
| What's the difference between **shared-nothing** and **shared-disk** architectures? | |
| Where do microservices and serverless fit in? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Data Systems, Law, and Society

| Cue / Question | Notes |
| --- | --- |
| What responsibilities do privacy and regulation place on data systems? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Trade-offs (the chapter's through-line)

| Axis | One side | Other side | When to choose which |
| ---- | -------- | ---------- | -------------------- |
| Workload | Operational (OLTP) | Analytical (OLAP) | |
| Hosting | Cloud / managed | Self-hosted | |
| Topology | Single-node | Distributed | |

**Summary:**
<!-- The chapter's thesis: most architectural questions have no single right answer — only approaches with different pros and cons. -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% e.g. operational DB --ETL--> data warehouse --> analytics
flowchart LR
```

## Open Questions / Follow-Ups

- [ ]

## Connections

- [[00-ddia-moc]] — chapter map / index.
- [[03-data-models-and-query-languages]] — "Stars and Snowflakes" reappears there as a query-language concern; ties back to the OLAP schemas introduced here.
