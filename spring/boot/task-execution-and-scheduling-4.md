---
title: "Task Execution and Scheduling — Spring Boot Auto-configuration"
source: "https://docs.spring.io/spring-boot/reference/features/task-execution-and-scheduling.html"
author:
published:
created: 2026-08-07
description: "Notes on Spring Boot's auto-configuration for task execution and scheduling: the auto-configured `AsyncTaskExecutor` and the `applicationTaskExecutor` bean that MVC, WebFlux, GraphQL, WebSocket, and JPA consume, how a custom `Executor` bean causes back-off and how `spring.task.execution.mode=force` and non-default candidates override that, the `ThreadPoolTaskExecutorBuilder`/`SimpleAsyncTaskExecutorBuilder` builders and the `AsyncConfigurer` route, the `spring.task.execution.*` and `spring.task.scheduling.*` properties, and the virtual-thread variants selected by `spring.threads.virtual.enabled`."
status: in-progress
tags:
  - "note"
  - "spring"
  - "spring-boot"
  - "concurrency"
  - "kotlin"
---
# Task Execution and Scheduling 4

> [!NOTE] Series: Task Execution and Scheduling
> [[task-execution-and-scheduling-1|Part 1 — TaskExecutor Abstraction]] · [[task-execution-and-scheduling-2|Part 2 — TaskScheduler Abstraction]] · [[task-execution-and-scheduling-3|Part 3 — Annotation Support]] · **Part 4 — Spring Boot Auto-configuration**

## What Boot Auto-Configures

In the absence of an `Executor` bean in the context, Spring Boot auto-configures an `AsyncTaskExecutor`.
- When virtual threads are enabled, `SimpleAsyncTaskExecutor` that uses virtual threads
- Otherwise, it will be a `ThreadPoolTaskExecutor` with sensible defaults.

## How Each Integration Finds Its Executor

The auto-configured `AsyncTaskExecutor` is used for the following unless a custom `Executor` bean is defined:

- Executions for asynchronous tasks using `@EnableAsync`, unless a bean of type `AsyncConfigurer` is defined.
- Asynchronous handling of `Callable` return values from controller methods in Spring for GraphQL.
- Asynchronous request handling in Spring MVC.
- Support for blocking execution in Spring WebFlux.
- Utilized for inbound and outbound message channels in Spring WebSocket.
- Bootstrap executor for JPA, based on bootstrap mode of JPA repositories.
- Bootstrap executor for background initialization of beans in the `ApplicationContext`.

## When Auto-Configuration Backs Off

By default, when a custom `Executor` bean is registered, the auto-configured `AsyncTaskExecutor` backs off, and the custom `Executor` is used for regular task execution (via `@EnableAsync`).

However, Spring MVC, Spring WebFlux, and Spring GraphQL all require a bean named `applicationTaskExecutor`.  For Spring MVC and Spring WebFlux, this bean must be of type `AsyncTaskExecutor`, whereas Spring GraphQL does not enforce this type requirement.

Spring WebSocket and JPA will use `AsyncTaskExecutor`

## Override Strategies

The following demonstrates how to register a custom `AsyncTaskExecutor` to be used

```kotlin
@Configuration(proxyBeanMethods = false)
class MyTaskExecutorConfiguration {
	@Bean("applicationTaskExecutor")
	fun applicationTaskExecutor(): SimpleAsyncTaskExecutor {
		return SimpleAsyncTaskExecutor("app-")
	}
}
```

### Name It `applicationTaskExecutor`

### Split `applicationTaskExecutor` and `taskExecutor`

If your application needs multiple `Executor` beans for different integrations, such as one for regular task execution

### Redirect `@Async` with `@Primary` or `AsyncConfigurer`

### Opt Out with `defaultCandidate = false`

### Force with `spring.task.execution.mode`

## Tuning the Thread Pool

When a `ThreadPoolTaskExecutor` is auto-configured, the thread pool uses 8 core threads that can grow and shrink according to the load. Those default settings can be fine-tuned using the `spring.task.execution` namespace.

```yaml
spring:
	task:
		execution:
			pool:
				max-size: 16
				queue-capacity: 100
				keep-alive: "10s"
```

## Scheduler Auto-Configuration

A scheduler can also be auto-configured if it needs to be associated with scheduled task execution (using `@EnableScheduling` for instance).

- If virtual threads are enabled: `SimpleAsyncTaskScheduler` that uses virtual threads. Ignores any pooling related properties.
- If virtual threads are not enabled: `ThreadPoolTaskScheduler` with sensible defaults.
	- `ThreadPoolTaskScheduler` uses one thread by default and its settings can be fine-tuned using the `spring.task.scheduling` namespace:

```yaml
spring:
	task:
		scheduling:
			thread-name-prefix: "scheduling-"
			pool:
				size: 2
```

## Executor and Scheduler Builders
