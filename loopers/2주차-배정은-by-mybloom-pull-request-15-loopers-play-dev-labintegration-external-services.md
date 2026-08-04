---
title: "[2주차] 배정은 by mybloom · Pull Request #15 · Loopers-play-dev-lab/integration-external-services"
source: "https://github.com/Loopers-play-dev-lab/integration-external-services/pull/15"
author:
  - "[[mybloom]]"
published: 2026-07-18
created: 2026-07-25
description: "이번 주에 무엇을 했나 구매 Saga — 구매를 \"포인트 적립 → 결제\"로 처리하고, 결제 결과(성공/실패/불확정)에 따라 확정·롤백예약·보류로 마무리했다. PG 보정 배치 — 불확정(PENDING) 구매를 PG 재조회로 확정 또는 실패로 수렴시켰다"
tags:
  - "clippings"
---

> [!summary]
> Study-group PR (Loopers week 2) solving the same purchase-Saga problem with an emphasis on operability: five design principles (never wrap external calls in one transaction, schedule compensation but execute it separately, hold PENDING instead of compensating it, isolate batch work per-record, and make the gray zone observable). Reconciliation runs on `@Scheduled` batches with a grace period — querying only rows where `createdAt < now - grace` — so records still settling at the PG aren't prematurely judged FAILED, and held/failure counts surface via Prometheus metrics, alerts, and a Grafana dashboard. Reviewer answers argue grace should track the external API's max response time (~1 min), that batch interval is a user-experience and policy question rather than a DB-load one (the external API bears the real load), and that the created-at grace filter is a common, sound industry approach.

## 이번 주에 무엇을 했나

1. **구매 Saga** — 구매를 "포인트 적립 → 결제"로 처리하고, 결제 결과(성공/실패/불확정)에 따라 확정·롤백예약·보류로 마무리했다.
2. **PG 보정 배치** — 불확정(PENDING) 구매를 PG 재조회로 확정 또는 실패로 수렴시켰다.
3. **포인트 보정 배치** — 회수 예약(REVOKE\_PENDING)된 포인트를 실제로 회수했다.
4. **자동화(NH)** — 보정 배치를 `@Scheduled` 로 주기 실행하고, grace period 로 회색영역 race 를 피했다.
5. **관측(NH)** — 보류(held) 메트릭·실패 로깅·Prometheus 알람으로 "조용한 실패"를 드러내고, Grafana 대시보드로 시각화했다.

## 이번 주 설계 원칙

1. **외부 호출을 하나의 트랜잭션으로 묶지 않는다** — 롤백으로 못 되돌리니 단계별 독립 저장으로 체크포인트를 만든다.
2. **보상은 예약하고 실행은 분리한다** — 요청 흐름은 의도(`REVOKE_PENDING`/`PENDING`)만 남기고, 실제 외부 회수·확정은 배치가 재시도한다.
3. **불확정(PENDING)은 보상하지 않고 보류한다** — 미확정을 실패로 오인해 되돌리면 이중 손실이다.
4. **배치는 건별로 격리한다** — 한 건 실패가 다른 건에 전파되지 않게 한다.
5. **회색영역은 관측 가능해야 한다** — 최종 일관성을 택한 대가(적체·보류)를 지표·로그·알람으로 드러낸다.

## 질문

1. **좋은 grace 시간**은 실제로 얼마인가? (실서비스 PG 지연 분포를 측정해 정해야 하나?)
2. **PENDING 수렴은 최악 ~60초(배치 주기 60초) 걸린다. 배치 주기를 줄이면 DB 폴링(조회) 부하가 늘고, 늘리면 수렴이 늦어진다.** 최적의 배치 주기는 얼마인가? (실서비스 PG 지연 분포를 측정해 정해야 하나?) — *참고: race(덜 익은 건 성급히 오판)는 배치 주기가 아니라 grace 가 통제한다(스케줄러가 매 실행마다 `now - grace` 로 안 익은 건을 스킵). grace 를 줄이면 오판이 늘고, 주기는 무관하다.*
3. **회색영역 race 를 "grace 시간을 빼서(`now - grace` 이전에 생성된 건만 조회)" 통제한 방식이 적절한가요? 실무에서도 이렇게 하나요?** 스케줄러가 매 실행마다 `createdAt < now - grace` 로 **방금 생성돼 아직 PG 정착 전일 수 있는 건을 조회 대상에서 제외**해, 성급히 `FAILED` 로 오판하는 것을 막았습니다. 이 **생성시각 기준 grace 필터** 방식이 잘 한 것인지, 실무에서도 같은 식으로 처리하는지(아니면 PG 콜백/웹훅 대기, 재시도 횟수·상태 타임스탬프 기반 등 다른 방식을 쓰는지) 궁금합니다.
	- `now - grace` 로 빼는 부분 → [`ReconcileScheduler.kt#L30`](https://github.com/Loopers-play-dev-lab/integration-external-services/blob/mybloom/project/week2/apps/commerce-api/src/main/kotlin/com/failsafe/application/reconcile/ReconcileScheduler.kt#L30)
		- grace 조회(덜 익은 건 제외) → [`PaymentReconciler.reconcileMatured` L30-31](https://github.com/Loopers-play-dev-lab/integration-external-services/blob/mybloom/project/week2/apps/commerce-api/src/main/kotlin/com/failsafe/application/reconcile/PaymentReconciler.kt#L30-L31) , [`PurchaseRepository.findByStatusAndCreatedAtBefore` L15-18](https://github.com/Loopers-play-dev-lab/integration-external-services/blob/mybloom/project/week2/apps/commerce-api/src/main/kotlin/com/failsafe/domain/purchase/PurchaseRepository.kt#L15-L18)

---

---

## Comments

> **codingjigi** ·
>
> > 좋은 grace 시간은 실제로 얼마인가? (실서비스 PG 지연 분포를 측정해 정해야 하나?)
>
> 우선 좋은 질문 감사합니다. 말씀해주신것처럼 저는 보통 실제 외부 API 최대 응답시간을 기준으로 정하는 것 같아요. 보통 timeout 시간이 1분을 넘는경우는 많이 없어서, 1분 정도 텀을 주고 조회하는 편입니다.
>
> > PENDING 수렴은 최악 ~60초(배치 주기 60초) 걸린다. 배치 주기를 줄이면 DB 폴링(조회) 부하가 늘고, 늘리면 수렴이 늦어진다. 최적의 배치 주기는 얼마인가? (실서비스 PG 지연 분포를 측정해 정해야 하나?) — 참고: race(덜 익은 건 성급히 오판)는 배치 주기가 아니라 grace 가 통제한다(스케줄러가 매 실행마다 now - grace 로 안 익은 건을 스킵). grace 를 줄이면 오판이 늘고, 주기는 무관하다.
>
> 고민 많이해보셨군요! 최적의 배치 주기는 제가 생각했을 때 사용자 관점에서 처리 결과를 얼마나 빨리 전달해야 하는가? 로 생각해보면 좋을 것 같습니다. 10분 이내의 스케줄러면 충분하지 않을까 생각들어요. 정책적인 부분도 엮여있을 것 같네요.
>
> 부하에 대한 제 생각을 말씀드리면 배치 주기를 줄였을 때 부하 관점은 우리 데이터베이스보다 외부 API 의 부하가 늘어나는 게 더 클 것 같습니다. 인덱스 설계와 조회 범위만 적절하다면 스케줄러에서 조회하는 쿼리 수준은 데이터베이스의 부하는 없을 것 같아요. 부하는 외부 API 입장에서 한번 생각해보면 좋을 것 같습니다.
>
> > 회색영역 race 를 "grace 시간을 빼서(now - grace 이전에 생성된 건만 조회)" 통제한 방식이 적절한가요? 실무에서도 이렇게 하나요? 스케줄러가 매 실행마다 createdAt < now - grace 로 방금 생성돼 아직 PG 정착 전일 수 있는 건을 조회 대상에서 제외해, 성급히 FAILED 로 오판하는 것을 막았습니다. 이 생성시각 기준 grace 필터 방식이 잘 한 것인지, 실무에서도 같은 식으로 처리하는지(아니면 PG 콜백/웹훅 대기, 재시도 횟수·상태 타임스탬프 기반 등 다른 방식을 쓰는지) 궁금합니다.
>
> `grace 시간을 빼서(now - grace 이전에 생성된 건만 조회)` 설계 하는 방식을 저는 애용하고 있습니다. 말씀해주신 다른 여러가지 방식도 있지만, 가장 직관적이고 좋은 것 같아요. 많은 조직을 경험해보진 못했지만 일반적인 것 같아요. (이 부분을 고려하지 않는 곳도 많을 것 같습니다)
>
> 매번 좋은 질문 주셔서 감사해요. 고생하셨습니다!
