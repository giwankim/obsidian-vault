---
title: "Dead Letter Queue Patterns in Apache Flink"
source: "https://dzone.com/articles/flink-dlq-patterns?utm_source=substack&utm_medium=email"
author:
  - "[[Rohit Muthyala]]"
published: 2026-07-02
created: 2026-07-06
description: "Prevent Apache Flink restart loops with production-ready DLQ patterns using side outputs, retries, tiered routing, durable sinks, metrics, and replay jobs."
tags:
  - "clippings"
---

> [!summary]
> Six production-ready dead letter queue patterns for Apache Flink 1.18 that stop poison messages from triggering endless restart loops: side outputs as the core DLQ primitive, retry with exponential backoff via checkpointed timers, tiered routing by failure class, Kafka vs S3 sink selection, DLQ-rate metrics and alerting, and replay through a dedicated reprocessing job. Includes Java and PyFlink examples plus a production checklist. The core rule: a bad message should never silently disappear, and it should never silently stop the stream.

Join the DZone community and get the full member experience.

[Join For Free](https://dzone.com/static/registration.html)

Streaming systems usually fail in one of two ways:

- **Loudly**, when infrastructure breaks
- **Quietly**, when one bad record keeps replaying until the pipeline is effectively dead

The second failure mode is more dangerous because it often starts with something small: malformed JSON, an unexpected schema change, a missing required field, or a downstream timeout that was never handled correctly.

In [Apache Flink](https://dzone.com/articles/apache-flink-1), one unhandled exception can trigger a restart. If the same poison message is still sitting in Kafka after recovery, the job reads it again, fails again, restarts again, and enters a loop. At that point, the pipeline is technically "recovering," but operationally it is down.

This is exactly why production Flink jobs need a [Dead Letter Queue](https://dzone.com/articles/modern-queue-patterns-guide) (DLQ) strategy from day one.

A proper DLQ pattern does three things:

1. **Isolates** bad records so they do not stop good ones
2. **Captures** enough failure context to debug the issue later
3. **Preserves replayability** so quarantined records can be reprocessed after the root cause is fixed

Anything less is not really a DLQ. It is either silent data loss or delayed outage.

In this article, I will walk through the most practical DLQ patterns for Apache Flink 1.18:

- Side outputs as the core DLQ primitive
- Retry with exponential backoff for transient failures
- Tiered DLQ routing by error class
- Kafka and S3 sink patterns
- Metrics and alerting
- Replay with a dedicated reprocessing job
- A PyFlink version of the side output pattern

The goal is simple: **a bad message should never silently disappear, and it should never silently stop the stream**.

## Why Poison Messages Break Otherwise Healthy Pipelines

A poison message is any record that consistently fails processing.

Typical examples include:

- Malformed JSON
- Incompatible schema versions
- Missing required fields
- Invalid business values
- Records that trigger unexpected code paths
- Messages that repeatedly fail downstream enrichment calls

Without DLQ handling, the failure path usually looks like this:

1. The record enters the pipeline
2. Deserialization or validation throws an exception
3. The operator fails
4. Flink restarts from the last checkpoint
5. The same record is consumed again
6. The same exception happens again

That loop can continue indefinitely.

The result is predictable:

- Throughput drops to zero
- Downstream consumers starve
- Checkpoint recovery does not help
- On-call engineers get paged for a problem caused by one record

This is why DLQ handling is not just an error-handling convenience. It is a core reliability pattern.

## What a DLQ Should Look Like in Flink

In a streaming architecture, a DLQ is a durable destination for records that could not be processed successfully.

For Flink, that means the DLQ record should usually include:

- Raw payload
- Error type
- Error message
- Stack trace or summarized failure context
- Failure timestamp
- Source metadata such as topic, partition, or offset when available

That information matters because a DLQ is only useful if someone can answer two questions later:

1. **Why did this record fail?**
2. **How do I replay it safely once the issue is fixed?**

If you only log the exception, you lose replayability. If you only store the payload, you lose debugging context. If you drop the record entirely, you lose both.

So the design target is not "catch exceptions." The design target is durable, observable, replayable failure handling.

## Pattern 1: Use Side Outputs as the Core DLQ Primitive

The most natural DLQ mechanism in Flink is the **side output**.

A side output allows one operator to emit records to multiple streams:

- The main stream for successful records
- One or more side streams for failures, late data, or quarantined records

That makes it the right primitive for DLQ routing.

### Define the DLQ Envelope and Output Tag

Java

17

```text/x-java
import org.apache.flink.util.OutputTag;
```

```text/x-java
import org.apache.flink.streaming.api.functions.ProcessFunction;
```

```text/x-java
import org.apache.flink.util.Collector;
```

```text/x-java
​
```

```text/x-java
public static final OutputTag<DeadLetterRecord> DLQ_TAG =
```

```text/x-java
new OutputTag<DeadLetterRecord>("dead-letter-queue") {};
```

```text/x-java
​
```

```text/x-java
public record DeadLetterRecord(
```

```text/x-java
String rawPayload,
```

```text/x-java
String errorType,
```

```text/x-java
String errorMessage,
```

```text/x-java
String stackTrace,
```

```text/x-java
long failedAtEpochMs,
```

```text/x-java
String sourceTopicPartition,
```

```text/x-java
long sourceOffset
```

```text/x-java
) {}
```

```text/x-java
​
```

The important point here is that the DLQ record is not just the failed payload. It is an envelope that preserves enough context for triage and replay.

### Route Failures Inside a ProcessFunction

Java

61

```text/x-java
public class EntityEventProcessor
```

```text/x-java
extends ProcessFunction<String, EntityEvent> {
```

```text/x-java
​
```

```text/x-java
@Override
```

```text/x-java
public void processElement(
```

```text/x-java
String rawMessage,
```

```text/x-java
Context ctx,
```

```text/x-java
Collector<EntityEvent> out) {
```

```text/x-java
​
```

```text/x-java
try {
```

```text/x-java
EntityEvent event = parseAndValidate(rawMessage);
```

```text/x-java
out.collect(event);
```

```text/x-java
​
```

```text/x-java
} catch (JsonParseException e) {
```

```text/x-java
ctx.output(DLQ_TAG, new DeadLetterRecord(
```

```text/x-java
rawMessage,
```

```text/x-java
"JSON_PARSE_FAILURE",
```

```text/x-java
e.getMessage(),
```

```text/x-java
getStackTrace(e),
```

```text/x-java
System.currentTimeMillis(),
```

```text/x-java
ctx.element().toString(),
```

```text/x-java
-1L
```

```text/x-java
));
```

```text/x-java
​
```

```text/x-java
} catch (SchemaValidationException e) {
```

```text/x-java
ctx.output(DLQ_TAG, new DeadLetterRecord(
```

```text/x-java
rawMessage,
```

```text/x-java
"SCHEMA_VALIDATION_FAILURE",
```

```text/x-java
e.getMessage(),
```

```text/x-java
getStackTrace(e),
```

```text/x-java
System.currentTimeMillis(),
```

```text/x-java
ctx.element().toString(),
```

```text/x-java
-1L
```

```text/x-java
));
```

```text/x-java
​
```

```text/x-java
} catch (Exception e) {
```

```text/x-java
ctx.output(DLQ_TAG, new DeadLetterRecord(
```

```text/x-java
rawMessage,
```

```text/x-java
"UNKNOWN_FAILURE",
```

```text/x-java
e.getMessage(),
```

```text/x-java
getStackTrace(e),
```

```text/x-java
System.currentTimeMillis(),
```

```text/x-java
ctx.element().toString(),
```

```text/x-java
-1L
```

```text/x-java
));
```

```text/x-java
}
```

```text/x-java
}
```

```text/x-java
​
```

```text/x-java
private EntityEvent parseAndValidate(String raw)
```

```text/x-java
throws JsonParseException, SchemaValidationException {
```

```text/x-java
EntityEvent event = objectMapper.readValue(raw, EntityEvent.class);
```

```text/x-java
if (event.entityId() == null || event.entityId().isBlank()) {
```

```text/x-java
throw new SchemaValidationException("entityId is required");
```

```text/x-java
}
```

```text/x-java
if (event.timestamp() <= 0) {
```

```text/x-java
throw new SchemaValidationException("timestamp must be positive");
```

```text/x-java
}
```

```text/x-java
return event;
```

```text/x-java
}
```

```text/x-java
}
```

```text/x-java
​
```

This is the minimum viable DLQ pattern, and it already solves the most important operational problem: **bad records no longer stop good ones**.

### Wire the Main Stream and DLQ Stream

Java

19

```text/x-java
StreamExecutionEnvironment env =
```

```text/x-java
StreamExecutionEnvironment.getExecutionEnvironment();
```

```text/x-java
​
```

```text/x-java
DataStream<String> kafkaSource = env
```

```text/x-java
.fromSource(buildKafkaSource(), WatermarkStrategy.noWatermarks(),
```

```text/x-java
"entity-events-source");
```

```text/x-java
​
```

```text/x-java
SingleOutputStreamOperator<EntityEvent> processed =
```

```text/x-java
kafkaSource.process(new EntityEventProcessor());
```

```text/x-java
​
```

```text/x-java
DataStream<EntityEvent> goodEvents = processed;
```

```text/x-java
DataStream<DeadLetterRecord> deadLetters =
```

```text/x-java
processed.getSideOutput(DLQ_TAG);
```

```text/x-java
​
```

```text/x-java
goodEvents.sinkTo(buildDownstreamKafkaSink());
```

```text/x-java
deadLetters.sinkTo(buildDlqKafkaSink());
```

```text/x-java
​
```

```text/x-java
env.execute("Entity Resolution Pipeline");
```

```text/x-java
​
```

If you do nothing else, do this. Side outputs should be the default DLQ foundation in Flink.

## Pattern 2: Retry Transient Failures Before Escalating to DLQ

Not every failure belongs in the DLQ immediately.

Some failures are transient:

- A downstream service is temporarily unavailable
- A database call times out
- An external API is rate-limited
- A network dependency is briefly unstable

If you send all of those directly to the DLQ, you create noise and bury the truly bad records.

The better pattern is:

1. Retry transient failures a limited number of times
2. Use exponential backoff
3. Escalate to DLQ only after retries are exhausted

### Retry With KeyedProcessFunction and Timers

Java

107

```text/x-java
public class RetryingEnrichmentProcessor
```

```text/x-java
extends KeyedProcessFunction<String, EntityEvent, EnrichedEvent> {
```

```text/x-java
​
```

```text/x-java
private static final int MAX_RETRIES = 3;
```

```text/x-java
private static final long BASE_BACKOFF_MS = 500L;
```

```text/x-java
​
```

```text/x-java
private transient ValueState<Integer> retryCountState;
```

```text/x-java
private transient ValueState<EntityEvent> pendingEventState;
```

```text/x-java
​
```

```text/x-java
@Override
```

```text/x-java
public void open(Configuration parameters) {
```

```text/x-java
retryCountState = getRuntimeContext().getState(
```

```text/x-java
new ValueStateDescriptor<>("retry-count", Integer.class));
```

```text/x-java
pendingEventState = getRuntimeContext().getState(
```

```text/x-java
new ValueStateDescriptor<>("pending-event", EntityEvent.class));
```

```text/x-java
}
```

```text/x-java
​
```

```text/x-java
@Override
```

```text/x-java
public void processElement(
```

```text/x-java
EntityEvent event,
```

```text/x-java
Context ctx,
```

```text/x-java
Collector<EnrichedEvent> out) throws Exception {
```

```text/x-java
​
```

```text/x-java
try {
```

```text/x-java
EnrichedEvent enriched = callEnrichmentService(event);
```

```text/x-java
retryCountState.clear();
```

```text/x-java
pendingEventState.clear();
```

```text/x-java
out.collect(enriched);
```

```text/x-java
​
```

```text/x-java
} catch (TransientServiceException e) {
```

```text/x-java
int retries = retryCountState.value() == null
```

```text/x-java
? 0 : retryCountState.value();
```

```text/x-java
​
```

```text/x-java
if (retries >= MAX_RETRIES) {
```

```text/x-java
retryCountState.clear();
```

```text/x-java
pendingEventState.clear();
```

```text/x-java
ctx.output(DLQ_TAG, new DeadLetterRecord(
```

```text/x-java
event.toString(),
```

```text/x-java
"MAX_RETRIES_EXCEEDED",
```

```text/x-java
"Failed after " + MAX_RETRIES + " retries: " + e.getMessage(),
```

```text/x-java
getStackTrace(e),
```

```text/x-java
System.currentTimeMillis(),
```

```text/x-java
ctx.getCurrentKey(),
```

```text/x-java
-1L
```

```text/x-java
));
```

```text/x-java
} else {
```

```text/x-java
retryCountState.update(retries + 1);
```

```text/x-java
pendingEventState.update(event);
```

```text/x-java
long backoffMs = BASE_BACKOFF_MS * (long) Math.pow(2, retries);
```

```text/x-java
ctx.timerService().registerProcessingTimeTimer(
```

```text/x-java
System.currentTimeMillis() + backoffMs
```

```text/x-java
);
```

```text/x-java
}
```

```text/x-java
​
```

```text/x-java
} catch (PoisonMessageException e) {
```

```text/x-java
ctx.output(DLQ_TAG, new DeadLetterRecord(
```

```text/x-java
event.toString(),
```

```text/x-java
"POISON_MESSAGE",
```

```text/x-java
e.getMessage(),
```

```text/x-java
getStackTrace(e),
```

```text/x-java
System.currentTimeMillis(),
```

```text/x-java
ctx.getCurrentKey(),
```

```text/x-java
-1L
```

```text/x-java
));
```

```text/x-java
}
```

```text/x-java
}
```

```text/x-java
​
```

```text/x-java
@Override
```

```text/x-java
public void onTimer(
```

```text/x-java
long timestamp,
```

```text/x-java
OnTimerContext ctx,
```

```text/x-java
Collector<EnrichedEvent> out) throws Exception {
```

```text/x-java
​
```

```text/x-java
EntityEvent pending = pendingEventState.value();
```

```text/x-java
if (pending == null) return;
```

```text/x-java
​
```

```text/x-java
try {
```

```text/x-java
EnrichedEvent enriched = callEnrichmentService(pending);
```

```text/x-java
retryCountState.clear();
```

```text/x-java
pendingEventState.clear();
```

```text/x-java
out.collect(enriched);
```

```text/x-java
​
```

```text/x-java
} catch (TransientServiceException e) {
```

```text/x-java
int retries = retryCountState.value();
```

```text/x-java
if (retries >= MAX_RETRIES) {
```

```text/x-java
retryCountState.clear();
```

```text/x-java
pendingEventState.clear();
```

```text/x-java
ctx.output(DLQ_TAG, new DeadLetterRecord(
```

```text/x-java
pending.toString(),
```

```text/x-java
"MAX_RETRIES_EXCEEDED",
```

```text/x-java
"Timer retry exhausted: " + e.getMessage(),
```

```text/x-java
getStackTrace(e),
```

```text/x-java
System.currentTimeMillis(),
```

```text/x-java
ctx.getCurrentKey(),
```

```text/x-java
-1L
```

```text/x-java
));
```

```text/x-java
} else {
```

```text/x-java
retryCountState.update(retries + 1);
```

```text/x-java
long backoffMs = BASE_BACKOFF_MS * (long) Math.pow(2, retries);
```

```text/x-java
ctx.timerService().registerProcessingTimeTimer(
```

```text/x-java
timestamp + backoffMs
```

```text/x-java
);
```

```text/x-java
}
```

```text/x-java
}
```

```text/x-java
}
```

```text/x-java
}
```

```text/x-java
​
```

### Why This Works Especially Well in Flink

This pattern is stronger in Flink than in many other stream processors because timers and state are checkpointed.

That means:

- Retry counters survive restarts
- Pending events survive restarts
- Scheduled retries resume after recovery

In other words, the retry workflow itself is fault-tolerant.

That is exactly what you want when handling transient failures in a long-running stream.

## Pattern 3: Split the DLQ by Failure Type

Once a pipeline matures, a single DLQ topic usually becomes too coarse.

Schema failures, business validation failures, exhausted retries, and unknown exceptions all end up mixed together. That makes triage slower and replay harder.

A better pattern is to classify failures and route them to separate DLQ streams.

### Define Failure Tiers

Java

7

```text/x-java
public enum DlqTier {
```

```text/x-java
TRANSIENT_EXHAUSTED,
```

```text/x-java
SCHEMA_INVALID,
```

```text/x-java
BUSINESS_RULE,
```

```text/x-java
UNKNOWN
```

```text/x-java
}
```

```text/x-java
​
```

### Route by Exception Class

Java

33

```text/x-java
public class TieredDlqRouter
```

```text/x-java
extends ProcessFunction<String, EntityEvent> {
```

```text/x-java
​
```

```text/x-java
@Override
```

```text/x-java
public void processElement(
```

```text/x-java
String raw, Context ctx, Collector<EntityEvent> out) {
```

```text/x-java
​
```

```text/x-java
try {
```

```text/x-java
EntityEvent event = parse(raw);
```

```text/x-java
validate(event);
```

```text/x-java
out.collect(event);
```

```text/x-java
​
```

```text/x-java
} catch (JsonParseException | MappingException e) {
```

```text/x-java
route(ctx, raw, DlqTier.SCHEMA_INVALID, e);
```

```text/x-java
​
```

```text/x-java
} catch (BusinessValidationException e) {
```

```text/x-java
route(ctx, raw, DlqTier.BUSINESS_RULE, e);
```

```text/x-java
​
```

```text/x-java
} catch (Exception e) {
```

```text/x-java
route(ctx, raw, DlqTier.UNKNOWN, e);
```

```text/x-java
}
```

```text/x-java
}
```

```text/x-java
​
```

```text/x-java
private void route(Context ctx, String raw,
```

```text/x-java
DlqTier tier, Exception e) {
```

```text/x-java
OutputTag<DeadLetterRecord> tag = getTierTag(tier);
```

```text/x-java
ctx.output(tag, new DeadLetterRecord(
```

```text/x-java
raw, tier.name(), e.getMessage(),
```

```text/x-java
getStackTrace(e), System.currentTimeMillis(), "", -1L
```

```text/x-java
));
```

```text/x-java
}
```

```text/x-java
}
```

```text/x-java
​
```

### Define One Output Tag Per Tier

Java

7

```text/x-java
public static final OutputTag<DeadLetterRecord> DLQ_SCHEMA =
```

```text/x-java
new OutputTag<>("dlq-schema-invalid") {};
```

```text/x-java
public static final OutputTag<DeadLetterRecord> DLQ_BUSINESS =
```

```text/x-java
new OutputTag<>("dlq-business-rule") {};
```

```text/x-java
public static final OutputTag<DeadLetterRecord> DLQ_UNKNOWN =
```

```text/x-java
new OutputTag<>("dlq-unknown") {};
```

```text/x-java
​
```

### Sink Each Tier Independently

Java

x

```text/x-java
SingleOutputStreamOperator<EntityEvent> processed =
```

```text/x-java
kafkaSource.process(new TieredDlqRouter());
```

```text/x-java
​
```

```text/x-java
processed.getSideOutput(DLQ_SCHEMA)
```

```text/x-java
.sinkTo(buildKafkaSink("dlq.schema-invalid"));
```

```text/x-java
​
```

```text/x-java
processed.getSideOutput(DLQ_BUSINESS)
```

```text/x-java
.sinkTo(buildKafkaSink("dlq.business-rule"));
```

```text/x-java
​
```

```text/x-java
processed.getSideOutput(DLQ_UNKNOWN)
```

```text/x-java
.sinkTo(buildKafkaSink("dlq.unknown"));
```

```text/x-java
​
```

This makes the DLQ operationally useful instead of just technically correct.

For example:

- Schema failures can be routed to the producer team
- Business rule failures can feed data quality workflows
- Unknown failures can trigger higher-severity alerting

## Pattern 4: Choose DLQ Sinks Based on How You Plan To Recover

Once records are routed to a DLQ stream, they need a durable destination. In practice, the two most common choices are Kafka and object storage.

### Kafka DLQ Sink

Kafka is the right choice when you want:

- Near-real-time inspection
- Streaming replay
- Operational integration with existing consumers

Java

18

```text/x-java
private static KafkaSink<DeadLetterRecord> buildDlqKafkaSink(
```

```text/x-java
String topicName) {
```

```text/x-java
​
```

```text/x-java
return KafkaSink.<DeadLetterRecord>builder()
```

```text/x-java
.setBootstrapServers("kafka-broker:9092")
```

```text/x-java
.setRecordSerializer(
```

```text/x-java
KafkaRecordSerializationSchema.builder()
```

```text/x-java
.setTopic(topicName)
```

```text/x-java
.setValueSerializationSchema(
```

```text/x-java
new JsonSerializationSchema<>(DeadLetterRecord.class))
```

```text/x-java
.setKeySerializationSchema(
```

```text/x-java
record -> record.errorType().getBytes())
```

```text/x-java
.build()
```

```text/x-java
)
```

```text/x-java
.setDeliveryGuarantee(DeliveryGuarantee.AT_LEAST_ONCE)
```

```text/x-java
.build();
```

```text/x-java
}
```

```text/x-java
​
```

### S3 DLQ Sink

Object storage is the better choice when you want:

- Long retention
- Low-cost quarantine
- Batch replay with Spark or Athena
- Partitioned storage by date or error type

Java

20

```text/x-java
private static FileSink<DeadLetterRecord> buildS3DlqSink() {
```

```text/x-java
return FileSink
```

```text/x-java
.forRowFormat(
```

```text/x-java
new Path("s3://your-bucket/dlq/entity-resolution/"),
```

```text/x-java
new JsonRowEncoder<>(DeadLetterRecord.class)
```

```text/x-java
)
```

```text/x-java
.withRollingPolicy(
```

```text/x-java
DefaultRollingPolicy.builder()
```

```text/x-java
.withRolloverInterval(Duration.ofMinutes(15))
```

```text/x-java
.withInactivityInterval(Duration.ofMinutes(5))
```

```text/x-java
.withMaxPartSize(MemorySize.ofMebiBytes(128))
```

```text/x-java
.build()
```

```text/x-java
)
```

```text/x-java
.withBucketAssigner(
```

```text/x-java
new DateTimeBucketAssigner<>(
```

```text/x-java
"error-type='unknown'/year=yyyy/month=MM/day=dd/hour=HH")
```

```text/x-java
)
```

```text/x-java
.build();
```

```text/x-java
}
```

```text/x-java
​
```

A practical production pattern is to use:

- Kafka for short-term operational handling
- S3 for long-term quarantine and replay

That gives you both fast response and durable history.

## Pattern 5: Monitor DLQ Rate, Not Just Job Uptime

A DLQ that nobody watches is just a backlog with better branding.

Job uptime alone is not enough. A Flink job can stay green while quietly routing 10% of traffic to the DLQ.

That is still a production incident.

### Add Metrics Inside the Operator

Java

39

```text/x-java
public class MonitoredEntityEventProcessor
```

```text/x-java
extends ProcessFunction<String, EntityEvent> {
```

```text/x-java
​
```

```text/x-java
private transient Counter dlqCounter;
```

```text/x-java
private transient Counter successCounter;
```

```text/x-java
private transient Histogram processingLatency;
```

```text/x-java
​
```

```text/x-java
@Override
```

```text/x-java
public void open(Configuration parameters) {
```

```text/x-java
MetricGroup metrics = getRuntimeContext()
```

```text/x-java
.getMetricGroup()
```

```text/x-java
.addGroup("entity_resolution");
```

```text/x-java
​
```

```text/x-java
dlqCounter = metrics.counter("dlq_routed_total");
```

```text/x-java
successCounter = metrics.counter("processed_success_total");
```

```text/x-java
processingLatency = metrics.histogram(
```

```text/x-java
"processing_latency_ms",
```

```text/x-java
new DescriptiveStatisticsHistogram(1000)
```

```text/x-java
);
```

```text/x-java
}
```

```text/x-java
​
```

```text/x-java
@Override
```

```text/x-java
public void processElement(
```

```text/x-java
String raw, Context ctx, Collector<EntityEvent> out) {
```

```text/x-java
​
```

```text/x-java
long start = System.currentTimeMillis();
```

```text/x-java
try {
```

```text/x-java
EntityEvent event = parseAndValidate(raw);
```

```text/x-java
successCounter.inc();
```

```text/x-java
out.collect(event);
```

```text/x-java
} catch (Exception e) {
```

```text/x-java
dlqCounter.inc();
```

```text/x-java
ctx.output(DLQ_TAG, buildDeadLetter(raw, e));
```

```text/x-java
} finally {
```

```text/x-java
processingLatency.update(System.currentTimeMillis() - start);
```

```text/x-java
}
```

```text/x-java
}
```

```text/x-java
}
```

```text/x-java
​
```

### Alert on DLQ Rate

A useful alert is DLQ throughput relative to successful throughput:

YAML

13

```text/x-yaml
- alert: FlinkDlqRateHigh
```

```text/x-yaml
expr: |
```

```text/x-yaml
rate(flink_entity_resolution_dlq_routed_total[5m])
```

```text/x-yaml
/
```

```text/x-yaml
rate(flink_entity_resolution_processed_success_total[5m])
```

```text/x-yaml
> 0.01
```

```text/x-yaml
for: 2m
```

```text/x-yaml
labels:
```

```text/x-yaml
severity: warning
```

```text/x-yaml
annotations:
```

```text/x-yaml
summary: "DLQ rate exceeds 1% of total throughput"
```

```text/x-yaml
description: "Check dlq.unknown Kafka topic for upstream schema changes"
```

```text/x-yaml
​
```

As a rule of thumb:

- above 1% often indicates schema drift or producer issues
- above 5% usually indicates a broader systemic problem

The exact thresholds depend on the pipeline, but the principle does not: **monitor DLQ rate as a first-class health signal**.

## Pattern 6: Replay With a Dedicated Reprocessing Job

A DLQ is only complete when replay is possible.

The cleanest design is a separate Flink job that reads from the DLQ topic and routes records back through the main processing logic.

### Example Replay Job

Java

31

```text/x-java
public class DlqReprocessingJob {
```

```text/x-java
​
```

```text/x-java
public static void main(String[] args) throws Exception {
```

```text/x-java
​
```

```text/x-java
StreamExecutionEnvironment env =
```

```text/x-java
StreamExecutionEnvironment.getExecutionEnvironment();
```

```text/x-java
​
```

```text/x-java
DataStream<DeadLetterRecord> dlqStream = env
```

```text/x-java
.fromSource(
```

```text/x-java
buildKafkaSource("dlq.schema-invalid"),
```

```text/x-java
WatermarkStrategy.noWatermarks(),
```

```text/x-java
"dlq-source"
```

```text/x-java
);
```

```text/x-java
​
```

```text/x-java
DataStream<String> replayStream = dlqStream
```

```text/x-java
.filter(r -> r.failedAtEpochMs() >= START_EPOCH
```

```text/x-java
&& r.failedAtEpochMs() <= END_EPOCH)
```

```text/x-java
.map(DeadLetterRecord::rawPayload);
```

```text/x-java
​
```

```text/x-java
SingleOutputStreamOperator<EntityEvent> reprocessed =
```

```text/x-java
replayStream.process(new EntityEventProcessor());
```

```text/x-java
​
```

```text/x-java
reprocessed.sinkTo(buildDownstreamKafkaSink());
```

```text/x-java
​
```

```text/x-java
reprocessed.getSideOutput(DLQ_TAG)
```

```text/x-java
.sinkTo(buildKafkaSink("dlq.permanent-quarantine"));
```

```text/x-java
​
```

```text/x-java
env.execute("DLQ Reprocessing Job");
```

```text/x-java
}
```

```text/x-java
}
```

```text/x-java
​
```

### Why Replay Should Be a Separate Job

Keeping replay separate from the main pipeline gives you:

- Independent scaling
- Independent scheduling
- Cleaner checkpoint behavior
- Safer operational control

It also lets you drain backlogs on your own terms:

- Off-peak hours
- Reduced parallelism
- Or maximum parallelism when you need to catch up quickly

That separation keeps the main pipeline stable while still making recovery practical.

## PyFlink Version: Same Pattern, Same Principle

If your team uses PyFlink, the same side output pattern applies.

Python

43

```text/x-python
from pyflink.datastream import StreamExecutionEnvironment
```

```text/x-python
from pyflink.datastream.functions import ProcessFunction
```

```text/x-python
from pyflink.common.typeinfo import Types
```

```text/x-python
from pyflink.datastream.output_tag import OutputTag
```

```text/x-python
​
```

```text/x-python
DLQ_TAG = OutputTag(
```

```text/x-python
"dead-letter-queue",
```

```text/x-python
Types.ROW_NAMED(
```

```text/x-python
["raw_payload", "error_type", "error_message", "failed_at_ms"],
```

```text/x-python
[Types.STRING(), Types.STRING(), Types.STRING(), Types.LONG()]
```

```text/x-python
)
```

```text/x-python
)
```

```text/x-python
​
```

```text/x-python
class EntityEventProcessor(ProcessFunction):
```

```text/x-python
def process_element(self, value, ctx):
```

```text/x-python
try:
```

```text/x-python
event = parse_and_validate(value)
```

```text/x-python
yield event
```

```text/x-python
except Exception as e:
```

```text/x-python
from pyflink.common import Row
```

```text/x-python
yield DLQ_TAG, Row(
```

```text/x-python
raw_payload=str(value),
```

```text/x-python
error_type=type(e).__name__,
```

```text/x-python
error_message=str(e),
```

```text/x-python
failed_at_ms=int(time.time() * 1000)
```

```text/x-python
)
```

```text/x-python
​
```

```text/x-python
env = StreamExecutionEnvironment.get_execution_environment()
```

```text/x-python
source_stream = env.from_source(...)
```

```text/x-python
​
```

```text/x-python
processed = source_stream.process(
```

```text/x-python
EntityEventProcessor(),
```

```text/x-python
output_type=Types.STRING()
```

```text/x-python
)
```

```text/x-python
​
```

```text/x-python
good_events = processed
```

```text/x-python
dead_letters = processed.get_side_output(DLQ_TAG)
```

```text/x-python
​
```

```text/x-python
good_events.sink_to(build_downstream_sink())
```

```text/x-python
dead_letters.sink_to(build_dlq_sink())
```

```text/x-python
​
```

```text/x-python
env.execute("Entity Resolution Pipeline")
```

```text/x-python
​
```

The syntax changes, but the design principle stays the same: **good records continue, bad records are isolated and persisted**.

## Production Checklist

Before shipping a Flink pipeline, verify the following:

| Requirement | Why It Matters |
| --- | --- |
| Risky operators wrapped in try/catch | Prevents restart loops from unhandled exceptions |
| DLQ output tags use explicit typing | Avoids runtime serialization failures |
| DLQ sink is durable | Failed records must survive restarts |
| DLQ metrics are exported | Silent DLQ growth is otherwise invisible |
| Replay path exists and is tested | A DLQ without replay is just storage |
| DLQ retention is long enough | Teams need time to diagnose and replay |
| Permanent quarantine exists | Prevents infinite replay loops |
| Alerting is based on DLQ rate | Job health alone is not enough |

This checklist is worth automating in code review or deployment readiness checks. DLQ handling is too important to leave to convention.

## Key Takeaways

If you are building Flink pipelines in production, the safest default is:

- Use side outputs for DLQ routing
- Retry transient failures before escalation
- Classify failures into separate DLQ streams
- Sink DLQ records durably
- Export DLQ metrics
- Replay through a dedicated job

The core rule is simple:

**A bad message should never silently disappear, and it should never silently stop the stream.**

That is what turns DLQ handling from a defensive coding trick into a real reliability pattern.

## Environment Notes

The examples in this article target:

- Apache Flink 1.18
- Java 17
- PyFlink 1.18

A few implementation notes:

- The retry timer pattern requires a keyed stream before `KeyedProcessFunction`
- RocksDB is usually the safer state backend for larger retry state
- HashMap state backend can work well for smaller, latency-sensitive workloads
- `AT_LEAST_ONCE` is usually sufficient for DLQ sinks

## Final Thoughts

Poison messages are not rare in streaming systems. They are inevitable.

The real question is whether one bad record can take down an otherwise healthy pipeline.

With the right DLQ design in Flink, the answer becomes no.

The stream keeps moving. Good records continue. Bad records are quarantined. Alerts fire. Replay remains possible. And the pipeline stays operational while the root cause is fixed.

That is the difference between a stream that works in staging and one that survives production.

Apache Flink Database Stream (computing) Big data

Opinions expressed by DZone contributors are their own.
