---
title: "Redis&Kafka를 활용한 선착순 쿠폰 이벤트 개발기 (feat. 네고왕)"
source: "https://techblog.gccompany.co.kr/redis-kafka%EB%A5%BC-%ED%99%9C%EC%9A%A9%ED%95%9C-%EC%84%A0%EC%B0%A9%EC%88%9C-%EC%BF%A0%ED%8F%B0-%EC%9D%B4%EB%B2%A4%ED%8A%B8-%EA%B0%9C%EB%B0%9C%EA%B8%B0-feat-%EB%84%A4%EA%B3%A0%EC%99%95-ec6682e39731"
author:
  - "[[김지황Paden(페이든) / 유저혜택개발팀]]"
published: 2022-07-08
created: 2026-11-02
description: "Redis&Kafka를 활용한 선착순 쿠폰 이벤트 개발기 (feat. 네고왕) 안녕하세요. 유저혜택개발팀 쿠폰 백앤드 개발자 페이든입니다. 이 글에서는 여기어때 …"
tags:
  - "clippings"
---

> [!summary]
> Yeogi Eottae's coupon team rebuilt first-come coupon events (Time Attack, 네고왕) on Redis and Kafka after the old RDB-based quantity check risked over-issuance and the monolith could spread a coupon outage to the whole service. The requirements were a daily cap, no over-issuance and one coupon per user. INCR handled the cap but not duplicates. A Redis SET handled duplicates but still over-issued under load when SCARD and SADD ran separately, so they wrapped both in a MULTI/EXEC transaction, noting it has no rollback and was used on standalone Redis rather than cluster. Load tests then showed the coupon INSERT hammering the shared write DB, so the API now only decides eligibility and publishes a zero-payload `TimeAttackCouponIssue` message (3 partitions, 3 consumers) that a Kafka app turns into the actual insert. 네고왕 (7,000 coupons a day at 1 p.m., Feb 24-28, 2022) peaked at 28,800+ concurrent users and 3,600+ TPS, with stable DB CPU and no over-issuance.

> 안녕하세요. 유저혜택개발팀 쿠폰 백앤드 개발자 페이든입니다.
>
> 이 글에서는 여기어때 서비스의 성수기나 네고왕 등의 선착순 쿠폰 지급 이벤트와 같이 동시에 많은 사용자가 접속하는 상황에도 대응 가능한 시스템 설계 경험을 공유해 드리고자 합니다.

## 들어가며

여기어때 유저혜택개발팀은 기존의 Monolithic 구조에서 벗어난 MSA 기반 신규 쿠폰 플랫폼을 10개월간의 개발 과정을 통해 작년 7월 오픈하였습니다.

고객 관점에서의 **신규 쿠폰 플랫폼** 은 기존의 쿠폰 시스템 대비 사용/지급/비용주체 등을 더욱 세분화 하여 쿠폰을 제공할 수 있습니다. 그리고 Event Driven Architecture 기반 Kafka를 활용하여 다양한 사용자 이벤트(체크아웃/예약시점,,,) 시점에도 쿠폰 지급이 가능합니다. 그리하여 쿠폰 발급과 사용에 대한 사용자 경험을 향상시킬 수 있습니다.

또한 관리자 관점에서도 실시간 대시보드 제공을 통해 쿠폰 시스템 안정성을 높일 수 있는 프로젝트입니다.

현재는 매일 **3000+** 종의 쿠폰이 생성되고 **200k+** 장의 쿠폰이 실제 사용자들에게 지급되고 있는 등, 신규 쿠폰 플랫폼을 통해 여기어때 고객께 다양한 혜택을 제공하고 있습니다. 이 플랫폼 오픈 이후 ‘타임어택’부터 최근의 ‘네고왕’까지 몇 번의 이벤트가 있었는데 정말 많은 고객께서 참여해 주셨습니다.

## 기존 선착순 이벤트 문제점😱

기존의 쿠폰 시스템을 활용한 선착순 이벤트에서는 RDB에 의존하여 수량 체크가 이루어졌기 때문에, 동시성 이슈로 인하여 선착순 쿠폰이 초과 지급될 위험이 있었고, Monolithic한 시스템 구조로 인해 쿠폰 시스템 장애 발생 시 여기어때 서비스 전체에 장애 전파될 가능성도 있는 상황이었습니다.

이를 해결하기 위해 신규 쿠폰 플랫폼을 개발하면서 선착순 이벤트 처리 프로세스의 개선 작업을 진행하게 되었고, 이와 관련된 고민의 내용과 처리 프로세스에 대하여 공유해 드리도록 하겠습니다.

## 선착순 이벤트 요구사항

> 1\. 이벤트 기간 동안, 매일 특정 시간 오픈하며 총 **지급 수량** 을 한정한다.
> 2\. 쿠폰의 지급 수량은 당일 정해진 양을 **초과** 해서는 안된다.
> 3\. 쿠폰은 **1인당 1장** 만 지급한다.

저희는 동시성 이슈를 해결하고 위 요구사항을 충족하기 위해 Redis를 활용하기로 하였습니다. 그 이유는, Redis가 단일 스레드 기반 커맨드를 순차적으로 실행하고 결과를 전달하기 때문에 동시성 이슈를 해결할 수 있으며, 다양한 데이터 타입과 커맨드를 제공해 주기 때문에 모든 요구사항들을 만족시킬 수 있을 거라 생각했기 때문입니다.

## Redis 를 활용한 선착순 이벤트! 고민의 흔적들 🕐

### 1) INCR 커맨드를 활용한 지급 재고 관리

[INCR 커맨드](https://redis.io/commands/incr/) 는 특정키의 값을 1씩 증가시키는 커맨드입니다. 시간 복잡도 O(1)를 가지며 빠르게 지급 재고 수량을 증가시키며, 재고를 초과 했을 때에는 지급되지 않도록 처리가 가능합니다.

```rb
-- KEY 정보
쿠폰정책ID : 쿠폰 정책 PK ID
일자별ID : 일자별 이벤트 시간 PK ID
key : coupon:time-attack:{쿠폰정책ID}:date-time:{일자별ID}:issued:count-- 최초 지급 개수 0개로 셋팅
redis> SET coupon:time-attack:1:date-time:1:issued:count 0
OK-- 지급 개수 조회
redis> GET coupon:time-attack:1:date-time:1:issued:count
(integer)1-- 지급 가능 여부 확인
if(지급 개수 < 전체 지급 개수) {
  INCR coupon:time-attack:1:date-time:1:issued:count // 지급 개수++
  실제 사용자 쿠폰 지급 처리 // RDB INSERT
}
```

요구 사항 1번과 2번 항목은 INCR 커맨드를 통해 처리할 수 있었지만, 3번 항목의 중복 지급 관련해서는 INCR 커맨드에서 처리가 불가능합니다.

INCR 커맨드를 활용할 경우에는 개수의 처리는 가능하지만, 실제 지급받은 사용자들의 정보를 별도 Redis or RDB에 저장해야 하는 이슈가 존재합니다.

### 2) SET 자료형을 통한 지급 재고 관리

쿠폰을 **1인당 1장** 만 지급해야하는 세 번째 요구사항을 만족시키기 위해 Redis의 [SET 자료형](https://redis.io/docs/manual/data-types/data-types-tutorial/#sets) 을 선택하기로 하였습니다.

SET 자료형은 JAVA의 SET 자료형과 유사하게 중복값을 제거해 줍니다. Redis에는 제공하는 자료형 중 순서 처리가 가능한 Sorted SET도 고려하였지만, 이벤트 요구사항에 Ordering 조건이 없기 때문에 SET 자료형이 더 적합하다고 생각했습니다.

SET 자료형을 활용해 사용자의 유니크한 userId를 value로 사용하여 기존에 이미 다운로드 받았는지 확인하고, 중복 지급을 막을 수 있게 되었습니다.

```rb
-- KEY 정보
쿠폰정책ID : 쿠폰 정책 PK ID
일자별ID : 일자별 이벤트 시간 PK ID-- VALUE 정보
사용자ID : 사용자 PK IDkey : coupon:time-attack:{쿠폰정책ID}:date-time:{일자별ID}:issued:users
value : 사용자 PK ID-- 실시간 지급 수량 확인
redis> SCARD coupon:time-attack:1:date-time:1:issued:users
(integer)0-- 지급 가능 여부 확인
if(지급 개수 < 전체 지급 개수) {
  SADD coupon:time-attack:1:date-time:1:issued:users 1 // 지급 처리
  실제 사용자 쿠폰 지급 처리 // RDB INSERT
}-- 실시간 지급 수량 확인
redis> SCARD coupon:time-attack:1:date-time:1:issued:users
(integer)1
```

저희는 SCARD 커맨드를 통해 이벤트 시작 시 지급 총 수량을 체크하고 SADD 커맨드를 통해서 지급 처리하는 방식으로 개발하고 성능테스트를 진행해 보았습니다. 그런데 이 방식에서는 트래픽이 몰릴 경우 동시성 이슈를 야기하며 아래 그림처럼 **초과 지급** 이 발생하는 케이스를 확인했습니다.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*W_bkV4N7Ta1MDUGvu2Mwdw.png)

초과 지급 발생 Case

이를 해결하고자 Redis의 Transaction을 활용하기로 하였습니다. Redis Transaction은 여러 개의 커맨드 묶음에 대하여 순차 처리를 보장합니다.

### 3) SET 자료형 + Redis Transaction 을 통한 지급 재고 관리

Redis에는 [Transaction](https://redis.io/docs/manual/transactions/) 관련 키워드들을 제공해주고 있습니다. 그 중에서 MULTI, EXEC 키워드를 통해 현재 지급 개수와 이미 지급 받은 사용자를 체크하는 커맨드를 Transaction 단위로 묶어서 처리하도록 하였습니다.

*( Redis Transaction의 경우 기존 RDB Transaction과 다르게* [*Rollback*](https://redis.com/blog/you-dont-need-transaction-rollbacks-in-redis/) *이 불가능한 케이스가 존재하기에, 이 부분은 별도 Rollback 로직을 구현해야 합니다.
그리고 Cluster Redis 환경에서는 Transaction이 지원되지 않고, Standalone Redis에서만 Transaction 지원 가능 한 점 참고 바랍니다.)*

```rb
-- KEY 정보
쿠폰정책ID : 쿠폰 정책 PK ID
일자별ID : 일자별 이벤트 시간 PK ID-- VALUE 정보
사용자ID : 사용자 PK IDkey : coupon:time-attack:{쿠폰정책ID}:date-time:{일자별ID}:issued:users
value : 사용자 PK ID-- 트랜잭션 시작
redis> MULTI-- 실시간 지급 수량 확인
redis> SCARD coupon:time-attack:1:date-time:1:issued:users
(integer)1-- 쿠폰 지급 처리 / 사용자ID : 1
redis> SADDcoupon:time-attack:1:date-time:1:issued:users 1
(integer)1 // 해당 value가 존재하면 0 아니면 1 리턴-- 트랜잭션 실행
redis> EXEC
```

위의 커맨드 묶음을 Transaction을 통해서 처리하고 해당 결과값을 통해 현재 지급 가능 상태인지, 이미 지급 받은 사용자인지 확인할 수 있었습니다. 또한 이를 통해 사용자에게 쿠폰 지급 가능 여부를 판단할 수 있습니다.

아래에서는 이를 처리하기 위한 Transaction 처리 코드와 Operation에 대하여 공유 드립니다. 이 내용은 Transaction 처리 관련한 코드이며, 실제 Redis Operation 커맨드의 경우 수량 조회 및 지급 처리 (SCARD+SADD)의 조합입니다.

## 동시성 이슈는 해결 완료! 성능은 어떨까? 🤣

Redis를 통해 동시성 이슈를 해결하고, 신난 마음에 성능 테스트 진행하였습니다.

저희는 테스트 장비를 상용 환경과 유사하게 설정하고, nGrinder를 통해 성능 테스트를 착수하였습니다. 이 테스트를 진행하며 모니터링한 결과… 실제 쿠폰을 지급하는 Insert Query가 선착순 쿠폰 지급 API 비즈니스 로직 내에서 이루어지기 때문에 Write DB에 부하가 발생하는 점을 확인했습니다.

Write DB의 경우 이벤트뿐만 아니라 기존 쿠폰 서비스에서도 사용하고 있기 때문에, 이벤트 트래픽의 영향으로 **장애 전파** 가 될 수 있다는 문제점을 파악하였습니다.

Read DB의 경우 API의 트래픽이 몰리는 경우를 대비하여 Scale-out을 통해 트래픽 분산 및 대응이 가능하지만, Write DB의 경우 Scale-up을 통해 대비를 하더라도 [Single Point of Failure](https://ko.wikipedia.org/wiki/%EB%8B%A8%EC%9D%BC_%EC%9E%A5%EC%95%A0%EC%A0%90) 가 발생할 경우 쿠폰 서비스 전체에 영향을 주게 됩니다.

![](https://miro.medium.com/v2/resize:fit:1102/format:webp/1*ujtUq-jhOBPC9UhaWfAsmA.png)

AWS Aurora Reader scale-out

이를 해결하기 위해 EDA 기반 Kafka를 활용하여 쿠폰 Kafka 애플리케이션에서 쿠폰 지급 처리하도록 변경하였습니다. 쿠폰 Kafka 애플리케이션은 아래 Topic을 Consume하여 쿠폰 지급하도록 작업하였습니다.

선착순 이벤트 진행 시 Topic 정보는 아래와 같습니다.

```rb
-- Kafka Topic 정보
Topic 명 : TimeAttackCouponIssue
Body 정보 :
{
 policyId: 1,
 userId: 1,
 issuedAt: "2022–02–26T11:31:42"
}
```

Topic Body의 내용은 Zero-Payload 방식으로 데이터를 전달하여 코드 및 아키텍처의 복잡성을 낮추었습니다. 해당 쿠폰 정책 ID(policyId), 사용자 ID(userId) 값을 통해 Kafka 애플리케이션에서 지급 처리하였습니다.

해당 토픽은 Partition 3, Replica 3으로 설정되어 있고, 쿠폰 Kafka Consumer 애플리케이션은 Partition 개수만큼 3대로 운영하고 있습니다.

> 저희 플랫폼개발실의 Kafka 구성은 앞서 파오리가 작성한 “[Apache Kafka를 사용하여 EDA 적용하기](https://techblog.gccompany.co.kr/apache-kafka%EB%A5%BC-%EC%82%AC%EC%9A%A9%ED%95%98%EC%97%AC-eda-%EC%A0%81%EC%9A%A9%ED%95%98%EA%B8%B0-bf263c79efd0)”에 자세히 설명되어 있으니, 관심 있으신 분들은 이 글도참고 바랍니다.

이를 통해 기존의 RDB 의존적으로 진행되며 일부 염려를 품고 있던 선착순 시스템에서 벗어나 Redis&Kafka를 활용하여 아래와 같은 구성으로 이벤트를 진행하도록 설계하였습니다.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*NZCbFv_crZQmbEnIxYWaMQ.png)

이벤트 처리 구성도

이를 통해 실제 이벤트 서비스 API가 DB에 접근하지 않고 지급 가능 여부만 판단하여 고객에게 응답을 주기 때문에 처리 속도가 개선되었고, 사용자 경험 또한 향상되는 결과를 얻을 수 있었습니다.

*그리고 이벤트 진행 중, 지급 성공 응답과 실제 쿠폰 지급 처리 사이에 Delay가 발생할 수 있기 때문에, 이 부분은 이벤트 기획 협의를 통해서 적절한 문구로 고객에게 안내 하였습니다.*

## 과연 실제 이벤트 당시 상황은? 💻

> 최근에 진행한 네고왕 이벤트를 예시로 당시의 쿠폰 시스템 상황에 대하여 말씀드리겠습니다.

[네고왕 이벤트](https://youtu.be/e-q1vg57VEI) 는 진행 기간(2022.02.24~28)동안 매일 오후 1시에 7,000장의 쿠폰을 선착순으로 지급하는 행사였습니다.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/0*IZcuw3dL_BFiGNjJ.jpg)

명불허전 네고왕 답게 역대급 트래픽을 기록하였고 오픈 당일 5만명 이상의 사용자들이 신규 회원 가입하고 선착순 쿠폰을 받으러들 오셨어요!

이벤트 진행 중 RDB는 선착순 쿠폰 지급 프로세스에서 격리했기 때문에, 아래와 같이 안정적인 CPU 사용률을 보여주었습니다.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*_TOwB7I7d3n1FH6HgzR0xg.png)

쿠폰 DB 모니터링

그리고 애플리케이션 상태도 트래픽은 늘어났지만, CPU 사용률 및 응답속도가 안정적인 모습을 보여주고 있습니다.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*VNBsUqf8zYPc8uRhddImKw.png)

Application Pinpoint 모니터링

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*VRNuQ369PhUBHcE6aA5ObQ.png)

Application CPU Usage

이렇게 네고왕 이벤트는
순간 최대 접속자 **28800+** 명, TPS **3600+** 의 트래픽에도 무사히 끝마칠 수 있었습니다👏 기존 쿠폰 시스템이었다면 상당히 염려가 되었을 쿠폰 초과 지급 사례도 찾아볼 수 없었습니다.

## 남은 To-Do-List!

지금까지는 특정 이벤트에만 Redis&Kafka를 활용하였는데, 향후에는 모든 이벤트에 적용하고자 이벤트 GW 분리 작업을 진행하고 있습니다. 상대적으로 준비 기간이 짧은 숙박대전, 놀이공원 할인대전 등의 이벤트에서도 위의 구조를 적용한다면 보다 많은 사용자 트래픽에도 안정적으로 대응할 수 있을 것으로 생각합니다.

## 마무리

선착순 쿠폰 이벤트 진행 중에 저와 저희 팀에서 고민했던 내용을 작성해 보았습니다. 읽어주셔서 감사드리며, 선착순 처리에 관하여 고민이 있으신 분들에게 도움이 되었으면 합니다.👍

그리고 여기어때 서비스를 발전시키고 함께 성장하고 싶은신 개발자분들의 많은 [지원](https://www.recruit-gccompany.co.kr/) 부탁드릴게요!

감사합니다.
