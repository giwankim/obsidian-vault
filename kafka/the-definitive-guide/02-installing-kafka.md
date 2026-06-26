******# 2. Installing Kafka

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## Environment Setup

| Cue / Question                                                          | Notes                                                                                                                                                                                |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Why is Linux the recommended OS for running Kafka in production?        |                                                                                                                                                                                      |
| Which JDK/JRE version does Kafka need, and JDK vs. JRE — which and why? |                                                                                                                                                                                      |
| What role does ZooKeeper play for a Kafka cluster?                      | Stores metadata about the Kafka cluster, as well as consumer client details.                                                                                                         |
| What is a ZooKeeper *ensemble*, and why is the size always odd?         | ZooKeeper is designed to work as a cluster to ensure high availability.                                                                                                              |
| What is *quorum* and how many nodes can an ensemble lose?               | Majority of elements in an ensemble in order for ZooKeeper to respond to request. In three-node ensemble, can run with one node missing. With five-node ensemble, two nodes missing. |

**Summary:**
<!-- 1-2 sentences, your words -->

## Installing a Kafka Broker

| Cue / Question | Notes |
| --- | --- |
| What are the basic steps to install and start a single broker? | |
| How do you verify the broker is up before sending any data? | |
| How do you create a topic, then produce and consume a test message from the CLI? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Configuring the Broker

| Cue / Question | Notes |
| --- | --- |
| What must `broker.id` be, and what happens if two brokers share one? | |
| What do `listeners` / `advertised.listeners` control, and why does the advertised one matter to clients? | |
| What does `zookeeper.connect` point at, and what is the chroot path for? | |
| Why prefer multiple `log.dirs` over one, and how are partitions spread across them? | |
| What does `auto.create.topics.enable` do, and why disable it in production? | |
| `num.partitions` — what does it set, and why can't you easily decrease it later? | |
| Retention by time vs. size (`log.retention.ms` vs. `log.retention.bytes`) — how do they interact? | |
| What is a log *segment*, and how do `log.segment.bytes` / `log.roll.ms` govern it? | |
| What does `min.insync.replicas` protect against, and how does it pair with producer acks? | |
| What does `message.max.bytes` cap, and what must stay consistent on the consumer side? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Selecting Hardware

| Cue / Question | Notes |
| --- | --- |
| Why is disk *throughput* the key spec for producer latency? | |
| SSD vs. HDD — what's the trade-off for a Kafka broker? | |
| How do you estimate the disk *capacity* a broker needs? | |
| Why does Kafka lean on page cache, and how does that shape memory sizing? | |
| When does networking become the bottleneck for a cluster? | |
| Why is CPU usually the *least* constrained resource (and what consumes it)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Kafka in the Cloud

| Cue / Question | Notes |
| --- | --- |
| What general trade-off drives instance/disk choice in the cloud? | |
| Azure — how do managed disks change the disk-vs-memory calculus? | |
| AWS — how do you match instance type and EBS to the workload? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Configuring Kafka Clusters

| Cue / Question | Notes |
| --- | --- |
| What factors decide *how many brokers* a cluster needs? | |
| Which broker configs must change when moving from one broker to a cluster? | |
| OS tuning — what virtual-memory settings (swappiness, dirty ratios) matter and why? | |
| Disk tuning — which filesystem/mount options help (e.g. `noatime`)? | |
| Networking tuning — which socket buffer settings should be raised? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Production Concerns

| Cue / Question | Notes |
| --- | --- |
| Why does the GC matter for Kafka, and what does G1GC tuning target? | |
| Datacenter layout — why spread brokers across racks/zones, and what config expresses that? | |
| What are the risks of colocating apps on the ZooKeeper ensemble? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw: client --> broker (log.dirs / segments) --> ZooKeeper ensemble; cluster of N brokers
flowchart LR
```
