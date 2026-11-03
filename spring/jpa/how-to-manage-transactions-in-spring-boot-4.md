---
title: "How to Manage Transactions in Spring Boot 4"
source: "https://alexanderobregon.substack.com/p/how-to-manage-transactions-in-spring?utm_source=substack&utm_medium=email"
author:
  - "[[Alexander Obregon]]"
published: 2026-10-28
created: 2026-11-01
description: "Database operations can involve several steps within the same service method, from creating a new record to updating existing data through multiple repository calls."
tags:
  - "clippings"
---

> [!summary]
> Using an order-and-inventory example with Spring Data JPA and PostgreSQL, this tutorial shows why separate repository calls can leave partial commits and how `@Transactional` on the service method makes them one unit under Spring Framework 7. It then covers rollback rules for different exceptions, read-only transactions, and transaction participation across service calls. It also explains self-invocation, where calls between methods bypass Spring's transactional proxy.

Database operations can involve several steps within the same service method, from creating a new record to updating existing data through multiple repository calls. If something fails partway through, earlier changes may already be committed while later operations never finish, leaving the database in an inconsistent state. Spring Boot 4 handles these situations through Spring Framework 7’s transaction management, allowing us to group related database operations within a single transaction through `@Transactional`. This gives us control over when changes are committed, how exceptions trigger rollbacks, and how read-only operations are handled. Knowing where transactions begin and end can also help explain why certain methods don’t always behave as expected, particularly when calls between service methods bypass Spring’s transaction proxy.

### Establishing the Transaction Boundary

Transactions become important when several database operations contribute to a single action, like creating an order while updating the inventory associated with it. If those operations execute independently, a failure halfway through can leave changes committed that should have been canceled. Spring Boot 4 gives us transaction management through Spring Framework 7, allowing related database operations to share the same transaction boundary. We’ll begin with repository calls that aren’t enclosed by a service-level transaction, then move that responsibility into the service so the database can commit or roll back the entire purchase.

#### Starting With Multiple Repository Calls

Placing an order usually involves more than inserting a record into a database. We also need to locate the purchased product, check its available quantity, and update inventory to reflect the purchase. These operations depend on each other because saving an order without reserving the inventory could leave the customer with a purchase that cannot be fulfilled.

For this example, we’ll use Spring Boot 4 with Spring Data JPA and PostgreSQL. Spring Data JPA provides repository interfaces for accessing database entities, while Hibernate handles persistence operations through JPA.

The required dependencies can be added to a Gradle project through `spring-boot-starter-data-jpa` and the PostgreSQL JDBC driver.

```markup
import jakarta.persistence.*;

@Entity
@Table(name = "inventory_items")
public class InventoryItem {

    @Id
    private Long id;

    @Version
    private Long version;

    @Column(nullable = false)
    private int availableQuantity;

    protected InventoryItem() {
    }

    public int getAvailableQuantity() {
        return availableQuantity;
    }

    public void reserve(int quantity) {
        if (quantity <= 0) {
            throw new IllegalArgumentException(
                "Quantity must be positive"
            );
        }

        if (availableQuantity < quantity) {
            throw new IllegalStateException(
                "Insufficient inventory"
            );
        }

        availableQuantity -= quantity;
    }
}
```

We’ve defined the entity with an identifier, an available quantity, and a version number managed by JPA. The `id` field identifies an existing inventory record, allowing the application to retrieve the corresponding product from the database. Its protected constructor gives JPA a way to instantiate the entity when loading records without requiring callers to create inventory objects through that constructor. The `reserve()` method handles the inventory adjustment. Before reducing the available quantity, we check that the requested amount is positive and doesn’t exceed the stock currently recorded. If either condition fails, an exception interrupts the operation before the quantity changes.

Keeping this validation within the entity prevents callers from reducing inventory below zero through `reserve()`. It also provides the ordering service with a way to detect purchases that cannot be completed, without requiring the service to repeat the inventory validation itself.

We’ve also included the `@Version` annotation, which introduces optimistic locking. Hibernate manages the version value and checks it when updating the entity. If a competing transaction has already committed a modification to the same record, the version comparison can detect that conflict rather than allowing an older inventory value to overwrite the newer one. This becomes important when multiple customers attempt to purchase the same product around the same time.

Next, we need a `PurchaseOrder` entity to represent an order submitted by a customer:

```markup
import jakarta.persistence.*;

@Entity
@Table(name = "purchase_orders")
public class PurchaseOrder {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Long itemId;

    @Column(nullable = false)
    private int quantity;

    protected PurchaseOrder() {
    }

    public PurchaseOrder(Long itemId, int quantity) {
        this.itemId = itemId;
        this.quantity = quantity;
    }

    public Long getId() {
        return id;
    }
}
```

Each purchase order records the inventory item being purchased and the quantity requested. Through the constructor, we can create an order from those values, while `@GeneratedValue(strategy = GenerationType.IDENTITY)` tells Hibernate that the database generates the identifier during insertion.

We now have two entities representing different information about the purchase. `PurchaseOrder` records what the customer ordered, while `InventoryItem` tracks the quantity remaining in stock. Completing the purchase requires changes to both records, and a failure affecting either operation should prevent the entire purchase from being committed.

To access these entities, we’ll create two Spring Data JPA repositories by extending `JpaRepository`. Each interface belongs in its own Java file.

We’ll begin with the inventory repository:

```markup
import org.springframework.data.jpa.repository.JpaRepository;

public interface InventoryRepository
        extends JpaRepository<InventoryItem, Long> {
}
```

By extending `JpaRepository<InventoryItem, Long>`, the interface inherits methods for retrieving, saving, deleting, and querying inventory entities. The first generic argument identifies the entity managed by the repository, while `Long` represents the type of its identifier.

The purchase order repository follows the same structure but operates on `PurchaseOrder` entities:

```markup
import org.springframework.data.jpa.repository.JpaRepository;

public interface PurchaseOrderRepository
        extends JpaRepository<PurchaseOrder, Long> {
}
```

Spring Data JPA supplies implementations for inherited methods such as `save()` and `findById()`, allowing us to access both tables without writing SQL statements for these operations. With the repositories defined, we can concentrate on coordinating the purchase rather than implementing database access methods individually.

Initially, the ordering operation could be written as a sequence of repository calls without placing a transaction around the entire service method:

```markup
PurchaseOrder order = orderRepository.save(
    new PurchaseOrder(itemId, quantity)
);

InventoryItem item = inventoryRepository.findById(itemId)
    .orElseThrow(() ->
        new IllegalArgumentException("Item not found")
    );

item.reserve(quantity);

inventoryRepository.save(item);
```

We begin by creating a `PurchaseOrder` and passing it to `orderRepository.save()`. After saving the order, we call `inventoryRepository.findById()` to retrieve the inventory record associated with the requested item. If the record doesn’t exist, `orElseThrow()` raises an `IllegalArgumentException` instead of allowing the purchase to continue.

Once the inventory item has been retrieved, `reserve()` checks the requested quantity and reduces the available stock. We then pass the modified entity to `inventoryRepository.save()` so the updated quantity can be persisted.

The sequence follows the expected purchasing process, but executing these statements inside an ordinary service method doesn’t automatically mean the database treats them as one purchase.

Spring Data JPA already provides transactional behavior for inherited repository methods. When we call `save()` without an existing transaction, Spring Data JPA can begin a transaction for that repository operation and commit it after the method finishes successfully.

This starts to be a problem if the order is saved before the inventory check fails.

Imagine a customer requests an inventory item that no longer exists. Our initial `orderRepository.save()` call may have already committed the purchase order, but the following `findById()` call throws an `IllegalArgumentException`. The earlier repository transaction has already finished, so the exception cannot undo the committed order.

Insufficient stock creates a similar situation. If the item exists but its available quantity is lower than the amount requested, `reserve()` throws an `IllegalStateException`. The inventory remains unchanged, but the purchase order could already be stored in the database.

We could also encounter a failure during the final inventory update because of a database constraint, connection problem, or conflicting modification. Without a transaction covering the complete purchase, successful earlier commits remain unaffected by that later failure.

The underlying issue comes from where the transaction boundary is established. Each inherited repository method has its own transaction configuration, but the service hasn’t told Spring that the order insertion and inventory update belong to the same database operation.

What we need is a transaction that remains active throughout the purchase, allowing both changes to commit successfully or be rolled back if the operation fails. The service is the appropriate location for that boundary because it coordinates the repository calls involved in completing the order.

#### Adding @Transactional to the Service

Spring provides the `@Transactional` annotation to declare transaction behavior on a method or class. Rather than manually beginning a transaction, performing database operations, and committing the result, we can annotate the service method responsible for the complete purchase.

The annotation tells Spring’s transaction infrastructure to establish a transaction boundary when the method is invoked through Spring’s transactional proxy.

For our ordering operation, we want the transaction to begin before the order is inserted and remain active until the inventory adjustment has finished. If something interrupts the purchase during that period, the database changes should be rolled back according to the transaction’s rollback rules.

We’ll move the repository calls into an `OrderService` class and place `@Transactional` directly above `placeOrder()`:

```markup
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderService {

    private final InventoryRepository inventoryRepository;
    private final PurchaseOrderRepository orderRepository;

    public OrderService(
            InventoryRepository inventoryRepository,
            PurchaseOrderRepository orderRepository) {

        this.inventoryRepository = inventoryRepository;
        this.orderRepository = orderRepository;
    }

    @Transactional
    public Long placeOrder(Long itemId, int quantity) {
        if (quantity <= 0) {
            throw new IllegalArgumentException(
                "Quantity must be positive"
            );
        }

        PurchaseOrder order = orderRepository.save(
            new PurchaseOrder(itemId, quantity)
        );

        InventoryItem item = inventoryRepository.findById(itemId)
            .orElseThrow(() ->
                new IllegalArgumentException("Item not found")
            );

        item.reserve(quantity);

        inventoryRepository.save(item);

        return order.getId();
    }
}
```

We’ve marked `OrderService` with `@Service`, allowing Spring to register it as a managed component and inject both repositories through its constructor. The `@Transactional` annotation then establishes a transaction boundary around `placeOrder()` when the method is invoked through Spring’s transaction infrastructure.

Notice that the repository calls haven’t changed from the earlier sequence. We still create the order, retrieve the inventory item, reserve the requested quantity, and persist the inventory modification. The difference is that Spring now coordinates those operations within a transaction rather than allowing each repository method to complete its own independent transaction.

When `placeOrder()` is called without an existing transaction, Spring begins a new transaction before executing the method. Both repositories participate in that transaction, meaning their database changes belong to the same operation and remain subject to the same final commit or rollback.

We’ve also added a quantity check at the beginning of the service method. This prevents an invalid quantity from reaching the database operation, while the validation inside `InventoryItem.reserve()` continues to protect inventory changes when that method is called from other locations.

Now let’s follow what happens if the purchase cannot be completed.

If the inventory lookup fails, `orElseThrow()` raises an `IllegalArgumentException`. That exception escapes `placeOrder()`, causing Spring to roll back the transaction. The purchase order inserted earlier is discarded because its insertion belongs to the same uncommitted transaction.

Insufficient stock follows the same general process. When `reserve()` throws an `IllegalStateException`, execution stops before the inventory update is completed. Spring detects the exception as it leaves the transactional method and rolls back the database changes associated with the purchase.

Both exceptions extend `RuntimeException`, which Spring treats as a reason to roll back under its default transaction configuration.

Successful execution follows a different outcome. After the repository operations complete and the service method returns, Spring proceeds with committing the transaction. Provided the database accepts the changes, the purchase order and updated inventory quantity become committed as part of the same transaction.

There’s an important distinction between calling `save()` and committing a transaction. In Spring Data JPA, `save()` requests that an entity be persisted or merged into the current persistence context. Hibernate determines when the corresponding SQL statements need to be executed, and those statements can execute before the transaction finishes.

Our `PurchaseOrder` entity provides a good example of this behavior. Because its identifier comes from `GenerationType.IDENTITY`, Hibernate generally needs to execute the insertion to retrieve the generated ID. That allows `order.getId()` to return the identifier before the enclosing transaction has committed.

Although the insertion has already happened at the SQL level, it can still be rolled back if a later operation fails. The database doesn’t treat the row as permanently committed merely because Hibernate executed the insertion.

The inventory entity behaves somewhat differently. After `findById()` retrieves the record inside the active transaction, the entity is managed by the JPA persistence context. When we call `reserve()`, we modify the entity’s quantity in memory, and Hibernate tracks that modification.

Because the entity is already managed, Hibernate can detect the changed quantity and persist it during synchronization with the database. Calling `inventoryRepository.save(item)` is valid, but it isn’t strictly required for an entity already managed within the transaction.

We could therefore remove the final `save()` call without changing how JPA tracks the quantity modification in this particular method. Keeping it in the example makes the intended persistence operation explicit, while the surrounding transaction remains responsible for the final commit.

Spring Boot 4 normally configures the transaction infrastructure automatically when the JPA starter, a configured data source, and the standard auto-configuration are present. We generally don’t need to register a transaction manager manually or add `@EnableTransactionManagement` to the application configuration.

The `@Transactional` annotation still comes from `org.springframework.transaction.annotation.Transactional`, and its basic behavior remains consistent with Spring Boot 3.

By placing the transaction boundary around `placeOrder()`, we’ve connected the database changes to the complete purchasing operation. An order that fails its inventory reservation won’t leave behind a committed purchase record, and successful inventory modifications are committed within the same transaction as their associated orders.

#### Following the Transaction Lifecycle

After adding `@Transactional`, we can examine how the transaction progresses from the initial service call through the final database commit. The timing is important because Hibernate can execute SQL statements before the transaction finishes, and certain failures aren’t detected until the remaining changes are synchronized with the database.

The process begins when a caller invokes `placeOrder()` through the Spring-managed service. Spring’s transaction proxy intercepts that call and delegates transaction management to the configured transaction manager. For a standard Spring Data JPA application connected to a single data source, this is normally a `JpaTransactionManager`.

Before the service method executes, the transaction manager establishes the transactional context. Hibernate then associates its persistence operations with that context, allowing the entity changes and repository calls to participate in the same database transaction.

As we enter `placeOrder()`, the quantity validation happens first. If the amount is invalid, the method throws an exception before creating an order or accessing the inventory repository.

For a valid quantity, we create a `PurchaseOrder` and pass it to the repository. Because the entity receives its identifier through `GenerationType.IDENTITY`, Hibernate generally executes the insertion at this point to retrieve the database-generated value.

The order row has now been inserted, but the surrounding transaction hasn’t committed. If the service encounters an exception that triggers rollback, the database can still discard that insertion.

Next, we retrieve the inventory item through `findById()`. Hibernate loads the corresponding entity into the current persistence context, allowing changes to its fields to be tracked for the duration of the transaction.

Calling `reserve()` modifies the `availableQuantity` field after checking that the requested quantity is valid. Hibernate doesn’t necessarily execute an `UPDATE` immediately when the Java method changes that value. Instead, the modification is tracked until Hibernate synchronizes the pending entity changes with the database.

This synchronization process is called a flush. During a flush, Hibernate executes the SQL statements needed to reflect pending changes in the database. Depending on the operations being performed and the configured flush mode, synchronization can happen before certain queries, through an explicit flush request, or during transaction completion.

Flushing and committing are different operations. Executing an `UPDATE` during a flush doesn’t mean the modified inventory quantity has been permanently committed.

If the transaction rolls back after that SQL statement executes, the database discards the uncommitted modification. This distinction becomes important when examining database logs because seeing an `INSERT` or `UPDATE` statement doesn’t prove that the transaction ultimately committed.

After the final repository call completes, `placeOrder()` returns the generated order ID to Spring’s transaction interceptor. From the service method’s perspective, the Java statements have finished successfully, but Spring still needs to complete the transaction.

The transaction manager begins that completion process by coordinating any remaining persistence operations. Hibernate synchronizes pending entity changes as needed, and the transaction manager requests that the database commit.

Certain failures can still occur during this stage.

Database constraints may reject an insertion or update, while concurrency checks can detect that an entity was modified by a competing transaction. These problems may surface during flushing rather than at the exact Java statement that originally changed the entity.

As a result, the service method body can finish without throwing an exception while the overall transactional invocation still fails during commit.

The caller receives a successful result only after Spring’s transaction interceptor finishes processing the commit. Returning the generated order ID from the service method doesn’t bypass that final transaction step.

Our inventory entity also includes an optimistic locking version field, which becomes important when multiple purchases affect the same inventory record.

Imagine two customers requesting the same product at nearly the same time. Their transactions could initially retrieve the same available quantity and version number, with both attempting to reserve inventory based on that earlier information.

When Hibernate updates a versioned entity, it checks the expected version against the version stored in the database. If a competing transaction has already committed a modification to that record, the version comparison detects the conflict.

The affected transaction then encounters an optimistic locking failure instead of silently overwriting the newer inventory quantity.

Depending on when Hibernate executes the update, the failure can occur during an earlier flush or during the synchronization performed as part of transaction completion. If the failure causes the transaction to roll back, the associated purchase order insertion is rolled back as well.

Through this behavior, `@Version` complements the transaction boundary. The transaction groups related database modifications into a single operation, while optimistic locking detects conflicting updates to the inventory record. Neither mechanism automatically retries a purchase that fails because of a concurrency conflict.

We should also keep in mind that database transactions only control operations participating in the transaction. If our service sends an email, invokes an external payment API, or publishes a message directly to an independent external system, rolling back the database transaction cannot undo those completed external actions.

For that reason, keeping the transaction focused on the database operations involved in the purchase is generally preferable. Holding a transaction open while waiting for an external network request can also keep database connections and locks occupied longer than necessary, potentially affecting concurrent operations.

In our ordering service, the transaction begins around `placeOrder()`, includes the purchase order insertion and inventory modification, and finishes when Spring processes the method’s outcome. Successful database changes commit within the same transaction, while failures that trigger rollback cause the participating changes to be discarded.

With the transaction boundary established at the service level, we can perform the related repository operations without allowing an earlier successful commit to leave the purchase partially recorded if a later database operation fails.

### Configuring Transaction Behavior

With a transaction boundary established, Spring provides several settings that determine how the transaction responds to exceptions, handles read operations, and interacts with other transactional methods. These settings become important as service methods begin coordinating more database activity, particularly when certain failures need different treatment or multiple services participate in the same operation. Spring Boot 4 and Spring Framework 7 allow us to configure these behaviors through `@Transactional`, giving us control over transaction handling directly from the service methods responsible for database access.

#### Controlling Rollback Rules

Spring’s default transaction behavior depends on the type of exception that interrupts a transactional method. Java distinguishes between checked exceptions, which generally need to be handled or declared, and unchecked exceptions, which can propagate without being declared in the method signature.

By default, Spring rolls back transactions when an exception extending `RuntimeException` escapes the transactional method. Instances of `Error` also trigger rollback, while checked exceptions such as `IOException` don’t automatically cause rollback with the default configuration.

For our earlier ordering service, `IllegalArgumentException` and `IllegalStateException` are both runtime exceptions. If either escapes `placeOrder()`, Spring rolls back the transaction, preventing an unsuccessful purchase from leaving committed database changes.

Checked exceptions need some attention because they don’t receive that same default treatment.

Imagine we’re importing purchase records from a file and saving them through a repository. The method reads each record and inserts it into the database, but an `IOException` could interrupt the import after several records have already been processed.

Without an explicit rollback rule, Spring’s default behavior allows the transaction to commit despite the checked exception escaping the method. That could leave a partially imported collection of records in the database.

We can change this through the `rollbackFor` attribute of `@Transactional`. Let’s create a method that imports purchase orders from a file while treating an `IOException` as a reason to cancel the entire transaction.

```markup
@Transactional(rollbackFor = IOException.class)
public void importOrders(Path file) throws IOException {
    try (BufferedReader reader = Files.newBufferedReader(file)) {
        String line;

        while ((line = reader.readLine()) != null) {
            String[] values = line.split(",");

            Long itemId = Long.parseLong(values[0]);
            int quantity = Integer.parseInt(values[1]);

            orderRepository.save(
                new PurchaseOrder(itemId, quantity)
            );
        }
    }
}
```

For this method, we’re expecting a file containing an item identifier and quantity on each line, with the values divided by a comma. We’ll assume the input follows that format, keeping the focus on transaction behavior rather than file validation.

We begin by opening the file through `Files.newBufferedReader()`, which provides a `BufferedReader` for reading the records individually. Each line is divided into values, converted into the expected Java types, and passed to `orderRepository.save()` as a new `PurchaseOrder`.

The important addition is `rollbackFor = IOException.class`. If reading the file fails after several records have been saved within the transaction, the escaping `IOException` tells Spring to roll back those database changes rather than commit a partial import.

The transaction still rolls back for runtime exceptions because adding `rollbackFor` doesn’t remove Spring’s normal rollback behavior. Instead, it extends the exceptions covered by the transaction’s rollback rules.

We can also specify a broader exception type when the operation should be canceled for any checked exception extending `Exception`:

```markup
@Transactional(rollbackFor = Exception.class)
```

Setting `rollbackFor` to `Exception.class` tells Spring to roll back for checked exceptions extending `Exception`, along with the unchecked exceptions already handled by default. This can be appropriate when a service operation shouldn’t commit after an exception escapes the method, although specifying individual exception types provides more control over which failures require rollback.

Spring Framework 7 also supports configuring rollback for all exceptions at the transaction management level through `@EnableTransactionManagement(rollbackOn = ALL_EXCEPTIONS)`. This capability was introduced in Spring Framework 6.2 and remains available with Spring Boot 4.

The global setting allows applications to adopt rollback behavior that includes checked exceptions without repeating `rollbackFor` across individual methods. It must be explicitly configured, though, because Spring’s default behavior still distinguishes checked exceptions from runtime exceptions.

There’s also an important difference between an exception escaping a method and an exception being caught inside it.

If we catch an exception before it escapes the transactional method, Spring’s transaction interceptor doesn’t automatically treat that caught exception as a reason to roll back.

Think about the ordering service encountering insufficient inventory. We could catch the exception from `reserve()` and return a result rather than allowing the exception to propagate:

```markup
try {
    item.reserve(quantity);
} catch (IllegalStateException ex) {
    return null;
}
```

The catch block prevents the `IllegalStateException` from leaving the transactional method. If no earlier operation has already marked the transaction for rollback, Spring sees a normal method return and proceeds toward committing the transaction.

Because the purchase order was inserted before the inventory reservation, that insertion could be committed despite the failed reservation. The returned `null` value doesn’t tell Spring that the database changes should be discarded.

Catching an exception doesn’t automatically cancel a transaction, so we need to be careful about handling failures inside methods that have already modified database records.

For failures that should cancel the entire operation, allowing the exception to propagate outside the transactional method is generally preferable. Spring can then apply the rollback rules, while the calling layer can handle the exception after the transaction has been completed.

Spring also provides a way to mark the current transaction for rollback manually through `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()`. However, allowing exceptions to propagate generally keeps the service focused on its database operations without introducing direct calls to the transaction infrastructure.

We should also remember that an earlier database or repository failure may have already marked the transaction for rollback. Catching that exception doesn’t necessarily restore the transaction’s ability to commit.

To verify the intended behavior, we can write an integration test that invokes the service and inspects the database afterward. For an insufficient-inventory purchase, the test could record the existing order count, invoke the service with an unavailable quantity, and check that the count hasn’t increased.

Running that verification without a transaction managed by the test itself allows us to examine the service’s transaction behavior rather than relying on an automatic test rollback.

#### Marking Read Operations as Read-Only

Service methods don’t always need to insert records or modify existing data. We regularly retrieve information for controllers, reports, and other application features, and Spring allows us to identify transactions intended exclusively for reading from the database. The `readOnly` attribute of `@Transactional` communicates that intention to the transaction infrastructure. With JPA, this can reduce the persistence processing associated with tracking modifications to entities that we only intend to retrieve.

Let’s create an `InventoryQueryService` that returns the available quantity of an inventory item without modifying its stored values:

```markup
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class InventoryQueryService {

    private final InventoryRepository inventoryRepository;

    public InventoryQueryService(
            InventoryRepository inventoryRepository) {
        this.inventoryRepository = inventoryRepository;
    }

    @Transactional(readOnly = true)
    public int getAvailableQuantity(Long itemId) {
        InventoryItem item = inventoryRepository.findById(itemId)
            .orElseThrow(() ->
                new IllegalArgumentException("Item not found")
            );

        return item.getAvailableQuantity();
    }
}
```

We’ve defined a Spring-managed service with a repository dependency and a public method for retrieving inventory information. The `getAvailableQuantity()` method calls `findById()` to locate the requested entity and throws an exception if the identifier doesn’t correspond to an existing record.

After retrieving the entity, we return the value from `getAvailableQuantity()` without changing any of its fields. The repository handles the database lookup, while the service determines what information should be returned to the caller.

The `@Transactional(readOnly = true)` annotation tells Spring that this method is intended for reading data. With Hibernate, the read-only transaction setting can reduce processing associated with detecting modifications to loaded entities, including changes to the flush behavior.

Spring also communicates the read-only setting to the underlying database infrastructure where supported, allowing the database or JDBC driver to apply its own behavior.

However, `readOnly = true` doesn’t universally prevent database writes.

The annotation communicates a transaction preference rather than providing a guaranteed restriction against modifications. Depending on the database and transaction manager, certain writes may be rejected, while other configurations don’t enforce that restriction.

We should therefore keep methods marked as read-only focused on retrieval operations instead of depending on the annotation to prevent accidental updates.

Spring Data JPA already provides read-only transaction settings for inherited repository reading methods, which is worth keeping in mind before adding annotations throughout a service.

Methods such as `findById()` and `findAll()` inherit transactional configuration from Spring Data JPA’s repository implementation. For ordinary calls to those methods without an existing transaction, the repository can establish its own read-only transaction.

This means we don’t necessarily need an additional service-level read-only transaction for a method that performs a single repository lookup.

The service annotation becomes more valuable when several database queries need to execute within a common transaction boundary.

Imagine we’re building a reporting service that retrieves purchase orders, loads their associated inventory records, and calculates information from the retrieved entities. By placing a read-only transaction around the service method, we keep those repository operations within the same transaction and JPA persistence context.

Sharing the persistence context can also help when accessing lazily loaded entity relationships during service execution, provided the required entities remain associated with the active persistence context.

Still, a read-only transaction doesn’t automatically guarantee that every query observes an identical database snapshot. The visibility of concurrent changes depends on the database’s transaction isolation level.

For our inventory query service, the main benefit is communicating that the method retrieves data without intending to modify it. This gives Spring and Hibernate information they can use when managing the persistence context and database interaction, while the service remains responsible for performing only the intended reading operations.

#### Recognizing Calls That Bypass the Transaction Proxy

Spring normally applies `@Transactional` through proxies that intercept calls to Spring-managed service methods. The proxy allows Spring to begin or join a transaction before passing execution to the actual method, applying the transaction settings declared on that method.

This mechanism explains why an annotated method can sometimes execute without its expected transaction settings being applied. What matters is how execution reaches the method.

When we invoke a transactional service through an injected Spring-managed bean, the call passes through Spring’s proxy. The transaction infrastructure can then inspect the annotation and apply the associated settings before the method executes. Calls between methods inside the same service instance behave differently because they don’t pass through that proxy.

Returning to our `OrderService`, imagine we add a method that internally calls the existing `placeOrder()` method:

```markup
public Long submitInternalOrder(Long itemId, int quantity) {
    return placeOrder(itemId, quantity);
}
```

We’ve introduced `submitInternalOrder()` as an ordinary public method without `@Transactional`. Its implementation calls the existing `placeOrder()` method directly from the same service instance.

If another component invokes `submitInternalOrder()`, Spring doesn’t establish a service-level transaction for that outer method because it has no transactional annotation.

The internal call to `placeOrder()` also doesn’t pass through the transaction proxy. As a result, the `@Transactional` annotation on `placeOrder()` isn’t applied to this invocation. That can recreate the earlier problem where repository operations execute within their individual transactions rather than participating in a transaction covering the entire purchase.

The annotation on `placeOrder()` remains valid, but Spring needs the call to reach the method through its transaction infrastructure for those settings to be applied.

We can address this by moving the calling operation into a different Spring-managed service. Through dependency injection, we’ll receive a reference to the transactional service that allows Spring to intercept the call.

For our ordering operation, let’s introduce a `CheckoutService` responsible for forwarding purchase requests to `OrderService`:

```markup
import org.springframework.stereotype.Service;

@Service
public class CheckoutService {

    private final OrderService orderService;

    public CheckoutService(OrderService orderService) {
        this.orderService = orderService;
    }

    public Long submit(Long itemId, int quantity) {
        return orderService.placeOrder(itemId, quantity);
    }
}
```

The `CheckoutService` constructor receives the Spring-managed `OrderService` bean. When we call `submit()`, it forwards the purchase request through that injected reference rather than calling a method on its own instance.

Spring can intercept the call to `orderService.placeOrder()` and apply the `@Transactional` annotation before the ordering operation executes.

This keeps the purchase transaction in the service responsible for modifying the database, while the checkout service coordinates access to that operation.

We could also place `@Transactional` on the outer method when it represents the complete database operation. The appropriate location depends on which method should establish the transaction boundary.

There’s an important distinction involving transactions that are already active.

Calling an annotated method from the same instance doesn’t cancel an existing transaction. If the outer method was invoked through Spring’s proxy and already established a transaction, the internal method executes within that existing transactional context.

What the internal call cannot do through ordinary proxy interception is apply the called method’s own transaction settings independently.

This becomes relevant when the called method declares different propagation behavior, a different isolation level, or other transactional attributes. Those settings aren’t applied merely because execution enters the annotated method through an internal Java call.

Private helper methods have a related limitation. Spring’s ordinary proxy-based transaction management cannot intercept private method calls, so placing `@Transactional` on a private helper doesn’t establish the expected transaction boundary.

Keeping transactional service methods public and calling them through Spring-managed beans gives us a consistent way to apply the intended transaction settings.

We also need to pay attention to thread boundaries. Transactions managed through the ordinary JPA transaction manager are associated with the current execution thread. If a service starts database operations through `@Async`, a new thread, or an executor, the caller’s transaction isn’t automatically transferred into that execution.

Database operations running asynchronously therefore need an appropriate transaction boundary of their own.

This distinction is important for services that perform background processing because an annotation on the original calling method doesn’t automatically cover database operations executed later in a different thread.

#### Controlling Transaction Participation

Transactions can involve calls across multiple services, and Spring needs to determine how those methods participate when a transaction is already active.

The `propagation` attribute of `@Transactional` controls this behavior. It determines if a transactional method joins an existing transaction, establishes an independent transaction, or follows a different participation rule.

Spring’s default propagation setting is `Propagation.REQUIRED`.

With `REQUIRED`, Spring joins an existing transaction when an appropriate transaction is available. If the calling thread doesn’t already have a transaction managed by the selected transaction manager, Spring starts a new transaction.

We can explicitly declare that setting through the annotation:

```markup
@Transactional(propagation = Propagation.REQUIRED)
```

This declaration provides the same propagation behavior as the default `@Transactional` annotation. We don’t normally need to specify it unless we’re documenting a particular transaction requirement or comparing it with a different propagation option.

Think about our ordering service calling a second transactional service that updates a related database record.

If both methods use `REQUIRED`, the second service participates in the transaction already established by the first. Its database changes belong to the same transaction, so an eventual rollback can discard changes made by both services.

This behavior is valuable when multiple service methods contribute to the same database operation, allowing the outer service to coordinate their database changes within a shared transaction.

There is, however, an important consequence when an inner transactional method encounters an exception.

If the inner method marks the shared transaction for rollback, catching its exception in the outer method doesn’t automatically make the transaction eligible for commit again.

The outer method can finish normally and attempt to commit, but Spring recognizes that the transaction has already been marked for rollback. In that situation, the outer caller can receive an `UnexpectedRollbackException`, indicating that its attempted commit couldn’t succeed because the shared transaction was rolled back.

This prevents callers from receiving an apparently successful transaction result when the database changes were actually discarded.

Spring also provides `Propagation.REQUIRES_NEW` for operations that need an independent transaction:

```markup
@Transactional(propagation = Propagation.REQUIRES_NEW)
```

With `REQUIRES_NEW`, Spring begins a new transaction for the annotated method rather than participating in an existing transaction. If an outer transaction is active, Spring suspends its transaction context while the independent transaction executes, provided the transaction manager supports that behavior.

The new transaction can commit or roll back independently of the outer transaction.

This can be appropriate for certain auditing operations where the application needs to record a failure even if the business operation that produced it is rolled back.

For instance, we could create an auditing service that stores an event through an `AuditRepository`, giving the audit operation its own transaction:

```markup
@Service
public class AuditService {

    private final AuditRepository auditRepository;

    public AuditService(AuditRepository auditRepository) {
        this.auditRepository = auditRepository;
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void recordFailure(Long orderId, String reason) {
        auditRepository.save(
            new AuditEntry(orderId, reason)
        );
    }
}
```

For this example, we’re assuming `AuditEntry` is a JPA entity representing a stored audit event and `AuditRepository` is its corresponding Spring Data JPA repository.

We’ve placed `REQUIRES_NEW` on `recordFailure()` so the audit entry can be persisted within its own transaction. If the method is invoked through the Spring-managed `AuditService` proxy while an ordering transaction is active, Spring suspends the ordering transaction and establishes a new transaction for the audit entry.

After the audit operation completes, Spring resumes the suspended transaction.

If the audit transaction commits successfully, its record isn’t automatically rolled back when the original ordering transaction later fails. Similarly, a rollback of the audit transaction doesn’t automatically mark the suspended ordering transaction for rollback.

The outcome still depends on how exceptions propagate through the calling service, so an audit failure that escapes into the outer transactional method can affect that method’s rollback behavior.

We also need to account for database connections when starting independent transactions.

The outer transaction may retain its database connection while the inner transaction requires an additional connection from the connection pool. If several requests use `REQUIRES_NEW` concurrently, the application can exhaust its available connections if the pool doesn’t have enough capacity.

For that reason, independent transactions are generally best reserved for operations that actually require their own commit or rollback behavior.

The proxy limitation discussed earlier also applies to `REQUIRES_NEW`. Calling an annotated method internally from the same service instance doesn’t create the independent transaction through ordinary Spring proxy-based transaction management. The method must be invoked through the appropriate transactional proxy for its propagation setting to take effect.

For most service operations, the default `REQUIRED` propagation setting remains appropriate because related database changes should generally participate in the same transaction.

Transaction propagation should also be distinguished from transaction isolation. Propagation controls how a method participates in an existing transaction, while isolation governs how concurrent transactions interact with database changes. Spring’s default isolation setting delegates to the database, so the resulting behavior depends on the database configuration.

We can configure an isolation level through the `isolation` attribute of `@Transactional`, but changing that setting doesn’t replace database constraints or concurrency controls.

In the ordering service, the `@Version` field on `InventoryItem` remains valuable because multiple customers can attempt to reserve the same inventory record concurrently. The transaction groups the related purchase modifications, while optimistic locking detects conflicting updates that could cause an outdated inventory quantity to overwrite a newer value.

When choosing the appropriate propagation setting for each service method, we control which database operations share a transaction and which need independent commit behavior. Spring handles transaction participation according to those settings, while the service methods remain responsible for the database operations they perform.

### Conclusion

Managing transactions in Spring Boot 4 starts with placing `@Transactional` around service methods that need related database operations to commit or roll back as a single unit. From there, we can adjust rollback rules for different exceptions, mark retrieval methods as read-only, and control how transactions behave across service calls. Keeping transaction boundaries in the right places and accounting for Spring’s proxy behavior helps prevent partial updates while giving us more control over how database changes are committed.

![](https://substackcdn.com/image/fetch/$s_!MMyS!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F83cf90da-0522-4c0f-a7b8-8ce42cdca350_276x276.png)

Spring Boot icon by Icons8
