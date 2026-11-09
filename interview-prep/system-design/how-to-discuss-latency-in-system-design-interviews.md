---
title: "How to discuss latency in system design interviews"
source: "https://interviewing.io/blog/how-to-discuss-latency-in-system-design-interviews"
author:
  - "[[Nimble Alligator]]"
published: 2026-11-05
created: 2026-11-06
description: "In the system design interviews I conduct at Google, I keep seeing bad latency requirements. Here's how to do it better."
tags:
  - "clippings"
---

> [!summary]
> A Google interviewer argues that latency is a design constraint rather than an optimization goal, and walks through realistic numbers from nanosecond memory access up to minute-scale human on-call response. Candidates should do the budget math, rule out what cannot fit at p99, and name the trade-off they accept, using examples like Postgres vs. Cassandra, Redis vs. Memcached, and Kafka vs. RabbitMQ. Interviewers are judging architectural coherence: whether the numbers stated early actually match the boxes drawn later.

We helped write the sequel to "Cracking the Coding Interview". [Read 9 chapters for free](https://bctci.co/free-chapters)[interviewing.io](https://interviewing.io/)

![Author avatar](https://interviewing.io/_next/image?url=https%3A%2F%2Fstrapi-iio.s3.us-west-2.amazonaws.com%2FNimble_Alligator_Avatar_e3788ae042.jpeg&w=384&q=75 "Nimble Alligator") Nimble Alligator

*Nimble Alligator is an anonymous interviewer and dedicated coach on interviewing.io, and a Senior Software Engineer at Google specializing in backend infrastructure.*

*In the system design interviews I conduct at Google and on interviewing.io, I keep seeing bad latency requirements. Sometimes a target is so tight it’s impossible to design for. Sometimes it’s so loose the design makes no sense. Either way, it’s an unforced error. At the extremes, this is obvious: you can’t accomplish any computing in a picosecond, and an hour is too long to wait for almost anything in a distributed system. The harder part is everything in between.*

*This post breaks down what makes sense at each latency tier, when each one matters in an interview, and how to present the trade-offs effectively. And there’s a cheat sheet at the end to help you keep your estimates in the right ballpark.*

---

I have seen candidates write something like "p99 latency < 10ms" on the whiteboard before they know what the system needs to do. Twenty minutes later, they have drawn a globally distributed system with an API gateway, an external auth check, three microservice hops, and a relational database commit across multiple regions. The latency requirement is long forgotten.

**Latency is not an optimization goal. Latency is a constraint that limits your design choices.**

I have seen a candidate go even further and promise to deliver an end-to-end p99 latency under 1 ms. But they were doomed to fail from the moment they set that requirement. Don't believe me? Open your terminal and ping your router right now. Go ahead. I’ll wait.

My computer is hardwired via Ethernet directly to a router in the same room. My average ping is about 1 ms. If I switch to Wi-Fi, that jumps to 7 ms. If I ping the nearest cloud datacenter, the round-trip takes 15-25 ms.

Even *inside a single datacenter*, a 1 ms p99 budget leaves you almost no room for sequential network calls. While a single warm intra-datacenter round-trip across Top-of-Rack switches might take 150-400 µs at the median, tail latency and hop count destroy your margin. Once you factor in the compounding math of hitting even two or three downstream services, your 1 ms budget is exhausted before your service runs a single line of business logic.

Let’s walk through what you can actually accomplish at each latency tier, starting from the metal and working our way up to global scale. Along the way, we will look at how you should use these numbers to justify your architecture out loud.

## 1\. The Nanosecond Tier: 1-1,000 ns (Silicon & Memory)

At the nanosecond level, we are talking about a handful of CPU clock cycles. If your code does anything more complex than a few raw machine instructions, you are already past a nanosecond.

- **L1 CPU cache hit:** ~0.5-1 ns
- **L2 / L3 cache access & atomic instructions:** 3-15 ns (p99: 40-80 ns)
- **Standard DRAM main memory access:** 60-100 ns (p99: 150-250 ns)

**When does this matter in an interview?** Almost never. You won't be designing CPU caches in a high-level system design interview, though it is useful context for why reading from local in-process memory is four orders of magnitude faster than calling an external cache over the network.

## 2\. The Microsecond Tier: 1-1,000 µs (Kernel & Local NVMe)

Once you leave CPU memory and talk to the operating system kernel or local flash storage on a single box, you are working in microseconds.

- **System call:** 100-500 ns (p99: 1-2 µs)
- **OS thread or process context switch:** 1-2 µs (p99: 10-30 µs)
- **Local NVMe SSD random 4 KB read:** 10-100 µs (p99: 100-300 µs)
- **Page cache append, no fsync:** 10-50 µs (p99: 50-500 µs)

**When does this matter in an interview?** Like nanoseconds, you rarely need to cite microsecond figures unless you are explaining why a single node can handle 100,000+ operations per second before the network becomes the bottleneck.

**How to say it in the interview:**

> *"At 50,000 writes per second with a 20 ms p99, I would avoid Postgres. An fsync’d commit can hit 20–50 ms at the tail, and scaling writes past one node means sharding by hand. Cassandra fits this write-heavy load. A write is a commit-log append plus a memtable insert, which takes tens of microseconds and leaves room for the cross-AZ quorum. The tradeoff is that the commit log syncs periodically, so a crashed node can lose a few seconds of acknowledged writes; replicating to three nodes covers that. We also give up ad-hoc queries and transactions."*

## 3\. The Single-Digit Millisecond Tier: 1-10 ms (Inside the Datacenter)

The 1-10 ms tier is where the components you draw on the whiteboard actually live. Once you cross the network inside a datacenter, every box you draw has a price tag in milliseconds.

- **Intra-datacenter RPC (e.g., gRPC pod-to-pod):** 0.2-0.5 ms (p99: 1-2 ms)
- **Distributed in-memory cache read (Redis / Memcached):** 0.5-1 ms (p99: 1-2 ms)
- **Cross-Availability Zone (AZ) network round-trip:** 1-2 ms (p99: 2-5 ms)
- **Indexed read in PostgreSQL or MySQL:** 1-5 ms (p99: 10-30 ms)
- **Transactional RDBMS commit (with fsync to WAL):** 2-10 ms (p99: 20-50 ms)
- **Raft consensus write (etcd / Consul):** 1-3 ms (p99: 5-25 ms)

### The Transport Tax: API Gateways

When you are trying to show a clean separation of concerns on the whiteboard, it is tempting to split every responsibility into its own microservice: an API Gateway, an Auth Service, a Rate Limiter, a User Service, and an Order Service. That looks great on an architecture diagram, but every box and arrow carries a real transport tax.

Putting an API gateway like Envoy or Kong in front of your stack adds 1.5-5 ms of p99 latency overhead for routing, TLS termination, and mTLS re-encryption. If that gateway makes a synchronous call to an Auth service on every request instead of validating JWTs locally, you just burned another network round-trip. In highly latency-sensitive paths, this may not be acceptable.

### How to Justify Your Tech Stack Using Latency Math

A common interview trap is naming a technology ("Let's use Redis and Postgres") and moving on without explaining why it fits. To stand out as a senior candidate, let your latency constraints make those decisions for you.

When you pick a database or cache, walk the interviewer through this three-step mental model:

1. **Do the math:** Roughly calculate how much of your latency SLO is left after accounting for gateway and network overhead.
2. **Rule out what won't fit:** Point out which patterns (like synchronous disk flushes, multi-hop fan-outs, or maintaining quorum across regions) will exceed your latency budget at p99.
3. **Name the tradeoff you are accepting:** Pick the tool that fits the time window, and state clearly what you are giving up (strict consistency, durability, or complex queries) to buy that speed.

Here is what that sounds like in two different scenarios:

**Scenario A: You have a relaxed latency budget, so you prioritize correctness.**

> *"Our order write-path has a 200 ms p99 budget, with payment authorized asynchronously. After gateway overhead, we have plenty of room for a 5-10 ms synchronous WAL flush. Since we don't need sub-millisecond writes, let's stick with PostgreSQL. It gives us strict relational integrity, foreign keys, and atomic transactions without the operational headache of a distributed NoSQL store."*

**Scenario B: You have a tight read budget that dictates which cache you pick.**

> *"To return ranked leaderboard updates in under 5 ms at p99, we cannot sort the leaderboard at read time. We should use Redis over Memcached here. Redis gives us in-memory sorted sets, which lets us update and query rankings in under 1 ms in a single network hop. With Memcached, we would have to serve potentially stale precomputed snapshots."*

### Strong Consistency vs. Low Latency

Strong consistency and low latency are natural enemies.

Writing to a strongly consistent Raft group (like etcd) requires a network round-trip to a majority quorum plus a disk fsync on a majority of nodes. Within one datacenter that takes a few milliseconds, but spread the quorum across availability zones on cloud disks and you can see 10–30 ms on average, with p99 spikes into the hundreds of milliseconds. Furthermore, when a primary database node dies, heartbeat timeouts and leader election take 1-60 seconds, depending on the solution. During that window, in-flight requests pile up. If your upstream clients don't have circuit breakers and exponential backoff with jitter, your cluster will tip over into a retry storm the moment the new leader comes online.

## 4\. The Multi-Millisecond Tier: 10-100 ms (The WAN & Mobile Networks)

Once packets leave your datacenter and travel across the country or over cellular towers, physics raises the floor.

Light travels through fiber-optic glass at roughly 200,000 kilometers per second. That gives us an unbreakable floor of about 5 µs per kilometer (or ~200 km per millisecond).

- Wired fiber optic home internet round-trip: 15-25 ms (p99: 20-40 ms)
- LEO satellite link (Starlink) round-trip: 30-50 ms (p99: 100-200 ms)
- 5G Sub-6 GHz radio round-trip: 10-40 ms (p99: 50-150 ms)
- 4G LTE radio round-trip: 40-70 ms (p99: 150-300 ms)
- US Coast-to-Coast round-trip (SF to NY): 60-80 ms (p99: 120-200 ms)

Let's do the math for a packet traveling from San Francisco to New York. The straight-line distance is about 4,100 km, but fiber cables follow highways and railroad tracks, stretching the actual path to roughly 5,500 km. Therefore, the absolute physical minimum for a round-trip is:

**Minimum Round Trip = 2 × (5,500 km × 5 µs/km) = 55 ms**

Add router hops and switching delays, and you are looking at 60-80 ms in the real world. A synchronous two-phase commit between the coasts needs two cross-country round trips, one to prepare and one to commit, so expect 120–160 ms per write. Multi-region Raft is cheaper: the leader needs only one round trip to a majority of replicas. That still costs 60–80 ms if the majority spans both coasts. You can shrink it by placing the leader close to a majority, for example with the leader in the central US and replicas on each coast, so a quorum only waits on the nearer coast. Either way, the client’s own trip to the leader still counts against your budget.

In an interview, you can use the speed of light to justify splitting your control plane from your data plane:

**For the control plane:**

> *"Our control plane manages cluster metadata and shard assignments. It updates infrequently and can easily tolerate a 500 ms write latency. We'll use a multi-region Raft group like etcd here to guarantee strict linearizability and prevent split-brain during network partitions, even though every write pays a cross-country quorum penalty."*

**For the data plane:**

> *"On the other hand, our user-facing data plane has a 30 ms p99 write budget. Because a round-trip from SF to NY takes at least 55 ms in fiber, we physically cannot wait for a cross-country quorum. We need to acknowledge writes locally in the user's nearest region and replicate asynchronously to other regions in the background, trading away strong global consistency to meet our latency SLO."*

**A quick note on mobile clients:** Mobile users on 4G or 5G pay an unavoidable radio latency tax before their packet ever hits the internet backbone. Waking a mobile radio from an idle state adds 50-100 ms to the very first packet. If you are designing a mobile app, squeezing your backend service down from 15 ms to 5 ms won't make the app feel fast. You need client-side optimistic UI updates and fewer round trips instead.

## 5\. The Second Tier: 100 ms to 10 Seconds (Global WAN, Heavy Compute & Humans)

At the 100 ms to 10-second scale, transoceanic cables, cryptographic handshakes, heavy compute, and human perception collide.

- **Transoceanic round-trip (US to Europe / Asia)**: 70-250 ms (p99: 400-800 ms)
- **Cold TCP + TLS 1.3 handshake over public WAN:** 100-300 ms (p99: 500-1,500 ms)
- **Feels instantaneous to a human:** under ~100 ms
- **Human cognitive context-switch threshold:** ~1 second
- **External payment processor call:** 250-1,000 ms (p99: 2-5 s)
- **User task-abandonment threshold:** ~10 seconds \[1\]

When physics or heavy third-party APIs stop you from making an operation faster, you can't optimize your code out of the problem. Instead, change the architecture to move the slow work off the critical path:

1. **Precompute on the write path:** Instead of running expensive multi-table joins when a user loads their feed, use background stream workers to pre-populate denormalized read views in Redis ahead of time. Sometimes, a hybrid (normally precompute writes, defer to read time for hot keys) approach may be warranted to avoid unnecessary write amplification.
2. **Prefetch predictable actions:** Pull the next likely page of data into client memory while the user is still reading the current screen.
3. **Use Optimistic UI updates:** Update the client UI the millisecond the user taps "Like," and let a background worker sync the state to the server. Only roll back the UI if the request fails.

### Synchronous vs. Asynchronous Decoupling

Human psychology influences rules for API design, too. Anything under 100 ms feels instantaneous. Once a request crosses 1 second, the user notices they are waiting on the computer. After 10 seconds, users close the tab or mash the submit button again.

Whenever an operation requires heavy compute (like video encoding), external banking rails, or wide downstream fan-out, holding open a synchronous HTTP connection makes it difficult to achieve latency targets. Instead, consider decoupling the request: have the client send an idempotency key, return an HTTP 202 Accepted with a job ID once the task is accepted into a queue, and notify the client via WebSockets, Server-Sent Events (SSE), or polling when it finishes.

Even when you decouple work with a queue, your latency requirements should dictate which broker you put on the board:

**When producer write latency and throughput are the bottleneck:**

> *"To keep our clickstream ingestion API under 25 ms p99 at 100,000 events per second, the producer can't wait around for downstream analytics services or per-message broker bookkeeping. Kafka appends batches to the page cache and gets its durability from replication rather than per-message fsync, so even waiting on replica acks we can acknowledge writes well within the budget and let independent consumer groups read the log at their own pace."*

**When complex routing matters more than ingestion speed:**

> *"For our document-conversion pipeline, ingestion volume is low and the user is already waiting on a multi-second async job, so sub-10 ms producer latency doesn't buy us anything. I'll use RabbitMQ over Kafka here because we need priority queues, flexible routing keys, and per-message worker acknowledgments with dead-letter retries for long-running tasks."*

## 6\. The Minute Tier: 10 Seconds to Minutes (Batch Jobs & Human Ops)

Past 10 seconds, you are out of the request-response lifecycle entirely. This is the world of batch pipelines and human incident response.

- **Bulk data warehouse scan or MapReduce stage:** 10-60 seconds
- **Database snapshot or full-text index rebuild:** 1-30 minutes
- **Daytime on-call engineer alert triage:** 2-5 minutes (p99: 15-30 minutes)
- **Nighttime on-call engineer alert triage (waking up):** 8-15 minutes (p99: 30-45 minutes)

Where does this show up in a system design interview? Most often when you are designing a monitoring, telemetry, or alerting pipeline, including use cases like cloud cost anomalies or IoT sensor monitoring.

If your pipeline ends in an alert to a human operator, size it to the human’s reaction time, not to what streaming infrastructure can do. Think about who is on the receiving end of that notification. A sleeping on-call engineer takes 10 minutes to wake up to a PagerDuty alert, grab their laptop, log into the VPN, open Grafana, and figure out what is broken. Even during the middle of the workday, an engineer optimistically takes 2-5 minutes to context-switch and triage an issue.

Shaving 500 milliseconds off your metrics ingestion pipeline does nothing when the human at the end of the webhook takes 5 minutes to read the page. If the output of your system is a human action, a 30-60 second batching and evaluation window is practically real-time:

> *"Since these alerts page an on-call engineer who will take at least a few minutes to triage the issue, sub-second streaming detection doesn't buy us any real-world speed. Instead of maintaining complex stateful stream processors to evaluate rules in milliseconds, we can check alert thresholds every 15 seconds against the last 30 seconds of metrics, and only page if the problem persists across two checks. That cuts compute costs and keeps brief network blips from paging anyone."*

On the flip side, if a failure mode will destroy your cluster in seconds (like a cascading retry storm or a dead database primary), **you cannot design an alert to a human as your mitigation strategy.** If your system handles 50,000 requests per second, a 10-minute human response window means dropping **30,000,000** requests before anyone runs a single command. Actions that require sub-second or single-digit-second reaction times (rate limiting, load shedding, circuit breaking, and failover) must be automated in software. Save the minute-scale alerting pipelines for problems that actually require human judgment.

## 7\. Interview Strategy: How to Negotiate the "Just Right" Latency

Candidates sometimes try to set latency targets by asking the interviewer directly: " *What should the latency target be?"*

In almost every interview, the interviewer will either shrug and say *"Reasonably fast,"* or turn the question right back around on you: ***"What do you think it should be?"***

Don't wait for them to bounce the question back. Strong candidates drive the requirements phase by proposing a concrete latency target based on the user experience, and then asking the interviewer if they agree.

### Anchor on human perception to give yourself breathing room

Don't sign up for a 10 ms SLO if the product doesn't need it. Every tier you move down also costs real money and complexity. You can often frame the budget around the user:

> *"Since we are building an interactive web dashboard, sub-10 ms response times don't add any user value because anything under about 100 ms already feels instantaneous. I suggest we target a p99 of 50 ms measured at our load balancer, since we can’t control the user’s network. That gives us enough room for a standard relational database without premature sharding or complex caching. Does that sound reasonable?"*

In one statement, you showed product awareness, defined where the clock starts, and kept your database architecture simple.

### Set separate budgets for your read and write paths

Nobody says your reads, writes, and background fan-out have to run at the same speed. Splitting them up lets each path meet only the constraint it actually needs:

> *"Our read path needs to be fast so user feeds load in under 100 ms, which we can hit using a cache-aside Redis cluster. On the write path, the user publishing a post needs an acknowledgement in under 250 ms, which we can do by persisting the post and dropping an event into a queue. Their followers won't notice if it takes 10 seconds for that post to appear in their feeds, so we can set a 10-second eventual consistency SLO for the background fan-out. The author sees their own post right away, since we show it client-side before the fan-out completes."*

### Define your SLO at the tail (p99), not the median (p50)

Averages and medians hide the truth. If 98% of requests finish in 1 ms and 2% stall for 1 second behind a garbage collection pause, your median is 1 ms and your average is about 21 ms, which looks fine on a dashboard. But your p99 is a full second and your heaviest users are having a terrible experience.

Furthermore, in a microservice architecture, tail latencies compound. If a user request fans out to 10 parallel services, and each service has a 1% chance of taking 500 ms (p99), the probability that the *overall* user request gets stuck waiting on at least one slow service jumps to nearly 10%:

**P(at least one slow call) = 1 - (0.99)^10 ≈ 9.6%**

State your targets in p95 or p99 from the very first minute of the interview, clarify whether that clock starts at the user's phone or at your load balancer, and let the physics of those numbers guide every box you draw.

## What your interviewer is evaluating

When I fill out interview feedback after a system design round, I am not checking off whether you memorized the latency of an NVMe SSD read. I do not care if an intra-datacenter RPC takes 300 microseconds or 800 microseconds.

You are being evaluated on **architectural coherence.**

I want to see if the numbers you write down in the first five minutes of the interview actually relate to the boxes you draw in the next thirty minutes.

If you claim a 10 ms p99 budget and then describe a multi-region synchronous database commit, those two things cannot coexist. It tells me you either didn’t know, didn’t notice, or didn’t care.

If you do the rough latency math and say, *"We can't afford a synchronous write here, so we’ll replicate asynchronously and accept a few seconds of data loss if a region fails,"* you have demonstrated exactly the kind of attention to detail that I look for in senior candidates.

Stop treating latency like a wish list. Treat it like a budget, spend your milliseconds deliberately, and let the numbers drive your design.

## Cheat sheet

| Nanoseconds | Reading from memory (CPU cache or RAM) |
| --- | --- |
| Microseconds | Reading or writing a local SSD |
| 1–10 ms | Committing a database write or calling across availability zones |
| 10–100 ms | Round trip across the United States or over a mobile network |
| 100 ms–1 s | Calling a slow third-party API, like a payment processor |
| 1–10 s | Starting a container that has to download its image first |
| 10–60 s | Generating an LLM response with extended thinking |
| Minutes+ | A human who isn’t already at the keyboard |

## Key Terms

| p50 / p99 (percentile latency) | The time within which 50% or 99% of requests finish. p50 is the median. p99 is the “tail”: 1 in 100 requests is slower than this. Latency targets are set at p99 because averages and medians hide stalls. |
| --- | --- |
| fsync | A system call that forces data out of the operating system’s in-memory page cache onto durable storage. Until it returns, a crash can lose data. It takes microseconds on a local NVMe and milliseconds on network-attached disks. |
| Write-ahead log (WAL) | An append-only log where a database records each change before applying it, so committed writes survive a crash. Most of a database’s commit latency is the time to fsync this log. |
| Availability Zone (AZ) vs. region | An AZ is one or more isolated datacenters inside a region, typically 1–2 ms apart from the other AZs. A region is a geographic area that contains several AZs, and regions are typically at least tens of milliseconds apart. Replicating across AZs survives a single datacenter failure. Replicating across regions survives a regional outage, but at a higher latency and ingress/egress cost. |
| Quorum | A majority of replicas (for example, 2 of 3) that must acknowledge an operation before it counts. Any two majorities overlap, so a committed write can’t be lost or contradicted. |
| Raft consensus | An algorithm where an elected leader replicates a log to follower nodes and commits each entry once a quorum acknowledges it. It’s used by etcd and Consul. Write latency is the leader’s round trip to the quorum plus an fsync on each replica. |
| SLO / latency budget | A Service Level Objective is a target for a measured metric, such as “99% of requests under 50 ms.” The latency budget is that SLO split into allowances for each component (gateway, network, database) that together must stay under it. |
| Strong (linearizable) vs. eventual consistency | Under strong consistency, every read sees the latest completed write, as if there were only one copy of the data. Under eventual consistency, replicas can return stale data for a while but converge once writes stop. Strong consistency costs a quorum round trip on every write. |
| Control plane vs. data plane | The control plane manages configuration and metadata, such as cluster membership, shard assignments and routing. It changes rarely and can typically afford slow, strongly consistent writes. The data plane serves user requests at high volume and usually needs low latency. |
| Fan-out | One operation spreading into many: a request calling several downstream services in parallel, or a write copied to many destinations (for example, a post pushed into every follower’s feed). Tail latency compounds with every parallel call. |

### Have interviews coming up? Study up on common questions and topics.

MEDIUM

Data Structures and Algorithms

### K Closest Points To Origin

[Given a list of tuples that represent (X, Y) coordinates on an XY plane and an integer K, return a list of the K-closest points to the origin (0, 0).](https://interviewing.io/questions/k-closest-points-to-origin)

MEDIUM

Data Structures and Algorithms

### Walls and Gates

[You are given a m x n 2D grid initialized with these three possible values. Fill each empty room with the distance to its nearest gate.](https://interviewing.io/questions/walls-and-gates)

MEDIUM

Data Structures and Algorithms

### Even Odd Tree

[Given a tree, verify that on even levels, all values in the level are strictly increasing and even. On odd levels, verify all values in the level are strictly decreasing and odd.](https://interviewing.io/questions/even-odd-tree)

## We know exactly what to do and say to get the company, title, and salary you want.

Interview prep and job hunting are chaos and pain. We can help. Really.

![App screenshot](https://interviewing.io/_next/image?url=%2Fstatic%2Fimages%2FFooterImg.png&w=3840&q=75)
