# 13. Monitoring Kafka

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## Metric Basics

| Cue / Question | Notes |
| --- | --- |
| Where do Kafka's metrics come from, and how are they exposed (JMX; scrape via an agent on the broker rather than remote JMX — why?)? | |
| Which metrics can't come from Kafka itself (infrastructure/OS, synthetic clients, client-side measurements)? | |
| How does the audience change which metrics you keep (alerting vs debugging; automation tolerates volume, humans get alert fatigue; historical retention)? | |
| How do you health-check a broker (external probe that it responds, or detect stale/absent metrics), and what's the trade-off? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Service-Level Objectives

| Cue / Question | Notes |
| --- | --- |
| How do SLI, SLO, and SLA differ, and who should each be visible to? | |
| What makes a good SLI (something clients actually experience — availability, latency, durability; measured client-side; event-based good/total ratios over quantiles)? | |
| Why alert on SLO burn rate instead of raw metrics (catches what matters at the rate it matters; underlying metrics become diagnostics, not pages)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Kafka Broker Metrics

| Cue / Question | Notes |
| --- | --- |
| Why is broker monitoring tricky to interpret (cluster vs host-level problems, load imbalance, config drift, or the apps on top)? | |
| What do under-replicated partitions (URPs) indicate, and why does the 2nd edition demote them from "the one alert" (too many false positives/sawtooth; prefer SLO alerting)? | |
| How do you read URP patterns (steady count = likely a down broker or unbalanced assignment; fluctuating = resource/perf problem) and drill down (`kafka-topics.sh --describe --under-replicated-partitions`)? | |
| What should active controller count sum to across the cluster, and what do 0 or 2 mean (exactly 1; none elected vs split brain)? | |
| What do controller event queue size and request handler idle ratio tell you (queue should return to baseline; idle ratio below ~20% warning, ~10% active problem)? | |
| Which throughput/balance metrics matter (all-topics bytes in/out, messages in; partition count and leader count balance; offline partitions must be 0)? | |
| Which phases make up total request time (request queue, local, remote, throttle, response queue, response send) and why watch percentiles per request type? | |
| What are topic- and partition-level metrics good for (per-topic growth, chargeback, finding hot partitions), and why not alert on all of them? | |
| What should you watch in the JVM and OS (GC counts/times, CPU si/sys, memory & swap, disk util and iowait, network throughput)? | |
| Which loggers deserve separate files (kafka.controller, kafka.server.ClientQuotaManager at INFO; kafka.log.LogCleaner for compaction health)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Client Monitoring

| Cue / Question | Notes |
| --- | --- |
| Which producer metric is the clearest alert candidate (`record-error-rate` — records that exhausted retries and were dropped)? | |
| Which producer metrics explain throughput/latency (`request-latency-avg`, byte/record/request rates, `batch-size-avg`, records-per-request), and what does shrinking batch size hint at? | |
| Which consumer metrics matter (`fetch-latency-avg`, fetch/records rates, bytes-consumed), and why is `fetch-latency-avg` noisy (`fetch.max.wait.ms` idle waits)? | |
| What do the consumer coordinator metrics reveal (sync time/rate = rebalance pauses, commit latency), and what per-partition metrics exist? | |
| How do quotas surface on the client (broker delays responses instead of erroring — watch throttle-time metrics)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Lag Monitoring

| Cue / Question | Notes |
| --- | --- |
| Why is external lag monitoring preferred over the consumer's own `records-lag-max` (a stuck/dead consumer stops reporting; max hides the other partitions)? | |
| How does Burrow assess consumer health (evaluates offset progress vs lag across all partitions into a group status, no thresholds to tune)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## End-to-End Monitoring

| Cue / Question | Notes |
| --- | --- |
| What question does end-to-end monitoring answer that broker metrics can't ("can clients actually produce and consume messages?")? | |
| How do synthetic-client tools like Xinfra Monitor (Kafka Monitor) work (continuously produce/consume to a canary topic, measure availability and latency)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw: metrics pipeline — broker JMX + OS stats --> agent --> monitoring system --> SLO burn-rate alerts (page) vs dashboards/diagnostics ; synthetic client produce/consume loop measuring end-to-end
flowchart LR
```
