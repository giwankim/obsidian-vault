---
title: "Resilience4j Bulkheads in Spring Boot for Concurrency Limits"
source: "https://alexanderobregon.substack.com/p/resilience4j-bulkheads-in-spring?utm_source=substack&utm_medium=email"
author:
  - "[[Alexander Obregon]]"
published: 2026-07-16
created: 2026-07-20
description: "Slow downstream calls can drain request capacity before a Spring Boot service begins returning obvious failures."
tags:
  - "clippings"
---

> [!summary]
> Deep dive into Resilience4j semaphore bulkheads in Spring Boot, which cap concurrent calls to a dependency via a fixed permit pool (`maxConcurrentCalls`, `maxWaitDuration`) so one slow downstream service can't drain servlet thread capacity. Covers the full permit lifecycle, semaphore vs thread pool bulkheads, handling `BulkheadFullException` with 503 responses or fallbacks, deterministic exhaustion testing with latches, and registry events/metrics for diagnosing saturation. Ends with how aspect ordering (Retry outside Bulkhead by default) determines whether permits are held across retry delays.

Slow downstream calls can drain request capacity before a Spring Boot service begins returning obvious failures. Servlet threads remain occupied while they wait on an inventory API, payment gateway, or database proxy, leaving fewer threads available for unrelated requests during a traffic spike. Resilience4j semaphore bulkheads place a concurrency boundary around the protected method by assigning a fixed number of permits. Every admitted call takes one permit and returns it after completion, while later calls either wait for the configured duration or fail immediately after the permit pool reaches zero. That admission boundary keeps one slow dependency from taking over the request capacity needed by the rest of the service. This is a bit longer read then normal because I wanted to cover the full bulkhead lifecycle, including permit admission, thread pool differences, exhaustion testing, saturation events, and the way retries or timeouts change how long capacity stays reserved.

### How Semaphore Bulkheads Control Concurrency

Semaphore bulkheads control admission before a protected call begins. The bulkhead keeps a fixed pool of permits for its named instance, and `maxConcurrentCalls` sets the size of that pool. Calls that receive permission enter the protected method, while later calls remain outside the boundary after every permit is occupied. This creates a firm ceiling on simultaneous execution around a dependency without moving the call to a separate executor.

The protected code still runs on the caller thread. An admitted servlet request therefore continues to occupy its request thread while the downstream call is active, yet only the permitted group can become tied up behind that dependency at the same time. Requests beyond the permit limit never enter the protected call until capacity returns through the configured admission rules.

Concurrency refers to overlap rather than traffic counted during a time window. Ten fast calls can reuse the same permits several times within a second, while ten slow calls can hold every permit for several seconds. Nothing refreshes on a timer because capacity returns only after admitted execution finishes and its permit goes back to the bulkhead. That behavior differs from a rate limiter, which controls call frequency across a period rather than calls active at the same moment.

#### Permits Mark Active Calls

Every admitted invocation removes a permit from the available count before the protected operation begins. If a named bulkhead allows eight concurrent calls, the first overlapping group can take those eight permits. The next caller cannot enter the protected operation until permission becomes available through the configured admission rules. Resilience4j performs this check at the boundary, so the downstream client has not started its request while the caller remains outside the bulkhead.

The permit belongs to the invocation rather than to a specific HTTP connection, database session, or server thread. Resilience4j does not reserve those resources ahead of time. It grants permission to cross the boundary, then the protected method obtains any other resources it needs. This distinction becomes important when resource pools have different capacities. Bulkhead admission can still be followed by a wait for an HTTP connection if every connection is busy, so the permit count should reflect the amount of concurrent dependency activity the service can accept rather than replace connection-pool limits.

Spring Boot commonly applies this boundary through `@Bulkhead`, while the core API can express the same mechanics directly. We can retrieve the named instance from `BulkheadRegistry` and place permission acquisition around the supplied operation:

```markup
package com.example.inventory;

import io.github.resilience4j.bulkhead.Bulkhead;
import io.github.resilience4j.bulkhead.BulkheadRegistry;
import org.springframework.stereotype.Component;

@Component
public class InventoryGateway {

    private final InventoryHttpClient client;
    private final Bulkhead inventoryBulkhead;

    public InventoryGateway(
            InventoryHttpClient client,
            BulkheadRegistry bulkheadRegistry
    ) {
        this.client = client;
        this.inventoryBulkhead =
                bulkheadRegistry.bulkhead("inventoryApi");
    }

    public InventoryResponse fetch(String sku) {
        return inventoryBulkhead.executeSupplier(
                () -> client.fetch(sku)
        );
    }
}
```

The constructor receives the registry and asks for the `inventoryApi` bulkhead. That lookup returns the registered instance rather than creating an isolated permit pool for every request. Inside `fetch`, `executeSupplier` requests permission before `client.fetch` runs, keeps the permit while the client call remains active, and returns the permit after the supplier finishes.

Two Spring beans that refer to `inventoryApi` share the same local concurrency boundary. Several methods can therefore call the same downstream API through that bulkhead, and their combined active count stays inside the shared limit. Product lookup, stock lookup, and warehouse lookup could all draw from the same permit pool when they reach the same dependency. No method receives a private copy of the full permit count merely because its Java method is different.

Separate bulkhead names create separate permit pools. That division can stop inventory traffic from spending capacity assigned to payment calls, shipping calls, or a different dependency with different latency and capacity. The name therefore identifies the boundary whose state will be shared, including its available permits and active-call count.

Shared state remains local to the running Spring Boot instance. Separate service instances do not exchange semaphore permits through Resilience4j. If every instance carries eight permits for `inventoryApi`, three instances can admit up to 24 overlapping calls across the deployment. Load balancing can distribute those calls, but permit accounting still happens independently inside each Java process. Deployment size therefore changes total downstream concurrency even when every instance has identical settings.

Spring AOP contributes a further boundary detail for annotated methods. Calls entering a proxied bean from a different bean pass through the bulkhead aspect before the method body runs. Calls from one method to a second annotated method on the same object normally stay inside the object and bypass the proxy, so no new permission check occurs for that internal call. Keeping the dependency operation behind a separately injected Spring bean preserves the intended interception point.

Permit counts track active admission rather than successful outcomes. Calls that later receive an HTTP error, throw during response mapping, or return valid data occupy permits for the time spent inside the boundary. The semaphore does not calculate failure percentages or decide that a dependency should stop receiving calls after repeated errors. Its responsibility is narrower because it limits overlap around the protected invocation.

Slow calls are the pressure being contained. Without a concurrency boundary, incoming requests can continue entering the same slow client call until some other resource reaches exhaustion. With a semaphore bulkhead, only the admitted group can remain inside that operation. Requests outside the group do not add further active calls to the slow dependency, which leaves request capacity available for controllers and downstream clients tied to different permit pools.

#### Semaphore Bulkhead Versus Thread Pool Bulkhead

Resilience4j provides two bulkhead implementations that limit concurrent execution in different ways. `SemaphoreBulkhead` leaves the protected call on its current thread and controls entry through permits. `FixedThreadPoolBulkhead` submits the call to a dedicated executor backed by a bounded queue. Both place a limit around dependency activity, but they occupy different resources while calls run or wait.

With a semaphore bulkhead, the caller thread requests a permit and continues into the protected method after admission. No separate executor receives the call, so a Spring MVC request remains on its servlet thread while the dependency request runs. If every permit is occupied, `maxWaitDuration` decides how long that same caller thread can wait before admission fails. No separate queue-capacity property exists for this bulkhead type because waiting happens at the semaphore boundary.

Thread pool bulkheads move accepted execution away from the caller thread. Submitted calls run on threads owned by the named `ThreadPoolBulkhead`, while calls that cannot start immediately can wait inside its bounded queue. `coreThreadPoolSize` and `maxThreadPoolSize` control executor threads, and `queueCapacity` controls how many accepted submissions can remain pending. Spring Boot keeps these settings under `resilience4j.thread-pool-bulkhead`, separate from the semaphore properties under `resilience4j.bulkhead`.

Keeping both pool values equal creates a fixed four-thread boundary for a shipping dependency:

```markup
resilience4j:
  thread-pool-bulkhead:
    instances:
      shippingApi:
        coreThreadPoolSize: 4
        maxThreadPoolSize: 4
        queueCapacity: 8
```

This definition gives `shippingApi` four executor threads and eight queue positions. The first four overlapping submissions can begin on bulkhead threads. Up to eight later submissions can remain queued while those threads are occupied. Further submissions reach full executor capacity after both the thread pool and queue are full, causing Resilience4j to reject them with `BulkheadFullException`.

Queue positions and semaphore permits represent different stages of execution. Every semaphore permit belongs to a call that has entered the protected boundary, though that call can still wait for an HTTP connection or another downstream resource. A thread pool queue position belongs to an accepted call that has not started running yet. Queued calls do not occupy bulkhead executor threads, but they remain pending and collect extra latency before dependency activity begins.

This difference changes how waiting affects the caller. Semaphore waiting blocks the thread that reached the boundary. Thread pool waiting stores the submission in the executor queue and returns a `CompletionStage` to the caller. Code farther up the call chain can remain asynchronous, though calling `get`, `join`, or another blocking operation on that stage would still occupy the thread that performs that wait.

Spring’s `@Bulkhead` annotation selects the semaphore type by default. Selecting `THREADPOOL` tells the aspect to retrieve the named thread pool bulkhead and submit the annotated invocation through its executor. The annotated method must return a `CompletionStage` type such as `CompletableFuture`.

```markup
package com.example.shipping;

import io.github.resilience4j.bulkhead.annotation.Bulkhead;
import java.util.concurrent.CompletableFuture;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class ShippingClient {

    private final RestClient restClient;

    public ShippingClient(RestClient.Builder builder) {
        this.restClient = builder
                .baseUrl("https://shipping.example.com")
                .build();
    }

    @Bulkhead(
            name = "shippingApi",
            type = Bulkhead.Type.THREADPOOL
    )
    public CompletableFuture<ShippingQuote> fetchQuote(
            String postalCode
    ) {
        ShippingQuote quote = restClient.get()
                .uri("/quotes/{postalCode}", postalCode)
                .retrieve()
                .body(ShippingQuote.class);

        return CompletableFuture.completedFuture(quote);
    }
}
```

Spring’s bulkhead aspect submits the annotated invocation to the `shippingApi` executor. The `RestClient` request therefore runs on a bulkhead thread rather than the servlet thread that entered the proxy. After the HTTP request returns or throws, the method’s `CompletableFuture` completes, and the executor thread becomes available for a queued submission.

Returning `CompletableFuture.completedFuture` in this case does not move the HTTP call to a new thread by itself. The thread change comes from `Bulkhead.Type.THREADPOOL`, which places the entire annotated method invocation on the bulkhead executor. Without that thread pool boundary, constructing a completed future after a synchronous HTTP request would leave the HTTP call on the original caller thread.

Thread pool isolation brings a second capacity layer beyond concurrent dependency calls. Executor threads limit active invocations, while the queue limits accepted calls waiting to begin. Larger queues can reduce immediate rejection during short bursts, but queued requests can age before execution and continue toward the dependency after the original burst has passed. Smaller queues reject sooner and keep pending latency lower.

Semaphore bulkheads fit synchronous code where the existing caller thread should perform the protected call and only concurrency admission needs a boundary. Thread pool bulkheads fit asynchronous APIs that need executor isolation along with bounded pending submissions. The thread pool form carries more configuration because thread count, queue size, thread-local context, and asynchronous completion all become part of the call lifecycle.

Thread-local values tied to the caller thread do not automatically become part of a different executor thread. Logging context, security context, tracing state, and request data can require explicit propagation when the protected method moves through a thread pool bulkhead. Semaphore calls remain on the current thread, so they do not introduce that particular thread-boundary concern.

Both implementations still enforce local capacity inside the current Spring Boot process. Separate service replicas own separate semaphore permits, executor threads, and queues. Four replicas with four `shippingApi` worker threads can therefore run up to 16 such calls across the deployment, with each replica accounting for its own queue and active threads.

The choice comes down to what should be isolated. Semaphore bulkheads limit entry while leaving execution on the thread that arrived. Thread pool bulkheads isolate execution through named executor threads and retain a bounded group of pending calls. In either form, accepted calls consume their assigned capacity until execution finishes, which connects directly to how permit release ends the reservation in the semaphore model.

#### Permit Release Ends the Reservation

Completion returns reserved capacity to the bulkhead. For a synchronous supplier, callable, function, or runnable, Resilience4j acquires permission before invocation and calls `onComplete` from a `finally` block afterward. Normal return and exceptional completion therefore follow the same release route. The permit represents active execution time rather than successful output, so a failed call does not permanently reduce the available count.

The core lifecycle can be written directly when manual control is required:

```markup
public InventoryResponse fetchWithManualBoundary(String sku) {
    inventoryBulkhead.acquirePermission();

    try {
        return client.fetch(sku);
    } finally {
        inventoryBulkhead.onComplete();
    }
}
```

`acquirePermission` takes capacity before the client call begins. The `try` block holds the protected invocation, and the `finally` block returns capacity through `onComplete` regardless of normal return or an exception. If `client.fetch` fails while opening a connection, reading a response, or converting the body, control still reaches `onComplete`.

Resilience4j decorators already provide this lifecycle, so direct calls to `acquirePermission` and `onComplete` are generally reserved for boundaries that need manual control. Methods such as `executeSupplier` and `executeCallable` place the release step around the protected code, reducing the chance that an exception leaves a permit occupied.

Calling `onComplete` too early would let a later request take the returned permit while the earlier dependency call was still active. Calling it too late would hold capacity after the protected operation had finished. The release point therefore belongs directly after the protected invocation, which is why the decorator wraps execution rather than returning permission at some unrelated point in the request.

Slow network activity has two costs for an admitted servlet request. The request thread remains occupied, and the bulkhead permit remains reserved. The bulkhead caps the size of that group, but it does not shorten the dependency call. HTTP connection and response timeouts control duration at the client layer. If a downstream request waits for 15 seconds, its permit can remain unavailable for those 15 seconds. When the client ends the call through a response, failure, or timeout, the decorated invocation completes and returns the permit.

Asynchronous return types need a completion boundary that follows the asynchronous result. Returning a `CompletionStage` from a supplier does not mean dependency activity has finished when the stage object is created. Resilience4j can keep the permit until the stage reaches successful or exceptional completion:

```markup
package com.example.shipping;

import io.github.resilience4j.bulkhead.Bulkhead;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.Executor;

public class ShippingGateway {

    private final ShippingClient client;
    private final Bulkhead shippingBulkhead;
    private final Executor executor;

    public ShippingGateway(
            ShippingClient client,
            Bulkhead shippingBulkhead,
            Executor executor
    ) {
        this.client = client;
        this.shippingBulkhead = shippingBulkhead;
        this.executor = executor;
    }

    public CompletionStage<ShippingQuote> quote(String postalCode) {
        return shippingBulkhead.executeCompletionStage(
                () -> CompletableFuture.supplyAsync(
                        () -> client.quote(postalCode),
                        executor
                )
        );
    }
}
```

The call to `executeCompletionStage` acquires permission before the stage supplier runs. `CompletableFuture.supplyAsync` then starts `client.quote` on the supplied executor, and the permit stays occupied while that asynchronous call remains unfinished. Successful completion returns the permit, while exceptional completion follows the same release route.

Permit release follows terminal completion of the `CompletionStage` supplied to `executeCompletionStage`. Canceling or abandoning the decorated stage returned to the caller does not propagate cancellation to the supplied stage, so the permit remains occupied while that supplied stage continues. If the supplied stage itself is canceled or reaches any terminal state, Resilience4j returns the permit even when separate underlying work ignores cancellation and keeps running. An HTTP client disconnect also does not return capacity by itself.

`releasePermission` serves a narrower case than `onComplete`. It returns permission that was acquired but never spent on an invocation, while `onComplete` records a finished call and returns its permit. Decorated execution calls `onComplete` after protected code runs. Manual code that acquires permission and then abandons execution before entering the protected operation can return unused capacity through `releasePermission`.

Every acquired permit needs exactly one matching release route. Calling both methods for the same reservation would return capacity twice and damage permit accounting, while calling neither would leave capacity occupied. The lifecycle must pair acquisition with either completion or release according to what happened after admission.

Permit duration directly affects the amount of traffic the boundary can process. Faster completion returns capacity sooner, while slower completion keeps the same finite pool occupied longer. The bulkhead does not create throughput by itself. It places a ceiling on overlap so one dependency can consume only the request capacity assigned to its boundary at any moment.

### Configuring Rejection Behavior in Spring Boot

Rejection behavior comes from two related settings on a named semaphore bulkhead. `maxConcurrentCalls` sets the amount of protected execution that can overlap, while `maxWaitDuration` sets how long a caller can remain blocked after every permit is occupied. Spring Boot binds those values from application properties, creates the registered bulkhead, and applies it when an annotated method enters through the Spring proxy. If admission still fails, Resilience4j reports local saturation before the protected method reaches its downstream client.

That order separates bulkhead rejection from a remote error. The inventory API, payment service, or database proxy never receives the extra call because the extra call never begins. Spring Boot receives the failure from the local bulkhead boundary and can return an HTTP response, call a fallback method, record an event, or let the exception continue to a higher handler.

#### Spring Boot Setup

The Spring Boot 4 integration comes from the `resilience4j-spring-boot4` starter. Annotation interception also needs Spring AOP, while Actuator supplies metric and event endpoints for registered bulkheads. Resilience4j 2.4.0 includes the Spring Boot 4 starter and the related auto-configuration.

Maven dependencies can bring in the Resilience4j starter, Spring MVC, `RestClient` support, AOP interception, and Actuator support:

```markup
<properties>
    <resilience4j.version>2.4.0</resilience4j.version>
</properties>

<dependencies>
    <dependency>
        <groupId>io.github.resilience4j</groupId>
        <artifactId>resilience4j-spring-boot4</artifactId>
        <version>${resilience4j.version}</version>
    </dependency>

    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-webmvc</artifactId>
    </dependency>

    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-restclient</artifactId>
    </dependency>

    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-aspectj</artifactId>
    </dependency>

    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-actuator</artifactId>
    </dependency>
</dependencies>
```

The Resilience4j starter contributes bulkhead auto-configuration, property binding, the registry, and the aspect that intercepts `@Bulkhead`. Spring AOP supplies the proxy layer that runs the aspect before the protected method. Actuator exposes registered instances, buffered events, and Micrometer measurements after the related endpoints are available to the application.

Configuration normally belongs under `resilience4j.bulkhead`. The `instances` map creates named boundaries, and every name can carry its own concurrency limit and admission wait:

```markup
resilience4j:
  bulkhead:
    instances:
      inventoryApi:
        maxConcurrentCalls: 12
        maxWaitDuration: 0
        eventConsumerBufferSize: 50
      paymentApi:
        maxConcurrentCalls: 6
        maxWaitDuration: 25ms
```

The `inventoryApi` instance can admit up to 12 overlapping calls and rejects the next caller immediately after capacity is full. The `paymentApi` instance owns a separate six-permit pool and allows a brief wait for returned capacity. `eventConsumerBufferSize` retains recent bulkhead events for the Actuator event endpoint, giving us a record of permitted, rejected, and finished calls.

Duration values such as `25ms` follow Spring Boot property binding, so the unit remains part of the value. Leaving the unit out can make the intended duration less obvious and can create confusion during later changes. Keeping the unit beside the number makes the admission delay readable in the configuration file.

The annotation name connects Java code to the registered instance:

```markup
package com.example.inventory;

import io.github.resilience4j.bulkhead.annotation.Bulkhead;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class InventoryClient {

    private final RestClient restClient;

    public InventoryClient(RestClient.Builder builder) {
        this.restClient = builder
                .baseUrl("https://inventory.example.com")
                .build();
    }

    @Bulkhead(
            name = "inventoryApi",
            type = Bulkhead.Type.SEMAPHORE
    )
    public InventoryResponse fetchInventory(String sku) {
        return restClient.get()
                .uri("/inventory/{sku}", sku)
                .retrieve()
                .body(InventoryResponse.class);
    }
}
```

Calls that enter `fetchInventory` through the Spring proxy are matched with the `inventoryApi` entry from `application.yml`. The aspect retrieves that registered bulkhead, requests permission, and runs the method only after admission succeeds. `SEMAPHORE` is already the annotation default, though writing it in the annotation records the selected type beside the method.

The protected method stays on the caller thread. Semaphore bulkheads do not submit the invocation to a separate executor, so a servlet request continues on its existing request thread after admission. The bulkhead controls entry into the method rather than changing where the method runs.

Names must match exactly between Java and configuration. Writing `inventory-api` in `application.yml` and `inventoryApi` in the annotation refers to different registry names. Spring Boot relaxes property names during binding, but the map entry under `instances` remains the identifier passed to the bulkhead registry.

Shared settings can be placed under `configs`, then attached to individual instances through `baseConfig`. This keeps repeated values in one property group while preserving a separate permit pool for every named instance:

```markup
resilience4j:
  bulkhead:
    configs:
      downstreamDefaults:
        maxConcurrentCalls: 8
        maxWaitDuration: 0
        eventConsumerBufferSize: 50

    instances:
      inventoryApi:
        baseConfig: downstreamDefaults
        maxConcurrentCalls: 12

      paymentApi:
        baseConfig: downstreamDefaults
        maxConcurrentCalls: 5
```

Both instances inherit the zero wait and event buffer from `downstreamDefaults`. `inventoryApi` replaces the inherited concurrency value with 12, while `paymentApi` replaces it with 5. Their values come from the same shared property group, but their runtime permit counts remain separate because the instance names differ.

#### maxConcurrentCalls Sets the Ceiling

The `maxConcurrentCalls` property defines the highest number of calls that can remain admitted inside a named semaphore bulkhead at the same moment. Resilience4j defaults this value to 25, though production values should come from downstream capacity, client pool sizes, latency measurements, replica count, and the amount of request capacity reserved for unrelated endpoints.

Setting the value to 12 does not reserve 12 servlet threads during startup or open 12 HTTP connections in advance. It creates 12 semaphore permits. Incoming calls take those permits as they enter the protected method, and later calls reach the admission rule after the available count falls to zero.

Connection pools need their own limit because the bulkhead does not own HTTP connections. Setting the bulkhead ceiling above the connection-pool limit can admit callers that later block while waiting for a connection. Those callers still occupy request threads and bulkhead permits, so the larger number does not create more useful parallel activity.

Setting the ceiling below the connection-pool limit can reserve some connections for other clients or dependency groups. That relationship depends on how the pool is shared. Several clients drawing from the same connection pool can still compete for connections after passing separate bulkheads, so both limits need values that reflect the surrounding client configuration.

Deployment size changes the total concurrency sent toward the dependency. Twelve permits on a single application instance allow up to 12 admitted calls from that process. Four instances carrying the same value can admit up to 48 calls across the deployment because Resilience4j semaphore permits stay local to each Java process.

Spring profiles can assign a different ceiling without changing the annotation:

```markup
# application-prod.yml
resilience4j:
  bulkhead:
    instances:
      inventoryApi:
        maxConcurrentCalls: 12
```

The Java annotation still refers to `inventoryApi`, while the active profile supplies the production permit ceiling. This keeps the method boundary stable as deployment configuration changes between local development, testing, and production environments.

Call rate alone cannot determine a suitable value because duration controls overlap. Incoming traffic can stay at the same rate while dependency latency rises, leaving more calls active at the same moment. The permit pool then reaches zero sooner, and rejections increase even though requests per second have not changed.

Latency percentiles, active-request counts, available connections, and rejected-call events provide a better basis for the ceiling. Average latency can hide short periods where requests remain active far longer than normal, so load tests should include normal responses, delayed responses, brief bursts, and sustained saturation.

Raising the ceiling admits more overlapping calls and places more request threads, connections, and downstream activity behind the same dependency during a slowdown. Lowering it preserves more capacity for the rest of the service while rejecting earlier. The selected number should represent the concurrency that both sides can carry without letting one dependency absorb the request capacity needed elsewhere.

#### maxWaitDuration Controls Admission Delay

Waiting begins after the permit count reaches zero. `maxWaitDuration` tells the semaphore how long the caller thread can remain blocked while waiting for returned capacity. The default value is zero, which produces an immediate admission decision rather than parking the caller.

With a zero duration, request-handling code receives a firm boundary. The first group enters the protected method, and callers beyond the ceiling fail without waiting at the entrance. Fast rejection keeps saturation from turning into a growing group of blocked servlet threads and gives the controller layer time to return a controlled response before an upstream timeout expires.

Brief nonzero waiting can absorb narrow overlap when active calls are close to completion:

```markup
resilience4j:
  bulkhead:
    instances:
      inventoryApi:
        maxConcurrentCalls: 12
        maxWaitDuration: 40ms
```

After the twelfth overlapping call takes the final permit, the next caller can remain blocked for up to 40 milliseconds. If a permit returns during that interval, the caller acquires it and enters `inventoryApi`. If no permit returns before the interval ends, admission fails and the protected method does not run.

The duration applies only to entry. It does not cap the HTTP request, cancel the protected method, or set the full request deadline. Client connect timeouts, response timeouts, and any outer request deadline still govern execution after admission.

Adding a 40-millisecond admission wait can increase total request time by as much as 40 milliseconds before the downstream call begins. That extra time belongs in the full latency budget. If the caller has little time remaining before its own deadline, waiting at the bulkhead can leave too little time for the dependency request.

Semaphore bulkheads do not expose a configured waiting-queue capacity. Every caller that reaches a full boundary can block on the semaphore for the allowed duration. During a sharp burst, a long duration can leave a large group of request threads waiting outside the protected method.

Those waiting callers consume no downstream permits, yet they still retain server memory, request state, thread capacity, and open upstream connections. Keeping the duration at zero or near zero prevents the admission boundary from becoming a large holding area during saturation.

The wait value should remain far below the caller’s remaining deadline. Brief waiting can absorb calls that finish a few milliseconds apart, while longer values tend to delay rejection and leave more request capacity blocked. Measured call duration and upstream timeout values should guide that number.

Thread interruption can end the semaphore wait before the full duration expires. The implementation restores the interruption flag and reports failed permission acquisition rather than leaving the thread blocked until the timer ends. Normal saturation after the wait expires results in `BulkheadFullException` through the standard acquisition flow.

#### Testing Permit Exhaustion

Permit exhaustion is easiest to verify when the test holds every admitted call inside the protected method, attempts an extra call, then releases the blocked calls. Relying on short delays can produce unstable results because thread scheduling varies between test runs. `CountDownLatch` gives the test an exact point where two calls have crossed the Spring proxy, taken both permits, and paused before returning. With `maxWaitDuration` set to zero, the third call should fail immediately while the first two remain active. Spring Boot test properties can override the bulkhead values for this test context, while `BulkheadRegistry` exposes the remaining permit count.

JUnit Jupiter, AssertJ, and the Spring testing APIs come from the usual test starter:

```markup
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>
```

The dependency belongs in test scope, so it does not become part of the application runtime. JUnit runs the test, AssertJ handles the assertions, and Spring Boot creates the application context that applies the `@Bulkhead` annotation through AOP.

We can then hold two calls inside a two-permit bulkhead and attempt a third call before releasing either permit:

```markup
package com.example.inventory;

import static java.util.concurrent.TimeUnit.SECONDS;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import io.github.resilience4j.bulkhead.Bulkhead;
import io.github.resilience4j.bulkhead.BulkheadFullException;
import io.github.resilience4j.bulkhead.BulkheadRegistry;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;

@SpringBootTest(properties = {
        "resilience4j.bulkhead.instances.inventoryApi.max-concurrent-calls=2",
        "resilience4j.bulkhead.instances.inventoryApi.max-wait-duration=0ms"
})
@Import(PermitExhaustionTest.PermitTestConfiguration.class)
class PermitExhaustionTest {

    @Autowired
    private PermitTestService permitTestService;

    @Autowired
    private BulkheadRegistry bulkheadRegistry;

    @Test
    void rejectsThirdCallWhileBothPermitsAreOccupied() throws Exception {
        ExecutorService executor = Executors.newFixedThreadPool(2);
        CountDownLatch entered = new CountDownLatch(2);
        CountDownLatch release = new CountDownLatch(1);

        Future<String> first = executor.submit(
                () -> permitTestService.holdPermit(entered, release)
        );
        Future<String> second = executor.submit(
                () -> permitTestService.holdPermit(entered, release)
        );

        try {
            assertThat(entered.await(2, SECONDS)).isTrue();

            Bulkhead bulkhead =
                    bulkheadRegistry.bulkhead("inventoryApi");

            assertThat(
                    bulkhead.getMetrics()
                            .getAvailableConcurrentCalls()
            ).isZero();

            assertThatThrownBy(
                    () -> permitTestService.holdPermit(
                            new CountDownLatch(0),
                            new CountDownLatch(0)
                    )
            ).isInstanceOf(BulkheadFullException.class);

            release.countDown();

            assertThat(first.get(2, SECONDS)).isEqualTo("finished");
            assertThat(second.get(2, SECONDS)).isEqualTo("finished");

            assertThat(
                    bulkhead.getMetrics()
                            .getAvailableConcurrentCalls()
            ).isEqualTo(2);
        } finally {
            release.countDown();
            executor.shutdownNow();
        }
    }

    @TestConfiguration(proxyBeanMethods = false)
    static class PermitTestConfiguration {

        @Bean
        PermitTestService permitTestService() {
            return new PermitTestService();
        }
    }

    public static class PermitTestService {

        @io.github.resilience4j.bulkhead.annotation.Bulkhead(
                name = "inventoryApi"
        )
        public String holdPermit(
                CountDownLatch entered,
                CountDownLatch release
        ) throws InterruptedException {
            entered.countDown();
            release.await();
            return "finished";
        }
    }
}
```

`@SpringBootTest` starts the application context with a two-permit `inventoryApi` bulkhead and a zero admission wait. `@Import` adds `PermitTestService` as a Spring bean, which means calls to `holdPermit` pass through the Resilience4j aspect. Constructing the service directly with `new PermitTestService()` would bypass the proxy and would not test annotation interception.

Both executor threads enter `holdPermit`, decrement `entered`, then wait on `release`. The main test thread does not continue until `entered.await` confirms that both calls have reached the method. At that point, the registry metric should report zero available permits.

The third invocation receives fresh latches, but it never reaches them. Both permits are already occupied, and the zero wait causes the aspect to throw `BulkheadFullException` before the method body runs. This assertion verifies the admission boundary rather than a failure created inside the protected operation.

After `release.countDown`, the first two calls return and their permits go back to the bulkhead. Waiting for both `Future` results confirms that execution has finished before the test checks the metric again. The final value of two verifies that completion restored the full permit pool.

Latches keep the result repeatable because the test controls the exact point where capacity becomes full. Tests based only on `Thread.sleep` can pass or fail according to scheduler timing, processor load, or a slow test runner. Holding the calls until the assertion finishes removes that timing race and tests permit exhaustion directly.

#### BulkheadFullException Defines Saturation

Local saturation becomes `BulkheadFullException` when the caller cannot obtain permission through the configured admission rule. The exception contains the bulkhead name and reports that the named boundary does not permit further calls. The protected method body is skipped, so no HTTP request, database operation, or other downstream action begins for that rejected invocation.

Spring MVC can translate the exception into an HTTP response through `@RestControllerAdvice`. HTTP 503 communicates temporary service unavailability for this case and can include a retry delay when later attempts fit the API contract:

```markup
package com.example.inventory;

import io.github.resilience4j.bulkhead.BulkheadFullException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class BulkheadExceptionHandler {

    @ExceptionHandler(BulkheadFullException.class)
    public ResponseEntity<ProblemDetail> handleBulkheadFull(
            BulkheadFullException exception
    ) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.SERVICE_UNAVAILABLE,
                "Inventory capacity is temporarily full."
        );
        problem.setTitle("Inventory request capacity is full");
        problem.setProperty(
                "bulkhead",
                exception.getBulkheadName()
        );

        return ResponseEntity
                .status(HttpStatus.SERVICE_UNAVAILABLE)
                .header("Retry-After", "1")
                .body(problem);
    }
}
```

The handler receives the saturation exception and creates a 503 response through `ProblemDetail`. `getBulkheadName` records which boundary denied admission, which helps when the service contains several named bulkheads. The `Retry-After` header belongs in the response only when retrying after that delay fits the endpoint contract and the operation can safely run again.

HTTP 503 fits temporary local saturation, but the response should not claim that the downstream service failed. The rejected call never reached that service, so the failure came from the caller’s own concurrency boundary.

Fallback methods provide a second handling point when the service has a valid alternate result. The fallback stays in the same class as the annotated method, receives the original parameters followed by the matching exception, and returns the same type:

```markup
package com.example.catalog;

import io.github.resilience4j.bulkhead.BulkheadFullException;
import io.github.resilience4j.bulkhead.annotation.Bulkhead;
import org.springframework.stereotype.Service;

@Service
public class CatalogService {

    private final CatalogClient catalogClient;
    private final CatalogCache catalogCache;

    public CatalogService(
            CatalogClient catalogClient,
            CatalogCache catalogCache
    ) {
        this.catalogClient = catalogClient;
        this.catalogCache = catalogCache;
    }

    @Bulkhead(
            name = "catalogApi",
            fallbackMethod = "cachedCatalog"
    )
    public CatalogItem findItem(String sku) {
        return catalogClient.findItem(sku);
    }

    private CatalogItem cachedCatalog(
            String sku,
            BulkheadFullException exception
    ) {
        return catalogCache.findRecent(sku)
                .orElseThrow(() -> exception);
    }
}
```

`findItem` calls the remote catalog only after bulkhead admission succeeds. Saturation routes control to `cachedCatalog`, where the service tries to return a recent cached item. If no cached value exists, the same `BulkheadFullException` continues outward rather than returning fabricated success data.

The final exception parameter narrows the fallback to bulkhead saturation. Broader parameters such as `Exception` can also receive failures thrown inside the protected method, but that can combine saturation with HTTP errors, mapping failures, and domain exceptions that need different responses. Keeping the parameter narrow preserves that separation.

Actuator and Micrometer expose two useful semaphore gauges. `resilience4j.bulkhead.available.concurrent.calls` reports remaining permits, while `resilience4j.bulkhead.max.allowed.concurrent.calls` reports the configured ceiling. Zero available permits means the boundary is full at that instant, though brief periods at zero can appear during normal bursts.

Buffered events become available through the bulkhead event endpoint after `eventConsumerBufferSize` is configured and the endpoint is exposed. Permitted, rejected, and finished events let us compare admission pressure with dependency duration. Frequent rejection does not automatically mean the ceiling should rise because slow responses, connection-pool limits, traffic bursts, and missing client timeouts can all keep permits occupied longer.

Immediate retry inside the same request can send the caller back to a boundary that remains full. Retry around `BulkheadFullException` needs delay, a low attempt count, and an operation that can safely run again. Without those limits, repeated admission attempts add pressure during saturation and can delay recovery.

#### Registry Events and Saturation Diagnosis

Bulkhead rejection gives the caller an immediate result, while registry events reveal how the boundary behaves across a longer period. The `BulkheadRegistry` holds each named semaphore bulkhead, so the application can retrieve `inventoryApi`, inspect its metrics, and subscribe to events from that same instance. Resilience4j publishes `CALL_PERMITTED` after admission succeeds, `CALL_REJECTED` after admission fails, and `CALL_FINISHED` after an admitted call completes. Every event carries the bulkhead name, event type, and creation time.

Those three event types answer different questions. `CALL_PERMITTED` records traffic that crossed the concurrency boundary. `CALL_REJECTED` records callers that never entered the protected operation. `CALL_FINISHED` records returned capacity after admitted execution ended. Finished events do not separate successful calls from failed calls, so they cannot replace HTTP client metrics, exception counters, or circuit breaker results. Their purpose is to record the bulkhead lifecycle.

We can attach listeners during Spring Boot startup through the registry:

```markup
package com.example.inventory;

import io.github.resilience4j.bulkhead.Bulkhead;
import io.github.resilience4j.bulkhead.BulkheadRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
public class BulkheadEventConfiguration {

    private static final Logger log =
            LoggerFactory.getLogger(BulkheadEventConfiguration.class);

    @Bean
    ApplicationRunner inventoryBulkheadEvents(
            BulkheadRegistry bulkheadRegistry
    ) {
        return arguments -> {
            Bulkhead bulkhead =
                    bulkheadRegistry.bulkhead("inventoryApi");

            bulkhead.getEventPublisher()
                    .onCallPermitted(event ->
                            log.debug(
                                    "Bulkhead {} permitted a call at {}",
                                    event.getBulkheadName(),
                                    event.getCreationTime()
                            )
                    )
                    .onCallRejected(event ->
                            log.warn(
                                    "Bulkhead {} rejected a call at {}",
                                    event.getBulkheadName(),
                                    event.getCreationTime()
                            )
                    )
                    .onCallFinished(event ->
                            log.debug(
                                    "Bulkhead {} finished a call at {}",
                                    event.getBulkheadName(),
                                    event.getCreationTime()
                            )
                    );
        };
    }
}
```

`ApplicationRunner` registers the listeners after Spring Boot has created the application context. The registry lookup returns the same `inventoryApi` instance used by `@Bulkhead`, so events from annotated calls reach these consumers. Each callback receives its matching event type and can read the bulkhead name or creation time without tracking that data separately.

Event consumers run during event publication rather than through a separate executor supplied by the bulkhead. Slow network calls, database writes, or large formatting operations inside a listener can therefore delay the thread publishing the event. Brief logging or counter updates fit this location better, while heavier processing should be handed to a separate queue or executor. The Resilience4j event processor calls registered consumers directly as it processes an event.

Events explain movement through the boundary, while metrics provide the current capacity snapshot. `getAvailableConcurrentCalls` returns the permits still available, and `getMaxAllowedConcurrentCalls` returns the configured ceiling. Subtracting the available value from the maximum gives the number of permits occupied at that instant.

```markup
package com.example.inventory;

import io.github.resilience4j.bulkhead.Bulkhead;
import io.github.resilience4j.bulkhead.BulkheadRegistry;
import org.springframework.stereotype.Component;

@Component
public class BulkheadCapacityReader {

    private final BulkheadRegistry bulkheadRegistry;

    public BulkheadCapacityReader(
            BulkheadRegistry bulkheadRegistry
    ) {
        this.bulkheadRegistry = bulkheadRegistry;
    }

    public BulkheadCapacity currentInventoryCapacity() {
        Bulkhead bulkhead =
                bulkheadRegistry.bulkhead("inventoryApi");

        Bulkhead.Metrics metrics = bulkhead.getMetrics();

        int maximum =
                metrics.getMaxAllowedConcurrentCalls();
        int available =
                metrics.getAvailableConcurrentCalls();
        int active = maximum - available;

        return new BulkheadCapacity(
                maximum,
                active,
                available
        );
    }

    public record BulkheadCapacity(
            int maximum,
            int active,
            int available
    ) {
    }
}
```

The returned record separates the configured ceiling, occupied permits, and remaining capacity. With a maximum of 12 and three available permits, nine calls currently hold admission. That snapshot can change immediately after the method returns, so it should be treated as observation data rather than a reservation or admission decision.

Diagnosis becomes more useful when events and capacity readings are read beside latency. A brief burst can reduce available permits to zero, create a few rejected events, and then recover as finished events arrive. Sustained saturation keeps the available count near zero while rejected events continue across several observation periods. If permitted calls rise but finished calls arrive slowly, admitted operations are retaining capacity for longer durations.

Repeated `CALL_REJECTED` events do not automatically prove that `maxConcurrentCalls` is too low. Dependency latency could have increased, the HTTP connection pool could be blocking admitted calls, or downstream timeouts could be retaining permits longer than expected. Raising the ceiling in those conditions admits more concurrent pressure without correcting the reason that calls remain active.

Event counts also need context from incoming traffic. Ten rejected calls during a very large burst carry a different meaning from ten rejected calls out of a small request total. Rejection percentage, time spent at zero available permits, dependency latency, and active request count provide a fuller reading than any isolated value.

`CALL_FINISHED` requires careful interpretation because it records completion after success or failure. Finished events arriving quickly can represent healthy responses, HTTP errors, parsing failures, or client timeouts. Pairing bulkhead events with HTTP status counters and latency measurements separates capacity recovery from dependency health.

Registry events are local to the current Spring Boot process, just like semaphore permits. Each replica publishes events for its own named bulkhead and reports its own available count. Deployment-level diagnosis therefore needs instance labels or tags so several replicas do not become an undifferentiated total. An overloaded replica can reject calls while a quieter replica still has permits, particularly when traffic distribution is uneven.

#### Bulkhead Order Changes What Holds the Permit

Several Resilience4j annotations can appear on the same Spring method, yet their written order above the method does not control nesting. Spring AOP applies aspect precedence, and the lower order value runs earlier on entry while finishing later on exit. Current defaults place Retry outside CircuitBreaker, followed by RateLimiter, TimeLimiter, and Bulkhead. The bulkhead aspect uses `Ordered.LOWEST_PRECEDENCE`, which places it nearest the protected method in that default chain.

This order decides how long a permit remains occupied. With Bulkhead nearest the method, permission is acquired directly before the method invocation and returned directly after that invocation finishes. Outer processing performed before entry or after release does not retain the semaphore permit.

Retry behavior provides the strongest example. The following method carries both annotations:

```markup
package com.example.inventory;

import io.github.resilience4j.bulkhead.annotation.Bulkhead;
import io.github.resilience4j.retry.annotation.Retry;
import org.springframework.stereotype.Service;

@Service
public class InventoryLookupService {

    private final InventoryClient inventoryClient;

    public InventoryLookupService(
            InventoryClient inventoryClient
    ) {
        this.inventoryClient = inventoryClient;
    }

    @Retry(name = "inventoryApi")
    @Bulkhead(name = "inventoryApi")
    public InventoryResponse findInventory(String sku) {
        return inventoryClient.fetchInventory(sku);
    }
}
```

The source order of `@Retry` and `@Bulkhead` does not establish runtime nesting. Under the default aspect orders, Retry wraps Bulkhead. Every retry attempt reaches the inner bulkhead separately, requests a permit, runs `findInventory`, and returns the permit when that attempt finishes.

Suppose the first dependency call fails and Retry waits before the second attempt. The permit is returned before the retry delay begins because the inner bulkhead has already finished that attempt. When the delay ends, the next attempt must acquire a permit again. Saturation can therefore reject a later retry even though the first attempt previously received admission.

This default prevents retry delays from retaining semaphore capacity. Calls waiting between attempts occupy retry state, but they do not keep bulkhead permits during the pause. Every attempt still competes with current traffic at the admission boundary, which keeps the concurrency ceiling tied to active protected invocations.

Circuit breaker processing follows a related rule. With CircuitBreaker outside Bulkhead, a call blocked by an open breaker never reaches the inner bulkhead and never acquires a permit. Calls allowed through the breaker proceed to bulkhead admission. If the bulkhead rejects them, the exception travels back through the outer aspects, where their own exception rules determine how that outcome is treated.

Rate limiter admission also occurs before bulkhead admission under the default order. Calls denied by the rate limiter never spend a semaphore permit. Calls receiving a rate-limit permission still need a bulkhead permit before the protected method runs. The two boundaries answer separate capacity questions, and passing the outer boundary does not guarantee passage through the inner boundary.

TimeLimiter appears immediately outside Bulkhead in the default chain. Its exact effect depends on the asynchronous return type and cancellation behavior. The semaphore permit remains tied to completion of the protected asynchronous stage. Reporting a timeout to the caller does not return the permit while the underlying stage continues. Capacity comes back after that protected stage reaches completion, so cancellation must reach the running operation when early release is expected.

Manual decoration makes the nesting difference easier to see because the wrapper order appears directly in Java. This version places Retry outside Bulkhead:

```markup
import io.github.resilience4j.bulkhead.Bulkhead;
import io.github.resilience4j.retry.Retry;
import java.util.function.Supplier;

Supplier<InventoryResponse> dependencyCall =
        () -> inventoryClient.fetchInventory(sku);

Supplier<InventoryResponse> bulkheadProtected =
        Bulkhead.decorateSupplier(
                inventoryBulkhead,
                dependencyCall
        );

Supplier<InventoryResponse> retryProtected =
        Retry.decorateSupplier(
                inventoryRetry,
                bulkheadProtected
        );

InventoryResponse response = retryProtected.get();
```

Calling `retryProtected.get` enters Retry first. Retry invokes `bulkheadProtected` for each attempt, so every attempt acquires and returns its own permit. Any delay between attempts occurs outside the bulkhead reservation.

Reversing the wrappers changes the reservation period:

```markup
import io.github.resilience4j.bulkhead.Bulkhead;
import io.github.resilience4j.retry.Retry;
import java.util.function.Supplier;

Supplier<InventoryResponse> dependencyCall =
        () -> inventoryClient.fetchInventory(sku);

Supplier<InventoryResponse> retryProtected =
        Retry.decorateSupplier(
                inventoryRetry,
                dependencyCall
        );

Supplier<InventoryResponse> bulkheadProtected =
        Bulkhead.decorateSupplier(
                inventoryBulkhead,
                retryProtected
        );

InventoryResponse response = bulkheadProtected.get();
```

Calling `bulkheadProtected.get` acquires a permit before the retry sequence starts. The permit remains occupied across the first attempt, retry delays, later attempts, and final completion. This form limits complete retry sequences rather than individual dependency attempts, but backoff periods now retain scarce concurrency capacity.

The difference can become large when retries have long delays. Three attempts separated by two long waits can hold one outer bulkhead permit for the full sequence. With Retry outside Bulkhead, the same call returns its permit after every attempt and holds no permit during either delay.

Spring annotation nesting does not change merely because the annotation lines are rearranged. Retry, CircuitBreaker, RateLimiter, TimeLimiter, and Bulkhead all expose configurable aspect-order properties. Bulkhead defaults to `Ordered.LOWEST_PRECEDENCE`, placing it nearest the protected method in the default chain, but `bulkheadAspectOrder` under `resilience4j.bulkhead` can replace that value. Runtime nesting follows the configured order values.

Order should be checked whenever the same method carries several resilience annotations because every wrapper changes what gets counted, retried, timed, or admitted. For semaphore bulkheads, the central question is the period covered by the permit. The default Spring order keeps that reservation close to each protected invocation, while manual decoration can extend it across a larger operation such as a full retry sequence.

### Conclusion

Resilience4j semaphore bulkheads limit concurrent calls through permits acquired before entry and returned after completion. `maxConcurrentCalls` sets the ceiling, `maxWaitDuration` controls admission delay, and `BulkheadFullException` marks local saturation before the protected dependency runs. Testing, registry events, and wrapper order reveal when permits are exhausted, how capacity returns, and how retries or timeouts affect the period a permit remains occupied.

![](https://substackcdn.com/image/fetch/$s_!8vJJ!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F2f41f59b-1734-4e4a-8388-87d450401c9a_276x276.png)

Spring Boot icon by Icons8
