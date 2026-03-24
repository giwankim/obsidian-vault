---
title: "Claude Code Cheat Sheet"
source: "https://cc.storyfox.cz/"
author:
published: 2026-03-23
created: 2026-03-24
description:
tags:
  - "clippings"
---

> [!summary]
> A comprehensive quick-reference for Claude Code keyboard shortcuts, slash commands, configuration files, MCP server management, plan mode, git worktrees, voice mode, context management, and CLI flags.

General Controls

⌘C Cancel input/generation

⌘D Exit session

⌘L Clear screen

⌘O Toggle verbose output

⌘R Reverse search history

⌘G Open prompt in editor

⌘B Background running task

⌘T Toggle task list

⌘V Paste image

⌘F Kill background agents (×2)

EscEsc Rewind / undo

Mode Switching

⇧Tab Cycle permission modes

⌥P Switch model

⌥T Toggle thinking

Input

\\Enter Newline (quick)

⌘J Newline (control seq)

Prefixes

/ Slash command

! Direct bash

@ File mention + autocomplete

Session Picker

↑↓ Navigate

←→ Expand/collapse

P Preview

R Rename

/ Search

A All projects

B Current branch

Add Servers

\--transport stdio Local process

\--transport sse Remote SSE

Scopes

Local ~/.claude.json (per project)

Project.mcp.json (shared/VCS)

User ~/.claude.json (global)

Manage

/mcp Interactive UI

claude mcp list List all servers

claude mcp serve CC as MCP server

Elicitation Servers request input mid-taskNEW

Session

/clear Clear conversation

/compact \[focus\] Compact context

/resume Resume/switch session

/rename \[name\] Name current session

/branch \[name\] Branch conversation (/fork alias)

/cost Token usage stats

/context Visualize context (grid)

/diff Interactive diff viewer

/copy Copy last response

/export Export conversation

Config

/config Open settings

/model \[model\] Switch model (←→ effort)

/fast \[on|off\] Toggle fast mode

/vim Toggle vim mode

/theme Change color theme

/permissions View/update permissions

/effort \[level\] Set effort (low/med/high)NEW

/color \[color\] Set prompt-bar color

Tools

/init Create CLAUDE.md

/memory Edit CLAUDE.md files

/mcp Manage MCP servers

/hooks Manage hooks

/skills List available skills

/agents Manage agents

/chrome Chrome integration

/reload-plugins Hot-reload plugins

Special

/btw <question> Side question (no context)

/plan \[desc\] Plan mode (+ auto-start)

/loop \[interval\] Schedule recurring task

/voice Push-to-talk voice (20 langs)

/doctor Diagnose installation

/rc Enable remote control

/stats Usage streaks & prefs

/insights Analyze sessions report

/desktop Continue in Desktop app

/remote-control Bridge terminal to claude.ai/codeNEW

/stickers Order stickers! 🎉

CLAUDE.md Locations

./CLAUDE.md Project (team-shared)

~/.claude/CLAUDE.md Personal (all projects)

/etc/claude-code/ Managed (org-wide)

.claude/rules/\*.md Project rules

~/.claude/rules/\*.md User rules

paths: frontmatter Path-specific rules

@path/to/file Import in CLAUDE.md

Auto Memory

~/.claude/projects/<proj>/memory/

MEMORY.md + topic files, auto-loaded

Plan Mode

⇧Tab Normal → Auto → Plan

\--permission-mode plan Start in plan mode

⌥T Toggle thinking on/off

"ultrathink" Max effort for turn

⌘O See thinking (verbose)

/effort ○ low · ◐ med · ● highNEW

Git Worktrees

\--worktree name Isolated branch per feature

isolation: worktree Agent in own worktree

sparsePaths Checkout only needed dirsNEW

/batch Auto-creates worktrees

Voice Mode

/voice Enable push-to-talk

Space (hold) Record, release to send

20 languages EN, ES, FR, DE, CZ, PL…

Context Management

/context Usage + optimization tips

/compact \[focus\] Compress with focus

Auto-compact ~95% capacity

1M context Opus 4.6 (Max/Team/Ent)

CLAUDE.md Survives compaction!

claude -c Continue last conv

claude -r "name" Resume by name

/btw question Side Q, no context cost

claude -p "query" Non-interactive

\--output-format json Structured output

\--max-budget-usd 5 Cost cap

cat file | claude -p Pipe input

/loop 5m msg Recurring task

/rc Remote control

\--remote Web session on claude.ai

Config Files

~/.claude/settings.json User settings

.claude/settings.json Project (shared)

.claude/settings.local.json Local only

~/.claude.json OAuth, MCP, state

.mcp.json Project MCP servers

Key Settings

modelOverrides Map model picker → custom IDs

autoMemoryDirectory Custom memory dir

worktree.sparsePaths Sparse checkout dirsNEW

ANTHROPIC\_API\_KEY

ANTHROPIC\_MODEL

CLAUDE\_CODE\_EFFORT\_LEVEL low/med/high

MAX\_THINKING\_TOKENS 0=off

ANTHROPIC\_CUSTOM\_MODEL\_OPTION Custom /model entry

CLAUDE\_CODE\_PLUGIN\_SEED\_DIR Multiple plugin seed dirs

Built-in Skills

/simplify Code review (3 parallel agents)

/batch Large parallel changes (5-30 worktrees)

/debug \[desc\] Troubleshoot from debug log

/loop \[interval\] Recurring scheduled task

/claude-api Load API + SDK reference

.claude/skills/<name>/ Project skills

~/.claude/skills/<name>/ Personal skills

Skill Frontmatter

description Auto-invocation trigger

allowed-tools Skip permission prompts

model Override model for skill

effort Override effort levelNEW

context: fork Run in subagent

$ARGUMENTS User input placeholder

${CLAUDE\_SKILL\_DIR} Skill's own directory

!\`cmd\` Dynamic context injection

Built-in Agents

Explore Fast read-only (Haiku)

Plan Research for plan mode

General Full tools, complex tasks

Bash Terminal separate context

Agent Frontmatter

permissionMode default/acceptEdits/dontAsk/plan

isolation: worktree Run in git worktree

memory: user|project Persistent memory

background: true Background task

maxTurns Limit agentic turns

SendMessage Resume agents (replaces resume)NEW

Core Commands

claude Interactive

claude "q" With prompt

claude -p "q" Headless

claude -c Continue last

claude -r "n" Resume

claude update Update

Key Flags

\--model Set model

\-w Git worktree

\-n / --name Session name

\--add-dir Add dir

\--agent Use agent

\--allowedTools Pre-approve

\--output-format json/stream

\--json-schema Structured

\--max-turns Limit turns

\--max-budget-usd Cost cap

\--console Auth via Anthropic Console

\--verbose Verbose

\--bare Minimal headless (no hooks/LSP)NEW

\--channels Permission relay / MCP pushNEW

\--remote Web session

\--chrome Chrome
