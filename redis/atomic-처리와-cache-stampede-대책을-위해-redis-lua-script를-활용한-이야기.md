---
title: "Atomic 처리와 cache stampede 대책을 위해 Redis Lua script를 활용한 이야기"
source: "https://engineering.linecorp.com/ko/blog/atomic-cache-stampede-redis-lua-script"
author:
  - "[[Kagaya Hokuto]]"
published:
created: 2026-10-26
description:
tags:
  - "clippings"
---

> [!summary]
> LINE GAME Platform explains why it reaches for Redis Lua scripts in Redis Cluster for two problems. First, friend lists cached from HBase were occasionally duplicated because at-least-once Kafka delivery let two workers interleave `DEL` and `RPUSH`, and `MULTI`/`EXEC` cannot be routed in Cluster, so a single script doing `DEL`, `RPUSH` and `EXPIRE` restores atomicity (keys go through `KEYS` with hash tags so they share a slot). Second, Probabilistic Early Recomputation (XFetch) against cache stampede: a GET script returns value, stored compute time and TTL in one call, and a request recomputes early when `time - delta * beta * log(random)` reaches the remaining TTL, which cut response time during cache exhaustion roughly threefold; `EVALSHA` was skipped since short scripts gain little and `SCRIPT LOAD` would have to run on every node.
> Note: the clipping captured only the title line; this summary was written from the source page.

Preventing Cache Stampede with Redis and XFetch
