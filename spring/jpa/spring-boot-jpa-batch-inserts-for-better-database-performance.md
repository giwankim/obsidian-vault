---
title: "Spring Boot JPA Batch Inserts for Better Database Performance"
source: "https://alexanderobregon.substack.com/p/spring-boot-jpa-batch-inserts-for?utm_source=substack&utm_medium=email"
author:
  - "[[Alexander Obregon]]"
published: 2026-09-15
created: 2026-09-29
description: "Saving a few rows through JPA rarely puts much pressure on a database, but importing hundreds or thousands of entities changes how much database activity is involved."
tags:
  - "clippings"
---

> [!summary]
> Hibernate JDBC batching is off by default. Enable it with `spring.jpa.properties.hibernate.jdbc.batch_size` and `order_inserts`. `GenerationType.IDENTITY` disables insert batching because each insert must run immediately to return its ID, so a sequence generator (with a matching `allocationSize`) is needed instead. A large import should `flush()` and `clear()` the `EntityManager` every N entities to cap persistence-context memory, weighing a single transaction against committed chunks. Batching can be verified through the `org.hibernate.orm.jdbc.batch` logger rather than by counting repeated INSERT lines.

Saving a few rows through JPA rarely puts much pressure on a database, but importing hundreds or thousands of entities changes how much database activity is involved. Every insert can involve JDBC calls, network round trips, database parsing, identifier generation, and memory inside the persistence context. Hibernate can group compatible insert statements into JDBC batches, letting the driver process several statements at a time instead of sending every insert individually. Spring Boot lets you pass native Hibernate properties through the `spring.jpa.properties` prefix, giving the application direct control over settings such as JDBC batch size and insert ordering. Service code also affects batching during a large import, particularly through the transaction boundary, identifier generation strategy, and periodic flush operations that keep thousands of managed entities from remaining in memory until the transaction finishes.

### What Happens During a Large JPA Insert

Persisting a handful of entities gives Hibernate very little repeated database activity to coordinate, while a collection containing hundreds or thousands of new entities creates a much larger stream of insert operations. JPA still treats every entity as its own managed object, and Hibernate still prepares an insert for every row that needs to be created. JDBC batching changes how compatible statements reach the driver by collecting several executions of the same prepared SQL statement before the driver sends them to the database. That reduces the number of calls between the application and database without changing the number of rows being inserted. Hibernate does not require a JDBC batch to become a single multi-row `INSERT` statement because the final form sent across the connection depends partly on the JDBC driver. At the ORM level, the entities still represent individual insert operations.

#### The Cost of Repeated Persist Calls

Persisting a large collection normally means Hibernate receives entities individually. Calling `persist()` registers a new entity with the persistence context and tells Hibernate that a row needs to be inserted. For identifier strategies that provide the identifier before insertion, Hibernate can keep that insert pending until persistence changes are synchronized with the database. Repeating `persist()` therefore does not automatically mean JDBC receives a database call at that exact moment.

We can see the Java side of that process with a small service method:

```markup
public void persistItems(List<InventoryItem> items) {
    for (InventoryItem item : items) {
        entityManager.persist(item);
    }
}
```

Every pass through the loop registers an additional `InventoryItem` with the persistence context. If the collection contains 5,000 items, Hibernate still has 5,000 new entities to track and 5,000 rows to insert. JDBC batching does not reduce that row count or turn the collection into a single JPA insert. Its benefit appears later, when Hibernate has compatible prepared statements ready for JDBC execution. This distinction helps explain why the Java call count and the database call count are not the same thing. JPA tracks entity state, while JDBC deals with SQL statements sent through a database connection. Hibernate connects those layers by translating new entity state into insert statements, binding values for every entity, and collecting compatible executions into JDBC batches when batching is active.

For several `InventoryItem` entities, Hibernate can repeatedly prepare SQL with the same structure:

```markup
insert into inventory_item (name, price, sku, id)
values (?, ?, ?, ?)
```

The question marks are parameter placeholders, so the SQL structure stays the same while values change from entity to entity. Hibernate binds the values for every row, then JDBC batching allows compatible executions to be sent in groups instead of requiring an isolated driver execution for every insert. The database still receives every row and still processes every requested insert.

Repeated `INSERT` text can therefore appear in SQL logs while batching is active. Hibernate is still creating an insert action for every entity and binding values for every execution. Batching changes how those compatible executions are handed to JDBC rather than turning thousands of entities into a single JPA operation. Some JDBC drivers can rewrite batched inserts before transmission, but that behavior belongs to the driver and database rather than JPA itself.

Spring Data JPA `saveAll()` follows the same basic idea. Passing a collection to `saveAll()` gives the repository several entities to persist, but the collection-based method does not activate JDBC batching by itself. For new entities, Spring Data eventually calls into the JPA persistence layer, while Hibernate still follows its configured batching behavior and the identifier rules of the mapped entity. If 5,000 new entities go through a single repository call, we should still think of them as 5,000 entity insert operations that Hibernate coordinates at the ORM layer.

Hibernate leaves JDBC batching disabled by default, with a batch size of zero representing that state. After batching is activated, the configured batch size places an upper limit on the number of compatible statements Hibernate can collect before asking JDBC to execute the batch. Values between 10 and 50 are commonly recommended as a starting range, though the exact configuration belongs in the later persistence settings. Batch size also means something different from the number of entities held in the persistence context. Setting a JDBC batch size of 50 tells Hibernate how large a compatible JDBC batch can become, but it does not tell Hibernate to detach the first 50 managed entities afterward. Memory inside the persistence context is handled independently, which becomes more relevant as an import grows and will be covered later.

#### Identifier Generation Can Block Insert Batching

Generated identifiers affect when Hibernate can send an insert to the database, which directly affects JDBC batching. With `GenerationType.IDENTITY`, the database creates the identifier as part of the insert. Hibernate therefore needs that row to be inserted before it can receive the generated identifier, and current Hibernate behavior does not support JDBC insert batching for entities backed by identity generation.

That timing requirement changes the insert flow. If we persist an entity whose identifier comes from an identity column, Hibernate needs the database-generated value before the entity has its final identifier in the persistence context. The insert cannot remain queued with several similar identity-backed inserts in the same way a sequence-backed insert can.

We can represent an identity-backed entity with a mapping like this:

```markup
@Entity
@Table(name = "inventory_item")
public class InventoryItem {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String sku;

    @Column(nullable = false)
    private String name;
}
```

The important line is `GenerationType.IDENTITY`. That choice tells Hibernate that the database will generate the identifier as part of inserting the row. Because Hibernate needs the generated value from that insert, these entity inserts cannot participate in Hibernate JDBC insert batching.

Databases with sequence support give Hibernate a different option. Sequence-generated identifiers can be obtained before the insert statement is executed, so Hibernate can know the entity identifier while the insert is still waiting for JDBC execution. We can map that behavior with an explicit sequence generator:

```markup
@Entity
@Table(name = "inventory_item")
public class InventoryItem {

    @Id
    @GeneratedValue(
        strategy = GenerationType.SEQUENCE,
        generator = "inventory_item_seq"
    )
    @SequenceGenerator(
        name = "inventory_item_seq",
        sequenceName = "inventory_item_seq",
        allocationSize = 50
    )
    private Long id;

    @Column(nullable = false)
    private String sku;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal price;

    protected InventoryItem() {
    }

    public InventoryItem(String sku, String name, BigDecimal price) {
        this.sku = sku;
        this.name = name;
        this.price = price;
    }
}
```

With this mapping, Hibernate gets identifiers from `inventory_item_seq` instead of waiting for every insert to create the identifier. The `allocationSize` value belongs to identifier allocation rather than JDBC statement batching. It tells the persistence provider how identifier values are allocated for that generator, while the JDBC batch size controls the number of compatible SQL executions that can be grouped before they are sent through JDBC.

Matching an allocation size of 50 with a JDBC batch size of 50 can be a reasonable thing to do, but the values do not have to match. They control different parts of persistence. Sequence allocation affects identifier retrieval, while JDBC batch size affects grouped statement execution.

The database schema also needs to agree with the entity mapping. If the mapping names `inventory_item_seq`, that sequence has to exist when schema creation is handled through database migrations, and its increment configuration needs to agree with the allocation strategy expected by Hibernate. Keeping those values aligned prevents identifier allocation conflicts and lets Hibernate reserve identifier ranges as intended.

Sequence generation is not the only option that can permit batching. Assigned identifiers already exist before insertion, while other generator choices depend on the database dialect and entity mapping. The limitation is narrower. If Hibernate has to execute every insert immediately to obtain the generated identifier, those inserts cannot be collected into a Hibernate JDBC insert batch.

This is why two entities saved through very similar service code can behave differently at the JDBC layer. An entity backed by `GenerationType.IDENTITY` needs an insert before Hibernate receives its identifier, while an entity backed by a compatible sequence strategy can receive its identifier earlier. Looking at the identifier strategy before tuning batch settings can explain why expected insert batching is absent.

### Building a Batch Insert Service

Good batch insert behavior comes from more than calling `persist()` repeatedly. Spring Boot passes native Hibernate properties through the `spring.jpa.properties` prefix, Hibernate groups compatible SQL statements according to its JDBC batch settings, and the service controls how long entities remain managed before pending changes reach the database. For a large import, those pieces need to line up so the driver receives batches at sensible intervals while the persistence context does not keep growing for the entire collection.

#### Hibernate Batch Configuration

Spring Boot passes Hibernate-specific settings through the `spring.jpa.properties` prefix. The property name after that prefix has to match the Hibernate property exactly because relaxed binding does not apply to these provider-specific entries. Spelling therefore needs to stay exact, while forms such as `hibernate.jdbc.batch-size` or `hibernate.jdbc.batchSize` are not treated as the same Hibernate setting.

For an insert-heavy service, we can start with configuration like this:

```markup
spring.jpa.properties.hibernate.jdbc.batch_size=50
spring.jpa.properties.hibernate.order_inserts=true
```

The first line sets the maximum JDBC batch size to 50 statements. Hibernate can execute a smaller batch when fewer compatible statements are ready, so the value is a ceiling rather than a promise that every database trip will contain exactly 50 inserts. Setting the batch size to zero or a negative value disables JDBC batching. The second line asks Hibernate to order pending inserts by entity type and identifier value so compatible statements have a better chance of being grouped into the same JDBC batch. Hibernate leaves insert ordering off by default because the sorting step adds its own cost.

We should read those settings as controls for two different parts of the insert process. `hibernate.jdbc.batch_size` controls the number of compatible statements Hibernate can collect before asking the driver to execute the batch, while `hibernate.order_inserts` changes the order of pending insert actions so statements for the same entity type can stay near each other. If a service only inserts a single entity type in a consistent sequence, insert ordering may have little effect. Transactions that create several entity types can gain more from it because interleaved insert actions can break larger groups into smaller batches.

Batch size should not be treated as a universal performance number either. Starting with 50 is reasonable, yet the best value depends on the JDBC driver, database engine, row size, connection latency, and competing database traffic. Raising the number indefinitely can increase memory held for pending statements and can place larger bursts of database activity into each execution. Lower values reduce the amount collected per batch but can increase the number of driver calls. Measuring import duration against the production database engine gives far better guidance than choosing the largest value available.

Spring Boot can pass other Hibernate properties through the same prefix, but adding settings without a specific reason can make persistence behavior harder to trace. For this service, batch size and insert ordering are enough to establish the JDBC batching behavior before we move into the service loop.

#### Flushing Large Collections in Chunks

Large imports can leave thousands of managed entities inside the persistence context if the service keeps calling `persist()` until the transaction ends. Hibernate tracks those entities while they remain managed, which means the persistence context can consume more memory as the collection grows. Periodic synchronization followed by detachment keeps that managed set from expanding for the full duration of the import.

We can place both operations directly in the insert loop:

```markup
@Service
public class InventoryImportService {

    private static final int BATCH_SIZE = 50;

    private final EntityManager entityManager;

    public InventoryImportService(EntityManager entityManager) {
        this.entityManager = entityManager;
    }

    @Transactional
    public void saveAll(List<InventoryItem> items) {
        for (int i = 0; i < items.size(); i++) {
            entityManager.persist(items.get(i));

            if ((i + 1) % BATCH_SIZE == 0) {
                entityManager.flush();
                entityManager.clear();
            }
        }

        if (items.size() % BATCH_SIZE != 0) {
            entityManager.flush();
            entityManager.clear();
        }
    }
}
```

Every entity enters the persistence context through `persist()`. After 50 entities, `flush()` asks Hibernate to synchronize pending persistence changes with the database, which lets the current insert statements reach JDBC in configured batches. The following EntityManager call detaches the managed entities from that persistence context, reducing how much entity state Hibernate continues tracking. The final conditional block handles a remainder when the collection size does not divide evenly by 50.

Calling `flush()` does not commit the transaction. The SQL can reach the database while the transaction remains open, so rows sent during earlier flushes still belong to the same transaction. If a later exception causes the surrounding transaction to roll back, those earlier inserts can roll back with it. Hibernate can also flush automatically in several situations, including transaction commit and some queries, but an explicit flush inside a large insert loop gives the service direct control over when pending inserts are synchronized.

The detachment call has a different purpose from `flush()`. Flushing synchronizes pending changes, while the following EntityManager operation detaches every entity currently managed by that persistence context. Later changes made directly to those detached objects are no longer tracked automatically. If later logic needs to modify an entity that was detached earlier, that code has to account for its detached state rather than assuming Hibernate still tracks it.

Matching the flush interval to the JDBC batch size makes the flow easy to follow, but the values do not have to be identical. With a JDBC batch size of 50 and a flush interval of 200, Hibernate can execute several JDBC batches during a flush. Flushing every 20 entities with the same JDBC batch size prevents that group from filling a 50-statement insert batch before synchronization occurs. The right interval balances persistence-context memory against the opportunity to fill JDBC batches efficiently.

Import services can also receive collections smaller than the configured interval. The remainder check at the end handles that case explicitly, though transaction commit would also trigger a flush under the normal `AUTO` flush mode. Keeping the final flush in the method makes the service behavior explicit because every pending insert is synchronized before the method exits.

#### Transaction Boundaries During Imports

Keeping the whole insert loop inside `@Transactional` gives Hibernate a single persistence context and database transaction for the method. That lets compatible insert statements accumulate between flush points and gives the import atomic behavior. If an unchecked exception reaches the transaction boundary, Spring marks the transaction for rollback, so inserts flushed earlier in the method do not become committed rows merely because their SQL already reached the database.

Transaction size deserves attention as import volume grows. Flushing every 50 entities controls persistence-context growth, but it does not shorten the database transaction. Locks can remain active, transaction logs can continue growing, and the database connection stays occupied while the import proceeds. Rolling back a very large transaction can also become expensive because the database has more changes to undo.

For imports containing a few thousand or tens of thousands of independent rows, a single transaction with periodic flushes can be a reasonable starting point. Much larger imports can benefit from committed chunks, but that changes failure semantics. If five chunks commit and the sixth fails, the first five remain stored unless the service has recovery logic that reverses or resumes the import. Chunked transactions therefore trade all-or-nothing behavior for shorter transaction duration and a smaller rollback scope.

We also need to keep transaction placement in mind when service methods call each other. Spring transaction handling normally operates through a proxy around the bean, so a direct call from one method to a different method on the same instance does not pass through that proxy again. Placing `@Transactional` on the public service boundary keeps the database operation inside the intended transaction without depending on an internal method call to start a new one.

#### Checking SQL Batch Activity

SQL logs can confirm the statements Hibernate prepares, but repeated `INSERT` lines by themselves do not prove that JDBC batching is active. Hibernate still creates an insert action for every entity, so the SQL logger can print the same statement repeatedly while JDBC later groups compatible executions into batches. Current Hibernate logging includes a dedicated category for JDBC batch execution, along with categories for SQL text and parameter binding.

Spring Boot logging levels can expose those details during local testing:

```markup
logging.level.org.hibernate.SQL=DEBUG
logging.level.org.hibernate.orm.jdbc.batch=TRACE
logging.level.org.hibernate.orm.jdbc.bind=TRACE
```

`org.hibernate.SQL` prints the SQL generated by Hibernate. `org.hibernate.orm.jdbc.batch` reports JDBC batch activity, which gives stronger confirmation that batching is actually taking place. `org.hibernate.orm.jdbc.bind` prints bound parameter information at trace level, letting us follow the values attached to prepared statements. Parameter logging can expose application data and create a large volume of output, so it belongs in short diagnostic sessions rather than normal production logging.

We can also ask Hibernate to collect runtime statistics during performance testing:

```markup
spring.jpa.properties.hibernate.generate_statistics=true
```

Hibernate leaves statistics collection off by default because collecting those metrics adds processing and memory overhead. Turning it on can provide broader information about ORM activity, but the batch logger is the more direct place to confirm JDBC batch execution. Statistics are better treated as a temporary diagnostic aid when deeper persistence measurements are needed. Database-side monitoring can fill in information that Hibernate logs cannot provide. The JDBC driver controls how a batch is transmitted after Hibernate hands it over, and database monitoring can reveal transaction duration, statement activity, server time, waits, and connection behavior. That becomes valuable when two JDBC drivers or database engines react differently to the same Hibernate batch size.

Checking the generated SQL also helps catch cases where statements cannot be grouped as expected. Insert statements need compatible SQL structure to share the same JDBC batch, so changes in entity type or SQL form can split execution into smaller groups. Identifier generation can block insert batching as covered earlier, and insert ordering can affect how closely compatible statements appear in Hibernate’s pending action queue. Reading the SQL, batch logs, and database metrics as three views of the same import gives a stronger performance check than relying on elapsed time alone.

### Conclusion

JPA batch inserts perform best when the whole persistence flow supports batching from entity creation through JDBC execution. Hibernate can group compatible inserts, sequence-backed identifiers can keep those inserts batchable, and periodic `flush()` and `clear()` calls keep the persistence context from growing through a large import. With the transaction boundary, batch size, insert ordering, and logging configured carefully, we can reduce database round trips while keeping control over how inserts move through Hibernate and JDBC.

![](https://substackcdn.com/image/fetch/$s_!TYsx!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F41abf2c3-5db5-4b8f-b1a8-e395022c9e89_276x276.png)

Spring Boot icon by Icons8
