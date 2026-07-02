---
title: "What Every Software Engineer Should Know about Apache Kafka: Events, Streams, Tables, Storage, Processing, And More"
source: "https://www.michael-noll.com/blog/2020/01/16/what-every-software-engineer-should-know-about-apache-kafka-fundamentals/"
author:
published: 2020-01-16
created: 2026-07-01
description: "To help fellow engineers wrap their head around Apache Kafka and event streaming, I wrote a 4-part series on the Confluent blog on Kafka’s core fundamentals...."
tags:
  - "clippings"
---

> [!summary]
> A short landing post linking to Michael Noll's 4-part Confluent series on Apache Kafka fundamentals. The series covers events, streams, tables, and the stream-table duality, then dives into Kafka's storage layer (topics, partitions) and processing layer (parallelism, elasticity, fault tolerance) via Kafka Streams and ksqlDB.

To help fellow engineers wrap their head around Apache Kafka and event streaming, I wrote a 4-part series on the [Confluent](https://www.confluent.io/) blog on Kafka’s core fundamentals. In the series, we explore Kafka’s storage and processing layers and how they interrelate, featuring Kafka Streams and ksqlDB.

![Streams vs. Tables in Chess](https://www.michael-noll.com/assets/uploads/streams-tables-chess-animation-large.gif)

In the first part, I begin with an overview of events, streams, tables, and the stream-table duality to set the stage. The subsequent parts take a closer look at Kafka’s storage layer, which is the distributed “filesystem” for streams and tables, where we learn about topics and partitions. Then, I move to the processing layer on top and dive into parallel processing of streams and tables, elastic scalability, fault tolerance, and much more. The series is related to my original article, [Of Streams and Tables in Kafka and Stream Processing, Part 1](https://www.michael-noll.com/blog/2018/04/05/of-stream-and-tables-in-kafka-and-stream-processing-part1/), but is both broader and deeper.

1. [Streams and Tables in Apache Kafka: A Primer](https://www.confluent.io/blog/kafka-streams-tables-part-1-event-streaming/) (**link is broken as of 2025**)
2. [Streams and Tables in Apache Kafka: Topics, Partitions, and Storage Fundamentals](https://confluent.io/blog/kafka-streams-tables-part-2-topics-partitions-and-storage-fundamentals/)
3. [Streams and Tables in Apache Kafka: Processing Fundamentals with Kafka Streams and ksqlDB](https://confluent.io/blog/kafka-streams-tables-part-3-event-processing-fundamentals/)
4. [Streams and Tables in Apache Kafka: Elasticity, Fault Tolerance, and other Advanced Concepts](https://www.confluent.io/blog/kafka-streams-tables-part-4-elasticity-fault-tolerance-advanced-concepts/)

I hope you enjoy the walkthrough!
