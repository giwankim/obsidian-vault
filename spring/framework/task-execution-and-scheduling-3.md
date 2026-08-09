---
title: "Task Execution and Scheduling — Annotation Support"
source: "https://docs.spring.io/spring-framework/reference/integration/scheduling.html"
author:
published:
created: 2026-08-06
description: "Notes on Spring's annotation support for scheduling and asynchronous execution: switching it on with `@EnableScheduling` and `@EnableAsync`, the `@Scheduled` trigger attributes (`fixedDelay`, `fixedRate`, `initialDelay`, and `cron`) and the constraints on scheduled methods, and `@Async` for asynchronous invocation — covering `Future`-typed return values, qualifying a non-default executor, and handling uncaught exceptions with `AsyncUncaughtExceptionHandler`."
tags:
  - "note"
  - "spring"
  - "concurrency"
  - "kotlin"
---
# Task Execution and Scheduling 3

> [!NOTE] Series: Task Execution and Scheduling
> [[task-execution-and-scheduling-1|Part 1 — TaskExecutor Abstraction]] · [[task-execution-and-scheduling-2|Part 2 — TaskScheduler Abstraction]] · **Part 3 — Annotation Support** · [[task-execution-and-scheduling-4|Part 4 — Spring Boot Auto-configuration]]

## Annotation Support for Scheduling and Asynchronous Execution

Spring provides annotation support for both task scheduling and asynchronous method execution.

### Enable Scheduling Annotations

To enable support for `@Scheduled` and `@Async` annotations, add `@EnableScheduling` and `@EnableAsync` to one of your `@Configuration` classes, as the following example shows:

```kotlin
@Configuration
@EnableAsync
@EnableScheduling
class SchedulingConfiguration
```

For more fine-grained control, implement the `SchedulingConfigurer` interface, the `AsyncConfigurer` interface, or both.

### The `@Scheduled` Annotation

You can add the `@Scheduled` annotation to a method, along with trigger metadata. The following method is invoked every five seconds with a fixed delay, meaning that the period is measured from the completion time of each preceding invocation:

```kotlin
@Scheduled(fixedDelay = 5000)
fun doSomething() {
	// something that should run periodically
}
```

The following method is invoked every five seconds (measured between the successive start times of each invocation):

```kotlin
@Scheduled(fixedRate = 5, timeUnit = TimeUnit.SECONDS)
fun doSomething() {
	// something that should run periodically
}
```

For fixed-delay and fixed-rate tasks, you can specify an initial delay, indicating how long to wait before the first invocation of the method:

```kotlin
@Scheduled(initialDelay = 1000, fixedRate = 5000)
fun doSomething() {
	// something that should run periodically
}
```

For one-time tasks, you can just specify an initial delay:

```kotlin
@Scheduled(initialDelay = 1000)
fun doSomething() {
	// something that should run only once
}
```

The following example runs only on weekdays:

```kotlin
@Scheduled(cron = "*/5 * * * * MON-FRI")
fun doSomething() {
	// something that should run on weekdays only
}
```

Methods to be scheduled must have a void return type and must not accept any arguments. If the method interacts with other objects from the application context, those would typically have been provided through dependency injection.

`@Scheduled` can be used as a repeatable annotation. If several scheduled declarations are found on the same method, each of them will be processed independently, with a separate trigger firing for each of them.

### The `@Async` Annotation

You can provide the `@Async` annotation on a method so that invocation of the method occurs asynchronously. In the simplest case, you can apply the annotation to a method that returns `void`:

```kotlin
@Async
fun doSomething() {
	// this will be run asynchronously
}
```

Unlike the methods annotated with the `@Scheduled` annotation, these methods can expect arguments.

Even methods that return a value can be invoked asynchronously. However, such methods are required to have a `Future`-typed return value.

```kotlin
@Async
fun returnSomething(i: Int): Future<String> {
	// this will be run asynchronously
}
```

> [!TIP]
> `@Async` methods may not only declare a regular `java.util.concurrent.Future` return type but also `java.util.concurrent.CompletableFuture`, for richer interaction with the asynchronous task and for immediate composition with further processing steps.

### Executor Qualification with `@Async`

When specifying `@Async` on a method, the executor that is used is the one configured when enabling async support. However, you can use the `value` attribute of the `@Async` annotation to indicate that an executor other than the default should be used when executing a given method.

```kotlin
@Async("otherExecutor")
fun doSomething(s: String) {
	// this will be run asynchronously by "otherExecutor"
}
```

In this case, `"otherExecutor"` can be the name of any `Executor` bean in the Spring container, or the name of a qualifier associated with any `Executor`.

### Exception Management with `@Async`

When an `@Async` method has a `Future`-typed return value, you can manage an exception that was thrown during the method execution, as this exception is rethrown when calling `get` on the `Future` result.

With a `void` return type, however, the exception is uncaught and cannot be transmitted. You can provide an `AsyncUncaughtExceptionHandler` to handle such exceptions.

```kotlin
class MyAsyncUncaughtExceptionHandler : AsyncUncaughtExceptionHandler {
	override fun handleUncaughtException(
		ex: Throwable,
		method: Method,
		vararg params: Any?,
	) {
		// handle exception
	}
}
```

By default, the exception is merely logged. You can define a custom `AsyncUncaughtExceptionHandler` by using `AsyncConfigurer`.
