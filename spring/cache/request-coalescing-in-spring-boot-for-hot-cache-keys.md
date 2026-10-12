---
title: "Request Coalescing in Spring Boot for Hot Cache Keys"
source: "https://alexanderobregon.substack.com/p/request-coalescing-in-spring-boot?utm_source=publication-search"
author:
  - "[[Alexander Obregon]]"
published: 2026-04-30
created: 2026-10-12
description: "Traffic spikes expose one of the hardest moments in a cache-aside flow."
tags:
  - "clippings"
---

> [!summary]
> In a cache-aside flow, concurrent misses on a hot key each reach the repository before the first `put` lands; request coalescing folds them into one in-flight lookup. Spring offers `@Cacheable(sync = true)` (a provider-dependent hint limited to one cache and no `unless`), `Cache.get(key, Callable)`, and since 6.1 `CompletableFuture` returns with Caffeine's async cache mode. For manual control, completed values live in Caffeine and running lookups in a `ConcurrentHashMap<String, CompletableFuture>` registered by a short `computeIfAbsent`, with removal in `whenComplete`'s `finally` so a failure reaches every waiter without blocking later reloads. Caffeine refresh is a different trade: it keeps serving the old value while reloading.

Traffic spikes expose one of the hardest moments in a cache-aside flow. Think about ten requests for the same product id arriving right after that entry expires, or before it has been stored in cache for the first time. Without request coalescing, all ten requests can slip past the empty cache and reach the database within the same small window. Request coalescing cuts that down by letting the first caller start the lookup while the rest wait for that same in-flight result, so they all receive the finished value instead of triggering duplicate reads. Spring’s cache abstraction already includes support for synchronized loading, and Spring Boot can auto-configure cache infrastructure after caching is turned on, but the exact way concurrent misses are folded still comes down to the cache provider and the API route you choose.

### Why Hot Cache Entries Create Repeat Misses

Heavy traffic puts pressure on the narrow slice of time between a miss and the moment a fresh value gets stored. Calls that seem harmless during a warm-cache period can turn into repeated reads during that gap, because every caller sees the same empty entry before the first lookup finishes its trip to storage. Spring cache support is built around returning a cached value after an entry already exists, but that first miss window is the part that drives duplicate database traffic.

#### How an Empty Entry Turns Into a Burst of Database Reads

Traffic against a hot entry can turn a very short gap into a pile of matching queries. The first caller checks the cache, finds nothing, and starts a database read. Then a second caller reaches the same code before the first result has come back, finds the same miss, and starts the same read. More callers can repeat that cycle until the cache finally receives a value. By then, the database may have handled the same lookup several times for the same id.

Look at a small cache-aside method:

```markup
public ProductView getProduct(String id) {
    ProductView cached = cache.getIfPresent(id);
    if (cached != null) {
        return cached;
    }

    ProductView loaded = productRepository.findViewById(id)
        .orElseThrow(() -> new ProductNotFoundException(id));

    cache.put(id, loaded);
    return loaded;
}
```

Every caller that enters this method before `cache.put(id, loaded)` runs will fall through to `productRepository.findViewById(id)`. Ten overlapping requests can produce ten repository calls for one row. Nothing unusual is happening in the method itself, and the issue comes from timing between the miss check and the later cache write.

Expiration is only one trigger. Fresh startup or the first request for an entry creates the same empty-slot state. Cache-aside logic does not care why the value is absent and just sees a miss, then starts a load. Heavy traffic around that id is what turns a brief miss into a burst of duplicate reads.

Run a short concurrency test and the repeated-read problem becomes easier to see:

```markup
ExecutorService pool = Executors.newFixedThreadPool(10);

List<Callable<ProductView>> calls =
    IntStream.range(0, 10)
        .<Callable<ProductView>>mapToObj(i -> () -> service.getProduct("p100"))
        .toList();

pool.invokeAll(calls);

System.out.println("Database reads = " + repository.readCount());
```

If the cache starts empty and repository reads take long enough to overlap, `readCount()` can climb past one very quickly. Hot entries amplify that effect because a large share of traffic is hitting the same missing slot during the same narrow span. That extra database traffic does not return new information, and it repeats the same trip until the first caller gets a value back into cache.

#### What Request Coalescing Changes

Request coalescing changes the miss sequence while leaving the hit case alone. Cached reads still return right away, but the first miss for a busy entry no longer gives every caller permission to launch a separate database fetch. The first caller begins the lookup, later callers wait for that same in-flight result, and the finished value goes back to every waiter. After the cache has been filled, later traffic returns to the normal hit case.

Spring reflects that idea through synchronized loading hooks. `Cache.get(Object, Callable<T>)` represents the common read sequence of check cache, load on miss, store the value, and return it. `@Cacheable(sync = true)` asks the cache layer to coordinate concurrent loads for the same entry, and final behavior still depends on the cache implementation, but the goal stays the same. That way, a single lookup fills the empty slot while the rest wait.

Spring exposes that idea directly:

```markup
@Cacheable(cacheNames = "products", key = "#id", sync = true)
public ProductView getProduct(String id) {
    return productRepository.findViewById(id)
        .orElseThrow(() -> new ProductNotFoundException(id));
}
```

Under concurrent traffic, callers for the same id do not all race through the repository line at the same moment. Instead, a single caller loads the value while the others wait for that result to finish. That shared wait state cuts repeat database hits during a miss storm, because the data returned to callers stays the same while the count of fetch trips during the empty-cache window drops.

Synchronized loading should be treated as its own cache behavior rather than something that appears automatically in every cache annotation case. That distinction helps frame the main point of request coalescing. It does not change the data a caller receives. It changes how the application behaves while the cache entry is still empty, so duplicate traffic gets folded into one in-flight lookup instead of being sent to storage again and again.

### Building Request Coalescing in Spring Boot

Spring Boot already gives you a strong starting place for request coalescing before any custom service logic enters the codebase. Turn caching on with `@EnableCaching`, add a cache provider such as Caffeine, and Boot will handle cache setup for you. Spring Framework also exposes both the classic `Cache.get(Object, Callable<T>)` route and future-based cache access through `CompletableFuture`, so the cache layer already has the pieces needed for folded miss handling when concurrent callers ask for the same value.

#### Where Spring Already Helps

Spring’s built-in cache support already covers more ground than people sometimes expect. `@Cacheable` handles the normal hit flow, and `sync = true` asks the cache provider to coordinate concurrent loads for the same entry instead of letting every caller run a separate read. That flag does come with limits. It supports only one cache on that method, it cannot be paired with `unless()`, and it cannot be combined with other cache operations on the same method. Spring also treats `sync = true` as a hint, so final behavior still comes down to the provider behind the annotation.

A synchronous service method can stay fairly compact when that matches the rest of the service boundary:

```markup
@Cacheable(cacheNames = "catalogItems", key = "#sku", sync = true)
public CatalogItemView getCatalogItem(String sku) {
    CatalogItem item = catalogRepository.findBySku(sku)
        .orElseThrow(() -> new CatalogItemNotFoundException(sku));

    return new CatalogItemView(item.sku(), item.name(), item.price());
}
```

That method leaves most of the coordination job to the cache layer. A stored value returns right away. On a miss, the method body runs, the result is cached, and overlapping callers for the same `sku` can be coordinated through the synchronized loading hint if the provider supports it in that form.

Lower-level cache access gives you the same basic read flow without relying on an annotation. Spring’s `Cache` interface includes `get(Object, Callable<T>)`, which represents the common sequence of checking cache state, loading on miss, storing the result, and handing that value back to the caller. That route can feel more direct in services where annotation behavior starts to hide too much of the timing.

Take a look at the same idea through the cache API:

```markup
public CatalogItemView getCatalogItem(String sku) {
    Cache cache = cacheManager.getCache("catalogItems");

    return cache.get(sku, () -> {
        CatalogItem item = catalogRepository.findBySku(sku)
            .orElseThrow(() -> new CatalogItemNotFoundException(sku));

        return new CatalogItemView(item.sku(), item.name(), item.price());
    });
}
```

Future-based methods are part of the current Spring cache story too. Spring Framework `6.1` and later can adapt `CompletableFuture` return values for cache annotations, including synchronized caching. With Caffeine through `CaffeineCacheManager`, that path needs async cache mode turned on with `setAsyncCacheMode(true)`. That becomes useful when your service already returns `CompletableFuture`, or when callers should wait on the same future instead of blocking a request thread while the miss is being resolved.

```markup
@Cacheable(cacheNames = "pricingViews", key = "#sku", sync = true)
public CompletableFuture<PricingView> getPricing(String sku) {
    return CompletableFuture.supplyAsync(() -> {
        PriceRow row = pricingRepository.findBySku(sku)
            .orElseThrow(() -> new PriceNotFoundException(sku));

        return new PricingView(row.sku(), row.amount(), row.currency());
    }, pricingExecutor);
}
```

Annotation-driven caching is a good fit when your service contract already lines up with the cache behavior you want. Manual coalescing starts to look better when you want tighter control over when the shared lookup is registered, how it is removed, where the cache write happens, or what happens after a failure.

#### Why an In-Flight Map Works So Well

Manual request coalescing becomes much easier to reason through when finished values and running lookups are kept apart. The cache answers one question. Do we already have a completed value for this id. The in-flight registry answers a different question. Is some caller already fetching that id right now. Keeping those jobs separate avoids awkward state handling and makes the read flow much easier to follow.

Most services model the registry as `ConcurrentHashMap<String, CompletableFuture<ItemView>>`. That pairing fits the job very well. `ConcurrentHashMap.computeIfAbsent` gives you an atomic way to install a shared future for a missing id, while `CompletableFuture` gives every overlapping caller a handle to the same result. Instead of juggling thread-local state or custom wait queues, the service can hand back the exact same future to every caller that arrives during the miss window.

That matters because the shared future becomes the single record of the lookup in progress. The first caller creates it. Later callers receive it. When the database call finishes, every waiter gets the same result from that same future. If the lookup fails, every waiter sees that same failure too.

Keep the map operation short, then let the database read happen after the map has returned. That detail deserves close attention because `computeIfAbsent` should register the future rather than run the full repository read inside the map callback. Short callbacks reduce lock contention inside the map and leave the control flow more readable later.

Per-instance scope deserves a quick mention too. Local in-flight maps coordinate callers only within the current application instance. If your service runs on several instances behind a load balancer, each instance will keep its own cache and its own in-flight registry. Coalescing therefore cuts repeated reads inside a given JVM, not across the full fleet. With a local memory cache, that behavior is expected.

#### Code Example

Seeing the full service in one place makes the control flow more readable than isolated fragments, at least for me it is. The example below uses a native Caffeine cache for completed values and a `ConcurrentHashMap` for lookups that are still running. The method returns `CompletableFuture<InventoryView>`, so callers can wait on the same future during a miss instead of launching duplicate repository reads.

```markup
package com.example.inventory;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executor;

@Configuration(proxyBeanMethods = false)
class InventoryCacheConfig {

    @Bean
    Cache<String, InventoryView> inventoryCache() {
        return Caffeine.newBuilder()
            .maximumSize(20_000)
            .expireAfterWrite(Duration.ofMinutes(5))
            .build();
    }

    @Bean
    Executor inventoryLookupExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(8);
        executor.setMaxPoolSize(16);
        executor.setQueueCapacity(200);
        executor.setThreadNamePrefix("inventory-lookup-");
        executor.initialize();
        return executor;
    }
}

@Service
class InventoryService {

    private final Cache<String, InventoryView> inventoryCache;
    private final InventoryRepository inventoryRepository;
    private final Executor inventoryLookupExecutor;

    private final ConcurrentHashMap<String, CompletableFuture<InventoryView>> inFlight =
        new ConcurrentHashMap<>();

    InventoryService(
        Cache<String, InventoryView> inventoryCache,
        InventoryRepository inventoryRepository,
        Executor inventoryLookupExecutor
    ) {
        this.inventoryCache = inventoryCache;
        this.inventoryRepository = inventoryRepository;
        this.inventoryLookupExecutor = inventoryLookupExecutor;
    }

    public CompletableFuture<InventoryView> getInventory(String sku) {
        InventoryView cached = inventoryCache.getIfPresent(sku);
        if (cached != null) {
            return CompletableFuture.completedFuture(cached);
        }

        return inFlight.computeIfAbsent(sku, this::startLookup);
    }

    private CompletableFuture<InventoryView> startLookup(String sku) {
        return CompletableFuture
            .supplyAsync(() -> loadInventory(sku), inventoryLookupExecutor)
            .whenComplete((value, error) -> {
                try {
                    if (error == null && value != null) {
                        inventoryCache.put(sku, value);
                    }
                } finally {
                    inFlight.remove(sku);
                }
            });
    }

    private InventoryView loadInventory(String sku) {
        InventoryRow row = inventoryRepository.findBySku(sku)
            .orElseThrow(() -> new InventoryNotFoundException(sku));

        return new InventoryView(row.sku(), row.available(), row.locationCode());
    }
}

record InventoryView(String sku, int available, String locationCode) {}

record InventoryRow(String sku, int available, String locationCode) {}

interface InventoryRepository {
    Optional<InventoryRow> findBySku(String sku);
}

class InventoryNotFoundException extends RuntimeException {
    InventoryNotFoundException(String sku) {
        super("Inventory not found for sku " + sku);
    }
}
```

Start with `getInventory`. A cache hit returns a completed future right away, so the in-flight registry is never touched for warm entries. A miss falls through to `inFlight.computeIfAbsent(sku, this::startLookup)`. That line is the hinge point of the whole section. The first caller for a missing `sku` installs a future into the map. Every later caller for that same `sku` receives the future that is already there rather than creating a fresh lookup.

`startLookup` is intentionally short. Its job is to create the future, start the repository read on an executor, and return that future immediately. The slow part happens later on the executor thread, not inside the map callback. That keeps the registry focused on coordination rather than holding map state while storage access is still in progress.

The `whenComplete` stage handles cleanup after the lookup settles. If the read finished successfully, the value is written into Caffeine. Then, in a `finally` block, the `sku` is removed from the in-flight map no matter how the future ended. That removal step is easy to underestimate, but it is what keeps the registry from holding a stale future forever. Without it, a failed or completed lookup could block all future reloads for that `sku`.

Flow through the service becomes very readable when seen in order. Warm entry means cache hit and immediate return. Cold entry means shared future registration. Successful lookup means cache fill and registry cleanup. Failed lookup means shared exception and registry cleanup. That sequence is why the map and the cache stay separate. One stores finished values. The other tracks values that are still on the way back.

#### Failure Paths

Failure handling decides how predictable the coalescing layer feels under pressure. Shared futures should share outcomes too. If the repository throws an exception while one lookup is in flight, every caller waiting on that future should receive the same exception rather than a mixture of different results from overlapping retries. That keeps the service behavior aligned with the fact that there was only one lookup in progress for that id.

Removal from the in-flight registry should happen no matter how the future completes. Successful completion needs that cleanup so later misses can register a fresh lookup after expiry. Exceptional completion needs it too, or the service can get stuck handing back a failed future forever. That is why cleanup belongs in `finally` rather than only in the success branch.

Missing-row behavior also needs a deliberate choice. Native Caffeine caches do not store `null`, so the service should not leave that case ambiguous. Throwing a not-found exception is a clean option when the API already treats missing data as an error. Another route is to return an explicit wrapper such as `Optional<InventoryView>` and cache a sentinel representation of not found if that lines up with the service contract. Either route is valid, but the code should make the rule obvious.

Refresh behavior is related, but it is not the same thing as miss coalescing. Caffeine refresh can keep returning the older cached value while a reload runs in the background. Expire-then-reload coalescing does something different. It makes callers wait on a shared future for the fresh lookup after the entry is gone. Those two choices lead to different user-visible results, so it helps to keep them mentally separate. Refresh favors continued reads of the previous value. Miss coalescing after expiry favors shared waiting for a fresh value.

Async execution also deserves a little care. Executor sizing, queue capacity, and backpressure rules still matter because coalescing only removes duplicate lookups for the same id. Heavy traffic across a large set of distinct ids can still create heavy executor usage. Coalescing cuts waste around repeated misses for a shared hot entry. It does not replace normal capacity planning for your lookup threads or data store connections.

### Conclusion

Request coalescing changes the busiest part of a cache-aside flow by treating concurrent misses for the same entry as a single lookup instead of a pile of matching reads. The first caller starts the fetch, later callers wait on that same in-flight result, the cache is filled when the read finishes, and future traffic returns to the normal hit flow. That coordination cuts repeat database trips during hot-entry misses and keeps a brief empty-cache window from turning into avoidable storage pressure.

![](https://substackcdn.com/image/fetch/$s_!BxLx!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F156ab07c-f499-45ac-b0f0-d28895f42e4a_276x276.png)

Spring Boot icon by Icons8
