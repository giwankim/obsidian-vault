---
title: "Deep Dive into Kafka Offset Commit with Spring Boot"
source: "https://piotrminkowski.com/2026/03/27/deep-dive-into-kafka-offset-commit-with-spring-boot/?utm_source=substack&utm_medium=email"
author:
  - "[[piotr.minkowski]]"
published: 2026-03-27
created: 2026-05-07
description: "This article uses straightforward Spring Boot examples to illustrate how your application can inadvertently lose messages or process them twice due to the Kafka offset commit mechanism. It builds upon the scenarios discussed in two of my previous posts on Kafka and Spring Boot, offering deeper insights: Source Code Feel free to use my source […]"
tags:
  - "clippings"
---

> [!summary]
> Walks through how Spring Kafka's default offset-commit behavior can silently cause Spring Boot consumers to lose messages or process them twice. The default `BATCH` mode uses a single thread that only commits after the entire batch is processed across all partitions; setting the listener's `concurrency` parameter to match the partition count gives each partition its own thread that commits independently. Includes runnable Spring Boot code and diagrams illustrating the single-threaded vs. concurrent commit flows.

This article uses straightforward Spring Boot examples to illustrate how your application can inadvertently lose messages or process them twice due to the Kafka offset commit mechanism. It builds upon the scenarios discussed in two of my previous posts on Kafka and Spring Boot, offering deeper insights:

- [Kafka Offset with Spring Boot](https://piotrminkowski.com/2024/03/11/kafka-offset-with-spring-boot/) – describes how to manage Kafka consumer offset with Spring Boot and Spring Kafka
- [Concurrency with Kafka and Spring Boot](https://piotrminkowski.com/2023/04/30/concurrency-with-kafka-and-spring-boot/) – describes how to configure concurrency for Kafka consumers with Spring Boot and Spring for Kafka

## Source Code

Feel free to use my source code if you’d like to try it out yourself. To do that, you must clone my sample GitHub [repository](https://github.com/piomin/sample-spring-boot-kafka.git). Then you should only follow my instructions.

## How It Works

Before diving into the exercise, let’s explore how Spring Kafka handles offset commit. By default, the Spring Kafka consumer processes messages in `BATCH` mode, meaning a batch of messages sent by the producer can be received on the consumer side all at once. Typically, only one thread manages this process, responsible for both receiving and processing messages. While this default setup can be customized extensively, understanding these core mechanisms is essential for effective use.

The diagram below illustrates the default scenario. Now, here’s the key point: this offset is only committed to the broker after the entire batch of incoming messages has been processed.

![spring-kafka-offset-commit-single](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-26-at-12.54.33.png?w=1814&ssl=1)

spring-kafka-offset-commit-single

I explained the potential consequences of this approach in my earlier blog post on concurrency with Kafka and Spring Boot. When we examine this mechanism closely, we see that a Kafka topic can have multiple partitions. However, Spring still processes messages in a single thread unless we explicitly configure it to do otherwise.

The diagram below offers a detailed view of this setup. A single consumer thread actively listens for messages across all partitions within a topic. After processing all messages, it commits the offsets on each partition.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-26-at-13.03.06.png?w=1858&ssl=1)

Let’s explore how we can improve the situation. Set the concurrency parameter on our listener to match the number of partitions in the topic. You might consider increasing it further, but that would be unnecessary, as any extra threads would remain idle.

In this situation, each thread assigned to a specific partition processes messages in the packet routed to that partition one after another. After processing the packet, the thread commits the offset for its respective partition. See the diagram below for an illustration of this scenario.

![spring-kafka-offset-commit-concurrent](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-26-at-13.19.11.png?w=1954&ssl=1)

spring-kafka-offset-commit-concurrent

Now that we’ve explored the theory, let’s dive into the practical side. In the next section, we’ll examine the source code.

## Use Spring Boot with Kafka

### Sending Messages

Let’s begin by implementing the message producer with Spring Kafka. When we use the `KafkaTemplate` bean to send messages, it defaults to batching. We also want to log each message immediately after sent. The `GET /transactions` endpoint allows us to control the destination topic and the total number of messages generated.

```
@RestController
public class TransactionsController {

    private static final Logger LOG = LoggerFactory
            .getLogger(TransactionsController.class);

    long id = 1;
    long groupId = 1;

    final KafkaTemplate<Long, Order> kafkaTemplate;

    public TransactionsController(KafkaTemplate<Long, Order> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @PostMapping("/transactions")
    public void generateAndSendMessages(@RequestBody InputParameters inputParameters) {
        for (long i = 0; i < inputParameters.getNumberOfMessages(); i++) {
            Order o = new Order(id++, i+1, i+2, 1000, "NEW", groupId);
            CompletableFuture<SendResult<Long, Order>> result =
                    kafkaTemplate.send(inputParameters.getTopic(), o.getId(), o);
            result.whenComplete((sr, ex) ->
                    LOG.info("Sent({}): {}", sr.getProducerRecord().key(), sr.getProducerRecord().value()));
        }
        groupId++;
    }

}
```

```
@RestController
public class TransactionsController {

    private static final Logger LOG = LoggerFactory
            .getLogger(TransactionsController.class);

    long id = 1;
    long groupId = 1;

    final KafkaTemplate<Long, Order> kafkaTemplate;

    public TransactionsController(KafkaTemplate<Long, Order> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @PostMapping("/transactions")
    public void generateAndSendMessages(@RequestBody InputParameters inputParameters) {
        for (long i = 0; i < inputParameters.getNumberOfMessages(); i++) {
            Order o = new Order(id++, i+1, i+2, 1000, "NEW", groupId);
            CompletableFuture<SendResult<Long, Order>> result =
                    kafkaTemplate.send(inputParameters.getTopic(), o.getId(), o);
            result.whenComplete((sr, ex) ->
                    LOG.info("Sent({}): {}", sr.getProducerRecord().key(), sr.getProducerRecord().value()));
        }
        groupId++;
    }

}
```

For clarity, here is the `InputParameters` class with the endpoint’s input parameters.

```
public class InputParameters {

    private int numberOfMessages;
    private String topic = "transactions";

    public int getNumberOfMessages() {
        return numberOfMessages;
    }

    public void setNumberOfMessages(int numberOfMessages) {
        this.numberOfMessages = numberOfMessages;
    }

    public String getTopic() {
        return topic;
    }

    public void setTopic(String topic) {
        this.topic = topic;
    }
}
```

```
public class InputParameters {

    private int numberOfMessages;
    private String topic = "transactions";

    public int getNumberOfMessages() {
        return numberOfMessages;
    }

    public void setNumberOfMessages(int numberOfMessages) {
        this.numberOfMessages = numberOfMessages;
    }

    public String getTopic() {
        return topic;
    }

    public void setTopic(String topic) {
        this.topic = topic;
    }
}
```

Below is a list of Spring Boot configuration settings for the Kafka producer. It sends messages in JSON format along with an `id` key.

```
spring:
  application.name: producer
  output.ansi.enabled: ALWAYS
  kafka:
    bootstrap-servers: ${KAFKA_URL:localhost:9092}
    producer:
      key-serializer: org.apache.kafka.common.serialization.LongSerializer
      value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
```

```
spring:
  application.name: producer
  output.ansi.enabled: ALWAYS
  kafka:
    bootstrap-servers: ${KAFKA_URL:localhost:9092}
    producer:
      key-serializer: org.apache.kafka.common.serialization.LongSerializer
      value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
```

Here’s the `Order` class that represents the JSON message exchanged between the producer and the consumer.

```
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

```
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

## Receiving Messages

First, let’s take a look at the list of dependencies. You should not add the Spring Boot Kafka starter or, for some reason, the `jackson-databind` library.

```
<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-kafka</artifactId>
  </dependency>
  <dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
  </dependency>
</dependencies>
```

```
<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-kafka</artifactId>
  </dependency>
  <dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
  </dependency>
</dependencies>
```

The message-sending application lets you choose a target topic. Meanwhile, the Spring Boot Kafka consumer offers several `@KafkaListener` annotations for different message reception scenarios. Let’s start with the simplest one, which processes messages in a single thread. The input topic is called `transactions`. The message processing method is straightforward. It prints the received message along with the partition number and offset. To simulate realistic processing time, it deliberately pauses for 10 seconds.

```
@Service
public class Listener {

    private static final Logger LOG = LoggerFactory
            .getLogger(Listener.class);

    @KafkaListener(
            id = "transactions",
            topics = "transactions",
            groupId = "a"
    )
    public void listen(@Payload Order order,
                       @Header(KafkaHeaders.OFFSET) Long offset,
                       @Header(KafkaHeaders.RECEIVED_PARTITION) int partition) throws InterruptedException {
        LOG.info("[partition={},offset={}] Starting: {}", partition, offset, order);
        Thread.sleep(10000L);
        LOG.info("[partition={},offset={}] Finished: {}", partition, offset, order);
    }
}
```

```
@Service
public class Listener {

    private static final Logger LOG = LoggerFactory
            .getLogger(Listener.class);

    @KafkaListener(
            id = "transactions",
            topics = "transactions",
            groupId = "a"
    )
    public void listen(@Payload Order order,
                       @Header(KafkaHeaders.OFFSET) Long offset,
                       @Header(KafkaHeaders.RECEIVED_PARTITION) int partition) throws InterruptedException {
        LOG.info("[partition={},offset={}] Starting: {}", partition, offset, order);
        Thread.sleep(10000L);
        LOG.info("[partition={},offset={}] Finished: {}", partition, offset, order);
    }
}
```

The second method (`listenMulti`) does the same thing as the previous one, but sets the number of consumer threads to `3`. It consumes messages from the `transactions-multi` topic.

```
@KafkaListener(
        id = "transactions-multi",
        topics = "transactions-multi",
        groupId = "a",
        concurrency = "3"
)
public void listenMulti(@Payload Order order,
                        @Header(KafkaHeaders.OFFSET) Long offset,
                        @Header(KafkaHeaders.RECEIVED_PARTITION) int partition) throws InterruptedException {
    LOG.info("[partition={},offset={}] Starting: {}", partition, offset, order);
    Thread.sleep(10000L);
    LOG.info("[partition={},offset={}] Finished: {}", partition, offset, order);
}
```

```
@KafkaListener(
        id = "transactions-multi",
        topics = "transactions-multi",
        groupId = "a",
        concurrency = "3"
)
public void listenMulti(@Payload Order order,
                        @Header(KafkaHeaders.OFFSET) Long offset,
                        @Header(KafkaHeaders.RECEIVED_PARTITION) int partition) throws InterruptedException {
    LOG.info("[partition={},offset={}] Starting: {}", partition, offset, order);
    Thread.sleep(10000L);
    LOG.info("[partition={},offset={}] Finished: {}", partition, offset, order);
}
```

The last `@KafkaListener` method processes messages asynchronously using thread pool provided by Java `ExecutorService`. The target topic in this is `transactions-async-auto`. For now, we won’t focus on this method. We’ll come back to it at the end of the article.

```
@KafkaListener(
        id = "transactions-async-auto",
        topics = "transactions-async-auto",
        groupId = "a"
)
public void listenAsyncAuto(@Payload Order order,
                        @Header(KafkaHeaders.OFFSET) Long offset,
                        @Header(KafkaHeaders.RECEIVED_PARTITION) int partition) {
    LOG.info("[partition={},offset={}] Starting Async Auto: {}", partition, offset, order);
    smallPool.submit(() -> processor.process(order, null));
}
```

```
@KafkaListener(
        id = "transactions-async-auto",
        topics = "transactions-async-auto",
        groupId = "a"
)
public void listenAsyncAuto(@Payload Order order,
                        @Header(KafkaHeaders.OFFSET) Long offset,
                        @Header(KafkaHeaders.RECEIVED_PARTITION) int partition) {
    LOG.info("[partition={},offset={}] Starting Async Auto: {}", partition, offset, order);
    smallPool.submit(() -> processor.process(order, null));
}
```

Before running the Spring Boot consumer, we need to start Kafka. The `docker-compose.yml` file is located in the repository’s root directory. So all you need to do is run the `docker compose up` command.

```
kafka:
    image: apache/kafka-native:4.1.1
    container_name: kafka-native
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_NODE_ID: 1
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@localhost:9093
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_NUM_PARTITIONS: 3
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
    volumes:
      - kafka-data:/var/lib/kafka/data
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9092"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  kafka-data:
    driver: local
```

```
kafka:
    image: apache/kafka-native:4.1.1
    container_name: kafka-native
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_NODE_ID: 1
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@localhost:9093
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_NUM_PARTITIONS: 3
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
    volumes:
      - kafka-data:/var/lib/kafka/data
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9092"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  kafka-data:
    driver: local
```

Next, simply enable the message consumer and producer using the commands below. Then, we can move on to our test scenarios.

```
$ cd consumer
$ mvn spring-boot:run

$ cd ../producer
$ mvn spring-boot:run
```

```
$ cd consumer
$ mvn spring-boot:run

$ cd ../producer
$ mvn spring-boot:run
```

## Duplicate Message Processing with Spring Kafka

### Single Consuming Thread

In this section, we’ll demonstrate how our application processes the same messages multiple times after a restart. You simply need to send the messages, stop the application, and then restart it. Spring Boot, combined with Spring Kafka, automatically handles graceful shutdown by waiting for all ongoing message processing to finish before shutting down. However, this mechanism has a timeout. By default, it is 30 seconds in Spring Boot. Since each message takes about 10 seconds to process due to an intentional delay with `Thread.sleep()`, you’ll see how Spring won’t commit Kafka offset before graceful shutdown.

First, let’s send 20 messages to the transactions topic using the endpoint exposed by the `producer` application.

```
curl -X POST http://localhost:8080/transactions \
  -H 'Content-Type: application/json' \
  -d '{"numberOfMessages": 20,"topic": "transactions"}'
```

```
curl -X POST http://localhost:8080/transactions \
  -H 'Content-Type: application/json' \
  -d '{"numberOfMessages": 20,"topic": "transactions"}'
```

Let’s see what’s happening on the consumer side. The logs show that the consumer received a batch of 20 messages from the `transactions` topic. It then processed the first message from partition 1. Subsequent messages are processed by a single thread at 10-second intervals.

![spring-kafka-offset-commit-log-single](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-26-at-18.05.40.png?w=2168&ssl=1)

spring-kafka-offset-commit-log-single

Here we see the end of the message handling for `offset=24` and the start for the message with `offset=25`.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-26-at-18.06.35.png?w=2164&ssl=1)

Let’s gracefully shut down the consumer application with the `CTRL+C` shortcut. You’ll notice that all listeners, except for the one subscribed to the `transactions` topic, will close. Spring Boot waits 30 seconds to process messages from this topic, and if it doesn’t receive them within that time, it closes with the error shown below. Consequently, the application doesn’t commit any offsets to the Kafka broker.

![spring-kafka-offset-commit-graful-shutdown](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-26-at-18.08.25.png?w=2160&ssl=1)

spring-kafka-offset-commit-graful-shutdown

After restarting, the consumer starts from the beginning with `offset=24`.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-26-at-18.09.21.png?w=2160&ssl=1)

This time, wait until all messages have been processed. Once that happens, you’ll see an entry like the one below in the log. This time, Spring Boot was able to commit the Kafka offset for all partitions.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-26-at-18.13.56.png?w=2160&ssl=1)

### Multiple Consuming Threads

Now we’ll repeat the same exercise, but for a message reception mode with three listener threads. To do this, send messages to the `transactions-multi` topic as shown below.

```
curl -X POST http://localhost:8080/transactions \
  -H 'Content-Type: application/json' \
  -d '{"numberOfMessages": 20,"topic": "transactions-multi"}'
```

```
curl -X POST http://localhost:8080/transactions \
  -H 'Content-Type: application/json' \
  -d '{"numberOfMessages": 20,"topic": "transactions-multi"}'
```

As shown below, messages are handled by three separate threads, each assigned to a single partition.

![spring-kafka-offset-commit-log-multiple](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-26-at-23.14.10.png?w=2388&ssl=1)

spring-kafka-offset-commit-log-multiple

I stop the application as soon as two out of three threads finish processing the messages. As shown below, these threads successfully commit their offsets in the Kafka topic.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-26-at-23.21.13.png?w=2378&ssl=1)

The last thread didn’t finish processing all messages before the application terminated, and the graceful timeout proved too short to complete this task.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-26-at-23.25.18.png?w=2380&ssl=1)

Therefore, after the restart, our Spring Boot application resumes processing all messages from partition 1, since the offset commit for that Kafka topic hadn’t been performed before.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-26-at-23.27.03.png?w=2378&ssl=1)

Of course, you can increase the graceful shutdown timeout to match the message processing time. To configure the timeout period, you must use the `spring.lifecycle.timeout-per-shutdown-phase` property.

## Lose Messages with Spring Kafka

In this section, we explore a new scenario where a Spring Boot application might lose messages. We set up a listener that receives messages from the `transactions-async-auto` topic. Messages arrive through a single consumer thread, but the processing occurs across five threads in the pool. Therefore, the Spring Kafka offset commit occurs in the main thread after the message batch is received. I’ve pasted this code snippet before, but let’s take another look at it for clarity.

```
ExecutorService smallPool = Executors.newFixedThreadPool(5);

@KafkaListener(
        id = "transactions-async-auto",
        topics = "transactions-async-auto",
        groupId = "a"
)
public void listenAsyncAuto(@Payload Order order,
                        @Header(KafkaHeaders.OFFSET) Long offset,
                        @Header(KafkaHeaders.RECEIVED_PARTITION) int partition) {
    LOG.info("[partition={},offset={}] Starting Async Auto: {}", partition, offset, order);
    smallPool.submit(() -> processor.process(order));
}
```

```
ExecutorService smallPool = Executors.newFixedThreadPool(5);

@KafkaListener(
        id = "transactions-async-auto",
        topics = "transactions-async-auto",
        groupId = "a"
)
public void listenAsyncAuto(@Payload Order order,
                        @Header(KafkaHeaders.OFFSET) Long offset,
                        @Header(KafkaHeaders.RECEIVED_PARTITION) int partition) {
    LOG.info("[partition={},offset={}] Starting Async Auto: {}", partition, offset, order);
    smallPool.submit(() -> processor.process(order));
}
```

Here’s the `Processor` `@Service`, which handles incoming messages asynchronously. As you can see, it also introduces an artificial 10-second delay in processing.

```
@Service
public class Processor {

    private static final Logger LOG = LoggerFactory
            .getLogger(Processor.class);

    public void process(Order order) {
        LOG.info("Processing: {}", order.getId());
        try {
            Thread.sleep(10000L);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
        LOG.info("Finished: {}", order.getId());
    }

}
```

```
@Service
public class Processor {

    private static final Logger LOG = LoggerFactory
            .getLogger(Processor.class);

    public void process(Order order) {
        LOG.info("Processing: {}", order.getId());
        try {
            Thread.sleep(10000L);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
        LOG.info("Finished: {}", order.getId());
    }

}
```

Below is a command that sends 30 messages to the `transactions-async-auto` topic.

```
curl -X POST http://localhost:8080/transactions \
  -H 'Content-Type: application/json' \
  -d '{"numberOfMessages": 30,"topic": "transactions-async-auto"}'
```

```
curl -X POST http://localhost:8080/transactions \
  -H 'Content-Type: application/json' \
  -d '{"numberOfMessages": 30,"topic": "transactions-async-auto"}'
```

Let’s examine the Spring Boot consumer logs. The listener receives a batch of 30 messages and actively processes the first five asynchronously, while the remaining messages wait for available threads in the pool.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-27-at-08.59.35.png?w=2368&ssl=1)

Now let’s take a closer look at the timing. Essentially, shortly after asynchronous processing of several messages begins, an offset commit occurs for all partitions. What does this mean in practice?

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-27-at-09.04.24.png?w=2376&ssl=1)

You can now shut down the application just as you did before. Spring Boot does not wait for the graceful shutdown period because it perceives that Kafka messages have already been received. Thankfully, you can configure message reception and processing in different ways to prevent this issue. For more details, refer to two of my earlier articles mentioned in the introduction to this post.

To complete the exercise, restart the Spring Boot application. Once it’s running again, notice that no messages appear in the topic. Depending on when you stopped it, some or all of the messages might have been lost.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/03/Screenshot-2026-03-27-at-09.12.51-scaled.png?w=2560&ssl=1)

## Conclusion

Understanding message reception and commit offset handling in Kafka reveals crucial insights into system reliability. When developers overlook these mechanisms, both on Kafka’s side and within the application’s framework, they risk severe failures during restarts or unexpected shutdowns. In this article, I illustrate scenarios that cause message loss and force the application to reprocess messages. I hope this sparks your interest and enhances your understanding of Kafka and how to build consumers with Spring Kafka.
