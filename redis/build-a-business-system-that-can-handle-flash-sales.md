---
title: "Build a business system that can handle flash sales"
source: "https://help.aliyun.com/en/redis/use-cases/use-apsaradb-for-redis-to-build-a-business-system-that-can-handle-flash-sales?spm=a2c4g.11186623.help-menu-26340.d_4_12_5.cc4140aekUL9Eh"
author:
published:
created: 2026-11-03
description: "Flash sales can spike your platform traffic by dozens or hundreds of times within minutes. Tair (Redis OSS-compatible) handles this load through a layered architecture: a Content Delivery Network (CDN) absorbs static traffic, a read/write splitting instance filters invalid order requests at over 600,000 queries per second (QPS), and a master-replica instance processes inventory deductions at over 100,000 QPS using atomic Lua scripts."
tags:
  - "clippings"
---

> [!summary]
> Alibaba Cloud's guide to a flash sale architecture on Tair (Redis OSS-compatible) that keeps traffic spikes away from row-locked database writes. It layers CDN-served static pages, a read/write splitting instance that gates order requests at over 600,000 QPS, and a master-replica instance that deducts inventory atomically at over 100,000 QPS with a Lua script using `HMGET` and `HINCRBY`. Accepted orders go onto a Redis list via `LPUSH` and `BRPOP` for asynchronous database writes, so order response time doesn't depend on database latency.

Flash sales can spike your platform traffic by dozens or hundreds of times within minutes. Tair (Redis OSS-compatible) handles this load through a layered architecture: a Content Delivery Network (CDN) absorbs static traffic, a read/write splitting instance filters invalid order requests at over 600,000 queries per second (QPS), and a master-replica instance processes inventory deductions at over 100,000 QPS using atomic Lua scripts.

**What you'll learn:**

- How flash sales traffic behaves across three phases and why databases fail under the load
- How to use a read/write splitting instance to filter invalid order requests before they reach your backend
- How to use a Lua script with `HMGET` and `HINCRBY` to deduct inventory atomically
- How to use a list-based message queue with `LPUSH` and `BRPOP` to write orders asynchronously

## How flash sales traffic works

A flash sales event sells limited quantities of items in a short window. Traffic spikes by dozens to hundreds of times compared to regular sales, but only a small fraction of requests result in actual purchases.

Traffic follows three distinct phases:

- **Before the event:** Buyers refresh the item details page continuously, generating a sustained read spike.
- **During the event:** Order requests peak simultaneously as buyers try to purchase.
- **After the event:** Buyers query order status, cancel orders, or keep refreshing to catch cancellation slots.

The core problem is that traditional databases use row-level locking to serialize inventory checks and order writes. Under high concurrency, threads queue behind the lock, response times climb, and the server stops responding.

## Architecture overview

The system uses four layers to absorb traffic before it reaches the database:

| **Layer** | **Component** | **Role** |
| --- | --- | --- |
| Static content | Browser cache + CDN | Absorbs page-refresh traffic before the event starts |
| Request filtering | Read/write splitting instance | Blocks invalid order requests during the event (>600,000 QPS) |
| Inventory deduction | Master-replica instance | Atomic inventory checks during the event (>100,000 QPS) |
| Order persistence | Master-replica instance (list queue) | Async order writes to the database |

## Layer 1: Serve item pages from CDN

Before a flash sales event, buyers refresh the item details page repeatedly. To prevent this traffic from reaching your servers, host flash sales item pages as static content — separate from regular item pages.

Static data (images, descriptions, prices) is cached in the browser and on CDN nodes. Only the place-order action requires a server round-trip. This eliminates the vast majority of pre-event traffic from your backend.

## Layer 2: Filter invalid order requests

When the event starts, the read/write splitting instance acts as a gate that tracks sale state and accepted order counts. Cache the following fields in the instance before the event begins:

```
"goodsId_count": 100   // Total number of items available
"goodsId_start": 0     // 0 = event not started; 1 = event started
"goodsId_access": 0    // Number of accepted order requests
```

The flow works as follows:

1. The server cluster reads `goodsId_start`. A value of `0` means the event has not started — reject all order requests.
2. The data control module sets `goodsId_start` to `1` to start the event.
3. The server cluster begins accepting order requests and increments `goodsId_access` for each accepted request. Remaining items = `goodsId_count - goodsId_access`.
4. When `goodsId_access` reaches `goodsId_count`, the system blocks all further order requests.

This gate lets you control exactly how many requests proceed to inventory deduction, even under extreme traffic.

## Layer 3: Deduct inventory atomically

After an order request passes the gate, the flash sales promotion server checks inventory and records the deduction. Store inventory data in the master-replica instance using a hash:

```
"goodsId" : {
    "Total": 100    // Total items in inventory
    "Booked": 0     // Items already ordered
}
```

> `goodsId` is the item ID. `Total` is the inventory count. `Booked` is the number of ordered items.

Use a Lua script to check and deduct inventory atomically. Redis executes Lua scripts as a single atomic unit using its single-threaded model, so no two requests can interleave between the read and the write:

```lua
local n = tonumber(ARGV[1])
if not n  or n == 0 then
    return 0
end
local vals = redis.call("HMGET", KEYS[1], "Total", "Booked");
local total = tonumber(vals[1])
local blocked = tonumber(vals[2])
if not total or not blocked then
    return 0
end
if blocked + n <= total then
    redis.call("HINCRBY", KEYS[1], "Booked", n)
    return n;
end
return 0
```

Load the script with `SCRIPT LOAD` instead of calling `EVAL` directly — this caches the script in the instance and reduces network bandwidth on every subsequent execution:

1. Load the script:
	```
	SCRIPT LOAD "lua code"
	```
	The instance returns the script's SHA1 hash:
	```
	"438dd755f3fe0d32771753eb57f075b18fed7716"
	```
2. Run the script using the SHA1 hash:
	```
	EVALSHA 438dd755f3fe0d32771753eb57f075b18fed7716 1 goodsId 1
	```
	A return value of `(integer) 1` means one item was successfully deducted from inventory. To verify:
	```
	HGET goodsId Booked
	```
	Returns `"1"`, confirming one item is booked.

If the script returns `n`, the deduction succeeded and the order can proceed. If it returns `0`, inventory is exhausted and the request is rejected.

## Layer 4: Write orders asynchronously

After a successful inventory deduction, write the order to a message queue in the master-replica instance rather than directly to the database. For promotions with more than 10,000 or 100,000 items, direct database writes cause lock conflicts and performance bottlenecks. Writing to the queue is treated as a successfully placed order.

The instance stores orders in a list:

```
orderList {
     [0] = {Order content}
     [1] = {Order content}
     [2] = {Order content}
     ...
 }
```

The flash sales system pushes orders to the list:

```
LPUSH orderList {Order content}
```

The asynchronous ordering module reads from the list and writes to the database in order:

```
BRPOP orderList 0
```

This decouples the order-placement response time from database write latency.

## Keep promotion data in sync

After the event ends, traffic shifts to order authentication failures and refund requests. The data control module regularly recomputes data in the database and syncs it to the master-replica instance, which then propagates to the read/write splitting instance. This keeps the cached state consistent with the actual order data throughout the post-event period.
