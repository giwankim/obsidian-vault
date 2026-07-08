---
title: "Temporal Primer - Building Long-Running Systems"
source: "https://arpitbhayani.me/blogs/temporal-primer"
author:
  - "[[Arpit Bhayani]]"
published: 2026-05-20
created: 2026-07-08
description: "If you have ever taped together a cron job, message queue, a database table for state, and a retry loop - only to watch the whole thing break during a network blip at 2am - you already understand the problem Temporal solves. The fix you built was a workflow engine. Temporal is workflow engine done right."
tags:
  - "clippings"
---

> [!summary]
> A primer on Temporal, the open-source durable-execution platform that lets multi-step distributed workflows resume exactly where they left off after crashes, deploys, or network partitions. Covers the core primitives — deterministic Workflows, side-effecting Activities, stateless Workers, event-history replay, signals, timers, and child workflows — plus the determinism constraint, retry/timeout policies, versioning, and Continue-As-New for capping long histories. Closes with where Temporal fits (agentic systems, payments, provisioning, human-in-the-loop) and where it doesn't (simple request-response APIs, high-throughput streaming, low-latency compute).

![](https://edge.arpitbhayani.me/img/arpit-6.jpg)

[Arpit Bhayani](https://arpitbhayani.me/)

engineering, databases, and systems. always building.

If you have ever taped together a [cron job](https://en.wikipedia.org/wiki/Cron), a [message queue](https://en.wikipedia.org/wiki/Message_queue), a [database table](https://en.wikipedia.org/wiki/Relational_database_management_system) for state, and a [retry loop](https://en.wikipedia.org/wiki/Retry_pattern) - only to watch the whole thing break during a network blip at 2am - you already understand the problem Temporal solves. The fix you built was a workflow engine. Temporal is a workflow engine done right.

[Temporal](https://github.com/temporalio/temporal) is an open-source [durable execution](https://docs.temporal.io/concepts/what-is-durable-execution) platform. The idea is simple - your code runs to completion no matter what happens to the underlying infrastructure - processes crash, network partitions happen, VMs get killed during deployments - nothing ends your workflow. It resumes exactly where it left off, with the exact state it had before.

This write-up is a primer on the core concepts and features of Temporal. It covers how the system works, what its major building blocks are, and where the non-obvious traps live. The goal is that after reading this, you understand the mental model well enough to evaluate whether Temporal belongs in your architecture and know what to reach for when it does.

Fun fact: temporal can come in very handy while building long-running [agentic systems](https://aws.amazon.com/what-is/agentic-ai/).

## The Problem With Distributed Workflows

Consider a multi-step process: charge a payment, provision a resource, send a confirmation email, update a billing record. In a naive implementation, you chain these calls in sequence. The first call succeeds. The third call throws a timeout. Now what?

You either retry the whole thing from the start, risking a double-charge, or you track which steps succeeded and build a resumption mechanism. That mechanism needs its own storage, its own retry logic, its own failure model. Now, you build a [state machine](https://en.wikipedia.org/wiki/Finite-state_machine). Then you realize it needs to handle concurrent runs. And timeouts at each step. And human-approval pauses. And you need to be able to cancel mid-flight. And you need observability into which step each run is on.

You have just reinvented what Temporal gives you for free.

The patterns we engineers reach for without a platform - status columns in databases, polling loops, dead-letter queues, hand-rolled [sagas](https://docs.temporal.io/concepts/what-is-a-saga-pattern) - all exist to approximate what [durable execution](https://docs.temporal.io/concepts/what-is-durable-execution) provides natively. Temporal collapses this complexity into a programming model where you write code that looks linear, and the platform handles all the failure recovery underneath.

## Workflows, Activities, and Workers

Everything in Temporal revolves around three concepts.

A Workflow is a function that defines your business logic. It orchestrates the overall process. It is the “what should happen and in what order” written as code in your language of choice: [Go](https://go.dev/), [Python](https://www.python.org/), [TypeScript](https://www.typescriptlang.org/), [Java](https://www.java.com/), [C#](https://learn.microsoft.com/en-us/dotnet/csharp/), or [PHP](https://www.php.net/). Crucially, Workflow functions must be deterministic. More on that constraint shortly, because it is the most important thing to internalize.

An Activity is a function that does actual work in the world. It calls external APIs, writes to databases, sends emails, and invokes [ML models](https://en.wikipedia.org/wiki/Machine_learning). Activities are the “do a thing” units. They are explicitly not deterministic - they interact with systems that can fail, return different results on different calls, and take unpredictable amounts of time. Temporal handles retrying Activities automatically when they fail.

A Worker is a process you deploy that polls Temporal’s task queue and executes your Workflow and Activity code. Workers are stateless. They can crash and be replaced. Temporal’s server coordinates which worker picks up which task.

Here is a minimal example in [Python](https://www.python.org/) to make this concrete:

```python
@activity.defn
async def charge_payment(order_id: str, amount: int) -> str:
    # Calls an external payments API; may fail, may be slow
    return await payments_client.charge(order_id, amount)

@workflow.defn
class OrderFulfillmentWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> None:
        # Each activity call is automatically retried on failure
        payment_id = await workflow.execute_activity(
            charge_payment,
            order_id,
            start_to_close_timeout=timedelta(seconds=30),
        )
        await workflow.execute_activity(
            provision_resource,
            order_id,
            start_to_close_timeout=timedelta(minutes=5),
        )
        await workflow.execute_activity(
            send_confirmation,
            order_id,
            start_to_close_timeout=timedelta(seconds=10),
        )
```

This looks like ordinary async code. The extraordinary part is that if your worker process crashes between the `charge_payment` and `provision_resource` calls, a new worker picks up the workflow and resumes from exactly the right point. The payment is not re-charged. The workflow does not restart from scratch. This just works, without any extra code on your part.

## How Durability Actually Works

Every significant event in a workflow’s life - an activity was scheduled, an activity completed, a timer fired, a signal arrived - is recorded as an immutable entry in an event history, persisted in Temporal’s database (tunable - [Cassandra](https://cassandra.apache.org/), [PostgreSQL](https://www.postgresql.org/), or [MySQL](https://www.mysql.com/)). This event history is the ground truth for a workflow’s state.

When a worker picks up a workflow task (after a crash or a new deployment), it does not restore memory from a snapshot. Instead, it replays the event history from the beginning, re-executing the workflow function. But here is the key: during replay, calls to `execute_activity` do not actually invoke the activity again.

If the event history already contains the result of that activity, Temporal returns the recorded result immediately. The workflow fast-forwards to the point where the history ends, then continues executing from there.

This is why workflow code must be deterministic. If your workflow function takes different code paths on replay than it did during the original execution, the commands it emits will not match the event history, and Temporal raises a non-determinism error. The replay mechanism requires that given the same history, the workflow always makes the same decisions.

Concretely, this means your workflow function cannot:

- Read the current time with `time.now()` - use `workflow.now()` instead, which returns the recorded time
- Generate random numbers with `random.random()` - use `workflow.random()`
- Make direct network calls or database queries - those belong in activities
- Spawn [goroutines](https://go.dev/tour/concurrency/1) or [threads](https://en.wikipedia.org/wiki/Thread_\(computing\)) that run outside Temporal’s control
- Access global mutable state or environment variables that could change between runs

The Temporal SDKs provide replay-safe equivalents for all of these. The constraint sounds limiting, but in practice, it is clean once you internalize it: anything that touches the outside world is an activity, and anything that only coordinates and makes decisions is the workflow.

## Determinism Constraint

The most common production issue for teams new to Temporal is breaking determinism when deploying new workflow code.

If you have running workflows and you rename an activity call, reorder two activity invocations, or add a new step mid-sequence, you have changed what commands the workflow will emit during replay. Any in-flight workflows will hit a non-determinism error when they next replay.

Temporal provides a versioning API specifically for this:

```python
v = workflow.get_version("add-fraud-check", workflow.DEFAULT_VERSION, 1)
if v == 1:
    # New code path with fraud check
    await workflow.execute_activity(
        fraud_check,
        order,
        start_to_close_timeout=timedelta(seconds=10),
    )
# Both old and new code then continue here
await workflow.execute_activity(
    charge_payment,
    order,
    start_to_close_timeout=timedelta(seconds=30),
)
```

The `get_version` call is recorded in the event history. Old workflows replay the old code path. New workflows replay the new one. Once all old workflows drain, you remove the version check and clean up. It is tedious but it is the correct mental model: workflow code is like a database migration, not a regular function you can change freely.

[Stripe](https://stripe.com/), which runs Temporal for critical financial workflows, built an internal platform team around this concern specifically. They wrapped the Temporal SDK to enforce versioning discipline across all teams.

## Retries, Timeouts, and Activity Reliability

Activities are where reliability actually lives. When you call an activity, you configure a retry policy and timeouts. Temporal handles the rest.

```python
await workflow.execute_activity(
    send_email,
    user_id,
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy=RetryPolicy(
        initial_interval=timedelta(seconds=1),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(minutes=5),
        maximum_attempts=10,
        non_retryable_error_types=["InvalidEmailError"],
    ),
)
```

There are four timeout types worth understanding:

- `schedule_to_close_timeout`: the maximum total time from when the activity is scheduled to when it must complete, including all retry attempts
- `start_to_close_timeout`: the maximum time a single attempt can take
- `schedule_to_start_timeout`: the maximum time the activity can wait in the queue before a worker picks it up
- `heartbeat_timeout`: for long-running activities, if no heartbeat is received within this window, Temporal considers the activity lost and retries it

Heartbeating is a pattern for activities that run for minutes or hours. The activity periodically calls `activity.heartbeat()` to tell Temporal it is still alive. If the worker dies, Temporal detects the absence of heartbeats and retries the activity on another worker. The activity can also read the heartbeat details to resume from a checkpoint rather than starting from zero.

```python
@activity.defn
async def process_large_file(file_id: str) -> None:
    details = activity.info().heartbeat_details
    start_offset = details[0] if details else 0

    for chunk_offset in range(start_offset, file_size, chunk_size):
        process_chunk(file_id, chunk_offset)
        activity.heartbeat(chunk_offset)  # Record progress
```

This pattern works well for any activity doing chunked processing: video encoding, large file uploads, batch data migration, [model training](https://en.wikipedia.org/wiki/Machine_learning) jobs.

## Signals

One of Temporal’s most underappreciated features is its messaging model for interacting with in-flight workflows.

Signals are asynchronous messages sent to a running workflow from the outside. The workflow receives the signal and can change its behavior based on it. This is how you implement human-in-the-loop processes, approval gates, and event-driven state transitions without polling.

```python
@workflow.defn
class LoanApprovalWorkflow:
    def __init__(self) -> None:
        self._approved: Optional[bool] = None

    @workflow.signal
    async def approve(self, approved: bool) -> None:
        self._approved = approved

    @workflow.run
    async def run(self, loan_id: str) -> str:
        # Run automated checks first
        await workflow.execute_activity(run_credit_check, loan_id, ...)

        # Wait indefinitely for a human decision
        await workflow.wait_condition(lambda: self._approved is not None)

        if self._approved:
            await workflow.execute_activity(disburse_funds, loan_id, ...)
            return "approved"
        return "rejected"
```

The `workflow.wait_condition` call durably suspends the workflow. It consumes no polling resources. If the worker crashes while waiting for the approval signal, a new worker resumes the workflow and waits again. The workflow can sit in this state for days or weeks without any degradation.

This signal pattern works for any workflow that models a stateful process over time: order fulfillment, mortgage underwriting, incident response, subscription lifecycle.

## Timers

Temporal lets you sleep for arbitrary durations in a workflow function:

```python
@workflow.run
async def run(self) -> None:
    for month in range(12):
        await workflow.execute_activity(send_monthly_report, ...)
        await workflow.sleep(timedelta(days=30))
```

This is not a thread sleep. The workflow is durably suspended for 30 days. No resources are consumed during the wait. If the Temporal server is restarted the day after the workflow sleeps, the timer still fires on schedule 29 days later. The timer state lives in Temporal’s persistent storage, not in any process’s memory.

This primitive alone eliminates an entire class of scheduler infrastructure. Any process that needs to “do something, wait a while, do something else” is a natural fit for Temporal timers rather than a cron job that re-fetched state on every execution.

## Child Workflows and Fan-Out

Workflows can spawn child workflows. This is the mechanism for decomposing complex processes, achieving parallelism, and managing scope.

```python
# Process 10,000 orders in parallel, each as its own durable workflow
futures = []
for order_id in order_ids:
    f = workflow.execute_child_workflow(
        ProcessOrderWorkflow.run,
        order_id,
        id=f"order-{order_id}",
    )
    futures.append(f)

# Wait for all to complete
await asyncio.gather(*futures)
```

Each child workflow has its own event history, its own retry semantics, and its own independent lifecycle. If one child fails, only that child fails. The parent can handle the failure as a normal error return. This fan-out pattern is the right model for batch processing, multi-tenant operations where each tenant gets its own isolated execution, and data pipeline steps that run in parallel.

The `id` assignment matters. Child workflows with stable, deterministic IDs based on their subject (an order ID, a user ID, a job ID) give you idempotency for free. Starting a child workflow with an ID that already exists and is still running does nothing extra - the existing one continues. This is the “at most once” guarantee without extra code.

## Long-Running Workflow Problem

Temporal terminates a workflow execution if its event history exceeds [50,000 events](https://docs.temporal.io/concepts/what-is-an-event-history#size-limit) or 50 MB in size. This exists because replay performance degrades proportionally to history length. A 40,000-event history takes measurably longer to replay than a 400-event history.

For workflows that run indefinitely - polling loops, perpetual subscription managers, long-running monitoring processes - this limit becomes relevant. The solution is [Continue-As-New](https://docs.temporal.io/concepts/what-is-continue-as-new): atomically complete the current workflow execution and start a new one with the same workflow ID but a fresh history, passing the current state as the new execution’s input.

```python
@workflow.run
async def run(self, state: WorkflowState) -> None:
    for i in range(1000):
        await workflow.execute_activity(process_batch, state.offset, ...)
        state.offset += BATCH_SIZE

        if i == 999:
            # Reset history by continuing as new with updated state
            workflow.continue_as_new(state)
```

Think of it as stackless recursion. You call the same function with updated parameters, but without accumulating a growing call stack. The old history is retained for the configured retention period and then deleted. The workflow continues seamlessly.

The practical guidance: design any workflow that runs for months or years to call `continue_as_new` periodically. A good trigger is when the event count crosses around 10,000 - well before the hard limit - to keep replay latency predictable.

## Task Queues and Worker Deployment

Temporal routes tasks to workers via named task queues. Workers poll a specific queue and execute only the workflow and activity code registered for that queue. This gives you a few important deployment properties.

Different worker pools can run different queues. You can have a “high-priority” queue polled by workers with more resources and a “batch” queue polled by workers with fewer. Activities that need [GPU](https://en.wikipedia.org/wiki/Graphics_processing_unit) resources can be routed to a GPU-provisioned worker pool via a dedicated queue. The routing is explicit in both the worker registration and the activity invocation.

```python
# Worker registered on GPU queue
worker = Worker(
    client,
    task_queue="ml-gpu-workers",
    workflows=[TrainingWorkflow],
    activities=[run_training_step, evaluate_model],
)

# Activity invocation targeting that queue
await workflow.execute_activity(
    run_training_step,
    model_config,
    task_queue="ml-gpu-workers",
    start_to_close_timeout=timedelta(hours=2),
)
```

Rolling deployments are also handled cleanly. Old workers drain their in-flight tasks while new workers pick up new tasks. Because workflow versioning decouples code changes from in-flight executions, you can deploy new worker code without killing running workflows.

## Where Temporal Fits and Where It Does Not

Temporal is the right choice when your problem involves multi-step processes with coordination, error recovery, and state accumulated over time. Specific use cases where it consistently delivers:

- Long-running [agentic systems](https://aws.amazon.com/what-is/agentic-ai/) where tool calls need retry guarantees and state must survive restarts
- Financial transaction flows where partial completion must be detected and compensated
- Infrastructure provisioning pipelines that span multiple cloud APIs and take minutes to hours
- Customer onboarding and lifecycle management where steps span days or weeks
- Batch data processing with fan-out and result aggregation
- Any approval workflow that requires human-in-the-loop steps with no polling

[Netflix](https://netflixtechblog.com/) uses Temporal for [CI/CD](https://www.redhat.com/en/topics/devops/what-is-ci-cd) deployment pipelines, bringing deployment failure rates from around 4% to near-zero. [Datadog](https://www.datadoghq.com/) runs incident management workflows that persist across days and service restarts with complete audit trails. [Stripe](https://stripe.com/) standardized on Temporal for payment processing workflows where exactly-once guarantees are non-negotiable. [Coinbase](https://www.coinbase.com/) migrated their transaction workflows to eliminate a homegrown [SAGA](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-architecture.html) implementation. These are systems where correctness matters more than raw throughput.

Temporal is the wrong choice for:

- Simple request-response APIs - the overhead of workflow persistence is not warranted
- High-throughput event streaming - [Kafka](https://kafka.apache.org/) or [Flink](https://flink.apache.org/) handle millions of events per second; Temporal is not a stream processor
- CPU-bound compute that needs low scheduling latency - the round-trip through Temporal’s task queue adds overhead
- Stateless, short-lived jobs that can trivially restart from scratch

## Footnote

*Temporal is a* *[durable execution](https://docs.temporal.io/concepts/what-is-durable-execution)* platform that makes long-running, multi-step distributed processes reliable by persisting workflow state as an append-only [event history](https://docs.temporal.io/concepts/what-is-an-event-history) and [replaying](https://docs.temporal.io/concepts/what-is-a-replay) it on failure. Its core primitives - [Workflows](https://docs.temporal.io/workflows) for orchestration logic, [Activities](https://docs.temporal.io/activities) for external side effects, [Signals](https://docs.temporal.io/concepts/what-is-a-signal) for event-driven interaction, [Timers](https://docs.temporal.io/concepts/what-is-a-timer) for durable sleep, and [Child Workflows](https://docs.temporal.io/concepts/what-is-a-child-workflow-execution) for composition - eliminate entire categories of infrastructure that engineers otherwise build by hand. [Determinism](https://docs.temporal.io/workflows#deterministic-constraints) is the key constraint: workflow code must produce the same decisions given the same history, which requires all non-deterministic operations to live in Activities. The pattern is used in production for agentic workflows, payment processing, deployment pipelines, incident management, and data workflows at companies including [Stripe](https://stripe.com/), [Netflix](https://netflixtechblog.com/), [Coinbase](https://www.coinbase.com/), and [Datadog](https://www.datadoghq.com/).

---

If you find this helpful and interesting,

- share it on [HackerNews](https://news.ycombinator.com/submitlink?u=https%3A%2F%2Farpitbhayani.me%2Fblogs%2Ftemporal-primer%2F&t=Temporal%20Primer%20-%20Building%20Long-Running%20Systems)
- subscribe to my [RSS feed](https://arpitbhayani.me/rss.xml) and get notified the moment I publish a new one.
