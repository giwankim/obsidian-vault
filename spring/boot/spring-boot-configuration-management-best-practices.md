---
title: "Spring Boot Configuration Management Best Practices"
source: "https://blog.jetbrains.com/idea/2026/08/spring-boot-configuration-management-best-practices/"
author:
  - "[[Siva Katamreddy]]"
published: 2026-08-21
created: 2026-08-23
description: "Learn best practices for managing Spring Boot configuration across environments, from defaults and validation to secure secrets handling."
tags:
  - "clippings"
---

> [!summary]
> Sorts Spring Boot configuration into three categories — application defaults, deployment config, and secrets — and argues for immutable `@ConfigurationProperties` records over scattered `@Value` annotations, with `@Validated` plus Jakarta Bean Validation so startup fails fast on missing or invalid values. Also covers property-source precedence, how environment variable names are derived from canonical property names, and binding properties to third-party classes via a wrapper. Closes with secrets management (Vault, Secrets Manager) and per-architecture guidance for monoliths, Kubernetes workloads, and microservices.

[IntelliJ IDEA](https://blog.jetbrains.com/idea/category/idea/)

Spring Boot provides comprehensive [externalized application configuration](https://docs.spring.io/spring-boot/reference/features/external-config.html#features.external-config) support. It enables one application artifact to run in different environments by supplying values from various sources such as:

- Property files
- Environment variables
- System properties
- Command-line arguments

In this article, we’ll explore the best practices for managing Spring Boot application configuration.
A well-designed configuration strategy should ensure that:

- Configuration remains separate from the application code.
- The application fails to start when the required configuration is missing or invalid.
- Default values can be overridden for each deployment environment.
- Sensitive values are supplied by a dedicated secrets management system.

## Configuration properties classification

Typically, Spring Boot application configuration falls into three categories:

- **Application defaults:** Safe, non-secret values such as third-party service URLs, timeouts, and retry limits. Store these with the application.
- **Deployment configuration:** Values that identify an environment, such as database hosts, queue names, and external service URLs. Supply these through the deployment platform.
- **Secrets:** Passwords, API keys, certificates, and private keys. Store these in a dedicated secrets system.

For example, `application.properties` can provide application default configuration properties:

app.promotion-service.base-url=http://localhost:8181

app.promotion-service.timeout=3s

app.promotion-service.retries=3

logging.level.com.jetbrains=DEBUG

spring.jpa.hibernate.ddl-auto=validate

spring.jpa.open-in-view=false

app.promotion-service.base-url=http://localhost:8181 app.promotion-service.timeout=3s app.promotion-service.retries=3 logging.level.com.jetbrains=DEBUG spring.jpa.hibernate.ddl-auto=validate spring.jpa.open-in-view=false

```
app.promotion-service.base-url=http://localhost:8181
app.promotion-service.timeout=3s
app.promotion-service.retries=3
logging.level.com.jetbrains=DEBUG
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.open-in-view=false
```

A default value should be safe for every environment in which it may be used. Properties such as database URLs and credentials should never be hard-coded in the application code. If a required value has no safe default, validate its presence during startup.

## Use @ConfigurationProperties for binding application properties

Spring applications can access configuration values through `Environment`, `@Value`, or `@ConfigurationProperties`.

Use `Environment` when property names must be resolved dynamically or infrastructure code needs direct access to property sources.

Use `@Value` for isolated values:

PromotionService(

@Value("${app.promotion-service.base-url}") String baseUrl,

@Value("${app.promotion-service.timeout}") Duration timeout,

@Value("${app.promotion-service.retries}") int retries) {

this.baseUrl = baseUrl;

this.timeout = timeout;

this.retries = retries;

}

PromotionService( @Value("{app.promotion-service.timeout}") Duration timeout, @Value("${app.promotion-service.retries}") int retries) { this.baseUrl = baseUrl; this.timeout = timeout; this.retries = retries; }

```
PromotionService(
  @Value("${app.promotion-service.base-url}") String baseUrl,
  @Value("${app.promotion-service.timeout}") Duration timeout,
  @Value("${app.promotion-service.retries}") int retries) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
    this.retries = retries;
}
```

Scattered `@Value` expressions make property names difficult to discover, validate, and refactor. A dedicated configuration type using `@ConfigurationProperties` supports all these features.

For related configuration properties, prefer `@ConfigurationProperties`. It provides:

- Type-safe binding and conversion
- Relaxed binding between property names and Java members
- Group-level validation
- IDE completion and navigation through generated metadata

For example, if we are integrating with a third-party REST API, we may want to configure the service base URL, timeout, and number of retries.

app.promotion-service.base-url=${PROMOTION\_SERVICE\_URL}

app.promotion-service.timeout=${PROMOTION\_SERVICE\_TIMEOUT:3s}

app.promotion-service.retries=3

app.promotion-service.base-url={PROMOTION\_SERVICE\_TIMEOUT:3s} app.promotion-service.retries=3

```
app.promotion-service.base-url=${PROMOTION_SERVICE_URL}
app.promotion-service.timeout=${PROMOTION_SERVICE_TIMEOUT:3s}
app.promotion-service.retries=3
```

In the above configuration, we are setting `base-url` value from the environment variable `PROMOTION_SERVICE_URL` and `timeout` value from the `PROMOTION_SERVICE_TIMEOUT` environment variable with a default value of 3 seconds.

Spring Boot supports setter-based binding. You can bind properties to a class that uses setters as follows:

@ConfigurationProperties(prefix = "app.promotion-service")

public class PromotionSvcProperties {

private String baseUrl;

private Duration timeout;

private int retries;

// Setters and getters

}

@ConfigurationProperties(prefix = "app.promotion-service") public class PromotionSvcProperties { private String baseUrl; private Duration timeout; private int retries; // Setters and getters }

```
@ConfigurationProperties(prefix = "app.promotion-service")
public class PromotionSvcProperties {

    private String baseUrl;
    private Duration timeout;
    private int retries;

    // Setters and getters
}
```

Register configuration types using `@ConfigurationPropertiesScan`:

@SpringBootApplication

@ConfigurationPropertiesScan

public class Application {

public static void main(String\[\] args) {

SpringApplication.run(Application.class, args);

}

}

@SpringBootApplication @ConfigurationPropertiesScan public class Application { public static void main(String\[\] args) { SpringApplication.run(Application.class, args); } }

```
@SpringBootApplication
@ConfigurationPropertiesScan
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

The `@ConfigurationPropertiesScan` annotation scans for `@ConfigurationProperties` annotated components and registers them as Spring beans.

Now we can inject `PromotionSvcProperties` into other Spring beans and access property values.

## Prefer Records for @ConfigurationProperties binding

Typically, configuration is normally established during startup and remains unchanged for the lifetime of the application.

For most application configurations, a Java record is the preferred option. It provides immutability out of the box so that their values won’t be modified even by mistake in contrast to class-based binding where you can accidentally invoke a setter:

@ConfigurationProperties(prefix = "app.promotion-service")

public record PromotionSvcProperties(

String baseUrl,

Duration timeout,

int retries) {

}

@ConfigurationProperties(prefix = "app.promotion-service") public record PromotionSvcProperties( String baseUrl, Duration timeout, int retries) { }

```
@ConfigurationProperties(prefix = "app.promotion-service")
public record PromotionSvcProperties(
        String baseUrl,
        Duration timeout,
        int retries) {
}
```

Spring Boot’s relaxed binding maps canonical kebab-case names such as `base-url` to the `baseUrl` field.

Sometimes we may want to bind properties to a bean provided by a third-party library, and we can’t change their source code to add `@ConfigurationProperties` annotation.

To bind configuration properties directly to a third-party class, declare it as a `@Bean` and annotate the bean method with `@ConfigurationProperties`:

@Configuration

public class ClientConfiguration {

@Bean

@ConfigurationProperties(prefix = "third-party.client")

public ThirdPartyClientProperties clientProperties() {

return new ThirdPartyClientProperties();

}

}

@Configuration public class ClientConfiguration { @Bean @ConfigurationProperties(prefix = "third-party.client") public ThirdPartyClientProperties clientProperties() { return new ThirdPartyClientProperties(); } }

```
@Configuration
public class ClientConfiguration {

    @Bean
    @ConfigurationProperties(prefix = "third-party.client")
    public ThirdPartyClientProperties clientProperties() {
        return new ThirdPartyClientProperties();
    }
}
```

You can configure the `third-party.client` properties as follows:

third-party.client.base-url=https://api.example.com

third-party.client.connect-timeout=5s

third-party.client.read-timeout=30s

third-party.client.base-url=https://api.example.com third-party.client.connect-timeout=5s third-party.client.read-timeout=30s

```
third-party.client.base-url=https://api.example.com
third-party.client.connect-timeout=5s
third-party.client.read-timeout=30s
```

If the third-party class is immutable or not supports setter binding, create your own properties class and use it to construct the third-party object:

@ConfigurationProperties(prefix = "third-party.client")

public record ClientProperties(

URI baseUrl,

Duration connectTimeout,

Duration readTimeout

) {}

@Configuration

@EnableConfigurationProperties(ClientProperties.class)

class ClientConfiguration {

@Bean

ThirdPartyClient thirdPartyClient(ClientProperties properties) {

return new ThirdPartyClient(

properties.baseUrl(),

properties.connectTimeout(),

properties.readTimeout()

);

}

}

@ConfigurationProperties(prefix = "third-party.client") public record ClientProperties( URI baseUrl, Duration connectTimeout, Duration readTimeout ) {} @Configuration @EnableConfigurationProperties(ClientProperties.class) class ClientConfiguration { @Bean ThirdPartyClient thirdPartyClient(ClientProperties properties) { return new ThirdPartyClient( properties.baseUrl(), properties.connectTimeout(), properties.readTimeout() ); } }

```
@ConfigurationProperties(prefix = "third-party.client")
public record ClientProperties(
    URI baseUrl,
    Duration connectTimeout,
    Duration readTimeout
) {}

@Configuration
@EnableConfigurationProperties(ClientProperties.class)
class ClientConfiguration {

    @Bean
    ThirdPartyClient thirdPartyClient(ClientProperties properties) {
        return new ThirdPartyClient(
                properties.baseUrl(),
                properties.connectTimeout(),
                properties.readTimeout()
        );
    }
}
```

The wrapper approach is generally preferable because it avoids coupling your application configuration directly to the third-party library’s class structure.

## Fail fast, fail early: validate configuration during startup

Configuration errors should be detected on application startup and fail fast if a configuration is missing or invalid. Add `@Validated` to a `@ConfigurationProperties` bean and apply **Jakarta Bean Validation** constraints to its properties.

@Validated

@ConfigurationProperties(prefix = "app.promotion-service")

public record PromotionSvcProperties(

@NotBlank String baseUrl,

@NotNull Duration timeout,

@Min(1) @Max(5) int retries,

@NotNull @Valid SyncProperties sync) {

public record SyncProperties(@NotEmpty String cron) {

}

}

@Validated @ConfigurationProperties(prefix = "app.promotion-service") public record PromotionSvcProperties( @NotBlank String baseUrl, @NotNull Duration timeout, @Min(1) @Max(5) int retries, @NotNull @Valid SyncProperties sync) { public record SyncProperties(@NotEmpty String cron) { } }

```
@Validated
@ConfigurationProperties(prefix = "app.promotion-service")
public record PromotionSvcProperties(
 @NotBlank String baseUrl,
        @NotNull Duration timeout,
        @Min(1) @Max(5) int retries,
        @NotNull @Valid SyncProperties sync) {

    public record SyncProperties(@NotEmpty String cron) {
    }
}
```

With `spring-boot-starter-validation` on the classpath, binding or validation failures stop application startup. Validate required values, numeric ranges, nested groups, and other application-level constraints.

Use wrapper types when absence must be distinguished from a Java default. For example, an `Integer` annotated with `@NotNull` can identify a missing value, while an `int` defaults to 0.

## Understand property precedence

Spring Boot combines multiple property sources. When the same property appears in more than one source, the source with higher precedence supplies the effective value.

The following simplified order shows the sources most commonly used in application deployments, from lowest to highest precedence:

application.properties/yaml (low-precedence)

↓

profile-specific configuration files

↓

OS environment variables

↓

Java system properties

↓

command-line arguments (high-precedence)

application.properties/yaml (low-precedence) ↓ profile-specific configuration files ↓ OS environment variables ↓ Java system properties ↓ command-line arguments (high-precedence)

```
application.properties/yaml (low-precedence)
           ↓
profile-specific configuration files
           ↓
OS environment variables
           ↓
Java system properties
           ↓
command-line arguments    (high-precedence)
```

Spring Boot configuration loading precedence matters when troubleshooting a value that differs from the expected configuration value.

Environment variables are widely supported by operating systems, container runtimes, and cloud platforms. Spring Boot derives environment variable names from canonical property names by replacing dots with underscores, removing dashes, and converting the result to uppercase:

app.payment-timeout -> APP\_PAYMENT\_TIMEOUT

spring.datasource.url -> SPRING\_DATASOURCE\_URL

app.payment-timeout -> APP\_PAYMENT\_TIMEOUT spring.datasource.url -> SPRING\_DATASOURCE\_URL

```
app.payment-timeout     -> APP_PAYMENT_TIMEOUT
spring.datasource.url   -> SPRING_DATASOURCE_URL
```

Determining the effective value of a property can be challenging when it is defined in multiple configuration sources. IntelliJ IDEA can display resolved configuration values as editor inlay hints. Selecting a hint identifies the property source that supplies the value and indicates whether it is overridden by another source, such as an environment variable or a system property.

<video controls="" src="https://blog.jetbrains.com/wp-content/uploads/2026/08/effective-config-values.mp4"></video>

IntelliJ IDEA also provides navigation between property declarations, `@ConfigurationProperties` members, and property usages. For custom configuration properties, this support is enhanced by the metadata generated by `spring-boot-configuration-processor`.

<video controls="" src="https://blog.jetbrains.com/wp-content/uploads/2026/08/property-navigation.mp4"></video>

## Store secrets in a dedicated system

Do not store passwords, API keys, certificates, or private keys in source control. Use a system such as [HashiCorp Vault](https://www.hashicorp.com/en/products/vault), [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/), [Google Cloud Secret Manager](https://cloud.google.com/security/products/secret-manager), [Azure Key Vault](https://azure.microsoft.com/en-us/products/key-vault), or an equivalent platform service.

Ensure that secrets are excluded from logs, error messages, configuration metadata, and publicly accessible management endpoints.

**NOTE:** In non-production environments, the **Actuator** `env` endpoint can help identify the source of an effective property. It should not be exposed publicly because configuration may contain sensitive information.

There is no single configuration-management approach that works for every application. Choose a strategy based on the application’s architecture, deployment environment, and complexity.

### Monolith

For a monolithic application, keep shared defaults in the application, use profile-specific files only where necessary, and supply deployment-specific overrides through environment variables. Store sensitive values in a dedicated secret manager.

### Containerized workloads

For workloads running in a container platform such as Kubernetes, keep sensible defaults in the application and provide deployment-specific configuration through [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/). Store secrets separately in a dedicated secret-management system.

### Microservices

For a microservices architecture, consider [Spring Cloud Config Server](https://spring.io/projects/spring-cloud-config) to centralize configuration, governance, and versioning. Continue to manage secrets through a dedicated secret-management system.

## Summary

Effective application configuration starts with sensible defaults, type-safe `@ConfigurationProperties`, and startup validation. Keep environment-specific values outside the application, understand property-source precedence, and store secrets in a dedicated secret-management system.

The right configuration strategy should reflect the application’s architecture and deployment environment.

During local development and [debugging remotely](https://blog.jetbrains.com/idea/2026/01/spring-boot-debugging-now-remote/), IntelliJ IDEA helps reveal the effective configuration by showing resolved property values and their sources, highlighting overrides, and providing navigation between configuration files and bound Java properties.

[![](https://admin.blog.jetbrains.com/wp-content/uploads/2026/07/ij-conf-2026-970x250-2x.png)](https://lp.jetbrains.com/intellij-idea-conf-2026/?utm_source=blog_banner&utm_medium=idea&utm_campaign=intellijideaconf)
