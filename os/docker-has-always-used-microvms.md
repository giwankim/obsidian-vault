---
title: "Docker has always used microVMs"
source: "https://dave.recoil.org/docker-has-always-used-microvms/"
author:
  - "[[Dave Scott]]"
published: 2003-10-01
created: 2026-11-11
description: "Docker Desktop has always run containers inside a minimal, purpose-built VM. Here is why, and what it bought us."
tags:
  - "clippings"
---

> [!summary]
> Dave Scott argues that Docker Desktop has run containers inside microVMs since 2016, combining the unikernel work of the acquired Unikernel Systems (MirageOS) with Linux containers. A minimal embedded "library VMM" (hyperkit, vpnkit, now Docker VMM) and a LinuxKit-based kernel enabled rootless operation, a small auditable host/VM interface, and VPN-friendly networking. The same tech now underpins Docker Sandboxes, which isolate coding agents in separate microVMs.

## Docker has always used microVMs (well, since 2016)

There's a lot of buzz about "microVMs", where a workload runs with a stripped down Linux kernel, on a minimalist VMM such as [firecracker](https://github.com/firecracker-microvm/firecracker) on top of a hypervisor like KVM or Xen. MicroVMs are often contrasted to, and considered more secure than, traditional Linux Docker containers. What if I told you that Docker Desktop has always used microVMs? (since 2016)

## Unikernels are microVMs

Unikernels can be considered an early form of microVM. Rather than booting a full Linux kernel on a full VMM, a unikernel links an app with only the drivers, filesystems and subsystems it actually needs; other code is omitted. For example a [MirageOS](https://mirageos.org/) unikernel app would have no processes, probably no filesystem, only one vCPU. Certainly no ssh or shell (unless you really want those). The VMM that hosts the Mirage unikernel was also minimal (see [Solo5](https://github.com/Solo5/solo5) and [mirage-solo5](https://github.com/mirage/mirage-solo5) ). No legacy required. We were so confident in the security of the system that we ran a [bitcoin pinata](https://mirage.io/blog/bitcoin-pinata-results) offering 10BTC to any hacker able to claim it. The BTC went unclaimed.

Boot can be really fast too: the "Just-In-Time Summoning of Unikernels" project ([paper](http://unikernel.org/files/2015-nsdi-jitsu.pdf), [code](https://github.com/mirage/jitsu)) optimized x86 VM creation time down to about 20ms (120ms on an underpowered 2015 ARM dev board)

The main (obvious) downside of unikernels is having to link your app with a bunch of kernel code. A lot of people would like to run existing Linux programs!

While we were developing Unikernels, Docker was busy inventing the modern form of Linux containers and revolutionising how software is built, shared and run. [Docker acquired Unikernel Systems in 2016](https://techcrunch.com/2016/01/21/docker-acquires-unikernel-systems-as-it-looks-beyond-containers/) and we combined the best of Unikernels (microVMs) and Linux containers into Docker for Mac (later Docker Desktop).

## A library VMM for Desktop applications

Our priority back then wasn't to add microVMs to Docker for their own sake. Instead our goal was to make Docker feel like a native app on Mac and Windows, rather than a bundle of components. Using our [Mirage Unikernel libraries](https://mirage.io/) we started building a "library VMM": a VMM which could be embedded inside the Docker application, and which would be single purpose, minimal, secure and fast. The first version was called [hyperkit](https://github.com/moby/hyperkit) (a fork of [xhyve](https://github.com/machyve/xhyve), itself derived from [bhyve](https://en.wikipedia.org/wiki/Bhyve) ). We linked the C code directly with the [MirageOS block layer](https://github.com/mirage/mirage-block-unix) and used the [Mirage userspace TCP/IP stack](https://github.com/mirage/mirage-tcpip) in a gvisor-like network stack [vpnkit](https://github.com/moby/vpnkit). The VMM code continues to evolve and is now called [Docker VMM](https://www.docker.com/blog/docker-vmm-public-beta/).<sup><a href="#fn1">1</a></sup>

The VM kernel and root filesystem were minimal too, based on the [LinuxKit](https://github.com/linuxkit/linuxkit) project. The current version is an even more slimmed down and efficient variant but conceptually the same, similar to [containerd/nerdbox](https://github.com/containerd/nerdbox).

## Docker for Mac in 2015-2016

Docker for Mac began in 2015 as **Project Piñata**, a skunkworks project to make Docker useful to more developers. In this 2018 tweet, Solomon Hykes recalls Docker's first use of unikernel technology and the collaboration between Paris, Cambridge and San Francisco:

![](https://x.com/i/status/961321299413893122)

For Docker for Mac (later renamed Docker Desktop) this allowed:

- **Running rootless on all platforms.** Without requiring "rootless inside Linux": the whole Linux kernel is untrusted, so even a [Linux CVE](https://lwn.net/Articles/1097401/) doesn't matter.
- **Minimal devices.** We could carefully limit the host / VM interface, making it easy to understand and audit.
- **VPNs and network policy.** It was easy to interoperate with VPNs, and to extend later to impose networking policy such as [Registry Access Management](https://www.docker.com/blog/introducing-registry-access-management-for-docker-business/).

Here's the OG 2015 Docker for Mac beta installation experience:

<iframe title="The OG Docker for Mac beta installation experience (2015)" width="560" height="315" src="https://crank.recoil.org/videos/embed/3re5G972kkqjzzujxHQ3E6" allow="fullscreen" sandbox="allow-same-origin allow-scripts allow-popups allow-forms"></iframe>

## And now in 2026

The Docker microVM tech is the foundation of both Docker Desktop and also *Docker Sandboxes* ([why microVMs](https://www.docker.com/blog/why-microvms-the-architecture-behind-docker-sandboxes/)), where each sandbox runs in a separate microVM, completely isolated from each other and the host. Docker Sandboxes enables you to do things like [run your favourite coding agent and harness securely](https://www.docker.com/blog/docker-sandboxes-run-claude-code-and-other-coding-agents-unsupervised-but-safely/), with strict isolation and governance.

To see what Docker microVM's can do, install [Docker Sandboxes (sbx)](https://docs.docker.com/ai/sandboxes/install/) and try \`sbx run claude\`.

## Further reading

To read more about the history of the tech, check out the article [A Decade of Docker Containers](https://cacm.acm.org/research/a-decade-of-docker-containers/) (Communications of the ACM).

Join the discussion on [LinkedIn](https://lnkd.in/p/eqES2ztb).

## Footnote

<sup>1</sup> Although we were aiming to make everything a library and link into a static unikernel-like process, for technical reasons it makes sense to still have a single host process per VM.

## ChangeLog

- 2026-10-03: original version
- 2026-10-04: added more history and cool install video
- 2026-10-05: added an inline timeline, with earlier systems context, the Bitcoin Piñata security challenge, Solo5 + ukvm integration and Docker for Mac release milestones
- 2026-10-09: added Simon Crosby's 2012 description of Bromium's micro-VMs, Intel Clear Containers and Kata Containers to the timeline
- 2026-10-09: added Project Piñata's 2015 origins and Solomon Hykes's tweet about the first use of unikernel technology at Docker
