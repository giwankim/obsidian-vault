---
title: "Kafka-based job queue library 'Decaton' examples"
source: "https://engineering.linecorp.com/en/blog/kafka-based-job-queue-library-decaton-examples"
author:
  - "[[Kazuki Matsushita]]"
published:
created: 2026-06-26
description: "Introduction: DecatonLINE recently released an in-house developed library, Decaton, as open source. Decaton is a Kafka-based asynchronous job queue..."
tags:
  - "clippings"
---

> [!summary]
> LINE introduces Decaton, its open-source Kafka-based asynchronous job queue library, through real use cases from the "Smart Channel" feature. As a job queue it adds value Kafka alone lacks — built-in retry handling via a separate retry topic, and parallel multi-threaded processing of a single partition — letting teams absorb traffic spikes without overloading downstream REST APIs. The post also showcases Decaton's delayed-job feature, used with Redis to classify impression events (click / mute / no-action) by reprocessing impressions 10 minutes later, a case where Kafka Streams proved hard to implement efficiently.

## Introduction: Decaton

LINE recently released an in-house developed library, Decaton, as open source. Decaton is a Kafka-based asynchronous job queue library, and it is widely used throughout LINE.

- GitHub: [line/decaton - High throughput asynchronous task processing on Apache Kafka](https://github.com/line/decaton)

In fact, Kafka offers Kafka Streams, its official library for processing streams. However, Kafka Streams did not meet our requirements at the time, and we decided to develop a Kafka-based library called Decaton. Decaton processes messages more efficiently, compared to Kafka Streams, and it can be easily incorporated into programs. In this post, I'll introduce how Decaton is being used in LINE with real use cases.

## LINE's case

Let's use "Smart Channel" which is currently in service in Japan, Taiwan, and Thailand as a sample case. Smart Channel is a feature in LINE to display certain content such as weather forecasts or news at the top of chat room tabs. Upon user's request, it provides real-time content optimized for each user among content candidates. As this service incurs a lot of traffic, some tasks are processed asynchronously. And, Decaton is used to collect event logs.

> Reference. Refer to [【Product Story #3】ユーザー調査とテストを徹底的に繰り返し、反対派も巻き込みローンチに至った「スマートチャンネル」開発プロジェクトの裏側 – LINE ENGINEERING](https://engineering.linecorp.com/ja/blog/product-story-03-smart-channel/) (Japanese) for more information on the development of Smart Channel.

### Job queue implementation

Decaton makes it simple to implement a job queue, using Kafka as a backend. Smart Channel uses Decaton when updating content on the user's device. Content for Smart Channel is imported by a batch job first, and Decaton is used when updating this content.

![](https://engineering.linecorp.com/wp-content/uploads/2020/05/decaton2-1024x518.png)

Smart Channel delivers weather forecasts or news. These contents are imported from linked services like LINE NEWS by API. Once relevant contents are updated, Smart Channel calls the REST API. Actual updates do not occur at this point, and the API saves Decaton tasks on Kafka. A separate worker process fetches the Decaton tasks saved in Kafka and conducts an actual update.

![](https://engineering.linecorp.com/wp-content/uploads/2020/05/decaton3-1024x408.png)

The current way of saving data update as Decaton task and processing update later offers a few advantages:

1. You can avoid overload amid a temporarily sharp increase in traffic. Even if there is a temporary pickup in update, this structure doesn't increase the load easily. You can prevent the worst case scenario of failing to import update due to unavailable REST API.
2. You don't have to implement a process for job retries. Kafka only passes on messages so you need to implement a retry process on your own. It's not the case with Decaton. Decaton separately keeps Kafka topic for retries and manages job retries. So, library users can simply write a code to process single Kafka topic without considering a retry process.
3. Last but not the least, single Kafka partition can be processed by multiple threads in parallel, which makes it more efficient than relying on Kafka alone.

Smart Channel project was able to build a reliable program thanks to these advantages of using Decaton as a job queue.

### Collecting event logs

Decaton has a feature to delay processing a job after the given time. Smart Channel uses it to collect various events from the displayed content to learn what would be the most optimized content for each user. In order to learn from event logs, the final result of the displayed content must be identified. There are mainly three actions, resulting from exposing the content:

1. Exposing the content → Click on the content
2. Exposing the content → Muting (closing) the content
3. Exposing the content → No action

![](https://engineering.linecorp.com/wp-content/uploads/2020/05/decaton5-768x450.png)

It is easy to identify the result for actions 1 and 2 as users take a specific action. As for action 3, however, there is no follow-up action. So action 3 should be explicitly defined. Let's say that we'll consider it to be action 3 when there is no action in 10 minutes after exposing the content.

I'll elaborate on how to process these events below. Usually an event triggered by another event is stored somewhere and processed later. Simply saving an event can't accurately determine if it fulfills the definition of action 3. In addition, there are too much data to save. Against this backdrop, Smart Channel made a use of Decaton's job delaying feature to determine which category each action falls into. Find the following diagram, showing the event collection architecture with Decaton.

![](https://engineering.linecorp.com/wp-content/uploads/2020/05/decaton6-1024x422.png)

When there is a user action, Smart Channel notifies it through a HTTPS request. Event delivered by the API is passed on to Kafka, and the worker for corresponding event processes it. Content click or mute events are stored in Redis, and an impression without any specific action is stored again in Kafka, using Decaton's job delaying feature, for the second round of processing after 10 minutes. Impression events are processed again after 10 minutes to see if it is action 1, 2 or 3. Click or mute events are assigned a unique ID, and impression event can use this ID to check the information of click or mute events saved in Redis. So, it can be defined as action 3 if there was no click or mute event. You can set the time of delay for Decaton in the actual code as follows.

```
long timestamp = clock.millis(); // Get current UNIX timestamp in milliseconds
Duration delay = Duration.ofMinutes(10L); // Run the task after 10 minutes
TaskMetadata metadata =
        TaskMetadata.newBuilder()
                    .setTimestampMillis(timestamp)
                    .setScheduledTimeMillis(timestamp + delay.toMillis());
                    .build()


Task task = new Task(); // Task is a class generated by protobuf.
Serializer<Task> serializer = new ProtocolBuffersSerializer<>();
DecatonTaskRequest taskRequest =
        DecatonTaskRequest.newBuilder()
                          .setMetadata(metadata)
                          .setSerializedTask(ByteString.copyFrom(serializer.serialize(task)))
                          .build();


// After creating a Decaton task, submit it to Kafka topic.
producer.send(new ProducerRecord<>("topic", "key", taskRequest));
```

The initial plan was to implement this step with Kafka Streams. However, our study showed that it would be difficult to efficiently implement it with Kafka Streams. So, we tried out the combination of Decaton and Redis and could achieve our intended goal, simply combining programs as above. Decaton's job delay feature can be adopted for many other uses and purposes.

## Wrap-up

I've shared how Smart Channel used Dacaton in this post. Smart Channel still uses Kafka Streams here and there. As Decaton offers advantages such as seamlessly processing job retries and using a single partition with multiple threads in parallel, we plan to replace Kafka Streams with Decaton in phases. We strongly recommend you to try out [Decaton](https://github.com/line/decaton), an open source library, as it can meet your needs in many ways.

- [Kafka](https://engineering.linecorp.com/en/blog/tag/Kafka)
- [Decaton](https://engineering.linecorp.com/en/blog/tag/Decaton)
