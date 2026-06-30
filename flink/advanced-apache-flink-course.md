---
title: "Advanced Apache Flink Course"
source: "https://streamacademy.io/course/advanced-apache-flink/"
author:
published: 2025-11-13
created: 2026-06-29
description: "Advanced Apache Flink: Deep dive into modern Flink 2 internals, DataStream & Table APIs, custom operators, and production best practices. Intensive course with hands-on workshops"
tags:
  - "clippings"
---

> [!summary]
> An advanced, vendor-neutral online course on Apache Flink 2.1+ that goes beyond documentation to teach Flink internals via source code, covering the DataStream and Table/SQL APIs, custom operators, and state management. It progresses from core APIs through efficient pipeline architecture to production deployment on Kubernetes, with hands-on workshops and a certificate of completion. Taught by Yaroslav Tkachenko, a data streaming specialist formerly at Activision, Shopify, and Goldsky.

## Advanced Apache Flink

Deep dive into modern Flink internals, production deployment, and advanced patterns

100% Online Training Watch On-demand Certificate Included

## Course Syllabus

### Course Overview

This bootcamp-style course takes you deep into Apache Flink internals and production best practices. Learn how Flink really works by studying the source code, master both DataStream and Table APIs, and gain hands-on experience building custom operators and production-ready pipelines.

This course covers **modern** versions of Apache Flink (2.1+). Also, it's **vendor-neutral**: it doesn't promote any specific vendor solutions, only open-source tools.

Most importantly, **this is an advanced course**. Many courses repeat what’s already in the documentation. This course is different: you won’t just learn what a sliding window is — you’ll learn the core building blocks that let you design any windowing strategy from the ground up.

Finally, you can treat this course as **training**. In fact, we use all the materials from this course in corporate training.

![](https://www.youtube.com/watch?v=yvaoEedYiy4)

### Prerequisites

##### Technical Knowledge

- Good understanding of Apache Flink basics (DataStream or Table API)
- Proficiency with Java
- Understanding of distributed systems concepts

##### Ideal Experience

- 1+ years working with Flink or similar streaming systems
- Familiarity with Kubernetes is helpful but not required

### Course Curriculum

- About This Course
- Overview: Deep Dive Into a Flink Pipeline

---

##### Flink Core APIs

###### 📚 Lessons

- Mastering DataStream API
- DataStream API: Data Routing
- DataStream API: State Management & Evolution
- DataStream API: Custom Watermark Strategies
- Mastering Table & SQL API
- Table API: State Evolution & Compiled Plans
- Workshop: SQL Query Evolution
- Mastering Connectors
- Workshop: Building Custom Operators

###### ⭐️ Key Takeaways

- Low-level Flink operator implementation
- State and timers as core primitives
- Data shuffling strategies
- Practical usage of the State Processor API and Compiled Plans for state evolution
- Changelog semantics
- Table Planner and Executor design, understanding query plans
- Efficient UDF implementation including PTFs (Process Table Functions)

---

##### Architecting Efficient Pipelines

###### 📚 Lessons

- Efficient Dataflows
- Data Enrichment
- Data Skew
- Batch API
- Workshop: Pipeline Design

###### ⭐️ Key Takeaways

- Flink pipeline design, applying changelog semantics end-to-end
- Serialization best practices
- Data enrichment strategies

---

##### Flink in Production

###### 📚 Lessons

- Deployment
- Deployment: Flink Kubernetes Operator
- Deployment: SQL-centric Workloads
- Reliability
- Observability
- Building a Control Plane
- Performance & Tuning
- Benchmarking & Profiling
- Workshop: Production-Ready Pipeline in Kubernetes

###### ⭐️ Key Takeaways

- Choosing right resources for your job
- Using the Flink Kubernetes Operator efficiently
- Best practices for running Flink in production at scale

Please note: the course curriculum is subject to change

### Certificate of Completion

All participants who complete the course and the hands-on workshops will receive a Certificate of Completion for the Advanced Apache Flink course.

## Instructor

#### Yaroslav Tkachenko, Lead Instructor

- Yaroslav has been building software for more than fifteen years, focusing on data platform engineering and data streaming in the past eight years.
- Yaroslav was a tech lead at Activision and Shopify, driving major initiatives with technologies like Apache Kafka and Apache Flink.
- Later, Yaroslav spent several years as a founding engineer at Goldsky, building a self-managed data streaming platform based on Apache Flink.
- Yaroslav is an [international speaker](https://sap1ens.com/talks/), author of the [Data Streaming Journal](https://www.streamingdata.tech/) newsletter, [Confluent Catalyst](https://developer.confluent.io/catalysts/yaroslav-tkachenko/) and the founder of [Irontools](https://irontools.dev/).

![](https://streamacademy.io/images/yaroslav.jpg)

## Testimonials

![Paolo Rampazzo](https://streamacademy.io/images/people/paolo.jpeg)

"Two very intense and content packed days. What really stood out was how deep Yaroslav went into Flink's internal library structure, explaining in detail the purpose and behavior of the core objects being used. That level of depth was honestly mind blowing. A complete, deep, and hands on bootcamp."

##### Paolo Rampazzo

Big Data Architect @ Caylent

🎓 January 2026 Cohort ![Ryan van Huuksloot](https://streamacademy.io/images/people/ryan.jpeg)

"I had the privilege of working with Yaroslav Tkachenko at Shopify, and it's rare to find someone with his depth of expertise across the entire streaming stack combined with an exceptional ability to make complex topics accessible. If you're serious about mastering streaming technologies, learning from someone with Yaroslav's real-world, battle-tested experience is an opportunity you don't want to miss."

##### Ryan van Huuksloot

Staff Engineer @ Shopify

![Sujay Jain](https://streamacademy.io/images/people/sujay.jpeg)

"I’ve been running large-scale streaming systems for years, and Yaroslav consistently stands out as someone who really understands Flink. His experience with stateful stream processing, best practices, and production patterns goes beyond what you typically see in documentation. The Advanced Apache Flink course looks genuinely useful for anyone looking to level up."

##### Sujay Jain

Senior Software Engineer @ Netflix

![Dionysios Stolis](https://streamacademy.io/images/people/dionysios.jpeg)

"An excellent training for anyone looking to master Apache Flink. Yaroslav guided us from understanding Flink internals and the core codebase all the way to practical deployment techniques. If you want to move beyond the basics and understand how Flink actually works under the hood, this is the course to take."

##### Dionysios Stolis

Machine Learning Engineer @ Just Eat

🎓 January 2026 Cohort ![Furkan Alaybeg](https://streamacademy.io/images/people/furkan.jpeg)

"As a Big Data Engineer working with real-time systems, this experience helped me go far beyond simply "using Flink" and truly understand how it works under the hood. We explored Flink’s pipeline anatomy — from SQL planning and code generation to network exchange, stream tasks, and state backends in Java. From fundamentals to production topics such as connector design, custom stateful operators, statement sets, and deployment strategies made the bootcamp especially valuable."

##### Furkan Alaybeg

Big Data & AI Engineer @ Vodafone

🎓 January 2026 Cohort ![Xiao Meng](https://streamacademy.io/images/people/xiao.jpeg)

"I've been fortunate to work with Yaroslav at both Activision and Goldsky. He's a first-principles thinker who excels at explaining trade-offs in complex topics. His expertise spans the entire streaming ecosystem - from zero-to-one platform design to production operations, Flink internals, and real-world war stories. Moreover, he's remarkably generous and patient when sharing knowledge. Anyone taking this course will greatly benefit from his deep expertise and practical insight."

##### Xiao Meng

Software Engineer @ Goldsky
