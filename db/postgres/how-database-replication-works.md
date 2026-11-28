---
title: "How Database Replication Works"
source: "https://www.joesluis.com/blog/how-database-replication-works"
author:
  - "[[Joe Sluis]]"
published: 2026-11-20
created: 2026-11-26
description: "how database replication works and why it is likely more complicated than you may think"
tags:
  - "clippings"
---

> [!summary]
> Joe Sluis explains Postgres replication from first principles: why shipping raw SQL breaks on non-deterministic functions like `NOW()`, and how physical replication instead streams WAL records that replicas write to their own WAL and replay, tracking progress by LSN and relying on replication slots to stop the primary from discarding WAL a replica still needs. It contrasts asynchronous and synchronous replication, including the `synchronous_commit` levels `remote_write`, `on`, and `remote_apply`, in terms of commit latency, availability, and data loss. It closes with failover in single-leader setups: heartbeat detection, promoting the replica with the highest LSN, split-brain, and fencing.

Database replication seems fairly simple. The basic idea is to copy data from one database server to another, typically for fault tolerance and read scalability. But there's a lot to consider: sync vs async replication, logical vs physical replication, single-leader vs multi-leader, replication lag, failovers, fencing, and more.

I ran into a lot of these questions even while building the simplest possible [Postgres failover controller in Rust](https://github.com/JoeS51/rust-systems-examples/tree/main/crates/pg-failover), which inevitably nerd-sniped me...

![Nerd sniping comic with a database replication question on the sign](https://www.joesluis.com/images/nerd-sniping-replication.png)

Nerd sniping comic with a database replication question on the sign

There are many flavors of database replication, so I won't be able to cover all the details, but my goal is to teach you how database replication actually works, so the tradeoffs become clear!

### What does the primary send to its replicas?

In database replication, the primary obviously needs to communicate with the replicas to keep them updated. Since the primary and replicas are usually on different servers entirely, this communications happens over the network. In Postgres, the primary listens on port `5432` by default and the replicas will create their own TCP connection to that port to establish communication. Once a replica connects to this port, what does the primary send?

Well, the primary could send the original SQL query to its replicas. For example:

```sql
INSERT INTO table1 (name, created_at) VALUES ('joe', NOW());
```

You might have noticed a problem here. If the primary and replica both recieve and execute this query separately, then they will each evaluate `NOW()` for themselves. The primary might store 12:00:00 in `created_at`, while the replica stores 12:00:01. Storing different data in the primary and replica would defeat the purpose of replication, so we need a different strategy.

*fun fact*: there are actually ways to do replication properly using this method, and it's called statement-based replication. Postgres doesn't natively support it though, so we won't be covering it. Look at MySQL if you're curious:)

Instead of sending the SQL queries from the primary to the replicas, we need to send the exact data we want to write on the replica and where to write it to in the database. Thankfully, we have the perfect thing for that: the write-ahead log (WAL). You can think of the WAL as one long append-only file where each change to the database is recorded. The WAL is comprised of these things called the WAL records.

Let's use the SQL query above as an example. The WAL records for that might look like this:

```
LSN: 0/1000100
Transaction ID: 742
Resource manager: Heap
Operation: INSERT
Relation (tablespace/database/file): 1663/16384/24576
Fork: main
Block: 0
Tuple offset: 1
Tuple data (decoded for readability):
  name: 'joe'
  created_at: '2026-11-20 12:00:00+00'

LSN: 0/1000180
Transaction ID: 742
Resource manager: Transaction
Operation: COMMIT
```

There are two WAL records here: one for the actual inserted data and the other for the COMMIT. You can see that the first WAL record contains the timestamp already computed on the primary, so if we can just send the replicas these WAL records, we avoid our earlier problem entirely. And that's what physical replication does! In physical replication, the primary just sends the raw WAL data to its replicas.

A common alternative to physical replication is logical replication. Instead of sending the raw WAL data to the replicas, Postgres decodes the WAL into row-level changes (INSERTs, UPDATEs, and DELETEs) and sends those changes to the replicas.

Term

Physical replication

Sends raw WAL so replicas can replay changes to database pages

Term

Logical replication

Decodes WAL into row-level changes and sends those changes to subscribers

From here on out, we will be focusing on physical replication, but the core idea remains the same.

### How does the replica receive and apply the WAL?

Before a replica can keep up with new changes from the primary, it needs a copy of the data that's already on the primary. A new physical replica typically starts from a base backup of the primary, which is just a copy of the primary's database cluster on disk (e.g. the pages that store the tables and indexes).

From there, the replica applies WAL to bring itself up to date. As the primary generates more WAL, it streams it to the replica, which keeps applying it to stay caught up. This describes streaming replication.

To keep track of its progress, the replica needs a way to identify positions in the WAL. That's what the LSN in our example above is for.

Term

Log Sequence Number (LSN)

the byte offset of a WAL record in the WAL

In Postgres, the LSN is a single 64-bit integer represented by 32-bit integer / 32-bit integer (I know it's weird). So in the example above, the first INSERT record is at byte offset 0x1000100 in the WAL and the second COMMIT record is at a byte offset 0x1000180. You can see how this can be important in database replication. By comparing the primary's current LSN with the LSN the replica has replayed up to, you can tell how far behind the replica is (this is called **replica lag**).

In Postgres streaming replication, the replica first connects to the primary and sends its latest LSN. This tells the primary how far behind the replica is.

1. If the LSN of the primary and the replica already match, then perfect! The primary doesn't need to send anything to the replica at that moment.
2. If the LSN of the replica is behind the primary's, then the primary will send all the WAL data from the replica's LSN onwards. The replica will receive all this WAL data and write that data directly into its own WAL

As the primary continues to receives writes from clients and append to its WAL, it will keep sending its WAL records to the replicas. The replica will also periodically report its LSN to the primary.

When the replica receives the WAL records from the primary, it has to do two things:

1. Put that WAL data into its own WAL - for durability purposes
2. Replay that WAL data, which essentially means applying the changes described by the WAL records to the replica's own database pages

This WAL replay is the same mechanism that is used when a database crashes and you need to bring your database up-to-speed.

**INSERT**

INSERTCOMMIT

WAL / TCP

INSERTCOMMIT

INSERTCOMMIT

But there's another problem we haven't considered yet. The primary can't keep its WAL around forever. At some point, it needs to clean up its old WAL data, so how do we prevent it from removing WAL that a replica still needs?

In Postgres, this is solved using something called replication slots. A replication slot keeps track of which WAL data a replica still needs and prevents the primary from removing it. This does introduce another problem though. If a replica goes offline for an extended period of time, the WAL on the primary can keep accumulating until it runs out of disk space.

### When is a write considered successful?

In the animation above, I intentionally left out a crucial detail about when can we tell the client that their transaction has been committed. The answer to that depends on whether you are using synchronous replication or asynchronous replication.

Term

Synchronous replication

The primary waits for the required replicas to acknowledge the transaction before reporting success to the client

Term

Asynchronous replication

The primary reports a successful commit without waiting for replica acknowledgements. Replicas catch up independently

Which one you should use depends on what you care about. With async replication, the primary can report a successful COMMIT without waiting for the replica. That keeps the replica off the commit path, but if the primary fails before the replica receives the commit record, then you could have lost data.

With sync replication, the primary waits for the required replica(s) to acknowledge the commit before telling the client it has succeeded. This adds latency to commits, and if the required replicas become unavailable, commits can block even while the primary is healthy. But the benefit is that a successful commit isn't only stored on the primary since the required replicas have acknowledged it too.

It's important to note here that there are different levels of sync replication. In Postgres, you can choose what the standby has to do before it sends that acknowledgment back to the primary. The [`synchronous_commit`](https://postgresqlco.nf/doc/en/param/synchronous_commit/) setting gives you three options when synchronous standbys are configured:

- `remote_write` - waits for the standby to write the commit record to its own WAL. At this point, the operating system can still have the write buffered in memory ([link](https://biriukov.dev/docs/page-cache/2-essential-page-cache-theory/) if you want to understand this better)
- `on` - this is the default in Postgres. The primary waits for the standby to save the commit record durably in its own WAL on disk. The standby can recover the transaction from its WAL, but a query there can still miss the new row until replay catches up
- `remote_apply` - waits for the replicas to replay the commit record. By the time the primary tells the client that COMMIT succeeded, a new query on that standby can see the row

Client **Waiting…**

WAL · disk

INSERTCOMMIT

Synchronous standbyWAL · OS cache

INSERTCOMMIT

WAL · disk

INSERTCOMMIT

table1 · readable row

joe12:00:00+00

Wait for: **Write to OS cache**

### What if the primary fails?

In this article, I mainly covered single-leader replication, but there are other models where there isn't just a single primary.

Term

Single-leader replication

A single primary takes care of all the writes and sends them to the replicas

Term

Multi-leader replication

Multiple nodes can independently accept writes and replicate their changes to each other

Term

Leaderless replication

There is no designated primary. Clients can send writes to multiple replicas, often using quorums to determine whether reads and writes are successful

In single-leader replication, if the primary crashes, then we need to promote one of the replicas as the new primary, this is called a failover.

At a high level, failover usually involves these three steps:

1. Detect that the primary has gone down
2. Choose a replica to promote as the new primary
3. Redirect clients/replicas to the new primary

Each step, as you can imagine, comes with its own challenges. For example, how do you tell that the primary has actually gone down? One common technique is to use heartbeats. If the primary hasn't responded in some amount of time, then we say it has failed and start the failover process.

For the second step, how do you know which replica to promote? Well, ideally you want to promote the replica with the highest LSN because that's the replica that has the most recent data. However, with asynchronous replication, even the replica with the highest LSN could be missing data that was on the primary. This means that transactions that were successfully committed and acknowledged to the client could be lost during failover.

Another interesting problem is what happens when the old primary comes back to life. If we promote a replica and the old primary starts accepting writes again, we now have two primaries that can independently accept writes. Their data can start to diverge, and this situation is known as split-brain (the implications are as scary as it sounds).

One way to prevent split-brain is through a mechanism called fencing, where we ensure that the old primary can no longer accept writes before allowing the new primary to do so. This can involve shutting down the old primary's machine, revoking its access to shared storage, etc.

Once a replica is promoted as the new primary and everything routes to the new primary, then everything can proceed as we described above.

### Conclusion

Database replication clearly has a lot of layers, and there's still more to the story than what I covered, but like I mentioned earlier, I strongly beleive that if you understand the principles behind it, then a lot of these database concepts become clear.

For example, take point-in-time recovery (PITR), which is a feature in Postgres and other databases where you can recover the state of the database back to what it was at some point-in-time. The mechanism behind PITR is very similar to what we covered with replication. If you have a base backup and the WAL, you can restore the database from the base backup and then replay the WAL until you reach the point you want. That shoulds sound familiar since that's the whole process behind replication that we described!

If you got this far, thank you, it really means a lot! If you have any feedback at all, please let me know [joesluis51@gmail.com](mailto:joesluis51@gmail.com).

### Bonus

Whenever I read articles, I like to ask myself questions about the content to see if I actually understood what I read (active recall ftw).

So I assembled some questions [here](https://www.joesluis.com/blog/how-database-replication-works/quiz) that you can try if it interests you!
