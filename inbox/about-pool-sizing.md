---
title: "About Pool Sizing"
source: "https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing"
author:
  - "[[Agents]]"
published:
created: 2026-02-25
description: "光 HikariCP・A solid, high-performance, JDBC connection pool at last. - About Pool Sizing · brettwooldridge/HikariCP Wiki"
tags:
  - "clippings"
---

> [!summary]
> Explains why database connection pools should be much smaller than most developers expect. The optimal pool size formula is roughly `(core_count * 2) + effective_spindle_count`, and over-provisioning connections actually degrades performance due to context switching overhead.

Configuring a connection pool is something that developers often get wrong. There are several, possibly counter-intuitive for some, principles that need to be understood when configuring the pool.

Imagine that you have a website that while maybe not Facebook-scale still often has 10,000 users making database requests simultaneously -- accounting for some 20,000 transactions per second. How big should your connection pool be? You might be surprised that the question is not *how big* but rather *how small!*

Watch this short video from the Oracle Real-World Performance group for an eye-opening demonstration (~10 min.):

[![](https://github.com/brettwooldridge/HikariCP/wiki/Oracle_Youtube.png)](https://www.youtube.com/watch?v=_C77sBcAtSQ)

{Spoiler Alert} if you didn't watch the video. Oh come on! Watch it then come back here.

You can see from the video that reducing the connection pool size alone, in the absence of any other change, decreased the response times of the application from ~100ms to ~2ms -- over 50x improvement.

#### But why?

We seem to have understood in other parts of computing recently that less is more. Why is it that with only 4-threads an *nginx* web-server can substantially out-perform an *Apache* web-server with 100 processes? Isn't it obvious if you think back to Computer Science 101?

Even a computer with one CPU core can "simultaneously" support dozens or hundreds of threads. But we all \[should\] know that this is merely a trick by the operating system though the magic of *time-slicing*. In reality, that single core can only execute *one* thread at a time; then the OS switches contexts and that core executes code for another thread, and so on. It is a basic Law of Computing that given a single CPU resource, executing **A** and **B** sequentially will *always* be faster than executing **A** and **B** "simultaneously" through time-slicing. Once the number of threads exceeds the number of CPU cores, you're going slower by adding more threads, not faster.

That is *almost* true...

#### Limited Resources

It is not quite as simple as stated above, but it's close. There are a few other factors at play. When we look at what the major bottlenecks for a database are, they can be summarized as three basic categories: *CPU*, *Disk*, *Network*. We could add *Memory* in there, but compared to *Disk* and *Network* there are several orders of magnitude difference in bandwidth.

If we ignored *Disk* and *Network* it would be simple. On a server with 8 computing cores, setting the number of connections to 8 would provide optimal performance, and anything beyond this would start slowing down due to the overhead of context switching. But we cannot ignore *Disk* and *Network*. Databases typically store data on a *Disk*, which traditionally is comprised of spinning plates of metal with read/write heads mounted on a stepper-motor driven arm. The read/write heads can only be in one place at a time (reading/writing data for a single query) and must "seek" to a new location to read/write data for a different query. So there is a seek-time cost, and also a rotational cost whereby the disk has to wait for the data to "come around again" on the platter to be read/written. Caching of course helps here, but the principle still applies.

During this time ("I/O wait"), the connection/query/thread is simply "blocked" waiting for the disk. And it is during this time that the OS could put that CPU resource to better use by executing some more code for another thread. So, because threads become blocked on I/O, we can actually get more work done by having a number of connections/threads that is greater than the number of physical computing cores.

How many more? We shall see. The question of how many more also depends on the *disk subsystem*, because newer SSD drives do not have a "seek time" cost or rotational factors to deal with. Don't be tricked into thinking, "SSDs are *faster* and therefore I can have *more* threads". That is exactly 180 degrees backwards. Faster, no seeks, no rotational delays means *less blocking* and therefore *fewer* threads \[closer to core count\] will perform better than more threads. *More threads only perform better when blocking creates opportunities for executing.*

*Network* is similar to *disk*. Writing data out over the wire, through the ethernet interface, can also introduce blocking when the send/receive buffers fill up and stall. A 10-Gig interface is going to stall less than Gigabit ethernet, which will stall less than a 100-megabit. But network is a 3rd place runner in terms of resource blocking and some people often omit it from their calculations.

Here's another chart to break up the wall of text.

![](https://github.com/brettwooldridge/HikariCP/wiki/Postgres_Chart.png)

You can see in the above PostgreSQL benchmark that TPS rates start to flatten out at around 50 connections. And in Oracle's video above they showed dropping the connections from 2048 down to just 96. We would say that even 96 is probably too high, unless you're looking at a 16 or 32-core box.

#### The Formula

The formula below is provided by the PostgreSQL project as a starting point, but we believe it will be largely applicable across databases. You should test your application, i.e. simulate expected load, and try different pool settings *around* this starting point:

```
A formula which has held up pretty well across a lot of benchmarks for years is
that for optimal throughput the number of active connections should be somewhere
near ((core_count * 2) + effective_spindle_count). Core count should not include
HT threads, even if hyperthreading is enabled. Effective spindle count is zero if
the active data set is fully cached, and approaches the actual number of spindles
as the cache hit rate falls. ... There hasn't been any analysis so far regarding
how well the formula works with SSDs.
```

Guess what that means? Your little 4-Core i7 server with one hard disk should be running a connection pool of:`9 = ((4 * 2) + 1)`. Call it `10` as a nice round number. Seem low? Give it a try, we'd wager that you could easily handle 3000 front-end users running simple queries at 6000 TPS on such a setup. If you run load tests, you will probably see TPS rates starting to fall, and front-end response times starting to climb, as you push the connection pool much past `10` (on that given hardware).

If you have 10,000 front-end users, having a connection pool of 10,000 would be shear insanity. 1000 still horrible. Even 100 connections, overkill. You want a small pool of a few dozen connections at most, and you want the rest of the application threads blocked on the pool awaiting connections. If the pool is properly tuned it is set right at the limit of the number of queries the database is capable of processing simultaneously -- which is rarely much more than (CPU cores \* 2) as noted above.

We never cease to amaze at the in-house web applications we've encountered, with a few dozen front-end users performing periodic activity, and a connection pool of 100 connections. Don't over-provision your database.

---

#### "Pool-locking"

The prospect of "pool-locking" has been raised with respect to single actors that acquire many connections. This is largely an application-level issue. Yes, increasing the pool size can alleviate lockups in these scenarios, but we would urge you to examine first what can be done at the application level before enlarging the pool.

The calculation of pool size in order to avoid deadlock is a fairly simple resource allocation formula:

*pool size = T <sub>n</sub> x (C <sub>m</sub> - 1) + 1*

Where *T <sub>n</sub>* is the maximum number of threads, and *C <sub>m</sub>* is the maximum number of *simultaneous connections* held by a single thread.

For example, imagine three threads (*T <sub>n</sub> =3*), each of which requires four connections to perform some task (*C <sub>m</sub> =4*). The pool size required to ensure that deadlock is never possible is:

*pool size = 3 x (4 - 1) + 1 = 10*

Another example, you have a maximum of eight threads (*T <sub>n</sub> =8*), each of which requires three connections to perform some task (*C <sub>m</sub> =3*). The pool size required to ensure that deadlock is never possible is:

*pool size = 8 x (3 - 1) + 1 = 17*

👉 This is not necessarily the *optimal* pool size, but the *minimum* required to avoid deadlock.

👉 In some environments, using a JTA (Java Transaction Manager) can dramatically reduce the number of connections required by returning the same Connection from `getConnection()` to a thread that is already holding a Connection in the current transaction.

---

#### Caveat Lector

Pool sizing is ultimately very specific to deployments.

For example, systems with a mix of long running transactions and very short transactions are generally the most difficult to tune with any connection pool. In those cases, creating two pool instances can work well (eg. one for long-running jobs, another for "realtime" queries).

In systems with primarily long running transactions, there is often an "outside" constraint on the number of connections needed -- such as a job execution queue that only allows a certain number of jobs to run at once. In these cases, the job queue size should be "right-sized" to match the pool (rather than the other way around).
