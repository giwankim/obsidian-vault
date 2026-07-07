# 14. Doing the Right Thing

> _Designing Data-Intensive Applications_, 2nd Edition — Martin Kleppmann & Chris Riccomini
> <https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ch14.html>
> Literature references: [ept/ddia-references](https://github.com/ept/ddia-references)

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions.
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

**Status:** not started

## Predictive Analytics and Algorithmic Decisions

| Cue / Question | Notes |
| --- | --- |
| Why does the book insist engineers own the *consequences* of data systems, not just their mechanics? | |
| How do algorithmic decisions (credit, hiring, policing…) create a class of people excluded by *prediction* rather than by fact? | |
| **Bias and discrimination**: why doesn't removing the protected attribute fix a model trained on biased data? | |
| **Responsibility and accountability**: when an automated decision is wrong, who can the affected person appeal to — and why is "the algorithm decided" corrosive? | |
| What are **feedback loops** in deployed models (predictions changing the world that trains the next model)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Privacy and Tracking

| Cue / Question | Notes |
| --- | --- |
| How does behavioral tracking shift from serving the user to **surveillance** — and why does "users consented" ring hollow? (no real choice or understanding) | |
| Why is "privacy" not secrecy but *control over disclosure* — and how do data systems take that control away? | |
| Data as **assets and power**: why does accumulated data attract abuse (breach, subpoena, acquisition, authoritarian misuse) regardless of intent? | |
| Why does the industrial-revolution analogy suggest regulation is how externalities (pollution ↔ data abuse) get priced in? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Legislation, Self-Regulation, and Doing Better

| Cue / Question | Notes |
| --- | --- |
| What does data-protection law (e.g. **GDPR**) require, and where does it fall short in practice? | |
| What would treating data with respect look like in engineering practice? (**data minimization**, purpose limitation, encryption, actually deleting data) | |
| Why is deleting data genuinely hard in log-centric, immutable-by-design systems — and what techniques help (crypto-shredding, tombstones)? | |
| What's the individual engineer's lever — what should *you* refuse to build or normalize? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Summary (the book's own)

| Cue / Question | Notes |
| --- | --- |
| What's the closing charge of the whole book — build systems that treat people with humanity and respect? | |
| Anything the book highlights that the notes above missed (e.g. environmental/societal costs)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Sketch the tracking feedback loop: user activity -> collected data ->
%% model -> decisions shown to user -> altered behavior -> more data.
%% Mark where consent, minimization, and deletion could break the loop.
flowchart LR
```

## Open Questions / Follow-Ups

- [ ]

## Connections

- [[00-ddia-moc]] — chapter map / index.
- [[01-trade-offs-in-data-systems-architecture]] — "Data Systems, Law, and Society" planted this seed in chapter 1; this chapter is the payoff.
- [[13-a-philosophy-of-streaming-systems]] — immutable event logs collide head-on with the right to be forgotten.
