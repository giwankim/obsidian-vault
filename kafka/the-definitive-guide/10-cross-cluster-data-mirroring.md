# 10. Cross-Cluster Data Mirroring

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## Use Cases of Cross-Cluster Mirroring

| Cue / Question | Notes |
| --- | --- |
| Which scenarios call for mirroring (regional → central aggregation, disaster recovery, cloud migration, edge-cluster aggregation, regulatory/data-residency constraints)? | |
| Why is mirroring different from replication within a cluster (asynchronous, between independent clusters, tolerates lag)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Multicluster Architectures

| Cue / Question | Notes |
| --- | --- |
| What realities of cross-datacenter networks shape every architecture (high latency, limited bandwidth, higher cost — never span one cluster's brokers across DCs over WAN)? | |
| Why is remote *consuming* preferred over remote *producing* (on network partition, data stays safe in the source cluster and the consumer just retries)? | |
| Hub-and-spoke: what does it buy you and what's the limitation (data produced locally, mirrored once to the center; one region can't see another region's data)? | |
| Active-active: what are the benefits (serve users nearby, redundancy, no idle hardware) and the hard problems (async conflicts, keeping users sticky to one DC, replication loops — avoided with namespaces/prefixes)? | |
| Active-standby: why is failover the hard part (data loss vs duplicates, offset translation for consumers, client redirection, unplanned failback)? | |
| What do stretch clusters require to be viable (2.5/3 nearby DCs, low latency, rack-aware replica placement, synchronous replication semantics)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Apache Kafka's MirrorMaker

| Cue / Question | Notes |
| --- | --- |
| Why did MirrorMaker 2 replace MM1 (built on Connect; preserves topic configs and partitions; offset translation; prevents replication cycles via `source.topic` remote naming)? | |
| How do you configure MM2 (clusters and replication flows, topic include/exclude regex, heartbeats and checkpoints)? | |
| How does consumer failover work across clusters (checkpoint topic + `RemoteClusterUtils`/automatic offset sync translate committed offsets to the target cluster)? | |
| Where should MirrorMaker run and why (in/near the *target* DC — consume remotely, produce locally)? | |
| What do you tune and monitor in production (Connect task count, producer/consumer throughput configs, TCP buffers for high-latency links; lag, connector task status, heartbeat-based end-to-end latency)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Other Cross-Cluster Mirroring Solutions

| Cue / Question | Notes |
| --- | --- |
| What problems do uReplicator (Uber) and Brooklin (LinkedIn) solve that stock MirrorMaker struggled with (rebalance churn, operating many pipelines, multi-system ingestion)? | |
| What do Confluent's options offer (Replicator for configs/schemas, Multi-Region Clusters with sync/async observers, Cluster Linking without extra infra)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw: pick one — hub-and-spoke (regional clusters --> central), active-active with prefixed topics both ways, or active-standby with MM2 checkpoints enabling consumer failover
flowchart LR
```
