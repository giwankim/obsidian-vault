---
title: "Spring 의 Cache 추상화를 사용하면서, 단건/다건 key 에 대한 동일 저장소 사용하기 | 우아한형제들 기술블로그"
source: "https://techblog.woowahan.com/2601/"
author:
published: 2019-01-04
created: 2026-10-11
description: "들어가며 이전에는 Google 의 Guava 를 이용하여 Local Cache 기능을 구현을 했습니다. 'guava' 단순하게 Key/Value 에 대해서 가장 쉽게 사용을 할 수 있는 것중의 하나가 Spring 에서 제공을 해주는 'Cache Abstraction' 을 사용을 하는 것으로 생각 됩니다. 이 글은 동일 request / response 를 유지를 하고 단순이 이 것을 List 로 만들고, 단건과 다건을 하나의"
tags:
  - "clippings"
---

> [!summary]
> Woowahan (2019) shows how to make single-key `@Cacheable` lookups and a multi-key collection lookup share one local cache store in Spring's cache abstraction. Looping over the single-key method from inside the bean doesn't work because self-invocation bypasses the AOP proxy. Instead, a `multiCacheGet` helper reads hits key by key from the `Cache`, bulk-loads only the missing keys, and writes them back; a `@CacheKey` annotation read via reflection removes the key-extractor parameter. They used Caffeine after hitting a cache2k bug with Spring Boot 2.0.

## Spring 의 Cache 추상화를 사용하면서, 단건/다건 key 에 대한 동일 저장소 사용하기

2019\. 01. 04. WoowaTech ![](https://www.gravatar.com/avatar/e34137fa161790cdbc0a3ffea00e9f29)

[Backend](https://techblog.woowahan.com/?pcat=backend)

## 들어가며

이전에는 Google 의 Guava 를 이용하여 Local Cache 기능을 구현을 했습니다. [‘guava’](https://github.com/google/guava)

단순하게 Key/Value 에 대해서 가장 쉽게 사용을 할 수 있는 것중의 하나가 Spring 에서 제공을 해주는 [‘Cache Abstraction’](https://techblog.woowahan.com/2601/%5Bhttps://docs.spring.io/spring/docs/current/spring-framework-reference/integration.html#cache) 을 사용을 하는 것으로 생각 됩니다.

이 글은 동일 request / response 를 유지를 하고 단순이 이 것을 List 로 만들고, 단건과 다건을 하나의 Local Cache 저장소를 사용하게 하는 경험을 적었습니다.

## 기본원리

Bean 으로 만든 CacheManager 를 주입을 받아서, 사용을 합니다.

아래 코드와 같이 cacheManager 를 bean으로 만드는 부분이 있을거에요.

```java
@Bean
public CacheManager cacheManager() {
    ...
}
```

여기서 각각 Local Cache 저장소를 만든것을 아래 코드와 같이 @Cacheable annotation 을 이용해서 사용을 하고, 이 annotation 이 적용된 method 의 parameter 값을 이용하여 cache 의 key 값을 정하게 됩니다.

```java
@Cacheable(cacheNames = "cache repository name")
public Response test(Long key)
```

이때 형태는 동일하고, Collection 으로 하나의 method 를 추가하고 싶은 경우가 있습니다. 아래처럼,

```java
@Cacheable(cacheNames = "cache repository name")
public Set<Response> test(Set<Long> key)
```

이때, 단순하게 생각해서

```java
@Cacheable(cacheNames = "cache repository name")
public Set<Response> test(Set<Long> keys) {
    List<Response> results = new ArrayList<>();

    for(Long key : keys) {
        results.add(test(key));
    }

    return results;
}
```

이렇게 하면은 당연히 안됩니다. @Cacheable annotation 도 AOP 기반으로 동작을 하기 때문이죠.

## 개발내용

위의 방법으로 되지 않는 것을 확인을 하였으니, Service 를 하나 만들어 로직을 구현해보겠습니다.

아래 코드가 핵심로직입니다.

```java
public <K, V> Set<V> multiCacheGet(String cacheKeyName,
                                   Class<K> keyClass,
                                   Class<V> valueClass,
                                   Collection<K> keys,
                                   Function<Set<K>, Set<V>> notCachedValueFinder,
                                   BiFunction<V, Class<K>, K> keyExtractor) {

    Cache cache = getCache(cacheKeyName);

    final Set<K> notCachedKeys = new HashSet<>();
    final Set<V> cachedValues = new HashSet<>();

    for (K key : keys) {
        V cachedValue = cache.get(key, valueClass);
        if (cachedValue != null) {
            cachedValues.add(cachedValue);
        } else {
            notCachedKeys.add(key);
        }
    }

    log.info("캐싱되지 않은 키값", notCachedKeys);

    Set<V> loadedValues = loadNotCachedValues(cache, keyClass, notCachedKeys, notCachedValueFinder, keyExtractor);

    cachedValues.addAll(loadedValues);
    return cachedValues;
}
```
- parameter 설명
	- cacheKeyName: 위에 Configuration class 에서 설정한 cache key 이름
		- keyClass: key 의 class
		- valueClass: value 의 class
		- keys: 찾아야 하는 값들의 key
		- notCachedValueFinder: 현재 cache 에 저장이 되어 있지 않은, key 들로 데이터를 찾는 function
		- keyExtractor: key 값을 추출하는 function

이제는 이것을 사용하게 코드만 변경하면 될 것 같습니다.

- 단건을 처리하는 method
	```java
	@Cacheable(cacheNames = "cache repository name")
	public CacheExampleResponse find(Long key) {
	log.info("단건 캐싱 시작 - key", key);
	return CacheExampleResponse.of(key, key + 1000L, key + "content");
	}
	```
- 다건을 처리하는 method
	```java
	public Set<CacheExampleResponse> find(Set<Long> keys) {
	log.info("다건 캐싱 시작 - keys", keys);
	return multiKeyCacheService.multiCacheGet(
	        "cache repository name",
	        Long.class,
	        CacheExampleResponse.class,
	        keys,
	        CacheExampleResponse::getKey,
	        this::findValue);
	}
	```
	로그를 확인해보면 동일 캐시저장소를 사용을하면서 잘 캐싱이 되는 것을 확인 하실 수 있습니다.

## 좀더 나아가서

- 위에서 봤듯이 6개의 parameter 를 받습니다. 여기서 한가지를 줄여 보겠습니다.
- valueClass 에는 key 값이 있습니다. 이 key 값에 annotation 을 넣어보겠습니다.
- 먼저 annotation class 를 선언합니다.
	```java
	@Target()
	@Retention(RetentionPolicy.RUNTIME)
	public @interface CacheKey {
	}
	```
- 그 다음에, value class 에 annotation 을 적용합니다.
	```java
	public class CacheExampleResponse {
	@CacheKey
	private Long key;
	...
	}
	```
- 아래 코드는 field 와 method 에서 @CacheKey annotation 이 적용된걸 찾습니다.
	```java
	private <K, V> K cacheKeyAnnotationExtractor(V v, Class<K> keyClass) {
	return Optional.ofNullable(cacheKeyAnnotationOfFieldExtractor(v, keyClass))
	        .orElseGet(() -> Optional.ofNullable(cacheKeyAnnotationOfMethodExtractor(v, keyClass))
	                .orElseThrow(() -> new IllegalStateException(String.format("@CacheKey 애노테이션이 어느 필드/메소드 에도 존재하지 않음 - %s", v.getClass().getName()))));
	}
	```
	```java
	private <K, V> K cacheKeyAnnotationOfFieldExtractor(V v, Class<K> keyClass) {
	for (Field field : v.getClass().getDeclaredFields()) {
	    if (field.getAnnotation(CacheKey.class) != null) {
	        try {
	            if (!field.getType().isAssignableFrom(keyClass)) {
	                throw new IllegalStateException(String.format("@CacheKey 애노테이션 Key의 타입 변환 실패 - %s - field: %s", v.getClass().getName(), field.getName()));
	            }
	            field.setAccessible(true);
	            return keyClass.cast(field.get(v));
	        } catch (IllegalAccessException | RuntimeException e) {
	            // accessible 을 true 로 변경하므로 발생할 수 없다.
	            throw new IllegalStateException(String.format("@CacheKey 애노테이션 값 읽기 실패 - %s - field: %s", v.getClass().getName(), field.getName()), e);
	        }
	    }
	}
	return null;
	}
	```
	```java
	private <K, V> K cacheKeyAnnotationOfMethodExtractor(V v, Class<K> keyClass) {
	for (Method method : v.getClass().getDeclaredMethods()) {
	    if (method.getAnnotation(CacheKey.class) != null) {
	        try {
	            if (!method.getReturnType().isAssignableFrom(keyClass)) {
	                throw new IllegalStateException(String.format("@CacheKey 애노테이션 Key의 타입 변환 실패 - %s - field: %s", v.getClass().getName(), method.getName()));
	            }
	            return keyClass.cast(method.invoke(v));
	        } catch (IllegalAccessException | RuntimeException | InvocationTargetException e) {
	            throw new IllegalStateException(String.format("@CacheKey 애노테이션 값 읽기 실패 - %s - method: %s", v.getClass().getName(), method.getName()), e);
	        }
	    }
	}
	return null;
	}
	```

## 적용하면서

처음에는 cache2k 라는 캐시 구현체를 사용을 할려고 했습니다. [‘cache2k’](https://cache2k.org/docs/latest/user-guide.html#spring)

하지만 spring boot 에서 사용을 한다면 예상치 못한 버그에 부딪칠 수 있습니다. 이건 이미 리포팅이 되었으며 자세한 내용은 링크를 참조 부탁드립니다. [‘bug reporting’](https://github.com/cache2k/cache2k/issues/94)

이때 필자가 사용했던 버전은

- cache2k 1.2.0.Final, Spring Boot 2.0.6 이다.
- cache2k 1.2.1 에는 버그가 수정 되었다는 댓글을 볼 수 있지만, 아직은 milestone 버전이라 caffeine 을 사용을 하였습니다.

## 예제소스

위에 설명한 내용을 예제 코드로 작성되었습니다.

소스를 다운받아 실행해보면 어떻게 작동을 하는지 쉽게 이해하실 수 있을거에요.

[‘https://github.com/woowabros/multi-key-spring-cache-example’](https://github.com/woowabros/multi-key-spring-cache-example)
