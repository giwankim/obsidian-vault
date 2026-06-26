# DDIA Slidev decks

Themed [Slidev](https://sli.dev) project for presenting DDIA chapter notes.
The `slides.md` here is a worked example for **Ch.3 — Data Models & Query Languages**.

## Run it

```bash
cd system-design/ddia/slides
pnpm install       # first time only
pnpm dev           # opens http://localhost:3030
```

Keys in the browser: `→/←` navigate · `o` overview · `p` presenter mode (speaker notes) · `d` dark toggle.

## Export

```bash
pnpm export            # → PDF  (needs: pnpm add -D playwright-chromium)
pnpm export:pptx       # → PowerPoint / Google Slides
```

Import the `.pptx` into Google Slides via Drive → *Open with → Google Slides*.

## What's where

| File | Role |
| --- | --- |
| `slides.md` | the deck — one `##`/`---` per slide |
| `style.css` | the **DDIA theme** — palette + typography (auto-imported) |
| `global-bottom.vue` | footer rendered on every slide (Slidev = Vue components) |
| `uno.config.ts` | Tailwind-style utility shortcuts usable inline |

## Workflow: notes → deck

1. Keep the Cornell notes in `../NN-*.md` as your **study** artifact.
2. Per chapter, copy `slides.md` → `NN-chapter.md` here and distill:
   - each cue/question → a **slide title**
   - the answer → **bullets** (on slide) + **speaker notes** (`<!-- -->`, off slide)
   - each `mermaid` sketch → drop straight into a ` ```mermaid ` block
3. Trade-off tables → `layout: two-cols`.

> One theme, reused per chapter — restyle once in `style.css`, every deck follows.

## Note

`node_modules/` lives inside the vault but is git-ignored, and is excluded from
Obsidian indexing via a `/node_modules/` regex filter in `.obsidian/app.json`
(*Settings → Files & Links → Excluded files*). Reload Obsidian for it to take effect.
