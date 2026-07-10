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
