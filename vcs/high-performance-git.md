---
title: "High Performance Git"
source: "https://gitperf.com/index.html"
author:
published:
created: 2026-04-30
description: "High Performance Git by Ted Nyman, a book about Git internals and large Git repositories."
tags:
  - "clippings"
---

> [!summary]
> Landing page for *High Performance Git* by Ted Nyman — a book reframing Git as not just a VCS but also a content-addressed database, filesystem cache, graph walker, and transfer protocol, and exploring the performance cost of each layer. Topics span objects, refs, the index, history traversal, packfiles, maintenance, sparse working trees, partial clone, transport, scale, diagnosis, configuration, and recovery. Aimed at build/CI engineers, monorepo owners, and DX teams who keep Git fast as repos and teams grow.

![Pencil sketch of a sailboat moored near a dock with shoreline buildings in the distance.](https://gitperf.com/index-art.png)

Pencil sketch of a sailboat moored near a dock with shoreline buildings in the distance.

Git looks like a version-control tool. It is also a content-addressed database, a filesystem cache, a graph walker, and a transfer protocol.

This book is about those layers and the performance costs of each one. It starts with objects, refs, the index, and history traversal, then moves outward into packfiles, maintenance, sparse working trees, partial clone, transport, repository scale, diagnosis, configuration, and recovery.

It is written for engineers who need Git to stay fast as repositories, histories, and teams get larger: build and CI engineers, monorepo owners, developer-experience teams, and the people who wind up debugging strange Git behavior when the easy explanations stop working.
