---
title: "Scaling Java-Based Real-Time Systems: The Hidden Tradeoffs of Event-Driven Design"
source: "https://www.infoq.com/articles/tradeoffs-event-driven-design/?utm_source=notification_email&utm_campaign=notifications&utm_medium=link&utm_content=&utm_term=daily"
author:
  - "[[Sagar Deepak Joshi]]"
published: 2026-06-30
created: 2026-07-01
description: "Hard lessons from scaling a Java + Kafka contact center platform: where event-driven architecture breaks under real-time load, and the Redis-backed patterns that fixed state, latency, and cascades."
tags:
  - "clippings"
---

> [!summary]
> A field report on scaling a Java + Kafka cloud contact center (80k busy-hour call completions, 10k concurrent agents, 5M daily transactions), cataloguing where event-driven architecture breaks under real-time load. It walks through a three-generation state-management evolution ending in Redis-backed shared state, plus hard lessons on Kafka partition ceilings, cross-cluster deduplication, JVM/GC tuning, the Kafka Streams RocksDB latency trap, and cascading failures from blocking consumer threads.

[Java](https://www.infoq.com/java/ "Java")

[QCon San Francisco (Nov 16-20): Deep technical sessions. Peer conversations that change how you think.](https://qconsf.com/?utm_source=infoq&utm_medium=referral&utm_campaign=infoqyellowbox_qsf26)

Listen to this article - 28:49

Event-driven architecture has become the default recommendation for building scalable, distributed systems. The promise is compelling: loose coupling, independent scalability, fault isolation, and the ability to handle massive throughput without tight synchronous dependencies. For real-time collaboration platforms such as contact centers, unified communications systems, and video conferencing, these properties seem tailor-made.

I spent years building and scaling a cloud contact center platform handling over eighty thousand busy hour call completions (BHCC) across ten thousand concurrent agents, processing more than five million daily transactions. We went all-in on event-driven architecture with Apache Kafka as the primary messaging backbone. The results were mixed in ways that architecture diagrams never show.

This is not an argument against event-driven design. It is an honest account of the tradeoffs that only become visible in production, particularly in systems where real-time responsiveness is not a nice-to-have but a core product requirement.

## The Fundamental Tension: Async by Default, Real-Time by Requirement

Contact center platforms are unforgiving environments. When an agent receives an inbound call, the UI must reflect that state within milliseconds, not seconds. When a supervisor views their team dashboard, stale presence data is not a minor inconvenience; it affects workforce management decisions in real time.

Event-driven architecture is, at its core, asynchronous. Every Kafka message that is published, consumed, and processed adds latency at each hop. In a microservices architecture where a single user action triggers a chain of downstream events including routing engine, agent state service, presence service, and UI notification service compounds that latency.

We observed scenarios in which agents placing outbound calls experienced UI lag of two to three seconds before the interface reflected the new call state. Under peak load, inbound call answer events occasionally failed to propagate in time, causing timeouts at the originating source. The system was technically working correctly. Events were being processed, but the async nature of the pipeline violated the real-time contract the product required.

The lesson learned was that event-driven architecture is an excellent fit when eventual consistency is acceptable. In real-time communication systems, there are critical paths (e.g., call signaling, agent state transitions, and presence updates) where eventual consistency is functionally equivalent to failure. These paths demand synchronous or near-synchronous communication, not asynchronous event pipelines.

## The Cache Mismatch Problem: Distributed State in Disguise

One of the canonical benefits of event-driven architecture is that each service maintains its own local state, derived from the event stream. This architecture eliminates shared databases and tight coupling. In practice, in a real-time collaboration platform, this approach creates a subtle and dangerous problem: cache mismatch across service instances.

In our system, each microservice maintained a local in-memory cache built from Kafka events. Under normal conditions, all service instances consumed the same event stream and maintained consistent state. Under edge conditions including network partitions, consumer lag, and partial restarts, different instances would diverge.

The consequence was not an error or an exception. It was silent incorrectness: Work cards for voice and chat engagements would become stuck on agent UIs, reflecting a state that no longer matched reality. Because the mismatch was between in-memory caches across pods, it was invisible to standard monitoring. Agents would report stuck cards, but by the time an engineer investigated, the state had often self-corrected. In some cases, work cards remained stuck for over twenty-four hours before the issue was identified and resolved.

This moment triggered our move to Redis as the authoritative shared state store, the third generation of our state management evolution, described in detail later in this article.

## The Three-Generation State Management Evolution

Our journey through state management strategies is perhaps the most instructive arc of the entire system and included three generations of design, each solving the previous generation's problems while introducing its own.

### Generation 1: Kafka Global State Stores

Our first approach used Kafka Streams global state stores, a built-in mechanism that replicates a topic's data across all pods, giving every instance a complete local copy of a shared state. This approach seemed ideal. Every pod had full state visibility without making network calls.

The problem was synchronization latency. Global state stores replicate asynchronously via Kafka's changelog topics. Under load, the replication lag between pods was measurable. In a real-time contact center, that lag was unacceptable. Pod A and Pod B would simultaneously hold different versions of the same agent's call state. Routing decisions made by Pod A could conflict with decisions made by Pod B moments later. User state and call state became transiently inconsistent in ways that were difficult to detect and nearly impossible to reproduce in testing.

### Generation 2: Local In-Memory Cache via Kafka Replay

The fix for sync latency was to abandon global state stores entirely and have each pod build its own local in-memory cache from the Kafka event stream. Each event carried a header flag (CREATED, UPDATED, or DELETED) and pods independently maintained their own state with no cross-pod synchronization and no replication lag.

This design eliminated the consistency problem but introduced two new ones. First came startup latency, in which a pod cold-starting had to replay the entire event backlog to rebuild its cache from scratch. In our system, this replay took approximately five minutes per pod, effectively disabling the Kubernetes Horizontal Pod Autoscaler (HPA), because new pods triggered by load spikes were unavailable for five minutes while rebuilding state. Next, there were edge conditions (e.g., network partitions, consumer lag, and partial restarts). Different pod instances would diverge, producing the cache mismatch problem described earlier work cards stuck for over twenty-four hours and silent incorrectness invisible to standard monitoring.

### Generation 3: Redis Shared Cache with Resilience Layer

The final architecture replaced local caches with Redis as the authoritative shared state store. Kafka events updated Redis; all pods read from Redis directly. This direct read eliminated both cross-pod inconsistency and the startup replay problem.

Startup delay dropped by sixty percent. Pods initialized from Redis rather than replaying thousands of Kafka events, but introducing Redis as a critical path dependency required a resilience strategy. A Redis outage could not be allowed to entirely take down the agent state.

The solution was a silent recovery thread. On pod startup, if Redis were unavailable or partially populated, a background thread would silently rebuild the Redis cache from the Kafka event stream without blocking the pod from serving traffic. The pod would start with degraded state and progressively improve as the recovery thread populated Redis, rather than waiting five minutes before accepting any traffic.

As shown in Figure 1, this design gave us the consistency of shared state, the startup speed of a warm cache, and the resilience of a self-healing recovery path; all without any of the three generations' original failure modes.

![](https://imgopt.infoq.com/fit-in/3000x4000/filters:quality(85)/filters:no_upscale()/articles/tradeoffs-event-driven-design/en/resources/223figure-1-1782458801615.jpg)

**Figure 1: Three-generation state management evolution (Created by the author).**

The lesson learned was that state management in event-driven systems is not a solved problem, it is a series of tradeoffs that only reveal themselves under production load. Global state stores introduce synchronization latency. Local caches introduce startup delays and divergence. Shared caches introduce availability dependencies. The key is to design for all three failure modes from the start: Use Redis for shared authoritative state, snapshot initialization for startup speed, and a background recovery thread for resilience. Do not discover these requirements one production incident at a time.

## Partition Limits: The Hidden Ceiling on Horizontal Scaling

Kafka's scalability model is elegant on paper: add more partitions, add more consumers, and scale linearly. In a production system with multiple services sharing topics, the reality is more constrained.

In our architecture, major topics had twelve partitions, mid-tier topics had six, and lower-volume topics had three. The consumer group model is built so that the maximum number of active consumers per topic equals the number of partitions. Deploy more consumer pods than partitions and the excess pods sit idle, consuming memory and compute resources while contributing nothing to throughput.

For shared topics consumed by multiple services, this design created a hard ceiling: We could not independently scale individual services beyond the partition count without paying the cost for idle pods across all consumers.

The obvious solution to this problem was to increase partition count, but that solution introduced its own problem. Repartitioning a live Kafka topic triggers consumer group rebalancing. During rebalancing, consumer processing pauses. In a real-time contact center, any processing pause is operationally significant. The risk of a production rebalancing event made partition increases operationally dangerous, effectively locking us into the partition counts we had set at initial deployment.

We eventually addressed this issue through two changes that came as part of the broader Redis migration. Moving shared state out of Kafka topics and into Redis significantly reduced cross-service topic dependencies and consolidating over-fragmented microservices into cohesive feature services reduced the number of consumer groups competing for partitions. Both changes were reactive, driven by production pain rather than upfront design.

The lesson learned was to choose partition counts deliberately at design time, because they are difficult to change safely in production. Avoid sharing topics across multiple services where possible; per-service topics give each team independent scaling control. Finally, recognize that horizontal scaling in Kafka is bounded by partitions, not by compute resources.

## Cross-Cluster Event Propagation: The Deduplication Tax

Our platform spanned two Azure Kubernetes Service clusters, the UI framework in one and the backend routing core in another, with the voice switch running separately on Google Cloud Platform (GCP). This topology introduced a deduplication problem that became one of our most significant latency sources.

The UI communicated with the backend over gRPC with separate upstream and downstream channels. Because all backend gRPC pods were subscribed to the same channel, every pod simultaneously received every UI message. Without deduplication, each pod would independently process the same event and publish duplicate downstream messages.

Our first solution to this issue used Kafka itself as the deduplication mechanism. All gRPC pods wrote received messages to a raw Kafka topic using `call_id` as the partition key. Because Kafka guarantees that messages with the same partition key land on the same partition, a single consumer pod would receive all duplicates for a given call. That consumer took the first message, dropped the rest, and published to a deduplicated downstream topic.

This solution was functionally correct, but introduced a compounding latency problem. The Kafka consumer default polling interval was one hundred milliseconds, so that every event incurred at minimum a one hundred millisecond delay at each Kafka hop. The deduplication pattern added two full Kafka hops to every UI interaction: one to the raw topic, one from the dedup topic to downstream services. At minimum polling intervals alone, that was two hundred milliseconds of unavoidable latency before downstream services saw any event, before any processing was done, any REST calls were made, or any cross-cluster network overhead was generated.

We eventually replaced the Kafka-based deduplication with a Redis first-write-wins pattern as shown in Figure 2. The first pod to successfully claim a `call_id` key in Redis became the designated processor; all other processors discarded the message immediately. This approach eliminated the raw topic entirely and removed one full Kafka hop from the critical path.

![](https://imgopt.infoq.com/fit-in/3000x4000/filters:quality(85)/filters:no_upscale()/articles/tradeoffs-event-driven-design/en/resources/167figure-2-1782458801615.jpg)

**Figure 2: Redis first-write-wins cross-cluster deduplication (Created by the author).**

The lesson learned was that using Kafka as a deduplication mechanism on latency-sensitive paths is expensive. The polling interval creates an unavoidable latency floor at every hop. For real-time systems, Redis-based coordination patterns eliminate this floor and should be the first choice for cross-instance deduplication.

## JVM-Specific Considerations: What Java Adds to These Tradeoffs

The failure modes described above are architectural and apply regardless of implementation language. But building this system in Java on the JVM introduced additional constraints worth addressing explicitly for Java architects.

### Spring Boot Startup Overhead

Spring Boot's application context initialization adds meaningful startup time before any Kafka consumer is ready to process events. In our system, Spring Boot context initialization added approximately thirty to forty-five seconds to pod startup time before Kafka consumer registration even began. Combined with the Kafka event replay problem described earlier, total pod startup time approached six minutes in worst-case scenarios, making the HPA autoscaling problem significantly worse than it would have been in a lighter runtime.

Two changes addressed this issue directly: lazy initialization (`spring.main.lazy-initialization=true`) deferred bean creation until first use and the move to Redis snapshot initialization eliminated the Kafka replay phase. Together these changes brought Spring Boot pod startup below ninety seconds under normal conditions.

### GC Pressure Under High-Throughput Kafka Consumption

At peak load, eighty thousand busy hour call completions and five million daily transactions, the volume of Kafka message deserialization, object creation, and state manipulation created significant garbage collection (GC) pressure on the JVM heap. We observed stop-the-world GC pauses during peak periods that contributed to consumer lag spikes. A pod experiencing a two hundred to four hundred millisecond GC pause during peak consumption would fall behind its partition's event rate, creating lag that could take minutes to recover.

Migrating to JDK 17 was the single highest-impact change we made. JDK 17's improved Garbage-First Garbage Collector (G1GC) implementation meaningfully reduced pause frequencies out of the box. Beyond the JDK upgrade, three additional JVM tuning changes compounded the improvement. The G1GC pause target (`-XX:MaxGCPauseMillis=100`) set an explicit upper bound on GC pause duration, reducing the frequency of longer pauses under peak load. Tiered compilation (`-XX:+TieredCompilation`) allowed the JVM to combine interpreted execution, C1 compiler optimization, and C2 compiler optimization across method execution stages, reducing CPU overhead for frequently called Kafka consumer methods and hot state management code paths. The improvement in CPU and memory usage was measurable under sustained peak load. Finally, object pooling improved the situation. Frequently allocated message wrapper objects were pooled to reduce allocation pressure and GC collection frequency. Together these changes brought CPU and memory usage to acceptable levels under peak load. a meaningful improvement over the pre-JDK 17 baseline where GC pressure was a consistent contributor to consumer lag spikes.

### JDK 21 Virtual Threads

JDK 21's virtual threads (Project Loom) directly address this class of problem. A Kafka consumer using virtual threads can make blocking REST calls without blocking the underlying carrier thread, allowing the JVM to schedule other work while the I/O completes. While it was not available to us during the incidents described here, this solution is worth evaluating for any Java-based Kafka consumer that cannot fully avoid downstream synchronous calls.

The lesson learned was that Java architects building Kafka-based real-time systems should treat Spring Boot startup time, GC pause behavior, and blocking I/O in consumer threads as first-class architectural concerns, not as implementation details. JDK 21 virtual threads meaningfully address the blocking I/O problem, while GC tuning and lazy initialization address startup overhead. It is important to explicitly plan for these details.

## Kafka Streams and the RocksDB Performance Trap

Several of our services used the Kafka Streams library for stateful stream processing, joining Agent events, UserFeature events, and VoiceAgent events into unified UserAggregate events. On paper, Kafka Streams was the right tool: It provided exactly-once semantics, built-in state management, and tight Kafka integration.

In practice, the performance profile was a poor fit for real-time contact center workloads.

Kafka Streams uses RocksDB as its embedded state store for intermediate aggregations. RocksDB is a high-performance disk-backed key-value store, which is fast for batch and near-real-time workloads, but not in-memory fast. For a platform where agent state changes needed to propagate within hundreds of milliseconds, the disk I/O overhead of RocksDB materialization added latency that was invisible in development and testing, but significant under production load.

We did not instrument RocksDB compaction latency directly, but the performance degradation was observable in end-to-end agent state propagation at times under peak load. The root cause was the topology design itself: Each transformer stage in the Kafka Streams pipeline maintained its own intermediate state store backed by RocksDB. With multiple transformer stages between source and sink, read/write operations to RocksDB compounded at each stage. Our assessment was that a topology with fewer transformer stages or a vanilla Kafka consumer bypassing RocksDB entirely would conservatively reduce state store read/write overhead by an estimated thirty percent, based on the reduction in intermediate materialization points. The compaction-driven latency spikes were most visible during peak load windows, where RocksDB's background compaction competed directly with foreground read/write operations servicing real-time state queries.

The deeper problem was consumer group design. The same consumer group was consuming both the source topics (e.g., Agent, UserFeature, and VoiceAgent) and the internal UserAggregate topic produced by the join operation. The lag on source topics directly starved the aggregate consumer, a single slow partition upstream could delay the entire join pipeline.

The lesson learned was that Kafka Streams is well-suited for analytical and near-real-time workloads where RocksDB's disk-backed performance is acceptable. For sub-second real-time requirements, minimize transformer stages to reduce RocksDB materialization points, each intermediate state store is a latency multiplier under compaction. Separate consumer groups for source and derived topics are non-negotiable. Shared consumer groups create invisible coupling between pipeline stages. Where possible, choose a vanilla Kafka consumer with Redis-backed state over Kafka Streams with RocksDB for latency-sensitive paths.

## The Cascading Failure: When Downstream Latency Freezes Upstream Consumers

The most severe production incident we experienced was not a single failure; it was a cascade triggered by a single slow REST API call propagating upstream through the entire pipeline.

The scenario was bulk agent provisioning. An administrator would trigger provisioning of up to ten thousand agents from the Admin UI, which published events to a Kafka topic with only three partitions. Our service consumed these events and called a downstream REST API to provision each agent on the client-side cloud. The Admin UI enforced a thirty-minute total timeout on the bulk operation.

The failure chain had four compounding problems operating simultaneously. First, with only three partitions and Kafka Streams using two threads per partition, a maximum of six threads were processing ten thousand agent provisioning events. Second, each consumer thread made a synchronous blocking REST call to the downstream service. When the downstream REST API degraded under load, those six threads blocked and remained blocked. While threads blocked, Kafka message consumption halted entirely. Third, the provisioning pipeline required three separate events per agent (e.g., Agent, UserFeature,and VoiceAgent) to be joined into a UserAggregate, which caused thirty thousand messages to flow through a three-partition bottleneck. Fourth, the shared consumer group meant that source event lag and aggregate event lag compounded each other.

Consumer lag built to over thirty minutes. The Admin UI timeout fired. The bulk provisioning operation failed, but not cleanly. Some agents had been provisioned on the client side, while others had not. The system was left in an inconsistent state with no automatic reconciliation.

The remediation required two significant architectural changes. First, the three separate provisioning events were consolidated into a single unified event, reducing message volume by two-thirds and eliminating the internal join topic entirely. Second, the synchronous REST call was replaced with a Redis queue. Consumer threads wrote provisioning requests to Redis and returned immediately, with a separate asynchronous worker pool independently processing REST calls. Consumer threads were never again blocked by downstream latency.

The partial inconsistency, some agents being provisioned on the client side, while others were not, required a manual reconciliation process. The recovery team cross-referenced the client-side provisioning system's confirmed records against the expected provisioning list from the Admin UI operation. Agents confirmed as provisioned on the client side but missing from the platform's internal state were re-triggered individually using idempotency checks: Each provisioning call included a unique operation ID, while the downstream system rejected duplicate provisioning requests for agents already in a provisioned state. Agents that had failed on the client side were identified and re-queued through the repaired pipeline. The full reconciliation took approximately three hours of manual engineering effort.

The results were measurable. Consumer lag dropped by approximately fifty percent, provisioning operations became restart-safe through Redis queue durability, and failed REST calls were automatically retried without re-consuming from Kafka.

The lesson learned was that synchronous blocking calls inside Kafka consumer threads are an architectural hazard. A single slow downstream dependency can freeze consumption across an entire topic, propagating latency upstream through the pipeline. Any consumer thread that must call an external service should do so asynchronously by writing to a durable queue and then returning to consume the next message. Treat the consumer thread as sacred, with its only job being to consume and hand off, never to block.

## What I Would Design Differently

Looking back, five architectural decisions would have significantly changed our trajectory:

Use synchronous paths for latency-sensitive operations. Call signaling, agent state transitions, and UI notifications should have used synchronous or low-latency pub/sub communication (such as WebSockets or gRPC streams) rather than Kafka. Reserve Kafka for durable, non-latency-sensitive flows: analytics, audit logs, and downstream CRM synchronization.

Use Redis shared cache with resilience from day one. Rather than evolving through three generations of state management, global state stores, local caches, and then Redis, start with Redis as the authoritative real-time state store, snapshot initialization for fast startup, and a background recovery thread for Redis outage resilience. Each of these three elements is essential; implementing only one or two creates a new failure mode.

Use snapshot-first initialization. Any service that requires local state should initialize from a snapshot, not from full event replay. Design the snapshot mechanism before deploying to production; retrofitting it is significantly more complex than building it in from the start.

Use Redis-first deduplication for cross-cluster fan-out. Any architecture where multiple pods simultaneously receive the same message should use Redis first-write-wins from day one. Kafka-based deduplication adds unavoidable polling latency at every hop.

Never block consumer threads. Consumer threads must never make synchronous external calls. Design asynchronous handoff patterns (e.g., Redis queues and separate worker pools) from the start. The consumer thread's job is to consume and hand off, nothing more.

## Conclusion

None of these issues are theoretical concerns. Every issue manifested as a production incident, including stuck work cards, agent provisioning timeouts, autoscaler paralysis, inconsistent call state, and UI lag. Each incident violated the real-time contract the product required.

These are not arguments against event-driven design. They are arguments for designing with eyes open: understanding where asynchronous is appropriate and where it is not, treating consumer threads as sacred, planning state management across all three failure modes from the start, and recognizing that partition topology and consumer group design are first-class architectural decisions, not implementation details.
