---
title: "Distributed Spring Batch Without a Message Broker"
source: "https://www.infoq.com/articles/spring-batch-without-broker/?utm_source=notification_email&utm_campaign=notifications&utm_medium=link&utm_content=&utm_term=daily"
author:
  - "[[Janardhan Reddy Chejarla]]"
published: 2026-10-21
created: 2026-10-22
description: "A brokerless design for distributed, fault-tolerant Spring Batch involves coordinate partitioning, claiming, and failover across a small-to-medium cluster using only the shared database."
tags:
  - "clippings"
---

> [!summary]
> An InfoQ article on a brokerless alternative to Spring Batch remote partitioning that coordinates a small-to-medium cluster (roughly 2-20 nodes) through the shared job-repository database alone. Three extra tables (a heartbeating node registry, partition lifecycle, per-job coordination) back a custom `PartitionHandler` and a live-node-aware `Partitioner`: the launching node is that job's master, partitions are preassigned round-robin or least-loaded, and a guarded compare-and-set UPDATE prevents double execution. Two-phase heartbeat failover (unreachable at ~10s, removed at ~30s) reassigns partitions declared transferable (idempotent) and fails the rest, and the author covers fencing limits, idempotent restarts, the database-contention ceiling, and when a broker is still the better tool.

[Java](https://www.infoq.com/java/ "Java")

[QCon San Francisco (Nov 16-20): Deep technical sessions. Peer conversations that change how you think.](https://qconsf.com/?utm_source=infoq&utm_medium=referral&utm_campaign=infoqyellowbox_qsf26)

Listen to this article - 25:19

## Introduction

[Spring Batch](https://spring.io/projects/spring-batch) has been the default framework for batch processing on the JVM for more than a decade. Jobs are built from steps, such as chunk-oriented readers, processors, and writers, with a metadata repository that makes runs restartable. For the nightly extract, transform, load (ETL), financial reconciliation, and data-validation workloads on a single machine, it is hard to beat.

The pressure appears when one machine is no longer enough. A reconciliation run that once fit inside its window grows with the business until it does not and the natural response is to spread the work across nodes. The established answer from Spring Batch is remote partitioning. A manager step divides the work into partitions and dispatches them to workers over a message broker such as [Apache Kafka](https://kafka.apache.org/), [RabbitMQ](https://www.rabbitmq.com/), or a JMS provider, via [Spring Integration](https://spring.io/projects/spring-integration).

Remote partitioning is a proven approach. When a broker is already part of the platform it is the right one. But a broker is an extra operational tier and many teams would otherwise never run one. They already operate a well-managed relational database (Spring Batch requires one for its job repository regardless). Teams have little appetite for standing up, securing, and monitoring a messaging cluster solely to fan out batch partitions.

This article describes an alternative for that common case: coordinating a distributed, fault-tolerant Spring Batch job across a small-to-medium cluster using only the shared database. It is not an argument against brokers, but an account of what it takes to remove one from this job, where the approach’s boundaries lie and where a broker is still the better tool.

## Where Single-Node Batch Ends and the Broker Question Begins

If you reduce the distributed batch to its essentials, four questions need to be answered through whatever your coordination.

First, how is the work divided and across how many workers? Split too coarsely and nodes sit idle; split too finely and overhead grows for nothing. The right number depends on how much capacity exists when the job starts.

Second, who is in charge of a given run? Something has to split the work, track it to completion, and finalize the job. In broker-based partitioning, that is the node running the manager step.

Third, how does a worker take ownership of a partition without a second worker also running it? Run it twice and you can corrupt data. Run it zero times and the job is silently incomplete.

Fourth, what happens when a node dies mid-run? Its in-flight work has to be detected and, where safe, recovered automatically, without violating the third requirement.

A broker answers some of these questions for you. Its queue hands each message to a single consumer and dispatch is decoupled from execution, so a slow or dead worker does not stall the producer. Take the broker away and every question has to be explicitly answered, in SQL, against a store built for durable shared state rather than message dispatch. The rest of this article is about answering them well.

## Structuring Database-Coordinated Partitioning

The design treats the database Spring Batch already needs as the sole coordination plan without broker or coordination service such as [Apache ZooKeeper](https://zookeeper.apache.org/) and no deployment platform. Every piece of cluster state lives in ordinary SQL tables, so the whole cluster is inspectable with a `SELECT` statement.

Three tables augment Spring Batch’s own schema. The `BATCH_NODES` table is the node registry, having one row per node, with its status (active or unreachable), its last heartbeat timestamp, and its current load. The `BATCH_PARTITIONS` table tracks the partition lifecycle, having one row per partition and keyed by that partition’s own step-execution ID (each partition is itself a Spring Batch `StepExecution`, distinct from the manager step that scopes the run), with its assigned node, its status (pending, claimed, completed, or failed), and whether or not it may be transferred to another node on failure. The `BATCH_JOB_COORDINATION` table binds each job execution to its master node and manager step, with a status of its own. What matters here is the shape of these three tables, not their full column lists.

One thing this design does not remove is the need for a shared, persistent job repository, but that requirement is intrinsic to distributed partitioning, not something added by this pattern. A partition’s payload, the execution context describing its slice of work, is written by the master and read back by whichever node executes it. The master then reads the result back to be aggregated. That handoff is a cross-JVM exchange of Spring Batch metadata, so the store has to be shared and durable. Spring Batch’s own remote partitioning imposes the same requirement. There, the broker carries only a pointer to the partition, never its data. What this design removes is the broker, not the repository. The one shared database serves as both the metadata store and the coordination plane.

Coordination is decentralized by design. There is no standing master elected for the whole cluster. That approach would reintroduce the leader-election machinery and single point of failure that dropping the broker avoids. Instead, the node that launches a job becomes that job’s master, for that execution only (a later section walks through what it does). Two jobs launched on two different nodes have two different masters running at the same time. Because mastership is scoped to a single job execution, losing a master affects only that one job, never the cluster. There is no coordinator to elect and none to lose.

## Reusing Spring Batch’s Partitioning Hooks: The Entry Point

For a Spring Batch developer the first question is practical: Where does my code plug in and how much of it changes? The answer is almost none, which makes the approach usable. That simplicity falls out of an extension point Spring Batch has always had.

Spring Batch already splits a partitioned step into two independent responsibilities. A `Partitioner` interface decides how work is split. It produces a set of named `ExecutionContext` objects, one per partition, each describing a slice of the input. A separate `PartitionHandler` decides how those partitions are executed. The built-in `TaskExecutorPartitionHandler` runs them in local threads, while Spring Batch’s own remote partitioning swaps in a `MessageChannelPartitionHandler` that ships them over a broker. The manager step is assembled from these two pieces plus a `StepExecutionAggregator` that combines the results:

```java
new StepBuilder("reconcileStep.manager", jobRepository)
    .partitioner("reconcileStep", clusterAwarePartitioner) // how work is split
    .partitionHandler(clusterAwarePartitionHandler)         // how partitions are distributed
    .step(reconcileStep)                                    // the ordinary worker step
    .aggregator(aggregator)
    .build();
```

That `partitionHandler(...)` line is the whole seam. Because Spring Batch treats partition distribution as a pluggable strategy, this approach supplies its own `PartitionHandler`, one that writes partition rows to the database and monitors them in the slot the broker-backed handler would otherwise occupy. The partitioner is a subclass of Spring Batch’s own `Partitioner`. Nothing else moves. The worker step (`reconcileStep` above) is an ordinary chunk- or tasklet-based step, results aggregate through the standard `StepExecutionAggregator`, and a restart works through the standard `JobRepository`. A developer comfortable with local partitioning writes the same manager step and changes exactly two beans, the `Partitioner` and the `PartitionHandler`.

That covers the manager. Turning the same deployable into a cluster member is configuration, not code. A single flag enables the behavior with auto-configuration registering the node, starting its heartbeat, and starting a poller, without either a broker client or extra beans. A few intervals tune that behavior, including heartbeat cadence, worker poll cadence, per-node concurrency, and the two heartbeat-age thresholds that drive failover, with production-sane defaults (a node is marked as unreachable at about ten seconds and removed at about thirty seconds).

From then on, every node, master and workers alike, runs one loop. On startup it inserts itself into the `BATCH_NODES` table and heartbeats on the configured interval, publishing its current load, which is the number of partitions it is running right now. On each poll, it scans the `BATCH_PARTITIONS` table for rows assigned to it, claims them with the compare-and-set update shown later, and then does the one thing that keeps the programming model intact: It looks up the worker step by name and runs it. That name is not arbitrary. It is the name passed to the `.partitioner("reconcileStep", ...)` method on the manager, recorded in the coordination row, so the worker resolves the same Spring Batch step bean and executes it with the partition’s `ExecutionContext`. Each node runs up to a configured number of partitions at once and when a step finishes it records it as `COMPLETED` or `FAILED`.

So the coordination lives behind extension points Spring Batch already asks you to implement, turned on by configuration rather than new code.

## Implementing It on a Spring Batch Cluster

![](https://imgopt.infoq.com/fit-in/3000x4000/filters:quality(85)/filters:no_upscale()/articles/spring-batch-without-broker/en/resources/1Figure-1-Architecture-a-per-job-master-and-worker-nodes-coordinating-through-the-shared-database-1792420793741.jpg)

**Figure 1. Architecture, a per-job master and worker nodes coordinating through the shared database. (Source: created by author.)**

Figure 1 shows the runtime shape. A standing set of peer JVM nodes each register in the `BATCH_NODES` table and heartbeat. When a job is launched on one of them, that node acts as master for that run. It queries the live nodes, sizes the split to them, writes the partition rows, and monitors to completion, while every node, master included, polls for and executes the partitions assigned to it.

### How the Master Step Drives the Run

The master step is not exotic. It is an ordinary Spring Batch partitioned (manager) step, running on whichever node launched the job. What makes that node the master is where the `PartitionHandler` runs. When Spring Batch executes the manager step, it calls the handler’s `handle(...)` method on that node, and the database-backed `PartitionHandler` blocks there until the whole distributed run is finished.

Inside that single call, the master does four things in order. First it records the run, writing a new row in the `BATCH_JOB_COORDINATION` table that ties this job execution to the manager step’s execution ID as the run’s identity and marks it as `STARTED`. Then it writes one `PENDING` row per partition into the `BATCH_PARTITIONS` table, each tagged with the node to which it is assigned. Then it runs a monitor loop, waking on a short interval to reassign any partitions orphaned by a removed node (their assigned node is gone from the `BATCH_NODES` table) and to check whether any partition is still `PENDING` or `CLAIMED`. Finally, when nothing is outstanding, it fails the manager step if any partition ends as `FAILED`, otherwise it marks the coordination row as `COMPLETED`, hands the workers’ step executions to the `StepExecutionAggregator`, and finishes the job.

Notice what is absent. Workers never call the master and the master never calls the workers. Every decision the master makes, it makes by reading and writing these rows. That is why losing a master is contained rather than causing a cluster outage. Its state is in the database, not in the memory of a coordinator.

### Enterprise Scenario

Consider nightly financial reconciliation across dynamically provisioned cloud nodes. The dataset is large enough that if one node misses the batch window, a well-managed relational database is already in place. The operations team has no appetite for a broker purely for this workload. The same shape recurs in mid-sized ETL and in data-validation jobs where each partition is a slice of input that must be recoverable if a node dies. These are the conditions this pattern targets.

### Sizing Work to the Live Cluster

Standard remote partitioning splits work before it knows how much capacity exists to run it. The grid size is chosen blind, often as a fixed constant, and the pieces are dispatched into the broker to be picked up as capacity frees. Without a broker, you have to face this issue directly. Before splitting, the master asks the database which nodes are currently alive and passes that count into the partitioner. The partitioner exposes one method that takes this live node count and returns the partitions, so the split is sized to the cluster that actually exists at that instant.

Each partition is expressed as a Spring Batch `ExecutionContext`, the framework’s key-value carrier for a partition’s input. The parameters that define one slice of work (a row range, a file name, and an ID window) go in and the worker step reads them back to know what to process. Because the partitioner is handed the live count, it can choose the partition count for the cluster at hand, using either one or two per live node or whatever the workload calls for.

An assignment strategy then maps those partitions onto nodes: round-robin for even distribution and fixed-node-count to confine a job to n nodes, or least-loaded, which places each partition on the node reporting the lowest current load and steers work toward the nodes that are most idle. Because assignment is both capacity-sized and load-aware, the split matches the cluster that exists instead of a number fixed in advance. Assignment is fixed at that point. It is placement, rather than runtime rebalancing, so a node that finishes early does not pull partitions from a slower peer and only node failure moves work. That runtime rebalancing is one thing a broker’s pull semantics give for free and this trades away.

### Claiming Work Without Double-Execution

Once partitions are written and assigned, each worker independently polls for its PENDING partitions and transitions them to `CLAIMED` before executing. That transition is the correctness-critical moment, a single guarded statement that drives every worker transition, with the target status passed in as a parameter.

```sql
-- claim, then later complete or fail: one guarded UPDATE
UPDATE batch_partitions
SET    status = ?,                 -- CLAIMED, then COMPLETED or FAILED
       last_updated = CURRENT_TIMESTAMP
WHERE  step_execution_id = ?
  AND  assigned_node = ?
  AND  status IN ('PENDING', 'CLAIMED');
```

The `WHERE` clause is the whole point. It explains why `CLAIMED` appears on both sides. It admits only a row that is still `PENDING` or `CLAIMED`, so once a partition reaches a terminal state (`COMPLETED` or `FAILED`) or is reassigned, no late write can move it. For the claim, the row starts as `PENDING`. Also, allowing `CLAIMED` makes a reclaim idempotent and allows the same statement to carry the later `COMPLETED` and `FAILED` writes, which start from `CLAIMED`.

Two properties then prevent double execution. First, each partition is assigned to exactly one node at partition time, so under normal operation only that node polls for its row. Second, both the worker’s write and the master’s reassignment are guarded. The worker’s write is guarded by the `assigned_node` and the `PENDING` / `CLAIMED` status, the reassignment is guarded by that status as it moves the row back to PENDING under a new node. So if a stalled node completes its partition just as the master reassigns it, the second write matches nothing. If the master went first, the completion fails because `assigned_node` no longer points to that node. If the node went first, the reassignment fails because the status is already terminal. Either way, exactly one write takes effect. This is not a contended pull-queue with `SELECT ... FOR UPDATE SKIP LOCKED` statements. Partitions are preassigned, so the guarded update governs the lifecycle, not the dispatch. The one-partition-one-node guarantee a broker gives through its queue here comes from row-level state transitions.

### Recovering From Node Failure

![](https://imgopt.infoq.com/fit-in/3000x4000/filters:quality(85)/filters:no_upscale()/articles/spring-batch-without-broker/en/resources/2Figure-2-Node-lifecycle-and-two-phase-failover-1792421365224.jpg)

**Figure 2. Node lifecycle and two-phase failover. (Source: created by author.)**

Nodes fail. Liveness here is tracked directly rather than inferred from broker acknowledgements. Every node updates a heartbeat timestamp on an interval, using the database clock rather than its own. The staleness check compares against that same clock, so liveness is unaffected by skew between the machines’ own clocks. Detection and removal are decentralized. Every node runs the cleanup sweeps, so no single monitor’s death blinds the cluster. Reassigning a removed node’s partitions, though, is done by each affected job’s own master in the monitor loop described earlier.

Recovery is a two-phase process, as shown in Figure 2. In phase one, a node whose heartbeat is older than the unreachable threshold (ten seconds by default) is flipped from active to unreachable. In phase two, a node that is still stale past the longer cleanup threshold (thirty seconds) is removed. Its incomplete partitions are resolved by contract. Transferable partitions become eligible for reassignment and non-transferable partitions are marked as `FAILED` so the job fails cleanly rather than risking a second run. The gap between the thresholds is a grace period window and is there on purpose. A brief garbage collection pause or network blip marks a node as unreachable without taking its work and it recovers on its next heartbeat. Only sustained absence escalates to removal. Reassignment reuses the same compare-and-set discipline as claiming, so a partition that has reached `COMPLETED` in the meantime is never resurrected.

## Best Practices and Gotchas: Making Database Coordination Production-Ready

### Treat Transferability as a Contract, Not a Hint

The most consequential design decision is that transferability is declared, not inferred. Each partition carries one bit of metadata. If the node running the partition dies, is that work safe to rerun elsewhere? The partitioner implementation marks each partition as transferable or not, with the framework following that marking exactly rather than deciding on its own. (In the reference implementation it is a method the partitioner overrides.)

Transferable partitions assert the work is idempotent and safe to rerun, an at-least-once guarantee. On node loss, a partition is reassigned and may run twice. Non-transferable partitions assert the opposite, at-most-once. On node loss a partition is failed rather than moved and is never run elsewhere. Summing a numeric range is transferable, but appending to an external ledger or calling a pay-once API is not. This choice is a correctness contract, so decide per partition on whether the work is idempotent.

### Rely on Fencing, but Do Not Trust It Alone

A node that loses its own heartbeat stops claiming work and aborts before running a claimed partition, leaving it for the master to reassign. This fencing shrinks the window in which two nodes run the same transferable partition, but it is best effort. A hard-paused JVM can wake and finish work already reassigned, so transferable work must be truly idempotent. What the system never relaxes is that no partition is silently lost. The partition either completes, or the job fails.

### Design Restarts to Be Idempotent

Worker failure is automatic, but master failure is harder. When a surviving node finds a coordination row still in flight whose master has left, it atomically claims the stranded job and marks it as failed, so the job is cleanly restartable rather than being stuck forever. Recovery is fail-and-restart, not resume-in-place, so a job can restart even when its master has died after every partition completed but before finalizing. Restarts must therefore be idempotent. This requirement also binds the at-most-once guarantee to a single execution. A lost master forces a restart while its workers may still be finishing, so non-transferable work that must survive one needs a reconciliation step on restart. Automatic takeover, resuming a job without a restart, is on the roadmap. The open work is making that takeover safe when two nodes could otherwise both act as the master.

### Run the Database Like a Critical Dependency

Once the database is the coordination plane, it is a hard dependency for the whole cluster, so run it replicated with backup and failover suited to the workload. The payoff for this design is that all coordination states are plain SQL. You diagnose a stuck run with a `SELECT` statement against the `BATCH_PARTITIONS` table rather than a broker console. Index the hot polling and completion-scan queries so they never fall to table scans.

### Know Where the Ceiling Is

The pattern targets roughly two to twenty nodes and the ceiling is database contention, not a fixed node count. Heartbeats, polling, and status updates are all database traffic. That traffic is modest on a small-to-medium cluster, but it grows with node count and job concurrency until it competes with the batch workload for the same connection pool and I/O. Validate the range under your own load.

## Trade-offs: When to Use Database Coordination and When to Reach for a Broker

Database coordination is not a universal replacement for broker-based partitioning. Choose it when the database is already present and well-managed, when operational simplicity and cost matter more than raw scale, when adding messaging middleware is impractical (constrained environments, limited operations capacity, and portability across clouds) and when the cluster sits in the small-to-medium range.

Reach for a broker when the cluster grows past that range into many dozens of nodes, when sub-second coordination latency is required, when the batch platform already shares a mature streaming backbone with other workloads, or when the work maps naturally onto the broker’s delivery and ordering semantics. The shared database also becomes a dependency you must manage at a high standard. If that approach is unrealistic, a broker’s separation of concerns may serve better.

It helps to place the database-coordinated approach against its neighbors. Spring Batch’s own remote partitioning dispatches over a broker with no built-in awareness of how many workers are live and no automatic reassignment when a worker dies after receiving a partition, which are the gaps this pattern closes. The Spring Cloud [Task](https://docs.spring.io/spring-cloud-task/docs/current/reference/html/) deployer-based partition handler is also broker-free, but it provisions a worker per partition through a platform such as Kubernetes, whereas this pattern coordinates a standing cluster of peer JVM nodes that poll for work. Database-coordinated schedulers such as [Quartz](https://www.quartz-scheduler.org/), [db-scheduler](https://github.com/kagkarlsson/db-scheduler), and [JobRunr](https://www.jobrunr.io/) share the instinct of coordinating through a database and failing over on node loss, but they target scheduling or general background jobs rather than Spring Batch partitioned-step execution.

## Conclusion

Removing the broker from distributed Spring Batch does not delete a requirement so much as move it into SQL. The same four questions a broker answers implicitly (sizing, coordination, single ownership, and node failure) get explicit answers: a live-node count feeding the partitioner, a per-job master with no standing coordinator, compare-and-set lifecycle transitions, and a two-phase heartbeat failover. The payoff is horizontal scaling and automatic recovery with nothing in the stack beyond the database Spring Batch already required.

The database is already there and is put to work for the common case where a broker would only add moving parts. The database has a real ceiling. Knowing where that ceiling sits is most useful. The takeaway is that a relational database used as a coordination plane is enough to run correct, fault-tolerant distributed batches for the many teams whose scale never demanded a broker.

**Author’s Note**

The design described here is drawn from `spring-batch-db-cluster-partitioning`, an open-source framework the author built and maintains, which was peer-reviewed and published in the *Journal of Open Source Software*. It is the worked example because it is the implementation the author knows in full detail; the patterns transfer whether a reader adopts it or builds their own. The full multi-database schemas, code, and a runnable multi-node example are available in the [open-source repository](https://github.com/jchejarla/spring-batch-db-cluster-partitioning).
