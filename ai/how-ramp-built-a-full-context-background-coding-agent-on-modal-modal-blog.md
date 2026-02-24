---
title: "How Ramp built a full context background coding agent on Modal | Modal Blog"
source: "https://modal.com/blog/how-ramp-built-a-full-context-background-coding-agent-on-modal"
author:
  - "[[Modal]]"
published:
created: 2026-02-24
description:
tags:
  - "clippings"
---

> [!summary]
> Ramp built "Inspect," a background coding agent on Modal Sandboxes that now writes over half of all merged PRs at Ramp. It uses filesystem snapshots for instant startup, runs full dev environments (Postgres, Redis, Temporal) in each sandbox, and is accessible to non-engineers via Slack, web, and Chrome extension.

GLM-5 is available to try on Modal.[Get started](https://modal.com/glm-5-endpoint)

February 19, 2026 • 4 minute read

![author](https://modal-cdn.com/cdnbot/gretas_ktpny8_7364f421.webp)

Greta Workman

Product Marketing

Ramp uses Modal to power [Ramp Inspect](https://builders.ramp.com/post/why-we-built-our-background-agent), an internal background coding agent that now writes [over half](https://x.com/rahulgs/status/2020984194038628832?s=20) of all merged pull requests at Ramp. Leveraging Modal Sandboxes, Ramp spins up full development environments in seconds, giving every builder at the company access to what is effectively unlimited parallel engineering capacity grounded by Ramp’s internal codebase, enterprise context, and developer tooling.

![](https://www.youtube.com/watch?v=ii9E5z8Gsrc)

## The idea: A coding agent as fast as local, accessible to everyone

Ramp's AI team saw an opportunity to give every builder at Ramp—engineers, product managers, designers—the ability to ship code using AI. They wanted to go beyond what was possible with local agents, which required dev environment setup and couldn't easily integrate with internal tooling. However, they knew that a background agent that was slower or less capable than working locally would never get adopted. Performance was crucial.

To get this right, it had to start just as fast as a local agent, integrate deeply enough with Ramp's stack—Sentry, Datadog, LaunchDarkly, Temporal—to verify its own work end to end, and require zero setup so anyone at Ramp could use it just as easily as an engineer.

![Ramp Inspect UI](https://modal-cdn.com/cdnbot/CleanShot%202026-02-18%20at%202129sj0wl7_df8084e4.webp)

## The solution: Inspect, a background coding agent on Modal

Ramp was already using Modal [for fine-tuning and batch inference](https://modal.com/blog/ramp-case-study), so building a background coding agent on top of Modal Sandboxes was a natural next step. A few engineers started prototyping on the side, and it quickly proved its value.

— Zach Bruggeman,Engineer at Ramp

Each Inspect session runs in a Modal Sandbox containing a full-stack development environment: Postgres, Redis, Temporal, RabbitMQ, and every service an engineer would have locally. Inside the sandbox, OpenCode runs as the coding agent, alongside a VS Code server for manual edits, a web terminal, and a VNC stack with Chromium for visual verification of frontend changes. The agent can take before-and-after screenshots, navigate the app in a real browser, and confirm its work visually—just as a human would. The whole setup is wired into GitHub, Slack, Buildkite, and Ramp's observability stack including Sentry and Datadog.

Running everything inside a single sandbox means the agent has the same low-latency access to services, files, and tools that an engineer would have locally. There's no network hop between the agent and the test suite, no remote filesystem to sync.

Outside the sandbox, the rest of Inspect's infrastructure is built on Modal's distributed primitives:

- [**Functions** run on a cron job](https://frontend.modal.com/docs/guide/cron#scheduling-remote-cron-jobs) every 30 minutes to clone repositories, install dependencies, and build fresh filesystem snapshots — so sandboxes always start from a near-current state
- [**Dicts**](https://frontend.modal.com/docs/guide/dicts) manage session locks and store image metadata, providing the shared coordination layer that makes multiplayer sessions possible
- [**Queues**](https://frontend.modal.com/docs/guide/queues) route prompts from any client — Slack, web, Chrome extension — into the right session, decoupling input from execution so multiple clients can feed into one session without conflicts

These are what allow Inspect to support multiplayer collaboration and scale to hundreds of concurrent sessions without any one session impacting another. Since Modal handles the distributed coordination, Ramp's team could focus entirely on the agent experience — the tools, the integrations, the UX — rather than the infrastructure underneath. That's how a prototype built in days scaled to hundreds of concurrent sessions without a rewrite.

### As fast as local: Filesystem snapshots for instant startup

To be adopted by Ramp’s fast-moving team, their coding agent needed to match or beat the experience of a local agent where the repo is already set up and services are already running.

They solved this with Modal’s [filesystem snapshots](https://modal.com/docs/guide/sandbox/snapshots). Every 30 minutes, a [Modal Cron](https://frontend.modal.com/docs/guide/cron#scheduling-remote-cron-jobs) clones each of Ramp's repositories, installs all dependencies, runs initial builds, and saves a snapshot of the Sandbox's filesystem. Because filesystem snapshots are stored as diffs from the base image, only the modified files are persisted—keeping them fast and lightweight.

When a builder starts a session, Inspect creates a new Sandbox from the latest snapshot. Since the snapshot is at most 30 minutes old, syncing with the head of the repo is nearly instant. End-to-end, sessions start working on a prompt in a few seconds.

### Zero setup, unlimited scale: Sandboxes for every builder

Because each session runs in its own Modal Sandbox, there's no contention between sessions and no load on anyone's laptop. A builder can kick off multiple versions of the same prompt, try different models, or let Inspect spawn child sessions to parallelize work across repositories—all running concurrently in the cloud.

This is where background agents pull ahead of local ones. Inspect gives every builder at Ramp what Rahul describes as "effectively hundreds of computers that they can work on simultaneously."

— Rahul Sengottuvelu,Head of Applied AI at Ramp

## Meeting builders where they work

Background agents also open up complete accessibility for users who don’t want to install things locally, and allowed the team to place it everywhere users are already working. Ramp built clients for Slack, a web interface with a hosted VS Code editor and streamed desktop view, and a Chrome extension that lets non-engineers visually select UI elements to change. All clients sync to the same session state, and every session supports multiplayer so colleagues can collaborate in real time.

There's no local setup required. A product manager or designer sends a prompt, Inspect spins up a full sandboxed environment with all dependencies installed, and they get the exact same developer setup an engineer would have, without thinking about it.

## The impact: Half of merged pull requests and climbing

Ramp didn't mandate Inspect, they let the product speak for itself. Within a couple of months, roughly half of all merged pull requests across Ramp's frontend and backend repos are started by Inspect, with over 80% of Inspect itself now being written by Inspect.

The impact extends well beyond engineering. Product managers are empowered to directly add features to their product. Designers operate with tight feedbacks between intent and implementation. The agent frees engineers to focus on high impact, high complex work where their expertise delivers the highest leverage — say, building systems like Inspect.

## What's next

— Zach Bruggeman,Engineer at Ramp

Ramp sees background agents only becoming more critical to engineering excellence as models improve. The current generation is already producing review-ready pull requests. As that rises, buoyed by hundreds of billions in capital expenditure on artificial intelligence, the bottleneck shifts from "can the agent write correct code" to "how many agents can you run in parallel". Modal Sandboxes provide the infrastructure teams need to break this bottleneck instead of being broken by it. [Try them today.](https://frontend.modal.com/docs/guide/sandboxes)
