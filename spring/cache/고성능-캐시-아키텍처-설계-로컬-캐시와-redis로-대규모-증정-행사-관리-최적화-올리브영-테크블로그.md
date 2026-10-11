---
title: "고성능 캐시 아키텍처 설계 - 로컬 캐시와 Redis로 대규모 증정 행사 관리 최적화 | 올리브영 테크블로그"
source: "https://oliveyoung.tech/2024-12-10/present-promotion-multi-layer-cache/"
author:
published:
created: 2026-10-11
description: "지연 없는 증정 행사 시스템을 위한 다중 레이어 캐싱 기법"
tags:
  - "clippings"
---

> [!summary]
> Olive Young's coupon/gift squad caches each day's gift-promotion rules as versioned Redis (ElastiCache) lists: every config change writes a new `..._v{n}` key, and readers first fetch the latest version number. Persistently high ElastiCache Network Bytes Out led them to add a Caffeine local cache layer keyed by that version, so instances stay consistent without any invalidation messaging, configured per cache through an enum-driven `SimpleCacheManager`. Load tests on the product detail page showed TPS up 478% and Redis outbound bytes down 99.1%.

![올리브영 테크블로그 포스팅 고성능 캐시 아키텍처 설계 - 로컬 캐시와 Redis로 대규모 증정 행사 관리 최적화](https://oliveyoung.tech/static/a6fd6b3fccd484d51dc97cebe0b84d52/8515c/main_banner.webp)

## 고성능 캐시 아키텍처 설계 - 로컬 캐시와 Redis로 대규모 증정 행사 관리 최적화

## 지연 없는 증정 행사 시스템을 위한 다중 레이어 캐싱 기법

## 2024.12.10

안녕하세요.️ 쿠폰증정스쿼드에서 백엔드 개발 담당하는 어푸입니다!

지난 글에서는 [Redis Pub/Sub을 활용한 쿠폰 발급 비동기 처리](https://oliveyoung.tech/2023-08-07/async-process-of-coupon-issuance-using-redis/) 로 개선된 쿠폰 발급 프로세스를 소개해 드렸는데요.

이번에는 올리브영에서 증정 행사를 어떻게 운영하고 있는지 소개해 보려고 합니다. 아래 목차대로 잘 따라와 주세요!

### 목차

---

## 올리브영의 증정 행사? 증정품?

![](https://oliveyoung.tech/4af994c87ebbb514d8aa7640e45cf111/free.webp)

출처 - [GIPHY](https://giphy.com/gifs/cetfreedom-drlisaturner-dr-lisa-turner-lisaturner-1yMZsLtI3aCFCdwW6a)

올리브영에서 증정품을 받아보셨나요?

올리브영에서 제공하는 증정품은 화장품의 작은 샘플, 인기 아이돌 포토 카드, 화장품 파우치, 혹은 쇼핑백과 같은 다양한 품목으로 이루어져 있습니다.

고객은 상품 상세 페이지나 주문서에서 상품 구매 시 받을 수 있는 증정품 정보를 확인할 수 있는데요.

이러한 증정품 혜택은 구매 고객에게 부가적인 만족감을 제공할 뿐만 아니라, 브랜드 충성도를 높이는 등 마케팅 전략으로 중요한 역할을 합니다.

![product present2](https://oliveyoung.tech/static/f49d540ad9d3e75348daed299c223a3e/8866f/product_present2.webp)

product present2

올리브영 모바일 상품 상세 페이지

![order present](https://oliveyoung.tech/static/ea8f876d097aaa29b523eef07b3d4002/8866f/order_present.webp)

order present

올리브영 모바일 주문서 페이지

하지만 이러한 증정품 제공은 생각보다 단순한 일이 아닙니다.

인기 있는 증정품 행사가 있는 경우, 수만 수십만 명의 사용자가 동시에 접속해 데이터를 조회하고, 행사 조건을 검증해야 할 수도 있습니다.

그래서 증정품들이 원활히 제공되기 위해서는 사전에 철저히 설정된 증정 행사 정보가 필요합니다.

이를 위해 올리브영의 쿠폰 증정 스쿼드는 각 증정 행사에 대한 지급 조건 데이터를 설정하고, 고객이 특정 조건을 충족 시 자동으로 증정품이 지급되도록 설계 및 관리하고 있습니다.

---

## 증정 행사 데이터는 어떻게 관리되고 있나요?

## 증정 행사의 기반 데이터는 어디에 저장될까요?

증정품 지급을 위해서는 고객의 구매 정보와 미리 설정된 행사 조건 데이터를 정확히 조합해야 합니다.

예를 들어, 고객이 특정 상품을 몇 개 구매했는지, 행사 대상 상품에 포함되는지 등을 판단하여 지급할 증정품의 종류와 수량을 결정합니다.

이 데이터는 관계형 데이터베이스(RDBMS)인 Amazon RDS에 저장됩니다.

![AmazonRDS](https://oliveyoung.tech/static/cbc26de714305ed60ad0de094114f5e6/0c8fb/AmazonRDS.webp)

ChatGPT로 생성된 이미지입니다.

행사 기간과 증정품을 지급하는 대상 상품, 배송할 수 있는 지점의 정보 등을 Amazon RDS 내 여러 테이블에 나누어 저장하고 있습니다.

고객이 구매하려는 상품 정보와 저장되어 있는 증정 행사 데이터를 조합하면, 어떤 증정품을 받을 수 있는지 확인할 수 있죠!

그런데 상품 상세 페이지와 주문서에 고객이 접근할 때마다 RDS로 증정 행사 데이터를 조회하면 어떨까요?

유입이 아주 적은 쇼핑몰이라면 괜찮을 수 있을지 모르겠지만 올리브영엔 정말 많은 고객분이 찾아주셔서요.

디스크 기반으로 데이터를 조회하는 RDS에 부하가 발생하면 응답 속도가 늦어지고, 장애로 이어질 가능성이 큽니다.

그래서 메모리 기반으로 빠른 조회 속도를 보장하는 Amazon ElastiCache를 사용하여 자주 조회하는 데이터를 제공하도록 했습니다.

## Amazon ElastiCache로 글로벌캐시를 사용해 봅시다!

### ✅ 캐시 데이터의 구조

자주 조회하는 데이터에 대해 메모리 기반으로 빠르게 읽을 수 있도록 Redis를 대중적으로 사용합니다.

쿠폰 증정 스쿼드에서는 캐시용 Redis 서버로 Amazon ElastiCache를 사용하고 있습니다.

캐싱할 데이터를 어떤 형태로 담아서 조회 속도를 높일 수 있을지 고민이 많았는데요.

증정 행사 기반 데이터 중 오늘 진행하는 행사 에 대해 List 형태로 캐싱해 두고, 캐시 된 데이터를 조합하여 빠르게 행사 정보를 전달하도록 했습니다.

![list cache data](https://oliveyoung.tech/static/7b5104e85664fba2e42449cee3cf7e0c/5d4cc/list_cache_data.webp)

list cache data

아래 내용은 어떤 방식으로 데이터가 캐시 되어 사용자에게 보이는지 이해를 돕기 위한 설명입니다. 위 그림의 번호와 매칭된 내용을 참고해 주세요.

1. 오늘 진행하는 증정 행사 에 대한 정보가 여러 개의 List 형태로 캐시 되어 있습니다.
2. 1번의 데이터들을 조합하여 고객에게 제공할 수 있는 증정 행사 데이터를 만듭니다.
3. 2번으로 만들어진 데이터를 고객이 볼 수 있는 화면에 보여줍니다.

(위 예제는 이해를 돕기 위하여 만들어진 것으로 실제 데이터와는 상이합니다.)

### ✅ 캐시 데이터 현행화

증정 행사의 설정 정보가 변경되면 캐시 데이터도 그에 맞춰 변경되어야 하는데요.

증정 행사의 데이터가 변경될 때마다 새로운 버전의 캐시 데이터를 생성하고, 고객이 증정 행사 데이터를 조회할 때는 항상 최신 버전의 캐시 데이터를 조회하도록 했습니다.

이를 위해 버전 정보도 ElastiCache에 저장해두고 있습니다. 버전은 1, 2, 3... 으로 숫자가 증가하는 형태이고, List 형태로 행사 정보가 들어가 있는 캐시 데이터의 key는 버전 정보를 담고 있죠.

![renew cache version](https://oliveyoung.tech/static/2b70ae16396b786d5c693275af95a0ad/8c31b/renew_cache_version.webp)

renew cache version

앞서 언급했던 증정 행사 캐시 데이터 중 **행사 지급 조건** 을 예로 들어보겠습니다!

위의 그림은 왼쪽부터 오른쪽으로 시간의 흐름에 따라 데이터 변경이 발생한 케이스입니다.

1. 하루에 한 번 캐시 생성 배치가 실행됩니다. 이때 최초로 버전 1의 캐시 데이터가 생성됩니다. → 캐시 key: 행사\_지급\_조건\_ **v1**
2. 행사 담당자가 갑자기 A라는 증정 행사를 중단하고 싶을 수도 있겠죠? 중단된 행사에 대해서는 증정품이 지급되면 안 되기 때문에 즉시 캐시 데이터에도 반영되어야 합니다. 변경 사항을 반영한 버전 2의 캐시를 생성합니다. → 캐시 key: 행사\_지급\_조건\_ **v2**
3. 다른 행사 담당자는 B라는 증정 행사의 행사명을 변경합니다. 이 내용도 즉시 반영할 수 있도록 버전 3의 캐시를 생성합니다. → 캐시 key: 행사\_지급\_조건\_ **v3**

그림에서는 **버전 3이 가장 최신 데이터** 이니 이후 행사 데이터 조회 요청이 들어오면 버전 3의 캐시 데이터인 **행사\_지급\_조건\_v3** 만 바라보고 처리합니다.

이렇게 메모리 기반으로 조회할 수 있는 Redis 서버를 두었으니 RDS를 직접 조회하는 것보단 빠른 응답시간을 보장할 것입니다.

### ✅ 개선 포인트

하지만... 저희에겐 숙제가 하나 더 남아있었습니다.

자원을 모니터링하면서 유독 수치가 높게 유지되는 항목이 있었는데요. 바로 Amazon ElastiCache의 Network Bytes out 즉, **송신 네트워크 바이트** 수치였습니다.

앞서 **'오늘' 진행하는 행사** 에 대해서만 List 자료구조로 캐시 데이터를 저장해두고, 이를 조회한다고 말씀드렸는데요.

진행하는 증정 행사의 개수가 많을수록 ElastiCache 에서 송신하는 데이터의 크기가 커지기 때문에, 진행하는 행사와 유입되는 사용자가 많아지면 송신 네트워크 바이트 수치가 높게 유지되었습니다.

송신 네트워크 바이트 수치가 지속해서 높으면 네트워크 대역폭 포화로 인해 응답지연이 발생할 수 있고 최악의 경우 장애가 발생할 확률이 높아집니다.

이를 방지하기 위해 로컬 캐시를 적용하여 ElastiCache로 접근하는 횟수를 줄이기로 했습니다.

## 다중 레이어 캐시를 활용하여 개선합니다!

### ✅ 분산 환경에서 로컬캐시 적용 시 유의 사항

로컬 캐시를 사용하면 서버의 메모리에 바로 접근해서 빠르게 데이터를 조회할 수 있다는 장점이 있습니다.

하지만 무턱대고 로컬 캐시를 사용하면 분산 환경에서는 제공하는 데이터의 일관성을 보장하지 못할 수도 있습니다.

보통 서비스를 운영할 때 여러 대의 서버를 띄워두고 클라이언트의 요청에 응답하게 되는데요.

운영되고 있는 서버가 아래처럼 3대라고 가정하면, 서버마다 다른 캐시 데이터를 저장할 수 있어서 일관된 데이터를 제공하지 못할 수도 있습니다.

![different cache in server](https://oliveyoung.tech/static/d4d0a83d1763ecd7d274564cbc664373/6e19d/different_cache_in_server.webp)

different cache in server

모든 서버가 일관된 데이터를 제공할 수 있도록 하려면 어떻게 해야 할까요?

바로 ElastiCache와 로컬 캐시를 결합한 다중 레이어 캐시 전략과 캐시의 버전 정보를 활용하면 문제를 해결할 수 있습니다.

### ✅ 다중 레이어 캐시 적용 방법

![multi layer cache](https://oliveyoung.tech/static/4ff4e71fd5c904a6663b194667e2fc06/8c31b/multi_layer_cache.webp)

multi layer cache

이해를 돕기 위해 그림에 번호를 붙여두었습니다. 자세한 내용이 궁금하시면 번호와 매칭되어 있는 아래 설명과 함께 그림을 확인해 주세요.

(위 예시는 상품 상세 페이지에서 고객이 특정 상품을 조회한 상황을 가정했습니다.)

1. 사용자가 상품 상세 페이지에 진입합니다.
2. 조회한 상품을 구입했을 때 받을 수 있는 증정품을 알기 위해 상품 상세 페이지에서 증정 행사 조회 API를 호출합니다.
3. 증정 행사를 관리하는 Application은 캐시 된 증정 행사 데이터를 조회해야 하는데요. 최신 데이터를 조회해야 하므로 ElastiCache에 저장되어 있는 **최신 버전 정보를 조회** 합니다. → 1, 2, 3... 와 같은 숫자로 버전 정보가 조회됩니다.
4. 최신 버전을 확인했으니 이제 **해당 버전에 맞는 로컬 캐시를 조회** 합니다. 메모리로부터 반환된 로컬 캐시 데이터가 있다면 바로 **7번** 으로 이동합니다.
5. 메모리로부터 조회된 로컬 캐시 데이터가 없는 경우 **ElastiCache에 해당 버전에 맞는 캐시 데이터를 조회하여 반환** 합니다.
6. ElastiCache로부터 조회된 데이터를 로컬 캐시로 저장합니다.
7. 증정 행사 Application에서 조회된 데이터를 요청한 상황에 맞게 가공합니다.
8. 가공된 증정 행사 데이터를 상품 상세 페이지로 반환합니다.
9. 이제 고객은 상품 상세 페이지에서 증정 행사 정보를 확인할 수 있습니다!

### ✅ Caffeine Cache로 로컬캐시 구현하기

자 그럼 로컬 캐시를 구현하기 위해 어떤 방식으로 구현해야 할지 선택해야 하는데요.

Spring Boot에서 사용할 수 있는 여러 로컬 캐시 중 가장 성능이 뛰어나다는 Caffeine Cache를 선택했습니다.

대표적인 캐시의 종류와 특징들은 아래와 같으니 참고해 주세요.

![many caches](https://oliveyoung.tech/static/2cc0ec78c1ecddb096e5c9759f5c8fb0/0532e/many_caches.webp)

many caches

Caffeine Cache는 성능도 매우 뛰어나지만, 아주 쉽게 여러 가지 옵션을 설정할 수 있습니다.

- maximumSize: 캐시에 포함할 수 있는 최대 키 개수를 지정합니다. (maximumWeight와 함께 설정할 수 없습니다.)
- maximumWeight: 캐시에 포함할 수 있는 최대 무게를 지정합니다. (maximumSize와 함께 설정할 수 없습니다.)
- expireAfterAccess: 캐시가 생성되고 나서 마지막으로 읽은 후 설정한 시간이 지나면 자동으로 캐시에서 제거됩니다.
- expireAfterWrite: 캐시가 생성되고 나서 설정한 시간이 지나면 자동으로 캐시에서 제거됩니다.
- refreshAfterWrite: 캐시가 마지막으로 업데이트된 후 설정된 시간 간격으로 새로고침 됩니다.
- weakKeys: Weak References로 키를 저장합니다. 키에 대한 강력한 참조가 없는 경우 GC에 의해 수집됩니다.
- weakValues: Weak References로 값을 저장합니다. 값에 대한 강력한 참조가 없는 경우 GC에 의해 수집됩니다.
- softValues: Soft References를 사용하여 값을 저장합니다. 메모리 수요에 따라 LRU(Least-Recently-Used) 방식으로 GC에 의해 수집됩니다.
- recordStats: 캐시에 대한 통계를 적용할 수 있습니다.

Caffeine Cache는 yml, properties 파일이나 클래스로 설정할 수 있는데요.

yml, properties 파일로 설정할 때는 캐시별로 개별 설정이 불가능하다는 단점이 있습니다.

그래서 저희는 Enum 클래스로 개별 옵션을 설정할 수 있도록 했습니다.

적용한 코드 예제를 아래에 간단히 소개합니다.

1. build.gradle 파일에 Caffeine Cache 의존성을 추가합니다.

```kotlin
dependencies {
    implementation("com.github.ben-manes.caffeine:caffeine:3.1.8"
)
    implementation("org.springframework.boot:spring-boot-starter-cache"
)
}
```

2. Configuration 파일을 추가하여 설정합니다.

```kotlin
@EnableCaching
@Configuration
class CaffeineCacheConfig {

    @Bean
    fun caffeineCacheManager(): CacheManager {
        val cacheManager = SimpleCacheManager()
        val caches = CaffeineCacheType.values().map { cache ->
            CaffeineCache(
                cache.cacheName,
                Caffeine.newBuilder()
                    .expireAfterWrite(
                        cache.expiredAfterWrite,
                        TimeUnit.SECONDS
                    )
                    .maximumSize(cache.maximumSize)
                    .build()
            )
        }
        cacheManager.setCaches(caches)
        return cacheManager
    }
}
```

3. enum class로 캐시 타입을 지정합니다.

```kotlin
enum class CaffeineCacheType(
    val cacheName: String,
    val expiredAfterWrite: Long,
    val maximumSize: Long
) {
    TODAY_PRESENT_CONDITION("todayPresentCondition"
, 60, 100) // 생성 후 60초 뒤에 소멸되며, key는 최대 100개까지 저장할 수 있습니다.
}
```

4. 캐시 대상 데이터를 @Cacheable 어노테이션으로 지정합니다.

```kotlin
@Cacheable(cacheNames = ["todayPresentCondition"
], key = "#version"
)
override fun todayPresentCondition(version: Long): List<Condition>? {
    return cacheDao.getList(version, 0, -1) // ElastiCache에서 조회한 결과값
}
```

메소드 위에 선언된 어노테이션 속성을 보시면 key에 파라미터로 전달받은 version이 들어가 있죠? 이 버전은 ElastiCache로부터 조회된 값이며, 이 버전 정보로 분산 환경에서도 로컬 캐시의 일관성을 지킬 수 있습니다.

---

## 다중 레이어 캐시를 적용하면 성능이 얼마나 개선될까요?

자, 그럼 로컬 캐시를 적용했을 때 대량 트래픽이 유입된 상황에서 성능이 얼마나 좋아졌는지, Redis Network Bytes out 수치가 얼마나 개선되었는지 확인해 봐야겠죠?

증정 행사의 조회가 가장 많은 상품 상세 페이지를 기준으로 성능 테스트를 진행했습니다.

![performance test](https://oliveyoung.tech/static/054a82defcfce8fb5dc1d951ef4aeec5/63688/performance_test.webp)

performance test

성능 테스트 결과

동일한 자원 환경과 데이터 기준으로 TPS(초당 트랜잭션 수)는 478% 증가, Redis Network Bytes out 수치는 99.1% 감소했습니다.

다중 레이어 캐시를 적용하여 성능이 크게 향상되었고, Redis Network Bytes out 수치는 대폭 하락하면서 장애 발생 가능성을 낮추었습니다.

---

## 마치며..

2024년 한 해 동안 올리브영의 온라인 증정 행사 시스템을 구축하면서 많은 시행착오를 겪었습니다.

캐시 데이터 구조를 어떻게 설계해야 할지, 성능을 어떻게 개선할 수 있을지, 네트워크 대역폭이 포화될 경우 어떤 문제가 발생하고 이를 어떻게 해결할지 등 수많은 고민과 도전을 거듭했습니다.

이 과정에서 많은 분들의 도움과 조언을 받을 수 있었고, 덕분에 보다 나은 방향으로 문제를 해결하며 시스템을 지속적으로 개선할 수 있었습니다.

이 글을 빌려 함께 협업한 스쿼드와 귀중한 조언을 아낌없이 나눠주신 시니어 개발자분들에게 감사의 말씀을 드립니다. 🙇🏻♀️

이번 글에서는 올리브영 온라인몰의 증정 행사 시스템을 소개해 드렸는데요. 현재는 매장에서 운영 중인 증정 행사 시스템의 개편 작업도 진행 중이며, 이를 통해 더 효율적이고 안정적인 운영 환경을 만들어 나갈 계획입니다.

앞으로도 고객 여러분이 더 편리하게 혜택을 누릴 수 있도록 기술적인 고민을 이어가며 부족한 부분을 꾸준히 개선해 나가겠습니다.

![](https://oliveyoung.tech/281ee2db9ba3f58d24ca6ef657e42834/thankyou.gif)

출처 - [GIPHY](https://giphy.com/gifs/thedrewbarrymoreshow-drew-barrymore-cole-sprouse-the-show-XxcOCzT9kBsc6NQfKw)

긴 글 읽어주셔서 감사합니다!!!

caffeinecachepromotion

어푸 |

Back-end Engineer

운동과 사진 찍는 걸 좋아하는 개발자입니다.

<iframe title="Comments" src="https://utteranc.es/utterances.html?src=https%3A%2F%2Futteranc.es%2Fclient.js&amp;repo=oy-techblog%2Ftech-blog-comment&amp;issue-term=pathname&amp;label=comment&amp;theme=github-light&amp;crossorigin=anonymous&amp;async=true&amp;url=https%3A%2F%2Foliveyoung.tech%2F2024-12-10%2Fpresent-promotion-multi-layer-cache%2F&amp;origin=https%3A%2F%2Foliveyoung.tech&amp;pathname=2024-12-10%2Fpresent-promotion-multi-layer-cache%2F&amp;title=%EA%B3%A0%EC%84%B1%EB%8A%A5+%EC%BA%90%EC%8B%9C+%EC%95%84%ED%82%A4%ED%85%8D%EC%B2%98+%EC%84%A4%EA%B3%84+-+%EB%A1%9C%EC%BB%AC+%EC%BA%90%EC%8B%9C%EC%99%80+Redis%EB%A1%9C+%EB%8C%80%EA%B7%9C%EB%AA%A8+%EC%A6%9D%EC%A0%95+%ED%96%89%EC%82%AC+%EA%B4%80%EB%A6%AC+%EC%B5%9C%EC%A0%81%ED%99%94+%7C+%EC%98%AC%EB%A6%AC%EB%B8%8C%EC%98%81+%ED%85%8C%ED%81%AC%EB%B8%94%EB%A1%9C%EA%B7%B8&amp;description=%EC%A7%80%EC%97%B0+%EC%97%86%EB%8A%94+%EC%A6%9D%EC%A0%95+%ED%96%89%EC%82%AC+%EC%8B%9C%EC%8A%A4%ED%85%9C%EC%9D%84+%EC%9C%84%ED%95%9C+%EB%8B%A4%EC%A4%91+%EB%A0%88%EC%9D%B4%EC%96%B4+%EC%BA%90%EC%8B%B1+%EA%B8%B0%EB%B2%95&amp;og%3Atitle=%EA%B3%A0%EC%84%B1%EB%8A%A5+%EC%BA%90%EC%8B%9C+%EC%95%84%ED%82%A4%ED%85%8D%EC%B2%98+%EC%84%A4%EA%B3%84+-+%EB%A1%9C%EC%BB%AC+%EC%BA%90%EC%8B%9C%EC%99%80+Redis%EB%A1%9C+%EB%8C%80%EA%B7%9C%EB%AA%A8+%EC%A6%9D%EC%A0%95+%ED%96%89%EC%82%AC+%EA%B4%80%EB%A6%AC+%EC%B5%9C%EC%A0%81%ED%99%94+%7C+%EC%98%AC%EB%A6%AC%EB%B8%8C%EC%98%81+%ED%85%8C%ED%81%AC%EB%B8%94%EB%A1%9C%EA%B7%B8&amp;session="></iframe>
