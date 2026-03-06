---
title: "Distributed Locking With PostgreSQL and Spring Boot"
source: "https://javabulletin.substack.com/p/distributed-locking-with-postgresql"
author:
  - "[[Suraj Mishra]]"
published: 2026-01-15
created: 2026-01-26
description: "Locks, PostgreSQL, Code , Examples and more."
tags:
  - "clippings"
---
### Locks, PostgreSQL, Code, Examples and more.

### Introduction

In modern microservices and high-traffic applications, multiple instances of your service often run concurrently. They may try to access the same resource—like refreshing a cache, updating a shared counter, or processing the same job—at the same time. Without coordination, this can lead to **race conditions, redundant work, or even database overload**.

This is where **distributed locking** comes in. A distributed lock ensures that **only one service instance at a time can perform a critical operation**, even if multiple servers are running in parallel.

We may think that we need a fancy distributed system like Redis, ZooKeeper, DynamoDB, or etcd to achieve this. Surprisingly, we can implement **effective distributed locks using a single PostgreSQL instance** that all our services share. Combined with **Spring Boot**, this provides a simple, robust solution without extra infrastructure.

---

#### Why Use Distributed Locks?

Consider a scenario: Spring Boot app caches user profiles from the database. When the cache entry expires, multiple requests hit at the same time. Without a lock:

- All app instances may simultaneously fetch the same data from the DB
- Database load spikes unexpectedly
- Cache stampedes happen, slowing down all users

With a distributed lock:

- Only **one instance refreshes the cache**
- Others either wait or continue serving stale data
- Database load is controlled, and performance stays consistent

#### PostgreSQL Advisory Locks

PostgreSQL provides **advisory locks**, which are lightweight application-level locks. Key properties:

- **Session-level**: held until connection closes, can be **blocking** (`pg_advisory_lock`) or **non-blocking** (`pg_try_advisory_lock`)
- **Transaction-level**: released at the end of the transaction, can be blocking (pg\_advisory\_xact\_lock), can be non-blocking (pg\_try\_advisory\_xact\_lock)

These locks are **global to all clients connecting to the same database**, so multiple Spring Boot instances can coordinate using them.

**Example SQL:**

**Blocking:**

![](https://substackcdn.com/image/fetch/$s_!77BL!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Ffaad8e60-4bdd-4eb8-9689-a5b9abab6b27_1104x532.png)

**Non-blocking:**

![](https://substackcdn.com/image/fetch/$s_!4CXL!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F6a018056-02f6-4167-88ad-65b307ff7d1b_1102x524.png)

---

**📢 📢 📢 Get actionable Java insights every week — from practical code tips to expert interview questions you can use today.**

Join 3400+ subscribers and level up your Spring & backend skills with hand-crafted content — no fluff.

**[I want to offer an additional 40% discount ($ 18 per year) until January 31st.](https://javabulletin.substack.com/subscribe?coupon=7b424e8b)**

**[Subscribe now](https://javabulletin.substack.com/subscribe?coupon=7b424e8b)**

Not convinced? Check out the **[details of the past work](https://javabulletin.substack.com/about)**

![](https://substackcdn.com/image/fetch/$s_!Lfvk!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F296fa0f3-c19e-4787-8e8c-d7320e608768_1592x632.png)

---

#### Spring Boot Implementation

With Spring Boot, we can create a service class that provides lock and unlock method wrappers on top of SQL functions we saw earlier.

If we use a native query:

![](https://substackcdn.com/image/fetch/$s_!A24L!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F01168729-45a7-40d8-b38a-c6dc9a21f042_1886x1336.png)

Using `@Transactional` ensures **same connection**, which is crucial for advisory locks.

We can also use Repository, with a native query:

![](https://substackcdn.com/image/fetch/$s_!WLos!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F71553ea4-7c35-4656-97c8-d0a18a96ae54_1278x990.png)

#### About lockId:

- PostgreSQL advisory locks don’t know anything about your application.
- They just **lock a 64-bit integer (BIGINT)** or **two 32-bit integers**.
- You can choose **any value**, as long as **all sessions that want the same lock use the same value**.
- PostgreSQL also allows:
```markup
SELECT pg_try_advisory_lock(key1, key2);
```
- Useful if you want to **combine two values** (e.g., app ID + user ID) without generating a big number manually.
- Example:
```markup
int appId = 123;
int userId = 456;
em.createNativeQuery("SELECT pg_try_advisory_lock(:key1, :key2)")
  .setParameter("key1", appId)
  .setParameter("key2", userId)
  .getSingleResult();
```

#### Service Layer

![](https://substackcdn.com/image/fetch/$s_!lLXv!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F49fee908-6b9f-4669-83f4-7c7169eacd26_1094x1460.png)

#### Benefits

- No extra infrastructure needed: uses your existing PostgreSQL database
- Safe across multiple Spring Boot instances
- Prevents cache stampedes or duplicate work
- Simple to implement and monitor

---

#### Caveats

- The lock is tied to a single DB instance; if the database goes down, locking fails
- Locks are connection-dependent: if the connection drops unexpectedly, the lock is released
- Not suitable for multi-database or geo-distributed setups without extra coordination.

---

#### Conclusion

Distributed locks are essential for preventing race conditions in high-concurrency environments. Using PostgreSQL advisory locks with Spring Boot is a **simple, effective, and production-ready approach**. It’s especially handy for cache refreshes, job processing, or any shared resource where only one instance should act at a time.

With this pattern, Spring Boot apps stay **fast, safe, and predictable**, without introducing extra distributed systems into your stack.

---

**📢 📢 📢 Get actionable Java insights every week — from practical code tips to expert interview questions you can use today.**

Join 3400+ subscribers and level up your Spring & backend skills with hand-crafted content — no fluff.

**[I want to offer an additional 40% discount ($ 18 per year) until January 31st.](https://javabulletin.substack.com/subscribe?coupon=7b424e8b)**

**[Subscribe now](https://javabulletin.substack.com/subscribe?coupon=7b424e8b)**

Not convinced? Check out the **[details of the past work](https://javabulletin.substack.com/about)**

![](https://substackcdn.com/image/fetch/$s_!Yr6g!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fad724a53-d2a8-4ee9-beb1-c1a055623b32_1592x632.png)

---

> #### Helpful Resources (7)

- **[32+ Real-World Use Case-Based Java/Spring Boot Interview Questions](https://javabulletin.substack.com/p/java-interview-questions)**
- **[Everything Bundle (Java + Spring Boot + SQL Interview + Certification)](https://gumroad.com/a/748969683/sowpfg)**
- **[Master DynamoDB with this premium course from Alex DeBrie](https://alexdebrie.gumroad.com/l/WPLqz?a=708943571)**
- **[Crack System Design Interview With Right Preparation](https://www.bugfree.ai/?via=suraj)**
- **[Get Your Hands Dirty on Clean Architecture (2nd edition)](https://leanpub.com/get-your-hands-dirty-on-clean-architecture/c/java-bulletin)**
- **[Top Java & Spring Boot Blogs](https://javabulletin.substack.com/archive?sort=top)**
- **[Interesting Java/Spring Boot Quizzes](https://javabulletin.substack.com/p/pro-quizzes)**
