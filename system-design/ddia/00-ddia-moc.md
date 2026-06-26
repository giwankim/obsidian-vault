# DDIA 2nd Edition — Map of Content

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/>

Home base for working through DDIA. Each chapter links to its note; track which learning paradigm you used and how far you've gotten.

> [!tip]- How to use this MOC
> - Click a chapter link to open it — or, if the note doesn't exist yet, to **create** it.
> - Copy a template from [Study templates](#study-templates) into the new note to start.
> - Update the **Paradigm** and **Status** columns as you progress.
> - **Status legend:** ⬜ not started · 🟡 in progress · ✅ done.

## Progress tracker

| #  | Chapter | Note | Paradigm(s) | Status |
| -- | ------- | ---- | ----------- | ------ |
| 1  | Trade-offs in Data Systems Architecture | [[01-trade-offs-in-data-systems-architecture]] |  | 🟡 |
| 2  | Defining Nonfunctional Requirements | [[02-defining-nonfunctional-requirements]] |  | ⬜ |
| 3  | Data Models and Query Languages | [[03-data-models-and-query-languages]] |  | 🟡 |
| 4  | Storage and Retrieval | [[04-storage-and-retrieval]] |  | ⬜ |
| 5  | Encoding and Evolution | [[05-encoding-and-evolution]] |  | ⬜ |
| 6  | Replication | [[06-replication]] |  | ⬜ |
| 7  | Sharding | [[07-sharding]] |  | ⬜ |
| 8  | Transactions | [[08-transactions]] |  | ⬜ |
| 9  | The Trouble with Distributed Systems | [[09-the-trouble-with-distributed-systems]] |  | ⬜ |
| 10 | Consistency and Consensus | [[10-consistency-and-consensus]] |  | ⬜ |
| 11 | Batch Processing | [[11-batch-processing]] |  | ⬜ |
| 12 | Stream Processing | [[12-stream-processing]] |  | 🟡 |
| 13 | A Philosophy of Streaming Systems | [[13-a-philosophy-of-streaming-systems]] |  | ⬜ |
| 14 | Doing the Right Thing | [[14-doing-the-right-thing]] |  | ⬜ |

## Study templates

Copy one into a chapter note to begin. Bodies are identical to the `kafka/the-definitive-guide/` versions, so the workflow is consistent across both books.

| Template | Paradigm | Reach for it… |
| -------- | -------- | ------------- |
| [[_template]] | Structured capture | First-pass reading; reference doc |
| [[_cornell-template]] | Cornell notes | First read with built-in self-test |
| [[_mental-model-template]] | Mental models / first principles | Consolidating "why this design" — highest leverage for DDIA |
| [[_feynman-template]] | Feynman technique | Pressure-testing your understanding |
| [[_active-recall-template]] | Active recall + spaced repetition | Retention across chapters |

## Recommended workflow for dense chapters

DDIA is trade-off- and mental-model-dense, not fact-dense. Layer the paradigms rather than picking one:

1. **Read (book open)** — Cornell *or* structured-capture template. Just get it down.
2. **Consolidate (book closed)** — mental-model template: draw the chapter as *one diagram*, then answer "what problem forces each design choice?"
3. **Pressure-test** — Feynman template: explain it plainly. Your stalls are your study list.
4. **Retain** — active-recall questions + `#flashcards` for spaced review.

> [!note] Plugin integrations you already have
> - **Spaced Repetition** — `#flashcards` tags and the `**Q:**` / `> A:` pairs in [[_active-recall-template]] feed directly into the plugin's review queue. Run *"Spaced Repetition: Review flashcards"* from the command palette.
> - **Mermaid Tools / Excalidraw** — for the diagram-first step in [[_mental-model-template]] and [[_cornell-template]]. Use a `mermaid` block for quick flows, or embed an Excalidraw drawing for richer topologies.

## Suggested study arc

A way to think about dependencies (a learning aid, not the book's official part structure):

- **Foundations** (ch. 1–5) — architecture trade-offs, requirements, data models, storage engines, encoding. The vocabulary everything else builds on.
- **Distributed data** (ch. 6–10) — replication, sharding, transactions, distributed-systems failure modes, consistency & consensus. The hardest, most interdependent stretch — lean on the mental-model template here.
- **Derived & dataflow** (ch. 11–14) — batch, stream, streaming-systems philosophy, and the ethics/future closer.
