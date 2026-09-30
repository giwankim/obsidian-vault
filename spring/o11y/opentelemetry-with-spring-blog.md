---
title: OpenTelemetry with Spring Blog
source: https://spring.io/blog/2025/11/18/opentelemetry-with-spring-boot
author:
published:
created: 2026-07-20
description: Level up your Java code and explore what Spring can do for you.
tags:
  - clippings
---

> [!summary]
> Spring team blog post introducing the new `spring-boot-starter-opentelemetry` in Spring Boot 4.0, comparing it against the OpenTelemetry Java Agent and the third-party OTel starter. It walks through exporting metrics, traces, and logs via OTLP using Micrometer, including Logback appender setup and OpenTelemetry semantic convention beans. It also covers trace context propagation across threads (`ContextPropagatingTaskDecorator`) and across services (W3C trace context via auto-configured client builders), demonstrated with a three-service sample using the Grafana LGTM stack.

## OpenTelemetry with Spring Boot

This is a new blog post in the [Road to GA series](https://spring.io/blog/2025/09/02/road_to_ga_introduction), and this time we're taking a look at OpenTelemetry with Spring Boot.

## Introduction

In modern cloud native architectures, observability is no longer optional; it is a fundamental requirement. You want to understand what your application is doing via metrics, how requests are flowing through it via traces, and what it is saying via logs.

The [OpenTelemetry project](https://opentelemetry.io/), sometimes abbreviated as OTel, provides a vendor-neutral, open-source framework to collect, process, and export telemetry data. Backed by the [Cloud Native Computing Foundation](https://www.cncf.io/), it offers an API, an SDK, a standard wire protocol called OTLP for exporting data, and a pluggable architecture (including the OpenTelemetry Collector) for handling ingestion, processing, and export to backends.

Instrumented projects and libraries use the API to emit observability data. The SDK, which implements that API, is used to configure how data is collected and exported. The collector is an optional component that can help to aggregate and filter data, but you can also send the data directly to any capable backend.

The Spring ecosystem has strong observability support via [Micrometer](https://micrometer.io/), and combining Spring Boot with OpenTelemetry is a powerful way to cover all observability signals (metrics, traces, and logs). The key enabler here is the OTLP protocol rather than a specific library.

In this post, we'll walk through what OpenTelemetry means and see how you can integrate with Spring Boot to cover the observability story perfectly.

## Using OpenTelemetry with Spring Boot

When you choose to integrate OpenTelemetry with Spring Boot, there are a few alternative paths, from "just drop in a runtime agent" to "use built-in Spring support". You have three options:

### Use the OpenTelemetry Java Agent

[Getting started](https://opentelemetry.io/docs/zero-code/java/agent/getting-started/) is simple: You attach the `opentelemetry-javaagent.jar` via the `-javaagent` flag at startup. This agent does bytecode-instrumentation for libraries (HTTP, JDBC, Spring, etc.). This is the easiest "zero code change" path. The agent figures out traces, spans (a span is the atomic part of a trace), metrics, etc.

The main problem with that approach is that the Java agent has to closely match your library versions because the agent modifies their bytecode. If there's a mismatch between the versions the agent has been tested with and the versions you use, issues can be hard to diagnose. Also, if you're using GraalVM's native-image or want to use Java's AOT cache, you have to jump through additional hoops. Additionally, if you're already using an agent, they may conflict.

### Use the 3rd-party OpenTelemetry Spring Boot Starter

OpenTelemetry has its own Spring Boot starter, which [instruments some technologies](https://opentelemetry.io/docs/zero-code/java/spring-boot-starter/out-of-the-box-instrumentation/). However, [they note](https://opentelemetry.io/docs/zero-code/java/spring-boot-starter/) that the OpenTelemetry Java Agent is their default choice of instrumenting and that the starter should only be used if the agent can't be used. Also, while [the starter itself is marked as stable](https://opentelemetry.io/blog/2024/spring-starter-stable/), it pulls in dependencies with an alpha suffix.

### Use the OpenTelemetry Spring Boot Starter from the Spring team

With Spring Boot 4.0, we're introducing a new Spring Boot Starter for OpenTelemetry. It is called `spring-boot-starter-opentelemetry` (we're really clever with those names, aren't we) and is selectable via the "OpenTelemetry" dependency on [start.spring.io](https://start.spring.io/).

We may be biased, but this is our favorite option to get observability in a Spring Boot application.

The starter includes the OpenTelemetry API and components to export Micrometer signals via OTLP. Micrometer Tracing with the OpenTelemetry bridge uses the OpenTelemetry API to export traces in OTLP format. The Micrometer [OtlpMeterRegistry](https://docs.micrometer.io/micrometer/reference/implementations/otlp.html) is used to send metrics collected via the Micrometer API to your OpenTelemetry-capable metrics backend via the OTLP protocol.

To reiterate: It's the protocol that matters, not the library used. Even though the Spring portfolio projects use Micrometer as their observability API, it is perfectly possible to export the signals via OTLP to any OpenTelemetry-capable backend, as you'll see soon.

Spring Boot also supports sending logs via OTLP to an OpenTelemetry-capable backend, but it doesn't install log appenders into Logback and Log4j2 out of the box. This may change in the future, but even right now, it's not hard to do, and we're walking through the setup in this blog post, too.

The rest of this blog post will focus on how to get a seamless OpenTelemetry experience in your Spring Boot application using the new Spring Boot Starter for OpenTelemetry from the Spring team.

## Exporting metrics

As hinted earlier, Spring Boot uses the Micrometer OTLP registry to export Micrometer metrics via OTLP to any OpenTelemetry-capable backend. The required dependency, `io.micrometer:micrometer-registry-otlp`, is already included in the `spring-boot-starter-opentelemetry`. With that dependency in place, Micrometer exports metrics in OTLP format to the backend at `http://localhost:4318/v1/metrics`. To customize the location to which metrics are exported, set the `management.otlp.metrics.export.url` property,.e.g.:

```markdown
management.otlp.metrics.export.url=http://otlp.example.com:4318/v1/metrics
```

The Micrometer team has also added so-called observation conventions for OpenTelemetry. Signals in OpenTelemetry adhere to the [OpenTelemetry Semantic Convention](https://opentelemetry.io/docs/concepts/semantic-conventions/), and the observation conventions in Micrometer implement the stable parts of the OpenTelemetry Semantic Convention. To use them in Spring Boot, you have to define some configuration (this will [likely be improved in the future](https://github.com/spring-projects/spring-boot/pull/47935)):

```java
@Configuration(proxyBeanMethods = false)
public class OpenTelemetryConfiguration {

    @Bean
    OpenTelemetryServerRequestObservationConvention openTelemetryServerRequestObservationConvention() {
        return new OpenTelemetryServerRequestObservationConvention();
    }

    @Bean
    OpenTelemetryJvmCpuMeterConventions openTelemetryJvmCpuMeterConventions() {
        return new OpenTelemetryJvmCpuMeterConventions(Tags.empty());
    }

    @Bean
    ProcessorMetrics processorMetrics() {
        return new ProcessorMetrics(List.of(), new OpenTelemetryJvmCpuMeterConventions(Tags.empty()));
    }

    @Bean
    JvmMemoryMetrics jvmMemoryMetrics() {
        return new JvmMemoryMetrics(List.of(), new OpenTelemetryJvmMemoryMeterConventions(Tags.empty()));
    }

    @Bean
    JvmThreadMetrics jvmThreadMetrics() {
        return new JvmThreadMetrics(List.of(), new OpenTelemetryJvmThreadMeterConventions(Tags.empty()));
    }

    @Bean
    ClassLoaderMetrics classLoaderMetrics() {
        return new ClassLoaderMetrics(new OpenTelemetryJvmClassLoadingMeterConventions());
    }

}
```

Spring Boot doesn't auto-configure the OpenTelemetry API for metrics. If you really want to use the OpenTelemetry metrics API (which we don't recommend) instead of the Micrometer API, or if you have a library that uses the OpenTelemetry metrics API, please take a look at [the Spring Boot documentation](https://docs.spring.io/spring-boot/4.0-SNAPSHOT/reference/actuator/observability.html#actuator.observability.opentelemetry.metrics.api-and-sdk) on how to get that working.

## Exporting traces

The Spring projects use the Micrometer Observation API to create observations. An observation is an interesting concept in Micrometer because it can be translated into a metric **and** a trace.

The traces generated by the observations are then adapted through the `io.micrometer:micrometer-tracing-bridge-otel` dependency (which is also included in the `spring-boot-starter-opentelemetry`) to the OpenTelemetry API.

Spring Boot contains auto-configuration for the OpenTelemetry SDK. For traces, it installs an `OtlpHttpSpanExporter` (or `OtlpGrpcSpanExporter` if you prefer gRPC to HTTP). With this exporter in place, the OpenTelemetry SDK now starts sending traces (which originate from a Micrometer Observation) in the OTLP format to your backend.

To enable it in your application, you have to set the `management.opentelemetry.tracing.export.otlp.endpoint` property, e.g.:

```markdown
management.opentelemetry.tracing.export.otlp.endpoint=http://localhost:4318/v1/traces
```

## Exporting logs

As said earlier, Spring Boot contains auto-configuration that configures the OpenTelemetry SDK with the ability to export logs in OTLP format. However, it does not install an appender into Logback or Log4j2, so while the underlying infrastructure is there, no logs are actually exported. To export logs in OTLP format, you have to do two things:

First, set the property `management.opentelemetry.logging.export.otlp.endpoint`, e.g.:

```markdown
management.opentelemetry.logging.export.otlp.endpoint=http://localhost:4318/v1/logs
```

And second, install an appender in Logback or Log4j2 that sends the log entries to the OpenTelemetry API.

For Logback, we first need to include the `io.opentelemetry.instrumentation:opentelemetry-logback-appender-1.0:2.21.0-alpha` dependency (`-alpha` in the version number means that it is marked as unstable; unfortunately, there are no non-alpha versions for the appender. [You can read more about that here](https://github.com/open-telemetry/opentelemetry-java-instrumentation/blob/main/VERSIONING.md#stable-vs-alpha)).

Then we have to create a custom logback configuration, which lives in the `src/main/resources/logback-spring.xml` file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <include resource="org/springframework/boot/logging/logback/base.xml"/>

    <appender name="OTEL" class="io.opentelemetry.instrumentation.logback.appender.v1_0.OpenTelemetryAppender">
    </appender>

    <root level="INFO">
        <appender-ref ref="CONSOLE"/>
        <appender-ref ref="OTEL"/>
    </root>
</configuration>
```

This configuration imports the base configuration for Logback from Spring Boot, and then defines an additional appender called `OTEL`, which sends all log events to the OpenTelemetry API. This appender is then added to the root logger, effectively sending all log entries to the OpenTelemetry API in addition to the console.

The last thing to do is to let the `OpenTelemetryAppender` know which OpenTelemetry API instance to use. For this, we can create a small bean that gets the `OpenTelemetry` instance injected:

```java
@Component
class InstallOpenTelemetryAppender implements InitializingBean {

    private final OpenTelemetry openTelemetry;

    InstallOpenTelemetryAppender(OpenTelemetry openTelemetry) {
        this.openTelemetry = openTelemetry;
    }

    @Override
    public void afterPropertiesSet() {
        OpenTelemetryAppender.install(this.openTelemetry);
    }

}
```

## Beware the context

Logging, metrics, and tracing use contextual information, like the current trace ID. By default, when Micrometer Tracing is on the classpath, Spring Boot adjusts the log pattern to also include the trace ID and the span ID in the log message. This can be very useful if you're trying to find the logs belonging to a trace.

One useful pattern is to include the trace ID of the request in the response from the server, e.g., via an HTTP header. This way, if users get an error response from your HTTP endpoint, they can include the trace ID in the ticket, and you can use this trace ID to get all the logs belonging to exactly this erroneous request.

Putting the trace ID in a header can be achieved with this Servlet filter:

```java
@Component
class TraceIdFilter extends OncePerRequestFilter {

    private final Tracer tracer;

    TraceIdFilter(Tracer tracer) {
        this.tracer = tracer;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        String traceId = getTraceId();
        if (traceId != null) {
            response.setHeader("X-Trace-Id", traceId);
        }
        filterChain.doFilter(request, response);
    }

    private @Nullable String getTraceId() {
        TraceContext context = this.tracer.currentTraceContext().context();
        return context != null ? context.traceId() : null;
    }

}
```

One thing you'll note if you're dealing with methods that switch threads, e.g., `@Async` annotated methods or the use of Spring's `AsyncTaskExecutor`, is that the context is lost in the new thread. The lost context affects logs, which don't include the trace ID anymore, and traces, which lose spans.

The context is lost because it is stored inside a `ThreadLocal`, which doesn't get transferred into the new thread. However, the solution is quite simple: Use the `ContextPropagatingTaskDecorator` in the `AsyncTaskExecutor` (which is also used for `@Async` annotated methods). The `ContextPropagatingTaskDecorator` uses Micrometer's Context Propagation API to make sure that the trace context is transferred to new threads. Installing the `ContextPropagatingTaskDecorator` is simple: just define a `@Bean` method, as shown in the following code snippet:

```java
@Configuration(proxyBeanMethods = false)
public class ContextPropagationConfiguration {

    @Bean
    ContextPropagatingTaskDecorator contextPropagatingTaskDecorator() {
        return new ContextPropagatingTaskDecorator();
    }

}
```

Spring Boot's auto-configuration looks for `TaskDecorator` beans and installs them into the `AsyncTaskExecutor`. With the `ContextPropagatingTaskDecorator` in place, the context is now transferred to new threads, fixing lost trace IDs in logs and lost spans. The whole setup with the `ContextPropagatingTaskDecorator` will [likely be improved in the future](https://github.com/spring-projects/spring-boot/issues/48033) for a more seamless experience.

## Context propagation, again

If you're dealing with multiple services, wouldn't it be nice if the trace ID were the same over all services so that you can look at one trace and see all involved services? Or find logs from all services participating in that trace? That's where the "distributed" in distributed tracing is coming from.

Now, have you ever wondered how the called service knows that it is part of an ongoing trace? This is context propagation again, but this time the context is not propagated over threads but over process boundaries.

There's a [W3C recommendation](https://www.w3.org/TR/trace-context/) for context propagation over HTTP, and Spring Boot configures all involved components to use this out of the box. The sending party has to add the current trace ID into a header, and the receiving party has to extract the trace ID from the header and restore the context.

This all works seamlessly, as long as you follow one simple rule: you do not talk about Fight Club. Oh, sorry, wrong script. The one rule you must follow is: Do not `new` up a `RestTemplate` / `RestClient` / `WebClient` yourself. Instead, inject a `RestTemplateBuilder` / `RestClient.Builder` / `WebClient.Builder` and use that to create the client.

Spring Boot auto-configures the builders with all the needed infrastructure to automatically send the trace context in a header. If you create a client with `new` yourself, this infrastructure is not there, and the context is not propagated, leading to sad on-call team members and red tiles in sprint retros.

## Let's see it in action

We've prepared [a sample project](https://github.com/mhalbritter/spring-boot-and-opentelemetry) that you can use to play around with OpenTelemetry observability. It consists of three services:

The user service uses an in-memory H2 database and Spring Data JDBC to look up users by user ID. It exposes an HTTP API to find a user by the given user ID.

The greeting service has an HTTP API that returns a greeting in a language specified by the `Accept-Language` header. It knows greetings in English, German, and Spanish.

The hello service is the entry point. It has an HTTP API that takes a user ID and returns a greeting for that user. To do that, it calls the user service with the user ID to get the user's name. It also calls the greeting service to get the greeting. It then combines the user's name with the greeting and returns it.

First, let's start all three services. The setup also includes the `spring-boot-docker-compose` module, which automatically detects the Docker Compose configuration file named `compose.yaml` and calls `docker compose up`. The `compose.yaml` file contains one service using the `grafana/otel-lgtm` image. The [Grafana LGTM stack](https://grafana.com/docs/opentelemetry/docker-lgtm/) contains OTLP-capable logs, metrics, and traces backends, all packaged together in one UI, which we can use to look at the observability signals.

After the Docker container is up and running, Spring Boot automatically configures the exporters for logs, metrics, and traces to point to the Docker container. That's why we don't find the OTLP export properties mentioned sooner in the `application.properties`; it's all happening behind the scenes. When you deploy it to production, you have to set the properties yourself. If you want to read more about that developer experience feature, please [read this blog post](https://spring.io/blog/2023/06/21/docker-compose-support-in-spring-boot-3-1).

Now let's execute our first request:

```yml
> curl -i http://localhost:8080/api/1
HTTP/1.1 200
X-Trace-Id: 0dbe0809731e35081d6db16c2ca0ef91
Content-Type: application/json
Content-Length: 12

Hello Moritz
```

Cool, that worked. Now let's try it in German:

```yml
> curl -i http://localhost:8080/api/1 --header "Accept-Language: de"
HTTP/1.1 200
X-Trace-Id: 6c0753c7ec390fff15fcf05f536e21cd
Content-Type: application/json
Content-Length: 12

Hallo Moritz
```

Nice, we now have two trace IDs to play around with. Notice how the trace IDs for the requests are included in the `X-Trace-Id` header, using the Servlet filter from above.

Let's look into the Grafana UI if we have some logs (*you can click the images to enlarge them*):

[![A screenshot of Grafana, showing logs from all three services](https://static.spring.io/blog/mhalbritter/20251118/1-logs.jpg "Logs for all three services")](https://static.spring.io/blog/mhalbritter/20251118/1-logs.jpg)

Here, we can see that the logs have been sent via OTLP to Grafana, and we're now able to view all logs from the three services in one UI. It is also possible to find the logs from all services for a trace ID.

[![A screenshot of Grafana, showing logs from all three services for a given trace id](https://static.spring.io/blog/mhalbritter/20251118/2-logs-by-trace-id.jpg "Logs from all three services for a given trace id")](https://static.spring.io/blog/mhalbritter/20251118/2-logs-by-trace-id.jpg)

Now let's look if we can find the trace for the trace ID.

[![A screenshot of Grafana, showing the trace details](https://static.spring.io/blog/mhalbritter/20251118/3-trace.jpg "Trace details")](https://static.spring.io/blog/mhalbritter/20251118/3-trace.jpg)

Found it! Here we can see that the hello service calls the greeting service and the user service in a nice waterfall diagram. You can also expand a span to see the span attributes:

[![A screenshot of Grafana, showing a span with the en-US locale](https://static.spring.io/blog/mhalbritter/20251118/4-span-en-us.jpg "Span showing the en-US locale")](https://static.spring.io/blog/mhalbritter/20251118/4-span-en-us.jpg)

In this case, we've used Micrometer's `@SpanTag` to attach the greeting locale (`en_US`) and the user ID (`1`) to the span. Let's look at the second trace, which should have the German locale in there:

[![A screenshot of Grafana, showing a span with the de locale](https://static.spring.io/blog/mhalbritter/20251118/5-span-de.jpg "Span showing the de locale")](https://static.spring.io/blog/mhalbritter/20251118/5-span-de.jpg)

Very good, works as expected.

Last stop, let's look at the metrics generated by the services:

[![A screenshot of Grafana, showing the custom say-hello metric](https://static.spring.io/blog/mhalbritter/20251118/6-custom-metrics.jpg "The say-hello custom metric")](https://static.spring.io/blog/mhalbritter/20251118/6-custom-metrics.jpg)

Here you can see a custom metric, called `say-hello` (created by annotating a method with `@Observed(name = "say-hello")`), which counts how many times a hello message has been generated.

You also get a lot of metrics about your application out of the box, such as the number of threads in executors, your HTTP server, etc.

[![A screenshot of Grafana, showing a part of the thread metrics](https://static.spring.io/blog/mhalbritter/20251118/7-thread-metrics.jpg "Some of the thread metrics")](https://static.spring.io/blog/mhalbritter/20251118/7-thread-metrics.jpg)

Or a lot of JVM metrics:

[![A screenshot of Grafana, showing a part of the JVM metrics](https://static.spring.io/blog/mhalbritter/20251118/8-jvm-metrics.jpg "Some of the JVM metrics")](https://static.spring.io/blog/mhalbritter/20251118/8-jvm-metrics.jpg)

## Conclusion

We hope you had fun during this whirlwind tour through OpenTelemetry with Spring Boot. As you saw, Spring Boot has nice integrations with OpenTelemetry. Whether you use Micrometer's Observation API or not, this doesn't really matter from the OTel integration perspective. It's the protocol, OTLP, that matters and abstracts away the API that has been used to instrument the application.

Spring Boot 4.0 with the new OpenTelemetry starter will be released on November 20th. [Micrometer 1.16](https://github.com/micrometer-metrics/micrometer/releases/tag/v1.16.0), with OpenTelemetry enhancements and lots of other new features, has already been released. If you find any issues or have great ideas on how to improve the whole OpenTelemetry story, please reach out to us in [our issue tracker](https://github.com/spring-projects/spring-boot/issues)!

![](https://spring.io/img/extra/footer.svg)

## Get ahead

VMware offers training and certification to turbo-charge your progress.

[Learn more](https://spring.academy/)

## Get support

Tanzu Spring offers support and binaries for OpenJDK™, Spring, and Apache Tomcat® in one simple subscription.

[Learn more](https://spring.io/support)

## Upcoming events

Check out all the upcoming events in the Spring community.

[View all](https://spring.io/events)
