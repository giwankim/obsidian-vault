---
title: "Cache Stampede Control in Spring Boot With Single Flight"
source: "https://alexanderobregon.substack.com/p/cache-stampede-control-in-spring?utm_source=publication-search"
author:
  - "[[Alexander Obregon]]"
published: 2026-06-25
created: 2026-10-12
description: "Cache-backed services can break down when a popular value expires and a rush of requests misses the cache at the same time."
tags:
  - "clippings"
---

> [!summary]
> When a hot entry expires, every caller that passes the `getIfPresent` check before `put` runs repeats the same database read. Single flight makes the first caller own the load for that key while matching callers wait on its result (shown with a `ConcurrentHashMap<String, CompletableFuture>` gate); in Spring Boot the same behavior comes from `@Cacheable(sync = true)` or Caffeine's atomic `cache.get(id, loader)`. The guard has to start before the load, last until the cache fills or the load fails, and stay scoped to one entry. A local cache protects only its own instance, so cluster-wide dedup needs shared coordination.

Cache-backed services can break down when a popular value expires and a rush of requests misses the cache at the same time. Instead of one database read filling the cache, every caller can run the same read for the same item. Single flight closes that miss window by letting the first caller start the load for a lookup id while matching callers wait for the result. After the load finishes, the cache stores the value and the waiting callers receive that value rather than starting more reads. The timing has to be tight. The guard starts before the expensive load begins, ends after the cache has a value or the load fails, and applies to the requested entry rather than the whole cache. In Spring Boot, that flow can come from Spring cache synchronization on a service method or from a Caffeine cache that performs atomic get-or-load behavior for the same lookup id.

### Why Single Flight Stops the Stampede

Repeated database reads usually appear during the smallest part of a cache request, the gap between a miss and the cache refill. That tiny gap can get expensive when the missing value is popular. Single flight gives that gap a rule. The first caller that notices the miss owns the load for that cache entry, and matching callers reuse the result from that active load instead of starting duplicate reads. The cache still behaves like a cache, but the miss path gets coordination instead of letting traffic fan out into the database.

#### Cache Miss Fan Out

Most cache reads feel harmless while traffic is low. We check the cache, find no value, read from the database, store the result, and return it to the caller. With a single request, that sequence does not create much pressure. Trouble starts when several callers ask for the same entry before the first database read has finished. The unsafe flow usually comes from separating the cache read, the database load, and the cache write into three independent steps. Every caller can pass the cache check before any caller reaches the cache write. At that point, the cache has no shared record of the load already running, so the database receives repeated reads for the same lookup id.

The unsafe version looks like this:

```markup
package com.alex.demo.products;

import java.time.Duration;
import java.util.NoSuchElementException;

import org.springframework.stereotype.Service;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;

@Service
public class ProductLookupService {
    private final ProductRepository repository;

    private final Cache<String, ProductView> products = Caffeine.newBuilder()
            .maximumSize(10_000)
            .expireAfterWrite(Duration.ofMinutes(5))
            .build();

    public ProductLookupService(ProductRepository repository) {
        this.repository = repository;
    }

    public ProductView findProduct(String productId) {
        ProductView cached = products.getIfPresent(productId);

        if (cached != null) {
            return cached;
        }

        ProductView loaded = repository.findViewById(productId)
                .orElseThrow(NoSuchElementException::new);

        products.put(productId, loaded);

        return loaded;
    }
}
```

The gap is not in the cache hit. The gap opens after `getIfPresent(productId)` returns `null` and before `products.put(productId, loaded)` runs. During that time, every caller that reaches the method can make the same decision. The cache has no value, so the service goes to the repository.

This code can pass local testing because one manual request usually finishes before the next one starts. Traffic changes the timing. Alex asks for product `P100`, sees a miss, and starts a database read. Kaitlyn asks for `P100` a few milliseconds later, sees the same miss, and starts the same read. Pippin follows with the same lookup id, and the repository gets hit again. The cache will eventually contain the value, but the extra reads have already happened during the refill window.

Those duplicated reads are wasteful because they have the same input and should produce the same cached result. The database does not get extra useful information from several matching reads for product `P100`. It only spends more time answering the same question while the cache is waiting to be refilled.

We can add a small timing log to make the fan out easier to see:

```markup
package com.alex.demo.products;

import java.time.Instant;
import java.util.NoSuchElementException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class ProductDebugService {
    private static final Logger log = LoggerFactory.getLogger(ProductDebugService.class);

    private final ProductRepository repository;

    public ProductDebugService(ProductRepository repository) {
        this.repository = repository;
    }

    public ProductView loadFromDatabase(String productId) {
        log.info("Database read started for product {} at {}", productId, Instant.now());

        return repository.findViewById(productId)
                .orElseThrow(NoSuchElementException::new);
    }
}
```

If the same product id appears in the log several times within the same short window, the cache is not reducing database pressure during the miss. That does not always mean the cache stores the wrong value. The stored value can still serve later requests correctly. The problem is narrower than that. The refill path allows duplicate reads while the value is still absent.

Cache expiration makes this easier to trigger. Hot entries can receive constant hits for several minutes, then expire during a busy moment. The next request starts the refill, but the requests already queued behind it also see a miss unless something coordinates them. Higher traffic makes the problem louder because more callers can fit inside the same miss window.

#### Single Flight Per Entry

Single flight changes the miss path from every caller can load to one caller loads for this entry. The first caller that reaches the miss starts the loader. Matching callers for the same lookup id attach to that active load. They do not call the repository while the first load is still running.

The coordination stays narrow. Product `P100` should not block product `P200`, because those are separate cache entries and can load at the same time. Only callers asking for the entry already being loaded need to wait. That is why single flight fits hot cache entries so well. It collapses duplicate reads without stopping unrelated reads.

We can represent the basic rule with an in-flight map. This is not the final Spring cache version, but it visually shows the behavior we want during a miss:

```markup
package com.alex.demo.products;

import java.util.NoSuchElementException;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.stereotype.Service;

@Service
public class ProductSingleFlightGate {
    private final ProductRepository repository;
    private final ConcurrentHashMap<String, CompletableFuture<ProductView>> inFlight = new ConcurrentHashMap<>();

    public ProductSingleFlightGate(ProductRepository repository) {
        this.repository = repository;
    }

    public ProductView loadOnce(String productId) {
        CompletableFuture<ProductView> current = inFlight.computeIfAbsent(
                productId,
                id -> CompletableFuture.supplyAsync(() -> loadFromDatabase(id))
        );

        try {
            return current.join();
        } finally {
            inFlight.remove(productId, current);
        }
    }

    private ProductView loadFromDatabase(String productId) {
        return repository.findViewById(productId)
                .orElseThrow(NoSuchElementException::new);
    }
}
```

The main rule is visible in `computeIfAbsent`. The first caller creates the `CompletableFuture` for that product id. Later callers with the same product id receive the existing future and wait for its result. Requests for a different id get a different future, so their loads stay independent.

Spring cache synchronization or cache-provider support is usually a better place for this behavior than a hand-written gate around every method. The point in this section is the rule itself. We want one active loader per entry, not one loader per caller.

That rule changes the cost of a hot miss. Without single flight, ten matching callers can create ten repository reads before the cache is filled. With single flight, the first caller creates the repository read and the other callers wait for the result tied to that lookup id. After the value is available, the cache can serve later callers from memory until expiration or eviction removes the entry.

Single flight has the most value when the lookup is expensive, repeated, and safe to share for one cache entry. Product summaries, public catalog data, feature configuration, tenant settings, permission snapshots, and similar read models can fit that profile when the method input fully identifies the cached value. The caller does not need a private load if the input is the same and the returned value belongs to that cache entry.

The cache stampede stops because the database no longer has to answer the same cache miss again and again during the refill window. The cache still needs a sensible expiration policy, and the loader still needs normal failure handling, but the repeated-read burst gets removed from the hottest part of the request path.

### Building the Flow in Spring Boot

Spring Boot gives the cache layer a practical place in the service read path. We can let Spring’s cache abstraction guard a method call, or we can call Caffeine directly when the service needs closer control over the local cache. Both versions keep the expensive loader behind a cache entry so the first miss starts the load and matching callers don’t create extra repository reads.

#### Spring Cache Synchronization

Method-level caching fits well when the method arguments identify the cached value and the method return value is the value we want to store. We keep the service method focused on loading the value from the repository, while the cache layer decides if the method needs to run.

The cache support starts with `@EnableCaching`. A small configuration class keeps that concern separate from the main application class:

```markup
package com.alex.demo.config;

import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
@EnableCaching
public class CacheConfiguration {
}
```

With caching active, Spring can intercept annotated service methods. On a cache hit, the method body does not run. On a miss, Spring lets the method run, stores the returned value, and sends that value back to the caller. The `sync = true` setting changes the miss behavior for matching arguments, so one caller computes the value while callers asking for the same cached entry wait.

```markup
package com.alex.demo.products;

import java.util.NoSuchElementException;

import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }

    @Cacheable(cacheNames = "products", key = "#productId", sync = true)
    public ProductView findProduct(String productId) {
        return repository.findViewById(productId)
                .orElseThrow(NoSuchElementException::new);
    }
}
```

The annotation has separate cache decisions in one place. `cacheNames = "products"` points to the cache region, and `key = "#productId"` tells Spring which argument identifies the entry inside that cache. The `sync = true` part belongs to the miss window. If several callers ask for the same product id while the value is absent, Spring coordinates the cache operation so the loader does not run repeatedly for the same entry.

Cache provider settings can live in properties. Caffeine fits this style well because it supports size limits, expiration, and Spring Boot cache auto-configuration can connect it to the cache abstraction.

```markup
spring.cache.type=caffeine
spring.cache.cache-names=products
spring.cache.caffeine.spec=maximumSize=10000,expireAfterWrite=300s
```

Those settings create a named `products` cache with a maximum entry count and a write-based expiration time. The expiration time controls how long a stored value can remain after it’s written. The single-flight part controls what happens when that value is missing and several matching callers arrive before the cache has been refilled.

#### Caffeine Atomic Loading

Direct Caffeine access is useful when the service needs to hold the cache object, read cache stats, invalidate entries manually, or keep the loading logic outside annotation-based caching. The important change from the unsafe read path is that we don’t split the miss into separate `getIfPresent`, repository call, and `put` steps. We let the cache perform the get-or-load operation as one cache action.

The cache settings can live in a dedicated bean:

```markup
package com.alex.demo.config;

import java.time.Duration;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import com.alex.demo.products.ProductView;
import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;

@Configuration(proxyBeanMethods = false)
public class ProductCacheConfiguration {
    @Bean
    Cache<String, ProductView> productCache() {
        return Caffeine.newBuilder()
                .maximumSize(10_000)
                .expireAfterWrite(Duration.ofMinutes(5))
                .recordStats()
                .build();
    }
}
```

The service receives the cache and calls `get(productId, this::loadProduct)`. That call is the center of the flow. If the value is present, Caffeine returns it. If the value is absent, Caffeine calls the mapping function for that entry and returns the loaded value.

```markup
package com.alex.demo.products;

import java.util.NoSuchElementException;

import org.springframework.stereotype.Service;

import com.github.benmanes.caffeine.cache.Cache;

@Service
public class ProductLookupService {
    private final ProductRepository repository;
    private final Cache<String, ProductView> productCache;

    public ProductLookupService(
            ProductRepository repository,
            Cache<String, ProductView> productCache) {
        this.repository = repository;
        this.productCache = productCache;
    }

    public ProductView findProduct(String productId) {
        return productCache.get(productId, this::loadProduct);
    }

    private ProductView loadProduct(String productId) {
        return repository.findViewById(productId)
                .orElseThrow(NoSuchElementException::new);
    }
}
```

The service no longer has a manual miss gap in its own code. We are not checking for absence, leaving the method open to matching callers, then writing the value afterward. The cache call owns that section, so callers asking for the same entry don’t all get a chance to run the repository call before the cache is filled.

Manual invalidation still has a place when the backing data changes. If a product update happens through the same service boundary, we can remove the cache entry so the next read reloads the fresh value.

```markup
package com.alex.demo.products;

import org.springframework.stereotype.Service;

import com.github.benmanes.caffeine.cache.Cache;

@Service
public class ProductUpdateService {
    private final ProductRepository repository;
    private final Cache<String, ProductView> productCache;

    public ProductUpdateService(
            ProductRepository repository,
            Cache<String, ProductView> productCache) {
        this.repository = repository;
        this.productCache = productCache;
    }

    public void renameProduct(String productId, String name) {
        repository.updateName(productId, name);
        productCache.invalidate(productId);
    }
}
```

That invalidation does not replace single flight. It deals with freshness after a write. Single flight deals with duplicate reads during a missing entry load. Both touch the same cache entry, but they answer different timing problems.

#### Waiting Caller Flow

Callers waiting behind a single in-flight load still follow a normal request path. They don’t get a stale response from single flight by default, and they don’t skip the cache. They wait for the same load that the first caller started for the matching entry.

We can read the flow through one hot product lookup. The first request asks for `P100` and finds no cached value. That request becomes the loader and calls the repository. While that read is still active, the next request for `P100` reaches the same cache entry and waits. More matching requests do the same. When the repository call finishes, the cache stores the value and the waiting callers receive that loaded value.

A small controller keeps the public request path easy to deal with while the service handles the cache read:

```markup
package com.alex.demo.products;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ProductController {
    private final ProductLookupService lookupService;

    public ProductController(ProductLookupService lookupService) {
        this.lookupService = lookupService;
    }

    @GetMapping("/products/{productId}")
    public ProductView findProduct(@PathVariable String productId) {
        return lookupService.findProduct(productId);
    }
}
```

The controller does not need special branching for cache hits, misses, or waiting callers. That belongs inside the service and cache layer. From the controller’s point of view, `findProduct(productId)` returns the product view or fails through the normal exception path.

The waiting flow trades duplicate backend calls for request waiting time. If the database read takes a small amount of time, matching callers may wait for that same amount rather than creating their own reads. That trade usually fits hot cache entries because the database sees one read for the entry instead of a burst of equal reads. The caller still gets the loaded value, while the backend avoids answering the same lookup again and again.

Errors should still behave like errors. If the loader fails, waiting callers should receive the failure from that active load instead of waiting forever. A later request can retry after the failed load is no longer active. That retry is important for brief database or network failures because a failed load should not poison the entry forever.

#### Lock Timing

The guard around the load has to begin before the repository call starts. If the guard appears after the repository call begins, matching callers can still slip through and start duplicate reads. It also needs to last until the cache has a value or the load fails. Ending the guard too early can wake waiting callers while the entry is still empty.

With `@Cacheable(sync = true)`, Spring handles that timing around the annotated method call. With direct Caffeine access, the cache handles the timing around `get(productId, this::loadProduct)`. In both cases, the service should keep expensive loading inside the guarded cache operation.

This guarded version keeps the expensive part inside the cache operation:

```markup
package com.alex.demo.products;

import java.util.NoSuchElementException;

import org.springframework.stereotype.Service;

import com.github.benmanes.caffeine.cache.Cache;

@Service
public class ProductPriceService {
    private final ProductPriceRepository repository;
    private final Cache<String, ProductPriceView> priceCache;

    public ProductPriceService(
            ProductPriceRepository repository,
            Cache<String, ProductPriceView> priceCache) {
        this.repository = repository;
        this.priceCache = priceCache;
    }

    public ProductPriceView findPrice(String productId) {
        return priceCache.get(productId, this::loadPrice);
    }

    private ProductPriceView loadPrice(String productId) {
        return repository.findCurrentPrice(productId)
                .orElseThrow(NoSuchElementException::new);
    }
}
```

The cache call wraps the miss and load for that product id. We are not loading the value first and then asking the cache to store it. The entry’s missing state, the loader, and the cached result all pass through the same cache operation.

The guard also needs the right scope. It should apply to the entry being loaded, not every entry in the cache. If `P100` is loading, requests for `P200` should not wait behind it. Entry-scoped coordination keeps hot-id protection from turning into a global bottleneck.

Failure cleanup belongs to the same timing conversation. When the loader throws, the active load should no longer be treated as the current result for that entry. Later callers need a chance to retry instead of being tied to a failed in-flight value. Cache-provider loading and Spring cache synchronization handle that through their own cache operation rules, which makes them safer than placing a hand-written global lock around repository calls.

#### Hot Entry Read Protection

Entries with constant traffic are the place where single flight gives the most protection. Low-traffic cache entries usually do not create much pressure when they expire, because only a few requests are likely to arrive during the refill window. Product records, tenant settings, permission views, and pricing records can behave differently because the same lookup id may be requested again and again.

Expiration is normal cache behavior. The pressure comes from the request pileup that can arrive before the replacement value has been stored. Single flight keeps that pileup from turning into repeated database reads for the same entry. The first caller reloads the value, and matching callers wait for that result.

We can show the same protection with a small read service for tenant settings:

```markup
package com.alex.demo.tenants;

import java.util.NoSuchElementException;

import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
public class TenantSettingsService {
    private final TenantSettingsRepository repository;

    public TenantSettingsService(TenantSettingsRepository repository) {
        this.repository = repository;
    }

    @Cacheable(cacheNames = "tenantSettings", key = "#tenantId", sync = true)
    public TenantSettingsView findSettings(String tenantId) {
        return repository.findSettingsView(tenantId)
                .orElseThrow(NoSuchElementException::new);
    }
}
```

Hot tenants can have several request paths reading the same settings. If the entry expires, those paths can all reach the service at nearly the same time. The synchronized cache miss lets one load refill the entry while matching reads wait for the same value.

Local cache protection applies inside one application instance. If the service runs on several instances, each instance has its own local Caffeine cache unless the application also has a shared cache layer. Single flight inside one instance still reduces duplicate loads within that process, which can cut down the per-instance read burst during hot traffic. Cluster-wide duplicate load control needs a shared coordination layer, but local single flight still gives the application useful protection against repeated reads inside each running instance.

Hot entries also need sensible size and expiration settings. TTL values that are too short can make the same entry reload constantly. Maximum size limits that are too small can evict useful hot entries under pressure. Single flight controls duplicate loads during a miss, while cache sizing and expiration decide how often those misses happen.

#### Conclusion

Single flight controls a cache stampede by changing the miss path instead of only relying on the stored value after a refill. The first caller for a missing entry starts the loader, matching callers wait for that same result, and the guard stays active until the cache receives the value or the load fails. In Spring Boot, `@Cacheable(sync = true)` can place that coordination around a service method, while Caffeine’s `get(id, loader)` keeps the lookup and load inside a single cache operation. That timing is what keeps hot entries from turning expiration or eviction into repeated database reads for the same lookup id.

![](https://substackcdn.com/image/fetch/$s_!PzL4!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F478bf768-0dac-4835-b0e3-5cae0acc8098_276x276.png)

Spring Boot icon by Icons8
