---
title: "What Is the Redlock Algorithm?"
source: "https://redisson.pro/glossary/redlock-algorithm.html"
author:
published:
created: 2026-11-11
description: "The Redlock algorithm coordinates a distributed lock across several independent Redis nodes. Learn how its quorum works, the fencing-token safety debate, and what Redisson recommends today."
tags:
  - "clippings"
---

> [!summary]
> A Redisson glossary entry explaining Redlock: acquiring a lock on a majority of independent Redis/Valkey masters within the lock's validity window to survive the failover hazard of a single replicated master. It summarizes the Kleppmann vs. antirez debate over timing assumptions and fencing tokens, concluding that correctness-critical locks need fencing. Redisson has deprecated its RedLock object in favor of RLock with replica-sync checking plus RFencedLock.

The **Redlock algorithm** is a method for implementing a distributed lock across several independent Redis (or Valkey) nodes. Instead of trusting a single server, a client must acquire the lock on a majority of the nodes within a short time window, so the lock survives the failure of any individual node. It was proposed by Redis creator Salvatore Sanfilippo (antirez).

Redlock exists to solve a specific weakness of the simplest Redis lock: if you hold a lock on one master and that master fails over to a replica that has not yet received the lock, two clients can end up holding the "same" lock — a [split-brain](https://redisson.pro/glossary/split-brain.html) at the level of a single lock. Redlock's answer is to remove the single point of failure by spreading the decision across independent nodes.

## What Problem Redlock Solves

A basic distributed lock writes a key to one Redis master with an expiry, using a unique value so that only the owner can release it. That works until the master fails. Because Redis replication is asynchronous, a lock acknowledged by the master may not have reached its replica before the master dies — and the promoted replica has no record of it. The window is small, but in a system that needs locks for correctness, "small" is not "never."

Redlock attacks this by not depending on replication at all. It uses several fully independent masters — no replication between them — and treats the lock as held only when a majority agree.

## How the N-Node Quorum Works

The canonical setup uses **five independent Redis masters**. To acquire the lock, a client:

1. Records the current time.
2. Tries to acquire the lock on all five nodes in sequence, using the same key and a unique random value, with a short per-node timeout so a dead node can't stall the whole attempt.
3. Considers the lock acquired only if **two conditions both hold**: it succeeded on a **majority of nodes (at least three of five)**, and the total time elapsed is less than the lock's validity (its TTL). The remaining validity is the original TTL minus the time spent acquiring, with a small allowance for clock drift.
4. If it fails either condition, it releases the lock on every node and may retry after a random delay.

To release, the client deletes the key on all nodes, using its unique value so it never releases a lock that has since been taken over by someone else.

The majority requirement is what provides fault tolerance: as long as most of the nodes are up and agree, the lock is held, and no single node failure can hand the lock to two clients at once.

## The Safety Debate: Do You Need Fencing Tokens?

Redlock is one of the more debated algorithms in distributed systems, and the debate is worth understanding before you adopt it.

In a [2016 analysis](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html), Martin Kleppmann distinguished two reasons to take a lock. For **efficiency** — avoiding duplicate work, where an occasional double-execution is merely wasteful — almost any lock is fine. For **correctness** — where two holders would corrupt data — he argued Redlock is not safe enough, for two reasons. First, it leans on timing assumptions: a long garbage-collection pause, a clock jump, or network delay can leave a client believing it still holds a lock that has actually expired. Second, and more fundamentally, Redlock provides no **fencing token** — a monotonically increasing number, handed out on each acquisition, that the protected resource records and uses to reject any later write carrying a smaller number. Without it, a client that pauses past expiry can wake up and corrupt data even though another client now holds the lock.

Sanfilippo replied in ["Is Redlock safe?"](http://antirez.com/news/101), arguing that the pause-and-write problem is not specific to Redlock — it affects any lock service — and that where fencing is needed, an incrementing token can be layered on regardless of which lock you use. The disagreement is partly about how strong real-world clock and timing assumptions are.

The practical takeaway both sides effectively agree on: **if your lock guards correctness, use fencing tokens.** That is exactly what modern implementations now provide.

## Redlock in Redisson

Redisson is a Java client for Redis and Valkey, and it historically shipped a `RedLock` object implementing the algorithm above. **That object is now deprecated**, superseded by `RLock` and `RFencedLock`. The reasoning matches the consensus that emerged from the debate: the algorithm's safety guarantees are contested, and running a quorum of independent instances is a lot of operational cost for what is usually a single master with replicas.

The recommended approach today has two parts.

**1\. A standard `RLock` with replica-synchronization checking.** This closes the original failover hazard without a five-node quorum. After acquiring a lock, Redisson verifies it has reached the connected replicas; if the replicas don't acknowledge within a timeout, the lock is released and the acquisition fails — so a client never keeps a lock that wasn't safely replicated. It is on by default:

```java
Config config = new Config();
config.setCheckLockSyncedSlaves(true)   // default
      .setSlavesSyncTimeout(1000);       // milliseconds, default
```

**2\. `RFencedLock` when the lock guards correctness.** This is the fencing token the safety debate called for. Each acquisition returns a monotonically increasing token; the protected resource records the highest token it has seen and rejects any operation carrying a lower one, fencing out a stale holder that resumes after a pause:

```java
RFencedLock lock = redisson.getFencedLock("myLock");

Long token = lock.lockAndGetToken();
try {
    // pass token to the protected resource, which must reject any write
    // whose token is lower than the highest it has already accepted
    storage.write(data, token);
} finally {
    lock.unlock();
}
```

`RFencedLock` is available from Redisson 3.19.0 onward. If you previously used `RedLock` / `RedissonRedLock`, the migration is to a plain [Redis distributed lock](https://redisson.pro/glossary/redis-lock.html) (`RLock`) for the common case, adding a fenced lock where correctness demands it — not to the `MultiLock` object, which serves a different purpose (grouping several distinct locks as one unit).
