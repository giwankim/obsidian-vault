# Working with Objects through `RedisTemplate`

- You are most likely to use `RedisTemplate` and its corresponding package, `org.springframework.data.redis.core`.
- While `RedisConnection` offers low-level methods that accept and return binary values (`byte` arrays), the template takes care of serialization and connection management.

The `RedisTemplate` class implements the `RedisOperations` interface.

> [!note] The preferred way to reference operations on a `RedisTemplate` instance is through the `RedisOperations` interface.

Moreover, the template provides operations views that offer generified interfaces.

Once configured, the template is thread-safe and can be reused across multiple instances.

`RedisTemplate` uses a Java-based serializer for most of its operations.

- You can change the serialization mechanism on the template, and the Redis module offers implementations in the `org.springframework.data.redis.serializer` package.
- You can also set any of the serializers to null and use `RedisTemplate` with raw byte arrays by setting the `enableDefaultSerializer` property to `false`.

Configuring the Template API:
```kotlin
@Configuration
class MyConfig {
    @Bean
    fun connectionFactory(): LettuceConnectionFactory {
        return LettuceConnectionFactory()
    }

    @Bean
    fun redisTemplate(connectionFactory: RedisConnectionFactory): RedisTemplate<String, String> {
        return RedisTemplate<String, String>().apply {
            setConnectionFactory(connectionFactory)
        }
    }
}
```

For cases where you need a certain template view, declare the view as a dependency and inject the template. The container automatically performs the conversion, eliminating the `opsFor[X]` calls.

Pushing an item to a list using `RedisTemplate`:
```kotlin
class Example {
    // inject the actual operations
    @Autowired
    private lateinit var operations: RedisOperations<String, String>

    // inject the template as ListOperations
    @Resource(name="redisTemplate")
    private lateinit var listOps: ListOperations<String, String>

    fun addLink(userId: String, url: URL) {
        listOps.leftPush(userId, url.toExternalForm())
    }
}
```

## String-focused Convenience Classes

The Redis module provides two extensions to `RedisConnection` and `RedisTemplate`: `StringRedisConnection` (with its `DefaultStringRedisConnection` implementation) and `StringRedisTemplate`. The template and the connection use the `StringRedisSerializer` underneath.

```kotlin
@Configuration
class RedisConfiguration {
    @Bean
    fun redisConnectionFactory(): LettuceConnectionFactory {
        return LettuceConnectionFactory()
    }

    @Bean
    fun stringRedisTemplate(redisConnectionFactory: RedisConnectionFactory): StringRedisTemplate {
        return StringRedisTemplate().apply {
            setConnectionFactory(redisConnectionFactory)
        }
    }
}
```

```kotlin
class Example {
    @Autowired
    private lateinit var redisTemplate: StringRedisTemplate

    fun addLink(userId: String, url: URL) {
        redisTemplate.opsForList().leftPush(userId, url.toExternalForm())
    }
}
```

`RedisTemplate` and `StringRedisTemplate` let you talk directly to Redis through the `RedisCallback` interface. The following example shows how to use the `RedisCallback` interface:
```kotlin
fun useCallback() {
    redisOperations.execute(RedisCallback<Unit> { connection ->
        val size = connection.dbSize()
        // Can cast to StringRedisConnection if using a StringRedisTemplate
        (connection as StringRedisConnection).set("key", "value")
    })
}
```

## Serializers

The conversion between user (custom) types and raw data is handled by Spring Data Redis in the `org.springframework.data.redis.serializer` package.

This package contains two types of serializers that take care of the serialization process:
- Two-way serializers based on `RedisSerializer`.
- Element readers and writers that use `RedisElementReader` and `RedisElementWriter`.

The main difference is that `RedisSerializer` primarily serializes to `byte[]`, while readers and writers use `ByteBuffer`.

Multiple implementations are available:
- `JdkSerializationRedisSerializer`, which is used by default for `RedisCache` and `RedisTemplate`.
- `StringRedisSerializer`.

However, one can use `OxmSerializer` for Object/XML mapping, or `Jackson2JsonRedisSerializer` or `GenericJackson2JsonRedisSerializer` for storing data in JSON format.
