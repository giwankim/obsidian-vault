---
title: "When Caches Lie: The Hidden Invalidation Traps in a Multi-Instance Spring Boot Microservice"
source: "https://dev.to/prasadmk/when-caches-lie-the-hidden-invalidation-traps-in-a-multi-instance-spring-boot-microservice-44pl"
author:
  - "[[Prasad MK]]"
published: 2026-08-03
created: 2026-10-15
description: "Your local dev environment lied to you. It ran one instance, one JVM, one cache. Everything... Tagged with springboot, java, kubernetes, redis."
tags:
  - "clippings"
---

> [!summary]
> Prasad MK covers four ways caches go stale once a Spring Boot service runs on multiple instances, even after moving to Redis. A `@CacheEvict` can fail silently after the transaction commits (evict in `afterCommit` with retries, plus a TTL backstop); a new pod can pass its readiness probe before its pub/sub invalidation subscription connects (gate readiness on the subscription and keep L1 TTLs short); and a slow or replica-routed read can repopulate the cache with an old value after an evict, the race Spring declined to fix in SPR-9304 (compare versions before caching). The last gap is read-your-own-writes at the API layer, closed by returning an ETag or version on writes and bypassing the cache when the client's version is newer.

Your local dev environment lied to you. It ran one instance, one JVM, one cache. Everything invalidated cleanly because there was nowhere else for stale data to hide.

Then you shipped two instances behind a load balancer, and the cache started telling a different story to different users.

## The greenfield illusion

Here's the setup almost everyone starts with: a Spring Boot app, `@EnableCaching`. In local dev environment, with one pod, it works perfectly. Every write is immediately visible on the next read, because there is exactly one place for that data to live.

Scale to two instances behind an ingress router and the illusion breaks. A `PUT` lands on Instance A. A `GET` five seconds later lands on Instance B, because that's how load balancing works, and Instance B never saw the write. It's still holding whatever it cached ten minutes ago.

[![ ](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fws8njrhvyyh3jvx9m47r.png)](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fws8njrhvyyh3jvx9m47r.png)
*diagram 1: Two JVM instances with isolated local caches pointing at one shared database*

This is not a bug. It's the correct behavior of two independent JVMs with no shared memory, doing exactly what you told them to do. The DB is the only thing in this picture that's telling the truth, and neither cache is listening to it in real time.

Most tutorials stop here and tell you to swap in Redis. That's necessary. It's not sufficient. Redis fixes the "two separate memory spaces" problem. It does nothing for the four scenarios below, and those are the ones that actually take down production.

## Scenario 1: the invalidation call that quietly fails

`@CacheEvict` looks like a guarantee. It is not. It's a method call, and method calls fail.

Picture the sequence: your service commits a database transaction, then calls out to evict the cache entry. If that eviction call hits a network blip, a Redis connection pool exhaustion, or a two-second timeout, the eviction silently doesn't happen. The transaction already committed. Nothing rolls back. Nothing throws past your controller. Your monitoring dashboard shows 200 OK on the write endpoint, because from the caller's perspective, the write succeeded. It did. The cache just never found out.

Now the cache holds a value that will never self-correct until its TTL expires, which might be six hours from now if you set a long TTL to reduce database load (a reasonable thing to want, for the wrong reason).

A few concrete patterns that catch this instead of hoping it doesn't happen:

**Set a TTL backstop even on entries you explicitly evict.** If your write frequency for a given entity is roughly once every ten minutes, a TTL of two to three times that (20 to 30 minutes) means a dropped eviction call self-heals within half an hour instead of persisting until the next deploy.

**Move the evict call after commit, not before, and make it retry.** Spring's default behavior with `@CacheEvict(beforeInvocation=false)` already fires after the method body runs, but "after the method body runs" is not the same as "after the transaction commits" if you're inside a `@Transactional` boundary with deferred commit. Use `TransactionSynchronizationManager.registerSynchronization` to fire the evict in `afterCommit`, and wrap it in a retry with backoff:

```
@Service
public class OrderStatusService {

    private final CacheManager cacheManager;
    private final OrderRepository orderRepository;

    @Transactional
    public void updateStatus(Long orderId, String newStatus) {
        orderRepository.updateStatus(orderId, newStatus);

        if (TransactionSynchronizationManager.isActualTransactionActive()) {
            TransactionSynchronizationManager.registerSynchronization(
                new TransactionSynchronization() {
                    @Override
                    public void afterCommit() {
                        evictWithRetry(orderId, 3);
                    }
                }
            );
        } else {
            // no transaction context to hook, evict right away
            evictWithRetry(orderId, 3);
        }
    }

    private void evictWithRetry(Long orderId, int attemptsLeft) {
        try {
            cacheManager.getCache("orderStatus").evict(orderId);
        } catch (Exception ex) {
            if (attemptsLeft > 0) {
                evictWithRetry(orderId, attemptsLeft - 1);
            } else {
                // log loudly here, this entry is now relying on TTL alone
                log.error("Cache evict failed after retries for order {}", orderId, ex);
            }
        }
    }
}
```

The retry is not elegant. It's honest about the fact that eviction is a network call, and network calls fail in ways your happy-path tests will never exercise.

Note the guard around `registerSynchronization`. It only works when a transaction is actually in flight. Call `updateStatus` from a path that isn't wrapped in `@Transactional`, a batch job, a test, a refactor that strips the annotation, and `registerSynchronization` throws `IllegalStateException: Transaction synchronization is not active` instead of quietly doing nothing. Checking `isActualTransactionActive()` first means the method still evicts correctly outside a transaction, it just does it immediately instead of waiting for a commit that will never come.

There's a second version of this failure that has nothing to do with the network. `@Transactional` and `@CacheEvict` are both AOP proxies, and Spring does not guarantee which one runs first unless you set the order explicitly. Stack them on the same method and let Spring pick, and you get eviction and commit racing each other inside a single call. If the eviction fires first and the transaction rolls back afterward, the outcome is harmless: the cache is empty, and the next read repopulates it correctly from the DB. The dangerous direction is the other one. A method that writes to two cache keys and only one of them sits behind the failed step keeps the untouched write in place, because a transaction rollback undoes the database, not the cache. The `afterCommit` pattern above closes both directions at once. The evict call cannot fire before the transaction is durable, and it never fires if the transaction dies. That is the actual reason to register a `TransactionSynchronization` instead of stacking annotations and trusting Spring to run them in the order you want.

## Scenario 2: the pod that wakes up already lying

Kubernetes rolling deployments and autoscaling mean your fleet of instances is never actually static. New pods come up cold. Old ones go away mid-request. And there's a window during pod startup that most cache architecture diagrams pretend doesn't exist.

[![ ](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F97cyt7r1rjsod3u8jhu5.png)](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F97cyt7r1rjsod3u8jhu5.png)
*diagram 2: Timeline showing a two second gap between a pod passing its readiness probe and its pub/sub subscription becoming active*

Any invalidation broadcast during that window between traffic starting and the subscription connecting is silently lost, and the pod won't know until its TTL backstop expires.

Here's the timeline. At T0, the container starts. Somewhere around T0 plus 2 seconds, the readiness probe passes and Kubernetes starts routing real traffic to it. But the pod's Redis pub/sub subscription, the one it needs in order to hear "hey, this key was just invalidated," might not finish connecting until T0 plus 4 seconds. That's a two-second window where the pod is serving live reads with an empty local cache and no way to hear about invalidations happening elsewhere in the cluster.

If a write happens on another pod during that window and broadcasts an invalidation event, this pod never receives it, because it wasn't listening yet. It'll cache whatever it reads from the DB at that moment (which might already be correct) but it has no mechanism to know that a subsequent invalidation was meant for a key it hadn't even cached. The gap compounds if the write pattern is bursty right around a deploy, which, deploys being deploys, it often is.

What actually mitigates this:

- Don't mark the pod ready until the pub/sub client reports itself connected, not just until the app context loads. Wire this into your readiness probe explicitly.
- Treat the local L1 cache (Caffeine, say) as advisory and short-lived. A 30 to 60 second TTL on L1, backed by Redis as L2, means a missed invalidation during startup costs you at most a minute of staleness instead of an indefinite one.
- Log every pub/sub connection event with a timestamp relative to pod start. If you've never measured this window in your own cluster, you don't actually know if it's 200 milliseconds or 4 seconds, and the fix you need depends entirely on which one it is.

## Scenario 3: the race Spring has known about since 2012

This one isn't new. It's filed as [Spring Framework issue SPR-9304](https://github.com/spring-projects/spring-framework/issues/13942), declined rather than fixed. If you're relying on `@Cacheable` and `@CacheEvict` to coordinate with each other, they don't, not by default, and the framework maintainers have said as much for over a decade.

[![ ](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F1rnlscitemk1d1sqcthd.png)](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F1rnlscitemk1d1sqcthd.png)
*diagram 3: Timeline of a slow GET reading a stale value and overwriting a cache after a concurrent PUT already evicted it*

DB says APPROVED. Cache says PENDING. Nothing threw an error. This is the exact race described in Spring's SPR-9304, declined rather than fixed.

Walk through it in order. Thread 1 starts a slow `SELECT` at t=0ms, maybe it's hitting an unindexed column or waiting on a lock. While that read is in flight, Thread 2 runs a `PUT`: the `UPDATE` commits at t=20ms, and the `@CacheEvict` fires at t=21ms, clearing the cache entry. Everything looks fine at this point. The cache is empty, which is a safe state.

Then, at t=120ms, Thread 1's slow read finally returns. It read the row before the update happened, so it's holding the old value. Spring's `@Cacheable` does exactly what it's designed to do: it writes that value into the now-empty cache, at t=121ms. There's no eviction after this point to clean it up, because as far as the system knows, nobody wrote anything new. The cache now holds a stale value indefinitely, right next to a database that has the correct one.

Nobody threw an exception. Nothing logged an error. The only symptom is a support ticket three days later asking why a customer's order still shows "pending" after they got a confirmation email.

The slow query is not the only trigger. Plenty of Spring setups route `@Transactional(readOnly=true)` reads to a database replica through an `AbstractRoutingDataSource`, a standard way to keep load off the primary. That routing turns an ordinary GET into a race against replication lag instead of query cost. The `PUT` commits on the primary at t=20ms. A read-only `GET` lands on a replica that has not replayed that write yet, reads the old row at t=25ms, and caches it. No slow query, no lock contention, just a replica a few milliseconds behind. This version fires far more often than the slow-query version, because replication lag is a constant background condition of the architecture, not an occasional unlucky query plan. `readOnly=true` also switches Hibernate to manual flush mode for that session, so a stray write inside a read-only method fails silently instead of throwing.

The fix that actually works in practice is a short-TTL safety net combined with versioned reads, not a synchronization primitive bolted onto `@Cacheable` (Spring's cache abstraction doesn't give you a clean hook for that without writing your own `CacheInterceptor`, which is more surface area than most teams want to maintain). A version column or `updated_at` timestamp compared at write time catches the case where the read result is older than the latest write, whether that staleness came from a slow query or a lagging replica, and lets you skip writing it into the cache at all:

```
public Optional<Order> cacheAwareRead(Long orderId) {
    Order fresh = orderRepository.findById(orderId).orElseThrow();
    Long lastKnownVersion = versionTracker.getLatestVersion(orderId);

    if (lastKnownVersion != null && fresh.getVersion() < lastKnownVersion) {
        // this read is older than a write we already know happened
        // do not let it land in the cache
        return Optional.of(fresh);
    }

    cacheManager.getCache("orders").put(orderId, fresh);
    return Optional.of(fresh);
}
```

It's a small check. It closes a gap that's been sitting open in a widely used framework since 2012, which tells you this isn't a corner case, it's a structural property of caching next to a mutable store.

## Scenario 4: what your frontend doesn't know it doesn't know

Say you've handled all three scenarios above. Your backend cache is now consistent with your database within a reasonable window. There's still one more layer where staleness sneaks back in: the contract between your API and whatever's consuming it.

A user submits a form. Your frontend gets a 200 back. It then re-fetches the same resource to refresh its view, and that `GET` happens to hit a replica or a CDN edge that hasn't picked up the change yet. From the user's point of view, they just submitted something and it didn't take. That's not a backend cache bug. It's a read-your-own-writes problem, and it lives at the API contract layer.

The fix is to hand the client something it can use to demand freshness on its next call. An ETag or a version token, returned on the write response and echoed back on the next read, lets the backend decide: is the cached response older than what this client already knows about? If yes, skip the cache and hit the DB.

```
@PutMapping("/orders/{id}")
public ResponseEntity<OrderResponse> updateOrder(
        @PathVariable Long id, @RequestBody OrderUpdateRequest request) {

    Order updated = orderService.update(id, request);
    String versionToken = String.valueOf(updated.getVersion());

    return ResponseEntity.ok()
        .eTag(versionToken)
        .body(OrderResponse.from(updated));
}

@GetMapping("/orders/{id}")
public ResponseEntity<OrderResponse> getOrder(
        @PathVariable Long id,
        @RequestHeader(value = "If-None-Match", required = false) String clientVersion) {

    OrderCacheEntry cached = orderCacheService.get(id);
    String cleanClientVersion = clientVersion != null ? clientVersion.replace("\"", "") : null;

    if (cleanClientVersion != null && cached != null
            && Long.parseLong(cleanClientVersion) > cached.getVersion()) {
        // the client already knows about a write newer than what we have cached
        Order fresh = orderService.forceRead(id);
        return ResponseEntity.ok().eTag(String.valueOf(fresh.getVersion())).body(OrderResponse.from(fresh));
    }

    return ResponseEntity.ok().eTag(String.valueOf(cached.getVersion())).body(OrderResponse.from(cached));
}
```

It closes a gap that no amount of backend cache tuning touches, because the problem isn't in the backend. It's in the assumption that the client and server agree on what "current" means.

One line in that handler is doing quiet, necessary work. The HTTP spec wraps ETag values in quotes, so `If-None-Match` arrives as `"12345"`, not `12345`. Passing that straight into `Long.parseLong` throws `NumberFormatException` on every single request, which is the kind of bug that survives code review because a manual curl test with a bare number in the header works fine and the quotes only show up when a real browser or HTTP client sends them. Stripping the quotes before parsing is the difference between this shipping and this getting reverted after the first production 500.

## A checklist worth pinning to the PR template

- Does `@CacheEvict` call happen after transaction commit, with a retry on failure, or does a network blip leave it silently unevicted?
- Do you have a TTL backstop on every cache entry, even the ones you explicitly evict, sized to two or three times your typical write frequency for that entity?
- Have you measured the gap between the pod's readiness probe passing and its pub/sub client actually connecting? If you haven't measured it, you don't know if it's 200ms or 4 seconds.
- Is L1 (local, in-process) cache TTL short enough that a missed invalidation during a pod's startup window costs you a minute, not an hour?
- Does a slow read that started before a write, but finishes after it, have any way to detect that it's about to write stale data back into the cache?
- Does the API return a version token or ETag on writes, and does the read path actually check it against the client's last known version, or does it just cache-and-serve regardless?

None of these are exotic. The expensive part isn't writing the fix. It's noticing the gap exists before a customer does.
