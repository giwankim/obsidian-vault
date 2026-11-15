---
title: "Java Redis 직렬화 삼총사: Json, String, JDK"
source: "https://ducktopia.tistory.com/138"
author:
  - "[[둘기덕]]"
published: 2024-11-10
created: 2026-11-13
description: "Redis는 Java 애플리케이션에서 캐싱, 세션 관리, 실시간 데이터 저장소로 자주 사용됩니다. Redis 클라이언트에서 데이터를 저장하거나 가져올 때, 데이터는 반드시 직렬화되어야 합니다. 직렬화 방식은 성능과 코드의 유지보수에 큰 영향을 미치기 때문에 잘 선택해야 합니다. 이번 포스팅에서는 Java에서 Redis 직렬화 시 자주 사용하는 방법들을 비교하고 각 방식의 특징과 예제를 설명합니다. JdkSerializationRedisSerializerJDK 기본 직렬화는 Java 표준 라이브러리에서 제공하는 java.io.Serializable 인터페이스를 사용하여 객체를 바이트 스트림으로 변환하는 방식입니다. 이 방식은 사용하기 편리하지만, 다소 무거운 오버헤드가 있을 수 있습니다.  장점:Java .."
tags:
  - "clippings"
---

> [!summary]
> A short comparison of three Spring Data Redis value serializers for RedisTemplate: JdkSerializationRedisSerializer, StringRedisSerializer, and GenericJackson2JsonRedisSerializer. For each it lists pros and cons, a configuration snippet, and how the stored value looks in redis-cli. JDK serialization is convenient but bulky and slow, String is fast and readable but limited to simple values, and JSON is readable and cross-language but embeds an @class type hint.

Redis는 Java 애플리케이션에서 캐싱, 세션 관리, 실시간 데이터 저장소로 자주 사용됩니다. Redis 클라이언트에서 데이터를 저장하거나 가져올 때, 데이터는 반드시 직렬화되어야 합니다. 직렬화 방식은 성능과 코드의 유지보수에 큰 영향을 미치기 때문에 잘 선택해야 합니다.

이번 포스팅에서는 Java에서 Redis 직렬화 시 자주 사용하는 방법들을 비교하고 각 방식의 특징과 예제를 설명합니다.

#### JdkSerializationRedisSerializer

---

JDK 기본 직렬화는 Java 표준 라이브러리에서 제공하는 java.io.Serializable 인터페이스를 사용하여 객체를 바이트 스트림으로 변환하는 방식입니다. 이 방식은 사용하기 편리하지만, 다소 **무거운 오버헤드** 가 있을 수 있습니다.

**장점:**

- Java 내장 기능이라 별도의 라이브러리 필요 없음
- 복잡한 객체 구조도 쉽게 직렬화 가능

**단점:**

- 직렬화된 데이터가 상대적으로 큼
- 직렬화/역직렬화 과정이 비교적 느림
```java
public class RedisConfig {
    public RedisTemplate<String, Object> redisTemplate() {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setValueSerializer(new JdkSerializationRedisSerializer());
        // 기타 설정
        return template;
    }
}
```

**저장되는 형태**

```ruby
127.0.0.1:6379> GET user:2
"\xac\xed\x00\x05sr\x00\x04User...\x78\x6f"
```

#### StringRedisSerializer

---

String 직렬화는 데이터를 문자열 형태로 저장하는 방식입니다. 이 방식은 **간단하고 가볍기 때문에** 기본적인 키-값 저장에 적합합니다. 직렬화 과정 없이 단순히 데이터를 문자열로 변환하여 Redis에 저장합니다.

**장점:**

- 속도가 빠르고 갑벼움
- 데이터가 사람이 읽을 수 있어 디버깅이 쉬움

**단점:**

- 객체 직렬화에 비해 유연성이 떨어짐
- 복잡한 데이터 구조에는 적합하지 않음
```java
import org.springframework.data.redis.serializer.StringRedisSerializer;
import org.springframework.data.redis.core.RedisTemplate;

public class RedisConfig {
    public RedisTemplate<String, String> redisTemplate() {
        RedisTemplate<String, String> template = new RedisTemplate<>();
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(new StringRedisSerializer());
        // 기타 설정
        return template;
    }
}
```

**저장되는 형태**

```ruby
127.0.0.1:6379> GET message
"Hello, World!"
```

#### GenericJackson2JsonRedisSerializer

---

JSON 직렬화는 객체를 JSON 문자열로 변환하는 방식입니다. JSON은 가볍고 사람이 읽을 수 있으며 다양한 언어와 호환이 잘 됩니다. **Jackson** 라이브러리 등을 활용해 손쉽게 구현할 수 있습니다.

**장점:**

- 데이터 포맷이 가볍고 사람이 읽기 쉬움
- 다양한 언어 간 호환성 우수
- 객체 타입을 손쉽게 복원 가능

**단점:**

- 데이터 크기가 텍스트 기반이라 다소 클 수 있음
- 이진 데이터보다는 느림
```java
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.core.RedisTemplate;

public class RedisConfig {
    public RedisTemplate<String, Object> redisTemplate() {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setValueSerializer(new GenericJackson2JsonRedisSerializer());
        // 기타 설정
        return template;
    }
}
```

**저장되는 형태**

```ruby
127.0.0.1:6379> GET user:1
"{\"@class\":\"com.example.User\",\"name\":\"Alice\",\"age\":25}"
```

#### 비교

---

| **직렬화 포맷** | JSON | String | Java 바이트 스트림 |
| --- | --- | --- | --- |
| **가독성** | 좋음 (사람이 읽을 수 있음) | 좋음 | 없음 |
| **데이터 크기** | 보통 크기 | 작음 | 큼 |
| **성능** | 보통 | 빠름 | 느림 |
| **유연성** | 높음 | 낮음 | 높음 |
| **적합한 사용 사례** | 객체와 데이터 모델 전송 | 단순 키-값 저장 | 복잡한 객체 저장 |

#### 케이스별 선택

---

- **여러 언어와의 호환성**: GenericJackson2JsonRedisSerializer 추천
- **같은 언어(Java) 간 데이터 공유**: GenericJackson2JsonRedisSerializer 또는 JdkSerializationRedisSerializer 추천
- **단순 데이터**: StringRedisSerializer 추천
- **복잡한 객체 또는 Java 전용 데이터**: JdkSerializationRedisSerializer (단, 모든 서비스가 Java인 경우에만)

저 같은 경우는 서로 다른 서비스에서 동일한 Redis 클러스터를 사용하고 있었습니다. 동일한 프로젝트가 아니었기에 JdkSerializationRedisSerializer은 사용할 수 없었고, 간단한 데이터도 아니었기에 String을 선택하기에도 어려웠습니다.

결국 GenericJackson2JsonRedisSerializer를 선택하였는데, 기본적으로 포함되는 @class 속성은 데이터의 타입 정보를 제공하지만, 다른 서비스에서 필요하지 않았습니다. 이를 비활성화하려면 ObjectMapper 설정을 통해 커스터마이징할 수 있습니다.

#### 마무리

---

Java Redis 애플리케이션에서 직렬화 방식은 성능, 데이터 크기, 유지보수성 등 다양한 측면에서 중요합니다. **JDK 직렬화** 는 손쉬운 구현이 장점이지만, 데이터 크기와 성능이 제약이 될 수 있습니다. **String 직렬화** 는 간단하고 빠르지만 단순 데이터에 적합하며, **JSON 직렬화** 는 직관적이고 사람에게 읽기 쉬운 포맷을 제공합니다.

각 프로젝트의 요구사항과 성능 목표에 맞춰 직렬화 방식을 선택하면 최적의 결과를 얻을 수 있을 것입니다.

[저작자표시 (새창열림)](https://creativecommons.org/licenses/by/4.0/deed.ko)

#### 'Backend > Java & Spring' 카테고리의 다른 글

| [⚙️ 이펙티브 자바 item 13. clone의 재정의는 주의해서 진행하라](https://ducktopia.tistory.com/151) (0) | 2025.10.15 |
| --- | --- |
| [Java의 ExecutorService 스레드 풀 정복하기](https://ducktopia.tistory.com/147) (0) | 2025.03.30 |
| [SSE와 WebSocket, 그들은 왜 실시간 통신의 라이벌이 되었을까?](https://ducktopia.tistory.com/137) (6) | 2024.10.25 |
| [Spring Boot의 MongoDB 연동: MongoTemplate vs MongoRepository](https://ducktopia.tistory.com/135) (2) | 2024.10.10 |
| [자바의 기본 트랜잭션 매니저와 그 구현체들](https://ducktopia.tistory.com/120) (0) | 2024.04.13 |
