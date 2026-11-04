---
title: "JVM Startup Time Story: From 330 Seconds to 3"
source: "https://medium.com/engineering-housing/we-stopped-our-jvm-from-ever-booting-cold-again-b5dbd492fe88"
author:
  - "[[PULKIT GARG]]"
published: 2026-11-03
created: 2026-11-04
description: "How a JVM service adopted CRaC in production, cutting pod readiness from about 330 seconds to 2-3, and the CPU-feature restore failure it hit along the way."
tags:
  - "clippings"
---

> [!summary]
> Housing.com's engineering team used CRaC (Coordinated Restore at Checkpoint, built on Linux CRIU) to restore pods from a frozen, already-warm JVM image, cutting pod readiness from about 330 seconds to 2-3 and full fleet deploys from about 20 minutes to 4. Steady-state pod CPU fell to about 20% of baseline, which made autoscaling and spot instances viable. A production restore failure traced to mixed CPU generations behind one node-group label was fixed by pinning the baseline CPU feature set used at checkpoint creation, and the team's lesson is to roll back first and find the root cause afterward.

*Coordinated Restore at Checkpoint: the OpenJDK feature most Java engineers have heard of and almost none have shipped to production. Here’s the problem it solves, the real numbers, and the incident it took to earn them.*

![](https://miro.medium.com/v2/resize:fit:1400/1*ZcxHV_gD_v0l1Kp2WVK7GA.png)

## What “warmup” actually means, for anyone who hasn’t lived in a JVM

Skip this if you already know — but it’s worth 20 seconds for anyone who doesn’t, because the rest of this post leans on it.

When a Java process starts, it runs your code through a simple bytecode interpreter first — correct, but slow. In the background, the JIT (Just-In-Time) compiler watches which pieces of code actually run a lot, and progressively recompiles those into fast native machine code, in increasingly aggressive tiers, the longer and more consistently they keep running. “Warmup” is that process: the JVM earning back the speed a natively-compiled program would have had from millisecond one. A freshly-started JVM is correct but slow. A warm one is correct and fast. The catch is that earning that speed costs real wall-clock time and real CPU — and a service that restarts often (deploys, autoscaling, pod churn, an attack killing pods) pays that cost over and over again, from zero, every single time it comes back up.

![](https://miro.medium.com/v2/resize:fit:1400/1*uKLbZenkkinFda65kvM3Pg.png)

## The tax nobody questioned

Every JVM shop pays the same tax and has stopped noticing it’s a tax: boot the app, then spend minutes re-teaching the JIT everything it already knew an hour ago — on every pod, every deploy, forever.

In our case: a pod took ~75 seconds to boot, then ran roughly 245 seconds of warmup before it could be trusted with real traffic — call it ~330 seconds, start to finish. Pods roll out a few at a time, so a full fleet deploy meant several batches back to back, about 20 minutes. A plain restart was exactly as slow as a deploy.

Nobody treated this as an incident, because it never paged anyone. But it was quietly expensive in ways that compound:

CPU had to be over-provisioned on every pod, permanently — warmup itself is CPU-heavy and spikes right where production traffic also lands, so you carry that headroom 24 hours a day to cover a cost you only pay once per pod’s life.

MTTR got worse exactly when it mattered most. Under an attack or a traffic spike, pods get killed and replaced — and replacements paid the full ~330-second tax again, at the worst possible moment.

![](https://miro.medium.com/v2/resize:fit:1400/1*qiQSI_BvdGGFgotyc8uxjA.png)

Autoscaling was theater. If a new pod takes over five minutes to become useful, scaling out in response to load doesn’t actually help. So the fleet ran fixed-size and fully provisioned, even at 3 AM.

![](https://miro.medium.com/v2/resize:fit:1400/1*v_7QzW2zXHcOoXO3QdLdaw.png)

## The two tempting half-measures

GraalVM native images promise near-instant startup — at the cost of a genuinely large rewrite and giving up the JIT’s peak throughput once you’re warm. AppCDS (class-data sharing) is the safer, smaller swing — it speeds up class loading, but does nothing for JIT tiering, inline caches, and GC heuristics settling in, which is where the real cost lives.

## The idea: stop booting, start cloning

The feature we used instead is CRaC — Coordinated Restore at Checkpoint, an OpenJDK project built on Linux’s CRIU (Checkpoint/Restore In Userspace — an OS-level feature for freezing a running process to disk and reviving it later, exactly as it was). Warm up one JVM, however long that takes, then freeze its entire process state to disk. Every other pod doesn’t boot and warm up at all — it restores from that frozen, already-hot image in seconds.

It’s not “make boot faster.” It’s “stop booting.” Every new pod is born warm, because it’s a clone of a JVM that was already running.

One runner does the expensive work once. Every pod after that restores from that frozen image in about 2–3 seconds — the ~330-second cold start simply doesn’t happen anymore.

![](https://miro.medium.com/v2/resize:fit:1400/1*PTnoOGFTBkKhAnuYjuL-Cg.png)

## The wins

New pod ready, per pod: ~330s before, ~2–3s after.

Full fleet deploy: ~20 min before, ~4 min after.

Steady-state pod CPU: baseline before, ~20% of baseline after.

Autoscaling: not viable before, enabled after.The per-pod number is the real win — a reclaimed pod that used to cost ~330 seconds to replace now costs single digits, which is also what makes spot instances far less scary.

## What this is actually worth

None of these numbers exist in isolation — they compound into an actual cost story, not just a latency one.

Smaller permanent footprint. Every pod used to carry enough CPU headroom to survive its own warmup spike, 24/7, whether or not it was ever under real load. Cutting steady-state CPU to ~20% of baseline shrinks the fleet’s permanent reserved capacity by roughly the same amount — capacity you were paying for around the clock to cover a cost you only actually incurred once per pod’s lifetime.

Real autoscaling, not a fixed fleet pretending to scale. A fleet that can’t safely add capacity in under a few minutes can’t be trusted to remove it either, so it runs provisioned for peak, all day, every day. Once a new pod is useful in ~2–3 seconds, scaling down during actual off-peak hours stops being risky and starts being free money.

Spot instances go from reckless to routine. Spot capacity is cheap precisely because it can be reclaimed on short notice — and most latency-sensitive services avoid it because losing a pod used to cost ~330 seconds to replace. At 2–3 seconds, a reclamation is a non-event, which opens up a meaningfully cheaper tier of compute that wasn’t safely usable before.

None of this shows up as a single line item — it stacks. The deploy-time number is what people notice first. The cost reduction is what actually pays for the engineering time spent getting here.

None of that came for free. Here’s what it actually took to get there.

## The Crash That Needed a Fast Rollback

A pod failed to come back up with this in the logs:

warp: error: Image constraint ‘cpu.features’ (bitmap subset) does not match:

```
warp: error: Required : f7 fb fd 05 18 4e e1 00 e6 0f 00 00 00 00 00 00
warp: error: Image has : f7 fb fd 9d 1b 4e e1 00 e6 0f 00 00 00 00 00 00
[crac] CRaC engine failed to restore from /var/checkpoint: error -1
[crac] Restore failed due to incompatible or missing CPU features.
Error: Could not create the Java Virtual Machine.
```

Not a crash mid-request. The JVM refused to even come up. Multiple pods, same error, same day.

### The rollback that actually worked

The right move in the moment wasn’t clever — it was fast: roll back to the last known-good image, one that had never gone anywhere near CRaC. Pods came back up on the old, boring path, traffic recovered, and the incident was contained with minimal downtime. A fast rollback to a known-good build is exactly what good incident response is supposed to look like, and it’s worth saying plainly when it works, not just when it doesn’t.

But a successful rollback isn’t the same as understanding what broke. CRaC wasn’t going back anywhere near production until the team actually knew why those pods had failed to restore in the first place.

### Why the hardware disagreed with itself

The actual mechanism: at checkpoint time, the JVM’s JIT queries the CPU for which instruction-set extensions are available and compiles machine code that uses them — for performance, this matters. A restore onto a host missing even one of those instructions would hit an illegal instruction mid-request. CRaC checks the CPU’s feature bitmap before restoring specifically to fail fast instead of crashing mid-traffic — the crash above was the safety check working correctly, not a malfunction.

The real question was why a single, supposedly-uniform node group had mixed hardware at all. Two things compounded:

An instance type isn’t one fixed microarchitecture. A given AWS instance type can span multiple hardware generations under the hood. Two nodes with the identical type label can disagree on CPU features.

The node group was dynamically provisioned, not statically pinned — an autoscaler free to pick whichever instance type and generation is available at scale-out time. One label on the node group didn’t mean one hardware profile running underneath it.

The fix was to stop assuming homogeneity and pin it explicitly: the startup script now reads an environment variable that fixes the baseline CPU feature set used at checkpoint creation, trading a sliver of possible peak performance for a checkpoint that restores correctly across the fleet’s actual hardware mix, not its labeled one.

## The lessons (the part you can steal)

A fast rollback to a known-good image is still your best incident response tool.

Don’t let root-causing block recovery. Get back to something that works first, protect uptime, and investigate from a position of safety — the two are different jobs and the first one doesn’t need to wait for the second.

**A node-group label is not a hardware guarantee under a dynamic autoscaler.**

If pods can land on different hardware generations under one label, pin what actually matters explicitly rather than assuming uniformity you never configured.

## The one-sentence version

We stopped booting the JVM and started cloning one that was already warm — 330 seconds became 2–3 — and it took a crash, a fast rollback that actually saved us, and a real root cause found afterward to get there safely.

Thanks for reading. If your deploys take 20 minutes because your JVM re-introduces itself from scratch every single time, this might be the fastest infrastructure win you ship this quarter — just make sure you understand the failure before you go anywhere near it again.
