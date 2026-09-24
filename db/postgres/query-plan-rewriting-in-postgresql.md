---
title: "Query plan rewriting in PostgreSQL"
source: "https://theconsensus.dev/p/2026/09/13/query-plan-rewriting-in-postgresql.html"
author:
  - "[[Phil Eaton]]"
published: 2026-09-13
created: 2026-09-21
description: "We take a look at some of the ways PostgreSQL rewrites your queries (or not)."
tags:
  - "clippings"
---

> [!summary]
> Phil Eaton uses `EXPLAIN` on PostgreSQL 18 to probe which static query rewrites the planner does and doesn't perform: constant folding (for IMMUTABLE and simple SQL functions, but not `0 + col`), subquery flattening, filter pushdown into subqueries and joins, LEFT JOIN and self-join elimination, and turning IN/EXISTS/NOT EXISTS into semi and anti joins. The gaps are just as instructive: NOT IN isn't rewritten because of its NULL semantics, an inner join isn't eliminated even when an FK guarantees a match, and `min()` with `GROUP BY` can't use the index. A follow-up article covers the statistics-driven optimizer.

You are getting early access to this article as a subscriber. Your support makes articles like this possible. Thank you.

A query plan is an abstract representation of operations on data such as scanning rows on disk, scanning an index, applying a filter, selecting a subset of columns, joining two tables, and operating on a column. To get to a query plan, a database parses your SQL query into an Abstract Syntax Tree (AST) and then resolves identifiers into a query plan.

Within the database, the query planner is responsible for rewriting and optimizing the query plan: folding constants, deciding which index to use (if any), deciding which table to scan first, deciding the type of join to do, etc. I'm using the term *rewriting* to mean the things that are statically knowable (e.g. `i+0` is the same as `i`) versus *optimizing* which are things that require checking statistics or other data-specific knowledge.

While every database has a query planner, and while they do similar things, knowledge about one database's query planner doesn't translate well to knowledge of another database's query planner. In this article we'll take a look at query plan rewriting that PostgreSQL does (and does not). Which will set us up to talk about query plan optimization that PostgreSQL does (and does not) in another article.

First, grab PostgreSQL 18.

```
sudo apt-get update -y
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
sudo apt update -y
sudo apt install -y postgresql-18
```

And let's set up two small tables for us to play around with.

```
DROP TABLE IF EXISTS users;
CREATE TABLE users (user_id INT PRIMARY KEY, user_name TEXT);
INSERT INTO users
  SELECT i, substring(md5(random()::text), 1, 12)
  FROM generate_series(1, 200_000) as i;

DROP TABLE IF EXISTS orders;
CREATE TABLE orders (order_id INT PRIMARY KEY, order_user_id INT, order_status TEXT);
INSERT INTO orders
  SELECT i, 1 + (i % 200_000), (ARRAY['paid', 'shipped', 'delivered'])[1+i%3]
  FROM generate_series(1,500_000) i;
VACUUM ANALYZE users;
VACUUM ANALYZE orders;
```

/tmp/init.sql

We run VACUUM ANALYZE to see stable-state query plans below.

Give it a run and then let's dig in.

```
$ sudo -u postgres psql -f /tmp/init.sql
DROP TABLE
CREATE TABLE
INSERT 0 200000
DROP TABLE
CREATE TABLE
INSERT 0 500000
VACUUM
VACUUM
```

## Constant folding

One of the very first topics you learn about in any compiler class is constant folding. If you have an AST sub-tree that is `+ 3 4` (so you've got at least three nodes there) you can rewrite the tree into a single node `7`. You've saved runtime work by evaluating part of the tree during the compilation step.

PostgreSQL is happy to do it.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users WHERE user_id = 100 + 100" | sudo -u postgres psql
             QUERY PLAN
--------------------------------------
 Index Scan using users_pkey on users
   Index Cond: (user_id = 200)
(2 rows)
```

Just as if you had passed in `200`.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users WHERE user_id = 200" | sudo -u postgres psql
              QUERY PLAN
--------------------------------------
 Index Scan using users_pkey on users
   Index Cond: (user_id = 200)
(2 rows)

$  echo "EXPLAIN (COSTS OFF) SELECT * FROM users WHERE 200 = user_id" | sudo -u postgres psql
              QUERY PLAN
--------------------------------------
 Index Scan using users_pkey on users
   Index Cond: (user_id = 200)
(2 rows)
```

And it doesn't matter which side the column is on.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users WHERE 100 + 100 = user_id" | sudo -u postgres psql
              QUERY PLAN
--------------------------------------
 Index Scan using users_pkey on users
   Index Cond: (user_id = 200)
(2 rows)
```

At least, so long as the addition is on the constant side. Otherwise we've lost both the constant folding and the index.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users WHERE user_id + 0 = 100" | sudo -u postgres psql
             QUERY PLAN
---------------------------------------
 Gather
   Workers Planned: 1
   ->  Parallel Seq Scan on users
         Filter: ((user_id + 0) = 100)
(4 rows)
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users WHERE 100 = user_id + 0" | sudo -u postgres psql
              QUERY PLAN
---------------------------------------
 Gather
   Workers Planned: 1
   ->  Parallel Seq Scan on users
         Filter: (100 = (user_id + 0))
(4 rows)
```

And ok yeah zero-folding is a bit of an edge case. And sure, we don't want to subtract the value from both sides, I guess. We do know we must index expressions in PostgreSQL if we want the index to be picked up by the planner. So let's add one.

```
$ echo "CREATE INDEX ON users ((user_id + 0)); VACUUM ANALYZE users;" | sudo -u postgres psql
CREATE INDEX
VACUUM
```

And it works.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users WHERE user_id + 0 = 100" | sudo -u postgres psql
               QUERY PLAN
------------------------------------------
 Index Scan using users_expr_idx on users
   Index Cond: ((user_id + 0) = 100)
(2 rows)
```

But not if we reorder the operations. Despite addition being commutative, we get kicked off the index scan.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users WHERE 0 + user_id = 100" | sudo -u postgres psql
             QUERY PLAN
---------------------------------------
 Gather
   Workers Planned: 1
   ->  Parallel Seq Scan on users
         Filter: ((0 + user_id) = 100)
(4 rows)
```

When it comes to functions, it will constant-fold them if the function is marked [IMMUTABLE](https://www.postgresql.org/docs/current/xfunc-volatility.html?utm_source=theconsensus.dev&utm_medium=referral#:~:text=An%20IMMUTABLE%20function,marked%20IMMUTABLE.) (and its arguments are immutable or constant).

```
$ echo "CREATE FUNCTION double(int) RETURNS int AS \$\$
  BEGIN RETURN \$1 * 2;
END \$\$ LANGUAGE plpgsql IMMUTABLE;" | sudo -u postgres psql
CREATE FUNCTION
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users WHERE user_id = double(100)" | sudo -u postgres psql
              QUERY PLAN
--------------------------------------
 Index Scan using users_pkey on users
   Index Cond: (user_id = 200)
(2 rows)
```

Or if the function is `sql` and [sufficiently simple](https://theconsensus.dev/project/postgresql/source/REL_18_6/src/backend/optimizer/util/clauses.c#L-4552).

```
$ echo "CREATE FUNCTION triple(int) RETURNS int AS 'SELECT \$1 * 3' LANGUAGE sql" | sudo -u postgres psql
CREATE FUNCTION
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users WHERE user_id = triple(100)" | sudo -u postgres psql
              QUERY PLAN
--------------------------------------
 Index Scan using users_pkey on users
   Index Cond: (user_id = 300)
(2 rows)
```

The index will still be chosen if the function is not immutable but [STABLE](https://www.postgresql.org/docs/current/xfunc-volatility.html?utm_source=theconsensus.dev&utm_medium=referral#:~:text=A%20STABLE%20function,index%20scan%20condition.) (like `now()`, whose result is determined [once](https://www.postgresql.org/docs/18/functions-datetime.html?utm_source=theconsensus.dev&utm_medium=referral#:~:text=transaction_timestamp%28%29%20is,to%20transaction_timestamp%28%29.) at transaction start). But it will not be constant-folded.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users WHERE 100 + EXTRACT(DAY FROM NOW())::INT = user_id" | sudo -u postgres psql
                              QUERY PLAN
----------------------------------------------------------------------
 Index Scan using users_pkey on users
   Index Cond: (user_id = (100 + (EXTRACT(day FROM now()))::integer))
(2 rows)
```

Which again is separate from not picking the index when the expression is [VOLATILE](https://www.postgresql.org/docs/current/xfunc-volatility.html?utm_source=theconsensus.dev&utm_medium=referral#:~:text=A%20VOLATILE%20function,value%20is%20needed.) or depends on the row.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users WHERE length(user_name) = user_id" | sudo -u postgres psql
                  QUERY PLAN
-----------------------------------------------
 Gather
   Workers Planned: 1
   ->  Parallel Seq Scan on users
         Filter: (length(user_name) = user_id)
(4 rows)
```

Let's move on.

## Flattening subqueries and filter pushdown

When a subquery is sufficiently simple, Postgres will just collapse the queries into one.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM (SELECT user_id, length(user_name) AS n FROM users) x WHERE x.user_id = 42;" | sudo -u postgres psql
              QUERY PLAN
--------------------------------------
 Index Scan using users_pkey on users
   Index Cond: (user_id = 42)
(2 rows)
```

But not in situations where it would no longer be an equivalent query, such as when there's a LIMIT in the subquery.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM (SELECT user_id, length(user_name) AS l FROM users LIMIT 3) u WHERE u.user_id = 100;" | sudo -u postgres psql
         QUERY PLAN
-------------------------------
 Subquery Scan on u
   Filter: (u.user_id = 100)
   ->  Limit
         ->  Seq Scan on users
(4 rows)
```

In case that's not intuitive, here's what the original query is and what the wrong rewrite would be.

```
$ echo "SELECT count(1) FROM (SELECT user_id, length(user_name) AS l FROM users LIMIT 3) u WHERE u.user_id = 100;" | sudo -u postgres psql
 count
-------
     0
(1 row)
$ echo "SELECT count(1) FROM (SELECT user_id, length(user_name) AS l FROM users WHERE user_id = 100 LIMIT 3) u WHERE u.user_id = 100;" | sudo -u postgres psql
 count
-------
     1
(1 row)
```

In more complex queries, it will try to push filters down.

```
$ echo "
EXPLAIN (COSTS OFF)
SELECT * FROM (
  SELECT order_user_id, count(*) AS orders
  FROM orders GROUP BY order_user_id) s
WHERE s.order_user_id = 100;" | sudo -u postgres psql
                    QUERY PLAN
---------------------------------------------------
 Finalize GroupAggregate
   ->  Gather
         Workers Planned: 1
         ->  Partial GroupAggregate
               ->  Parallel Seq Scan on orders
                     Filter: (order_user_id = 100)
(6 rows)
```

And not just on equality.

```
$ echo "
EXPLAIN (COSTS OFF)
SELECT * FROM (
  SELECT order_user_id, count(*) AS orders
  FROM orders GROUP BY order_user_id) s
WHERE s.order_user_id > 100;" | sudo -u postgres psql
              QUERY PLAN
---------------------------------------
 HashAggregate
   Group Key: orders.order_user_id
   ->  Seq Scan on orders
         Filter: (order_user_id > 100)
(4 rows)
```

Which is pretty cool.

Now let's take a brief detour to remind ourselves about two basic join types and PostgreSQL's strategies for implementing them.

## Joins

`JOIN` is an inner join which requires both sides to match the condition. `LEFT JOIN` is an outer join which keeps every row on the left of the join whether or not the join condition is met and fills the right side with `NULL` if there is no match for the left.

PostgreSQL has three [join strategies](https://www.postgresql.org/docs/current/planner-optimizer.html?utm_source=theconsensus.dev&utm_medium=referral#PLANNER-OPTIMIZER-GENERATING-POSSIBLE-PLANS). The docs are pretty good here so I'll let them speak.

For nested loop joins:

> The right relation is scanned once for every row found in the left relation. This strategy is easy to implement but can be very time consuming. (However, if the right relation can be scanned with an index scan, this can be a good strategy. It is possible to use values from the current row of the left relation as keys for the index scan of the right.)

For merge joins:

> Each relation is sorted on the join attributes before the join starts. Then the two relations are scanned in parallel, and matching rows are combined to form join rows. This kind of join is attractive because each relation has to be scanned only once. The required sorting might be achieved either by an explicit sort step, or by scanning the relation in the proper order using an index on the join key.

And for hash joins:

> The right relation is first scanned and loaded into a hash table, using its join attributes as hash keys. Next the left relation is scanned and the appropriate values of every row found are used as hash keys to locate the matching rows in the table.

So if the EXPLAIN output says `Hash Left Join` it's a left join executed as a hash join.

And there are two more terms you'll see in EXPLAIN output: [semi and anti joins](https://theconsensus.dev/project/postgresql/source/REL_18_6/src/include/nodes/nodes.h#L-313). A semi join is used to check for at least one match. Similarly, an anti join is used to check for zero matches.

Let's keep going.

## Filter pushdown into joins

Similar to pushdowns into subqueries, PostgreSQL can copy an outer equality comparison across a join.

```
$ echo "EXPLAIN (COSTS OFF)
SELECT o.order_id, u.user_name
FROM orders o JOIN users u ON u.user_id = o.order_user_id
WHERE o.order_user_id = 100" | sudo -u postgres psql
                       QUERY PLAN
----------------------------------------------------------
 Gather
   Workers Planned: 1
   ->  Nested Loop
         ->  Parallel Seq Scan on orders o
               Filter: (order_user_id = 100)
         ->  Materialize
               ->  Index Scan using users_pkey on users u
                     Index Cond: (user_id = 100)
(8 rows)
```

But not (yet) for other operators.

```
$ echo "EXPLAIN (COSTS OFF)
SELECT o.order_id, u.user_name
FROM orders o JOIN users u ON u.user_id = o.order_user_id
WHERE o.order_user_id < 100" | sudo -u postgres psql
                     QUERY PLAN
-------------------------------------------------------
 Gather
   Workers Planned: 1
   ->  Nested Loop
         ->  Parallel Seq Scan on orders o
               Filter: (order_user_id < 100)
         ->  Index Scan using users_pkey on users u
               Index Cond: (user_id = o.order_user_id)
(7 rows)
```

Moving on.

## Eliminated JOINs

Sometimes, when PostgreSQL can prove a join has no effect, it will remove the join. For example, it will drop the join entirely when you do a LEFT JOIN, never use the right side, and the right side is provably unique.

```
$ echo "EXPLAIN (COSTS OFF) SELECT o.order_id FROM orders o LEFT JOIN users u ON u.user_id = o.order_user_id;" | sudo -u postgres psql
     QUERY PLAN
----------------------
 Seq Scan on orders o
(1 row)
```

But this doesn't always apply. If we set up a foreign key constraint between the two tables and do an inner join, the join is not eliminated, even though the right side's join column is provably unique (its primary key) and every left row provably has exactly one match on the right (its foreign key plus NOT NULL).

```
$ echo "
ALTER TABLE orders ALTER COLUMN order_user_id SET NOT NULL;
ALTER TABLE orders ADD CONSTRAINT orders_user_fk FOREIGN KEY (order_user_id) REFERENCES users(user_id);
VACUUM ANALYZE orders;

EXPLAIN (COSTS OFF) SELECT o.order_id FROM orders o JOIN users u ON u.user_id = o.order_user_id;" | sudo -u postgres psql
ALTER TABLE
ALTER TABLE
VACUUM
                 QUERY PLAN
--------------------------------------------
 Hash Join
   Hash Cond: (o.order_user_id = u.user_id)
   ->  Seq Scan on orders o
   ->  Hash
         ->  Seq Scan on users u
(5 rows)
```

Postgres (new in 18) does remove one kind of inner join though, a [table self-joined](https://theconsensus.dev/project/postgresql/source/REL_18_6/src/backend/optimizer/plan/analyzejoins.c#L-2737) on a unique column.

```
$ echo "EXPLAIN (COSTS OFF) SELECT a.order_status, b.order_user_id FROM orders a JOIN orders b ON a.order_id = b.order_id" | sudo -u postgres psql
      QUERY PLAN
----------------------
 Seq Scan on orders b
(1 row)
```

Moving on!

## IN and EXISTS

Trivial variations of IN and EXISTS get flattened and constant folded.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users u WHERE u.user_id IN (SELECT 100 + 100)" | sudo -u postgres psql
              QUERY PLAN
----------------------------------------
 Index Scan using users_pkey on users u
   Index Cond: (user_id = 200)
(2 rows)
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users u WHERE EXISTS (SELECT 1 WHERE u.user_id = 100 + 100)" | sudo -u postgres psql
               QUERY PLAN
----------------------------------------
 Index Scan using users_pkey on users u
   Index Cond: (user_id = 200)
(2 rows)
```

Otherwise they're rewritten into JOINs rather than per-row queries.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users u WHERE u.user_id IN (SELECT o.order_user_id FROM orders o WHERE o.order_status = 'paid')" | sudo -u postgres psql
                 QUERY PLAN
-----------------------------------------------
 Hash Right Semi Join
   Hash Cond: (o.order_user_id = u.user_id)
   ->  Seq Scan on orders o
         Filter: (order_status = 'paid'::text)
   ->  Hash
         ->  Seq Scan on users u
(6 rows)
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users u WHERE EXISTS (SELECT 1 FROM orders o WHERE o.order_status = 'paid' AND o.order_user_id = u.user_id)" | sudo -u postgres psql
                 QUERY PLAN
-----------------------------------------------
 Hash Right Semi Join
   Hash Cond: (o.order_user_id = u.user_id)
   ->  Seq Scan on orders o
         Filter: (order_status = 'paid'::text)
   ->  Hash
         ->  Seq Scan on users u
(6 rows)
```

Even NOT EXISTS can get rewritten into a(n anti) JOIN.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users u WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.order_status = 'paid' AND o.order_user_id = u.user_id)" | sudo -u postgres psql
                        QUERY PLAN
-----------------------------------------------------------
 Gather
   Workers Planned: 1
   ->  Parallel Hash Anti Join
         Hash Cond: (u.user_id = o.order_user_id)
         ->  Parallel Seq Scan on users u
         ->  Parallel Hash
               ->  Parallel Seq Scan on orders o
                     Filter: (order_status = 'paid'::text)
(8 rows)
```

But the same query as NOT IN seemingly cannot, because NOT IN produces a NULL rather than true when the subquery [produces a NULL](https://www.postgresql.org/docs/18/functions-subquery.html?utm_source=theconsensus.dev&utm_medium=referral#FUNCTIONS-SUBQUERY-NOTIN:~:text=the%20result%20of%20the%20NOT%20IN%20construct%20will%20be%20null%2C%20not%20true.), even though we already said both `user_id` and `order_user_id` are NOT NULL.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users u WHERE u.user_id NOT IN (SELECT o.order_user_id FROM orders o WHERE o.order_status = 'paid')" | sudo -u postgres psql
                        QUERY PLAN
-----------------------------------------------------------
 Seq Scan on users u
   Filter: (NOT (ANY (user_id = (hashed SubPlan 1).col1)))
   SubPlan 1
     ->  Seq Scan on orders o
           Filter: (order_status = 'paid'::text)
(5 rows)
```

And JOIN pushdowns from before still even happen here.

```
$ echo "EXPLAIN (COSTS OFF) SELECT * FROM users u WHERE EXISTS (SELECT 1 FROM orders o WHERE o.order_status = 'paid' AND o.order_user_id = u.user_id) AND u.user_id = 100" | sudo -u postgres psql
                                   QUERY PLAN
---------------------------------------------------------------------------------
 Nested Loop Semi Join
   ->  Index Scan using users_pkey on users u
         Index Cond: (user_id = 100)
   ->  Gather
         Workers Planned: 1
         ->  Parallel Seq Scan on orders o
               Filter: ((order_user_id = 100) AND (order_status = 'paid'::text))
(7 rows)
```

There is no index on `order_user_id`, so that scan is expected, but our filter was still pushed down into it.

## Aggregate reads

The last case we'll look at is when Postgres can turn some plain aggregates (an aggregate without a `GROUP BY`) into a single row scan on an index.

```
$ echo "EXPLAIN (COSTS OFF) SELECT min(order_id) FROM orders o" | sudo -u postgres psql
                        QUERY PLAN
-------------------------------------------------------------
 Result
   InitPlan 1
     ->  Limit
           ->  Index Only Scan using orders_pkey on orders o
(4 rows)
```

Which makes sense. And it makes sense this can't work with `sum` and `count`.

```
$ echo "EXPLAIN (COSTS OFF) SELECT count(order_id) FROM orders o" | sudo -u postgres psql
                   QUERY PLAN
-------------------------------------------------
 Finalize Aggregate
   ->  Gather
         Workers Planned: 1
         ->  Partial Aggregate
               ->  Parallel Seq Scan on orders o
(5 rows)
```

But Postgres also can't do this on a `GROUP BY`.

```
$ echo "EXPLAIN (COSTS OFF) SELECT order_user_id, min(order_id) FROM orders GROUP BY order_user_id;" | sudo -u postgres psql
        QUERY PLAN
----------------------------
 HashAggregate
   Group Key: order_user_id
   ->  Seq Scan on orders
(3 rows)
```

But this would take something more like a [new type of index scan](https://wiki.postgresql.org/wiki/Loose_indexscan?utm_source=theconsensus.dev&utm_medium=referral) to fix.

## Parting thoughts

Postgres is constantly evolving. Some of these do not seem incredibly hard or risky to do. And rewriting is probably the easier place for changes to happen in the planner. But who knows, maybe there are good reasons Postgres has not made some of these changes so far.

Until next time, when we talk about the statistical optimizer side of things.
