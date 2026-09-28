---
title: "How to Run Async Methods in Spring Boot"
source: "https://alexanderobregon.substack.com/p/how-to-run-async-methods-in-spring?utm_source=substack&utm_medium=email"
author:
  - "[[Alexander Obregon]]"
published: 2026-09-19
created: 2026-09-29
description: "Slow operations do not always need to hold the HTTP request thread until every step finishes."
tags:
  - "clippings"
---

> [!summary]
> `@EnableAsync` turns on proxy-based interception, and `@Async` methods called through another Spring bean are handed to an executor: Boot's `ThreadPoolTaskExecutor`, or a virtual-thread `SimpleAsyncTaskExecutor` when `spring.threads.virtual.enabled=true`. The article covers the self-invocation pitfall, transactions and thread-locals not following the call onto the new thread, how core size, queue capacity, and max size interact in `spring.task.execution.pool`, and named executors. Results and failures come back through a returned `CompletableFuture` or, for `void` methods, an `AsyncUncaughtExceptionHandler`; in-memory async execution is not durable.

Slow operations do not always need to hold the HTTP request thread until every step finishes. Sending email, generating a report, recording an audit event through a remote service, or calling a slower external API can run on another executor when the caller does not need the result before continuing. Spring handles this with `@Async`, while `@EnableAsync` turns on annotation-driven asynchronous method execution. Spring Boot can provide the executor when the application has not defined one, letting selected service methods move away from the request thread while the rest of the application keeps its normal synchronous flow.

### How Spring Async Execution Runs

Spring handles asynchronous method execution through interception rather than requiring callers to use a different style of Java method invocation. Code can call a service method normally, while Spring gets a chance to intercept that invocation before the target method begins. If the method carries `@Async`, Spring sends the invocation to an executor and allows the calling thread to continue. That boundary lets selected service operations run away from the original thread without forcing the rest of the application into the same asynchronous flow.

Two parts need to be present before that behavior can happen. `@EnableAsync` activates Spring’s annotation processing for asynchronous methods, while `@Async` marks methods that should pass through the async interceptor. Spring Boot can provide the executor that receives those invocations when the application hasn’t supplied its own executor configuration.

#### Turning On Async Processing

Before `@Async` can affect a method call, Spring needs async annotation processing active in the application context. Placing `@EnableAsync` on a configuration class registers the infrastructure Spring uses to recognize eligible method calls and send them to an executor.

Keeping that activation in a dedicated configuration class gives us a compact place for it:

```markup
package com.example.demo.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;

@Configuration(proxyBeanMethods = false)
@EnableAsync
public class AsyncConfig {
}
```

`@Configuration` places `AsyncConfig` in the Spring application context, while `@EnableAsync` activates annotation-driven asynchronous execution. The `proxyBeanMethods = false` setting is appropriate here because this class doesn’t call other `@Bean` methods that need interception through a configuration proxy.

Turning on `@EnableAsync` doesn’t make every method asynchronous. Methods without an async boundary continue on the thread that called them, so we can add asynchronous execution only where the application needs it. That gives us a narrow change at the service boundary rather than changing how unrelated service calls behave.

Spring doesn’t require `@EnableAsync` to live in its own class. Smaller applications can place it directly on the main Spring Boot application class:

```markup
package com.example.demo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class DemoApplication {

    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}
```

Both locations activate the same async infrastructure. The first version gives the async configuration its own place, while the second keeps the activation next to the rest of the application bootstrap configuration. Spring only needs the annotation to be discovered as part of a managed configuration class.

Spring Boot also participates in executor selection. If the application context hasn’t supplied an executor that takes over regular async execution, Boot can provide an `AsyncTaskExecutor`. With virtual threads disabled, Spring Boot gives us `ThreadPoolTaskExecutor`. On Java 21 or later, setting `spring.threads.virtual.enabled=true` changes Boot’s auto-configured executor to a `SimpleAsyncTaskExecutor` backed by virtual threads.

Service methods don’t need different annotations for those two executor styles. `@Async` talks to Spring’s executor abstraction, so the service remains focused on the async boundary while Boot chooses the executor implementation from the application configuration. The executor is where intercepted method invocations eventually run. `@EnableAsync` doesn’t directly create a fresh Java thread every time Spring encounters `@Async`. Spring first registers the interception infrastructure, then that infrastructure delegates accepted invocations to the executor associated with async execution.

Following the call from beginning to end gives us three distinct pieces. `@EnableAsync` activates the interception feature, `@Async` marks the method boundary, and the executor runs the intercepted invocation on a different thread.

#### What Happens During the Call

Calling an `@Async` method still looks like an ordinary Java method call from the caller’s point of view. Spring’s default async mode is proxy based, so the Spring-managed reference held by another bean can intercept the call before the target object receives it.

We can see that boundary with two small service classes. The first service receives another Spring-managed bean through constructor injection:

```markup
package com.example.demo.orders;

import org.springframework.stereotype.Service;

@Service
public class OrderService {

    private final ReceiptService receiptService;

    public OrderService(ReceiptService receiptService) {
        this.receiptService = receiptService;
    }

    public void finishOrder(long orderId) {
        receiptService.prepareReceipt(orderId);
    }
}
```

`OrderService` doesn’t create `ReceiptService` with `new`. Spring supplies the managed reference through the constructor, which gives Spring the interception point needed when `prepareReceipt` is called. From the code inside `finishOrder`, the invocation still reads like a regular method call.

The receiving service can then mark the method with `@Async`:

```markup
package com.example.demo.orders;

import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

@Service
public class ReceiptService {

    @Async
    public void prepareReceipt(long orderId) {
        buildReceipt(orderId);
    }

    private void buildReceipt(long orderId) {
        // Receipt processing
    }
}
```

During `receiptService.prepareReceipt(orderId)`, the call reaches Spring’s proxy before it reaches the method body. Spring sees `@Async`, submits the intercepted invocation to the configured executor, and returns control to `OrderService` without waiting for `prepareReceipt` to finish. The method body then runs from an executor thread rather than continuing on the thread that called `finishOrder`.

That sequence is why the location of the call is important. Spring needs the invocation to cross the managed bean proxy so the async interceptor can act on it. Calling the same method internally from the same object follows normal Java dispatch and never crosses that proxy boundary.

The following class has an `@Async` method, but the call to it remains inside the same object:

```markup
package com.example.demo.orders;

import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

@Service
public class ReceiptService {

    public void startReceipt(long orderId) {
        prepareReceipt(orderId);
    }

    @Async
    public void prepareReceipt(long orderId) {
        // Receipt processing
    }
}
```

`startReceipt` calls `prepareReceipt` directly through `this`, even though `this` isn’t written explicitly. Spring’s proxy never receives that internal invocation, so the async interceptor doesn’t submit it to the executor. The call follows normal synchronous Java execution from `startReceipt` into `prepareReceipt`.

Placing the async boundary between managed beans avoids that self-invocation behavior. It also makes the thread transition easier to follow because one service owns the caller side while another service owns the asynchronous method. The same rule explains why constructing an async service manually with `new ReceiptService()` bypasses `@Async`. That object wasn’t obtained from Spring, so no Spring proxy exists around that reference.

Thread changes also affect state associated with the calling thread. Spring transaction state is bound to the current thread, which means a transaction active around the caller doesn’t automatically move to the executor thread. If asynchronous processing needs its own database transaction, that transaction has to begin within the async execution rather than relying on the caller’s transaction to continue there.

Other thread-local values follow the same basic rule, because moving execution to an executor thread creates a different thread context, so code inside an async method shouldn’t assume every value associated with the original request thread will automatically appear on the executor thread.

From the caller’s perspective, very little syntax changes. We still call a Java method through a Spring-managed bean reference. The important activity happens at that bean boundary, where Spring intercepts the invocation, recognizes `@Async`, submits the invocation to an executor, and lets the caller continue. That mechanism provides the base for later decisions around executor configuration, returned values, failure handling, and moving slower operations away from HTTP request threads.

### Moving Slow Operations Off the Request Thread

After asynchronous execution is available, the next step is deciding which service calls can leave the request thread without delaying the response. Good candidates are operations whose result is not needed before the HTTP exchange can finish, such as sending a notification, creating a report, updating a remote search index, or starting a longer export. We still keep the request flow responsible for anything the response depends on, while `@Async` moves selected follow-up processing to the executor.

This distinction keeps the application flow easy to follow. Saving an order before returning a success response belongs on the request thread if the response means the order was accepted and stored. Sending a confirmation message after that save can run asynchronously because the caller does not need to wait for the mail provider before receiving the response. The same reasoning applies to other slower operations that can finish after the request has ended.

#### Making a Service Method Async

Selected service methods can move away from the request thread by placing `@Async` on the method that represents the background boundary. We keep the method on a Spring-managed bean so the call passes through Spring’s async interceptor, then let the caller continue after the invocation has been submitted to the executor.

Take a service that starts an invoice export after the invoice has already been stored:

```markup
package com.example.demo.invoice;

import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

@Service
public class InvoiceExportService {

    private final ExportClient exportClient;

    public InvoiceExportService(ExportClient exportClient) {
        this.exportClient = exportClient;
    }

    @Async
    public void exportInvoice(long invoiceId) {
        exportClient.createInvoiceExport(invoiceId);
    }
}
```

`exportInvoice` returns `void` because the caller does not need a result from the export. The `@Async` annotation tells Spring to submit the invocation to the async executor, so `ExportClient` runs from the executor thread after the caller has crossed that boundary. The method still receives normal Java arguments, which lets us pass an identifier or other data needed by the background operation.

The HTTP layer can then finish its response without waiting for the export call to finish:

```markup
package com.example.demo.invoice;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class InvoiceExportController {

    private final InvoiceExportService invoiceExportService;

    public InvoiceExportController(InvoiceExportService invoiceExportService) {
        this.invoiceExportService = invoiceExportService;
    }

    @PostMapping("/invoices/{invoiceId}/export")
    public ResponseEntity<Void> export(@PathVariable long invoiceId) {
        invoiceExportService.exportInvoice(invoiceId);
        return ResponseEntity.accepted().build();
    }
}
```

We call `exportInvoice` through the injected Spring bean, then return HTTP `202 Accepted`. That response says the request was accepted for processing rather than claiming the export has already finished. The request thread no longer waits for the slower export operation, while the executor thread continues processing after the controller returns.

Moving an operation off the request thread also changes what we should pass into the method. Values such as identifiers, email addresses, or immutable request data are usually better suited to crossing the boundary than objects tied to the HTTP request itself. If the async method needs current database data, it can load that data from an identifier during its own execution rather than depending on request-scoped state that has already reached the end of its lifetime.

The timing of database changes needs similar care. If a request stores data and immediately calls an async method that expects to read that data, the async thread can begin before the caller’s surrounding transaction has committed. Code that depends on committed data should place the async call at a point where that data is available to other transactions, or coordinate the handoff through transaction-aware application logic. This comes from the fact that two threads can now move forward independently.

#### Controlling the Thread Pool

Spring Boot can create the async executor automatically, but applications that run regular platform threads can tune its pool through `spring.task.execution` properties. Current Spring Boot defaults to eight core threads for its auto-configured `ThreadPoolTaskExecutor`, and pool settings let us change how much concurrency and queued processing the executor can hold.

The pool can be bounded through these properties:

```markup
spring.task.execution.thread-name-prefix=async-
spring.task.execution.pool.core-size=4
spring.task.execution.pool.max-size=8
spring.task.execution.pool.queue-capacity=100
spring.task.execution.pool.keep-alive=30s
```

We now have four core threads, room to grow to eight threads, and a queue that can hold up to 100 pending submissions. The `async-` prefix also helps identify executor threads in logs or thread dumps. Threads above the core size can be reclaimed after remaining idle for the configured keep-alive period.

Queue capacity changes how the core and maximum sizes interact. While fewer than four executor threads are active, new submissions can run on available core threads. After the core size is occupied, later submissions enter the queue until it reaches 100 entries. Only after that queue fills can the executor grow beyond four threads, up to the maximum of eight. If the queue is full and all eight threads are occupied, the executor rejects the next submission rather than letting the backlog grow without a limit.

That behavior is worth keeping in mind when changing only `max-size`. An unbounded queue can keep submissions waiting in the queue instead of allowing the pool to grow beyond its core size. Giving the queue a finite capacity creates a point where Spring’s thread pool can begin adding threads above the core value. Pool sizes and queue capacity therefore need to be selected as a group rather than treated as unrelated numbers.

The right values depend on what the async methods spend their time doing. Processing that consumes CPU for most of its lifetime puts different pressure on the machine than calls that spend much of their lifetime waiting for network or storage I/O. Measurements from the application can tell us how long the queue becomes, how busy the executor remains, and how long requests wait before background processing begins.

Virtual threads change this part of the configuration. With Java 21 or later and `spring.threads.virtual.enabled=true`, Spring Boot auto-configures a `SimpleAsyncTaskExecutor` backed by virtual threads instead of the regular `ThreadPoolTaskExecutor`. Pool sizing properties do not control that virtual-thread execution model, so `core-size`, `max-size`, and the regular pool queue should not be treated as controls for virtual-thread concurrency.

Applications can also assign a named executor to a particular async method when different categories of processing need different capacity. The qualifier supplied to `@Async` selects an `Executor` or `TaskExecutor` bean by name or qualifier.

```markup
@Async("reportExecutor")
public void rebuildMonthlyReport(long accountId) {
    reportGenerator.rebuild(accountId);
}
```

We have explicitly directed `rebuildMonthlyReport` to the bean named `reportExecutor` rather than leaving executor selection at the default. That can keep long report processing from consuming the same executor capacity reserved for shorter asynchronous calls elsewhere in the application.

#### Returning a CompletableFuture

Some asynchronous methods produce data that the caller needs later. Spring allows an `@Async` method to return `Future`, including the more capable `CompletableFuture`, so the caller can receive a handle immediately and react when the calculation finishes. The target method still runs on the executor thread, while the proxy exposes the asynchronous result to the caller.

We can return a generated summary without making the caller wait at the point of invocation:

```markup
package com.example.demo.summary;

import java.util.concurrent.CompletableFuture;

import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

@Service
public class AccountSummaryService {

    private final SummaryRepository summaryRepository;

    public AccountSummaryService(SummaryRepository summaryRepository) {
        this.summaryRepository = summaryRepository;
    }

    @Async
    public CompletableFuture<AccountSummary> buildSummary(long accountId) {
        AccountSummary summary = summaryRepository.createSummary(accountId);
        return CompletableFuture.completedFuture(summary);
    }
}
```

Spring invokes `buildSummary` on the executor thread, where `createSummary` produces the result. The target method returns `CompletableFuture.completedFuture(summary)` because its declared signature has to match the asynchronous return type. The proxy gives the caller the asynchronous future that tracks completion of the intercepted method invocation.

Calling code can attach a continuation rather than blocking immediately:

```markup
CompletableFuture<AccountSummary> future =
        accountSummaryService.buildSummary(accountId);

future.thenAccept(summary ->
        logger.info("Summary completed for account {}", summary.accountId()));
```

We receive the `CompletableFuture` immediately, then register `thenAccept` for processing that should run after the summary becomes available. The calling thread does not need to stop at `buildSummary` and wait for the result before moving forward.

Methods such as `get()` and `join()` still allow the caller to wait for completion, but calling either one immediately after invoking the async method turns that point back into a blocking wait. There are valid cases where later code eventually needs the value, yet delaying that wait or composing more `CompletableFuture` stages preserves more of the benefit gained from asynchronous execution.

Failures also travel through a returned future. If the async method throws before producing its result, the future completes exceptionally rather than delivering a normal value. That gives the caller a place to attach recovery or logging behavior as part of the future chain.

```markup
accountSummaryService.buildSummary(accountId)
        .exceptionally(ex -> {
            logger.error("Summary failed for account {}", accountId, ex);
            return AccountSummary.empty(accountId);
        });
```

`exceptionally` runs when the future completes with an exception and returns a fallback `AccountSummary` for the rest of the chain. We can choose different completion methods when recovery is not appropriate, but the important part is that result-bearing async methods carry failure information through the returned future rather than relying on the `void` exception channel.

#### Handling Failures

Failure handling depends on the return type of the async method. With `CompletableFuture`, the caller has an object that can carry successful completion or an exception. With `void`, there is no returned object through which Spring can deliver an exception to the original caller, so uncaught exceptions from that async method are sent to an `AsyncUncaughtExceptionHandler`. Spring logs those exceptions by default.

Applications that need their own handling for `void` async failures can provide that handler through `AsyncConfigurer`:

```markup
package com.example.demo.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.aop.interceptor.AsyncUncaughtExceptionHandler;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.scheduling.annotation.EnableAsync;

@Configuration(proxyBeanMethods = false)
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {

    private static final Logger logger =
            LoggerFactory.getLogger(AsyncConfig.class);

    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return (ex, method, params) ->
                logger.error(
                        "Async method {} failed with parameters {}",
                        method.getName(),
                        params,
                        ex);
    }
}
```

`getAsyncUncaughtExceptionHandler` supplies the handler Spring calls after an uncaught exception leaves a `void` async method. We record the method name, its parameters, and the exception, which gives the application more context than relying on an unstructured failure message. `AsyncConfigurer` provides default methods, so this configuration does not have to replace the async executor merely because we want a custom exception handler.

Catching an exception inside the async method is also valid when the method itself has enough context to react. Logging alone can be appropriate for an optional notification, while processing tied to billing, external state changes, or processing that must eventually complete can require retry logic or durable persistence beyond the executor.

`@Async` keeps submitted invocations inside the running application process. That execution is not durable, so unfinished processing can disappear if the process stops before it completes. Operations that must survive a restart are better backed by persistent state, a message broker, or a durable processing mechanism rather than relying only on an in-memory async executor.

### Conclusion

Spring async works by letting a call cross a Spring-managed proxy, where `@Async` sends the method to an executor and returns control to the caller. `@EnableAsync` activates that interception, while executor settings decide where the work runs and `CompletableFuture` or an exception handler handles results and failures. With that boundary in place, slower work can leave the request thread without changing the rest of the service flow.

![](https://substackcdn.com/image/fetch/$s_!B2I0!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F347183b0-1d5c-44c9-acb7-ca129a45d11b_276x276.png)

Spring Boot icon by Icons8
