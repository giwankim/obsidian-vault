---
title: "Spring Boot Integration Testing with Testcontainers"
source: "https://alexanderobregon.substack.com/p/spring-boot-integration-testing-with?utm_source=substack&utm_medium=email"
author:
  - "[[Alexander Obregon]]"
published: 2026-09-30
created: 2026-10-05
description: "Unit tests are great for checking individual classes, but database behavior can be harder to test through mocks alone."
tags:
  - "clippings"
---

> [!summary]
> Walks through running Spring Boot 4 integration tests against a real, temporary PostgreSQL container instead of mocks or H2, which can diverge on SQL syntax, data types, and vendor features. It covers the Testcontainers 2 dependencies (`testcontainers-postgresql` and the relocated `org.testcontainers.postgresql.PostgreSQLContainer`) and declares the container as a `@TestConfiguration` bean with `@ServiceConnection` so Spring Boot wires the `DataSource` without manual properties. It then tests a repository with `@DataJpaTest` and a service with `@SpringBootTest`, noting that a service-connection database is not swapped for an embedded one under the default `NON_TEST` replacement mode.

Unit tests are great for checking individual classes, but database behavior can be harder to test through mocks alone. An in-memory database can help, but PostgreSQL, MySQL, MongoDB, and other databases can behave differently from the database the application runs against outside the test suite. Testcontainers lets integration tests start temporary containerized databases for the duration of the test run, then remove them when testing finishes. Spring Boot can connect supported containers through `@ServiceConnection`, letting repository and service tests run against the same database technology the application depends on without keeping a dedicated test database running.

### Building the Test Environment

Integration testing gets more valuable when the database involved in the test behaves like the database the application depends on outside the test suite. Testcontainers fills that gap by starting short-lived services inside containers for the duration of testing, which gives Spring Boot a database it can connect to rather than a mocked repository or an unrelated in-memory engine. The container can come from a normal database image, receive temporary connection details, and disappear after testing finishes. That keeps database-dependent tests self-contained while still exercising behavior that mocks cannot reproduce.

#### Why Containers Belong in Integration Tests

Mocks are good for checking logic inside a class because they let us control what a dependency returns. Repository behavior goes further than that. JPA mappings, generated SQL, database constraints, column types, indexes, native queries, transactions, and vendor-specific SQL all depend on the database engine receiving the request. Replacing that database with a mock removes those pieces from the test completely.

An in-memory database goes a step further because it executes SQL and stores rows, so it can help with fast database-related tests. The limitation comes from differences between database engines. H2, PostgreSQL, and MySQL do not behave identically, and the differences can show up in SQL syntax, data types, identity generation, JSON support, locking rules, indexes, and built-in functions. Passing a test against an in-memory database confirms behavior against that engine, not automatically against the database chosen for the application.

PostgreSQL-specific SQL gives us a good example of where that distinction becomes relevant:

```markup
SELECT id, metadata ->> 'author' AS author
FROM books
WHERE title ILIKE '%spring%';
```

The `->>` operator reads a JSON value as text, while `ILIKE` performs case-insensitive matching in PostgreSQL. If our repository depends on SQL like this, testing it against PostgreSQL gives us feedback from the same database technology that will process the query later. An in-memory database could reject the syntax, interpret it differently, or lack the same feature entirely.

Testcontainers handles this by starting the requested database image inside a container. Our test still communicates through the normal database driver and Spring data access stack, while the database process exists only for the testing lifecycle. Depending on the container lifecycle we choose later, the same container can remain available across a Spring test context before it is stopped. Host ports are assigned dynamically rather than forcing every PostgreSQL test to claim port `5432`. That helps when PostgreSQL is already running locally and also prevents multiple test environments from competing for the same host port. Testcontainers keeps track of the assigned port and connection information, so our test configuration can receive the actual address instead of assuming a fixed value.

The first test run can download the requested container image if it is not already stored locally. Later runs can start from the locally available image, which avoids downloading it every time. Testcontainers still needs access to a supported container runtime, so the developer machine or CI runner must provide an environment where the requested containers can start.

Containers do not replace unit tests. Logic that has no dependency on database behavior can still be tested quickly with normal objects or mocks. Container-backed integration tests become more relevant around repository mappings, custom queries, schema migrations, transaction behavior, database constraints, and service methods whose behavior depends heavily on persisted data.

Spring Boot adds service connection support on top of Testcontainers. When we mark a supported container with `@ServiceConnection`, Spring Boot can create connection details for that service and pass them into the matching auto-configuration. This removes the need to manually copy a generated host, mapped port, username, or password into test properties. The actual container declaration comes later, but the important idea at this stage is that Spring Boot can receive those temporary connection details through its normal test configuration.

#### Add the Test Dependencies

Before PostgreSQL can become part of the test suite, the project needs dependencies for normal database access and dependencies that exist only during testing. The application still needs Spring Data JPA and the PostgreSQL JDBC driver, while the test classpath gets Spring Boot JPA testing support, Spring Boot Testcontainers integration, and the PostgreSQL Testcontainers module.

With Maven and Spring Boot dependency management in place, individual version numbers can stay out of these dependency declarations:

```markup
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>

    <dependency>
        <groupId>org.postgresql</groupId>
        <artifactId>postgresql</artifactId>
        <scope>runtime</scope>
    </dependency>

    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa-test</artifactId>
        <scope>test</scope>
    </dependency>

    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-testcontainers</artifactId>
        <scope>test</scope>
    </dependency>

    <dependency>
        <groupId>org.testcontainers</groupId>
        <artifactId>testcontainers-postgresql</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>
```

`spring-boot-starter-data-jpa` provides Spring Data JPA and Hibernate for the application. The PostgreSQL dependency supplies the JDBC driver that allows Java code to communicate with PostgreSQL. Testcontainers does not replace that driver because the container module is responsible for starting PostgreSQL, while the JDBC driver is responsible for the database connection itself.

`spring-boot-starter-data-jpa-test` provides the Spring Boot 4 test support intended for JPA-focused testing. It also brings in the general Spring testing pieces needed for JUnit Jupiter, assertions, and Spring test contexts. Keeping that dependency in test scope means those libraries stay limited to testing rather than becoming part of the normal application runtime.

`spring-boot-testcontainers` adds the Spring Boot integration needed for features such as `@ServiceConnection`. The `testcontainers-postgresql` dependency adds PostgreSQL-specific Testcontainers support, including the current `PostgreSQLContainer` class that we will configure later.

Gradle projects can declare the same dependencies with their matching configurations:

```markup
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    runtimeOnly 'org.postgresql:postgresql'

    testImplementation 'org.springframework.boot:spring-boot-starter-data-jpa-test'
    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
    testImplementation 'org.testcontainers:testcontainers-postgresql'
}
```

`implementation` keeps Spring Data JPA available to the application code, while `runtimeOnly` places the PostgreSQL driver on the runtime classpath without treating it as an API dependency. The three `testImplementation` entries are available during test compilation and execution, which is where Spring Boot testing support and Testcontainers belong.

The PostgreSQL module name deserves attention when reading older tutorials. Testcontainers 2 gives PostgreSQL support through the `testcontainers-postgresql` artifact, and the current container class lives in `org.testcontainers.postgresql.PostgreSQLContainer`. Older material can still contain `org.testcontainers.containers.PostgreSQLContainer`, but that class belongs to the older package location and is deprecated in Testcontainers 2.

No JUnit Testcontainers extension is required for the Spring-managed container bean style covered later. Spring Boot can manage container beans through the application context, including starting them before dependent beans need their connection information and stopping them when that context closes. Projects that choose the JUnit `@Testcontainers` and `@Container` style can add `testcontainers-junit-jupiter`, though that follows a different lifecycle model from the Spring-managed configuration we will build next.

Keeping the Testcontainers dependencies in test scope also prevents the container libraries from becoming part of normal application startup. The application retains Spring Data JPA and the PostgreSQL driver it already needs, while container management and Spring Boot Testcontainers integration remain limited to the test classpath.

### Testing the Application Against PostgreSQL

With the project dependencies in place, we can connect the application layer to a temporary PostgreSQL database and follow the request from Java code through persistence and back again. The production classes stay unaware of Testcontainers because container configuration belongs on the test side of the project. Spring Boot receives temporary connection details through the test context, while the entity, repository, and service keep the same responsibilities they have during normal application startup.

#### Create a Small Data Layer

We can begin with a compact JPA entity so the database behavior stays easy to follow. `Book` represents a row in the `books` table, with an automatically generated identifier and a required title. Nothing in the entity refers to Testcontainers, PostgreSQL credentials, or a test-specific connection because those details belong outside the domain class.

```markup
package com.example.books;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "books")
public class Book {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String title;

    protected Book() {
    }

    public Book(String title) {
        this.title = title;
    }

    public Long getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }
}
```

JPA needs a public or protected no-argument constructor so the persistence provider can create entity instances when rows come back from the database. The second constructor gives application code a direct way to create a book from a title, while `GenerationType.IDENTITY` leaves identifier generation to PostgreSQL. With schema generation active during these tests, `@Column(nullable = false)` also contributes a non-null constraint for the `title` column.

The repository can stay small because Spring Data JPA can derive the query from the method name:

```markup
package com.example.books;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface BookRepository extends JpaRepository<Book, Long> {

    Optional<Book> findByTitle(String title);
}
```

Spring Data reads `findByTitle` from the repository interface and creates a query based on the `title` property from `Book`. Returning `Optional<Book>` gives the caller an explicit result when PostgreSQL has no matching row, rather than passing a `null` value back to the service layer. That return type also pairs naturally with the service method we will add next.

The service adds application logic above the repository. In this case, we ask the repository for a title and throw an exception when no matching book exists:

```markup
package com.example.books;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class BookService {

    private final BookRepository bookRepository;

    public BookService(BookRepository bookRepository) {
        this.bookRepository = bookRepository;
    }

    public Book getByTitle(String title) {
        return bookRepository.findByTitle(title)
                .orElseThrow(() -> new IllegalArgumentException("Book not found"));
    }
}
```

Constructor injection gives `BookService` access to the repository through Spring, while `@Transactional(readOnly = true)` places its read operations inside a read-only transaction when transaction management is active. The service does not need database credentials, container details, or a JDBC URL. Those concerns remain in test configuration, which lets this class behave the same during normal startup and integration testing.

#### Start PostgreSQL for Tests

Container configuration belongs under `src/test/java` because it exists only for testing. We can declare PostgreSQL as a Spring bean inside a class marked with `@TestConfiguration`, then place `@ServiceConnection` on the bean method so Spring Boot can derive connection details from the typed PostgreSQL container:

```markup
package com.example.books;

import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.context.annotation.Bean;
import org.testcontainers.postgresql.PostgreSQLContainer;

@TestConfiguration(proxyBeanMethods = false)
public class PostgresTestConfiguration {

    @Bean
    @ServiceConnection
    PostgreSQLContainer postgresContainer() {
        return new PostgreSQLContainer("postgres:17-alpine")
                .withDatabaseName("books_test")
                .withUsername("test")
                .withPassword("test");
    }
}
```

`PostgreSQLContainer` starts PostgreSQL from the requested image and exposes connection information after the container is running. The database name and credentials belong only to this temporary instance, so they do not need to match production values. Testcontainers maps PostgreSQL to an available host port rather than requiring port `5432` on the machine running the tests, which lets the temporary database start without depending on a fixed local port.

`@ServiceConnection` links the container with Spring Boot database auto-configuration. Because the bean method returns the typed `PostgreSQLContainer`, Spring Boot can identify the service and create JDBC connection details for it. JPA then receives a `DataSource` backed by the container without a manually assembled `spring.datasource.url`, host name, or mapped port. Service connection details take precedence over normal connection properties for the matching service.

Marking the class with `@TestConfiguration` keeps it on the test side of the project rather than regular application component scanning. The `proxyBeanMethods = false` setting tells Spring that this configuration does not need method interception for calls between bean methods. Later test classes can bring the configuration into their context through `@Import(PostgresTestConfiguration.class)`.

The container bean follows the lifecycle of the Spring test context. Spring Boot starts container beans early enough for dependent connection details to become available, then stops them when that context closes. No manual `start()` or `stop()` calls are needed for the Spring-managed bean style shown here.

#### Test the Repository

Repository tests can stay focused on JPA rather than loading the full application context. `@DataJpaTest` brings in entity scanning, Spring Data JPA repositories, Hibernate, JDBC support, and the related test auto-configuration, while regular application components such as `BookService` are left out of this slice by default. Spring Boot also runs JPA tests inside transactions and rolls them back after each test method.

We can import the PostgreSQL configuration and let Hibernate create the schema for this compact example:

```markup
package com.example.books;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;
import org.springframework.context.annotation.Import;

@DataJpaTest(properties = "spring.jpa.hibernate.ddl-auto=create-drop")
@Import(PostgresTestConfiguration.class)
class BookRepositoryTest {

    @Autowired
    private BookRepository bookRepository;

    @Test
    void findsBookByTitle() {
        Book savedBook = bookRepository.saveAndFlush(
                new Book("Spring Testing")
        );

        Book foundBook = bookRepository.findByTitle("Spring Testing")
                .orElseThrow();

        assertThat(foundBook.getId()).isEqualTo(savedBook.getId());
        assertThat(foundBook.getTitle()).isEqualTo("Spring Testing");
    }
}
```

`@Import` adds the test configuration, which brings the PostgreSQL container bean into this test context. The `ddl-auto=create-drop` property tells Hibernate to create the table from the entity mapping for this example and remove the generated schema when the persistence context closes. Projects that manage schema changes through Flyway or Liquibase can let those migrations prepare the container database instead.

Inside the test method, `saveAndFlush()` persists the new `Book` and flushes pending SQL to PostgreSQL before the lookup runs. `findByTitle()` then sends the repository query to PostgreSQL, and the assertions confirm that the row returned through JPA carries the generated identifier and expected title. This verifies more than a mocked repository could because Hibernate produces SQL, PostgreSQL processes it, and Spring Data maps the result back into the entity.

Spring Boot 4 treats a database supplied through `@ServiceConnection` as a test database for test database replacement. The default replacement mode is `NON_TEST`, so this container-backed `DataSource` remains in place rather than being replaced by an embedded database. No `@AutoConfigureTestDatabase(replace = NONE)` annotation is needed for this configuration.

The transactional behavior of `@DataJpaTest` also prevents repository tests from leaving committed rows behind. Each method can prepare the records it needs, execute repository calls, and finish with the transaction rolled back, which keeps later methods from inheriting data created by an earlier test. That isolation becomes more important as the repository test class grows and different methods insert records with different values.

#### Test the Service

Service-level integration testing loads more of the Spring Boot context because we now want Spring to create `BookService` along with the repository, Hibernate, transaction management, and the PostgreSQL connection. `@SpringBootTest` loads the application context rather than the narrower JPA slice, while the same test configuration can supply the temporary PostgreSQL instance.

We can store a book through the repository and then retrieve it through the service:

```markup
package com.example.books;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest(properties = "spring.jpa.hibernate.ddl-auto=create-drop")
@Import(PostgresTestConfiguration.class)
@Transactional
class BookServiceIntegrationTest {

    @Autowired
    private BookRepository bookRepository;

    @Autowired
    private BookService bookService;

    @Test
    void returnsBookStoredInPostgres() {
        bookRepository.saveAndFlush(
                new Book("Testing Spring Boot")
        );

        Book book = bookService.getByTitle("Testing Spring Boot");

        assertThat(book.getTitle()).isEqualTo("Testing Spring Boot");
    }
}
```

The test context creates the normal service and repository beans, then imports the PostgreSQL container configuration beside them. Saving through `BookRepository` places the row in PostgreSQL, while the following `BookService` call passes through the service method, repository query, Hibernate, JDBC driver, and temporary database. The assertion checks the value returned after that call chain completes, so we are testing the service with the same persistence stack configured for the application.

Placing `@Transactional` on the test class keeps changes from each test method inside the test transaction, which Spring rolls back afterward. The service already carries `@Transactional(readOnly = true)`, while the surrounding test transaction lets us prepare data before calling the read method without leaving committed rows behind.

The missing-record branch can live in the same integration test class:

```markup
@Test
void throwsExceptionWhenBookDoesNotExist() {
    assertThatThrownBy(
            () -> bookService.getByTitle("Missing Book")
    ).isInstanceOf(IllegalArgumentException.class);
}
```

`assertThatThrownBy` receives the service call as a lambda and checks that it ends with `IllegalArgumentException`. No row is inserted for the requested title, so `findByTitle()` returns an empty `Optional` and `BookService` reaches its `orElseThrow` branch. We still pass through the repository and PostgreSQL for the lookup, which lets the test cover the service behavior without replacing persistence with a mock.

The same service connection model can support other database technologies. MySQL follows a similar relational flow with its Testcontainers module and container class, while MongoDB projects rely on Spring Data MongoDB and `MongoDBContainer` rather than JPA and JDBC. The container type changes with the database, but Spring Boot can still receive supported connection details through `@ServiceConnection`.

### Conclusion

Testcontainers gives Spring Boot integration tests a temporary PostgreSQL database that can be started from test configuration and connected through `@ServiceConnection`. From there, `@DataJpaTest` can exercise repository behavior through JPA and PostgreSQL, while `@SpringBootTest` can load the broader application context for service-level testing. The container stays outside production code, Spring Boot supplies the connection details, and each test can run against PostgreSQL without keeping a dedicated test database running.

![](https://substackcdn.com/image/fetch/$s_!zjcM!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F75341fb5-0e2a-4507-8b75-7decdc140fd8_276x276.png)

Spring Boot icon by Icons8
