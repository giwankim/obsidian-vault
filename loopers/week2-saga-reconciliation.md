---
title: "Week 2 Study — Saga & Reconciliation Design Rationale"
source: "https://github.com/Loopers-play-dev-lab/integration-external-services"
author:
published:
created: 2026-07-30
description: "Design rationale behind the two-step purchase saga in commerce-api: why point compensation runs as a scheduled batch instead of @Async, how a 30s grace period prevents false compensation, the retryable/business exception taxonomy, and why no transaction spans the PG call."
tags:
  - "note"
  - "loopers"
  - "distributed-systems"
  - "payments"
  - "connection-pooling"
---

> [!summary]
> Design rationale for a two-step purchase saga that accumulates points and then charges the customer as independent external calls, recording *intent* (`PENDING`, `REVOKE_PENDING`) in the `purchases` table and leaving scheduled `PaymentReconciler`/`PointReconciler` batches to converge it — durable across crashes in a way a fire-and-forget `@Async` compensation is not.
> Covers the gray-zone race where a delayed PG commit lands after commerce-api has already given up (closed with a 30s grace period to prevent *false compensation*), and the exception taxonomy that splits business-vs-system and definitive-vs-ambiguous failures across resilience4j retry and circuit-breaker config, under the rule that only a definitive answer may move a purchase's status.
> Also distinguishes compensating transactions from local rollback, and explains why no `@Transactional` spans the PG call: holding a pooled connection for a ~6-second retry budget turns ordinary PG latency into HikariCP pool exhaustion, with the resulting visible intermediate state being exactly what the reconcilers exist to heal.

# Week 2 Study — Saga & Reconciliation Design Rationale

`PurchaseSaga` (`apps/commerce-api/.../application/purchase/PurchaseSaga.kt`) accumulates points
and then charges the customer as two independent external calls, each committing its own outcome
to the `purchases` table instead of an all-or-nothing transaction. Because neither call can be
undone synchronously, and either can fail in a way that isn't immediately classifiable as
success or failure, the saga records *intent* (`PENDING`, `REVOKE_PENDING`) and leaves two
scheduled batches — `PaymentReconciler` and `PointReconciler`, both invoked from
`ReconcileScheduler` — to converge that intent to a final state. The five sections below are the
design decisions behind that split, answered against the code as implemented and tested.

## Why Point Compensation Runs as a Batch, Not `@Async`

`Purchase.failWithPointRevokePending()` does not call `pointClient.revoke()` itself — it flips
`pointStatus` to `REVOKE_PENDING` and returns. Revocation happens later, when
`PointReconciler.reconcile()` re-scans `purchaseRepository.findByPointStatus(REVOKE_PENDING)` and
calls `pointClient.revoke(orderId, amount, pointAmount)` for each row. The reason is durability: a
`REVOKE_PENDING` row in MySQL survives a crash or redeploy, while a fire-and-forget `@Async` task
dies with the JVM and would need its own bespoke retry/backoff logic bolted onto the saga itself.

Because `reconcile()` re-reads the full `REVOKE_PENDING` set on every `fixedDelay` tick
(`reconcile.scheduling.point-delay=30s` in `application.yml`) rather than tracking an in-memory
queue, an interrupted run is automatically retried on the next tick — at-least-once convergence
without per-item checkpointing. Re-running `revoke()` is safe to repeat: `PointHttpClient.revoke()`
posts to the same `/api/v1/points/accumulate` endpoint as `accumulate()`, with `orderId` suffixed
`"$orderId:R"` (a synthetic reversal order id), and pg-simulator's
`PointApplicationService.accumulate()` deduplicates by `(userId, orderId)` before inserting — a
repeated call for the same reversal id returns the existing row instead of double-crediting.
Because the batch reads shared DB state rather than an in-memory queue, any commerce-api instance
can pick up a `REVOKE_PENDING` row; `ReconcileScheduler` has no leader election. The cost is
latency: a revoke can lag up to `point-delay` behind the failure that triggered it — acceptable
because points are a secondary reward, not the purchase's own success/failure signal.

## The Gray-Zone Race and the Grace Period

`PurchaseSaga` hands a purchase off as `PurchaseStatus.PENDING` (`Purchase.pendingPayment`)
whenever `ResilientPgClient` can't get a definitive answer from pg-simulator within its retry
budget — `PgConfirmResult.pending()` is the deliberate fallback, per the rule stated directly in
`ResilientPgClient`'s own comment: "❗성공 위장 금지" (never fake success). pg-simulator's request
handling isn't cancelled just because commerce-api gave up waiting:
`TossPaymentSimulator.applyInfraFault()` injects delay/failure *before* the payment row is
created, and past that point `TossPaymentService.confirm()` still commits normally on its own
thread. So a payment can
legitimately land at PG after commerce-api already marked the purchase `PENDING`.

If `PaymentReconciler.reconcile()` queries `pgClient.getPayment(paymentKey)` before that delayed
commit lands, PG returns 404, `PgHttpConnector` maps it to `PgDeclinedException`, and the
reconciler's catch block calls `purchase.failAndSave()` — FAILED, `pointStatus` flipped to
`REVOKE_PENDING`. Minutes later PG's commit lands anyway: the customer was charged, the purchase
reads FAILED, and the batch revokes points that were legitimately earned. That's a *false
compensation* — the worst outcome the system can produce, since it actively corrupts a purchase
that succeeded rather than merely delaying one that didn't.

`reconcile.grace-period=30s` closes the window: `PaymentReconciler.reconcile()` computes
`cutoff = LocalDateTime.now(clock).minus(gracePeriod)` and queries
`purchaseRepository.findByStatusCreatedBefore(PENDING, cutoff)`, so rows younger than the window
aren't touched. Thirty seconds comfortably clears commerce-api's own worst-case per-call patience:
`resilience4j.retry.instances.pg.max-attempts=3` means confirm() can be attempted up to three
times total, each bounded by `pg.read-timeout-ms=2000`, roughly six seconds end to end — with wide
margin even if PG's simulated delay is reconfigured higher.

`PointReconciler` carries no equivalent grace period, correctly: `pointClient.accumulate()` must
return before the saga attempts payment, so `pointAccumulated()` only fires after that call has
already resolved — no uncommitted-async window to protect. `REVOKE_PENDING` is only set after a
*definitive* payment failure, by which point accumulation is long settled.

The post-grace "not found" read is trustworthy because `PaymentFacade.pay()` generates
`paymentKey` client-side (`PaymentKeyGenerator.generate()`, a random `PK-<uuid>`) and sends it to
PG in the confirm request rather than letting PG assign an id; `PaymentFacade.pay()` even falls
back to the client's own key if PG's response omits one (`val resolvedKey = result.paymentKey ?:
paymentKey`). Because the key originates from commerce-api, an unknown key after the grace window
genuinely means the confirm request never landed — no ambiguity from a PG-assigned identifier.

## Classifying Exceptions on the Retryable/Business Axes

Three exception types drive three different state transitions — one per combination of business
vs. system failure, and definitive vs. ambiguous outcome.

`PointException` (`infrastructure/point/PointException.kt`) is thrown uniformly by
`PointHttpClient` for every point-call failure: a `>= 400` HTTP status and a connection/read
timeout (`ResourceAccessException`) both funnel into the same exception type, with no retry inside
`PointHttpClient` itself. `PurchaseSaga.purchase()` catches it around `pointClient.accumulate()`
and calls `purchase.failWithoutPoint()` immediately — no PG call is attempted, no compensation is
scheduled, because nothing external has committed yet.

On the payment side, `PgHttpConnector` splits by HTTP status: 4xx becomes `PgDeclinedException`
(business, definitive — a rejected card, an invalid amount); 5xx or `ResourceAccessException`
becomes `PgServerException` (system, transient). `application.yml` wires this taxonomy straight
into resilience4j: `circuitbreaker.instances.pg.ignore-exceptions` excludes `PgDeclinedException`
from failure-rate accounting (a declined card isn't PG's fault), while
`retry.instances.pg.retry-exceptions` retries only `PgServerException`, up to three attempts.
`ResilientPgClient.confirmFallback` then converts whatever survives: `PgDeclinedException` becomes
`PgConfirmResult.declined()` → `PaymentOutcome.FAILED` → `purchase.failWithPointRevokePending()`;
anything else (retry-exhausted `PgServerException`, an open circuit, a rejected bulkhead slot)
becomes `PgConfirmResult.pending()` → `PaymentOutcome.PENDING` → `purchase.pendingPayment(...)`.

`PaymentReconciler` applies the identical taxonomy later, directly against the same exception
types thrown by `pgClient.getPayment()`: `PgDeclinedException` moves the row to FAILED,
`PgServerException` leaves it PENDING for the next cycle (`ItemOutcome.HELD`, logged but not
counted as processed). The rule holding both layers together: only a definitive answer is allowed
to move a purchase's status; anything ambiguous holds and waits for more information.

## Compensating Transaction vs. Simple Rollback

The dividing line is whether an external system has already committed a side effect the
`purchases` row now depends on. If `pointClient.accumulate()` throws `PointException`, nothing was
ever recorded — pg-simulator's `PointApplicationService.accumulate()` never executed the insert
for that `orderId` — so `failWithoutPoint()` is a pure local rollback: `status=FAILED`,
`pointStatus=NONE`, done.

If `accumulate()` had already succeeded (`pointStatus=ACCUMULATED`) and the subsequent PG confirm
call then fails, the situation is different: an external system already holds a committed record
tied to this `orderId`. `Purchase.failWithPointRevokePending()` encodes that asymmetry directly in
its guard — `status` becomes FAILED, but `pointStatus` only moves to `REVOKE_PENDING` "if
(pointStatus == PurchasePointStatus.ACCUMULATED)"; if points were never accumulated, there is
nothing to compensate and the field is left alone. `REVOKE_PENDING` is not itself the
compensation — it is a durable instruction that `PointReconciler` later executes by calling
`pointClient.revoke()`, converging the row to `REVOKED` (or leaving it for the next cycle on
failure).

A rollback undoes something that never left the process; a compensating transaction reverses
something a separate system already accepted, and can only be undone by issuing another explicit
call to that system — it cannot be achieved by discarding local state. `Purchase` models this by
keeping `status` (the saga's own outcome) and `pointStatus` (whether an external commitment exists,
and its resolution) as separate fields, so an external side effect is always tracked independently
of the purchase's own success or failure.

## Pushing External Calls Outside Transactions

`PurchaseSaga` carries no `@Transactional` annotation. Its `purchase()` method makes two short,
independent `purchaseService.save()` calls bracketing the external round trips, rather than one
call wrapped in a transaction: the initial `Purchase` row is saved (PENDING/NONE) before
`pointClient.accumulate()` is invoked, and — after either an early `failWithoutPoint()` exit or a
full pass through `paymentFacade.pay()` — a second save persists whatever the saga has learned. At
no point does an open database transaction span an HTTP call to pg-simulator.

`PaymentFacade` follows the identical rule and documents why directly in its class comment:
"facade 자체에는 트랜잭션을 두지 않는다 — 외부 호출(PG) 동안 DB 커넥션을 잡지 않도록" (the facade
itself carries no transaction, so a DB connection isn't held for the duration of the PG call) —
only the idempotency-record bookkeeping (`IdempotencyService`) gets its own short transaction.
The confirm call can legitimately take up to the `pg.read-timeout-ms: 2000` read-timeout, and with
`resilience4j.retry.instances.pg.max-attempts: 3` the worst-case retry budget is roughly six
seconds; holding a transaction across a call of that length would pin a pooled connection for the
whole window, and under concurrent load that turns ordinary PG latency into HikariCP pool exhaustion
for unrelated requests — exactly the failure mode the week-1 PG connection-pool work
(`docs/superpowers/specs/2026-07-17-pg-http-pool-timeouts-design.md`) sized
`pool-max-total`/`pool-max-per-route` and the connection-request-timeout to detect and fail fast
on, on the HTTP client side of the same call.

The cost is visible intermediate state: a crash between the two saves — after `accumulate()`
succeeds but before the payment call returns, or after payment resolves but before the final save
— leaves a `purchases` row sitting in PENDING or with `pointStatus=REVOKE_PENDING` indefinitely on
its own. That isn't a bug to fix; it's exactly the case `PaymentReconciler` and `PointReconciler`
exist to heal on their next scheduled pass.
