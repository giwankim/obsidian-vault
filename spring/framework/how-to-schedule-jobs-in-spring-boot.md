---
title: "How to Schedule Jobs in Spring Boot"
source: "https://alexanderobregon.substack.com/p/how-to-schedule-jobs-in-spring-boot?utm_source=substack&utm_medium=email"
author:
  - "[[Alexander Obregon]]"
published: 2026-09-23
created: 2026-09-28
description: "Routine maintenance can pile up quickly when an application depends on manual steps, command-line scripts, or reminders someone has to remember at the right time."
tags:
  - "clippings"
---

> [!summary]
> A walkthrough of Spring Boot's `@Scheduled` support, from enabling it with `@EnableScheduling` to choosing between `fixedDelay` (measured from completion), `fixedRate` (planned start cadence), and six-field cron expressions with a `zone` and property placeholders. It covers overlap behavior: the default single-thread scheduler pool, the switch to `SimpleAsyncTaskScheduler` under virtual threads, and guarding a job with a `ReentrantLock`. That lock only protects one JVM, so multi-instance deployments need a database-backed or distributed lock.

Routine maintenance can pile up quickly when an application depends on manual steps, command-line scripts, or reminders someone has to remember at the right time. Spring Boot can bring recurring jobs into the application through scheduling support, letting methods run after a fixed delay, at a fixed rate, or at specific times through cron expressions. Time zones can be assigned directly to cron schedules, which keeps clock-based jobs tied to the intended region rather than the server’s local time. That makes scheduling a good option for removing expired records, refreshing stored data, generating reports, or checking for unfinished processing, while giving you control over how each run is timed and what happens if an earlier run is still active.

### Starting Scheduled Jobs

Spring’s annotation-based scheduler lets recurring application jobs live beside the services they call instead of depending on someone to launch a script at the right time. We first want to activate scheduling support, after which Spring can register methods marked with `@Scheduled` as the application context starts. From there, each job can follow a timing rule that matches what it needs to do, while the method itself stays focused on the operation being performed.

#### Turn On Scheduling

Before Spring can register `@Scheduled` methods, scheduling support has to be active in the application context. `@EnableScheduling` handles that, and the main Spring Boot application class is a common place for the annotation because it keeps the scheduling configuration near the application entry point.

```markup
package com.example.scheduling;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class SchedulingApplication {

    public static void main(String[] args) {
        SpringApplication.run(SchedulingApplication.class, args);
    }
}
```

We add `@EnableScheduling` beside `@SpringBootApplication`, so Spring checks its managed beans for scheduled methods during application startup. `SpringApplication.run()` creates the application context as usual, while `@EnableScheduling` adds the scheduling support needed for Spring to register methods carrying `@Scheduled`.

That managed-bean detail is important because placing `@Scheduled` on an object created manually with `new` does not place that object under Spring’s scheduling management. Classes containing scheduled methods are commonly registered through annotations such as `@Component` or `@Service`, which lets Spring create the instance and inspect it during startup.

The scheduler belongs to the running application process, so scheduled methods stop when the application stops. Spring does not store missed executions in a durable queue for later recovery, which means a basic scheduled method should be treated as part of the application’s active runtime rather than as a persistent job record. If the process is offline when a scheduled time passes, that missed execution is not automatically replayed after startup.

#### Create the First Job

Scheduled methods are commonly kept small so they can call a service that contains the application logic. This keeps timing concerns in the scheduling class while database access, file processing, HTTP calls, and other application behavior stay in the service that already owns them.

```markup
package com.example.scheduling;

import java.util.concurrent.TimeUnit;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class MaintenanceJobs {

    @Scheduled(fixedDelay = 15, timeUnit = TimeUnit.MINUTES)
    public void removeExpiredRecords() {
        System.out.println("Removing expired records");
    }
}
```

Spring registers `MaintenanceJobs` because `@Component` makes the class a managed bean. The `@Scheduled` annotation tells Spring when `removeExpiredRecords()` should be called, while `timeUnit = TimeUnit.MINUTES` lets us express the interval in minutes instead of converting fifteen minutes into milliseconds. Without `timeUnit`, Spring treats fixed delay, fixed rate, and initial delay values as milliseconds.

The method itself takes no arguments, which lets Spring call it without having to supply input values. Returning `void` also matches the common synchronous form because the scheduler is interested in invoking the method at the configured time rather than receiving a value back from it.

As the operation grows beyond a small demonstration, we can move the application logic into a service and leave the scheduling method responsible for triggering that service.

```markup
package com.example.scheduling;

import java.util.concurrent.TimeUnit;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class MaintenanceJobs {

    private final ExpiredRecordService expiredRecordService;

    public MaintenanceJobs(ExpiredRecordService expiredRecordService) {
        this.expiredRecordService = expiredRecordService;
    }

    @Scheduled(fixedDelay = 15, timeUnit = TimeUnit.MINUTES)
    public void removeExpiredRecords() {
        expiredRecordService.removeExpiredRecords();
    }
}
```

Spring supplies `ExpiredRecordService` through the constructor when it creates `MaintenanceJobs`, and the scheduled method then calls `removeExpiredRecords()` at the configured interval. That keeps the scheduling class centered on timing while the service handles the actual record removal. Method names are worth keeping specific because scheduled jobs usually run without someone directly triggering them. Names such as `removeExpiredRecords`, `refreshCatalogCache`, or `recalculateDailyTotals` make logs and stack traces more informative than a generic name such as `run`.

Spring also supports reactive scheduled methods, but regular synchronous jobs can stay with the no-argument form shown above. For the maintenance jobs covered here, that keeps the execution flow easy to follow while we focus on how Spring determines the next run time.

#### Run With a Fixed Delay

With `fixedDelay`, Spring calculates the next execution from the completion of the previous execution. The waiting period begins after the method finishes, so the amount of processing time naturally affects when the following run begins.

```markup
@Scheduled(
    initialDelay = 1,
    fixedDelay = 10,
    timeUnit = TimeUnit.MINUTES
)
public void removeExpiredSessions() {
    sessionService.removeExpiredSessions();
}
```

We give the first execution a one-minute startup delay through `initialDelay`, then tell Spring to wait ten minutes after every completed run through `fixedDelay`. If `removeExpiredSessions()` takes three minutes, Spring waits until those three minutes are finished before starting the ten-minute delay. The next execution therefore begins about thirteen minutes after the previous start.

Longer processing follows the same rule, if session removal takes twenty minutes, Spring waits for those twenty minutes to finish and then waits the full ten-minute delay before calling the method again. Execution duration becomes part of the overall spacing between starts because the delay clock does not begin until the previous call has returned.

This timing model works well for recurring operations where some breathing room after completion is desirable. Polling a data source, deleting expired sessions, checking an import directory, or refreshing data from a remote service can all benefit from a full pause between runs because the next execution does not try to preserve an earlier start schedule.

`initialDelay` affects only the first execution after scheduling begins. Later calls follow the configured `fixedDelay`, so the startup pause does not get added again after every run.

Fixed delay can also make timing easier to reason through when processing duration changes. We always have the same relationship between executions, which is completion first, followed by the configured delay, followed by the next start.

#### Run at a Fixed Rate

With `fixedRate`, Spring bases the schedule on planned start times rather than waiting for the previous execution to finish and then beginning a new delay. If the rate is five minutes, the scheduler targets five-minute intervals from the established schedule:

```markup
@Scheduled(
    initialDelay = 30,
    fixedRate = 5,
    timeUnit = TimeUnit.MINUTES
)
public void refreshInventoryTotals() {
    inventoryService.refreshTotals();
}
```

We delay the first execution by thirty minutes, then give later executions a five-minute fixed rate. If `refreshInventoryTotals()` finishes well before the next planned start, the remaining time passes before Spring calls it again. If processing takes longer than five minutes, a later execution can begin late because the scheduled start time has already passed.

With Spring Boot’s regular `ThreadPoolTaskScheduler`, successive executions of the same fixed-rate job do not run concurrently. If one execution is still running when the next scheduled start arrives, that later call waits rather than running beside the earlier call. With virtual threads enabled, Spring Boot uses `SimpleAsyncTaskScheduler`, which can start fixed-rate executions on separate threads.

The difference from fixed delay becomes easier to see when the method takes a noticeable amount of time. If a fixed-rate job begins at 2 PM with a five-minute period, its planned schedule continues around 2:05, 2:10, 2:15, and later intervals. If an execution lasts two minutes, the remaining time before the next planned start is about three minutes.

With a five-minute fixed delay, that same two-minute execution would finish first and then begin a full five-minute wait. The next start would come about seven minutes after the earlier start instead of following the original five-minute cadence. Fixed rate is a good match for recurring activity where planned start cadence is more important than leaving a full pause after completion. Refreshing counters, sampling internal values, or recalculating stored data at regular intervals can follow that timing model when the processing normally finishes comfortably inside its configured period.

Fixed delay and fixed rate therefore answer different timing needs. Fixed delay measures from completion, while fixed rate follows planned start intervals, and recognizing that difference early keeps scheduled behavior from becoming surprising later.

### Controlling Job Timing

Clock-based scheduling gives recurring jobs a precise calendar instead of relying only on elapsed intervals. We can tell Spring to call a method at a particular minute, hour, weekday, or combination of calendar fields, then assign a time zone so the schedule follows the intended region. Timing also deserves closer attention as an application gains more scheduled jobs because scheduler threads, repeated declarations, asynchronous execution, and multiple application instances can affect when calls begin and how they interact.

#### Schedule With Cron

Cron expressions are a good choice when a job needs to follow the clock rather than wait for a repeating interval. Spring cron expressions contain six fields ordered as second, minute, hour, day of month, month, and day of week. Remembering the seconds field helps when moving between Spring and cron formats that contain five fields because leaving it out changes the meaning of the expression.

For a nightly archive job that should begin at 2:30 AM, we can place the full schedule directly on the method:

```markup
@Scheduled(cron = "0 30 2 * * *")
public void archiveOldEvents() {
    eventService.archiveOldEvents();
}
```

Reading from left to right, the first `0` selects second zero, `30` selects minute thirty, and `2` selects the 2 AM hour. The remaining wildcard fields allow every day of the month, every month, and every day of the week, so Spring schedules `archiveOldEvents()` for 2:30 AM each day.

Weekday schedules can narrow the final field to the days we want. If a report should be generated at 6 AM from Monday through Friday, we can express the schedule like this:

```markup
@Scheduled(cron = "0 0 6 * * MON-FRI")
public void createMorningReport() {
    reportService.createMorningReport();
}
```

We still have six fields, but the final field now limits execution to Monday through Friday. The first three values select second zero, minute zero, and hour six, while the two middle calendar fields allow every day of the month and every month. Spring therefore calls `createMorningReport()` at 6 AM on weekdays.

Clock-based jobs can also carry a defined time zone when a local business time needs to stay consistent across deployments. The `zone` attribute on `@Scheduled` tells Spring which region should be applied when it evaluates the cron expression:

```markup
@Scheduled(
    cron = "0 30 2 * * *",
    zone = "America/Chicago"
)
public void archiveOldEvents() {
    eventService.archiveOldEvents();
}
```

We now tie the 2:30 AM execution to `America/Chicago`, so Spring follows that region rather than relying on the default time zone of the host process. Region IDs such as `America/Chicago` also carry daylight saving time rules, which makes them appropriate for schedules tied to local civil time rather than a fixed UTC offset.

Keeping the cron expression outside Java can help when environments need different run times. Spring resolves property placeholders inside `@Scheduled`, so we can move both the expression and zone into application configuration:

```markup
@Scheduled(
    cron = "${jobs.archive.cron}",
    zone = "${jobs.archive.zone}"
)
public void archiveOldEvents() {
    eventService.archiveOldEvents();
}
```

The matching `application.properties` entries can hold the actual values:

```markup
jobs.archive.cron=0 30 2 * * *
jobs.archive.zone=America/Chicago
```

We leave the Java method unchanged while configuration supplies its clock time and region. Development, staging, and production can then carry different values without editing the scheduling method for every environment.

Spring also accepts cron macros such as `@hourly`, `@daily`, `@weekly`, `@monthly`, and `@yearly`. These macros replace common six-field expressions when their built-in timing matches what we need:

```markup
@Scheduled(cron = "@hourly")
public void refreshSummaryData() {
    summaryService.refresh();
}
```

We tell Spring to call `refreshSummaryData()` at the start of every hour, which corresponds to `0 0 * * * *`. More specific schedules still benefit from an explicit six-field expression, such as a weekday run at 6:15 AM or a nightly operation tied to a named region.

Cron timing also affects what happens when an execution lasts long enough to pass a later cron time. With the regular thread-pool scheduler, Spring’s cron trigger calculates its next execution from completion of the preceding run, so a cron time that passes while that run is still active can be skipped rather than replayed immediately afterward. When virtual threads are active, Spring Boot uses `SimpleAsyncTaskScheduler`, which can start cron executions on new threads, so overlap behavior depends on the scheduler being used.

#### Prevent Unexpected Overlap

Concurrency becomes more relevant when several scheduled methods share the same application process or when more than one trigger can reach the same operation. With virtual threads turned off, Spring Boot starts with a scheduling pool size of `1`, so a long-running scheduled method can occupy the scheduler thread while a different scheduled method is ready to begin.

The scheduler pool can be increased through configuration:

```markup
spring.task.scheduling.pool.size=4
```

We now give Spring four scheduler threads instead of the default single thread, allowing different scheduled methods to execute at the same time when capacity remains. The pool-size property does not control scheduler concurrency when Spring Boot virtual threads are active, so that configuration applies to the regular platform-thread scheduler.

More scheduler threads can reduce delays between unrelated jobs, but they also allow those jobs to reach the database, filesystem, remote services, or shared application state at the same time. Increasing the pool therefore changes more than execution capacity because operations that previously ran one after the other can now run concurrently. Repeated `@Scheduled` declarations deserve closer attention because Spring processes every declaration independently. The annotation is repeatable, so the same method can carry more than one schedule, and those schedules can reach the method independently if their timing becomes close enough.

We can protect a locally scheduled import with a `ReentrantLock` when several local triggers or other entry points can reach the same operation:

```markup
package com.example.scheduling;

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class ImportJobs {

    private final Lock importLock = new ReentrantLock();
    private final UpdateService updateService;

    public ImportJobs(UpdateService updateService) {
        this.updateService = updateService;
    }

    @Scheduled(cron = "0 0 8 * * MON-FRI")
    @Scheduled(cron = "0 0 12 * * MON-FRI")
    public void importUpdates() {
        if (!importLock.tryLock()) {
            return;
        }

        try {
            updateService.importUpdates();
        } finally {
            importLock.unlock();
        }
    }
}
```

We give `importUpdates()` two independent weekday schedules, with calls planned for 8 AM and noon. Before starting the import, `tryLock()` checks the local lock. If an earlier invocation still owns it, the later call returns without starting a second import. The `finally` block releases the lock after `updateService.importUpdates()` finishes, including cases where that service call throws an exception.

That protection reaches only the current JVM. If the same Spring Boot application runs in several instances, every instance has its own scheduler and its own `ReentrantLock`, so each instance can still start the import independently. Jobs that must execute a single time across several application instances need coordination shared by those instances, such as a database-backed lock, distributed locking mechanism, or scheduler built for clustered execution.

Asynchronous execution changes the timing boundary as well. If a scheduled method sends processing to an asynchronous executor and returns before that processing finishes, the scheduler treats the method invocation as completed while the asynchronous operation remains active. Later triggers can then submit more processing before the earlier asynchronous call has finished, so operations that must remain single-flight need protection around the processing itself rather than only around the scheduling callback.

### Conclusion

Spring Boot scheduling comes down to choosing how each recurring job should run, then matching that timing to `@Scheduled`. Fixed delay waits from the end of the previous run, fixed rate follows planned start intervals, and cron expressions handle clock-based schedules with optional time zones, while scheduler configuration and locking help keep overlapping executions from creating duplicate processing.

![](https://substackcdn.com/image/fetch/$s_!4Obd!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F762e3b8b-750c-42e0-a944-4a3fd46e76fe_276x276.png)

Spring Boot icon by Icons8
