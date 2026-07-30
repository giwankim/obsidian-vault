---
title: "How PostgreSQL Works, in 3D"
source: "https://nikolays.github.io/PGSimCity/"
author:
published:
created: 2026-07-28
description: "An independent, non-commercial educational visualization of PostgreSQL internals. Not affiliated with Electronic Arts."
tags:
  - "clippings"
---

> [!summary]
> PGSimCity is an independent, non-commercial 3D visualization of PostgreSQL internals, structured as a 14-step walkthrough of the engine as a working model.
> Step one covers connection handling: the postmaster has been listening since boot, verifies the user and database, then forks an entire new process per client rather than pulling from a thread pool.
> The author labels it an early, unreviewed prototype likely to contain inaccuracies, and invites issues and pull requests on GitHub.

1of 14

## A client connects

Everything starts with a TCP connection. The postmaster has been listening since the server booted: it checks who you are, checks the database exists, and then does something no thread pool would ever do — it forks an entire new process to serve you, and steps out of the way. Watch the pulse leave the tower and land in the row of buildings ahead.

Your pace

## PGSimCity

PGSimCity is an independent, non-commercial educational visualization of PostgreSQL internals. It is not affiliated with, sponsored, endorsed, or approved by Electronic Arts Inc. SimCity is a trademark of Electronic Arts Inc.

A working model of the PostgreSQL engine

ready

**Early, unreviewed prototype.** It almost certainly contains inaccuracies in both the model and explanations. Found one? [Open an issue](https://github.com/NikolayS/PGSimCity/issues/new?ref=pgsimcity-boot) or send a [pull request](https://github.com/NikolayS/PGSimCity/pulls?ref=pgsimcity-boot).
