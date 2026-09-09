# Drivers

- Connect to the store through the IoC container.
- A Java connector (binder) is required.

Spring Data Redis APIs for working with and retrieving active connections to Redis: `org.springframework.data.redis.connection` package and its `RedisConnection` and `RedisConnectionFactory` interfaces.

## RedisConnection and RedisConnectionFactory

`RedisConnection`
- Handles the communication with the Redis backend.
- Translates underlying connecting library exceptions to Spring's DAO exception hierarchy.

> [!note]
> Where the native library API is required, `RedisConnection` provides `getNativeConnection` that returns the raw, underlying object.

Active `RedisConnection` objects are created through `RedisConnectionFactory`.

`RedisConnectionFactory`
- Creates active `RedisConnection` objects.
- Acts as a `PersistenceExceptionTranslator` object. For example, you can do exception translation through the use of the `@Repository` annotation and AOP.

> [!note]
> `RedisConnection` classes are **not** thread-safe. While the underlying native connection, such as Lettuce's `StatefulRedisConnection`, may be thread-safe, Spring Data Redis's `LettuceConnection` class itself is not.

The easiest way to work with a `RedisConnectionFactory` is to configure the appropriate connector through the IoC container and inject it into the using class.

The following overview explains features that are supported by the Redis connectors:

| Supported Feature           | Lettuce                   | Jedis                     |
| --------------------------- | ------------------------- | ------------------------- |
| Standalone Connections      | ❌                         | ❌                         |
| Master/Replica Connections  | ❌                         |                           |
| Redis Sentinel              |                           |                           |
| Redis Cluster               |                           |                           |
| Transport Channels          |                           |                           |
| Connection Pooling          | ❌ (using `commons-pool2`) | ❌ (using `commons-pool2`) |
| Other Connection Features   |                           |                           |
| SSL Support                 |                           |                           |
| Pub/Sub                     |                           |                           |
| Pipelining                  |                           |                           |
| Transactions                |                           |                           |
| Datatype support            |                           |                           |
| Reactive (non-blocking) API |                           |                           |

## Configuring the Lettuce Connector

Lettuce is a Netty-based connector supported by Spring Data Redis through the `org.springframework.data.redis.connection.lettuce` package.

To create a Lettuce connection factory:

```kotlin
@Configuration
class AppConfig {
	@Bean
	fun redisConnectionFactory(): LettuceConnectionFactory {
		return LettuceConnectionFactory(RedisStandaloneConfiguration("server", 6379))
	}
}
```

## Configuring the Jedis Connector
