---
title: "Apache Kafka 4.0: 아키텍처 및 주요 특징"
source: "https://velog.io/@hyungki26/Apache-Kafka-4.0-%EC%95%84%ED%82%A4%ED%85%8D%EC%B2%98-%EB%B0%8F-%EC%A3%BC%EC%9A%94-%ED%8A%B9%EC%A7%95"
author:
published:
created: 2026-10-28
description: "완벽합니다! 이제 카프카 4.0에 대한 포괄적인 마크다운 블로그 글을 작성해드리겠습니다.Apache Kafka 4.0은 2025년 3월에 출시된 메이저 릴리즈로, 이벤트 스트리밍 플랫폼의 역사에서 중요한 전환점을 맞이했습니다. 가장 주목할 만한 변화는 10년 이상 Ka"
tags:
  - "clippings"
---

> [!summary]
> 2025년 3월 출시된 Apache Kafka 4.0의 주요 변경점을 정리한 글이다. ZooKeeper를 완전히 제거하고 KRaft 모드만 지원하게 된 아키텍처 변화와 함께, Stop-the-World 리밸런싱을 없앤 차세대 컨슈머 그룹 프로토콜(KIP-848)과 Share Group 기반 큐 시맨틱(KIP-932, Early Access)을 소개한다. 이 밖에 ELR·Pre-Vote 같은 안정성 개선, 브로커 Java 17·클라이언트 Java 11 요구사항, Log4j2 전환, 구 프로토콜 API 제거와 업그레이드 체크리스트를 다룬다.

![thumbnail](https://velog.velcdn.com/images/gwk/profile/3f7c8383-982b-4ed4-85d2-d644e0b576c6/image.webp)

[GarionNachal](https://velog.io/@hyungki26/posts) ·2025년 12월 23일

## kafka

목록 보기

2/25

## 들어가며

Apache Kafka 4.0은 2025년 3월에 출시된 메이저 릴리즈로, 이벤트 스트리밍 플랫폼의 역사에서 중요한 전환점을 맞이했습니다. 가장 주목할 만한 변화는 10년 이상 Kafka의 중추 역할을 해온 **Apache ZooKeeper의 완전한 제거** 입니다. 이제 Kafka는 자체 개발한 KRaft 모드를 기본으로 사용하며, 더욱 간결하고 확장 가능한 아키텍처로 진화했습니다.

---

## 1\. ZooKeeper에서 KRaft로: 아키텍처의 혁명

### ZooKeeper 의존성 제거

Kafka 4.0의 가장 큰 변화는 **KRaft(Kafka Raft) 모드가 기본** 이 되었다는 점입니다. 과거에는 메타데이터 관리를 위해 별도의 ZooKeeper 앙상블을 운영해야 했지만, 이제는 Kafka 자체적으로 모든 메타데이터를 관리합니다.

![KRaft Architecture Without ZooKeeper](https://sspark.genspark.ai/cfimages?u1=ARvwdTn%2BMFhhMFwEDqcifD6UlPxWFxWDK7NsM3E6xEiSQDDn1%2F9ERZcMV%2BODNeyPgFJ6nqQ1ybaaSAnsyPmpA9s9lHgB5qjfxoQJ31gYC%2FIMv%2F2XLoruACdOQ3EYeTwFbAnDJEdZuR%2FQNL3Hm4nnx%2Fj%2FmAGwihFG5RFDA3j3FsqcXYq%2B5Iy0Qxk1Z2Y%3D&u2=bD999uFbSgu%2B9BhG&width=2560)

### KRaft의 주요 이점

**운영 복잡성 감소**

- 별도의 ZooKeeper 클러스터 관리 불필요
- 설치 및 배포 과정 간소화
- 통합된 시스템으로 관리 포인트 축소

**확장성 향상**

- 100만 개 이상의 파티션 지원 가능
- ZooKeeper의 10만 파티션 제한 극복
- 더 빠른 메타데이터 처리

**성능 개선**

- 컨트롤러 페일오버 시간 단축
- 메타데이터 변경 작업의 응답 속도 향상
- 클러스터 복구 시간 감소

![ZooKeeper to KRaft Migration](https://sspark.genspark.ai/cfimages?u1=KS6Q8VVpLcEL3ahwugd0eYiqKvhLlJOLDUHdy7h2E2%2F4Xl5v9TBjFXsrrGQdocH03Q3LQtR5j%2BIjrQSPE7a4%2Bk0DiEqc4EbMIxHumKQ%2FGv6m%2Fjq9qgHIkEsyO0k%3D&u2=LvfPsfXEilSe%2FXwm&width=2560)

---

## 2\. 차세대 컨슈머 그룹 프로토콜 (KIP-848)

Kafka 4.0은 **완전히 새로운 컨슈머 그룹 프로토콜** 을 도입하여 리밸런싱 성능을 획기적으로 개선했습니다.

![Consumer Rebalance Protocol](https://sspark.genspark.ai/cfimages?u1=4hQKd092yUv1mpumsdMju6sbcHKVnEFvBds59UQFVHB6HBHCQadgh7oIMogP1UngnsSI7OA0P%2F7uaTzZCbWbfLxiDf905WB1dDGInJ4fAkHQALKoVeQs%2B1rJ4Hv9bXFEE37jRRlIp4850F%2BhkVVvav1BLhQ8tVlYxVT8zHvAHIqKqF4%3D&u2=HBzcStVjcocZuCPd&width=2560)

### 주요 개선사항

**Stop-the-World 리밸런싱 제거**

- 기존: 리밸런싱 중 모든 컨슈머의 메시지 처리 중단
- 개선: 점진적 리밸런싱으로 다운타임 최소화

**성능 향상**

- 대규모 컨슈머 그룹에서 리밸런싱 시간 대폭 단축
- 레이턴시 감소로 실시간 스트리밍 안정성 향상
- 컨슈머 추가/제거 시 영향 최소화

**사용 방법**

- 서버 측: 기본으로 활성화
- 클라이언트 측: `group.protocol=consumer` 설정으로 옵트인
```
# 새로운 컨슈머 프로토콜 활성화
group.protocol=consumer
```

---

## 3\. Queues for Kafka: 큐 시맨틱 지원 (KIP-932)

Kafka 4.0은 **전통적인 메시지 큐 기능** 을 Early Access로 제공합니다. 이는 Kafka의 활용 범위를 Pub-Sub 패턴을 넘어 Point-to-Point 메시징으로 확장합니다.

### Share Group 개념

**Share Group이란?**

- 여러 컨슈머가 하나의 토픽을 협력적으로 소비
- 각 메시지는 그룹 내 하나의 컨슈머만 처리
- 기존 시스템의 "Durable Shared Subscription"과 유사

**사용 사례**

- 작업 큐(Work Queue) 패턴 구현
- 로드 밸런싱이 필요한 태스크 처리
- 병렬 처리가 필요한 배치 작업

![Kafka Architecture Overview](https://sspark.genspark.ai/cfimages?u1=6kdVKJQ93eMJIjFLlDM15DRIrVMFUQCOaJ3QxXDi8eQfTcRncS26hIAbIgcgvm81bltW4RBtnUz6%2BrmcCbMzhVx4IjY%3D&u2=Q20FQSllg3f7p9jN&width=2560)

---

## 4\. 기타 주요 기능 및 개선사항

### 보안 및 안정성 강화

**트랜잭션 서버 측 방어 (KIP-890)**

- 프로듀서 장애 시 "좀비 트랜잭션" 발생 가능성 감소
- 트랜잭션 무결성 강화

**Eligible Leader Replicas (KIP-966)**

- 데이터 손실 없는 안전한 리더 선출
- High-Watermark까지 완전한 데이터를 가진 복제본만 리더 후보로 지정

**Pre-Vote 메커니즘 (KIP-996)**

- 불필요한 KRaft 리더 선출 감소
- 네트워크 파티션이나 일시적 문제로 인한 중단 최소화

### 클라이언트 및 관리 도구 개선

**애플리케이션 메트릭 수집 (KIP-1076)**

- Kafka Streams 같은 임베디드 클라이언트의 메트릭 수집 가능
- 클라이언트 메트릭과 애플리케이션 메트릭 통합 모니터링

**기간 기반 오프셋 리셋 (KIP-1106)**

- `auto.offset.reset` 옵션에 duration 기반 전략 추가
- 무한 스토리지 환경에서 유용한 시간 기반 초기화
```
# 24시간 전부터 소비 시작
auto.offset.reset=by-duration:PT24H
```

**그룹 관리 개선 (KIP-1043, KIP-1099)**

- 새로운 `kafka-groups.sh` 도구로 모든 그룹 타입 조회
- Consumer Group과 Share Group 정보 상세 표시
- 트러블슈팅 향상

### 플랫폼 업그레이드

**Java 버전 요구사항 상향**

- Kafka Clients & Kafka Streams: **Java 11 이상**
- Kafka Brokers, Connect, Tools: **Java 17 이상**
- 최신 Java 기능 활용 및 성능 최적화

**로깅 프레임워크 업그레이드 (KIP-653)**

- Log4j에서 **Log4j2** 로 마이그레이션
- `log4j-transform-cli` 도구로 기존 설정 자동 변환
- 보안 및 성능 개선

**구 프로토콜 API 제거 (KIP-896)**

- 최소 12개월 이상 deprecated된 API 제거
- 업그레이드 전 브로커 버전 2.1 이상 필요
- 명확한 업그레이드 경로 제시 (KIP-1124)

---

## 5\. Kafka Streams & Connect 개선

### Kafka Streams

**Foreign Key 추출 개선 (KIP-1104)**

- 키와 값 모두에서 Foreign Key 추출 가능
- 조인 작업 간소화 및 스토리지 오버헤드 감소

**커스텀 프로세서 래핑 (KIP-1112)**

- `ProcessorWrapper` 인터페이스 도입
- 횡단 관심사(Cross-cutting concerns) 로직 적용 간편화

**프로덕션 예외 핸들링 (KIP-1065)**

- `ProductionExceptionHandler` 에 "RETRY" 옵션 추가
- 재시도 루프 제어 및 에러 복구 전략 유연성 향상

**향상된 메트릭 (KIP-1091)**

- 각 StreamThread와 클라이언트 인스턴스의 상태 메트릭 추가
- 애플리케이션 상태에 대한 상세한 가시성 제공

### Kafka Connect

**사용자 내부 토픽 복제 (KIP-1074)**

- MirrorMaker 2에서 `.internal` 또는 `-internal` 접미사 토픽 복제 가능
- 커스텀 복제 정책 없이 비즈니스 토픽 복제

**하트비트 복제 비활성화 (KIP-1089)**

- MirrorSourceConnector에서 하트비트 토픽 복제 선택적 비활성화
- 여러 커넥터 사용 시 중복 복제 방지

**Jakarta EE 10 업그레이드 (KIP-1032)**

- Java 17 필수 요구사항
- 현대적인 Jakarta EE 프레임워크와의 호환성 향상

---

## 6\. Kafka 4.0으로의 마이그레이션

### 업그레이드 전 체크리스트

1. **버전 요구사항 확인**
	- 브로커: 2.1 이상 버전에서 업그레이드
		- Java: Clients(Java 11), Brokers(Java 17) 준비
2. **KRaft 모드 마이그레이션**
	- Kafka 4.0은 **KRaft 모드만 지원**
		- ZooKeeper 모드 완전 제거
		- 메타데이터 버전 최소 3.3.x 이상 필요
3. **Deprecated API 확인**
	- 12개월 이상 deprecated된 API 제거됨
		- 애플리케이션 코드에서 구 API 사용 여부 점검
4. **로깅 설정 변환**
	- Log4j 설정을 Log4j2 형식으로 변환
		- `log4j-transform-cli` 도구 활용

### 업그레이드 경로

**권장 순서**
1\. 개발 환경에서 테스트
2\. 브로커를 먼저 업그레이드 (Java 17)
3\. 클라이언트 및 애플리케이션 업그레이드 (Java 11)
4\. 새로운 컨슈머 프로토콜 점진적 활성화
5\. Share Group 기능 테스트 (선택사항)

**주의사항**

- KRaft 모드로의 전환은 신중하게 계획
- 롤백 불가능한 지점 이후 주의 필요
- 상세한 내용은 [공식 업그레이드 가이드](https://kafka.apache.org/40/getting-started/upgrade/) 참고

---

## 마치며

Apache Kafka 4.0은 단순한 버전 업그레이드가 아닌, **아키텍처의 근본적인 혁신** 을 이룬 릴리즈입니다. ZooKeeper 의존성 제거는 10년 이상 지속된 관계의 종료를 의미하지만, 동시에 Kafka가 더욱 자립적이고 확장 가능한 플랫폼으로 진화했음을 보여줍니다.

차세대 컨슈머 프로토콜과 큐 시맨틱 지원은 Kafka의 활용 범위를 더욱 넓혀, 다양한 메시징 패턴을 하나의 통합 플랫폼에서 처리할 수 있게 합니다. 175명의 기여자가 참여한 이번 릴리즈는 오픈소스 커뮤니티의 힘을 다시 한번 증명했습니다.

Kafka 4.0으로의 마이그레이션을 계획하고 있다면, 충분한 테스트와 단계적 접근을 통해 안전하게 전환하시기 바랍니다. 새로운 기능들을 활용하여 더욱 견고하고 효율적인 이벤트 스트리밍 아키텍처를 구축하시길 바랍니다.

---

## 참고 자료

- [Apache Kafka 4.0 Release Notes](https://archive.apache.org/dist/kafka/4.0.0/RELEASE_NOTES.html)
- [Kafka 4.0: KRaft Simplifies Architecture - InfoQ](https://www.infoq.com/news/2025/04/kafka-4-kraft-architecture/)
- [Apache Kafka 4.0 Release Blog - Confluent](https://www.confluent.io/blog/latest-apache-kafka-release/)
- [KIP-848: New Consumer Rebalance Protocol](https://cwiki.apache.org/confluence/x/HhD1D)
- [KIP-932: Queues for Kafka](https://cwiki.apache.org/confluence/x/4hA0Dw)

[![profile](https://velog.velcdn.com/images/hyungki26/profile/9b700248-5e2a-4e48-a985-06fd3ebcdd9b/image.jpeg)](https://velog.io/@hyungki26/posts)

[GarionNachal](https://velog.io/@hyungki26/posts)

AI를 꿈꾸는 BackEnd개발자

이전 포스트

### [Quorum과 Kafka의 Quorum 동작 방식 완벽 가이드](https://velog.io/@hyungki26/Quorum%EA%B3%BC-Kafka%EC%9D%98-Quorum-%EB%8F%99%EC%9E%91-%EB%B0%A9%EC%8B%9D-%EC%99%84%EB%B2%BD-%EA%B0%80%EC%9D%B4%EB%93%9C)

다음 포스트

### [Kafka MirrorMaker 2란?](https://velog.io/@hyungki26/Kafka-MirrorMaker-2%EB%9E%80)

#### 0개의 댓글

관심 있을 만한 포스트

#### [Kafka 시스템 구조 알아보기](https://velog.io/@jwpark06/Kafka-%EC%8B%9C%EC%8A%A4%ED%85%9C-%EA%B5%AC%EC%A1%B0-%EC%95%8C%EC%95%84%EB%B3%B4%EA%B8%B0)

\- Kafka 관련 이전 포스팅 1) AWS EC2에 Kafka 설치하기 Kafka를 공부하다 보면 여러 용어들을 볼 수 있습니다. 어딘지 모르게 익숙한 용어인 Cluster 부터 생소한 Zookeeper나 Topic 같은 용어들이 있습니다. 실제 데이터 처리를 할...

2021년 4월 16일·1개의 댓글

[by **망7H**](https://velog.io/@jwpark06/posts)

14

[![](https://velog.velcdn.com/images/songyuheon/post/ac077d94-8535-4d1c-b738-c5c406376964/image.png)](https://velog.io/@songyuheon/Apache-Kafka-%EC%84%A4%EC%B9%98-%EB%B0%8F-%EC%8B%A4%ED%96%89-Windows-11-%ED%99%98%EA%B2%BD)

#### [Apache Kafka 설치 및 실행 (Windows 11 환경)](https://velog.io/@songyuheon/Apache-Kafka-%EC%84%A4%EC%B9%98-%EB%B0%8F-%EC%8B%A4%ED%96%89-Windows-11-%ED%99%98%EA%B2%BD)

이 글에서는 Windows 11 환경에서 Apache Kafka 2.8.0 버전을 설치하고 실행하는 방법을 상세하게 설명합니다. 설치 순서는 Kafka 다운로드, 파일 구성 확인, Zookeeper 및 Kafka 실행, 그리고 Kafka Topic 생성 순입니다Apac...

2023년 10월 27일·0개의 댓글

[by **song yuheon**](https://velog.io/@songyuheon/posts)

1

[![](https://velog.velcdn.com/images/ehdrms2034/post/1dc99179-eed9-4f84-a339-193985bdde5e/image.png)](https://velog.io/@ehdrms2034/Kafka-3%EC%9E%A5-%EC%B9%B4%ED%94%84%EC%B9%B4-%EA%B8%B0%EB%B3%B8-%EA%B0%9C%EB%85%90-%EC%84%A4%EB%AA%85-1)

#### [\[Kafka\] 3장 카프카 기본 개념 설명 (1)](https://velog.io/@ehdrms2034/Kafka-3%EC%9E%A5-%EC%B9%B4%ED%94%84%EC%B9%B4-%EA%B8%B0%EB%B3%B8-%EA%B0%9C%EB%85%90-%EC%84%A4%EB%AA%85-1)

이 포스팅은 최원영 저자님의 아파치 카프카 어플리케이션 프로그래밍 with 자바를 기반으로 정리한 포스팅입니다.카프카 클라이언트와 데이터를 주고받기 위해 사용되는 주체데이터를 분산 저장하여 장애가 발생하더라도 안전하게 사용할 수 있도록 도와주는 어플리케이션하나의 서버...

2021년 6월 1일·1개의 댓글

[by **600g (Kim Dong Geun)**](https://velog.io/@ehdrms2034/posts)

4

[![](https://velog.velcdn.com/images/hanblueblue/post/308b442e-4c5f-4dfe-b6dc-5908ca6a9af5/kafka-logo-600x390.jpg)](https://velog.io/@hanblueblue/%EB%B2%88%EC%97%AD-kafka)

#### [\[번역\] kafka](https://velog.io/@hanblueblue/%EB%B2%88%EC%97%AD-kafka)

APACHE kafka를 번역합니다.

2020년 7월 12일·0개의 댓글

[by **rin**](https://velog.io/@hanblueblue/posts)

4

[![](https://velog.velcdn.com/images/hyeondev/post/35aa8bef-a1bc-4ed9-b5f1-c03e2ec0ed32/img.png)](https://velog.io/@hyeondev/Apache-Kafka-%EC%9D%98-%EA%B8%B0%EB%B3%B8-%EC%95%84%ED%82%A4%ED%85%8D%EC%B3%90)

#### [Apache Kafka 의 기본 아키텍쳐](https://velog.io/@hyeondev/Apache-Kafka-%EC%9D%98-%EA%B8%B0%EB%B3%B8-%EC%95%84%ED%82%A4%ED%85%8D%EC%B3%90)

아파치 카프카(Apache Kafka)는 분산 메시지 스트리밍 플랫폼이며 데이터 파이프 라인을 구성할 때 많이 사용된다. 카프카 학습의 기반이 될 수 있는 내용을 위주로 정리해보았다.

2020년 10월 27일·0개의 댓글

[by **juhyeon**](https://velog.io/@hyeondev/posts)

10

[![](https://velog.velcdn.com/images/jaehyeong/post/33295fa0-a89f-47cd-b9f2-6ed0a07d36a1/What_is_Apache_Kafka_.png)](https://velog.io/@jaehyeong/Apache-Kafka%EC%95%84%ED%8C%8C%EC%B9%98-%EC%B9%B4%ED%94%84%EC%B9%B4%EB%9E%80-%EB%AC%B4%EC%97%87%EC%9D%B8%EA%B0%80)

#### [Apache Kafka(아파치 카프카)란 무엇인가?](https://velog.io/@jaehyeong/Apache-Kafka%EC%95%84%ED%8C%8C%EC%B9%98-%EC%B9%B4%ED%94%84%EC%B9%B4%EB%9E%80-%EB%AC%B4%EC%97%87%EC%9D%B8%EA%B0%80)

기존 링크드인의 데이터 처리 시스템은 각 파이프라인이 파편화되고 시스템 복잡도가 높아 새로운 시스템을 확장하기 어려운 상황이였음기존 메시징 큐 시스템인 ActiveMQ를 사용했지만, 링크드인의 수많은 트래픽과 데이터를 처리하기에는 한계가 있었음이로 인해 새로운 시스템의...

2021년 7월 18일·3개의 댓글

[by **jaehyeong.an\_**](https://velog.io/@jaehyeong/posts)

24

[![](https://velog.velcdn.com/images/joyfulbean/post/742a7cd1-4941-47df-8b1f-91d7e3798e06/image.jpg)](https://velog.io/@joyfulbean/Apache-Kafka-Zookeeper-%EC%A0%9C%EA%B1%B0-%EC%9D%B4%EC%9C%A0)

#### [Apache Kafka Zookeeper 제거 이유](https://velog.io/@joyfulbean/Apache-Kafka-Zookeeper-%EC%A0%9C%EA%B1%B0-%EC%9D%B4%EC%9C%A0)

주키퍼를 없앤 카프카

2022년 8월 4일·0개의 댓글

[by **Joyfulbean**](https://velog.io/@joyfulbean/posts)

1

[![](https://velog.velcdn.com/images/seungyeon/post/ba6697fd-010d-4abf-acc1-bb24834cbf65/image.png)](https://velog.io/@seungyeon/%EC%B9%B4%ED%94%84%EC%B9%B4-%EB%AC%B4%EC%97%87%EC%9D%B4%EA%B3%A0-%EC%99%9C-%ED%95%84%EC%9A%94%ED%95%A0%EA%B9%8C)

#### [\[카프카\] 무엇이고, 왜 필요할까?](https://velog.io/@seungyeon/%EC%B9%B4%ED%94%84%EC%B9%B4-%EB%AC%B4%EC%97%87%EC%9D%B4%EA%B3%A0-%EC%99%9C-%ED%95%84%EC%9A%94%ED%95%A0%EA%B9%8C)

배경지식 MOM(Message Oriented Middleware): 메시지 지향 미들웨어 1.1 다른 미들웨어 종류: RPC 방식, ORB 방식 1.2 미들웨어: 어플리케이션들을 연결시켜, 서로 데이터를 교환할 수 있게 해주는 소프트웨어 1.3 메시지 지향: 메시...

2021년 5월 5일·0개의 댓글

[by **Seungyeon Choi**](https://velog.io/@seungyeon/posts)

9

[![](https://velog.velcdn.com/images/pha2616/post/372e03e9-fb5b-483e-8ac3-217165e0565b/p4o3xoj.jpeg)](https://velog.io/@pha2616/Apache-Kafka-bootstrap.server)

#### [\[Apache Kafka\] bootstrap.server](https://velog.io/@pha2616/Apache-Kafka-bootstrap.server)

개요 Kafka Command line 명령어 중, consumer 생성 명령어

2021년 12월 21일·0개의 댓글

[by **박현아**](https://velog.io/@pha2616/posts)

2

[![](https://velog.velcdn.com/images/ehdrms2034/post/9ed23cb6-cb80-48b8-84bd-7c7333a14525/image.png)](https://velog.io/@ehdrms2034/%EC%B9%B4%ED%94%84%EC%B9%B4-%EC%BB%A8%EC%8A%88%EB%A8%B8-%EC%83%81%EC%84%B8%EA%B0%9C%EB%85%90)

#### [카프카 컨슈머 상세개념](https://velog.io/@ehdrms2034/%EC%B9%B4%ED%94%84%EC%B9%B4-%EC%BB%A8%EC%8A%88%EB%A8%B8-%EC%83%81%EC%84%B8%EA%B0%9C%EB%85%90)

카프카는 처리량을 늘리기 위해 파티션 개수 와 컨슈머 개수 를 늘려서 운영할 수 있음.파티션과 컨슈머 개수를 동일하게 맞추는 것이 가장 좋은 카프카 운영법파티션의 데이터를 처리하는 방법은 다수의 프로세스 를 운영하거나, 다수의 쓰레드 를 운영하는 방법이 존재자바는 Th...

2021년 7월 20일·0개의 댓글

[by **600g (Kim Dong Geun)**](https://velog.io/@ehdrms2034/posts)

1

[![](https://velog.velcdn.com/images/king3456/post/2372a076-727b-4feb-9690-378a7d5cd544/%E1%84%89%E1%85%B3%E1%84%8F%E1%85%B3%E1%84%85%E1%85%B5%E1%86%AB%E1%84%89%E1%85%A3%E1%86%BA%202021-02-14%20%E1%84%8B%E1%85%A9%E1%84%92%E1%85%AE%201.52.40.png)](https://velog.io/@king3456/Apache-Kafka-%EA%B8%B0%EB%B3%B8%EA%B0%9C%EB%85%90)

#### [Apache Kafka - 기본개념](https://velog.io/@king3456/Apache-Kafka-%EA%B8%B0%EB%B3%B8%EA%B0%9C%EB%85%90)

일반적인 IT 시스템 기반에 서비스를 제공하는 플랫폼 등에서 발생되는 데이터를 처리한다고 가정해보자. 아래와 같이 시스템이 복잡해짐에 따라 데이터를 제공하는 시스템(=Source System)의 수와 데이터를 제공받는 시스템(=target system)의 수가 증가함에...

2021년 2월 14일·0개의 댓글

[![](https://velog.velcdn.com/images/cobin_dev/post/6ce1a2c9-d79c-4aa7-87e3-52e63f2643ce/image.jpg)](https://velog.io/@cobin_dev/Kafka%EC%99%80-Zookeeper%EC%9D%98-%EA%B0%9C%EB%85%90)

#### [Kafka와 Zookeeper의 개념](https://velog.io/@cobin_dev/Kafka%EC%99%80-Zookeeper%EC%9D%98-%EA%B0%9C%EB%85%90)

카프카(Kafka)는 Apache 소프트웨어 재단에서 개발한 분산형 스트리밍 플랫폼이다. 주로 대용량의 실시간 로그 데이터를 처리하는 데 사용된다. 카프카는 데이터를 여러 프로듀서에서 생성하여 여러 컨슈머에서 소비할 수 있는 효율적인 방법을 제공한다. 기존 데이터 시스...

2024년 5월 30일·1개의 댓글

[![Powered by GraphCDN, the GraphQL CDN](https://i.imgur.com/BMhDSUt.png)](https://graphcdn.io/?ref=powered-by)
