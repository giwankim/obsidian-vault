---
title: "[2주차] 이진우 by ljw1126 · Pull Request #17 · Loopers-play-dev-lab/integration-external-services"
source: "https://github.com/Loopers-play-dev-lab/integration-external-services/pull/17"
author:
  - "[[ljw1126]]"
published: 2026-07-18
created: 2026-07-25
description: "개요 구매를 [포인트 적립 → 결제 승인] Saga로 처리하고, 불확정 상태를 두 개의 보정 배치가 종착 상태로 수렴시킵니다. 인수 테스트 BUY-1~8 전체 🟢 GREEN (26/26) 구현 내용 1. PurchaseSaga — 정방향 흐름 +"
tags:
  - "clippings"
---

> [!summary]
> Study-group PR (Loopers week 2) implementing a purchase flow as a Saga — point accrual → payment approval — where each step commits its own short transaction as a checkpoint and external calls stay outside transactions. The payment outcome branches three ways: SUCCESS confirms, FAILED marks the purchase failed and schedules point revocation (`REVOKE_PENDING`), and PENDING is held rather than compensated, with two reconciliation batches (`PaymentReconciler` polling the PG, `PointReconciler` executing revocations) converging the uncertain states. The discussion covers whether raw PG status strings like `"DONE"` should reach the application layer or be mapped to an enum at the adapter boundary, plus practitioner advice on tuning connect/read timeouts from observed response times.

## 개요

- 구매를 \[포인트 적립 → 결제 승인\] Saga로 처리하고, 불확정 상태를 두 개의 보정 배치가 종착 상태로 수렴시킵니다.
- 인수 테스트 BUY-1~8 전체 🟢 GREEN (26/26)

## 구현 내용

### 1\. PurchaseSaga — 정방향 흐름 + 롤백 예약

- 단계마다 짧은 독립 트랜잭션으로 체크포인트 save → Saga 로그 역할 (외부 호출은 트랜잭션 밖)
- 포인트 실패(BUY-3): 첫 단계라 되돌릴 외부 효과가 없으므로 보상 없이 FAILED 종료
- 결제 outcome 3분기(BUY-1/2/4/5): SUCCESS→CONFIRMED / FAILED→FAILED+포인트 회수 예약(REVOKE\_PENDING) / PENDING→보류

### 2\. PaymentReconciler — PENDING 구매를 PG 조회로 수렴 (BUY-6/7)

- PG 상태에 따라
	- "DONE" → CONFIRMED 처리
		- 미존재·거절(PgDeclinedException) → FAILED + 회수 예약
		- 판단 불가는 확정하지 않고 보류:
		- 1. PG 일시장애(PgServerException)인 경우
				- 2. paymentKey 없는 행(Saga 중단 흔적 — poison pill 방지)
				- 3. "DONE"이 아닌 상태
- 처리 건수 = Σ 확정(CONFIRMED/FAILED) 건수 (보류는 제외)

### 3\. PointReconciler — 롤백 예약된 포인트 회수 (BUY-8)

- REVOKE\_PENDING → revoke 성공 시 REVOKED, 실패(PointException)는 다음 주기 재시도

---

## 질문

1. `PaymentReconciler`에서 getPayment가 200 응답을 주지만 status가 "DONE"이 아닌 경우는 우선 `보류`로 처리했습니다. PG사의 상태 코드 문자열(ex."DONE" )이 application 레이어에 들어오는 게 맞는지 다른 상태 값도 명시적으로 처리 해줬어야 하는지 고민입니다. confirm()이 PgOutcome으로 흡수하듯 getPayment도 어댑터에서 enum으로 매핑하는 게 맞을까요?
2. 실무에서 `connect-timeout` , `read-timeout`을 터져 장애 대응해보신 경험이 있으신가요? 그때 어떻게 알아 채셨는지, 그리고 어떻게 원인 분석 후 값을 산정해 문제 해결하신 건지 사고 과정이 궁금합니다.

---

## Comments

> **codingjigi** ·
>
> > PaymentReconciler에서 getPayment가 200 응답을 주지만 status가 "DONE"이 아닌 경우는 우선 보류로 처리했습니다. PG사의 상태 코드 문자열(ex."DONE" )이 application 레이어에 들어오는 게 맞는지 다른 상태 값도 명시적으로 처리 해줬어야 하는지 고민입니다. confirm()이 PgOutcome으로 흡수하듯 getPayment도 어댑터에서 enum으로 매핑하는 게 맞을까요?
>
> 답변부터 해드리면 저는 외부 상태코드는 애플리케이션 레이어에 전파하진 않아요.
> 의존성 때문에 외부 상태코드를 어디서 관리해야되냐.. 이게 매번 고민인 것 같습니다.
> 시원한 답변이 아닐 수 있지만, 제 생각부터 말씀드리면 트레이드오프의 영역인 것 같아요.
> 외부 상태 코드를 애플리케이션 레이어에 관리하지 않게되면 사용하는 클래스마다 매번 생성을 해줘야 되는 단점이 있긴하죠.. 이런 의존성 제약에 따른 모듈 설계 관점을 고민하신 것만으로도 충분히 대단하신 것 같습니다.
>
> > 실무에서 connect-timeout , read-timeout을 터져 장애 대응해보신 경험이 있으신가요? 그때 어떻게 알아 채셨는지, 그리고 어떻게 원인 분석 후 값을 산정해 문제 해결하신 건지 사고 과정이 궁금합니다.
>
> timeout 으로 인한 장애 경험은 없습니다. 다만 외부 API 모니터링 시 특정 서버 간의 timeout 이 잦으면 모니터링 도구를 통해 실제 응답이 몇초만에 서버에 도달했고, timeout 설정은 어떻게 되어있었는지 확인 후 적절하게 늘려보거나 (혹은 줄이거나) 하는 편입니다.
