---
title: "JOIN Algorithms"
source: "https://arpitbhayani.me/blogs/join-algorithms"
author:
  - "[[Arpit Bhayani]]"
published: 2026-02-24
created: 2026-02-26
description: "When you write a SQL query with a JOIN clause, you probably do not think much about what happens next. You just expect the database to return the right rows. But this simple keyword forces your database to make one of the most consequential decisions a query planner makes: which join algorithm should it use?"
tags:
  - "clippings"
---

> [!summary]
> Detailed walkthrough of 6 SQL join algorithms — Nested Loop, Hash, Merge (Sort-Merge), Index (Indexed Nested Loop), Grace Hash, and Broadcast — with Go pseudocode, time/IO complexity analysis, and guidance on when each algorithm shines or struggles. Also covers how query planners choose between them.

![](https://edge.arpitbhayani.me/img/arpit-6.jpg)

[Arpit Bhayani](https://arpitbhayani.me/)

engineering, databases, and systems. always building.

When you write a SQL query with a [JOIN clause](https://en.wikipedia.org/wiki/Join_\(SQL\)), you probably do not think much about what happens next. You just expect the database to return the right rows. But this simple keyword forces your database to make one of the most consequential decisions a query planner makes: which join algorithm should it use?

The choice matters a ton. A bad join algorithm on a large dataset can turn a millisecond query into a minutes-long. A good one can make joining two tables with billions of rows feel effortless.

This write-up covers the join algorithms that power every major relational database, why each one exists, when to use each, and what tradeoffs you are making when you pick one over another. The write-up will cover

- Nested Loop Join
- Hash Join
- Merge Join (Sort-Merge Join)
- Index Join (Indexed Nested Loop Join)
- Grace Hash Join, and
- Broadcast Join

## Pre-requisites

Before diving in, you should be comfortable with:

- Basic SQL and what a JOIN operation conceptually means
- How [tables are stored on disk](https://youtu.be/09E-tVAUqQw?si=n2Fc2seo0YKX3iHB) and the difference between sequential and random I/O
- What an index is and [how a B-tree index works](https://youtu.be/3G293is403I?si=kQLLxyA2YbEqVxZu) at a high level

## Why Join Algorithms Exist

A join is conceptually simple. Given two tables `R` and `S`, find all pairs of rows `(r, s)` where `r.key` = `s.key`. The naive way to do this is to compare every row in `R` with every row in `S`. That is `O(|R| * |S|)` comparisons.

Join algorithms are strategies to avoid doing all those comparisons when a set of conditions is met. These algorithms, like any other, exploit structure and patterns. Join algorithms exploit - sorting, hashing, indexing, or partitioning to drastically reduce the search space.

Let us go through each one.

## Nested Loop Join

This is the most intuitive join algorithm. For every row in the outer table, scan the entire inner table looking for matches.

```go
// Pseudocode: Nested Loop Join

func nestedLoopJoin(outer []Row, inner []Row, predicate func(Row, Row) bool) []Row {

    var result []Row

    for _, outerRow := range outer {

        for _, innerRow := range inner {

            if predicate(outerRow, innerRow) {

                result = append(result, merge(outerRow, innerRow))

            }

        }

    }

    return result

}
```

This is `O(|R| * |S|)` in time complexity. For two tables with a million rows each, that is a trillion comparisons. Not good.

By the way, nested loop join is not completely useless. It is actually the algorithm of choice in several real scenarios. Here’s where it shines

- When the outer table has very few rows, the inner table gets scanned only that many times — so even if the inner table is huge, the total work stays small. (explained below)
- When there is no useful index, sort order, or hash-friendly key available. So, nested loop join becomes the default fallback approach.

### Why Smaller Outer and Larger Inner Is Preferred

In a nested loop join, the outer table controls how many times the inner table is scanned (as seen in the pseudocode). If the outer table has 5 rows, you scan the inner table exactly 5 times. If the outer table has 1 million rows, you scan the inner table 1 million times.

Now, the total number of comparisons is the same either way — 5 \* 1M is the same as 1M \* 5. So why does it matter which side is outer?

It comes down to I/O, not computation.

Every time the inner loop restarts, the database has to read the inner table again. If the inner table does not fit in the buffer pool (in-memory cache), those reads hit disk. Disk reads are orders of magnitude slower than memory reads. So the fewer times you restart the inner scan, the fewer expensive disk reads you pay for.

When the outer table is small, the inner table gets re-read only a handful of times. The first scan loads most of the inner table into the buffer pool, and subsequent scans are largely served from cache. When the outer table is large, the buffer pool gets thrashed — pages loaded for one outer row get evicted before the next outer row can reuse them.

So the rule of thumb is: put the smaller table on the outside to minimize the number of inner scans, and let the buffer pool do its job of caching the inner table across those few passes.

This is also why the block nested loop join optimization exists. Let’s dig in …

### Block Nested Loop Join

The main optimization in practice is Block Nested Loop Join. Instead of reading one row at a time from the outer table, you load a chunk (block) of outer rows into memory, then scan the inner table once for that entire chunk.

```go
// Pseudocode: Block Nested Loop Join

func blockNestedLoopJoin(outer []Row, inner []Row, blockSize int, predicate func(Row, Row) bool) []Row {

    var result []Row

    for i := 0; i < len(outer); i += blockSize {

        block := outer[i:min(i+blockSize, len(outer))]

        // build an in-memory lookup for this block

        lookup := buildLookup(block)

        for _, innerRow := range inner {

            if matches := lookup.find(innerRow); len(matches) > 0 {

                for _, outerRow := range matches {

                    if predicate(outerRow, innerRow) {

                        result = append(result, merge(outerRow, innerRow))

                    }

                }

            }

        }

    }

    return result

}
```

With `B` buffer pages available, you can load `B-2` pages of the outer table at a time (leaving one page for the inner scan and one for output). This reduces the number of times you scan the inner table from `|R|` to `ceil(|R| / (B-2))`. If the outer table fits entirely in memory, you only scan the inner table once. That is a huge win.

By the way, PostgreSQL uses nested loop join heavily when one side of the join is small or when it can combine it with an index on the inner table (which leads us to Index Join later).

## Hash Join

Hash join is actually one of the most widely used join algorithms. The idea is to build a hash table from one of the two relations, then probe it using the other (similar, not the same, to what we did in Block Nested Loop Join)

There are two phases:

Phase 1 (Build): Scan the smaller relation (the build side). For every row, compute a hash of the join key and insert the row into a hash table in memory.

Phase 2 (Probe): Scan the larger relation (the probe side). For every row, compute the same hash of the join key and look it up in the hash table. Emit matching pairs.

```go
// Pseudocode: Hash Join

func hashJoin(small []Row, large []Row, keyFn func(Row) any) []Row {

    // Phase 1: build

    hashTable := make(map[any][]Row)

    for _, row := range small {

        key := keyFn(row)

        hashTable[key] = append(hashTable[key], row)

    }

    // Phase 2: probe

    var result []Row

    for _, row := range large {

        key := keyFn(row)

        if matches, ok := hashTable[key]; ok {

            for _, srow := range matches {

                result = append(result, merge(srow, row))

            }

        }

    }

    return result

}
```

Time complexity is `O(|R| + |S|)` — linear in the size of both tables. This is dramatically better than a nested loop join for large tables.

The catch? The build phase requires the hash table to fit in memory. If the smaller relation is 500MB and you only have 256MB of RAM, you are in trouble. This is where Grace Hash Join (covered later) comes in.

When does hash join shine?

- Large equijoins with no useful sort order or index
- When the build side (smaller table) fits in memory
- When the query planner estimates high cardinality on both sides

When does it struggle?

- Non-equijoins: you cannot hash on `>` or `BETWEEN` predicates
- Skewed data: if many rows share the same key (think NULL values, or a status column with 99% of rows being “active”), your hash buckets become unbalanced, and performance degrades
- Memory pressure: if the build side does not fit in memory, the database has to spill to disk or switch strategies

PostgreSQL, MySQL (since 8.0), SQL Server, and virtually every other major database support hash join. In PostgreSQL, you can see it in query plans as a `Hash Join` with a `Hash` node underneath.

## Merge Join (Sort-Merge Join)

Merge join exploits sorted order. If both relations are sorted on the join key, you can merge them in a single linear pass — similar to the merge step in [merge sort](https://en.wikipedia.org/wiki/Merge_sort).

The core idea is to maintain a pointer into each sorted relation. At each step, compare the current rows. If they match, emit the result and advance. If one is smaller, advance that pointer. Repeat until one relation is exhausted.

```go
// Pseudocode: Sort-Merge Join

func sortMergeJoin(left []Row, right []Row, keyFn func(Row) int) []Row {

    // assume both are sorted on keyFn

    var result []Row

    i, j := 0, 0

    for i < len(left) && j < len(right) {

        lKey, rKey := keyFn(left[i]), keyFn(right[j])

        switch {

        case lKey == rKey:

            // handle duplicates: collect all matching rows from right

            jStart := j

            for j < len(right) && keyFn(right[j]) == lKey {

                result = append(result, merge(left[i], right[j]))

                j++

            }

            i++

            // if left also has duplicates, rewind right pointer

            if i < len(left) && keyFn(left[i]) == lKey {

                j = jStart

            }

        case lKey < rKey:

            i++

        default:

            j++

        }

    }

    return result

}
```

If the data is already sorted, merge join is `O(|R| + |S|)`. If it is not sorted, you pay `O(|R| log |R| + |S| log |S|)` for the sort step upfront. That sorting cost is the key tradeoff.

When does merge join shine?

- When both relations are already sorted on the join key (e.g., both have a clustered index on the join column)
- When you need the output in sorted order anyway (the sort is “free” from the planner’s perspective)
- Large equijoins where neither relation fits comfortably in memory for hashing
- Range joins (e.g., `r.date BETWEEN s.start AND s.end`) can sometimes use a variation of the merge join

When does it struggle?

- When neither side is pre-sorted, and the sort cost is high
- When join keys have many duplicates, the rewinding of the right pointer can cause quadratic behavior in degenerate cases
- When data arrives in streaming fashion (though external sort-merge can help)

A key advantage of merge join over hash join is that it handles memory gracefully. Sorting can be done in chunks and merged externally; you do not need to hold the entire build side in memory at once.

PostgreSQL, Oracle, and SQL Server all support merge join. You will see it in PostgreSQL query plans as `Merge Join`.

## Index Join (Indexed Nested Loop Join)

Index join is a specialized form of nested loop join where the inner table has an index on the join key. Instead of scanning the entire inner table for each outer row, you do an index lookup, which is typically O(log n) or even O(1) for hash indexes.

```go
// Pseudocode: Index Nested Loop Join

func indexNestedLoopJoin(outer []Row, innerIndex Index, keyFn func(Row) any) []Row {

    var result []Row

    for _, outerRow := range outer {

        key := keyFn(outerRow)

        // index lookup instead of full scan

        matchingInnerRows := innerIndex.Lookup(key)

        for _, innerRow := range matchingInnerRows {

            result = append(result, merge(outerRow, innerRow))

        }

    }

    return result

}
```

The time complexity is `O(|R| * log|S|)` when using a B-tree index, or `O(|R|)` amortized for a hash index (ignoring collisions). Compared to the `O(|R| * |S|)` of plain nested loop join, this is a massive improvement.

Here, the index turned the inner scan into a seek. Instead of reading every page of the inner table, you jump directly to the relevant rows.

This algorithm is also I/O-friendly in a subtle way. If the outer table is accessed in order of the inner index key, you get sequential-ish access patterns on the inner table, which is cache-friendly.

When does a index join shine?

- When the inner table has an index on the join key
- When the outer table is small (fewer rows = fewer index lookups)
- When the join is highly selective (few rows match per outer row)
- Point lookups or equality joins

When does it struggle?

- When the outer table is large, and the inner table index has poor selectivity, you end up doing many random I/Os, which can be slower than a full sequential scan
- When there is no index on the join key, (then it degrades to a plain nested loop join)
- For range predicates, B-tree indexes help, but performance depends heavily on the range width

## Grace Hash Join

Grace hash join solves the problem that regular hash join has: what happens when the build side does not fit in memory? The algorithm has two phases, both using partitioning:

Phase 1 (Partitioning): Partition both `R` and `S` into `k` buckets using the same hash function `h1`. All rows with the same join key will end up in the same partition pair `(R_i, S_i)` on disk. This requires two sequential passes over both relations.

Phase 2 (Probing): For each partition pair `(R_i, S_i)`, load `R_i` into memory, build a hash table using a second hash function `h2`, then probe it with `S_i`. Since partitions are smaller than the original tables, each one should now fit in memory.

```go
// Pseudocode: Grace Hash Join

func graceHashJoin(R []Row, S []Row, numPartitions int, keyFn func(Row) any) []Row {

    // Phase 1: partition both relations to disk

    rPartitions := make([][]Row, numPartitions)

    sPartitions := make([][]Row, numPartitions)

    for _, row := range R {

        bucket := hash1(keyFn(row)) % numPartitions

        rPartitions[bucket] = append(rPartitions[bucket], row)

    }

    for _, row := range S {

        bucket := hash1(keyFn(row)) % numPartitions

        sPartitions[bucket] = append(sPartitions[bucket], row)

    }

    // Phase 2: for each partition pair, do an in-memory hash join

    var result []Row

    for i := 0; i < numPartitions; i++ {

        // build hash table from R partition (should fit in memory now)

        hashTable := make(map[any][]Row)

        for _, row := range rPartitions[i] {

            key := keyFn(row)

            hashTable[key] = append(hashTable[key], row)

        }

        // probe with S partition

        for _, row := range sPartitions[i] {

            key := keyFn(row)

            if matches, ok := hashTable[key]; ok {

                for _, rRow := range matches {

                    result = append(result, merge(rRow, row))

                }

            }

        }

    }

    return result

}
```

The I/O cost of Grace Hash Join is `3 * (|R| + |S|)` page reads and writes: one pass to partition, and one pass to join each partition pair. This is competitive with sort-merge join and significantly better than naive nested loop join.

The number of partitions `k` needs to be chosen carefully. If you have `B` buffer pages available, you need at least `sqrt(|R|)` partitions so that each `R` partition fits in `B` pages during the probe phase. A common rule of thumb is `k = ceil(sqrt(|R| / B))`.

When does Grace Hash Join shine?

- Large equijoins where neither side fits in memory
- When data has no useful sort order
- Parallel and distributed settings where partitioning can happen across nodes

When does it struggle?

- Skewed data with many duplicate join keys (one partition becomes huge, causing recursive partitioning)
- When I/O is expensive (it writes everything to disk and reads it back)
- For very small tables, a simple hash join or a nested loop is cheaper due to lower overhead

Most production databases implement Grace Hash Join (or a variant of it) as their fallback when regular in-memory hash join runs out of memory. PostgreSQL calls this “hash join with batches” — you can see the number of batches in the `EXPLAIN ANALYZE` output. If batches > 1, it has spilled to disk.

## Broadcast Join

Broadcast join exists primarily in distributed databases and query engines (like [Apache Spark](https://spark.apache.org/), [Presto](https://prestodb.io/), Google BigQuery, Snowflake, etc.). It is not a new join algorithm in the computational sense — it combines with any of the above — but it addresses a specific problem in distributed systems: how do you join two tables that live across many nodes?

The idea is simple - If one of the two relations is small enough, send (broadcast) a complete copy of it to every single node in the cluster. Then each node independently joins its local partition of the large table with the full copy of the small table, using any local join algorithm (usually hash join).

```go
// Pseudocode: Broadcast Join (distributed)

func broadcastJoin(smallTable []Row, largeTablePartitions [][]Row, keyFn func(Row) any) []Row {

    // coordinator broadcasts smallTable to all worker nodes

    broadcastSmallTable(smallTable) // network operation

    var result []Row

    // each worker node independently runs a local hash join

    for _, partition := range largeTablePartitions {

        localResult := hashJoin(smallTable, partition, keyFn) // local join

        result = append(result, localResult...)

    }

    return result

}
```

By broadcasting the small table, you avoid shuffling (repartitioning) the large table across the network. Network shuffles are often the most expensive operation — they involve serialization, network transfer, deserialization, and disk I/O. Broadcast eliminates all of that for the large table.

- Broadcast cost: send the small table to all N nodes. If the small table is `S` bytes, that is `O(N * S)` network transfer.
- Join cost: each node does a local hash join on its partition of the large table.
- No shuffle of the large table.

Compare this to a shuffle join (also called a partitioned hash join or repartition join): both tables are shuffled so that rows with the same key end up on the same node. Cost is `O(|R| + |S|)` in network transfer, but this scales with the size of both tables.

Broadcast join wins when: `N * |small| << |large|`. In other words, when the small table is small enough that broadcasting it everywhere is cheaper than shuffling the large table.

When does broadcast join shine?

- One table is significantly smaller than the other
- The large table is already partitioned across nodes, and you want to avoid reshuffling it
- Low-latency, high-throughput analytical queries where the small table fits in memory on each node

When does it struggle?

- When the “small” table is not actually that small — broadcasting a 10GB table to 1000 nodes means 10TB of network transfer
- When the cluster has limited network bandwidth
- When the small table changes frequently (broadcasting is a snapshot; you need to re-broadcast on updates)

## How Databases Choose Between Algorithms

The query planner does not pick join algorithms randomly. It uses cost-based optimization: it estimates the cost of each candidate plan and picks the cheapest one.

The key inputs to this decision are:

- Table cardinality
- Working memory limit for this query
- Indexes on the join keys
- Sort order of the join key
- Join predicate type - equality, range, etc
- Cluster topology - single-node or distributed execution

## Conclusion

Join algorithms are a foundational piece of database internals, and understanding them is important when you are debugging slow queries, designing schemas, or evaluating distributed systems.

The key takeaways are

- Nested loop join is simple and flexible, but expensive for large tables; it becomes powerful when combined with an index.
- Hash join is the most common join, and it suits large equijoins in memory.
- Merge join excels when data is pre-sorted and handles disk gracefully.
- Grace Hash Join extends hash join to handle data that does not fit in memory by partitioning both relations to disk first.
- Broadcast join is the go-to strategy in distributed systems when one table is small enough to replicate to every node.

---

![Arpit Bhayani](https://edge.arpitbhayani.me/img/arpit-6.jpg)

Ex-staff engg at GCP Memorystore & Dataproc, Creator of [DiceDB](https://github.com/dicedb/dice), ex-Amazon Fast Data, ex-Director of Engg. SRE and Data Engineering at Unacademy. I spark engineering curiosity through my no-fluff engineering videos on [YouTube](https://www.youtube.com/c/ArpitBhayani) and my courses

- [System Design Masterclass](https://arpitbhayani.me/masterclass)
- [System Design for Beginners](https://arpitbhayani.me/system-design-for-beginners)
- [Redis Internals](https://arpitbhayani.me/redis-internals)
