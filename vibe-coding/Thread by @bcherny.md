---
title: "Thread by @bcherny"
source: "https://x.com/bcherny/status/2017742741636321619"
author:
  - "[[@bcherny]]"
published: 2026-02-01
created: 2026-02-01
description:
tags:
  - "clippings"
---
**Boris Cherny** @bcherny [2026-01-31](https://x.com/bcherny/status/2017742741636321619)

I'm Boris and I created Claude Code. I wanted to quickly share a few tips for using Claude Code, sourced directly from the Claude Code team. The way the team uses Claude is different than how I use it. Remember: there is no one right way to use Claude Code -- everyones' setup is different. You should experiment to see what works for you!

---

**Boris Cherny** @bcherny [2026-01-31](https://x.com/bcherny/status/2017742743125299476)

1\. Do more in parallel

Spin up 3–5 git worktrees at once, each running its own Claude session in parallel. It's the single biggest productivity unlock, and the top tip from the team. Personally, I use multiple git checkouts, but most of the Claude Code team prefers worktrees -- it's the reason @amorriscode built native support for them into the Claude Desktop app!

Some people also name their worktrees and set up shell aliases (za, zb, zc) so they can hop between them in one keystroke. Others have a dedicated "analysis" worktree that's only for reading logs and running BigQuery

See https://code.claude.com/docs/en/common-workflows#run-parallel-claude-code-sessions-with-git-worktrees…

![Image](https://pbs.twimg.com/media/HABmmP6bwAAWgUM?format=jpg&name=large)

---

**Boris Cherny** @bcherny [2026-01-31](https://x.com/bcherny/status/2017742745365057733)

2\. Start every complex task in plan mode. Pour your energy into the plan so Claude can 1-shot the implementation.

One person has one Claude write the plan, then they spin up a second Claude to review it as a staff engineer.

Another says the moment something goes sideways, they

![Image](https://pbs.twimg.com/media/HABm-MtbEAAMlsS?format=png&name=large)

---

**Boris Cherny** @bcherny [2026-01-31](https://x.com/bcherny/status/2017742747067945390)

3\. Invest in your http://CLAUDE.md. After every correction, end with: "Update your http://CLAUDE.md so you don't make that mistake again." Claude is eerily good at writing rules for itself.

Ruthlessly edit your http://CLAUDE.md over time. Keep iterating

![Image](https://pbs.twimg.com/media/HABoHn9bQAAE-S1?format=png&name=large)

---

**Boris Cherny** @bcherny [2026-01-31](https://x.com/bcherny/status/2017742748984742078)

4\. Create your own skills and commit them to git. Reuse across every project.

Tips from the team:

\- If you do something more than once a day, turn it into a skill or command

\- Build a /techdebt slash command and run it at the end of every session to find and kill duplicated code

\- Set up a slash command that syncs 7 days of Slack, GDrive, Asana, and GitHub into one context dump

\- Build analytics-engineer-style agents that write dbt models, review code, and test changes in dev

Learn more:

---

**Boris Cherny** @bcherny [2026-01-31](https://x.com/bcherny/status/2017742750473720121)

5\. Claude fixes most bugs by itself. Here's how we do it:

Enable the Slack MCP, then paste a Slack bug thread into Claude and just say "fix." Zero context switching required.

Or, just say "Go fix the failing CI tests." Don't micromanage how.

Point Claude at docker logs to

![Image](https://pbs.twimg.com/media/HABy6cObEAQ4Rep?format=png&name=large)

---

**Boris Cherny** @bcherny [2026-01-31](https://x.com/bcherny/status/2017742752566632544)

6\. Level up your prompting

a. Challenge Claude. Say "Grill me on these changes and don't make a PR until I pass your test." Make Claude be your reviewer. Or, say "Prove to me this works" and have Claude diff behavior between main and your feature branch

b. After a mediocre

---

**Boris Cherny** @bcherny [2026-01-31](https://x.com/bcherny/status/2017742753971769626)

7\. Terminal & Environment Setup

The team loves Ghostty! Multiple people like its synchronized rendering, 24-bit color, and proper unicode support.

For easier Claude-juggling, use /statusline to customize your status bar to always show context usage and current git branch. Many

![Image](https://pbs.twimg.com/media/HABpv-MbEAAIskz?format=jpg&name=large)

---

**Boris Cherny** @bcherny [2026-01-31](https://x.com/bcherny/status/2017742755737555434)

8\. Use subagents

a. Append "use subagents" to any request where you want Claude to throw more compute at the problem

b. Offload individual tasks to subagents to keep your main agent's context window clean and focused

c. Route permission requests to Opus 4.5 via a hook — let it

![Image](https://pbs.twimg.com/media/HAB0KLmbEAEfDJ6?format=png&name=large)

---

**Boris Cherny** @bcherny [2026-01-31](https://x.com/bcherny/status/2017742757666902374)

9\. Use Claude for data & analytics

Ask Claude Code to use the "bq" CLI to pull and analyze metrics on the fly. We have a BigQuery skill checked into the codebase, and everyone on the team uses it for anlytics queries directly in Claude Code. Personally, I haven't written a line
