---
title: "LINE에서 Kafka를 사용하는 방법"
source: "https://engineering.linecorp.com/ko/blog/how-to-use-kafka-in-line-1"
author:
  - "[[Kawamura Yuto]]"
published:
created: 2026-10-26
description: "참고. 이번 블로그는 LINE DEVELOPER DAY 2018에서 Yuto Kawamura 님이 발표한 ‘Multi-Tenancy Kafka cluster for LINE services with 250 billion..."
tags:
  - "clippings"
---

> [!summary]
> Part 1 of a three-part transcript of Yuto Kawamura's LINE DEVELOPER DAY 2018 talk on LINE's company-wide multi-tenant Kafka cluster. Explains the two usage patterns (distributed task queue and data hub for propagating events such as friend-graph updates), why everything is deliberately concentrated in one cluster (easy data discovery and uniform access, plus operating cost that does not grow with the number of tenants), and the scale: over 250 billion records and 210 TB per day, peaking above 4 GB/s, serving about 50 services. The reliability section argues request count matters more than data volume because Kafka relies on client batching and the OS page cache, so LINE applies Kafka request quotas to every client by default to keep one misconfigured tenant from degrading the brokers.

## LINE에서 Kafka를 사용하는 방법 - 1편

> 참고. 이번 블로그는 [LINE DEVELOPER DAY 2018](https://linedevday.linecorp.com/jp/2018/en/) 에서 Yuto Kawamura 님이 발표한 ‘Multi-Tenancy Kafka cluster for LINE services with 250 billion daily messages’ 세션을 기록한 내용을 각색하여 옮긴 글입니다(원문 기록 및 제공: [logmi](https://logmi.jp/tech/articles/320330)).

## 들어가며

안녕하세요. LINE에서 소프트웨어 엔지니어로 일하고 있는 Kawamura Yuto입니다. 저는 LINE 서버 개발을 중심으로 HBase 운영 등의 업무를 하고 있으며, 현재 전사적으로 [Kafka](https://kafka.apache.org/) 플랫폼을 제공하는 팀의 리더를 맡고 있습니다. 이번 글에선 LINE에서 운영하고 있는 대규모 Kafka 플랫폼에 대해서 말씀드리려고 합니다.

Kafka라는 소프트웨어에 대해 간단하게 설명하자면, Kafka는 스트리밍 데이터를 다루기 위한 미들웨어와 그 주변 생태계를 말합니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/1kafka1-1024x576.jpg)

Kafka는 LINE과 같이 서비스를 제공하는 기업에게 중요한 몇 가지 특성이 있습니다. 하나는 높은 확장성(scalability)과 가용성(availability)을 갖추고 있다는 점입니다. 또 하나는 데이터 영속성(persistency)을 지원한다는 점인데요. Kafka에 한 번 입력된 데이터는 그 시점에서 영속화되었다고 볼 수 있다는 의미입니다. 그리고 마지막으로 Pub/Sub 모델을 사용한 데이터 분포를 지원한다는 점입니다.

### Kafka를 이해하기 위한 세 가지 컴포넌트

Kafka 아키텍처를 이해하려면 아래 그림에 보이는 세 가지 컴포넌트를 이해해야 합니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/1kafka2-1024x576.jpg)

먼저 왼쪽의 'Producer'는 Kafka에 데이터를 입력하는 클라이언트입니다. 다음으로 가운데에 위치한 'Broker cluster'는 임의 개수의 노드로 구성되는 클러스터로 'topic'이라고 불리는 데이터 관리 유닛을 임의 개수만큼 호스팅할 수 있습니다. Producer는 그 중 하나의 topic을 대상으로 데이터를 입력합니다. 마지막으로 오른쪽에 위치한 'Consumer'는 Kafka에서 데이터를 가져오는 클라이언트입니다. Consumer는 데이터를 가져올 topic을 지정한 후 해당 topic에서 데이터를 가져오는데요. 여기서 중요한 특성은 하나의 topic에 여러 개의 Consumer가 각각 다른 목적으로 존재한다는 점입니다. 일단 topic에 입력된 데이터는 여러 Consumer가 서로 다른 처리를 하기 위해 여러 번 가져올 수 있는데요. 이것이 바로 Pub/Sub라고 불리는 데이터 분포 모델입니다.

## LINE에서 Kafka를 사용하는 방법

LINE은 아주 큰 규모의 Kafka 클러스터를 운영하고 있습니다. 특정 서비스나 시스템만을 대상으로 한 것이 아니라, 사내의 모든 서비스와 시스템에서 이용할 수 있는 범용적인 플랫폼입니다. 처음에는 LINE 메세지 서버 개발 팀에서 너무 복잡해진 아키텍처를 간소화하기 위한 중간 레이어로 사용하고자 채택했는데요. 당시 성공적으로 적용되어 높은 운영 실적을 내자 이를 지켜본 다른 여러 팀에서 사용하기를 원해서 전사적인 플랫폼으로 자연스럽게 발전하게 되었습니다.

LINE에서 Kafka를 사용하는 방법은 크게 두 가지입니다. 첫 번째는 단순하게 분산 큐잉 시스템으로 사용하는 방법입니다. 예를 들어, 어떤 서비스의 웹 애플리케이션 서버에서 처리하는 데 자원을 많이 사용해야 하는 업무가 발생했을 때, 이를 내부에서 처리하지 않고 다른 프로세스에서 작동 중인 백그라운드의 태스크 프로세서에 요청하기 위한 큐로 사용하는 경우를 들 수 있습니다.

두 번째는 데이터 허브로 사용하는 방법입니다. 이 방법은 어떤 서비스에 데이터 업데이트가 발생했을 때, 해당 데이터를 사용하는 다른 여러 서비스에 전파하기 위한 허브로 사용하는 방법입니다. 구체적인 예를 들어 설명하겠습니다. LINE에서는 사용자의 친구 관계를 데이터로 저장하고 있습니다. 예를 들어 아래 그림과 같이 어떤 사용자 A가 다른 사용자 B를 친구로 추가했을 때, LINE 내부에서는 그에 따른 처리를 수행하고 업데이트된 관계를 Kafka의 topic에 이벤트로 입력합니다. 이 이벤트는 사용자 그래프를 활용해서 제공하는 통계 시스템이나 타임라인 등의 서비스에서 사용합니다. 또한 평소에 LINE을 사용하면서 모르는 친구가 갑자기 추가되어 스팸이나 광고를 보내는 불쾌한 경험을 하신 분도 계실 텐데요. 이런 액티비티를 분석해서 자동으로 패널티를 부여하는 시스템에서도 사용하고 있습니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/1kafka3-1024x576.jpg)

### 하나의 클러스터에 데이터를 집중시키는 이유

여기에서 중요한 포인트는 큰 규모의 클러스터를 독립적인 여러 서비스와 시스템에서 공통으로 사용하고 있다는 점입니다. 그 이유는 크게 두 가지가 있습니다.

첫 번째 이유는 데이터 허브라는 콘셉트입니다. 저희는 일부러 많은 데이터를 하나의 클러스터에 집중시키고 있습니다. 이렇게 하면 데이터를 사용하는 서비스가 해당 데이터를 쉽게 찾을 수 있을 뿐 아니라, 서비스에서 데이터에 접근하는 수단도 통일시킬 수 있습니다. 그 결과 아키텍처를 단순하게 유지할 수 있습니다.

두 번째 이유는 운영 효율입니다. 지원하는 모든 서비스와 시스템별로 Kafka 클러스터를 하나씩 준비해야 한다면, 지원 대상 서비스와 시스템 수에 비례해서 운영 비용이 증가하게 됩니다. 이런 상황을 피하기 위해 서비스와 시스템이 하나의 클러스터를 사용하게 하고 엔지니어링 자원을 전부 그 클러스터에 집중시켜서 클러스터의 신뢰성과 성능을 극대화하는 전략을 취하고 있습니다.

이런 이유로 현재 LINE에서는 아래와 같이 매우 많은 서비스가 Kafka 플랫폼에 의존해서 동작하고 있습니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/1kafka4-1024x576.jpg)

LINE 메시징 서비스는 물론이고 블록체인 플랫폼, 광고 플랫폼, LINE LIVE 등의 서비스와 데이터 분석 시스템을 포함해 그 외에도 수많은 서비스가 Kafka를 백엔드로 사용해서 구축되었습니다. 그 결과 저희 클러스터는 매우 큰 규모의 트래픽을 다루게 되었습니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/1kafka5-1024x576.jpg)

매일 2,500억 건이 넘는 레코드가 입력되고, 데이터 양은 일일 210테라바이트에 달합니다. 가장 많을 때는 1초에 4기가바이트를 넘는 데이터가 입력됩니다. 이 데이터들은 50여 개의 독립적인 서비스와 시스템에서 사용하는 데이터입니다. 단일 클러스터로는 세계 최대 규모입니다.

## 높은 신뢰성과 성능 확보

위에서 말씀드린 바와 같이, Kafka 클러스터는 많은 서비스에서 백엔드로 사용하고 있습니다. 따라서 매우 높은 신뢰성과 성능이 필요합니다. 이와 같은 요구사항을 멀티테넌시(multitenancy) 클러스터에서 충족시키려면 몇 가지 조건을 달성해야 합니다.

첫 번째 조건은 클러스터를 가혹한 작업 부하(workload)에서 보호할 수 있어야 한다는 점입니다. 저희 플랫폼은 사내 서비스와 시스템을 대상으로 제공하기 때문에 악의적으로 클러스터를 공격하는 경우는 고려하지 않아도 됩니다. 하지만 사용자가 설정하거나 배포하면서 실수하면, 예기치 못한 작업 부하가 클러스터에 걸리게 될 수는 있습니다.

두 번째로, 어느 요청이 어느 클라이언트에서 온 것인지를 정확히 파악해야 합니다. 예기치 못한 자원의 활동이 클러스터에서 감지되었을 때, 그 원인이 되는 클라이언트를 신속하게 찾아내서 해결해야 하기 때문입니다.

마지막으로, 클라이언트 간 일정 수준의 작업 부하 격리를 유지해야 합니다. 예를 들어, 어떤 클라이언트가 그 자체의 작업 부하로 응답 시간이 느려졌을 때, 같은 클러스터에 접속하고 있는 전혀 관련 없는 클라이언트가 같은 이유로 응답 시간이 저하되는 상황이 있어서는 안 된다는 뜻입니다.

이런 조건을 달성하기 위해 저희가 취한 방법을 말씀드리겠습니다.

### 요청 수 제어하기

클러스터를 가혹한 작업 부하에서 보호해야 하는 첫 번째 조건과 관련하여, Kafka 클러스터를 운영하면서 데이터 양보다 요청 수를 제어하는 것이 중요하다는 사실을 경험을 통해 알게 되었습니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/1kafka6-1024x576.jpg)

Kafka는 대용량 데이터를 아주 잘 다룰 수 있도록 설계된 소프트웨어입니다. 예를 들어, Kafka 자체에는 캐시 레이어가 없습니다. 그 대신 OS별로 제공되는 페이지 캐시에 캐시 기능을 전면적으로 의존하고 있어서, 대용량 데이터가 애플리케이션의 메모리와 OS의 페이지 캐시에 중복으로 캐시되는 것을 방지합니다. 또 Kafka의 클라이언트에는 배칭(batching)이라는 기능이 기본적으로 지원됩니다. 이 기능은 여러 개의 레코드를 하나의 큰 요청으로 묶어서 클러스터에 전달할 수 있는 기능인데요. 이를 이용하면 데이터 양이나 레코드 수가 늘어나도 요청 수 증가를 억제할 수 있어 요청 별로 발생하는 오버헤드를 방지할 수 있습니다. 그래서 클라이언트가 보내는 요청 수를 제어해야 합니다. 이를 위해 Kafka의 '요청 쿼터(request quota)'라는 기능을 사용하고 있습니다.

![](https://engineering.linecorp.com/wp-content/uploads/2019/10/1kafka7-1024x576.jpg)

이 기능은 특정 클라이언트가 사용할 수 있는 브로커의 자원, 엄밀히 말하면 브로커가 가진 스레드의 시간을 제한할 수 있는 기능입니다. 이 기능을 모든 클라이언트에 기본으로 설정하면, 하나의 클라이언트가 사용할 수 있는 브로커 자원의 양을 제한할 수 있습니다. 이렇게 하면 한 클라이언트가 예기치 못한 폭발적인 수준으로 클러스터에 요청을 보냈을 경우에도 클러스터 전체가 멈춰버리거나 성능이 저하되는 등의 사태가 발생하지 않게 됩니다.

이번 글에서는 LINE에서 Kafka를 사용하는 방법과 Kafka 클러스터의 높은 신뢰성과 성능을 확보하기 위해 저희가 요청 수를 제어하는 방법에 대해 설명했습니다. 이어서 다음 글에서는 클라이언트 간의 작업 부하 격리와 관련하여 실제 저희 운영 환경에서 발생했던 문제를 예시로 설명하겠습니다. 다음 편을 기대해 주세요!
