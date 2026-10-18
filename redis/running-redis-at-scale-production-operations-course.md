---
title: "Running Redis at Scale: Production Operations Course"
source: "https://redis.io/tutorials/operate/redis-at-scale/"
author:
  - "[[Redis]]"
published: 2026-01-27
created: 2026-10-16
description: "Master running Redis at scale. Comprehensive course on high availability, clustering, observability, persistence, and performance tuning for production workloads."
tags:
  - "clippings"
---

> [!summary]
> Landing page for Redis's free "Running Redis at Scale" course on operating self-managed open-source Redis in production. It outlines five units: client connection management and pipelining, persistence with RDB snapshots and AOF, high availability through replication and Sentinel failover, horizontal scaling with Redis Cluster sharding, and observability and latency diagnostics, all taught through Docker-based hands-on labs. Prerequisites are basic Redis commands, a Linux shell, Docker Compose, and Git.

## Running Redis at Scale: Course Overview & Introduction

> **TL;DR:**
>
> This course teaches you everything you need to run Redis in production at scale. You'll learn how to connect and tune Redis clients, persist data to disk with RDB and AOF, set up replication and failover with Redis Sentinel for high availability, horizontally scale with Redis Cluster, and monitor your deployment with built-in observability tools. By the end, you'll have the knowledge to operate a performant, durable, and highly available Redis deployment.

## Course Structure

This tutorial is part of the **Running Redis at Scale** course. You can jump to any section:

1. **Introduction to Running Redis at Scale** ← You are here
2. [Talking to Redis](https://redis.io/tutorials/operate/redis-at-scale/talking-to-redis/) - Connection management, client libraries, pipelining, and performance tuning
3. [Persistence and Durability](https://redis.io/tutorials/operate/redis-at-scale/persistence-and-durability/) - RDB snapshots, AOF logging, and hybrid persistence strategies
4. [High Availability](https://redis.io/tutorials/operate/redis-at-scale/high-availability/) - Replication, Redis Sentinel, and automatic failover
5. [Scalability](https://redis.io/tutorials/operate/redis-at-scale/scalability/) - Redis Cluster, sharding, and horizontal scaling
6. [Observability](https://redis.io/tutorials/operate/redis-at-scale/observability/) - Metrics, monitoring, latency diagnostics, and troubleshooting
7. [Course Conclusion](https://redis.io/tutorials/operate/redis-at-scale/course-wrap-up/)

---

## Welcome

[Embedded Content](https://youtu.be/3H896s0rr8E)

The world's data is growing exponentially. That exponential growth means that database systems must scale. This is a course about running Redis, one of the most popular databases, at scale.

So, how do you run Redis at scale? There are two general answers to this question, and it's important that we address them right away. That's because the easiest and most common way to run Redis at scale is to let someone else manage your Redis deployment for you.

The convenience of "database-as-a-service" offerings means that you don't have to know much about how your database scales, and that saves a lot of time and potential false starts.

We at Redis offer Redis Cloud, a highly available cloud-based Redis service that provides a lot of features you can't find anywhere else, like active-active, geo-distribution.

Redis Cloud is also really easy to use and has a free tier so you can get going quickly. So, that's the first answer. To run Redis these days, you might just use a fully-managed offering like Redis Cloud. But not everyone can or wants to use a cloud-hosted database.

There are a bunch of reasons for this. For example, maybe you're a large enterprise with your own data centers and dedicated ops teams. Or perhaps you're a mission-critical application whose SLAs are so rigid that you need to be able to dig deeply into any potential performance issue. This often rules out cloud-based deployments, since the cloud hides away the hardware and networks you're operating in. In this case, you're deploying Redis on your own. And for that, you need to know how Redis scales.

Learning this isn't just useful; it's also genuinely interesting. Sharding, replication, high availability, and disaster recovery are all important concepts that anyone can understand with the right explanation. These concepts aren't rocket science. They're no harder to understand than basic high school math, and knowing about them makes you a better developer. In this course, we'll look closely at how open source Redis scales. And you'll learn by doing, as we present a lot of the ideas through hands-on labs.

These ideas will apply whether you're deploying open source Redis on your own or managing a Redis cluster - which is, ultimately, what you'll want to reach for if you ever outgrow open source Redis. These are some important topics to consider during your time with this course. But let's first learn how to walk before we run.

We sincerely hope you enjoy what you learn with us about scaling Redis, and as always, it's my pleasure to help.

---

## Course Overview

This course is broken up into units covering topics around scaling Redis for production deployment.

Scaling means more than just performance. We have tried to identify key topics that will help you have a performant, stable, and secure deployment of Redis. This course is divided into the following units:

- **[Talking to Redis](https://redis.io/tutorials/operate/redis-at-scale/talking-to-redis/)**: Connection management, client configuration, pipelining, and Redis performance tuning best practices.
- **[Persistence and Durability](https://redis.io/tutorials/operate/redis-at-scale/persistence-and-durability/)**: Options for persisting Redis data to disk, including RDB snapshots and AOF (Append Only File) logging.
- **[High Availability](https://redis.io/tutorials/operate/redis-at-scale/high-availability/)**: How to make sure Redis and your data are always available using replication and Redis Sentinel for automatic failover.
- **[Scalability](https://redis.io/tutorials/operate/redis-at-scale/scalability/)**: Scaling Redis for both higher throughput and capacity using Redis Cluster and data sharding.
- **[Observability](https://redis.io/tutorials/operate/redis-at-scale/observability/)**: Visibility into your Redis deployment through metrics, latency monitoring, and troubleshooting techniques.

Our goal is to give you all the information you need to run Redis at scale, in whichever way is best for your organization. We hope you enjoy the course, and please don't hesitate to reach out on the course [Discord channel](https://discord.gg/ZnjZbDMDub) if you have any questions along the way.

---

## Prerequisites

Before starting this course, you should have:

- **Basic Redis knowledge** - Familiarity with Redis data structures and core commands (try the [Redis basics](https://redis.io/tutorials/) tutorials first if you're new)
- **A Linux-based system** - Access to and familiarity with a Linux environment
- **Redis installed** - Redis server and redis-cli installed and available in your `$PATH`
- **Docker and Docker Compose** - Required for the hands-on labs and exercises
- **A Git client** - For cloning exercise repositories

> **NOTE**
>
> This repo contains sample demonstrations of Redis running in various scaled configurations, and is not directly correlated with all of the exercises in this course. See the specific exercise instructions for usage.

---

## Assumptions

- Comfortable with Linux Bash shell exercises
- Legacy terminology in Redis uses 'master' and 'slave' but in the course we will use 'primary' and 'replica'. You will still see the legacy terms in many commands, configurations, and field names.
- We will use $ to indicate command line prompt and > to indicate a redis-cli prompt

---

## Next Steps

Ready to start running Redis at scale? Begin with the first unit to learn about connection management and client tuning:

> **Next**: [Talking to Redis →](https://redis.io/tutorials/operate/redis-at-scale/talking-to-redis/)

If you're already familiar with a specific topic, feel free to jump directly to any section using the [course structure](#course-structure) above.
