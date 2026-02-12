---
title: "Thread by @bcherny"
source: "https://x.com/bcherny/status/2021701379409273093"
author:
  - "[[@bcherny]]"
published: 2026-02-12
created: 2026-02-12
description: "Claude Code @anthropicai"
tags:
  - "clippings"
---
**Boris Cherny** @bcherny [2026-02-11](https://x.com/bcherny/status/2021699851499798911)

Reflecting on what engineers love about Claude Code, one thing that jumps out is its customizability: hooks, plugins, LSPs, MCPs, skills, effort, custom agents, status lines, output styles, etc.

Every engineer uses their tools differently. We built Claude Code from the ground up

---

**Boris Cherny** @bcherny [2026-02-11](https://x.com/bcherny/status/2021699859359883608)

1/ Configure your terminal

\- Theme: Run /config to set light/dark mode

\- Notifs: Enable notifications for iTerm2, or use a custom notifs hook

\- Newlines: If you use Claude Code in an IDE terminal, Apple Terminal, Warp, or Alacritty, run /terminal-setup to enable shift+enter for

![Image](https://pbs.twimg.com/media/HA6EwD8bsAQnna5?format=jpg&name=large)

---

**Boris Cherny** @bcherny [2026-02-11](https://x.com/bcherny/status/2021699860869902424)

2/ Adjust effort level

Run /model to pick your preferred effort level. Set it to:

\- Low, for less tokens & faster responses

\- Medium, for balanced behavior

\- High, for more tokens & more intelligence

Personally, I use High for everything.

![Image](https://pbs.twimg.com/media/HA6FCTCakAI5FFk?format=png&name=large)

---

**Boris Cherny** @bcherny [2026-02-11](https://x.com/bcherny/status/2021699862522364149)

3/ Install Plugins, MCPs, and Skills

Plugins let you install LSPs (now available for every major language), MCPs, skills, agents, and custom hooks.

Install a plugin from the official Anthropic plugin marketplace, or create your own marketplace for your company. Then, check the

![Image](https://pbs.twimg.com/media/HA6FQOSbcAA6ybR?format=jpg&name=large)

---

**Boris Cherny** @bcherny [2026-02-11](https://x.com/bcherny/status/2021700144039903699)

4/ Create custom agents

To create custom agents, drop .md files in .claude/agents. Each agent can have a custom name, color, tool set, pre-allowed and pre-disallowed tools, permission mode, and model.

There's also a little-known feature in Claude Code that lets you set the

![Image](https://pbs.twimg.com/media/HA6Fi_WaMAA2_LG?format=png&name=large)

---

**Boris Cherny** @bcherny [2026-02-11](https://x.com/bcherny/status/2021700332292911228)

5/ Pre-approve common permissions

Claude Code uses a sophisticated permission system with a combo of prompt injection detection, static analysis, sandboxing, and human oversight.

Out of the box, we pre-approve a small set of safe commands. To pre-approve more, run /permissions

![Image](https://pbs.twimg.com/media/HA6FurbbsAM95NS?format=png&name=large)

---

**Boris Cherny** @bcherny [2026-02-11](https://x.com/bcherny/status/2021700506465579443)

6/ Enable sandboxing

Opt into Claude Code's open source sandbox runtime (https://github.com/anthropic-experimental/sandbox-runtime…) to improve safety while reducing permission prompts.

Run /sandbox to enable it. Sandboxing runs on your machine, and supports both file and network isolation. Windows support

![Image](https://pbs.twimg.com/media/HA6F4hrbsAEjpXW?format=png&name=large)

---

**Boris Cherny** @bcherny [2026-02-11](https://x.com/bcherny/status/2021700784019452195)

7/ Add a status line

Custom status lines show up right below the composer, and let you show model, directory, remaining context, cost, and pretty much anything else you want to see while you work.

Everyone on the Claude Code team has a different statusline. Use /statusline to

![Image](https://pbs.twimg.com/media/HA6GIPDaEAEE7nm?format=jpg&name=large)

---

**Boris Cherny** @bcherny [2026-02-11](https://x.com/bcherny/status/2021700883873165435)

8/ Customize your keybindings

Did you know every key binding in Claude Code is customizable? /keybindings to re-map any key. Settings live reload so you can see how it feels immediately

---

**Boris Cherny** @bcherny [2026-02-11](https://x.com/bcherny/status/2021701059253874861)

9/ Set up hooks

Hooks are a way to deterministically hook into Claude's lifecycle. Use them to:

\- Automatically route permission requests to Slack or Opus

\- Nudge Claude to keep going when it reaches the end of a turn (you can even kick off an agent or use a prompt to decide
