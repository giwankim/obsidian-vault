---
title: "JPA Transactional 잘 알고 쓰고 계신가요? | 카카오페이 기술 블로그"
source: "https://tech.kakaopay.com/post/jpa-transactional-bri/#set_option%EC%9D%80-%EB%AC%B4%EC%97%87%EC%9D%B8%EA%B0%80"
author:
published: 2025-01-23
created: 2026-09-30
description: "JPA Transactional과 그에 따른 DB 쿼리 성능과의 관계에 대해서 설명합니다."
tags:
  - "clippings"
---

> [!summary]
> 카카오페이 온라인결제 DB에서 set_option 쿼리가 약 14K QPS까지 치솟은 원인을 추적해 보니, `@Transactional(readOnly=true)`가 select 한 번에 autocommit 설정·set session transaction·commit 등 부가 쿼리를 최대 6개까지 붙이고 있었다. 트랜잭션을 뺀 조회에서 select 처리량이 2~3배 늘어난 것을 확인한 뒤, 단건 수정은 트랜잭션 없이 처리하고 readOnly에는 `propagation = SUPPORTS`를 묶은 `@ReadOnlyTransactional`을 쓰며, 조회가 많은 엔티티는 `findById`를 override하고 클래스 레벨 `@Transactional`은 쓰지 않는 컨벤션을 정했다. 조회·단일 row 수정·동시성 제어에는 트랜잭션이 필요 없다는 근거와 `SimpleJpaRepository`에 기본으로 붙은 트랜잭션의 함정도 함께 설명한다.

> 요약: 이 글은 JPA의 @Transactional 사용과 데이터베이스 쿼리 성능 간의 관계를 다루며, 기본 설정의 문제점과 개선 가능성을 탐구합니다. JPA의 편리함이 성능에 영향을 미칠 수 있음을 지적하며, 기본 설정을 되돌아보고 성능 이슈 발생 전에 최적화 방안을 모색할 필요가 있음을 강조합니다. 특히, 구조 변경 없이 성능을 개선할 방법을 제시하려는 점에서 유용한 통찰을 제공합니다.

💡 **리뷰어 한줄평**

**dory.m** 애플리케이션은 최근에 들어선 쉽게 스케일 아웃 할 수 있는 여러 방법들이 있지만, 아직도 데이터베이스는 그렇지 않습니다. 귀중한 데이터베이스 리소스를 효율적으로 활용하고 있는지 다시금 생각하게 해주는 글입니다.

**wade.hong** JPA를 다루는 개발자라면 구동되는 원리를 정확하게 알아야 한다고 생각합니다. 그런 점에서 이 내용은 필수적으로 봐야 하는 내용입니다. 한 번 더 JPA Transactional를 점검할 기회인 거 같습니다.

**wonny.p** 당연하게 사용하던 Transactional에 대해서 고찰할 수 있는 시간을 갖게 해주는 좋은 글이라 생각합니다.👍🏻 실제 개선했던 내용들이 들어 있어서 더욱 읽기 좋았습니다.

## 시작하며

안녕하세요 카카오페이에서 온라인결제 서비스 백엔드 개발을 맡고 있는 bri.ghten입니다.

본 포스팅에서는 JPA Transactional과 그에 따른 DB 쿼리 성능과의 관계에 대해서 설명합니다.
따라서 DB Transaction과 Spring Transactional, JPA, Spring data source에 대한 기본적인 이해가 필요합니다.

DataSource로는 Mysql을 기준으로 설명하며 쿼리 튜닝 및 인덱스 튜닝으로 인한 성능 개선에 대해서는 설명하지 않습니다.

## 어느 날 DBA 에게서 위험 알림이 왔다.

어느 날, DBA가 서비스 위험을 감지하고 알림을 보냈습니다.

![dba-alert](https://tech.kakaopay.com/_astro/db-cpu-alert.BlH8J7Nf_1owkzm.webp)

dba-alert

당시 지표를 정리하면 다음과 같습니다.

- peak total qps: 24K
- select, commit 쿼리: 약 5K
- update, insert 쿼리: 약 3K 미만
- set\_option 쿼리: 약 14K

peak total qps는 24K 정도로 잡혀있었지만 select와 commit 쿼리는 약 5K, update와 insert 쿼리는 3K 미만으로 식별이 힘들었고, set\_option 쿼리가 약 14K 정도로 높다는 점이 수상했습니다. set\_option 쿼리를 살펴볼 필요가 있었습니다.

### set\_option은 무엇인가?

Mysql에서의 set\_option은 말 그대로 option setting 하는 모든 쿼리입니다.
카카오페이 온라인결제 서비스의 개발환경에서 DB 로그를 약 4일간 켜두고 어떤 쿼리들이 가장 많이 호출되는지 10위까지의 순위를 찾아봤습니다.

![general-log-query-ranking](https://tech.kakaopay.com/_astro/query-ranking.B1lZ0uij_ZJlsMm.webp)

general-log-query-ranking

이 중 set\_option과 연관된 쿼리들을 보니 `autocommit`, `transaction`, `sql_mode`, `character_set_results` 등이 있는 걸 확인할 수 있습니다.
저희는 여기서 autocommit과 transaction 관련 쿼리를 눈여겨보았습니다.

카카오페이 온라인결제 서비스 백엔드에서는 JPA를 통한 DB Access 처리를 하고 있는데요. 여기서 JPA Transactional이 DB 리소스 사용, 즉 DB 조회 성능에 알게 모르게 영향을 끼치고 있음을 알게 되었습니다.

### 실제로 set\_option과 commit이 성능에 영향을 미칠까?

autocommit과 transaction 관련 쿼리가 조회 쿼리도 아니고 DB cpu나 메모리를 잡아먹는 큰 허들이 될까 싶었지만 직접 테스트를 진행해 확인해 보기로 했습니다. 테스트는 운영 중인 서비스에서 실제 최다 조회되는 테이블을 기준으로 진행했습니다.

아래 예제 코드는 테스트한 실제 예제코드와 최대한 비슷하게 작성한 코드입니다.

```kotlin
// 서비스에서 가장 많이 사용 되는 Order entity
@Entity
@DynamicUpdate
class Order constructor(
    @Id
    @Column(nullable = false)
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long = 0,
    @Column(nullable = false)
    val transactionId: String,

    //... 추가 컬럼 생략
)
```
```kotlin
// 성능 테스트용 컨트롤러
@RestController
@RequestMapping("/test/read")
class TestController(
    private val orderRepository: OrderRepository,
) {
    @PostMapping("/transaction/{transactionId}")
    @Transactional(readOnly=true)
    fun transactionTest(
        @PathVariable transactionId: String,
    ) : String {
        return orderRepository.findByTransactionId(transactionId)?.id?.toString() ?: "nohit"
    }

    @PostMapping("/{transactionId}")
    fun transactionTest(
        @PathVariable transactionId: String,
    ) : String {
        return orderRepository.findByTransactionId(transactionId)?.id?.toString() ?: "nohit"
    }
}
```

해당 코드로 성능 테스트를 진행하였고 외부 요인을 제거하기 위해 osiv=false로 두고 조회는 db id가 아닌 내부 uniqueId로 진행했습니다.

아래 테스트는 K6로 테스트를 진행한 것인데요. 카카오페이 사내에서는 개발자를 위한 편리한 성능테스트 도구가 있어서 해당 시스템을 사용하였습니다.

> 해당 시스템이 궁금하신 분은 [카카오페이 성테존 소개](https://tech.kakaopay.com/post/perftest_zone/) 콘텐츠를 참고해 주세요 ^^.

![transactional db 성테_트랜잭션](https://tech.kakaopay.com/_astro/perf-test-db-transaction.CrgpD_gn_Z2fC7bT.webp)

transactional db 성테\_트랜잭션

![transactional_db_성테_단일쿼리](https://tech.kakaopay.com/_astro/perf-test-db-none.BaVOxR19_ZNVKUo.webp)

transactional\_db\_성테\_단일쿼리

결과를 간단하게 요약하자면 트랜잭션이 없는 경우, select 쿼리가 약 2~3배 정도 증가해 DB 사용 성능이 향상된 것을 알 수 있었습니다. 별도로 첨부하진 않았지만 api 테스트 결과 역시 마찬가지로 약 2배가량 좋아진 것을 확인했습니다.

이를 통해 set\_option, commit 쿼리가 적어도 DB 조회 성능에 유의미 한 영향은 미칠 수 있다는 것을 한번 더 확인할 수 있었습니다.

---

## 카카오페이 온라인 결제에서 결정한 Transactional 사용 방식

위와 같은 이유로 서비스 코드 persistence layer에서의 `@Transactional` 사용에 관한 컨벤션을 다시 잡기로 하였고 그에 맞춰 코드들을 수정하기로 했습니다.

큰 방향성은 아래와 같습니다.

- transactional이 필요 없는 구간은 최대한 사용하지 않는다.
- transactional 사용 구간 안에 3rd party api가 끼지 않도록 persistence layer 바깥에서는 transactional을 사용하지 않는다.
- 의도치 않은 transaction 설정을 피하기 위해 class level에서의 transactional 설정은 하지 않는다.

다음은 위 내용들을 적용하기 위해 진행했던 방법입니다.

### 1\. 단건 요청에 대해서는 Transaction 제거하기

단순 조회만 수행하는 쿼리들이 아닌 update나 insert 요청 메서드에 대해서도 해당 메서드가 단건이라면 Transactional을 제거하도록 했습니다. 이렇게 정한 이유는 이후 [JPA Transactional에 대하여](#jpa-transactional%EC%97%90-%EB%8C%80%ED%95%98%EC%97%AC) 목차에 설명해 두었습니다.

### 2\. @Transactional(readOnly=true)에 propagation 넣기

저희는 CQRS 패턴을 사용하고 있기 때문에 readOnly DB를 접근하면서 transactional이 DB에 전파되지 않을 방법을 찾아야 했습니다.

> 여기서 CQRS 패턴이란?
> 조회 dataSource와 수정용 dataSource를 분리하는 패턴입니다. 보통 `@Transactional(readOnly=true)` 를 설정하면 조회용 dataSource를 접근하도록 설정을 하는데요. 해당 방법에 대한 내용은 설명하지 않겠습니다. 다만 특이한 점은 온라인 결제 서비스는 실시간성 보장을 위해 조회용 dataSource 또한 master DB를 사용하고 있습니다.

다행히 `@Transactional(readOnly=true)` 와 함께 `propagation` 설정을 잘 활용하면 readOnly DataSource는 보지만 transaction은 수행되지 않아 트랜잭션 없는 readOnly DB 접근이 가능해졌습니다.

따라서 readOnly를 사용할 때에는 `propagation` 을 활용하기로 하였습니다.

#### readOnly 용 Propagation 종류와 사용 방안

저희 서비스 내에서는 성능이 중요하기 때문에 다음과 같은 제약사항이 존재했습니다.

1. 하나의 스레드 내에 DB connection pool 연결은 1개가 좋다.
2. DB connection이 하나라면 transaction도 스레드당 1개여야 한다.
3. readOnly 단독 사용의 경우 transaction은 없어야 한다.

우선 transactional이 발생하지 않는 propagation의 종류는 다음과 같습니다.

- SUPPORTS
- NEVER
- NOT\_SUPPORTED

이 중 두 가지의 경우 다음과 같은 문제가 있을 수 있습니다.

- NEVER: 의도치 않은 exception이 발생할 수 있습니다.
- NOT\_SUPPORTED: 상위 트랜잭션이 있는 경우 일시정지 후 추가 커넥션이 발생할 여지가 있습니다.

따라서 `SUPPORTS` 를 사용하기로 했습니다.
`SUPPORTS` 는 default Propagation인 `REQUIRED` 와 비슷한 동작을 취하고 있어 메서드 단독 수행 시에는 트랜잭션이 동작하지 않지만 상위에 트랜잭션이 있는 경우 상위트랜잭션에 포함되어 수행되는 전파방식입니다.

#### 컨벤션 강제화를 위한 Custom Annotation

위와 같은 이유로 propagation 컨벤션을 정하고 서비스 내에서는 예외상황 없이 전부 해당 Propagation을 사용하기로 했습니다.

- Transactional의 경우 default `REQUIRED`
- Transactional readOnly의 경우 `SUPPORTS`

따라서 헷갈리지 않기 위해 공통 annotation 또는 확장 함수로 제공하여 비즈니스 로직에서는 직접적으로 `@Transactional(readOnly=true)` 을 사용하지 않도록 PR 및 코드 컨벤션을 정했습니다.

**\[Custom Annotation 버전\]**

```kotlin
@Transactional(readOnly = true, propagation = Propagation.SUPPORTS)
annotation class ReadOnlyTransactional
```

**\[확장 함수형 버전\]**

```kotlin
object Tx {
    @Suppress("ktlint:standard:backing-property-naming")
    private lateinit var _txRunner: TxRunner

    fun initialize(txRunner: TxRunner) {
        _txRunner = txRunner
    }

    fun <T> masterTx(function: () -> T): T = _txRunner.runTx(function)

    fun <T> readOnlyTx(function: () -> T): T = _txRunner.runReadOnly(function)
}

@Configuration
class TxConfig {
    @Bean("txInitBean")
    fun txInitialize(txRunner: TxRunner): InitializingBean =
        InitializingBean { Tx.initialize(txRunner) }
}

@Component
class TxRunner {
    @Transactional
    fun <T> runTx(block: () -> T): T = block()

    @ReadOnlyTransactional
    fun <T> runReadOnly(block: () -> T): T = block()
}
```

### 3\. 조회가 빈번한 엔티티는 findById override 하기

[JPA Transactional의 함정](#%EC%9D%98%EB%8F%84%ED%95%98%EC%A7%80-%EC%95%8A%EC%9D%80-transactional-%EB%8F%99%EC%9E%91) 에 후술 할 내용으로 findById를 그냥 쓰면 내부 `SimpleJpaRepository` 가 `@Transactional(readOnly=true)` 를 붙여버립니다.

이를 우회하기 위해 가장 조회가 많이 수행되는 테이블 기준으로 2개 정도의 테이블만 `findById` 를 override 하였습니다.

```kotlin
@Repository
interface InhouseTestRepository :
    JPARepository<TestEntity, Long>,
    InhouseTestCustomRepository

interface InhouseTestCustomRepository {
    fun findById(id: Long): Optional<TestEntity>
}

class InhouseTestCustomRepositoryImpl :
    QuerydslRepositorySupport<TestEntity>(),
    InhouseTestCustomRepository {

    @Transactional(readOnly = true, propagation = SUPPORTS)
    override fun findById(id: Long): Optional<TestEntity> {
        val qTestEntity = QTestEntity.testEntity
        return Optional.ofNullable(
            this.queryFactory.select(qTestEntity)
                .from(qTestEntity)
                .where(
                    qTestEntity.id.eq(id),
                ).fetchOne()
        )
    }
}
```

### 4\. class definition은 쓰지 말기

마지막으로 의도치 않게 transactional이 동작하는 걸 방지하기 위해 class level에서 Transactional이 붙어 있던 부분을 전부 메서드 level로 내렸습니다.

```kotlin
// 수정 전
@Transactional(readOnly=true)
class TestService(
    val testRepository: InhouseTestRepository,
) {

    fun getTransactionId(
        id: Long,
    ): String = testRepository.findByIdOrNull(id)?.transactionId ?: "nohit"

    @Transactional
    fun updateTransactionId(
        id: Long,
        tid: String,
    ) = testRepository.findByIdOrNull(id)?.let { it.transactionId=tid }
}
```
```kotlin
// 수정 후
class TestService(
    val testRepository: InhouseTestRepository,
) {

    fun getTransactionId(
        id: Long,
    ): String = readOnlyTx { // 또는 fun 위에 @ReadOnlyTransactional 설정.
        testRepository.findByIdOrNull(id)?.transactionId ?: "nohit"
    }

    fun updateTransactionId(
        id: Long,
        tid: String,
    ) = masterTx {
        testRepository.findByIdOrNull(id)?.let { it.transactionId=tid }
    }
}
```

### 컨벤션 정리

다시 한번 컨벤션에 대해 정리하자면 다음과 같습니다.

1. 단건 수정 요청에서 Transactional 미사용
2. `@Transactional(readOnly=true)` 대신 `@ReadOnlyTransactional` (커스텀 어노테이션) 사용
3. 조회가 많이 되는 엔티티의 경우 findById override 고려
4. class 레벨에서의 `@Transactional` 미사용

## JPA Transactional에 대하여

위 컨벤션 정리한 부분들을 보시고 대체 왜 이렇게 컨벤션 규칙을 정하고 정리하게 되었는지 궁금하신 분들이 있으실 텐데요.
바쁘신 분들은 그냥 그렇구나 하고 지금 넘어가셔도 좋습니다만 그렇게 되면 왜 이런 결론에 도달하게 되었는지 알 수 없기 때문에 읽어보시길 추천드립니다. ^^.

먼저 Spring Transactional에 대해 다시 생각해 보았습니다.

### @Transactional이란?

Spring Transactional annotation, 이하 `@Transactional` 은 spring에서 메서드의 원자성을 보장하기 위해 정의된 annotation interface입니다. Spring으로 원자성을 보장하기 위해서는 persistence layer를 구성하여 수행하는데요, 이는 보통 DB 연결로 수행 하기 때문에 구현체로 DB 관련 TransactionManager를 많이 사용하게 됩니다.

그렇다면 우리는 `@Transactional` 을 꼭 써야 할까요?

여기서 제가 내린 결론은 **쓰지 말자**, 입니다.

너무 도발적이군요, 순화해서 다시 쓰자면 `@Transactional` 을 **쓸 상황을 최대한 줄이자**, 가 되겠습니다.

#### @Transactional 기능의 역할과 책임의 제한

위에서 말했듯이 `@Transactional` 스펙은 DB 한정이 아닌 기능 동작에 관한 원자성을 보장하는 interface입니다. 하지만 Spring이 데이터 저장소는 아니기 때문에 DB 등 다른 솔루션 없이 원자성을 보장하는 것에 한계가 있습니다. 그러다 보니 자연스럽게 DB 조회 및 업데이트 관련 원자성 보장에 많이 활용하는 편입니다.

카카오페이 온라인 결제 역시 서비스 전체적인 Transaction 처리는 Saga Pattern을 활용하고 있기 때문에, 각 서비스 내부에서의 `@Transactional` 사용은 DB 접근의 원자성 보장 한정으로 사용하고 있습니다.
특히나 DB 접근을 위해 JPA를 활용하고 있기 때문에 구현체 또한 JPA Transactional을 적극 활용하고 있습니다.

#### 데이터 접근에 대한 원자성 보장을 위한 JPA Transaction 역할

그렇다면 언제 이 원자성이 보장되어야 할까요?

바로 여러 데이터에 대한 update가 필요할 때입니다.
이 외의 경우에는 필요가 없는데요 다음 3가지가 필요 없는 경우에 해당됩니다.

1. 조회만 필요한 경우, Transactional이 필요하지 않습니다.
	- 이미 영구적인 데이터를 조회만 하고 있기 때문에, Transaction이 보장해 주는 ACID의 기능 중 Durability, 영구 적용성이 필요가 없습니다.
		- DB에서 제공해 주는 일관된 읽기를 위한다면 application 입장에서의 단일 스레드 안에서 같은 data 요청을 여러 번 하는 것이 유지보수성이 높아지는지, 성능적 이점이 있는지 고민해 볼 필요가 있습니다.
2. 하나의 row만 update 할 경우, Transactional이 필요하지 않습니다.
	- 이미 하나의 데이터에 관한 update는 DB에서 원자성을 보장해주기 때문에 Transactional이 필요하지 않습니다.
3. 동시성 제어만 필요한 경우, 다른 방법을 고려할 수 있습니다.
	- 단일 select update와 같은 경우에 동시성 제어가 필요한 경우에는 Transactional 만으로는 완벽한 제어가 불가능한 경우가 있습니다. (mysql의 경우 [phantom read](https://dev.mysql.com/doc/refman/8.4/en/innodb-next-key-locking.html))
		- Transactional isolation을 serializable 모드로 강하게 한다던지 (이 경우 성능 영향)
				- optimistic lock을 따로 적용을 한다던지 추가적인 작업이 필요합니다.
				- 그렇게 까지 진행할 작업이 아니라면 비즈니스-도메인 구조에 대해서 다시 생각해 볼 수 있습니다.
			- 단일 key에 대한 update가 동시적으로 들어올 수 있는 비즈니스 구조 자체가 문제가 있는 건 아닌지 생각해 볼 수 있습니다.
		- redis 등을 활용한 서비스 api 요청 단위에서의 중복 요청 제어 등을 고려해 볼 수 있습니다.

위 3가지 경우를 제외하고 나면 JPA 입장에서 여러 데이터를 save 하게 되는 경우로 귀결됩니다.

### JPA Transactional 함정

#### 의도하지 않은 Transactional 동작

위와 같이 Transactional 사용을 최대한 절제하고 쓰지 않는다고 해도 JPA 사용 시 기본적인 메서드 사용 시에는 내부 코드에서 Transactional이 사용됩니다.

가장 대표적인 게 findById, save, delete 등을 구현하고 있는 SimpleJPARepository 메서드들입니다.

해당 클래스는 클래스 레벨에서 이미 `@Transactional(readOnly=true)` 가 선언되어 있으며 save, delete 등의 update 메서드에는 `@Transactional` 이 붙어 있습니다. JPA는 어떤 datasource든 동일한 접근 방식을 제공하려는 프레임워크이고 기본적으로 commit을 통한 최종 데이터 update를 수행하기 위해서는 `@Transactional` 을 활용하게 되어 있기 때문입니다.

다만 Querydsl이나 jpql 사용 등의 custom 쿼리 동작 시에는 당연하게도 simpleJPARepository 메서드 구현체가 동작하지 않기 때문에 default Transactional에서 자유로워지게 됩니다.

#### @Transactional(readOnly=true) 동작에서 DB로의 쿼리 전파

`@Transactional(readOnly=true)` 사용 시 spring 진영에서는 애플리케이션 입장에서 dirtyChecking을 진행하지 않기 때문에 성능 개선의 측면이 있다고 이야기합니다. 또한 몇몇 개발자들의 입장에서는 명시적인 효과도 있다고 이야기하고 있습니다.

다만 여기서 의도치 않은 동작이 추가로 진행되는데요.

아래와 같이 `@Transactional(readOnly=true)` 를 사용하는 메서드가 있다고 가정해 봅시다.

```kotlin
@Transactional(readOnly = true)
fun getDetail(
    @PathVariable id: Long,
): String = testRepository.findByIdOrNull(id)?.transactionId ?: "nohit"
```

실제 위 메서드를 수행한 뒤 Mysql general log를 살펴보면 다음과 같습니다.

![read-only 시 쿼리](https://tech.kakaopay.com/_astro/read-only-query-general-log.TIYZMAKb_2hl4Sm.webp)

read-only 시 쿼리

우리가 실제 필요한 쿼리는 5번 row의 `select ~....`인데요. `@Transaction(readOnly = true)` 사용 시 실제 DB 트랜잭션 모드를 readOnly로 설정해 DB 트랜잭션을 사용하게끔 동작합니다. 이를 위해 autoCommit setting, commit 요청, set session transaction 세팅 등으로 6개의 쿼리가 더 날아가고 있네요.

사실 위와 같은 상황이 생기는 게 맞는 것이 `@Transactional(readOnly=true)` 경우에는 propagation이 설정되어 있지 않습니다. default propagation setting은 `REQUIRED` 로써 상위 메서드의 transaction이 없을 시에는 만들고, 있을 시에는 참여하여 DB로 실제 Transaction 사용을 요청하는 동작을 수행합니다.

##### @Transactional(readOnly=true), 성능에 좋은 영향을 미치나?

spring 진영에서는 `@Transactional(readOnly=true)` 가 dirtyChecking 모드를 Manual모드로 바꿔 줄 수 있기 때문에 application 성능 개선에 도움이 될 수 있다고 설명합니다.

다만 대부분의 DB 입장에서는 read-only 세팅으로 트랜잭션을 열게 되면 성능적 이점이 아주 약간 있거나 없을 것이라 설명하고 있습니다.

이 기능의 주요 목적은 ACID 중 읽기 작업만 수행했을 때의 Isolation 제공을 위한 일관된 읽기 수행 제공에 있기 때문입니다.

단순히 이를 위해 `@Transactional(readOnly=true)` 를 사용하는 것은 지불해야 할 비용이 너무 큽니다. DB 입장 에서의 Transaction read-only 세팅 비용이 크지 않다 하더라도, 이 단순한 추가 쿼리로 인해 DB까지의 네트워크 요청 건수 또한 최대 6배까지 늘어나게 됩니다.

실제로 이러한 의문을 가지고 위의 [실제로 set\_option과 commit이 성능에 영향을 미칠까?](#%EC%8B%A4%EC%A0%9C%EB%A1%9C-set_option%EA%B3%BC-commit%EC%9D%B4-%EC%84%B1%EB%8A%A5%EC%97%90-%EC%98%81%ED%96%A5%EC%9D%84-%EB%AF%B8%EC%B9%A0%EA%B9%8C)에서 성능 테스트를 수행한 건데요. 위에 설명은 안 했지만 코드를 잘 보시면 `@Transactioanl(readOnly=true)` 유무로 성능 비교를 진행했습니다. 그리고 아시다시피 결과는 없는 게 낫다는 결론으로 나왔습니다.

거기에 대부분의 성능 허들은 application이 아닌 DB에 있습니다. scale-out이 쉽지 않기 때문이죠.

이를 위해 보통의 경우 `@Transactional(readOnly=true)` 를 활용한 CQRS 패턴 까지도 적용하여 성능의 이점을 꾀하게 됩니다.

다만 저희 서비스의 경우 DB 복제 지연의 영향 또한 막기 위해 실시간 서비스에 한해서 slave DataSource 또한 master DB를 보게 해 DB connection pool만 분리해 둔 상황입니다.

#### set\_option 및 auto commit 옵션

추가로 transactional 사용 중 최초 db config 옵션에 auto commit을 빼면 최소한 트랜잭션 수행 시 set autoCommit=1,0에 대한 요청은 줄일 수 있습니다. 다만 이렇게 사용할 경우 [위](#1-%EB%8B%A8%EA%B1%B4-%EC%9A%94%EC%B2%AD%EC%97%90-%EB%8C%80%ED%95%B4%EC%84%9C%EB%8A%94-transaction-%EC%A0%9C%EA%B1%B0%ED%95%98%EA%B8%B0) 경우에도 무조건 트랜잭션을 붙여줘야 하기에 해당 방법은 빼기로 했습니다.

게다가 `@Transcational(readOnly=true)` 를 사용하게 될 경우 auto commit을 0으로 둔다 하더라도 무조건 commit 쿼리가 따라서 요청되고 set session 변환에 관한 쿼리는 없어지지 않습니다. 따라서 해당 옵션 변경에 관한 노력보다는 Transactional 자체를 줄이는데 집중하기로 했습니다.

## 마치며

알람이 뜨고 컨벤션을 정하면서는 어렴풋이 알고 있어서 쉽게, 또는 안일하게 default option만 사용하고 있던 JPA Transactional을 정리하는 계기가 되었다면, 이 글을 쓰면서는 그 JPA Transactional에 대해 깊이 그리고 더 정확히 알게 되고 다시 한번 생각해 보는 계기가 되었습니다.

빠른 생산성을 위해 dataSource 접근을 쉽게 해주는 JPA, 시간이 지나면 이러한 기본적인 세팅들이 오히려 성능에 영향을 미칠 수 있습니다. 이를 위해 이미 잘 동작하고 있는 서비스, 라이브러리라도 한 번쯤 되돌아보면 좋을 것 같습니다.

또한 서비스가 성장해 가고 점점 성능에 관한 챌린지가 생긴다면 쉽게 DB upgrade를 하거나 샤딩으로 크게 구조 변경을 하기 이전에, 다음과 같은 방법으로 개선할 방법이 있는지 알아보시기 바랍니다.
