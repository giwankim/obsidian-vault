---
title: "캐시 스탬피드를 대응하는 성능 향상 전략, PER 알고리즘 구현 – 화해 블로그 | 기술 블로그"
source: "https://blog.hwahae.co.kr/all/tech/14003"
author:
published:
created: 2026-10-11
description: "새로운 기능을 개발하다보면 자연스레 운영 비용은 늘어나기 마련입니다. 서비스가 성장할수록 트래픽 또한 증가하는데요. 그럼에도 화해 커머스 도메인은 상시 운영 서버를 줄여 인프라 비용을 아꼈습니다. 그 중 하나인 PER 알고리즘 구현 사례를 공유합니다."
tags:
  - "clippings"
---

> [!summary]
> Hwahae explains cache stampede (a burst of duplicate DB reads and cache writes when a hot entry expires) and implements Probabilistic Early Recomputation, the XFetch algorithm from the 2015 VLDB paper "Optimal Probabilistic Cache Stampede Prevention", in Python as a template-method base class that stores the recompute duration next to the cached value in Redis. In their tests the cache never expired under load, and they give guidance on tuning β relative to TTL and recompute time. They also fix a race where the entry expired between the `PTTL` check and the `GET`.

## 캐시 스탬피드를 대응하는 성능 향상 전략, PER 알고리즘 구현

2024\. 02. 13

안녕하세요, 화해 백엔드 플랫폼 엔지니어 이현재입니다.

백엔드 엔지니어라면 데이터 관리를 위한 Oracle, MySQL 혹은 PostgreSQL처럼 DBMS도 사용하지만, Redis 같은 in-memory DBMS(이하 IMDB)도 빠질 수 없습니다. 주 메모리에 데이터를 적재하는 IMDB는 저장 매체 특성에 따라 전형적인 디스크 방식보다 데이터 조회 성능이 우월합니다. 다만 IMDB는 휘발성 저장 공간에 쌓는 데이터라 DBMS를 보조하는 캐시 저장소로 사용되는 편이죠.

이번에는 캐시를 사용할 때 자주 접하게 될 문제 중 하나인 캐시 스탬피드와 이를 해결하는 방법을 가볍게 소개해드리고자 합니다.

---

## 캐시 스탬피드란?

IMDB도 DBMS 한 종류이므로 당연히 한정된 저장 공간을 지닙니다. 한정된 저장 공간을 효율적으로 사용하기 위해 캐시에 만료 시간인 TTL을 지정하는 게 일반적인 사용 방법이죠. 따라서 대개 캐시는 `생성-조회-만료` 생명주기를 가집니다.

DBMS에서 꺼낸 데이터를 가공하여 캐시로 보관한다고 가정해봅시다. 만약 캐시가 만료되어 새로운 캐시를 생성하는 시간동안 요청이 몰리면 어떻게 될까요? 다들 예상하셨듯이 캐시가 재생성되기 전까지 순간적으로 DBMS에 읽기 요청이 집중되고 그게 다시 IMDB에 중복된 쓰기 요청을 야기합니다. 우리는 이러한 현상을 캐시 스탬피드라 부릅니다.

![](https://blog-wp.hwahae.co.kr/wp-content/uploads/2024/02/horses-5733227_1920.jpg)

사진 출처: pixabay

```
💡캐시 스탬피드 Cache Stampede
캐시가 만료된 상태로 요청이 몰리면 순간적으로 DB에 동일한 데이터를 조회한 뒤
캐시 시스템에 중복된 쓰기 요청이 몰리는 현상
```

캐시 스탬피드를 해결하기 위한 방법으로 캐시가 만료되기 전 배치로 재생성할 수도 있고, 여러 번 반복되는 이벤트가 발생할 때 마지막 이벤트만 실행하도록 디바운스 `Debounce` 개념을 도입하는 등 다양한 방식이 존재합니다. 하지만 이번에는 확률에 의거 한 PER알고리즘을 함께 살펴봅시다.

## PER알고리즘 논문 분석

**P** robabilistic **E** arly **R** ecomputation를 뜻하는 PER 알고리즘은 캐시 유효 기간이 만료되기 전 일정 확률로 캐시를 재연산하는 방식을 뜻합니다. 앞서 살펴본 캐시 스탬피드를 방지하기 위한 목적으로 등장한 PER 알고리즘은 2015년 VLDB 컨퍼런스에서 소개되며 알려집니다.

```
💡Very Large Data Bases, VLDB
데이터 관리 및 데이터베이스 연구자, 벤더 그리고 실무자를 위한 연례 국제 포럼
```

PER 알고리즘 논문 중 일부를 발췌하여 함께 살펴볼까요?

국제 표준 연속 간행물 번호, ISSN 2150-8097에 등재된 『Proceedings of the VLDB Endowment』에서 「Optimal Probabilistic Cache Stampede Prevention」 논문을 찾을 수 있는데요. 12페이지에 달하는 논문을 읽어보면 중간에 PER 알고리즘을 구현하기 위한 의사 코드를 소개합니다.

```javascript
function XFetch(key, ttl; β = 1)
    value, ∆, expiry ← CacheRead(key)
    if !value or Time() − ∆β log(rand()) ≥ expiry then
        start ← Time()
        value ← RecomputeValue()
        ∆ ← Time() – start
        CacheWrite(key, (value, ∆), ttl)
    end
    return value
end
```

의사 코드를 바탕으로 PER 알고리즘이 가진 핵심을 요약해볼까요?

1. `캐시 데이터value` 조회
2. `캐시 생성 소요 시간∆` 을 바탕으로 `가중치β` 를 부여한 뒤 랜덤한 x 생성
3. x와 `캐시 만료 시간expiry` 을 비교하여 캐시 갱신 여부 결정

즉, PER 알고리즘을 구현하려면 캐시 대상 데이터 뿐만 아니라 캐시 생성 소요 시간을 Redis에 함께 저장할 필요가 존재합니다. 의사 코드를 바탕으로 실제 동작하는 코드로 바꿔봅시다! 화해 백엔드는 주력 언어로 파이썬을 사용하니 이를 바탕으로 실제 동작하는 코드를 만들어볼게요.

## 파이썬으로 구현한 PER 알고리즘

가장 먼저 필요한 작업은 Redis에 담길 데이터 구조를 정의하는 일입니다.

```python
@dataclass
class RedisPERData:
    cached_data: Any
    expiry_gap_ms: int
```

이제 템플릿 메서드 패턴으로 PER 알고리즘을 사용하는 추상클래스를 구현해볼까요?

```python
@dataclass
class RedisCacheInfo:
    key: str
    cache_keep_second: int

class RedisPERCache(ABC):
    redis_client: Redis = redis_client()

    def per_fetch(self, beta: float = 1):
        expiry_ttl = self.redis_client.pttl(self._get_cache_info().key)
        if expiry_ttl <= 0:
            return self.__save_redis_per_cache()

        redis_data: RedisPERData = self.__find_redis_cache()
        gap_score = redis_data.expiry_gap_ms * beta * -math.log(random.random())
        if gap_score >= expiry_ttl:
            return self.__save_redis_per_cache()

        return redis_data.cached_data

    def __find_redis_cache(self) -> RedisPERData:
        return self.redis_client.get(self._get_cache_info().key)

    def __save_redis_per_cache(self):
        start_time = time.perf_counter()
        result_from_db = self._get_resource_data()
        processed_time = time.perf_counter() - start_time

        cache_info: RedisPERCacheInfo = self._get_cache_info()
        self.redis_client.set(
            cache_info.key,
            RedisPERData(
                cached_data=result_from_db,
                expiry_gap_ms=int(processed_time * 1000),
            ),
            cache_info.cache_keep_second,
        )

        return result_from_db

    @abstractmethod
    def _get_cache_info(self) -> RedisCacheInfo:
        pass

    @abstractmethod
    def _get_resource_data(self):
        pass
```

부모 클래스에서 public 메서드는 `per_fetch()` 뿐이며, 상속 받는 자식 클래스는 protected로 선언된 추상 메서드 `_get_cache_info()` 와 `_get_resource_data()` 만 구현하면 됩니다. 구상 클래스는 다음과 같은 모습을 그립니다.

```python
class ProductListCache(RedisPERCache):
    PRODUCT_LIST_CACHE_TTL = 60

    def _get_cache_info(self) -> RedisCacheInfo:
        return RedisCacheInfo(
            key="[REDIS_KEY]",
            cache_keep_second=self.PRODUCT_LIST_CACHE_TTL,
        )

    def _get_resource_data(self) -> List[Product]:
        return ProductService().get_list()

product_list: List[Product] = ProductListCache().per_fetch()
```

## 템플릿 메서드 패턴으로 구현한 이유

객체지향 원리 상 상속을 사용하면 자식 클래스는 부모 클래스를 바라봅니다. 상속은 여러 자식 클래스가 한 부모 클래스를 바라보게 만들죠. 그로 인하여 부모 클래스가 변경되면 수많은 자식 클래스에 영향을 미치는데요. 이처럼 상속은 의존성을 굉장히 넓게 퍼트리는 주범입니다. 부모 클래스를 건드는 순간 상속 받은 모든 자식 클래스가 영향을 받습니다. 결국 사이드이펙트가 겁이 날 수밖에 없는 개발자는 부모 클래스를 고칠 수 없는 상황을 맞이하게 되죠. 그렇기에 순수 객체지향을 추구할수록 상속을 지양하라고 이야기합니다.

다만 **상속에서 유일하게 템플릿 메서드 패턴은 부모와 자식 간 의존성 방향을 역전** 시킵니다. 추상 메서드를 인터페이스 대신 활용하여 부모 클래스가 자식 클래스를 미리 알고 있게 만듭니다. 이로서 자식 클래스는 부모 클래스가 지닌 내부 로직을 몰라도 되고, 자식클래스 자신이 책임질 `hook` 만 구현하면 되죠.

```
💡템플릿 메서드 패턴 template method pattern
상속 중 유일하게 부모-자식 간 의존성을 역전시킨다.
구조를 변경하지 않고 알고리즘(혹은 비즈니스 로직) 특정 단계를 다시 정의할 수 있게 만든다.
```

일반적인 상속과 달리 템플릿 메서드 패턴을 사용하면 자식 클래스 변경점은 자기자신만 영향을 받으며, 부모 클래스에 그 여파를 퍼트리지 않습니다. 또한 부모 클래스에 의존하는 자식 클래스를 만들지 않아 부모 클래스 변경점은 자식 클래스에 영향을 끼치지 않습니다.

인터페이스가 따로 존재하지 않는, 다중 상속이 가능한 파이썬은 다이아몬드 상속에 취약합니다. 상속 뿐인 파이썬은 추상 클래스를 사용할 때 더 조심해야 하니 템플릿 메서드 패턴으로 만들어보았습니다.

## PER 알고리즘 실제 테스트 결과

파이썬으로 구현한 코드가 실제로 잘 동작하는지 확인해보기 위하여 다음과 같은 조건으로 테스트하였습니다.

### 실험 조건

- 5분 간 0.2초 간격으로 호출, 각각 3회 반복
- 캐시 생성 시간, 5초 ~ 15초 랜덤

![](https://blog-wp.hwahae.co.kr/wp-content/uploads/2024/02/%E1%84%80%E1%85%B3%E1%84%85%E1%85%A2%E1%84%91%E1%85%B3.png)

TTL은 크게 60초와 90초로 테스트하였습니다. PER알고리즘이 아니라면 갱신 기대횟수는 TTL 60초는 5회, 90초는 3.3회입니다. 하지만 beta 1 기준으로 각각 30+회, 6.7회 실행되는 걸 관찰할 수 있습니다. 5분이라는 시간동안 모든 케이스에서 단 한 번도 캐시가 만료된 적은 없습니다. beta를 0.5로 지정해도 캐시가 만료된 다음 캐시를 재생성한 경우는 단 한 번도 존재하지 않습니다. TTL 60초와 90초간 캐시 갱신 횟수 차이가 큰 건 캐시 생성 소요 시간이 5~15초로 TTL과 60초와 큰 차이가 나지 않은 게 영향을 미쳤습니다. TTL 60초는 최소한 45초마다 캐시를 갱신해야 만료되지 않거든요. TTL 90초는 75초마다 재실행되면 캐시가 만료되지 않습니다. 이 외에 따로 정리하지 않았으나, 다양한 변인으로 실험으로 도출한 결과를 공유해드립니다.

1. 캐시 생성 소요 시간이 지나칠 정도로 작은 값인 경우 PER 알고리즘은 큰 의미를 갖지 못합니다.
	1. 베타 값이 이를 보완하기 위한 옵션입니다.
		2. 캐시가 자주 갱신되도 상관없다면 베타값을 일정 수준까지 높여도 문제가 없습니다.
		3. 하지만 캐시 생성 소요 시간이 지나칠 정도로 작은 값이라면 보통 캐시를 쌓지 않을 겁니다.
2. 반면 캐시 생성 시간과 TTL 간 차이가 크지 않다면 베타값을 줄이길 권장해드립니다.
	1. 실험 결과에서 알 수 있듯이 TTL과 캐시 생성 시간이 큰 차이나지 않는다면 캐시 갱신 횟수가 지나칠 정도로 많습니다.
3. PER 알고리즘은 확률에 의해 캐시를 갱신하므로 요청 횟수가 적다면 `gap_score` 가 `expiry_ttl` 보다 높을 확률이 낮아 큰 효과를 발휘하지 못 합니다.
4. 만약 캐시 생성 소요 시간이 TTL/tpm ms보다 크다면 PER알고리즘이 유의미한 효과를 보입니다.
	1. 변인을 변경하며 계속 테스트해보니 위와 같은 조건을 지키면 항상 캐시가 만료되기 전에 갱신되었습니다.

## 운영 중에 발생한 이슈 개선

코드를 보면 별다른 문제가 없어 보이지만, 아닙니다. 캐시 만료 시간을 Redis에서 꺼내오는 만큼 빈틈이 존재하는데요. 그 상황은 다음과 같습니다.

- Redis 캐시 만료 시간 조회 → 캐시 존재
- Redis 캐싱 데이터 만료 → 캐시 삭제
- Redis 캐시 데이터 조회 시 캐시 만료로 실패

이를 보완하고자 캐시 만료 시간을 조회 시 충분한 버퍼를 지정하여 캐시 데이터 조회 시간을 벌 수도 있습니다.

```python
def __has_redis_cache(self) -> bool:
    # 레디스 캐시 유무 확인 후 데이터 조회 시 캐시가 만료되는 걸 막기 위한 100ms
    return self.redis_client.pttl(self._get_cache_info().key) > 100
```

하지만 더 간단한 방법이 존재하죠? 처음부터 캐시 만료 여부를 캐시 만료 시간이 아니라 실데이터로 처리하면 됩니다.

### 개선 코드

```python
def per_fetch(self, beta: float = 1):
    redis_data: Optional[RedisPERData] = self.__find_redis_cache()
    if not redis_data:
        return self.__save_redis_per_cache()

    random_gap = random.random() or 1
    gap_score = redis_data.expiry_gap_ms * beta * -math.log(random_gap)
    expiry_ttl = self.redis_client.pttl(self._get_cache_info().key)
    if gap_score >= expiry_ttl:
        return self.__save_redis_per_cache()

    return redis_data.cached_data
```

몇 줄 안 되는 이 코드를 통해 우리는 비로소 캐시 스탬피드에 자유로울 수 있습니다. PER 알고리즘을 정의하고 논증하는 방법은 복잡해보일지라도 실제 코드로는 간단한 몇 줄 추가로 끝납니다. 참고 자료로 첨부한 논문 저자 페이지에서 PER알고리즘 논문을 PDF로 다운로드 받을 수 있으니 PER알고리즘에 대해 자세한 내용이 궁금하다면 찾아보길 권해드립니다.

## 맺음말

매년 새로운 기능을 개발하다보면 자연스레 운영 비용은 늘어나기 마련입니다. 서비스가 성장할수록 트래픽은 늘기 마련이고, 화해위크 등 프로모션을 진행할 때 평소 트래픽보다 5배 이상 늘어나는 건 예삿일이죠. 그럼에도 불구하고 화해 커머스는 최근에 상시 운영 서버를 줄여 인프라 비용을 아꼈습니다. 저 뿐만 아니라 커머스 도메인을 담당하는 모든 개발자들이 매 분기 별 모니터링 결과를 바탕으로 꾸준히 성능 개선을 챙겨주신 덕분입니다. PER 알고리즘은 그 중 하나일 뿐이죠. 흔히 우스갯소리로 ‘서버를 늘리는 비용이 개발자 임금보다 싸다.’라고 말하더라도 성능을 경시하지 않는 개발자가 되시길 바라겠습니다.

## 참고자료

논문 저자 홈페이지: [https://cseweb.ucsd.edu/~avattani](https://cseweb.ucsd.edu/~avattani)

논문: [https://cseweb.ucsd.edu/~avattani/papers/cache\_stampede.pdf](https://cseweb.ucsd.edu/~avattani/papers/cache_stampede.pdf)

객체지향, 상속과 합성: [https://www.linkedin.com/pulse/007-%25EC%2583%2581%25EC%2586%258D%25EA%25B3%25BC-%25ED%2595%25A9%25EC%2584%25B1-%25EC%2598%25A4%25EB%25B8%258C%25EC%25A0%259D%25ED%258A%25B8-66-%25ED%2598%2584%25EC%259E%25AC-%25EC%259D%25B4](https://www.linkedin.com/pulse/007-%25EC%2583%2581%25EC%2586%258D%25EA%25B3%25BC-%25ED%2595%25A9%25EC%2584%25B1-%25EC%2598%25A4%25EB%25B8%258C%25EC%25A0%259D%25ED%258A%25B8-66-%25ED%2598%2584%25EC%259E%25AC-%25EC%259D%25B4)

![avatar image](https://blog-wp.hwahae.co.kr/wp-content/uploads/2023/01/230104_fin_08_%E1%84%8B%E1%85%B5%E1%84%92%E1%85%A7%E1%86%AB%E1%84%8C%E1%85%A2.jpg)
