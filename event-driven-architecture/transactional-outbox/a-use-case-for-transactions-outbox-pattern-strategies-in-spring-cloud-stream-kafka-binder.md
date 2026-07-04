---
title: "A Use Case for Transactions: Outbox Pattern Strategies in Spring Cloud Stream Kafka Binder"
source: "https://spring.io/blog/2023/10/24/a-use-case-for-transactions-adapting-to-transactional-outbox-pattern"
author:
published:
created: 2026-07-04
description: "Level up your Java code and explore what Spring can do for you."
tags:
  - "clippings"
---

> [!summary]
> Final part of Spring's six-part series on transactions in Spring Cloud Stream Kafka applications, covering the transactional outbox pattern and lighter-weight alternatives to it. Shows how synchronizing Kafka transactions with JPA transactions — in both producer-initiated and consume-process-produce flows — achieves similar semantics without an outbox table or polling process. Warns these shortcuts lack the outbox pattern's crash fault-tolerance: if the app dies after the database commit but before the Kafka publish, state becomes inconsistent.

**Other parts in this blog series**

Part 1: [Introduction to Transactions in Spring Cloud Stream Kafka Applications](https://spring.io/blog/2023/09/27/introduction-to-transactions-in-spring-cloud-stream-kafka-applications)

Part 2: [Producer Initiated Transactions in Spring Cloud Stream Kafka Applications](https://spring.io/blog/2023/09/28/producer-initiated-transactions-in-spring-cloud-stream-kafka-applications)

Part 3: [Synchronizing with External Transaction Managers in Spring Cloud Stream Kafka Applications](https://spring.io/blog/2023/10/04/synchronizing-with-external-transaction-managers-in-spring-cloud-stream)

Part 4: [Transactional Rollback Strategies with Spring Cloud Stream and Apache Kafka](https://spring.io/blog/2023/10/11/transactional-rollback-strategies-with-spring-cloud-stream-and-apache-kafka)

Part 5: [Apache Kafka’s Exactly-Once Semantics in Spring Cloud Stream Kafka Applications](https://spring.io/blog/2023/10/16/apache-kafkas-exactly-once-semantics-in-spring-cloud-stream-kafka)

In this last part of this blog series, we dive into a relatively new design pattern first proposed by [Chris Richardson](https://microservices.io/book) but seeing it from the perspective of Spring Cloud Stream. We will see what the outbox pattern is, how it works, and a few strategies to adapt when using Spring Cloud Stream and Apache Kafka. See the descriptions [here](https://microservices.io/patterns/data/transactional-outbox.html) for an introduction to how the Outbox pattern works.

### Quick Summary of the Outbox Pattern

In a nutshell, the outbox pattern ensures the delivery of a database or external system and publishing to a messaging system within a single atomic unit by strictly avoiding [two-phase commits (2PC)](https://martinfowler.com/articles/patterns-of-distributed-systems/two-phase-commit.html).

In the outbox pattern, the developer needs to follow these steps:

1. The processor method receives the message.
2. In its logic, it first engages with the database transactionally and then creates a new record in a particular table called the outbox within the same transaction.
3. An external process queries this outbox table and publishes the message to Kafka.
4. The record is removed from the outbox table once the Kafka publishing succeeds.

**Here is a diagrammatic view of this flow:**

![outbox-pattern-txn-blog-part-6](https://github.com/spring-cloud/spring-cloud-stream/raw/gh-pages/images/outbox-pattern-txn-blog-part-6.png)

The result is that the **end-to-end** flow of events is semantically done in a transactional manner. We wrote, “semantically,” because the process that updates the messaging system, in this case, is outside the database transaction yet achieves the data integrity guarantee that a transactional system guarantees. If the database write was successful, the downstream process sees that and publishes the record from the outbox table to the Kafka topic. If the database transaction doesn’t succeed, nothing is written to Kafka. It is important to note that we still need to use synchronization during the Kafka publishing part and during the removal of the outbox record.

An important benefit of using the outbox pattern is that it avoids complex transactions strategies such as distributed 2 phase commits (2-PC) or cooridinating the various commits using a single shared transactional resource etc. But still gives you the semantic benefits of a distributed transaction by introducing some extra processes such as persisting the event to an outbox table and then based on this let another process publish the event to the message broker.

### Adapting to Outbox pattern in Spring Cloud Stream

The outbox pattern works in many different use cases that involve message brokers. If your use case specifically requires the usage of this pattern, you can implement this pattern as prescribed. However, in this blog, we show you some alternative strategies when it comes to these use cases if you are a Spring and Apache Kafka user and can relax the strict rules for following the outbox pattern.

Although, conceptually, the outbox design pattern is a good abstraction for messaging systems in general when an application wants to avoid 2PC, as we discussed in [part 3](https://spring.io/blog/2023/10/04/synchronizing-with-external-transaction-managers-in-spring-cloud-stream) of this series, with Apache Kafka and Spring Cloud Stream, there are some options if you don't need the full-blown support of the outbox pattern. First, there are complexities in the implementation, such as the need for the application to maintain an extra database table for outbox, extra code to consume it and then publish to Kafka, more code to delete it explicitly from it after the message gets published, and so on.

When writing Spring Cloud Stream Kafka applications, we can avoid this complexity by relying on the transactional support available in Spring Cloud Stream through Spring for Apache Kafka.

Imagine a service written for the same order-service as above but rewritten as a transactional Spring Cloud Stream application. As with the original outbox pattern’s premise of avoiding 2PC, we don’t have to use a 2-phase commit with distributed transaction managers in this model as well. At the same time, we can also avoid needing the extra outbox table and external code for querying it and publishing it to the Kafka topic. All this could be done within the scope of a single atomic unit when using transactional support in the Spring Cloud Stream Kafka ecosystem. As we saw in our detailed analysis in [part 3](https://spring.io/blog/2023/10/04/synchronizing-with-external-transaction-managers-in-spring-cloud-stream), the Kafka transaction synchronizes with the database transaction.

There are a few caveats to keep in mind when looking at this as an alternative strategy for the outbox pattern. The ideas presented here are **not** the complete semantical equivalent of what outbox pattern provides. If your use case needs that level of guarantee, it is recommended to use the outbox pattern directly. In the sections below, we call out the situations, where the solutions lack the full guarantee of the outbox pattern.

### Outbox pattern semantics in producer-initiated applications

In [part 2](https://spring.io/blog/2023/09/28/producer-initiated-transactions-in-spring-cloud-stream-kafka-applications) of the series, we saw producer-initiated transactions:

```java
@Autowired
Sender sender;

@PostMapping("/send-data")
public void sendData() throws InterruptedException {
   sender.send(streamBridge, repository);
}

@Component
static class Sender {

   @Transactional
   public void send(StreamBridge streamBridge, OrderRepository repository){
       Order order = new Order();
       order.setId("order-id");

       Order savedOrder = repository.save(order);

       OrderEvent event = new OrderEvent();
       event.setId(savedOrder.getId());
       event.setType("OrderType");
       streamBridge.send("process-out-0", event);
   }
}
```

The main trigger for the workflow is a REST endpoint, which calls a method annotated with `@Transactional`. The transaction interceptor starts the JPA transaction, and the database operation occurs, but no commit happens as part of it since the method is in the middle of a transaction. After this, we publish to Kafka through the `StreamBridge` send method. The `KafkaTemplate` used by `StreamBridge` uses a transactional producer factory (assuming we set the `transaction-id-prefix`). Rather than starting a new Kafka transaction, the transactional resource synchronizes with the JPA transaction. When the method exits, the JPA commits first, followed by the synchronized Kafka one. As you can see, it accomplishes the same result proposed by the outbox pattern by using different strategies.

**Here is a visual representation of this flow:**

![producer-init-txn-blog-part-6](https://github.com/spring-cloud/spring-cloud-stream/raw/gh-pages/images/producer-init-txn-blog-part-6.png)

As can be seen from this diagram, the end-to-end flow runs as part of a single transactional context, and this solution does not require any extra outbox table and external process to query it and then only publish to Kafka and so on. **There is an important caveat though.** If the application crashes after the database operation, no data will be sent to Kafka and this leaves the application in an inconsistent state. If your application cannot withstand this inconsistency, the best solution is to rely on the outbox pattern (or use a proper 2-PC strategy).

### Outbox pattern semantics in consume-process-produce applications

When it comes to **consumer-process-produce** type applications, the situation is more involved, because the message listener container in Spring for Apache Kafka starts a Kafka transaction after consuming the record.

Let’s revisit the code for a **consume-process-produce** pattern we saw in [blog 3](https://spring.io/blog/2023/10/04/synchronizing-with-external-transaction-managers-in-spring-cloud-stream) in the series:

```java
@Bean
public Consumer<OrderEvent> process(TxCode txCode) {
   return txCode::run;
}

@Component
class TxCode {

   @Transactional
   void run(OrderEvent orderEvent) {
       Order order = new Order();
       order.setId(orderEvent.getId());

       Order savedOrder = repository.save(order);

       OrderEvent event = new OrderEvent();
       event.setId(savedOver.getId());
       event.setType("OrderType");
       streamBridge.send("process-out-0", event);
   }
}
```

This code transactionally publishes to both the database and Kafka.

The message listener container starts the Kafka transaction, and then we use `@Transactional` to wrap our internal run method with a JPA transaction. If the database operation succeeds, we publish to the Kafka topic, and the Kafka publish operation uses the same transactional resources created at the beginning of this process by the message listener container. Once the method exits, JPA commits, and, once the control reaches back to the message listener container, it commits the Kafka transaction.

**Here is what is happening pictorially:**

![cons-process-prod-txn-blog-part-6](https://github.com/spring-cloud/spring-cloud-stream/raw/gh-pages/images/cons-process-prod-txn-blog-part-6.png)

This way, we can keep the implementation very thin without needing the extra database setup and an external process to query the table and publish it to Kafka with synchronization, deleting the outbox record, and other complexities.

#### Special Caveats

As in the producer-initiated scenario, there are a few things to keep in mind here. This solution does not provide any fault-tolerance if the application crashes in the middle, let's say after the database operaion. In that case, no reccords get published to Kafka and that leaves the application in an inconsistent state. You need to write application level safeguards such as an idempotent consumer and other similar strategies to make sure that the application works correctly during this inconsistency and this may be error-prone and not very practical. Therefore, in this case, your best option is to consider using the proper outbox pattern or implement some 2-PC strategies.

### Conclusion

Building on the transactional foundations we learned throughout this series, we saw in this article some strategies that we can use in Spring when an application requires the use of the outbox pattern. These strategies use a light-weight approach by building on the transactional support in Spring and Apache Kafka. These solutions are not a replacement for the outbox pattern, but provided as some pointers to consider if your application does not need the full guarantees of the outbox pattern.

It is worth repeating here that, in both the **consumer-process-produce** pattern and the **producer-initiated** transaction scenarios, if you want to follow the original rules of the outbox pattern implementation strictly, you can do that without going through the above shortcuts. Spring Cloud Stream and Spring for Apache Kafka let you do that. Just follow the pattern as prescribed.

### Acknowledgements

As we wrap this series on Spring Cloud Stream and Apache Kafka transactions, I would like to thank a few people that gave me valuable feedback and guidance throughout this series. I want to thank [Gary Russell](https://spring.io/team/garyrussell), the project lead for Spring for Apache Kafka, in a very special way for guiding me through all the nitty-gritty technical details of how transactions work in Spring for Apache Kafka at a very low level. Gary answered a countless number of my questions on Spring and transactions and especially from a Spring for Apache Kafka/Spring Cloud Stream perspective and I am grateful to him. I also want to especially thank [Jay Bryant](https://spring.io/team/Buzzardo) for meticulously proofreading all the blog drafts and making all the necessary corrections. Special thanks also goes to [Ilayaperumal Gopinathan](https://spring.io/team/ilayaperumalg) and [Oleg Zhurakousky](https://spring.io/team/olegz) for all the guidance and support they gave.

Once again, here are the links to all the other parts in this blog series.

Part 1: [Introduction to Transactions in Spring Cloud Stream Kafka Applications](https://spring.io/blog/2023/09/27/introduction-to-transactions-in-spring-cloud-stream-kafka-applications)

Part 2: [Producer Initiated Transactions in Spring Cloud Stream Kafka Applications](https://spring.io/blog/2023/09/28/producer-initiated-transactions-in-spring-cloud-stream-kafka-applications)

Part 3: [Synchronizing with External Transaction Managers in Spring Cloud Stream Kafka Applications](https://spring.io/blog/2023/10/04/synchronizing-with-external-transaction-managers-in-spring-cloud-stream)

Part 4: [Transactional Rollback Strategies with Spring Cloud Stream and Apache Kafka](https://spring.io/blog/2023/10/11/transactional-rollback-strategies-with-spring-cloud-stream-and-apache-kafka)

Part 5: [Apache Kafka’s Exactly-Once Semantics in Spring Cloud Stream Kafka Applications](https://spring.io/blog/2023/10/16/apache-kafkas-exactly-once-semantics-in-spring-cloud-stream-kafka)

![](https://spring.io/img/extra/footer.svg)

## Get ahead

VMware offers training and certification to turbo-charge your progress.

[Learn more](https://spring.academy/)

## Get support

Tanzu Spring offers support and binaries for OpenJDK™, Spring, and Apache Tomcat® in one simple subscription.

[Learn more](https://spring.io/support)

## Upcoming events

Check out all the upcoming events in the Spring community.

[View all](https://spring.io/events)
