---
title: "Spring Boot Read-Through Caching With Redis"
source: "https://alexanderobregon.substack.com/p/spring-boot-read-through-caching?utm_source=publication-search"
author:
  - "[[Alexander Obregon]]"
published: 2026-05-07
created: 2026-10-12
description: "Spring Boot 4 still handles this through Spring’s cache abstraction, which makes the full caching flow much easier to follow as you read through it."
tags:
  - "clippings"
---

> [!summary]
> Walks through Redis-backed read-through caching in Spring Boot 4 (Spring Framework 7): with `spring-boot-starter-cache` and `spring-boot-starter-data-redis` (Lettuce) on the classpath, Boot auto-configures a `RedisCacheManager`, and `@Cacheable` keys come from the default `KeyGenerator` unless narrowed with `key`. It swaps the default JDK serialization for Jackson 3's `GenericJacksonJsonRedisSerializer` through a `RedisCacheManagerBuilderCustomizer`. Entries never expire without `entryTtl`, and reads extend the TTL only with `enableTimeToIdle()` (Redis 6.2 `GETEX`). For busy misses, `sync = true` coordinates method calls, which is separate from the `RedisCacheWriter` choice; the locking writer locks the whole cache, not one entry.

Spring Boot 4 still handles this through Spring’s cache abstraction, which makes the full caching flow much easier to follow as you read through it. Turn caching on with `@EnableCaching`, add Redis to the application, and Boot can auto-configure a `RedisCacheManager` when Redis is present and configured. From there, you can trace the full lookup order in a natural way, from the first cache check to the database call after a miss and the cache write that follows. Spring Boot 4 is the current stable line, it builds on Spring Framework 7, the starter names still include `spring-boot-starter-cache` and `spring-boot-starter-data-redis`, and the Redis starter still uses Lettuce by default.

### How Spring Boot 4 Fits Redis Into a Read Path

Breaking the caching layer into its main parts first makes the Redis read flow easier to walk through before the request sequence gets more involved. Spring Framework provides the cache abstraction that can wrap a method call with cache behavior. Spring Boot fills in the surrounding beans when the Redis starter is on the classpath and the connection settings are present. That split lets service code stay focused on fetching data while Boot supplies the cache manager and Redis client layer around it. In the current Boot 4 line, that still means Spring Boot built on Spring Framework 7, with Redis support coming from `spring-boot-starter-data-redis`, caching turned on through `@EnableCaching`, and Lettuce serving as the default Redis client.

A good thing to note is that Spring’s cache abstraction is method-based, not table-based and not repository-based. Redis enters the lookup sequence through cache annotations placed on service methods, so the first thing to follow is the method call boundary. Spring checks a cache name, computes an entry id from the method arguments, and then decides how that invocation should proceed.

#### What the Cache Layer Really Does

Generally speaking, put `@Cacheable` on a service method and Spring treats that method as a lookup boundary. Call it with a given argument set and Spring checks the named cache before it lets the method body run. If a stored value already matches that invocation, Spring returns the cached value and skips the method body. If nothing matches, the call moves into the method body and the returned value becomes eligible for storage in the cache.

```markup
package com.example.catalog;

import org.springframework.cache.annotation.CacheConfig;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
@CacheConfig(cacheNames = "products")
public class ProductLookupService {

    private final ProductRepository productRepository;

    public ProductLookupService(ProductRepository productRepository) {
        this.productRepository = productRepository;
    }

    @Cacheable(key = "#productId")
    public ProductView findProduct(long productId) {
        return productRepository.findViewById(productId)
                .orElseThrow(() -> new IllegalArgumentException("Product " + productId + " was not found"));
    }
}
```

Class-level `@CacheConfig` keeps the cache name in one place, so the method only needs to state the lookup rule that differs at the operation level. That annotation can also share a custom `KeyGenerator`, `CacheManager`, or `CacheResolver` across the class. Even with that in place, caching still does not happen until `@EnableCaching` is turned on somewhere in the application context.

Method arguments are more important than they first appear. Spring takes those values and turns them into the Redis entry identifier unless you tell it to do something else. The default `KeyGenerator` follows a short rule set. No arguments produce `SimpleKey.EMPTY`, one argument returns that argument itself, and more than one argument produces a `SimpleKey` holding all arguments. That default fits nicely when the method signature already maps directly to a single cached lookup.

Some methods carry extra arguments that should not split the cache into separate entries. Pagination values, flags, or formatting choices are common examples. In cases like that, the annotation can narrow the identifier with the `key` attribute so the cache entry lines up with the actual lookup value rather than the full method signature.

```markup
@Cacheable(cacheNames = "products", key = "#productId")
public ProductView findProduct(long productId, boolean includeHidden, String requestedBy) {
    return productRepository.findViewById(productId)
            .orElseThrow(() -> new IllegalArgumentException("Product " + productId + " was not found"));
}
```

That version makes the cache entry depend on `productId` alone. Without the explicit `key` expression, a different `requestedBy` value or a different `includeHidden` value would produce a separate cache entry for the same product lookup. Spring is not reading repository intent and filling in that choice on your behalf. It takes the method invocation as written unless the annotation says otherwise.

Seen at the service layer, the cache abstraction wraps the call rather than replacing the service itself. Repository code still stays in the method body, exception handling still stays in the method body, and returned values still come from the method body on a cache miss. The cache layer simply decides when that method body needs to run and when a stored value can be returned instead.

#### Boot 4 Pieces You Need

Getting Boot 4 ready for Redis caching does not take a large amount of code, but each piece has a specific purpose. `spring-boot-starter-cache` brings in Spring’s caching support. `spring-boot-starter-data-redis` brings in Spring Data Redis and the default Lettuce client. With those starters present and Redis configured, Boot can auto-configure a `RedisCacheManager`, which means the first step is usually dependency setup and configuration rather than writing a cache manager by hand.

```markup
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-cache")
    implementation("org.springframework.boot:spring-boot-starter-data-redis")
}
```

Redis also has to be reachable from the application. Boot still reads connection settings from the `spring.data.redis.*` property family, and cache names can still be declared up front through `spring.cache.cache-names`. Keeping that part in configuration makes the Redis-backed cache layer easier to trace from the service annotation down to the cache manager.

```markup
spring:
  data:
    redis:
      host: localhost
      port: 6379
  cache:
    cache-names: products
```

Declaring the cache name up front gives the application a named Redis-backed cache that lines up with the `products` cache referenced in the service class. Boot also prefixes Redis cache entries by default so separate caches do not collide when the identifier text happens to be the same.

Caching still needs an explicit on switch. Putting `@EnableCaching` on a dedicated configuration class keeps that decision in a focused place instead of folding it into the main application class. That keeps the caching switch easier to follow when the application grows or when alternate contexts are loaded in tests.

```markup
package com.example.catalog;

import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
@EnableCaching
class CacheConfiguration {
}
```

Serializer choice becomes more important in Boot 4 because the Spring line moved to Jackson 3, while Spring Data Redis 4 deprecated `GenericJackson2JsonRedisSerializer` in favor of `GenericJacksonJsonRedisSerializer`. Spring Data Redis also defaults to Java native serialization for cache values unless you replace it. For a Redis cache that stores application data in a form that lines up with the current API surface, JSON is usually the better fit.

```markup
package com.example.catalog;

import org.springframework.boot.cache.autoconfigure.RedisCacheManagerBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.serializer.GenericJacksonJsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext;

@Configuration(proxyBeanMethods = false)
class RedisCacheCustomization {

    @Bean
    RedisCacheManagerBuilderCustomizer redisCacheManagerBuilderCustomizer() {
        var json = RedisSerializationContext.SerializationPair
                .fromSerializer(new GenericJacksonJsonRedisSerializer());

        return builder -> builder.withCacheConfiguration(
                "products",
                RedisCacheConfiguration.defaultCacheConfig()
                        .serializeValuesWith(json)
        );
    }
}
```

That configuration leaves Boot’s auto-configured cache manager in place while changing how values are written for the `products` cache. Boot still provides the main Redis cache infrastructure, and the customizer steps in to refine the cache configuration rather than replace the whole layer.

As a whole, the Boot 4 side of this so far is less about building a large caching subsystem from scratch and more about putting the right pieces in place. Bring in the cache starter and Redis starter, point Boot at Redis, turn caching on in configuration, and choose a value serializer that matches the current Spring Data Redis line. After that, the method annotations from the earlier subsection have a Redis-backed cache manager ready to serve them.

### What Happens on Hits, Misses, Expiration, Busy Misses

For me, runtime behavior is where the Redis cache flow started to feel tangible. Some requests return from Redis right away, some continue into the service method, some refill an entry after time has knocked it out of the cache, and some arrive close enough to each other that they all want the same missing value at nearly the same moment. Spring’s cache abstraction lays out the broad sequence, while Spring Data Redis fills in the Redis-specific expiration rules and cache writer behavior that affect how that sequence plays out.

#### Cache Hit Order

Take a call like `findProduct(17)`. Spring builds an entry id from the method arguments, checks the named cache for that id, and returns the stored value right away if Redis already has it. On that cache hit, the method body is skipped, so the repository call never runs for that request.

Boot prefixes Redis cache entries with the cache name by default. That keeps a `products` entry for `17` separate from an `orders` entry for `17`. The argument text may be the same, yet the cache names are different, so the stored Redis entries stay separate as well. That small detail prevents unrelated caches from colliding when they happen to share the same lookup value text.

Nothing unusual happens to the return type during a hit. Spring hands back the cached value as the method result, and the caller receives it in the same form it would receive from the method body. From the caller’s point of view, the service still returns a normal application object. The difference is that the earlier request already paid the cost of loading and storing that value.

This controller and service pair makes the hit order easier to trace:

```markup
package com.example.catalog;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ProductController {

    private final ProductReadService productReadService;

    public ProductController(ProductReadService productReadService) {
        this.productReadService = productReadService;
    }

    @GetMapping("/products/{id}")
    public ProductView getProduct(@PathVariable long id) {
        return productReadService.findProduct(id);
    }
}
```

```markup
package com.example.catalog;

import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
public class ProductReadService {

    private final ProductRepository productRepository;

    public ProductReadService(ProductRepository productRepository) {
        this.productRepository = productRepository;
    }

    @Cacheable(cacheNames = "products", key = "#id")
    public ProductView findProduct(long id) {
        return productRepository.findViewById(id)
                .orElseThrow(() -> new IllegalArgumentException("Product " + id + " was not found"));
    }
}
```

The controller calls the service method. Spring checks the `products` cache before the method body runs. If Redis already holds an entry for that `id`, Spring returns it and the repository line is never reached.

#### Miss Flow

Redis misses move the request farther into the service layer. When no stored value is found for the lookup, Spring lets the method body run. The service then loads from its backing store, returns the result, and Spring places that returned value into the cache before sending it back to the caller.

That sequence matters because the repository is not writing into Redis directly. The method body focuses on loading data and returning it. Spring handles the cache write after the method returns. Keeping those jobs separate makes the read flow easier to reason through when you look at a cache miss from start to finish.

For example, this service method keeps that miss flow easy to read:

```markup
package com.example.pricing;

import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
public class PriceReadService {

    private final PriceRepository priceRepository;

    public PriceReadService(PriceRepository priceRepository) {
        this.priceRepository = priceRepository;
    }

    @Cacheable(cacheNames = "prices", key = "#sku")
    public PriceView findPrice(String sku) {
        return priceRepository.findViewBySku(sku)
                .orElseThrow(() -> new IllegalArgumentException("Price " + sku + " was not found"));
    }
}
```

With no matching `prices` entry in Redis, Spring calls `findPrice`, the repository lookup runs, and the returned `PriceView` is stored in the cache. Later calls for that same SKU can stop at Redis instead of repeating the repository read. That is why the first request and the next request for the same lookup can have very different database cost while still returning the same value to the caller.

Cache population after a miss follows the method return value, so the return value itself becomes part of the cache story. Throw an exception and nothing is written. Return an object and that object becomes the cache entry. Return `null` and cache behavior then depends on how the cache has been configured for `null` values. That is one reason cache configuration decisions matter beyond the annotation alone.

#### Stale Entry Timing

Cached data stays current only for as long as its entry lifetime allows. Spring Data Redis defaults to no expiration for cache entries, which means a stored value can remain in Redis until code replaces it, code removes it, or the cache is cleared. With no TTL configured, Redis does not start a countdown for that entry. Add a TTL and that open-ended lifetime turns into storage with an expiration clock attached. Spring Data Redis applies TTL when an entry is written, and a later write resets the TTL from that new write time. Reads by themselves do not push that deadline forward. So a value written with a five-minute TTL still expires five minutes later if requests only read it during that span and nothing writes it again.

This configuration gives a cache a fixed TTL:

```markup
package com.example.catalog;

import java.time.Duration;

import org.springframework.boot.cache.autoconfigure.RedisCacheManagerBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;

@Configuration(proxyBeanMethods = false)
class CatalogCacheTtlConfiguration {

    @Bean
    RedisCacheManagerBuilderCustomizer catalogCacheTtlCustomizer() {
        return builder -> builder.withCacheConfiguration(
                "catalog-pages",
                RedisCacheConfiguration.defaultCacheConfig()
                        .entryTtl(Duration.ofMinutes(5))
        );
    }
}
```

With that in place, every `catalog-pages` entry gets five minutes in Redis from the time it is written. Write the same entry again before those five minutes run out and the timer starts fresh from the new write. Leave it alone except for reads and Redis removes it when that TTL ends.

Time alone is not the only way cached data becomes stale. Source data can change while the cached entry is still alive. That leaves the cache holding an older value until the TTL runs out unless code updates or removes the entry earlier. `@CachePut` writes the returned value into the cache after the method body runs, while `@CacheEvict` removes the entry so the later read has to load it again.

Here, the service shows both of those write-side actions:

```markup
package com.example.catalog;

import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.CachePut;
import org.springframework.stereotype.Service;

@Service
public class ProductWriteService {

    private final ProductRepository productRepository;

    public ProductWriteService(ProductRepository productRepository) {
        this.productRepository = productRepository;
    }

    @CachePut(cacheNames = "products", key = "#result.id")
    public ProductView refreshProduct(long id) {
        return productRepository.findViewById(id)
                .orElseThrow(() -> new IllegalArgumentException("Product " + id + " was not found"));
    }

    @CacheEvict(cacheNames = "products", key = "#id")
    public void evictProduct(long id) {
    }
}
```

`refreshProduct` still runs the method body and then writes the returned `ProductView` into the cache. `evictProduct` removes the stored value for that id. Those two annotations become useful when time-based expiration alone is not enough to keep cached data lined up with source changes.

Spring Data Redis can also support time-to-idle style behavior, but Redis does not provide true TTI by itself. Spring Data Redis handles that by resetting expiration during cache reads through Redis `GETEX`, and that feature has to be turned on explicitly with TTL configured as well.

This is what that looks like:

```markup
package com.example.inventory;

import java.time.Duration;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;

@Configuration(proxyBeanMethods = false)
class InventoryCacheTtiConfiguration {

    @Bean
    RedisCacheConfiguration inventoryCacheConfiguration() {
        return RedisCacheConfiguration.defaultCacheConfig()
                .entryTtl(Duration.ofMinutes(10))
                .enableTimeToIdle();
    }
}
```

With TTI-like behavior active, a read through the cache layer can refresh the expiration window. That only holds up if the application keeps reading that entry through expiration-aware cache access. Read the same Redis value through some other route that does not refresh expiration and the idle-style expectation falls apart. Redis `GETEX` is available in Redis `6.2` and later, so that server support is part of the story too.

#### Several Requests for One Missing Value

Busy misses are where request timing starts to matter. Spring’s default cache behavior does not place a lock around a missing entry. If several threads ask for the same lookup at nearly the same moment, the same value can be computed more than once, and more than one thread can reach the backing store before the cache finally holds the result.

`sync = true` on `@Cacheable` narrows that problem. With synchronized caching turned on for that method, Spring asks the cache provider to coordinate those calls so a single thread computes the value while the others wait for the cache entry to be filled.

Looking at the service code helps make that miss sequence make more sense:

```markup
package com.example.inventory;

import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
public class InventoryReadService {

    private final InventoryRepository inventoryRepository;

    public InventoryReadService(InventoryRepository inventoryRepository) {
        this.inventoryRepository = inventoryRepository;
    }

    @Cacheable(cacheNames = "inventory-snapshots", key = "#sku", sync = true)
    public InventorySnapshot findSnapshot(String sku) {
        return inventoryRepository.findSnapshotBySku(sku)
                .orElseThrow(() -> new IllegalArgumentException("Inventory " + sku + " was not found"));
    }
}
```

Put `sync = true` on a hot lookup like this and a burst of concurrent requests for the same missing SKU no longer has to send every thread through the repository call. Spring coordinates those calls so the first thread loads the value and the waiting threads receive the cached result after the entry has been written.

Redis adds a second layer to this story through the cache writer. Spring Data Redis defaults to a lock-free `RedisCacheWriter`, which improves throughput but can permit overlapping multi-command sequences for operations like `putIfAbsent` and cache clearing. Spring Data Redis also provides a locking writer, but that lock applies at the cache level rather than the individual cache entry level, so it is a heavier form of coordination.

That distinction helps keep two related ideas separate. `sync = true` changes how Spring coordinates concurrent method calls for the same missing lookup. The Redis cache writer setting changes how Redis cache operations are carried out behind that layer. Both affect busy misses, but they are not the same mechanism and they do not act at the same level.

### Conclusion

Read-through caching with Redis in Spring Boot comes down to a repeatable flow. Spring checks the cache before the service method runs, falls through to the data source when no entry is found, stores the returned value after that read, and then relies on entry lifetime, refresh calls, eviction, and request coordination to control how long data stays in Redis and how repeated traffic behaves around missing entries. Follow that flow from method call to cached return value, and the mechanics of the cache layer stay readable from start to finish.

![](https://substackcdn.com/image/fetch/$s_!BmSP!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Ff3d55e0c-5bd5-4111-8e7c-08580bdee1fa_276x276.png)

Spring Boot icon by Icons8
