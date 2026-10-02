---
title: "Resilience4j Circuit Breakers in Spring Boot That Actually Trip"
source: "https://alexanderobregon.substack.com/p/resilience4j-circuit-breakers-in?utm_source=substack&utm_medium=email"
author:
  - "[[Alexander Obregon]]"
published: 2026-06-30
created: 2026-07-12
description: "Circuit breakers protect Spring Boot services from sending every request into a dependency that is already failing, slow, or overloaded."
tags:
  - "clippings"
---

> [!summary]
> A practical walkthrough of why Resilience4j circuit breakers in Spring Boot often fail to trip during testing: the `@CircuitBreaker` annotation only records call outcomes, and the breaker opens only after the sliding window holds `minimumNumberOfCalls` and failure or slow-call rates cross their thresholds. Covers common pitfalls — self-invocation bypassing the Spring proxy, `recordExceptions` silently excluding thrown types, and count-based vs time-based window semantics. Ends with how HALF_OPEN trial calls decide whether the breaker recloses or reopens.

Circuit breakers protect Spring Boot services from sending every request into a dependency that is already failing, slow, or overloaded. Resilience4j does that by recording call results, calculating rates inside a sliding window, and changing state only after the configured rules have enough data. The annotation on a method is only the entry point. The breaker still needs recorded outcomes, thresholds, and state movement from `CLOSED` to `OPEN` to `HALF_OPEN` before traffic starts getting rejected.

### How Circuit Breakers Open

Circuit breaker behavior begins before the breaker rejects traffic. In the closed state, Resilience4j lets calls pass through and records what happened afterward. That record becomes part of the current sliding window, and the breaker calculates rates from that window. The breaker opens only when those recorded rates reach the configured rules. We can read the first part of circuit breaker behavior as a record-keeping flow, where the annotation marks the protected call, the call finishes, and the result becomes part of the breaker’s recent history.

#### The Call Outcome Record

Each protected call gives the breaker one outcome to store. While the breaker is `CLOSED`, the method still runs. Resilience4j wraps the call, waits for it to finish, then records the result as a success, failure, slow success, or slow failure based on the configured rules. The annotation does not mean calls are blocked right away. Blocking begins only after the breaker has recorded enough outcomes and moved to `OPEN`.

For a Spring Boot service, the protected method usually lives on a Spring-managed bean. Calls need to enter that bean through the Spring proxy that applies `@CircuitBreaker`. Controller calls into a service bean are a normal fit. Scheduled jobs calling a service bean also fit that model. Calling another method inside the same class skips the proxy, so the breaker is not part of that call. During local testing, that detail can make the annotation look inactive, even though the call route never passes through the decorated bean.

The protected HTTP client can be written like this:

```markup
package com.example.catalog;

import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class CatalogClient {

    private final RestClient restClient;

    public CatalogClient(RestClient.Builder builder) {
        this.restClient = builder
                .baseUrl("https://catalog.internal")
                .build();
    }

    @CircuitBreaker(name = "catalogClient", fallbackMethod = "fallbackCatalog")
    public CatalogResponse fetchCatalog(String sku) {
        return restClient.get()
                .uri("/items/{sku}", sku)
                .retrieve()
                .body(CatalogResponse.class);
    }

    CatalogResponse fallbackCatalog(String sku, Throwable throwable) {
        return new CatalogResponse(sku, "temporary catalog response", true);
    }
}
```

```markup
package com.example.catalog;

public record CatalogResponse(
        String sku,
        String name,
        boolean fallback
) {
}
```

The breaker named `catalogClient` records the result of `fetchCatalog`. If the `RestClient` call throws an exception that counts as a failure, Resilience4j records a failed call before the fallback response goes back to the caller. The fallback changes the response path for the caller, but it does not erase the failure from the breaker’s history.

The fallback signature needs to match the protected method’s arguments, with a trailing exception parameter. That exception parameter can be `Throwable` for a broad handler, or a more specific exception type when separate fallback methods are needed. The fallback method can be package-private, as shown above, because Spring and Resilience4j can still invoke it from the same class.

Calls from a controller give the breaker a normal proxied entry point:

```markup
package com.example.catalog;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class CatalogController {

    private final CatalogClient catalogClient;

    public CatalogController(CatalogClient catalogClient) {
        this.catalogClient = catalogClient;
    }

    @GetMapping("/catalog/{sku}")
    public CatalogResponse catalog(@PathVariable String sku) {
        return catalogClient.fetchCatalog(sku);
    }
}
```

The controller does not need to read breaker state or call Resilience4j directly. It calls the Spring bean, the proxy applies the breaker, and the client method either returns the remote response, throws an exception, or falls back if a matching fallback is available.

Failure recording depends on what leaves the protected method. Thrown exceptions can count as failures. Returned objects count as successes unless result-based rules are configured. Slow responses can still count as successful from an exception point of view while also being recorded as slow from a timing point of view. Those categories feed the breaker’s later rate calculation, so the state change comes from recorded outcomes rather than a single bad call.

Spring HTTP clients make this flow visible. With `retrieve()`, `RestClient` raises Spring exceptions for `4xx` and `5xx` HTTP status codes by default. Server-side `500` responses become exceptions unless status handling has been customized, and those exceptions can be recorded by the breaker. JSON responses that carry error fields still count as normal return values when the HTTP call returns successfully, unless the client code turns those responses into exceptions or a result predicate is configured.

The first breaker rules can stay near the client name:

```markup
resilience4j:
  circuitbreaker:
    instances:
      catalogClient:
        slidingWindowType: COUNT_BASED
        slidingWindowSize: 10
        minimumNumberOfCalls: 10
        failureRateThreshold: 50
        slowCallRateThreshold: 60
        slowCallDurationThreshold: 2s
        permittedNumberOfCallsInHalfOpenState: 3
        waitDurationInOpenState: 10s
```

These values give the breaker a ten-call sample while it is closed. The breaker records outcomes until it has enough data to calculate rates. At that point, the failure and slow-call settings can move the breaker toward `OPEN` if the recorded calls reach the configured limits.

#### The Sliding Window

Recent outcomes live inside a sliding window. The window decides which recorded calls belong to the current breaker calculation, so old call results do not stay in the rate forever. Resilience4j supports count-based and time-based sliding windows, and both styles still depend on recorded call outcomes from the protected method. With a count-based window, the breaker keeps a fixed number of recent call records. Size ten means the current rate comes from the latest ten calls in the sample. New calls finish, older call records fall out of that sample, and the breaker keeps judging the dependency from the recent set held by the window rather than a lifetime score.

That count-based behavior fits routes with enough traffic to fill the sample at a normal pace. The configuration can stay small for a local demo, or larger for a busier dependency:

```markup
resilience4j:
  circuitbreaker:
    instances:
      inventoryClient:
        slidingWindowType: COUNT_BASED
        slidingWindowSize: 8
        minimumNumberOfCalls: 8
        failureRateThreshold: 50
        slowCallRateThreshold: 75
        slowCallDurationThreshold: 1500ms
```

With this configuration, the breaker uses the latest eight recorded calls as the current sample. Older records leave as newer records arrive, so the rate can move up or down as traffic continues. If several early calls fail and later calls succeed, the later successes can push the old failures out of the active sample.

Time-based windows use recent time instead of a fixed call count. Thirty seconds of window size means the breaker keeps call records from the most recent thirty seconds. That can fit traffic that arrives in bursts because the rate is tied to a recent time period. It also means very low traffic may not produce enough recorded calls inside the time window to evaluate the rate.

The time-based version uses the same instance style, but the window unit changes:

```markup
resilience4j:
  circuitbreaker:
    instances:
      pricingClient:
        slidingWindowType: TIME_BASED
        slidingWindowSize: 30
        minimumNumberOfCalls: 10
        failureRateThreshold: 50
        slowCallRateThreshold: 60
        slowCallDurationThreshold: 2s
```

With this configuration, the breaker reads from the latest thirty seconds of recorded calls. The value `slidingWindowSize` means seconds when `slidingWindowType` is `TIME_BASED`. It means number of calls when `slidingWindowType` is `COUNT_BASED`. That shared property name can cause confusion during review, so the window type and size should be read as a pair.

The sliding window is separate from concurrency control. Closed circuit breakers permit calls to enter and record results after those calls finish. If twenty requests reach the protected method at nearly the same time while the breaker is closed, the breaker does not treat the window size as a cap of ten or thirty active requests. It records outcomes into the window as calls complete. Bulkheads handle concurrent-call limits in Resilience4j, while circuit breakers decide if a dependency should keep receiving traffic based on recent recorded outcomes.

Window choice changes how quickly the breaker can react. Count-based windows can react after a set number of completed calls, which makes them direct for steady request flow and local tests. Time-based windows focus on a recent time range, which can fit burst-heavy traffic. Both window types still need recorded calls from the protected method, and those calls only affect state after Resilience4j has enough data inside the current sample.

### Why Breakers Stay Closed

Closed breakers can be surprising during testing because the protected dependency is visibly failing, yet traffic still passes through. Resilience4j does not react to a single failed request by default. It waits for enough recorded calls, applies the exception and slow-call rules, then checks the current rates inside the active window. The breaker stays closed whenever the data is incomplete, the thrown exception is not counted as a failure, or the calls do not cross the configured failure-rate or slow-call limits.

#### The Minimum Call Gate

Rate calculation does not begin until `minimumNumberOfCalls` has been reached. If the breaker needs ten calls and only three have failed, the failure rate is not evaluated yet. That can feel strange during a small manual test, but the breaker is still collecting its first sample.

This gate keeps the breaker from opening after too little traffic. Without it, a single bad call could look like a 100 percent failure rate. With the gate in place, Resilience4j waits until the sample has enough recorded outcomes. The failure rate and slow-call rate are only checked after that point.

Local test values can be tightened like this:

```markup
resilience4j:
  circuitbreaker:
    instances:
      catalogClient:
        slidingWindowType: COUNT_BASED
        slidingWindowSize: 4
        minimumNumberOfCalls: 4
        failureRateThreshold: 50
        waitDurationInOpenState: 5s
        permittedNumberOfCallsInHalfOpenState: 2
```

This configuration lets the breaker calculate rates after four recorded calls. Two failures out of four reach a 50 percent failure rate, so the breaker can move to `OPEN`. With `minimumNumberOfCalls` set to ten, those same two failures would not be enough for rate evaluation.

The gate also affects time-based windows. With a thirty-second window and `minimumNumberOfCalls` set to ten, the breaker needs ten recorded calls during that active time range before it checks rates. Low-traffic endpoints can keep missing that gate if only a few calls arrive before the time window moves forward.

Production values usually need more care than demo values. Tiny samples can open the breaker too quickly during normal network noise, while oversized samples can delay protection during an outage. The right value comes from the call volume of the protected dependency and the amount of failure the caller can tolerate before shedding traffic.

#### Exception Rules

Recorded failures depend on the exception rules attached to the breaker. By default, thrown exceptions are recorded as failures. That default changes when `recordExceptions`, `ignoreExceptions`, or result predicates are configured. The application can still throw an exception to the caller while the breaker treats that exception differently for its own rate calculation.

Ignored exceptions are not counted as failures. They are also not counted as successes. They are left out of the breaker’s rate math. That fits caller mistakes or domain validation errors that do not say anything about the downstream dependency. Bad SKUs, missing fields, and invalid requests should not automatically move a dependency breaker toward `OPEN`.

The exception types can stay explicit in the application code:

```markup
package com.example.catalog;

public class CatalogValidationException extends RuntimeException {

    public CatalogValidationException(String message) {
        super(message);
    }
}
```

```markup
package com.example.catalog;

public class CatalogUnavailableException extends RuntimeException {

    public CatalogUnavailableException(String message, Throwable cause) {
        super(message, cause);
    }
}
```

Those two exceptions can be treated differently by the breaker:

```markup
resilience4j:
  circuitbreaker:
    instances:
      catalogClient:
        slidingWindowType: COUNT_BASED
        slidingWindowSize: 10
        minimumNumberOfCalls: 10
        failureRateThreshold: 50
        recordExceptions:
          - java.net.SocketTimeoutException
          - org.springframework.web.client.ResourceAccessException
          - org.springframework.web.client.HttpServerErrorException
          - com.example.catalog.CatalogUnavailableException
        ignoreExceptions:
          - com.example.catalog.CatalogValidationException
```

With these rules, dependency failures count toward the failure rate, while validation failures stay out of the breaker math. If `CatalogValidationException` is thrown, the caller can still receive an error, but the circuit breaker does not treat that call as proof that the catalog dependency is unhealthy.

Adding `recordExceptions` narrows the set of exceptions that count as failures. Exception types not named in that list are treated as successes unless they are ignored. That detail explains a lot of closed breakers during testing. The protected method may throw an exception, yet the breaker never moves toward `OPEN` because the thrown type is not part of the recorded failure set.

HTTP behavior deserves a direct check here. `RestClient.retrieve()` can throw Spring exceptions for server errors and client-side access problems, but the actual type depends on what failed. Timeouts, connection refusals, server-side 500 responses, and local validation branches do not always throw the same class. When a breaker stays closed, the exception type leaving the protected method should match the configured rule.

#### Slow Call Rules

Latency can also move a breaker toward `OPEN`. Resilience4j records slow calls when their duration is greater than `slowCallDurationThreshold`, then calculates a slow-call rate inside the current window. The call does not need to throw an exception to be counted as slow. This helps with dependencies that still respond but take too long. Callers can be hurt by slow responses long before every request fails. Slow-call settings let the breaker react to that degraded behavior through timing, not only exceptions.

The same minimum-call gate still applies to slow calls. If the breaker needs ten recorded calls, nine slow calls are still not enough for a slow-call rate calculation. The breaker is collecting data, but it has not reached the point where it can compare the slow-call rate with `slowCallRateThreshold`.

Slow-call settings can live beside the failure-rate settings:

```markup
resilience4j:
  circuitbreaker:
    instances:
      inventoryClient:
        slidingWindowType: COUNT_BASED
        slidingWindowSize: 10
        minimumNumberOfCalls: 10
        failureRateThreshold: 50
        slowCallRateThreshold: 60
        slowCallDurationThreshold: 2s
```

This breaker can open from failures or slow calls. If six out of ten recorded calls take longer than two seconds, the slow-call rate reaches 60 percent. Resilience4j can move the breaker to `OPEN` even if those slow calls eventually return successful responses.

Timeout values should be read beside slow-call values. If the HTTP client times out after one second and the slow-call threshold is two seconds, the breaker will usually record timeout failures rather than slow successes. If the HTTP client waits longer than the slow-call threshold, Resilience4j can record calls that returned successfully but crossed the latency limit.

Calls that throw after the slow-call threshold can be both slow and failed. Calls that return after the threshold can be slow successes. Those categories feed separate rates, and either rate can open the breaker when the configured threshold is reached after the minimum call gate.

#### Half Open Trial Calls

Recovery testing happens after the breaker has already opened. While the breaker is `OPEN`, Resilience4j rejects calls with `CallNotPermittedException`. The protected method is not called during those rejected requests. If a fallback method exists, the fallback can still return a response to the caller, but the dependency call is skipped.

After `waitDurationInOpenState` passes, the breaker can move to `HALF_OPEN`. This state allows a limited number of trial calls through to the protected method. Those trial calls decide the next state. If the trial results are healthy enough, the breaker returns to `CLOSED`. If the trial results reach the failure or slow-call threshold, the breaker returns to `OPEN`.

The half-open settings can be kept small so recovery probes do not send full traffic back all at once:

```markup
resilience4j:
  circuitbreaker:
    instances:
      pricingClient:
        slidingWindowType: COUNT_BASED
        slidingWindowSize: 10
        minimumNumberOfCalls: 10
        failureRateThreshold: 50
        slowCallRateThreshold: 60
        slowCallDurationThreshold: 2s
        waitDurationInOpenState: 15s
        permittedNumberOfCallsInHalfOpenState: 3
        maxWaitDurationInHalfOpenState: 10s
        automaticTransitionFromOpenToHalfOpenEnabled: false
```

With this configuration, the breaker waits fifteen seconds in `OPEN`, then permits a small trial group when the next eligible call arrives. Only three calls can pass through in `HALF_OPEN`. Extra calls during that trial period are rejected until the permitted trial calls finish or the half-open wait limit is reached.

The automatic transition flag changes how the breaker leaves `OPEN`. With `automaticTransitionFromOpenToHalfOpenEnabled` set to false, the breaker moves toward `HALF_OPEN` when a call arrives after the open wait duration. With it set to true, Resilience4j can transition without waiting for that next caller. Both styles still rely on trial call results before returning to `CLOSED`.

Half-open behavior explains why a breaker can appear to reopen right after its wait period. The first few calls after the wait are not normal traffic yet. They are trial calls. If those trial calls fail or run too slowly at a rate that reaches the configured threshold, the breaker goes back to `OPEN` and the wait period starts again.

### Conclusion

Circuit breakers become relatively predictable when we read them as recorded state changes. The breaker starts in `CLOSED`, records outcomes inside the active sliding window, waits for `minimumNumberOfCalls`, and opens only when failure or slow-call rates reach the configured thresholds. While `OPEN`, it rejects calls instead of touching the dependency, then moves through `HALF_OPEN` trial calls to test recovery before normal traffic returns.

![](https://substackcdn.com/image/fetch/$s_!hWmR!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fb18d1cd3-0edd-452e-8f8f-e78b39d5744b_276x276.png)

Spring Boot icon by Icons8
