---
title: "LINE에서 Kafka를 사용하는 방법"
source: "https://engineering.linecorp.com/ko/blog/how-to-use-kafka-in-line-2"
author:
  - "[[Kawamura Yuto]]"
published:
created: 2026-10-26
description: "참고. 이번 블로그는 LINE DEVELOPER DAY 2018에서 Yuto Kawamura 님이 발표한 ‘Multi-Tenancy Kafka cluster for LINE services with 250 billion..."
tags:
  - "clippings"
---

> [!summary]
> Part 2 is the incident investigation: Produce API p99 latency degraded 50 to 100 times while brokers showed heavy disk reads and saturated network threads, even though request volume had not changed. Kawamura explains Kafka's two thread layers (network threads running a non-blocking event loop with one response queue each, and request handler threads polling a single shared request queue), then isolates what makes the Fetch API different: its response is served through the `sendfile` syscall straight from disk to socket, which blocks the network thread whenever the data is not already in the page cache. A SystemTap histogram of `sendfile` durations showed a tail of calls over 8 ms, supporting the hypothesis that one cold Fetch stalls every unrelated response queued on the same network thread.

## LINE에서 Kafka를 사용하는 방법 - 2편

> 참고. 이번 블로그는 [LINE DEVELOPER DAY 2018](https://linedevday.linecorp.com/jp/2018/en/) 에서 Yuto Kawamura 님이 발표한 ‘Multi-Tenancy Kafka cluster for LINE services with 250 billion daily messages’ 세션을 기록한 내용을 각색하여 옮긴 글입니다(원문 기록 및 제공: [logmi](https://logmi.jp/tech/articles/320330)).

## 들어가며

안녕하세요. LINE에서 소프트웨어 엔지니어로 일하고 있는 Kawamura Yuto입니다. 지난 [1편](https://engineering.linecorp.com/ko/blog/how-to-use-kafka-in-line-1/) 에 이어 이번 글에서는 Kafka 클러스터의 신뢰성과 성능을 확보하기 위한 클라이언트 간의 작업 부하 격리와 관련해서, 실제 운영 환경에서 발생했던 문제를 예시로 설명하겠습니다.

## 운영 환경에서 발생한 문제

우선 클러스터의 성능 저하를 발견한 게 계기가 되었습니다. Kafka의 클라이언트가 클러스터에 데이터를 입력할 때 사용하는 'Produce'라는 API가 있습니다. 이 Produce API 응답 시간의 99번째 퍼센타일이 평소보다 50배에서 100배까지 악화된 것을 발견했습니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/2kafka1-1024x576.jpg)

관련하여 조사한 결과 크게 두 가지 사실을 알게 되었습니다. 하나는 해당 시간대에 브로커 기기에 매우 많은 양의 디스크 읽기(disk read)가 발생했다는 점입니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/2kafka2-1024x576.jpg)

또 하나는 Kafka 내부에 존재하는, 클라이언트와의 I/O를 담당하는 '네트워크 스레드(network thread)'라는 이름의 스레드의 이용률(utilization)이 매우 높아졌다는 점입니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/2kafka3-1024x576.jpg)

## 문제 원인 조사

먼저 Kafka가 요청을 어떻게 처리하는지 간단하게 설명하고 넘어가겠습니다.

### Kafka의 요청 핸들링

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/2kafka4-1024x576.jpg)

Kafka가 요청을 처리할 때 크게 두 개의 스레드 레이어를 사용하는데요. 그중 하나인 네트워크 스레드는 클라이언트와의 I/O를 담당하는 스레드입니다. 네트워크 스레드는 클라이언트 소켓에 도착한 요청을 가져와서 요청 객체를 생성하고, 준비된 응답 객체를 클라이언트 소켓에 입력하는 역할을 합니다.

다른 하나는 요청 핸들러 스레드입니다. 네트워크 스레드가 가져온 요청의 내용을 처리해서 필요한 응답 객체를 네트워크 스레드에 반환하는 역할을 합니다.

전체적인 흐름은 다음과 같습니다. 먼저 클라이언트 소켓에 요청이 도착하면, 네트워크 스레드가 그 요청을 가져와서 요청 객체를 생성합니다. 요청 객체는 요청 큐에 저장됩니다. 이 요청 큐는 브로커 내에 하나만 존재하며, 모든 요청 핸들러 스레드가 이 큐를 폴링해서 요청을 가져옵니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/2kafka5-1024x576.jpg)

요청 핸들러 스레드 하나가 큐에서 요청을 취득하면 처리가 진행됩니다. API 유형에 따라 로컬 디스크로 I/O가 실행되는 경우가 있으며, 응답 객체가 생성됩니다. 응답 객체는 응답 큐에 저장됩니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/2kafka6-1024x576.jpg)

네트워크 스레드가 응답 큐에서 응답을 가져갑니다. 네트워크 스레드 하나당 응답 큐가 하나씩 존재하는 모델입니다. 따라서 이 응답 큐에 저장된 응답은 이를 담당하는 네트워크 스레드로만 처리됩니다. 네트워크 스레드가 응답 큐에서 응답을 가져오면 그 내용을 클라이언트 소켓에 입력해서 처리를 완료합니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/2kafka7-1024x576.jpg)

즉, 네트워크 스레드란 이벤트 루프를 처리하는 스레드입니다. 이른바 이벤트 기반 비동기 I/O 처리를 수행하는 것이죠. 여러 개의 소켓을 다중화해서 IO 준비가 완료된 소켓을 순차적으로 처리하는 작업을 계속 반복 수행하는 것이 바로 네트워크 스레드입니다.

기본적으로 네트워크 스레드 내에서 이루어지는 처리는 I/O에 의해 차단되지 않습니다. 브로커에 새로운 연결이 생성되면 그 연결은 브로커 내에 있는 여러 네트워크 스레드 중 하나에 할당되고 이후 해당 네트워크 스레드로만 처리하게 됩니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/2kafka8-1024x576.jpg)

### 원인 검증

저희가 지금 조사하는 네트워크 스레드의 이용률 증가 현상이 어떤 경우에 발생하는지를 생각해 봤습니다. 먼저 첫 번째로는, 실제로 처리해야 하는 요청 수가 많아져서 바쁘게 처리를 하는 상황을 가정할 수 있습니다. 하지만 저희는 요청 수에 변동이 없다는 사실을 확인했기 때문에 다른 가능성을 염두에 두었습니다. 두 번째로 가능성이 있는 상황은 네트워크 스레드가 처리를 수행하는 과정인 이벤트 루프 내의 특정 처리에서 차단된 경우입니다. 이로 인해 스레드의 이용률이 높아졌을 가능성을 고려했습니다.

이런 상황이 어떤 경우에 발생할 수 있는지를 이해하기 위해 Kafka 소스 코드를 살펴보았고, 이런 상황을 초래할 수 있는 가능성을 하나 발견했습니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/2kafka9-1024x576.jpg)

이 내용을 이해하려면 Kafka의 API별 응답 처리 방식의 차이를 이해해야 합니다. Fetch라는 API와 그 외의 다른 API는 처리 방식이 다릅니다.

먼저 다른 API의 응답 처리 방식을 설명하겠습니다. Fetch를 제외한 다른 API는 네트워크 스레드가 응답 큐에서 응답 객체를 취득한 시점에 클라이언트 소켓에 입력해야 할 데이터가 모두 메모리에 저장되어 있습니다. 따라서 네트워크 스레드는 저장되어 있는 데이터를 클라이언트 소켓에 그냥 복사만 하면 됩니다.

하지만, Fetch API의 경우는 사정이 다릅니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/2kafka10-1024x576.jpg)

Fetch라는 API는 Consumer가 topic의 데이터를 클러스터에서 가져올 때 사용하는 API입니다. 따라서 브로커는 응답을 반환할 때 로컬 디스크에 저장되어 있는 topic의 데이터를 클라이언트 소켓에 복사해야 합니다. 이 처리를 위해 브로커는 'sendfile'이라는 시스템 콜을 사용합니다. sendfile이란 리눅스 커널(Linux kernel) 등에서 제공하는 시스템 콜로, 로컬 디스크의 데이터를 클라이언트 소켓에 바로 복사할 수 있게 해 주는 API입니다. 이 API를 사용하면 데이터를 사용자 공간의 메모리에 한 번 복사하는 오버헤드를 막을 수 있어서 매우 효율적이라고 알려져 있습니다. Kafka는 설계상 이 기능에 크게 의존합니다. sendfile을 처리할 때 대상 데이터가 페이지 캐시에 있으면 리눅스 커널이 그 데이터를 클라이언트 소켓에 복사하기만 하면 되는데, 만약 페이지 캐시에 데이터가 없다면 로컬 디스크에서 데이터를 로딩해와야 합니다.

### 시스템 콜 처리 시간 조사

그럼 디스크에서 데이터를 로딩하면 어떻게 되는지를 알아보겠습니다.

대상 데이터가 페이지 캐시에 존재할 경우, 앞서 말씀드린 바와 같이 단순하게 메모리 복사 작업을 수행하면 됩니다. 보통 수십 마이크로초에서 수백 마이크로초의 매우 짧은 시간 내에 처리가 완료된다고 합니다. 반면에 대상 데이터를 디스크에서 가져와야 할 경우 매우 느려집니다. 보통 수 밀리초에서 수십 밀리초의 긴 시간이 소요된다고 알려져 있습니다. 만약 이런 처리가 이벤트 루프 중에 발생한다면 큰 문제가 되겠지요.

이 시나리오에 대해서 확증을 얻기 위해 저희는 sendfile 시스템 콜의 처리 시간을 알아보기로 했습니다. 이런 조사를 할 때 저희가 자주 사용하는 툴 중 하나로 'SystemTap'이라는 툴이 있습니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/2kafka11-1024x576.jpg)

SystemTap은 동적 트레이싱 툴이라고 불리는데요. 스크립트를 몇 줄 작성하면 커널 내에서 발생하는 각종 이벤트를 관측할 수 있는 툴입니다. 위 이미지의 오른쪽에 간단한 예가 있는데요. 어떤 기기에서 호출된 시스템 콜 수를 세기만 하는 스크립트입니다. 쉽게 설명하면, 두 번째 줄의 `global cnt` 에서 선언된 변수에 대해 그 아래의 블록에서 시스템 콜이 호출될 때마다 같은 이름의 엔트리를 증분(increment)합니다. 그리고 마지막 블록에서 `cnt` 변수를 반복(iterate)하면서 시스템 콜의 이름과 시스템 콜이 호출된 횟수를 출력합니다. 이게 끝입니다. 보시는 바와 같이 시스템 콜의 이름과 해당 시스템 콜이 호출된 횟수가 나옵니다.

이 SystemTap은 LINE 같이 규모가 큰 서비스를 제공하는 기업에게 매우 중요한 특성을 하나 가지고 있습니다. 아주 낮은 오버헤드로 동작한다는 점입니다. 그렇기 때문에 운영 환경에서도 오버헤드를 신경 쓸 필요 없이 안심하고 실행할 수 있습니다. 비슷한 툴로 DTrace나 eBPF도 유명합니다.

### 조사 결과

SystemTap을 사용해서 브로커가 발행한 sendfile 시스템 콜의 처리 시간을 측정해 봤고, 다음과 같은 히스토그램을 얻을 수 있었습니다(스크립트 내용은 생략하겠습니다).

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/2kafka12-1024x576.jpg)

보시다시피 대부분 2마이크로초에서 32마이크로초의 매우 짧은 시간 내에 처리가 완료되었는데요. 극히 일부가 8미리초 이상의 매우 긴 시간이 소요된 것을 볼 수 있습니다. 이 결과를 보고 확증을 얻어 다음과 같이 문제의 가설을 세웠습니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/2kafka13-1024x576.jpg)

브로커가 Fetch 요청을 처리합니다. 그 과정에서 sendfile 호출을 하면서 디스크 읽기가 필요할 경우 네트워크 스레드의 이벤트 루프가 차단됩니다. 그렇게 되면 현재 처리 중인 요청뿐만 아니라 같은 네트워크 스레드로 처리되어야 하는 후속 응답, 다른 관련 없는 API의 응답이 모두 차단된다는 것이 가설의 내용입니다. 디스크 읽기 때문에 발생한 지연이 처리 대기 중이던 모든 응답에 영향을 끼치는 상태인 거죠. 이로써 원래 관련 없던 Produce API의 응답 시간이 저하된 것도 설명이 가능합니다.

이제 'LINE에서 Kafka를 사용하는 방법'의 마지막 편이 남았는데요. 다음 편에서는 문제를 해결한 방법을 설명하고 적용 결과를 말씀드리겠습니다. 다음 편을 기대해 주세요!
