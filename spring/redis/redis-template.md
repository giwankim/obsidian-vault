# Working with Objects through `RedisTemplate`

- You are most likely to use `RedisTemplate` and its corresponding package, `org.springframework.data.redis.core`.
- While `RedisConnection` offers low-level methods that accept and return binary values (`byte` arrays), the template takes care of serialization and connection management.

The `RedisTemplate` class implements the `RedisOperations` interface.

> [!note] The preferred way to reference operations on a `RedisTemplate` instance is through the `RedisOperations` interface.

Moreover, the template provides operations views that offer generified interfaces.

Once configured, the template is thread-safe and can be reused across multiple instances.

`RedisTemplate` uses a Java-based serializer for most of its operations.

- You can change the serialization mechanism on the template, and the Redis module offers implementations, which are available in the `org.springframework.data.redis.serializer` package.
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

## Serializers
