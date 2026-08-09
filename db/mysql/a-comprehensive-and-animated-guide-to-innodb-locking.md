---
title: "A Comprehensive (and Animated) Guide to InnoDB Locking"
source: "https://jahfer.com/posts/innodb-locks/"
author:
published:
created: 2026-08-09
description: "Musings on software development that you didn't ask for."
tags:
  - "clippings"
---

> [!summary]
> An animated walkthrough of InnoDB's locking primitives — record locks, gap locks, and the next-key locks built from both — and how their behaviour changes between the `SERIALIZABLE` and `REPEATABLE READ` isolation levels. The key rule: queries that resolve rows through a unique index or primary key need only a record lock, while non-unique index lookups must take gap locks on either side to keep reads repeatable. A notable trap is that a next-key lock on the first or last record in an index extends the gap all the way to ±Infinity, silently blocking a whole range of inserts at the tail of an index.

Recently, I had a chance to go deep on InnoDB’s locking mechanisms while attempting to debug some contention in MySQL that only appeared during high-throughput. This post is a culmination of my learnings on how InnoDB locking behaves under common scenarios.

## Introduction

InnoDB only has a handful of locking concepts, but their use and behaviour depend greatly on the transaction isolation level that is active for the connection.

> …the isolation level is the setting that fine-tunes the balance between performance and reliability, consistency, and reproducibility of results when multiple transactions are making changes and performing queries at the same time. ~ [14.7.2.1 Transaction Isolation Levels](https://dev.mysql.com/doc/refman/5.7/en/innodb-transaction-isolation-levels.html)

There are four transaction isolation levels for InnoDB (in order of most-to-least strict):

- `SERIALIZABLE`
- `REPEATABLE READ` (default)
- `READ COMMITTED`
- `READ UNCOMMITTED`

Locking behaves very differently under each of these, and I’ll touch on just the first two for now. To help explain these concepts, let’s make a table for tracking our book collection:

```sql
CREATE TABLE \`books\` (
  \`id\` bigint(20) NOT NULL AUTO_INCREMENT,
  \`author_id\` bigint(20) NOT NULL,
  \`title\` varchar(255) NOT NULL,
  \`borrowed\` tinyint(1) DEFAULT '0',
  PRIMARY KEY (\`id\`),
  KEY \`idx_books_on_author_id\` (\`author_id\`)
);

INSERT INTO \`books\` (\`author_id\`, \`title\`)
VALUES
  (101, "The Pragmatic Programmer"),
  (102, "Clean Code"),
  (102, "The Clean Coder"),
  (104, "Ruby Under a Microscope");
```

| id | author\_id | title | borrowed |
| --- | --- | --- | --- |
| `1` | `101` | The Pragmatic Programmer | `FALSE` |
| `2` | `102` | Clean Code | `FALSE` |
| `3` | `102` | The Clean Coder | `FALSE` |
| `4` | `104` | Ruby Under a Microscope | `FALSE` |

## InnoDB Lock Types

Before diving too deeply into the details, we should start with an important semantic that applies to all of the locks we’ll be looking at in this article. InnoDB locks can either be “ `shared` ” or “ `exclusive` ”:

> A shared (S) lock permits the transaction that holds the lock to read a row.
> An exclusive (X) lock permits the transaction that holds the lock to update or delete a row.
> ~ [14.7.1 InnoDB Locking](https://dev.mysql.com/doc/refman/5.7/en/innodb-locking.html#innodb-shared-exclusive-locks)

Like their names suggest, a `shared` lock can be held by multiple concurrent transactions since they may only read the row. In order to perform a write, an `exclusive` lock must be obtained, and can only be held by one transaction at a time. An `exclusive` lock cannot be taken if some other transaction holds a `shared` lock on the record; this is how InnoDB can guarantee the results of a read performed under a `shared` lock won’t change while being read.

Locks that are `shared` will *only lock rows in the index used to perform the read*. This is because the read needs to be reproducible, but only in the context of how the records were found. On the opposite end, `exclusive` locks are taken against the primary key of the record(s) which may have a larger impact since all secondary indexes are affected.

### Next-Key Locks

This blog post was intended to be primarily about a single type of InnoDB lock: the [next-key lock](https://dev.mysql.com/doc/refman/5.7/en/innodb-locking.html#innodb-next-key-locks). In an effort to thwart my abbreviated commentary, a next-key lock is actually a combination of *two other* kinds of locks: a [record lock](https://dev.mysql.com/doc/refman/5.7/en/innodb-locking.html#innodb-record-locks) and a [gap lock](https://dev.mysql.com/doc/refman/5.7/en/innodb-locking.html#innodb-gap-locks).

### Record Locks

Record locks are one of the simplest in InnoDB. It’s a lock taken on a specific row inside of an index. If we want to make sure no one updates our row while we’re inside of our transaction, we can acquire a shared read lock:

```sql
-- open transaction
BEGIN;
-- perform read
SELECT *
FROM \`books\`
-- obtain a shared (S) lock
WHERE \`id\` = 2 LOCK IN  MODE;
--         ... FOR SHARE; in MySQL 8.0
```

If we take a look at active locks via [`performance_schema.metadata_locks`](https://dev.mysql.com/doc/mysql-perfschema-excerpt/5.7/en/performance-schema-metadata-locks-table.html), we’ll see that we have a `SHARED_READ` lock on the `books` table:

```
mysql> SELECT OBJECT_NAME, LOCK_TYPE, LOCK_DURATION, LOCK_STATUS
    -> FROM performance_schema.metadata_locks
    -> WHERE OBJECT_NAME="books";
+-------------+-------------+---------------+-------------+
| OBJECT_NAME | LOCK_TYPE   | LOCK_DURATION | LOCK_STATUS |
+-------------+-------------+---------------+-------------+
| books       | SHARED_READ | TRANSACTION   | GRANTED     |
+-------------+-------------+---------------+-------------+
1 row in set (0.00 sec)
```

Multiple transactions are able to hold this lock, and they prevent any connection from updating the book where `id = 2` as long as the lock is held. This lock will be released once the transaction ends, either via `COMMIT` or `ROLLBACK`.

Now that we’ve seen how to acquire a lock for reading, let’s take a look at how we can acquire a lock for writing a record:

```sql
-- open transaction
BEGIN;
-- perform read
SELECT *
FROM \`books\`
-- obtain an exclusive (X) lock
WHERE \`id\` = 2 FOR UPDATE;
```

This query is slightly different in that we’ve acquired an *exclusive* lock for the row, meaning that anyone else who requests a lock for this row will have to wait for us to be done. This is because we’ve signaled to InnoDB that we’re going to change some of the values (via `FOR UPDATE`) so other updates would be operating on potentially-stale data.

```
mysql> SELECT OBJECT_NAME, LOCK_TYPE, LOCK_DURATION, LOCK_STATUS
    -> FROM performance_schema.metadata_locks
    -> WHERE OBJECT_NAME="books";
+-------------+--------------+---------------+-------------+
| OBJECT_NAME | LOCK_TYPE    | LOCK_DURATION | LOCK_STATUS |
+-------------+--------------+---------------+-------------+
| books       | SHARED_WRITE | TRANSACTION   | GRANTED     |
+-------------+--------------+---------------+-------------+
```

In this case we see a `SHARED_WRITE` lock, unlike the `SHARED_READ` we got before. Confusingly this is *not* the same `shared` semantic that we covered earlier; since it’s a lock for a write, the lock is actually `exclusive`. To avoid going on too much of a tangent, this post won’t go into the special semantics of `SHARED_WRITE (IX)` vs. `SHARED_READ (IS)` locks, but if you’re curious you can read about [intention locks](https://dev.mysql.com/doc/refman/5.7/en/innodb-locking.html#innodb-intention-locks).

### Gap Locks

A gap lock is a lock across a range of values in an index. InnoDB uses this lock type to ensure a set of selected records and the surrounding records maintain their relationship. If a lock is held on a gap, no other statement is allowed to `INSERT`, `UPDATE` or `DELETE` a record that falls within that gap. A gap lock may be taken on any index for the table, including the table’s [clustered index](https://dev.mysql.com/doc/refman/5.7/en/innodb-index-types.html).

To understand gap locking, we’ll need to understand how InnoDB stores its index records. Using [`innodb_ruby`](https://github.com/jeremycole/innodb_ruby), we can inspect our records in `idx_books_on_author_id` directly:

```ruby
$ innodb_space -s ./data/ibdata1 -T test/books -I idx_books_on_author_id index-recurse

ROOT NODE #4: 4 records, 84 bytes
  RECORD: (author_id=101) → (id=1)
  RECORD: (author_id=102) → (id=2)
  RECORD: (author_id=102) → (id=3)
  RECORD: (author_id=104) → (id=4)
```

InnoDB is able to lock the space between any two adjacent records. If we list out each pair of records in our index, we can see all of the possible gap locks InnoDB could use inside of a transaction:

- `(-Infinity, (101 → 1)]`
- `((101 → 1), (102 → 2)]`
- `((102 → 2), (102 → 3)]`
- `((102 → 3), (104 → 4)]`
- `((104 → 4), +Infinity)`

Let’s take a closer look at the third one in this list:

```
((102 → 2), (102 → 3)]
```

I’ve used interval notation here, so the left side is *exclusive* to the range and the right side is *inclusive*.

If we take this gap lock, any other connection that attempts to execute an `INSERT`, `UPDATE` or `DELETE` will have to wait for us if their record has an `author_id >= 102` and an `id` in the range of `2 < id <= 3`.

<video controls=""><source src="https://jahfer.com/static/gap-lock-basic.mp4?325f445cf087a6e897c7" type="video/mp4"></video>

Gap locks apply to the space between records.

With some high-level concepts down, let’s take a closer look at how these locks are used in real queries.

## Transaction Isolation Level: SERIALIZABLE

For statements performed within a `SERIALIZABLE` transaction isolation level, every record read by the query must be locked to ensure no other connection can modify the records being viewed. This is the strictest isolation level and its locking ensure that concurrent transactions can be reordered safely without impacting one another.

> For `SERIALIZABLE` level, the search sets shared next-key locks on the index records it encounters. ~ [14.7.3 Locks Set by Different SQL Statements in InnoDB](https://dev.mysql.com/doc/refman/5.7/en/innodb-locks-set.html)

If the `SELECT` query is using a unique index (such as the `PRIMARY KEY`), it does not need to use a gap lock since it can guarantee it is only affecting unique records.

> However, only an index record lock is required for statements that lock rows using a unique index to search for a unique row. ~ [14.7.3 Locks Set by Different SQL Statements in InnoDB](https://dev.mysql.com/doc/refman/5.7/en/innodb-locks-set.html)

## Transaction Isolation Level: REPEATABLE READ

Typical applications don’t need the guarantees `SERIALIZABLE` offers, so the default transaction isolation level InnoDB uses is `REPEATABLE READ`. A transaction using `REPEATABLE READ` will perform reads as if they were run at the same point in time (*“snapshotted”*) as the very first read in the transaction. This allows a consistent view of the database across queries without running into “ [phantom rows](https://dev.mysql.com/doc/refman/5.7/en/innodb-next-key-locking.html) ”: records that appear or disappear on subsequent reads.

The only time InnoDB is unable to use the snapshotted record is when it selects rows for an `UPDATE` or `DELETE`. In these scenarios, InnoDB must read the most recent version from the database to prevent it from accidentally operating against a stale value. While we don’t need to lock every record we come across (as done in `SERIALIZABLE` reads), it still means we must prevent other connections from writing records that could affect our statements.

### Locks on Primary Keys & Unique Indexes

The simplest case is when a locking query selects records using the table’s primary key:

```sql
-- open transaction
BEGIN;
-- issue statement
UPDATE \`books\`
SET \`borrowed\` = TRUE
WHERE \`id\` = 3;
```

Under `REPEATABLE READ` InnoDB ensures that this update is reproducible; it will always affect the same records because it blocks any other statements from impacting the results. While this transaction is open, no other client may `INSERT`, `UPDATE` or `DELETE` a record whose value overlaps this query.

When using a unique index (such as the table’s primary key), InnoDB does not need to take a gap lock on the left or right of the selected records since it is sure the values matched by the query are distinct from all others. In this example, we just need a record lock on the matching row, preventing others from updating or deleting it while this transaction is open.

<video controls=""><source src="https://jahfer.com/static/record-lock-basic.mp4?336a12e620d6c81e7c0d" type="video/mp4"></video>

A record lock is acquired on the clustered index for our distinct record.

Since we’ve left the transaction open above, the following statement will wait until that transaction is closed before executing:

```sql
UPDATE \`books\`
SET \`borrowed\` = TRUE
WHERE \`id\` = 3;
-- this waits until the first transaction exits,
-- as \`id = 3\` conflicts with the existing lock
```

In contrast, we can happily insert a record that isn’t conflicting:

```sql
INSERT INTO \`books\` (\`author_id\`, \`id\`, \`title\`)
VALUES (103, 5, "Database Internals");
-- success! \`id = 5\` doesn’t conflict with our UPDATE
```

When using InnoDB, working with a unique value (such as `id` above) is vastly preferred to when the engine cannot be sure of a unique result. InnoDB determines a record is unique if:

1. The record is selected by its `PRIMARY KEY`, *or…*
2. The record is selected by a `UNIQUE` index *and* using all components of that index in its selection

Of course, these two are shades of the same rule as `PRIMARY KEY` values are necessarily unique by nature. If the index being used to search meets the criteria for a ”unique” value, it does not need to use a gap lock. This is because InnoDB can be certain no possible conflicting values will be inserted as the value is guaranteed unique.

### Locks on Non-Unique Indexes

If the statement is selecting records that cannot be guaranteed as unique, it must use a gap lock to ensure the read query performed can be repeated while returning the same result (hence `REPEATABLE READ`). This is where the semantics of the next-key locking come into play.

> If one session has a shared or exclusive lock on record R in an index, another session cannot insert a new index record in the gap immediately before R in the index order. ~ [14.7.1 InnoDB Locking](https://dev.mysql.com/doc/refman/5.7/en/innodb-locking.html#innodb-next-key-locks)

Let’s take a look at our table and index again since we’ve made some modifications since the beginning:

| id | author\_id | title | borrowed |
| --- | --- | --- | --- |
| `1` | `101` | The Pragmatic Programmer | `FALSE` |
| `2` | `102` | Clean Code | `FALSE` |
| `3` | `102` | The Clean Coder | `TRUE` |
| `4` | `104` | Ruby Under a Microscope | `FALSE` |
| `5` | `103` | Database Internals | `FALSE` |

```ruby
$ innodb_space -s ./data/ibdata1 -T test/books -I idx_books_on_author_id index-recurse

ROOT NODE #4: 5 records, 105 bytes
  RECORD: (author_id=101) → (id=1)
  RECORD: (author_id=102) → (id=2)
  RECORD: (author_id=102) → (id=3)
  RECORD: (author_id=103) → (id=5)
  RECORD: (author_id=104) → (id=4)
```

From here, we can walk through an `UPDATE` statement that uses `idx_books_on_author_id` to investigate its locking behaviour:

```sql
-- open transaction
BEGIN;
-- issue statement
UPDATE \`books\`
SET \`borrowed\` = TRUE
-- select record by a non-unique value as
-- idx_books_on_author_id is not a UNIQUE index
WHERE \`author_id\` = 103;
```

Since we’ve selected a record using a non-unique value (`WHERE author_id = 103`), InnoDB must acquire two locks:

1. A record lock on the clustered index where `id = 5` (this is the primary key of the record where `author_id = 103`)
2. A next-key lock on `idx_books_on_author_id` where `author_id = 103`
<video controls=""><source src="https://jahfer.com/static/multi-lock.mp4?dbad03fd3863709342a2" type="video/mp4"></video>

The next-key lock on idx\_books\_on\_author\_id: a record lock with a gap lock on each side.

InnoDB must ensure that no other records that *could* meet this search result are inserted while this transaction is open. To do so, InnoDB acquires a gap lock on either side of the record. If you remember the section on [next-key locks](#next-key-locks), you might recall these locks are actually made up of two other lock types: record and gap locks.

In this example, there are three locks taken on `idx_books_on_author_id` to produce the next-key lock:

1. A record lock on `(author_id=103) → (id=5)`
2. A gap lock between the record’s values and next *smallest* values
3. A gap lock between the record’s values and next *largest* values

It's important to realize that InnoDB only needs to lock the *immediate* records surrounding the locked row, so while this query would be blocked:

```sql
INSERT INTO \`books\` (\`author_id\`, \`id\`, \`title\`)
VALUES (102, 6, "Clean Architecture");
-- (author_id=102) → (id=6) would need to be
-- inserted in the gap just before our record
```

…this query doesn’t get caught up in our lock:

```sql
INSERT INTO \`books\` (\`author_id\`, \`id\`, \`title\`)
VALUES (104, 6, "Clean Architecture");
-- (author_id=104) → (id=6) falls outside
-- of our gap lock range
```

We aren't blocked strictly on the range of `author_id` values (which would have been `102` – `104`), but the combination of `author_id` and `PRIMARY KEY` in the index.

A particularly surprising case comes when working with values at either end of an index. When acquiring a next-key lock on the first or last record in an index *and* the search does not meet the criteria for uniqueness, InnoDB must lock all values towards positive or negative infinity to make sure no other record overlaps this record’s position in the table.

> For the last interval, the next-key lock locks the gap above the largest value in the index and the “supremum” pseudo-record having a value higher than any value actually in the index. ~ [14.7.1 InnoDB Locking](https://dev.mysql.com/doc/refman/5.7/en/innodb-locking.html#innodb-next-key-locks)

Let’s go back to our table to see this in action:

```sql
-- open transaction
BEGIN;
-- issue statement
UPDATE \`books\`
SET \`borrowed\` = TRUE
-- select the largest author_id
WHERE \`author_id\` = 104;
```

<video controls=""><source src="https://jahfer.com/static/multi-lock-infinity.mp4?2ed472dae2aec29e7b76" type="video/mp4"></video>

One of the gap locks on the next-key lock continues all the way to +Infinity.

In this case, the next-key lock holds exclusive write access to `idx_books_on_author_id` from just after `(author_id=103) → (id=5)` all the way to `+Infinity`!

Since there was no `author_id` in the index `> 104`, InnoDB needed to lock the gap up to `+Infinity`. We’ve now blocked all insertions that contain an `author_id` larger than `104`; oops!

```sql
INSERT INTO \`books\` (\`author_id\`, \`title\`)
VALUES (153, "A Series of Unfortunate Events");
-- oh no! lock wait because 104 < 153 < +Infinity
```

This can be a particularly nasty problem since it’s not uncommon for insertions happen at the tail end of an index. As long as you make sure you’re selecting via a unique index or the primary key, you won’t have to worry about this type of lock contention.

## Conclusion

Hopefully you found this exploration of InnoDB’s locking mechanisms interesting! If you're looking for a broader—or more bite-sized—overview of InnoDB locking, I highly recommend [InnoDB Locking Explained with Stick Figures](https://www.slideshare.net/billkarwin/innodb-locking-explained-with-stick-figures) by Bill Karwin.

If you like this stuff in general, I have a (slow going) blog series where I’m attempting to build a [lock-free cache-oblivious B-tree](https://jahfer.com/posts/co-btree-0) as a fast cache in front of MySQL. I can’t promise you’ll find any feelings of satisfaction in those posts, but you might just learn something with me.
