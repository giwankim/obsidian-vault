---
title: "Kafka NetworkClient Internals"
source: "https://d2.naver.com/helloworld/0853669"
author:
published:
created: 2026-06-28
description:
tags:
  - "clippings"
---

> [!summary]
> KafkaProducer와 KafkaConsumer가 브로커와 통신할 때 사용하는 NetworkClient의 내부 구조를 분석한다. 브로커 연결 상태 관리(ClusterConnectionStates, DISCONNECTED~READY), IdleExpiryManager의 LRU 연결 정리, InFlightRequests, Java NIO Selector를 이용한 I/O 멀티플렉싱, KafkaChannel을 통한 인증·암호화(PLAINTEXT/SSL/SASL)를 설명한다. 또한 토픽으로부터 브로커 주소를 알아내는 Metadata와 MetadataUpdater의 갱신 동작 및 관련 설정값을 다룬다.

Apache Kafka는 Distributed Event Streaming Platform으로, 데이터의 생산자(producer)와 소비자(consumer)를 중개하는 메시징 시스템입니다. Kafka의 기본 개념과 용어에 관해서는 Kafka가 제공하는 문서인 [Introduction](https://kafka.apache.org/intro) 과 [Main Concpets and Terminology](https://kafka.apache.org/documentation/#intro_concepts_and_terms) 를 참고하기 바랍니다.

Kafka는 데이터의 생산자(KafkaProducer)가 데이터를 Kafka 클러스터로 전송할 수 있도록 Producer API를 제공하고, 데이터의 소비자(KafkaConsumer)가 데이터를 읽을 수 있도록 Consumer API를 제공합니다.

![그림 1 Kafka 클러스터와 KafkaProducer, KafkaConsumer](https://d2.naver.com/content/images/2022/01/KafkaClientInternalsNetworkClient-01.png)

그림 1 Kafka 클러스터와 KafkaProducer, KafkaConsumer

이전 글인 [KafkaProducer Client Internals](https://d2.naver.com/helloworld/6560422) 에서 설명한 것처럼 KafkaProducer는 효율적인 데이터 전송과 압축을 위해 RecordAccumulator를 사용해 여러 개의 Record를 하나의 RecordBatch로 묶어서 전송하는 로직을 도입했습니다. KafkaConsumer에서는 [KafkaConsumer Client Internals](https://d2.naver.com/helloworld/0974525) 에서 설명한 것처럼 여러 개의 KafkaConsumer가 Kafka 클러스터에서 데이터를 효과적으로 읽을 수 있도록 리밸런스(rebalance) 동작과 Processing guarantees를 구현했습니다.

이 글에서는 ["KafkaProducer Client Internals"](https://d2.naver.com/helloworld/6560422) 와 ["KafkaConsumer Client Internals"](https://d2.naver.com/helloworld/0974525) 에서 구체적으로 다루지 않은 NetworkClient와 I/O 멀티플렉싱(I/O multiplexing 동작에 대해 알아보겠습니다.

이 글은 Kafka 클라이언트 0.10.2.1 버전을 기준으로 작성되었습니다.

## NetworkClient

Kafka 클라이언트인 KafkaProducer와 KafkaConsumer는 브로커 노드와 통신하기 위해 NetworkClient라는 클래스를 사용한다.

![그림 2 Kafka 클라이언트에서의 NetworkClient](https://d2.naver.com/content/images/2022/01/KafkaClientInternalsNetworkClient-02.png)

그림 2 Kafka 클라이언트에서의 NetworkClient

그림 2에서 볼 수 있듯이 Kafka 클라이언트의 내부 로직에서 브로커에 보낼 ClientRequest가 만들어진다. Kafka 클라이언트의 내부 로직에서 생성된 ClientRequest는 NetworkClient로 전해져 네트워크를 통해 브로커로 전송된다. 브로커로부터 응답이 도착하면 NetworkClient가 응답을 읽어 ClientResponse로 만들어 내부 로직으로 전달한다.

NetworkClient는 다음과 같은 KafkaClient 인터페이스를 구현한 클래스이다.

예제 1 KafkaClient 인터페이스

```java
public interface KafkaClient extends Closeable {

    // 노드에 요청을 보낼 수 있는 상태인지 확인
    boolean isReady(Node node, long now);

    // 노드에 요청을 보낼 수 있는 상태인지 확인하고 필요한 경우 Connection 생성
    boolean ready(Node node, long now);

    // 다음 연결 시도까지 얼마나 기다려야 하는지 확인
    long connectionDelay(Node node, long now);

    // 노드로의 연결이 끊겼는지 확인
    boolean connectionFailed(Node node);

    // 노드로의 연결 닫기
    void close(String nodeId);

    // 보내야 할 요청을 큐에 저장(나중에 준비되면 요청을 전송)
    void send(ClientRequest request, long now);

    // 실제 I/O 수행 및 받은 응답을 가져옴
    List<ClientResponse> poll(long timeout, long now);

    // 가장 요청을 적게 받은 노드를 선택
    Node leastLoadedNode(long now);

    // 브로커로 전송되었지만 응답을 아직 받지 못한 요청들의 총합
    int inFlightRequestCount();

    // 특정 브로커로 전송되었지만 응답을 아직 받지 못한 요청들의 수
    int inFlightRequestCount(String nodeId);

    // I/O 수행을 기다리고 있는 스레드를 깨움
    void wakeup();
}
```

KafkaClient 인터페이스의 메서드 이름이 나타내는 것처럼 NetworkClient는 Kafka 클라이언트와 브로커 노드들의 연결 상태를 관리하고 브로커 노드로 데이터를 쓰거나 브로커 노드에서 데이터를 읽는 역할을 한다.

### ClusterConnectionStates

NetworkClient는 브로커와의 연결 상태를 ClusterConnectionStates로 관리한다.

ClusterConnectionStates는 Kafka 클라이언트와 연결되어 있는 브로커의 연결 상태에 관한 정보를 브로커마다 NodeConnectionState 객체에 기록한다. 다음 그림에서 노란색 박스에 해당하는 NodeConnectionState에는 현재 연결 상태를 나타내는 ConnectionState와 마지막으로 연결을 시도했던 시간 정보가 기록된다.

![그림 3 ClusterConnectionStates를 통한 연결관리](https://d2.naver.com/content/images/2022/01/KafkaClientInternalsNetworkClient-03.png)

그림 3 ClusterConnectionStates를 통한 연결 관리

Kafka 클라이언트가 브로커와 연결을 시도하면 ConnectionState는 다음 그림과 같이 CONNECTING 상태와 CHECKING *API* VERSION 상태를 거쳐 최종적으로 READY 상태가 된다. Kafka 클라이언트가 브로커 노드와 요청과 응답을 주고받으려면 브로커와의 연결 상태가 READY 상태여야 한다. 만약 각 연결 단계에서 문제가 발생한다면 DISCONNECTED 상태로 바뀌고 브로커와 통신하기 위해 다시 연결을 시도한다.

![그림 4 ConnectionState의 변경 순서](https://d2.naver.com/content/images/2022/01/KafkaClientInternalsNetworkClient-04-1.png)

그림 4 ConnectionState의 변경 순서

ConnectionState의 각 연결 상태의 의미는 다음과 같다.

| 연결 상태 | 설명 |
| --- | --- |
| DISCONNECTED | 브로커와 연결이 끊긴 상태 |
| CONNECTING | 소켓을 생성하고 연결을 생성 중인 상태 |
| CHECKING\_API\_VERSIONS | 연결이 생성되었고 브로커와 API 버전이 호환되는지 확인 중인 상태 |
| READY | 브로커로 요청을 전송할 수 있는 상태 |

#### DISCONNECTED 상태

DISCONNECTED 상태는 Kafka 클라이언트와 브로커 노드의 연결이 끊긴 상태를 의미한다. 다음과 같이 다양한 경우에 브로커 노드와 연결이 DISCONNECTED 상태로 설정된다.

- 브로커 노드로의 연결 초기화가 실패한 경우
- API 버전이 호환되지 않는 경우
- 브로커 노드로 요청 전송이 실패한 경우
- 요청이 전송되고 응답을 기다리다가 타임아웃이 발생한 경우
- 일정 시간 동안 브로커로 새로운 요청을 보내지 않은 경우

브로커와 연결 상태가 DISCONNECTED 상태라면 브로커로 요청을 보내기 위해 다시 연결을 시도해야 한다. 이때 Kafka 클라이언트가 특정 브로커와의 연결을 너무 빈번하게 재시도하지 않도록 최소한 `reconnect.backoff.ms` 에 설정한 시간이 지난 이후에 재연결을 시도한다. `reconnect.backoff.ms` 설정의 기본값은 '50'으로, 브로커로 연결 시도 사이에 최소 50ms의 시간차를 둔다. 이 백오프(backoff) 시간을 보장하기 위해서 NetworkClient는 브로커의 NodeConnectionState에 마지막 연결 시도 시간을 기록한다.

#### CONNECTING 상태

Kafka 클라이언트가 브로커와 연결을 시도할 때 CONNECTING 상태가 된다. ConnectionState의 상태를 CONNECTING으로 변경하고 브로커와 통신하기 위한 SocketChannel을 생성한다. 이때 생성되는 SocketChannel의 크기는 `send.buffer.bytes` 에 설정된 송신 버퍼(send buffer size)의 크기와 `receive.buffer.bytes` 에 설정된 수신 버퍼(receive buffer)의 크기이다. 크기를 별도로 설정하지 않으면 송신 버퍼의 크기는 128KB이고, 수신 버퍼의 크기는 64KB이다. 만약 값을 '-1'로 설정하면 실행하는 운영체제의 기본값인 `SO_SNDBUF` 와 `SO_RCVBUF` 가 적용된다.

SocketChannel을 생성한 다음 [Java NIO](#javanio) 에서 설명할 I/O 멀티플렉싱을 위해 NetworkClient 내에 있는 Selector에 SocketChannel을 등록하고 KafkaChannel을 생성하는 등 네트워크 통신과 연결 관리에 필요한 각종 객체를 생성한다.

#### CHECKINGAPIVERSIONS 상태, READY 상태

Kafka 클라이언트와 브로커가 통신하기 위해 필요한 객체들이 생성되면 CHECKING *API* VERSIONS 상태로 ConnectionState의 상태를 변경한다. Kafka 클라이언트와 브로커 사이에 연결이 수립되어 통신은 가능하지만 둘 사이의 API 버전이 맞지 않다면 정상적으로 동작할 수 없다. Kafka 클라이언트와 브로커가 호환되는 API 버전인지 확인하기 위해 Kafka 클라이언트는 자신의 API 버전 정보를 담은 ApiVersionRequest를 생성해서 브로커로 전송한다. 그러면 브로커가 호환되는 버전인지를 판단해서 ApiVersionResponse를 Kafka 클라이언트에 돌려준다. Kafka 클라이언트는 이 응답을 통해 API 호환 여부를 알 수 있다.

API가 문제없이 호환된다면 브로커의 연결 상태는 READY 상태가 된다.

### IdleExpiryManager

Kafka 클라이언트는 불필요한 연결을 정리하기 위해 IdleExpiryManager를 사용한다. READY 상태로 통신할 준비가 되어 있는 브로커 연결을 일정 시간 동안 사용하지 않으면 IdleExpiryManager에 의해 연결이 정리될 수 있다.

NetworkClient는 브로커와 연결된 SocketChannel들을 Java NIO의 Selector에 등록한 다음 비동기로 연산을 수행한다. NetworkClient의 poll() 메서드가 주기적으로 실행되면서 Selector에 등록된 SocketChannel 중 이벤트가 있는 것들을 그때그때 비동기 방식과 논블로킹 방식으로 처리한다. IdleExpiryManager는 특정 SocketChannel에 어떤 이벤트가 처리되었을 때 그 시간을 기록해 두며, 이 시간을 기준으로 브로커 연결을 LRU(Least Recently Used) 알고리즘으로 관리한다.

Selector에서 이벤트를 처리할 때마다 IdleExpiryManager는 가장 오래된 브로커 연결이 `connections.max.idle.ms` 설정값만큼 지났는지 확인한다. 만약 가장 오래된 연결이 이 시간 동안 아무 일도 하지 않았다면 연결을 닫고 관련 객체들을 정리한다. 이 설정의 기본값은 '540000'으로, 9분 동안 아무 이벤트가 없었다면 연결이 정리된다. 만약 이 값을 음수로 지정하면 IdleExpiryManager를 생성하지 않으며 관련 동작도 수행하지 않는다.

### InFlightRequests

NetworkClient는 [KafkaProducer Client Internals](https://d2.naver.com/helloworld/6560422) 에서 설명한 InFlightRequests도 관리한다.

Kafka 클라이언트는 브로커에 요청(request)을 전송하고 응답(response)을 기다린다. 요청을 매번 하나씩만 보내고 응답을 기다린다면 매우 긴 시간 동안 브로커의 응답을 기다릴 것이다. Kafka 클라이언트는 성능 향상을 위해서 이전에 보낸 요청에 대한 응답을 받기 전에 다음 요청을 브로커로 전송할 수 있게 한다. 이를 'in-flight request'라고 한다. 'in-flight'는 '운항 중의'라는 뜻의 영어 단어로, Kafka 클라이언트에서는 브로커로 전송은 되었지만 응답을 아직 받지 못한 요청을 의미한다.

![그림 5 InFlightRequest 관리](https://d2.naver.com/content/images/2022/01/KafkaClientInternalsNetworkClient-05.png)

그림 5 InFlightRequest 관리

NetworkClient는 각 브로커로 전송한 요청을 Deque라는 자료구조에 저장한다. 브로커마다 전송할 수 있는 최대 요청은 `max.in.flight.requests.per.connection` 에 설정한 만큼이다. 이 값에 다다랐다면 SocketChannel을 통해 브로커로 데이터를 보낼 수 있는 상황이라도 추가 요청을 전송하지 않는다. 그림 5는 Broker1 브로커로 요청 Req1과 Req2, Req3이 순차적으로 전송된 상황이다. InFlightRequests의 Broker1 항목에 대한 Deque에 Req1과 Req2, Req3이 저장되어 있다.

브로커로부터 응답이 도착하면 그 브로커에 보냈던 요청을 저장해둔 Deque의 가장 앞쪽에서 요청을 하나 제거하고 응답을 처리한다. 만약 요청에 대한 응답에 오류가 있다면 Deque의 가장 앞에 있던 요청을 가장 뒤로 다시 넣고 요청을 브로커에 재전송한다. 이 때문에 `max.in.flight.requests.per.connection` 설정값을 1보다 큰 값으로 설정하면 오류가 발생했을 때 데이터 전송 순서가 바뀔 수 있다. 그림 5는 Broker1에서 응답 Res1이 온 상황이다. Res1이 왔으므로 Broker1의 Deque에서 가장 앞에 있는 Req1을 제거하고 Res1에 대한 처리를 한다.

## Selector

Kafka 클러스터는 보통 수십에서 수백 대에 이르는 브로커 노드로 구성되어 있다. 따라서 Kafka 클라이언트는 수많은 브로커와의 네트워크 통신을 효율적으로 관리해야 한다.

Kafka 클라이언트의 NetworkClient는 Java NIO를 사용해 브로커들과의 네트워크 통신을 구현했다. Kafka 클라이언트의 네트워크 통신 구현을 이해하기 위해 먼저 Java NIO를 사용한 I/O 멀티플렉싱을 간단히 살펴보겠다. 그리고 Kafka 클라이언트와 브로커 사이의 인증과 암호화도 살펴보겠다.

### Java NIO

네트워크 통신을 다루는 가장 간단한 방법은 다음 그림과 같이 모든 연결마다 전담하는 스레드(I/O Thread)를 생성하는 것이다.

![그림 6 I/O 스레드 생성을 통한 네트워크 통신 방법](https://d2.naver.com/content/images/2022/01/KafkaClientInternalsNetworkClient-06.png)

그림 6 I/O 스레드 생성을 통한 네트워크 통신 방법

통신할 서버와 연결이 생성될 때 그 서버와 통신할 전담 스레드를 생성한다. 특정 서버로 전송할 요청이 생기면 전담 스레드를 통해서 요청을 전송하고, 서버에서 오는 데이터 역시 전담 스레드가 읽는다. 이 방법은 가장 직관적이면서 간단한 방법이다.

하지만 Kafka 클라이언트가 구동되는 도중 대부분의 스레드는 통신을 하지 않고 대기 상태에 있을 것이다. 대부분의 스레드가 동작하지 않고 대기 상태에 머물러 있기 때문에 상당한 리소스 낭비가 발생한다. 연결할 서버의 개수가 많을수록, 그리고 주고받는 데이터의 양이 적을수록 대기 상태에서 보내는 시간이 길어지기 때문에 리소스 낭비는 더 심해진다. 게다가 전담 스레드가 많아질수록 공유 자원에 대한 동기화 이슈로 오히려 코드가 복잡해지거나 의외의 부분에서 병목 현상이 발생할 가능성도 높아진다.

Kafka 클라이언트의 NetworkClient는 이러한 전담 스레드 모델 대신 Java NIO를 사용한 비동기 통신 모델로 구현되었다.

Java NIO는 다음 그림과 같이 하나의 스레드가 Selector라는 컴포넌트를 두고 여러 SocketChannel을 관리할 수 있게 한다. 스레드는 Selector를 사용해서 Selector에 등록된 SocketChannel들 중 하나라도 읽거나 쓰는 등 뭔가를 할 수 있는 상황이 되면 바로 알 수 있다. 이런 방식을 SocketChannel의 '멀티플렉싱'이라고 한다.

![그림 7 Java NIO Selector 생성을 통한 비동기 네트워크 통신 방법](https://d2.naver.com/content/images/2022/01/KafkaClientInternalsNetworkClient-07.png)

그림 7 Java NIO Selector를 통한 비동기 네트워크 통신 방법

Java NIO를 사용해 여러 SocketChannel을 멀티플렉싱 방식으로 관리하려면 먼저 Selector를 생성해야 한다. Selector는 다음 예와 같이 정적 메서드인 open() 메서드를 사용해서 만들 수 있다.

예제 2 Java NIO Selector 생성

```java
Selector selector = Selector.open();
```

그리고 Kafka 클라이언트가 메타데이터를 통해 알고 있는 브로커 노드 정보를 사용해 SocketChannel을 생성한다.

예제 3 Java NIO SocketChannel 생성

```java
SocketChannel socketChannel = SocketChannel.open();
socketChannel.configureBlocking(false);
socketChannel.connect(new InetSocketAddress(node.host(), node.port());
```

예제 3에서 주의해야 할 부분은 `socketChannel.configureBlocking(false)` 이다. Selector를 사용한 멀티플렉싱을 위해 생성되는 SocketChannel은 반드시 논블로킹 모드로 설정해야 한다.

그런 다음 SocketChannel을 Selector에 등록한다. 다음과 같이 SocketChannel의 register() 메서드를 사용해 SocketChannel을 등록할 수 있다.

예제 4 Selector에 SocketChannel 등록

```java
// Selector에 SocketChannel 등록
SelectionKey selectionKey = channel.register(selector, SelectionKey.OP_CONNECT | SelectionKey.OP_READ);
```

register() 메서드의 첫 번째 파라미터는 등록할 Selector이고, 두 번째 파라미터는 interestSet이다. interestSet은 interest operation의 집합으로, 이 SocketChannel에서 어떤 연산을 수행하고 싶은지 Selector에 알려주는 역할을 한다. 즉, Selector에 '이 SocketChannel에 이런 연산들이 가능해지면 알려줘'라고 말하는 것이다.

SocketChannel을 Selector에 등록하면 SelectionKey 객체를 얻게 된다. SelectionKey 객체를 사용해서 Selector 객체와 SocketChannel 객체를 얻어올 수 있고, 다음 예처럼 SelectionKey 객체를 사용해 등록했던 interestSet을 바꿀 수도 있다.

예제 5 특정 채널의 interestSet 변경

```java
selectionKey.interestOps(SelectionKey.OP_READ | SelectionKey.OP_WRITE);
```

Selector에 설정할 수 있는 interest operation은 다음과 같다. Bitwise OR 연산(`|`)으로 하나의 채널에 대해서 두 개 이상의 interest operation을 설정하는 것도 가능하다.

- OP\_READ
- OP\_WRITE
- OP\_CONNECT
- OP\_ACCEPT

NetworkClient는 브로커로의 새로운 연결이 필요할 때 SocketChannel을 생성하고 내부 Selector에 등록한다. 그리고 필요에 따라 OP *CONNECT, OP* READ, OP\_WRITE를 설정한다. 필요한 SocketChannel의 등록이 끝났으면 Selector를 사용해서 등록된 SocketChannel 중 필요한 연산을 수행할 수 있는 것이 나타날 때까지 기다린다.

다음 예처럼 select() 메서드를 호출하면 Selector에 등록된 SocketChannel이 각각의 interestSet을 수행할 준비가 될 때까지 select() 메서드의 내부에서 기다린다. 이후 연산할 준비가 된 SocketChannel이 생기거나 타임아웃 시간이 지나면 select() 메서드가 깨어난다. 이때 사용되는 타임아웃 시간은 Kafka 클라이언트의 내부 로직에 따라 매우 다양하게 결정되며 꼭 필요한 만큼만 기다린다.

예제 6 select() 메서드를 통해 이벤트가 발생할 때까지 대기

```java
selector.select(timeout);
```

select() 메서드가 깨어난 이후 Selector의 selectedKeys() 메서드를 호출하면 준비된 SocketChannel의 SelectionKey를 가져올 수 있다. 보통 다음 예와 같은 형태의 코드가 사용된다.

예제 7 이벤트가 발생한 채널을 순회하며 처리

```java
// 등록한 브로커 중 필요한 연산을 할 수 있는 SocketChannel의 SelectionKey
Set<SelectionKey> selectedKeys = selector.selectedKeys();

// SelectedKeys 순회
Iterator<SelectionKey> iterator = selectedKeys.iterator();
while(iterator.hasNext()) {

    SelectionKey key = iterator.next();
    iterator.remove();

    if (key.isReadable()) {
        // ... 실행 코드
    }

    if (key.isWritable()) {
        // ... 실행 코드
    }
    ...
}
```

selectedKeys() 메서드를 통해 가져온 SelectionKey들은 뭔가 연산을 할 준비가 된 SocketChannel에 대한 것들이며, 이들을 순회하면서 SocketChannel에 Send 혹은 Receive 같은 연산을 수행하면 된다.

KafkaProducer와 KafkaConsumer에서 브로커와 통신을 담당하는 스레드는 반복적으로 NetworkClient의 poll() 메서드를 호출한다. poll() 메서드의 내부에서는 Selector의 select() 메서드가 실행되며, 이를 통해서 브로커들과의 통신이 멀티플렉싱 방식으로 처리된다.

### KafkaChannel과 인증, 암호화

Kafka는 Kafka 클라이언트와 브로커 사이에 생성된 SocketChannel을 기반으로 인증과 암호화 기능을 추가하기 위해 KafkaChannel 클래스를 구현한다.

예제 8 KafkaChannel 클래스의 주요 멤버

```java
public class KafkaChannel {

    // 브로커 ID
    private final String id;

    // SocketChannel과 SelectionKey를 사용한 전송 동작
    private final TransportLayer transportLayer;

    // Kafka 클라이언트 인증 과정
    private final Authenticator authenticator;

    // 브로커에서 받은 데이터
    private final int maxReceiveSize;
    private NetworkReceive receive;

    // 브로커로 전송할 데이터
    private Send send;
    ...
}
```

예제 8에 있는 KafkaChannel의 주요 멤버 중 Authenticator와 TransportLayer는 각각 Kafka 클라이언트를 인증하기 위한 동작과 브로커와의 통신 암호화를 위해 사용된다. 만약 인증을 사용한다면 다음 그림처럼 Authenticator가 TransportLayer를 통해서 브로커와 인증 정보를 주고받으며 Kafka 클라이언트에 대한 인증을 진행한다.

![그림 8 KafkaChannel의 Authenticator를 사용한 Kafka 클라이언트 인증](https://d2.naver.com/content/images/2022/01/KafkaClientInternalsNetworkClient-08.png)

그림 8 KafkaChannel의 Authenticator를 사용한 Kafka 클라이언트 인증

인증이 끝나면 다음 그림과 같이 TransportLayer를 통해 브로커와 통신하면서 Send에 있는 데이터를 전송하거나 브로커로부터 데이터를 받아서 NetworkReceive에 담아 둔다.

![그림 9 KafkaChannel의 TransportLayer를 통한 브로커 통신](https://d2.naver.com/content/images/2022/01/KafkaClientInternalsNetworkClient-09.png)

그림 9 KafkaChannel의 TransportLayer를 통한 브로커 통신

Send는 NetworkClient 밖에서 브로커로 전송할 목적으로 생성한 ClientRequest를 직렬화(serialize)한 바이트 버퍼(byte buffer)라고 생각하면 된다. 반대로 NetworkReceive는 브로커에서 전송된 데이터를 조금씩 받아서 저장해 두는 곳으로, 데이터 수신이 끝나면 ClientResponse를 만들어 반환한다.

앞서 Selector에 등록된 SocketChannel은 KafkaChannel의 TransportLayer 객체로 래핑된다.

KafkaChannel은 브로커와의 연결이 맺어지는 과정에서 ChannelBuilder에 의해 생성된다. ChannelBuilder는 `security.protocol` 설정값에 따라 정해지며, 생성되는 KafkaChannel의 Authenticator와 TransportLayer의 구현체를 결정한다.

`security.protocol` 에 설정할 수 있는 값에는 다음과 같은 4가지가 있다.

|  | 인증 미사용 | 인증 사용 |
| --- | --- | --- |
| 암호화 미사용 | PLAINTEXT | SASL\_PLAINTEXT |
| 암호화 사용 | SSL | SASL\_SSL |

`SASL_PLAINTEXT` 와 `SASL_SSL` 처럼 접두어 'SASL\_'로 시작하는 설정을 사용하면 Kafka 클라이언트 연결에 인증을 사용하겠다는 의미이다. 인증을 사용하면 브로커와의 연결에 사용되는 KafkaChannel 객체의 Authenticator로 SaslClientAuthenticator가 사용된다. 이 SaslClientAuthenticator의 동작을 설정하기 위해서 'sasl.\*' 형태의 설정값을 사용한다.

예를 들어 다음과 같이 설정할 수 있다.

```java
bootstrap.servers=kafkahost:9093
security.protocol=SASL_PLAINTEXT
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required \
   username="user1" \
   password="user1passwd";
```

'SASL\_' 같은 접두어가 없는 설정값인 `PLAINTEXT` 나 `SSL` 을 사용하면 KafkaChanel 객체의 Authenticator로 DefaultAuthenticator가 사용되며, Kafka 클라이언트가 브로커로 연결할 때 인증 동작을 수행하지 않는다.

설정 이름에 'SSL'이 있는 `SSL` 이나 `SASL_SSL` 을 사용하면 브로커와의 통신을 암호화한다. 이 경우 SocketChannel을 사용해 통신을 수행하는 TransportLayer로 SslTransportLayer가 사용된다. 이 SslTransportLayer의 동작을 설정하기 위해서 'ssl.\*' 형태의 설정값을 사용한다.

예를 들어 다음과 같이 설정할 수 있다.

```java
bootstrap.servers=kafkahost:9093
security.protocol=SSL
ssl.truststore.location=/var/private/ssl/kafka.client.truststore.jks
ssl.truststore.password=test1234
ssl.keystore.location=/var/private/ssl/kafka.client.keystore.jks
ssl.keystore.password=test1234
ssl.key.password=test1234
```

이름에 SSL이 없는 `PLAINTEXT` 나 `SASL_PAINTEXT` 을 사용하면 TransportLayer로 PlaintextTransportLayer가 사용되며, 단순히 SocketChannel로 데이터를 전송하기만 한다.

SASL을 통한 Kafka 클라이언트의 인증 동작이나 SSL을 사용한 통신 암호화를 적용하기 위해서는 브로커의 설정 변경이 필요할 수 있다. SASL 설정과 SSL 설정에 관한 내용은 이 글에 담기에는 너무 길기 때문에 설명을 생략하겠다. 대신 SASL 설정에 관해서는 Confluent의 [Authentication with SASL](https://docs.confluent.io/platform/current/kafka/authentication_sasl/auth-sasl-overview.html) 문서를 참고하고, SSL 설정에 관해서는 [Encryption and Authentication with SSL](https://docs.confluent.io/platform/current/kafka/authentication_ssl.html) 문서를 참고한다.

## Metadata

지금까지 NetworkClient가 특정 브로커와 통신하는 방법에 대해서 알아봤다. 여기까지의 내용은 Kafka 클라이언트가 접속할 브로커의 주소 정보를 알고 있다는 가정이 있었다. 하지만 Kafka 클라이언트의 사용자는 메시지를 전송하거나 읽기 위해 어떤 브로커에 접속해야 하는지 모른다. 데이터의 접근 포인트로 클러스터에 있는 '토픽' 이름만 알고 있을 뿐이다.

KafkaProducer API를 사용하는 다음 예를 보자. KafkaProducer 사용자는 어떤 토픽으로 Key, Value 데이터를 전송할 것인지 ProducerRecord 객체를 만들어 넘겨준다. 사용자 입장에서는 이 데이터가 어떤 브로커 노드로 전송되어야 하는지 모른다.

예제 9 KafkaProducer 예제

```java
Properties properties = new Properties();
properties.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka01:9092");
properties.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
properties.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());

KafkaProducer<byte[], byte[]> producer = new KafkaProducer<>(properties);

String key = "My Key";
String value = "My Value";

ProducerRecord<byte[], byte[]> record = new ProducerRecord<>("MyTopic", key.getBytes(), value.getBytes());
producer.send(record, null);

producer.close();
```

사용자로부터 ProducerRecord 객체를 넘겨받은 KafkaProducer는 내부적으로 다음 그림과 같은 순서로 브로커 주소를 알게 된다.

![그림 10 사용자의 데이터가 해석되어 브로커 노드를 찾는 순서](https://d2.naver.com/content/images/2022/01/KafkaClientInternalsNetworkClient-10.png)

그림 10 사용자의 데이터가 해석되어 브로커 노드를 찾게 되는 순서

ProducerRecord를 전달받은 KafkaProducer는 Partitioner를 사용해 토픽의 몇 번 파티션으로 데이터를 전송해야 하는지 결정한다. 하지만 여전히 그 파티션이 어떤 브로커 노드에 있는지는 모른다. Kafka 클라이언트는 토픽의 파티션이 어떤 브로커에서 서비스되고 있는지 Metadata 클래스를 통해 알게 된다.

Metadata에는 Kafka 클라이언트가 알아야 할 Kafka 클러스터의 메타데이터와 그 메타데이터를 갱신하기 위한 동작이 정의되어 있다.

Metadata에서 관리되는 첫 번째 메타데이터는 클러스터를 구성하고 있는 브로커 노드의 접속 정보이다.

클러스터를 구성하는 브로커 노드는 브로커 ID로 구별할 수 있다. 다음 예와 같이 Kafka 클라이언트가 특정 브로커 노드에 접속하기 위해 Metadata에서 얻어온 Node 객체에는 SocketChannel을 생성하기 위한 주소 정보가 담겨 있다.

예제 10 브로커 노드 정보를 저장하는 Node 객체

```java
public class Node {
    private final int id;
    private final String idString;
    private final String host;
    private final int port;
    private final String rack;
  ...
}
```

두 번째로, Kafka 클라이언트가 사용하는 토픽에 대한 정보가 관리된다.

Kafka 클라이언트가 사용하는 토픽이 몇 개의 파티션으로 구성되어 있는지, 파티션의 복제본(replica)이 어떤 브로커에서 서비스되는지, 그중 Leader는 어디에 있는지, In-Sync 상태인 복제본은 어떤 브로커에 있는지 등이 관리된다. Metadata 내부에서는 다음과 같은 PartitionInfo 객체에 파티션에 대한 정보가 담겨있다.

예제 11 파티션 정보를 저장하는 PartitionInfo 객체

```java
public class PartitionInfo {
  private final String topic;
  private final int partition;
  private final Node leader;
  private final Node[] replicas;
  private final Node[] inSyncReplicas;
...
}
```

### MetadataUpdater

Kafka 클라이언트가 Metadata로 관리하는 메타데이터는 클러스터가 운영되는 도중에 얼마든지 바뀔 수 있다. 예를 들어 새로운 토픽이 만들어지거나 파티션 개수가 추가될 수 있다. 성능을 위해서 신규 브로커 장비가 클러스터에 추가되는 경우도 있고, 장비 장애로 클러스터에서 브로커가 제외되는 경우, 노후 장비 교체로 브로커의 장비가 교체되는 경우도 얼마든지 있을 수 있다.

일반적으로 Kafka 클라이언트는 다음의 경우에 메타데이터 갱신이 필요하다.

1. 특정 브로커 노드로 연결하다가 실패한 경우
2. 특정 브로커 노드에 요청을 보냈는데 타임아웃이 발생한 경우
3. 새로운 토픽에 데이터를 전송하거나 새로운 토픽을 구독하는 경우
4. 컨슈머 코디네이터 객체가 생성되는 경우
5. Fetcher에서 데이터를 가져오려는데 Leader의 정보를 알 수 없을 경우
6. 데이터 요청을 보냈는데 Unknown Partition이라는 오류가 응답으로 오거나 Leader가 아니라는 오류가 응답으로 왔을 때
7. 그 밖에 메타데이터가 Stale 상태일 경우 만나게 되는 각종 Exception이 발생할 때

Kafka 클라이언트가 동작하다가 자기가 알고 있는 메타데이터와 조금 다르거나 이상함을 감지하면 바로 메타데이터 갱신이 필요하다고 인지하게 된다. 매끄러운 동작을 위해서는 Kafka 클라이언트가 메타데이터의 변경을 감지했을 때 재 구동 없이 최신 메타데이터로 갱신할 수 있어야 한다. Kafka 클라이언트의 NetworkClient는 Metadata를 갱신하기 위해 MetadataUpdater라는 클래스를 사용한다.

다음 그림과 같이 MetadataUpdater는 MetadataRequest라는 요청을 생성해서 브로커로 전송한다. MetadataRequest를 전송할 브로커 노드는 현재 InFlightRequest 항목이 제일 적은 노드들 중에 임의로 선택한 노드이다. 요청을 받은 브로커 노드가 메타데이터를 정리해서 MetadataResponse에 담아 반환하면 반환받은 정보를 바탕으로 Metadata의 정보를 갱신한다.

![그림 11 MetadataUpdater의 Metadata 갱신](https://d2.naver.com/content/images/2022/01/KafkaClientInternalsNetworkClient-11.png)

그림 11 MetadataUpdater의 Metadata 갱신

Kafka 클라이언트 인스턴스가 최초로 생성되었을 때에는 Metadata를 요청할 브로커 주소 정보조차 가지고 있지 않다. 따라서 Kafka 클라이언트가 최초로 구동될 때 Metadata를 얻어올 수 있도록 `bootstrap.servers` 설정에 Kafka 클라이언트의 브로커 중 일부의 주소를 입력해야 한다.

Kafka 클라이언트가 최초로 구동되거나 없는 토픽을 막 만들어내기 시작하면 메타데이터에 대한 갱신 요청(MetadataRequest)이 너무 빈번하게 브로커로 전송될 수 있다. 따라서 메타데이터 갱신 요청이 너무 빈번하게 브로커로 전송되지 않도록 백오프 시간을 설정할 수 있다. Metadata에는 마지막으로 정보가 갱신된 시간이 기록되어 있고, `retry.backoff.ms` 설정을 사용하면 마지막 갱신 시간으로부터 `retry.backoff.ms` 설정값만큼 시간이 지날 때까지 새로운 MetadataRequest를 전송하지 않고 기다린다. `retry.backoff.ms` 설정의 기본값은 '100'이다.

반대로 메타데이터에 대한 변경이 오랜 시간 동안 감지되지 않더라도 일정 시간이 지나면 갱신 요청을 브로커로 전송한다. 당장은 필요하지 않더라도 Kafka 클러스터에 추가된 브로커나 파티션에 대한 정보를 미리 알아오면 나중에 MetadataRequest를 전송하고 기다리지 않아도 되기 때문이다. MetadataUpdater는 마지막 메타데이터 갱신이 성공한 이후 `metadata.max.age.ms` 에 설정한 시간이 지나면 다시 갱신 요청을 전송한다. `metadata.max.age.ms` 설정의 기본 값은 '300000'으로, 5분이다.

MetadataUpdater가 생성하는 MetadataRequest에는 Kafka 클라이언트가 관심 있어 하는 토픽의 리스트가 담겨 있다. 다시 돌아오는 응답에는 Kafka에 있는 Kafka 클라이언트가 관심 있다고 보낸 토픽의 정보만 담겨 있다. 만약 오랜 기간 동안 사용되지 않은 토픽이 있다면 MetadataRequest에 쓸데없는 정보가 포함되어 브로커도 느려지고 주고받는 요청의 크기도 커진다. KafkaProducer는 일정 기간 동안 사용되지 않은 토픽의 정보는 메타데이터에서 제외한다. 제외된 토픽은 앞으로 전송되는 메타데이터 갱신 요청에 포함되지 않는다. 이 기간은 설정할 수 있는 값이 아니며, 5분이라는 고정값으로 설정되어 있다.

## 마치며

지금까지 Kafka 클라이언트에서 네트워크 통신을 위해 사용한 NetworkClient의 내부 구조와 설정값에 관해 알아보았다.

Kafka 클라이언트는 클러스터를 구성하고 있는 수많은 브로커와의 통신을 Java NIO를 통해서 구현했다. 사실 가장 궁금했던 것은 '왜 Java NIO를 사용해서 직접 구현했는가'였다. [Apache Storm](https://storm.apache.org/) 의 경우에는 Worker들의 네트워크 통신을 [Netty](https://netty.io/) 라는 네트워크 프레임워크를 통해서 구현했다. Kafka의 공식 입장은 아니지만 Kafka 커미터의 [Quora 답변](https://www.quora.com/Why-did-Kafka-developers-prefer-to-implement-their-own-socket-server-instead-of-using-Netty-Does-that-help-with-performance-Does-Kafka-implement-such-features-already) 을 통해 어느 정도 이유를 알 수 있었다. 우선 가장 최적의 성능을 구현할 수 있기 때문이다. 그리고 '의존성 지옥(dependency hell)'을 최대한 피하기 위함이라고 한다. 특히 다양한 환경에서 실행되는 Kafka 클라이언트에서는 의존성이 충돌하는 상황이 얼마든지 발생할 수 있기 때문에 되도록 의존성이 추가되는 것을 피하려고 노력한다는 것이다.

실제로 Kafka 클라이언트의 코드를 보면 굉장히 많은 부분이 라이브러리를 사용하지 않고 직접 구현되어 있다. Kafka처럼 의존성이 문제가 될 가능성이 있는 클라이언트 라이브러리를 개발하는 경우라면 Kafka 클라이언트의 코드를 참고하는 것이 많은 도움이 될 것이다.

Tag

![](https://d2.naver.com/image/20220127/638655852651.jpeg)

글쓴이

안인석|네이버 Platform

소개

네이버에서 대용량 데이터 저장소 운영 및 개발을 담당하고 있습니다.

관련글

- [![썸네일](https://d2.naver.com/content/images/2016/04/---.png)
	대용량 스트리밍 데이터 실시간 분석
	](https://d2.naver.com/helloworld/7731491)
- [![썸네일](https://d2.naver.com/content/images/2015/07/1044388.PNG)
	Storm과 Elasticsearch Percolator를 이용한 NELO2 알람 기능 개선
	](https://d2.naver.com/helloworld/1044388)
- [![썸네일](https://d2.naver.com/content/images/2025/12/-----------2025-12-17------5-26-31.png)
	비용, 성능, 안정성을 목표로 한 지능형 로그 파이프라인 도입
	](https://d2.naver.com/helloworld/0004394)
- [![썸네일](https://d2.naver.com/content/images/2020/08/hwhw_200813.png)
	KafkaProducer Client Internals
	](https://d2.naver.com/helloworld/6560422)

##### 댓글

3

- 이동승
	좋은 글 잘 보았습니다.
	2023-12-11 09:46
	[**답글** 0](#)
	**공감/비공감** [공감 *0*](#) [비공감 *0*](#)
- geog\*\*\*\*
	기존 producer 와 consumer가 blockingRequest나 대기열이나 bloking io로 인해 많은 대안들이 나왔었는데요 java 1.6부터 nonblocking이 제공됐고 이후 nio패키지가 나왔는데, 당시 java.sun에서 제공된 코드체계가 현재에 이르러 아파치에서 카프카라는 형태로 대부분 차용한 형태를 보이는 걸 볼 수 있는데, workThead같은 역활로 분산처리방법을 좀더 효과적으로 아파치로 들여오면서 보완한 것으로 이해되내요. 글 잘 봤습니다..
	2022-02-14 17:35
	[**답글** 0](#)
	**공감/비공감** [공감 *0*](#) [비공감 *0*](#)
- 팽팽
	좋은 글 잘 보았습니다.
	2022-02-04 09:55
	[**답글** 0](#)
	**공감/비공감** [공감 *0*](#) [비공감 *1*](#)
