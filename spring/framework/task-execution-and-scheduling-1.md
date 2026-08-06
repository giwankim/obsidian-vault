---
title: "Task Execution and Scheduling — `TaskExecutor` Abstraction"
source: "https://docs.spring.io/spring-framework/reference/integration/scheduling.html"
author:
published:
created: 2026-08-06
description: "Notes on Spring's `TaskExecutor` abstraction: the five built-in implementations and when each applies, wiring `ThreadPoolTaskExecutor` through dependency injection with pool/queue bean properties, and wrapping submitted tasks with `TaskDecorator` (and `CompositeTaskDecorator` for several)."
tags:
  - "note"
  - "spring"
  - "concurrency"
  - "kotlin"
---
# Task Execution and Scheduling 1

Spring Framework provides abstractions for the asynchronous execution and scheduling of tasks with the `TaskExecutor` and `TaskScheduler` interfaces, respectively.

## `TaskExecutor` Abstraction

Executor is the JDK name for the concept of thread pools.

Spring's `TaskExecutor` interface is identical to the `java.util.concurrent.Executor` interface. The interface has a single method (`execute(Runnable task)`) that accepts a task for execution.

### `TaskExecutor` Types

Spring includes a number of pre-built implementations of `TaskExecutor`.

- `SyncTaskExecutor`:
	- Not asynchronous.
	- Each invocation takes place in the calling thread.
- `SimpleAsyncTaskExecutor`:
	- Does not reuse any threads.
	- Starts up a new thread for each invocation.
	- Supports a concurrency limit.
	- Uses virtual threads when the "virtualThreads" option is enabled.
	- Supports graceful shutdown through Spring's lifecycle management.
- `ConcurrentTaskExecutor`
	- Adapter for a `java.util.concurrent.Executor` instance.
	- There is an alternative (`ThreadPoolTaskExecutor`) that exposes the `Executor` configuration parameters as bean properties.
	- Rarely a need to use `ConcurrentTaskExecutor` directly.
- `ThreadPoolTaskExecutor`
	- Most commonly used.
	- Exposes bean properties for configuring a `java.util.concurrent.ThreadPoolExecutor` and wraps it in a `TaskExecutor`.
	- If you need to adapt to a different kind of `java.util.concurrent.Executor`, we recommend that you use a `ConcurrentTaskExecutor` instead.
	- Provides a pause/resume capability and graceful shutdown through Spring's lifecycle management.
- `DefaultManagedTaskExecutor`: Uses a JNDI-obtained `ManagedExecutorService` in a JSR-236 compatible runtime environment.

### Using a `TaskExecutor`

Spring's `TaskExecutor` implementations are commonly used with dependency injection.

```kotlin
class TaskExecutorExample(private val taskExecutor: TaskExecutor) {
	private inner class MessagePrinterTask(private val message: String) : Runnable {
		override fun run() {
			println(message)
		}
	}

	fun printMessages() {
		for (i in 0..24) {
			taskExecutor.execute(
				MessagePrinterTask("Message$i")
			)
		}
	}
}
```

Rather than retrieving a thread from the pool and executing it yourself, you add your `Runnable` to the queue. Then the `TaskExecutor` uses its internal rules to decide when the task gets run.

To configure the rules that the `TaskExecutor` uses, we expose simple bean properties:

```kotlin
@Bean
fun taskExecutor() : ThreadPoolTaskExecutor {
	return ThreadPoolTaskExecutor().apply {
		corePoolSize = 5
		maxPoolSize = 10
		queueCapacity = 25
	}
}

@Bean
fun taskExecutorExample(taskExecutor: ThreadPoolTaskExecutor) : TaskExecutorExample {
	return TaskExecutorExample(taskExecutor)
}
```

Most `TaskExecutor` implementations provide a way to automatically wrap tasks submitted with a `TaskDecorator`. Decorators should delegate to the task they are wrapping, possibly implementing custom behavior before/after the execution of the task.

```kotlin
class LoggingTaskDecorator : TaskDecorator {
	override fun decorate(runnable: Runnable): Runnable {
		return Runnable {
			logger.debug("Before execution of $runnable")
			runnable.run()
			logger.debug("After execution of $runnable")
		}
	}

	companion object {
		private val logger: Log = LogFactory.getLog(LoggingTaskDecorator::class.java)
	}
}
```

Then configure our decorator on a `TaskExecutor` instance:

```kotlin
@Bean
fun decoratedTaskExecutor(): ThreadPoolTaskExecutor {
	return ThreadPoolTaskExecutor().apply {
		setTaskDecorator(LoggingTaskDecorator())
	}
}
```

In case multiple decorators are needed, the `org.springframework.core.task.support.CompositeTaskDecorator` can be used to execute multiple decorators sequentially.
