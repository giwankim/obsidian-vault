---
title: "KafkaConsumer Client Internals"
source: "https://d2.naver.com/helloworld/0974525"
author:
published:
created: 2026-06-28
description:
tags:
  - "clippings"
---

> [!summary]
> KafkaConsumer의 구성 요소(ConsumerNetworkClient, SubscriptionState, ConsumerCoordinator, Fetcher, HeartBeat 스레드)와 poll 메서드의 동작 방식을 설명한다. 컨슈머 리밸런스 2단계(Join/Sync) 프로토콜과 파티션 할당 정책, 커밋된 오프셋 가져오기 및 auto.offset.reset 기반 오프셋 초기화, 오프셋 커밋(자동/수동)을 다룬다. 또한 KIP-62로 추가된 백그라운드 HeartBeat 스레드와 max.poll.interval.ms·session.timeout.ms 등 관련 설정을 설명한다.

Apache Kafka는 Distributed Event Streaming Platform으로, 성능이 뛰어나고 원하는 기간만큼 안정적으로 데이터를 저장합니다. 또한 모든 기능이 분산되어 있어 확장성과 내결함성(fault tolerance)이 뛰어납니다. 이러한 특징 덕분에 Kafka는 기존 메시징 시스템(Active MQ, Rabbit MQ)을 대체하기도 하고 시스템 로그를 모으거나 데이터 가공을 위해 파이프라인을 구성할 때 등 다양한 경우에 사용되고 있습니다.

![kafka0.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-3e52258554e1.png)

그림 1 Kafka 컨셉

Kafka는 TCP 위에서 동작하는 자체 바이너리 프로토콜을 사용합니다. 모든 바이너리 프로토콜은 요청과 응답의 쌍으로 이루어져 있습니다. Kafka는 이 바이너리 프로토콜을 적절히 구현한 프로듀서(KafkaProducer)와 컨슈머(KafkaConsumer)를 클라이언트로 제공하며 KafkaProducer를 사용하여 데이터를 발행(publish)하고 KafkaConsumer를 사용하여 데이터를 구독(subscribe)합니다.

브로커와 Kafka 클라이언트가 바이너리 프로토콜을 사용하여 통신하기 때문에 Kafka 클라이언트가 바이너리 프로토콜을 어떻게 사용하는지 이해하면 Kafka를 이해하는 데 도움이 됩니다. Kafka의 바이너리 프로토콜 구조는 [Kafka Protocol Guide 문서](https://kafka.apache.org/protocol.html) 에서 살펴볼 수 있습니다.

KafkaProducer는 라우팅 계층 없이 브로커와 직접 통신하고 성능 향상을 위해 메모리에 데이터를 모아 일괄 전송하는 특징이 있습니다. KafkaProducer에 대한 자세한 설명은 [KafkaProducer Client Internals](https://d2.naver.com/helloworld/6560422) 를 참고하기 바랍니다.

이 글에서는 KafkaConsumer의 구성 요소와 동작 방식에 대해 알아보겠습니다. Kafka에 대한 기본적인 개념과 사용법은 익숙하다고 가정하고 있습니다. Kafka에 대한 기본적인 컨셉과 용어는 Kafka 문서 [Introduction](https://kafka.apache.org/intro) 과 [Main Concepts and Terminology](https://kafka.apache.org/documentation/#intro_concepts_and_terms) 를 참고하기 바랍니다.

이 글은 Kafka 클라이언트 0.10.2.1 기준으로 작성되었습니다.

## KafkaConsumer의 Poll

KafkaConsumer는 사용자가 직접 사용하는 클래스로, 사용자는 KafkaConsumer의 poll 메서드를 사용해 브로커에서 데이터를 가져올 수 있다.

예제 1 KafkaConsumer 이벤트 루프

```java
final Properties props = new Properties();
props.put("bootstrap.servers", brokers);
props.put("group.id", "testGroup");
props.put("key.deserializer", "org.apache.kafka.common.serialization.ByteArrayDeserializer");
props.put("value.deserializer", "org.apache.kafka.common.serialization.ByteArrayDeserializer");

// KafkaConsumer 생성
try (final KafkaConsumer<byte[], byte[]> consumer = new KafkaConsumer<>(props)) {
    // 구독할 토픽
    consumer.subscribe(Arrays.asList("topic1"));

    // 무한 루프
    while (true) {
        // poll 메서드를 통해 데이터를 가져온다.
        final ConsumerRecords<byte[], byte[]> records = consumer.poll(100);
        for (final ConsumerRecord<byte[], byte[]> record : records) {
            // processing...
        }
    }
}
```

일반적으로 KafkaConsumer를 사용하여 브로커에서 데이터를 가져오기 위해서는 예제 1처럼 `group.id` 에 컨슈머 그룹 ID를 입력하고 subscribe 메서드에 구독할 토픽을 입력한 후 poll 메서드를 호출한다.

poll 메서드를 호출하면 KafkaConsumer는 내부 구성 요소들과 협력하여 컨슈머 그룹에 참여한 후 브로커로부터 데이터를 가져온다.

같은 `group.id` 를 사용하는 컨슈머를 묶어서 컨슈머 그룹이라고 한다. 레코드(record)는 컨슈머 그룹 내에 오직 1개의 컨슈머로만 전달된다.

컨슈머 그룹을 통해서 Kafka는 가용성 확보와 병렬 처리를 한다. 만약 컨슈머 그룹 내에 특정 컨슈머의 처리가 일정 시간(`max.poll.interval.ms` 설정만큼) 정지된다면 해당 컨슈머는 그룹에서 제외되고 나머지 컨슈머들로만 데이터가 분배된다.

만약 컨슈머 그룹의 처리량을 늘리고 싶다면 `group.id` 가 같은 새로운 KafkaConsumer를 만들어서 poll 메서드를 호출하면 된다. 같은 컨슈머 그룹에 속한 KafkaConsumer는 다른 파티션을 할당받기 때문에 컨슈머 그룹 내 데이터 처리를 확장한다. Kafka는 파티션 단위로 데이터를 분배하기 때문에 파티션의 수보다 많은 컨슈머를 그룹에 추가한 경우 파티션의 수를 초과한 컨슈머는 파티션을 할당받지 못하여 데이터를 소비하지 못한다.

브로커 중 하나가 컨슈머 그룹를 관리하고 이를 GroupCoordinator라고 부른다. GroupCoordinator는 그룹의 메타데이터와 그룹을 관리한다.

Kafka는 리밸런스(rebalance)를 통해 컨슈머의 할당된 파티션을 다른 컨슈머로 이동시킨다. 컨슈머 그룹에 새로운 컨슈머가 추가되거나 컨슈머 그룹에 속해 있던 컨슈머가 제외되는 경우에 그룹 내 파티션을 다시 할당해야 하므로 리밸런스가 발생한다.

![KafkaCosumerStructure-poll.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-c760d3a61002.png)

그림 2 컨슈머 리밸런스 프로토콜

그림 2는 3개의 컨슈머가 컨슈머 그룹에 참여하는 과정을 보여준다. 컨슈머 리밸런스 프로토콜은 2단계로 이루어져 있다.

첫 번째 단계에서는 JoinGroup 요청을 GroupCoordinator로 보내 그룹에 참여한다. 이후 리더(leader)로 선정된 컨슈머는 그룹 내 파티션을 할당한다. 모든 컨슈머는 Synchronization barrier를 넘어가기 전에 메시지 처리를 중지하고 오프셋을 커밋해야 한다.

두 번째 단계에서 모든 컨슈머는 SyncGroup 요청을 보낸다. 리더는 SyncGroup 요청을 보낼 때 파티션 할당 결과를 요청에 포함시킨다. GroupCoordinator는 파티션 할당 결과를 SyncGroup의 응답으로 준다. 컨슈머 리밸런스에 대한 자세한 설명은 [ConsumerCoordinator](#ConsumerCoordinator) 부분에서 다루겠다. 이후 오프셋 초기화 과정을 끝낸 후 컨슈머는 브로커에서 데이터를 가져올 수 있다.

컨슈머 리밸런스가 일어날 때 모든 컨슈머에 할당된 파티션이 해제(revoke)되므로 새로 파티션이 할당되기 전까지 데이터 처리가 일시 정지된다.

이 과정은 poll 메서드가 호출될 때 KafkaConsumer가 내부 구성 요소들과 협력하여 수행한다. 내부 구성 요소들이 어떻게 협력하는지 알아보기 위해 다음으로 KafkaConsumer의 구성 요소와 각 구성 요소의 역할에 대해 알아보겠다.

## 구성 요소

KafkaConsumer는 ConsumerNetworkClient, SubscriptionState, ConsumerCoordinator, Fetcher, HeartBeat 스레드로 구성된다.

![KafkaCosumerStructure-component.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-c7281ad17e60.png)

그림 3 KafkaConsumer

KafkaConsumer가 생성되면 그림 3처럼 ConsumerNetworkClient, SubscriptionState, ConsumerCoordinator, Fetcher가 생성된다. HeartBeat 스레드는 poll 메서드 호출 시 ConsumerCoordinator에 의해 생성되고(그림 3의 6) KafkaConsumer와는 별도의 스레드로 동작한다.

## ConsumerNetworkClient

ConsumerNetworkClient는 KafkaConsumer의 모든 네트워크 통신을 담당한다.

ConsumerNetworkClient의 모든 요청은 비동기로 동작한다. 따라서 ConsumerNetworkClient의 응답값은 RequestFuture 클래스로 확인한다. RequestFuture 클래스는 ConsumerNetworkClient의 비동기 요청에 대한 결과를 반환하는 클래스이다.

예제 2 RequestFuture 클래스가 제공하는 메서드

```java
public class RequestFuture<T> {
    /* 요청에 대한 처리가 끝났는지 여부 */
    public boolean isDone();
    /* 결과값 */
    public T value();
    /* 요청이 성공했는지 여부 */
    public boolean succeeded();
    /* 재시도가 가능한 오류인지 여부 */
    public boolean isRetriable();
    /* 오류가 발생했을 때 오류를 확인하는 메서드 */
    public RuntimeException exception();
    /* 요청이 완료 처리될 때 호출된다. complete가 호출된 이후 succeeded()가 true로 반환되고 value()를 통해 응답을 확인한다. */
    public void complete(T value);
    /* 요청이 실패한 경우 호출된다. */
    public void raise(RuntimeException e);
    /* complete 메서드가 호출되었을 때 호출될 listener를 추가한다. */
    public void addListener(RequestFutureListener<T> listener);
    /* RequestFuture의 응답 타입을 T에서 S로 바꿔준다. */
    public <S> RequestFuture<S> compose(final RequestFutureAdapter<T, S> adapter);
}
```

예제 2를 살펴보면 RequestFuture 클래스는 Java에서 비동기 작업에 대한 반환값으로 사용되는 Future 클래스와 유사하지만 다르다. RequestFuture 클래스는 RequestFuture 타입을 바꿀 수 있는 compose 메서드와 비동기 요청이 완료되는 시점에 호출될 listener를 추가하는 addListener 메서드를 제공한다는 점이 Java Future 클래스와 다른 점이다.

compose 메서드가 KafkaConsumer 내부에서 어떻게 사용되는지 알아보겠다.

예제 3 compose 메서드 사용

```java
/* ClientResponse를 ByteBuffer로 바꾸는 Adapter 예 */
class JoinGroupResponseHandler extends RequestFutureAdapter<ClientResponse, ByteBuffer> {
    @Override
    public void onSuccess(ClientResponse response, RequestFuture<ByteBuffer> future) {...}

    @Override
    public void onFailure(RuntimeException e, RequestFuture<ByteBuffer> future) {...}
}

/* compose 메서드 사용 예 */
class Coordinator {
    private final ConsumerNetworkClient client;

    private RequestFuture<ByteBuffer> sendJoinGroupRequest() {
        // send 메서드의 반환값은 RequestFuture<ClientResponse>이다.
        final RequestFuture<ClientResponse> requestFuture = client.send(coordinator, requestBuilder);
        // Adapter를 사용하여 RequestFuture의 타입을 ClientResponse에서 ByteBuffer로 바꾸었다.
        final RequestFuture<ByteBuffer> composeResult = requestFuture.compose(new JoinGroupResponseHandler());
        return composeResult;
    }
}
```

compose 메서드를 호출하기 위해서는 인수로 넘겨줄 Adapter(`RequestFutureAdapter<T, S>`)가 필요하다. Adapter는 내부에서 T 타입을 S 타입으로 바꿔주는 클래스이다.

예제 3에서는 JoinGroupResponseHandler(Adapter)가 ClientResponse(T)를 ByteBuffer(S)으로 바꿔준다. ConsumerNetworkClient의 send 메서드를 호출하면 `RequestFuture<ClientResponse>` 가 반환된다. compose 메서드를 사용하여 `RequestFuture<ClientResponse>` 를 `RequestFuture<ByteBuffer>` 로 바꾸었다.

예제 4 메서드의 연속적인 호출

```java
client.send(coordinator, requestBuilder).compose(new JoinGroupResponseHandler());
```

compose 메서드는 KafkaConsumer 내부에서 빈번하게 사용되는데 예제 4처럼 메서드를 연속적으로 호출하는 방식으로 사용되고 있다.

다음으로 ConsumerNetworkClient가 요청과 응답을 처리하는 과정에 대해 알아보겠다. ConsumerNetworkClient로 전달된 요청의 실제 처리는 NetworkClient를 통해 이루어진다. NetworkClient는 비동기 네트워크 IO를 담당하는 클래스인데 KafkaConsumer 범위를 벗어난다고 판단되어 자세한 설명은 생략한다.

![KafkaCosumerStructure-networkclient.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-3e5314da54f0.png)

그림 4 ConsumerNetworkClient와 NetworkClient 개요

그림 4는 ConsumerNetworkClient와 NetworkClient의 관계를 단순화한 그림이다. ConsumerNetworkClient는 자신에게 전달된 모든 요청을 ClientRequest로 만들어 NetworkClient로 보낸다. NetworkClient는 응답으로 ClientResponse를 준다.

다음 그림은 ConsumerNetworkClient가 요청을 전송하는 과정이다.

![KafkaCosumerStructure-ConsumerNetworkClientRequest.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-c72a5eee7efd.png)

그림 5 ConsumerNetworkClient의 요청 전송 과정

KafkaConsumer의 모든 요청은 ConsumerNetworkClient의 send 메서드를 통해 시작된다. ConsumerNetworkClient는 send 메서드를 통해 전달된 모든 요청을 ClientRequest로 바꾼다. ClientRequest에는 요청이 완료되었을 때 호출될 RequestFuture가 설정되어 있다. 이 RequestFuture는 ConsumerNetworkClient의 send 메서드를 호출한 콜러(caller)에게 반환된다. 콜러는 RequestFuture를 통해 비동기 요청이 완료되었는지 확인한다.

ConsumerNetworkClient는 ClientRequest를 바로 전송하지 않고 내부 버퍼인 Unsent Map에 먼저 저장한다. Unsent Map의 Key는 요청을 전송할 브로커의 호스트이고 Value는 브로커로 전송해야 하는 ClientRequest의 리스트이다.

ClientRequest의 전송은 ConsumerNetworkClient의 poll 메서드가 호출될 때 이루어진다(그림 5의 a). ConsumerNetworkClient의 poll 메서드는 KafkaConsumer가 실행 중인 스레드 외에 HeartBeat 스레드에 의해서도 호출된다.

다음으로 응답이 처리되는 과정에 대해 알아보겠다. 다음 그림은 ConsumerNetworkClient가 응답을 처리하는 과정이다.

![KafkaCosumerStructure-ConsumerNetworkClientResponse.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-c72b66577f42.png)

그림 6 ConsumerNetworkClient의 응답 처리 과정

브로커가 응답을 주면 NetworkClient는 ConsumerNetworkClient의 내부 큐인 pendingCompletion에 send 메서드 호출 시 콜러(Caller)에게 반환된 RequestFuture를 추가한다. pendingCompletion에 추가된 RequestFuture는 ConsumerNetworkClient의 poll 메서드가 호출될 때 complete 메서드가 호출되어 완료 처리가 된다.

## SubscriptionState

KafkaConsumer는 다른 메시지 시스템과 달리 자신이 소비하는 토픽, 파티션, 오프셋 정보를 추적 및 관리한다. SubscriptionState가 토픽, 파티션, 오프셋 정보 관리를 담당하고 있다.

![KafkaCosumerStructure-SubscriptionState.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-c72ca8e77fb3.png)

그림 7 SubscriptionState

KafkaConsumer에 토픽, 파티션 할당은 assign 메서드를 통해 이루어진다. 컨슈머의 그룹 관리 기능을 사용하지 않고 사용자가 assign 메서드를 직접 호출하여 수동으로 토픽, 파티션을 할당할 수 있는데 이 경우에는 컨슈머 리밸런스가 일어나지 않는다.

컨슈머의 그룹 관리 기능을 사용하기 위해서는 특정 토픽에 대해 구독 요청을 해야 한다. 구독 요청은 KafkaConsumer의 subscribe 메서드를 통해 한다. 사용자가 구독을 요청한 토픽 정보는 SubscriptionState의 subscription에 저장된다. subscription에 저장된 토픽 정보는 컨슈머 리밸런스 과정에서 사용된다. 그룹 관리 기능을 사용한 경우에는 컨슈머 리밸런스 과정에서 코디네이터에 의해 토픽, 파티션이 할당된다.

assign 메서드를 통해 할당된 파티션은 초기 오프셋 값 설정이 필요하다. 초기 오프셋 값이 없으면 Fetch가 불가능한 파티션으로 분류된다. seek 메서드를 통해 초기 오프셋 값을 설정한다. 초기 오프셋 설정은 오프셋 초기화 과정을 통해 이루어진다. 사용자가 KafkaConsumer의 seek 메서드를 사용하여 설정할 수도 있다.

## ConsumerCoordinator

ConsumerCoordinator는 컨슈머 리밸런스, 오프셋 초기화(일부), 오프셋 커밋을 담당한다. ConsumerCoordinator 내부에는 Heartbeat 스레드가 존재한다. Heartbeat 스레드는 주기적으로 heartbeat를 GroupCoordinator에게 전송한다.

![KafkaCosumerStructure-ConsumerCoordinatorStructure.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-c7359d6307f0.png)

그림 8 ConsumerCoordinator

ConsumerCoordinator에서는 RequestFutureAdapter를 상속한 다양한 Handler 클래스를 사용하고 있다.

컨슈머 리밸런스에서는 JoinGroupResponseHandler, SyncGroupResponseHandler가 사용된다. 오프셋 초기화 과정에서는 OffsetFetchResponseHandler가 사용된다. 오프셋 커밋 과정에서는 OffsetCommitResponseHandler가 사용되고, Heartbeat 전송 과정에서는 HeartbeatResponseHandler가 사용된다.

다음으로 각 과정에 대해 자세히 알아보겠다.

### 컨슈머 리밸런스

파티션의 소유권이 다른 컨슈머로 이전되는 것을 리밸런스라고 한다. 리밸런스는 토픽에 변경 사항이 생기거나 컨슈머 그룹에 새로운 컨슈머가 추가되거나 컨슈머 그룹에 속해 있던 컨슈머가 제외되는 경우에 발생한다.

리밸런스가 발생한 컨슈머 그룹은 리밸런스 작업이 끝날 때까지 브로커로부터 데이터를 가져오지 않는다. 따라서 리밸런스가 진행되는 동안에는 컨슈머들이 일시 정지된 것처럼 보인다. 리밸런스는 KafkaConsumer의 가용성과 확장성을 높여주기 때문에 중요한 작업이다. ConsumerCoordinator는 서버측 코디네이터(GroupCoordinator)에 의존하여 컨슈머 리밸런스를 수행한다. 컨슈머 리밸런스는 2단계로 이루어진다.

![KafkaCosumerStructure-ConsumerReProtocol.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-c74ccdb311f4.png)

그림 9 컨슈머 리밸런스 과정

- GroupCoordinator 찾기
	- ConsumerCoordinator는 [FindCoordinator API](https://kafka.apache.org/protocol#The_Messages_FindCoordinator) 를 사용하여 JoinGroup 요청을 보낼 GroupCoordinator를 찾는다.
- 1단계: Join
	- KafkaConsumer들이 [JoinGroup API](https://kafka.apache.org/protocol#The_Messages_JoinGroup) 를 사용하여 GroupCoordinator에게 그룹 참여 요청을 보내는 단계이다.
		- GroupCoordinator는 그룹에 참여하는 클라이언트 정보와 그룹 메타데이터(subscription 정보)를 수집한다.
		- GroupCoordinator에 의해 리더로 선정된 클라이언트가 그룹 내 파티션을 할당한다.
- 2단계: Sync
	- 리더가 파티션 할당을 마치면 [SyncGroup API](https://kafka.apache.org/protocol#The_Messages_SyncGroup) 를 사용하여 파티션 할당 결과를 그룹 내에 전파한다.

#### GroupCoordinator 찾기

GroupCoordinator는 그룹이 구독한 토픽과 파티션을 관리하고 그룹의 멤버를 관리한다. 따라서 KafkaConsumer가 그룹 참여를 요청하기 위해서는 먼저 GroupCoordinator를 찾아야 한다. GroupCoordinator는 FindCoordinator API를 통해 찾을 수 있다. FindCoordinator API 요청을 보낼 브로커는 브로커들 중 랜덤으로 하나를 선택한다.

**[FindCoordinator API](https://kafka.apache.org/protocol#The_Messages_FindCoordinator)**

- 요청 예
```bash
(
    type=GroupCoordinatorRequest,
    groupId=testGroup
)
```
- 응답 예
```nix
{
    error_code=0,
    coordinator={
        node_id=1,
        host=broker01,
        port=9092
    }
}
```

FindCoordinator API 요청을 보내 특정 그룹에 대한 GroupCoordinator 정보를 요청하면 브로커는 GroupCoordinator의 호스트와 포트 정보를 응답으로 준다.

#### 1단계: Join

첫 번째 단계는 KafkaConsumer가 GroupCoordinator에게 그룹 참여를 요청하는 단계이다. GroupCoordinator를 찾은 ConsumerCoordinator는 JoinGroup API를 사용하여 GroupCoordinator에게 그룹 참여를 요청한다. ConsumerCoordinator는 JoinGroup API 요청을 보내기 전에 Heartbeat 스레드가 JoinGroup을 방해하지 못하도록 Heartbeat 스레드를 일시 정지시킨다.

**[JoinGroup API](https://kafka.apache.org/protocol#The_Messages_JoinGroup)**

- 요청 예
```nix
(
    type: JoinGroupRequest,
    groupId=testGroup,
    sessionTimeout=10000,
    rebalanceTimeout=300000,
    memberId=,
    protocolType=consumer,
    groupProtocols=(
        name: range,
        metadata: topic1, topic2
    )
)
```
- 응답 예
```clojure
{
    error_code=0,
    generation_id=11,
    group_protocol=range,
    leader_id=consumer-1,
    member_id=consumer-1,
    members=[
        {
            member_id=consumer-1,
            member_metadata=Subscription(topics=[topic1, topic2])
        },
        {
            member_id=consumer-2,
            member_metadata=Subscription(topics=[topic2, topic2])
        }
    ]
}
```

JoinGroup API 요청에는 groupId, sessionTimeout, rebalanceTimeout, groupProtocols이 포함된다.

- groupId
	- 컨슈머가 속할 그룹을 나타낸다.
- sessionTimeout
	- 컨슈머가 sessionTimeout 시간 내에 heartbeat 요청을 GroupCoordinator에 보내지 않으면 GroupCoordinator는 해당 컨슈머가 죽은 것으로 판단한다.
		- `session.timeout.ms` 를 통해 설정한다.
- rebalanceTimeout
	- 그룹에 속한 컨슈머들은 리밸런스가 발생했을 때 rebalanceTimeout 이내에 JoinGroup 요청을 보내야 한다. rebalanceTimeout 이내에 JoinGroup 요청을 보내지 않은 컨슈머는 컨슈머 그룹에서 제외된다.
		- rebalanceTimeout은 `max.poll.interval.ms` 으로 설정된다.
- groupProtocols
	- 메타데이터로 컨슈머가 구독하려는 토픽과 컨슈머가 지원하는 파티션 할당 정책이 포함된다.
		- 컨슈머가 지원하는 파티션 할당 정책은 `partition.assignment.strategy` 을 통해 설정한다. `partition.assignment.strategy` 의 기본값은 `org.apache.kafka.clients.consumer.RangeAssignor` 이다.

JoinGroup API 요청을 받은 GroupCoordinator는 JoinGroup API의 응답으로 현재 컨슈머의 Id(member *id)와 그룹 리더의 Id(leader* id), 그룹 멤버 정보(members), 그룹 파티션 할당 정책(group\_protocol)을 보낸다.

member *id와 leader* id가 같은 컨슈머가 리더가 되며, 리더는 그룹 내에 파티션을 할당할 책임이 있다.

GroupCoordinator는 가장 처음으로 그룹에 참여한 클라이언트를 리더로 선출한다. 리더로 선정된 컨슈머는 그룹 파티션 할당 정책에 따라 그룹에 파티션을 할당한다. Kafka는 다양한 파티션 할당 정책을 지원하고 있다.

![KafkaCosumerStructure-Assignor.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-c71c4f9f2fe2.png)

그림 10 파티션 할당 정책

Kafka에서는 `RangeAssignor`, `RoundRobinAssignor`, `StickyAssignor` 를 기본으로 제공한다. 만약 이외에 커스텀한 파티션 할당 정책이 필요한 경우에는 `PartitionAssignor` 을 구현한 후 `partition.assignment.strategy` 에 설정하면 된다.

`RangeAssignor` 는 각 토픽별로 파티션을 할당한다. `RangeAssignor` 는 파티션은 숫자 순서대로 정렬을 하고 컨슈머는 사전 순서대로 정렬을 한다. 그리고 각 토픽의 파티션을 컨슈머 숫자로 나누어 컨슈머에게 할당해야 하는 파티션 수를 결정한다. 만약 고르게 나누어지지 않는다면 앞쪽 컨슈머가 더 많은 파티션을 할당받는다. 그림 10의 경우 `RangeAssignor` 는 파티션을 `Consumer 1 = {T1-0, T1-1, T2-0, T2-1}`, `Consumer 2 = {T1-2, T2-2}` 으로 할당했다.

`RoundRobinAssignor` 는 모든 파티션을 컨슈머에게 번갈아가면서 할당한다. 그림 10의 경우 `RoundRobinAssignor` 는 파티션을 `Consumer 1 = {T1-0, T1-2, T2-1}`, `Consumer 2 = {T1-1, T2-0, T2-2}` 으로 할당했다.

`StickyAssignor` 는 최대한 파티션을 균등하게 분배하고, 파티션 재할당이 이루어질 때 파티션의 이동을 최소화하려는 할당 정책이다.

#### 2단계: Sync

그룹에 참여하는 모든 컨슈머는 2단계에서 SyncGroup API 요청을 GroupCoordinator에 보내고 리더는 파티션 할당 결과를 SyncGroup API 요청에 포함시킨다.

GroupCoordinator는 SyncGroup API 응답으로 컨슈머에 할당된 토픽, 파티션 정보를 보낸다.

**[SyncGroup API](https://kafka.apache.org/protocol#The_Messages_SyncGroup)**

- 요청 예
```scheme
(
    type=SyncGroupRequest,
    groupId=testGroup,
    generationId=25,
    memberId=consumer-1,
    groupAssignment=(
        (memberId=consumer-1, assignment=Assignment(partitions=[topic1-0, topic1-1, topic2-0, topic2-1]))
        (memberId=consumer-2, assignment=Assignment(partitions=[topic1-2, topic2-2]))
    )
)
```
- 응답 예
```
{
    error_code=0,
    member_assignment=Assignment(partitions=[topic1-0, topic1-1, topic2-0, topic2-1]))
}
```

SyncGroup API 응답을 받은 컨슈머는 자신에게 할당된 토픽, 파티션 정보를 SubscriptionState의 assign 메서드를 사용하여 업데이트한다.

최신 Kafka 버전에서는 컨슈머 리밸런스 과정에서 KafkaConsumer 처리가 정지되는 Stop the world 현상을 없애기 위해 컨슈머 리밸런스 과정을 증분으로 진행하는 기능이 추가되었다. 자세한 내용은 아래 문서를 참고하기 바란다.

- [Design and Implementation of Incremental Cooperative Rebalancing](https://www.confluent.io/online-talks/design-and-implementation-of-incremental-cooperative-rebalancing-on-demand/)
- [Incremental Cooperative Rebalancing in Apache Kafka: Why Stop the World When You Can Change It?](https://www.confluent.io/blog/incremental-cooperative-rebalancing-in-kafka/)
- [KAFKA-8179: Incremental Rebalance Protocol for Kafka Consumer](https://issues.apache.org/jira/browse/KAFKA-8179)

### 오프셋 초기화

브로커에서 데이터를 읽기 위해서는 파티션의 초기 오프셋 값이 필요하다. SubscriptionState의 assign 메서드를 통해 할당된 파티션은 초기 오프셋 값이 없다. KafkaConsumer는 오프셋 초기화 과정을 통해 초기 오프셋 값을 설정한다.

![KafkaCosumerStructure-OffsetInit.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-c74d0e471266.png)

그림 11 오프셋 초기화 과정

오프셋 초기화는 커밋된 오프셋을 가져오는 과정과 커밋된 오프셋이 없는 경우 오프셋 초기화 정책에 따라 오프셋을 초기화하기 위해 파티션의 오프셋을 가져오는 과정으로 이루어진다.

#### 커밋된 오프셋 가져오기

초기 오프셋 값이 없는 경우 KafkaConsumer는 ConsumerCoordinator를 통해 커밋된 오프셋 값을 확인한다. ConsumerCoordinator는 OffsetFetch API를 통해 GroupCoordinator에게 커밋된 오프셋 정보를 요청한다(그림 11의 3).

**[OffsetFetch API](https://kafka.apache.org/protocol#The_Messages_OffsetFetch)**

- 요청 예
```nix
(
    type=OffsetFetchRequest,
    groupId=testGroup,
    partitions=topic1-0
)
```
- 응답 예
```nix
{
    responses=[
        {
            topic=topic1,
            partition_responses=[{partition=0, offset=4067, metadata=, error_code=0}]
        }
    ],
    error_code=0
}
```

GroupCoordinator는 OffsetFetch API 응답으로 커밋된 오프셋 정보를 알려준다(그림 11의 4). ConsumerCoordinator는 OffsetFetch API를 통해 가져온 커밋된 오프셋 정보를 SubscriptionState에 업데이트한다(그림 11의 6). SubscriptionState에 업데이트된 오프셋 값은 Fetcher에 의해 파티션의 오프셋 초기값으로 설정된다(그림 11의 9).

#### 파티션의 오프셋 가져오기

만약 커밋된 오프셋 정보가 없다면 KafkaConsumer는 `auto.offset.reset` 설정에 따라 오프셋을 초기화한다. `auto.offset.reset` 에는 `earliest`, `latest`, `none` 을 설정할 수 있다. 기본값은 `latest` 이다.

- `earliest`: 파티션의 가장 처음 오프셋을 사용한다.
- `latest`: 파티션의 가장 마지막 오프셋을 사용한다.
- `none`: 오프셋을 초기화하지 않는다.

`auto.offset.reset` 설정에 따라 오프셋을 초기화하기 위해서는 파티션의 가장 처음 오프셋이나 가장 마지막 오프셋을 알아야 한다. Fetcher는 파티션의 가장 처음 오프셋과 가장 마지막 오프셋을 알아내기 위해 특정 시간(timestamp)에 해당하는 오프셋을 조회하는 ListOffsets API를 활용한다. ListOffsets API 요청에 timestamp를 -2로 설정하면 가장 처음 오프셋을 알 수 있고 timestamp를 -1로 설정하면 가장 마지막 오프셋을 알 수 있다. `auto.offset.reset` 가 `earliest` 인 경우에는 ListOffsets API 요청에 timestamp를 -2로 설정하고 `latest` 인 경우에는 timestamp를 -1로 설정한다.

Fetcher는 파티션의 가장 처음/마지막 오프셋을 알아내기 위해 파티션 리더 브로커로 ListOffsets API 요청을 보낸다(그림 11의 11).

**[ListOffsets API](https://kafka.apache.org/protocol#The_Messages_ListOffsets)**

- 요청 예
```
(
    type=ListOffsetRequest,
    replicaId=-1,
    partitionTimestamps={topic1-0=-1},
    minVersion=0
)
```
- 응답 예
```nix
{
    responses=[
        {
            topic=topic1,
            partition_responses=[{partition=0, error_code=0, timestamp=-1, offset=4067}]
        }
    ]
}
```

파티션 리더 브로커는 ListOffsets API 응답으로 timestamp에 해당하는 오프셋 정보를 알려준다.(그림 11의 12) 응답으로 받은 오프셋 값은 SubscriptionState의 seek 메서드를 통해 파티션의 초기 오프셋으로 설정된다(그림 11의 14).

### 오프셋 커밋

Kafka는 다른 메시지 서비스와 다르게 컨슈머가 오프셋 정보를 관리하기 때문에 데이터를 읽은 후 컨슈머는 적절한 시점에 오프셋을 커밋해야 한다.

만약 `enable.auto.commit` 설정이 true인 경우 KafkaConsumer가 `auto.commit.interval.ms` 마다 오프셋을 자동으로 커밋한다. `enable.auto.commit` 의 기본값은 true이고 `auto.commit.interval.ms` 의 기본값은 5000ms(5초)이다.

자동 커밋 방식은 편리하지만 리밸런스나 비정상적인 클라이언트 종료 등으로 데이터 누락이 발생할 수 있다. 이를 방지하기 위해서는 수동으로 적절한 시점에 오프셋을 커밋해야 한다.

![KafkaCosumerStructure-OffsetCommit1.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-c7543d423834.png)

그림 12 commitSync 메서드를 사용하여 오프셋을 커밋하는 과정

수동으로 오프셋을 커밋하려면 KafkaConsumer의 commitSync 메서드를 호출하면 된다. 그림 12는 KafkaConsumer의 commitSync 메서드를 사용하여 오프셋을 커밋하는 과정을 보여주고 있다. ConsumerCoordinator는 OffsetCommit API를 사용하여 GroupCoordinator에게 오프셋 커밋을 요청한다.

**[OffsetCommit API](https://kafka.apache.org/protocol#The_Messages_OffsetCommit)**

- 요청 예
```nix
(
    type=OffsetCommitRequest,
    groupId=testGroup,
    memberId=consumer-1,
    generationId=37,
    retentionTime=-1,
    OffsetData={
        topic1-0=(timestamp=-1, offset=5734, metadata=),
        topic1-1=(timestamp=-1, offset=5113, metadata=)
    }
)
```
- 응답 예
```clojure
{
    responses=[
        {
            topic=topic1,
            partition_responses=[
                {partition=0,error_code=0},
                {partition=1,error_code=0}
            ]
        }
    ]
}
```

OffsetCommit API의 요청에는 커밋할 토픽, 파티션과 오프셋 정보가 포함된다. GroupCoordinator는 OffsetCommit API의 응답으로 오류 코드(error\_code)를 보내는데 오류 코드가 0이면 정상이다.

commitSync 메서드를 사용하여 오프셋 커밋을 요청하면 KafkaConsumer가 오프셋 커밋 요청이 끝날 때까지 대기하기 때문에 KafkaConsumer가 일시 중지된다. 만약 이를 방지하고 싶다면 commitAsync 메서드를 사용하여 비동기 커밋을 해야 한다.

### HeartBeat 스레드

HeartBeat 스레드는 [KIP-62](https://cwiki.apache.org/confluence/display/KAFKA/KIP-62%3A+Allow+consumer+to+send+heartbeats+from+a+background+thread) 에서 제안되어 0.10.1 버전부터 추가되었다.

0.10.1 이전에는 HeartBeat 시간(Consumer가 중단되진 않았는지 GroupCoordinator가 감시하는 시간)과 Polling 간격 시간(브로커로부터 가져온 데이터를 처리하는 시간)이 구분되지 않아서 싱글 스레드로 KafkaConsumer을 사용할 때 Polling 간격이 session timout을 초과하면 컨슈머 그룹에서 제외되는 문제가 있었다. 또한 데이터 처리 시간이 항상 session timout보다 긴 경우에는 사용자가 문제를 인지하고 수정하기 전까지는 프로세스가 진행되지 않는 문제가 있었다.

KIP-62는 이러한 문제를 해결하기 위해 백그라운드에서 동작하는 HeartBeat 스레드를 추가했다.

![KafkaCosumerStructure-heartbeat-thread.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-c75fadb409f8.png)

그림 13 HeartBeat 스레드와 Process 스레드

HeartBeat 스레드 추가로 Polling과 HeartBeat 구분이 가능해졌다.

- `max.poll.interval.ms`
	- poll 메서드는 `max.poll.interval.ms` 이내에 호출되어야 한다.
		- 만약 poll 메서드가 제한 시간 내에 호출되지 않으면 해당 컨슈머는 정상이 아닌 것으로 간주되어 컨슈머 그룹에서 제외되고 컨슈머 리밸런스가 일어난다.
		- HeartBeat 스레드가 현재 시간과 마지막으로 poll 메서드가 호출된 시간의 차이를 계산하여 해당 시간의 차가 `max.poll.interval.ms` 보다 큰 경우 컨슈머 그룹에서 탈퇴한다.
		- `max.poll.interval.ms` 의 기본값은 300000ms(5분)이다.
- `heartbeat.interval.ms`
	- Heartbeat 전송 시간 간격이다. HeartBeat 스레드는 `heartbeat.interval.ms` 간격으로 Heartbeat을 전송한다.
		- `heartbeat.interval.ms` 의 값은 항상 `session.timeout.ms` 보다 작아야 하며 일반적으로 `session.timeout.ms` 의 1/3 이하로 설정한다.
		- `heartbeat.interval.ms` 의 기본값은 3000ms(3초)이다.
- `session.timeout.ms`
	- `session.timeout.ms` 내에 HeartBeat이 도착하지 않으면 브로커는 해당 컨슈머를 그룹에서 제거한다.
		- `session.timeout.ms` 는 브로커 설정인 `group.min.session.timeout.ms` 와 `group.max.session.timeout.ms` 사이 값이여야 한다. `group.min.session.timeout.ms` 의 기본값은 6000ms(6초)이고, `group.max.session.timeout.ms` 의 기본값은 버전에 따라 다른데 0.10.2에서는 300000ms(5분)이고 최신 버전(2.7)에서는 1800000ms(30분)이다.
		- `session.timeout.ms` 의 기본값은 10000ms(10초)이다.

그림 13에서 Process 스레드가 정상적으로 동작하지 않는다면 `max.poll.interval.ms` 으로 감지가 된다. 만약 KafkaConsumer가 정상이 아닌 경우에는 `session.timeout.ms` 로 감지된다.

## Fetcher

Fetcher는 브로커로부터 데이터를 가져오는 역할을 담당하는 클래스이다.

![KafkaCosumerStructure-Fetcher.png](https://d2.naver.com/content/images/2021/03/0a705587-7652-1b4c-8177-c7578a534acf.png)

그림 14 Fetcher

Consumer 리밸런스와 오프셋 초기화 과정이 끝나면 KafkaConsumer의 poll 메서드를 통해 브로커로부터 데이터를 가져올 수 있다. KafkaConsumer의 poll 메서드가 호출되면 먼저 Fetcher의 fetchedRecords 메서드가 호출된다. fetchedRecords 메서드는 내부 캐시인 nextInLineRecords와 completedFetches를 확인하여 브로커로부터 이미 가져온 데이터가 있는 경우에는 `max.poll.records` 설정 값만큼 레코드를 반환한다. `max.poll.records` 의 기본값은 500이다.

브로커에서 가져온 데이터가 없는 경우에는 KafkaConsumer는 Fetcher의 sendFetches 메서드를 호출한다. Fetcher의 sendFetches 메서드는 Fetch API 요청을 파티션 리더가 위치한 각 브로커에게 보낸다. KafkaConsumer는 Fetcher가 브로커로부터 응답을 받을 때까지 대기한다.

**[Fetch API](https://kafka.apache.org/protocol#The_Messages_Fetch)**

- 요청 예
```nix
(
    type:FetchRequest,
    replicaId=-1,
    maxWait=500, // "fetch.max.wait.ms"
    minBytes=1,  // "fetch.min.bytes"
    maxBytes=52428800, // "fetch.max.bytes"
    fetchData={
        topic1-0=(offset=5734, maxBytes=1048576), // "max.partition.fetch.bytes"
        topic1-1=(offset=5810, maxBytes=1048576)
    }
)
```
- 응답 예
```clojure
{
    throttle_time_ms=0,
    responses=[
        {
            topic=topic1,
            partition_responses=[
                {partition_header={partition=0,error_code=0,high_watermark=5734},record_set=[...]},
                {partition_header={partition=1,error_code=0,high_watermark=5810},record_set=[...]}
            ]
        }
    ]
}
```

Fetch API 요청에는 다음 설정들이 사용된다.

- `fetch.max.wait.ms`
	- 브로커가 Fetch API 요청을 받았을 때 `fetch.min.bytes` 값만큼 데이터가 없는 경우 응답을 주기까지 최대로 기다릴 시간이다.
		- 기본값은 500ms(0.5초)이다.
- `fetch.min.bytes`
	- Fetch API 요청이 왔을 때 브로커는 최소한 `fetch.min.bytes` 값만큼 데이터를 반환해야 한다.
		- 반환할 만큼 데이터가 충분하지 않다면 브로커는 데이터가 누적되길 기다린다.
		- 기본값은 1이다.
- `fetch.max.bytes`
	- Fetch API 요청에 대해 브로커가 반환해야 하는 최대 데이터 크기이다.
		- 이 값은 절대적으로 적용되는 값은 아니다. 첫 번째 파티션의 첫 번째 메시지가 이 값보다 크다면 컨슈머가 계속 진행될 수 있도록 데이터가 반환된다.
		- 브로커가 허용하는 최대 메시지 크기는 `message.max.bytes` 와 `max.message.bytes` 를 통해 설정한다.
		- 기본값은 52428800(50MiB)이다.
- `max.partition.fetch.bytes`
	- 브로커가 반환할 파티션당 최대 데이터 크기이다.
		- `fetch.max.bytes` 와 동일하게 첫 번째 파티션의 첫 번째 메시지가 이 값보다 크다면 컨슈머가 계속 진행될 수 있도록 데이터가 반환된다.
		- 기본값은 1048576(1MiB)이다.

Fetcher가 브로커로부터 응답을 받으면 KafkaConsumer는 Fetcher의 fetchedRecords 메서드를 다시 호출하여 사용자에게 반환할 레코드를 가져온다. KafkaConsumer는 레코드를 사용자에게 반환하기 전에 다음 poll 메서드 호출 시에 브로커로부터 응답을 대기하는 시간을 없애기 위해 Fetcher의 sendFetches 메서드를 호출한 후 레코드를 반환한다.

## 마치며

지금까지 KafkaConsumer 구성 요소와 동작 방식에 대해 알아보았다.

KafkaConsumer의 poll 메서드가 호출되면 KafkaConsumer는 분주히 브로커로부터 데이터를 가져올 준비를 한다. KafkaConsumer가 올바르게 동작하기 위해서는 리밸런스는 필요하지만 안정적인 데이터 처리를 위해서 불필요한 리밸런스는 줄이는 것이 좋다. 불필요한 리밸런스를 줄이기 위해서는 `max.poll.interval.ms` 와 `max.poll.records` 를 적절히 조정하여 poll 메서드가 일정 간격으로 호출되도록 해야 한다. 필요한 경우에는 `heartbeat.interval.ms` 와 `session.timeout.ms` 를 조정한다.

앞에서 언급했듯이 리밸런스가 유발하는 Stop the world 현상을 완화시키기 위해 최근에 Kafka는 컨슈머 리밸런스 과정을 증분으로 진행하는 기능을 추가했다. 증분 리밸런스를 통해 리밸런스 과정에서 발생하는 컨슈머 정지 시간을 줄일 수 있다. 최신 버전의 KafkaConsumer를 사용한다면 증분 리밸런스 기능 사용을 고려해보면 좋을 것 같다.

또한 KafkaConsumer는 다양한 Processing guarantees(No guarantee, At most once, At least once, Effectively once)를 지원한다. At least once 방식이 성능은 높이면서 처리를 보장한다. 컨슈머가 중복된 데이터를 처리해도 문제가 없다면 At least once 방식을 사용하는 것이 유리하다.

Kafka를 운영하다 보면 다양한 이슈와 맞닥뜨리게 되는데 이슈를 이해하기 위해서는 내부 구성 요소와 동작 방식에 대한 이해가 필요할 때가 있다. 이 글이 KafkaConsumer의 동작 방식을 이해하는 데 진입점이 될 수 있으면 좋겠다.

Tag

![](https://d2.naver.com/image/20210407/894392911471.png)

글쓴이

강민우|네이버 Search

소개

네이버 검색에서 데이터 저장소 개발 및 운영을 담당하고 있습니다.

관련글

- [![썸네일](https://d2.naver.com/content/images/2020/08/hwhw_200813.png)
	KafkaProducer Client Internals
	](https://d2.naver.com/helloworld/6560422)
- [![썸네일](https://d2.naver.com/content/images/2022/02/kafka_2022_Helloworld.png)
	Kafka NetworkClient Internals
	](https://d2.naver.com/helloworld/0853669)
- [![썸네일](https://d2.naver.com/content/images/2023/10/PC_170x120_231021.png)
	Kafka에서 파티션 증가 없이 동시 처리량을 늘리는 방법 - Parallel Consumer
	](https://d2.naver.com/helloworld/7181840)
- [![썸네일](https://d2.naver.com/content/images/2016/04/---.png)
	대용량 스트리밍 데이터 실시간 분석
	](https://d2.naver.com/helloworld/7731491)

##### 댓글

8

- 동동
	좋은 글 감사합니다.
	2023-12-11 10:37
	[**답글** 0](#)
	**공감/비공감** [공감 *0*](#) [비공감 *0*](#)
- 안녕
	정독했습니다. 감사합니다!
	2023-11-08 09:37
	[**답글** 0](#)
	**공감/비공감** [공감 *0*](#) [비공감 *0*](#)
- Seanical
	KafkaConsumer의 poll 메서드가 호출되면 먼저 Fetcher의 fetchedRecords 메서드가 호출된다. 여기서 fetchedRecords -> fetchRecords 인것같습니다.
	2022-07-24 23:20
	[**답글** 0](#)
	**공감/비공감** [공감 *0*](#) [비공감 *0*](#)
- ㅁㄴㅇㄹ
	좋은 글 감사합니다.
	2022-04-13 00:34
	[**답글** 0](#)
	**공감/비공감** [공감 *0*](#) [비공감 *0*](#)
- 찬찬
	좋은글 감사합니다 ~
	2021-10-21 08:15
	[**답글** 0](#)
	**공감/비공감** [공감 *0*](#) [비공감 *0*](#)
