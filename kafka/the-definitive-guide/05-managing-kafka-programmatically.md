# 5. Managing Apache Kafka Programmatically

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## AdminClient Overview

| Cue / Question | Notes |
| --- | --- |
| What problem does `AdminClient` solve vs. CLI tools or speaking the wire protocol directly? | |
| Why is the API asynchronous and *eventually consistent* — what is a `*Result` object / `KafkaFuture`? | |
| What do `*Options` parameters generally control? | |
| What does "flat hierarchy" mean for how the API is organized? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## AdminClient Lifecycle: Creating, Configuring, and Closing

| Cue / Question | Notes |
| --- | --- |
| How do you create, configure, and close an `AdminClient`, and why does `close()` take a timeout? | |
| `client.dns.lookup` — what does it change, and when does it matter? | |
| `request.timeout.ms` — what does it bound for admin calls? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Essential Topic Management

| Cue / Question | Notes |
| --- | --- |
| How do you list, create, describe, and delete topics programmatically? | |
| How do you check whether a topic exists and create-if-missing without a race? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Configuration Management

| Cue / Question | Notes |
| --- | --- |
| How do you read and alter topic/broker configs (`ConfigResource`, `incrementalAlterConfigs`)? | |
| Why prefer *incremental* alter over a full replace? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Consumer Group Management

| Cue / Question | Notes |
| --- | --- |
| How do you list and describe consumer groups and read their committed offsets? | |
| How do you modify (reset) a group's offsets, and what state must the group be in? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Cluster Metadata

| Cue / Question | Notes |
| --- | --- |
| How do you discover the cluster's brokers, the controller, and the topic/partition layout? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Advanced Admin Operations

| Cue / Question | Notes |
| --- | --- |
| Adding partitions — why is it disruptive for keyed topics (breaks key → partition mapping)? | |
| Deleting records — what does `deleteRecords` actually do (advances the low-water mark)? | |
| Leader election — preferred vs. unclean, and when do you trigger each? | |
| Reassigning replicas — what does it move, and what's the cost (network/disk load)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Testing

| Cue / Question | Notes |
| --- | --- |
| What does `MockAdminClient` enable for unit tests, and where are its limits? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw: app --> AdminClient --> (async *Result / KafkaFuture) --> controller --> brokers
flowchart LR
```
