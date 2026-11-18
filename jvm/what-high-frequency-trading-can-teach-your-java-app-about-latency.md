---
title: "What High-Frequency Trading Can Teach Your Java App About Latency"
source: "https://www.azul.com/blog/what-high-frequency-trading-can-teach-your-java-app-about-latency/?utm_source=substack&utm_medium=email"
author:
  - "[[Miles Dawborne]]"
published: 2026-11-11
created: 2026-11-16
description: "Ten habits trading firms use to keep Java fast, translated for microservices, Kubernetes, and autoscaling, with a five-minute check for each one."
tags:
  - "clippings"
---

> [!summary]
> An Azul engineer translates ten latency habits from high-frequency trading firms into practices for Java microservices on Kubernetes and the cloud, each with a five-minute check. Key lessons include measuring P99.9 and max from full histograms, avoiding coordinated omission, using jHiccup to separate JVM stalls from platform stalls, guarding against CPU throttling and cold JIT warm-up, and minding topology and instance choice. The punchline is that tail latency is a whole-stack property, illustrated by 30-second outliers traced to Linux dirty-page writeback.

![](https://azul.imgix.net/wp-content/uploads/01Picture1.png?auto=format&crop=faces,entropy&fit=max&q=80&w=739&s=5134f06994718a2ef8b4fa6313e0cdb6)

**Figure 1. Where the microseconds live: from the rack, through the market feed, to Java code.**

I’ve spent a decade helping banks, exchanges, and trading firms make Java fast enough to trade with, often down to a few tens of microseconds wire-to-wire. What that taught me: high-frequency trading isn’t a different discipline from yours. It’s the same one with the stakes cranked up. Trading firms fight the same enemies you do (GC pauses, cold JIT compilers, allocation churn, an unexplained latency tail); they just can’t afford to ignore them. And your app arguably lives somewhere more hostile than a tuned trading rack: shared hardware, noisy neighbors, throttled containers, and autoscalers handing traffic to cold JVMs.

If you don’t trade, the tail still costs you. Teams that can’t see or trust their P99 buy headroom instead: extra instances, CPU targets of 30–55%, pods kept warm “just in case.” Each lesson below helps you buy that headroom back with evidence.

## Lesson 1: Measure the tail your users actually feel

#### ON THE TRADING FLOOR

An options market maker I worked with had a beautiful 2μs median inside its pricing engine, and a 99th percentile that blew out fifty-fold whenever the garbage collector woke up.

#### IN YOUR APP

Your users don’t experience your mean either; they experience their *worst* request. Averages smooth over spikes, and a single percentile can hide them. Only the raw data shows them. A half-second stall can sit inside a healthy-looking P99 (Figure 2), and whether the P99 sees it at all depends on the window you measure over (Figure 3).

![](https://azul.imgix.net/wp-content/uploads/02Picture2.png?auto=format&crop=faces,entropy&fit=max&q=80&w=739&s=1c2f61dceae5cae9a4731fc060996d16)

**Figure 2. One minute at 1,000 transactions per second. A 500ms stall delays 500 transactions, too few to move the P99.**

![](https://azul.imgix.net/wp-content/uploads/03-Picture3.png?auto=format&crop=faces,entropy&fit=max&q=80&w=739&s=a11d9ba1e0ae984bd2c9d2b635871607)

**Figure 3. The same stall measured over windows from one second to one hour. The max is 500ms in every one. The P99 sees the stall only while it fills more than 1% of the window, and averaging per-second P99s gives numbers that aren’t the P99 of anything.**

**Chart P99.9 and max beside P99, from full histograms, not rollups.** HdrHistogram’s interval logs are built for this. And check whether your APM tool averages per-interval P99s when you zoom out; that’s the dashed line in Figure 3. Until you can see the tail, you can’t tell which of your spare instances actually protect it.

**Check it in five minutes:** add P99.9 and max to the latency panel of your most important service, and look at one busy hour at 1-minute resolution.

## Lesson 2: You can’t fix what you can’t see

#### ON THE TRADING FLOOR

The measurement rig is built *before* anything is tuned, and it’s checked from outside the process, because in-app timestamps come from the system you’re observing. At one bank, the equities desk measures latency on the switch itself, with packet capture and hardware timestamps.

#### IN YOUR APP

You don’t need a network tap: your load balancer or real-user monitoring does the same job by timing requests from outside the process. Then avoid two traps:

- **Coordinated omission.** A load generator that waits out a stall before its next request quietly erases your worst samples. Send at a fixed rate.
- **Unfair tests.** Start every bake-off with an A/A run, comparing two identical setups, to see how much the numbers move on their own. Then replay production traffic and check the boring settings. One social network’s JVM bake-off looked lopsided until someone noticed the two sides ran different logging levels. The same rigor tells you when a smaller fleet or a higher CPU target is safe.

To see whether the platform itself is stalling, run jHiccup in one service as a -javaagent. It runs a thread that does nothing but sleep and record how late it wakes up. Because that thread runs none of your code, any delay it sees comes from the JVM or its environment: GC and other safepoint pauses, the OS, the hypervisor, or a noisy neighbor (Figure 4). To see only the environmental pauses, add -c: jHiccup then also starts an idle control JVM that your app and its GC can’t touch.

Its silence is evidence too. An FX broker saw 360ms stalls that jHiccup never recorded, so the culprit had to be inside the process: a `Runtime.availableProcessors()` call the app made every 15 seconds.

![](https://azul.imgix.net/wp-content/uploads/04-Picture4.png?auto=format&crop=faces,entropy&fit=max&q=80&w=739&s=d17032b59fbdbda0c40bac9ca6d8d35f)

**Figure 4. jHiccup output: regular GC stalls and one 180ms outlier an average would never show.**

Sometimes the answer only shows up when you lay the latency timeline against the operating system’s own charts. One exchange chased outliers of up to 100ms that arrived like clockwork every 30 seconds, while the JIT and GC logs stayed silent. (The culprit comes at the end.)

**Check it in five minutes:** run jHiccup as a -javaagent in one service for a day and overlay its max on your P99.9. If both spike together, look at the platform, and add -c to tell GC from the environment; if only the app spikes, look inside.

## Lesson 3: Make sure your JVM gets the CPU you’re paying for

#### ON THE TRADING FLOOR

Trading systems isolate cores, so the scheduler and “that one rogue monitoring agent” run elsewhere. At one trading firm, the rogue agent was real: monitoring tools that scanned the JVM’s memory maps caused multi-second latency spikes, and removing those tools was a big part of getting to a clean trading day.

#### IN YOUR APP

Core isolation is overkill for most services, but two lessons carry over.

**Know what shares your box:** log shippers, APM sidecars, and security scanners steal CPU everywhere. At one bank, CPU run queues rose visibly after a security agent rolled out across its estate.

**Watch your Kubernetes CPU limits.** The modern footgun is a limit set too tight. The JVM sizes its GC and JIT threads from the limit, but your thread pools usually don’t: request handlers, async executors and event loops can all run at once. When they burn through the quota, the limit throttles your whole JVM, GC and JIT threads included, and produces stalls no profiler explains (Figure 5). A fintech’s API gateway sat pinned at its 2-CPU limit with 99–100% of scheduling periods throttled. Teams usually answer that with more replicas, but fixing the limit is cheaper: for a latency-critical service, give it whole CPUs with request equal to limit; with the kubelet’s static CPU manager policy, those become exclusive cores, Kubernetes’ version of core isolation. Otherwise, size the limit for bursts (GC, JIT and your pools at once), not for average load, and size thread pools to match. If you drop the limit entirely, set -XX:ActiveProcessorCount, because without a limit the JVM sizes itself for the whole node.

**Why a CPU limit freezes everything**
Linux enforces Kubernetes CPU limits in 100ms periods. A 2-CPU limit buys 200ms of CPU time per period. If eight threads, mostly from your own pools, run on eight cores at once, they spend that in about 25ms, and every thread in the container, the garbage collector included, sits frozen for the remaining ~75ms.

![](https://azul.imgix.net/wp-content/uploads/05Picture5.png?auto=format&crop=faces,entropy&fit=max&q=80&w=739&s=c01fa31363cf34f62e62892ff0b62ed1)

**Figure 5. A 2-CPU limit with eight busy threads: 25ms of work, then 75ms frozen, in every 100ms period.**

**Check it in five minutes:** compare `container_cpu_cfs_throttled_periods_total` with `container_cpu_cfs_periods_total` for your latency-sensitive pods. It’s a five-minute look that has ended multi-week investigations.

## Lesson 4: Cold JVMs are slow exactly when you’re busiest

#### ON THE TRADING FLOOR

One exchange asked me: “Why are the first transactions seeing 1ms latency, compared to 0.013ms later on?” That’s a 77x penalty on trade one, at the market open. Every method starts in the interpreter and reaches optimized C2 code only after thousands of profiled invocations, so the first trades run on the slowest code the JVM has. A trading system typically restarts once a day and warms up before the bell (with the right technology).

#### IN YOUR APP

Every deploy, scale-up, and reschedule starts a fresh JVM, and a fresh JVM is slowest for its first several thousand requests. So the pod your autoscaler adds during a spike is the slowest one you have, at the moment you need it most. Bursty traffic makes it worse: a flash sale, or an AI agent fanning one request into dozens of service calls, lands on freshly scaled, still-cold pods. If P99 gets worse as you add capacity, this is usually why. It’s also why teams keep spare pods warm “just in case.” Fix warm-up and you can run leaner.

Your main options, from least to most effort:

| **Option** | **What it does** | **Effort** | **Trade-offs** |
| --- | --- | --- | --- |
| **Warm-up requests** | Sends representative traffic before the readiness probe passes | Low | Warms only the code it touches; lengthens startup |
| **OpenJDK AOT cache (Project Leyden, JDK 24+)** | A training run stores loaded classes and, from JDK 25, early method profiles | Low | Mainly helps startup and early warm-up; regenerate it when the classpath or JDK changes |
| **Azul Prime ReadyNow (see Lesson 10)** | Reuses the JIT profile and compiler decisions recorded on earlier runs | Low | Requires Azul Prime; record the profile under representative traffic |
| **CRaC (in builds such as Azul Zulu)** | Restores a snapshot of an already-warm JVM in milliseconds | Medium | App must close and reopen connections around the checkpoint; the snapshot holds secrets |
| **GraalVM Native Image** | Compiles ahead of time, so the app starts almost instantly | High | Reflection and dynamic loading need configuration; often lower peak throughput than a warmed JIT |

**Check it in five minutes:** plot P99 by pod age (minutes since start) for one service. If the first few minutes stand out, you pay a warm-up tax on every scale event.

## Lessons 5-9: Quick hits

### 5\. Distance costs you

Light in fiber travels about 5ns per meter, so traders rent rack space inside the exchange. You can’t buy a cross-connect in the cloud, but the principle holds: forty service hops, microservices chatting across availability zones, a database left in another region since 2021. Then there’s the wire tax: `TCP_NODELAY` left unset is the classic mysterious ~40ms, and unpooled connections and un-resumed TLS sessions add round-trips to every hop.

*No JVM tuning wins back what a lazy topology gives away. Cross-zone chatter bills you twice: once in your P99, once on the invoice.*

### 6\. Choose instances that won’t stall under load

Trading racks disable BIOS power-saving because a napping core takes microseconds to wake. Your equivalent is a burstable instance whose CPU credits run out mid-spike; use fixed-performance families for latency-sensitive work. On most x86 instances a vCPU is a hyperthread, not a core, yet the JVM sizes its GC and JIT threads as if each were a core.

Managed platforms don’t remove the problem; they hide it. One Spring service on AWS Fargate saw several-hundred-millisecond spikes while its GC pause P99 read a healthy 3.3ms: the host was starving the container. Watch for the stall where your platform shows it. On EC2, check CPU steal and, on burstable types, CPUCreditBalance. On VMware, check CPU Ready (%RDY). On Fargate, where you can’t see the host, compare task CPU against its reservation, check cgroup throttling, and let jHiccup’s max show you the stalls. Fixing the stall costs less than padding the fleet to hide it.

### 7\. Keep your fleet on current CPU generations

Trading engineers tune for the CPU itself. They pad hot data structures so two threads don’t fight over the same 64-byte cache line (false sharing), and they buy new CPU generations early for their wider vector instructions.

You won’t pad cache lines, but you do choose instance generations, and fleets accumulate old ones. That costs you twice. Newer generations are typically cheaper per unit of work, and old silicon can lack instructions the JVM would otherwise use. One SaaS company’s SHA-heavy hot path ran four times faster on Ice Lake than on 2017-era Skylake, which lacks the SHA instructions.

### 8\. Stop making garbage

The cheapest GC pause is the one you never cause. The options market maker from Lesson 1 got allocation under 10MB a second, and its collector ran 0.3% of the time. You don’t need their heroics. Cutting the churn nobody profiled gets you most of the way, because **allocation rate drives GC frequency, GC frequency drives your tail, and both drive your cloud bill.** The classic, at 5,000 requests per second:

`log.debug("processed order " + order.getId() + " in " + elapsedMs + "ms"); `

builds its string on every request even with debug off. The parameterized form allocates almost nothing when debug is off (at most boxing the numbers):

`log.debug("processed order {} in {}ms", order.getId(), elapsedMs); `

A hundred bytes a call is nearly two gigabytes of garbage an hour, from one line, and a busy service has hundreds of lines like it. Profile allocation with JFR or async-profiler before changing anything; the culprits are rarely where you’d guess.

### 9\. Don’t let GC set your heap size and CPU targets

Trading shops work around the garbage collector. Some keep data off-heap, in memory the collector never scans, often through `sun.misc.Unsafe` (whose memory-access methods are now [deprecated for removal](https://openjdk.org/jeps/471) in favor of the Foreign Function & Memory API, final in JDK 22), so the GC can never pause it. Others size the young generation so GC never runs through the trading session, then restart after market close.

The lesson isn’t to copy them. Every heroic workaround marks a spot where the platform hurts, and because your app has no closing bell, it has no quiet window to restart in.

Your workarounds are milder but come from the same fear: heaps capped because “big heaps pause,” fleets of small JVMs, and servers kept lightly loaded. For example, one adTech server running a couple of hundred instances scaled out at 55% CPU because the “SLA is broken constantly when GC takes place.” Small pods may still make sense, but the collector shouldn’t be what decides that.

## Lesson 10: Your JVM is a choice, not a constant

Everything so far works on any JVM. Most teams pick theirs once and never revisit it; trading firms rerun the bake-off on their own traffic whenever the stakes change. Many of the firms I work with chose Azul Prime for their most latency-sensitive systems. The JVM touches three things this post has already covered: warm-up, the machine code itself, and garbage collection.

**Warm-up.** ReadyNow persists the JIT’s profile and decisions across restarts, so hot code compiles early (Figure 6) and fewer deoptimizations hit P99 when traffic shifts. Optimizer Hub adds fleet-wide profile serving and offloaded compilation; Azul [reports](https://www.azul.com/newsroom/azuls-high-performance-java-platform-achieves-historic-first-with-10000-customer-jvms-collaborating-and-sharing-performance-optimizations-cutting-cloud-costs-by-20/) one enterprise running more than 10,000 JVMs this way and cutting cloud costs by more than 20%.

![](https://azul.imgix.net/wp-content/uploads/06Picture6.png?auto=format&crop=faces,entropy&fit=max&q=80&w=739&s=ee645659437c219036b6166b8f1aa136)

**Figure 6. Illustrative warm-up: Prime starting from a ReadyNow profile reaches steady state thousands of transactions sooner.**

**Machine code.** Prime’s Falcon JIT is built on LLVM, which keeps pace with new x86 and Arm instruction sets, and it auto-vectorizes more loop shapes than C2’s SuperWord pass (using AVX2 and AVX-512 on x86, for example). In Azul’s published [Kafka benchmark,](https://github.com/AzulSystems/kafka-benchmark) Prime, with Falcon and C4 working together, carried 30% more traffic while keeping P99 under 200ms and reached 45% higher maximum throughput (Figure 7). The baseline was a 2023 setup on vanilla OpenJDK; Azul’s write-up doesn’t name its version or collector.

![](https://azul.imgix.net/wp-content/uploads/07Picture7.png?auto=format&crop=faces,entropy&fit=max&q=80&w=739&s=f08ed2faf72003ba3aa2054021613192)

**Figure 7. Azul’s published Apache Kafka benchmark: three brokers on i3en.2xlarge, the same hardware for both JVMs. Usable capacity is the highest load that kept P99 under 200ms.**

**Garbage collection.** G1, the default collector, pauses the application for its young and mixed collections and [aims for a 200ms pause target by default](https://www.oracle.com/java/technologies/g1gc.html), which is fine for many services. Generational ZGC (JDK 21+) and Shenandoah (generational since JDK 25) do **nearly** all their work concurrently, with typical pauses under a millisecond. Their weak spot is the traffic spike: when allocation outruns the collector, ZGC stalls the allocating threads and Shenandoah falls back to pacing or a stop-the-world cycle. Azul Prime’s C4 collector also compacts concurrently and is built to keep up through those bursts on large heaps. In Azul’s MEMX case study, the US stock exchange reports P99.9 response times 80 times better on its key application with Prime.

**When stock OpenJDK is enough**

Azul Prime earns its keep on long-running, latency-sensitive services with room to breathe. It’s the wrong tool when:

- **Instances are tiny.** On one or two vCPUs, the JIT and concurrent collector compete with your app for headroom, unless you offload compilation: Optimizer Hub’s Cloud Native Compiler exists for this case, so test with it.
- **Processes start and stop quickly.** Batch jobs, CI runs, CLI tools, and short-lived functions exit before an optimizing JIT pays back its startup cost.
- **The time isn’t in the JVM.** No JVM fixes the network, the database, or an architecture.

Otherwise, test it the way traders do: an A/A run, then an A/B canary on production traffic, judged on P99.9, max, and instance count.

## The punchline

Latency is a whole-stack property. The tail has many owners: the CPU your JVM actually gets, your warm-up, your topology, your instances and CPU generations, your allocation rate, your heap and CPU targets, and your JVM. Fix one of these, and the next-loudest problem takes its place.

Remember the exchange in Lesson 2 whose outliers arrived like clockwork every 30 seconds? The culprit was Linux writing back pages that had been dirty for more than 30 seconds (`vm.dirty_expire_centisecs`, which defaults to 3000). Not the JVM, not the app: the stack.

What separates a trading desk from your app isn’t physics or talent; it’s stakes and budget. Start at the tail, work down the stack, and remember that your users, like the markets, only remember your worst moment.

## Ten checks for this week

| **Lesson** | **Symptom** | **Metric or tool** | **Five-minute check** |
| --- | --- | --- | --- |
| 1 | Dashboards look fine, users complain | P99.9 and max from full histograms | Add both beside P99; view a busy hour at 1-minute resolution |
| 2 | Stalls your profiler and GC logs don’t explain | jHiccup | Run it as a -javaagent (with -c) for a day; overlay its max on your P99.9 |
| 3 | Stalls on Kubernetes | container\_cpu\_cfs\_throttled\_periods\_total | Compare throttled with total periods for latency-sensitive pods |
| 4 | P99 worse after deploys or scale-out | P99 by pod age | Split P99 by minutes since pod start |
| 5 | Mysterious ~40ms delays | TCP\_NODELAY, pool metrics, TIME\_WAIT | Run ss -s on a busy host; confirm pooling and TLS reuse |
| 6 | Random multi-millisecond spikes on VMs | Fargate: cgroup throttling, jHiccup. EC2/VMware: CPU steal, CPUCreditBalance, %RDY | Look for burstable types and steal on your hottest service |
| 7 | Old fleet | Instance generations in use | List them; price one canary on the current generation |
| 8 | GC running more often | Allocation rate (JFR, async-profiler) | One 60-second allocation profile of a hot service |
| 9 | Paying for idle CPU | Autoscaling CPU target | Ask why it’s set there; if the answer is “GC,” measure it |
| 10 | Same JVM since the service launched | JVM vendor and version per service | List them; pick one latency-critical service for an A/A, then A/B canary |

**Try it on your own traffic**

- **Evaluate Azul Prime:** [request a trial](https://www.azul.com/downloads/) and run an A/A, then an A/B canary on a latency-sensitive service.
- **Rerun the Kafka benchmark:** [github.com/AzulSystems/kafka-benchmark](https://github.com/AzulSystems/kafka-benchmark).
- **Talk to an engineer:** [azul.com/contact](https://www.azul.com/contact/). Bring your P99.9, your throttling numbers, and your autoscaling targets.

#### Now go find your outliers.

## FAQ

**What causes high P99 latency in Java applications?**
High P99 latency in Java usually has several owners across the stack: Kubernetes CPU limits that throttle the whole JVM, cold JVMs after deploys and scale-ups, garbage collection pauses, allocation churn, and extra network hops. Averages hide these stalls, so teams should chart P99.9 and max from full histograms. Azul Prime addresses three of the causes: ReadyNow for warm-up, the Falcon JIT compiler for machine code, and the C4 garbage collector for pauses.

**How do I reduce Java warm-up time after deploys and autoscaling?**
Every deploy, scale-up, and reschedule starts a cold JVM that runs slowest for its first several thousand requests. Options range from warm-up requests and the OpenJDK AOT cache (Project Leyden, JDK 24 and later) to CRaC snapshots in builds such as Azul Zulu and GraalVM Native Image. Azul Prime ReadyNow reuses the JIT profile and compiler decisions recorded on earlier runs, so hot code compiles early.

**Why does my Java service stall in Kubernetes when CPU use looks normal?**
A CPU limit set too tight can throttle the entire JVM, including its garbage collection and JIT threads, once busy thread pools burn through the quota. The stalls appear as latency spikes that profilers do not explain. To check, compare `container_cpu_cfs_throttled_periods_total` with `container_cpu_cfs_periods_total` for latency-sensitive pods, a five-minute look recommended by Azul Field Engineering.

**How can I lower Java cloud costs without hurting latency?**
Teams that cannot trust their P99 often buy headroom instead: extra instances, CPU targets of 30 to 55 percent, and pods kept warm. Measuring the tail from full histograms lets them replace that headroom with evidence. Azul Optimizer Hub, used with Azul Prime, serves JIT profiles across a fleet and offloads compilation, and Azul reports one enterprise running more than 10,000 JVMs this way and cutting cloud costs by more than 20%.

**How do I choose a JVM for low-latency Java services?**
Run a bake-off on your own traffic, starting with an A/A run of two identical setups to see how much the numbers move on their own. Then compare candidates on warm-up, machine code quality, and garbage collection behavior under traffic spikes. In Azul’s published Apache Kafka benchmark, Azul Prime carried 30% more traffic while keeping P99 under 200ms and reached 45% higher maximum throughput than vanilla OpenJDK. Learn more about Azul Prime.
