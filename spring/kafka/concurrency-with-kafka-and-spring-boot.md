---
title: "Concurrency with Kafka and Spring Boot"
source: "https://piotrminkowski.com/2023/04/30/concurrency-with-kafka-and-spring-boot/"
author:
  - "[[piotr.minkowski]]"
published: 2023-04-30
created: 2026-10-26
description: "This article will teach you how to configure concurrency for Kafka consumers with Spring Boot and Spring for Kafka"
tags:
  - "clippings"
---

> [!summary]
> Piotr Minkowski walks through four scenarios for scaling a Spring Kafka consumer, using Redpanda as the broker and k6 for load generation: a single-partition topic is processed on one thread, adding partitions only helps once more app instances join and rebalance, the `concurrency` attribute on `@KafkaListener` gives one thread per partition inside a single instance but is capped by the partition count, and finally handing each record to an `ExecutorService` pool decouples processing threads from partitions at the cost of per-partition ordering. Closes by switching the ack mode from `BATCH` to `RECORD` so consumer-group lag reflects real processing progress. Companion to his Kafka transactions post and built on the same sample repository.

This article will teach you how to configure concurrency for Kafka consumers with Spring Boot and Spring for Kafka. Concurrency in Spring for Kafka is closely related to the Kafka partitions and consumer groups. Each consumer within a consumer group can receive messages from multiple partitions. While a consumer inside a group uses a single thread, the group of consumers utilizes multiple threads to consume messages. Although each consumer is single-threaded, the processing of records can leverage multiple threads. We will analyze how to achieve it with Spring Boot and Spring for Kafka.

The topic described today, concurrency with Kafka and Spring Boot, rather deals with the basic issues. If you are looking for something more advanced in this area, you can read some of my other articles. In [that](https://piotrminkowski.com/2021/11/11/kafka-streams-with-spring-cloud-stream/) article, you can find information about Kafka Streams and the Spring Cloud Stream project. You can also read more about Kafka transactions with Spring Boot in the following [article](https://piotrminkowski.com/2022/10/29/kafka-transactions-with-spring-boot/).

## Source Code

If you would like to try it by yourself, you may always take a look at my source code. In order to do that you need to clone my GitHub [repository](https://github.com/piomin/sample-spring-kafka-transactions.git). Then you should go to the `no-transactions-service` directory. After that, you should just follow my instructions. Let’s begin.

## Prerequisites

We will use three different tools in the exercise today. Of course, we will create the Spring Boot consumer app using the latest version of Spring Boot 3 and Java 19. In order to run Kafka locally, we will use Redpanda – a platform compatible with Kafka API. You can easily start and manage Redpanda with their CLI tool – `rpk`. If you want to install `rpk` on your laptop please follow the installation instructions available [here](https://docs.redpanda.com/docs/get-started/rpk-install/).

Finally, we need a tool for load testing. I’m using the [k6](https://k6.io/) tool and its extension for integration with Kafka. Of course, it is just a proposition, you can use any other solution you like. With `k6` I’m able to generate and send a lot of messages to Kafka quickly. In order to use k6 you need to install it on your laptop. [Here](https://k6.io/docs/get-started/installation/) are the installation instructions. After that, you need to install the `xk6-kafka` extension. In the following [documentation](https://k6.io/docs/extensions/get-started/explore/), you have a full list of the `k6` extensions.

## Introduction

For the purpose of this exercise, we will create a simple Spring Boot application that connects to Kafka and receives messages from a single topic. From the business logic perspective, it handles transactions between the accounts and stores inside an in-memory database. Here’s a list of dependencies we need to include in the Maven `pom.xml`:

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

Then, let’s see the configuration settings. Our app connects to the Kafka broker using the address set in the `KAFKA_URL` environment variable. It expects messages in JSON format. Therefore we need to set `JsonDeserializer` as a value deserializer. The incoming message is serialized to the `pl.piomin.services.common.model.Order` object. To make it work, we need to set the `spring.json.value.default.type` and `spring.json.trusted.packages` properties. The `k6` tool won’t set a header with information containing the JSON target type, so we need to disable that feature on Spring for Kafka with the `spring.json.use.type.headers` property.

```yaml
spring:
  application.name: no-transactions-service
  kafka:
    bootstrap-servers: ${KAFKA_URL}
    consumer:
      key-deserializer: org.apache.kafka.common.serialization.LongDeserializer
      value-deserializer: org.springframework.kafka.support.serializer.JsonDeserializer
      properties:
        "[spring.json.value.default.type]": "pl.piomin.services.common.model.Order"
        "[spring.json.trusted.packages]": "pl.piomin.services.common.model"
        "[spring.json.use.type.headers]": false
    producer:
      key-serializer: org.apache.kafka.common.serialization.LongSerializer
      value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
```

Here’s the class representing incoming messages.

```java
public class Order {

   private Long id;
   private Long sourceAccountId;
   private Long targetAccountId;
   private int amount;
   private String status;

   // GETTERS AND SETTERS...
}
```

The last thing we need to do is to enable Spring for Kafka and generate some test accounts for making transactions.

```java
@SpringBootApplication
@EnableKafka
public class NoTransactionsService {

   public static void main(String[] args) {
      SpringApplication.run(NoTransactionsService.class, args);
   }

   private static final Logger LOG = LoggerFactory
      .getLogger(NoTransactionsService.class);

   Random r = new Random();

   @Autowired
   AccountRepository repository;

   @PostConstruct
   public void init() {
      for (int i = 0; i < 1000; i++) {
         repository.save(new Account(r.nextInt(1000, 10000)));
      }
   }

}
```

## Running Kafka using Redpanda

Once we successfully installed the `rpk` CLI we can easily run a single-node Kafka broker by executing the following command:

```bash
$ rpk container start
```

Here’s the result. As you see the address of my broker is `localhost:51961`. The port number is generated automatically, so yours will probably be different. To simplify the next actions, let’s just set it as the `REDPANDA_BROKERS` environment variable.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-30-at-13.12.41.png?w=1378&ssl=1)

Once we created a broker we can create a topic. We will use the topic with the `transactions` name in our tests. In the first step, we make tests with a single partition.

```bash
$ rpk topic create transactions -p 1
```

## Prepare Load Tests for Kafka

Our load test will generate and send orders in JSON format with random values. The `k6` tool allows us to write tests in JavaScript. We need to use the `k6` Kafka extension library. The address of the Kafka broker is retrieved from the `KAFKA_URL` environment variable. We are incrementing the order’s id field each time we generate a new message.

```javascript
load-test.jsimport {
  Writer,
  SchemaRegistry,
  SCHEMA_TYPE_JSON,
} from "k6/x/kafka";
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

const writer = new Writer({
  brokers: [\`${__ENV.KAFKA_URL}\`],
  topic: "transactions",
});

const schemaRegistry = new SchemaRegistry();

export function setup() {
  return { index: 1 };
}

export default function (data) {
  writer.produce({
    messages: [
      {
        value: schemaRegistry.serialize({
          data: {
            id: data.index++,
            sourceAccountId: randomIntBetween(1, 1000),
            targetAccountId: randomIntBetween(1, 1000),
            amount: randomIntBetween(10, 50),
            status: "NEW"
          },
          schemaType: SCHEMA_TYPE_JSON,
        }),
      },
    ],
  });
}

export function teardown(data) {
  writer.close();
}
```

Before running the test we need to set the `KAFKA_URL` environment variable. Then we can use the `k6 run` command to generate and send a lot of messages.

```bash
$ k6 run load-test.js -u 1 -d 30s
```

## Scenario 1: Single-partition Topic Listener

Let’s start with the defaults. Our topic has just a single partition. We are creating the `@KafkaListener` just with the topic and consumer group names. Once the listener receives an incoming message it invokes the `AccountService` bean to process the order.

```java
@Inject
AccountService service;

@KafkaListener(
   id = "transactions",
   topics = "transactions",
   groupId = "a")
public void listen(Order order) {
   LOG.info("Received: {}", order);
   service.process(order);
}
```

Our Spring Boot Kafka app is prepared for concurrency. We will lock the `Account` entity during the transaction with the `PESSIMISTIC_WRITE` mode.

```java
public interface AccountRepository extends CrudRepository<Account, Long> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    Optional<Account> findById(Long id);
}
```

Here’s the implementation of our `AccountService` bean for handling incoming orders. The `process(...)` method is `@Transactional`. In the first step, we find the source **(1)** and target **(2)** `Account` entity. Then we perform a transfer between the account if there are sufficient funds on the source account **(3)**. I’m also simulating a delay just for test purposes **(4)**. Finally, we can send a response asynchronously to another topic using the `KafkaTemplate` bean **(5)**.

```java
@Service
public class AccountService {

    private static final Logger LOG = LoggerFactory
            .getLogger(AccountService.class);
    private final Random RAND = new Random();

    KafkaTemplate<Long, Order> kafkaTemplate;
    AccountRepository repository;

    public AccountService(KafkaTemplate<Long, Order> kafkaTemplate,
                          AccountRepository repository) {
        this.kafkaTemplate = kafkaTemplate;
        this.repository = repository;
    }

    @Transactional
    public void process(Order order) {
        Account accountSource = repository
                .findById(order.getSourceAccountId())
                .orElseThrow(); // (1)

        Account accountTarget = repository
                .findById(order.getTargetAccountId())
                .orElseThrow(); // (2)

        if (accountSource.getBalance() >= order.getAmount()) { // (3)
            accountSource.setBalance(accountSource.getBalance() - order.getAmount());
            repository.save(accountSource);
            accountTarget.setBalance(accountTarget.getBalance() + order.getAmount());
            repository.save(accountTarget);
            order.setStatus("PROCESSED");
        } else {
            order.setStatus("FAILED");
        }

        try {
            Thread.sleep(RAND.nextLong(1, 20)); // (4)
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }

        LOG.info("Processed: order->{}", new OrderDTO(order, accountSource, accountTarget));

        // (5)
        CompletableFuture<SendResult<Long, Order>> result = kafkaTemplate
           .send("orders", order.getId(), order);
        result.whenComplete((sr, ex) ->
                LOG.debug("Sent(key={},partition={}): {}",
                        sr.getProducerRecord().partition(),
                        sr.getProducerRecord().key(),
                        sr.getProducerRecord().value()));
    }

}
```

Let’s set the address of the Kafka broker in the `KAFKA_URL` environment variable and then start the app.

```bash
$ export KAFKA_URL=127.0.0.1:51961
$ mvn spring-boot:run
```

Let’s analyze what happens. Our listener is connecting to the `transactions` topic. It establishes just a single connection since there is a single partition.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-30-at-13.16.56.png?resize=2048%2C338&ssl=1)

In that case, we have just a single instance of our app running and a single thread responsible for handling messages. Let’s verify the current lag on the partition for our consumer group. As you see, the messages are processed very slowly. At first glance, you may be quite surprised.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-30-at-13.19.18.png?resize=2048%2C394&ssl=1)

## Scenario 2: Multiple-partitions Topic Listener

Let’s analyze the next scenario. Now, the `transactions` topic consists of 10 partitions. We won’t change anything in the app code and configuration. We will just remove the previously created topic and create a new one with 10 partitions using the following commands:

```bash
$ rpk topic delete transactions
$ rpk topic create transaction -p 10
```

Once again, we are starting the app using the following Maven command:

```bash
$ mvn spring-boot:run
```

Let’s analyze the app logs. As you see, although we have 10 partitions there is still a single thread listening on them.

![spring-boot-kafka-concurrency-single-partition](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-29-at-16.26.21.png?w=2042&ssl=1)

spring-boot-kafka-concurrency-single-partition

So, our situation hasn’t changed anymore. The app performance is exactly the same. However, now we can run another instance of our Spring Boot app. Once you do it you can take a look at the app logs. A new instance of the app takes 5 partitions.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-29-at-16.29.15.png?resize=2048%2C433&ssl=1)

In that case, a rebalancing occurs. The first instance of our Spring Boot holds 5 other partitions. Now the overall performance is twice as good as before.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-29-at-16.30.15.png?resize=2048%2C437&ssl=1)

Of course, we can run more app instances. In that case, we can scale up to 10 instances since there are 10 partitions on the topic.

## Scenario 3: Consumer Concurrency with Multiple Partitions

Let’s analyze another scenario. Now, we are enabling concurrency at the Kafka listener level. In order to achieve it, we need to set the `concurrency` field inside the `@KafkaListener` annotation. This parameter is still related to Kafka partitions. So, there is no sense to set the value higher than the number of partitions. In our case, there are 10 partitions – the same as in the previous scenario.

```java
@KafkaListener(
   id = "transactions",
   topics = "transactions",
   groupId = "a",
   concurrency = "10")
public void listen(Order order) {
   LOG.info("Received: {}", order);
   service.process(order);
}
```

After that, we can start the Spring Boot app. Let’s see what happens. As you see, we have 10 concurrent connections – each bound to a single thread.

![spring-boot-kafka-concurrency-multi](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-29-at-23.56.57.png?w=1478&ssl=1)

spring-boot-kafka-concurrency-multi

In that case, the app performance for a single instance is around 10 times better than before. There are 10 concurrent threads, which process incoming messages.

![spring-boot-kafka-concurrency-processing](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-30-at-00.00.41.png?resize=2048%2C798&ssl=1)

spring-boot-kafka-concurrency-processing

However, if we run our load tests the lag on partitions is still large. Here’s the result after sending ~25k messages in 10 seconds.

![spring-boot-kafka-concurrency-lag](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-30-at-00.13.06.png?resize=2048%2C527&ssl=1)

spring-boot-kafka-concurrency-lag

Theoretically, we can scale up the number of instances to improve the overall performance. However, that approach won’t change anything. Why? Let’s run another one and take a look at the logs. Now, only 5 threads are still bound to the partitions. Five other threads are in the idle state. The overall performance of the system is not changed.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-30-at-00.19.46.png?w=1576&ssl=1)

## Scenario 4: Process in Multiple Threads

Finally the last scenario. We will create a thread pool with the Java `ExecutorService`. We may still use the custom thread pool with the Kafka consumer concurrency feature as shown below (through the `concurrency` parameter). Each time the listener receives new messages it processes them in a separate thread.

```java
@Service
public class NoTransactionsListener {

    private static final Logger LOG = LoggerFactory
            .getLogger(NoTransactionsListener.class);

    AccountService service;
    ExecutorService executorService = Executors.newFixedThreadPool(30);

    public NoTransactionsListener(AccountService service) {
        this.service = service;
    }

    @KafkaListener(
            id = "transactions",
            topics = "transactions",
            groupId = "a",
            concurrency = "3")
    public void listen(Order order) {
        LOG.info("Received: {}", order);
        executorService.submit(() -> service.process(order));
    }

}
```

In that case, one thing should be clarified. With the custom thread pool at the app level, we are losing message ordering within the single partition. The previous model guaranteed ordering, since we have a thread per partition. For our Spring Boot app, it is not important, because we are just processing messages independently.

Let’s start the app. There are 3 concurrent threads that receive messages from the partitions.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-30-at-11.02.47.png?resize=2048%2C372&ssl=1)

There are 30 threads for processing messages and 3 threads for listening to the partitions. Once the message is received in the consumer thread, it is handled by the worker threads.

![spring-boot-kafka-concurrency-multi-threads](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-30-at-11.04.50.png?resize=2048%2C1006&ssl=1)

spring-boot-kafka-concurrency-multi-threads

We can run other instances of our Spring Boot Kafka concurrency apps. I’ll run another two. The first instance grabs 4 partitions, while the next two instances 3.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-30-at-11.13.57.png?resize=2048%2C312&ssl=1)

Now, we can run again load test. It generated and sent ~85k messages to our Kafka broker (around 2.7k per second).

![spring-boot-kafka-concurrency-k6](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-30-at-11.27.10.png?w=1988&ssl=1)

spring-boot-kafka-concurrency-k6

Let’s verify the lag within the consumer group using the `rpk group` command. The lag on partitions is not large. In fact, there are 90 threads within the three app instances that simultaneously are processing the incoming messages. But wait… does it mean that with 90 threads we are able to process 2.7k orders per second? We should also remember about a custom delay between 1 and 20 ms we added before (with the `Thread.sleep` method).

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-30-at-11.31.41.png?resize=2048%2C531&ssl=1)

The lag looks really fine, although the app is not able to process all requests without a delay. That’s because the default ack mode for commit offset in Spring Kafka is `BATCH`. If we change it to the `RECORD` mode, which commits the offset when the listener returns after processing the record, we should get a more precise lag value. In order to override that option, we need to define the `ConcurrentKafkaListenerContainerFactory` bean as shown below.

```java
@Bean
ConcurrentKafkaListenerContainerFactory<Integer, String>
    kafkaListenerContainerFactory(ConsumerFactory<Integer, String> consumerFactory) {
   ConcurrentKafkaListenerContainerFactory<Integer, String> factory =
      new ConcurrentKafkaListenerContainerFactory<>();
   factory.setConsumerFactory(consumerFactory);
   factory.setConcurrency(3);
   factory.getContainerProperties()
      .setAckMode(ContainerProperties.AckMode.RECORD);
   return factory;
}
```

Let’s restart the app and make a load test once again. Now, the lag value is much closer to the reality.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2023/04/Screenshot-2023-04-30-at-11.59.13.png?resize=2048%2C532&ssl=1)

## Final Thoughts

Concurrency and performance are one of the most important things to consider when working with Kafka and Spring Boot. In this article, I wanted to explain to you some basics with simple examples. I hope it clarifies some concerns over Spring Kafka project usage.
