---
title: "Redis Pub/Sub을 활용한 쿠폰 발급 비동기 처리 | 올리브영 테크블로그"
source: "https://oliveyoung.tech/2023-08-07/async-process-of-coupon-issuance-using-redis/"
author:
published: 2023-08-07
created: 2026-11-10
description: "올리브영에서 쿠폰 발급 프로세스를 어떻게 개선 했는지 알아봅시다."
tags:
  - "clippings"
---

> [!summary]
> Olive Young's coupon squad moved first-come coupon issuance for its 0:00 and 12:00 sale drops from a synchronous flow to a separate worker. Plain Redis Pub/Sub failed stress tests twice: every subscribed worker processed each message, so four workers issued a coupon four times, and after routing each message to one chosen worker, coupons went unissued because Pub/Sub does not guarantee delivery. The final design uses Pub/Sub only to pick a worker's serial number and carries the data in a per-worker Redis List (RPush, then periodic size check and LPop) before inserting into the main DB. The June 2023 sale reached 2.2x the March peak of coupons issued per minute, with all coupons gone in 1-2 minutes.

[Tech](https://oliveyoung.tech/categories/tech/) 2023.08.07

## Redis Pub/Sub을 활용한 쿠폰 발급 비동기 처리

올리브영에서 쿠폰 발급 프로세스를 어떻게 개선 했는지 알아봅시다.

[Coupon](https://oliveyoung.tech/tags/coupon/) [Redis](https://oliveyoung.tech/tags/redis/) [async](https://oliveyoung.tech/tags/async/)

안녕하세요.️ 쿠폰스쿼드 백엔드 개발자 어푸입니다!

쿠폰 스쿼드에서는 올리브영을 방문하시는 많은 고객님이 안정적으로 쿠폰 서비스를 받으실 수 있도록 개선 작업을 진행하고 있습니다.

지난번 레이 님이 [올리브영 쿠폰 발급 개선 이야기](https://oliveyoung.tech/2022-09-28/Oliveyoung-Coupon-Count-Moving-Redis/) 를 통해

Redis 저장소를 사용하여 선착순 쿠폰 발급 수량 조회 개선에 대한 이야기를 해주셨는데요.

이번에는 Redis Pub/Sub을 활용하여 쿠폰 발급을 비동기로 처리하고 그로 인해 개선된 쿠폰 발급 서비스에 관해 이야기해 보려고 합니다.

---

## 1년에 4번 찾아오는 올영세일.. 선착순 쿠폰을 받아보셨나요?

올영 세일 기간에는 0시, 12시 선착순 쿠폰 다운로드 이벤트를 진행하고 있습니다.

해당 시간대에 접속한 사용자 수가 늘어난 만큼 트래픽이 몰리면서 쿠폰을 다운로드 받는데 걸리는 대기 시간이 증가하게 되고,

이는 좋지 못한 사용자 경험을 제공하게 됩니다.

![](https://oliveyoung.tech/blog-images/2023-08-07/serving.gif)

출처 - [GIPHY](https://giphy.com/gifs/smart-lunch-sos-dwLk9Qb116F3y)

그래서 올리브영 온라인몰에 방문한 사용자들이 지루한 대기시간을 거치지 않고 빠르게 쿠폰을 받으실 수 있도록 개선 작업을 진행했습니다.

---

## 기존 쿠폰 발급 프로세스는 어땠을까요?

![](https://oliveyoung.tech/_img/eec6e19c7cf4591f-1040.webp)

위의 모든 과정이 Sync로 처리되며, 트래픽이 몰리는 경우 쿠폰 발급 과정에서 DB Connection 등의 자원을 많이 점유하게 됩니다.

높은 트래픽 환경에서도 안정적으로 서비스를 제공하기 위해 접속한 사용자가 순서대로 쿠폰 발급을 시도할 수 있도록 제어하고 있으며,

사용자는 본인의 순서가 돌아올 때까지 긴 시간을 대기해야 합니다.

---

## 프로세스를 어떻게 개선할까요?

![](https://oliveyoung.tech/_img/72614d9fef73dadb-1575.webp)

쿠폰 발급에 필요한 유효성 검사까지 기존 로직을 사용하고, 발급 처리는 신규 시스템인 쿠폰 발급 Worker로 위임합니다.

올리브영 온라인몰 ↔ 쿠폰 발급 Worker 사이의 데이터 전달은 Redis Pub/Sub과 Redis의 List 자료구조를 활용했습니다.

---

## Redis Pub/Sub 이란?

![](https://oliveyoung.tech/_img/ad48a3f0357ec02f-1020.webp)

특정 주제(Topic / Channel)를 구독한 구독자에게 메시지를 발행하는 통신 방법으로, publisher가 메시지를 publish 하면

해당 Topic을 구독하고 있는 다수의 subscriber가 메시지를 받을 수 있는 구조입니다.

Redis는 In-Memory 기반이기 때문에 네트워크 통신이 필요한 웹 소켓을 이용하는 것보다 매우 빠르게 메시지를 주고받을 수 있습니다.

다만, 구조가 매우 단순하게 되어 있어서 publish 한 메시지는 따로 보관되지 않으며 subscriber가 수신했는지 확인하지 않습니다.

메시지를 빠르게 보내고 싶을 때, 전송한 메시지를 저장하거나 수신 확인이 필요하지 않으며

100% 전송 보장이 되지 않아도 문제없는 케이스에 사용하기 좋습니다.

예를 들어, 특정한 작업을 반복 수행하는 시스템에 비동기적으로 작업을 보내 처리하도록 하거나

앱 사용자에게 푸시를 발송하도록 하는 과정을 pub/sub 원리로 실행할 수 있습니다.

자세한 내용은 [공식 홈페이지 내용](https://redis.io/docs/latest/develop/pubsub/) 을 참고해 주세요!

---

## Redis Pub/Sub을 쿠폰 발급에 적용해 봅시다!

![](https://oliveyoung.tech/_img/e71e01df7bf63055-1380.webp)

올리브영 온라인몰에서 ‘쿠폰발급’이라는 Topic에 쿠폰 발급 데이터를 publish 하면

‘쿠폰발급’을 구독하고 있는 쿠폰 발급 Worker는 전달받은 쿠폰 발급 데이터를 Main DB에 INSERT 하여 발급 처리를 진행하게 됩니다.

계획한 대로 쿠폰 발급이 잘 진행되었으면 좋았겠지만.. 스트레스 테스트를 진행하면서 두 가지 이슈가 발생했습니다.

### Redis Pub/Sub 적용 후 이슈 첫 번째: 쿠폰 과발급 현상

![](https://oliveyoung.tech/_img/9720a0d9b0578f19-1600.webp)

단일 쿠폰 발급 Worker로 발급 테스트를 진행했을 때는 인지하지 못했던 문제점이 다중 Worker로 스트레스 테스트 중에 발생했습니다.

쿠폰 발급 Worker는 실제 운영환경에서 여러 대가 실행되며, 각 Worker는 쿠폰 발급 정보를 전달해 주는 하나의 Topic을 구독하고 있습니다.

즉, 위의 그림처럼 4대의 Worker가 존재하는 경우 같은 message를 각각 받아 쿠폰 발급 처리 로직을 실행하게 되어,

1건의 쿠폰 발급 데이터가 publish 될 때마다 쿠폰 발급은 4회 실행됩니다.

실제 운영환경에서 이런 일이 발생하면 안 되겠죠?

그래서 올리브영 온라인몰에서 message를 publish 할 때 여러 개의 Worker 중 1개의 Worker를 고르고,

해당 Worker만 message를 받아 쿠폰 발급 처리를 할 수 있도록 로직을 변경했습니다.

### Redis Pub/Sub 적용 후 이슈 두 번째: 쿠폰 미발급 현상

![](https://oliveyoung.tech/_img/c26128fe96b45272-1600.webp)

쿠폰 과발급 문제를 해결하고 나니 이번엔 미발급 현상이 발생했습니다.

미발급 현상을 해결하기 위해 Worker 내부 로직을 Async로 전환해 보고 ThreadPoolSize도 조정해 보았지만, 만족할 만한 효과가 없었습니다.

결국 Redis Pub/Sub의 특징 중 하나인 ‘100% 전송 보장이 되지 않아도 문제없는 케이스에 사용하기 좋다.’ 를 간과한 것이 문제라고 판단하고

데이터 전달 방식에 변화를 줬습니다.

쿠폰 발급 데이터의 유실을 막기 위해 Redis에서 제공하는 List 자료구조를 활용했습니다.

먼저 기존처럼 올리브영 온라인몰에서 여러 개의 Worker 중 1개의 Worker를 골라 ‘일련번호’를 획득합니다.

그리고 list 자료구조로 되어 있는 ‘쿠폰발급 저장소’에 쿠폰 발급 데이터(message)를 RPush 합니다.

쿠폰발급 Worker는 본인의 ‘일련번호’로 채번된 ‘쿠폰발급 저장소’의 크기를 주기적으로 체크하면서, 0보다 크면 LPop 하여 쿠폰 발급 처리를 합니다.

이렇게 하면 쿠폰 발급 데이터의 유실을 막으면서 지정된 1개의 Worker만 쿠폰 발급 처리를 할 수 있게 됩니다!

---

## 최종으로 적용된 쿠폰 발급 로직

![](https://oliveyoung.tech/_img/3f6417891b307666-1520.webp)

자~ 그럼 최종적으로 쿠폰 발급이 어떻게 이루어지는지 정리해 보겠습니다!

위 그림에 있는 번호와 아래 설명을 매칭하여 봐주세요~

1. 쿠폰 발급 Worker가 구동되면 ‘쿠폰발급’ 이라는 Topic에 대한 ‘일련번호’가 생성됩니다. Worker마다 각각의 ‘일련번호’가 할당되어 있습니다.
2. 각 Worker들은 ‘쿠폰발급’이라는 Topic을 구독합니다.
3. 주기적으로 ‘쿠폰 발급 저장소’ List의 크기가 0보다 큰지 확인하고, 0보다 크면 List에서 데이터를 Pop 하여 쿠폰을 발급하는 프로세스가 실행됩니다.

위의 1~3번 과정은 쿠폰 발급을 위해 기본적으로 미리 실행되어 있어야 합니다.

아래 4~8번 과정은 실제 사용자가 쿠폰 발급을 요청했을 때 어떤 흐름으로 동작하는지 설명합니다.

4. 올리브영 온라인몰을 통해 고객이 쿠폰 발급을 요청합니다.
5. 올리브영 온라인몰에서는 각 Worker들이 가지고 있는 ‘일련번호’ 중 1개를 골라서 ‘쿠폰발급’ 이라는 Topic에 publish 합니다.
6. 고객의 쿠폰 발급 데이터를 각 ‘일련번호’마다 할당된 ‘쿠폰 발급 저장소’ list에 RPush 합니다.
7. 6번 과정으로 ‘쿠폰 발급 저장소’의 크기가 0보다 커졌으므로 쿠폰발급 Worker는 해당 list를 LPop하여 쿠폰 발급 데이터를 가져옵니다.
8. 7번에서 가져온 쿠폰 발급 데이터를 온라인몰 Main DB에 INSERT 하여 발급 처리를 완료합니다.

**결론적으로, 여러 Worker 중 어떤 Worker를 통해 쿠폰을 발급할지 결정지어 주는 역할을 Redis Pub/Sub 기능을 활용하여 구현(1개의 ‘일련번호’ 선택)하였고, 실제 쿠폰 발급에 필요한 데이터는 각 Worker 별로 지정된 ‘쿠폰 발급 저장소’에 저장되었다가 쿠폰 발급이 진행됩니다.**

---

## 대망의 2023년 6월 올영세일! 그 결과는??

![](https://oliveyoung.tech/blog-images/2023-08-07/cat.gif)

출처 - [GIPHY](https://giphy.com/gifs/reactiongifs-vSSdLSLbGIXio)

![](https://oliveyoung.tech/_img/b25c770e9204bb19-1600.webp)

2023년 3월 올영세일 대비 분당 최대 쿠폰 발급량이 2.2배에 달하는 속도 개선이 있었습니다.

사용자의 쿠폰 발급 대기 시간도 많이 줄어들어 모든 쿠폰이 1~2분 만에 소진되었고, 덕분에 사용자 경험도 좋아지고 매출 증가에도 좋은 영향을 끼쳤습니다.

---

## 다음으로..

하지만, 세일 기간 동안 운영하면서 여러 시행착오가 있었습니다.

Redis Pub/Sub과 list 자료구조를 사용하는 것보다 더 좋은 대안이 있지 않을까요?

다음 편에서는 더욱 개선된 쿠폰 발급 프로세스를 소개해 보도록 하겠습니다.

### 그럼 다음 편에서 만나요!!

![](https://oliveyoung.tech/blog-images/2023-08-07/bye.gif)

출처 - [GIPHY](https://giphy.com/gifs/baby-bye-slide-m9eG1qVjvN56H0MXt8)

올리브영 테크 블로그는 구성원들이 진심을 담아 손수 작성하고 있습니다
