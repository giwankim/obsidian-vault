---
title: "Sending Reliable Event Notifications with Transactional Outbox Pattern"
source: "https://medium.com/event-driven-utopia/sending-reliable-event-notifications-with-transactional-outbox-pattern-7a7c69158d1b"
author:
  - "[[Dunith Danushka]]"
published: 2021-07-12
created: 2026-06-30
description: "Friends don’t let friends do dual writes!"
tags:
  - "clippings"
---

> [!summary]
> Explains why "dual writes" — separately updating a database and publishing to a message broker — leave distributed systems inconsistent when one write fails, and how the Transactional Outbox pattern fixes it by writing the aggregate change and an OUTBOX record within one local ACID transaction. A message relay then publishes those OUTBOX entries to the broker, best implemented via log-based CDC (e.g., Debezium) rather than exhaustive polling. Because delivery is at-least-once, consumers should stay idempotent — e.g., an INBOX table tracking processed event UUIDs.

## Friends don’t let friends do dual writes!

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/0*qMFodG3kf2AtEy8i)

Photo by Brett Jordan on Unsplash

Although the Microservices maintain their state private to them, they hardly operate in isolation. Some business use cases require them to change their state first, then notify that change to a broader audience.

The [Transactional Outbox](https://microservices.io/patterns/data/transactional-outbox.html) pattern describes an approach for services to execute these two tasks atomically.

In this post, I discuss why dual writes in distributed systems are bad, how you can fix that with the outbox pattern, and some inner workings of the pattern. This post doesn’t stand up as an implementation guide but instead brings in the fundamentals you should use when implementing in production.

## The problem with dual writes

Imagine there are two microservices; the Order service and the Shipping service. The business logic states the Order service should notify the Shipping service about a new order reception to prepare a shipment.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*9y1sztLbXlRTES8iJ6o0rw.png)

What are the options we have here?

**Synchronous approach:** The Order service synchronously invokes an API method of the Shipping service to do the notification. The drawback is that it introduces a coupling between two services. The Order service must depend on the Shipping service’s availability, dealing with retries, rate limits, etc. Considering the scalability, we can rule this approach out.

**Asynchronous approach:** The Order service inserts the new Order into its database. Then publishes a [domain event](https://microservices.io/patterns/data/domain-event.html) to a message broker describing the state change that happened. The Shipping service that subscribed to that event eventually receives the event and prepares the shipment.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*5svc7TChGSLj5Qu0Hm_1DA.png)

Event-driven notification with domain events

The asynchronous approach appears to be a fitting solution in terms of scalability. But what could be the possible odds?

> The main problem is that the Order service must update two systems simultaneously — the database and the message broker. That is called making a “ ***dual write,***” which is considered an original sin in distributed systems literature.

==A failure to update two systems atomically leaves the entire system in an inconsistent state.==

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*9MaF8X-9vcRza6KtKix3BA.png)

The sequence of two operations

As per the above sequence diagram, if the event publishing fails due to a broker outage, we will have an order in the system but without a shipment. Also, if the new order insertion fails due to a database error, the event anyway gets published. That creates a shipment without a corresponding order.

This problem related to dual writes demands us to be on the lookout for a solution to make the database update and event publishing atomic.

## The Transactional Outbox pattern

The Transaction Outbox pattern solves this problem by writing to two database tables, the aggregate table and an OUTBOX table, within the same transaction scope and then use the content written to the OUTBOX table to drive the event publishing process.

The pattern comprises two components.

1. The OUTBOX table.
2. The message relay.

### The OUTBOX table

The pattern introduces a supplementary table, called OUTBOX, to the service’s database. This table stores the event notifications that are supposed to send from the service to the message broker. When service writes to the aggregate table, it also writes a record to the OUTBOX table as a part of the same transaction.

The record written to the OUTBOX table describes a change event that happened in the service. For example, it could be a new customer registration or a customer changing the email address.

### The message relay

The message relay component asynchronously monitors the OUTBOX table for new entries. If any, they will be transformed into events and published to the message broker.

Once published, the message will be deleted from the OUTBOX table to prevent reprocessing and the table growth.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*FvKGbWicxxqOBSqCQZ3PHA.png)

The Outbox pattern architecture — Credits

## The OUTBOX table format

The OUTBOX table should have the following structure at a minimum.

```c
create table OUTBOX (
 id varchar(255) primary key,
 aggregate_type varchar(255) not null,
 aggregate_id varchar(255) not null,
 type varchar(255) not null,
 payload text not null
);
```
- ***id*:** unique id of each message; can be used by consumers to detect any duplicate events.
- ***aggregate\_type***: the type of the *aggregate root* to which a given event is related. That comes from the Domain-Driven Design (DDD), where the exported event should be associated with an aggregate root. In our example, this is the Order.
- ***aggregate\_id:*** this is the ID of the aggregate object affected by the update operation. That can be the order ID here. The Shipping service will use it as a reference to the shipment record.
- ***type***: type of the event. For example, “ *OrderCreated*.”
- ***payload***: a JSON representation of the actual event content. For instance, it contains the order ID, customer ID, total, etc.

## How this solves the dual write problem?

The Outbox pattern enables achieving atomicity when writing to the database and publishing events to the broker. We can leverage the power of local transactions to do both actions or nothing.

### At least once delivery of change events

By writing a record to the OUTBOX table, we benefit from the at-least-once delivery guarantee for the change event. In case of a broker outage, the message relay can retry reliably after reading OUTBOX messages. The broker may not be reachable for hours or days. But we have a persistent record of the message to be sent when the broker is back online. That way, we can guarantee that the **change** **event will reach the broker at least once**.

### Prevent fake event publication with clean rollbacks

Furthermore, we can benefit from a local ACID transaction when writing to both tables at the same time. **If writing to either of the tables fails, we will have a clean rollback**. That prevents fake messages from getting published to the broker. Fake message as in, the aggregate table update could’ve failed, but an event has been published to the broker.

## Challenges — Sending duplicate events

After publishing an event, the message relay deletes the corresponding record in the OUTBOX table to prevent reprocessing. The logic would look like the following:

```c
for (OutboxMessage message:messages) {
    brokerConnection.publish(message.toOutboxEvent());
    outboxTable.delete(message);
}
```

But the message relay may fail to do so if it crashes during the attempt to delete the record. When it restarts, it sees the same record, thus publishes it to the broker for the second time.

That is one challenge often associated with the Outbox pattern. We can fix it by making the downstream event consumer idempotent.

## Duplicate detection with an idempotent consumer

A failure in the message relay to delete the OUTBOX record, a message broker restart, or an unknown error may cause the event consumer to receive duplicate events. Achieving exactly once semantics in a distributed system is a challenge we all have to face.

Shipping service in our example might receive the same Order twice so that it would prepare the same shipment twice, which is not acceptable. The consumer can prevent this by checking whether the event with the given UUID has been processed before. If so, any further calls for that same event will be ignored.

Similar to the OUTBOX table, we can maintain an INBOX table inside the consumer service’s database. It simply keeps track of what events were processed by recording their UUIDs.

After processing an event for the first time, the consumer marks the event as processed in the INBOX table. That should be transactional — making it possible to trap any rollbacks at the consumer level so that it can retry receiving the event.

![](https://miro.medium.com/v2/resize:fit:1100/format:webp/1*71dEGAbPn8jl93Fd9Dm2bA.png)

Making the consumer service idempotent by adding an INBOX table

## Pattern implementation choices

I would say implementing this pattern is straightforward. All you need is a programming language that supports transactional writes to a database.

A simple Java code sample for sending events to the OUTBOX should look like the following:

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*93kNs55dZZeNSGRYmPmBNg.png)

Implementation is based on Quarkus, Debezium, and Kafka

The challenge comes after. That is, implementing the message relay. There are two strategies you can consider.

### Polling publisher

This publisher publishes messages by polling the OUTBOX table for new entries. Frequent polling will exhaust the database soon. Hence this is not a scalable solution. You can read Kamil Grzybek’s [post](http://www.kamilgrzybek.com/design/the-outbox-pattern/) about implementing a polling message relay with.NET.

### Message relay based on Change Data Capture (CDC)

Here, you have a transaction log mining component that tails the database transaction log to capture the changes made to the OUTBOX table. The transaction log records all transactions committed against the database in a strongly ordered manner. The miner reads the transaction log and publishes each change as a message to the message broker.

This process is often referred to as [Log-based Change Data Capture](https://debezium.io/blog/2018/07/19/advantages-of-log-based-change-data-capture/). Unlike the polling counterpart, event capture happens with a very low overhead in near-real-time.

I would recommend [Debezium](https://debezium.io/) as the best solution to implement a CDC-based message relay. Once you configure Debizium to listen to your OUTBOX table, it’ll take things from there. That way, changes made to the OUTBOX table will end up in a Kafka topic.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*YLcHfN844wVFcBBpDJ13LQ.png)

Implementing outbox pattern with Debezium and Kafka — Source

## Practical use cases

In general, this pattern can be used to propagate state changes among Microservices reliably. Some use cases are as follows.

- **Sending reliable notifications to other services:** The sender can guarantee that the message will be delivered to the receiver at least once.
- **Sending event notifications in choreography-based** [**Sagas**](https://microservices.io/patterns/data/saga.html): One service can reliably notify others about its state change.
- **Updating query-side materialized views:** To reliably notify query-side Microservices about the state changes on the command side so that they can update their materialized views.

## Takeaways

- When sending notifications amongst microservices, use an asynchronous, event-driven approach for better reliability and scalability.
- While doing so, dual writes are inevitable. Hence use the Outbox pattern to avoid that and introduce reliable delivery for notifications.
- There are few implementation choices for the pattern, but a log-based CDC approach seems the popular choice.
- The pattern might deliver duplicate notifications. But you should make the consumers idempotent to avoid that.

## References

[Transaction Outbox](https://microservices.io/patterns/data/transactional-outbox.html) — Chris Richardson

[Reliable Microservices Data Exchange With the Outbox Pattern](https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/) — Gunnar Morling
