---
title: "캐시를 적용하기 까지의 험난한 길 (TPS 1만 안정적으로 서비스하기)"
source: "https://toss.tech/article/34481"
author:
published:
created: 2026-10-11
description: "TPS가 평균 1만, 최대 2만까지 늘어난 약관(terms) 서버에 안정적인 서비스 제공을 위해 캐시를 적용한 이야기를 들려드리려고 해요."
tags:
  - "clippings"
---

> [!summary]
> Toss Bank's terms-agreement server (10k average, 20k peak TPS) needs strong consistency, since a revoked consent must never be served stale, so it chose a look-aside Redis cache over read replicas and evicts only after commit via JPA entity listeners and `@TransactionalEventListener(AFTER_COMMIT)`. A failed eviction force-opens a Resilience4j circuit breaker that sends all reads to the DB, and a 3 ms race with Kafka consumers was fixed by ordering the eviction before the Kafka publish through `TransactionSynchronization` ordering. The last gap, reads between commit and eviction, was closed by redefining the consistency policy around API completion instead of writing more code.

![캐시를 적용하기 까지의 험난한 길 (TPS 1만 안정적으로 서비스하기)](https://resources-fe.toss.im/image-optimize/width=3840,quality=75/https%3A%2F%2Fstatic.toss.im%2Fassets%2Ffinance-tips%2Fcover-financial-tips-cache-data.jpg)

#Server

김경윤 · 토스뱅크 ML Engineer

2025년 3월 31일

안녕하세요, 토스뱅크 Server Developer 김경윤 입니다.

토스 커뮤니티, 그리고 토스뱅크에서는 하루에 수 백번의 라이브 배포가 일어나고 있으며 다양한 개선점과 신규 제품들이 빠르게 출시되고 있어요. 이렇게 많은 배포를 기반으로 토스뱅크가 성장하면서 토스뱅크를 이용하는 사용자도 많아졌는데요. 이로 인해서 TPS가 평균 1만, 최대 2만까지 늘어난 약관(terms) 서버에 안정적인 서비스 제공을 위해 캐시를 적용한 이야기를 들려드리려고 해요.

## Database: 더 이상 버틸 수 없다!

약관 서버는 사용자가 동의 또는 철회한 약관 및 동의서 동의 여부를 기록하고 조회할 수 있는 서비스예요. 사용자가 동의 그리고 철회하는 경우는 그렇게 많지 않지만, 동의 여부에 따라서 개인 정보를 제3자에게 제공해도 되는지, 토스뱅크가 사용해도 되는지 등 다양한 비지니스에서 약관 및 동의서 동의 여부를 확인해요.

(앞으로는 ‘약관 및 동의서’를 간단히 ‘약관’이라고 부를게요.)

![](https://static.toss.im/ipd-tcs/toss_core/live/7feb8944-5dee-4996-903c-d9db84387ab7/image.png)

어느 날, 토스뱅크에서 새로운 서비스를 배포하면서 TPS가 급증했고, 이로 인해 DB 조회량이 급증하여 DB 부하가 심각해졌었어요. 이 트래픽이 유지될 경우 다른 서비스에도 문제가 생길 수 있다고 판단했고, 급히 롤백을 진행하며 DB 부하를 줄일 방안을 고민하게 되었어요. 그 결과, 많은 분들이 알고 계신 ‘캐시’를 적용하기로 했지만, 막상 시도해 보니 생각보다 간단치 않았어요.

## 캐시 적용은 보다 신중하게

이 글을 읽으면서, “어? 그럼 Replication된 Database를 두고 부하를 분산하면 되는거 아니야?” 라고 생각할 수 있어요. 약관은 토스뱅크 고객의 개인정보와 밀접한 연관성이 있어요. 약관 동의 여부는 사용자의 정보를 특정 목적으로 이용해도 되는지, 제3자에게 공유가 되도 되는지 결정하는 기준이기 때문이에요.

그래서 약관 동의 여부는 값이 DB에 Commit 되는 순간, 바로 다음 요청에 DB에 저장된 값이 정확하게 응답되어야해요. 이를 Strong Consistency라고 부르며, 데이터의 무결성을 보장하기 위해 필수적이에요. 만약, 잘못된 응답을 한 번이라도 발생하면, 고객이 약관을 철회한 이후에도 개인정보가 공유되는 등의 보안 문제가 발생할 수 있어요. 따라서 데이터 신뢰성과 정확성을 보장하기 위해 Replication Database는 사용하지 않기로 했어요. Replication 구조에서는 복제 지연(Replication Delay)이 발생할 가능성이 있기 때문이에요. 대신, Strong Consistency를 유지하면서도 빠르게 조회가 가능한 Redis Cache를 활용해 고객의 약관 동의 상태를 안전하게 관리하기로 결정했어요.

### 이러한 방식으로 캐시를 적용했어요!

![](https://static.toss.im/ipd-tcs/toss_core/live/cb4390cc-0d43-4d98-998f-ff21a1d7102d/image.png)

약관 서버는 대부분 조회성으로 캐시를 접근하므로, DB의 정보가 자주 변경되지 않고, 대부분의 케이스는 Cache Hit를 하기 때문에, Look-aside 전략을 사용했어요. Look-aside 전략은 캐시에 원하는 데이터가 있는지 먼저 확인하고, 데이터가 없다면 DB에 접근한 후에 캐시에 저장하고 응답하는 방식이예요. 만약 DB 정보가 자주 변경된다면 다른 방식을 고민해야해요.

```
@Component
class TermsAgreementEntityListener {
    private val eventPublisher: ApplicationEventPublisher by lazy {
        SpringContext.context
    }

    @PostUpdate
    @PostRemove
    @PostPersist
    fun postProcess(termsAgreement: TermsAgreement) {
        eventPublisher.publishEvent(
            StrongConsistencyCacheEvictEvent.of(
            termsAgreement = termsAgreement,
            )
        )
    }
}

@Component
class StrongConsistencyCacheEvictListener(
    private val strongConsistencyCacheService: StrongConsistencyCacheService,
) {
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    fun listen(event: StrongConsistencyCacheEvictEvent) {
        strongConsistencyCacheService.evict(
            // ...
        )
    }
}
```

캐시 만료처리는 Spring의 `@EntityListener` 와 `@TransactionalEventListener` 를 사용해서, DB에 Commit된 이후에 캐시가 만료되도록 했어요. DB에 Commit 전에 만료처리를 한다면, 다른 요청에서 Commit 전 데이터를 다시 캐시에 적재하는 아래와 같은 케이스가 발생할 수 있기 때문이에요.

### \[과거 버전이 다시 적재되는 케이스\]

1. A Thread: 약관 동의 여부가 변경되어, Entity Version이 1에서 2로 올라감
2. A Thread: Entity Version 1 캐시가 Evict 처리 됨 (아직 Commit 전)
3. B Thread: Cache Miss로 Database에서 ⚠️ Entity Version 1을 다시 Cache에 적재함 ⚠️
4. A Thread: Entity Version 2 Commit
5. C Thread: Cache Hit로 ⚠️ 잘못된 Entity Version 1을 응답함 ⚠️

이렇게 보면, 완벽한 것 같지만, `@TransactionalEventListener` 가 `AFTER_COMMIT` 으로 설정되어 있어, Cache Evict 처리가 실패해도, 이미 Commit 된 상태이기 때문에 Transaction이 Rollback 되지 않는 문제가 있어요. 그러면, 과거 캐시 버전이 지속적으로 응답되는 문제가 있죠.

```
/* Strong Consistency Cache 서비스 */
@Service
@CircuitBreaker(name = ResilienceConfiguration.REDIS_CIRCUIT_BREAKER)
class StrongConsistencyCacheService

/* Circuit Breaker 설정 */
@Bean
fun redisCircuitBreaker(registry: CircuitBreakerRegistry): CircuitBreaker {
    val circuitBreaker = registry.circuitBreaker(
        REDIS_CIRCUIT_BREAKER,
        circuitBreakerConfig()
    )

    circuitBreaker.eventPublisher.onError { error: CircuitBreakerOnErrorEvent ->
        // 하나의 오류라도 발생하면, 즉시 Force Open
        circuitBreaker.transitionToForcedOpenState()
    }

    return circuitBreaker
}

/* Cache Get 하는 메서드 */
fun <T> getOrElse(
    key: String,
    orElseFunc: () -> T?,
): T? {
    val value: T? = try {
            // [1] - Cache Get 도중에 Circuit이 걸려서 Exception 발생
        strongConsistencyCacheService.get(
                        key = key,
        )
    } catch (ex: Exception) {
            // [2] - Circuit이 열려 있으면?
        if (redisCircuitBreaker.state.isOpened()) {
                // [3] - Database 기준으로 리턴!
            return orElseFunc()
        } else {
                        throw e
        }
    }

    // ...
}
```

그러한 문제를 해결하기 위해서, Circuit Breaker를 활용했어요. 만약, Cache Evict을 실패하면, Circuit을 Force Open 해서 자동으로 닫히지 않도록 하고, Cache Get할 때 Circuit이 Open 되어있다면, 모든 트래픽은 바로 Database를 조회하도록 하여, 잘못된 캐시가 응답되지 않도록 방어해두었어요. 이러한 방법은 Database에 큰 부하가 부담될 수 있지만, 잘못된 약관 동의 상태가 응답되어 문제가 발생되는 것보다, Database에 부하를 주고 빠르게 캐시에 대한 문제를 파악 및 해결하는 것이 맞다고 생각해서에요. 아직 이러한 경우를 만난 적이 없지만, 문제 발생 시 빠르게 확인, 해결할 수 있도록 상시 모니터링 중입니다!

## 이렇게 열심히 생각했지만 현실은…?

그럼 Strong Consistency를 잘 지키고 있는지 확인을 해야 하는데요. 그러기 위해서 서버에는 캐시를 적용했지만, 응답은 항상 DB에 저장된 데이터를 응답 하도록하고 DB와 캐시 데이터를 비교해서 확인했어요. 열심히 준비했기 때문에 한 번에 테스트를 통과할 줄 알았지만 언제나 그렇듯, 아래와 같은 문제를 만났어요.

### 0.003초 차이로 발생하는 불일치 케이스

\[문제 과정\]

- A Thread - 약관 동의 발생
- A Thread - `TermsAgreement` 값이 변경되어서, ApplicationEvent 발행
- A Thread - 약관 동의 여부 변경 Kafka Event Produce
- A Thread - `TermsAgreement` 가 DB에 Commit 됨
- B Thread - 약관 동의 여부 변경 Kafka Event Consume
- B Thread - 약관 동의 여부 조회시 캐시로부터 ⚠️ 이전 Entity Version 조회 됨 ⚠️
- A Thread - `AFTER_COMMIT` 설정이 되어있어, 이때 Cache Evict 됨

A Thread에서 Commit 이후, Cache를 Evict하는 그 0.003초 사이에 Kafka Event를 Consume한 곳에서 잘못된 캐시를 조회한 문제를 발견했어요. 이 케이스는 생각보다 간단히 해결할 수 있었어요. Kafka Event를 Cache Evict 처리 이후에 발행하도록 하면 되죠.

```
/* Strong Consistency Cache Evict Listener */
@Component
class StrongConsistencyCacheEvictListener(
    private val strongConsistencyCacheService: StrongConsistencyCacheService,
) {
    @Order(Ordered.LOWEST_PRECEDENCE - 1)
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    fun listen(event: StrongConsistencyCacheEvictEvent)
}

/* @TransactionalEventListener와 동일한 역할을 하는 메서드 */
fun doActionAfterCommitIfTransactionExist(order: Int = Ordered.LOWEST_PRECEDENCE, action: () -> Unit) {
    if (TransactionSynchronizationManager.isSynchronizationActive()) {
        TransactionSynchronizationManager.registerSynchronization(object : TransactionSynchronization {
            override fun afterCommit() {
                action()
            }

            override fun getOrder(): Int {
                return order
            }
        })
    } else {
        action()
    }
}

/* Kafka Event Produce 하는 부분 */
doActionAfterCommitIfTransactionExist {
    tossKafkaTemplate.send(
        topic = termsAgreementChangeTopic,
        key = termsAgreement.userId.toString(),
        value = termsAgreement,
    )
}
```

Cache Evict과 비슷한 방식으로, Database Commit 이후에 처리되도록 `TransactionSynchronizationManager` 를 활용했어요. 이때, Cache Evict과 Kafka Event Produce가 Commit 이후에 발생하도록 되어있으므로, 반드시 Cache Evict 이후에 Kafka Event Produce가 되도록 `@Order` 와 `TransactionSynchronization` Interface의 `getOrder` 메서드를 Override 하여 순서를 지정하여 처리 순서를 보장되도록 했어요. 자, 이제 그러면 아래와 같이 처리되므로 문제가 해결될거예요.

\[문제 해결 후 과정\]

- A Thread - 약관 동의 발생
- A Thread - `TermsAgreement` 값이 변경되어서, ApplicationEvent 발행
- A Thread - `TermsAgreement` 가 DB에 Commit 됨
- A Thread - `AFTER_COMMIT` 설정이 되어있어, 이때 Cache Evict 됨
- A Thread - 약관 동의 여부 변경 Kafka Event Produce
- B Thread - 약관 동의 여부 변경 Kafka Event Consume
- B Thread - 약관 동의 여부 조회시 캐시로부터 변경 후 Entity Version이 조회 됨

### 그래도 Commit 이후 Cache Evict 처리 되기전에 조회하면…?

Kafka Event가 아니더라도, 발생할 확률은 엄청나게 낮지만, 여전히 Cache Evict 되기 전에 사용자의 요청이 들어온다면, 발생할 수 있어요. 이 경우는 코드로 어떻게든 해결할 수 있지만, 정책으로 해결했어요. “정책??” 이라는 생각이 잠깐 드실 거예요. 다시 처음으로 가보면, 우리는 아래와 같은 목표를 가졌어요.

> 약관 동의 여부는 값이 DB에 Commit 되는 순간, 바로 다음 요청에 DB에 저장된 값이 응답되어야 한다.

중요한 포인트는 “바로 다음 요청에 DB에 저장된 값이 응답되어야 한다” 입니다. `@TransactionalEventListener` 로 전달된 이벤트가 모두 처리되기 전에는 아직 API 응답을 하기 전 상태예요. 즉, 약관 동의 또는 철회 요청이 아직 완벽히 처리가 되기 전인 상태입니다. 그래서, Cache Evict 처리 되기 전은 아직 API가 처리 중인 상태인거죠! 그래서, 약관 서버는 아래와 같은 정책을 최종적으로 가지게 됩니다.

> 약관 동의 여부는 약관 동의 또는 철회 요청 API 처리가 완료된 순간, 바로 다음 요청에 DB에 저장된 값이 응답되어야 한다.

이러면, 제가 생각했던 문제가 더 이상 문제가 아니게 되었고, 코드를 작성하는 저와 제품을 담당하는 PO 모두 행복하게 약관을 서비스할 수 있게 되었어요!

## 캐시를 적용하면서 느낀점

### Execution Over Perfection (완벽해지려 하기보다 실행에 집중하라)

토스 커뮤니티의 여러 Core Value 중 하나인데요. 사실 매우 중요한 시스템 중 하나이기 때문에, 캐시를 적용하기 전에 완벽해지기 위해 Legal, Compliance 등 다양한 부분들을 먼저 검토하고 어떤 문제가 발생할지에 대해 다양한 방면을 고민하느라 캐시를 적용하는데 많은 시간이 들었던 것 같아요. 만약 Legal, Compliance 검토 이후 정책을 바로 세우고 캐시를 적용하여 모니터링해가며 만났던 문제들을 하나씩 해결해 나간다면 좀 더 빠르게 적용할 수 있었지 않을까 생각이 들었어요.

### 코드로 해결할 수 있지만, 정책을 조금만 틀면 더 쉽게 해결할 수 있다

프로그래머는 모든 것을 코드로 해결하려고 하면 안된다고 개인적으로 생각해요. 다양한 문제들이 존재할 때, 코드보다 더 쉬운 방법이 어딘가에는 존재할거에요. 이번에 말씀드린 문제를 해결한 과정은 정말 짧아 보이지만, 그 전에 수 많은 코드를 작성하고, 지웠고, 방법들을 고민했었어요. 결국 정책을 수정하여 코드보다 간단히 해결할 수 있었어요.

### 마무리

지금은 DB에 큰 부하 없이, 최대 2만 TPS 트래픽을 든든하게 버텨주는 서비스가 되었어요. 최대 2만 TPS의 트래픽은 사실, 한 번 사용자의 요청에 MSA 서비스들이 여러번 호출해서 수치가 높게 보이는 부분도 있는데요? 이런 불필요한 트래픽을 줄이기 위해, Netflix의 Passport와 비슷한 개념인, TermsPassport 와 같은 기술도 고민하고 있어요. 아직은 트래픽이 그렇게 높지 않아 적용을 하지 않지만, 만약 적용한다면 추후에 다시 글로 찾아뵐께요!

[Server Developer로 지원하기](https://toss.im/career/job-detail?job_id=4071141003&company=%ED%86%A0%EC%8A%A4%EB%B1%85%ED%81%AC&detailedPosition=Product)

댓글 33

댓글 관련 문의: [toss-tech@toss.im](mailto:toss-tech@toss.im)

![프로필 이미지](https://resources-fe.toss.im/image-optimize/width=96,quality=75/https%3A%2F%2Fstatic.toss.im%2Fillusts%2Fimg-profile-emoji-10.png)

랜덤 변경

명랑한기린

단순히 캐시 Look Aside 전략 쓰면 1만 tps 버틸 수 있다 확인

활기찬다람쥐

안녕하세요 데이터베이스에 2만 TPS가 들어오는것을 막기위해 레디스 캐싱을했을때 발생할수있는 문제점이 있을것 같아요. 해당 데이터를 클러스터에 한 노드에 넣는다면 핫키 이슈가 발생할 것같은데요 해당 이슈는 없었나요?

유쾌한나비

ㅁㄴㅁ

쾌활한캥거루

잘 읽었습니다! \[문제 해결 후 과정\] 에서 Kafka Consumer 는 이벤트를 소비할 때 어떤 작업을 수행하는지 알 수 있을까요?!

신나는고래

afterCommit을 활용하여 Cache Evict·Kafka Event Produce 하는 경우, Commit 이후 즉시 애플리케이션 크래시가 발생했다고 가정한다면 Cache는 무효화되지 않고, Kafka Event는 유실될 것 같은데 어떻게 대처하는지 알 수 있을까요? Outbox 등의 기법을 활용하여 데이터 영속화(Commit)와 Cache Evict·Kafka Event Produce를 원자적으로 묶지 않아도 될지 궁금합니다.

재치있는다람쥐

안녕하세요 단순하게 글 내용으로는 캐시레이어를 도입하여 2만 TPS를 버텼다로 보입니다. 좀 더 자세히 듣고 싶습니다. 디비 스펙은 어떻게 되며 서버는 몇대인것인지 단일 디비 인지 캐시 서버로 레디스를 도입했을때 레디스 서버의 스펙과 서버 대수는 몇대인지 레디스 서버 cpu/mem 에는 문제가 없었는지? 캐시 방출 됬을때 데이터베이스 cpu는 어디까지 올라오는지? 등이 궁금합니다.

재치있는기린

안녕하세요, 혹시 Circuit Breaker의 상태는 인스턴스 간에 어떻게 공유하셨나요? 한 인스턴스가 커밋했지만 Redis에 반영하지 못해 서킷이 열렸을 때 다른 인스턴스는 이 사실을 어떻게 통지받는지, 아니면 약관 서버는 다중 인스턴스가 아닌 단일 인스턴스 구조인지 궁금합니다.

초보개발자취준생

Look-aside 사용하실때 race condition 해결은 어떻게 하셨나요?

씩씩한사자

테스트

다정한곰

안녕하세요, '문제 해결 후 과정' 파트에서, "B Thread - 약관 동의 여부 조회시 캐시로부터 변경 후 Entity Version이 조회 됨" 대신에, "B Thread - 약관 동의 여부 조회시 캐시가 비어있어서 DB 를 조회함" 이 될 것 같은데, 제가 맞게 이해한걸까요?

김경윤

넵 이해하신게 맞아요! 캐시가 비어있어, DB로 부터 조회된 데이터를 적재한 후이고, 약관 동의 여부 조회시 캐시로부터 "변경 후 Entity Version"이 조회가 된 상황입니다!

다정한곰

안녕하세요, '0.003초 차이로 발생하는 불일치 케이스' 파트에서, ('이러한 방식으로 캐시를 적용했어요!'에서 사용하신) @TransactionalEventListener 대신 class TransactionSynchronizationManager 를 사용하신 이유가 궁금합니다.

김경윤

@TransactionalEventListener는 기본 설정이면 트랜잭션이 없을 때 이벤트가 아예 무시돼요. fallbackExecution = true 옵션을 줘야 실행되는데, 이걸 실수로 빼먹으면 이벤트가 호출되지 않아 디버깅이 어려울 수 있어요. 그래서 코드 수정 최소화하면서 안정적으로 처리하려고 TransactionSynchronizationManager를 사용했습니다.

신나는원숭이

왠지 JPA 2차캐시를 사용했다면 일련의 문제가 없었을것 같은데, JPA 2차 캐시를 사용하지 않은 이유가 있을까요?

김경윤

JPA 2차 캐시는 고려 대상에 없었는데요? 지금 간단히 생각해보면, Circuit Breaker를 통한 Fallback 핸들링이 힘들고, 실제로 캐시할 때 사용되는 키는 Entity의 ID가 아니라, 사용자의 정보와 Entity의 다른 필드를 조합한 Key를 사용하고 있어서, 자유롭게 키를 만들기 어려운 환경이다보니 적합하지 않은 방법일 것 같습니다!

다정한고양이

좋은 글 감사합니다

유쾌한나비

안녕하세요! 글 너무 잘 읽었습니다! 특히 cache evict 실패를 고려해서 circuit breaker를 도입하신 부분이 정말 인상 깊고 유익한 내용이었어요 👍👍 관련해서 한 가지 질문이 있어요! 데이터 신뢰성과 정확성을 보장하기 위해 복제 지연이 발생할 가능성이 있는 Replication Database는 사용하지 않기로 하셨다고 하셨는데요, 복제 방식 중 동기식 복제를 활용하는 방법도 있을 것 같은데, 혹시 해당 방식을 채택하지 않으신 이유가 있으실까요??

김경윤

말씀하신 것 처럼, 모든 Replication Database에 복제가 완벽하게 되는 것을 보장받는 설정으로 DB에 의존할 수 있을 것 같아요. 하지만, 토스뱅크에서는 여러 개의 Replication Database를 사용하고 있고, 이러면 N개의 DB에 복제되는 것을 기다려야하는 Master Database의 Write 성능이 크게 떨어질 수 있어서 피할 수 있다면 피하는게 좋다고 생각해요.

씩씩한부엉이

좋은 글 써 주셔서 감사합니다. ☺️ 별도로 TermsAgreementEntityListener 를 정의하고, 캐시 무효화 이벤트 발행 - 이벤트 리스너에서 캐시 무효화하는 분리된 프로세스를 정의한 배경이 있을까요? 만약 별도의 도메인 이벤트를 사용하고 있다면 StrongConsistencyCacheEvictListener 에서 도메인 이벤트를 핸들링하는 방식으로도 접근해볼 수 있었을 것 같아 질문 드립니다!

김경윤

캐시 무효화 이벤트를 TermsAgreementEntityListener에서만 발행하는 것이 아니라, 강제로 캐시를 초기화하는 것과 같은 다른 비지니스에서도 무효화를 할 니즈가 있었기 때문입니다. 말씀하신 것 처럼 StrongConsistencyCacheEvictListener에서 도메인 이벤트를 처리할 수 있지만, 이 Lisener가 Entity의 변경사항을 받아서 처리한다는 느낌은 없는 것 같아요. 관점의 차이 같습니다!

다정한곰

좋은 글 써주셔서 감사합니다👍 엔티티 저장시에는 캐시에 값이 없을 것 같은데. PostPersist에도 캐시 evict하는 이유가 따로 있는지 궁금합니다.

김경윤

좋은 부분을 짚어주셨네요! TermsAgreement Entity가 DB에 아에 없을 때, 약관을 동의하지 않은 상태로 Cache에 동의하지 않았다고 저장해두기 때문입니다. Entity가 새롭게 DB에 Insert 될 때, Evict 하여 기존에 동의하지 않았다는 캐시를 비우기 위해서에요.

씩씩한햄스터

혹시 Cache Evict을 실패하는 경우가 어떤 경우가 있는지 알 수 있을까요?

김경윤

상황은 정말 다양할 것 같습니다! 가장 흔한 이유는, Redis 장애로, 서비스가 Redis와 통신을 실패하여 Evict을 처리하지 못하는 경우가 있을 것 같아요.

다정한곰

아래 댓글 답변 중에 1. 약관 동의 발생 2. TermsAgreement 값이 변경되어서, ApplicationEvent 발행 3. AFTER\_COMMIT 설정이 되어있어, 이때 Cache Evict 됨 4. AFTER\_COMMIT 설정이 되어있어, 이때 Kafka Event Produce 5. 모든 ApplicationEvent가 처리되어 API 응답 내용이 있는데요. 이 말은 api 호출 시 이벤트를 발행하고 해당 이벤트가 완료되기 까지 대기하고 응답을 준다는 말씀이시죠?

김경윤

이해하신 내용이 맞습니다! 좀 더 자세히 설명드리자면, \`AFTER\_COMMIT\`이 설정되어있는, \`@TransactionalEventListener\`로 전달된 ApplicationEvent는 Transaction이 Commit이 된 이후에 이벤트 처리가 시작되고, 별도 쓰레드가 아닌, 동기 방식으로 처리가 되기 때문입니다.

다정한곰

대부분의 코드들이 다 이벤트 기반으로 처리하는 것 같아 되게 낯선 코드들이 많이 보이네요.. 덕분에 좋은 아이디어 받아갑니닷!

활기찬부엉이

\[문제 해결 후 과정\] A Thread - 약관 동의 발생 A Thread - TermsAgreement 값이 변경되어서, ApplicationEvent 발행 A Thread - AFTER\_COMMIT 설정이 되어있어, 이때 Cache Evict 됨 A Thread - TermsAgreement가 DB에 Commit 됨 A Thread - 약관 동의 여부 변경 Kafka Event Produce B Thread - 약관 동의 여부 변경 Kafka Event Consume B Thread - 약관 동의 여부 조회시 캐시로부터 변경 후 Entity Version이 조회 됨 Commit 다음에 Cache Evict 가 나와야 할 거 같습니다!

김경윤

확인해주셔서 감사합니다! 수정했습니다!

씩씩한고릴라

"약관 동의 여부는 약관 동의 또는 철회 요청 API 처리가 완료된 순간, 바로 다음 요청에 DB에 저장된 값이 응답되어야 한다." 이건 어떻게 보장해주나요? 대기큐 같은 것인 있는 걸까요?

김경윤

말씀주신 부분에 대한 보장은 \`@TransactionalEventListener\`로 전달된 Cache Evict 또는 Kafka Event Produce 이벤트가 모두 처리되고 나서, API 응답이 나가는 부분을 이용하여 보장하고 있어요. 순서를 정리하면 아래와 같아요. 1. 약관 동의 발생 2. TermsAgreement 값이 변경되어서, ApplicationEvent 발행 3. AFTER\_COMMIT 설정이 되어있어, 이때 Cache Evict 됨 4. AFTER\_COMMIT 설정이 되어있어, 이때 Kafka Event Produce 5. 모든 ApplicationEvent가 처리되어 API 응답

씩씩한치타

여러 서비스 사이에서 Consistency를 유지하기 위해 동작들의 순서를 세심하게 설정하고, 정책을 명확하게 설정하는 것으로 해결한 점이 인상 깊네요 잘 읽었습니다.

활기찬늑대

잘 읽었습니다!

김경윤님의 다른 글

- #### [AI가 팀 규칙을 지키도록 하는 방법](https://toss.tech/article/52631)
	2026년 09월 08일
- ![DS와 MLE가 함께 일하는 법](https://resources-fe.toss.im/image-optimize/width=256,quality=75/https%3A%2F%2Fstatic.toss.im%2Fdisposables%2Fog%2Fpair-coding-thumb.png)
	#### [DS와 MLE가 함께 일하는 법](https://toss.tech/article/ds-mle-cowork)
	2026년 08월 03일
