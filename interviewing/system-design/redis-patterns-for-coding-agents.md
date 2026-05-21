---
title: "Redis Patterns for Coding Agents"
source: "https://redis.antirez.com/"
author:
published:
created: 2026-03-11
description:
tags:
  - "clippings"
  - "redis"
  - "system-design"
  - "coding-agents"
---
> [!summary]
> Antirez's comprehensive reference of Redis design patterns organized for both human developers and LLM coding agents, covering fundamental patterns (caching, locking, rate limiting, queues, streams), community patterns (leaderboards, pub/sub, session management), and production case studies from Pinterest, Twitter, and Uber.

Comprehensive Redis design patterns, best practices, and command references. This site is optimized for both human developers and LLM coding agents.

### How to Use This Documentation

**For Humans:** Browse the sections below and click on any pattern to read the documentation.

**For LLM Coding Agents:** Start by fetching the machine-readable index:

`[llms.txt](https://redis.antirez.com/llms.txt)` — Lists all available documentation files with descriptions

Then fetch individual `.md` files as needed. All pattern documents are written in Markdown with Redis commands shown as indented code blocks.

**For Command Reference:** The official Redis documentation is mirrored locally:

`[commands-index.md](https://redis.antirez.com/commands-index.md)` — Auto-generated index of all commands by category
`[commands/content/commands/](https://redis.antirez.com/commands/content/commands/)` — Individual command docs (e.g., [set.md](https://redis.antirez.com/commands/content/commands/set.md), [hset.md](https://redis.antirez.com/commands/content/commands/hset.md))

**Official Resources:**
• Source Code: [github.com/redis/redis](https://github.com/redis/redis)
• Documentation: [github.com/redis/docs](https://github.com/redis/docs) → [redis.io/docs](https://redis.io/docs/)

## Commands Reference

Browse Redis commands organized by category:

- **Commands Index:**([html](https://redis.antirez.com/commands-index.html)) ([markdown](https://redis.antirez.com/commands-index.md)) — Auto-generated index of commands by category
- **Command Documentation:**[commands/content/commands/](https://redis.antirez.com/commands/content/commands/) — Individual command files
- **Full Documentation:**[commands/content/](https://redis.antirez.com/commands/content/) — develop/, integrate/, operate/ guides

This is a mirror of [github.com/redis/docs](https://github.com/redis/docs).

## Fundamental Design Patterns

Core architectural patterns for building systems with Redis.

- **Atomic Update Patterns** ([html](https://redis.antirez.com/fundamental/atomic-updates.html)) ([markdown](https://redis.antirez.com/fundamental/atomic-updates.md))
	Ensure data integrity with atomic read-modify-write operations using WATCH/MULTI/EXEC for optimistic locking, Lua scripts for complex logic, and shadow-key patterns for safe bulk updates.
- **Cache-Aside Pattern (Lazy Loading)** ([html](https://redis.antirez.com/fundamental/cache-aside.html)) ([markdown](https://redis.antirez.com/fundamental/cache-aside.md))
	Use Cache-Aside for read-heavy workloads: on cache miss, fetch from the database and populate the cache; on write, invalidate or update the cache explicitly.
- **Cache Stampede Prevention** ([html](https://redis.antirez.com/fundamental/cache-stampede-prevention.html)) ([markdown](https://redis.antirez.com/fundamental/cache-stampede-prevention.md))
	Prevent multiple clients from simultaneously regenerating an expired cache key using locking, probabilistic early refresh, or request coalescing.
- **Server-Assisted Client-Side Caching** ([html](https://redis.antirez.com/fundamental/client-side-caching.html)) ([markdown](https://redis.antirez.com/fundamental/client-side-caching.md))
	Eliminate network round-trips for frequently accessed keys by caching values in application memory, with Redis 6+ automatically sending invalidation messages when data changes.
- **Cross-Shard Consistency Patterns** ([html](https://redis.antirez.com/fundamental/cross-shard-consistency.html)) ([markdown](https://redis.antirez.com/fundamental/cross-shard-consistency.md))
	Detect and handle torn writes across multiple Redis instances using transaction stamps, version tokens, and commit markers when atomic multi-key operations aren't possible.
- **Delayed Queue Pattern** ([html](https://redis.antirez.com/fundamental/delayed-queue.html)) ([markdown](https://redis.antirez.com/fundamental/delayed-queue.md))
	Schedule tasks for future execution using a Sorted Set where the score is the Unix timestamp when the task should run.
- **Distributed Locking with Redis** ([html](https://redis.antirez.com/fundamental/distributed-locking.html)) ([markdown](https://redis.antirez.com/fundamental/distributed-locking.md))
	Implement mutual exclusion across distributed processes using \`SET key value NX PX timeout\` for atomic lock acquisition with automatic expiration.
- **Hash Tag Co-location Patterns** ([html](https://redis.antirez.com/fundamental/hash-tag-colocation.html)) ([markdown](https://redis.antirez.com/fundamental/hash-tag-colocation.md))
	Force related keys to the same Redis Cluster slot using hash tags, enabling atomic multi-key operations, transactions, and Lua scripts across logically related data.
- **Lexicographic Sorted Set Patterns** ([html](https://redis.antirez.com/fundamental/lexicographic-sorted-sets.html)) ([markdown](https://redis.antirez.com/fundamental/lexicographic-sorted-sets.md))
	Use Sorted Sets with identical scores (typically 0) to create B-tree-like indexes supporting prefix queries, range scans, and composite key lookups on string data.
- **Memory Optimization Patterns** ([html](https://redis.antirez.com/fundamental/memory-optimization.html)) ([markdown](https://redis.antirez.com/fundamental/memory-optimization.md))
	Reduce Redis memory consumption by leveraging compact encodings (listpack, intset), using Hashes for small object storage, and choosing memory-efficient data structures.
- **Probabilistic Data Structures** ([html](https://redis.antirez.com/fundamental/probabilistic-data-structures.html)) ([markdown](https://redis.antirez.com/fundamental/probabilistic-data-structures.md))
	Count unique items with HyperLogLog (12KB fixed), test set membership with Bloom filters, or estimate frequencies with Count-Min Sketch—trading small accuracy loss for massive memory savings.
- **Rate Limiting Patterns** ([html](https://redis.antirez.com/fundamental/rate-limiting.html)) ([markdown](https://redis.antirez.com/fundamental/rate-limiting.md))
	Implement distributed rate limiting using fixed window, sliding window log, sliding window counter, token bucket, or leaky bucket algorithms with Redis atomic operations.
- **Redis as a Primary Database** ([html](https://redis.antirez.com/fundamental/redis-as-primary-database.html)) ([markdown](https://redis.antirez.com/fundamental/redis-as-primary-database.md))
	Use Redis as the authoritative data store for applications requiring sub-millisecond latency and high write throughput, treating disk as a recovery mechanism rather than the primary storage layer.
- **The Redlock Algorithm** ([html](https://redis.antirez.com/fundamental/redlock.html)) ([markdown](https://redis.antirez.com/fundamental/redlock.md))
	Achieve fault-tolerant distributed locking by acquiring locks on a majority (N/2+1) of N independent Redis instances, tolerating node failures without losing lock consistency.
- **Reliable Queue Pattern** ([html](https://redis.antirez.com/fundamental/reliable-queue.html)) ([markdown](https://redis.antirez.com/fundamental/reliable-queue.md))
	Guarantee at-least-once message delivery using LMOVE to atomically transfer messages to a processing list, enabling recovery if consumers crash before completing work.
- **Streams Consumer Group Patterns** ([html](https://redis.antirez.com/fundamental/streams-consumer-patterns.html)) ([markdown](https://redis.antirez.com/fundamental/streams-consumer-patterns.md))
	Implement reliable message processing with Redis Streams consumer groups, handling failure recovery, poison pills, and memory management—the operational patterns that production systems require beyond basic XREADGROUP usage.
- **Redis Streams and Event Sourcing** ([html](https://redis.antirez.com/fundamental/streams-event-sourcing.html)) ([markdown](https://redis.antirez.com/fundamental/streams-event-sourcing.md))
	Build persistent message queues with consumer groups, message acknowledgment, and historical replay using Redis Streams—ideal for event sourcing and multi-consumer workloads.
- **Vector Sets and Similarity Search** ([html](https://redis.antirez.com/fundamental/vector-sets.html)) ([markdown](https://redis.antirez.com/fundamental/vector-sets.md))
	Store vectors and find similar items using Redis 8's native Vector Sets—an HNSW-based data structure supporting semantic search, RAG, recommendations, and classification with optional filtered queries.
- **Write-Behind (Write-Back) Caching Pattern** ([html](https://redis.antirez.com/fundamental/write-behind.html)) ([markdown](https://redis.antirez.com/fundamental/write-behind.md))
	Maximize write throughput by writing only to Redis and asynchronously syncing to the database later—trades immediate durability for performance.
- **Write-Through Caching Pattern** ([html](https://redis.antirez.com/fundamental/write-through.html)) ([markdown](https://redis.antirez.com/fundamental/write-through.md))
	Maintain cache-database consistency by synchronously writing to both Redis and the database before returning success—ensures reads always hit cache with fresh data.

## Community Patterns

Patterns developed by the Redis community for common use cases.

- **Bitmap Patterns** ([html](https://redis.antirez.com/community/bitmap-patterns.html)) ([markdown](https://redis.antirez.com/community/bitmap-patterns.md))
	Store millions of boolean flags in minimal memory using Redis bitmaps—1 bit per flag with O(1) access, plus fast aggregate operations across entire datasets.
- **Geospatial Patterns** ([html](https://redis.antirez.com/community/geospatial.html)) ([markdown](https://redis.antirez.com/community/geospatial.md))
	Store locations and query by radius, distance, or bounding box using GEOADD, GEOSEARCH, and GEODIST commands built on geohash-encoded Sorted Sets.
- **Leaderboard Patterns** ([html](https://redis.antirez.com/community/leaderboards.html)) ([markdown](https://redis.antirez.com/community/leaderboards.md))
	Build real-time rankings with Sorted Sets: O(log N) score updates, O(log N) rank lookups, and efficient range queries for top-N or around-me leaderboards.
- **Pub/Sub Patterns** ([html](https://redis.antirez.com/community/pubsub.html)) ([markdown](https://redis.antirez.com/community/pubsub.md))
	Broadcast real-time events to multiple subscribers using fire-and-forget messaging—ideal for notifications, chat, and live updates where missed messages are acceptable.
- **Session Management Patterns** ([html](https://redis.antirez.com/community/session-management.html)) ([markdown](https://redis.antirez.com/community/session-management.md))
	Store user sessions in Redis with automatic expiration using TTL, choosing between Hashes (field-level access), Strings (serialized), or JSON (nested data) based on access patterns.
- **Vector Search and AI Patterns** ([html](https://redis.antirez.com/community/vector-search-ai.html)) ([markdown](https://redis.antirez.com/community/vector-search-ai.md))
	Build semantic search, RAG pipelines, recommendation systems, and AI agent infrastructure using Redis Vector Sets—native HNSW-based similarity search with sub-millisecond latency.

## Production Patterns

Real-world patterns from major tech companies at scale.

- **Linux Kernel Tuning for Redis** ([html](https://redis.antirez.com/production/kernel-tuning.html)) ([markdown](https://redis.antirez.com/production/kernel-tuning.md))
	Configure Linux kernel parameters to prevent latency spikes, persistence failures, and connection drops in production Redis deployments—essential settings that override defaults hostile to in-memory databases.
- **Pinterest: Task Queue and Functional Partitioning** ([html](https://redis.antirez.com/production/pinterest-task-queue.html)) ([markdown](https://redis.antirez.com/production/pinterest-task-queue.md))
	Learn Pinterest's Redis scaling patterns: functional partitioning by use case, List-based reliable queues for background jobs, and horizontal scaling from 1 to 1000+ instances.
- **Twitter/X: Deep Internals and Custom Data Structures** ([html](https://redis.antirez.com/production/twitter-internals.html)) ([markdown](https://redis.antirez.com/production/twitter-internals.md))
	Historical case study of Twitter's Redis customizations—many of these innovations are now built into Redis core (quicklist, improved memory management).
- **Uber: Resilience Patterns and Staggered Sharding** ([html](https://redis.antirez.com/production/uber-resilience.html)) ([markdown](https://redis.antirez.com/production/uber-resilience.md))
	Study Uber's resilience techniques: staggered sharding to prevent coordinated failures, circuit breakers, and graceful degradation patterns for 150M+ ops/sec cache workloads.

---

**Quick Start for AI Agents:** Fetch [llms.txt](https://redis.antirez.com/llms.txt) first, then retrieve specific `.md` files as needed.
