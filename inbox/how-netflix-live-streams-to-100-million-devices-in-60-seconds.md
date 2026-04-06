---
title: "How Netflix Live Streams to 100 Million Devices in 60 Seconds"
source: "https://blog.bytebytego.com/p/how-netflix-live-streams-to-100-million?utm_source=post-email-title&publication_id=817132&post_id=190438250&utm_campaign=email-post-title&isFreemail=true&r=8x3s&triedRedirect=true&utm_medium=email"
author:
  - "[[ByteByteGo]]"
published: 2026-03-25
created: 2026-03-25
description: "In this article, we will look at the architecture of this system and the challenges Netflix faced while building it."
tags:
  - "clippings"
  - "distributed-systems"
  - "system-design"
  - "performance"
  - "redis"
---

> [!summary]
> Netflix's Live Origin architecture delivers live streams to 100+ million devices using redundant regional encoding pipelines, intelligent segment selection, and a custom storage layer built on Cassandra with EVCache write-through caching. Key optimizations include millisecond-grain HTTP caching, priority-based rate limiting, and metadata streaming through HTTP headers for scalable event notifications.

## New Year, New Metrics: Evaluating AI Search in the Agentic Era (Sponsored)

![](https://substackcdn.com/image/fetch/$s_!8ZPR!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F3e07ebdc-da60-480c-874b-162a215a186b_1600x840.png)

Most teams pick a search provider by running a few test queries and hoping for the best – a recipe for hallucinations and unpredictable failures. [This technical guide](https://go.bytebytego.com/You_032426) from [You.com](https://go.bytebytego.com/You_032426) gives you access to an exact framework to evaluate AI search and retrieval.

**What you’ll get:**

- A four-phase framework for evaluating AI search
- How to build a golden set of queries that predicts real-world performance
- Metrics and code for measuring accuracy

Go from “looks good” to proven quality.

---

Netflix Live Origin is a custom-built server that sits between the cloud live streaming pipelines and Open Connect, Netflix’s Content Delivery Network (CDN). It acts like a quality control checkpoint that decides which video segments get delivered to millions of viewers around the world.

When Netflix first introduced live streaming, they needed a system that could handle the unique challenges of real-time video delivery. Unlike Video on Demand (VOD), where content is prepared in advance, live streaming operates under time constraints. Every video segment must be encoded, packaged, and delivered to viewers within seconds. The Live Origin was designed specifically to handle these demands.

In this article, we will look at the architecture of this system and the challenges Netflix faced while building it.

*Disclaimer: This post is based on publicly shared details from the Netflix Engineering Team. Please comment if you notice any inaccuracies.*

## How the System Works

The Live Origin operates as a multi-tenant microservice on Amazon EC2 instances. The communication model is quite straightforward:

- The Packager, which prepares video segments for distribution, sends these segments to the Origin using HTTP PUT requests.
- Open Connect nodes retrieve these segments using HTTP GET requests. The URL used for the PUT request matches the URL used for the GET request, creating a simple storage and retrieval pattern.

See the diagram below:

![](https://substackcdn.com/image/fetch/$s_!kH_d!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Ff55b0d4c-052a-480a-9855-079860193dc8_3052x1988.png)

Netflix made a couple of architectural decisions that shaped how the Live Origin functions.

- First, they achieve reliability through redundant regional live streaming pipelines. Instead of relying on a single encoding pipeline, Netflix runs two independent pipelines simultaneously. Each pipeline operates in a different cloud region with its own encoder, packager, and video contribution feed.
- Second, Netflix adopted a manifest design with segment templates and constant segment duration. Instead of constantly updating a manifest file to list available segments, they use a predictable template where each segment has a fixed duration of 2 seconds. This design choice allows the Origin to predict exactly when segments should be published.

## Multi-Pipeline Awareness and Intelligent Selection

Live video streams inevitably contain defects because of the unpredictable nature of live video feeds and the strict real-time publishing deadlines. Common problems include short segments with missing video frames or audio samples, completely missing segments, and timing discontinuities where the decode timestamps are incorrect.

Running two independent pipelines substantially reduces the chance that both will produce defective segments at the same time. Because the pipelines use different cloud regions, encoders, and video sources, when one pipeline produces a bad segment, the other typically produces a good one.

The Live Origin leverages its position in the distribution path to make intelligent decisions. When Open Connect requests a segment, the Origin checks candidates from both pipelines in a predetermined order and selects the first valid one. To detect defects, the Packager performs lightweight media inspection and includes defect information as metadata when publishing segments to the Origin. In the rare case where both pipelines have defective segments, this information passes downstream so clients can handle the error appropriately.

---

## No invasive meeting bots (Sponsored)

![](https://substackcdn.com/image/fetch/$s_!vVis!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F682ca22f-67c4-40f0-b36d-40cb54cadd22_1000x750.png)

Ever had a meeting where a random bot joins the call and, suddenly, everyone’s distracted?

**Granola works differently.**

There are **no meeting bots**. Nothing joins your call.
Granola transcribes directly from **your device’s audio** (on your computer or your phone). It works with **any meeting tool**: Zoom, Google Meet, Microsoft team … and even for in-person conversations.

You stay focused and jot down notes like you normally would.
Granola quietly transcribes and enhances the important bits in the background.

And if you want to be extra thoughtful or compliant, you can always send a quick consent email beforehand - automatically disclosing your use of Granola.

Try Granola on your **next meeting** and see how much easier it is to stay present.

Get one month free on any paid plan using the code **BYTEBYTEGO**

---

## Optimizing for Open Connect

When the Live project started, Open Connect was highly optimized for VOD delivery. Netflix had spent years tuning nginx (a web server) and the underlying operating system for this use case. Unlike traditional CDNs that fill caches on demand, Open Connect pre-positions VOD assets on carefully selected servers called Open Connect Appliances (OCAs).

Live streaming did not fit neatly into this model, so Netflix extended nginx’s proxy-caching functionality. They made several optimizations to reduce unnecessary traffic and improve performance.

Open Connect nodes receive the same segment templates provided to clients. Using the template information, OCAs can determine the legitimate range of segments for any event at any point in time. This allows them to reject requests for segments outside this range immediately, preventing unnecessary requests from traveling through the network to the Origin.

When a segment is not yet available, and the Origin receives a request for it, the Origin returns a 404 status code (File Not Found) along with an expiration policy. Open Connect can cache this 404 response until just before the segment is expected to be published. This prevents repeated failed requests.

Netflix implemented a clever optimization for requests at the live edge, which is the most recent part of the stream. When a request arrives for the next segment that is about to be published, instead of returning another 404 that would propagate back through the network to the client, the Origin holds the request open. Once the segment is published, the Origin immediately responds to the waiting request. This significantly reduces network traffic for requests that arrive slightly early.

To support this functionality, Netflix added millisecond-grain caching to nginx. Standard HTTP Cache Control only works at the second granularity, which is too coarse when segments are generated every 2 seconds.

## Streaming Metadata Through HTTP Headers

Netflix uses custom HTTP headers to communicate streaming events in a highly scalable way. The live streaming pipeline provides notifications to the Origin, which inserts them as HTTP headers on segments generated at that point in time. These headers are cumulative, meaning they persist to future segments.

Whenever a segment arrives at an OCA, the notification information is extracted from the response headers and stored in memory using the event ID as the key. When an OCA serves a segment to a client, it attaches the latest notification data to the response. This system ensures that, regardless of where viewers are in the stream, they receive the most recent notification data. The notifications can even be conveyed on responses that do not supply new segments.

This approach allows Netflix to communicate information like ad breaks, content warnings, or live event updates to millions of devices efficiently and independently of their playback position.

## Cache Invalidation and Origin Masking

Netflix built an invalidation system that can flush all content associated with an event by altering the version number used in cache keys. This is particularly useful during pre-event testing, allowing the network to return to a pristine state between tests.

Each segment published by the Live Origin includes metadata about which encoding pipeline generated it and which region it came from. The enhanced invalidation system takes these variants into account. Netflix can invalidate a specific range of segment numbers, but only if they came from a particular encoder or from a specific encoder in a specific region.

Combined with this cache invalidation capability, the Live Origin supports selective encoding pipeline masking. This feature allows operations teams to exclude problematic segments from a particular pipeline when serving to Open Connect. When bad segments are detected during a live event, this system protects millions of viewers by hiding the problematic content, especially important during the DVR playback window when viewers might rewind to that part of the stream.

## Storage Architecture Evolution

Netflix initially used AWS S3 for Live Origin storage, similar to their VOD infrastructure. This worked well for low-traffic events, but as they scaled up, they discovered that live streaming has unique requirements that differ significantly from on-demand content.

While S3 met its stated uptime guarantees, the strict 2-second retry budget inherent to live events meant that any delays were problematic. In live streaming, every write is critical and time-sensitive. The requirements were closer to those of a global, low-latency, highly available database rather than object storage.

Netflix established five key requirements for the new storage system.

- First, they needed extremely high write availability within a single AWS region with low-latency replication to other regions. Any failed write operation within 500 milliseconds was considered a bug.
- Second, the system needed to handle high write throughput with hundreds of megabytes replicating across regions.
- Third, it had to efficiently support large writes that accumulate to thousands of keys per partition.
- Fourth, they needed strong consistency within the same region to achieve read latency under one second.
- Fifth, during worst-case scenarios involving Open Connect edge cases, the system might need to handle gigabytes of read throughput without affecting writes.

Netflix had previously built a Key-Value Storage Abstraction that leveraged Apache Cassandra to provide chunked storage of large values. This abstraction was originally built to support cloud game saves, but the Live use case would push its boundaries in terms of write availability, cumulative partition size, and read throughput.

The solution breaks large payloads into chunks that can be independently retried. Combined with Apache Cassandra’s local-quorum consistency model, which allows write availability even with an entire Availability Zone outage, and a write-optimized Log-Structured Merge Tree storage engine, Netflix could meet the first four requirements.

The performance improvements were solid. The median latency dropped from 113 milliseconds to 25 milliseconds, and the 99th percentile latency improved from 267 milliseconds to 129 milliseconds. This new solution was more expensive, but minimizing cost was not the primary objective.

![](https://substackcdn.com/image/fetch/$s_!ej3Y!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F655a5509-2932-4bc7-ae6e-6514f888c8fb_2800x1784.png)

Source: Netflix Tech Blog

However, handling the Origin Storm failure case required additional work. In this scenario, dozens of Open Connect top-tier caches could simultaneously request multiple large video segments. Calculations showed worst-case read throughput could reach 100 gigabits per second or more.

Netflix could respond to reads at network line rate from Apache Cassandra, but observed unacceptable performance degradation on concurrent writes. To resolve this, they introduced write-through caching using EVCache, their distributed caching system based on Memcached. This allows almost all reads to be served from a highly scalable cache, enabling throughput of 200 gigabits per second and beyond without affecting the write path.

In the final architecture, the Live Origin writes and reads to the KeyValue, which manages a write-through cache to the EVCache and implements a chunking protocol that spreads large values across the Apache Cassandra storage cluster. Almost all read load is handled from cache, with only cache misses hitting the storage layer. This combination has successfully met the demanding needs of the Live Origin for over a year.

![](https://substackcdn.com/image/fetch/$s_!c4EP!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Ffb3e5352-7ae0-4cef-afda-5a8a29fe374f_2938x1844.png)

Source: Netflix Tech Blog

## Scalability and Request Prioritization

Netflix’s live streaming platform handles a high volume of diverse stream renditions for each live event. This complexity comes from supporting various video encoding formats with multiple quality levels, numerous audio options across languages and formats, and different content versions such as streams with or without advertisements. During the Tyson vs. Paul fight event in 2024, Netflix observed a historic peak of 65 million concurrent streams.

Netflix chose to build a highly scalable origin rather than relying on traditional origin shields for better cache consistency control and simpler system architecture. The Live Origin connects directly with top-tier Open Connect nodes distributed geographically across several sites. To minimize load on the origin, only designated nodes per stream rendition at each site can fill directly from the origin.

See the diagram below:

![](https://substackcdn.com/image/fetch/$s_!Jifx!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Ff648d6dc-a648-4212-8568-b99321562885_3052x1988.png)

While the origin service can scale horizontally using EC2 instances, other system resources like storage platform capacity and backbone bandwidth cannot scale automatically. Not all requests to the live origin have the same importance. Origin writes are most critical because failure directly impacts the streaming pipeline. Origin reads for the live edge are critical because failure impacts the majority of clients. Origin reads for DVR mode are less critical because failure only affects clients who are rewinding.

Netflix implemented comprehensive publishing isolation to protect the latency-sensitive and failure-sensitive origin writes. The origin uses separate EC2 stacks for publishing and CDN traffic. The storage abstraction layer features distinct clusters for read and write operations. The storage layer itself separates the read path through EVCache from the write path through Cassandra. This complete path isolation enables independent scaling of publishing and retrieval traffic and prevents CDN traffic surges from impacting publishing performance.

The Live Origin implements priority-based rate limiting when the underlying system experiences stress. This approach ensures that requests with greater user impact succeed while requests with lower user impact are allowed to fail during periods of high load. Live edge traffic is prioritized over DVR traffic during periods of high load on the storage platform. The detection is based on the predictable segment template, which is cached in memory at the origin node. This allows priority decisions without accessing the datastore, which is valuable especially during datastore stress.

To mitigate traffic surges, Netflix uses TTL cache control alongside priority rate limiting. When low-priority traffic is impacted, the Origin instructs Open Connect to cache identical requests for 5 seconds by setting a max-age directive and returning an HTTP 503 error code. This strategy dampens traffic surges by preventing repeated requests within that 5-second window.

## Handling 404 Storms

Publishing isolation and priority rate limiting successfully protect the live origin from DVR traffic storms. However, traffic storms generated by requests for non-existent segments present additional challenges and opportunities for optimization.

The Live Origin structures metadata hierarchically as event, stream rendition, and segment. The segment publishing template is maintained at the stream rendition level. This hierarchical organization allows the origin to preemptively reject requests using highly cacheable event and stream rendition level metadata, avoiding unnecessary queries to segment level metadata.

The process works as follows:

- If the event is unknown, the request is rejected with a 404 error.
- If the event is known but the segment request timing does not match the expected publishing timing, the request is rejected with a 404 and cache control TTL matching the expected publishing time.
- If the event is known but the requested segment was never generated or missed the retry deadline, the request is rejected with a 410 (Gone) error, which tells the client to stop requesting.

At the storage layer, metadata is stored separately from media data in the control plane datastore. Unlike the media datastore, the control plane datastore does not use a distributed cache to avoid cache inconsistency. Event and rendition level metadata benefits from high cache hit ratios when in-memory caching is utilized at the live origin instance. During traffic storms involving non-existent segments, the cache hit ratio for control plane access easily exceeds 90 percent.

The use of in-memory caching for metadata effectively handles 404 storms at the live origin without causing datastore stress. This metadata caching complements the storage system’s distributed media cache, providing a complete solution for traffic surge protection.

## Conclusion

The Netflix Live Origin is a sophisticated system built specifically for the unique demands of live streaming at a massive scale.

Through redundant pipelines, intelligent segment selection, optimized caching strategies, prioritized request handling, and a custom storage architecture, Netflix has created a reliable foundation for delivering live events to millions of concurrent viewers worldwide.

The system successfully balances the competing demands of write reliability, read scalability, and operational flexibility, proving its effectiveness during major events like the Tyson vs. Paul fight that reached 65 million concurrent streams.

**References:**

- [Netflix Live Origin](https://netflixtechblog.com/netflix-live-origin-41f1b0ad5371)
- [Ephemeral volatile caching in the Cloud](https://netflixtechblog.com/ephemeral-volatile-caching-in-the-cloud-8eba7b124589)
