---
title: "KafkaProducer Client Internals"
source: "https://d2.naver.com/helloworld/6560422"
author:
published:
created: 2026-06-28
description:
tags:
  - "clippings"
---

> [!summary]
> Java KafkaProducer 클라이언트의 내부 구조와 주요 설정이 동작에 어떻게 반영되는지 설명한다. send() 호출 시 일어나는 직렬화·파티셔닝·압축 과정, Record를 TopicPartition별 Deque에 모으는 RecordAccumulator 배치 처리, 그리고 RecordBatch를 ProduceRequest로 묶어 Java IO 멀티플렉싱으로 브로커에 전송하는 Sender 스레드를 다룬다. batch.size, buffer.memory, max.in.flight.requests.per.connection 등 설정값이 내부 동작과 순서 보장에 미치는 영향을 보여준다.

Kafka는 Distributed Streaming Platform으로, 다음과 같이 Producer와 Consumer가 연결되어 데이터가 전달됩니다.

![image](https://d2.naver.com/content/images/2020/08/4609fc00-bf80-11ea-8bb8-b60302de3855.png)

Kafka는 Producer의 데이터 전송을 위해서 Producer API를 제공합니다. 이 글에서는 Java Producer API인 KafkaProducer Client의 내부 구조를 설명하고, KafkaProducer의 주요 설정이 실제 내부 동작에서 어떻게 적용되는지 알아봅니다.

이 글은 Kafka와 관련된 기본적인 개념을 이해하고 있고 사용법에 익숙한 사용자를 대상으로 합니다. Kafka와 관련된 기본적인 개념과 사용법은 [Kafka 공식 문서](http://kafka.apache.org/documentation/) 에 잘 설명돼 있으니 해당 문서를 참고하기 바랍니다.

이 글은 Kafka Client 0.10.2.1 버전 기준으로 작성되었습니다.

## 기본 구성 요소

KafkaProducer Client는 크게 3가지 요소로 구성된다.

첫 번째는 사용자가 직접 사용하는 KafkaProducer이다. 사용자는 이 클래스의 send()를 호출함으로써 Record를 전송한다.

두 번째는 RecordAccumulator이다. 사용자가 KafkaProducer의 send()를 호출하면 Record가 바로 Broker로 전송되는 것이 아니라 RecordAccumulator에 저장된다. 그리고 실제로 Broker에 전송되는 것은 이후에 비동기적으로 이루어진다.

세 번째는 Sender이다. KafkaProducer는 별도의 Sender Thread를 생성한다. Sender Thread는 RecordAccumulator에 저장된 Record들을 Broker로 전송하는 역할을 한다. 그리고 Broker의 응답을 받아서 사용자가 Record 전송 시 설정한 콜백이 있으면 실행하고, Broker로부터 받은 응답 결과를 Future를 통해서 사용자에게 전달한다.

![image](https://d2.naver.com/content/images/2020/08/0ec97800-cd00-11ea-8f7d-e6f2df9ecc99.png)

## KafkaProducer send()

사용자는 send() 호출 시 전송할 Record와 전송 완료 후 실행할 콜백을 지정할 수 있다. send()가 호출되면 Serialization, Partitioning, Compression 작업이 이루어지고 최종적으로 RecordAccumulator에 Record가 저장된다.

![image](https://d2.naver.com/content/images/2020/08/75d23700-ccd6-11ea-988c-d46b7046e448.png)

### Serialization

사용자로부터 전달된 Record의 Key, Value는 지정된 Serializer에 의해서 Byte Array로 변환된다. Serializer는 `key.serializer`, `value.serializer` 설정값으로 지정하거나, KafkaProducer 생성 시 지정할 수 있다.

다음과 같이 설정을 통해서 지정할 수 있다.

```java
Properties props = new Properties();
props.put("bootstrap.servers", "localhost:9092");
props.put("acks", "all");
props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

Producer<String, String> producer = new KafkaProducer<>(props);
for (int i = 0; i < 100; i++)
    producer.send(new ProducerRecord<String, String>("my-topic", Integer.toString(i), Integer.toString(i)));

producer.close();
```

또는 다음과 같이 KafkaProducer 생성 시에 직접 Serializer 객체를 생성해서 전달할 수 있다.

```java
Producer<String, String> producer = new KafkaProducer<>(props, new StringSerializer(), new StringSerializer());
```

StringSerializer 외에 다음과 같은 Serializer를 기본적으로 제공하고 있다.

- ByteArraySerializer
- ByteBufferSerializer
- BytesSerializer
- DoubleSerializer
- IntegerSerializer
- LongSerializer

### Partitioning

Kafka의 Topic은 여러 개의 Partition으로 나뉘어 있는데, 사용자의 Record는 지정된 Partitioner에 의해서 어떤 파티션으로 보내질지 정해진다. Partitioner는 기본적으로 Record를 받아서 Partition Number를 반환하는 역할을 한다. `partitioner.class` 를 설정하여 Partitioner를 지정할 수 있으며, Partitioner를 지정하지 않으면 `org.apache.kafka.clients.producer.internals.DefaultPartitioner` 가 사용된다.

Record 생성 시 Partition 지정이 가능하기 때문에, Partition이 지정되어 있는 경우에는 Partitioner를 사용하지 않고 지정된 Partition이 사용된다. Record에 지정된 Partition이 없는 경우 DefaultPartitioner는 다음과 같이 동작한다.

- Key 값이 있는 경우 Key 값의 Hash 값을 이용해서 Partition을 할당한다.
- Key 값이 없는 경우 Round-Robin 방식으로 Partition이 할당된다.

### Compression

사용자가 전송하려는 Record는 압축을 함으로써 네트워크 전송 비용도 줄일 수 있고 저장 비용도 줄일 수 있다. Record는 RecordAccumulator에 저장될 때 바로 압축되어 저장된다. `compression.type` 을 설정하여 압축 시 사용할 코덱을 지정할 수 있다. 다음과 같은 코덱를 사용할 수 있으며 지정하지 않는 경우 기본값은 `none` 이다.

- gzip
- snappy
- lz4

## RecordAccumulator append()

사용자가 전송하려는 Record는 전송 전에 먼저 RecordAccumulator에 저장된다. RecordAccumulator는 batches라는 Map을 가지고 있는데, 이 Map의 Key는 `TopicPartition` 이고, Value는 `Deque<RecordBatch>` 이다.

![image](https://d2.naver.com/content/images/2020/08/5db2e580-ccdf-11ea-9358-87e74551ebe1.png)

RecordAccumulator에 저장하기 전에 Record의 Serialized Size를 검사한다. Serialized Size가 `max.request.size` 설정값 또는 `buffer.memory` 설정값보다 크면 RecordTooLargeException이 발생한다. 크기가 문제 없으면, RecordAccumulator의 append()를 이용해서 저장한다.

![image](https://d2.naver.com/content/images/2020/08/ad91ac80-ccdf-11ea-8508-6060e1e2acb9.png)

RecordAccumulator의 append()가 호출되면 batches에서 추가될 Record에 해당하는 TopicPartition의 Deque를 찾는다. 이 Deque의 Last에서 RecordBatch 하나를 꺼내서 Record를 저장할 공간이 있는지 확인한다. 여유 공간이 있으면 해당 RecordBatch에 Record를 추가하고, 여유 공간이 없으면 새로운 RecordBatch를 생성해서 Last쪽으로 저장한다. Queue를 사용하지 않고 Deque가 사용된 이유는 append() 시에 가장 최근에 들어간 RecordBatch를 꺼내서 봐야 하기 때문이다.

![image](https://d2.naver.com/content/images/2020/08/62686a80-b576-11ea-8839-3eb52b31945d.png)

새로운 RecordBatch를 생성할 때는 BufferPool에서 RecordBatch가 사용할 ByteBuffer를 받아온다. BufferPool의 전체 Size는 `buffer.memory` 설정에 의해서 결정된다. RecordBatch 생성을 위해 요청한 Buffer Size만큼의 여유가 없으면 할당이 Blocking되고 BufferPool에서 용량이 확보될 때까지 `max.block.ms` 설정값만큼 기다린다. `max.block.ms` 설정값만큼의 시간이 초과해도 확보되지 않으면 TimeoutException이 발생한다.

RecordBatch 생성 시 사용하는 Buffer Size는 `batch.size` 설정값과 저장할 Record Size 중에서 큰 값으로 결정된다. 즉, Record가 `batch.size` 보다 작으면 하나의 RecordBatch에 여러 개의 Record가 저장되지만, Record가 `batch.size` 보다 크면 하나의 RecordBatch에 하나의 Record만 저장된다. `compression.type` 설정값에 압축 코덱이 지정되어 있는 경우 Record가 RecordBatch에 저장될 때 압축된다.

## Sender Thread

Sender Thread는 RecordAccumulator에 저장된 Record를 꺼내서 Broker로 전송하고 Broker의 응답을 처리한다.

![image](https://d2.naver.com/content/images/2020/08/cc099f00-cd03-11ea-8965-36bcd60e4d38.png)

Sender Thread에서는 Broker로 Record를 전송하기 위해서 RecordAccumulator에서 Record를 꺼낸다. RecordAccumulator의 drain()을 통해서 각 Broker별로 전송할 RecordBatch List를 얻을 수 있다.

drain()에서는 먼저 각 Broker Node에 속하는 TopicPartition 목록을 얻어온다. 그리고 각 Node에 속한 TopicPartition을 보면서 Deque First쪽의 RecordBatch 하나를 꺼내서 RecordBatch List에 추가한다. 이렇게 Node 단위로 RecordBatch List가 `max.request.size` 설정값을 넘지 않을 때까지 모은다. 모든 Node에 이 동작을 반복하면 Node별로 전송할 RecordBatch List가 모인다.

![image](https://d2.naver.com/content/images/2020/08/260c6380-cd08-11ea-8a5c-91f15cf7c945.png)

이렇게 모인 RecordBatch List는 하나의 ProduceRequest로 만들어져서 Broker Node로 전송된다. ProduceRequest는 InFlightRequests라는 Node별 Deque에 먼저 저장된다. 그리고 이렇게 저장된 순서대로 실제 Broker Node로 전송이 이루어진다.

![image](https://d2.naver.com/content/images/2020/08/98f3b480-b579-11ea-885b-d402af123591.png)

Broker Node로의 전송은 Java IO Multiplexing 방식으로 별도의 Thread를 사용하지 않고 Sender Thread에서 비동기적으로 이루어진다. 이에 대한 자세한 설명은 이 글의 범위를 벗어난다고 판단되어 생략한다.

![image](https://d2.naver.com/content/images/2020/08/930a0400-ccdc-11ea-8f31-379ef6cbd39c.png)

InFlightRequests Deque의 Size는 `max.in.flight.requests.per.connection` 설정값에 의해서 정해진다. 이 값은 KafkaProducer Client가 하나의 Broker로 동시에 전송할 수 있는 요청 수를 의미한다.

참고로, 요청이 실패할 경우 `retries` 설정값이 1 이상인 경우 재시도하기 때문에 `max.in.flight.requests.per.connection` 값이 1보다 크면 순서가 바뀔 수 있다. 순서를 보장하려면 `max.in.flight.requests.per.connection` 값을 1로 설정해야 한다. 하지만 이렇게 설정하면 동시에 1개의 요청만 처리할 수 있기 때문에 전송 성능이 떨어질 수 있다.

Broker는 하나의 Connection에 대해서 요청이 들어온 순서대로 처리해서 응답한다. 응답의 순서가 보장되기 때문에, KafkaProducer Client는 Broker로부터 응답이 오면 항상 InFlightRequests Deque의 가장 오래된 요청을 완료 처리한다. ProduceRequest가 완료되면 요청에 포함되었던 모든 RecordBatch의 콜백을 실행하고 Broker로부터의 응답을 Future를 통해서 사용자에게 전달한다. 그리고 RecordBatch에서 사용한 ByteBuffer를 BufferPool로 반환하면서 Record 전송 처리가 모두 마무리된다.

## 마치며

Kafka는 기본적으로 Scala 언어로 작성되어 있고, Java Producer API도 처음에는 Scala로 작성되었다. 이로 인해서 Java Producer API를 사용하려면 Scala Library 의존성이 생겼었고, 특히 사용자 프로젝트에서 Scala를 사용할 경우 Scala Library 버전을 잘 맞춰야 했다. 이를 잘 맞추지 못하면 문제가 생기는 경우도 많았다.

이를 개선하기 위해서 Kafka 0.8.2에서 새로운 Producer를 Java만을 이용해서 만들었고 Java IO Multiplexing 방식을 적용하여 성능도 크게 향상되었다. 이 글에서 설명한 KafkaProducer는 이렇게 새롭게 만든 Producer API이다.

새롭게 만든 KafkaProducer는 RecordAccumulator를 두어서 가능하면 여러 Record를 하나의 RecordBatch로 묶으려 했고, 그 결과 압축과 전송 효율을 높일 수 있도록 구성되어 있다. 그리고 Sender Thread에서는 Java IO Multiplexing을 이용해서, 전송을 위한 별도의 Thread를 생성하지 않고도 효율적으로 전송을 함으로써 전송 성능도 크게 향상시킬 수 있었다.

이 글에서는 이러한 새로운 KafkaProducer의 전체적인 내부 동작을 설명했고, 각 설정이 실제 동작에 어떻게 영향을 미치는지 설명했다. 이 글이 Kafka 운영 시 KafkaProducer에서 발생하는 문제를 해결하는 데 도움이 되길 바란다.

이번 글은 이렇게 마치며, 추후 기회가 된다면 Kafka NetworkClient에서 IO Multiplexing을 이용해서 어떻게 전송이 이루어지는지, 그리고 KafkaConsumer의 내부 동작은 어떤지 알아보겠다.

Tag

![](https://d2.naver.com/image/20200813/340228529593.jpg)

글쓴이

최호연|네이버 Search

소개

대용량 데이터 저장 및 유통을 위한 시스템인 Cuve 운영 및 개발을 담당하고 있습니다.

관련글

- [![썸네일](https://d2.naver.com/content/images/2022/02/kafka_2022_Helloworld.png)
	Kafka NetworkClient Internals
	](https://d2.naver.com/helloworld/0853669)
- [![썸네일](https://d2.naver.com/content/images/2021/04/kafka2.png)
	KafkaConsumer Client Internals
	](https://d2.naver.com/helloworld/0974525)
- [![썸네일](https://d2.naver.com/content/images/2023/10/PC_170x120_231021.png)
	Kafka에서 파티션 증가 없이 동시 처리량을 늘리는 방법 - Parallel Consumer
	](https://d2.naver.com/helloworld/7181840)
- [![썸네일](https://d2.naver.com/content/images/2016/04/---.png)
	대용량 스트리밍 데이터 실시간 분석
	](https://d2.naver.com/helloworld/7731491)

##### 댓글

7

- 네이브별명
	좋은 글 잘 읽었습니다. 감사합니다. 👍
	2025-10-25 17:06
	[**답글** 0](#)
	**공감/비공감** [공감 *0*](#) [비공감 *0*](#)
- 토마토공포증
	좋은 글 감사합니다.
	2025-09-21 15:41
	[**답글** 0](#)
	**공감/비공감** [공감 *0*](#) [비공감 *0*](#)
- 승짱
	좋은 내용 감사합니다
	2021-01-03 00:40
	[**답글** 0](#)
	**공감/비공감** [공감 *1*](#) [비공감 *1*](#)
- 후덥
	정말 간만에 좋은 글 보고 갑니다.
	2020-10-07 15:09
	[**답글** 0](#)
	**공감/비공감** [공감 *0*](#) [비공감 *1*](#)
- 김지훈
	좋은 글 감사합니다.
	2020-08-14 13:09
	[**답글** 0](#)
	**공감/비공감** [공감 *7*](#) [비공감 *1*](#)
