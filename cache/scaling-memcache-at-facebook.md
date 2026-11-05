---
title: "Scaling Memcache at Facebook"
source: "https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala"
author:
  - "[[Rajesh Nishtala]]"
  - "[[Hans Fugal]]"
  - "[[Steven Grimm]]"
  - "[[Marc Kwiatkowski]]"
  - "[[Herman Lee]]"
  - "[[Harry C. Li]]"
  - "[[Ryan McElroy]]"
  - "[[Mike Paleczny]]"
  - "[[Daniel Peek]]"
  - "[[Paul Saab]]"
  - "[[David Stafford]]"
  - "[[Tony Tung]]"
  - "[[Venkateshwaran Venkataramani]]"
published:
created: 2026-11-05
description:
tags:
  - "clippings"
---

> [!summary]
> USENIX NSDI 2013 landing page for the paper on how Facebook built a distributed key-value store on memcached, handling billions of requests per second and trillions of items; the clip holds the abstract and PDF, slides, and audio links, not the paper's full text. Michael Piatek's public summary calls it a roadmap for scaling the sharded SQL stack through cache-database coordination and failover handling. Piatek also notes that the system's semantics are hard to state precisely, making it a counter-example to the belief that strong semantics are essential at scale.

Rajesh Nishtala, Hans Fugal, Steven Grimm, Marc Kwiatkowski, Herman Lee, Harry C. Li, Ryan McElroy, Mike Paleczny, Daniel Peek, Paul Saab, David Stafford, Tony Tung, and Venkateshwaran Venkataramani, *Facebook Inc.*

Memcached is a well known, simple, in memory caching solution. This paper describes how Facebook leverages memcached as a building block to construct and scale a distributed key-value store that supports the world’s largest social network. Our system handles billions of requests per second and holds trillions of items to deliver a rich experience for over a billion users around the world.

## Rajesh Nishtala, Facebook Inc.

## Hans Fugal, Facebook Inc.

## Steven Grimm, Facebook Inc.

## Marc Kwiatkowski, Facebook Inc.

## Herman Lee, Facebook Inc.

## Harry C. Li, Facebook Inc.

## Ryan McElroy, Facebook Inc.

## Mike Paleczny, Facebook Inc.

## Daniel Peek, Facebook Inc.

## Paul Saab, Facebook Inc.

## David Stafford, Facebook Inc.

## Tony Tung, Facebook Inc.

## Venkateshwaran Venkataramani, Facebook Inc.

## Open Access Media

USENIX is committed to Open Access to the research presented at our events. Papers and proceedings are freely available to everyone once the event begins. Any video, audio, and/or slides that are posted after the event are also free and open to everyone. [Support USENIX](https://www.usenix.org/annual-fund) and our commitment to Open Access.

BibTeX

@inproceedings {180324,
author = {Rajesh Nishtala and Hans Fugal and Steven Grimm and Marc Kwiatkowski and Herman Lee and Harry C. Li and Ryan McElroy and Mike Paleczny and Daniel Peek and Paul Saab and David Stafford and Tony Tung and Venkateshwaran Venkataramani},
title = {Scaling Memcache at Facebook},
booktitle = {10th USENIX Symposium on Networked Systems Design and Implementation (NSDI 13)},
year = {2013},
isbn = {978-1-931971-00-3},
address = {Lombard, IL},
pages = {385--398},
url = {https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala},
publisher = {USENIX Association},
month = apr
}

[Download](https://www.usenix.org/biblio/export/bibtex/180324)

[Nishtala PDF](https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf "nsdi13-final170_update.pdf")

[View the slides](https://www.usenix.org/sites/default/files/conference/protected-files/nishtala_nsdi13_slides.pdf)

## Presentation Video

#### Presentation Audio

<audio controls=""><source src="https://2459d6dc103cb5933875-c0245c5c937c5dedcca3f1764ecc9b2f.ssl.cf2.rackcdn.com/nsdi13/nishtala.mp3"> <a href="https://2459d6dc103cb5933875-c0245c5c937c5dedcca3f1764ecc9b2f.ssl.cf2.rackcdn.com/nsdi13/nishtala.mp3">MP3 Download</a></audio>

[Download Audio](https://2459d6dc103cb5933875-c0245c5c937c5dedcca3f1764ecc9b2f.ssl.cf2.rackcdn.com/nsdi13/nishtala.mp3)

Public Summary:

*by Michael Piatek*

Responsiveness is essential for web services. Speed drives user engagement, which drives revenue. To reduce response latency, modern web services are architected to serve as much as possible from in-memory caches. The structure is familiar: a database is split among servers with caches for scaling reads.

Over time, caches tends to accumulate more responsibility in the storage stack. Effective caching makes issuing costly queries feasible, even on the critical response path. Intermediate or highly transient data may never need to be written to disk, assuming caches are sufficiently reliable. Eventually, the state management problem is flipped on its head. The cache becomes the primary data store, without which the service cannot function.
This is a common evolution path with common pitfalls. Consistency, failure handling, replication, and load balancing are all complicated by relying on soft-state caches as the de-facto storage system. This paper describes how Facebook has engineered their caching layer, based on memcached, to cope with these issues.

The techniques described provide a valuable roadmap for scaling the typical sharded SQL stack: improvements to the software implementation, coordination between the caching layer and the database to manage consistency and replication, as well as failover handling tuned to the operational needs of a billion-user system. Most of these techniques are reusable, making this a must-read paper for anyone building large-scale web services today.

While the ensemble of techniques described by the authors has proven remarkably scalable, the semantics of the system as a whole are difficult to state precisely. Memcached may lose or evict data without notice. Replication and cache invalidation are not transactional, providing no consistency guarantees. Isolation is limited and failurehandling is workload dependent. Won't such an imprecise system be incomprehensible to developers and impossible to operate?
For those who believe that strong semantics are essential for building large-scale services, this paper provides a compelling counter-example. In practice, performance, availability, and simplicity often outweigh the benefits of precise semantics, at leastfor one very large-scale web service.
