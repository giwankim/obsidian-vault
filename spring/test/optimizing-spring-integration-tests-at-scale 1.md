---
title: "Optimizing Spring Integration Tests at Scale"
source: "https://javapro.io/2025/12/17/optimizing-spring-integration-tests-at-scale/"
author:
  - "[[Sergei Chernov]]"
published: 2025-12-17
created: 2026-09-30
description: "Sprint Boot provides rich platform for integration testing. At a big scale there can be specific performance issues that need to be solved"
tags:
  - "clippings"
---

> [!summary]
> Spring's test context cache is keyed on `MergedContextConfiguration`, so every distinct mix of configuration classes, profiles, properties, and `@MockBean`/`@SpyBean` customizers boots another heavyweight context, and the default cache size of 32 can keep many TestContainers-backed contexts alive at once. Sergei Chernov walks through the classic fixes: a smaller `spring.test.context.cache.maxSize`, a shared test parent, static reusable containers, lazily started DataSources, random ports, and containers and executors managed as proper beans. He then introduces his spring-test-smart-context library, which reorders JUnit 5 test classes by context configuration and closes each context after its last test, so at most one context is active at a time.

## 1\. Introduction

Sprint Boot is a popular Java framework that provides a rich platform for integration testing. It’s pretty convenient and flexible; however, at a large scale, when the project has hundreds or even thousands of integration tests using lots of heavy components (like TestContainers-managed beans), there can be performance and other issues. **There are many hidden details that make much sense when the codebase becomes bigger and the configuration becomes more complicated.** In this article, we’ll look at how the framework works under the hood, why it can be slow and inefficient, and how to boost the performance.

## 2\. Spring Context Cache Explained

Let’s take a look at a simple Spring Boot Integration test. It declares the configuration, can have a parent super-class, injected fields, and *@Test* methods.

The spring-test framework decides if a new spring context should be created or an existing one cached can be reused based on test class signatures. E.g., these annotations that declare configurations, profiles, or properties:

```java
@ContextConfiguration(classes = {
    FeatureServiceIntTest.Configuration.class
})
@ActiveProfiles("test")
@TestPropertySource(properties = {
    "parameter = value"
})
publicclassFeatureServiceIntTest extendsAbstractIntTest {
    @MockBean
    privateFeatureRepository featureRepository;
...
```

In total, there are around 10 such parameters gathered from the test class and its super-classes aggregated to an object of [org.springframework.test.context.MergedContextConfiguration](https://github.com/spring-projects/spring-framework/blob/main/spring-test/src/main/java/org/springframework/test/context/ContextConfiguration.java) class:

- ***locations***, ***classes***, ***contextInitializerClasses***, ***contextLoader*** (from *@ContextConfiguration*)
- ***activeProfiles*** (from *@ActiveProfiles*)
- ***propertySourceDescriptors***, ***propertySourceLocations***, ***propertySourceProperties*** (from *@TestPropertySource*)
- ***contextCustomizers*** (from *@ContextCustomizerFactory*) – e.g. *@DynamicPropertySource*, *@MockBean/@MockitoBean* and *@SpyBean/@MockitoSpyBean*
- ***parent*** (for contexts with an inheritance hierarchy)

***MergedContextConfiguration* is a key for the Spring context cache.** It means that if all these fields are equal, the existing spring context can be used. Otherwise, Spring creates a new context, puts it into a cache with this key, and uses it for the integration test.

Consider a test suite of 8 test classes that have 4 different configurations (according to their *MergedContextConfiguration*). If we run these tests, eventually there will be 4 separate active spring contexts, each context is created on demand (*Test1IT*, *Test3IT*, *Test4IT,* and *Test5IT* create new context; *Test2IT*, *Test6IT,* and *Test8IT* reuse existing). The same color means the test class has an equal configuration:

![](https://javapro.io/wp-content/uploads/2026/01/01.png)

This article is part of the JAVAPRO magazine issue: Agentic AI Meets Java Explore how agentic AI introduces new opportunities and challenges for Java development — from conceptual shifts to practical learnings. Discover the edition →

All these spring contexts will be closed on the JVM shutdown hook, but it can be too late. Too late means that at this moment few things may already have happened:

- tests conflicting with each other on resources like fixed ports
- too many active contexts share too many heavy-weight spring beans (like managed by TestContainers), leading to OOM or an overloaded Docker host

Also, **each context initialization can be quite long**. For a rich context that bootstraps a web application with databases and lots of components, the initialization time is usually way more than the test execution.

So far, we can have several intermediate conclusions:

- somehow limit the number of currently active spring contexts
- to optimize tests, we need to reduce the number of unique context configurations
- increase the shared state to reduce the overhead of each subsequent context initialization
- after all, **can we revisit the standard behavior to have the maximum benefit of it**?

Let’s go through each of these points.

## 3\. Classic Optimizations

### 3.1. @DirtiesContext Annotation

There is a *@DirtiesContext* annotation, which closes the Spring context before/after the test method or test class. The purpose of this annotation is to avoid reusing a shared spring context that was modified in a way that may be incompatible with other tests. In the most radical scenario, when this annotation is added to a parent integration test class, we’ll have lots of reinitialization. While this may solve some test conflict problems, **it brings huge overhead in time**. The time diagram demonstrates how each subsequent test creates and closes the new context:

![](https://javapro.io/wp-content/uploads/2026/01/02.png)

This article is part of the JAVAPRO magazine issue: Agentic AI Meets Java Explore how agentic AI introduces new opportunities and challenges for Java development — from conceptual shifts to practical learnings. Discover the edition →

### 3.2. Context Cache Size

The next point is the adjustment of the context cache size. By default, it’s 32 (which may be too high in case of heavy-weight beans) and can be adjusted to a smaller number. It’s possible to specify it via the property in the *spring.properties* file on the classpath:

```
spring.test.context.cache.maxSize=4
```

Or this can be specified in the settings of the Maven or Gradle build:

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

With a cache of size *1,* the new time diagram will look like this:

![](https://javapro.io/wp-content/uploads/2026/01/03.png)

This article is part of the JAVAPRO magazine issue: Agentic AI Meets Java Explore how agentic AI introduces new opportunities and challenges for Java development — from conceptual shifts to practical learnings. Discover the edition →

You can notice that when tests with the same context configuration are executed subsequently, one after another, the context is kept alive. This is already better than using the globally configured *@DirtiesContext* annotation. Also, pay attention that there is a small overlay of active contexts (old context is closed only after the new one is created), this may be crucial if fixed server ports are used for tests (this point is explained below).

### 3.3. Introduce Common Test Parent

One of the easiest ways to reduce the number of unique context configurations is to introduce a common integration test parent super-class. Add all needed configurations there. The subclasses should not declare additional configurations whenever possible (including *@MockBean* and *@SpyBean* annotations), as these are also context configuration customizations, which lead to the creation of a separate spring context:

![](https://javapro.io/wp-content/uploads/2026/01/04.png)

This article is part of the JAVAPRO magazine issue: Agentic AI Meets Java Explore how agentic AI introduces new opportunities and challenges for Java development — from conceptual shifts to practical learnings. Discover the edition →

For JUnit 5 tests, instead of introducing the base super-class, the meta-annotation can also be used – add all configurations there, and Spring will transitively use it.

### 3.4. Properly Define @MockBean

Using *@MockBean* (replaced with *@MockitoBean* in the latest Spring releases) and *@SpyBean* (replaced with *@MockitoSpyBean*) is a pretty convenient and flexible approach to override behavior or define a missing bean in the context. However, as already mentioned, it’s one of the so-called customizers (see definition of *MergedContextConfiguration* above). Whenever possible, try to locate *@MockBean* / *@SpyBean* declarations in the parent integration test classes or shared *@TestConfiguration* class.

### 3.5. Reusable Static Docker Container Bean

Instead of creating TestContainer-managed Docker containers as beans for each Spring context, the static single container may be used. Use a specialized static bean declaration:

```java
@TestConfiguration
publicclassLocalStackS3TestConfiguration {

    privatestaticLocalStackContainer localStackS3;

    // override destroy method to empty to avoid closing docker container
    // bean on closing spring context
    @Bean(destroyMethod = "")
    publicLocalStackContainer localStackS3Container() {
        synchronized(LocalStackS3TestConfiguration.class) {
            if(localStackS3 == null) {
                localStackS3 = newLocalStackContainer(DockerImageName.parse("localstack/localstack:4.6.0"))
                        .withServices(LocalStackContainer.Service.S3);
                localStackS3.start();
            }
            returnlocalStackS3;
        }
    }
}
```

Note that it’s required to override the *destroyMethod* annotation parameter to avoid closing it on context close.

### 3.6. Lazy Initialization of Database Containers

If an application has a single database, it’s not that critical. But if there are several *DataSource* s accessing different schemas, **it makes sense to start database containers only on demand (lazily)**. As in many tests, these initializations will be simply redundant (rare integration tests are using all possible DataSources). Technically, it can be implemented this way:

- created TestContainers Container object is not started immediately
- create a wrapping DataSource object that will start the underlying container on the very first getConnection call

We can base our implementation on Spring [DelegatingDataSource](https://github.com/spring-projects/spring-framework/blob/main/spring-jdbc/src/main/java/org/springframework/jdbc/datasource/DelegatingDataSource.java) (it should also be Closeable to delegate bean shutdown):

```java
publicclassLateInitDataSource extendsDelegatingDataSource implementsCloseable {
    privatefinalSupplier<DataSource> dataSourceSupplier;

    publicLateInitDataSource(Supplier<DataSource> dataSourceSupplier) {
        // SingletonSupplier: call dataSourceSupplier.get() not more than once
        this.dataSourceSupplier = SingletonSupplier.of(() -> {
            DataSource dataSource = dataSourceSupplier.get();
            setTargetDataSource(dataSource);
            returndataSource;
        });
    }

    @Override
    publicvoidafterPropertiesSet() {
        // no op to skip getTargetDataSource setup
    }

    @Override
    protectedDataSource obtainTargetDataSource() {
        returndataSourceSupplier.get();
    }

    @Override
    publicvoidclose() throwsIOException {
        DataSource targetDataSource = getTargetDataSource();
        if(targetDataSource instanceofAutoCloseable) {
            try{
                ((AutoCloseable) targetDataSource).close();
            } catch(IOException e) {
                throwe;
            } catch(Exception e) {
                thrownewIOException("Error while closing targetDataSource", e);
            }
        }
    }

    @Override
    publicString toString() {
        return"LateInitDataSource{"+ ", delegate="+ getTargetDataSource() + '}';
    }
}
```

and then declare the *DataSource* beans:

```java
@Bean
publicDataSource dataSource(PostgreSQLContainer<?> container) {
    // lazy late initialization
    returnnewLateInitDataSource(() -> {
        LOGGER.info("Late initialization data source docker container {}", container);
        // start only on demand
        container.start();
        returncreateHikariDataSourceForContainer(container);
    });
}
```

### 3.7. Bad practice: fixed ports

Using fixed port numbers (as we usually configure in production) is convenient for integration testing; however, it limits possible parallelization of test execution. It’s about both test classes in the same module or in multiple modules that are executed simultaneously. We can observe test server initialization issues like:

```
Caused by: java.io.IOException: Failed to bind to address
0.0.0.0/0.0.0.0:8080 (address already in use)
```

Instead of configuring fixed ports for HTTP, GRPC, and TestContainer ports, the dynamic port should be used. Avoid declarations like this in spring-boot tests:

```java
@SpringBootTest(webEnvironment = WebEnvironment.DEFINED_PORT)
```

but prefer *WebEnvironment.RANDOM\_PORT*:

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
// will inject actual dynamic port
@LocalServerPort
privateintport;
```

In case the server socket is initialized manually, use server socket port *0* (zero); it will auto-assign a random available server port. Configure the test clients accordingly.

### 3.8. Bad Practice: Container is not a @Bean

The Docker container managed by TestContainers should have lifecycle management by Spring. Avoid declarations like:

```java
@TestConfiguration
publicclassDockerDataSourceTestConfiguration {

    @Bean
    publicDataSource dataSource() {
        // container is not a manageable bean!
        var container = newPostgreSQLContainer("postgres:9.6");
        container.start();
        returncreateDataSource(container);
    }

    privatestaticDataSource createDataSource(JdbcDatabaseContainer container) {
        var hikariDataSource = newHikariDataSource();
        hikariDataSouce.setJdbcUrl(container.getJdbcUrl());
        ...
        returnhikariDataSource;
    }
}
```

Instead, declare the Container as a bean and inject it as a DataSource creation parameter:

```java
@TestConfiguration
publicclassDockerDataSourceTestConfiguration {

    // will be terminated with Spring context
    @Bean(initMethod = "start")
    publicPostgreSQLContainer postgreSQLContainer() {
        returnnewPostgreSQLContainer("postgres:9.6");
    }

    @Bean
    publicDataSource dataSource(PostgreSQLContainer postgreSQLContainer) {
        returncreateDataSource(postgreSQLContainer);
    }
...
}
```

### 3.9. Bad Practice: ExecutorService is not Properly Shut Down

There is a similar situation with *ExecutorService* created during class initialization. If it’s not properly managed, eventually the runtime can have lots of active threads that complicate test failure analysis, increase the resource consumption, and may lead to confusing failure messages in test execution logs for failing scheduled tasks in such executors that are still active. Add missing *@PreDestroy* methods:

```java
@Service
publicclassDefaultScheduler {

    privatefinalScheduledExecutorService scheduler = Executors.newScheduledThreadPool(16);

    publicvoidscheduleNow(Runnable command, longperiodSeconds) {
        scheduler.scheduleAtFixedRate(command, 0L, periodSeconds, TimeUnit.SECONDS);
    }

    // to avoid thread leakage in test execution
    @PreDestroy
    publicvoidshutdown() {
        scheduler.shutdown();
    }
}
```

This simple approach will also have a positive effect on a proper application shutdown.

## 4\. Let’s Revisit Standard Test Execution Behavior

It’s possible to maximize the optimization of resource consumption during test execution. Before the suite is started, the list of test classes is known, hence it’s possible to predict at which moment the spring context is not used anymore, hence can be eagerly closed:

![](https://javapro.io/wp-content/uploads/2026/01/05.png)

This article is part of the JAVAPRO magazine issue: Agentic AI Meets Java Explore how agentic AI introduces new opportunities and challenges for Java development — from conceptual shifts to practical learnings. Discover the edition →

On the time diagram, we can see that the same context is used for *Test1IT*, *Test2IT,* and *Test7IT*. It means that after *Test7IT,* the context can be terminated, releasing all resources. Similar for *Test3IT*, *Test4IT* and *Test8IT*.

Let’s mix it with the second optimization: reorder test execution to sequentially execute tests that share the same context:

![](https://javapro.io/wp-content/uploads/2026/01/06.png)

This article is part of the JAVAPRO magazine issue: Agentic AI Meets Java Explore how agentic AI introduces new opportunities and challenges for Java development — from conceptual shifts to practical learnings. Discover the edition →

Now, at any moment in time, we have no more than 1 active spring context. This way test suite needs the minimal possible amount of resources (like CPU and memory). This will also reduce the load on the Docker environment that manages TestContainer Spring beans.

To support this behavior, we have to implement:

- suite test classes reordering
- auto-closing of the Spring context

Spring framework cannot control the test class order; it’s a responsibility of the test engine (like TestNG or JUnit). JUnit 5 supports test reordering via a specialized listener [org.junit.jupiter.api.ClassOrderer](https://docs.junit.org/5.8.1/api/org.junit.jupiter.api/org/junit/jupiter/api/ClassOrderer.html). The implementation of such a reordering listener can be found in the [spring-test-smart-context](https://github.com/seregamorph/spring-test-smart-context/blob/master/spring-test-smart-context/src/main/java/com/github/seregamorph/testsmartcontext/jupiter/SmartDirtiesClassOrderer.java) project. The class implementing the *ClassOrderer* should be in the classpath of the module with tests, so it will be auto-discovered via [junit-platform.properties](https://github.com/seregamorph/spring-test-smart-context/blob/master/spring-test-smart-context/src/main/resources/junit-platform.properties). The ordering logic is based on the calculated *MergedContextConfiguration* object of the test class.

To auto-close the Spring context, this simple [SmartDirtiesContextTestExecutionListener](https://github.com/seregamorph/spring-test-smart-context/blob/master/spring-test-smart-context/src/main/java/com/github/seregamorph/testsmartcontext/SmartDirtiesContextTestExecutionListener.java) is used; it’s also a part of the spring-test-smart-context project.

### 4.1. Easy-to-use solution

Such logic can be implemented in the project, but it’s easier to use a simple plug-in library that will be auto-discovered via the classpath. There are three simple steps.

1\. Add a [library](https://github.com/seregamorph/spring-test-smart-context) to the test classpath:

```xml
<dependency>
    <groupId>com.github.seregamorph</groupId>
    <artifactId>spring-test-smart-context</artifactId>
    <version>0.14</version>
    <scope>test</scope>
</dependency>
```

or for Gradle:

```groovy
testImplementation("com.github.seregamorph:spring-test-smart-context:0.14")
```

2\. Remove from tests (especially parent test classes) the *@DirtiesContext* annotations if it was used, or replace them with declarations:

```java
@TestExecutionListeners(listeners = {
    SmartDirtiesContextTestExecutionListener.class
})
```

3\. Optionally enable *INFO* logging for *com.github.seregamorph.testsmartcontext* logger to see more details

Sample log output during test execution can look like

![](https://javapro.io/wp-content/uploads/2026/01/07.png)

This article is part of the JAVAPRO magazine issue: Agentic AI Meets Java Explore how agentic AI introduces new opportunities and challenges for Java development — from conceptual shifts to practical learnings. Discover the edition →

There, we can see the estimated number of tests to execute, how many unique configurations they use, and understand how the existing context is reused between different tests.

### 4.2. Implicit benefits

Besides all the described advantages of using smart test ordering and context closing, there are a few more. All tests are executed in a single thread, closing all allocated resources on context close, so now it’s way easier to inspect JVM monitoring to analyze heap and thread leakages:

![](https://javapro.io/wp-content/uploads/2026/01/08.png)

This article is part of the JAVAPRO magazine issue: Agentic AI Meets Java Explore how agentic AI introduces new opportunities and challenges for Java development — from conceptual shifts to practical learnings. Discover the edition →

As you may notice, the chart of active thread numbers has drops – these are Spring context closing. But there is an obvious ascending trend in the number of threads, which signals the thread leakages. A similar heap dump chart, which may also highlight missing closing allocated resources properly.

## 5\. Conclusions

Inspecting and optimizing Spring integration tests can significantly reduce the amount of resources, such as CPU and memory. It may stabilize test execution. Also, with fewer resources allocated, the **test execution will always be faster**. There is a simple explanation: the system will not lose resources on redundant Docker container management, thread pools, etc.

Addressing such problems with integration tests can also enhance the proper graceful shutdown cycle of the application, making deployments more seamless.

In rare cases, it can even help to find leakages affecting production code!

## 6\. Code samples

The [spring-test-smart-context](https://github.com/seregamorph/spring-test-smart-context) library and code samples are available [over on GitHub](https://github.com/seregamorph/spring-test-smart-context/tree/master/demo).

![](https://javapro.io/wp-content/uploads/2025/04/Cover_2026-01.png)

This article is part of the JAVAPRO magazine issue: Agentic AI Meets Java Explore how agentic AI introduces new opportunities and challenges for Java development — from conceptual shifts to practical learnings. Discover the edition →

**This article is part of the JAVAPRO magazine issue:**

***Agentic AI Meets Java***

Explore how agentic AI introduces new opportunities and challenges for Java development — from conceptual shifts to practical learnings.

Discover the edition [→](https://javapro.io/2026/01/30/01-2026-agentic-ai-meets-java/)
