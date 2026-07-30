---
title: "How MVCC and Transactions Work in RocksDB"
source: "https://artem.krylysov.com/blog/2026/07/23/how-mvcc-and-transactions-work-in-rocksdb/?from_theconsensus=1"
author:
published:
created: 2026-07-29
description:
tags:
  - "clippings"
---

> [!summary]
> An LSM-tree gives RocksDB half of MVCC for free — writes never mutate in place — and this post covers the other half: monotonic sequence numbers stamped into every internal key, snapshots that pin a published sequence number, and a reference-counted `SuperVersion` that stops compaction from freeing memtables or SSTs an in-flight read still needs.
> On that primitive sit atomic write batches and two transaction flavors: pessimistic (per-key locks taken at write time, can deadlock) and optimistic (1M hashed mutexes validated at commit against the memtable), plus how `set_snapshot` and `get_for_update` map onto read-committed, snapshot isolation, and near-serializable behavior — including where write skew and phantom reads still leak through.
> Ends with benchmarks showing which flavor wins under which contention profile, and notes that TiKV, YugabyteDB, and CockroachDB all skip RocksDB-native transactions because they are node-local.

- [databases](https://artem.krylysov.com/tag/databases/)
- [key-value](https://artem.krylysov.com/tag/key-value/)
- [lsm](https://artem.krylysov.com/tag/lsm/)
- [rocksdb](https://artem.krylysov.com/tag/rocksdb/)

RocksDB is built on an LSM-tree, which never modifies data in-place - every write creates a new version of the key. That's half of what you need to implement Multi-Version Concurrency Control ([MVCC](https://en.wikipedia.org/wiki/Multiversion_concurrency_control)).

Real-world databases serve many clients reading and writing the same data at the same time. The simplest way to make concurrent access safe is locking (think of a hash map protected with a mutex). This works from the correctness perspective, but makes readers and writers block each other, which can quickly become a performance bottleneck. MVCC solves this problem, allowing readers and writers to proceed concurrently. The idea is that:

1. Writers never modify or delete keys in-place, instead they create new versions of the keys
2. Readers see a consistent view of the data as it existed when the read started - they access older versions of the keys, while writers keep creating new versions independently

MVCC is used in many DBs including [PostgreSQL](https://www.postgresql.org/docs/18/mvcc-intro.html), [CockroachDB](https://www.cockroachlabs.com/glossary/distributed-db/mvcc-multiversion-concurrency-control/), [FoundationDB](https://apple.github.io/foundationdb/developer-guide.html), MongoDB [WiredTiger](https://www.mongodb.com/docs/manual/core/wiredtiger/), and [LMDB](http://www.lmdb.tech/doc/). Today we'll see how RocksDB implements the other half of MVCC - snapshots that give readers that consistent view, atomic updates and transactions built on top.

### Versioning Keys

All inserts, updates and deletes go through a write buffer (*memtable*) and then get flushed to disk into an immutable *SST* (Static Sorted Table) file - you naturally have multiple versions of the same key. Compaction is the garbage collection process that merges SSTs and removes older versions of keys.

> [!note] Note
> If you want to go deeper on LSM internals, I covered them in [How RocksDB works](https://artem.krylysov.com/blog/2023/04/19/how-rocksdb-works/).

Let's pretend our database is an insert-only list ordered by key. If we add these key-value pairs dog,a, chipmunk,a, cat,a, raccoon,a, we'll end up with a list that looks like this:

It's a toy database, so point lookup queries run by scanning the entire list. Now a query starts, trying to look up dog. While the query is running, a writer proceeds more quickly and overwrites dog with b before the reader reaches it. The reader is still at chipmunk, but the writer already finished inserting dog,b:

![](https://artem.krylysov.com/images/2026-rocksdb-mvcc/list-rw.svg)

Should the reader see dog,b since it's the latest value inserted, or see dog,a because that was the value when the reader started the query? "Readers see a consistent view" clearly answers this - the reader should see dog,a.

Earlier I said the LSM-tree already does half of what's needed to implement MVCC, *half* because having immutable memtables and SSTs alone is not enough. You also need a way to provide readers a snapshot of the database, and the GC process needs some way of knowing which tables are being accessed by in-flight queries.

Internally, RocksDB assigns each inserted key a monotonically increasing number, which it calls a *sequence number*. When you insert a key into RocksDB, what actually gets into the memtable and SST files on disk is a triplet of *(user\_key, sequence\_number, value\_type)*, stored together with the value. The *user key* is the key you provided, the *sequence number* is a counter incremented on every write, and finally the *value type* is whether it's an insert or a delete (or other operations, which are irrelevant for this blog post).

With these, the updated representation of the list from the example before is:

![](https://artem.krylysov.com/images/2026-rocksdb-mvcc/list-seqnum.svg)

RocksDB tracks two sequence numbers - the *last allocated sequence* (the last number assigned on write), and the *published sequence* (the number visible to readers, advanced after a write completes).

In our example, the last allocated sequence number is 5 - the number that was assigned to dog,b. The published sequence when the reader R started was 4, and it will be 5 after the write completes.

When a read query starts, RocksDB captures the published sequence number. This sequence is then used for querying the memtables and the SSTs on disk. The reader R, when it sees dog,b with the sequence number 5, will skip over it, as it is allowed to see only keys with a sequence number of 4 or below.

> [!note] Note
> RocksDB is highly configurable. I'm describing the default configurations and behaviors with some simplifications to manage the complexity of this blog post.

The memtable implementation in RocksDB is not that far from our toy example. As in the example we used, it's based on a linked list, specifically on a [skip list](https://en.wikipedia.org/wiki/Skip_list). The data structure adds layers of links that allow fast search and insertion in sorted order:

![](https://artem.krylysov.com/images/2026-rocksdb-mvcc/skiplist.svg)

Layer 0 contains every entry - like the linked list from the example before. Each next layer contains a subset of the previous layer's entries. The search starts at the sparsest layer, descending to the full linked list. This structure gives O(log n) average time complexity for search.

When comparing internal keys, RocksDB first orders by the user-provided key ascending and then by the sequence number descending, so that when two keys share the same user key, the one with the larger sequence number comes first. A read query that captured the published sequence number 4 translates into a skip list seek to dog 4. The seek starts with cat 3 at layer 1, skips to dog 5 on layer 1, descends to dog 5 on layer 0 and finally lands on dog 1. The search can stop there since in the internal key order dog 4 is larger than dog 5, but smaller than dog 1. In Rust this could be expressed with the Ord trait this way:

```rust
impl Ord for InternalKey {
    fn cmp(&self, other: &Self) -> Ordering {
        if self.user_key == other.user_key {
            // Reversed - the larger sequence number comes first.
            other.sequence_number.cmp(&self.sequence_number)
        } else {
            self.user_key.cmp(&other.user_key)
        }
    }
}
```

The skip list in RocksDB is concurrent, meaning it doesn't require locking, so reads and writes can truly happen concurrently. The implementation uses atomic operations on pointers. Garbage collection in concurrent algorithms in non-GC languages is a hard problem, which RocksDB solves elegantly by relying on an [arena allocator](https://en.wikipedia.org/wiki/Region-based_memory_management) - individual entries are never freed, deletes are inserts with a DELETE value type and the memory for the entire memtable is freed after the memtable is no longer in use.

### Atomic Updates

The write batch API provides *atomicity* - keys written in the same batch become visible together:

```rust
let mut wb = WriteBatch::new();
wb.put("a", "1");
wb.put("b", "2");
wb.put("c", "3");
db.write(wb)?;
```

> [!note] Note
> RocksDB is written in C++. The code examples in this post are in Rust using the [rocksdb crate](https://crates.io/crates/rocksdb), a wrapper around the C API.

Atomicity becomes straightforward to implement with the key versioning and sequencing mechanism we discussed above. When the batch is applied to the database (the db.write call), sequence numbers for all keys are allocated atomically by incrementing the sequence number by 3 (the number of keys in the batch) and then publishing that number only after all three keys are inserted into the memtable. This ensures no reader can see a partial batch - they either see all three keys, or none of them.

### Snapshots

Every get implicitly captures the latest published sequence number. The snapshot API pins it explicitly, so multiple reads can see the database at the same point in time:

```rust
db.put("a", "1")?;
let snapshot = db.snapshot();
db.put("a", "2")?;
snapshot.get("a")?; // Returns "1" - the value at the time the snapshot was taken.
db.get("a")?; // Returns "2" - the latest value.
```

A snapshot is just the published sequence number recorded when db.snapshot() is called - reads through the snapshot skip keys with higher sequence numbers. RocksDB also registers the snapshot in a list of active snapshots. Compaction checks the list and drops an older version of a key only if no live snapshot can still see it.

### Versioning Tables

Going back to GC, older key versions are removed by compactions, but how does the database know when an SST file or a memtable is safe to delete? What if there is an in-flight reader still accessing an already flushed memtable, or reading an SST that compaction is supposed to remove?

RocksDB maintains a structure called SuperVersion, which is a reference-counted view of everything needed for reads:

```rust
struct SuperVersion {
    active_memtable: ReferenceCounter<Memtable>,          // memtable accepting writes
    immutable_memtables: Vec<ReferenceCounter<Memtable>>, // memtables ready to be flushed or just flushed
    ssts: ReferenceCounter<SstLevels>,                    // on-disk SSTs, each reference-counted individually
}
```

When a read starts, it acquires a reference to the structure. The reference is released only after the read is done. When the number of references to SuperVersion drops to zero, it releases its child fields, decrementing their reference counts. This way neither the structure itself nor any of its children can be freed mid-read. The cleanup - freeing the memtable memory or scheduling files for deletion is performed only when a child's own reference count reaches zero.

The Wikipedia definition of MVCC says it's a "non-locking concurrency control method". In the database literature there is a distinction between locks and latches. Locks are logical - over keys, key ranges, or rows. When a lock is held on a key, nobody else can modify it until the lock is released. Latches are physical, e.g. mutexes that protect the database structures from data races during concurrent access.

By this definition, the core of RocksDB doesn't take logical key locks, and the read and write paths are designed to not hold latches in the common hot cases. Some less frequently exercised code paths, however, do require latches - e.g. there is a coarse-grained per-DB mutex held briefly after a flush or compaction to replace the current SuperVersion.

### Transactions

Let's see how we can implement a classic balance transfer example with RocksDB, where Alice sends $10 to Bob:

```rust
// For simplicity, balances are stored as strings parsed to integers, e.g. "30" for $30.
let alice_balance = parse_balance(db.get("alice.balance")?); // $30
if alice_balance < 10 {
    return Err("not enough money".into());
}

let bob_balance = parse_balance(db.get("bob.balance")?); // $0

// Another writer sets Alice's balance to $40

db.put("alice.balance", (alice_balance - 10).to_string())?; // Set to $20
db.put("bob.balance", (bob_balance + 10).to_string())?; // Set to $10
```

Never do anything like this! The code snippet has major correctness issues when there is more than a single writer. Alice's balance should have been $30 (40 - 10), but ended up being set to $20 (30 - 10). $10 is lost because another concurrent writer modified Alice's balance between get and put calls.

Transactions exist to solve exactly this kind of problem by providing a way to execute a sequence of operations in isolation, detecting conflicts between concurrent writers. RocksDB builds a transactional layer on top of versioning. Writes are staged in the transaction buffer and get applied to the database only after the transaction commits. Reading from the uncommitted transaction merges the transaction buffer with the rest of the tree. This way transactions can read their own writes.

Transactions in RocksDB come in optimistic and pessimistic flavors. The pessimistic flavor checks for conflicts between transactions when updating a key - calling put or delete. In the optimistic flavor, conflict checks are moved to commit time. The API for both flavors looks the same - the flavor is picked when opening the database as either [TransactionDB](https://docs.rs/rocksdb/latest/rocksdb/struct.TransactionDB.html) or [OptimisticTransactionDB](https://docs.rs/rocksdb/latest/rocksdb/type.OptimisticTransactionDB.html):

```rust
let t1 = db.transaction();
t1.put("a", "1")?;
t1.get("a")?; // Returns "1" - the transaction reads its own uncommitted write.
t1.put("b", "1")?;
t1.put("c", "1")?;
t1.commit()?; // Updates to keys "a", "b" and "c" are applied to the memtable.
```

#### Pessimistic Transactions

When using pessimistic transactions, keys involved in write operations are locked to perform conflict detection - the lock manager puts each updated key in a per-DB map, associating it with the transaction ID.

```python
key_locks = {
    "a": T1,
    "b": T1,
    "c": T1,
}
```

If another transaction tries to update one of the locked keys concurrently, the conflicting transaction T2 blocks until T1 commits or rolls back - if that doesn't happen before the lock timeout, the operation returns an error:

```rust
let t2 = db.transaction();
// T1 has not committed yet.
t2.put("c", "2")?; // T2 is blocked waiting until it times out, or until T1 commits.
t2.put("d", "2")?;
// T1 committed.
t2.commit()?;
```

Locks are released when a transaction commits or rolls back. A third transaction, running at the same time as T1, but modifying a different set of keys, could proceed without being blocked.

> [!note] Note
> Blocking on locks means pessimistic transactions can deadlock - e.g. T1 waits for a key locked by T2, while T2 waits for a key locked by T1. With deadlock\_detect enabled, transactions check for wait cycles before blocking and return a deadlock error immediately instead of waiting. Detection is disabled by default - a deadlock resolves as a lock timeout.

By default, the conflict checks are done right when the operation is performed, which doesn't guarantee that no one else has updated the key since the transaction started:

```rust
let t1 = db.transaction();
{
    let t2 = db.transaction();
    t2.put("a", "2")?;
    t2.commit()?;
}
t1.put("a", "1")?; // Succeeds since T2 committed before this call.
t1.commit()?;
```

Setting a snapshot at the beginning of the transaction makes conflict detection catch updates made since the transaction started:

```rust
let mut opts = TransactionOptions::default();
// Setting a snapshot is the only difference compared to the previous example.
opts.set_snapshot(true);
let t1 = db.transaction_opt(&WriteOptions::default(), &opts);
{
    let t2 = db.transaction();
    t2.put("a", "2")?;
    t2.commit()?;
}
t1.put("a", "1")?; // Fails because T2 modified key "a" after the snapshot was set for T1.
t1.commit()?;
```

After T1 acquires a lock on key a, it checks whether the key was updated after the snapshot was set - whether there is a version of the key in the database with a sequence number higher than the snapshot sequence number. If there is, the write returns an error.

> [!note] Note
> I find this API confusing. set\_snapshot doesn't pin reads to the snapshot the same way as the snapshot API does. set\_snapshot only affects conflict detection.

#### Optimistic Transactions

Optimistic transactions don't check for conflicts on write operations, so put or delete never block or fail. Conflict checking happens on commits.

At a high level, commit-time validation is similar to how it's done in pessimistic transactions, but the implementation is more lightweight. Instead of tracking individual locked keys in a shared map, the lock manager hashes keys into [1M](https://github.com/facebook/rocksdb/blob/c9536aaef7815467f406ddf94cb2feeb772068f9/include/rocksdb/utilities/optimistic_transaction_db.h#L75) pre-allocated mutexes (yes, 1M is a lot - it trades off memory for reduced contention). Each operation on a key records the published sequence number at the time of the call.

While the mutexes are held for all keys involved in the commit, the transaction checks the memtable. If it contains a key with a sequence number larger than the recorded one, it means another transaction already committed the same key - the commit fails. The mutexes are released after all keys are validated and all updates are applied to the memtable.

Optimistic transactions limit validation to memtables (pessimistic transactions check the whole tree). If the memtable is flushed mid-transaction, there is nothing left to validate against, so the commit fails and the transaction has to be retried.

#### Mapping to Isolation Levels

Isolation levels in databases define semantics of concurrent access - what happens when two concurrent transactions access the same data. I'll cover the most common levels used in modern databases. In SQL databases you can set the isolation level explicitly per transaction. There is no similar high-level API in RocksDB, but you can build different levels yourself with lower-level APIs.

> [!note] Note
> The definitions of levels are fuzzy - academia and vendors often disagree on what each level implies. I'll try to stick close to Jepsen's [definitions](https://jepsen.io/consistency/models).

*Read uncommitted* - the lowest isolation level, where the only guarantee is that concurrent transactions won't physically corrupt the database. This permits *dirty reads* - a transaction seeing uncommitted data from another transaction. Impossible in RocksDB because transaction writes sit in a buffer that gets applied to the database atomically on commit.

*Read committed* - a transaction sees only committed data, including data committed by other transactions after it started. You get this with a plain db.get, or when transactions don't use snapshots for reads. Two consecutive gets can see different values mid-transaction:

```rust
db.put("a", "1")?;
let t1 = db.transaction();
t1.get("a")?; // Returns "1"
{
    let t2 = db.transaction();
    t2.put("a", "2")?;
    t2.commit()?;
}
t1.get("a")?; // Returns "2"
```

*Snapshot isolation* - all reads in the transaction see a consistent snapshot of the database, and the transaction succeeds only if no updates it made conflict with updates made by other transactions since the snapshot was created. Can be achieved by enabling snapshots for both reads and write conflict detection - set\_snapshot covers only conflict detection, and reads have to go through the transaction's snapshot(). You avoid non-repeatable reads, but the [write skew](https://jepsen.io/consistency/phenomena/a5b) anomaly is possible.

The snippet below illustrates the anomaly that happens when two transactions read the same data, then each updates a different key based on what it read. Alice has two bank accounts, $100 in each. The bank allows a single account to go negative, as long as the total across both accounts stays non-negative. Two concurrent transactions each withdraw $200 from a different account:

```rust
db.put("alice.checking", "100")?;
db.put("alice.savings", "100")?;

let mut opts = TransactionOptions::default();
opts.set_snapshot(true);

// T1 withdraws $200 from checking. T2 concurrently runs the same code,
// withdrawing $200 from savings.
let t1 = db.transaction_opt(&WriteOptions::default(), &opts);
let t2 = db.transaction_opt(&WriteOptions::default(), &opts);

let checking = parse_balance(t1.snapshot().get("alice.checking")?); // $100
let savings = parse_balance(t1.snapshot().get("alice.savings")?); // $100
if checking + savings - 200 >= 0 { // $100 + $100 - $200 = $0, the check passes.
    t1.put("alice.checking", (checking - 200).to_string())?; // Set to -$100.
}

// T2 passes the same check against its own snapshot and sets alice.savings to -$100.

// The transactions updated different keys, so conflict validation passes for both.
t1.commit()?;
t2.commit()?;

// Both accounts are now at -$100, the total is -$200.
```

*Serializable* - concurrent transactions run as if they were executed in serial order. You can get something close if you use get\_for\_update with *snapshot isolation* when transactions involve only point reads - you avoid dirty and non-repeatable reads and write skew. get\_for\_update is a special version of get used in transactions to avoid read-write conflicts e.g. when updating a key depends on the result of a read. get\_for\_update triggers conflict checks the same way as put and delete do. Here is the write skew example fixed by reading the balances with get\_for\_update, the rest of the code stays the same:

```rust
// Unlike snapshot reads, get_for_update reads participate in conflict detection.
let checking = parse_balance(t1.get_for_update("alice.checking", true)?); // $100
let savings = parse_balance(t1.get_for_update("alice.savings", true)?); // $100

// With pessimistic transactions, get_for_update blocks until it times out, then
// fails - the key is locked by T1. With optimistic transactions, the call
// succeeds and T2 aborts at commit.
t2.get_for_update("alice.checking", true)?;
```

The *phantom reads* anomaly is possible for transactions running range scans:

```rust
// Alice has a single account alice.checking.
db.put("alice.checking", "100")?;

let mut opts = TransactionOptions::default();
opts.set_snapshot(true);
let t1 = db.transaction_opt(&WriteOptions::default(), &opts);

// T1 computes the total across Alice's accounts, locking every key the scan returns.
let mut total = 0;
for item in t1.snapshot().iterator(IteratorMode::From(b"alice.", Direction::Forward)) {
    let (key, _) = item?;
    total += parse_balance(t1.get_for_update(key, true)?);
}
// total = $100.

// T2 opens a new account with a $50 deposit.
// The put doesn't conflict with T1 - T1 never read or locked alice.savings.
let t2 = db.transaction();
t2.put("alice.savings", "50")?;
t2.commit()?; // Succeeds.

t1.commit()?; // Succeeds.
```

T1 commits believing the total is $100, while Alice's accounts now hold $150. The new account is a phantom - get\_for\_update locked the keys the scan returned, but alice.savings didn't exist yet, so there was nothing to lock.

RocksDB has a [range lock manager](https://github.com/facebook/rocksdb/blob/865568398ab413806b527b650662bf08ea75eff1/include/rocksdb/utilities/transaction.h#L433) that locks key ranges instead of individual keys to prevent phantom reads. It was [contributed](https://github.com/facebook/rocksdb/pull/7506) in 2020, but it's not documented anywhere on the RocksDB wiki and not exposed through the C or Java APIs, so the feature is usable only from C++.

#### Fixing the Transfer

With all we learned we can finally fix the $10 transfer bug between Alice and Bob. Transactions (either pessimistic or optimistic) with a snapshot set, using get\_for\_update instead of plain get, are what we need - another transaction can't change a balance between the read and the write without triggering a conflict:

```rust
let mut opts = TransactionOptions::default();
opts.set_snapshot(true);
let tx = db.transaction_opt(&WriteOptions::default(), &opts);

let Ok(alice_balance) = tx.get_for_update("alice.balance", true) else {
    // Can happen with pessimistic transactions.
    return Err("another transaction updated Alice's balance".into());
};
let alice_balance = parse_balance(alice_balance);
if alice_balance < 10 {
    return Err("not enough money".into());
}

let Ok(bob_balance) = tx.get_for_update("bob.balance", true) else {
    // Can happen with pessimistic transactions.
    return Err("another transaction updated Bob's balance".into());
};
let bob_balance = parse_balance(bob_balance);

tx.put("alice.balance", (alice_balance - 10).to_string())?;
tx.put("bob.balance", (bob_balance + 10).to_string())?;

if tx.commit().is_err() {
    // Can happen with optimistic transactions.
    return Err("another transaction updated Bob's or Alice's balance or the memtable was flushed".into());
}
```

#### Optimistic vs Pessimistic Performance

From the user perspective, the only difference between pessimistic and optimistic transactions is where a transaction can abort on a conflict. Pessimistic transactions acquire locks on every write operation and abort early on conflicts (after exceeding the lock timeout). Optimistic transactions require no per-key locks on writes - coarse-grained locks are taken for the duration of a commit. Optimistic transactions typically provide higher throughput on workloads where conflicts between transactions are rare and where retrying the entire transaction on a conflict is cheap.

I benchmarked two workloads (source code is [here](https://github.com/akrylysov/rocksdb-txn-bench)) - one where pessimistic transactions win and one where optimistic transactions win.

In the "mostly read" workload, every transaction reads a shared key with get\_for\_update and writes a unique key - roughly one transaction in 1024 replaces the shared key instead. Starting from 2 threads, the throughput of optimistic transactions stays flat, while pessimistic transactions queue on the shared key's lock:

![](https://artem.krylysov.com/images/2026-rocksdb-mvcc/benchmark-mostly-read.png)

In the "contended key" workload, every transaction reads the same key with get\_for\_update, does CPU-bound work and writes the key back. Pessimistic transactions wait on the lock without consuming CPU, so the work runs once per commit. Optimistic transactions discover the conflict only at commit, after the work is done, redoing the expensive work on retry:

![](https://artem.krylysov.com/images/2026-rocksdb-mvcc/benchmark-contended-key.png)

#### Who Uses RocksDB-native Transactions

[MyRocks](https://github.com/facebook/mysql-5.6) - the MySQL storage engine built on RocksDB, and [ArangoDB](https://github.com/arangodb/arangodb) are the only large projects I'm aware of that rely on RocksDB transactions. Facebook's MyRocks repository was archived on GitHub on Mar 1, 2026, but the engine is still available as a part of [MariaDB](https://github.com/MariaDB/server/tree/main/storage/rocksdb) or [Percona Server](https://github.com/percona/percona-server/tree/8.4/storage/rocksdb).

TiDB/TiKV and YugabyteDB, which run on RocksDB, don't use RocksDB-native transactions. CockroachDB's [RocksDB-inspired](https://github.com/cockroachdb/pebble) key-value store Pebble doesn't support transactions at all. TiDB, YugabyteDB and CockroachDB implement their own distributed transactional layer above the key-value stores. The reason for this is that RocksDB-native transactions are node-local, i.e. the locks are held per key-value store instance running on a single node, and with a distributed database you have to coordinate transactions across multiple nodes.

### Conclusion

While LSM-trees give half of MVCC for free, there is a lot of practical complexity in implementing the other half. Concurrent algorithms are hard to get right, and making them efficient requires low-level techniques like using atomic operations on pointers. If you are implementing a database from scratch (I hope this blog post convinces you not to do that!), you are on your own with these techniques - in Rust, code built on raw pointers gets no protection from the borrow checker, and even memory-safe concurrent code paths covered entirely by the borrow checker are not free from logical races. The hard part is the concurrency, not the MVCC itself. Snapshots, atomic batches and conflict detection in both transaction flavors all come down to the same primitive - comparing sequence numbers.
