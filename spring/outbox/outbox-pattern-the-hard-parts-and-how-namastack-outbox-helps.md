---
title: "Outbox Pattern: The Hard Parts (and How Namastack Outbox Helps)"
source: "https://dev.to/namastack/outbox-pattern-the-hard-parts-and-how-namastack-outbox-helps-507m"
author:
published: 2026-01-20
created: 2026-10-31
description: "Most people know the Transactional Outbox Pattern at a high level.  What’s often missing are the... Tagged with java, kotlin, springboot, outbox."
tags:
  - "clippings"
---

> [!summary]
> Namastack's own post on the production details of a transactional outbox, starting with per-key rather than global ordering, where `stop-on-first-failure` decides whether later records for a key wait behind a failed one. Scaling across instances uses 256 hash-based partitions with heartbeat-driven rebalancing instead of database locks, so each key lands on one instance, though a hot key becomes a throughput bottleneck. Retries use configurable backoff with include/exclude exception lists, and records that exhaust them go to a fallback handler or end up `FAILED` for alerting or manual replay.

Most people know the Transactional Outbox Pattern at a high level.

What’s often missing are the production-grade details - the “hard parts” that decide whether your outbox is reliable under real load and failures:

- ordering semantics (usually per aggregate/key, not global) and what happens when one record in a sequence fails
- scaling across multiple instances without lock pain (partitioning + rebalancing)
- retries that behave well during outages
- a clear strategy for permanently failed records
- monitoring and operations (backlog, failures, partitions, cluster health)

This article focuses on those hard parts and how [**Namastack Outbox**](https://outbox.namastack.io/) addresses them.

If you want to browse the relevant docs sections upfront:

- [Ordering & partitioning](https://outbox.namastack.io/latest/features/core/#record-ordering)
- [Schema management](https://outbox.namastack.io/latest/features/database/#schema-management)
- [Monitoring & metrics](https://outbox.namastack.io/latest/features/monitoring/)
- [Configuration reference](https://outbox.namastack.io/latest/features/configuration/)

If you want a quick primer first, this video introduces **Namastack Outbox** and recaps the basic concepts behind the Outbox Pattern:

![](https://www.youtube.com/watch?v=857Pm6iC1Fw)

---

## The Hard Parts

### Ordering: what you actually need in production

When people say “we need ordering”, they often mean *global ordering*. In production, that’s usually the wrong goal.

What you typically need is **ordering per business key** (often per aggregate):

- for a given `order-123`, process records strictly **in creation order**
- for different keys (`order-456`, `order-789`), process in parallel

#### How Namastack Outbox defines ordering

Ordering is defined by the **record key**:

- same key → sequential, deterministic processing
- different keys → concurrent processing
```
@Service
class OrderService(
    private val outbox: Outbox,
    private val orderRepository: OrderRepository
) {
    @Transactional
    fun createOrder(command: CreateOrderCommand) {
        val order = Order.create(command)
        orderRepository.save(order)

        // Schedule event - saved atomically with the order
        outbox.schedule(
            payload = OrderCreatedEvent(order.id, order.customerId),
            key = "order-${order.id}"  // Groups records for ordered processing
        )
    }
}
```

With Spring events:

```
@OutboxEvent(key = "#this.orderId")
data class OrderCreatedEvent(val orderId: String)
```

#### Failure behavior: should later records wait?

The key production question is what happens if one record in the sequence fails.

By default (`outbox.processing.stop-on-first-failure=true`), later records with the same key **wait**. This preserves strict semantics when records depend on each other.

If records are independent, you can set `outbox.processing.stop-on-first-failure=false` so failures don’t block later records for the same key.

#### Choosing good keys

Use the key for the **unit where ordering matters**:

- `order-${orderId}`
- `customer-${customerId}`

Avoid keys that are too coarse (serialize everything), e.g. `"global"`.
Avoid keys that are too fine (no ordering), e.g. a random UUID.

#### Why ordering still works when scaling out

Namastack Outbox combines key-based ordering with **hash-based partitioning**, so a key consistently routes to the same partition and one active instance processes it at a time.

---

### Scaling: partitioning and rebalancing

Scaling an outbox from 1 instance to N instances is where many implementations fall apart.

At that point you need two things at the same time:

- **work distribution** (so all instances can help)
- **no double processing + preserved ordering** (especially for the same key)

A common approach is “just use database locks”. That can work, but it often brings lock contention, hot rows, and unpredictable latency once traffic grows.

#### Namastack Outbox approach: hash-based partitioning

Instead of distributed locking, Namastack Outbox uses **hash-based partitioning**:

- There are **256 fixed partitions**.
- Each record key is mapped to a partition using consistent hashing.
- Each application instance owns a subset of those partitions.
- An instance only polls/processes records for its assigned partitions.

As a result:

- Different instances don’t compete for the same records (low lock contention).
- Ordering stays meaningful: **same key → same partition → processed sequentially**.

#### What rebalancing means

In production, the number of active instances changes:

- you deploy a new version (rolling restart)
- autoscaling adds/removes pods
- an instance crashes

Namastack Outbox periodically re-evaluates which instances are alive and redistributes partitions.
This is the “rebalancing” part.

Important: rebalancing is designed to be automatic — you shouldn’t need a separate coordinator.

#### Instance coordination knobs

These settings control how instances coordinate and detect failures:

```
outbox:
  rebalance-interval: 10000                  # ms between rebalance checks

  instance:
    heartbeat-interval-seconds: 5            # how often to send heartbeats
    stale-instance-timeout-seconds: 30       # when to consider an instance dead
    graceful-shutdown-timeout-seconds: 15    # time to hand over partitions on shutdown
```

Rules of thumb:

- Lower heartbeat + stale timeout → faster failover, more DB chatter.
- Higher values → less overhead, slower reaction to node failure.

#### Practical guidance

- Keep your **key design** intentional (see Ordering chapter). It drives both ordering and partitioning.
- If one key is extremely “hot” (e.g., `tenant-1`), it will map to a single partition and become a throughput bottleneck. In that case, consider a more granular key if business semantics allow it.
- For near real-time delivery requirements, pure polling will always add some latency; consider CDC or broker-native transaction integrations.

---

### Outages: retries and failed records

Outages and transient failures are not edge cases — they’re normal: rate limits, broker downtime, flaky networks, credential rollovers.

The hard part is making retries predictable:

- retry too aggressively → you amplify the outage and overload your own system
- retry too slowly → your backlog grows and delivery latency explodes

#### Namastack Outbox retry model (high level)

Each record is processed by a handler. If the handler throws, the record is not lost — it is rescheduled for another attempt.

Records move through a simple lifecycle:

- `NEW` → waiting / retrying
- `COMPLETED` → successfully processed
- `FAILED` → retries exhausted (needs attention)

#### Default configuration knobs

You can tune polling, batching, and retry via configuration:

```
outbox:
  poll-interval: 2000
  batch-size: 10

  retry:
    policy: exponential
    max-retries: 3

    # Optional: only retry specific exceptions
    include-exceptions:
      - java.net.SocketTimeoutException

    # Optional: never retry these exceptions
    exclude-exceptions:
      - java.lang.IllegalArgumentException
```

A good production default is **exponential backoff**, because it naturally reduces pressure during outages.

#### What happens after retries are exhausted?

At some point, you need a deterministic outcome.

Namastack Outbox supports fallback handlers for exactly that case:

- retries exhausted, or
- non-retryable exception

For annotation-based handlers, the fallback method must be on the same Spring bean as the handler.

```
@Component
class OrderHandlers(
  private val publisher: OrderPublisher,
  private val deadLetter: DeadLetterPublisher,
) {
  @OutboxHandler
  fun handle(event: OrderCreatedEvent) {
    publisher.publish(event)
  }

  @OutboxFallbackHandler
  fun onFailure(event: OrderCreatedEvent, ctx: OutboxFailureContext) {
    deadLetter.publish(event, ctx.lastFailure)
  }
}
```

If a fallback succeeds, the record is marked `COMPLETED`.
If there’s no fallback (or the fallback fails), the record becomes `FAILED`.

#### Practical guidance

- Decide early what “FAILED” means in your org: alert, dashboard, dead-letter, or manual replay.
- Keep retry counts conservative when handlers talk to external systems; rely on backoff rather than fast loops.
- For critical flows, use metrics to alert when `FAILED` records appear or when backlog grows.

---

## Next steps

If you found this useful, I’d really appreciate a ⭐ on GitHub — and feel free to share the article or leave a comment with feedback / questions.
