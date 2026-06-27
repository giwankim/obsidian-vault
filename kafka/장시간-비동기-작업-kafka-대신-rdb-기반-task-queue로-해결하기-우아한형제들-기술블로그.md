---
title: "장시간 비동기 작업, Kafka 대신 RDB 기반 Task Queue로 해결하기 | 우아한형제들 기술블로그"
source: "https://techblog.woowahan.com/23625/"
author:
published: 2025-11-25
created: 2026-06-26
description: "장시간 비동기 작업, Kafka 대신 RDB 기반 Task Queue로 해결하기 | 전자계약서 시스템에서는 다양한 업무 목적에 따라 여러 형태의 대용량 엑셀 파일을 생성할 수 있습니다. 예를 들어 생산성 지표 엑셀, 근무 관리 엑셀, 행정 처분 추정 업주 엑셀, 계약현황 엑셀 등 각기 다른 조건과 데이터로 구성된 엑셀을 이메일로 받아볼 수 있는 기능인데요. 데이터 조건에 따라 엑셀 생성 시간이 오래 걸려, 화면에서 결과를 기다리지 않게 Kafka를 이용한"
tags:
  - "clippings"
---

> [!summary]
> 우아한형제들 전자계약서 팀이 30분 이상 걸리는 대용량 엑셀 생성 작업에서 Kafka의 `max.poll.interval.ms`(5분) 초과로 리밸런싱이 발생해 같은 메시지가 중복 소비·발송되던 문제를 다룬다. "우리가 발행하고 우리가 소비하는" 장시간 작업에는 Kafka가 부적합하다고 판단하고, RDB 기반 Task Queue + Heartbeat 아키텍처(상태 컬럼, Redis 분산 락 선점, 코루틴 Heartbeat 갱신, 3회 재시도, ShedLock 기반 Fallback 복구 스케줄러)로 재설계한 과정을 코드와 함께 설명한다. 결론은 트랜잭션 특성에 따라 메시징 시스템을 선택해야 한다는 것 — 짧고 빠른 작업엔 Kafka, 길고 상태 관리가 복잡한 작업엔 RDB 폴링 방식이 적합하다.

## 장시간 비동기 작업, Kafka 대신 RDB 기반 Task Queue로 해결하기

2025\. 11. 25. 박민규

[Backend](https://techblog.woowahan.com/?pcat=backend)

전자계약서 시스템에서는 다양한 업무 목적에 따라 여러 형태의 대용량 엑셀 파일을 생성할 수 있습니다. 예를 들어 `생산성 지표 엑셀`, `근무 관리 엑셀`, `행정 처분 추정 업주 엑셀`, `계약현황 엑셀` 등 각기 다른 조건과 데이터로 구성된 엑셀을 이메일로 받아볼 수 있는 기능인데요. 데이터 조건에 따라 엑셀 생성 시간이 오래 걸려, 화면에서 결과를 기다리지 않게 Kafka를 이용한 비동기로 처리로 구현되어 있습니다.

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/%EC%97%91%EC%85%80_%EC%83%9D%EC%84%B1_%ED%94%8C%EB%A1%9C%EC%9A%B0-as-is.jpg)

Kafka를 이용한 엑셀 생성 플로우

즉, 어드민에서 엑셀 생성이 요청되면 Kafka 이벤트를 발행하고, Worker가 이를 소비하여 엑셀을 생성한 뒤 메일로 발송하는 방식입니다. 초기에는 대부분의 엑셀 생성이 10분 이내에 완료되었으나, 최근 신규 엑셀 타입을 추가로 개발하면서 각 행마다 여러 개의 타 팀의 API를 호출해 데이터를 채워야 하는 구조였기 때문에 데이터 조회만으로도 30분 이상이 소요되기 시작했습니다.

어느 날, 사용자로부터 **"같은 엑셀 파일을 여러 번 받았어요."** 라는 문의가 들어왔습니다. 확인해보니 동일한 조건과 데이터로 생성된 엑셀 파일이 여러 번 발송되어 있었습니다. 로그를 추적한 결과, Kafka Consumer가 동일한 메시지를 두 번 처리한 흔적을 발견했습니다.

원인은 **수만 건의 데이터를 처리하며 외부 API를 호출하다 보니 30분 이상 걸리는 작업이 Kafka의 5분 타임아웃(`max.poll.interval.ms`)을 초과하면서 리밸런싱이 발생** 한 것이었습니다. Kafka는 5분 동안 `poll()` 이 호출되지 않으면 Consumer가 죽은 것으로 판단하고, 동일한 메시지를 다른 Consumer에게 재할당했고 그 메시지가 재처리되어서 중복으로 발송되었습니다. 타임아웃을 1시간으로 늘리면 해결할 수 있지만, 이 방식은 근본적인 해결책이 아니었습니다. 1시간으로 늘리면 1시간 30분 걸리는 작업에서 또 문제가 발생하고, 무엇보다 **실제 Worker 장애 시 감지가 1시간이나 지연** 되는 부작용이 생깁니다.

결국 여러 대안을 검토한 끝에, **엑셀 생성에서 Kafka를 걷어내고 RDB 기반 Task Queue + Heartbeat 아키텍처** 로 재설계하였습니다. 이 글에서는 아키텍처를 재설계하는 과정에서 의사결정 흐름, 새 구조가 어떤 방식으로 안정성을 확보하게 되었는지 소개하겠습니다.

## 문제 상황

### 기존 구조

기존 구조는 API 서버(Producer)가 엑셀 생성 요청을 Kafka에 발행하는 방식이었습니다. Kafka는 이 이벤트를 Worker(Consumer)에게 전달하고, Worker는 장시간 엑셀을 생성한 뒤 결과를 메일로 발송합니다. 발송 작업이 끝나면 Worker가 Kafka에 ACK를 보내는 형태입니다.

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/%EC%8A%A4%ED%81%AC%EB%A6%B0%EC%83%B7-2025-10-30-12.52.31.png)

기존 엑셀 생성 플로우

### 발생한 이슈

그런데 특정 엑셀 생성 시 네트워크 지연과 타 팀 서버 응답 지연이 누적되면서 전체 처리 시간이 크게 늘어났습니다. 엑셀 생성 작업 시간이 30분 이상 소요되자 Worker가 그동안 `poll()` 을 호출하지 못하게 되었습니다.

Kafka는 이를 "Worker가 죽었다"고 판단하여 약 5분 뒤 리밸런싱을 시작했습니다. 그 결과, 같은 이벤트가 다른 Worker에게 다시 할당되었습니다. 이렇게 두 Worker가 동일 작업을 수행하면서 중복 발송 문제가 발생했습니다.

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/%EC%8A%A4%ED%81%AC%EB%A6%B0%EC%83%B7-2025-10-30-12.52.50.png)

기존 엑셀 생성 플로우에서 발생한 이슈

## 임시 해결책 (핫픽스)

엑셀 파일이 중복으로 발송되는 문제는 실제 운영 업무에 직접적인 영향을 주는 심각한 이슈였습니다. 근본적인 문제 해결 전에 급하게 핫픽스 형태의 임시 조치를 적용해야 했습니다.

우선 Kafka 리밸런싱으로 동일 메시지가 두 번 소비되는 상황을 막기 위해, createExcel()을 비동기 처리한 뒤 즉시 ACK하도록 변경했습니다.

```kotlin
//  기존: 엑셀 생성 완료 후 ACK
fun listen(message: Message, ack: Acknowledgment) {
    excelCreateManager.createExcel(message)  // 30분 걸림
    ack.acknowledge()  // 너무 늦음
}

//  임시 해결: 비동기 처리 + 즉시 ACK
fun listen(message: Message, ack: Acknowledgment) {
    CoroutineScope(singleThread).launch {
        excelCreateManager.createExcel(message)  // 백그라운드에서 처리
    }
    ack.acknowledge()  // 즉시 ACK
}
```

위 방식은 `max.poll.interval.ms` 를 초과하지 않기 때문에, Consumer가 죽었다고 오판되어 리밸런싱되는 문제를 피할 수 있었습니다. 즉, 중복 발송 문제는 일시적으로 해결되었습니다. 하지만 이 접근은 완전한 해결책이 아니었습니다. ACK를 먼저 처리하기 때문에 작업 도중 오류가 발생하면 데이터가 유실될 수 있고, 서버 배포나 장애 시 진행 중인 작업이 사라지는 문제도 남아 있었습니다. 단기적인 응급처치일 뿐 장기적으로는 신뢰할 수 있는 구조가 아니었습니다.

이 경험을 계기로 팀 내에서는 **"정말 비동기 엑셀 생성 작업에 Kafka가 필요한 도구일까?"** 라는 근본적인 논의를 하게 되었습니다.

## 꼭 Kafka가 필요한가

우리는 처음에 대량 엑셀 발송 작업을 비동기화하기 위해 Kafka를 도입했습니다. API 서버가 Topic에 작업 메시지를 발행하고 별도의 Worker가 이를 구독해 처리하는 구조를 만들면, 급격한 트래픽 변화에도 탄력적으로 대응하고 필요한 경우 Consumer Group을 확장할 수 있음을 기대했습니다.

하지만 실제 운영에서 우리는 그 기대를 거의 누리지 못했습니다. 엑셀 발송은 트래픽이 폭발적으로 증가할 일이 없었고, 생산자와 소비자가 모두 우리 서비스 안에 있어 Consumer Group을 여러 개로 늘릴 필요도 없었습니다. 오히려 장시간이 걸리는 작업 특성 때문에 `max.poll.interval.ms` 를 주기적으로 넘기며 Consumer가 죽었다고 판단되는 문제가 자주 발생했고, 이를 피하기 위해 타임아웃을 늘리면 실제 장애를 감지하는 속도가 크게 늦어지는 딜레마에 빠졌습니다.

결국 **"우리가 발행하고 우리가 소비하는 구조에서 장시간 비동기 작업에서 Kafka는 필요하지 않다."** 는 결론에 도달했습니다.

## 근본적인 해결책

Kafka가 적합하지 않다는 결론에 도달한 뒤, 새로운 아키텍처가 갖춰야 할 요구사항을 정리했습니다.

### 요구사항

| 요구사항 | 설명 |
| --- | --- |
| **시간 제한 없음** | 작업이 1시간, 2시간 걸려도 문제없이 완료되어야 함 |
| **배포 영향 없음** | – 30분짜리 작업 중 서버 배포가 진행되면 즉시 중단되어야 함   – Graceful shutdown으로 작업 완료를 기다리면 배포 자체가 30분 넘게 걸릴 수 있어 비현실적임 |
| **작업 유실 방지** | 서버가 다운되더라도 작업이 재처리되어 유실되지 않아야 함 |
| **자동 재시도** | 타 팀 API 의존성 등으로 일시적 오류가 발생하면 자동으로 재시도되어야 함 |
| **병렬 처리** | 여러 Worker가 동시에 작업을 분산 처리할 수 있어야 함 |
| **중복 방지** | 동일한 작업이 중복 처리되어서는 안 됨 |

위와 같은 요구사항을 모두 만족하기 위해, 기존 Kafka 기반 구조를 걷어내고 RDB 기반의 Task Queue 아키텍처로 새롭게 설계했습니다. 아래에서는 새로 도입한 구조의 전체 흐름을 그림으로 먼저 살펴본 뒤, 각 컴포넌트가 어떤 방식으로 동작하며 위 요구사항을 충족했는지 구체적인 구현 코드를 중심으로 설명드리겠습니다.

## 변경된 아키텍처

새로운 구조는 엑셀 생성 작업을 RDB에 영구적으로 저장하고, Worker가 주기적으로 Heartbeat를 갱신하며 작업 상태를 관리하는 방식으로 설계되었습니다. 아래 그림은 이러한 Task Queue 흐름과 Worker 간 역할 분리를 한눈에 볼 수 있도록 정리한 아키텍처입니다.

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/c04a9369-2316-4ec2-a9f3-3786e30394cd.jpeg)

RDB 기반 Task Queue + Heartbeat 아키텍처

### 테이블 구조

엑셀 생성 요청은 단순히 메시지 큐에 의존하지 않고, **RDB에 영구적으로 저장되는 작업 단위(task)** 로 관리됩니다. 모든 작업은 상태(status)와 마지막 Heartbeat(last\_heartbeat\_at) 정보를 가지고 있으며, Worker가 주기적으로 생존 신호를 갱신합니다. 이를 통해 Worker 서버가 중단되거나 재시작되더라도 작업을 복구할 수 있습니다.

```sql
CREATE TABLE excel_download_request (
    id BIGINT PRIMARY KEY,
    status VARCHAR(20),           -- PENDING, IN_PROGRESS, DONE, FAILED
    last_heartbeat_at DATETIME,   -- Worker 생존 신호 마지막 수신 시각
    retry_count INT DEFAULT 0,    -- 재시도 횟수 (최대 3회)
    created_at DATETIME,
    updated_at DATETIME
);
```

### 처리 로직

#### 1\. 작업 선점

먼저 Worker는 일정 주기(3초마다)로 대기 중(PENDING) 상태의 작업을 조회합니다. 조회된 작업을 Redis 분산 락을 이용해 선점함으로써, 여러 Worker 간의 중복 처리를 방지합니다.

```sql
-- PENDING 작업 조회
SELECT * FROM excel_download_request
WHERE status = 'PENDING'
ORDER BY id ASC
LIMIT 20;
```
```kotlin
@Scheduled(fixedDelay = 3000)  // 3초마다 실행
fun processExcelTasks() {
    runBlocking(Dispatchers.IO) {
        // 1. 대기 중인 작업 조회
        val candidateTasks = taskQueryService.findByStatus(status = "PENDING"
, limit = 20)

        // 2. Redis 분산 락으로 작업 선점 (최대 2개만)
        val lockedTasks = candidateTasks
            .asSequence()
            .filter { task ->
                redisClient.tryLock("TASK:${task.id}"
, leaseTime = 10_000)
            }
            .take(2) // 2개 선점
            .toList()

        // 3. 선점한 작업들을 병렬로 처리
        lockedTasks.map { task ->
            async { executeTask(task) }
        }.awaitAll()
    }
}
```

각 Worker는 한 번에 두 개의 작업을 선점합니다. 이렇게 하면 시스템 리소스를 안정적으로 활용할 수 있습니다.

##### 셀프 Q&A

**Q. PENDING 작업을 조회할 때 왜 20개씩 조회하는 건가요?**

**A.** 현재 Worker 서버는 총 10대가 구동 중이며, 각 Worker는 동시에 최대 2개의 작업을 병렬로 처리하도록 설계되어 있습니다. 즉, `**Worker 10대 × 병렬 처리 2개 = 20개**` 가 시스템의 최대 처리 용량입니다. 모든 서버는 동시에 `PENDING` 상태의 작업을 조회한 뒤, 각 작업별로 Redis 락을 시도합니다. 이때 락을 얻은 작업만 실제로 처리되고, 락을 얻지 못한 작업은 다른 서버가 처리할 수 있도록 그대로 남겨둡니다. 만약 조회 개수를 너무 많이 잡으면, 여러 서버가 동일한 작업에 대해 락을 시도하게 되어 불필요한 경합이 발생합니다. 반대로 너무 적게 잡으면, 트래픽이 몰렸을 때 일부 Worker가 처리할 작업을 배정받지 못해 시스템 전체 처리율이 떨어집니다. 결국 20개씩 조회는 락 경합과 처리 효율 간의 균형을 고려해, 모든 Worker가 동시에 최대 처리량을 낼 수 있도록 설정된 기준값입니다.

#### 2\. Heartbeat 시작 및 엑셀 생성

작업이 선점되면 즉시 상태를 IN\_PROGRESS로 변경하고 Redis 락을 해제합니다. 이후 Worker는 주기적으로 DB에 Heartbeat를 갱신하여 Worker가 아직 작업 중임을 알립니다. Heartbeat 갱신 작업으로 Worker가 비정상 종료되더라도, 일정 시간이 지나면 다른 Worker가 해당 작업을 복구할 수 있습니다.

```kotlin
private suspend fun executeTask(task: ExcelTask) = coroutineScope {
    // 1. 상태 변경 후 락 해제
    taskCommandService.updateStatus(
        id = task.id,
        status = "IN_PROGRESS"
,
    )
    redis.unlock("TASK:${task.id}"
)

    // 2. Heartbeat update 코루틴 시작
    val heartbeatUpdateJob = launch {
        while (this.isActive) {
            taskService.updateHeartbeat(task.id, LocalDateTime.now())
            delay(60_000)  // 1분마다
        }
    }

    try {
        // 3. 실제 엑셀 생성 작업 수행 (최대 1시간~2시간 소요)
        generateExcel(task)
        taskCommandService.updateStatus(task.id, "DONE"
)
    } catch (e: Exception) {
        // 4. 실패 시 재시도 처리
        handleRetry(task)
    } finally {
        heartbeatUpdateJob.cancelAndJoin()
    }
}
```

위 코드의 핵심은 Heartbeat 업데이트 작업을 별도의 코루틴으로 분리했다는 점입니다.

#### 3\. 재시도 처리

엑셀 생성 도중 외부 API 실패나 일시적 네트워크 오류가 발생할 수 있습니다. 이런 경우에는 단순히 실패로 끝내지 않고, 재시도 횟수를 늘린 뒤 다시 `PENDING` 상태로 되돌립니다.

```kotlin
fun handleRetry(task: ExcelTask) {
    val retryCount = task.retryCount + 1
    if (retryCount < 3) {
        // 3회 미만 - PENDING으로 되돌려 재시도
        taskService.updateRetryCount(task.id, retryCount)
        taskService.updateStatus(task.id, "PENDING"
)
    } else {
        // 3회 이상 - 최종 실패 처리
        taskService.updateStatus(task.id, "FAILED"
)
    }
}
```

위 방식으로 작업이 실패하더라도 3회까지 수행하도록 설계되어, 외부 API 장애와 같은 일시적 오류 상황에서도 안정적인 처리가 가능합니다.

#### 4\. 장애 복구 메커니즘

Worker가 갑자기 죽거나 서버 배포로 인해 프로세스가 중단되더라도, 2분 이상 Heartbeat가 갱신되지 않은 작업은 자동으로 감지하여 다시 PENDING 상태로 되돌립니다. 로직은 단순하지만 별도의 큐 관리나 재시작 절차 없이, DB 상태만으로 장애 복구가 가능합니다.

```sql
-- 2분 이상 Heartbeat 없는 작업 찾기
SELECT * FROM excel_download_request
WHERE status = 'IN_PROGRESS'
  AND last_heartbeat_at < NOW() - INTERVAL 2 MINUTE;
```
```kotlin
// 새로운 스케쥴러
@Scheduled(cron = "0 */2 * * * *"
) // 2분마다 실행
@SchedulerLock( // 1대의 워커에서만 수행되도록 Shedlock 사용
    name = "FallbackSupportScheduler"
,
    lockAtLeastFor = "PT1M"
,
    lockAtMostFor = "PT2M"
,
)
fun fallbackSupportScheduler() {
    // 2분 이상 heartbeat 없는 작업 조회
    val stopedTasks = taskService.findFallbackTasks(
        now = LocalDateTime.now()
    )

    stopedTasks.forEach { task ->
        // PENDING으로 되돌려 다른 Worker가 처리하도록 함
        taskService.updateStatus(task.id, "PENDING"
)
    }
}
```

이때 중요한 점은, 복구 스케줄러가 여러 워커에서 동시에 실행되지 않도록 제어해야 한다는 것입니다. 만약 모든 워커가 동시에 복구 로직을 수행한다면, 같은 작업이 여러 번 복구될 수 있습니다.이를 방지하기 위해 `ShedLock(@SchedulerLock)` 을 적용하여 동시에 여러 인스턴스가 같은 스케줄을 실행하지 못하도록 보장합니다.

##### 셀프 Q&A

**Q. retryCount로 재시도 처리가 가능한데, 왜 별도 Fallback 스케줄러가 필요한가요?**

**A.** Worker 서버 배포 시 엑셀 생성 작업은 기다리지 않고 즉시 종료됩니다. Graceful shutdown이 적용된다면 배포가 30분~1시간씩 지연되어 현실적이지 않습니다. 또한 서버가 갑자기 다운될 경우, 별도의 장애 복구 메커니즘이 반드시 필요했습니다.

## 상황별 시나리오

지금까지 설명한 RDB 기반 Task Queue 아키텍처가 실제로 어떻게 동작하는지, 세 가지 대표적인 상황을 시퀀스 다이어그램으로 정리했습니다.

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/%EC%8A%A4%ED%81%AC%EB%A6%B0%EC%83%B7-2025-10-30-16.53.30.png)

정상 처리 시나리오

가장 기본적인 시나리오입니다. Worker가 작업을 선점하고 Heartbeat를 주기적으로 갱신하며 정상적으로 완료하는 과정입니다.

![](https://techblog.woowahan.com/wp-content/uploads/2025/11/%EC%8A%A4%ED%81%AC%EB%A6%B0%EC%83%B7-2025-12-01-17.16.20.png)

실패 & 재시도 시나리오

작업 처리 중 오류가 발생했을 때 자동으로 재시도하는 과정입니다. 재시도 횟수가 3회 미만이면 `PENDING` 으로 되돌려 다시 처리하고, 3회를 초과하면 최종 실패 처리됩니다.

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/%EC%8A%A4%ED%81%AC%EB%A6%B0%EC%83%B7-2025-10-30-17.00.31.png)

장애 복구 시나리오

Worker가 갑자기 중단되었을 때 Fallback 스케줄러가 이를 감지하고 작업을 복구하는 과정입니다. 2분 이상 Heartbeat가 갱신되지 않으면 자동으로 다른 Worker가 작업을 이어받습니다.

## 새로운 아키텍처의 효과

아키텍처를 RDB 기반 Task Queue로 전환하면서 얻은 특징들을 정리하면 다음과 같습니다.

### 개선된 점

#### 1\. 시스템 복잡도 감소

- Kafka 메시지 플로우 제거로 디버깅 용이
- 단일 데이터 소스(RDB)로 상태 관리 단순화

#### 2\. 안정성 향상

- 메시지 재발행/유실 문제 원천 차단
- 서버 다운 시 자동 복구 메커니즘
- Graceful Shutdown을 설정하지 않아 배포 시간에 영향 없음

#### 3\. 운영 효율성

- Worker 수평 확장 용이
	- 기존 Kafka는 파티션 증설 및 리밸런싱 필요
- 단순 쿼리로 실시간 모니터링 가능

### 트레이드오프

#### 1\. DB 부하 여지

- 지속적인 폴링 쿼리가 추가되지만 커버링 인덱스로 효율을 극대화
- 분당 20~30회 쿼리로 무시 가능한 수준

#### 2\. 처리 시작 지연

- 폴링 주기(3초)만큼 지연이 발생함. 하지만 엑셀 다운로드에서 3초 지연은 허용 가능한 수준

## 마무리

이번 아키텍처 전환을 통해 중요한 인사이트를 얻을 수 있었습니다.
**작업 트랜잭션 특성에 따라 메시징 시스템 선택이 달라져야 한다** 는 점입니다.

**트랜잭션이 짧고 빠른 처리가 필요한 작업** 은 Kafka와 같은 이벤트 스트리밍 플랫폼이 적합합니다. 실시간 알림, 결제 승인, 로그 수집 등이 대표적인 예시인데요. 이런 작업들은 밀리초 단위의 지연도 중요하고, 높은 처리량을 요구합니다.

반면 **트랜잭션이 길고 복잡한 상태 관리가 필요한 작업** 은 RDB 기반의 폴링 방식이 더 적합합니다. 대용량 엑셀 생성처럼 수십 분씩 걸리는 작업은 중간 상태 추적, 실패 시 재시도, 부분 완료 처리 등 복잡한 요구사항을 갖습니다. 이런 경우 트랜잭션 보장과 재시도 처리가 가능한 RDB 기반 Task Queue 아키텍처가 더 안정적인 것 같습니다.

좋은 시스템은 복잡한 기술 위에 세워지는 것이 아니라, 명확한 문제 정의와 단순한 설계 원칙 위에서 만들어진다고 생각합니다. **중요한 것은 문제의 본질을 이해하고, 거기에 맞는 구조를 설계하는 것** 이라는 점을 다시 한번 느낄 수 있었습니다.
