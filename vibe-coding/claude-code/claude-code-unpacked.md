---
title: "Claude Code Unpacked"
source: "https://ccunpacked.dev/"
author:
  - "[[Claude Code Unpacked]]"
published:
created: 2026-04-03
description: "What actually happens when you type a message into Claude Code? The agent loop, 50+ tools, multi-agent orchestration, and unreleased features, mapped from source."
tags:
  - "clippings"
---

> [!summary]
> An interactive exploration of Claude Code's source architecture, mapping its 1,891+ files and 517K+ lines of TypeScript across tools (53+), commands (95+), and internal modules. Provides a visual treemap of the source tree and catalogs every built-in tool and slash command by category, including hidden feature-flagged capabilities.

What actually happens when you type a message into Claude Code? The agent loop, 50+ tools, multi-agent orchestration, and unreleased features, mapped straight from the source.

1,891+

Files

517K+

Lines of Code

53+

Tools

95+

Commands

[Start exploring↓](#agent-loop)

02

## Architecture Explorer

Click around the source tree to explore what's inside.

Tools & Commands

Core Processing

UI Layer

Infrastructure

Support & Utilities

Personality & UX

<svg viewBox="0 0 900 500" class="w-full h-auto" role="img" aria-label="Treemap visualization of Claude Code source architecture"><g class="cursor-pointer" role="button" tabindex="0" aria-label="utils directory, 564 files. Shared utility modules — the largest directory by far" opacity="0"><rect x="3" y="3" width="455.11414790996787" height="291.13221406086046" fill="#8A8580" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect><text x="11" y="23" fill="#0D0D0D" font-size="13" font-weight="600" font-family="var(--font-mono)" pointer-events="none">utils/</text> <text x="11" y="41" fill="rgba(13,13,13,0.6)" font-size="11" font-family="var(--font-mono)" pointer-events="none">564 files</text></g> <g class="cursor-default" role="button" tabindex="0" aria-label="components directory, 389 files. React (`Ink`) components for the terminal UI" opacity="0"><rect x="3" y="297.13221406086046" width="455.11414790996787" height="199.86778593913954" fill="#7B9EB8" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect><text x="11" y="317.13221406086046" fill="#0D0D0D" font-size="13" font-weight="600" font-family="var(--font-mono)" pointer-events="none">components/</text> <text x="11" y="335.13221406086046" fill="rgba(13,13,13,0.6)" font-size="11" font-family="var(--font-mono)" pointer-events="none">389 files</text></g> <g class="cursor-default" role="button" tabindex="0" aria-label="commands directory, 189 files. 95 CLI command handlers — from `/init` to `/ultraplan`" opacity="0"><rect x="461.11414790996787" y="3" width="161.90939571573767" height="270.8127053669222" fill="#D4A853" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect><text x="469.11414790996787" y="23" fill="#0D0D0D" font-size="13" font-weight="600" font-family="var(--font-mono)" pointer-events="none">commands/</text> <text x="469.11414790996787" y="41" fill="rgba(13,13,13,0.6)" font-size="11" font-family="var(--font-mono)" pointer-events="none">189 files</text></g> <g class="cursor-default" role="button" tabindex="0" aria-label="tools directory, 184 files. 42 built-in tool implementations plus 11 feature-gated tools registered in `tools.ts`" opacity="0"><rect x="626.0235436257055" y="3" width="157.54671328939548" height="270.8127053669222" fill="#D4A853" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect><text x="634.0235436257055" y="23" fill="#0D0D0D" font-size="13" font-weight="600" font-family="var(--font-mono)" pointer-events="none">tools/</text> <text x="634.0235436257055" y="41" fill="rgba(13,13,13,0.6)" font-size="11" font-family="var(--font-mono)" pointer-events="none">184 files</text></g> <g class="cursor-pointer" role="button" tabindex="0" aria-label="services directory, 130 files. Core service layer — API, MCP, compaction, streaming, analytics" opacity="0"><rect x="786.570256915101" y="3" width="110.42974308489897" height="270.8127053669222" fill="#6BA368" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect><text x="794.570256915101" y="23" fill="#0D0D0D" font-size="13" font-weight="600" font-family="var(--font-mono)" pointer-events="none">services/</text> <text x="794.570256915101" y="41" fill="rgba(13,13,13,0.6)" font-size="11" font-family="var(--font-mono)" pointer-events="none">130 files</text></g> <g class="cursor-default" role="button" tabindex="0" aria-label="hooks directory, 104 files. React hooks for terminal UI state management" opacity="0"><rect x="461.11414790996787" y="276.8127053669222" width="211.09065955611322" height="113.05739320920043" fill="#7B9EB8" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect><text x="469.11414790996787" y="296.8127053669222" fill="#0D0D0D" font-size="13" font-weight="600" font-family="var(--font-mono)" pointer-events="none">hooks/</text> <text x="469.11414790996787" y="314.8127053669222" fill="rgba(13,13,13,0.6)" font-size="11" font-family="var(--font-mono)" pointer-events="none">104 files</text></g> <g class="cursor-default" role="button" tabindex="0" aria-label="ink directory, 96 files. `Ink` framework extensions — React rendering in the terminal via `Yoga` flexbox" opacity="0"><rect x="461.11414790996787" y="392.87009857612264" width="211.09065955611322" height="104.12990142387736" fill="#7B9EB8" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect><text x="469.11414790996787" y="412.87009857612264" fill="#0D0D0D" font-size="13" font-weight="600" font-family="var(--font-mono)" pointer-events="none">ink/</text> <text x="469.11414790996787" y="430.87009857612264" fill="rgba(13,13,13,0.6)" font-size="11" font-family="var(--font-mono)" pointer-events="none">96 files</text></g> <g class="cursor-default" role="button" tabindex="0" aria-label="bridge directory, 31 files. Remote control infrastructure — control Claude Code from phone or browser" opacity="0"><rect x="675.2048074660811" y="276.8127053669222" width="94.41125009803147" height="73.03083663324628" fill="#C17B5E" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect><text x="683.2048074660811" y="296.8127053669222" fill="#0D0D0D" font-size="13" font-weight="600" font-family="var(--font-mono)" pointer-events="none">bridge/</text> <text x="683.2048074660811" y="314.8127053669222" fill="rgba(13,13,13,0.6)" font-size="11" font-family="var(--font-mono)" pointer-events="none">31 files</text></g> <g class="cursor-default" role="button" tabindex="0" aria-label="constants directory, 21 files. Configuration constants, feature flags, default values" opacity="0"><rect x="675.2048074660811" y="352.8435420001685" width="94.41125009803147" height="48.50476029994104" fill="#8A8580" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect><text x="683.2048074660811" y="372.8435420001685" fill="#0D0D0D" font-size="13" font-weight="600" font-family="var(--font-mono)" pointer-events="none">constants/</text> <text x="683.2048074660811" y="390.8435420001685" fill="rgba(13,13,13,0.6)" font-size="11" font-family="var(--font-mono)" pointer-events="none">21 files</text></g> <g class="cursor-default" role="button" tabindex="0" aria-label="skills directory, 20 files. Skill system — loadable prompt modules for specialized tasks" opacity="0"><rect x="675.2048074660811" y="404.34830230010954" width="94.41125009803147" height="46.05215266661048" fill="#D4A853" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect><text x="683.2048074660811" y="424.34830230010954" fill="#0D0D0D" font-size="13" font-weight="600" font-family="var(--font-mono)" pointer-events="none">skills/</text> <text x="683.2048074660811" y="442.34830230010954" fill="rgba(13,13,13,0.6)" font-size="11" font-family="var(--font-mono)" pointer-events="none">20 files</text></g> <g class="cursor-default" role="button" tabindex="0" aria-label="cli directory, 19 files. CLI transport layer — `stdin`/`stdout`, `NDJSON`, remote IO" opacity="0"><rect x="675.2048074660811" y="453.40045496672" width="94.41125009803147" height="43.59954503327998" fill="#C17B5E" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect><text x="683.2048074660811" y="473.40045496672" fill="#0D0D0D" font-size="13" font-weight="600" font-family="var(--font-mono)" pointer-events="none">cli/</text></g><g class="cursor-default" role="button" tabindex="0" aria-label="keybindings directory, 14 files. Terminal keyboard shortcuts and Vim mode bindings" opacity="0"><rect x="772.6160575641126" y="276.8127053669222" width="45.19932957033575" height="66.3943689195284" fill="#7B9EB8" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="tasks directory, 12 files. Background task management for agent sub-tasks" opacity="0"><rect x="820.8153871344483" y="276.8127053669222" width="38.3137110602878" height="66.3943689195284" fill="#6BA368" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="types directory, 11 files. Shared TypeScript type definitions" opacity="0"><rect x="862.1290981947361" y="276.8127053669222" width="34.870901805263884" height="66.3943689195284" fill="#8A8580" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="migrations directory, 11 files. Data migration scripts between versions" opacity="0"><rect x="772.6160575641126" y="346.2070742864506" width="35.92287129985448" height="64.5188454352168" fill="#8A8580" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="context directory, 9 files. Context assembly — `CLAUDE.md`, tools, memory, system prompt" opacity="0"><rect x="811.538928863967" y="346.2070742864506" width="28.845985608971887" height="64.5188454352168" fill="#6BA368" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="memdir directory, 8 files. Persistent memory directory — session-to-session knowledge" opacity="0"><rect x="843.3849144729389" y="346.2070742864506" width="25.30754276353059" height="64.5188454352168" fill="#6BA368" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="entrypoints directory, 8 files. CLI bootstrap — main entry points for the `claude` command" opacity="0"><rect x="871.6924572364695" y="346.2070742864506" width="25.30754276353059" height="64.5188454352168" fill="#C17B5E" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="state directory, 6 files. Global state management stores" opacity="0"><rect x="772.6160575641126" y="413.7259197216674" width="44.07667437848011" height="27.449675392352674" fill="#8A8580" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="buddy directory, 6 files. AI companion pet — an easter egg with species, rarity, and personality" opacity="0"><rect x="772.6160575641126" y="444.1755951140201" width="44.07667437848011" height="27.449675392352674" fill="#9B7CB8" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="vim directory, 5 files. Vim mode — modal editing keybindings for the terminal UI" opacity="0"><rect x="772.6160575641126" y="474.6252705063728" width="44.07667437848011" height="22.37472949362723" fill="#9B7CB8" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="remote directory, 4 files. Remote session management" opacity="0"><rect x="819.6927319425927" y="413.7259197216674" width="23.76908935246911" height="32.699619425516914" fill="#C17B5E" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="query directory, 4 files. Query processing pipeline" opacity="0"><rect x="846.4618212950618" y="413.7259197216674" width="23.76908935246911" height="32.699619425516914" fill="#6BA368" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="native-ts directory, 4 files. Native TypeScript compilation helpers" opacity="0"><rect x="873.2309106475309" y="413.7259197216674" width="23.76908935246911" height="32.699619425516914" fill="#8A8580" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="server directory, 3 files. `HTTP`/`WebSocket` server for bridge and remote modes" opacity="0"><rect x="819.6927319425927" y="449.42553914718434" width="25.343741667320273" height="22.287230426407802" fill="#C17B5E" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="screens directory, 3 files. Full-screen terminal UI views" opacity="0"><rect x="819.6927319425927" y="474.71276957359214" width="25.343741667320273" height="22.28723042640786" fill="#7B9EB8" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="upstreamproxy directory, 2 files. `HTTP` proxy for API request interception" opacity="0"><rect x="848.036473609913" y="449.42553914718434" width="20.619784722766894" height="17.229784341126276" fill="#C17B5E" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="plugins directory, 2 files. Plugin system — external extension loading" opacity="0"><rect x="848.036473609913" y="469.6553234883106" width="20.619784722766894" height="17.229784341126276" fill="#D4A853" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="voice directory, 1 files. Voice mode — microphone input for hands-free coding" opacity="0"><rect x="848.036473609913" y="489.8851078294369" width="20.619784722766894" height="7.11489217056311" fill="#9B7CB8" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="schemas directory, 1 files. `Zod` schemas for configuration validation" opacity="0"><rect x="871.6562583326798" y="449.42553914718434" width="11.171870833660137" height="13.85815361760524" fill="#8A8580" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="outputStyles directory, 1 files. Terminal output formatting styles" opacity="0"><rect x="885.82812916634" y="449.42553914718434" width="11.171870833660023" height="13.85815361760524" fill="#7B9EB8" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="moreright directory, 1 files. Extended permission rule helpers" opacity="0"><rect x="871.6562583326798" y="466.2836927647896" width="11.171870833660137" height="13.858153617605183" fill="#8A8580" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="coordinator directory, 1 files. Multi-agent mode toggle — actual orchestration lives in `utils/swarm/`" opacity="0"><rect x="885.82812916634" y="466.2836927647896" width="11.171870833660023" height="13.858153617605183" fill="#6BA368" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="bootstrap directory, 1 files. Application bootstrap state" opacity="0"><rect x="871.6562583326798" y="483.14184638239476" width="11.171870833660137" height="13.85815361760524" fill="#C17B5E" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g><g class="cursor-default" role="button" tabindex="0" aria-label="assistant directory, 1 files. Session history for assistant mode" opacity="0"><rect x="885.82812916634" y="483.14184638239476" width="11.171870833660023" height="13.85815361760524" fill="#6BA368" rx="4" class="transition-[filter] duration-200 hover:brightness-125" stroke="rgba(0,0,0,0.3)" stroke-width="1"></rect></g></svg>

03

## Tool System

Every built-in tool Claude Code can call, sorted by what it does.

File Operations

6 tools

Execution

3 tools

Search & Fetch

4 tools

Agents & Tasks

11 tools

Planning

5 tools

MCP

4 tools

System

11 tools

Experimental

8 tools

Click a tool to see details and source code

04

## Command Catalog

Every slash command available in Claude Code, sorted by what it does.

Setup & Config12

Daily Workflow24

Code Review & Git13

Debugging & Diagnostics23

Advanced & Experimental23

Click a command to see details and source code

05

## Hidden Features

Stuff that's in the code but not shipped yet. Feature-flagged, env-gated, or just commented out.

Click a feature to explore
