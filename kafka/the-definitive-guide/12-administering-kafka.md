# 12. Administering Kafka

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## Topic Operations

| Cue / Question | Notes |
| --- | --- |
| Which tool manages topics, and how does it connect to the cluster (`kafka-topics.sh --bootstrap-server`, not ZooKeeper anymore)? | |
| How do you create a topic, and which arguments are required (`--create --topic --partitions --replication-factor`)? | |
| What topic-naming pitfalls should you avoid (`.` vs `_` collide in metric names; double-underscore prefix is reserved for internal topics)? | |
| Which `--describe` filters help find problem topics (`--under-replicated-partitions`, `--at-min-isr-partitions`, `--under-min-isr-partitions`, `--unavailable-partitions`, `--topics-with-overrides`)? | |
| Why is adding partitions risky for keyed topics (key-to-partition mapping changes, ordering per key breaks)? | |
| Why can't you reduce partition count, and what's the alternative (delete and recreate the topic)? | |
| What actually happens when you delete a topic (asynchronous "marked for deletion"; requires `delete.topic.enable=true`; no reversal)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Consumer Groups

| Cue / Question | Notes |
| --- | --- |
| How do you list and describe groups, and what do the describe fields mean (`kafka-consumer-groups.sh`; current-offset, log-end-offset, lag, consumer-id, host)? | |
| When can you delete a group or its offsets (only when the group has no active members)? | |
| How do you reset a group's offsets safely (export to CSV first; `--reset-offsets --dry-run` before `--execute`; group must be stopped)? | |
| Which reset targets exist and when would you use each (`--to-earliest`, `--to-latest`, `--to-offset`, `--to-datetime`, `--shift-by`)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Dynamic Configuration Changes

| Cue / Question | Notes |
| --- | --- |
| Which entity types can `kafka-configs.sh` override at runtime (topics, brokers, users, clients)? | |
| How do you override a topic config, e.g. retention (`--alter --entity-type topics --add-config retention.ms=...`)? | |
| How are client/user quotas expressed (`producer_byte_rate`, `consumer_byte_rate`, request percentage — per broker, not per cluster)? | |
| Why are dynamic broker config overrides useful (change without restart; per-broker or cluster-wide default)? | |
| How do you see and remove overrides (`--describe`; `--alter --delete-config`) — and why should you check before assuming defaults apply? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Producing and Consuming

| Cue / Question | Notes |
| --- | --- |
| When are the console producer/consumer the right tool, and when not (ad-hoc checks and debugging — not production data flows)? | |
| Which console-producer options matter (key serialization with `--property key.separator/parse.key`, `--producer-property` pass-through)? | |
| Which console-consumer options matter (`--from-beginning`, `--max-messages`, `--partition`, formatters)? | |
| How can you inspect `__consumer_offsets` directly (consume it with the OffsetsMessageFormatter)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Partition Management

| Cue / Question | Notes |
| --- | --- |
| What is a preferred replica election and why is it needed (leadership drifts after broker failures; `kafka-leader-election.sh`; `auto.leader.rebalance.enable`)? | |
| When do you reassign partitions (broker imbalance, adding/removing brokers, rack changes), and what's the 3-step flow (`kafka-reassign-partitions.sh --generate` / `--execute` / `--verify`)? | |
| What impact does reassignment have on the cluster, and how do you limit it (replication traffic and page-cache churn; `--throttle`, remember to remove the throttle; `--cancel` to abort)? | |
| What tricks make large reassignments safer (batch by topic/partition subsets; move leadership first; save the current assignment JSON as rollback)? | |
| What are `kafka-dump-log.sh` and `kafka-replica-verification.sh` for (inspecting segment contents / index sanity; verifying replicas match — but it hits the cluster hard)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Other Tools

| Cue / Question | Notes |
| --- | --- |
| Which other CLI tools ship with Kafka and what's each for (`kafka-acls.sh` for security, MirrorMaker for replication, `kafka-*-perf-test.sh` for load testing)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Unsafe Operations

| Cue / Question | Notes |
| --- | --- |
| How do you force a controller move, and when is it justified (delete the `/admin/controller` ZNode; only when the controller is wedged)? | |
| How do you clear a stuck topic deletion (remove the topic's ZNode under `/admin/delete_topics`), and what risk does that carry? | |
| What does deleting a topic manually require (all brokers stopped, delete ZK metadata, delete log dirs on every broker), and why is it a last resort? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw: partition reassignment flow — current assignment --> --generate proposal --> --execute (throttled replication) --> --verify / remove throttle ; with rollback JSON saved before execute
flowchart LR
```
