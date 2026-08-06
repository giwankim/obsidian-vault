---
title: "Lock @Scheduled Tasks With ShedLock and Spring Boot"
source: "https://rieckpil.de/lock-scheduled-tasks-with-shedlock-and-spring-boot/"
author:
  - "[[Philip Riecks]]"
published: 2021-01-12
created: 2026-07-17
description: "Learn how to integrate ShedLock with Spring Boot to sure an only-once execution of your @Scheduled jobs when running with multiple instances."
tags:
  - "clippings"
---

> [!summary]
> Explains how ShedLock ensures a `@Scheduled` task runs on only one instance when a Spring Boot application is scaled out, since Spring offers no built-in solution. It details the lock mechanics at the database level — how `lock_until`, `locked_at`, and `locked_by` are atomically updated to acquire and release locks — and why `lockAtLeastFor` is needed to guard short-running tasks against clock drift between nodes. Includes a full PostgreSQL setup with Flyway migrations and `JdbcTemplateLockProvider`.

As soon as you scale out your Spring Boot application (run with multiple instances) to e.g. increase throughput or availability, you have to ensure your application is ready for this architecture. Some parts of an application require tweaks before they fit for such an architecture. The use of `@Scheduled` tasks is a candidate for this. Most of the time, you only want this execution to happen in one instance and not in parallel. With this blog post, you’ll learn how ShedLock can be used to only execute a scheduled task once for a Spring Boot application.

## @Scheduled Tasks in a Scaled-Out Environment

A lot of Spring Boot applications use the `@Scheduled` annotation to execute tasks regularly. Starting from simple reporting jobs every evening, over cleanup jobs, to synchronization mechanisms, the variety of use cases is huge.

As long as our application is running with one instance, there is no problem as the execution happens only once. But as soon as our application is deployed to a load-balanced environment where multiple instances of the same Spring Boot application are running in parallel, our scheduled jobs are executed in parallel.

In the case of reporting or synchronization, we might want to execute this only once for the whole application. By default, every instance would execute the scheduled task, regardless of whether or not any other instance is already running it. This might result in inconsistent data or duplicated actions.

Spring doesn’t provide a solution for running `@Scheduled` tasks on only one instance at a time out-of-the-box. This is where [ShedLock](https://github.com/lukas-krecan/ShedLock) comes into play as it solves this problem.

## How ShedLock Ensures to Only Run a Job Once

ShedLock is a distributed lock for scheduled tasks.

It ensures a task is only executed once at the same time. Once the first Spring Boot instance acquires the lock for a scheduled task, all other instances will skip the task execution. As soon as the next task scheduling happens, all nodes will try to get the lock again.

ShedLock stores information about each scheduled job using persistent storage (so-called `LockProvider`) that all nodes connect to. There are multiple implementations for this `LockProvider` (e.g. for RDBMS, MongoDB, DynamoDB, Etcd, …) and we’ll pick PostgreSQL as an example.

The database table that ShedLock uses internally to manage the locks is straightforward, as it only has four columns:

- `name`: A unique name for the scheduled task
- `lock_until`: How long the current execution is locked
- `locked_at`: The timestamp a node acquired the current lock
- `locked_by`: An identifier for the node that acquired the current lock

ShedLock creates an entry for every scheduled task when we run the task for the first time. From this point on the database row (one row for each job) is always present and will only be updated (not deleted and re-created).

## How ShedLocks Locks a Scheduled Task

The actual locking of a scheduled task happens by setting the `lock_until` column to a date in the future.

As soon as a task is scheduled for execution, all application instances try to update the database row for this task. They are only able to lock the task if the task is currently not running (meaning `lock_until` <= `now()`).

The node that is able to update the columns for `lock_until`, `locked_at`, `locked_by` has the lock for this execution period and sets `lock_until` to `now() + lockAtMostFor (e.g. 30minutes)`:

ShedLock database table after acquiring a lock

Java

| 1  2  3  4  5 | +-------------+--------------------------+--------------------------+---------+  \|name \|lock\_until \|locked\_at \|locked\_by\|  +-------------+--------------------------+--------------------------+---------+  \|revenueReport\|2021-01-11 12:30:00.010691\|2021-01-11 12:00:00.010691\|duke \|  +-------------+--------------------------+--------------------------+---------+ |
| --- | --- |

All other nodes fail to acquire the lock because they’ll try to update the row for the job where `lock_until` <= `now()`. No row will be updated because the lock was already acquired by one instance and this instance set `lock_until` to a date in the future.

As soon as the task finishes, ShedLock updates the database row and sets `lock_until` to the current timestamp. There is one exception where ShedLock won’t use the current timestamp, which we’ll discover in the next section.

With the updated `lock_until` all nodes are eligible to run the next task execution:

ShedLock database table after releasing a lock

Java

| 1  2  3  4  5 | +-------------+--------------------------+--------------------------+---------+  \|name \|lock\_until \|locked\_at \|locked\_by\|  +-------------+--------------------------+--------------------------+---------+  \|revenueReport\|2021-01-11 12:00:04.610691\|2021-01-11 12:00:00.010691\|duke \|  +-------------+--------------------------+--------------------------+---------+ |
| --- | --- |

In case the task doesn’t finish (e.g. the node crashes or there is an unexpected delay), we get a new task execution after `lockAtMostFor`. As we’ll see in the upcoming sections, we have to provide a `lockAtMostFor` attribute for all our tasks. This acts as a safety net to avoid deadlocks when a node dies and hence is unable to release the lock.

## Lock Short Running Tasks With ShedLock

For short-running tasks, we can configure a lock that lasts for **at least** X. Without such a configuration, we could get multiple executions of a task if the clock difference between our nodes is greater than the job’s execution time.

Let’s see how the locking works for short-running tasks.

The procedure for acquiring the lock is the same compared to the already described scenario. What’s different is the unlock phase. Instead of setting `lock_until` to `now()`, ShedLock sets it to `locked_at + lockAtLeastFor` whenever the task execution is faster than `lockAtLeastFor`.

Let’s use an example to understand this better. For this purpose, let’s assume our application executes a short-running task every minute.

RevenueReporter.java

Java

| 1  2  3  4  5 | @Scheduled(cron = "0 \* \* \* \* \*")  @SchedulerLock(name = "shortRunningTask", lockAtMostFor = "50s", lockAtLeastFor = "30s")  public void shortRunningTask() {  System.out.println("Start short running task");  } |
| --- | --- |

Once this task finishes, ShedLock would set `lock_until` to `now()`. If we have a clock difference (which is hard to avoid in a distributed system) between our instances another node might pick up the execution again if the task execution is extremely fast.

To avoid such a scenario, we set `lockAtLeastFor` as part of our job definition, to block the next execution for at least the specified period.

ShedLock will then set `lock_until` to at least `locked_at + lockAtLeastFor` when unlocking the job.

First example (`lockAtLeastFor=30s`, really fast execution):

- The job starts at 8:00:00.000
- The job finishes at 8:00:00.450
- When unlocking this job, ShedLock sets `lock_until` to 8:00:30.000 and **not** to `now()`

Second example (`lockAtLeastFor=30s`, slow execution):

- The job starts at 8:00:00.000
- The job finishes at 8:00:31.500
- When unlocking this job, ShedLock sets `lock_until` to 8:00:31.500 (`now()`) because the execution took longer than our configure `lockAtLeastFor`

## Spring Boot Project Setup

We’re integrating ShedLock with a Spring Boot application that uses two Spring Boot Starters: Web and Data JPA.

Furthermore, our application connects to a PostgreSQL database and uses [Flyway](https://rieckpil.de/howto-best-practices-for-flyway-and-hibernate-with-spring-boot/) for database schema migrations.

The important parts of our `pom.xml` are the following:

pom.xml

XHTML

| 1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16  17  18  19  20  21  22  23  24  25  26  27  28  29  30  31  32  33  34  35  36  37  38  39  40  41  42  43  44  45  46  47  48  49  50  51  52  53  54  55  56  57  58  59  60  61  62  63  64  65  66  67  68 | <?xml version="1.0" encoding="UTF-8"?>  \<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"  xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">  \<modelVersion>4.0.0\</modelVersion>  \<parent>  \<groupId>org.springframework.boot\</groupId>  \<artifactId>spring-boot-starter-parent\</artifactId>  \<version>2.5.5\</version>  \<relativePath/> <!-- lookup parent from repository -->  \</parent>  \<groupId>de.rieckpil.blog\</groupId>  \<artifactId>spring-boot-shedlock\</artifactId>  \<version>0.0.1-SNAPSHOT\</version>  \<name>spring-boot-shedlock\</name>  \<description>Demo project for Spring Boot\</description>  \<properties>  <java.version>11</java.version>  <testcontainers.version>1.16.0</testcontainers.version>  <shedlock.version>4.29.0</shedlock.version>  \</properties>  \<dependencies>  \<dependency>  \<groupId>org.springframework.boot\</groupId>  \<artifactId>spring-boot-starter-web\</artifactId>  \</dependency>  \<dependency>  \<groupId>org.springframework.boot\</groupId>  \<artifactId>spring-boot-starter-data-jpa\</artifactId>  \</dependency>  \<dependency>  \<groupId>org.flywaydb\</groupId>  \<artifactId>flyway-core\</artifactId>  \</dependency>  \<dependency>  \<groupId>net.javacrumbs.shedlock\</groupId>  \<artifactId>shedlock-spring\</artifactId>  \<version>${shedlock.version}\</version>  \</dependency>  \<dependency>  \<groupId>net.javacrumbs.shedlock\</groupId>  \<artifactId>shedlock-provider-jdbc-template\</artifactId>  \<version>${shedlock.version}\</version>  \</dependency>  \<dependency>  \<groupId>org.postgresql\</groupId>  \<artifactId>postgresql\</artifactId>  \<scope>runtime\</scope>  \</dependency>  <!-- Dependencies for testing -->  \</dependencies>  \<build>  \<plugins>  \<plugin>  \<groupId>org.springframework.boot\</groupId>  \<artifactId>spring-boot-maven-plugin\</artifactId>  \</plugin>  \</plugins>  \</build>  \</project> |
| --- | --- |

ShedLock also comes with a [Micronaut integration](https://github.com/lukas-krecan/ShedLock#micronaut-integration) and can also be used [without any framework](https://github.com/lukas-krecan/ShedLock#locking-without-a-framework).

## Creating the ShedLock Table With Flyway

The README of ShedLock [contains copy-and-paste DDL statements](https://github.com/lukas-krecan/ShedLock#jdbctemplate) for multiple database vendors. As we are using PostgreSQL, we pick the corresponding statement to create ShedLock’s internal table `shedlock`.

We create a dedicated [Flyway](https://rieckpil.de/howto-best-practices-for-flyway-and-hibernate-with-spring-boot/) migration file for this statement and store it inside `src/main/resources/db/migration/V001__INIT_SHEDLOCK_TABLE.sql`:

src/main/resources/db/migration/V001\_\_INIT\_SHEDLOCK\_TABLE.sql

Transact-SQL

| 1  2  3  4  5  6  7 | CREATE TABLE shedlock(  name VARCHAR(64) NOT NULL,  lock\_until TIMESTAMP NOT NULL,  locked\_at TIMESTAMP NOT NULL,  locked\_by VARCHAR(255) NOT NULL,  PRIMARY KEY (name)  ); |
| --- | --- |

That’s everything we need setup-wise for our database.

Shedlock’s internal `LockProvider` also works with other underlying storage systems. We aren’t limited to relational databases and can also use e.g. MongoDB, DynamoDB, Hazelcast, Redis, Etcd, etc.

## Spring Boot Configuration Setup for ShedLock

As a first step, we have to enable scheduling and ShedLock’s Spring integration for our Spring Boot application.

ShedLock then expects a Spring Bean of type `LockProvider` as part of our `ApplicationContext`.

For our relational database setup, we make use of the `JdbcTemplateLockProvider` and configure it using the auto-configured `DataSource`:

ShedLockConfig.java

Java

| 1  2  3  4  5  6  7  8  9  10  11  12  13  14  15 | @Configuration  @EnableScheduling  @EnableSchedulerLock(defaultLockAtMostFor = "15m")  public class ShedLockConfig {  @Bean  public LockProvider lockProvider(DataSource dataSource) {  return new JdbcTemplateLockProvider(  JdbcTemplateLockProvider.Configuration.builder()  .withJdbcTemplate(new JdbcTemplate(dataSource))  .usingDbTime()  .build()  );  }  } |
| --- | --- |

While enabling ShedLock’s Spring integration (`@EnableSchedulerLock`) we have to specify `defaultLockAtMostFor`. This is attribute acts as our fallback configuration for locks where we don’t specify `lockAtMostFor` explicitly.

With this configuration in place, we can start adding locks to our scheduled tasks.

## Adding a Lock to a Scheduled Task With Spring Boot

What’s left is to add `@SchedulerLock` to all our `@Scheduled` jobs that we want to prevent multiple parallel executions.

As part of this annotation, we provide a name for the scheduled task that ShedLock uses as the primary key for the internal `shedlock` table. Hence this name has to be unique across our application:

RevenueReporter.java

Java

| 1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16 | @Component  public class RevenueReporter {  @Scheduled(cron = "0 0 12 \* \* \*")  @SchedulerLock(name = "revenueReport", lockAtMostFor = "30m")  public void report() {  // report revenue based on e.g. orders in database  System.out.println("Reporting revenue");  }  @Scheduled(cron = "0 \* \* \* \* \*")  @SchedulerLock(name = "shortRunningTask", lockAtMostFor = "50s", lockAtLeastFor = "30s")  public void shortRunningTask() {  System.out.println("Start short running task");  }  } |
| --- | --- |

For short-running tasks, we should configure the `lockAtLeastFor`. This prevents our short-running tasks to be executed multiple times due to a clock difference between our application nodes.

In summary, the integration of ShedLock almost takes no effort for our Spring Boot application. Due to the variety of `LockProvider` s, you should be able to use your primary storage solution also for this purpose. What’s left is to tweak `lockAtMostFor` and `lockAtLeastFor` (if required) for each of your jobs. It might help to monitor the execution time of your jobs and then decide on those values.

The source code for this [Spring Boot and ShedLock demonstration](https://github.com/rieckpil/blog-tutorials/tree/master/spring-boot-shedlock) is available on GitHub.

Have fun locking your scheduled tasks with ShedLock,

Philip
