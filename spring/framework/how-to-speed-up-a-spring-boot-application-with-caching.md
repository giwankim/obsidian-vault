---
title: "How to Speed Up a Spring Boot Application with Caching"
source: "https://medium.com/@AlexanderObregon/how-to-speed-up-a-spring-boot-application-with-caching-b6372cba82b6"
author:
  - "[[Alexander Obregon]]"
published: 2026-08-26
created: 2026-09-05
description: "More"
tags:
  - "clippings"
---

> [!summary]
> Introduces Spring's method-level cache abstraction: `@EnableCaching`, `@Cacheable` for repeated reads, `@CachePut` with `key = "#id"` to refresh an entry on update, and `@CacheEvict` (targeted or `allEntries`) on delete. Flags the proxy pitfall where same-bean internal calls bypass cache annotations, and recommends caching small view records rather than JPA entities. Compares Caffeine (in-JVM, per-instance, tuned via `spring.cache.caffeine.spec` with `maximumSize`/`expireAfterWrite`) against Redis (shared across instances, needs an explicit `time-to-live` and `Serializable` values).

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*o5FmjKTPdJTbhGE2MIjo6w.jpeg)

Image Source

Repeated database queries and remote API calls can take up a large share of the time spent handling a Spring Boot request. Caching gives the application a faster place to read data it has already fetched or calculated, which can cut down on repeated trips to a database or external service. Spring’s cache abstraction operates at the method level, so the service method can keep its normal return type while Spring checks the cache before the method body runs. If a matching entry is already stored, Spring returns that value without running the method again. If no entry is found, the method runs normally, Spring stores the result, and later calls for the same input can receive that cached value. This is good for read operations where the same input is requested repeatedly and the returned data can stay valid for a set amount of time. After caching is activated, Spring Boot can configure the cache infrastructure automatically, while the cache provider determines where entries are stored and how long they remain available.

*You can also check out my* [*Substack*](https://alexanderobregon.substack.com/)*, where I post more articles like this and keep a* [*Java/JVM section*](https://alexanderobregon.substack.com/s/java) *with related posts. I publish my weekly recaps there too!*

## Adding Cache Support to an Existing Service

Spring’s cache abstraction lets an existing service keep its normal method signatures while cache behavior wraps selected calls. The service can still ask a repository for product data or call an external client for supplier information, while Spring checks for a stored result before certain method bodies run. This keeps cache handling close to the service operation that benefits from it instead of spreading cache access through controllers and repositories. We can add the cache infrastructure first, activate annotation processing, then mark read and write methods that should store, refresh, or remove entries.

### Adding the Cache Dependency

Spring Boot gives us `spring-boot-starter-cache` for the infrastructure behind Spring’s cache annotations. An existing web or data application can add the starter without changing its controller contract, repository interface, or service return types. Spring’s abstraction then communicates with the cache provider through `Cache` and `CacheManager`, while our service code stays centered on annotations such as `@Cacheable`, `@CachePut`, and `@CacheEvict`.

For a Caffeine-backed cache, the Maven dependencies can be added like this:

```rb
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-cache</artifactId>
</dependency>

<dependency>
    <groupId>com.github.ben-manes.caffeine</groupId>
    <artifactId>caffeine</artifactId>
</dependency>
```

Caching can then be activated in a configuration class:

```rb
package com.example.store.config;

import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
@EnableCaching
public class CacheConfiguration {
}
```

Spring now processes cache annotations on managed beans. The default annotation mode relies on Spring proxies, which means a cached public method needs to be called through its Spring-managed proxy for the annotation to take effect. Calls coming from a controller or from a different Spring bean follow that route normally.

Direct calls from one method to a second cached method inside the same bean behave differently because that internal call does not pass through the proxy. If `loadProduct()` directly calls `findById()` inside the same service class, the cache annotation on `findById()` will not intercept that internal call under the default proxy mode. Keeping cached service operations callable from other Spring beans avoids that issue without changing the service’s public contract.

If no supported provider is present, Spring Boot can fall back to an in-memory concurrent-map cache. That fallback is handy for initial development and small tests, but production applications normally select a provider that fits their deployment and data needs.

### Caching Repeated Reads

Repeated reads are where `@Cacheable` has the most immediate effect. Think about a product page that receives repeated requests for the same product during the day. Without caching, every request can reach the repository and repeat the same database query while the product data remains unchanged. With `@Cacheable`, Spring checks the named cache before the method body runs and returns the stored result if a matching entry already exists.

We can keep the cached value focused on what callers need by returning a small service-level record instead of caching the persistence entity itself.

```rb
package com.example.store.product;

import java.math.BigDecimal;

public record ProductView(
        Long id,
        String name,
        BigDecimal price
) {
}
```

This record carries only the values required by callers of the service. The JPA entity can remain focused on persistence behavior, while the cached value stays independent from entity state and persistence context details.

The service method can then apply `@Cacheable` to the database read.

```rb
package com.example.store.product;

import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
public class ProductService {

    private final ProductRepository productRepository;

    public ProductService(ProductRepository productRepository) {
        this.productRepository = productRepository;
    }

    @Cacheable(cacheNames = "products")
    public ProductView findById(Long id) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException(id));

        return new ProductView(
                product.getId(),
                product.getName(),
                product.getPrice()
        );
    }
}
```

The first call to `findById(1001L)` does not have a stored entry yet, so we still reach the repository. After the repository returns the product, the method creates a `ProductView`, and Spring stores that returned value in the `products` cache. Later calls with `1001L` can receive the cached `ProductView` before the method body runs, which removes the repeated repository call from those requests.

Spring derives the cache entry identifier from the method arguments when we do not provide a custom expression. With a single `Long id` parameter, that ID distinguishes one cached product from the next. Two different IDs therefore lead to two different entries inside the same named cache.

The same idea applies to remote API calls. If a supplier lookup repeatedly requests data for the same supplier, the returned object can be cached at the service boundary.

```rb
@Cacheable(cacheNames = "suppliers")
public SupplierView findSupplier(Long supplierId) {
    return supplierClient.fetchSupplier(supplierId);
}
```

The first call for a given `supplierId` still reaches the remote service, and Spring stores the returned `SupplierView`. Later calls with that same ID can receive the stored result without sending the HTTP request again. Callers continue invoking `findSupplier()` normally, so cache handling does not leak into the controller or client-facing code.

`@Cacheable` fits methods where repeated calls with the same relevant input can reuse the same logical result for some period of time. Methods that depend on changing state not represented by their arguments are poor candidates because the cache lookup cannot account for information it never receives. Exceptions also do not produce a normal return value for Spring to store, so a failed repository or client call does not become a regular cached result through `@Cacheable`.

### Refreshing Cached Values

Cached reads can become stale after the database changes, which is why update methods need to keep the cached entry aligned with the newly saved data. `@CachePut` handles that case by allowing the method body to run every time and then storing its returned value in the named cache.

We can apply it to an update method that saves the product and returns the same `ProductView` type as the read method. Like this:

```rb
@CachePut(cacheNames = "products", key = "#id")
public ProductView updateProduct(
        Long id,
        ProductUpdateRequest request
) {
    Product product = productRepository.findById(id)
            .orElseThrow(() -> new ProductNotFoundException(id));

    product.setName(request.name());
    product.setPrice(request.price());

    Product saved = productRepository.save(product);

    return new ProductView(
            saved.getId(),
            saved.getName(),
            saved.getPrice()
    );
}
```

The database update still runs on every call to `updateProduct()`. After `save()` returns, Spring takes the returned `ProductView` and places it into the `products` cache for the product identified by `id`. The next call to `findById(id)` can then receive the newly cached value instead of the older version that existed before the update.

The `key = "#id"` expression is important in this method because `updateProduct()` accepts both `id` and `request`. The read method identifies entries from the product ID alone, so the update method needs to target that same entry. Without the expression, Spring would derive the identifier from both method arguments, which would not match the entry created by `findById(Long id)`.

This gives us a useful division between the read and update methods. `@Cacheable` can skip its method body after a cache hit because its job is to return an existing value when one is already stored. `@CachePut` always runs its method body because it needs the new result produced by the update before it can refresh the cache.

Putting both annotations on the same method generally creates conflicting execution behavior. Keeping `@Cacheable` on read methods and `@CachePut` on update methods makes the flow much easier to follow because each method has one cache responsibility tied to what that method already does.

### Removing Stale Entries

Delete operations do not produce a replacement value that belongs in the cache, so `@CacheEvict` removes an entry after the underlying data has been deleted. This prevents a later read from returning an object that no longer exists in the database.

We can connect eviction directly to the service method responsible for deleting a product.

```rb
@CacheEvict(cacheNames = "products", key = "#id")
public void deleteProduct(Long id) {
    productRepository.deleteById(id);
}
```

After `deleteById()` completes successfully, Spring removes the matching entry from the `products` cache. If product `1001` had been cached earlier, a later call to `findById(1001L)` cannot receive that old value. The request reaches the repository again, where the service can react to the missing database row through its normal error handling.

By default, Spring performs this eviction after the annotated method finishes successfully. That timing is helpful for database writes because a failed delete does not remove the cached value before the database operation has completed. Spring also supports `beforeInvocation = true`, which changes the order so eviction happens before the method body runs. If the method then throws an exception, the cache entry has already been removed.

Some write operations affect the entire cached collection rather than a single entry. Replacing a full product catalog is a case where removing all entries from the named cache can match the scope of the database change.

```rb
@CacheEvict(cacheNames = "products", allEntries = true)
public void replaceCatalog(List<Product> products) {
    productRepository.deleteAll();
    productRepository.saveAll(products);
}
```

After `replaceCatalog()` finishes successfully, Spring removes every entry from the `products` cache. Later product reads return through `findById()` and repopulate entries as they are requested again. The method can return `void` because `@CacheEvict` removes cached data rather than storing a method result.

Targeted eviction fits changes to a known product because unrelated cached entries can remain available. Full-cache eviction fits operations that replace or invalidate the whole data set. Matching the eviction scope to the database change prevents older entries from surviving after writes while leaving unaffected cached values available for later reads.

## Tuning Cache Behavior for Faster Reads

Good cache performance depends on more than storing a result and returning it later. Cached data also needs limits that match how quickly the source can change, how much memory the application can devote to entries, and where those entries should live. The annotations from the previous section stay the same while the cache provider controls details such as expiration and storage location. We can tune those provider settings without moving cache logic into the service methods themselves.

### Setting Expiration Boundaries

Cached values should not remain available forever when their source can change outside the service methods that call `@CachePut` or `@CacheEvict`. Product data could be changed by an import, supplier information could come from an external API, or a different application could update the same database. Expiration gives cached entries a defined lifetime so older values eventually leave the cache even when no annotated write method removes them.

With Caffeine, Spring Boot accepts a cache specification through `spring.cache.caffeine.spec`. We can give the `products` and `suppliers` caches both an entry limit and a fixed expiration period:

```rb
spring.cache.type=caffeine
spring.cache.cache-names=products,suppliers
spring.cache.caffeine.spec=maximumSize=1000,expireAfterWrite=10m
```

The `maximumSize=1000` setting limits each configured cache to roughly 1,000 entries, with Caffeine removing entries as needed when a cache grows beyond that limit. `expireAfterWrite=10m` gives each entry ten minutes from creation or its latest replacement before it becomes eligible for expiration. Reading an entry does not restart that ten-minute period, so frequently requested data can still expire after the configured time.

That distinction becomes important when deciding what expiration should represent. If product information should be refreshed at least every ten minutes, `expireAfterWrite` matches that rule because cache hits do not keep an old value alive indefinitely. Caffeine also supports `expireAfterAccess`, which moves the expiration point after reads or writes. With `expireAfterAccess=10m`, an entry that keeps receiving traffic can remain cached while an entry that receives no activity for ten minutes can expire.

Expiration values should follow the freshness requirements of the data rather than a single duration applied everywhere. Product descriptions that change rarely can tolerate a longer period, while inventory counts or rapidly changing prices may need a much shorter period. Very short lifetimes can reduce the benefit of caching because entries disappear before enough later requests can read them, sending traffic back to the database or remote API more frequently.

Redis follows the same general idea, though the configuration is expressed through Redis cache properties. To back Spring’s cache abstraction with Redis, add the Redis starter:

```rb
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

Spring Boot can then apply a time-to-live value to entries managed by `RedisCacheManager`:

```rb
spring.cache.type=redis
spring.cache.cache-names=products
spring.cache.redis.time-to-live=10m
spring.cache.redis.cache-null-values=false

spring.data.redis.host=localhost
spring.data.redis.port=6379
```

The `spring.cache.redis.time-to-live=10m` property gives cache entries a ten-minute lifetime. Spring Boot leaves Redis cache entries without a finite expiration by default, so setting a time-to-live value is important when cached data should age out on its own. The `cache-null-values=false` property prevents null results from being stored, while the host and port tell Spring Data Redis where the Redis server is available.

Redis time-to-live is refreshed when an entry is created or updated. Normal reads do not restart that timer, so an entry can expire after ten minutes even if callers read it several times during that period. For a fixed freshness window, regular time-to-live behavior keeps the expiration rule tied to creation or replacement rather than read frequency.

Expiration does not replace `@CachePut` or `@CacheEvict`. Those annotations react to changes that pass through the application, while expiration provides a fallback boundary for entries that remain untouched. If `updateProduct()` replaces a cached value immediately, callers do not need to wait for the old entry to expire. If data changes somewhere outside that method, the configured lifetime limits how long the earlier value can remain available.

### Choosing Caffeine or Redis

Provider choice changes where cached values live and what happens when the application runs across multiple instances. Caffeine stores values directly inside the JVM process, so a cache hit does not require a network request to a different service. That makes it well suited to local cached data where the current application instance can keep its own entries.

Caffeine entries belong to the process that created them. If the application restarts, those in-memory values disappear and are populated again as requests arrive. Multiple application instances also get independent caches, which means an entry removed from a single instance does not automatically disappear from the Caffeine caches held by the others.

This distinction becomes more important after the application is scaled across several instances. If three instances have cached product `1001`, a call to `@CacheEvict` on the first instance removes its local entry. The other instances can still have their earlier copies because their Caffeine caches live in different JVM processes. Spring’s cache abstraction does not distribute those local eviction operations across application processes by itself.

Redis places the cache outside the application process. Multiple Spring Boot instances connected to the same Redis deployment can read and replace entries from the same cache store, so an eviction against a shared Redis entry affects what the other instances can retrieve from that store as well. This makes Redis a better choice when several application instances need access to the same cached state. There is a cost to that shared storage though. Caffeine can return an object already held in the current JVM, while Redis requires communication with the Redis server and conversion of values to and from its storage format. Redis can still return data far faster than repeating an expensive database query or remote API request, but its cache-hit cost includes network and serialization activity that a local Caffeine cache does not have.

Serialization is a further difference worth accounting for when moving from Caffeine to Redis. Spring Data Redis defaults cache values to `JdkSerializationRedisSerializer`, so values stored with that default serializer need to support Java serialization. The earlier `ProductView` record can be adjusted like this if the Redis default remains in place:

```rb
package com.example.store.product;

import java.io.Serializable;
import java.math.BigDecimal;

public record ProductView(
        Long id,
        String name,
        BigDecimal price
) implements Serializable {
}
```

Adding `Serializable` lets the default Redis value serializer convert `ProductView` instances into the binary representation stored by Redis and reconstruct them when the cache is read. Caffeine does not cross a serialization boundary because it keeps the object directly in JVM memory. Spring Data Redis can also be configured with a different value serializer, including JSON-based serializers, when Java serialization is not the desired storage format.

The deployment model gives us a practical way to choose between the two providers. Caffeine performs well for a single application instance and can also serve multiple instances when independent local caches are acceptable. Redis becomes more attractive when cached state should be shared across instances, when cache entries should live outside any individual application process, or when coordinated replacement and eviction are important across the deployment.

Memory limits deserve attention with Caffeine because cached objects occupy the same JVM heap as the rest of the application. Settings such as `maximumSize` keep the entry count bounded rather than allowing every distinct request value to remain cached indefinitely. Redis moves that storage into the Redis server, which reduces cache storage inside the application heap but introduces the network and serialization cost that comes with external cache access.

Neither provider makes every request faster by default. The largest gains come from removing expensive repeated activity such as database queries or remote API calls. If the original method already returns quickly and receives little repeated traffic for the same entries, the cache can add storage and lifecycle concerns without removing much request time. Caffeine and Redis both become more valuable when the cache receives enough hits to avoid activity that costs far more than retrieving the cached value.

## Conclusion

Caching in Spring Boot speeds up repeated reads by cutting back on database queries and remote API calls that would return the same data again. With `@Cacheable`, `@CachePut`, and `@CacheEvict`, cached values can be returned, refreshed, or removed as requests move through the application, while expiration keeps older entries from remaining indefinitely. Caffeine keeps entries in JVM memory, while Redis gives multiple application instances access to the same cache store, leaving the main mechanics centered on reducing repeated calls and keeping cached data current.

**Thanks for reading! If you found this helpful, highlighting, clapping, or leaving a comment really helps me out.**

![](https://miro.medium.com/v2/resize:fit:1100/format:webp/1*7LCQHSwaBMSQIyaz83xAWg.png)

Spring Boot icon by Icons8
