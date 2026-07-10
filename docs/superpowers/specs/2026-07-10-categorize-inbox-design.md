# categorize-inbox Skill Design

**Date:** 2026-07-10
**Status:** Approved

## Purpose

Complete the clipping pipeline: clip → `/clippings-to-inbox` → `/categorize-inbox`. The skill files inbox articles into the vault's topic folders according to fixed rules, with the user approving the full mapping before any file moves.

## Context

The vault has ~55 top-level topic folders, some with subfolders (`db/cdc/`, `spring/msa/`, `event-driven-architecture/transactional-outbox/`). The established workflow from git history: clippings land in `inbox/`, then get filed into a topic folder and committed as `docs(<topic>): add ... clipping`. Until now the filing step was ad-hoc; this skill makes it a repeatable, rule-driven workflow.

## Categorization Rules

1. **Technology wins.** An article that fits both a concept folder (`ai/`, `performance/`) and a technology folder (`spring/`, `kafka/`) files under the technology. Concept folders catch articles with no technology angle.
2. **Never create folders.** Triage only uses folders that already exist. An article with no fitting folder stays in `inbox/` and is flagged for the user to decide separately. Creating a new topic folder is always a deliberate user decision, never a triage side effect.
3. **Deepest existing match.** File into an existing subfolder when one clearly fits (a CDC article → `db/cdc/`), otherwise the topic folder root (a Spring testing article → `spring/`, since no `spring/testing/` exists).
4. **Non-articles stay in inbox.** Reading lists, TODO queues, and other working notes (e.g., `open-tabs.md`) are skipped. `inbox/` doubles as their home. Heuristic: a file without `source:` frontmatter is not a clipping.
5. **Concept-folder ties go to the user.** When two concept folders both plausibly fit (e.g., `performance/` vs `system-design/`), the skill proposes its best pick with the alternative noted in the rationale; the user settles it at the approval step.

## Workflow

1. List `.md` files in `inbox/`. Skip non-articles (no `source:` frontmatter). If nothing remains, inform the user and stop.
2. Read each article's frontmatter and summary callout. Match against the live folder tree (enumerate folders with `ls`/`find` at triage time — never a hardcoded list).
3. Present one mapping table: article → proposed destination → one-line rationale. Articles with no fitting folder appear in a separate "no home — staying in inbox" section.
4. User approves or adjusts the mapping (single batch approval, not per-article).
5. Move approved files with plain `mv`. Filenames are already kebab-case from `/clippings-to-inbox` and are not changed. If a file with the same name already exists at the destination, do not overwrite — flag it as a likely duplicate clipping and leave the inbox copy in place for the user to resolve.
6. No commit. The user runs `/commit-push`, which auto-splits by scope and matches the existing `docs(<topic>)` one-commit-per-topic convention.

## Structure

- `SKILL.md` only — no script. The moves are plain `mv` commands driven by the approved table; unlike kebab-casing there is no deterministic transform worth encoding.
- Installed in both `.claude/skills/categorize-inbox/` and `.agents/skills/categorize-inbox/`, matching the vault's existing skill layout.
- Frontmatter description triggers on: "categorize inbox", "file inbox articles", "triage inbox", "process inbox".

## Worked Example (inbox as of 2026-07-10)

| Article | Destination | Rule applied |
|---|---|---|
| 6개월-만에-…-db-cdc-복제-도구-…교체하기.md | `db/cdc/` | deepest existing match |
| optimizing-spring-integration-tests-at-scale.md | `spring/` | topic root; no `spring/testing/` exists |
| 학습에이전트-building-the-brain.md | `spring/spring-ai/` | technology wins over `ai/` |
| 네이버-메인-페이지의-트래픽-처리.md | `performance/` (alt: `system-design/`) | concept tie → user settles |
| 동영상-플랫폼-개선기-1-….md | stays in inbox | no fitting folder; flagged |
| open-tabs.md | stays in inbox | non-article, skipped |

## Out of Scope

- Creating topic folders or subfolders (user-only decision).
- Committing or pushing (delegated to `/commit-push`).
- Renaming files or editing article content.
- Moving the current inbox files — that is the first *run* of the skill, a separate step after the skill is written.
