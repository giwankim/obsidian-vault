---
title: "Learn Claude Code"
source: "https://learn.shareai.run/en/"
author:
published:
created: 2026-03-16
description: "Build a nano Claude Code-like agent from 0 to 1, one mechanism at a time"
tags:
  - "clippings"
  - "claude-code"
  - "coding-agents"
  - "agent-orchestration"
---

> [!summary]
> An educational resource that teaches how to build a Claude Code-like agent from scratch through 12 progressive sessions (184–694 LOC each), covering the agent loop, planning with TodoWrite, subagents, skills, context compaction, tasks, background execution, agent teams, team protocols, autonomous agents, and worktree isolation.

Build a nano Claude Code-like agent from 0 to 1, one mechanism at a time

[Start Learning](https://learn.shareai.run/en/timeline/)

## The Core Pattern

Every AI coding agent shares the same loop: call the model, execute tools, feed results back. Production systems add policy, permissions, and lifecycle layers on top.

```
while True:
    response = client.messages.create(messages=messages, tools=tools)
    if response.stop_reason != "tool_use":
        break
    for tool_call in response.content:
        result = execute_tool(tool_call.name, tool_call.input)
        messages.append(result)
```

## Message Growth

Watch the messages array grow as the agent loop executes

messages\[\]len=0

\[\]

## Learning Path

12 progressive sessions, from a simple loop to isolated autonomous execution[s0184 LOC](https://learn.shareai.run/en/s01/)

### The Agent Loop

The minimal agent kernel is a while loop + one tool

[View original](https://learn.shareai.run/en/s01/)### TodoWrite

s03176 LOC

An agent without a plan drifts; list the steps first, then execute

[View original](https://learn.shareai.run/en/s03/)### Subagents

s04151 LOC

Subagents use independent messages\[\], keeping the main conversation clean

[View original](https://learn.shareai.run/en/s04/)### Skills

s05187 LOC

Inject knowledge via tool\_result when needed, not upfront in the system prompt

[View original](https://learn.shareai.run/en/s05/)### Compact

s06205 LOC

Context will fill up; three-layer compression strategy enables infinite sessions

[View original](https://learn.shareai.run/en/s06/)### Tasks

s07207 LOC

A file-based task graph with ordering, parallelism, and dependencies -- the coordination backbone for multi-agent work

[View original](https://learn.shareai.run/en/s07/)### Background Tasks

s08198 LOC

Run slow operations in the background; the agent keeps thinking ahead

[View original](https://learn.shareai.run/en/s08/)### Agent Teams

s09348 LOC

When one agent can't finish, delegate to persistent teammates via async mailboxes

[View original](https://learn.shareai.run/en/s09/)### Team Protocols

s10419 LOC

One request-response pattern drives all team negotiation

[View original](https://learn.shareai.run/en/s10/)### Autonomous Agents

s11499 LOC

Teammates scan the board and claim tasks themselves; no need for the lead to assign each one

[View original](https://learn.shareai.run/en/s11/)### Worktree + Task Isolation

s12694 LOC

Each works in its own directory; tasks manage goals, worktrees manage directories, bound by ID

[View original](https://learn.shareai.run/en/s12/)

## Architectural Layers

Five orthogonal concerns that compose into a complete agent

### Tools & Execution

2 versions

### Planning & Coordination

4 versions

### Memory Management

1 versions

[s06: Compact](https://learn.shareai.run/en/s06/)

### Concurrency

1 versions

[s08: Background Tasks](https://learn.shareai.run/en/s08/)

### Collaboration

4 versions
