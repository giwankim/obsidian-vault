---
title: "Spring의 ConcurrentWebSocketSessionDecorator 소개"
source: "https://prostars.net/362"
author:
  - "[[prostars]]"
published: 2025-04-28
created: 2026-07-19
description: "스프링 부트에서 단순히 웹소켓을 사용하는 건 어렵지 않다. 스프링 부트 3.4.3 기준으로 기본 설정된 서블릿 컨테이너는 임베디드 톰캣이고, 모든 TCP 처리는 서블릿 컨테이너에서 처리한다. 이 글에서는 스프링 부트에서 웹소켓을 사용할 때 멀티스레드가 하나의 세션에 동시에 메시지를 전송할 때 발생하는 문제를 확인하고 대응하는 한 가지 방법을 소개한다. 여기서 사용하는 예제는 나의 온라인 강의의 파트 2-챕터 2 'Rest API와 WebSocket의 기본’ 중에서 '08. 채팅 프로젝트를 그룹 메시지로 확장하기’에 있는 코드에서 웹소켓에 대한 처리와 테스트 코드를 가져왔다.이 예제는 Java 17에 Spring Boot 3.4를 사용하고, 통합 테스트 구성은 Groovy 4.0에 Spock 2.4를 사.."
tags:
  - "clippings"
---

> [!summary]
> Korean article demonstrating what goes wrong when multiple threads send messages over a single Spring WebSocket session concurrently on embedded Tomcat, using a group-chat style `TextWebSocketHandler` example (Spring Boot 3.4, Java 17, Spock integration tests). The recommended fix is wrapping each session in Spring's `ConcurrentWebSocketSessionDecorator`, which serializes concurrent sends and bounds send time and buffer size per session.

스프링 부트에서 단순히 웹소켓을 사용하는 건 어렵지 않다. 스프링 부트 3.4.3 기준으로 기본 설정된 서블릿 컨테이너는 임베디드 톰캣이고, 모든 TCP 처리는 서블릿 컨테이너에서 처리한다.

이 글에서는 스프링 부트에서 웹소켓을 사용할 때 멀티스레드가 하나의 세션에 동시에 메시지를 전송할 때 발생하는 문제를 확인하고 대응하는 한 가지 방법을 소개한다.

여기서 사용하는 예제는 [나의 온라인 강의](https://fastcampus.co.kr/dev_online_chat) 의 파트 2-챕터 2 'Rest API와 WebSocket의 기본’ 중에서 '08. 채팅 프로젝트를 그룹 메시지로 확장하기’에 있는 코드에서 웹소켓에 대한 처리와 테스트 코드를 가져왔다.

이 예제는 Java 17에 Spring Boot 3.4를 사용하고, 통합 테스트 구성은 Groovy 4.0에 Spock 2.4를 사용한다.

전체 코드는 [GitHub](https://github.com/prostars/websocket-multi-thread-example) 에 올라가 있다. Postman을 웹소켓 클라이언트로 사용한다.

Gradle 설정은 아래와 같다.

```java
plugins {
    id 'java'
    id 'groovy'
    id 'org.springframework.boot' version '3.4.3'
    id 'io.spring.dependency-management' version '1.1.7'
}

group = 'net.prostars'
version = '0.0.1-SNAPSHOT'

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(17)
    }
}

repositories {
    mavenCentral()
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-websocket'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.spockframework:spock-core:2.4-M5-groovy-4.0'
    testImplementation 'org.spockframework:spock-spring:2.4-M5-groovy-4.0'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

build.gradle

스프링 부트를 사용하므로 main 구성은 간단하게 아래와 같이 한다.

```java
@SpringBootApplication
public class WebsocketMultiThreadExample {

  public static void main(String[] args) {
    SpringApplication.run(WebsocketMultiThreadExample.class, args);
  }
}
```

WebsocketMultiThreadExample.java

간단한 그룹 채팅과 비슷한 동작을 구현하기 위해서 웹소켓을 텍스트 베이스로 사용한다. TextWebSocketHandler를 상속받아서 빈을 하나 만든다. 서버에 접속한 모든 웹소켓 세션은 ConcurrentHashMap을 사용해서 관리한다.

이 핸들러의 동작은 서버가 클라이언트에게 메시지를 받으면 이 메시지를 전송한 클라이언트를 제외한 나머지 모든 클라이언트에게 이 메시지를 전송한다.

핸들러의 전체 코드는 아래와 같다.

```java
@Component
public class MessageHandler extends TextWebSocketHandler {

  private static final Logger log = LoggerFactory.getLogger(MessageHandler.class);
  protected final Map<String, WebSocketSession> sessions = new ConcurrentHashMap<>();

  @Override
  public void afterConnectionEstablished(WebSocketSession session) {
    sessions.put(session.getId(), session);
  }

  @Override
  public void afterConnectionClosed(WebSocketSession session, CloseStatus status)
      throws IOException {
    WebSocketSession webSocketSession = sessions.remove(session.getId());
    if (webSocketSession != null) {
      webSocketSession.close();
    }
  }

  @Override
  protected void handleTextMessage(WebSocketSession senderSession, TextMessage message) {
    try {
      for (WebSocketSession session : sessions.values()) {
        if (!senderSession.getId().equals(session.getId())) {
          session.sendMessage(new TextMessage(message.getPayload()));
          log.info("Send {} to {}", message.getPayload(), session.getId());
        }
      }
    } catch (Exception ex) {
      log.error("Failed to send from {} error: {}", senderSession.getId(), ex.getMessage());
    }
  }
}
```

handler/MessageHandler.java

핸들러를 하나 준비했으므로, 아래와 같이 웹소켓 엔드포인트에 연결해야 한다.

여기서는 엔드포인트를 '/ws/v1/message' 로 설정했다.

```java
@Configuration
@EnableWebSocket
public class WebSocketHandlerConfig implements WebSocketConfigurer {

  private final MessageHandler messageHandler;

  public WebSocketHandlerConfig(MessageHandler messageHandler) {
    this.messageHandler = messageHandler;
  }

  @Override
  public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
    registry.addHandler(messageHandler, "/ws/v1/message");
  }
}
```

config/WebSocketHandlerConfig.java

일단 필요한 구성을 다 했으니, 서버를 실행할 수 있다. 서버를 실행하면 기본 포트인 8080 포트로 임베디드 톰캣이 실행된다.
Postman을 웹소켓 클라이언트로 사용한다.

아래와 같이 'ws://localhost:8080/ws/v1/message'로 접속해서 텍스트 메시지를 보내고 받을 수 있다.
여기서는 4개의 Postman을 열어서 모두 서버에 접속한 상태에서 '좌상단, 우상단, 좌하단, 우하단' 순서로 메시지를 보냈다.
'좌상단’이 메시지를 보내면 나머지 3개의 클라이언트가 메시지를 받는다.

![](https://blog.kakaocdn.net/dna/mjVWJ/btsNCmN3IlY/AAAAAAAAAAAAAAAAAAAAACzGJ_nthD_tasojBClKIeuuipe43XXRDEZY15ErEflC/img.jpg?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=Mb%2Bf%2FvdvDP1o26lE5iW4n7ookjw%3D)

혼자서 4개의 클라이언트를 왔다 갔다 하며 메시지를 보내보면 잘 동작한다. 이 속도로는 멀티스레드 문제가 발생하지 않는다.

멀티스레드 문제가 발생하려면 최소한 2개의 스레드에서 거의 동시에 하나의 웹소켓 세션에 메시지 전송을 시도 해야 한다.

이런 상황이 발생하면 어떤 문제가 있는지 확인하기 위해서 통합 테스트가 필요하다. 테스트에 사용할 웹소켓 클라이언트는 서버에게 받은 메시지를 블로킹 큐에 저장하고, 테스트 코드에서 꺼내서 정상 수신 여부를 확인할 때 사용한다.

이 테스트는 3개의 클라이언트를 준비하고, 3개의 클라이언트가 각각 메시지를 연속으로 보낸다. 정상 동작은 1개의 클라이언트가 보낸 메시지를 다른 2개의 클라이언트가 받아야 한다.

클라이언트가 메시지를 받지 못하면 블로킹 큐에서 꺼낼 때 지정한 타임아웃 시간을 초과하고 null을 받는다. 모든 클라이언트가 받은 메시지를 result에 모아서 null이 포함되어 있는지 확인한다. null이 포함되었다는 건 메시지를 받지 못한 클라이언트가 있다는 것이다. 이 조건을 테스트 통과 조건으로 설정한다.

이렇게 설정하는 이유는 어떤 클라이언트가 어떤 메시지를 못 받을지는 알 수 없고, 모든 클라이언트가 메시지를 받는 정상 동작은 지금 구현에서는 테스트를 실행하는 장비의 성능이 매우 좋아야 한다. 만약, 현재 구현에서 모든 클라이언트가 메시지를 받아서 이 테스트가 실패한다면, 테스트에 참여하는 클라이언트를 몇 개 더 추가해 보자.

```java
@SpringBootTest(
        classes = WebsocketMultiThreadExample,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class SendMessageMultiThreadSpec extends Specification {

    @LocalServerPort
    int port

    def clientA, clientB, clientC

    def cleanup() {
        clientA.session?.close()
        clientB.session?.close()
        clientC.session?.close()
    }

    def 'Group Chat Basic Test'() {
        given:
        def url = "ws://localhost:${port}/ws/v1/message"
        (clientA, clientB, clientC) = [createClint(url), createClint(url), createClint(url)]

        when:
        clientA.session.sendMessage(new TextMessage('clientA: 안녕하세요. A 입니다.'))
        clientB.session.sendMessage(new TextMessage('clientB: 안녕하세요. B 입니다.'))
        clientC.session.sendMessage(new TextMessage('clientC: 안녕하세요. C 입니다.'))

        then:
        def result = (0..1).collect { clientA.queue.poll(1, TimeUnit.SECONDS) }
        result << (0..1).collect { clientB.queue.poll(1, TimeUnit.SECONDS) }
        result << (0..1).collect { clientC.queue.poll(1, TimeUnit.SECONDS) }

        and:
        result.contains(null)
    }

    static def createClint(String url) {
        BlockingQueue<String> blockingQueue = new ArrayBlockingQueue<>(5)
        def client = new StandardWebSocketClient()
        def webSocketSession = client.execute(new TextWebSocketHandler() {
            @Override
            protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
                blockingQueue.put(message.payload)
            }
        }, url).get()

        [queue: blockingQueue, session: webSocketSession]
    }
}
```

SendMessageMultiThreadSpec.groovy

위의 테스트를 실행하면 서버 입장에서는 메시지 3개가 거의 동시에 들어오는 것으로 처리되고, 3개의 스레드에서 각각 전송자를 제외한 현재 연결된 모든 세션으로 메시지 전송하려고 시도한다.

예를 들어 아래와 같이 clientA는 clientB와 clientC에게 보내고 clientB는 clientA와 clientC에게 보내려고 시도한다.

![](https://blog.kakaocdn.net/dna/cig8GU/btsNBLOlfwN/AAAAAAAAAAAAAAAAAAAAAASIcD6_m1YPPMD1fpPtC1ypQVu9frt3UHFLr-oz4cJt/img.jpg?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=z0Ir2AjKoQc8YDcZ0xiAe%2BwPMzc%3D)

이때, clientA의 스레드와 clientB의 스레드에서 clientC의 웹소켓 세션에 거의 동시에 메시지를 전송하려고 sendMessage()를 호출하는 상황이 발생한다.

이 상황이 발생하면, 아래와 같이 테스트 실행 중 서버 로그에서 'The remote endpoint was in state \[TEXT\_PARTIAL\_WRITING\] which is an invalid state for called method' 라는 에러 메시지를 확인할 수 있다.

![](https://blog.kakaocdn.net/dna/cYcqT6/btsNCpD20bc/AAAAAAAAAAAAAAAAAAAAAJVIWhLYLZiMpZxSilUqLSgFImGGXcqcpTH4m_0wyrrw/img.jpg?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=Q2SiyQG%2BwTOdTEKjPmYovxHYqh8%3D)

이 에러가 발생하는 이유는 Spring WebSocketSession 인터페이스에 있는 sendMessage() 메서드의 주석을 확인해 보면 알 수 있다.

> Note: The underlying standard WebSocket session (JSR-356) does not allow concurrent sending. Therefore, sending must be synchronized. To ensure that, one option is to wrap the WebSocketSession with the ConcurrentWebSocketSessionDecorator.

sendMessage()는 스레드 세이프하지 않다. 멀티스레드에서 하나의 웹소켓 세션에 sendMessage()로 메시지를 보내는 것은 허용되지 않는다고 명시되어 있다. 그리고, ConcurrentWebSocketSessionDecorator를 사용하는 방법이 있다고 안내한다.

이제 ConcurrentWebSocketSessionDecorator를 사용하면 스레드 세이프한지 확인해 보자.

ConcurrentWebSocketSessionDecorator()는 간단히 적용할 수 있다. 파라미터로 WebSocketSession과 전송 타임아웃과 전송 버퍼 크기만 설정해 주면 된다.

여기서는 타임아웃 5초, 전송 버퍼 제한은 100kb로 설정했다. 버퍼 제한을 초과했을 때의 처리는 예외를 던질지 가장 오래된 메시지를 버퍼에서 버릴지 동작을 선택할 수 있고, 설정을 생략하면 예외를 발생시키는 OverflowStrategy.TERMINATE 가 기본값으로 설정된다.

타임아웃에 대한 동작을 설정하는 기능은 없고 타임아웃이 발생하면 예외를 던진다.

아래와 같이 MessageHandler를 상속받아서 ConcurrentMessageHandler 빈을 하나 만든다.

```java
@Component
public class ConcurrentMessageHandler extends MessageHandler {

  private static final Logger log = LoggerFactory.getLogger(ConcurrentMessageHandler.class);

  @Override
  public void afterConnectionEstablished(WebSocketSession session) {
    log.info("ConnectionEstablished: {}", session.getId());
    sessions.put(
        session.getId(), new ConcurrentWebSocketSessionDecorator(session, 5000, 100 * 1024));
  }
}
```

handler/ConcurrentMessageHandler.java

새로 만든 핸들러를 아래와 같이 새로운 엔드포인트 '/ws/v2/message’로 연결한다.

```java
@Configuration
@EnableWebSocket
@SuppressWarnings("unused")
public class WebSocketHandlerConfig implements WebSocketConfigurer {

  private final MessageHandler messageHandler;
  private final ConcurrentMessageHandler concurrentMessageHandler;

  public WebSocketHandlerConfig(
      MessageHandler messageHandler, ConcurrentMessageHandler concurrentMessageHandler) {
    this.messageHandler = messageHandler;
    this.concurrentMessageHandler = concurrentMessageHandler;
  }

  @Override
  public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
    registry
        .addHandler(messageHandler, "/ws/v1/message")
        .addHandler(concurrentMessageHandler, "/ws/v2/message");
  }
}
```

config/WebSocketHandlerConfig.java

이제 '/ws/v2/message’로 연결되는 웹소켓 세션은 스레드 세이프하게 동작한다.

아래와 같이 동시성 상황에서 정상 동작을 검증할 테스트를 하나 추가한다. 이 테스트는 모든 클라이언트가 기대하는 메시지를 2개씩 모두 받아서 정확히 6개의 메시지를 받았는지까지 검증한다.

```java
def 'Group Chat Concurrent Test'() {
    given:
    def url = "ws://localhost:${port}/ws/v2/message"
    (clientA, clientB, clientC) = [createClint(url), createClint(url), createClint(url)]

    when:
    clientA.session.sendMessage(new TextMessage('clientA: 안녕하세요. A 입니다.'))
    clientB.session.sendMessage(new TextMessage('clientB: 안녕하세요. B 입니다.'))
    clientC.session.sendMessage(new TextMessage('clientC: 안녕하세요. C 입니다.'))

    then:
    def resultA = (0..1).findResults { clientA.queue.poll(1, TimeUnit.SECONDS) }.join('')
    def resultB = (0..1).findResults { clientB.queue.poll(1, TimeUnit.SECONDS) }.join('')
    def resultC = (0..1).findResults { clientC.queue.poll(1, TimeUnit.SECONDS) }.join('')
    resultA.contains('clientB') && resultA.contains('clientC')
    resultB.contains('clientA') && resultB.contains('clientC')
    resultC.contains('clientA') && resultC.contains('clientB')

    and:
    clientA.queue.isEmpty()
    clientB.queue.isEmpty()
    clientC.queue.isEmpty()
}
```

SendMessageMultiThreadSpec.groovy

이 테스트에서도 BlockingQueue에 테스트 클라이언트가 받은 메시지를 모았다가 모두 꺼내서 합친 후에 받은 내용을 확인하는 이유는 메시지를 받는 순서를 알 수 없기 때문이다.

테스트 코드에서 clientA, clientB, clientC 순서로 메시지를 전송한다고 서버에서 각 클라이언트의 요청을 멀티스레드로 처리할 때 테스트 코드에서 전송한 순서와 같은 순서로 처리된다는 보장은 없다. 실행해 보면 테스트는 통과한다.

ConcurrentWebSocketSessionDecorator는 지금 테스트 코드에서 사용한 것과 같은 BlockingQueue를 사용하여 멀티스레드에서 들어오는 전송 요청을 모두 큐에 넣어놓고 하나씩 꺼내서 전송해 준다. 구현체는 테스트 코드에서 간단히 사용한 ArrayBlockingQueue가 아니라 LinkedBlockingQueue를 사용한다. 내부 구현이 복잡하지 않으니 한번 열어서 보는 것도 좋다.

이렇게 멀티스레드 환경에서 웹소켓을 사용할 때 발생할 수 있는 동시성 문제 중 하나를 확인하고 간단히 대응하고 검증하는 방법까지 하나의 예제로 구성해 봤다.

이상으로 ConcurrentWebSocketSessionDecorator에 대한 소개를 마치면서, 제 강의 쿠폰을 첨부합니다.

30% 할인 코드명: 채팅플랫폼 (~25/5/12) \*결제 창에서 쿠폰 코드 '채팅플랫폼' 입력.

강의 링크: [https://buly.kr/Edt2csp](https://buly.kr/Edt2csp)

[

대규모 채팅 플랫폼으로 한 번에 끝내는 실전 대용량 트래픽 커버 완전판 | 패스트캠퍼스

전 카톡 서버 운영자가 알려주는 채팅 플랫폼 기반 '대용량' 트래픽 처리

fastcampus.co.kr

](https://buly.kr/Edt2csp)

[저작자표시 비영리 변경금지 (새창열림)](https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ko)

#### 'Dev' 카테고리의 다른 글

| [IntelliJ의 Groovy Console 소개](https://prostars.net/361) (1) | 2025.03.04 |
| --- | --- |
| [Partitioner와 Multi Thread를 활용한 Spring Batch 성능 개선](https://prostars.net/357) (0) | 2024.05.21 |
| [가상 면접 사례로 배우는 대규모 시스템 설계 기초 2](https://prostars.net/355) (0) | 2024.03.16 |
| [진화적 아키텍처](https://prostars.net/353) (0) | 2023.09.24 |
| [자바 알고리즘 인터뷰 with 코틀린 - 102가지 알고리즘 문제 풀이로 완성하는 코딩 테스트](https://prostars.net/352) (0) | 2023.09.14 |
