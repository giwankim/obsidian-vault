# 3. Data Models and Query Languages

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch03.html>
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references)

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions.
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

**Status:** not started

## Relational Versus Document Models

| Cue / Question | Notes |
| --- | --- |
| Why does the choice of data model matter so much for an application? | |
| What is the *object-relational mismatch* (impedance mismatch), and how do ORMs and the document model each respond to it? | |
| Normalization vs. denormalization: what's the trade-off, and why do **joins** sit at the center of it? | |
| How do the relational and document models each handle **many-to-one** and **many-to-many** relationships? Where does the document model struggle? | |
| What are **star** and **snowflake** schemas (fact vs. dimension tables), and why are they used for analytics? | |
| When would you reach for a document model vs. a relational one? (schema-on-read vs. schema-on-write, data locality, access patterns) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Graph-Like Data Models

| Cue / Question | Notes |
| --- | --- |
| When is a graph model a better fit than relational or document? (highly connected, many-to-many, evolving relationships) | |
| What is the **property graph** model (vertices, edges, properties), and how is it stored in a relational database? | |
| What does a traversal look like in **Cypher**? | |
| How do you express graph queries in SQL (`WITH RECURSIVE` / recursive CTEs), and why is it awkward? | |
| What is the **triple-store** model and **SPARQL**? How do RDF triples (subject–predicate–object) relate to property graphs? | |
| What is **Datalog**, and how do recursive rules compose into queries? | |
| What is **GraphQL**, and why does it belong in a different category from the others? (an API query language, not a database model) | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Event Sourcing and CQRS

| Cue / Question | Notes |
| --- | --- |
| What is **event sourcing**? Why store the log of events instead of just current state? | |
| What is **CQRS** (Command Query Responsibility Segregation), and how do the read and write models diverge? | |
| How does this connect to derived data / materialized views — and to stream processing in [[12-stream-processing]]? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## DataFrames, Matrices, and Arrays

| Cue / Question | Notes |
| --- | --- |
| What workloads do dataframes/matrices/arrays serve that relational tables handle poorly? (analytics, ML, scientific computing) | |
| How does a **dataframe** differ from a relational table? (ordered rows/columns, positional access, columnar — pandas/R) | |
| Where do dense vs. sparse **matrices** and array databases fit in? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Summary (the book's own)

| Cue / Question | Notes |
| --- | --- |
| What does the chapter emphasize as the through-line across all these models? | |
| Anything the book highlights that the notes above missed? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Sketch the SAME data (e.g. people + the orgs/places they connect to)
%% represented three ways: relational tables, a nested document, a property graph.
flowchart LR
```

## Open Questions / Follow-Ups

- [ ]

## Connections

- [[01-trade-offs-in-data-systems-architecture]] — "Stars and Snowflakes" reappears here as a query-language concern; ties back to OLAP schemas.
