# categorize-inbox Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/categorize-inbox` skill that files inbox clippings into existing vault topic folders per fixed rules, with one batch user approval before any move.

**Architecture:** A single prose `SKILL.md` (no script) at `.agents/skills/categorize-inbox/`, registered via a relative symlink at `.claude/skills/categorize-inbox` — the vault's established two-location layout. The skill encodes five categorization rules and a seven-step workflow; file moves are plain `mv` driven by a user-approved mapping table.

**Tech Stack:** Markdown skill file, bash one-liners embedded in the skill, git symlink (mode 120000).

**Spec:** `docs/superpowers/specs/2026-07-10-categorize-inbox-design.md`

## Global Constraints

- The skill must never create folders or subfolders — articles with no fitting folder stay in `inbox/`, flagged.
- The skill must never commit or push — committing is delegated to `/commit-push`.
- The skill must never rename files or edit article content.
- Destination folders are enumerated live at triage time — no hardcoded folder list anywhere in the skill.
- Approval is a single batch step over the full mapping table, not per-article.
- On destination filename conflict: do not overwrite; flag as likely duplicate and leave the inbox copy.
- `inbox/` and `Clippings/` are git-ignored; `.agents/skills/` files and `.claude/skills/` symlinks are git-tracked.
- Pre-commit hooks run markdownlint-cli2, end-of-file, and whitespace checks on committed markdown; the working tree has an unrelated uncommitted `spring/testing.md` deletion — never stage it.

---

### Task 1: Author SKILL.md

**Files:**

- Create: `.agents/skills/categorize-inbox/SKILL.md`

**Interfaces:**

- Consumes: nothing (first task).
- Produces: `.agents/skills/categorize-inbox/SKILL.md` — the symlink target Task 2 points at. The directory name `categorize-inbox` and frontmatter `name: categorize-inbox` must match exactly.

- [ ] **Step 1: Write the skill file**

Create `.agents/skills/categorize-inbox/SKILL.md` with exactly this content:

````markdown
---
name: categorize-inbox
description: File inbox articles into the vault's existing topic folders using fixed categorization rules, with one batch approval before any file moves. Use when the user says "categorize inbox", "file inbox articles", "triage inbox", or "process inbox".
---

# Categorize Inbox

File `.md` clippings from `inbox/` into existing topic folders. Propose a
complete mapping, get one batch approval, then move the files. Never create
folders. Never commit.

## Categorization Rules

1. **Non-articles stay in inbox.** A file without a `source:` line in its
   frontmatter is not a clipping (reading lists, TODO notes such as
   `open-tabs.md`). Skip it; `inbox/` is its home.
2. **Technology wins.** An article that fits both a concept folder (`ai/`,
   `performance/`) and a technology folder (`spring/`, `kafka/`) files under
   the technology. Concept folders catch articles with no technology angle.
3. **Deepest existing match.** File into an existing subfolder when one
   clearly fits (a CDC article goes to `db/cdc/`); otherwise the topic folder
   root (a Spring testing article goes to `spring/` while no `spring/testing/`
   exists).
4. **Never create folders.** Only file into folders that already exist. If
   nothing fits, the article stays in `inbox/`, flagged in the report so the
   user can decide separately.
5. **Concept ties go to the user.** When two concept folders both plausibly
   fit, propose the better one and name the alternative in the rationale; the
   user settles it at the approval step.

## Workflow

1. From the vault root, identify candidate articles and skip non-articles:

   ```bash
   find inbox -maxdepth 1 -name '*.md' | sort | while read -r f; do
     if head -20 "$f" | grep -q '^source:'; then
       echo "ARTICLE  $f"
     else
       echo "SKIP     $f"
     fi
   done
   ```

   If there are no articles, inform the user and stop.

2. Enumerate destination folders live — never use a remembered or hardcoded
   list:

   ```bash
   find . -mindepth 1 -maxdepth 2 -type d \
     -not -path '*/.*' \
     -not -path './inbox' -not -path './inbox/*' \
     -not -path './Clippings' -not -path './Clippings/*' \
     -not -path './scripts' -not -path './scripts/*' \
     -not -path './docs' -not -path './docs/*' \
     | sort
   ```

3. Read each article's frontmatter (`title`, `description`) and its
   `> [!summary]` callout. Only read the full body if those are missing or
   inconclusive.

4. Apply the rules and present one mapping table, plus a separate list for
   articles with no fitting folder:

   ```markdown
   | Article | Destination | Rationale |
   |---------|-------------|-----------|
   | some-cdc-article.md | db/cdc/ | deepest existing match |

   No home — staying in inbox:
   - some-new-topic-article.md (no fitting folder; create one?)
   ```

5. Ask for one batch approval of the whole mapping. Apply any adjustments the
   user gives, then proceed — do not re-ask per article.

6. Move approved files with `mv`. Before each move, check for a name
   conflict; on conflict, do not overwrite — report the file as a likely
   duplicate clipping and leave the inbox copy in place:

   ```bash
   [ -e "db/cdc/some-cdc-article.md" ] && echo "CONFLICT — skipping" \
     || mv "inbox/some-cdc-article.md" "db/cdc/"
   ```

7. Report what moved and what stayed. Remind the user that `inbox/` is
   git-ignored, so moved files appear as new untracked files, and that
   `/commit-push` groups them into `docs(<topic>)` commits.
````

- [ ] **Step 2: Verify the article-detection command against the live inbox**

Run from the vault root:

```bash
cd /Users/gwk/Development/obsidian/vault && find inbox -maxdepth 1 -name '*.md' | sort | while read -r f; do
  if head -20 "$f" | grep -q '^source:'; then echo "ARTICLE  $f"; else echo "SKIP     $f"; fi
done
```

Expected (with the inbox as of 2026-07-10): 5 `ARTICLE` lines and exactly one `SKIP` line, for `inbox/open-tabs.md`. If the inbox has changed since, verify only that every `SKIP` file genuinely lacks `source:` frontmatter.

- [ ] **Step 3: Verify the folder-enumeration command**

Run the exact `find` command from workflow step 2 (from the vault root).

Expected output includes `./ai`, `./db`, `./db/cdc`, `./spring`, `./spring/spring-ai`, `./system-design` — and does NOT include `./inbox`, `./Clippings`, `./docs`, `./scripts`, or any dot-directory such as `./.claude` or `./.agents`.

- [ ] **Step 4: Commit**

```bash
cd /Users/gwk/Development/obsidian/vault && git add .agents/skills/categorize-inbox/SKILL.md && git commit -m "feat(skills): add categorize-inbox skill" -- .agents/skills/categorize-inbox/SKILL.md
```

Expected: pre-commit hooks (`fix end of files`, `trim trailing whitespace`, `markdownlint-cli2`, `sync README.md topic list`) all pass — `.agents/` is in the sync script's EXCLUDE set, so the README is untouched. Commit succeeds with 1 file changed. If markdownlint fails, fix the reported line in SKILL.md and re-run the same command.

---

### Task 2: Register the skill in .claude/skills/

**Files:**

- Create: `.claude/skills/categorize-inbox` (relative symlink)

**Interfaces:**

- Consumes: `.agents/skills/categorize-inbox/` from Task 1.
- Produces: tracked symlink `.claude/skills/categorize-inbox` → `../../.agents/skills/categorize-inbox`, matching the six existing skill symlinks.

- [ ] **Step 1: Create the symlink**

```bash
cd /Users/gwk/Development/obsidian/vault && ln -s ../../.agents/skills/categorize-inbox .claude/skills/categorize-inbox
```

- [ ] **Step 2: Verify the symlink resolves and matches the existing pattern**

```bash
cd /Users/gwk/Development/obsidian/vault && ls -la .claude/skills/ && cat .claude/skills/categorize-inbox/SKILL.md | head -4
```

Expected: `categorize-inbox -> ../../.agents/skills/categorize-inbox` listed alongside the six existing symlinks in the same relative form, and the `cat` prints the frontmatter starting with `---` / `name: categorize-inbox`.

- [ ] **Step 3: Commit**

```bash
cd /Users/gwk/Development/obsidian/vault && git add .claude/skills/categorize-inbox && git commit -m "feat(skills): register categorize-inbox in .claude/skills" -- .claude/skills/categorize-inbox
```

Expected: hooks pass (a symlink is not markdown-linted); commit succeeds with 1 file changed, mode `120000`. Verify with `git ls-files -s .claude/skills/categorize-inbox` showing mode `120000`.

---

## Out of Scope (from spec)

- Running the skill on the current six inbox files — that is the first real run, a separate user-initiated step after this plan lands.
- Creating any topic folder (e.g., for the 동영상 플랫폼 article).
- Committing the user's pending `spring/testing.md` deletion.
