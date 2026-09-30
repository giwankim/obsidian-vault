---
title: "Optimizing Spring Integration Tests at Scale"
source: "https://www.baeldung.com/spring-integration-test-optimize"
author:
  - "[[Sergey Chernov]]"
published: 2025-09-04
created: 2026-07-08
description: "Learn how the Spring Test framework works under the hood, why it can be slow and consume a lot of resources, and how to boost the performance."
tags:
  - "clippings"
---

> [!summary]
> Explains how the Spring Test framework caches application contexts using `MergedContextConfiguration` as the cache key, and why divergent test configurations (`@MockBean`, profiles, properties) spawn expensive duplicate contexts. Covers classic optimizations — a common test parent, reusable static TestContainers beans, lazy DataSource initialization, random ports — and their bad-practice counterparts. Finishes with the spring-test-smart-context library, which reorders test classes by context configuration and eagerly closes contexts so at most one is active at a time.

## 1\. Introduction

Spring Boot is a popular Java framework that provides a rich platform for integration testing. It’s pretty convenient and flexible; however, at a large scale, when the project has hundreds or even thousands of integration tests using lots of heavy components (like TestContainers-managed beans), there can be performance and other issues.

In this article, we’ll look at how the framework works under the hood, why it can be slow and consume a lot of resources, and how to boost the performance. **With knowledge of these details, you’ll be able to efficiently scale your test suites.**

## 2\. Spring Context Cache Explained

### 2.1. Definition of MergedContextConfiguration

Let’s take a look at a simple Spring Boot Integration test. It declares the configuration and can have a parent super-class, injected fields, and *@Test* methods.

The Spring Test framework reads test class signatures and decides whether to create a new Spring context or reuse an existing one from the cache. Let’s look at a few annotations that declare configurations, profiles, or properties:

```java
@ContextConfiguration(classes = {
    FeatureServiceIntTest.Configuration.class
})
@ActiveProfiles("test")
@TestPropertySource(properties = {
    "parameter = value"
})
public class FeatureServiceIntTest extends AbstractIntTest {
    @MockBean
    private FeatureRepository featureRepository;

    // ...
}
```

In total, Spring gathers around a dozen of such parameters from the test class and its super-classes and aggregates them to an object of *[org.springframework.test.context.MergedContextConfiguration](https://github.com/spring-projects/spring-framework/blob/main/spring-test/src/main/java/org/springframework/test/context/ContextConfiguration.java)* class:

- ***locations***, ***classes***, ***contextInitializerClasses***, ***contextLoader*** (from *@ContextConfiguration*)
- ***activeProfiles*** (from *@ActiveProfiles*)
- ***propertySourceDescriptors***, ***propertySourceLocations***, ***propertySourceProperties*** (from *@TestPropertySource*)
- ***contextCustomizers*** (from *@ContextCustomizerFactory*) – e.g. *@DynamicPropertySource*, *@MockBean/@MockitoBean* and *@SpyBean/@MockitoSpyBean*
- ***parent*** (for contexts with an inheritance hierarchy)

***MergedContextConfiguration* is a key for the Spring context cache.** It means that if all these fields are equal, the existing Spring context can be used. Otherwise, Spring creates a new context, puts it into a cache with this key, and uses it for the integration test.

### 2.2. Example of Test Suite Execution

Consider a test suite of eight test classes that have four different configurations (according to their *MergedContextConfiguration*). If we run these tests, eventually there will be four separate active Spring contexts, and each context is created on demand (*Test1IT*, *Test3IT*, *Test4IT,* and *Test5IT* create new context; *Test2IT*, *Test6IT,* and *Test8IT* reuse existing). The same color means the test class has an equal configuration:

[![tests default time diagram 1024x286](https://www.baeldung.com/wp-content/uploads/2025/08/tests_default_time_diagram-1024x286.png)](https://www.baeldung.com/wp-content/uploads/2025/08/tests_default_time_diagram.png)

Spring will close all these contexts on the JVM shutdown hook, but it can be too late, meaning that at this moment, a few things may already have happened:

- tests conflicting with each other on resources like fixed ports
- too many active contexts share too many heavy-weight Spring beans (like managed by TestContainers), leading to OOM or an overloaded Docker host

Also, **each context initialization can be quite long**. For a rich context that bootstraps a web application with databases and lots of components, the initialization time is usually way more than the test execution.

So far, we can have several intermediate conclusions:

- somehow limit the number of currently active Spring contexts
- to optimize tests, we need to reduce the number of unique context configurations
- increase the shared state to reduce the overhead of each subsequent context initialization
- after all, **can we revisit the standard behavior to have the maximum benefit of it**?

Let’s go through each of these points.

## 3\. Classic Optimizations

### 3.1. @DirtiesContext Annotation

The [*@DirtiesContext*](https://docs.spring.io/spring-framework/reference/testing/annotations/integration-spring/annotation-dirtiescontext.html) annotation closes the Spring context before/after the test method or test class. The purpose of this annotation is to avoid reusing a shared Spring context that was modified in a way that may be incompatible with other tests.

In the most radical scenario, when this annotation is added to a parent integration test class, we’ll have lots of reinitialization. While this may solve some test conflict problems, **it brings huge overhead in time**. The time diagram demonstrates how each subsequent test creates and closes the new context:

[![Dirties Context on parent class 1024x348](https://www.baeldung.com/wp-content/uploads/2025/08/DirtiesContext_on_parent_class-1024x348.png)](https://www.baeldung.com/wp-content/uploads/2025/08/DirtiesContext_on_parent_class.png)

### 3.2. Context Cache Size

The next point is the adjustment of the context cache size. By default, it’s *32* (which may be too high in case of heavy-weight beans) and can be adjusted to a smaller number. It’s possible to specify it via the property in the *spring.properties* file on the classpath:

```
spring.test.context.cache.maxSize=4
```

Or, this can be specified in the settings of the Maven or Gradle build:

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-failsafe-plugin</artifactId>
    <version>${maven-surefire.version}</version>
    <configuration>
        <argLine>-Dspring.test.context.cache.maxSize=1 ...</argLine>
    </configuration>
</plugin>
```

With a cache of size *1 (one),* the new time diagram will look like:

[![Context Cache size1-1024x283](https://www.baeldung.com/wp-content/uploads/2025/08/ContextCache_size1-1024x283.png)](https://www.baeldung.com/wp-content/uploads/2025/08/ContextCache_size1.png)

You can notice that when tests with the same context configuration are executed subsequently, one after another, the context is kept alive. This is already better than using the globally configured *@DirtiesContext* annotation.

Also, pay attention that there is a small overlay of active contexts (old context is closed only after the new one is created), which may be crucial if fixed server ports are used for tests, as we’ll further explain below.

### 3.3. Introduce Common Test Parent

One of the easiest ways to reduce the number of unique context configurations is to introduce a common integration test parent super-class. Add all needed configurations there.

Whenever possible, the subclasses should not declare additional configurations (including *@MockBean* and *@SpyBean* annotations), as these are also context configuration customizations, which lead to the creation of a separate Spring context:

[![common test parent 1024x735](https://www.baeldung.com/wp-content/uploads/2025/08/common_test_parent-1024x735.png)](https://www.baeldung.com/wp-content/uploads/2025/08/common_test_parent.png)

### 3.4. Properly Define @MockBean

Using *@MockBean* (replaced with *@MockitoBean* in the latest Spring releases) and *@SpyBean* (replaced with *@MockitoSpyBean*) is a pretty convenient and flexible approach to override behavior or define a missing bean in the context.

However, as already mentioned, it’s one of the so-called customizers (see definition of *MergedContextConfiguration* above). Whenever possible, try to locate *@MockBean* / *@SpyBean* declarations in the parent integration test classes or shared *@TestConfiguration* class.

### 3.5. Reusable Static Docker Container Bean

Instead of creating TestContainer-managed Docker containers as beans for each Spring context, use a specialized static bean declaration:

```java
@TestConfiguration
public class LocalStackS3TestConfiguration {
    private static LocalStackContainer localStackS3;

    // override destroy method to empty to avoid closing docker container
    // bean on closing Spring context
    @Bean(destroyMethod = "")
    public LocalStackContainer localStackS3Container() {
        synchronized (LocalStackS3TestConfiguration.class) {
            if (localStackS3 == null) {
                localStackS3 = new LocalStackContainer(DockerImageName.parse("localstack/localstack:4.6.0"))
                        .withServices(LocalStackContainer.Service.S3);
                localStackS3.start();
            }
            return localStackS3;
        }
    }
}
```

Note that the *destroyMethod* annotation parameter should be overridden to avoid closing it on context close.

### 3.6. Lazy Initialization of Database Containers

If an application has a single database, it’s not that critical. But if there are several *DataSource* s accessing different schemas, **it makes sense to start database containers only on demand (lazily)**. As in many tests, these initializations will be simply redundant (rare integration tests are using all possible *DataSource* s). Technically, it can be implemented this way:

- don’t start the TestContainers *Container* object immediately
- create a wrapping *DataSource* object that will start the underlying container on the very first *getConnection()* call

We can base our implementation on Spring *[DelegatingDataSource](https://github.com/spring-projects/spring-framework/blob/main/spring-jdbc/src/main/java/org/springframework/jdbc/datasource/DelegatingDataSource.java)* (it should also be *Closeable* to delegate bean shutdown):

```java
public class LateInitDataSource extends DelegatingDataSource implements Closeable {
    private final Supplier<DataSource> dataSourceSupplier;

    public LateInitDataSource(Supplier<DataSource> dataSourceSupplier) {
        // SingletonSupplier: call dataSourceSupplier.get() not more than once
        this.dataSourceSupplier = SingletonSupplier.of(() -> {
            DataSource dataSource = dataSourceSupplier.get();
            setTargetDataSource(dataSource);
            return dataSource;
        });
    }

    @Override
    public void afterPropertiesSet() {
        // no op to skip getTargetDataSource setup
    }

    @Override
    protected DataSource obtainTargetDataSource() {
        return dataSourceSupplier.get();
    }

    @Override
    public void close() throws IOException {
        DataSource targetDataSource = getTargetDataSource();
        if (targetDataSource instanceof AutoCloseable) {
            try {
                ((AutoCloseable) targetDataSource).close();
            } catch (IOException e) {
                throw e;
            } catch (Exception e) {
                throw new IOException("Error while closing targetDataSource", e);
            }
        }
    }

    @Override
    public String toString() {
        return "LateInitDataSource{" + ", delegate=" + getTargetDataSource() + '}';
    }
}
```

Then, we also need to declare the *DataSource* beans:

```java
@Bean
public DataSource dataSource(PostgreSQLContainer<?> container) {
    // lazy late initialization
    return new LateInitDataSource(() -> {
        LOGGER.info("Late initialization data source docker container {}", container);
        // start only on demand
        container.start();
        return createHikariDataSourceForContainer(container);
    });
}
```

### 3.7. Bad Practice: Fixed Ports

Using fixed port numbers (as we usually configure in production) is convenient for integration testing; however, it limits possible parallelization of test execution. For example, it prevents multiple test classes in the same module or in multiple modules from being executed simultaneously. We can observe test server initialization issues like:

```
Caused by: java.io.IOException: Failed to bind to address 0.0.0.0/0.0.0.0:8080 (address already in use)
```

Instead of configuring fixed ports for HTTP, GRPC, and TestContainer ports:

```java
@SpringBootTest(webEnvironment = WebEnvironment.DEFINED_PORT)
```

Prefer using *WebEnvironment.RANDOM\_PORT*:

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
// will inject actual dynamic port
@LocalServerPort
private int port;
```

For the case of manual Server Socket initialization, use server socket port *0* (zero); it will auto-assign a random available server port. Configure the test clients accordingly.

### 3.8. Bad Practice: Container Is Not a @Bean

The Docker container managed by TestContainers should have lifecycle management by Spring. Avoid declarations like:

```java
@TestConfiguration
public class DockerDataSourceTestConfiguration {
    @Bean
    public DataSource dataSource() {
        // not a manageable bean!
        var container = new PostgreSQLContainer("postgres:9.6");
        container.start();
        return createDataSource(container);
    }

    private static DataSource createDataSource(JdbcDatabaseContainer container) {
        var hikariDataSource = new HikariDataSource();
        hikariDataSouce.setJdbcUrl(container.getJdbcUrl());
        ...
        return hikariDataSource;
    }
}
```

Instead, declare the *Container* as a bean and inject it as a *DataSource* creation parameter:

```java
@TestConfiguration
public class DockerDataSourceTestConfiguration {
    // will be terminated with Spring context
    @Bean(initMethod = "start")
    public PostgreSQLContainer postgreSQLContainer() {
        return new PostgreSQLContainer("postgres:9.6");
    }

    @Bean
    public DataSource dataSource(PostgreSQLContainer postgreSQLContainer) {
        return createDataSource(postgreSQLContainer);
    }

    // ...
}
```

### 3.9. Bad Practice: ExecutorService Is Not Properly Shut Down

There is a similar situation with *ExecutorService* created during class initialization. It should be properly managed; otherwise, eventually, the runtime can have lots of active threads that complicate test failure analysis, increase the resource consumption, and may lead to confusing failure messages in test execution logs for failing scheduled tasks in such executors that are still active. To address the problem, add missing *@PreDestroy* methods:

```java
@Service
public class DefaultScheduler {
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(16);

    public void scheduleNow(Runnable command, long periodSeconds) {
        scheduler.scheduleAtFixedRate(command, 0L, periodSeconds, TimeUnit.SECONDS);
    }

    // to avoid thread leakage in test execution
    @PreDestroy
    public void shutdown() {
        scheduler.shutdown();
    }
}
```

This simple approach will also have a positive effect on a proper application shutdown.

## 4\. Let’s Revisit Standard Test Execution Behavior

It’s possible to maximize the optimization of resource consumption during test execution. When the test engine starts the suite, we already know the list of test classes. This way, we can predict the exact moment when the Spring context stops being used and eagerly close it:

[![auto close context](https://www.baeldung.com/wp-content/uploads/2025/08/auto-close_context.png)](https://www.baeldung.com/wp-content/uploads/2025/08/auto-close_context.png)

On the time diagram, we can see that the same context is used for *Test1IT*, *Test2IT,* and *Test7IT*. It means that after *Test7IT,* we can terminate the context, releasing all resources. The same goes for *Test3IT*, *Test4IT* and *Test8IT*.

Let’s mix it with the second optimization — reorder test execution to sequentially execute tests that share the same context:

[![auto close and reorder](https://www.baeldung.com/wp-content/uploads/2025/08/auto-close_and_reorder.png)](https://www.baeldung.com/wp-content/uploads/2025/08/auto-close_and_reorder.png)

Now, at any moment in time, we have no more than one active Spring context. This way, the test suite needs the minimal possible amount of resources (like CPU and memory). This will also reduce the load on the Docker environment that manages TestContainer Spring beans.

To support this behavior, we have to implement:

- suite test classes reordering
- auto-closing of the Spring context

Spring Framework cannot control the test class order; it’s a responsibility of the test engine (like TestNG or JUnit). JUnit 5 supports test reordering via a specialized listener *[org.junit.jupiter.api.ClassOrderer](https://docs.junit.org/5.8.1/api/org.junit.jupiter.api/org/junit/jupiter/api/ClassOrderer.html)*. The implementation of such a reordering listener is a part of the *[spring-test-smart-context](https://github.com/seregamorph/spring-test-smart-context/blob/master/spring-test-smart-context/src/main/java/com/github/seregamorph/testsmartcontext/jupiter/SmartDirtiesClassOrderer.java)* project.

The class implementing the *ClassOrderer* should be in the classpath of the module with tests so that it will be auto-discovered via *[junit-platform.properties](https://github.com/seregamorph/spring-test-smart-context/blob/master/spring-test-smart-context/src/main/resources/junit-platform.properties)*. The ordering logic is based on the calculated *MergedContextConfiguration* object of the test class.

To auto-close the Spring context, use *[SmartDirtiesContextTestExecutionListener](https://github.com/seregamorph/spring-test-smart-context/blob/master/spring-test-smart-context/src/main/java/com/github/seregamorph/testsmartcontext/SmartDirtiesContextTestExecutionListener.java)* or base your implementation on it.

### 4.1. Easy-to-Use Solution

Such logic can be implemented in the project, but it’s easier to use a simple plug-in library that will be auto-discovered via the classpath. There are three simple steps.

First, we need to add a [library](https://github.com/seregamorph/spring-test-smart-context) to the test classpath:

```xml
<dependency>
    <groupId>com.github.seregamorph</groupId>
    <artifactId>spring-test-smart-context</artifactId>
    <version>0.14</version>
    <scope>test</scope>
</dependency>
```

Or for Gradle, we add:

```groovy
testImplementation("com.github.seregamorph:spring-test-smart-context:0.14")
```

Then, remove from tests (especially parent test classes) the *@DirtiesContext* annotations if it was used, or replace al uses of it with declarations:

```java
@TestExecutionListeners(listeners = {
    SmartDirtiesContextTestExecutionListener.class,
})
```

Optionally, enable *INFO* logging for *com.github.seregamorph.testsmartcontext* logger to see more details.

Sample log output during test execution can look like:

[![spring test smart context log 1024x364](https://www.baeldung.com/wp-content/uploads/2025/08/spring-test-smart-context-log-1024x364.png)](https://www.baeldung.com/wp-content/uploads/2025/08/spring-test-smart-context-log.png)

There, we can see the estimated number of tests to execute and how many unique configurations they use, and we can understand how Spring reuses existing context between different tests.

### 4.2. Implicit Benefits

Besides all the described advantages of using smart test ordering and context closing, there are a few more. When the test engine executes all tests in a single thread, closing all allocated resources on context close, it’s way easier to inspect JVM monitoring to analyze heap and thread leakages:

[![heap and thread leakage](https://www.baeldung.com/wp-content/uploads/2025/08/heap_thread_leakage.png)](https://www.baeldung.com/wp-content/uploads/2025/08/heap_thread_leakage.png)

As we can see here, the chart of active thread numbers has drops – these are Spring context closings. But there is an obvious ascending trend in the number of threads, which signals the thread leakages. A similar heap dump chart may also highlight if we’ve missed closing allocated resources properly.

## 5\. Conclusion

Inspecting and optimizing Spring integration tests can significantly reduce the amount of required resources, such as CPU and memory, and it may stabilize test execution. Also, with fewer resources allocated, the **test execution will always be faster**. There’s a simple explanation for this: The system will not lose resources on redundant Docker container management, thread pools, and so on.

Addressing such problems with integration tests can also enhance the proper graceful shutdown cycle of the application, making deployments more seamless.

In rare cases, it can even help to find leakages affecting production code!

The code backing this article is available on GitHub. Once you're **logged in as a [Baeldung Pro Member](https://www.baeldung.com/members/)**, start learning and coding on the project.
