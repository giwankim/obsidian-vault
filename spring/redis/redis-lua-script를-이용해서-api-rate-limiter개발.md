---
title: "Redis Lua Script를 이용해서 API Rate Limiter개발"
source: "https://dev.gmarket.com/69"
author:
  - "[[G마켓 기술블로그]]"
published: 2023-03-16
created: 2026-11-11
description: "안녕하세요. Item Engineering 팀 박상윤입니다. 이번 글에서는 상품 엑셀 등록 서비스 개발하고 컨슈머에서 사용할 API Rate Limiter 개발하면서 발생한 이슈를 정리한 글입니다. 이 글은 아래와 같이 구성되어 있습니다. API Rate Limiter 도입 필요성 API Rate Limiter 적용 API Rate Limiter 동시성 문제 Lua script 실행시켜서 atomic 연산을 보장하도록 개선 정리 1. API Rate Limiter 도입 필요성 상품 엑셀 등록 서비스는 상품 정보를 엑셀에 입력하여 최대 500개의 상품을 동시에 등록할 수 있는 서비스입니다. 상품 엑셀 등록 서비스는 엑셀을 파싱 해서 상품등록 모델로 생성시켜 주는 프로듀서와 등록 모델을 수신해서 상품 등록 .."
tags:
  - "clippings"
---

> [!summary]
> Gmarket's Item Engineering team built a per-seller rate limiter (100 product-registration calls per minute) for a 16-consumer Excel bulk-upload service, using a custom `@LimitRequestPerTime` annotation, a Spring AOP `@Around` aspect and a `RedisTemplate`-based `RateLimiter`. The first get-then-increment version let calls past the limit because concurrent consumers read the same count, and `WATCH`/`MULTI` was not an option since the service ran on Redis Cluster and `get` returns null inside a transaction. The fix is a short Lua script run via `DefaultRedisScript` that checks, `INCRBY`s and `EXPIRE`s atomically on the server, with the caveat that scripts must stay brief because they block Redis's single thread.

## 티스토리 뷰

**[Backend](https://dev.gmarket.com/category/Backend)**

### Redis Lua Script를 이용해서 API Rate Limiter개발

2023\. 3. 16. 09:04

안녕하세요. Item Engineering 팀 박상윤입니다.

이번 글에서는 상품 엑셀 등록 서비스 개발하고 컨슈머에서 사용할 API Rate Limiter 개발하면서 발생한 이슈를 정리한 글입니다. 이 글은 아래와 같이 구성되어 있습니다.

1. API Rate Limiter 도입 필요성
2. API Rate Limiter 적용
3. API Rate Limiter 동시성 문제
4. Lua script 실행시켜서 atomic 연산을 보장하도록 개선
5. 정리

## 1\. API Rate Limiter 도입 필요성

상품 엑셀 등록 서비스는 상품 정보를 엑셀에 입력하여 최대 500개의 상품을 동시에 등록할 수 있는 서비스입니다. 상품 엑셀 등록 서비스는 엑셀을 파싱 해서 상품등록 모델로 생성시켜 주는 `프로듀서` 와 등록 모델을 수신해서 `상품 등록 API` 를 호출하는 `컨슈머` 로 구성되어 있습니다. 이때 상품등록 API에서는 최근 등록일을 기준으로 1분당 최대 100회의 상품등록이 가능하도록 설계되어 있습니다. 즉, 판매자가 상품을 최대 500개까지 한 번에 등록시킬 수 있는 서비스를 개발했지만, 상품등록 API에 존재하는 비즈니스 로직 때문에 1분당 100회 이상 상품을 등록하려고 하면 상품등록에 실패하는 상황이 발생합니다.

"일반셀러는 1분당 100건의 상품만 등록할 수 있고 상품 엑셀 등록 서비스로는 최대 500개까지 상품을 한 번에 등록시킬 수 있다"라는 요구사항을 만족시키기 위해서는 결국 컨슈머에서 자체적으로 셀러별 API 호출 수를 기록하고 100회에 도달했을 때는 상품등록 API를 호출하지 않고 잠시 대기해야 합니다.

![](https://blog.kakaocdn.net/dna/RStOK/btr35wuzeo0/AAAAAAAAAAAAAAAAAAAAAH_xjzIpe4wSilBNXiR6bQloi9s5sNkod7xUA5L59kiJ/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1796050799&allow_ip=&allow_referer=&signature=KAtIwr6BTAP7u65UFrVsgdHIvfY%3D)

## 2\. API Rate Limiter 적용

"1분당 100건의 상품만 등록할 수 있고 상품 엑셀 등록 서비스로는 최대 500개까지 상품을 한 번에 등록시킬 수 있다"라는 요구사항을 처리하기 위해서 Redis를 이용해서 API 호출 수를 기록하고 API 호출 수가 100 미만일 경우에만 상품 등록 API를 호출하도록 해야 합니다.

![](https://blog.kakaocdn.net/dna/rP18y/btr32udz5nU/AAAAAAAAAAAAAAAAAAAAAJUEghqbDQkvyoLU8UTJZ7_wAAB2TMCPhS7xDn4lfWJ0/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1796050799&allow_ip=&allow_referer=&signature=ykehvdhdbl%2BaEz%2BO1MC4nR9qT78%3D)

API Rate Limiter에 필요한 메타데이터를 관리하기 위해서 커스텀 어노테이션을 활용했습니다. 해당 커스텀 어노테이션으로 시간 단위, 시간, 레디스에 저장할 unique key prefix, 몇 회로 제한할지를 아래와 같이 정의했습니다.

```cs
@Target({ElementType.TYPE, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
public @interface LimitRequestPerTime {

  /**
   * 분당호출 제한시킬 unique key prefix
   */
  String prefix() default "";

  /**
   * 호출 제한 시간
   */
  int ttl() default 1;

  /**
   * 호출 제한 시간 단위
   */
  TimeUnit ttlTimeUnit();

  /**
   * 분당 호출제한 카운트
   */
  int count();

}
```

위에서 작성한 커스텀 어노테이션을 사용할 때는 아래와 같이 API를 호출하는 메서드 위에 비즈니스별로 설정하려는 값을 작성하는 형태로 사용할 수 있습니다. 아래 예시코드는 1분당 100회 호출 제한을 가지도록 커스텀 어노테이션을 정의했습니다.

```typescript
@LimitRequestPerTime(
    prefix="prefix:",
    ttl=1,
    ttlTimeUnit = TimeUnit.MINUTES,
    count=100
)
public void saveItem(SaveItemRequest saveItemRequest) {
  //여기서 실제 상품 등록 api 호출 (나머지 코드 생략...)
}
```

API Rate Limiter에 필요한 메타데이터를 커스텀 어노테이션으로 정의하였습니다. 이제 이 커스텀 어노테이션 `@LimitRequestPerTime` 을 활용해서 분당호출 수 제한을 걸어주는 로직을 작성해 보겠습니다.

API Rate Limiter를 구현하는 방법은 다양하기 때문에, 코드 레벨에서의 확장성을 높이기 위해 인터페이스를 활용하여 구현하였습니다. `tryApiCall` 메서드 인자에 대한 설명은 코드에 주석으로 작성했습니다.

```java
/**
 * API Rate Limiter 인터페이스
   key : prefix 붙일 실제 unique key
   limetRequestPerTime : API Rate Limiter에 필요한 메타데이터
   proceedingJoinPoint : AOP에서 타겟으로 설정한 메서드 정보
 */
public interface RateLimiter {
  void tryApiCall(String key, LimitRequestPerTime limitRequestPerTime, ProceedingJoinPoint joinPoint) throws Throwable;
}
```

아래 코드는 RateLimiter라는 인터페이스를 구현한 구체클래스인 RedisRateLimiter 클래스입니다. 해당 클래스는 RedisTemplate을 주입받아서 API호출이 가능한지 체크하고 가능하다면 API를 호출하는 로직이 작성되어 있습니다.

```java
/**
 * API Rate Limiter 구현클래스
 */
@Component("RedisRateLimiter")
@Slf4j
@RequiredArgsConstructor
public class RedisRateLimiter implements RateLimiter{

 private final RedisTemplate<String, Serializable> redisTemplate;

  @Override
  public void tryApiCall(String key, LimitRequestPerTime limitRequestPerTime, ProceedingJoinPoint joinPoint) throws Throwable {
    //이전까지의 상품등록 API 호출 수 조회
    Long previousCount = (Long) redisTemplate.opsForValue().get(key);
    //호출 수가 설정한 값(100) 이상이면 exception
    if (previousCount != null && previousCount.intValue() > limitRequestPerTime.count()) {
      throw new RequestPerMinuteException("1분당 호출수 초과");
    }
    //호출 수가 설정한 값(100) 미만이면 분당 호출 수를 기존값 + 1해주고 API 호출
    redisTemplate.execute(new SessionCallback() {
      @Override
      public Object execute(RedisOperations operations) throws DataAccessException {
        try {
          operations.multi();
          if(previousCount == null) {
            redisTemplate.opsForValue().set(key, 0, limitRequestPerTime.ttl(), limitRequestPerTime.ttlTimeUnit());
          }
          redisTemplate.opsForValue().increment(key);
          redisTemplate.expire(key, limitRequestPerTime.ttl(), limitRequestPerTime.ttlTimeUnit());
        } catch (Exception e) {
          log.error(e.getMessage(),e);
          operations.discard();
          throw e;
        }
        return operations.exec();
      }
    });
    joinPoint.proceed();
  }
}
```

API Rate Limiter 로직은 비즈니스 핵심로직이 아닌 부가기능이라고 판단해서 AOP를 활용해서 개발했습니다. 이제 AOP에서 활용하기 위한 Aspect를 구현하겠습니다.

핵심 메서드를 호출하는 기능 (. proceed())이 포함된 ProceedingJoinPoint 객체를 활용하기 위해서 `@Around` PointCut을 활용했습니다. AOP에 대한 부가적인 설명은 지마켓 기술블로그에 작성되어 있는 다른 글을 참고해 보시면 좋을 것 같습니다.( [AOP, Swagger를 이용한 인증 로직 구현하기](https://dev.gmarket.com/59) )

- AOP: 부가기능을 분리해서 한 곳에서 관리할 수 있도록 개발하는 기법
- Aspect: 비즈니스 핵심로직과 분리시킨 부가기능 + 부가기능을 어디에 적용할지에 대한 내용
- PointCut: Aspect 객체에서 작성한 코드가 실행될 시점을 정의하는 어노테이션
```kotlin
@Component
@Aspect
@Slf4j
public class RateLimiterAspect {

  private final RateLimiter rateLimiter;

  public RateLimiterAspect(@Qualifier("RedistRateLimiter") RateLimiter rateLimiter) {
    this.rateLimiter = rateLimiter;
  }

 /*
 * 런타임 시점에 타겟으로 설정한 메서드가 실행되기 직전에 실행되는 코드입니다.
 * @Around어노테이션에는 타겟으로 설정 가능한 범위를 정의합니다. (https://www.baeldung.com/spring-aop-pointcut-tutorial) 아래 예시코드는 com.example.component패키지에 속한 모든 클래스 메서드에 적용 가능합니다.
 */
  @Around("execution(* com.example.component.*.*(..)))")
  public void interceptor(ProceedingJoinPoint joinPoint) throws Throwable {
    LimitRequestPerTime limitRequestPerTime = getLimitRequestPerTimeAnnotationFromMethod(joinPoint);
    //LimitRequestPerTime 커스텀 어노테이션이 설정되지 않은 타겟 메서드는 분당 호출 제한을 체크하지 않고 바로 실행
    if(Objects.isNull(limitRequestPerTime)) {
       joinPoint.proceed();
       return;
    }
    //LimitRequestPerTime 커스텀 어노테이션을 설정한 타겟 메서드만 분당 호출 제한을 체크
    Long uniqueKey = getUniqueKeyFromMethodParameter(joinPoint);
    rateLimiter.tryApiCall(
        composeKeyWithUniqueKey(limitRequestPerTime.prefix(),uniqueKey,"ApiCounter"),
        limitRequestPerTime,
        joinPoint
    );
  }

  /*
  * ProceedingJoinPoint로부터 메서드에 태깅되어 있는 커스텀 어노테이션을 추출하는 메서드 입니다.
  */
  private LimitRequestPerTime getLimitRequestPerTimeAnnotationFromMethod(ProceedingJoinPoint joinPoint) {
    MethodSignature signature = (MethodSignature) joinPoint.getSignature();
    Method method = signature.getMethod();
    LimitRequestPerTime limitRequestPerTime = method.getAnnotation(LimitRequestPerTime.class);
    return limitRequestPerTime;
  }

  /*
  * ProceedingJoinPoint로부터 메서드의 인자목록에서 unique key를 추출하는 메서드 입니다.
  */
  private Long getUniqueKeyFromMethodParameter(ProceedingJoinPoint joinPoint) {
    List<Object> parameters = Arrays.asList(joinPoint.getArgs());
    return (Long) parameters.get(0);
  }

  /*
  * LimitRequestPerTime 커스텀 어노테이션에 정의한 prefix와 메서드의 인자에 포함되어 있는 unique key값을 합쳐주는 메서드 입니다.
  */
  private String composeKeyWithUniqueKey(String prefix, int uniqueId,String suffix) {
    StringBuffer stringBuffer = new StringBuffer();
    return stringBuffer
        .append(prefix).append(":")
        .append(uniqueId).append(":")
        .append(suffix)
        .toString();
  }

}
```

## 3\. API Rate Limiter에서 발생하는 문제

현재 코드를 구현하고 실행시켜 보면 실제로 1분당 100건이 호출 수가 지켜지지 않고 일부 호출은 1분당 100건을 초과했지만 그대로 상품등록 API에 유입되는 것을 확인할 수 있습니다. 단일 컨슈머로 처리하는 게 아니라 16개의 컨슈머로 상품등록을 처리하기 때문에 `race condition` 이 발생하는 것입니다.

단일 컨슈머로 처리한다면 위의 코드는 아무 문제 없이 반드시 1분에 100개의 호출을 처리하지만 아래 그림처럼 4개의 컨슈머가 동시에 API 호출 수가 99인 상황에서 조회하면 4개의 컨슈머는 현재 API 호출 수가 99이므로 마지막으로 API호출이 가능하다고 판단하고 API를 호출합니다. 셀러별 API 호출 수를 조회하고 100보다 작은 값인지 확인 후 1 증가시켜 주는 로직이 atomic 하지 않아서 race condition이 발생하는 것입니다.

Redis는 싱글스레드와 이벤트루프 기반의 비동기방식으로 동작하기 때문에 한 번에 하나의 요청을 처리합니다. 하지만, 컨슈머 코드에서 처리한 API 호출수 제한 로직은 atomic 연산이 아니었습니다. 즉, 아래의 flow가 atomic이 보장되도록 처리하면 이런 문제는 발생하지 않지만 1번 과정에서 동시에 여러 컨슈머가 같은 값을 읽어가서 발생하는 문제입니다.

```
1. 현재 셀러의 API 호출 수를 get 해온다. (4개의 컨슈머가 1번에 동시에 접근한다면 모두가 99라는 값을 읽어가는 문제 발생)
2. API 호출수가 max값보다 작으면 API 호출 수를 1 증가시킨다
3. TTL을 설정한다.
```
![](https://blog.kakaocdn.net/dna/bJNc7E/btr4aL5lVWY/AAAAAAAAAAAAAAAAAAAAAPH_4N_q1Z6I60hptUgjBZGy77L7Wb588HLx5dOnDfGi/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1796050799&allow_ip=&allow_referer=&signature=tw%2BdRlL3Y2Nps3e4QuT%2B8lC5%2B%2Bg%3D)

Redis `Watch` 명령어로 Optimistic Locking을 걸고 Redis 트랜잭션을 활용해서 race condition을 해결할 수 있지만 제약조건이 있습니다. 상품 엑셀 등록 서비스에서는 Redis 클러스터를 사용하고 있었기 때문에 WATCH와 트랜잭션을 사용하지 못합니다. 따라서 다른 방법으로 race condition을 해결해야 합니다.

#### Redis 트랜잭션 제약조건

1. Redis Cluster 환경에서는 트랜잭션을 지원하지 않습니다. Redis 클러스터 환경에서 아래 코드를 실행시키면 `org.springframework.dao.InvalidDataAccessApiUsageException: WATCH is currently not supported in cluster mode.` Exception이 발생합니다
	([Is there any Redis client (Java prefered) which supports transactions on Redis cluster?](https://stackoverflow.com/questions/42088324/is-there-any-redis-client-java-prefered-which-supports-transactions-on-redis-c/42091605#42091605))
2. 트랜잭션 도중에 해당 key값에 해당하는 value를 조회하려고 하면 항상 null이 return 되므로 value값에 따라 분기처리 불가능
```java
/**
 * API Rate Limiter 구현클래스
 */
@Component("RedisRateLimiter")
@Slf4j
@RequiredArgsConstructor
public class RedisRateLimiter implements RateLimiter{

 private final RedisTemplate<String, Serializable> redisTemplate;

  @Override
  public void tryApiCall(String key, LimitRequestPerTime limitRequestPerTime, ProceedingJoinPoint joinPoint) throws Throwable {

    boolean success = redisTemplate.execute(new SessionCallback()<Boolean> {
      @Override
      public Boolean execute(RedisOperations operations) throws DataAccessException {
        try {
           //key에 Optimistic Locking을 적용
           operations.watch(key);

           //이전까지의 상품등록 API 호출 수 조회
           Long previousCount = (Long) operations.opsForValue().get(key);

          //호출 수가 설정한 값(100) 이상이면 exception
          if (previousCount != null && previousCount.intValue() > limitRequestPerTime.count()) {
            throw new RequestPerMinuteException("1분당 호출수 초과");
          }

          //트랜잭션 시작 (트랜잭션 시작 이후 get(key) 하면 항상 null return)
          operations.multi();

          //호출 수가 설정한 값(100) 미만이면 분당 호출 수를 기존값 + 1해주고 API 호출한다. rece condition발생시 해당 트랜잭션은 discard
          if(previousCount == null) {
            redisTemplate.opsForValue().set(key, 0, limitRequestPerTime.ttl(), limitRequestPerTime.ttlTimeUnit());
          }
          redisTemplate.opsForValue().increment(key);
          redisTemplate.expire(key, limitRequestPerTime.ttl(), limitRequestPerTime.ttlTimeUnit());
          try {
            joinPoint.proceed();
          } catch (Throwable e) {
            throw new RuntimeException(e);
          }
        }
        catch (Exception e) {
          log.error(e.getMessage(),e);
          //race condition발생시 트랜잭션 discard
          operations.discard();
          // lock release
          operations.unwatch();
          return false;
        }
        // 트랜잭션 종료
        operations.exec();
        // lock release
        operations.unwatch();
        return true;
      }
    });
    if(!success) {
      throw new RequestPerMinuteException("1분당 호출수 초과");
    }
  }
}
```

`get(key)` 메서드의 주석을 확인하면 트랜잭션이 시작되고 나서는 해당 key로 조회하면 항상 null을 return 한다고 설명되어 있습니다.

```puppet
/**
* Get the value of {@code key}.
*
* @param key must not be {@literal null}.
* @return {@literal null} when key does not exist or used in pipeline / transaction.
* @see <a href="https://redis.io/commands/get">Redis Documentation: GET</a>
*/
@Nullable
V get(Object key);
```

## 4\. Lua script를 실행시켜 atomic연산을 보장하도록 개선

Redis는 2.6 버전부터 내장된 Lua Script Engine을 이용하여 서버에서 Lua Script를 실행할 수 있습니다. 이 기능을 이용하여 API Rate Limiter에서 발생하는 race condition 문제를 해결할 수 있습니다. Lua Script에 작성한 로직을 실행하면 해당 연산이 Redis 서버에서 원자적(atomic)으로 처리되기 때문입니다.

컨슈머에서 API 호출 수를 사용할 때 race condition이 발생한다는 것을 확인했는데 이를 해결하기 위해서는 **Lua script를 작성하고 Lua script을 실행시켜서 atomic연산이 보장되도록 개선** 이 필요합니다. 동시에 4개의 컨슈머가 Lua Script를 실행시킨다면 레디스 서버에서 순차적으로 atomic연산으로 실행시키므로 가장 먼저 도착한 컨슈머의 Lua Script가 API 호출 수를 100으로 증가시키기 때문에 다음 Lua script에서는 API 호출수가 100 임을 확인하고 더 이상 API 호출 수를 증가시키지 않고 그대로 현재 값을 반환합니다.

Lua Script를 사용하면 atomic 연산을 처리할 수 있지만 주의해야 할 점이 있습니다. **Redis에서 Lua Script를 실행시킬 경우 해당 스크립트는 반드시 짧게 끝나는 로직으로 작성해야 합니다.** 만약, 처리시간이 오래 걸리는 로직이 들어가면 싱글스레드 기반의 레디스는 해당 스크립트를 실행하는 동안 다른 요청을 처리하지 못하는 일이 발생합니다.

Lua script에는 조회해야 하는 셀러의 API 호출 수를 조회하고 최댓값에 도달했는지에 따라서 1을 증가시키거나 바로 0을 리턴하는 코드가 작성되어 있습니다. 이 코드는 atomic 하게 실행되므로 여러 컨슈머가 동시에 실행했더라도 레디스 서버에서 순차적으로 차례차례 실행시키므로 동시성 문제가 발생하지 않습니다.

```bash
local key = KEYS[1] -- unique key
local limitCount = tonumber (ARGV[1]) -- limit size
local limitTime = tonumber (ARGV[2]) --  limiting time
local current = tonumber(redis.call('get', key) or '0')

if current + 1 > limitCount then -- 분당호출수 초과시 0 return
    return 0

else
    redis.call('INCRBY', key,'1')
    redis.call('expire', key,limitTime)
    return current + 1
end
```

RedisRateLimiter라는 인터페이스의 두 번째 버전인 RedisWithLuaScriptRateLimiter라는 구현체를 아래와 같이 추가했습니다.

```java
@Component("RedisWithLuaScriptRateLimiter")
@RequiredArgsConstructor
public class RedisWithLuaScriptRateLimiter implements RateLimiter{
  private final DefaultRedisScript<Long> defaultRedisScript;
  private final RedisTemplate<String, Serializable> redisTemplate;

  /**
   * lua script를 실행시켜서 redis에서 atomic한 연산이 진행되도록 한다
   */
  @Override
  public void tryApiCall(String key, LimitRequestPerTime limitRequestPerTime,ProceedingJoinPoint joinPoint) throws Throwable {
    Long callCounter = redisTemplate.execute(
        defaultRedisScript,Collections.singletonList(key),
        limitRequestPerTime.count(),
        TimeUnit.SECONDS.convert(limitRequestPerTime.ttl(),limitRequestPerTime.ttlTimeUnit())
    );
    if(callCounter == null) {
      log.error("redis 셀러별 분당 호출수 조회 실패");
      joinPoint.proceed();
      return;
    }
    if (callCounter.intValue() != 0 && callCounter.intValue() <= limitRequestPerTime.count()) {
      joinPoint.proceed();
      return;
    }
    throw new RequestPerMinuteException("1분당 호출수 초과");
  }
}
```

이를 사용하는 RateLimiterAspect에서 주입받아서 사용하도록 Qualifier만 변경해 주면 이제 컨슈머는 Lua script를 실행해서 API 호출 수를 계산하고 API 호출여부를 결정합니다.

- @Qualifier: 같은 타입의 Bean이 여러 개 있을 경우 주입받을 Bean을 설정할 수 있는 어노테이션
```kotlin
@Component
@Aspect
@Slf4j
public class RateLimiterAspect {

  private final RateLimiter rateLimiter;

  //Lua Script로 구현한 RateLimiter가 주입되도록 수정
  public RateLimiterAspect(@Qualifier("RedisWithLuaScriptRateLimiter") RateLimiter rateLimiter) {
    this.rateLimiter = rateLimiter;
  }

 /*
 * 런타임 시점에 타겟으로 설정한 메서드가 실행되기 직전에 실행되는 코드입니다.
 * @Around어노테이션에는 타겟으로 설정 가능한 범위를 정의합니다. (https://www.baeldung.com/spring-aop-pointcut-tutorial) 아래 예시코드는 com.example.component패키지에 속한 모든 클래스 메서드에 적용 가능합니다.
 */
  @Around("execution(* com.example.component.*.*(..)))")
  public void interceptor(ProceedingJoinPoint joinPoint) throws Throwable {
    LimitRequestPerTime limitRequestPerTime = getLimitRequestPerTimeAnnotationFromMethod(joinPoint);
    //LimitRequestPerTime 커스텀 어노테이션이 설정되지 않은 타겟 메서드는 분당 호출 제한을 체크하지 않고 바로 실행
    if(Objects.isNull(limitRequestPerTime)) {
       joinPoint.proceed();
       return;
    }
    //LimitRequestPerTime 커스텀 어노테이션을 설정한 타겟 메서드만 분당 호출 제한을 체크
    Long uniqueKey = getUniqueKeyFromMethodParameter(joinPoint);
    rateLimiter.tryApiCall(
        composeKeyWithUniqueKey(limitRequestPerTime.key(),uniqueKey,"ApiCounter"),
        limitRequestPerTime,
        joinPoint
    );
  }

  /*
  * ProceedingJoinPoint로부터 메서드에 태깅되어 있는 커스텀 어노테이션을 추출하는 메서드 입니다.
  */
  private LimitRequestPerTime getLimitRequestPerTimeAnnotationFromMethod(ProceedingJoinPoint joinPoint) {
    MethodSignature signature = (MethodSignature) joinPoint.getSignature();
    Method method = signature.getMethod();
    LimitRequestPerTime limitRequestPerTime = method.getAnnotation(LimitRequestPerTime.class);
    return limitRequestPerTime;
  }

  /*
  * ProceedingJoinPoint로부터 메서드의 인자목록에서 unique key를 추출하는 메서드 입니다.
  */
  private Long getUniqueKeyFromMethodParameter(ProceedingJoinPoint joinPoint) {
    List<Object> parameters = Arrays.asList(joinPoint.getArgs());
    return (Long) parameters.get(0);
  }

  /*
  * LimitRequestPerTime 커스텀 어노테이션에 정의한 prefix와 메서드의 인자에 포함되어 있는 unique key값을 합쳐주는 메서드 입니다.
  */
  private String composeKeyWithUniqueKey(String prefix, int uniqueId,String suffix) {
    StringBuffer stringBuffer = new StringBuffer();
    return stringBuffer
        .append(prefix).append(":")
        .append(uniqueId).append(":")
        .append(suffix)
        .toString();
  }

}
```

## 5\. 정리

Lua Script는 Redis의 메인스레드에서 실행되기 때문에 실행시간이 짧은 연산만 실행해야 한다는 점만 주의해서 사용한다면 atomic연산이 가능하기 때문에 동시성문제를 해결할 수 있습니다. Redis가 싱글스레드이기 때문에 동시성 문제가 발생하지 않는다고 생각했지만 API Rate Limiter를 개발하면서 atomic 연산이 아니라면 동시성 문제가 발생할 수 있다는 사실을 확인했습니다. Redis를 데이터 캐싱 이외에도 다양한 시스템을 설계하려는 분에게 도움이 되길 바라며 글을 마칩니다.

#### 'Backend' 카테고리의 다른 글

| [docker-compose를 이용하여 로컬 개발환경 구성하기(Part1)](https://dev.gmarket.com/72) (2) | 2023.04.12 |
| --- | --- |
| [초보 개발자를 위한 Redis Cluster Migration 가이드라인](https://dev.gmarket.com/71) (1) | 2023.03.28 |
| [Java Logger의 또다른 식구, tinylog](https://dev.gmarket.com/67) (0) | 2023.03.02 |
| [Handling-request-binding-exception in webflux](https://dev.gmarket.com/66) (0) | 2023.02.15 |
| [Thread의 개인 수납장 ThreadLocal](https://dev.gmarket.com/62) (0) | 2023.02.01 |

**댓글**

- [캔시플](https://jangjoon.tistory.com/) 좋은 포스팅 잘봤습니다
	굿밤되세요 ~ 2023.03.16 20:43 [신고](https://dev.gmarket.com/toolbar/popup/abuseReport/?entryId=69&commentId=13573694) 댓글 메뉴
	[댓글주소](https://dev.gmarket.com/69#comment13573694) [수정/삭제](#) [댓글쓰기](#)
- ykC 제가 작업하는 부분에서도 응용할수 있을것같습니다. 감사합니다 2023.03.27 10:12 [신고](https://dev.gmarket.com/toolbar/popup/abuseReport/?entryId=69&commentId=13594855) 댓글 메뉴
	[댓글주소](https://dev.gmarket.com/69#comment13594855) [수정/삭제](#) [댓글쓰기](#)
- 아무개 깔끔하고 정돈된 글 감사합니다. 2024.04.02 08:44 [신고](https://dev.gmarket.com/toolbar/popup/abuseReport/?entryId=69&commentId=16933395) 댓글 메뉴
	[댓글주소](https://dev.gmarket.com/69#comment16933395) [수정/삭제](#) [댓글쓰기](#)
- 족발ㄱ? 글의 분량이 꽤 되는데도 설명을 상세하게 잘해주셔서 몰입하면서 읽었네요 잘 읽었습니다! 2024.09.25 16:56 [신고](https://dev.gmarket.com/toolbar/popup/abuseReport/?entryId=69&commentId=19269198) 댓글 메뉴
	[댓글주소](https://dev.gmarket.com/69#comment19269198) [수정/삭제](#) [댓글쓰기](#)
