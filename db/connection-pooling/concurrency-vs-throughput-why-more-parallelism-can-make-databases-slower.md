---
title: "Concurrency vs. Throughput: why more parallelism can make databases slower"
source: "https://planetscale.com/blog/concurrency-vs-throughput-vitess-mysql"
author:
  - "[[Liz van Dijk]]"
published: 2026-08-07
created: 2026-08-08
description: "Increasing throughput sometimes requires reducing parallelism. A look into why this is the case for Vitess + MySQL databases"
tags:
  - "clippings"
---

> [!summary]
> A PlanetScale post-mortem of a sixteen-minute MySQL meltdown where one uncommitted batch transaction held row locks, and the ten thousand queries admitted behind it — mostly snapshot reads, not lock waiters — each had to walk ever-longer version chains until the buffer pool collapsed. The fix was counterintuitive: shrink the Vitess transaction pool from ten thousand back to roughly a thousand and make a full pool queue rather than error, mimicking the thread pool the workload used before migrating off Cloud SQL. The article frames this with Little's Law and Gunther's Universal Scalability Law, where the coherency term β scales with N(N−1) and causes retrograde scaling — past a critical concurrency, admitting more work reduces total throughput.

Not long ago we watched a production MySQL database melt down for sixteen minutes.

The errors started as a trickle, a handful per minute, then fed on themselves:

```
minute   errors/min   queries/s
  0          5          15,000   <- a burst of work arrives
  2         60           3,900
  4        300           2,500
  6        550           2,000
  8        900           1,900
 10      1,400           1,500   <- error peak = throughput trough
 12        700           1,700
 14        250           2,000
 16          0           2,500   <- locks released, backlog drained
 18          0           8,500   <- full recovery, throughput jumps 5x
```

The trigger was fairly mundane: A batch job opened a transaction against a hot table, took row locks, and then held them for fifteen minutes without committing. A common application bug, the kind that eventually sneaks into many large codebases.

What happened around this long transaction is the interesting bit! The queries piling up behind that transaction were mostly not blocked on its locks at all. They were simple reads, where InnoDB didn't need to wait for row locks; it reads a consistent snapshot instead. Building that snapshot means walking back through the version history of every row the open transaction had touched, and that history grew for fifteen straight minutes.

This caused reads that normally took milliseconds to start blowing through their 90-second execution ceilings. The application retried them in a tight loop. Within minutes, more than ten thousand requests were piled up inside the storage engine. Processing each required reconstructing ever-longer version chains, and the resulting page reads outpaced the buffer pool's ability to free memory.

Now requests that had nothing to do with the locked rows, that touched entirely different tables, began failing too. The otherwise correctly sized buffer pool suddenly became too small to serve the crowd of queries.

At PlanetScale, we run our MySQL databases with Vitess, whose configured transaction timeout eventually killed the long-running transaction. Its locks were released, and the sixteen-minute backlog drained in about thirty seconds.

One slow transaction should not take down a database, and much of Vitess's plumbing is built around avoiding exactly this situation. So what went wrong? This was caused by the combination of the single long-running query and the ten thousand requests allowed in after.

## Migration from Cloud SQL to Vitess

Some context on how a seemingly healthy database could end up like this in the first place.

This workload had recently been migrated onto PlanetScale from Cloud SQL, which ran Managed Connection Pooling, a thread-pool-style layer, in front of the database. A thread pool caps how many statements execute at once, commonly around a thousand, and queues the rest. A client arriving when the pool is full waits for a slot, usually for milliseconds, occasionally for a few hundred milliseconds. This cap can protect InnoDB's internals even under extreme load.

On PlanetScale, every MySQL shard sits behind a Vitess proxy called [vttablet](https://vitess.io/docs/reference/programs/vttablet/). These have a transaction pool, which caps how many transactions can be open against MySQL at once. Unlike a thread pool, when this pool fills, requests wait a set amount of time and then *fail with an error*.

For this workload, that small difference made the issue way worse. Errors propagated up an application stack that had never needed to handle them (since the Cloud SQL thread pool queued requests, pool-full errors effectively didn't exist there).

The solution that was initially tried was to **raise the transaction pool cap and increase the timeout**.

The pool was increased to ten thousand, a number chosen not by sizing but because it made the errors stop. However, this now limited Vitess's ability to control the backpressure between the application and the database storage engine.

## Why high concurrency reduces MySQL throughput

Picture database transactions as items flowing down a conveyor belt (Factorio, anyone?). If they never interacted, throughput would scale in a straight line: twice the items in flight, twice the work done. That is the dream of a perfectly [shared-nothing](https://en.wikipedia.org/wiki/Shared-nothing_architecture) system, but rarely is that achieved. Somewhere on the belt there is a junction where multiple conveyor belts meet. In MySQL, this is the equivalent of a hot row, a latch, a CPU run queue, etc.

Below is a simple playground to visualize how request rate and queuing impact latency. Adjust the `ARRIVALS / S` slider to see the impact.

<iframe src="https://planetscale.com/blog/doing-more-with-less/iframe#junction" title="Interactive: rising load against a single junction"></iframe>

[Little's Law](https://en.wikipedia.org/wiki/Little%27s_law) describes this well. In steady state, `N = X * W`. Work-in-flight equals throughput times the time each request spends inside the database. Rearranged, `X = N / W`.

Adding in-flight requests raises throughput only as long as query execution time holds steady. If each new arrival stretches the execution/wait time of all the other queries within the database, the denominator now grows along with the numerator.

Just how badly can that go? [Gunther's Universal Scalability Law](https://www.perfdynamics.com/Manifesto/USLscalability.html) splits the cost of concurrency into three terms:

```
γN
X(N) = ───────────────────────────
        1 + α(N−1) + βN(N−1)
```

- `N` is how much work you allow to run at once.
- `γ` is the ideal single-request throughput: the linear scaling coefficient if requests never interacted.
- `α` (contention) is the cost of taking turns for a shared resource.
- `β` (coherency) is the cost of requests making *each other* slower. Put differently, the work a database must do to keep shared state consistent across everything in flight.

Note the multiplier `N(N−1)`, which grows with the number of *pairs* of requests. When `N` doubles, this coherency cost roughly quadruples.

Past a critical point, `N_max = √((1−α)/β)`, `β` dominates, and total throughput actually starts to reverse. Gunther calls it retrograde scaling: beyond the peak, every request you admit requires coordination overhead and makes everything slower.

<iframe src="https://planetscale.com/blog/doing-more-with-less/iframe#usl-curve" title="Interactive: the Universal Scalability Law curve"></iframe>

Let's look at how the problem from earlier maps to this equation. The row locks were `α`. The transactions that wanted those rows had to take turns, and no amount of concurrency changed the queue's drain rate. `β`, the real issue, was InnoDB trying to process so many queries at once: ten thousand concurrent snapshot reads, each made more expensive by the version history every *other* in-flight transaction was generating. The per-request cost rose with the increase in in-flight requests.

This is why focusing on "lock contention" does not explain the issue. The lock is just one of many potential junctions. It is the damage *around* the junction, the mutual slowdown of everything admitted past it, that scales with the square of concurrency and turns a slow batch job into a wider outage.

## Reducing pool size and implementing queuing

To solve this, we implemented the reverse of the change that set this up, in both dimensions at once:

1. Reduce the Vitess transaction pool size from ten thousand to roughly the thousand the old thread pool used. We now did this consciously and with evidence-backed proof: that workload had run successfully for years with a pool of that size.
2. Instead of erroring after waiting, a transaction arriving at a full pool now queues for a slot with a longer timeout.

In other words, we configured Vitess's vttablet layer to mimic the old thread pool's behavior.

For this to be safe, two things must be true. The clients have to tolerate periodic waiting during bursts and the wait itself has to be bounded, so that a truly undersized system announces itself with timeouts at the queue rather than accumulating latency forever. Both are true for this workload.

The morning after rolling out this new configuration, it met its first test. A traffic burst arrived on a different Vitess shard of the same database, one that handles an order of magnitude more steady traffic. At peak, the pool handled around twenty-five thousand transaction pool slot requests *per second* against its thousand-odd available slots. Here are the results, in the same view we opened with:

```
minute   slot requests/s   errors/min   queries/s
  0             3,000           0         58,000
 10             9,000           0         61,000
 20            26,000           0         60,000   <- peak pressure, throughput flat
 30            17,000           0         59,000
 40             8,000           0         62,000
 50             4,000           0         60,000
 60             2,000           0         57,000   <- burst drained, queue empty
```

During the earlier incident, errors climbed to 1,400 a minute and throughput fell to a tenth of what the workload requested.

With the new and improved configuration, the application experienced no disruption and QPS didn't drop.

Over the entire day, database health was much better:

- **One rejected transaction.** Despite slot requests/s at times jumping as high as 40,000, the queue absorbed effectively everything. Waits sat comfortably within the timeout.
- **Fewer than two hundred statements executing inside MySQL at any instant.** InnoDB managed the bursts well. Sixty thousand queries a second through fewer than two hundred concurrent slots is Little's Law again: about three milliseconds apiece.
- **Lock contention didn't change.** The hot-row pattern was just a minor contributor here. We were able to solve the problem without changing the lock contention dynamics.

This allowed the database to do less work *at once*, allowing it to do more work in total.

Below is another playground to visualize the difference between an open request flow and a gated one. Send bursts of traffic, simulate a locking event, and see the difference between a gated and ungated solution with the buttons below.

<iframe src="https://planetscale.com/blog/doing-more-with-less/iframe#before-after" title="Interactive: same workload, opposite overflow behavior"></iframe>

## When to limit database concurrency

This is not a universal recommendation to tightly limit concurrency. Its applicability must be understood in the context of your workload.

- Workloads built on pessimistic locking and contended shared state.
- Hot rows updated by many workers.
- `SELECT ... FOR UPDATE` on popular keys.
- Long transactions holding locks while they do unrelated work.
- Counters, balances, job queues.

If that describes your workload, added concurrency might just decrease your throughput!

The principles described here are not MySQL-specific. Postgres can have similar problems, but also a similar solution: [PgBouncer](https://planetscale.com/docs/postgres/connecting/pgbouncer) 's transaction pooling exists to allow for more client concurrency than server concurrency. This is why our [Postgres offering](https://planetscale.com/docs/postgres) comes with a local PgBouncer, and can be configured with dedicated primary and replica PgBouncer instances too.

## Building systems that handle backpressure

**Backpressure can't always be avoided, so make conscious choices about the expected behavior.** The answer is almost never to simply raise a limit out of reach, but to fix what happens when that limit is reached.

Sometimes the fastest thing you can do for a busy system is to simply let less happen at once.
