---
title: "Task Execution and Scheduling — `TaskScheduler` Abstraction"
source: "https://docs.spring.io/spring-framework/reference/integration/scheduling.html"
author:
published:
created: 2026-08-06
description: "Notes on Spring's `TaskScheduler` SPI: the scheduling method signatures, the `Trigger`/`TriggerContext` interfaces that let execution times depend on prior execution outcomes, the `CronTrigger` and `PeriodicTrigger` implementations, and the `TaskScheduler` implementations that decouple scheduling from the deployment environment."
tags:
  - "note"
  - "spring"
  - "concurrency"
  - "java"
  - "kotlin"
---
# Task Execution and Scheduling

## `TaskScheduler` Abstraction

Spring has a `TaskScheduler` SPI with a variety of methods for scheduling tasks to run at some point in the future.

```java
public interface TaskScheduler {
	Clock getClock();
	ScheduledFuture schedule(Runnable task, Trigger trigger);
	ScheduledFuture schedule(Runnable task, Instant startTime);
	ScheduledFuture scheduleAtFixedRate(Runnable task, Instant startTime, Duration period);
	ScheduledFuture scheduleAtFixedRate(Runnable task, Duration period);
	ScheduledFuture scheduleAtFixedDelay(Runnable task, Instant startTime, Duration delay);
	ScheduledFuture scheduleAtFixedDelay(Runnable task, Duration delay);
}
```

### `Trigger` Interface

Execution times may be determined based on past execution outcomes or even arbitrary conditions. If these determinations take into account the outcome of the preceding execution, that information is available within a `TriggerContext`.

```java
public interface Trigger {
	Instant nextExecution(TriggerContext triggerContext);
}
```

The `TriggerContext` encapsulates all of the relevant data and is open for extension in the future, if necessary. The `TriggerContext` is an interface (a `SimpleTriggerContext` implementation is used by default).

```java
public interface TriggerContext {
	Clock getClock();
	Instant lastScheduledExecution();
	Instant lastActualExecution();
	Instant lastCompletion();
}
```

### `Trigger` Implementations

Spring provides two implementations of the `Trigger` interface. `CronTrigger` enables the scheduling of tasks based on cron expressions. For example, the following task is scheduled to run 15 minutes past each hour but only during 9-to-5 "business hours" on weekdays:

```kotlin
scheduler.schedule(task, CronTrigger("0 15 9-17 * * MON-FRI"))
```

The other implementation is a `PeriodicTrigger` that accepts:
- a fixed period,
- an optional initial delay value,
- and a boolean to indicate whether the period should be interpreted as a fixed-rate or a fixed-delay.

Since the `TaskScheduler` interface already defines methods for scheduling tasks at a fixed rate or with a fixed delay, those methods should be used directly whenever possible. The value of the `PeriodicTrigger` implementation is that you can use it within components that rely on the `Trigger` abstraction.

### `TaskScheduler` Implementations

The primary benefit of the `TaskScheduler` arrangement is that an application's scheduling needs are decoupled from the deployment environment.

This abstraction level is particularly relevant when deploying to an application server environment where threads should not be created directly by the application itself. For such scenarios, Spring provides a `DefaultManagedTaskScheduler` that delegates to a JSR-236 `ManagedScheduledExecutorService` in a Jakarta EE environment.

Whenever external thread management is not a requirement, a simpler alternative is a local `ScheduledExecutorService` setup, which can be adapted through Spring's `ConcurrentTaskScheduler`. As a convenience, Spring also provides a `ThreadPoolTaskScheduler`, which internally delegates to a `ScheduledExecutorService` to provide common bean-style configuration.

As of 6.1, `ThreadPoolTaskScheduler` provides a pause/resume capability and graceful shutdown through Spring's lifecycle management. There is also a new option called `SimpleAsyncTaskScheduler`, which is aligned with JDK 21's Virtual Threads, using a single scheduler thread but firing up a new thread for every scheduled task execution (except for fixed-delay tasks, which all operate on a single scheduler thread).
