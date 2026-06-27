---
title: "career-ops — AI-powered job search command center"
source: "https://career-ops.org/"
author:
  - "[[Niko Efstathiou]]"
published: 2026-04-05
created: 2026-06-07
description: "Open source AI-powered job search system. Runs in your CLI on your machine. CLI-agnostic, MIT-licensed, local-first. Evaluate jobs, generate tailored CVs, track applications."
tags:
  - "clippings"
---

> [!summary]
> career-ops is an open-source, MIT-licensed, local-first job-search system that runs inside any AI coding CLI (Claude Code, Codex, Gemini CLI, Qwen, Copilot). It evaluates job listings against your CV with a six-dimension rubric scoring 1.0–5.0, generates ATS-optimized tailored PDF resumes, drafts answers to Greenhouse/Ashby/Lever application questions, scans 150+ company portals token-free, and tracks the pipeline in a terminal dashboard. Everything stays on your machine — no cloud, account, or telemetry — with the only cost being whichever AI CLI you already pay for.

![career-ops terminal interface showing the job pipeline tracker](https://career-ops.org/_next/image?url=%2Fhero_image.avif&w=3840&q=75)

## Open source AI-powered job search.Runs in your CLI. Your data, your machine.

Featured in

---

> “Companies use AI to filter candidates.
> I just gave candidates AI to choose companies.”

## What is career-ops?

\>\_ /career-ops --describe

career-ops is an open-source AI-powered job search system that runs locally on your machine inside any AI coding CLI — Claude Code, Codex, OpenCode, Gemini CLI, Qwen, or GitHub Copilot. It evaluates job listings against your CV using a six-dimension rubric scoring 1.0–5.0, generates ATS-optimized PDF resumes tailored per role, drafts answers to open-ended application questions on Greenhouse, Ashby and Lever forms, scans 150+ company portals zero-token, and tracks the pipeline in a Go-based terminal dashboard. Everything lives on your machine: no cloud, no telemetry, no account. MIT-licensed and free forever; the only cost is whichever AI coding CLI you already pay for. Built by Santiago Fernández de Valderrama after a real 2026 job search of 740 listings, 66 applications, 12 interviews, and one offer.

// 49K+stars · Open source · MIT

## Turn any AI coding CLI into a full job search command center.

![](https://career-ops.org/_next/image?url=%2Fbuffalo-dither.png&w=3840&q=75)

Try it out

`git clone https://github.com/santifer/career-ops.git` Copied

```
/career-ops auto-pipeline https://jobs.acme.c
```

Instead of manually tracking applications in a spreadsheet, you get an AI-powered pipeline that scans portals, generates tailored PDFs and tracks everything for you.

> “It's like having a career coach for your job search, but without the cost.”

### AI-Native & Agnostic

Works with any coding CLI — Claude Code, Codex, OpenCode, Gemini CLI, Qwen CLI, GitHub Copilot. Built on the Open Agent Skill Standard.

### Drafts the open-ended answers.

Greenhouse, Ashby and Lever forms ask “Why this role?” and “Tell us about a project.” `/career-ops apply` reads the form, drafts every answer from your CV and the JD, and hands them back paste-ready.

You edit, you submit. The assistant never clicks for you.

[See how apply works](https://career-ops.org/docs/reference/modes/apply)

### 150+ company portals. Zero manual searching.

Pre-configured scrapers check 150+ career pages across Greenhouse, Ashby and Lever on demand — zero API tokens spent. Run `/career-ops scan` and get a ranked list back in minutes.

[See all portals](https://career-ops.org/docs)

### Shipped with the community.

career-ops grows through pull requests from people running real job searches. Issues get triaged in Discord, fixes ship the same week. You don't just use the tool — you help shape what it becomes.

[Join 3,300+ builders in Discord](https://career-ops.org/community)

## Comparing tools?

Side-by-side honest comparisons. Feature matrix, pricing, the killer feature none of them ship.

## Frequently asked

How does career-ops score job listings?

career-ops uses a rubric-guided LLM evaluation across six dimensions — match, north-star alignment, comp, cultural signals, red flags, and global fit — producing a 1.0–5.0 score with citations to specific CV lines and JD requirements. Anything below 4.0 the agent recommends against applying. No closed-form formula, no spray-and-pray. The full rubric is published at [career-ops.org/methodology](https://career-ops.org/methodology).

Is career-ops free? What is the business model?

career-ops is permanently free, MIT-licensed, and community-funded. There is no paid tier, no waitlist, no account, no telemetry, and no premium features. You clone the repo, configure your profile, and run the system locally with whichever AI coding CLI you already use. Sustainability comes from voluntary community patronage via GitHub Sponsors — not from premium tiers, paid features, or data. The maintainer has other paid work for income; sponsorship enables deeper focus on the project. See [career-ops.org/sustain](https://career-ops.org/sustain) for details.

Who built career-ops?

career-ops was built by [Santiago Fernández de Valderrama](https://career-ops.org/about) — an Applied AI Operator with 16+ years building products, founder and operator of a Spanish phone-repair business (2009–2025) before exiting, and currently Head of Applied AI at Zinkee. He created career-ops in early 2026 to manage his own AI-era job search — 740 listings evaluated, one Head of AI role landed — and open-sourced it under MIT once he no longer needed it.

Is career-ops a Claude Code skill or a standalone tool?

career-ops is CLI-agnostic. It works with Claude Code, Codex, OpenCode, Gemini CLI, Qwen, and Copilot — whichever AI coding agent the user already pays for. The skill files (`modes/`) live in the repo as plain markdown prompts; any agent that supports skill loading can invoke them. There is no Anthropic-specific dependency. Claude Code happens to be the most common runtime because of its skill loader, but the same modes run unchanged in the other CLIs.

How is career-ops different from other AI job search tools?

Most AI job search tools — Jobscan, Teal, Huntr, autoapply.ai — are cloud SaaS products that upload your resume and job data to their servers, charge $20–80/month, and keep their matching algorithm closed. career-ops is the inverse: open source, MIT-licensed, runs locally on your machine through whichever AI CLI you already use, and publishes the full evaluation rubric. The only recurring cost is your AI CLI subscription. Side-by-side comparisons at [career-ops.org/compare](https://career-ops.org/compare).

What AI tools does career-ops work with?

Claude Code (primary), Codex (OpenAI), OpenCode, Gemini CLI (Google), Qwen, and GitHub Copilot. The same mode files run on all six. Each user picks the CLI that fits their existing subscription and cost preferences — career-ops never locks you to one provider. A typical job search runs on Claude Pro at $20/month, but the choice is yours.

Ready to filter offers, not get filtered?

[Your turn](https://career-ops.org/docs)

Or follow what we ship.

Release announcements and occasional updates.
Unsubscribe anytime.
