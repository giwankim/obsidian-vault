---
title: "수억 건의 데이터, 맛있게 쪼개 먹는 방법 (with. Partitioning) | 카카오페이 기술 블로그"
source: "https://tech.kakaopay.com/post/spring-batch-partitioning/"
author:
published: 2026-03-18
created: 2026-03-18
description: "Spring Batch Partitioning, Cursor 기반 ItemReader, Bulk Operations를 활용해 수억 건 데이터 처리 성능을 향상시킨 실전 경험을 공유합니다."
tags:
  - "clippings"
---

> [!summary]
> KakaoPay의 수억 건 원장 데이터 재생성 과정에서 발생한 OOM 문제를 Spring Batch Partitioning, MongoCursorItemReader(서버 사이드 커서 스트리밍), Bulk Operations를 조합해 해결한 사례를 다룬다. 날짜 기준 파티셔닝으로 병렬 분할하고, Paging 대신 Cursor로 O(1) 읽기 성능을 확보하며, saveAll 대신 bulkWrite로 네트워크 왕복을 최소화하여 500만 건 기준 약 10.9배 성능 향상을 달성했다.

> 요약: 수억 건의 대량 데이터를 Spring Batch로 처리하며 발생한 OOM(Out of Memory) 문제를 Partitioning, Cursor 기반 ItemReader, Bulk Write를 활용해 해결한 과정을 공유합니다.

💡 **리뷰어 한줄평**

**yun.cheese** Spring Batch의 ‘진짜’ 실무를 만나다: 이론을 넘어 성능 최적화의 정석을 보여준 가이드.

**wade.hong** Spring Batch Partitioning 할 때 **정석처럼** 볼 수 있는 내용이에요. 참고해서 성능 확 끌어올려 보세요!

## 시작하며

(*이 글은 **실무에서 Spring Batch로 대량 데이터를 처리하며 OOM 문제를 경험한 개발자**, **Spring Batch의 Partitioning 기능을 학습하고 싶은 개발자**, **대량 데이터 처리 파이프라인 설계에 관심 있는 백엔드 개발자** 를 위해 작성되었습니다.*)

안녕하세요, 카카오페이 정산플랫폼팀의 와이입니다.

수억 건의 데이터를 처리하는 일은 마치 거대한 초콜릿 케이크를 한 번에 먹으려는 것과 같습니다. 보기만 해도 군침이 돌지만, 무작정 도전했다가는 탈이 나기 쉽죠. 저 역시 원장 통계 데이터를 재생성하면서 대량의 데이터를 한 번에 읽다가 OOM(Out of Memory) 이슈를 겪었습니다.

(*원장 통계: 거래의 원본 기록인 ‘원장’ 데이터를 바탕으로 집계하여 산출한 통계*)

이 글에서는 Spring Batch의 `Partitioning` 으로 대량 데이터를 효과적으로 분할하고, `Cursor` 기반 `ItemReader` 와 `Bulk Write` 로 안정적으로 처리한 경험을 공유합니다. 데이터라는 케이크를 맛있게 먹는 저만의 레시피, 지금부터 공개합니다.

## 문제 정의 및 해결 전략: 수억 건의 데이터, 어떻게 처리할까?

최근 원장 통계 데이터 구조가 변경되면서, 과거 통계 데이터 전체를 재생성해야 하는 과제가 주어졌습니다. 하루에만 수백만 건의 원장 데이터가 쌓이는 채널도 있어, 월 단위로는 수천만 건, 연 단위로는 수억 건에 달합니다.

(*채널: 결제가 발생하는 서비스 경로(예: 앱, 웹, 오프라인 매장 등)*)

이처럼 방대한 데이터를 다루기 위해 단계별 분할 처리 전략을 세웠습니다. 이 전략으로 데이터 정합성과 안정적인 처리 속도를 모두 확보하고자 했습니다.

- **1차 분할:** 전체 처리 기간을 ‘월’ 단위로 나누어 배치 작업을 실행
- **2차 분할:** 한 달 치 데이터(약 수천만 건)의 부하를 줄이기 위해, 배치 내부에서 다시 ‘일’ 단위로 작업을 나누어 병렬 처리

이 전략을 바탕으로 Spring Batch를 활용해 데이터를 안전하고 효율적으로 처리한 과정을 소개합니다.

## Spring Batch의 확장 및 병렬 처리

> [Scaling and Parallel Processing](https://docs.spring.io/spring-batch/reference/scalability.html)

Spring Batch는 대량 처리를 위해 다양한 확장 및 병렬 처리 기능을 제공합니다.
이 기능들은 크게 하나의 JVM 내에서 `멀티스레드` 를 활용하여 성능을 최적화하는 **단일 프로세스(Single-process)** 방식과 여러 JVM으로 `부하를 분산` 하여 물리적인 한계를 극복하는 **다중 프로세스(Multi-process)** 방식 두 가지로 분류할 수 있습니다.

- **Multi-threaded Step (single-process)**
	- ItemProcessor를 멀티 스레드로 실행
		- ItemReader와 ItemWriter는 싱글 스레드로 동작하므로 전체 성능은 입출력 속도에 의존
- **Parallel Steps (single-process)**
	- 서로 독립적인 로직을 여러 Step으로 분리하고 동시에 실행
		- 각 Step이 완전히 독립적이어야 하며, 모든 Flow가 완료될 때까지 대기하므로 가장 느린 Step이 전체 성능을 결정
- **Local Chunking of Step (single-process)**
	- Chunk 단위의 읽기/처리/쓰기 전 과정을 여러 스레드에서 독립적으로 병렬 처리
		- Multi-threaded Step과 달리 Reader/Writer까지 멀티스레드로 동작하므로 모두 thread-safe 필요
- **Remote Chunking of Step (multi-process)**
	- Manager가 읽은 데이터를 메시지 큐를 통해 여러 대의 Remote Worker로 전달하여 처리와 쓰기 과정을 분산 처리
		- Manager가 데이터를 읽고 Chunk를 전송하므로 Manager 속도에 의존
- **Partitioning a Step (single or multi-process)**
	- 데이터를 논리적으로 분할하여 여러 Worker Step이 각자 독립적으로 처리
		- 정교한 데이터 분할 전략을 위한 초기 설정이 복잡
- **Remote Step (multi-process)**
	- 메시징 채널을 통해 Step 실행을 Remote Worker나 클러스터로 분산
		- 로컬 작업 환경과 Remote Worker 간의 복잡한 메시징 인프라 설정이 필요

이번 2차 분할 작업의 핵심은 **한 달 치 데이터를 하루 단위로 쪼개어 독립적으로 처리하는 것** 입니다. Spring Batch가 제공하는 다양한 병렬 처리 방식 중 단일 프로세스 환경에서 데이터를 명확히 분할하고 병렬성을 극대화할 수 있는 [Local Partitioning](https://docs.spring.io/spring-batch/reference/scalability.html#partitioning) 전략을 선택했습니다.

## Partitioning

![partitioning overview](https://tech.kakaopay.com/_astro/image-1.df52c127_cw4us.png)

partitioning overview

**Partitioning** 은 대량 데이터를 여러 개의 **Partition** (조각)으로 나누고, 각 조각을 별도의 스레드에서 동시에 독립적으로 처리하는 병렬 처리 모델입니다.

- **Manager Step (Master)**: 전체 작업을 관리하며 데이터를 어떻게 나눌지 결정
- **Worker Step (Slave)**: `Manager` 로부터 할당받은 데이터 조각을 실제로 처리

각 `Worker Step` 은 자신만의 **ItemReader, ItemProcessor, ItemWriter** 인스턴스를 가지므로, 다른 스레드의 작업에 영향을 받지 않고 독립적으로 실행됩니다. 이 구조 덕분에 데이터 경합 없이 안전하게 병렬 처리 성능을 극대화할 수 있습니다.

이러한 **Partitioning** 을 구현하는 두 가지 핵심 인터페이스가 바로 `Partitioner` 와 `PartitionHandler` 입니다. 본격적으로 두 인터페이스를 살펴보기 전에, **Partitioning** 의 전체적인 동작 과정을 먼저 살펴보겠습니다.

### Partitioning의 전체적인 동작 과정

![Partitioning 상세 동작 과정](https://tech.kakaopay.com/_astro/image-2.22ff4b1f_cuUjB.png)

Partitioning 상세 동작 과정

**Partitioning** 은 크게 **분할(Split) → 실행(Execute) → 취합(Aggregate)** 세 단계로 진행됩니다.

#### 1️⃣. 분할 (Split)

👨🏼🔧 **역할:** **Manager Step** 이 `Partitioner` 를 통해 전체 작업을 어떻게 나눌지 결정하고, 각 `Worker Step` 에 전달할 작업 명세서(`ExecutionContext`)를 생성합니다.

🛠️ **동작:**

| 순서 | 동작 |
| --- | --- |
| 1 | **Job** 이 시작되면 **Manager Step** 역할을 하는 `PartitionStep` 이 실행됩니다.   \- [void doExecute(StepExecution stepExecution)](https://docs.spring.io/spring-batch/docs/current/api/org/springframework/batch/core/partition/support/PartitionStep.html#doExecute\(org.springframework.batch.core.StepExecution\)) |
| 2 | **PartitionStep** 은 분할 로직을 담당하는 `PartitionHandler` 에게 작업을 위임합니다.   \- [Collection<StepExecution> handle(StepExecutionSplitter stepSplitter, StepExecution stepExecution)](https://docs.spring.io/spring-batch/docs/current/api/org/springframework/batch/core/partition/PartitionHandler.html#handle\(org.springframework.batch.core.partition.StepExecutionSplitter,org.springframework.batch.core.StepExecution\)) |
| 3 | **PartitionHandler** 는 `StepExecutionSplitter` 를 통해 `Partitioner` 를 호출하여, 설정된 `gridSize` 에 따라 데이터를 분할합니다.   \- [Set<StepExecution> split(StepExecution stepExecution, int gridSize)](https://docs.spring.io/spring-batch/docs/current/api/org/springframework/batch/core/partition/StepExecutionSplitter.html#split\(org.springframework.batch.core.StepExecution,int\)) |
| 4 | **Partitioner** 는 각 스레드가 처리할 데이터의 범위 정보(`ExecutionContext`)를 생성하여 반환합니다.   \- [Map<String, ExecutionContext> partition(int gridSize)](https://docs.spring.io/spring-batch/docs/current/api/org/springframework/batch/core/partition/support/Partitioner.html#partition\(int\)) |

#### 2️⃣. 실행 (Execute)

👨🏼🔧 **역할:** **PartitionHandler** 가 **Partitioner** 로부터 받은 `ExecutionContext` 목록을 기반으로 `Worker Step` 을 병렬로 실행합니다.

🛠️ **동작:**

| 순서 | 동작 |
| --- | --- |
| 1 | **PartitionHandler** 는 `TaskExecutor` 를 통해 `gridSize` 만큼의 스레드를 생성하고, 각각에 `Worker Step` 을 할당합니다. |
| 2 | 각 스레드는 자신에게 할당된 `ExecutionContext` 를 참조하여 독립적으로 데이터 처리(Read-Process-Write)를 수행합니다. |
| 3 | **PartitionHandler** 는 모든 `Worker Step` 이 작업을 마치고 `ExitStatus` 를 반환할 때까지 대기합니다. |

#### 3️⃣. 취합 (Aggregate)

👨🏼🔧 **역할:** 모든 **Worker Step** 의 실행 결과를 하나로 합산하여 **Manager Step** 의 최종 상태를 결정하고 전체 작업을 마무리합니다.

🛠️ **동작:**

| 순서 | 동작 |
| --- | --- |
| 1 | 모든 **Worker Step** 의 실행이 완료되면, **PartitionHandler** 는 각 스텝의 실행 결과(`StepExecution`)를 수집하여 **Manager Step** 에 반환합니다. |
| 2 | `StepExecutionAggregator` 가 각 **Worker Step** 의 결과들을 종합하여 **Manager Step** 의 최종 상태를 업데이트하고 전체 Step을 마무리합니다.   \- [aggregate(StepExecution result, Collection<StepExecution> executions)](https://docs.spring.io/spring-batch/docs/current/api/org/springframework/batch/core/partition/support/StepExecutionAggregator.html#aggregate\(org.springframework.batch.core.StepExecution,java.util.Collection\)) |

이제 Partitioning의 핵심 인터페이스인 `Partitioner` 와 `PartitionHandler` 를 코드로 만나보겠습니다.

### Partitioner Interface

**Partitioner** 는 **‘작업을 어떻게 나눌 것인가’** 를 정의합니다.

| 구분 | 설명 |
| --- | --- |
| **역할** | 전체 데이터를 어떤 기준으로 나눌지 결정하고, 각 파티션에 대한 메타데이터(`ExecutionContext`)를 생성 |
| **핵심 메서드** | `Map<String, ExecutionContext> partition(int gridSize)` |
| **동작 방식** | \- `gridSize` 를 참고하여 데이터 분할 범위를 계산   \- 각 파티션 정보를 `ExecutionContext` 에 저장   \- 고유한 키를 가진 **Map** 형태로 반환 |
| **특징** | 비즈니스 로직을 직접 실행하지 않고, **‘어디서부터 어디까지 처리하라’** 는 범위 정보만 정의하는 작업 명세서 생성 |

아래는 **jobParameters** 로 받은 시작 날짜와 종료 날짜를 기준으로, 하루 단위 파티션을 생성하는 **DateRangePartitioner** 구현 예시입니다.

```markdown
class DateRangePartitioner(
    private val startDate: LocalDate,
    private val endDate: LocalDate
) : Partitioner {
    override fun partition(gridSize: Int): Map<String, ExecutionContext> {
        val daysBetween = ChronoUnit.DAYS.between(
            startDate,
            endDate.plusDays(1)
        )

        return (0 until daysBetween).associate { i ->
            val targetDate = startDate.plusDays(i)
            val context = ExecutionContext().apply {
                putString("targetDate", targetDate.toString())
            }
            "partition_$i" to context
        }
    }
}
```

> partition 메서드는 **gridSize** 를 인자로 받지만, 이 예제에서는 날짜를 기준으로 파티션을 생성하므로 직접 사용하지 않았습니다.
>
> partition 메서드가 반환하는 `Map<String, ExecutionContext>` 의 각 엔트리는 하나의 **Worker Step** 에 할당될 작업 단위가 됩니다.
>
> **ExecutionContext** 에는 해당 **Worker Step** 이 작업을 수행하는 데 필요한 모든 데이터(여기서는 **targetDate**)를 담아 전달할 수 있습니다.

### PartitionHandler Interface

**PartitionHandler** 는 **Partitioner** 가 생성한 작업 명세서들을 받아, **‘어떻게 병렬로 실행할 것인가’** 를 결정합니다.

| 구분 | 설명 |
| --- | --- |
| **역할** | 파티션의 실행 방식을 결정하고 전체 프로세스를 관리 |
| **주요 설정** | \- **gridSize**: 동시에 실행할 파티션(스레드)의 수   \- **taskExecutor**: 병렬 처리를 수행할 스레드 풀   \- **step**: 실제 로직을 수행할 **Worker Step** 지정 |
| **동작 방식** | \- **Partitioner** 를 호출하여 분할 정보를 가져옴   \- **TaskExecutor** 를 통해 **Worker Step** 에 `ExecutionContext` 를 전달하고 병렬로 실행   \- 모든 작업이 완료될 때까지 대기 후 최종 상태를 취합 |

아래 코드는 **Partitioner** 와 **PartitionHandler** 를 설정하여 배치 Job을 구성하는 예시입니다.

```markdown
@Bean
fun generateStatisticsJob(managerStep: Step): Job =
    JobBuilder("generateStatisticsJob", jobRepository)
        .incrementer(RunIdIncrementer())
        .start(managerStep)
        .build()

@Bean
fun managerStep(
    partitionHandler: PartitionHandler,
    partitioner: Partitioner,
): Step = StepBuilder("managerStep", jobRepository)
    .partitioner("dailyPartition", partitioner) // 어떻게 데이터를 쪼갤지
    .partitionHandler(partitionHandler) // 어떤 방식으로 실행할지
    .build()

@Bean
fun partitionHandler(workerStep: Step): PartitionHandler =
    TaskExecutorPartitionHandler().apply {
        setTaskExecutor(batchTaskExecutor()) // 사용할 스레드 풀
        step = workerStep // 실행할 Slave 스텝
        gridSize = GRID_SIZE // 병렬 스레드 개수
    }

@Bean
@StepScope
fun batchTaskExecutor(): TaskExecutor =
    ThreadPoolTaskExecutor().apply {
        corePoolSize = GRID_SIZE
        maxPoolSize = 10
        setThreadNamePrefix("batch-thread-")
        initialize()
    }

@Bean
@JobScope
fun partitioner(
    @Value("#{jobParameters['startDate']}") startDate: String,
    @Value("#{jobParameters['endDate']}") endDate: String
): Partitioner {
    val formatter = DateTimeFormatter.ISO_LOCAL_DATE
    return DateRangePartitioner(
        startDate = LocalDate.parse(startDate, formatter),
        endDate = LocalDate.parse(endDate, formatter)
    )
}

@Bean
fun workerStep(
    reader: ItemReader<String>,
    writer: ItemWriter<String>
): Step = StepBuilder("workerStep", jobRepository)
    .chunk<String, String>(CHUNK_SIZE, transactionManager)
    .reader(reader)
    .writer(writer)
    .build()
```

> 🔄 **Partitioner와 PartitionHandler의 협력 과정**
>
> 1. **Manager Step 실행**: Job이 시작되면, 파티셔닝을 총괄하는 `Manager Step` 이 실행됩니다.
> 2. **Partitioner의 작업 분할**: **Manager Step** 은 `Partitioner` 를 호출하여, 처리할 전체 데이터의 범위를 나누고 각 **Worker Step** 에 전달할 작업 명세서(`ExecutionContext`)를 생성합니다.
> 3. **PartitionHandler의 작업 분배**: **PartitionHandler** 는 **Partitioner** 가 생성한 작업 명세서를 받아, 설정된 **TaskExecutor** 를 통해 스레드를 생성하고 각 스레드에 `Worker Step` 을 할당합니다.
> 4. **Worker Step의 독립적인 처리**: 각 스레드에서 실행되는 **Worker Step** 은 자신에게 할당된 `ExecutionContext` 정보를 바탕으로 독립적인 **Reader-Processor-Writer** 로직을 수행합니다.
> 5. **결과 취합 및 종료**: 모든 **Worker Step** 의 실행이 완료되면, **PartitionHandler** 가 각 스텝의 실행 결과를 취합합니다. 이 결과를 바탕으로 **Manager Step** 의 최종 상태를 결정하고 전체 작업을 마무리합니다.

### Partitioning 설정 최적화: ThreadPool과 gridSize 튜닝

Partitioning의 성능은 `ThreadPoolTaskExecutor` 와 `gridSize` 설정에 크게 좌우됩니다. 이 두 요소를 어떻게 구성하느냐에 따라 병렬 처리의 효율이 극명하게 달라집니다.

#### ThreadPoolTaskExecutor 주요 설정

```markdown
@Bean
@StepScope
fun batchTaskExecutor(): TaskExecutor =
    ThreadPoolTaskExecutor().apply {
        corePoolSize = 6 // 기본 스레드 풀 크기
        maxPoolSize = 10 // 최대 스레드 풀 크기
        queueCapacity = 0 // 대기열 크기 (0 = 대기열 미사용)
        setThreadNamePrefix("batch-thread-") // 스레드 이름 접두사
        initialize()
    }
```

**각 설정 항목의 의미와 영향**

| 설정 항목 | 설명 | 권장 값 |
| --- | --- | --- |
| **corePoolSize** | 기본으로 유지할 스레드 수   \- Partitioning에서는 **gridSize** 와 동일하게 설정   \- Partitioning은 시작 시점에 모든 Worker Step을 동시에 실행 | **gridSize** 와 동일 |
| **maxPoolSize** | 최대 생성 가능한 스레드 수 (급격한 부하 증가 시 확장 여력) | **corePoolSize + 2~4** |
| **queueCapacity** | 작업 대기열 크기 (Partitioning은 초기에 모든 작업을 할당하므로 대기열 불필요) | **0 (대기열 미사용)** |
| **threadNamePrefix** | 스레드 이름 접두사 (로그 추적 및 디버깅에 활용) | **의미 있는 이름** |

#### gridSize 결정 전략

`gridSize` 는 동시에 실행할 Worker Step의 개수를 결정합니다. 적절한 값을 찾는 것이 성능 최적화의 핵심입니다.

**gridSize 결정 기준**

적정한 `gridSize` 를 찾는 가장 간단한 방법은 **서버의 CPU 코어 수를 기준으로 시작** 하는 것입니다.

```markdown
// 대부분의 배치 작업(DB 조회 + 데이터 가공)
val gridSize = (cpuCores * 1.5).toInt()  // 4코어 × 1.5 = 6
```

이후 실행하면서 다음과 같이 조정합니다.

| 실행 결과 | 조치 |
| --- | --- |
| CPU 사용률이 낮고(50% 이하) 작업이 느림 | **gridSize를 1.5배 증가** |
| 메모리 부족 에러 발생 | **gridSize를 절반으로 감소** |
| DB 커넥션 부족 에러 발생 | **gridSize 감소 또는 커넥션 풀 증가** |

### 병렬 처리의 함정: 메모리 부족 문제

Spring Batch의 `Partitioning` 기능으로 대량 데이터를 하루 단위로 분할하여 병렬로 처리하는 구조를 설계했습니다. 하지만 예상치 못한 문제가 발생했습니다.

- **스레드당 데이터**: 수백만 건 (하루 치)
- **병렬 실행 스레드**: 6개
- **메모리 적재 시도**: 수백만 건 × 6 = **수천만 건**

결국 수천만 건에 달하는 방대한 데이터가 한꺼번에 메모리에 적재되려 했고, 서버는 **OOM(Out of Memory)** 의 늪에 빠졌습니다.

데이터를 쪼개 병렬로 처리하는 것만으로는 부족했습니다. 한정된 메모리 자원을 효율적으로 사용하려면, 데이터를 한 번에 조회하지 않고 일정한 크기로 나누어 처리하는 최적화가 필요했습니다.

## ItemReader 최적화: 한 입씩 꺼내 먹는 Cursor 스트리밍

거대한 케이크를 한꺼번에 접시에 올리면 넘치고 먹는 사람도 부담을 느끼게 됩니다. 데이터 역시 한 번에 많은 양을 메모리에 적재하는 대신, 케이크 조각을 한 입씩 꺼내 먹듯 데이터를 읽는 `ItemReader` 로 전환해야 했습니다.

이미 **Partitioner** 로 날짜별로 작업 범위를 분할한 상태여서, 남은 과제는 각 **Worker Step** 내부에서 메모리 점유율을 최소화하며 데이터를 읽어오는 것이었습니다.

Spring Batch에서 제공하는 MongoDB 기반의 `ItemReader` 는 크게 두 가지 방식이 있습니다.

👉🏻 **Paging vs Cursor**

| 비교 항목 | MongoPagingItemReader | MongoCursorItemReader |
| --- | --- | --- |
| 조회 방식 | 페이지 단위로 데이터를 끊어서 조회   skip()과 limit() 사용 | DB 서버와 커서를 유지하며 스트리밍 방식으로 데이터를 한 건씩 호출 |
| 성능 특징 | 뒤쪽 페이지로 갈수록 skip 오버헤드 급증 | 데이터 위치와 상관없이 일정한 고속 성능 유지 |
| 메모리 사용 | 페이지 단위로 데이터를 로드하여 관리 | 스트리밍 방식으로 메모리 점유율이 매우 낮음 |
| 데이터 정합성 | 읽는 도중 데이터가 추가/삭제되면 중복/누락 발생 가능 | 커서 오픈 시점의 스냅샷 기반으로 비교적 안정적 |

제한된 메모리 환경에서 수백만 건의 데이터를 안정적으로 처리하기 위해 `MongoCursorItemReader` 를 채택하게 되었습니다. 그 이유는 `MongoPagingItemReader` 의 **skip() 연산의 성능 특성** 때문입니다.

`MongoPagingItemReader` 는 페이지 단위로 데이터를 조회하며 **skip()** 과 **limit()** 을 사용합니다. 문제는 MongoDB의 `skip(N)` 연산이 **‘결과 세트의 처음부터 N개의 문서를 순회해야 한다’** 는 점입니다. 예를 들어 페이지 크기 1,000의 1,000번째 페이지를 조회하려면 앞의 999,000개 문서를 모두 스캔해야 하므로, 페이지가 뒤로 갈수록 응답 시간이 선형적으로 증가합니다(*O(N²)*). 수백만 건을 처리하는 배치 작업에서는 이러한 오버헤드가 치명적입니다.

> 📌 **MongoDB 공식 문서**: “The skip() method requires the server to scan from the beginning of the input results set before beginning to return results. As the offset increases, skip() will become slower.” — [cursor.skip()](https://www.mongodb.com/docs/manual/reference/method/cursor.skip/)

반면 `MongoCursorItemReader` 는 MongoDB의 **서버 사이드 커서** 를 사용합니다. 커서는 한 번 열린 후 서버에서 현재 위치를 유지하며, 설정된 `cursorBatchSize` 만큼의 데이터를 배치로 가져옵니다. **skip()** 없이 다음 문서로 바로 이동하므로, 데이터 위치와 관계없이 문서당 *O(1)* 의 일정한 비용을 유지합니다. 전체 컬렉션 처리의 시간 복잡도는 *O(N)* 으로, 대규모 배치 작업에 훨씬 적합합니다.

### Spring Batch에서의 MongoCursorItemReader 구현

Spring Batch의 `MongoCursorItemReader` 는 MongoDB의 **서버 사이드 커서** 를 활용하여 효율적인 데이터 스트리밍을 구현합니다.

> 📚 **MongoCursorItemReader**
>
> The `MongoCursorItemReader` is an ItemReader that reads documents from MongoDB by using a streaming technique. Spring Batch provides a MongoCursorItemReaderBuilder to construct an instance of the MongoCursorItemReader.
>
> *by. [Spring Batch Documentation](https://docs.spring.io/spring-batch/reference/readers-and-writers/item-reader-writer-implementations.html#databaseReaders)*

**동작 프로세스**

1️⃣. **쿼리 빌딩 및 설정**
데이터를 읽기 전, **어떤 데이터를 어떻게 가져올지 정의** 하는 단계

```markdown
// MongoCursorItemReader.java @Since: 5.1
private Query createQuery() {
    // ...
    mongoQuery.cursorBatchSize(batchSize); // 한 번에 가져올 데이터 묶음
    mongoQuery.limit(limit);
    if (maxTime != null) {
        mongoQuery.maxTime(maxTime);
    }
    else {
        mongoQuery.noCursorTimeout(); // 배치 작업 중 커서가 서버에서 자동으로 닫히는 것을 방지
    }

    return mongoQuery;
}
```

2️⃣. **Cursor 오픈 및 초기 배치 반환**
MongoDB 서버에 쿼리를 전송하고 커서를 생성하는 단계

```markdown
@Override
protected void doOpen() throws Exception {
    // 쿼리 객체 준비
    Query mongoQuery = (queryString != null) ? createQuery() : query;

    // MongoTemplate을 통해 Stream 형태로 데이터를 오픈 (Cursor 생성)
    Stream<? extends T> stream = template.stream(mongoQuery, targetType, collection);

    // 자원 해제가 가능한 CloseableIterator로 변환
    this.cursor = streamToIterator(stream);
}
```

**MongoDB 서버의 내부 동작:**

- 서버는 즉시 커서 객체를 생성하고 고유한 커서 ID를 할당합니다.
- 첫 번째 배치(설정된 `batchSize` 만큼)를 클라이언트에 즉시 반환합니다.
- 서버는 **쿼리 실행 계획을 메모리에 유지** 하며, 다음 읽기 위치 정보를 저장합니다.
```markdown
// MongoDB 서버의 초기 응답 구조
{
  cursor: {
    id: NumberLong("123456789"), // 서버가 할당한 커서 ID
    ns: "payment", // 네임스페이스
    firstBatch: [ ... ] // 초기 문서들
  },
  ok: 1
}
```

3️⃣. **데이터 스트리밍 (getMore를 통한 반복 호출)**
Spring Batch의 Chunk 프로세스 안에서 **한 건씩 데이터를 뽑아내는** 단계

```markdown
@Override
protected T doRead() throws Exception {
    // 커서가 가리키는 다음 데이터가 있으면 반환, 없으면 null(배치 종료)
    return cursor.hasNext() ? cursor.next() : null;
}
```

**MongoDB 서버의 내부 동작:**

- **cursor.next()** 호출 시 클라이언트 메모리 버퍼를 확인합니다.
- 버퍼가 비어있으면 드라이버가 자동으로 `getMore` 명령을 서버에 전송합니다.
- 서버는 저장해둔 위치 정보를 참조하여 **skip() 없이** 다음 배치를 즉시 반환합니다.
```markdown
// getMore 명령 구조
{
  getMore: NumberLong("123456789"),  // 이전에 받은 커서 ID
  collection: "ledger",
  batchSize: 1000
}
```

**Paging vs Cursor 비교:**

|  | Paging 방식 | Cursor 방식 |
| --- | --- | --- |
| 조회 | 1,000번째 페이지 조회 | 1,000번째 배치 조회 |
| 클라이언트 | db.find().skip(999000).limit(1000) | getMore(cursorId, batchSize=1000) |
| 서버 | 999,000개 문서 순회 → 1,000개 반환 | 저장된 위치 정보 참조 → 다음 1,000개 즉시 반환 |
| 비용 | 매 페이지마다 누적(skip + limit) | 항상 일정(batchSize) |

4️⃣. **자원 반납**
배치가 끝나거나 에러가 났을 때 **서버 자원을 정리** 하는 단계

```markdown
@Override
protected void doClose() throws Exception {
    // 명시적으로 커서를 닫아 MongoDB 서버의 메모리 해제
    this.cursor.close();
}
```

**MongoDB 서버의 내부 동작:**

- 서버는 각 커서에 대해 최소한의 메타데이터만 유지합니다.
- 실제 문서 데이터는 배치 단위로 전송 후 즉시 메모리에서 해제됩니다.
- 기본적으로 커서는 30분간 활동이 없으면 자동 타임아웃됩니다. (위 1단계의 [noCursorTimeout()](https://www.mongodb.com/ko-kr/docs/manual/reference/method/cursor.noCursorTimeout/) 으로 방지)

이러한 내부 메커니즘 덕분에 `MongoCursorItemReader` 는 수백만 건의 데이터를 처리할 때도 일정한 성능을 유지할 수 있습니다.

`MongoCursorItemReader` 는 아래와 같이 적용할 수 있습니다.

```markdown
@Bean
@StepScope
fun reader(
    @Value("#{stepExecutionContext['startDate']}") startDate: String,
    @Value("#{stepExecutionContext['endDate']}") endDate: String
): MongoCursorItemReader<PaymentLedger> {
    val query = ...

    return MongoCursorItemReaderBuilder<PaymentLedger>()
        .name("reader")
        .template(mongoTemplate)
        .collection(LEDGER_COLLECTION)
        .targetType(PaymentLedger::class.java)
        .query(query)
        .sorts(mapOf("orderNumber" to Sort.Direction.ASC))
        .batchSize(1000)
        .build()
}
```

이렇게 Cursor 방식을 적용함으로써 메모리 효율성과 안정성을 모두 확보할 수 있었습니다.

- **메모리 효율성**: 페이징 방식은 다음 페이지를 조회할 때마다 이전 데이터를 **skip** 해야 하므로 뒤로 갈수록 느려지지만, 커서는 스트리밍 방식이라 메모리 사용량이 일정하게 유지됩니다.
- **안정성**: 여러 **Worker Step** 이 병렬로 실행되더라도, 각 스레드가 커서를 통해 필요한 만큼만 데이터를 가져오기 때문에 OOM 발생 위험을 원천적으로 차단할 수 있습니다.

> 💡 **참고.** Aggregation Pipeline으로 조회하면 안될까❓
>
> MongoDB의 Aggregation Pipeline은 데이터 변환(`$group`, `$project` 등)과 복잡한 집계 연산에 특화되어 있지만, 각 스테이지가 **100MB 메모리 제한** 을 가지며 초과 시 디스크 I/O가 발생합니다.
>
> 이번 작업은 원장 데이터를 읽어 애플리케이션 레벨에서 통계로 재구성하는 과정으로, 조회 단계에서는 단순히 필터링된 원본 데이터를 순차적으로 읽기만 하면 되었습니다.
>
> 따라서 **배치 단위로 스트리밍** 하는 Cursor 방식이 메모리 효율성과 처리량 측면에서 더 적합했습니다.

## ItemWriter 최적화: 케이크 조각을 빠르게 먹는 Bulk Operations

데이터를 읽는 속도보다 쓰는 속도가 느리면, 메모리에 데이터가 계속 쌓여 결국 OOM이 발생할 수 있습니다. 마치 케이크 조각이 접시에 계속 올라오는데 먹는 속도가 느리면 접시가 넘치는 것과 같습니다.

이러한 병목 현상을 해소하고, 메모리 관리를 효율적으로 하기 위해 **Bulk Operations** 를 적용했습니다.

🤷🏼♂️ **왜 Bulk Operations인가?**

- **네트워크 효율성**: Spring Batch의 Chunk 구조를 활용하면, 설정한 청크 사이즈만큼 데이터가 모였을 때 단 한 번의 통신으로 일괄 **INSERT** 를 수행합니다. 예를 들어, 1,000번의 개별 **INSERT** 를 1번의 **Bulk Insert** 로 줄여 I/O 오버헤드를 획기적으로 낮출 수 있습니다.
- **메모리 관리**: 쓰기 속도가 빨라지면 **ItemProcessor** 가 생성한 객체들이 메모리에 머무는 시간이 줄어들어, 전체적인 메모리 사용량이 안정화되고 GC 부담이 감소합니다.
```markdown
@Bean
fun writer(): ItemWriter<Statistics> = ItemWriter { items ->
    if (items.isEmpty) return@ItemWriter

    val bulkOps = mongoTemplate.bulkOps(
        BulkOperations.BulkMode.UNORDERED,
        Statistics::class.java,
        LEDGER_BACKUP_COLLECTION
    )

    bulkOps.insert(items.toList())
    bulkOps.execute()
}
```

Spring Batch의 Chunk 지향 모델 덕분에, `write()` 가 종료되면 해당 Chunk 리스트는 스코프를 벗어나므로 별도의 **list.clear()** 호출 없이도 GC 대상이 되어 메모리에서 효율적으로 해제됩니다.

**mongoTemplate.bulkOps** 를 사용할 때 `UNORDERED` 모드를 채택한 이유는, 각 데이터는 서로 독립적이며 저장 순서가 결과에 영향을 주지 않았기 때문입니다. 순서를 보장할 필요가 없으면 MongoDB 내부에서 병렬 쓰기 최적화가 가능합니다. 또한 특정 작업이 실패해도 나머지는 계속 진행되므로 대량 처리에도 유리합니다.

> 📚 **BulkOperations**
>
> Bulk operations for insert/update/remove actions on a collection. …
>
> This interface defines a fluent API to add multiple single operations or list of similar operations in sequence which can then eventually be executed by calling execute().
>
> by. [Interface BulkOperations](https://docs.spring.io/spring-data/mongodb/docs/current/api/org/springframework/data/mongodb/core/BulkOperations.html)

### DefaultBulkOperations 동작 원리

1️⃣. **모델 큐잉**
**DefaultBulkOperations.insert(List)** 가 호출되면, 전달된 모든 객체는 MongoDB 드라이버가 이해할 수 있는 `WriteModel` 객체로 변환되어 내부 리스트에 저장됩니다.

2️⃣. **벌크 타입 결정**
벌크 연산을 생성할 때 결정된 모드에 따라 처리 방식이 달라집니다.

- `Ordered` (default): 목록 순서대로 실행하며, 중간에 에러가 발생하면 중단됩니다.
- `Unordered`: 순서 상관없이 병렬 실행이 가능하며, 에러가 발생해도 나머지는 진행됩니다.

3️⃣. **실행 명령**
Spring Batch의 MongoItemWriter가 Chunk 단위 처리를 끝내고 마지막에 **bulkOps.execute()** 를 호출하는 시점입니다.

```markdown
@Override
public BulkWriteResult execute() {
    //...
    BulkWriteResult result = mongoOperations.execute(collectionName, this::bulkWriteTo);
    // ...
}

private BulkWriteResult bulkWriteTo(MongoCollection<Document> collection) {
    // ...
    return collection.bulkWrite(
        // 메모리에 쌓아둔 models 리스트를 통째로 MongoDB 드라이버에 전달
        models.stream()
            .map(this::extractAndMapWriteModel)
            .collect(Collectors.toList()),
        bulkOptions
    );
    // ...
}
```

4️⃣. **단일 네트워크 왕복**
드라이버는 models 리스트를 하나의 메시지로 패키징하여 MongoDB 서버로 전송합니다. 서버는 이를 수신하여 한 번에 처리한 후, 결과(성공 개수, 실패 에러 등)를 한 번에 반환합니다.

### saveAll vs Bulk Operations: 쓰기 방식 비교

MongoDB에 여러 건의 데이터를 저장할 때 `MongoRepository.saveAll()` 과 `BulkOperations.insert()` 를 사용할 수 있습니다. 하지만 두 방식의 내부 동작은 크게 다르며, 대규모 배치 처리에서는 이 차이가 성능에 결정적인 영향을 미칩니다.

✅ **saveAll() 방식**

1. **saveAll()** 은 각 문서에 대해 **개별적으로 `save()` 메서드를 호출**
2. 각 save() 호출은 다음 단계를 거침:
	- 문서에 `_id` 가 있는지 확인
		- 있으면 `UPDATE` 연산 (기존 문서 조회 후 업데이트)
		- 없으면 `INSERT` 연산
3. 각 연산마다 **별도의 네트워크 요청** 발생

✅ **Bulk Operations insert() 방식**

1. 모든 문서를 `WriteModel` 객체로 변환하여 내부 리스트에 저장
2. `execute()` 호출 시 **단 한 번의 `bulkWrite` 명령** 으로 모든 문서를 서버에 전송
3. MongoDB 서버가 내부적으로 최적화하여 일괄 처리
4. 단 한 번의 응답으로 모든 결과 반환

**성능 및 특성 비교**

| 비교 항목 | saveAll() | Bulk Operations insert() |
| --- | --- | --- |
| **네트워크 요청 횟수** | N번 (N = 문서 수) | 1번 (단일 일괄 요청) |
| **내부 동작** | 각 문서마다 INSERT/UPDATE 판별 | 모두 INSERT로 간주 |
| **서버 부하** | 각 요청마다 커넥션 할당 및 해제 | 단일 커넥션으로 일괄 처리 |
| **예외 처리** | 첫 번째 실패 시 즉시 예외 발생 | UNORDERED: 일부 실패해도 나머지 계속 |
| **사용 사례** | 소량 데이터, UPDATE 포함 | 대용량 INSERT, 배치 처리 |

> 💡 **Tip.** Spring Data MongoDB의 **MongoRepository.saveAll()** 은 내부적으로 각 문서를 개별적으로 처리하므로, 대규모 배치에서는 **반드시 `BulkOperations` 를 사용** 하여 일괄 쓰기를 수행해야 합니다. 특히 수천만 건 이상의 데이터를 처리할 때 성능 차이가 크게 나타납니다.

## 성능 비교: 10배 더 빠르게 즐기는 완벽한 케이크 시식 코스

대량 데이터 처리를 위해 적용된 최적화 전략의 순수한 성능을 비교하기 위해, 별도의 비즈니스 로직 없이 **단순히 데이터를 읽고 다시 쓰는 배치** 로 테스트를 진행했습니다.

아래 그래프는 데이터 규모가 커질수록 **기본 배치 방식(파란색)** 과 **최적화된 방식(빨간색)** 간의 처리 시간 차이를 보여줍니다.

- 최적화된 방식은 **‘Partitioning + Cursor Reader + Bulk Operations’** 이 적용된 방식
- 두 방식 모두 **chunkSize** 는 1,000으로 동일하게 설정
- 그래프의 Y축은 비교하기 쉬운 10진법 분(decimal minute) 단위로 표현
![partitioning compare](https://tech.kakaopay.com/_astro/image-3.4e50ee80_Z2neoOf.png)

partitioning compare

**데이터 건수별 실제 처리 시간**

| 데이터 건수 | 기본 방식 | 최적화 방식 | 성능 차이 |
| --- | --- | --- | --- |
| 10,000 | 3초 | 2초 | 1.5배 |
| 100,000 | 33초 | 15초 | 2.2배 |
| 1,000,000 | 11분 22초 | 1분 53초 | 약 6배 |
| 5,000,000 | 1시간 37분 25초 | 8분 55초 | 약 10.9배 |

✅ **확장성 차이**: 1만 건 정도의 소량 데이터에서는 두 방식의 차이가 미미하지만, 데이터가 100만 건, 500만 건으로 늘어날수록 기본 방식은 처리 시간이 기하급수적으로 증가합니다. 반면, 최적화 방식은 훨씬 완만한 증가 폭을 유지합니다.

✅ **성능 격차 심화**: 500만 건 처리 시, 기본 방식(약 97분) 대비 최적화 방식(약 9분)은 **약 10.9배** 의 압도적인 속도 향상을 보였습니다.

✅ **최적화 전략의 효과**:

- **Partitioning**: 데이터를 분할하여 병렬로 처리함으로써 전체 작업 시간을 단축했습니다.
- **Cursor Reader**: 스트리밍 방식으로 데이터를 읽어 메모리 부하를 줄이고, 대량의 데이터에서도 일정한 읽기 속도를 유지했습니다.
- **Bulk Operations**: 일괄 쓰기를 통해 오버헤드를 최소화하고, 처리된 객체를 빠르게 메모리에서 해제하여 성능을 향상시켰습니다.

결국 데이터가 많아질수록 단순 병렬 처리만으로는 분명 한계가 존재합니다. 메모리 효율(`Cursor Reader`)과 쓰기 최적화(`Bulk Operations`)를 결합한 `Partitioning` 전략이 필수입니다.

배치 성능에 관심이 많으시다면 아래 글들도 함께 읽어보시는 것을 추천합니다.

- [Batch Performance를 고려한 최선의 Reader](https://tech.kakaopay.com/post/ifkakao2022-batch-performance-read/#%EC%83%88%EB%A1%9C%EC%9A%B4-cursoritemreader)
- [Batch Performance를 고려한 최선의 Aggregation](https://tech.kakaopay.com/post/ifkakao2022-batch-performance-aggregation/#itemreader)
- [Spring Batch 애플리케이션 성능 향상을 위한 주요 팁](https://tech.kakaopay.com/post/spring-batch-performance/#in-update-%EC%84%B1%EB%8A%A5-%EC%B8%A1%EC%A0%95)

## 마치며: 거대한 케이크를 안전하게 먹는 레시피

처음 수억 건의 데이터라는 거대한 케이크를 마주했을 때 **OOM 이슈** 는 어쩌면 당연한 결과였습니다. 하지만 문제를 하나씩 분해하고 Spring Batch의 도구들을 조합하며, **메모리** 라는 한정된 접시 위에서 케이크를 안전하게 먹는 법을 배웠습니다.

이번 경험을 통해 완성한 ‘거대한 케이크 맛있게 쪼개 먹는 방법’의 핵심을 정리하면 다음과 같습니다.

- **케이크 자르기 (Partitioning)**: 거대한 케이크를 한 입 크기의 조각으로 자릅니다.
- **조각을 그릇에 올리고 포크로 떠먹기 (Cursor Reader)**: 잘라낸 조각을 한 조각씩 그릇에 올리고, 포크로 여러 조각을 떠서 계속 입으로 가져옵니다.
- **모아서 한 번에 삼키기 (Bulk Operations)**: 입에 든 케이크가 적당히 쌓이면 한 번에 꿀꺽 삼킵니다.

단순히 스레드 수만 늘리는 것은 케이크를 더 빨리 먹으려고 포크만 여러 개 사용하는 것과 같습니다. 오히려 제어되지 않은 병렬성은 OOM이라는 부메랑이 되어 돌아왔죠. 중요한 것은 데이터의 유입부터 소멸까지, 즉 케이크를 자르고, 그릇에 올리고, 먹고, 삼키는 전 과정을 시스템의 처리 능력에 맞춰 세밀하게 설계하는 것임을 깨달았습니다.

다만, Partitioning이 만능은 아닙니다. 학습 곡선과 설정 복잡도가 상대적으로 높기 때문에, 처음부터 Partitioning을 도입하기보다는 **멀티스레드, 쿼리 최적화, 캐싱 전략을 먼저 시도** 해보시길 권장합니다. 이러한 기본 최적화 기법으로도 성능 개선이 충분하지 않을 때, Partitioning을 고려하는 것이 좋은 전략이라고 생각합니다.

혹시 지금 거대한 데이터 앞에서 막막함을 느낀다면, 가장 먼저 ‘어떻게 나눌 수 있을까?‘를 고민해보시길 바랍니다. 기술적인 정답은 환경마다 다르겠지만, **‘리소스를 어떻게 효율적으로 사용할 것인가’** 에 대한 고민은 언제나 좋은 해답의 시작점이 될 것입니다. 이 글이 비슷한 과제를 안고 고민하는 분들에게 작은 실마리가 되길 바랍니다.

![wi.fi](https://tech.kakaopay.com/_astro/wi_fi.9adf0b20_12Q6ej.webp)

**wi.fi**

카카오페이 정산플랫폼팀에서 백엔드 개발을 하고 있는 와이입니다. 더 나은 세상을 만드는 일에 관심이 많습니다.
