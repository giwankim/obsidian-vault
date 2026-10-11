---
title: "이제 Redis를 멈춰보겠습니다: @CacheEvict 파헤치기 | 우아한형제들 기술블로그 |"
source: "https://techblog.woowahan.com/23138/"
author:
published: 2025-11-04
created: 2026-10-11
description: "@CacheEvict의 allEntries=true 사용 시 Keys가 호출된다. 이는 금지 명령어로 실패하거나 서비스 지연(Block)으로 이어진다. Bean 재정의로 Scan 변경 방법과 실무에서 allEntries를 피해야 하는 이유에 대해서 살펴본다."
tags:
  - "clippings"
---

> [!summary]
> Tracing Spring's cache code shows that `@CacheEvict(allEntries = true)` ends in `RedisCache.clear()`, which Spring Data Redis runs with `BatchStrategies.keys()` by default: a blocking O(N) `KEYS` + `DEL` on single-threaded Redis, or a `RedisCommandExecutionException` where `KEYS` is disabled. Switching to `BatchStrategies.scan()` through a `RedisCacheManagerBuilderCustomizer` avoids `KEYS`, but a full `SCAN` over a large cache still hit the API timeout, and a locking cache writer blocks regardless. The advice is to avoid `allEntries` in production, keep bulk deletion in separate SCAN-based admin or batch jobs, and prefer `UNLINK` over `DEL`.

## 이제 Redis를 멈춰보겠습니다: @CacheEvict 파헤치기

2025\. 11. 04. 신익수 ![](https://www.gravatar.com/avatar/https://gravatar.com/tigerso7658c718df)

[Backend](https://techblog.woowahan.com/?pcat=backend)

### 0\. 프로젝트 환경

---

- Spring Boot 3.3.7
- Spring Data Redis 3.3.7
- Lettuce 6.3.2

ㅤ

### 1\. 개요

---

운영 환경에서 캐시를 다루다 보면 한 번쯤은 @CacheEvict(allEntries = true) 설정을 써볼까 고민하게 됩니다.

테스트에서 잘 동작하던 코드가, 서비스에서는 지연이나 장애로 이어지는 경우가 간혹 발생합니다.

그 이유는 설정 때문만은 아니라, Spring의 캐시 추상화 방식과 Redis의 동작 구조가 맞물리면서 생기는 특성 때문입니다.

본 글에서는 Spring의 @CacheEvict 어노테이션이 내부적으로 어떤 과정을 거쳐 동작하는지를 코드 레벨에서 살펴보고,

allEntries = true 설정이 실제 운영 환경에서 왜 위험한지, 그리고 실무에서는 어떻게 안전하게 대응할 수 있는지를 정리했습니다.

이 글은 Spring Boot 기반에서 캐시를 다뤄본 경험이 있는 중급 이상 백엔드 개발자를 대상으로 합니다.

Spring의 캐시 구조나 Redis 키 관리 방식을 어느 정도 알고 있다면 이해하기 어렵지 않을 것입니다.ㅤ

ㅤ

### 2\. Spring 의 Cache Annotation

---

우아한형제들에서는 주로 Cache 용도로 Redis를 사용하며 Spring Data Redis의 클라이언트로 Lettuce를 사용합니다.

이때 Spring이 제공하는 주요 어노테이션이 있는데, 아래와 같습니다.

- @Cacheable: 메서드 결과를 캐시에 저장하고, 다음 호출 시 캐시에서 반환
- @CacheEvict: 특정 조건에 맞으면 캐시 데이터를 삭제
- @CachePut: 강제 갱신 메서드를 실행하고, 결과를 캐시에 갱신

@Cache 계열 어노테이션들은 모두 **키(key)** 를 기반으로 캐시를 조회·저장·삭제하는 구조입니다.

즉, 메서드 파라미터나 표현식(SpEL)을 이용해 Redis의 캐시 키를 결정하고, 그 키를 통해 캐시를 제어합니다.

이때 @CacheEvict는 키를 제거할 때 사용되는데, 내부적으로 어떻게 동작하는지 살펴보겠습니다.

ㅤ

### 3\. @CacheEvict의 메커니즘

---

**CacheEvict.java**

```java
@Target({ElementType.TYPE, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Inherited
@Documented
public @interface CacheEvict {
    @AliasFor("cacheNames")
    String[] value() default {};

    @AliasFor("value")
    String[] cacheNames() default {};

    String key() default "";

    String keyGenerator() default "";

    String cacheManager() default "";

    String cacheResolver() default "";

    String condition() default "";

    boolean allEntries() default false;

    boolean beforeInvocation() default false;
}
```

Spring에서 사용하는 **@CacheEvict** 어노테이션입니다.

아래와 같이 cacheNames와 key에 값을 넣어 하나의 key를 해제하는 데 사용합니다.

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/CacheEvict_%EC%98%88%EC%8B%9C_01-e1761020265482.png))

이때, **22 Line에 allEntries 필드** 가 있는 것을 알 수 있습니다.

@CacheEvict로 작성된 정보는 아래의 parseCacheAnnotations() 메서드 16 Line의 **parseEvictAnnotation()** 호출을 통하여 **CacheEvictOperation** 객체로 만들어집니다.

ㅤ

**SpringCacheAnnotationParser.java**

```java
@Nullable
private Collection<CacheOperation> parseCacheAnnotations(
        SpringCacheAnnotationParser.DefaultCacheConfig cachingConfig, AnnotatedElement ae, boolean localOnly) {

    Collection<? extends Annotation> anns = (localOnly ?
            AnnotatedElementUtils.getAllMergedAnnotations(ae, CACHE_OPERATION_ANNOTATIONS) :
            AnnotatedElementUtils.findAllMergedAnnotations(ae, CACHE_OPERATION_ANNOTATIONS));
    if (anns.isEmpty()) {
        return null;
    }

    final Collection<CacheOperation> ops = new ArrayList<>(1);
    anns.stream().filter(ann -> ann instanceof Cacheable).forEach(
            ann -> ops.add(parseCacheableAnnotation(ae, cachingConfig, (Cacheable) ann)));
    anns.stream().filter(ann -> ann instanceof CacheEvict).forEach(
            ann -> ops.add(parseEvictAnnotation(ae, cachingConfig, (CacheEvict) ann)));
    anns.stream().filter(ann -> ann instanceof CachePut).forEach(
            ann -> ops.add(parsePutAnnotation(ae, cachingConfig, (CachePut) ann)));
    anns.stream().filter(ann -> ann instanceof Caching).forEach(
            ann -> parseCachingAnnotation(ae, cachingConfig, (Caching) ann, ops));
    return ops;
}
```

**SpringCacheAnnotationParser.java(계속)**

```java
private CacheEvictOperation parseEvictAnnotation(
        AnnotatedElement ae, SpringCacheAnnotationParser.DefaultCacheConfig defaultConfig, CacheEvict cacheEvict) {

    CacheEvictOperation.Builder builder = new CacheEvictOperation.Builder();

    builder.setName(ae.toString());
    builder.setCacheNames(cacheEvict.cacheNames());
    builder.setCondition(cacheEvict.condition());
    builder.setKey(cacheEvict.key());
    builder.setKeyGenerator(cacheEvict.keyGenerator());
    builder.setCacheManager(cacheEvict.cacheManager());
    builder.setCacheResolver(cacheEvict.cacheResolver());
    builder.setCacheWide(cacheEvict.allEntries());
    builder.setBeforeInvocation(cacheEvict.beforeInvocation());

    defaultConfig.applyDefault(builder);
    CacheEvictOperation op = builder.build();
    validateCacheOperation(ae, op);

    return op;
}
```

이때 위의 parseEvictAnnotation()의 13 Line에서 **allEntries가 cacheWide로 변환** 됩니다.

위 메서드로 **CacheEvictOperation** 이 반환됩니다.

ㅤ

**CacheAspectSupport.java**

```java
private void performCacheEvicts(List<CacheOperationContext> contexts, @Nullable Object result) {
    for(CacheOperationContext context : contexts) {
        CacheEvictOperation operation = (CacheEvictOperation)context.metadata.operation;
        if (this.isConditionPassing(context, result)) {
            Object key = context.getGeneratedKey();

            for(Cache cache : context.getCaches()) {
                if (operation.isCacheWide()) {
                    this.logInvalidating(context, operation, (Object)null);
                    this.doClear(cache, operation.isBeforeInvocation());
                } else {
                    if (key == null) {
                        key = this.generateKey(context, result);
                    }

                    this.logInvalidating(context, operation, key);
                    this.doEvict(cache, key, operation.isBeforeInvocation());
                }
            }
        }
    }
}
```

CacheEvictOperation 객체는 CacheInterceptor의 부모인 CacheAspectSupport 내 performCacheEvicts()에서 사용되고 결과적으로 **cacheWide로 분기되어 doClear() 또는 doEvict()를 호출** 하여 처리하게 됩니다.

ㅤ
ㅤ

### 4\. allEntries = true일 경우

---

위 CacheEvict 메커니즘에서 **allEntries가 cacheWide로 변환** 되어 분기문에 사용되었습니다.

**cacheWide = false** 일 때는 doEvict()가 호출되어 특정 키로 del 명령어가 수행됩니다.

그렇다면 **cacheWide = true** 로서 doClear()가 호출 되면 어떤 일이 벌어질까요?

코드를 살펴보겠습니다.

ㅤ

**AbstractCacheInvoker.java**

```java
protected void doClear(Cache cache, boolean immediate) {
    try {
        if (immediate) {
            cache.invalidate();
        } else {
            cache.clear();
        }
    } catch (RuntimeException ex) {
        getErrorHandler().handleCacheClearError(ex, cache);
    }
}
```

immediate로 분기되지만 내부적으로는 결국 **cache.clear()** 를 호출합니다.

그리고 이때의 Cache는 인터페이스로서 내부 로직을 보려면 구현체를 찾아야 합니다.

spring-framework에서는 Cache의 구현체로 AbstractValueAdaptingCache를 제공하는데

Spring Data Redis에서는 그것을 상속받은 **RedisCache.java** 가 등장합니다.

ㅤ

**RedisCache.java**

```java
public class RedisCache extends AbstractValueAdaptingCache {
    ...
    @Override
    public void clear() {

        byte[] pattern = conversionService.convert(createCacheKey("*"), byte[].class);
        cacheWriter.clean(name, pattern);

    }
    ...
}
```

pattern으로 `"*"` 인 와일드카드를 반환하고 cacheWriter.clean(name, pattern)에 넘겨주고 있습니다.
(이때, createCacheKey(Object)에서 Cache.getName() 과 `"*"` 을 결합한 pattern을 사용합니다.)

이때 호출된 CacheWriter는 인터페이스인 DefaultCacheWriter로서 구현체를 봐야 합니다.

Spring Data Redis에서는 **DefaultRedisCacheWriter.java** 입니다.

ㅤ

**DefaultRedisCacheWriter.java**

```java
class DefaultRedisCacheWriter implements RedisCacheWriter {
    ...
    @Override
    public void clean(String name, byte[] pattern) {

        Assert.notNull(name, "Name must not be null!");
        Assert.notNull(pattern, "Pattern must not be null!");

        execute(name, connection -> {

            boolean wasLocked = false;

            try {

                if (isLockingCacheWriter()) {
                    doLock(name, connection);
                    wasLocked = true;
                }

                long deleteCount = batchStrategy.cleanCache(connection, name, pattern);
                while (deleteCount > Integer.MAX_VALUE) {
                    statistics.incDeletesBy(name, Integer.MAX_VALUE);
                    deleteCount -= Integer.MAX_VALUE;
                }
                statistics.incDeletesBy(name, (int) deleteCount);

            } finally {

                if (wasLocked && isLockingCacheWriter()) {
                    doUnlock(name, connection);
                }
            }

            return "OK";
        });
    }
    ...
}
```

20 Line에서 batchStrategy.cleanCache()를 호출하는데 batchStrategy도 인터페이스입니다.

구현체는 두 가지인데 **Keys와 Scan** 입니다.(Redis를 사용하시는 분들은 Keys를 보고 흠칫하셨을 지도 모르겠습니다.)

ㅤ

**BatchStrategies.java**

```java
static class Keys implements BatchStrategy {

    static BatchStrategies.Keys INSTANCE = new BatchStrategies.Keys();

    @Override
    public long cleanCache(RedisConnection connection, String name, byte[] pattern) {

        byte[][] keys = Optional.ofNullable(connection.keys(pattern)).orElse(Collections.emptySet())
                .toArray(new byte[0][]);

        if (keys.length > 0) {
            connection.del(keys);
        }

        return keys.length;
    }
}
```

Keys의 cleanCache()는 전달받은 패턴을 KEYS 명령을 통해 모두 조회하고 DEL 명령으로 삭제합니다.

이때의 **KEYS는 선형적으로 전체 키 집합을 스캔하는 O(N)으로서 비용이 매우 많이 드는 연산** 이기 때문에 실무에서 사용되면 싱글 스레드로 동작하는 Redis의 다른 요청들은 Block되어 지연이 발생 합니다.

호출되면 위험한 명령어가 @CacheEvict로 인해 오픈되어 있는 것입니다.

> - DEL은 키가 많을 경우 메모리 해제 작업이 오래 걸려 이벤트 루프를 점유하게 되며, 이 때문에 다른 요청 처리가 지연될 수 있어 위험한 명령어 중 하나입니다. 따라서 background에서 메모리 해제가 일어나는 **UNLINK** 를 사용하는 것이 좋습니다.
> - DEL을 호출하더라도 내부적으로 UNLINK로 동작하도록 세팅해두는 방법도 있습니다.
> 	- 참고 링크: [lazyfree-lazy-user-del](https://redisgate.kr/redis/configuration/param_lazyfree.php "lazyfree-lazy-user-del")
> - Valkey8.0부터는 DEL 명령어 호출 시 UNLINK처럼 동작하는 것이 Default가 되었습니다.
> 	- 참고 링크: [valkey8.0 LAZY FREEING](https://raw.githubusercontent.com/valkey-io/valkey/8.0/valkey.conf#:~:text=%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%20LAZY%20FREEING%20%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23%23)

ㅤ

이제 Scan 구현체를 보겠습니다.

**BatchStrategies.java**

```java
static class Scan implements BatchStrategy {

    private final int batchSize;

    Scan(int batchSize) {
        this.batchSize = batchSize;
    }

    @Override
    public long cleanCache(RedisConnection connection, String name, byte[] pattern) {

        Cursor<byte[]> cursor = connection.scan(ScanOptions.scanOptions().count(batchSize).match(pattern).build());

        long count = 0;

        BatchStrategies.PartitionIterator<byte[]> partitions = new BatchStrategies.PartitionIterator<>(cursor, batchSize);
        while (partitions.hasNext()) {

            List<byte[]> keys = partitions.next();
            count += keys.size();

            if (keys.size() > 0) {
                connection.del(keys.toArray(new byte[0][]));
            }
        }

        return count;
    }
}
```

SCAN은 저희가 알고 있는 Redis SCAN과 동일하게 cursor 기반으로 탐색하여 제거하고 이를 반복하여 수행합니다.

→ 이 위험한 KEYS 대신 SCAN이 기본 설정으로 되어있을 것으로 생각될 수 있지만 **Spring Boot에서 자동 생성 기본값은 KEYS** 입니다.

#### KEYS가 왜 기본값일까요? 그 이유는 아래의 공식 문서 내용에서 알 수 있습니다.

```
The KEYS batch strategy is fully supported using any driver and Redis operation mode (Standalone, Clustered). SCAN is fully supported when using the Lettuce driver. Jedis supports SCAN only in non-clustered modes.

- KEYS 전략은 모든 드라이버와 Redis 운영 모드(Standalone, Clustered)에서 완전히 지원됩니다. SCAN은 Lettuce 드라이버를 사용할 때 완전히 지원됩니다. Jedis는 비 클러스터 모드에서만 SCAN을 지원합니다.
- 참고링크
```

ㅤ
**RedisCacheWriter.java**

```java
public interface RedisCacheWriter extends CacheStatisticsProvider {

    static RedisCacheWriter nonLockingRedisCacheWriter(RedisConnectionFactory connectionFactory) {
        return nonLockingRedisCacheWriter(connectionFactory, BatchStrategies.keys());
    }
```

위에서 batchStrategy.cleanCache()를 호출하는 DefaultRedisCacheWriter의 인터페이스를 들어가 보면 위 코드 4번째 줄에 기본값으로 **BatchStrategies.keys()** 를 주입하는 것을 알 수 있습니다.

ㅤ

ㅤ

### 5\. Spring Boot 자동설정 기본값 예시

---

**RedisCacheConfiguration.java**

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/RedisCacheConfiguration_%EB%A1%9C%EC%A7%81_01-750x449.png))

RedisCacheManagerBuilder 부분입니다.

Spring Data Redis의 기본 RedisCacheManagerBuilder를 사용하고 있습니다.

ㅤ
**RedisCacheManager.java**

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/%EC%BB%A4%EB%A8%B8%EC%8A%A4_%EC%84%9C%EB%B9%84%EC%8A%A4_%EC%86%8C%EC%8A%A4_03-750x139.png))

이는 RedisCacheWriter의 nonLockingRedisCacheWriter를 사용하고 있습니다.

ㅤ
**RedisCacheWriter.java**

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/%EC%BB%A4%EB%A8%B8%EC%8A%A4_%EC%84%9C%EB%B9%84%EC%8A%A4_%EC%86%8C%EC%8A%A4_04-750x193.png))

allEntries의 수행 명령어로 keys를 default로 가져가게 됩니다.

ㅤ
**BatchStrategies.java**

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/%EC%BB%A4%EB%A8%B8%EC%8A%A4_%EC%84%9C%EB%B9%84%EC%8A%A4_%EC%86%8C%EC%8A%A4_05-750x362.png))

최종적으로 keys가 호출되는 것을 알 수 있습니다.

ㅤ

ㅤ

### 6\. Scan 변경 예시

---

아래는 자체적으로 RedisCacheManager의 Bean을 재정의하는 코드입니다.

ㅤ

**RedisConfig.java(예시)**

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/RedisCacheManagerBuilderCustomizer_%EA%B5%AC%ED%98%84%EB%B6%80_01-750x238.png))

Config 클래스에 **@EnableCaching** 을 추가하고 RedisCacheManagerBuilderCustomizer Bean을 재정의하며 BatchStrategies를 Scan으로 선언합니다.

ㅤ

**DefaultRedisCacheWriter.java**

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/DefaultRedisCacheWriter_%EA%B5%AC%ED%98%84%EB%B6%80_01-750x741.png))

기본적으로 batchStrategy.cleanCache()를 호출하고 내부적으로 파티셔닝하여 제거하고 있습니다.
이때 cleanCache 호출 전후로 doLock() / doUnlock()이 호출되는 것에 유의해야 합니다.

> BatchStrategies가 배치형 비차단 반복 명령인 Scan이더라도
> nonLockingRedisCacheWriter가 아닌 lockingRedisCacheWriter를 사용하면 execute가 수행될 때 Block 되게 됩니다.
> **그렇기 때문에 캐시량이 많을 때는 @CacheEvict에서 allEntries=true 설정을 하지 않도록 주의해야 합니다.**
>
> ![](https://techblog.woowahan.com/wp-content/uploads/2025/10/DefaultRedisCacheWriter_%EA%B5%AC%ED%98%84%EB%B6%80_02-750x193.png))

ㅤ

ㅤ

#### Scan 실행 예시

![소스코드 상 서비스 단에 걸려있는 Cache Evict라는 어노테이션](https://techblog.woowahan.com/wp-content/uploads/2025/09/%EC%BB%A4%EB%A8%B8%EC%8A%A4_%EC%84%9C%EB%B9%84%EC%8A%A4_%EC%86%8C%EC%8A%A4_01-750x93.png)

Bean을 Scan으로 재정의하고 API에 @CacheEvict **(allEntries=true)** 를 걸었을 경우

ㅤ

![Redis scan 수행량이 무수히 많은 상태 이미지](https://techblog.woowahan.com/wp-content/uploads/2025/09/%EC%BB%A4%EB%A8%B8%EC%8A%A4_%EC%84%9C%EB%B9%84%EC%8A%A4_%EB%AA%A8%EB%8B%88%ED%84%B0%EB%A7%81_02-750x475.png)

Pinpoint로 분석했을 때 Scan 명령어가 호출됩니다.

ㅤ

! [![서버 에러가 발생했습니다. timeout of 600000ms exceeded.](https://techblog.woowahan.com/wp-content/uploads/2025/09/%EC%BB%A4%EB%A8%B8%EC%8A%A4_%EC%84%9C%EB%B9%84%EC%8A%A4_%EC%96%B4%EB%93%9C%EB%AF%BC_01-750x154.png)

그러나 캐시량이 많아 최종적으로 서버 API 타임아웃(60초)이 발생했습니다.

ㅤ

ㅤ

### 7\. 실무 관점의 인사이트

---

**지금까지의 내용을 기반으로, 실무 적용 시 주의사항은 다음과 같습니다.**

- 실 서비스에서는 인프라 단에서 Redis의 고위험 명령어를 막아두고 운영할 가능성이 높습니다.(우아한형제들 또한 그렇습니다)
- 기본 값인 KEYS 명령어를 Redis에서 막아두어 수행되지 못하면 **RedisCommandExecutionException** 이 발생하므로 유의해야 합니다.
- RedisCacheManager Bean 재정의 시 Keys가 주입되지 못하도록 Scan으로 선언해야 합니다.
- SCAN이 KEYS 보다 덜 위험하긴 하지만, 여전히 전체 키 탐색이므로 데이터가 많으면 **API 타임아웃·Redis CPU** 증가할 수 있습니다.
- **따라서 실무에서 allEntries = true를 사용하지 않는 것이 좋습니다.**
- 전체 키 제거가 필요할 경우 **BatchStrategy.Scan으로 수행되는 별도 로직** 으로 구현해야 합니다.

ㅤ

**그렇다면 allEntries 속성은 왜 있는 것일까요?**

> #### allEntries 속성 값에 따른 동작
>
> - **allEntries = true**
> 	1. KEYS/SCAN + DEL 명령어로 캐시 전체를 제거합니다. // O(N)
> 		2. 아래 상황들처럼 캐시 전체의 일관성이 깨졌을 때 사용합니다.
> 		a. 데이터가 한꺼번에 대량 변경될 때
> 		b. 캐시 키 규칙이 바뀌었을 때(ex. key prefix 변경)
> 		c. 테스트나 장애 대응 때(ex. 전체 삭제로 복구하는 경우)
> 		3. **운영 중에는 거의 쓰지 않고, 보통 관리 endpoint나 배치성 작업에서 사용됩니다.**
> - **allEntries = false(default)**
> 	1. DEL 명령어로 특정 키만 제거합니다. // O(1)
> 		2. 정확한 key 기반 단일 건만 수행합니다.
> 		3. 별도의 추가적인 탐색은 일어나지 않습니다.

ㅤ

#### \[Tip\] KEYS 명령어 금지하기

```shell
# Redis 설정 파일 열기 (Homebrew 설치 기준)
> vi /opt/homebrew/etc/redis.conf
또는
> vi /usr/local/etc/redis.conf

# 아래 내용 추가 (고위험 명령 숨김 예시)
# "" 대신 유추가 어려운 임의의 텍스트로 변경하여도 됩니다.
> rename-command KEYS ""

# Redis 재시작
brew services restart redis

# 정상 적용 확인
> redis-cli
127.0.0.1:6379> KEYS *
(error) ERR unknown command \`KEYS\`, with args beginning with: '*',
```

#### Keys 명령어를 금지한 후 호출한 결과

![](https://techblog.woowahan.com/wp-content/uploads/2025/10/%EC%BB%A4%EB%A8%B8%EC%8A%A4_%EB%A0%88%EB%94%94%EC%8A%A4_%EA%B8%88%EC%A7%80%EB%AA%85%EB%A0%B9%EC%96%B4_key%EC%88%98%ED%96%89_01-750x207.png))

ㅤ

ㅤ

### 8\. 마무리

---

Spring의 편리한 기능들은 로컬에서 테스트할 때는 이상적으로 동작할 수 있습니다.
그러나 운영환경에 떠있는 싱글 스레드 기반의 Redis를 조작할 때는 아주 조심스러워야 합니다.
의심 가는 부분이 있을 때는 구현체의 끝까지 파고들어가는 몰입을 즐겨보는 것을 추천합니다.

ㅤ
ㅤ

##### 참고 문헌

- [Spring Data Redis / Redis Cache](https://docs.spring.io/spring-data/redis/reference/redis/redis-cache.html "spring-data-redis/Redis Cache")
