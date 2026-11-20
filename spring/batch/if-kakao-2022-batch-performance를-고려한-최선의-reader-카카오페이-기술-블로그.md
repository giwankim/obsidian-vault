---
title: "[if kakao 2022] Batch Performance를 고려한 최선의 Reader | 카카오페이 기술 블로그"
source: "https://tech.kakaopay.com/post/ifkakao2022-batch-performance-read/"
author:
published: 2022-12-09
created: 2026-11-20
description: "if(kakao)2022 대량의 데이터를 Batch로 읽을 때의 노하우를 공유합니다."
tags:
  - "clippings"
---

> [!summary]
> 카카오페이 정산플랫폼팀의 if(kakao) 2022 발표 후속 글 1편으로, 하루 1억 건 규모의 배치에서 전체 성능의 대부분을 좌우하는 ItemReader 선택을 다룬다. MySQL Limit Offset 기반의 RepositoryItemReader·JpaPagingItemReader는 뒤 페이지로 갈수록 느려지고 JpaCursorItemReader는 전체 데이터를 메모리에 올려 OOM을 유발하므로, PK 조건(`where id > 마지막 id`)으로 offset을 항상 0으로 유지하는 QuerydslZeroOffsetItemReader와 Exposed DSL로 쿼리를 작성하는 ExposedCursorItemReader를 자체 구현했다. 300만 건 측정에서 JpaPagingItemReader가 약 112분 걸린 반면 두 Reader는 4~5분대로 데이터 건수에 선형 비례했고 Heap 사용도 안정적이었다.

## 시작하며

🔗 **if(kakao) 발표 영상 보러 가기: [Batch Performance 극한으로 끌어올리기](https://www.youtube.com/watch?v=L9K0l65wMbQ)**

안녕하세요. if(kakao)에서 ‘Batch Performance 극한으로 끌어올리기: 1억 건 데이터 처리를 위한 노력’ 세션을 진행한 카카오페이 정산개발파트 베니입니다. 세션에서 다루었던 이야기를 2편의 콘텐츠에 걸쳐 보다 자세히 설명드리려고 합니다. 첫 번째 편인 이번 콘텐츠에서는 배치 성능을 고려한 최선의 데이터 Read 경험을 말씀드리겠습니다. 배치 성능에 관심 있는 분들께 도움이 되었으면 좋겠습니다.

아직 if(kakao) 세션 영상을 보지 못하셨다면 영상 먼저 보고 오시길 추천드립니다. [Batch Performance 극한으로 끌어올리기: 1억 건 데이터 처리를 위한 노력](https://www.youtube.com/watch?v=L9K0l65wMbQ)

## 대량 데이터 처리

2017년도의 카카오페이와 2022년 4분기를 앞둔 카카오페이를 비교해보면 놀랄 만큼의 사업적 성장이 있었습니다. 제가 속한 팀인 정산플랫폼팀에서는 2017년에는 하루 평균 데이터 Access횟수가 25만 번 정도였다면, 2022년 말 현재는 하루 평균 1억 번 정도 데이터에 Access하고 있습니다. 이 과정에서 얻은 배치 성능 개선의 많은 노하우를 정리해보았습니다.

## 배치에서 Reader란?

배치에서 데이터(Item)를 Read하는 것(ItemReader)은 배치의 전체 성능에서 매우 큰 부분을 좌우합니다. 감히 저의 예측으로는 평균 80% 이상을 결정할 수 있다고 봅니다. 이렇게까지 READ를 중요하게 생각하는 이유는 무엇일까요?

![read\_1million\_in\_1million](https://tech.kakaopay.com/_astro/read_in_small.1_eVBfQ1_Z1DG7Q5.webp)

read\_1million\_in\_1million

전체 데이터인 100만 개 중에 100만 개를 모두 읽는다고 가정해보겠습니다. 아무런 걸림돌 없이 앞에서부터 차례대로 데이터를 읽으면 됩니다. 그러나 대부분의 상황은 이렇지 않습니다.

![read\_1million\_in\_10billion](https://tech.kakaopay.com/_astro/read_in_many.DX4CDrTe_1hcGut.webp)

read\_1million\_in\_10billion

보통은 이렇게 10억 개라는 많은 데이터 중에 필요한 데이터만 골라내야 합니다. **10억 개 중에 100만 개를 골라내는 작업** 이 바로 배치의 전체 성능을 크게 좌우하는 부분입니다. 대표적인 예시로 RDBMS에서 select 쿼리를 튜닝하는 것만으로도 극적으로 성능이 개선됩니다.

## Chunk Processing

Chunk는 하나의 큰 덩어리를 뜻하는 단어입니다. 데이터를 어떤 Chunk(덩어리) 단위로 나누어 처리하는 것을 Chunk Processing이라고 하고 대량 배치 처리 시에는 반드시 Chunk Processing으로 동작해야 합니다. 그 이유는 아래의 예시를 보면 이해할 수 있습니다. 수십 개의 적은 데이터를 처리할 때는 서버 애플리케이션에서 충분히 한 번에 처리할 수 있습니다. 그러나 1,000만 개와 같은 대량의 데이터를 처리하는 경우에는 서버의 물리적 한계로 한 번에 처리할 수 없습니다. 1,000개씩 나누어 10,000번 처리해야 합니다.

![](https://tech.kakaopay.com/_astro/chunk_processing.Cnn55yz6_Z1qKMdf.webp)

### 1,000만개의 데이터를 한 번에 처리할 수 없는 이유

1. 데이터가 1,000만 개가 아니라 2,000만 개로 늘어나는 경우도 고려해야 합니다. 결국에는 한계가 존재하고 무한정 메모리를 늘릴 수는 없습니다.
2. 배치 애플리케이션이 한 번에 1,000만 개를 받아들일 수 있더라도 그 외의 다른 시스템들은 불가능합니다. 예를 들어 그 어떤 RDBMS, NOSQL이라도 1,000만 개를 한 번에 read하고 write하는 것은 불가합니다.

## Pagination

Chunk Processing을 하기 위해서 데이터를 일정 개수만큼 나누어야 합니다. 이때, PageItemReader를 사용하게 되면 Page라는 단위로 데이터를 잘라서 처리할 수 있습니다. 전체 데이터 건수가 100만 개고 Page의 크기가 100이라고 하면 1번부터 만 번 Page까지로 나눌 수 있습니다.

### 기존의 PageItemReader

일반적으로 많이 사용하는 PageItemReader는 크게 2가지 정도가 있습니다.

1. **RepositoryItemReader**
2. **JpaPagingItemReader**

위의 ItemReader는 page number와 page size로 Item(데이터)을 구하는 방식입니다. 이런 ItemReader를 MySQL에서 사용하면 limit, offset 구문을 사용해 데이터를 구합니다.

```sql
-- 36번째 Page, 100개 Size
select * from student where gender = 'MALE' limit 3600, 100
```

### MySQL Limit Offset

MySQL의 Limit Offset은 Page 단위로 데이터를 읽는 쉬운 방법입니다. 그러나, Limit Offset은 **태생적인 성능 한계** 가 존재합니다.

Limit Offset이 없는 아래 쿼리의 결과가 1억 건이라고 가정해보겠습니다.

```sql
-- 조회결과: 1억 건, gender에 index 추가
select * from student where gender = 'MALE'
```

아래는 1억 건 중 최초의 100건만 조회하는 쿼리입니다.

```sql
-- 조회 결과: 100건, 조회 속도: 매우 빠름
select * from student where gender = 'MALE' limit 0, 100
```

아래는 1억 건 중 5천만 번째부터 100건만 조회하는 쿼리입니다. index가 있는 조건으로 조회하고 결과가 100건밖에 되지 않음에도 불구하고 아래 쿼리는 매우 느리게 조회됩니다.

```sql
-- 조회 결과: 100건, 조회 속도: 매우 느림 (환경에 따라 다르지만 최소 수 십 초는 걸림)
select * from student where gender = 'MALE' limit 50000000, 100
```

이 문제를 회피하기 위해서는 Limit Offset을 아예 사용하지 않거나 Offset이 작은 경우만 사용해야 합니다.

### ZeroOffsetItemReader

ZeroOffsetItemReader는 명칭에서 알 수 있듯이 Offset을 0으로 유지합니다.

![](https://tech.kakaopay.com/_astro/zerooffset.DFZeYg6j_NoJeS.webp)

1. PK(id)값 오름차순으로 정렬합니다.
2. 3번 Page를 조회한다면 2번 Page의 마지막 id값인 5235를 사용해 ‘where id > 5235’를 쿼리에 자동으로 추가합니다.
3. offset을 0으로 유지합니다.

이런 방식이면 offset이 항상 0이기 때문에 쿼리 조회 속도가 느려지지 않게 됩니다. 배치를 구현할 때 ZeroOffsetItemReader를 메인으로 사용하고 있습니다.

#### QueryDslZeroOffsetItemReader

ZeroOffsetItemReader의 쿼리 구현을 QueryDsl로 할 수 있도록 개선하였습니다.

```kotlin
QuerydslZeroOffsetItemReader(
    name = "orderQueryDslZeroOffsetItemReader",
    pageSize = 1000,
    entityManagerFactory = entityManagerFactory,
    idAndSort = Asc,
    idField = qOrder.id
) {
    it.from(qOrder)
        .innerJoin(qOrder.customer).fetchJoin()
        .select(qOrder)
        .where(qOrder.category.eq(CATEGORY.BOOK))
}
```

## Cursor

Chunk Processing으로 동작하기 위해 데이터를 나눠서 읽는 방법은 Pagination만 있는 것이 아닙니다. Cursor를 사용해 데이터를 조금씩 가져올 수도 있습니다.

![Cursor란?](https://tech.kakaopay.com/_astro/cursor.BVRKd_QM_Z1w2rFP.webp)

Cursor란?

### 기존 CursorItemReader

일반적으로 많이 사용하는 CursorItemReader는 크게 3가지 정도가 있습니다.

1. **JpaCursorItemReader**
2. **JdbcCursorItemReader**
3. **HibernateCursorItemReader**

CursorItemReader별 문제점은 다음과 같습니다.

JpaCursorItemReader는 올바른 MySQL Cursor 방식이 아닙니다. 데이터를 DB에서 모두 읽고 서비스 인스턴스에서 직접 Iterator로 cursor로 동작하는 것처럼 흉내 내는 방식입니다. 즉, 모든 데이터를 메모리에 들고 있기 때문에 OOM을 유발합니다.

사용한다면 JdbcCursorItemReader 혹은 HibernateCursorItemReader를 사용해야 합니다. MySQL Cursor방식으로 동작해서 데이터를 조금씩 가져와 OOM을 유발하지 않고 안전합니다. 그러나 쿼리를 구현할 때 JdbcCursorItemReader는 Native SQL로 구현해야 하고, HibernateCursorItemReader는 HQL로 구현해야 합니다. 즉, 모든 쿼리를 텍스트로 구현해야 합니다.

### 새로운 CursorItemReader

JdbcCursorItemReader 혹은 HibernateCursorItemReader를 사용한다면 배치가 동작할 때 큰 문제는 없습니다. 그러나 ItemReader의 쿼리를 Native SQL이나 HQL와 같은 텍스트로 구현하는 것은 가시적이지 않으며 실수를 유발할 가능성이 높습니다. 이런 문제를 해결하고자 ExposedCursorItemReader를 자체 개발하여 사용하고 있습니다.

#### ExposedCursorItemReader

쿼리를 구현할 때 텍스트로 구현하기보다 DSL(Domain-Specific Languages)형식으로 구현할 수 있다면 더 직관적이며 실수가 적어지게 됩니다. 그래서 Exposed DSL로 쿼리를 구현하는 방식을 도입하였습니다. 동작 방식은 JdbcCursorItemReader와 동일하지만 쿼리만 Exposed DSL로 구현하는 ExposedCursorItemReader를 개발하였습니다.

```kotlin
ExposedCursorItemReader<Order>(
    name = "orderExposedCursorItemReader",
    dataSource = dataSource,
    fetchSize = 5000
) {
    (Orders innerJoin Customers)
        .slice(Orders.columns)
        .select {
            (Orders.category eq "BOOK") and
                (Customers.age greaterEq 11)
        }
}
```

#### Exposed 특징

[JetBrains Exposed Github](https://github.com/JetBrains/Exposed)

1. 데이터베이스 Access 방식: SQL을 매핑한 DSL 방식, 경량화한 ORM인 DAO 방식
2. 지원하는 데이터베이스: H2, MySQL, MariaDB, Oracle, PostgreSQL, SQL Server, SQLite
3. Kotlin 호환성 (자바 프로젝트는 사용 불가)

## 성능 측정

JpaPagingItemReader, ZeroOffsetItemReader, ExposedCursorItemReader의 성능 측정자료입니다. 성능 비교는 동일한 네트워크에서 10만, 50만, 100만, 300만 4가지 상황에서 진행하였습니다. ChunkSize, PageSize, FetchSize는 모두 1,000개, Read하는 컬럼 개수는 30개로 통일하였습니다.

![reader performance test](https://tech.kakaopay.com/_astro/performance_result.BSuITFhG_BhXsH.webp)

reader performance test

### 결과 분석

#### 10만 개 -> 50만 개

50만 개는 10만 개와 비교하여 데이터 건수는 5배로 늘었지만 ItemReader별 read시간 차이는 더욱 벌어졌습니다.

- JpaPagingItemReader: 18초 -> 235초(약 4분) **13배 증가**
- QueryDslZeroOffsetItemReader: 9초 -> 47초 **5배 증가**
- ExposedCursorItemReader: 11초 -> 50초 **5배 증가**

#### 100만 개 -> 300만 개

위의 상황과 마찬가지로 300만 개는 100만 개와 비교하여 데이터 건수는 3배로 늘었지만 ItemReader별 read시간 차이는 더욱 벌어졌습니다.

- JpaPagingItemReader: 842초(약 14분) -> 6752초(약 112분) **8배 증가**
- QueryDslZeroOffsetItemReader: 82초(약 1분 20초), 266초(약 4분 26초) **3배 증가**
- ExposedCursorItemReader: 96초(약 1분 36초), 290초(약 4분 50초) **3배 증가**

#### 성능 결론

ZeroOffsetItemReader와 ExposedCursorItemReader는 JpaPagingItemReader보다 절대적인 속도도 훨씬 빠릅니다. 또한 데이터 건수에 비례하여 선형적으로 Read시간이 증가합니다. 새로 구현한 2개의 ItemReader가 수백만, 수천만 개 이상의 대량처리에 더 적합합니다.

## 안정성 측정

새로 구현한 2개의 ItemReader의 300만 개 Heap Space 모니터링 결과입니다.

![reader heap space monitoring results](https://tech.kakaopay.com/_astro/heap_result.wpnRuzQj_ZlFSRg.webp)

reader heap space monitoring results

### 안정성 결론

매우 안정적인 모습의 GC가 발생하며 대량 처리에도 전혀 문제 없습니다.

## 최종 결론

### 총정리

| 구분 | RepositoryItemReader JpaPagingItemReader | JdbcCursorItemReader HibernateCursorItemReader | JpaCursorItemReader | (QueryDsl)ZeroOffsetItemReader | ExposedCursorItemReader |
| --- | --- | --- | --- | --- | --- |
| 쿼리구현방식 | Query Method, QueryDSL, JPQL | Native Query, HQL | JPQL | QueryDSL | Kotlin Exposed |
| 동작 방식 | Pagination Limit Offset 구문 사용 | Cursor 방식 | 애플리케이션에서 직접 Cursor 처리 | Offset을 항상 0으로 유지 PK를 where 조건에 추가하는 방식 | JdbcCursorItemReader와 동일한 방식 |
| 성능 | 조회할 데이터가 많다면 뒷 Page로 갈수록 느려짐 | Cursor 기반으로 Fetch size와 DB설정만 제대로 세팅하면 조회 속도가 매우 빠름 | 성능은 매우 우수하나 OOM 유발 가능 | 첫 Page를 읽었을 때와 동일하게 항상 일관된 조회 성능을 가짐 | Cursor 기반으로 많은 양의 데이터를 빠르게 가져오며 일관된 조회 성능을 가짐 |

#### 대량 처리 시 사용해도 좋은 ItemReader

- ZeroOffsetItemReader (직접 구현)
- ExposedCursorItemReader (직접 구현)
- JdbcCursorItemReader (Spring Batch에서 기본 제공)
- HibernateCursorItemReader (Spring Batch에서 기본 제공)

#### 대량 처리 시 사용하면 안 되는 ItemReader

- RepositoryItemReader (Spring Batch에서 기본 제공)
- JpaPagingItemReader (Spring Batch에서 기본 제공)
- JpaCursorItemReader (Spring Batch에서 기본 제공)

## 마치며

카카오페이 정산팀에서는 그동안 많은 배치 구현 경험을 통해 가장 이상적인 ItemReader로써 ZeroOffsetItemReader와 ExposedCursorItemReader를 개발해 사용하고 있습니다. 개선된 ItemReader를 사용하면서 수년 전에는 상상할 수 없었던 만큼의 데이터를 처리하고 있습니다.

또한, 저희 팀에서는 데이터를 읽는 것뿐만 아니라 대량의 데이터를 어떻게 가공하고(Processor) 합치고(Aggregation) 쓸지(Write) 고민해왔습니다. 다음 편에서는 이런 노하우들 중에 최선의 Aggregation 방법을 소개하고자 합니다.
