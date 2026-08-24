# Redis

Redis is a cache, message broker, and richly featured key-value store. Spring Boot offers basic auto-configuration for the Lettuce and Jedis client libraries and the abstractions on top of them provided by Spring Data Redis.

There is a `spring-boot-starter-data-redis` starter, which by default uses Lettuce. That starter handles both traditional and reactive applications.

## Connecting to Redis

You can inject auto-configured `RedisConnectionFactory`, `StringRedisTemplate`, or vanilla `RedisTemplate`.
```kotlin
@Component
class MyBean(private val template: StringRedisTemplate) {

	// ...

}
```

By default, the instance tries to connect to a Redis server at `localhost:6379`. You can specify custom connection details using `spring.data.redis.*` properties.
```yaml
spring:
	data:
		redis:
			host: "localhost"
			port: 6379
			database: 0
			username: "user"
			password: "secret"
```

```yaml
spring:
	data:
		redis:
			url: "redis://user:secret@localhost:6379"
			database: 0
```

> [!tip] You can also register an arbitrary number of beans that implement `LettuceClientConfigurationBuilderCustomizer`. `ClientResources` can also be customized using `ClientResourcesBuilderCustomizer`. If you use Jedis, `JedisClientConfigurationBuilderCustomizer` is also available.

Alternatively, you can register a bean of type `RedisStandaloneConfiguration`, `RedisSentinelConfiguration`, `RedisClusterConfiguration`, or `RedisStaticMasterReplicaConfiguration` to take full control over the configuration.

If you add your own `@Bean` of any of the auto-configured types, it replaces the default (except in the case of `RedisTemplate`, when the exclusion is based on the bean name, `redisTemplate`, not its type).

By default, a pooled connection factory is auto-configured if `commons-pool2` is on the classpath.

The auto-configured `RedisConnectionFactory` can be configured to use SSL for communication with the server by setting the properties:
```yaml
spring:
	data:
		redis:
			ssl:
				enabled: true
```
Custom SSL trust material can be configured in an SSL bundle and applied to the `RedisConnectionFactory` as shown in this example:
```yaml
spring:
	data:
		redis:
			ssl:
				bundle: "example"
```
