# Scripting

Spring Data Redis provides a high-level abstraction for running scripts that handles serialization and automatically uses the Redis script cache.

Scripts can be run by calling the `execute` methods of `RedisTemplate` and `ReactiveRedisTemplate`. Both use a configurable `ScriptExecutor` to run the provided script.

The default `ScriptExecutor` optimizes performance by retrieving the SHA1 of the script and attempting first to run `evalsha`, falling back to `eval` if the script is not yet present in the Redis script cache.

The following example runs a common "check-and-set" scenario by using a Lua script.

```kotlin
@Bean
fun script(): RedisScript<Boolean> {
	return RedisScript<Boolean>(ClassPathResource("META-INF/scripts/check_and_set.lua"))
}
```

```kotlin
class Example {
	@Autowired
	lateinit var redisOperations: RedisOperations<String, String>

	@Autowired
	lateinit var script: RedisScript<Boolean>

	fun checkAndSet(expectedValue: String, newValue: String): Boolean {
		return redisOperations.execute(script, listOf("key"), expectedValue, newValue)
	}
}
```

```lua
local current = redis.call('GET', KEYS[1])
if current == ARGV[1]
	then redis.call('SET', KEYS[1], ARGV[2])
	return true
end
return false
```

The script `resultType` should be one of `Long`, `Boolean`, `List`, or a deserialized value type. It can also be `null` if the script returns a throw-away status (specifically, `OK`).

>[!tip] It is ideal to configure a single instance of `DefaultRedisScript` to avoid re-calculation of the script's SHA1 on every script run.

Scripts can be run within a `SessionCallback` as part of a transaction or pipeline.
