---
title: "Using PostgreSQL as a Dead Letter Queue for Event-Driven Systems"
source: "https://www.diljitpr.net/blog-post-postgresql-dlq"
author:
  - "[[Diljit]]"
published: 2025-12-25
created: 2026-01-28
description: "Learn how to use PostgreSQL as a Dead Letter Queue (DLQ) for event-driven systems. Case study from Wayfair showing how to handle failures in Kafka consumers with PostgreSQL for better observability and retry mechanisms."
tags:
  - "clippings"
---
While I was working on a project with Wayfair, I got the opportunity to work on a system that generated daily business reports aggregated from multiple data sources flowing through event streams across Wayfair. At a high level, Kafka consumers listened to these events, hydrated them with additional data by calling downstream services, and finally persisted the enriched events into a durable datastore—CloudSQL PostgreSQL on GCP.

When everything was healthy, the pipeline worked exactly as expected. Events flowed in, got enriched, and were stored reliably. The real challenge started when things went wrong, which, in distributed systems, is not an exception but a certainty.

There were multiple failure scenarios we had to deal with. Sometimes the APIs we depended on for hydration were down or slow. Sometimes the consumer itself crashed midway through processing. In other cases, events arrived with missing or malformed fields that could not be processed safely. These were all situations outside our direct control, but they still needed to be handled gracefully.

This is where the concept of a Dead Letter Queue came into the picture. Whenever we knew an event could not be processed successfully, instead of dropping it or blocking the entire consumer, we redirected it to a DLQ so it could be inspected and potentially reprocessed later.

Our first instinct was to use Kafka itself as a DLQ. While this is a common pattern, it quickly became clear that it wasn't a great fit for our needs. Kafka is excellent for moving data, but once messages land in a DLQ topic, they are not particularly easy to inspect. Querying by failure reason, retrying a specific subset of events, or even answering simple questions like "what failed yesterday and why?" required extra tooling and custom consumers. For a system that powered business-critical daily reports, this lack of visibility was a serious drawback.

That's when we decided to treat PostgreSQL itself as the Dead Letter Queue.

Instead of publishing failed events to another Kafka topic, we persisted them directly into a DLQ table in PostgreSQL. We were already using CloudSQL as our durable store, so operationally this added very little complexity. Conceptually, it also made failures first-class citizens in the system rather than opaque messages lost in a stream.

Whenever an event failed processing—due to an API failure, consumer crash, schema mismatch, or validation error—we stored the raw event payload along with contextual information about the failure. Each record carried a simple status field. When the event first landed in the DLQ, it was marked as `PENDING`. Once it was successfully reprocessed, the status was updated to `SUCCEEDED`. Keeping the state model intentionally minimal made it easy to reason about the lifecycle of a failed event.

### DLQ Table Schema and Indexing Strategy

To support inspection, retries, and long-term operability, the DLQ table was designed to be simple, query-friendly, and retry-aware.

#### Table Schema

```
CREATE TABLE dlq_events (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    error_reason TEXT NOT NULL,
    error_stacktrace TEXT,
    status VARCHAR(20) NOT NULL, -- PENDING / SUCCEEDED
    retry_count INT NOT NULL DEFAULT 0,
    retry_after TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

#### Key Design Considerations

- `payload` is stored as `JSONB` to preserve the raw event without enforcing a rigid schema.
- `status` keeps the lifecycle simple and explicit.
- `retry_after` prevents aggressive retries when downstream systems are unstable.
- `retry_count` allows retry limits to be enforced without external state.
- Timestamps make auditing and operational analysis straightforward.

#### Indexes

```
CREATE INDEX idx_dlq_status
ON dlq_events (status);

CREATE INDEX idx_dlq_status_retry_after
ON dlq_events (status, retry_after);

CREATE INDEX idx_dlq_event_type
ON dlq_events (event_type);

CREATE INDEX idx_dlq_created_at
ON dlq_events (created_at);
```

These indexes allow the retry scheduler to efficiently locate eligible events while still supporting fast debugging and time-based analysis without full table scans.

### DLQ Retry Mechanism with ShedLock

Persisting failed events solved the visibility problem, but we still needed a safe and reliable way to retry them.

For this, we introduced a DLQ retry scheduler backed by ShedLock. The scheduler periodically scans the DLQ table for `PENDING` events that are eligible for retry and attempts to process them again. Since the service runs on multiple instances, ShedLock ensures that only one instance executes the retry job at any given time. This eliminates duplicate retries without requiring custom leader-election logic.

#### Retry Configuration

```
dlq:
  retry:
    enabled: true
    max-retries: 240
    batch-size: 50
    fixed-rate: 21600000 # 6 hours in milliseconds
```

#### How Retries Work

- The scheduler runs every six hours.
- Up to fifty eligible events are picked up per run.
- Events exceeding the maximum retry count are skipped.
- Successful retries immediately transition the event status to `SUCCEEDED`.
- Failures remain in `PENDING` and are retried in subsequent runs.

#### Query Implementation

The retry scheduler uses a SQL query with `FOR UPDATE SKIP LOCKED` to safely select eligible events across multiple instances. This PostgreSQL feature ensures that even if multiple scheduler instances run simultaneously, each will pick up different rows without blocking each other:

```
@QueryHints(@QueryHint(name = "jakarta.persistence.lock.timeout", value = "-2"))
@Query(
    value = "SELECT * FROM dlq_table "
        + "WHERE messagetype = :messageType "
        + "AND retries < :maxRetries "
        + "AND (replay_status IS NULL OR replay_status NOT IN ('COMPLETED')) "
        + "ORDER BY created_at ASC "
        + "FOR UPDATE SKIP LOCKED",
    nativeQuery = true
)
```

The `FOR UPDATE SKIP LOCKED` clause is crucial here. It allows each instance to lock and process different rows concurrently, preventing duplicate processing while maintaining high throughput. The query hint sets the lock timeout to `-2`, which means "wait indefinitely" but combined with `SKIP LOCKED`, it effectively means "skip any rows that are already locked by another transaction."

This setup allowed the system to tolerate long downstream outages while avoiding retry storms and unnecessary load on dependent services.

### Operational Benefits

With this approach, failures became predictable and observable rather than disruptive. Engineers could inspect failures using plain SQL, identify patterns, and reprocess only the events that mattered. If a downstream dependency was unavailable for hours or even days, events safely accumulated in the DLQ and were retried later without human intervention. If an event was fundamentally bad, it stayed visible instead of being silently dropped.

Most importantly, this design reduced operational stress. Failures were no longer something to fear; they were an expected part of the system with a clear, auditable recovery path.

### My Thoughts

The goal was never to replace Kafka with PostgreSQL. Kafka remained the backbone for high-throughput event ingestion, while PostgreSQL handled what it does best—durability, querying, and observability around failures. By letting each system play to its strengths, we ended up with a pipeline that was resilient, debuggable, and easy to operate.

In the end, using PostgreSQL as a Dead Letter Queue turned failure handling into something boring and predictable. And in production systems, boring is exactly what you want.
