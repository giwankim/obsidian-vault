---
title: "ShedLock - Prevent Concurrent Execution of Scheduled Methods in Spring Boot"
source: "https://blog.rasc.ch/2025/07/shedlock.html"
author:
published:
created: 2026-07-17
description:
tags:
  - "clippings"
---

> [!summary]
> Demonstrates using ShedLock to prevent `@Scheduled` methods from running concurrently across multiple Spring Boot instances, with a demo app built on jOOQ, Flyway, and PostgreSQL using `JooqLockProvider`. Covers the mandatory `defaultLockAtMostFor` setting, using `lockAtLeastFor` to stop fixed-delay schedules from drifting into rapid re-execution, extending active locks with `LockExtender`, and catching misconfiguration with `LockAssert.assertLocked()`. Notes the `InMemoryLockProvider` for tests and ShedLock's wide range of supported storage backends.

Spring and Spring Boot make it straightforward to schedule tasks. You only need to enable scheduling support with the `@EnableScheduling` annotation, and then you can use the `@Scheduled` annotation to schedule any method to run at a fixed rate, with a fixed delay, or at a specific time.

This works great as long as you have only a single instance of your application running. Problems arise when you run multiple instances of your application. All `@Scheduled` methods will run in all instances, which can lead to problems like multiple instances trying to process the same task at the same time.

A common approach to solve this problem is to use a distributed lock so that only one instance of your application can run the scheduled task at a time. There are many different ways to implement such a lock. In this blog post, we will take a look at a library called [ShedLock](https://github.com/lukas-krecan/ShedLock), which provides a simple way to implement distributed locks for scheduled tasks in Spring applications.

The library abstracts away many different locking mechanisms, so you can use it with different databases or distributed caches. You can switch between different backends with only a few lines of code changes.

Here is a list of supported backends: Relational databases, MongoDB, DynamoDB, ZooKeeper, Redis, Hazelcast, Couchbase, ElasticSearch, OpenSearch, CosmosDB, Cassandra, Consul, ArangoDB, Neo4j, Etcd, Apache Ignite, In-Memory, Memcached, Datastore, and S3.

In this blog post, I will demonstrate how to use ShedLock with a simple Spring Boot application and a relational database as the locking mechanism.

## Problem

Let's first look at the problem we want to solve. I created a simple Spring Boot application with [jOOQ](https://www.jooq.org/), [Flyway](https://www.red-gate.com/products/flyway/), and PostgreSQL as the database. You find the complete code on [GitHub](https://github.com/ralscha/blog2022/tree/master/shedlockdemo).

The application contains a scheduled method that runs every minute. The method reads all users from a user table and sends a notification to each user.

```
private final DSLContext dsl;

public NotificationService(DSLContext dsl) {
  this.dsl = dsl;
}

@Scheduled(fixedDelay = 60_000)
@Transactional
public void processNotificationsWithNoLock() {
```

[NotificationService.java](https://github.com/ralscha/blog2022/blob/master/shedlockdemo/src/main/java/ch/rasc/shedlockdemo/service/NotificationService.java#L25-L33)

When you run multiple instances of the Spring Boot application, each instance will run the `processNotificationsWithNoLock` method every minute.

```
./mvnw spring-boot:run -Dspring-boot.run.arguments=--server.port=8080
./mvnw spring-boot:run -Dspring-boot.run.arguments=--server.port=8081
```

If you start the two instances at the exact same time, both instances will run the scheduled method at the same time. This is not always a problem, but in this contrived example, it sends the notifications twice to each user, and this is something we want to avoid.

In the next section, I will show you how to solve this problem with ShedLock so that only one instance of the application will run the scheduled task at a time.

## Setup

For ShedLock, you add the main dependency `shedlock-spring` to the `pom.xml` or `build.gradle` file. You also need to add the dependency for the backend you want to use. This example uses jOOQ, so add the `shedlock-provider-jooq` dependency. Check the [ShedLock documentation](https://github.com/lukas-krecan/ShedLock?tab=readme-ov-file#configure-lockprovider) to find the correct dependency for your preferred backend.

```
<dependency>
  <groupId>net.javacrumbs.shedlock</groupId>
  <artifactId>shedlock-spring</artifactId>
  <version>7.7.0</version>
</dependency>
<dependency>
  <groupId>net.javacrumbs.shedlock</groupId>
  <artifactId>shedlock-provider-jooq</artifactId>
  <version>7.7.0</version>
</dependency>
```

[pom.xml](https://github.com/ralscha/blog2022/blob/master/shedlockdemo/pom.xml#L27-L36)

In a configuration class, you enable ShedLock with the `@EnableSchedulerLock` annotation and configure the `LockProvider`.

```
@Configuration
@EnableScheduling
@EnableSchedulerLock(defaultLockAtMostFor = "10m")
public class SchedulingConfig {

  @Bean
  LockProvider getLockProvider(DSLContext dslContext) {
    return new JooqLockProvider(dslContext);
  }
}
```

[SchedulingConfig.java](https://github.com/ralscha/blog2022/blob/master/shedlockdemo/src/main/java/ch/rasc/shedlockdemo/config/SchedulingConfig.java#L12-L21)

Note that `defaultLockAtMostFor` is mandatory and defines the default maximum time a lock should be kept in case the instance that got the lock crashed before releasing the lock. When a scheduled method finishes without any error, the lock is released immediately. But in case of a crash, the lock will be released after the specified time.

This value is a fallback and can be overridden in each `@SchedulerLock` annotation. This value should be set to a value much higher than the normal duration of the scheduled task to avoid the lock being released while the method is still running.

For a database lock, you need to create a table used to store the locks. You find the DDL for the supported databases in the [ShedLock documentation](https://github.com/lukas-krecan/ShedLock?tab=readme-ov-file#jdbctemplate).

In this example, Flyway creates the table with this migration script:

```
CREATE TABLE shedlock(
    name VARCHAR(64) NOT NULL,
    lock_until TIMESTAMP NOT NULL,
    locked_at TIMESTAMP NOT NULL,
    locked_by VARCHAR(255) NOT NULL,
    PRIMARY KEY (name));
```

[V2\_\_create\_shedlock.sql](https://github.com/ralscha/blog2022/blob/master/shedlockdemo/src/main/resources/db/migration/V2__create_shedlock.sql)

## Using ShedLock

To use ShedLock, annotate the scheduled method with `@Scheduled` and `@SchedulerLock`. The ShedLock annotation defines the lock name and the maximum time the lock should be kept.

```
this.dsl.selectFrom(APP_USER).where(APP_USER_EMAIL.isNotNull())
    .forEach(appUser -> {
      sendNotification(appUser.get(APP_USER_EMAIL));
    });
```

[NotificationService.java](https://github.com/ralscha/blog2022/blob/master/shedlockdemo/src/main/java/ch/rasc/shedlockdemo/service/NotificationService.java#L35-L38)

Only methods annotated with `@SchedulerLock` are locked by ShedLock. Only one task with the same name can be executed at the same time. Because this is a distributed lock, it works across multiple instances of your application. If the lock is being held by one instance, other instances will not wait for the lock; they will simply skip the execution of the task.

The lock is released as soon as the method finishes. If the JVM crashes before the method finishes, the lock will be released after the time specified in `lockAtMostFor`. If you don't specify `lockAtMostFor`, the default value from `@EnableSchedulerLock` will be used.

Note that this method is scheduled with a fixed delay `@Scheduled(fixedDelay = 300_000)`. Even if you start the instances at the exact same time, over time this method will drift apart and will not run at the same time anymore. One instance might run the method, and just 10 seconds later, the other instance runs it again. ShedLock only prevents the same scheduled method from running at the same time. This is where the `lockAtLeastFor` parameter helps. With that, you can specify that the lock should be held for at least a certain time.

If, for example, you annotate the method like this, ShedLock will ensure that the lock is held for at least 4 minutes, and the method will not run more than once every 4 minutes.

```
@Scheduled(fixedDelay = 300_000)
@SchedulerLock(name = "processNotifications", lockAtMostFor = "4m", lockAtLeastFor="4m")
@Transactional
public void processNotifications() {
```

ShedLock also supports extending an active lock. If something unexpected happens during runtime and there is a way to detect that, you can extend the active lock with the following code.

```
LockExtender.extendActiveLock(Duration.ofMinutes(5), ZERO);
```

To prevent misconfiguration errors, you can call `LockAssert.assertLocked()` in your scheduled method. This will throw an exception if the lock is not held, which can help to catch configuration errors early.

```
@Scheduled(...)
@SchedulerLock(..)
public void scheduledTask() {
   LockAssert.assertLocked();
   // Your scheduled task logic here
}
```

## Testing

For testing purposes, you can use the `InMemoryLockProvider`, which is a simple in-memory implementation of the `LockProvider` interface. This provider does not require any database or external storage. This is useful for unit tests or integration tests where you don't want to rely on an external database.

```
<dependency>
    <groupId>net.javacrumbs.shedlock</groupId>
    <artifactId>shedlock-provider-inmemory</artifactId>
    <version>7.6.0</version>
    <scope>test</scope>
</dependency>
```
```
import net.javacrumbs.shedlock.provider.inmemory.InMemoryLockProvider;

@Bean
public LockProvider lockProvider() {
  return new InMemoryLockProvider();
}
```

Make sure not to accidentally enable the `InMemoryLockProvider` in production, as it does not provide any distributed locking capabilities.

## Conclusion

ShedLock is a handy library to implement distributed locks for scheduled tasks in Spring applications. It supports and abstracts away many different storage backends, so you can choose a technology that you are already using in your application or that you are familiar with.
