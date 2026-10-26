---
title: "Kafka Transactions with Spring Boot"
source: "https://piotrminkowski.com/2022/10/29/kafka-transactions-with-spring-boot/"
author:
  - "[[piotr.minkowski]]"
published: 2022-10-29
created: 2026-10-26
description: "In this article, you will learn how to use Kafka transactions with the Spring Kafka project in your Spring Boot app."
tags:
  - "clippings"
---

> [!summary]
> Piotr Minkowski introduces Kafka transactions in Spring Kafka against an Upstash cluster: setting `spring.kafka.producer.transaction-id-prefix` auto-configures a `KafkaTransactionManager`, yet the consumer still saw uncommitted messages until `isolation.level` was changed from the default `read_uncommitted` to `read_committed`. He then demonstrates producer-side rollback (unchecked exceptions only unless `rollbackFor` is set), shows that rolled-back records still occupy broker offsets, and adds H2 with Spring Data JPA so each service has two transaction managers to name in `@Transactional`. Ends with the caveat that Kafka has no XA support, so Spring simply runs two separate transactions, and points to Debezium and the outbox pattern for real consistency.

In this article, you will learn how to use Kafka transactions with the Spring Kafka project in your Spring Boot app. In order to run the Kafka cluster we will use [Upstash](https://upstash.com/?utm_source=Piotr2). This article provides a basic introduction to Kafka transactions. If you are looking for more advanced usage and scenarios you may refer to that [article](https://piotrminkowski.com/2022/02/07/deep-dive-into-saga-transactions-with-kafka-streams-and-spring-boot/), about distributed transactions in microservices. You can also read more about Kafka Streams the Spring Cloud Stream project in this [article](https://piotrminkowski.com/2021/11/11/kafka-streams-with-spring-cloud-stream/).

## Source Code

If you would like to try it by yourself, you may always take a look at my source code. In order to do that you need to clone my GitHub [repository](https://github.com/piomin/sample-spring-kafka-transactions.git). After that, you should just follow my instructions. Let’s begin.

## Getting Started with Kafka in Spring Boot

I have already created a Kafka cluster on Upstash using a web [dashboard](https://console.upstash.com/?utm_source=Piotr2). All the connection credentials are generated automatically. You can find and copy them on the main page of your cluster.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-18-at-13.52.14.png?w=1848&ssl=1)

Assuming we have a username as the KAFKA\_USER variable and a password as the KAFKA\_PASS variable we need to provide the following Spring configuration in the `application.yml` file:

```yaml
spring:
  application.name: transactions-service
  kafka:
    bootstrap-servers: inviting-camel-5620-eu1-kafka.upstash.io:9092
    properties:
      security.protocol: SASL_SSL
      sasl.mechanism: SCRAM-SHA-256
      sasl.jaas.config: org.apache.kafka.common.security.scram.ScramLoginModule required username="${KAFKA_USER}" password="${KAFKA_PASS}";
```

Here’s a list of required dependencies. Since we exchange JSON messages, we need the Jackson library for serialization or deserialization. Of course, we also need to include Spring Boot starter and Spring Kafka.

```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter</artifactId>
</dependency>
<dependency>
  <groupId>org.springframework.kafka</groupId>
  <artifactId>spring-kafka</artifactId>
</dependency>
<dependency>
  <groupId>com.fasterxml.jackson.core</groupId>
  <artifactId>jackson-databind</artifactId>
</dependency>
```

The `transactions-service` is generating and sending orders. We will create the test topic `transactions` on the app startup.

```java
@SpringBootApplication
public class TransactionsService {

   public static void main(String[] args) {
      SpringApplication.run(TransactionsService.class, args);
   }

   @Bean
   public NewTopic transactionsTopic() {
      return TopicBuilder.name("transactions")
          .partitions(3)
          .replicas(1)
          .build();
   }

}
```

## Enabling Kafka Transactions in Spring Boot

In Kafka, a producer initiates a transaction by making a request to the transaction coordinator. You can find a detailed description of that process in the following [article](https://www.confluent.io/blog/transactions-apache-kafka/) on the Confluent blog.

With Spring Boot, we just need to set the `spring.kafka.producer.transaction-id-prefix` property to enable transactions. Spring Boot will do the rest by automatically configuring a `KafkaTransactionManager` bean and wiring it into the listener container. Here’s a part of the configuration responsible for the message producer. We use JsonSerializer to serialize data from objects into JSON. Transactions prefix is `tx-`.

```yaml
spring:
  kafka:
    producer:
      key-serializer: org.apache.kafka.common.serialization.LongSerializer
      value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
      transaction-id-prefix: tx-
```

During our scenario, we will send 10 messages within a single transaction. In order to observe logs on the consumer side we set a delay between subsequent attempts to 1 second.

```java
@Transactional
public void generateAndSendPackage()
      throws InterruptedException, TransactionException {
   for (long i = 0; i < 10; i++) {
      Order t = new Order(id++, i+1, i+2, 1000, "NEW");
      ListenableFuture<SendResult<Long, Order>> result =
         kafkaTemplate.send("transactions", t.getId(), t);
      result.addCallback(callback);
      Thread.sleep(1000);
   }
}
```

## Enable Transactions on the Kafka Consumer Side

In the first step, we will just print the incoming messages. We need to annotate the listener method with the `@KafkaListener`. The target topic is `transactions`, and the consumer group is `a`. Also, we have to add the `@Transactional` annotation to enable transaction support for the listen method.

```java
@Service
public class TransactionsListener {

   private static final Logger LOG = LoggerFactory
          .getLogger(TransactionsListener.class);

   @KafkaListener(
          id = "transactions",
          topics = "transactions",
          containerGroup = "a",
          concurrency = "3")
   @Transactional
   public void listen(Order order) {
      LOG.info("{}", order);
   }
}
```

Let’s run the producer app first. To do go to the `transactions-service` directory and execute the command `mvn spring-boot:run`. It is a good idea to enable more detailed logs for Spring Kafka transactions. To do that add the following line to the `application.yml` file:

```yaml
logging:
  level:
    org.springframework.transaction: trace
    org.springframework.kafka.transaction: debug
```

After that, let’s run the consumer app. In order to that go to the `accounts-service` directory and run the same command as before. You should see the following topic created in the Upstash console:

![kafka-transactions-spring-boot-upstash](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-18-at-15.34.27.png?w=1710&ssl=1)

kafka-transactions-spring-boot-upstash

The `transactions-service` app exposes the REST endpoint for sending messages. It just starts that procedure of generating and sending 10 messages within a single transaction I mentioned in the previous section. Let’s call the endpoint:

```bash
$ curl -X POST http://localhost:8080/transactions
```

Let’s see at the logs on the producer side. After sending all the messages it committed the transaction.

![kafka-transactions-spring-boot-logs](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-18-at-15.41.15.png?w=1962&ssl=1)

kafka-transactions-spring-boot-logs

Now, let’s see how it looks on the consumer side. All the messages are received just after being sent by the producer app. It is not something that we expected…

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-18-at-15.44.50.png?w=1616&ssl=1)

In order to verify what happened, we need to take a look at the consumer app logs. Here’s a fragment with Kafka consumer settings. As you see, by default Spring Kafka sets the transactions isolation level to `read_uncommitted` for Spring Boot.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-18-at-15.48.22.png?w=1718&ssl=1)

## Deep Dive into Transactions with Spring Kafka

In order to solve the problem with transactions from the previous section, we need to change the default isolation level in the `application.yml` file. As the `spring.kafka.consumer.properties` we have to set the `isolation.level` property to `read_commited` as shown below.

```yaml
spring:
  application.name: accounts-service
  kafka:
    consumer:
      key-deserializer: org.apache.kafka.common.serialization.LongDeserializer
      value-deserializer: org.springframework.kafka.support.serializer.JsonDeserializer
      properties:
        spring.json.trusted.packages: "*"
        isolation.level: read_committed
```

After that let’s run the `accounts-service` app once again.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-18-at-15.57.06.png?w=1596&ssl=1)

Now, all the messages have been received after the producer committed the transaction. There are three consumer threads as we set the `@KafkaListener` `concurrency` parameter to `3`.

![kafka-transactions-spring-boot-producer](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-18-at-15.57.37.png?w=1582&ssl=1)

kafka-transactions-spring-boot-producer

In the next step, we will test the rollback of transactions on the producer side. In order to do that, we will modify the method for generating and sending orders. Now, the `generateAndSendPackage` is getting a boolean parameter, that indicates if a transaction should be rollbacked or not.

```java
@Transactional
public void generateAndSendPackage(boolean error)
       throws InterruptedException {
   for (long i = 0; i < 10; i++) {
      Order t = new Order(id++, i+1, i+2, 1000, "NEW");
      ListenableFuture<SendResult<Long, Order>> result =
            kafkaTemplate.send("transactions", t.getId(), t);
      result.addCallback(callback);
      if (error && i > 5)
         throw new RuntimeException();
      Thread.sleep(1000);
   }
}
```

Here are the logs from our test. After sending six orders the method throws a `RuntimeException` and Spring rollbacks a transaction. As expected, the consumer app does not receive any messages.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-18-at-23.16.32.png?resize=2048%2C571&ssl=1)

It is important to know that Spring rollbacks are only on ***unchecked*** exceptions by default. To rollback ***checked*** exceptions, we need to specify the `rollbackFor` on the `@Transactional` annotation.

The transactional producer sends messages to the Kafka cluster even before committing the transaction. You could see it in the previous section, where the listener was continuously receiving messages if the isolation level was `read_uncommited`. Consequently, if we roll back a transaction on the producer side the message sent before rollback occurs come to the Kafka broker. We can see it e.g. in the Upstash live message view for the `transactions` topic.

![kafka-transactions-spring-boot-live](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-19-at-15.30.23.png?w=1836&ssl=1)

kafka-transactions-spring-boot-live

Here’s the current value of offsets for all partitions in the `transactions` topic for the `a` consumer group. We made a successful commit after sending the first package of 10 messages and we rollbacked the transaction with the second package. The sum of offsets is 10 in that case. But in fact, it is different that the current latest offset on those partitions.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-19-at-00.33.48.png?resize=2048%2C600&ssl=1)

To verify it, we can, for example, change a consumer group name for the listener to `b` and start another instance of the `accounts-service`.

```java
@KafkaListener(
     id = "transactions",
     topics = "transactions",
     containerGroup = "b",
     concurrency = "3")
@Transactional
public void listen(Order order) {
   LOG.info("{}", order);
}
```

Here’s the current value of offsets for the `b` consumer group.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-19-at-15.31.52.png?resize=2048%2C656&ssl=1)

Of course, the messages have been rollbacked. But the important thing to understand here is that these operations happen on the Kafka broker side. The transaction coordinator changes the values of Kafka offsets. We can easily verify that consumer won’t receive messages after rollback even if we the initial offset to the earliest with the `spring.kafka.consumer.auto-offset-reset` property.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-19-at-15.34.27.png?w=1584&ssl=1)

## Add Database

In this section, we will extend our scenario with new functionalities. Our app will store the status of orders in the database. Just for demo purposes, we will use an in-memory database H2. There are two dependencies required in this scenario: H2 and Spring Data JPA.

```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
<dependency>
  <groupId>com.h2database</groupId>
  <artifactId>h2</artifactId>
  <scope>runtime</scope>
</dependency>
```

There the `OrderGroup` entity that stores the current status of the package (`SENT`, `CONFIRMED`, `ROLLBACK`), the total number of orders in the single package, and the total number of processed orders by the `accounts-service`.

```java
@Entity
public class OrderGroup {

   @Id
   @GeneratedValue(strategy = GenerationType.IDENTITY)
   private Long id;
   private String status;
   private int totalNoOfOrders;
   private int processedNoOfOrders;

   // GETTERS/SETTERS ...
}
```

In order to manage the entity we use the Spring Data repository pattern:

```java
public interface OrderGroupRepository extends
   CrudRepository<OrderGroup, Long> {
}
```

We will also include a database in the `accounts-service` app. When it processes the incoming orders it performs transfers between the source and target account. It will store the account balance in the database.

```java
@Entity
public class Account {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private int balance;

   // GETTERS/SETTERS ...
}
```

The same as before there is a repository bean for managing the `Account` entity.

```java
public interface AccountRepository extends
   CrudRepository<Account, Long> {
}
```

We also need to modify the `Order` message exchanged between the apps. It has to contain the `groupId` field for processing confirmations.

```java
public class Order {

    private Long id;
    private Long sourceAccountId;
    private Long targetAccountId;
    private int amount;
    private String status;
    private Long groupId;

   // GETTERS/SETTERS ...
}
```

Here’s the diagram that illustrates our architecture for the described scenario.

![kafka-transactions-spring-boot-arch](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-19-at-11.53.29.png?resize=2048%2C919&ssl=1)

kafka-transactions-spring-boot-arch

## Handling Transactions Across Multiple Resources

After including Spring Data JPA there are two registered `TransactionManager` beans with names `transactionManager` and `kafkaTransactionManager`. Therefore we need to choose the name of the transaction manager inside the `@Transactional` annotation. In the first step, we add a new entity to the database. The primary key `id` is auto-generated in the database and then returned to the object. After that, we get `groupId` and generate the sequence of orders within that group. Of course, both operations (save to database, sent to Kafka) are part of the same transaction.

```java
@Transactional("kafkaTransactionManager")
public void sendOrderGroup(boolean error) throws InterruptedException {
   OrderGroup og = repository.save(new OrderGroup("SENT", 10, 0));
   generateAndSendPackage(error, og.getId());
}

private void generateAndSendPackage(boolean error, Long groupId)
      throws InterruptedException {
   for (long i = 0; i < 10; i++) {
      Order o = new Order(id++, i+1, i+2, 1000, "NEW", groupId);
      ListenableFuture<SendResult<Long, Order>> result =
         kafkaTemplate.send("transactions", o.getId(), o);
      result.addCallback(callback);
      if (error && i > 5)
         throw new RuntimeException();
      Thread.sleep(1000);
   }
}
```

The `accounts-service` app listens for incoming orders. It is processing every single order in a separate transaction. It checks if sufficient funds are in the customer account to make a transfer. If there is enough money, it performs a transfer. Finally, it sends the response to `transactions-service` with the transaction status. The message is sent to the `orders` topic.

```java
@KafkaListener(
   id = "transactions",
   topics = "transactions",
   groupId = "a",
   concurrency = "3")
@Transactional("kafkaTransactionManager")
public void listen(Order order) {
   LOG.info("Received: {}", order);
   process(order);
}

private void process(Order order) {
   Account accountSource = repository
      .findById(order.getSourceAccountId())
      .orElseThrow();
   Account accountTarget = repository
      .findById(order.getTargetAccountId())
      .orElseThrow();
   if (accountSource.getBalance() >= order.getAmount()) {
      accountSource.setBalance(accountSource.getBalance() - order.getAmount());
      repository.save(accountSource);
      accountTarget.setBalance(accountTarget.getBalance() + order.getAmount());
      repository.save(accountTarget);
      order.setStatus("PROCESSED");
   } else {
      order.setStatus("FAILED");
   }
   LOG.info("After processing: {}", order);
   kafkaTemplate.send("orders", order.getId(), order);
}
```

The `transactions-service` listens for order confirmations on the `orders` topic. Once it receives the message it increases the number of processed orders within an order group and stores the current result in the database. We should use a default Spring transaction manager since we don’t send any messages to Kafka.

```java
@KafkaListener(
      id = "orders",
      topics = "orders",
      groupId = "a",
      concurrency = "3")
@Transactional("transactionManager")
public void listen(Order order) {
   LOG.info("{}", order);
   OrderGroup og = repository
      .findById(order.getGroupId())
      .orElseThrow();
   if (order.getStatus().equals("PROCESSED")) {
      og.setProcessedNoOfOrders(og.getProcessedNoOfOrders() + 1);
      og = repository.save(og);
      LOG.info("Current: {}", og);
   }
}
```

Don’t forget to lock the `OrderGroup` record during the transaction. Since we are processing messages concurrently (with 3 threads) we need to lock the `OrderGroup` record until we update the value of `processedNoOfOrders` column:

```java
public interface OrderGroupRepository extends
        CrudRepository<OrderGroup, Long> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    Optional<OrderGroup> findById(Long groupId);
}
```

Let’s test a positive scenario. We will generate a group of orders that should be confirmed. To do that let’s call our endpoint `POST /transactions`:

```bash
$ curl -X 'POST' 'http://localhost:8080/transactions' \
  -H 'Content-Type: application/json' \
  -d 'false'
```

Here are the logs from the `accounts-service` app:

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-21-at-16.19.43.png?resize=2048%2C500&ssl=1)

We can also take at the logs generated by the `transactions-service` app:

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2022/10/Screenshot-2022-10-21-at-16.20.34.png?resize=2048%2C469&ssl=1)

Finally, we can verify the current status of our order group by calling the following endpoint:

```bash
$ curl -X GET 'http://localhost:8080/transactions'
```

What happens if we roll back the transaction? Try it by yourself with the following command:

```bash
$ curl -X 'POST' 'http://localhost:8080/transactions' \
  -H 'Content-Type: application/json' \
  -d 'true'
```

## Final Thoughts

You can easily handle Kafka transactions with Spring Boot using the Spring Kafka project. You can integrate your app with a database and handle transactions across multiple resources. However, one thing needs to be clarified – Kafka does not support XA transactions. It may result in data inconsistency. Spring does not solve that case, it just performs two transactions in the background. When the `@Transactional` method exits, Spring Boot will commit the database transactions first and then the Kafka transactions. You can just change that order to enable Kafka transaction commit first by configuring the outer method configured to use the `DataSourceTransactionManager`, and the inner method to use the `KafkaTransactionManager`.

Can we solve that case somehow? Of course. There is, for example, project Debezium that allows you to stream database changes into Kafka topics. With that approach, you can just commit changes in the database, and then configure Debezium to send events with changes to Kafka. For more details about that tool and outbox pattern please refer to the article available [here](https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/).
