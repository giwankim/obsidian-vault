---
title: "How to Improve Spring Boot Logging for Production"
source: "https://alexanderobregon.substack.com/p/how-to-improve-spring-boot-logging?utm_source=substack&utm_medium=email"
author:
  - "[[Alexander Obregon]]"
published: 2026-09-17
created: 2026-09-29
description: "Production logging becomes far more valuable when each entry carries enough context to answer practical questions without making someone dig through long blocks of text."
tags:
  - "clippings"
---

> [!summary]
> Spring Boot's built-in structured logging (Logstash/ECS/GELF JSON), SLF4J 2 fluent `addKeyValue` fields, and an MDC correlation ID set in a `OncePerRequestFilter` make production logs searchable by named fields instead of message text. The article also covers package-specific levels and logging groups, a compact request-logging filter (method, URI without query string, status, duration), and keeping secrets and PII out of logs. Exceptions should be logged once, with the throwable attached, at the layer that actually handles the failure.

Production logging becomes far more valuable when each entry carries enough context to answer practical questions without making someone dig through long blocks of text. Spring Boot applications can already record controller activity, service events, database failures, and exceptions, but finding the event tied to a specific request gets harder when identifiers and request details are buried inside free-form messages. Structured fields give important values their own place in the log, while correlation IDs connect entries that belong to the same request as it moves through the application. Package-specific log levels can keep noisy libraries from filling production output, request logging can capture details such as the HTTP method, URI, response status, and duration, and careful exception logging can preserve the information needed to trace a failure back to its source. Spring Boot already includes the logging support needed for these changes, so most of the improvement can come from configuration and focused SLF4J logging rather than replacing the application’s logging framework.

### Giving Logs Searchable Context

Searchable logs depend on context that stays attached to an event in a predictable form. Production output can contain entries from controllers, services, database clients, scheduled jobs, and framework components, so a message by itself rarely tells the whole story. Fields such as an order ID, customer ID, operation name, correlation ID, or service name give a log platform direct values it can filter without pulling identifiers out of sentence text. Spring Boot can emit structured JSON directly, while SLF4J can attach event fields and MDC values that become part of that JSON output.

Much of the value comes from giving related information a consistent place. During an order investigation, we should be able to search for the order ID, find the events tied to it, and then follow the correlation ID through activity from the same request. That turns the log stream into searchable event data instead of forcing us to read long stretches of output line by line.

#### Structured JSON Output

Production log platforms can do far more with structured data than with identifiers buried inside formatted sentences. Spring Boot supports JSON output in Elastic Common Schema, GELF, and Logstash formats. Console output and file output can be configured independently, which works well when standard output is collected by a container platform while files follow a different storage policy.

Logstash JSON can be selected directly from `application.properties`:

```markup
logging.structured.format.console=logstash
```

We tell Spring Boot to format console output as Logstash JSON. From that point forward, each console event becomes a JSON object containing standard logging data such as the timestamp, message, logger name, thread name, and level. MDC values and SLF4J fluent fields can also become members of that structured event.

That difference changes how production events can be searched. If order `78125` appears only inside a message such as `Order 78125 submitted`, the logging platform receives text that must be searched as text. Giving the order identifier its own `orderId` field lets the platform filter directly on that value, group related events, or combine it with other fields such as service name or event type.

Spring Boot can also emit Elastic Common Schema output when the surrounding logging platform expects ECS:

```markup
spring.application.name=order-service
logging.structured.format.console=ecs
```

The first property gives Spring Boot the application name, while the second selects ECS for console events. With ECS output, that application name becomes the default service name unless a different ECS service value is configured, which keeps service identity consistent without repeating it in every logging call.

Projects with `logback-spring.xml` need extra attention because a custom appender owns its encoder configuration. Setting the Spring Boot structured format property does not replace an encoder that was already declared inside that file. Spring Boot provides `StructuredLogEncoder` so a custom Logback appender can still follow the configured structured console format:

```markup
<encoder class="org.springframework.boot.logging.logback.StructuredLogEncoder">
    <format>${CONSOLE_LOG_STRUCTURED_FORMAT}</format>
    <charset>${CONSOLE_LOG_CHARSET}</charset>
</encoder>
```

We place the encoder inside the relevant appender so Logback can format that appender’s events through Spring Boot’s structured logging support. `CONSOLE_LOG_STRUCTURED_FORMAT` supplies the selected console format, while `CONSOLE_LOG_CHARSET` carries the configured character set. Projects with deeper Logback configuration can keep their custom file while still getting Spring Boot’s structured output.

Structured JSON should stay focused rather than turning every event into a large record filled with unrelated values. Fields earn their place when they help identify the event, connect it to a business operation, or narrow an investigation. Dumping large objects into every entry usually adds storage cost and makes searches harder to scan.

Consistent names become important as the application grows. If the same order identifier appears as `orderId` in one class, `order_id` somewhere else, and `id` in a third place, every search has to account for all three forms. Keeping one field name for the same concept gives us predictable queries across controllers, services, scheduled processing, and integration code.

#### Add Fields to Important Events

Readable messages still have value because developers will inspect logs directly during troubleshooting. Searchable fields serve a different purpose by giving identifiers and event data their own named entries instead of leaving a logging platform to interpret sentence text.

Traditional parameterized SLF4J logging can record an order ID inside the message:

```markup
log.info("Order {} submitted for customer {}", orderId, customerId);
```

We pass `orderId` and `customerId` into placeholders, so the resulting line is easy to read in a terminal. Those values still belong to the formatted message, though, rather than existing as named fields that a JSON-aware logging platform can query directly.

SLF4J 2 provides a fluent logging API with `addKeyValue`, which Spring Boot’s built-in structured formats can carry into the generated JSON event:

```markup
log.atInfo()
        .addKeyValue("event", "order-submitted")
        .addKeyValue("orderId", orderId)
        .addKeyValue("customerId", customerId)
        .log("Order submitted");
```

We begin at `INFO`, attach an event name, then add the order and customer identifiers before writing the human-readable message. The resulting event still says what happened, while `event`, `orderId`, and `customerId` become named data that can be filtered or grouped independently.

Stable event names can be valuable when wording changes later. A message could move from `Order submitted` to `Order accepted for processing` during normal editing, while `event=order-submitted` can stay unchanged. Saved searches and dashboards can then depend on the event field rather than the exact message text.

Structured fields can also keep native value types such as numbers and booleans rather than turning everything into text:

```markup
log.atInfo()
        .addKeyValue("event", "inventory-reserved")
        .addKeyValue("orderId", orderId)
        .addKeyValue("productId", productId)
        .addKeyValue("quantity", quantity)
        .addKeyValue("backordered", backordered)
        .log("Inventory reservation completed");
```

We attach identifiers first, then keep `quantity` as a numeric value and `backordered` as a boolean value. JSON-aware log storage can then treat those fields according to their data type, which makes filtering on quantities or backorder state much more practical than parsing those values from a sentence.

Fields are strongest when they represent durable facts about the event. Business identifiers, operation names, dependency names, status values, attempt counts, and result categories usually belong naturally in structured data. Full domain objects usually do not because serializing an entire order, customer, or request object can create oversized entries and copy unrelated data into long-term storage.

Naming consistency deserves the same attention as the values themselves. If payment events always record `paymentProvider`, developers do not have to remember that one class calls the same concept `provider`, another calls it `gateway`, and a third calls it `processorName`. Keeping the vocabulary stable makes cross-class searches far less tedious.

Field count also deserves restraint. Logging every local variable from a method does not create better diagnostics by default. We get more value from a smaller group of fields that tells us which business operation happened, which entity it involved, and what result the operation produced.

#### Carry a Correlation ID

Individual fields explain a single event, while a correlation ID connects events produced during the same request. Two requests can reach the same endpoint within milliseconds of each other and produce interleaved entries, making timestamps alone a weak way to tell which lines belong to which request. MDC gives application code a context map associated with logging activity on the current thread. Spring Boot’s built-in structured JSON formats include MDC entries, so a correlation value placed there can travel into compatible log events without adding it manually to every SLF4J call.

For a servlet application without distributed tracing, `OncePerRequestFilter` can create a correlation ID near the beginning of request processing:

```markup
package com.example.orders.logging;

import java.io.IOException;
import java.util.UUID;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class CorrelationIdFilter extends OncePerRequestFilter {

    private static final String MDC_NAME = "correlationId";
    private static final String HEADER_NAME = "X-Correlation-ID";

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        String correlationId = UUID.randomUUID().toString();

        MDC.put(MDC_NAME, correlationId);
        response.setHeader(HEADER_NAME, correlationId);

        try {
            filterChain.doFilter(request, response);
        } finally {
            MDC.remove(MDC_NAME);
        }
    }
}
```

We create a UUID when the request enters the filter, place it in MDC under `correlationId`, and return the same value through `X-Correlation-ID`. The call to `filterChain.doFilter` then lets request processing continue while the MDC value remains available to logging calls on that thread.

The `finally` block removes the value after processing finishes. Servlet containers reuse request threads, so leaving the MDC entry behind could let a later request handled by the same thread inherit context from an earlier request. Removing it at the boundary keeps that request context limited to the lifetime we intended.

Sending the correlation ID back in the response can help during support cases as well. Client software or support staff can retain that identifier and provide it when reporting a failed call, giving developers a direct value to search instead of relying only on timestamps, endpoint names, or user reports.

Incoming correlation IDs need a defined policy rather than being accepted blindly. Some environments let an API gateway create the identifier and forward it downstream so several services share the same value. Public clients should not automatically control every internal logging identifier, particularly when downstream components expect a restricted format or maximum length. Generating the value inside the service is a reasonable starting point when no trusted upstream component already owns request correlation.

Applications with Micrometer Tracing already have trace context for broader request tracking, and those trace identifiers can remove the need for a second custom request ID. Trace and span values also integrate with logging context, making them more suitable when activity crosses service boundaries.

Thread changes deserve attention because MDC context is tied to execution context and does not automatically follow every asynchronous handoff. If request processing moves into a different executor, the correlation information needs an explicit propagation mechanism when later events must retain the same request identity. Synchronous servlet processing does not expose that issue as readily, which is why correlation can appear complete until asynchronous processing enters the application.

#### Keep Sensitive Data Out

More searchable context increases the amount of information copied into the logging platform, so field selection needs to account for privacy and security from the beginning. Production logs can remain stored long after an HTTP request finishes, and access to those logs can extend beyond the people who normally interact with the original application data.

Authorization headers, passwords, session cookies, access tokens, refresh tokens, private cryptographic material, payment card values, and authentication credentials should stay out of routine logs. Request and response bodies deserve similar care because their contents can hold personal or confidential data even when the endpoint name gives no warning that such information is present.

Query strings also deserve a bit more restraint. URLs can carry email addresses, search terms, temporary tokens, account references, or private values supplied by a client. Recording only the request URI without its query string reduces the chance that those values enter long-term log storage, while approved non-sensitive values can be added individually when they are needed for diagnosis. Business identifiers fall into a more contextual area. Internal order IDs can help during an investigation because they connect related events without exposing a customer’s name, email address, or street address. Logging an entire customer object just to capture that order relationship would copy far more information than the investigation needs.

Structured fields make those decisions deliberate because developers can choose which values become named members of an event. Fields such as `orderId`, `productId`, `event`, and `paymentProvider` are easy to review in code, while serialized request bodies can hide private values several levels deep and can change as request models evolve.

Values coming from outside the application deserve the same care. Usernames, request headers, form fields, uploaded filenames, and data returned by external services can all contain information that should not enter production logs. Recording only the identifiers and state needed for diagnosis keeps the event focused while limiting the amount of private information copied into long-lived storage.

Sensitive data can also appear indirectly through objects whose `toString()` output includes more fields than expected. Passing a full request object, entity, or response model into a logging call can expose values that were never intentionally selected for logging. Choosing individual fields gives us tighter control over what reaches the log and makes later review far more manageable.

### Control Production Log Detail

Production logging becomes harder to read when every package reports at the same level and every request produces more information than developers need during normal operation. Good production configuration keeps routine events available while reserving deeper detail for the areas currently being investigated. Request entries should capture enough information to reconstruct what reached the application and how it finished, while exception entries should preserve the failure without recording the same stack trace at several layers. The severity attached to an event also carries meaning. `INFO`, `DEBUG`, `WARN`, and `ERROR` should reflect what happened rather than how closely developers are examining a class at that moment. Keeping those meanings consistent makes log searches, dashboards, and alerts far more dependable.

#### Set Package-Specific Levels

Spring Boot lets us assign logging levels through `logging.level.<logger-name>`, including the root logger and individual package names. That gives us much finer control than moving the entire application to `DEBUG` when only a small area needs extra detail.

Production configuration can keep the general level at `INFO` while giving a smaller package `DEBUG` output:

```markup
logging.level.root=INFO
logging.level.com.example.orders=INFO
logging.level.com.example.orders.payment=DEBUG
logging.level.org.springframework.web=INFO
logging.level.org.hibernate.SQL=WARN
```

We start with `INFO` at the root, then give the payment package more detail through `DEBUG`. Spring web logging remains at `INFO`, while Hibernate SQL output is restricted to `WARN`. The result keeps deeper diagnostic output centered on payment code instead of opening every dependency and application package to `DEBUG`.

Package hierarchy matters because logger configuration follows Java package names. Setting `com.example.orders.payment` to `DEBUG` affects loggers beneath that package unless a more specific logger has its own level. Code elsewhere under `com.example.orders` can remain at `INFO`, which keeps extra output focused on the area being investigated. Spring Boot also supports logging groups. Groups help when several logger names belong to the same operational area but do not share a convenient parent package. Spring Boot provides predefined `web` and `sql` groups, while custom groups can cover application packages that developers want to control as a unit.

```markup
logging.group.checkout=com.example.orders.payment,com.example.orders.inventory,com.example.orders.shipping
logging.level.checkout=DEBUG
```

We give the related packages the group name `checkout`, then assign `DEBUG` to that group. Payment, inventory, and shipping code can now produce deeper detail during a checkout investigation while unrelated packages retain their existing levels.

Severity should follow the meaning of the event. Routine business milestones worth retaining can remain at `INFO`, while deeper diagnostic values belong at `DEBUG`. `WARN` is appropriate for an unusual condition that the application can recover from, while `ERROR` should represent an operation that failed and deserves attention.

That distinction affects monitoring too, if every rejected client request becomes `ERROR`, an alert based on error volume can report trouble while the server is behaving as intended. Recording dependency failures only at `INFO` creates the opposite problem because serious failures can disappear among normal activity.

Spring Boot Actuator can expose logger configuration at runtime through the `loggers` endpoint when Actuator is present and that endpoint has been exposed. Individual logger levels can then be changed without restarting the application, which can help during a focused production investigation. Management endpoint access should follow the application’s normal security policy because raising log levels can increase output and expose more diagnostic data.

Long-term logger values normally belong in application configuration, environment values, or deployment configuration so the intended levels remain documented and repeatable. Runtime changes are better treated as temporary diagnostic adjustments that can be returned to their normal values after the investigation ends.

#### Record Request Information

HTTP request logging gives us an outer record of traffic moving through the web layer. Rather than copying every header or request body, a compact request event can capture the HTTP method, request URI, response status, and elapsed time. Correlation data established earlier can connect that request entry to service activity produced during the same call.

Servlet filters are well suited to this because they can run before and after the remaining request chain. Spring’s `OncePerRequestFilter` provides a base class for code that should run a single time during a request dispatch, with controls for asynchronous and error dispatches when an application needs them.

```markup
package com.example.orders.logging;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class RequestLoggingFilter extends OncePerRequestFilter {

    private static final Logger log =
            LoggerFactory.getLogger(RequestLoggingFilter.class);

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        long startedAt = System.nanoTime();

        try {
            filterChain.doFilter(request, response);
        } finally {
            long durationMs = TimeUnit.NANOSECONDS.toMillis(
                    System.nanoTime() - startedAt);

            log.atInfo()
                    .addKeyValue("httpMethod", request.getMethod())
                    .addKeyValue("requestUri", request.getRequestURI())
                    .addKeyValue("status", response.getStatus())
                    .addKeyValue("durationMs", durationMs)
                    .log("HTTP request completed");
        }
    }
}
```

We capture the starting point with `System.nanoTime()` before passing control farther down the filter chain. After processing returns, the `finally` block calculates elapsed time and records the method, URI, current response status, and duration. `System.nanoTime()` is appropriate for elapsed-time measurement because it is monotonic and does not depend on wall-clock changes.

Calling `getRequestURI()` gives us the request URI without automatically adding the query string. That makes it a safer default for a general request event because query parameters can contain account values, search input, temporary credentials, or other data that should not become routine production output.

The response status provides valuable context when a request succeeds or Spring MVC finishes an error response before control returns through the filter. Cases where an exception escapes far enough for the servlet container to perform a later error dispatch need extra attention because the final status can be assigned after the original dispatch has finished. `OncePerRequestFilter` has dedicated behavior for `ERROR` and `ASYNC` dispatches, so applications that depend heavily on those flows should decide which dispatch is responsible for recording the request entry.

Elapsed time needs the right interpretation as well. The timer above measures the period spent inside the remaining filter chain for that dispatch. It gives us a practical server-side duration for the request processing covered by the filter, rather than the full amount of time experienced by the client outside the server.

Recording every successful request at `INFO` can create a large amount of output for busy services. Traffic volume, storage cost, retention policy, metrics, and tracing all affect how much request logging belongs in production. Whatever volume is selected, the request entry should remain compact enough that developers can scan and filter it without carrying entire headers or bodies into every event.

Health checks can create a lot of unnecessary log traffic because infrastructure may call them every few seconds. Those requests can dominate the log stream while contributing very little diagnostic value. Applications can exclude those routes from routine request entries, assign them a lower logging level, or leave that traffic to server access logging depending on how the deployment is operated.

#### Log Exceptions at the Right Boundary

Exception entries should preserve the throwable and carry enough business context to identify the failed operation. Recording only `ex.getMessage()` throws away the stack trace, which can remove the class and call location that led to the failure.

The following logging call records the order identifier and exception message but does not pass the throwable itself:

```markup
log.error("Payment capture failed for order {}: {}", orderId, ex.getMessage());
```

We can still read the failure message, but the logger never receives the original exception. If that message only reports a connection failure or invalid value, much of the diagnostic information needed to trace the source is gone.

Passing the throwable retains its type and stack trace:

```markup
log.error("Payment capture failed for order {}", orderId, ex);
```

We still record the order identifier so the event has business context, while SLF4J receives `ex` as the throwable associated with the event. The logging backend can then retain the stack trace rather than reducing the failure to its message text.

Structured logging can carry the same failure while keeping business values as named fields:

```markup
log.atError()
        .addKeyValue("orderId", orderId)
        .addKeyValue("paymentProvider", paymentProvider)
        .setCause(ex)
        .log("Payment capture failed");
```

We attach the order identifier and payment provider first, then pass the original exception through `setCause`. The resulting event keeps searchable business context beside the throwable, so developers can filter by the affected order or provider and still inspect the complete failure chain.

The layer that handles a failure should usually be the place where its stack trace is recorded. Repeating the same exception in a repository, service, controller, and exception handler can produce several copies of the same stack trace while adding little diagnostic value. If a lower layer catches an exception only to translate it into an application-specific exception and pass it upward, recording both failures can create duplicate entries for the same incident.

Context helps determine the best location. Database code may have details about the failed database operation, while the service layer may know which order or payment operation was in progress. If the service catches the lower-level exception and turns it into the final application failure, that layer can record the event with the business identifiers needed during investigation. If the exception continues to a centralized handler that owns the final response, the handler can record it there instead.

Expected client outcomes deserve different severity from unexpected server failures. Missing resources, validation failures, rejected state changes, and invalid input do not automatically require an `ERROR` stack trace. Treating routine client mistakes as server errors can distort failure counts and fill production logs with stack traces that do not represent a failed server operation.

Dependency outages, unexpected database failures, invalid internal state, and uncaught defects are stronger candidates for `ERROR` with the throwable attached. Those entries should carry enough context to identify the failed operation without repeating the same stack trace farther up the call chain.

Exception messages can also expose more information than expected because third-party libraries can include request values, SQL details, remote response content, or other data in the exception text. Preserving the throwable remains valuable for diagnosis, but developers should be familiar with the exceptions produced by important dependencies so production logs do not unexpectedly retain sensitive information.

### Conclusion

With structured JSON, named fields, correlation IDs, package-specific levels, compact request records, and exception logging at the right boundary, Spring Boot logs can carry enough context to trace a request without flooding production output. These mechanics make events searchable, connect related activity, control diagnostic detail, and preserve the failure that ended an operation. Kept consistent across the application, they give developers a faster way to move from a reported problem to the log entries that explain what happened.

![](https://substackcdn.com/image/fetch/$s_!knjz!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F61d035cb-0a75-4403-8d4e-300440616183_276x276.png)

Spring Boot icon by Icons8
