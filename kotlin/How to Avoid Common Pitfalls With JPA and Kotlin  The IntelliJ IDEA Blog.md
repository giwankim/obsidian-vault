---
title: "How to Avoid Common Pitfalls With JPA and Kotlin | The IntelliJ IDEA Blog"
source: "https://blog.jetbrains.com/idea/2026/01/how-to-avoid-common-pitfalls-with-jpa-and-kotlin/"
author:
  - "[[Anna Rovinskaia                    January 22]]"
  - "[[2026]]"
  - "[[Marit van Dijk                    September 16]]"
  - "[[2025]]"
  - "[[Irina Mariasova                    September 5]]"
  - "[[Teodor Irkhin                    September 4]]"
  - "[[Teodor Irkhin]]"
  - "[[About the author]]"
published: 2026-01-20
created: 2026-01-26
description: "This article outlines a set of best practices to help you avoid problems and build reliable persistence layers with Kotlin and Jakarta Persistence. And to share some good news before diving in, IntelliJ IDEA 2026.1 will automatically detect many of these issues, highlight them with warnings, and provide support through various inspections."
tags:
  - "clippings"
---
## How to Avoid Common Pitfalls With JPA and Kotlin

*This post was written together with [Thorben Janssen](https://thorben-janssen.com/), who has more than 20 years of experience with JPA and Hibernate and is the author of “Hibernate Tips: More than 70 Solutions to Common Hibernate Problems” and the JPA newsletter.*

Kotlin and Jakarta Persistence (also known as JPA) are a popular combination for server-side development. Kotlin offers concise syntax and modern language features, while Jakarta Persistence provides a proven persistence framework for enterprise applications.

However, Jakarta Persistence was originally designed for Java. Some of Kotlin’s popular features and concepts, like null safety and data classes, help you tremendously when implementing your business logic, but they don’t align well with the specification.

This article outlines a set of best practices to help you avoid problems and build reliable persistence layers with Kotlin and Jakarta Persistence. And to share some good news before diving in, IntelliJ IDEA 2026.1 will automatically detect many of these issues, highlight them with warnings, and provide support through various inspections.

Jakarta Persistence defines several [requirements](https://jakarta.ee/specifications/persistence/3.2/jakarta-persistence-spec-3.2#a18) for entity classes that form the foundation for how persistence providers manage entity objects.

An entity class must:

- **Provide a no-argument constructor**The persistence provider uses reflection to call the no-argument constructor to create entity instances when loading data from the database.
- **Have non-final attributes**When fetching an entity object from the database, the persistence provider sets all attribute values after it calls the no-argument constructor to instantiate the entity object. This process is called hydration.  
	After that is done, the persistence provider keeps a reference to the entity object to perform automatic dirty checks, during which it detects changes and updates the corresponding database records automatically.
- **Be non-final**The persistence provider often creates proxy subclasses to implement features such as [lazy loading](https://www.baeldung.com/hibernate-lazy-eager-loading) for @ManyToOne and @OneToOne relationships. For this to work, the entity class can’t be final.

In addition to these specification requirements, it is a widely accepted best practice to:

- **Implement `equals`, `hashCode`, and `toString` carefully  
	**These methods should rely only on the entity’s identifier and type to avoid unexpected behavior in persistence contexts. You can find approaches for better implementing those [here](https://thorben-janssen.com/ultimate-guide-to-implementing-equals-and-hashcode-with-hibernate/).

These rules are easy to follow in Java but conflict with some of Kotlin’s defaults, such as final classes, immutable properties, and constructor-based initialization.  
  
The following sections show how to adapt your Kotlin classes to meet these requirements while still using Kotlin’s language features effectively.

[Kotlin’s data classes](https://kotlinlang.org/docs/data-classes.html) are designed to hold data. They are final and provide several utility methods, including getters and setters for all fields, as well as `equals`, `hashCode`, and `toString`.

This makes data classes a great fit for DTOs, which represent query results and are not managed by your persistence provider.

Below is a typical usage of a data class to fetch data:

data class EmployeeWithCompany (val employeeName: String, val companyName: String)

val query = entityManager.createQuery ("" "

SELECT new com.company.kotlin.model.EmployeeWithCompany(p.name, c.name)

FROM Employee e

JOIN e.company c

WHERE p.id =:id" "")

val employeeWithCompany = query.setParameter ("id", 1L).singleResult;

data class EmployeeWithCompany(val employeeName: String, val companyName: String) val query = entityManager.createQuery(""" SELECT new com.company.kotlin.model.EmployeeWithCompany(p.name, c.name) FROM Employee e JOIN e.company c WHERE p.id =:id""") val employeeWithCompany = query.setParameter("id", 1L).singleResult;

```
data class EmployeeWithCompany(val employeeName: String, val companyName: String)

val query = entityManager.createQuery("""
   SELECT new com.company.kotlin.model.EmployeeWithCompany(p.name, c.name)
    FROM Employee e
       JOIN e.company c
    WHERE p.id = :id""")

val employeeWithCompany = query.setParameter("id", 1L).singleResult;
```

However, entities differ because they are managed objects. And that causes problems when you model them as a data class.

For entities, the persistence provider automatically detects changes and uses lazy loading for relationships. To support this, it expects entity classes to follow the requirements defined in the Jakarta Persistence specification, which we discussed at the beginning of this chapter.

As you can see in the following table, that makes Kotlin’s data classes a bad fit for entity classes.

|  | **Kotlin Data Class** | **Jakarta Persistence Entity** |
| --- | --- | --- |
| **Class Type** | Final | Must be open (non-final) so the provider can create proxy subclasses |
| **Constructors** | Primary constructor with required parameters | Must provide a no-argument constructor, used by the persistence provider |
| **Mutability** | Immutable by default (val properties) | Must have mutable, non-final attributes so the provider can perform lazy loading as well as detect and persist changes |
| **equals** **and** **hashCode** | Use all properties | Should rely only on type and primary key |
| **toString** | Includes all properties | Should only reference eagerly loaded attributes to avoid additional queries |

The recommended approach is to use regular open classes to model your entities. They are mutable and proxy-friendly, and they don’t cause any issues with Jakarta Persistence.

@Entity

open class Person {

@Id

@GeneratedValue

var id: Long? = null

var name: String? = null

}

@Entity open class Person { @Id @GeneratedValue var id: Long? = null var name: String? = null }

```
@Entity
open class Person {
   @Id
   @GeneratedValue
   var id: Long? = null

   var name: String? = null
}
```

[As discussed earlier](https://blog.jetbrains.com/idea/2026/01/how-to-avoid-common-pitfalls-with-jpa-and-kotlin/#entity-class-design), Jakarta Persistence requires entity classes to be non-final and provide a no-argument constructor.

Kotlin’s classes are final by default and don’t have to offer a no-argument constructor.

But don’t worry, it’s easy to fulfill the requirements without changing your code or implementing your entity classes in a specific way. Just add the no-arg and all-open plugins and add [kotlin-reflect](https://kotlinlang.org/docs/reflection.html) to your dependencies. This adds the required constructor and marks annotated classes as open at build time.

Currently, you need the compiler plugins `plugin.spring` and `plugin.jpa`, which will automatically add the no-arg and all-open plugins. When creating a new Spring project using the *New Project* wizard in IntelliJ IDEA or via [start.spring.io](http://start.spring.io/), both plugins are automatically configured for you. And starting with IntelliJ IDEA 2026.1, this will also be the case when you add a Kotlin file to an existing Java project.

plugins {

kotlin ("plugin.spring") version "2.2.20"

kotlin ("plugin.jpa") version "2.2.20"

}

allOpen {

annotation ("jakarta.persistence.Entity")

annotation ("jakarta.persistence.MappedSuperclass")

annotation ("jakarta.persistence.Embeddable")

}

plugins { kotlin("plugin.spring") version "2.2.20" kotlin("plugin.jpa") version "2.2.20" } allOpen { annotation("jakarta.persistence.Entity") annotation("jakarta.persistence.MappedSuperclass") annotation("jakarta.persistence.Embeddable") }

```
plugins {
   kotlin("plugin.spring") version "2.2.20"
   kotlin("plugin.jpa") version "2.2.20"
}

allOpen {
   annotation("jakarta.persistence.Entity")
   annotation("jakarta.persistence.MappedSuperclass")
   annotation("jakarta.persistence.Embeddable")
}
```

When configuring this manually, pay close attention to both parts of this setup. `plugin.jpa` appears to provide the required configuration, but it only configures the no-arg plugin, not the all-open one. This will be improved with the upcoming JPA plugin update. You will then no longer have to add the allOpen section. See: [KT-79389](https://youtrack.jetbrains.com/issue/KT-79389/Add-allopen-plugin-JPA-preset-to-kotlin.plugin.jpa)

As a Kotlin developer, you’re used to analyzing whether information is mutable or immutable and modelling your classes accordingly. And when defining your entities, you might want to do the same. But that creates potential issues.

In Kotlin, you use val to define an immutable field or property and var for mutable ones. Under the hood, val is compiled in Java to a final field. But as discussed earlier, the Jakarta Persistence specification requires all fields to be non-final.

So, in theory, you can’t use val when modelling your entities. However, if you look at various projects, you can find several entities that use val without causing any bugs.

@Entity

class Person (name: String) {

@Id

@GeneratedValue

var id: Long? = null

val name: String = name

}

@Entity class Person(name: String) { @Id @GeneratedValue var id: Long? = null val name: String = name }

```
@Entity
class Person(name: String) {
   @Id
   @GeneratedValue
   var id: Long? = null

   val name: String = name
}
```

That’s because your Jakarta Persistence implementation, the persistence provider, populates entity fields through reflection if you use field-based access, which is usually the case when implementing Jakarta Persistence entities in Kotlin. `final` fields can also be [modified using reflection](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html#jls-17.5.3). As a result, your persistence provider can modify val fields, but this contradicts Kotlin’s immutability guarantees.

So, practically, you can use `val` to model immutable fields of your entity class. Still, it’s not in line with the Jakarta Persistence specification, and your fields are not as immutable as you might expect. To make it even worse, [JEP 500: Prepare to Make Final Mean Final](https://openjdk.org/jeps/500) discusses introducing a warning and future changes to restrict final field modifications via reflection. This would prevent you from using `val` on your entity fields and break many persistence layers using Jakarta Persistence and Kotlin.

Be careful when using `val` for your entity fields and make sure everyone on your team understands the implications.

Starting with version 2026.1, IntelliJ IDEA will display a weak warning indicating that a val field will be modified when the persistence provider, such as Hibernate or EclipseLink, instantiates the entity object.

The Jakarta Persistence specification defines two access types that determine if your persistence provider uses getter and setter methods to access your entity’s fields or reflection.

You can define the access type explicitly by annotating your entity class with the `@Access` annotation. Or, as almost all development teams do, define it implicitly by where you place your mapping annotations:

- Annotations on entity fields → field access = direct access using reflection
- Annotations on getter methods → property access = access via getter or setter methods

Most Kotlin developers put their annotations on properties, which Hibernate treats as field access by default.

@Entity

class Company {

@Id

@GeneratedValue

var id: Long? = null

var name: String? = null

get () {

println ("Getter called")

return field

}

set (value) {

println ("Setter called")

field = value

}

}

@Entity class Company { @Id @GeneratedValue var id: Long? = null var name: String? = null get() { println("Getter called") return field } set(value) { println("Setter called") field = value } }

```
@Entity
class Company {
   @Id
   @GeneratedValue
   var id: Long? = null

   var name: String? = null
       get() {
           println("Getter called")
           return field
       }
       set(value) {
           println("Setter called")
           field = value
       }
}
```

In this example, it might look like the getter and setter methods will be called to access the name property. But that’s only the case for your business logic. Because we annotated the fields, the persistence provider will use reflection to access them directly, bypassing the getter and setter methods.

As a general best practice, it’s recommended to stick to field access. It’s easier to read and lets your persistence provider access the entity’s fields directly. You can then provide getter and setter methods that help your business code without affecting your database mapping.

If you want to use property access, you can either annotate your entity class with `@Access(AccessType.PROPERTY)` or annotate the accessors explicitly:

@Entity

class Company {

@get:Id

@get:GeneratedValue

var id: Long? = null

var name: String? = null

get () {

println ("Getter called")

return field

}

set (value) {

println ("Setter called")

field = value

}

}

@Entity class Company { @get:Id @get:GeneratedValue var id: Long? = null var name: String? = null get() { println("Getter called") return field } set(value) { println("Setter called") field = value } }

```
@Entity
class Company {
   @get:Id
   @get:GeneratedValue
   var id: Long? = null

   var name: String? = null
       get() {
           println("Getter called")
           return field
       }
       set(value) {
           println("Setter called")
           field = value
       }
}
```

However, when you do this, you must ensure that all fields are defined as `var`. Kotlin doesn’t provide setter methods for fields defined as `val`.

@Entity

class Company {

@get:Id

@get:GeneratedValue

var id: Long? = null

val name: String? = null

}

@Entity class Company { @get:Id @get:GeneratedValue var id: Long? = null val name: String? = null }

```
@Entity
class Company {
   @get:Id
   @get:GeneratedValue
   var id: Long? = null

   val name: String? = null 
}
```

You can see this when checking Kotlin’s decompiled bytecode of a snippet above.

import jakarta.persistence.Entity;

import jakarta.persistence.GeneratedValue;

import jakarta.persistence.Id;

import kotlin.Metadata;

import org.jetbrains.annotations.Nullable;

@Entity

…

public final class Company {

@Nullable

private Long id;

@Nullable

private final String name;

@Id

@GeneratedValue

@Nullable

public final Long getId () {

return this.id;

}

public final void setId (@Nullable Long var1) {

this.id \= var1;

}

@Nullable

public final String getName () {

return this.name;

}

}

import jakarta.persistence.Entity; import jakarta.persistence.GeneratedValue; import jakarta.persistence.Id; import kotlin.Metadata; import org.jetbrains.annotations.Nullable; @Entity … public final class Company { @Nullable private Long id; @Nullable private final String name; @Id @GeneratedValue @Nullable public final Long getId() { return this.id; } public final void setId(@Nullable Long var1) { this.id = var1; } @Nullable public final String getName() { return this.name; } }

```
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import kotlin.Metadata;
import org.jetbrains.annotations.Nullable;

@Entity
…
public final class Company {
  @Nullable
  private Long id;
  @Nullable
  private final String name;

  @Id
  @GeneratedValue
  @Nullable
  public final Long getId() {
     return this.id;
  }

  public final void setId(@Nullable Long var1) {
     this.id = var1;
  }

  @Nullable
  public final String getName() {
     return this.name;
  }
}
```

Your persistence provider will check that each field has a getter and a setter method. As long as you use var to define your entity fields, property access works with Kotlin.

Null safety and default values are two popular features in Kotlin that don’t exist in that form in Java. It’s no surprise that you have to pay special attention if you want to use them in your Jakarta Persistence entities.

Kotlin allows you to define whether a field or property supports `null ` values. Unfortunately, reflection can bypass Kotlin’s null prevention, and as explained earlier, the persistence provider uses reflection to initialize your entity objects.

Even if you define an entity attribute as non-nullable, your persistence provider will set it to `null` if the database contains a `null` value. In your business code, this can lead to runtime exceptions similar to those seen in Java.

@Entity

@ Table (name = "user")

class User (

@Id

var id: Long? = null

var name: String

)

fun testLogic (){

// Suppose the row with id = 1 has name = NULL in the database

val user = userRepository.findById (1).get ()

println ("Firstname: ${user.name}") // null, because Hibernate saves null via reflection

}

@Entity @Table(name = "user") class User( @Id var id: Long? = null var name: String ) fun testLogic(){ // Suppose the row with id = 1 has name = NULL in the database val user = userRepository.findById(1).get() println("Firstname: ${user.name}") // null, because Hibernate saves null via reflection }

```
@Entity
@Table(name = "user")
class User(
   @Id
   var id: Long? = null

   var name: String
)

fun testLogic(){
   // Suppose the row with id = 1 has name = NULL in the database
   val user = userRepository.findById(1).get()
   println("Firstname: ${user.name}") // null, because Hibernate saves null via reflection
}
```

And unfortunately, solving this problem is not as easy as it seems.

You could argue that all non-nullable entity fields should map to a database column with a not-null constraint. So, your database can’t contain any `null` values.

In general, this is a great approach. But it does not eliminate the risk completely. Constraints can get out of sync between different environments or during migrations. Therefore, using not-null constraints on your database is highly recommended, but it doesn’t provide an unbreakable guarantee that you will never fetch a `null` value from the database.

To make it even worse, all Jakarta Persistence implementations call the no-argument constructor of your entity class to instantiate an object and then use reflection to initialize each field. This means that technically, all your entity fields must be nullable.

What does that mean for your entities? Should you use `val` or `var` to model your fields?

That decision is ultimately up to you. Both of them work, but we recommend sticking to the Kotlin way: Use `val` if an entity field is not supposed to be changed by your business logic, and `var` otherwise. However, due to the issues discussed earlier, it is also essential to ensure that everyone on your team is aware that your Jakarta Persistence implementation may set those fields to `null` if your database lacks a not-null constraint.

The previous paragraphs already discussed why all entity fields should be nullable. However, many developers consider primary key attributes to be distinct because the database requires a primary key value, and the Jakarta Persistence specification defines it as immutable. Primary keys are mandatory and immutable as soon as you persist the entity object in your database. But let’s quickly discuss why this doesn’t mean that primary key values should be not-nullable, especially if you’re using database-generated primary key values.

When you want to store a new record in your database, you create a new entity object without a primary key and persist it.

Unfortunately, the Jakarta Persistence specification doesn’t clearly define how to implement the persist operation. But it requires generating a primary key value if none is provided. The handling of provided primary key values differs across implementations, but that’s a topic for a different article.

The important thing here is that all persistence providers treat null as a not-provided primary key value. They then use a database sequence or an auto-incremented column to generate a primary key value and set it on the entity object. Due to this mechanism, the primary key value is `null ` before the entity gets persisted, and changes during the persist operation.

An interesting side note is that Hibernate handles the primary key value 0 differently when calling the persist or the merge method. The persist method throws an exception because it expects the object to be an already-persisted entity. In contrast, Hibernate’s merge method generates a new primary key value and inserts a new record into the database. That’s why you can model a primary key with the default value 0 and save the new entity object using Spring Data JPA. The default repository implementation recognizes the already set primary key value and calls the merge method instead of the persist method.

Now, returning to the initialization of primary key fields.

When you fetch an entity object from the database, your persistence provider uses the parameterless constructor to instantiate a new object. It then uses reflection to set the primary key value before it returns the entity object to your business code.

All of this clearly shows that the Jakarta Persistence specification expects the primary key field to be mutable, even though the primary key value is not allowed to change after it was assigned. To avoid any portability issues across different Jakarta Persistence implementations, use `null ` to represent an undefined primary key value.

@Entity

class Company {

@Id

@GeneratedValue

var id: Long? = null

}

@Entity class Company { @Id @GeneratedValue var id: Long? = null }

```
@Entity
class Company {
   @Id
   @GeneratedValue
   var id: Long? = null
}
```

Kotlin’s support for default values can simplify your business code and prevent `null` values.

@Entity

class Company (

@Id @GeneratedValue

var id: Long? = null,

@NotNull

var name: String = "John Doe",

@Email

var email: String = "default@email.com"

)

@Entity class Company( @Id @GeneratedValue var id: Long? = null, @NotNull var name: String = "John Doe", @Email var email: String = "default@email.com" )

```
@Entity
class Company(
   @Id @GeneratedValue 
   var id: Long? = null,

   @NotNull
   var name: String = "John Doe",

   @Email
   var email: String = "default@email.com"
)
```

However, please be aware that these default values will have no effect when your persistence provider fetches an entity object from the database.

val companyFromDb = companyRepository.findById (1).get ()

println (companyFromDb.email) // <- If email in DB is empty, it will not set to "default@email.com"

val companyFromDb = companyRepository.findById(1).get() println(companyFromDb.email) // <- If email in DB is empty, it will not set to "default@email.com"

```
val companyFromDb = companyRepository.findById(1).get()
println(companyFromDb.email) // <- If email in DB is empty, it will not set to "default@email.com"
```

The Jakarta Persistence specification requires a parameterless constructor that the implementations call when fetching an entity object from the database. After that, they use reflection to map all values retrieved from the database to the corresponding entity fields. As a result, the default values defined in your constructor will not be used, and some fields of your entity object might not be set even though you expect your constructor to assign default values. This may not cause any issues in your application, but it is something you and your team should be aware of.

In Java, annotations are typically applied directly to the field, method, or class you annotate. In Kotlin, by contrast, annotations can target different elements, such as constructor parameters, properties, or fields.

Before Kotlin 2.2, this often caused problems because annotations applied to properties were applied only to the constructor parameter by default. This often caused problems for Jakarta Persistence and validation frameworks. Annotations like `@NotNull`, `@Email`, or even `@Id` didn’t end up where the framework expected them to be. This led to missed validations or mapping issues.

The good news is that this has been improved in Kotlin 2.2. With the new compiler option, which IntelliJ IDEA will suggest enabling, annotations will be applied to the constructor parameter and the property or field by default. So, your code now works as expected without requiring any changes.

To learn more, check out the [blog post](https://blog.jetbrains.com/idea/2025/09/improved-annotation-handling-in-kotlin-2-2-less-boilerplate-fewer-surprises/).

In the upcoming 2026.1 release, IntelliJ IDEA will provide inspections and quick-fixes to address many of the problems mentioned in this article, thereby improving your overall experience. Be sure to update when the release becomes available. Here are a few examples of what you’ll get with the new release:

- Highlighting missing no-arg constructors or final entity classes and suggestions to enable the correct Kotlin plugins.
- Autoconfiguration of all essential setup when configuring Kotlin in the project.
- Detection and quick fix for data classes and val fields on JPA-managed properties.

And other JPA-related updates!

![](https://blog.jetbrains.com/wp-content/uploads/2025/12/Thorben-Janssen-400x400-1.jpg)

#### Thorben Janssen

- Share

[![](https://admin.blog.jetbrains.com/wp-content/uploads/2026/01/IJ-IDEA-BD-25-Billboard-970x250-2x.png)](https://jb.gg/IJ25)

#### Subscribe to IntelliJ IDEA Blog updates

![image description](https://blog.jetbrains.com/wp-content/themes/jetbrains/assets/img/img-form.svg)

[![](https://blog.jetbrains.com/wp-content/uploads/2026/01/Blog_1280x720.png)](https://blog.jetbrains.com/idea/2026/01/intellij-idea-conf-2026-learn-from-the-people-building-the-jvm-ecosystem/)

[You’re invited to IntelliJ IDEA Conf 2026 – a free online conference for developers working across the JVM ecosystem. Join us for two days of in-depth technical talks, practical insights, and conversations with experts who build and shape modern Java and Kotlin development. The conference will ta…](https://blog.jetbrains.com/idea/2026/01/intellij-idea-conf-2026-learn-from-the-people-building-the-jvm-ecosystem/)

[![](https://blog.jetbrains.com/wp-content/uploads/2025/09/IJ-social-BlogSocialShare-1280x720-2x-4.png)](https://blog.jetbrains.com/idea/2025/09/java-25-lts-and-intellij-idea/)

[Full support for Java 25 is available in IntelliJ IDEA!](https://blog.jetbrains.com/idea/2025/09/java-25-lts-and-intellij-idea/)

[![](https://blog.jetbrains.com/wp-content/uploads/2025/09/IJ-social-BlogFeatured-1280x720-2x-2.png)](https://blog.jetbrains.com/idea/2025/09/java-annotated-monthly-september-2025/)

[This month’s Java Annotated Monthly comes with a fresh mix of Java, Kotlin, AI, and tech news, plus a look at some great events you won’t want to miss.](https://blog.jetbrains.com/idea/2025/09/java-annotated-monthly-september-2025/)

[![](https://blog.jetbrains.com/wp-content/uploads/2025/08/IJ-social-BlogFeatured-1280x720-2x-4.png)](https://blog.jetbrains.com/idea/2025/09/improved-annotation-handling-in-kotlin-2-2-less-boilerplate-fewer-surprises/)