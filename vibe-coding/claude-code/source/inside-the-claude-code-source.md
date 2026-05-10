---
title: "Inside the Claude Code source"
source: "https://gist.github.com/Haseeb-Qureshi/d0dc36844c19d26303ce09b42e7188c1?utm_source=tldrnewsletter"
author:
published:
created: 2026-04-06
description: "Inside the Claude Code source. GitHub Gist: instantly share code, notes, and snippets."
tags:
  - "clippings"
---

> [!summary]
> A deep technical analysis of Claude Code's source architecture, comparing it with OpenAI's Codex. Covers the async generator agent loop, React/Ink terminal UI, four-layer compaction hierarchy (proactive, reactive, snip, context collapse), prompt cache boundary trick for global token reuse, asymmetric session persistence, and build-time dead code elimination via feature flags. Key insight: the ~500K-line "harness" around the API call is where production experience lives.

Anthropic's Claude Code CLI source code leaked onto GitHub recently. All of it. About 1,900 files and a lot of TypeScript.

I read through the key modules. What follows is a breakdown of the surprising parts: how the system actually works, where Anthropic made clever engineering choices, and where their approach diverges from OpenAI's Codex in ways you wouldn't guess from using either tool.

## Lifecycle of a request

Here's what happens when you type a message into Claude Code:

```
User types message
         |
         v
  +-----------------+
  | Process Input   |  Slash commands, attachments, queued commands
  +-----------------+
         |
         v
  +-----------------+
  | Assemble System |  15 composable prompt sections
  | Prompt          |  split at DYNAMIC_BOUNDARY for caching
  +-----------------+
         |
         v
  +-----------------+
  | Snapshot Files  |  LRU cache (100 files, 25MB) for undo
  +-----------------+
         |
         v
  +=====================+
  | query() loop        |  while(true) {
  |                     |
  |  +---------------+  |    Stream from Anthropic API
  |  | LLM Response  |-------> text, tool_use blocks, thinking
  |  +---------------+  |
  |         |           |
  |    tool_use?        |
  |    /        \       |
  |  yes         no     |
  |   |           |     |
  |   v           v     |
  | Execute    end_turn |----> Return to user
  | Tools        or     |
  |   |       budget    |
  |   v       exceeded  |
  | Feed results back   |
  | as user messages    |
  |   |                 |
  |   +---> continue    |
  |                     |
  | If context too big: |
  |   compact and       |
  |   continue          |
  +=====================+
         |
         v
  +-----------------+
  | Persist session |  JSON transcript (fire-and-forget
  | transcript      |  for assistant, awaited for user)
  +-----------------+
```

The whole thing is an async generator. Every event (text chunks, tool calls, progress updates, errors, compaction boundaries) flows through one `yield` -based stream. The CLI, SDK, and IDE bridge all consume the same event stream. They just render it differently.

This is different from Codex, which uses a Rust `Session` struct with `submit()` and `next_event()` methods on an async channel. Same idea, different concurrency primitive. Claude Code's generator pattern is more composable because you can `yield*` into sub-generators. Codex's channel pattern is more explicit about ownership.

## The terminal UI is a React app

This surprised me. The CLI entrypoint is `src/entrypoints/cli.tsx`. That `.tsx` extension is not a typo. The entire terminal interface is a React component tree rendered with Ink, which is React for the terminal.

Message bubbles, tool call displays, permission prompts, progress indicators, the markdown renderer: all React components. Same mental model as a web app, except the "DOM" is your terminal.

Codex went a completely different direction. Their TUI is built in Rust with `ratatui` and `crossterm`. No JavaScript in the rendering path at all. The Rust TUI has lower memory overhead and faster rendering, but the Claude Code approach means the same team that builds the web experience can contribute to the CLI. I think that's the real reason they did it this way.

## Compaction: four strategies vs. two

This is where the two tools diverge most interestingly, and it's invisible from the outside.

When you use a coding agent for a long session, the conversation eventually overflows the LLM's context window. Both tools solve this, but differently.

Claude Code runs four compaction strategies in a hierarchy:

1. Proactive compaction. Monitors token count each turn. When it approaches the limit, it summarizes older messages into a "compact boundary" marker. Everything before the boundary gets replaced with a summary. This happens before sending to the API, so the user never sees a failure.
2. Reactive compaction. A fallback. If the proactive check misses (race condition, bad token estimate) and the API returns `prompt_too_long`, this catches the error, compacts retroactively, and retries. The user sees a brief delay, not a crash.
3. Snip compaction. SDK/headless mode only. Instead of summarizing, it truncates at defined boundaries to keep memory bounded in long automated sessions. The REPL keeps full history for scrollback; the SDK doesn't need to.
4. Context collapse. Feature-flagged, internally called "marble\_origami." Compresses verbose tool results mid-conversation without triggering full compaction. If a tool returned 500 lines of output three turns ago and you don't need it anymore, this collapses it to a shorter representation. The interesting wrinkle: collapse commits are persisted to the transcript as `ContextCollapseCommitEntry` records, which means they can be selectively un-compacted later. Codex has nothing equivalent to this.

Codex takes a different approach. It has `compact.rs` and `compact_remote.rs` in its Rust core. It supports pre-turn compaction (before sending to the API) and mid-turn compaction (while processing). It also has a `compact_remote` variant that delegates summarization to a remote service.

The key architectural difference: Codex tracks a `reference_context_item` that snapshots settings between turns, then diffs against it to only send changed items. Claude Code doesn't do this. It re-sends the full system prompt each turn, relying on prompt caching to avoid the cost. Codex minimizes what gets sent at the protocol level.

Both use LLM-generated summaries for the actual compaction. Claude Code's four-layer fallback chain is more defensive. Codex's diff-based approach is more token-efficient per turn.

## The prompt cache boundary trick

The system prompt is assembled from about 15 composable functions. The clever part is the cache split.

A marker called `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` divides the prompt into two halves. Everything above is static: behavioral instructions, coding style rules, safety guidelines. Everything below is per-session: the user's CLAUDE.md files, MCP server instructions, environment info.

The static half gets cached with `scope: 'global'` in the API. The source has comments about "Blake2b prefix hash variants," meaning they hash the cacheable prefix to maximize cache hits across users. About 3,000 tokens of instructions are cached and reused globally. Per-session context is injected after the boundary.

Codex doesn't have an equivalent mechanism. Its system prompt is smaller and more focused, with the sandbox policy injected directly. Claude Code pays for a larger prompt but amortizes the cost through caching. Codex keeps the prompt small and avoids the caching complexity entirely.

## Anthropic's internal prompts are different from yours

A `process.env.USER_TYPE === 'ant'` check runs throughout the prompt construction. Internal Anthropic engineers get different instructions than external users.

Some of the differences:

- Internal: "If you notice the user's request is based on a misconception, say so." External users don't get this.
- Internal: "Never claim 'all tests pass' when output shows failures." This is an anti-hallucination guardrail that was apparently needed badly enough to add explicitly.
- Internal: "Keep text between tool calls to <=25 words." A source comment notes "research shows ~1.2% output token reduction vs qualitative 'be concise'." They A/B tested this specific phrasing.
- Internal: a `VERIFICATION_AGENT` feature flag that spawns an adversarial sub-agent to review non-trivial changes before reporting completion.

There are `@[MODEL LAUNCH]` markers throughout the code, like `capy v8 thoroughness counterweight (PR #24302)`. These are A/B test tracking annotations. Anthropic iterates on prompt wording the way ad companies iterate on copy.

There's also an `isUndercover()` mode that strips all model names and IDs from the system prompt, so internal model identifiers can't leak into public commits or PRs. The dead code elimination comments around this are paranoid in a good way:

```
// DCE: \`process.env.USER_TYPE === 'ant'\` is build-time
// --define. It MUST be inlined at each callsite (not
// hoisted to a const) so the bundler can constant-fold
// it to \`false\` in external builds and eliminate the
// branch.
```

## Build-time dead code elimination

The codebase uses Bun's `feature()` function for compile-time feature flags:

```
import { feature } from 'bun:bundle'

if (feature('VOICE_MODE')) {
  // stripped at build time if flag is off
}
```

The conditional imports are structured so the bundler can eliminate entire modules:

```
const proactiveModule =
  feature('PROACTIVE') || feature('KAIROS')
    ? require('../proactive/index.js')
    : null
```

If the flag is off, the `require` never executes and the module is tree-shaken out. This is how Anthropic ships different builds for different contexts: the public CLI, the internal build, the SDK, the IDE bridge. Same codebase, different feature sets, no runtime cost for disabled features.

Some of the flags hint at unreleased capabilities: `VOICE_MODE`, `COORDINATOR_MODE`, `KAIROS` (appears to be an autonomous proactive agent), `ABLATION_BASELINE` (A/B testing infrastructure).

## Session persistence is asymmetric on purpose

Transcript writes are fire-and-forget for assistant messages but `await` ed for user messages. The source comment explains the reasoning:

```
If the process is killed before the API responds, the
transcript is left with only queue-operation entries;
getLastSessionLog filters those out, returns null, and
--resume fails with "No conversation found". Writing
now makes the transcript resumable from the point the
user message was accepted.
```

This is a production scar. Someone lost a session because the process died between the user hitting enter and the API responding. The fix: always persist the user's message synchronously, but let assistant messages write asynchronously (they're already durable in the API response and can be replayed).

Codex stores sessions differently. JSONL files with a `session_log.rs` module and a `resume_picker.rs` for resuming. It also has a SQLite-backed state system in `codex-rs/state/` for thread metadata, agent jobs, and memories. Heavier infrastructure, but more queryable.

## The "thinking rules" scar

There's a comment in `query.ts` that tells you everything about the pain of shipping a production agent:

```
The rules of thinking are lengthy and fortuitous. They
require plenty of thinking of most long duration and deep
meditation for a wizard to wrap one's noggin around.

The rules follow:
1. A message that contains a thinking block must be part
   of a query whose max_thinking_length > 0
2. A thinking block may not be the last message in a block
3. Thinking blocks must be preserved for the duration of
   an assistant trajectory

Heed these rules well, young wizard. For they are the
rules of thinking, and the rules of thinking are the
rules of the universe. If ye does not heed these rules,
ye will be punished with an entire day of debugging and
hair pulling.
```

Not documentation. A warning from someone who lost a day to a subtle API constraint. The mock-medieval English is there to make sure nobody skims past it.

## The permission system feeds denials back to the model

Every tool call passes through a permission pipeline: mode check, hook evaluation, rule matching, user prompt. That part is straightforward.

What's less obvious is what happens on denial. The permission denial is wrapped as a tool result and fed back to the model as if the tool had returned an error. Claude sees "permission denied" as a tool output and adjusts its approach. The system also tracks all denials across the session and reports them to the SDK caller, so IDE integrations can surface patterns (e.g., "the user keeps denying bash commands in /etc").

Codex handles permissions at a different level entirely. Because it has OS-level sandboxing, many decisions happen at the kernel, not the application. The model never tries to run `rm -rf /` and gets denied; the sandbox prevents it silently. When something does get blocked, Codex has a "sandbox escalation" pattern where a denied action can trigger a sandbox policy upgrade (with user approval) and retry.

There's also a subtle OS-level detail in Codex's process management: on Linux, it sets a parent death signal via `prctl(2)` on spawned child processes. If the main Codex process dies, all its children get killed automatically. No orphan processes lingering. Claude Code doesn't need this because its tools run in-process, not as subprocesses.

## Speculation and memory prefetch

Two latency-hiding tricks that aren't visible from the outside.

Speculation: Claude Code pre-computes likely next responses while the user is typing. For predictable interactions (follow-up questions, confirmation prompts), the response can be ready before the user hits enter.

Memory prefetch during streaming: while the model generates its response, the system prefetches relevant memories from CLAUDE.md files:

```
using pendingMemoryPrefetch =
  startRelevantMemoryPrefetch(
    state.messages,
    state.toolUseContext,
  )
```

The `using` keyword is TC39 explicit resource management. It ensures the prefetch is cleaned up on all generator exit paths (normal completion, early abort, error). The prefetch runs alongside the stream, and the results are available by the time tools start executing. This hides the I/O latency of memory loading.

## What "harness" means here

Claude Code is about 500K lines of TypeScript. The actual API call is maybe 200 of them.

Everything else is the harness. Four-layer compaction. Prompt cache boundaries. Permission pipeline with denial feedback. Asymmetric session persistence. Build-time feature flags. Speculative pre-computation. Memory prefetch during streaming.

Nobody talks about the harness. Everyone talks about which model is smarter. But when I look at these two codebases, the model is the part that's most interchangeable. The harness is where the years of production experience live.
