---
title: "로그 데이터 운영 비용 효율화— Spring Batch 병렬 처리 전략"
source: "https://medium.com/@hyeon9mak/%EB%A1%9C%EA%B7%B8-%EB%8D%B0%EC%9D%B4%ED%84%B0-%EC%9A%B4%EC%98%81-%EB%B9%84%EC%9A%A9-%ED%9A%A8%EC%9C%A8%ED%99%94-spring-batch-%EB%B3%91%EB%A0%AC-%EC%B2%98%EB%A6%AC-%EC%A0%84%EB%9E%B5-fea8cbc019db"
author:
  - "[[Hyeon9mak]]"
published: 2026-03-05
created: 2026-03-08
description: "Spring Batch 가 제공하는 병렬 처리 전략들을 알아보고, 상황별로 올바른 전략을 선택하는 방법과, 저는 결국 어떤 전략을 선택했는지 알아보겠습니다."
tags:
  - "clippings"
---

> [!summary]
> Spring Batch parallel processing strategies for migrating log data from RDB to AWS S3. Compares AsyncItemProcessor, Multi-threaded Step, and Partitioning, recommending Partitioning for its transaction safety and failure isolation.

[Sitemap](https://medium.com/sitemap/sitemap.xml)

서비스를 운영하다 보면 시시각각 변화하는 트랜잭션 데이터뿐 아니라, 시스템의 모든 발자취를 담은 로그성 데이터도 함께 쌓게 됩니다. 트랜잭션 데이터는 비즈니스 흐름에 따라 생성-수정-삭제 되는 자연스러운 생명주기를 가지지만, 로그성 데이터는 별도로 관리해주지 않는다면 끊임없이 축적됩니다.

만약 로그성 데이터를 관계형 데이터베이스(RDB)에 쌓는다면 조회에 대한 부하 뿐만 아니라 인덱스 생성 및 관리에도 부담이 생기게 됩니다. 대부분의 RDB 는 가용성을 확보하기 위해 Replication 을 이용하므로 부담이 배로 증가합니다. 때문에 AWS S3 와 같은 Object Storage 로 데이터를 이관-적재하여 운영 비용을 효율화 할 수 있습니다.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*_UrOrf5UEW8NpOdR2JIuQQ.png)

이번 시리즈에서는 RDB 에 쌓인 로그성 데이터를 AWS S3 로 이관-적재하면서 거쳤던 고민들과 최종적으로 운영 비용을 효율화 시켰던 개인적인 경험에 대해 공유하려고 합니다. 데이터 운영 전문가의 노하우가 아닌 백엔드 엔지니어의 온몸 비틀기로 재밌게 봐주셨으면 합니다.

전체적인 시리즈 순서는 아래와 같습니다.

1. Spring Batch 병렬 처리 전략
2. [No-offset Pagination (with UUIDv4)](https://medium.com/%40hyeon9mak/%EB%A1%9C%EA%B7%B8-%EB%8D%B0%EC%9D%B4%ED%84%B0-%EC%9A%B4%EC%98%81-%EB%B9%84%EC%9A%A9-%ED%9A%A8%EC%9C%A8%ED%99%94-no-offset-pagination-with-uuidv4-1c048b47e8d2)
3. [Parquet 압축과 S3 Glacier](https://medium.com/%40hyeon9mak/%EB%A1%9C%EA%B7%B8-%EB%8D%B0%EC%9D%B4%ED%84%B0-%EC%9A%B4%EC%98%81-%EB%B9%84%EC%9A%A9-%ED%9A%A8%EC%9C%A8%ED%99%94-parquet-%EC%95%95%EC%B6%95%EA%B3%BC-s3-glacier-a1aab5a83f2b)

이미 많은 분들이 아시듯 Spring Batch 는 주로 대용량 데이터를 효율적으로, 자동으로 처리 하기 위해 사용합니다. Batch 는 비실시간 작업인 경우가 많아 뛰어난 성능을 요구하진 않지만, 데이터 양이 많아 처리 시간이 지나치게 오래 걸린다던지, 다른 작업과 연결되어 최소한의 처리 시간이 요구되는 경우도 분명히 존재합니다. 그리고 저희는 이럴 때 Spring Batch 가 제공하는 병렬 처리 전략을 채택하여 작업 처리 시간을 크게 단축시킬 수 있습니다.

이번 글에서는 Spring Batch 가 제공하는 병렬 처리 전략들을 알아보고, 상황별로 올바른 전략을 선택하는 방법과, 저는 결국 어떤 전략을 선택했는지 알아보겠습니다.

이번 글의 목차는 아래와 같습니다.

- Spring Batch 병렬 처리 전략 필요성
- Spring Batch Step 에서 데이터를 처리하는 단위
- Spring Batch 병렬 처리 전략 종류
- 시나리오별 권장 전략

## Spring Batch 병렬 처리 전략 필요성

Batch 작업을 병렬로 처리하고 싶을 때 Spring Batch 가 제공하는 방법 외에도 직접 구현이 가능합니다. 대표적으로 Java CompletableFuture, Kotlin Coroutines 등을 이용해서 비동기적으로 작업을 처리시킬 수 있습니다.

```c
// 기본적인 처리 로직
fun processItem(item: Item): ProcessedItem {
    return ProcessedItem(item)
}

// CompletableFuture 를 이용한 병렬 처리 로직
fun processItems(items: List<Item>): List<ProcessedItem> {
  val executor = Executors.newFixedThreadPool(10)
  return try {
    items.map { item ->
      CompletableFuture.supplyAsync({ ProcessedItem(item) }, executor)
    }.map { it.join() }
  } finally {
    executor.shutdown()
  }
}
```

그러나 이와 같은 방법으로 직접 구현을 할 경우 여러가지 문제가 생기기 쉽습니다.

**Collection 단위로 인해 발생하는 비효율
**`processItems` 메서드 파라미터로 넘어온 1,000,000 건의 데이터 중 1건의 데이터에 문제가 발생하여 Retry 가 발생했다고 가정해볼까요? 단 1건의 데이터에 문제가 발생했음에도 불구하고, `processItems` 메서드 내부에서는 1,000,000 건의 데이터를 모두 재처리해야 합니다.

Skip 을 적용하면 어떨까요? 1,000,000 건의 데이터들 중, 1건의 데이터에 문제가 발생하여 Retry 가 진행된다고 가정해봐도 문제가 생깁니다. 1건을 제외하고 정상 처리가 가능한 999,999 건의 데이터가 모두 Skip 됩니다.

**Transaction 관리 부담
**Spring 은 기본적으로 ThreadLocal 을 이용해 Thread 단위의 Transaction 을 관리합니다. 따라서 Spring Batch Step 내부에서 별도의 병렬 처리 코드를 작성하는 경우, 병렬 처리에 사용된 Thread 들은 Step 의 Transaction Context 를 공유하지 못하게 됩니다.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/0*L7YKxwAJiuKpHJsv)

새롭게 생성된 Thread 들은 Step 의 Transaction Context 를 알지 못하기 때문에 Transaction 을 보장 받지 못하게 됩니다. Step Chunk Thread 가 rollback 될 때 병렬 처리에 사용된 Thread 들의 작업은 rollback 되지 않고, JPA 사용 환경에서 lazy loading, persistence context 등도 활용할 수 없습니다.

**예외 처리 복잡도 증가**
Spring Batch 에서는 Step 을 생성하는 과정에서 Chunk 단위 데이터 처리에 Skip, Retry 와 같은 강력한 예외 처리 기능을 설정할 수 있습니다. Spring Batch 에서 제공하는 병렬 처리 전략을 이용하는 경우 이를 자연스럽게 활용할 수 있으나, 직접 병렬 처리를 구현하는 경우 Skip, Retry 와 같은 예외 처리 기능을 활용하기 위해 별도 코드 작성이 필요하게 됩니다. 특히 CompletableFuture 를 사용한 위 예시 같은 경우, 예외가 CompletionException 으로 감싸져 전파되기 때문에 아래와 같은 추가 예외 처리가 필요합니다.

```c
fun processItems(items: List<Item>): List<ProcessedItem> {
  val executor = Executors.newFixedThreadPool(10)
  return try {
    items.map { item ->
      try {
        CompletableFuture.supplyAsync({ ProcessedItem(item) }, executor)
      } catch (exception: Exception) {
        throw exception.cause ?: throw exception
      }
    }.map { it.join() }
  } finally {
    executor.shutdown()
  }
}
```

Spring Batch 가 제공하는 병렬처리 전략들(AsyncItemProcessor, Multi-threaded Step 등)이 모든 상황에서 만능은 아니지만, 대부분의 경우 위와 같은 문제를 쉽게 해결할 수 있도록 동작을 보장해주기 때문에 이를 이해하는 것이 유리합니다. 각 상황 별로 어떤 전략을 선택할지 구분할 수 있는 지혜가 필요하겠습니다.

## Spring Batch Step 에서 데이터를 처리하는 단위

Spring Batch 에서 제공하는 병렬처리 전략을 활용하기 위해서는 Spring Batch Step 내부에서 데이터를 어떤 단위로 처리 하는지 먼저 이해해야 합니다.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/0*iwIyFB-ABOYclcRC.png)

[https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing.html](https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing.html)

대량 데이터를 처리할 땐 Chunk 기반의 처리 방식(Chunk-oriented Processing)을 사용합니다. Chunk 기반 처리 방식은 Step 이 데이터를 일정 단위로 읽고(Read), 처리하고(Process), 기록(Write)하는 방식을 의미합니다. 그림을 자세히 살펴보면 `read() - read() - process() - process() - write()` 와 같은 흐름을 갖고 있습니다.

Chunk 기반 처리 방식에서 각 작업들은 아래와 같은 특징을 갖습니다.

- Reader: Item 단위로 하나씩 데이터를 읽음. Chunk 수 만큼 반복.
- Processor: Reader 가 읽어온 Item 단위 데이터 가공.
	Processor 가 없는 경우 Reader 가 읽어온 Item 을 그대로 Write 로 전달.
- Writer: Item 들을 모아 Chunk 단위로 한꺼번에 기록.

**ItemReader Paging 처리
**Reader 에서 Item(데이터) 단위로 RDB 에 SELECT query 를 수행하는 것은 지나치게 비효율적입니다. 그렇다고 모든 데이터를 한꺼번에 읽어올 순 없습니다. 분명 메모리에 큰 부담을 제공하니까요.

때문에 Reader 내부적으로는 Paging 처리를 이용해서 적정한 크기의 데이터를 읽어오도록 합니다. Page 단위로 얻어온 데이터를 `List<Item>` 로 변환하여 Processor 에게 넘길 수도 있고, Iterator 를 활용해 Item 단위로 하나씩 넘길 수도 있습니다.

아래와 같은 예시를 들어보겠습니다.

- RDB 에 10,000 건의 데이터가 존재한다.
- Chunk 크기를 1,000 으로 설정한다.
- Reader 는 Paging 처리를 이용해 한 번에 100 건의 데이터를 읽어온다.

이 때 Iterator 를 이용해 하나씩 넘기는 과정을 살펴보면 다음과 같게 됩니다.

1. Reader 가 100 건의 데이터를 읽어온다.
2. Reader 가 읽어온 100 건의 데이터를 Item 단위로 하나씩 Step 에 전달한다.
3. Step 은 Item 단위로 Processor 를 호출해 데이터를 가공한다.
4. Step 은 가공된 Item 들을 모아 Chunk 크기(1,000) 가 될 때까지 대기한다.
5. Step 은 Chunk 크기(1,000) 가 될 때마다 Writer 를 호출해 데이터를 기록한다.
6. 위 과정을 모든 데이터(10,000 건) 가 처리될 때까지 반복한다.

간단하게 Spring Batch Step 에서 데이터를 처리하는 단위를 이해했다면, 이번엔 각 병럴 처리 전략들의 컨셉과 특징을 이해할 차례입니다.

## Spring Batch 병렬 처리 전략 — AsyncItemProcessor

![](https://miro.medium.com/v2/resize:fit:640/format:webp/0*lSraVV2Heij2N9f2)

AsyncItemProcessor 는 Chunk 동작 단위 중 process 단계에서 새로운 thread 를 할당해 비동기적으로 Item 을 처리합니다. **process 단계가 완료되면 writer 로 Feature 를 넘기고, writer 단계에서 Future 를 종합하여 기록** 합니다.

```c
@Bean
fun eatStep(
  jobRepository: JobRepository,
  transactionManager: PlatformTransactionManager,
  eatableCookLogReader: ItemReader<EatableCookingLog>,
  asyncItemProcessor: AsyncItemProcessor<EatableCookingLog, AteCookingLog>,
  ateCookingLogAsyncWriter: AsyncItemWriter<AteCookingLog>,
): Step {
  return StepBuilder(STEP_NAME, jobRepository)
    .chunk<EatableCookingLog, Future<AteCookingLog>>(CHUNK_SIZE)
    .transactionManager(transactionManager)
    .reader(eatableCookLogReader)
    .processor(asyncItemProcessor)
    .writer(ateCookingLogAsyncWriter)
    .build()
}

@Bean
fun eatableCookLogReader(
  jdbcTemplate: JdbcTemplate,
): ItemReader<EatableCookingLog> {
  return NoOffsetPagingItemReader(
    jdbcTemplate = jdbcTemplate,
    chunkSize = CHUNK_SIZE,
  )
}

@Bean
fun asyncItemProcessor(): AsyncItemProcessor<EatableCookingLog, AteCookingLog> {
  val processor = ItemProcessor<EatableCookingLog, AteCookingLog> { it.eat() }
  val asyncItemProcessor = AsyncItemProcessor(processor)
  asyncItemProcessor.setTaskExecutor(cookingLogUpdateExecutor())
  return asyncItemProcessor
}

@Bean
fun ateCookingLogAsyncWriter(
  ateCookingLogWriter: ItemWriter<AteCookingLog>,
): AsyncItemWriter<AteCookingLog> {
  return AsyncItemWriter(ateCookingLogWriter)
}

@Bean
fun cookingLogUpdateExecutor(): TaskExecutor {
  val executor = ThreadPoolTaskExecutor()
  executor.corePoolSize = POOL_SIZE
  executor.maxPoolSize = POOL_SIZE
  executor.setThreadNamePrefix("async-processor-")
  executor.setWaitForTasksToCompleteOnShutdown(true)
  executor.initialize()
  return executor
}
```

> 전체 코드는 [https://github.com/Hyeon9mak/lab/tree/master/spring-batch-async-item-processor](https://github.com/Hyeon9mak/lab/tree/master/spring-batch-async-item-processor) 에서 확인할 수 있습니다.

기본적으로 병렬 처리에 사용되는 thread 의 수는 `SimpleAsyncTaskExecutor` 에 의해 결정됩니다. `**SimpleAsyncTaskExecutor**` **는 가용 가능한 자원만큼 무제한으로 thread 를 생성하기 때문에, 자원 고갈에 따른 OOM 이슈가 발생** 할 수 있습니다. 따라서 대량의 데이터를 운용하는 운영 환경에서는 직접 `TaskExecutor` 를 구현해 적정한 thread 수를 제어하는 것이 필수 입니다.

**순서 보장**
Chunk 내부의 process 에서 병렬 처리가 수행되므로, Chunk 단위에서는 순서를 보장받을 수 있습니다. 때문에 `ItemStreamReader`, `ItemStreamWriter` 를 사용하는 경우에도 순서가 보장됩니다.

**process 만 병렬 처리
**그림을 통해 이해할 수 있듯, `AsyncItemProcessor` 는 process 단계에서만 병렬 처리를 수행합니다. 당연하게도 reader, writer 에서 병목이 발생하는 경우 큰 효과를 기대하기 어렵습니다.

**예외 처리
**앞서 강조했듯, `AsyncItemProcessor` 는 process 단계에서 Feature 를 이용한 비동기 처리를 수행한 후 writer 단계에서 Future 를 정리하고 적재합니다. 따라서 process 단계에서 예외가 발생한 경우 예외가 Feature 로 wrapping 되어있기 때문에, Feature 를 unwrapping 하는 writer 단계에서야 예외가 처리됩니다.

가령 process 단계에서 `BusinessException` 에 대한 skip 설정을 해두었어도, process 단계에서 발생한 `BusinessException` 은 writer 단계에서 `ExecutionException` 으로 wrapping 되어 전파됩니다. `ExecutionException` 에 대한 별도 설정을 하지 않았다면 Batch 가 그대로 중단 되는 것 입니다.**Transaction 관리
**`AsyncItemProcessor` 는 process 단계에서 새로운 thread 를 생성해 비동기적으로 Item 을 처리합니다. 따라서 process 단계에서 생성된 thread 들은 Step 의 Transaction Context 를 공유하지 못합니다. 이는 앞서 언급한 직접 병렬 처리 구현 시 발생하는 문제점과 동일합니다.

## Spring Batch 병렬 처리 전략 — Multi-threaded Step

![](https://miro.medium.com/v2/resize:fit:640/format:webp/0*4xhsKoad_z-bFWyC)

Multi-threaded Step 은 Chunk 단위 동작 전체를 하나의 thread 로 처리합니다. 즉 reader, processor, writer 단계가 모두 하나의 thread 에서 처리됩니다.

```c
@Bean
fun cookingLogUpdateExecutor(): TaskExecutor {
    val executor = ThreadPoolTaskExecutor()
    executor.corePoolSize = POOL_SIZE
    executor.maxPoolSize = POOL_SIZE
    executor.setThreadNamePrefix("multi-threaded-step-")
    executor.setWaitForTasksToCompleteOnShutdown(true)
    executor.initialize()
    return executor
}

@Bean
fun eatStep(
    jobRepository: JobRepository,
    transactionManager: PlatformTransactionManager,
    cookingLogUpdateExecutor: TaskExecutor,
    eatableCookLogReader: ItemReader<EatableCookingLog>,
    eatCookLogProcessor: ItemProcessor<EatableCookingLog, AteCookingLog>,
    ateCookingLogWriter: ItemWriter<AteCookingLog>,
): Step {
    return StepBuilder(STEP_NAME, jobRepository)
    .chunk<EatableCookingLog, AteCookingLog>(CHUNK_SIZE, transactionManager)
    .reader(eatableCookLogReader)
    .processor(eatCookLogProcessor)
    .writer(ateCookingLogWriter)
    .taskExecutor(cookingLogUpdateExecutor)
    .build()
}
```

> 전체 코드는 [https://github.com/Hyeon9mak/lab/tree/master/spring-batch-multi-threaded-step](https://github.com/Hyeon9mak/lab/tree/master/spring-batch-multi-threaded-step) 에서 확인할 수 있습니다.

Spring Batch 6.0 이전 버전에서는 `.chunk<EatableCookingLog, AteCookingLog>(CHUNK_SIZE, transactionManager)` 형태로 내부에서 `ChunkOrientedTasklet` 를 생성하여 각각의 Chunk 단위로 thread 를 할당해서 read-process-write 를 수행할 수 있었습니다.

[**그러나 Spring Batch 6.0 부터는**](https://github.com/spring-projects/spring-batch/wiki/Spring-Batch-6.0-Migration-Guide#new-chunk-oriented-model-implementation) `[**StepBuilder**](https://github.com/spring-projects/spring-batch/wiki/Spring-Batch-6.0-Migration-Guide#new-chunk-oriented-model-implementation)` [**에서 아래와 같은 형태로 호출 방식이 변경되었습니다.**](https://github.com/spring-projects/spring-batch/wiki/Spring-Batch-6.0-Migration-Guide#new-chunk-oriented-model-implementation)

```c
@Bean
fun eatStep(
    jobRepository: JobRepository,
    transactionManager: PlatformTransactionManager,
    cookingLogUpdateExecutor: AsyncTaskExecutor, // AsyncTaskExecutor 로 변경
    eatableCookLogReader: ItemReader<EatableCookingLog>,
    eatCookLogProcessor: ItemProcessor<EatableCookingLog, AteCookingLog>,
    ateCookingLogWriter: ItemWriter<AteCookingLog>,
): Step {
return StepBuilder(STEP_NAME, jobRepository)
    .chunk<EatableCookingLog, AteCookingLog>(CHUNK_SIZE)  // transactionManager 제거 후 별도로 설정
    .transactionManager(transactionManager)
    .reader(eatableCookLogReader)
    .processor(eatCookLogProcessor)
    .writer(ateCookingLogWriter)
    .taskExecutor(cookingLogUpdateExecutor)
    .build()
}
```

기존 `ChunkOrientedTasklet` 를 생성하는 대신 `ChunkOrientedStep` 를 생성하도록 변경되었습니다. `ChunkOrientedStep` 는 read, write 작업은 단일 thread 에서 처리하고 process 작업만 별도의 worker-thread 로 분화하여 처리하는 구조로, 결국 **AsyncItemProcessor 와 유사한 구조** 가 된 것 입니다.

기존 `ChunkOrientedTasklet` 을 이용하여 정통적으로 수행되던 Multi-threaded Step 의 구조를 다시 생각해보면, read-process-write 작업이 모두 하나의 thread 에서 처리되는 특징을 갖고 있습니다. 그러나 저희는 이미 read/write 를 수행하는 I/O bound 작업이 병렬처리 효율성이 그다지 높지 않다는 것을 알고 있습니다. Spring Batch 팀에서도 병렬처리 효율성과 트랜잭션 관리, 재시도 일관성 보장 복잡성 등을 고려하여 `ChunkOrientedStep` 구조로 변경한 것으로 추측할 수 있습니다.

**Spring Batch 7.0 이후 버전부터는** `**ChunkOrientedTasklet**` **가 제거될 예정이므로, Multi-threaded Step 은 사실상 앞으로 큰 의미가 없는 전략입니다.**

## Spring Batch 병렬 처리 전략 — Pagination

![](https://miro.medium.com/v2/resize:fit:640/format:webp/0*xnHEASox18u-uZuO)

Partitioning 은 Step 자체를 여러 개로 나누어 병렬로 처리하는 전략입니다. 각각의 Step 들이 Context(`StepExecution`, `StepExecutionContext`) 를 독립적으로 갖기 때문에, Step 별로 개별적인 상태 관리가 가능하다는 특징이 있습니다.

```c
@Configuration
class CookingLogUpdateJob {

  @Bean(JOB_NAME)
  fun job(
    jobRepository: JobRepository,
    eatStepManager: Step,
  ): Job {
    return JobBuilder(JOB_NAME, jobRepository)
      .start(eatStepManager)
      .preventRestart()
      .build()
  }

  @Bean
  fun cookingLogUpdateExecutor(): TaskExecutor {
    val executor = ThreadPoolTaskExecutor()
    executor.corePoolSize = POOL_SIZE
    executor.maxPoolSize = POOL_SIZE
    executor.setThreadNamePrefix("partition-thread")
    executor.setWaitForTasksToCompleteOnShutdown(true)
    executor.initialize()
    return executor
  }

  @Bean
  fun eatStepPartitionHandler(
    eatStep: Step,
    cookingLogUpdateExecutor: TaskExecutor,
  ): TaskExecutorPartitionHandler {
    val partitionHandler = TaskExecutorPartitionHandler()
    partitionHandler.step = eatStep
    partitionHandler.setTaskExecutor(cookingLogUpdateExecutor)
    partitionHandler.gridSize = POOL_SIZE
    return partitionHandler
  }

  @StepScope
  @Bean
  fun eatStepPartitioner(
    @Value("#{jobParameters['startDate']}") startDate: String?,
    @Value("#{jobParameters['endDate']}") endDate: String?,
    jdbcTemplate: JdbcTemplate,
  ): CookingLogIdRangePartitioner {
    requireNotNull(startDate) { "startDate job parameter is required" }
    requireNotNull(endDate) { "endDate job parameter is required" }

    val startDateInstant = LocalDate.parse(startDate, DateTimeFormatter.ISO_LOCAL_DATE)
      .atStartOfDay(KST_ZONE_ID)
      .toInstant()
    val endDateInstant = LocalDate.parse(endDate, DateTimeFormatter.ISO_LOCAL_DATE)
      .atStartOfDay(KST_ZONE_ID)
      .toInstant()
    return CookingLogIdRangePartitioner(
      jdbcTemplate = jdbcTemplate,
      startDate = startDateInstant,
      endDate = endDateInstant,
      dataCountPerPartition = CHUNK_SIZE,
    )
  }

  @Bean
  fun eatStepManager(
    jobRepository: JobRepository,
    eatStepPartitioner: CookingLogIdRangePartitioner,
    partitionHandler: TaskExecutorPartitionHandler,
  ): Step {
    return StepBuilder("eat-step-manager", jobRepository)
      .partitioner(STEP_NAME, eatStepPartitioner)
      .partitionHandler(partitionHandler)
      .build()
  }

  @Bean
  fun eatStep(
    jobRepository: JobRepository,
    transactionManager: PlatformTransactionManager,
    eatableCookLogReader: ItemReader<EatableCookingLog>,
    ateCookingLogWriter: ItemWriter<AteCookingLog>,
  ): Step {
    return StepBuilder(STEP_NAME, jobRepository)
      .chunk<EatableCookingLog, AteCookingLog>(CHUNK_SIZE)
      .transactionManager(transactionManager)
      .reader(eatableCookLogReader)
      .processor(processor())
      .writer(ateCookingLogWriter)
      .build()
  }
}
```

> 전체 코드는 [https://github.com/Hyeon9mak/lab/tree/master/spring-batch-partitioning](https://github.com/Hyeon9mak/lab/tree/master/spring-batch-partitioning) 에서 확인할 수 있습니다.

Partitioning 에는 기본적인 Job 과 달리 크게 2가지 개념의 신규 Component 가 추가됩니다.

- Partitioner: 조건에 따라 Partition(Step) 을 나누는 역할.
	각 Step 들이 처리할 Chunk 범위 결정.
- StepManager: Partitioner 와 나눠진 Partition(Step) 관리.

구현이 복잡하다고 느낄 수 있지만, 개념을 이해하고 코드를 따라간다면 크게 어렵지 않습니다.

Partitioning 은 별도 설정이 없다면 병렬 처리에 사용되는 thread 의 수가 `SimpleAsyncTaskExecutor` 에 의해 결정됩니다. `**SimpleAsyncTaskExecutor**` **는 가용 가능한 자원만큼 무제한으로 thread 를 생성하기 때문에, 자원 고갈에 따른 OOM 이슈가 발생** 할 수 있습니다. 때문에 대량의 데이터가 운용되는 환경에서는 직접 TaskExecutor 를 구현하여 적정한 thread 수를 미리 제한해두어야합니다.

**Transaction 관리
**Partitioning 은 Step 자체를 여러 개로 나누어 병렬로 처리하는 전략입니다. Chunk 내부 동작은 모두 단일 Thread 에서 처리되기 때문에, Transaction 관리가 아주 쉽다는 장점이 있습니다.

**순서 보장
**Partitioning 은 Step 내부 read — process — write 가 하나의 thread 에서 처리되기 때문에, 각 partition 간 순서를 보장할 수 없습니다. 다만 Step 내부 에서는 단일 Thread 로, 하나의 `StepExecution` 과 `StepExecutionContext` 를 공유하기 때문에 Chunk 단위에서는 순서를 보장 할 수 있습니다. 이 덕분에 `ItemStreamReader`, `ItemStreamWriter` 를 사용하는 경우에도 순서가 보장됩니다.

**Step 간 실패로부터 격리
**각 Partition(Step) 들이 독립적인 Context 를 갖기 때문에, 서로 다른 Step 들 간의 실패로부터 격리됩니다. 가령 Partition(Step) A 가 실패하더라도 Partition(Step) B 는 영향을 받지 않고 정상적으로 완료됩니다. 이 모든 결과는 StepManager 가 집계하여 최종 Job 결과로 반영한다.

```c
Partition(Step) A: FAILED
Partition(Step) B: COMPLETED
Partition(Step) C: COMPLETED
------------------
Job: FAILED
```

이 경우 Batch 를 재시작하여 실패한 Partition(Step) A 만 동작하도록 할 수 있습니다. Partitioning 이 실패를 다루기에 가장 좋은 전략인 이유이기도 합니다.

주의할 점은, 위와 같은 특성으로 인해 Step 내부에서 Skip 을 잘못 사용할 경우 실패지점을 찾아 재실행 하기 어려워집니다.

```c
Partition(Step) A: COMPLETED (1,000 건 중 1건 Skip)
Partition(Step) B: COMPLETED
Partition(Step) C: COMPLETED
------------------
Job: COMPLETED
```

Partitioning 과 같은 병렬 처리를 고민하는 시점이라면 이미 대량의 데이터를 다루고 있을 가능성이 높습니다. 때문에 전체 데이터를 다시 처리하는 비효율을 피하기 위해 성공/실패 시나리오를 명확히 구분하고, 설계를 진행하는 것이 중요합니다.

## 시나리오별 권장 전략

당연하게도, Multi-threaded Step 은 모든 시나리에서 배제됩니다.

**외부 API 호출이 병목 지점인 경우**

- AsyncItemProcessor 권장
- read/write 단계에서 DB I/O bound 가 적지만
	process 단계에서 API I/O bound 가 큰 경우 유리
- Partitioning 은 구현 복잡도 + Chunk 처리 순서 보장이 어려움

**CPU 연산이 병목 지점인 경우**

- AsyncItemProcessor 권장
- read/write 단계에서 DB I/O bound 가 적은 대신
	process 단계에서 CPU bound 가 큰 경우 유리
- Partitioning 은 구현 복잡도 + Chunk 처리 순서 보장이 어려움

**대량 데이터 통계 집계**

- Partitioning 권장
- read/write 단계에서 DB I/O bound 가 큰 경우 유리
- ID, 날짜 등으로 범위를 나눠서 Partition 을 나누어 독립 수행 시키기 좋음
- 실패시 재실행 지점이 명확

**실패 격리가 필요한 경우**

- Partitioning 권장
- Partition(Step) 간 실패 격리가 필요한 경우 유리
- 실패한 Partition(Step) 만 재실행 시키기 좋음

두 전략 모두 병렬 처리를 이용한 성능 향상을 목적으로 하기 때문에, 병렬로 쏟아지는 요청을 받아낼 데이터베이스의 성능도 필수로 고려해야 합니다. 데이터베이스가 감당할 수 있는 Connection Pool 크기를 고려하는 등 애플리케이션 레벨을 넘어 인프라 레벨까지 고민하는 디테일이 필요합니다.

## 마치며

약간의 **구현 복잡도만 감수한다면 Partitioning 이 가장 직관적이고, 부분적인 실패를 다루기도 용이하기 때문** 에 대부분의 경우 권장할만한 병렬 처리 전략입니다. 이 때문에 저는 **Partitioning 을 이용한 병렬 처리 전략을 채택** 했습니다.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*UFZ_3IwRUgrSTjeIVLPMYw.png)

앞으로 현재 데이터 구조를 파악하여 Partitioning 이 용이하도록 데이터 조회 방법을 고도화하고, Object Storage 에 효율적으로 변환하여 적재하는 스탭이 남았습니다.

다음 글에서는 Partitioning 을 이용한 병렬 처리 전략을 도입함과 동시에, 대량의 데이터를 조회할 때 필수적인 Pagination 에 대해서 고민해 볼 예정입니다. 특히 순서(Order)를 규정짓기 어려운 UUIDv4 PK 환경에서 조금이라도 더 나은 조회 성능 향상을 위해 No-offset 기반 Pagination 을 도입하는 방안에 대해 이야기 해보겠습니다.

## References

- [https://hyeon9mak.github.io/spring-batch-parallel-processing-strategies/](https://hyeon9mak.github.io/spring-batch-parallel-processing-strategies/)
- [https://github.com/Hyeon9mak/lab/tree/master/spring-batch-async-item-processor](https://github.com/Hyeon9mak/lab/tree/master/spring-batch-async-item-processor)
- [https://github.com/Hyeon9mak/lab/tree/master/spring-batch-multi-threaded-step](https://github.com/Hyeon9mak/lab/tree/master/spring-batch-multi-threaded-step)
- [https://github.com/Hyeon9mak/lab/tree/master/spring-batch-partitioning](https://github.com/Hyeon9mak/lab/tree/master/spring-batch-partitioning)
- [https://github.com/spring-projects/spring-batch/wiki/Spring-Batch-6.0-Migration-Guide#new-chunk-oriented-model-implementation](https://github.com/spring-projects/spring-batch/wiki/Spring-Batch-6.0-Migration-Guide#new-chunk-oriented-model-implementation)
- [https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing.html](https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing.html)

## More from Hyeon9mak

## Recommended from Medium

[

See more recommendations

](https://medium.com/?source=post_page---read_next_recirc--fea8cbc019db---------------------------------------)
