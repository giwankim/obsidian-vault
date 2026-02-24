---
title: "Database Transactions — PlanetScale"
source: "https://planetscale.com/blog/database-transactions"
author:
published: 2026-01-14
created: 2026-02-24
description: "What are database transactions and how do SQL databases isolate one transaction from another?"
tags:
  - "clippings"
---

> [!summary]
> PlanetScale's interactive guide to database transactions covering ACID fundamentals, how Postgres uses multi-row versioning (xmin/xmax) vs. MySQL's undo log for consistent reads, and the four isolation levels (Serializable, Repeatable Read, Read Committed, Read Uncommitted) with their tradeoffs.

Want to move to PlanetScale? Postgres migration assistance is now available.[Get started](https://planetscale.com/migrate)

[Blog](https://planetscale.com/blog) |

## Database Transactions

By Ben Dicken |

**Transactions** are fundamental to how SQL databases work.Trillions of transactions execute every single day, across the thousands of applications that rely on SQL databases.

## What is a database transaction?

A transaction is a sequence of actions that we want to perform on a database as a single, atomic operation.An individual transaction can include a combination of reading, creating, updating, and removing data.

In MySQL and Postgres, we begin a new transaction with `begin;` and end it with `commit;`.Between these two commands, any number of SQL queries that search and manipulate data can be executed.

The example above shows a transaction begin, three query executions, then the `commit`.You can hit the ↻ button to replay the sequence at any time.The act of committing is what atomically applies all of the changes made by those SQL statements.

There are some situations where transactions do not commit.This is sometimes due to *unexpected* events in the physical world, like a hard drive failure or power outage.Databases like MySQL and Postgres are designed to correctly handle many of these unexpected scenarios, using disaster recovery techniques.Postgres, for example, handles this via its write-ahead log mechanism (WAL).

There are also times when we want to *intentionally* undo a partially-executed transaction.This happens when midway through a transaction, we encounter missing / unexpected data or get a cancellation request from a client.For this, databases support the `rollback;` command.

In the example above, the transaction made several modifications to the database, but those changes were *isolated* from all other ongoing queries and transactions.Before the transaction committed, we decided to `rollback`, undoing all changes and leaving the database unaltered by this transaction.

By the way, you can use the menu below to change the speed of all the sessions and animations in this article.If the ones above were going too fast or too slow for your liking, fix that here!

A key reason transactions are useful is to allow execution of many queries simultaneously without them interfering with each other.Below you can see a scenario with *two* distinct sessions connected to the same database.**Session A** starts a transaction, selects data, updates it, selects again, and then commits.**Session B** selects that same data twice during a transaction and again after both of the transactions have completed.

Session B does not see the name update from `ben` to `joe` until after Session A commits the transaction.

Consider the same sequence of events, except instead of `commit` ing the transaction in Session A, we `rollback`.

The second session never sees the effect of any changes made by the first, due to the `rollback`.This is a nice segue into another important concept in transactions: **Consistent reads**.

## Consistent Reads

During a transaction's execution, we would like it to have a consistent view of the database.This means that even if another transaction simultaneously adds, removes, or updates information, our transaction should get its own isolated view of the data, unaffected by these external changes, until the transaction commits.

MySQL and Postgres both support this capability when operating in `REPEATABLE READ` mode (plus all stricter modes, too).However, they each take different approaches to achieving this same goal.

Postgres handles this with **multi-versioning of rows**.Every time a row is inserted or updated, it creates a new row along with metadata to keep track of which transactions can access the new version.MySQL handles this with an **undo log**.Changes to rows immediately overwrite old versions, but a record of modifications is maintained in a log file, in case they need to be reconstructed.

Let's take a close look at each.

## Multi-row versioning in Postgres

Below, you'll see a simple `user` table on the left and a sequence of statements in `Session A` on the right.Click the "play sessions" button and watch what happens as the statements get executed.

Let's break down what happened:

- `begin` starts a new transaction
- An update is made to the user with ID `4`, changing the name from "liz" to "aly".This causes a new version of the row to be created, while the other is maintained.
- The old version of the row had its `xmax` set to 10 (xmax = max transaction ID)
- The new version of the row also had its `xmin` set to 10 (xmin = min transaction ID)
- The transaction commits, making the update visible to the broader database

But now we have two versions of the row with ID = 4.Ummm... that's odd!The key here is `xmin` and `xmax`.

`xmin` stores the ID of the transaction that *created* a row version, and `xmax` is the ID of the transaction that caused a replacement row to be created.Postgres uses these to determine which row version each transaction sees.

Let's look at `Session A` again, but this time with an additional `Session B` running simultaneously.Press "play sessions" again.

Before the commit, Session B could not see Session A's modification.It sees the name as "liz" while Session A sees "aly" within the transaction.At this stage, it has nothing to do with `xmin` and `xmax`, but rather because other transactions cannot see uncommitted data.After Session A commits, Session B can now see the new name of "aly" because the data is committed and the transaction ID is greater than 10.

If the transaction instead gets a `rollback`, those row changes do not get applied, leaving the database in a state as if the transaction never began in the first place.

This is a simple scenario.Only one of the transactions modifies data.Session B only does `select` statements!When both simultaneously modify data, each one will be able to "see" the modifications it made, but these changes won't bleed out into other transactions until commit.Here's an example where each transaction selects data, updates data, selects again, commits, and finally both do a final select.

The concurrent transactions cannot see each other's changes until the data is committed.The same mechanisms are used to control data visibility when there are hundreds of simultaneous transactions on busy Postgres databases.

Before we move on to MySQL, one more important note.What happens to all those duplicated rows?Over time, we can end up with thousands of duplicate rows that are no longer needed.There are several things Postgres does to mitigate this issue, but I'll focus on the `VACUUM FULL` command.When run, this purges versions of rows that are so old that we know no transactions will need them going forward.It compacts the table in the process.Try it out below.

Notice that when the `vacuum full` command executes, all unused rows are eliminated, and the gaps in the table are compressed, reclaiming the unused space.

## Undo log in MySQL

MySQL achieves the consistent read behavior using a different approach.Instead of keeping many copies of each row, MySQL immediately overwrites old row data with new row data when modified.This means it requires less maintenance over time for the rows (in other words, we don't need to do vacuuming like Postgres).

However, MySQL still needs the ability to show different versions of a row to different transactions.For this, MySQL uses an **undo log** — a log of recently-made row modifications, allowing a transaction to reconstruct past versions on-the-fly.

Notice how each MySQL row has two metadata columns (in blue).These keep track of the ID of the transaction that updated the row most recently (`xid`), and a reference to the most recent modification in the undo log (`ptr`).

When there are simultaneous transactions, transaction A may clobber the version of a row that transaction B needs to see.Transaction B can see the previous version(s) of the row by checking the undo log, which stores old values so long as any running transaction may need to see it.

There can even be several undo log records in the log for the same row simultaneously.In such a case, MySQL will choose the correct version based on transaction identifiers.

## Isolation Levels

The idea of **Repeatable reads** is important for databases, but this is just one of several **isolation levels** databases like MySQL and Postgres support.This setting determines how "protected" each transaction is from seeing data that other simultaneous transactions are modifying.Adjusting this setting gives the user control of the tradeoff between isolation and performance.

Both MySQL and Postgres have four levels of isolation:From strongest to weakest, these are: **Serializable**, **Repeatable Read**, **Read Committed**, **Read Uncommitted**.

Stronger levels of isolation provide more protections from data inconsistency issues across transactions, but come at the cost of worse performance in some scenarios.

**Serializable** is the strongest.In this mode, all transactions behave as if they were run in a well-defined sequential order, even if in reality many ran simultaneously.This is accomplished via complex locking and waiting.

The other three gradually loosen the strictness, and can be described by the *undesirable* phenomena they allow or prohibit.

### Phantom reads

A **phantom read** is one where a transaction runs the same `SELECT` multiple times, but sees different results the second time around.This is typically due to data that was inserted and committed by a different transaction.The timeline below visualizes such a scenario.The horizontal axis represents time passing on a database with two clients.Hit the ↻ button to replay the sequence at any time.

After **serializable**, the next least strict isolation level is called **repeatable read**.Under the SQL standard, the **repeatable read** level allows phantom reads, though in Postgres they still aren't possible.

### Non-repeatable reads

These happen when a transaction reads a row, and then later re-reads the same row, finding changes by another already-committed transaction.This is dangerous because we may have already made assumptions about the state of our database, but that data has changed under our feet.

The **read committed** isolation level, the next after **repeatable read**, allows these and phantom reads to occur.The tradeoff is slightly better database transaction performance.

### Dirty reads

The last and arguably worst is **dirty reads**.A **dirty read** is one where a transaction is able to see data written by another transaction running simultaneously that is not yet committed.This is really bad!In most cases, we never want to see data that is uncommitted from other transactions.

The loosest isolation level, **read uncommitted**, allows for dirty reads and the other two described above.It is the most dangerous and also most performant mode.

## Concurrent writes

The keen-eyed observer will notice that I have ignored a particular scenario, quite on purpose, up to this moment.What if two transactions need to modify the *same* row at the *same* time?

Precisely how this is handled depends on both (A) the database system and (B) the isolation level.To keep the discussion simple, we'll focus on how this works for the strictest (`SERIALIZABLE`) level in Postgres and MySQL.Yet again, the world's two most popular relational databases take very different approaches here.

### MySQL: Row-level locking

Simply put, MySQL handles conflicting writes with locks.

A **lock** is a software mechanism for giving ownership of a piece of data to one transaction (or a set of transactions).Transactions **obtain a lock** on a row when they need to "own" it without interruption.When the transaction is finished using the rows, it **releases the lock** to allow other transactions access.

Though there are many types of locks in practice, the two main ones you need to know about here are **shared locks** and **exclusive locks**.

A **shared (S) lock** can be obtained by multiple transactions on the same row simultaneously.Typically, transactions will obtain shared locks on a row when *reading* it, because multiple transactions can do so simultaneously safely.

An **exclusive (X) lock** can only be owned by one transaction for any given row at any given time.When a transaction requests an X lock, no other transactions can have any type of lock on the row.These are used when a transaction needs to write to a row, because we don't want two transactions simultaneously messing with column values!

In `SERIALIZABLE` mode, all transactions must always obtain X locks when updating a row.Most of the time, this works fine other than the performance overhead of locking.In scenarios where two transactions are both trying to update the same row simultaneously, this can lead to deadlock!

MySQL can detect deadlock and will kill one of the involved transactions to allow the other to make progress.

### Postgres: Serializable Snapshot Isolation

Postgres handles write conflicts in `SERIALIZABLE` mode with less locking, and avoids the deadlock issue completely.

As transactions read and write rows, Postgres creates **predicate locks**, which are "locks" on sets of rows specified by a predicate.For example, if a transaction updates all rows with IDs 10–20, it will take a lock on the predicate `WHERE id BETWEEN 10 AND 20`.These locks are not used to block access to rows, but rather to *track* which rows are being used by which transactions, and then detect data conflicts on-the-fly.

Combined with multi-row versioning, this lets Postgres use optimistic conflict resolution.It never blocks transactions while waiting to acquire a lock, but it will kill a transaction if it detects that it's violating the SERIALIZABLE guarantees.

Let's look at a similar timeline from the MySQL example, but this time watching Postgres' optimistic technique.

The difference is subtle visually, but implemented in quite different ways.Both Postgres and MySQL leverage the killing of one transaction in favor of maintaining SERIALIZABLE guarantees.Applications must account for this outcome, and have retry logic for important transactions.

## Conclusion

Transactions are just one tiny corner of all the amazing engineering that goes into databases, and we only scratched the surface!But a fundamental understanding of what they are, how they work, and the guarantees of the four isolation levels is helpful for working with databases more effectively.

What esoteric corner of database management systems would you like to see us cover next?Join our [Discord community](https://pscale.link/community) and let us know.

Happy databasing.
