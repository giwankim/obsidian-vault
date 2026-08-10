---
title: "Using Spring Data JDBC With Kotlin"
source: "https://blog.jetbrains.com/idea/2026/04/using-spring-data-jdbc-with-kotlin/"
author:
  - "[[Teodor Irkhin]]"
published: 2026-04-09
created: 2026-08-10
description: "This post was written together with Thorben Janssen, who has more than 20 years of experience with JPA and Hibernate and is the author of “Hibernate Tips: More than 70 Solutions to Common Hiberna"
tags:
  - "clippings"
---

> [!summary]
> A JetBrains walkthrough (with Thorben Janssen) of Spring Data JDBC in Kotlin, covering aggregate roots as immutable `data` classes, constructor-based mapping, `CrudRepository` with derived and `@Query` methods, `data` class projections, and one-to-many child entities. It highlights how `@JvmInline value` classes map to columns out of the box, where Java needs the heavier `@Embedded` entity concept plus far more boilerplate. The core model is explicit and stateless: no dirty checking or proxies, `save()` just branches on whether the ID is null, and reads/writes always load and persist the entire aggregate.

[Features](https://blog.jetbrains.com/idea/category/features/) [Kotlin](https://blog.jetbrains.com/idea/category/kotlin/)

Read this post in other languages:

- [简体中文](https://blog.jetbrains.com/zh-hans/idea/2026/05/using-spring-data-jdbc-with-kotlin/)

*This post was written together with [Thorben Janssen](https://thorben-janssen.com/), who has more than 20 years of experience with JPA and Hibernate and is the author of “Hibernate Tips: More than 70 Solutions to Common Hibernate Problems” and the JPA newsletter.*

Spring Data JDBC provides a simple and predictable persistence model. It focuses on aggregate roots, constructor-based mapping, and clear rules for reading and writing data. If you enjoy working with explicit data flows and want full control over your SQL, Spring Data JDBC might be the perfect framework for your project.

And with Kotlin, everything becomes so much easier. Its focus on immutability, null safety, and concise data structures aligns nicely with Spring Data JDBC’s design. In this article, you will see how to model aggregates, store and retrieve data, use `value` objects, handle child entities, and define custom queries using Kotlin.

## Kotlin’s strengths for JDBC-based persistence

Before looking at concrete examples, it helps to understand why Kotlin fits so well into this programming model.

`Data` classes keep your aggregates concise. They define constructor parameters, implement the `equals()`, `hashCode()`, and `toString()` methods, and encourage immutable states. Spring Data JDBC provides strong support for constructor-based mapping and handles immutable aggregates with ease, significantly reducing boilerplate code.

Kotlin’s type system also reduces many common mistakes. Nullability is explicit, so you can see immediately which fields may not contain a value. Constructor-based mapping becomes more reliable because there is no silent conversion of null values into empty strings or default primitives.

Lightweight `value` classes allow you to express domain concepts without adding noise. An email address, a customer number, or a price becomes a first-class concept in your model. And Spring Data JDBC can, of course, map them without requiring any additional boilerplate code or mapping annotations.

Kotlin also simplifies custom query projections, because `data` classes work very well with constructor mapping. Default parameters, named arguments, and collection operations make aggregate updates straightforward.

All these features create a natural fit for Spring Data JDBC and Kotlin.

## Defining an aggregate root with Kotlin

An aggregate is a pattern introduced by [domain-driven design (DDD)](https://martinfowler.com/bliki/DDD_Aggregate.html) concepts. It consists of one or more entities that are handled as a unit when reading or writing them to the database. The aggregate root is the primary object of the aggregate. You address it when referencing the aggregate or when fetching it from the database.

Let’s start with a simple aggregate that only consists of the aggregate root. Each instance is stored as a record in your database whenever you decide to persist or update it. There is no hidden state and no proxying.

The following `data` class represents a person. The `@Table` annotation is optional, but it clearly marks the class as an entity. This helps IntelliJ IDEA to provide you with the most suitable tooling when building your persistence layer.

The `@Id` annotation marks the field as the object’s identifier. The `@Sequence` annotation is optional and tells Spring Data to retrieve a value from the database sequence when persisting a new object. And because this happens after you created a new Person object in your code, the ID field has to be nullable.

If you want, you can define all other fields as non-nullable.

@Table

data class Person(

@Id

@Sequence(sequence = "person\_seq")

val id: Long? = null,

val firstName: String,

val lastName: String

)

@Table data class Person( @Id @Sequence(sequence = "person\_seq") val id: Long? = null, val firstName: String, val lastName: String )

```
@Table
data class Person(
    @Id
    @Sequence(sequence = "person_seq")
    val id: Long? = null,
    val firstName: String,
    val lastName: String
)
```

As you can see in the code snippet, you don’t need to provide any additional mapping annotations. By default, Spring Data JDBC maps the class to a database table with the same name and each field to a column with the same name. You can change this mapping by annotating your class with `@Table` and a field with `@Column`. But most teams try to avoid that to keep their entities easy to read and understand.

By default, Spring Data JDBC uses the primary constructor to create and hydrate entity instances. You can also annotate a constructor with `@PersistenceCreator` if you want Spring Data JDBC to use it instead. This is an excellent match for Kotlin’s `data` classes, because all non-primary-key fields can be immutable, mandatory, and have default values. This helps you avoid uninitialized properties and the need for no-argument constructors that you might be familiar with in Spring Data JPA and other persistence frameworks.

After you define the aggregate, you have to create a repository to manage it.

## Creating repositories and defining queries

Spring Data JDBC uses repository interfaces to define data access operations. The simplest way to define a repository is to extend Spring Data JDBC’s `CrudRepository`.

interface PersonRepository: CrudRepository<Person, Long> {}

interface PersonRepository: CrudRepository<Person, Long> {}

```
interface PersonRepository : CrudRepository<Person, Long> {}
```

This provides you with basic methods, including `save()`, `findById()`, and `deleteById()`.

You can also add your own queries using Spring Data JDBC’s derived query methods. These are methods whose names describe the query that Spring Data JDBC should execute. The framework parses the method name, creates the appropriate SQL statement, and maps the query result.

And if you need more control over the executed query statement, you can define a method, annotate it with `@Query`, and provide your own SQL statement. Spring Data JDBC handles the rest!

Here are a few examples.

interface PersonRepository: CrudRepository<Person, Long> {

fun findByLastName(lastName: String): List\<Person>

@Query("select \* from Person p where p.last\_name =:lastName")

fun getByLastName(lastName: String): List\<Person>

}

interface PersonRepository: CrudRepository<Person, Long> { fun findByLastName(lastName: String): List\<Person> @Query("select \* from Person p where p.last\_name =:lastName") fun getByLastName(lastName: String): List\<Person> }

```
interface PersonRepository : CrudRepository<Person, Long> {
    fun findByLastName(lastName: String): List<Person>

    @Query("select * from Person p where p.last_name = :lastName")
    fun getByLastName(lastName: String): List<Person>
}
```

You can also return Kotlin `data` class projections. This works well when you want to read specific columns but not the entire aggregate, or when you want to transform your data into a different structure.

The following PersonName `data` class and `findPersonNameById` repository method show a typical example.

data class PersonName(

val id: Long,

val name: String

)

interface PersonRepository: CrudRepository<Person, Long> {

@Query("select p.id, p.first\_name || ' ' || p.last\_name as name FROM Person p where p.id =:id")

fun findPersonNameById(id: Long): PersonName

}

data class PersonName( val id: Long, val name: String ) interface PersonRepository: CrudRepository<Person, Long> { @Query("select p.id, p.first\_name || ' ' || p.last\_name as name FROM Person p where p.id =:id") fun findPersonNameById(id: Long): PersonName }

```
data class PersonName(
    val id: Long,
    val name: String
)

interface PersonRepository : CrudRepository<Person, Long> {
    @Query("select p.id, p.first_name || ' ' || p.last_name as name FROM Person p where p.id = :id")
    fun findPersonNameById(id: Long): PersonName
}
```

Spring Data JDBC executes the defined query and maps the query result to the constructor parameters of the `PersonName` class. This keeps the projection code clean and allows you to avoid manual mapping.

2025-12-09T21:59:12.572+01:00 DEBUG 7484 --- \[SDJWithKotlin\] \[ main\] o.s.jdbc.core.JdbcTemplate: Executing prepared SQL statement \[select p.id, p.first\_name || ' ' || p.last\_name as name FROM Person p where p.id =?\]

2025-12-09T21:59:12.595+01:00 INFO 7484 --- \[SDJWithKotlin\] \[ main\] c.t.j.k.s.SpringDataJdbcKotlinTests: PersonName(id=401, name=Jane Smith)

2025-12-09T21:59:12.572+01:00 DEBUG 7484 --- \[SDJWithKotlin\] \[ main\] o.s.jdbc.core.JdbcTemplate: Executing prepared SQL statement \[select p.id, p.first\_name || ' ' || p.last\_name as name FROM Person p where p.id =?\] 2025-12-09T21:59:12.595+01:00 INFO 7484 --- \[SDJWithKotlin\] \[ main\] c.t.j.k.s.SpringDataJdbcKotlinTests: PersonName(id=401, name=Jane Smith)

```
2025-12-09T21:59:12.572+01:00 DEBUG 7484 --- [SDJWithKotlin] [           main] o.s.jdbc.core.JdbcTemplate               : Executing prepared SQL statement [select p.id, p.first_name || ' ' || p.last_name as name FROM Person p where p.id = ?]
2025-12-09T21:59:12.595+01:00  INFO 7484 --- [SDJWithKotlin] [           main] c.t.j.k.s.SpringDataJdbcKotlinTests      : PersonName(id=401, name=Jane Smith)
```

## Persisting and loading aggregates

Working with repositories is straightforward. Each call interacts directly with the database. There is no state tracking or implicit updates. This makes the behavior easy to understand and gives you full control over the executed statements.

@Service

@Transactional

class PersonService(private val personRepository: PersonRepository) {

fun createNewPerson(firstName: String, lastName: String): Person {

// add additional validations and/or logic...

return personRepository.save(

Person(

firstName = firstName,

lastName = lastName

)

)

}

fun updateLastName(id: Long, lastName: String): Person {

val person = personRepository.findById(id).orElseThrow()

val updated = person.copy(lastName = lastName)

return personRepository.save(updated)

}

}

@Service @Transactional class PersonService(private val personRepository: PersonRepository) { fun createNewPerson(firstName: String, lastName: String): Person { // add additional validations and/or logic... return personRepository.save( Person( firstName = firstName, lastName = lastName ) ) } fun updateLastName(id: Long, lastName: String): Person { val person = personRepository.findById(id).orElseThrow() val updated = person.copy(lastName = lastName) return personRepository.save(updated) } }

```
@Service
@Transactional
class PersonService(private val personRepository: PersonRepository) {
    fun createNewPerson(firstName: String, lastName: String): Person {
        // add additional validations and/or logic ...
        return personRepository.save(
            Person(
                firstName = firstName,
                lastName = lastName
            )
        )
    }

    fun updateLastName(id: Long, lastName: String): Person {
        val person = personRepository.findById(id).orElseThrow()
        val updated = person.copy(lastName = lastName)
        return personRepository.save(updated)
    }
}
```

The only logic Spring Data JDBC provides when you call the `save()` method is a check to see if the identifier is `null`. If it is, the record is inserted. Otherwise, an update is executed. Since all fields are immutable, you’re always working with complete and consistent objects.

## Using Kotlin value objects in your aggregate

Real-world aggregates often contain values that deserve their own type. Using Kotlin, you can model them using `value` classes, and Spring Data JDBC supports them out of the box.

If your `value` class only wraps one value, you should annotate it with [@JvmInline](https://kotlinlang.org/docs/inline-classes.html). This activates a Kotlin-specific optimization removing the performance overhead of a wrapper class by replacing it with its inlined value at runtime.

@JvmInline

value class Email(val value: String)

data class Person(

@Id

@Sequence(sequence = "person\_seq")

val id: Long? = null,

val firstName: String,

val lastName: String,

val email: Email

)

@JvmInline value class Email(val value: String) data class Person( @Id @Sequence(sequence = "person\_seq") val id: Long? = null, val firstName: String, val lastName: String, val email: Email )

```
@JvmInline
value class Email(val value: String)

data class Person(
    @Id
    @Sequence(sequence = "person_seq")
    val id: Long? = null,
    val firstName: String,
    val lastName: String,
    val email: Email
)
```

As you can see, Kotlin’s `value` and `data` classes make the code very easy to read and quick to write.

Doing the same in Java requires much more code, an additional mapping annotation and Spring Data JDBC’s embedded entity concept.

@Table

public class Person {

@Id

@Sequence(sequence = "person\_seq")

private Long id;

private String firstName;

private String lastName;

@Embedded.Nullable

private Email email;

public Long getId() {

return id;

}

public void setId(Long id) {

this.id = id;

}

public String getFirstName() {

return firstName;

}

public void setFirstName(String firstName) {

this.firstName = firstName;

}

public String getLastName() {

return lastName;

}

public void setLastName(String lastName) {

this.lastName = lastName;

}

public Email getEmail() {

return email;

}

public void setEmail(Email email) {

this.email = email;

}

}

public class Email {

private String email;

public Email(String email) {

this.email = email;

}

public String getEmail() {

return email;

}

public void setEmail(String email) {

this.email = email;

}

}

@Table public class Person { @Id @Sequence(sequence = "person\_seq") private Long id; private String firstName; private String lastName; @Embedded.Nullable private Email email; public Long getId() { return id; } public void setId(Long id) { this.id = id; } public String getFirstName() { return firstName; } public void setFirstName(String firstName) { this.firstName = firstName; } public String getLastName() { return lastName; } public void setLastName(String lastName) { this.lastName = lastName; } public Email getEmail() { return email; } public void setEmail(Email email) { this.email = email; } } public class Email { private String email; public Email(String email) { this.email = email; } public String getEmail() { return email; } public void setEmail(String email) { this.email = email; } }

```
@Table
public class Person {

    @Id
    @Sequence(sequence = "person_seq")
    private Long id;

    private String firstName;

    private String lastName;

    @Embedded.Nullable
    private Email email;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public Email getEmail() {
        return email;
    }

    public void setEmail(Email email) {
        this.email = email;
    }
}

public class Email {

    private String email;

    public Email(String email) {
        this.email = email;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }
}
```

Java doesn’t know `value` classes. Spring Data JDBC tries to compensate for this by introducing the concept of an [embedded entity](https://docs.spring.io/spring-data/relational/reference/jdbc/mapping.html#entity-persistence.embedded-entities).

You define an embedded entity by creating a Java class with a set of properties. In this example, that’s the `Email` class with its email property. To use the Email class as a property type, you have to annotate it with `@Embedded`. Spring Data JDBC then applies the same mapping we covered in the example demonstrating Kotlin’s `value` class. It maps the `email` field to a database column with the same name, enabling you to use it in all your queries.

So, it looks like you have to write more code and use an embedded entity in Java to get the same result as you got with a simple `value` class in Kotlin. But it’s actually worse than that. In Kotlin, you can annotate your simple `value` classes with `@JvmInline` and get the previously described optimizations. These don’t exist in Java. As a result, your embedded class mapping not only requires more code – it also carries a much greater performance overhead.

Now, let’s get back to our Kotlin-based examples.

Spring Data JDBC maps the value object based on its wrapped value and doesn’t require any additional mapping annotations.

You can even use the `value` class as a parameter type in your derived or custom queries.

interface PersonRepository: CrudRepository<Person, Long> {

fun findByEmail(email: Email): Person?

}

interface PersonRepository: CrudRepository<Person, Long> { fun findByEmail(email: Email): Person? }

```
interface PersonRepository : CrudRepository<Person, Long> {
    fun findByEmail(email: Email): Person?
}
```

2025-12-09T22:03:49.340+01:00 DEBUG 14665 --- \[SDJWithKotlin\] \[ main\] o.s.jdbc.core.JdbcTemplate: Executing prepared SQL statement \[SELECT "person"."id" AS "id", "person"."email" AS "email", "person"."last\_name" AS "last\_name", "person"."first\_name" AS "first\_name" FROM "person" WHERE "person"."email" =?\]

2025-12-09T22:03:49.363+01:00 INFO 14665 --- \[SDJWithKotlin\] \[ main\] c.t.j.k.s.SpringDataJdbcKotlinTests: Person(id=401, firstName=Jane, lastName=Smith, email=Email(value=a@b.com))

2025-12-09T22:03:49.340+01:00 DEBUG 14665 --- \[SDJWithKotlin\] \[ main\] o.s.jdbc.core.JdbcTemplate: Executing prepared SQL statement \[SELECT "person"."id" AS "id", "person"."email" AS "email", "person"."last\_name" AS "last\_name", "person"."first\_name" AS "first\_name" FROM "person" WHERE "person"."email" =?\] 2025-12-09T22:03:49.363+01:00 INFO 14665 --- \[SDJWithKotlin\] \[ main\] c.t.j.k.s.SpringDataJdbcKotlinTests: Person(id=401, firstName=Jane, lastName=Smith, email=Email(value=a@b.com))

```
2025-12-09T22:03:49.340+01:00 DEBUG 14665 --- [SDJWithKotlin] [           main] o.s.jdbc.core.JdbcTemplate               : Executing prepared SQL statement [SELECT "person"."id" AS "id", "person"."email" AS "email", "person"."last_name" AS "last_name", "person"."first_name" AS "first_name" FROM "person" WHERE "person"."email" = ?]
2025-12-09T22:03:49.363+01:00  INFO 14665 --- [SDJWithKotlin] [           main] c.t.j.k.s.SpringDataJdbcKotlinTests      : Person(id=401, firstName=Jane, lastName=Smith, email=Email(value=a@b.com))
```

## Modeling one-to-many relationships

Aggregates can contain collections of child entities. Spring Data JDBC stores each of these entity types in separate tables.

data class Company(

@Id

var id: Long,

val name: String,

val employees: List\<Employee>

)

data class Employee(

@Id

var id: Long,

var name: String

)

data class Company( @Id var id: Long, val name: String, val employees: List\<Employee> ) data class Employee( @Id var id: Long, var name: String )

```
data class Company(
    @Id
    var id: Long,
    val name: String,
    val employees: List<Employee>
)

data class Employee(
    @Id
    var id: Long,
    var name: String
)
```

When you read the aggregate, Spring Data JDBC always fetches the entire aggregate with all child entities. And it handles all write operations the same way. When persisting or updating an aggregate, it writes the entire aggregate with all its entities to the database. This fits well with Kotlin’s immutable list types, but requires some attention when defining your aggregates to avoid performance issues.

## Transactions and practical considerations

Spring Data JDBC integrates with Spring’s transaction management. A transactional boundary ensures that all write operations within the aggregate are applied consistently.

Kotlin reduces many typical pitfalls. Properties must be initialized, nullability is clear, and immutable data helps avoid accidental side effects. When updating an aggregate, you create a new instance with the correct state as opposed to modifying an existing one. This results in a predictable and maintainable persistence layer.

## Conclusion

Spring Data JDBC offers a clear and simple approach to relational persistence. You work with aggregates that are written and read as complete units, and you always know which statements are executed. Kotlin supports this style through immutable data structures, `value` classes, nullability rules, and concise syntax.

If you design your aggregates carefully and treat each instance as a complete snapshot of its state, you can build applications that remain easy to understand and maintain. The combination of Spring Data JDBC and Kotlin gives you a persistence stack that stays simple even as your application grows.

To learn more about persistence with Kotlin, check out our two previous articles in this series:
