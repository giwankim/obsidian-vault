---
title: "Offset and Keyset Pagination with Spring Data JPA"
source: "https://thorben-janssen.com/offset-and-keyset-pagination-with-spring-data-jpa/"
author:
  - "[[Thorben Janssen]]"
published: 2025-11-26
created: 2026-07-20
description: "Pagination is a common and easy approach to ensure that huge result sets don’t slow down your application. The idea is simple. Instead of fetching the entire result set, you only fetch the subset you want to show in the UI or process in your business code. When doing that, you can choose between 2..."
tags:
  - "clippings"
---

> [!summary]
> Compares offset and keyset pagination in Spring Data JPA. Offset pagination is built in via `Pageable`, `Page`, and `Slice` and works across derived, JPQL, and native queries, but degrades as the offset grows because the database must process all skipped rows. Keyset pagination excludes already-fetched rows with a WHERE predicate instead, and while Spring Data JPA lacks native support, it can be implemented with a composite repository fragment using Hibernate's `getKeyedResultList` API.

Pagination is a common and easy approach to ensure that huge result sets don’t slow down your application. The idea is simple. Instead of fetching the entire result set, you only fetch the subset you want to show in the UI or process in your business code.

When doing that, you can choose between 2 general forms: Offset pagination and keyset pagination.

Offset pagination is easier and more commonly used. Spring Data JPA provides a great abstraction for it that requires almost no custom code.

Keyset pagination is more complex but also more efficient when working with huge result sets. Spring Data JPA doesn’t support it out of the box, but you can build it yourself.

In this article, I will explain the differences between the two pagination approaches, show you how to use Spring Data JPA’s abstraction for offset pagination and explain how to implement keyset pagination.

## Offset vs Keyset Pagination

But before we talk about the implementation details, let me quickly explain the difference between offset and keyset pagination.

You most likely know offset pagination from your SQL statements. In SQL, it consists of an offset and a limit clause. Those tell the database to skip the *offset* number of rows and return the following *limit* number of rows. This is simple and commonly used, but it slows down as the offset increases because the database still needs to build the entire result set and process all skipped rows.

Keyset pagination uses a different approach. Instead of skipping rows, it excludes the records that were already returned from the result set. This requires a unique sort order, often based on the primary key and an additional predicate in the where clause. That makes it a little more complex, but it’s more efficient for large datasets because the database can skip directly to the next set of rows.

OK, enough theory. Let’s use both pagination options with Spring Data JPA

## Offset Pagination with Spring Data JPA

Offset pagination is the default approach supported by Spring Data JPA. It builds on the `Pageable` interface that gets provided as a method parameter and works well for most use cases.

```java
Page<T> findAll(Pageable pageable);
```

When you request a `Page`, Spring Data JPA generates a query that uses offset pagination to retrieve the defined number of rows. You can then access the result as a `Slice` or a `Page`.

A `Slice` only contains the requested records, the size of the current slice, and whether additional slices exist.

A `Page` includes more metadata, such as the total number of elements and pages. Spring Data JPA needs to execute an additional count query to provide this information.

Here is a simple example using the `findAll` method of `PagingAndSortingRepository`. You create a `PageRequest` specifying the page size, the page you want to retrieve, and the ordering of the results, and provide it as a parameter to the `findAll` method.

```java
PageRequest page = PageRequest.of(1, 5, Sort.by("lastName").ascending());
Page<ChessPlayer> players = playerRepo.findAll(page);
assertThat(players.getNumber()).isEqualTo(1);
assertThat(players.getSize()).isEqualTo(5);
assertThat(players.getNumberOfElements()).isEqualTo(5);
assertThat(players.getTotalPages()).isEqualTo(4);
assertThat(players.getTotalElements()).isEqualTo(19);
```

When you execute this code, Spring Data JPA generates two queries. The first retrieves the selected rows, and the second counts the total number of elements to calculate the page’s metadata.

```sql
10:51:03.854+01:00 DEBUG 22266 --- [Pagination] [           main] org.hibernate.SQL                        :
    select
        cp1_0.id,
        cp1_0.birth_date,
        cp1_0.first_name,
        cp1_0.last_name,
        cp1_0.version
    from
        chess_player cp1_0
    order by
        cp1_0.last_name
    offset
        ? rows
    fetch
        first ? rows only
10:51:03.886+01:00 DEBUG 22266 --- [Pagination] [           main] org.hibernate.SQL                        :
    select
        count(cp1_0.id)
    from
        chess_player cp1_0
```

### Pagination in Derived Queries

Spring Data JPA also applies pagination if you declare derived queries that return a `Page` or a `Slice` and expect a `Pageable` instance as the last parameter.

Here is a simple example:

```java
public interface ChessPlayerRepository extends JpaRepository<ChessPlayer, Long> {

    Page<ChessPlayer> findByLastName(String lastName, Pageable page);

    Slice<ChessPlayer> findSlicedByLastName(String lastName, Pageable page);
}
```

You use these methods in the same way as the previous example. You create a `PageRequest` specifying the page size, the page you want to retrieve, and the ordering of the results, and set it as a parameter.

```java
PageRequest page = PageRequest.of(1, 5, Sort.by("lastName"));
Page<ChessPlayer> players = playerRepo.findByLastName("Doe", page);
```

As in the previous example, Spring Data JPA generates and executes a count query, if your derived query returns a `Page`.

```sql
10:48:42.760+01:00 DEBUG 18942 --- [Pagination] [           main] org.hibernate.SQL                        :
    select
        cp1_0.id,
        cp1_0.birth_date,
        cp1_0.first_first_name,
        cp1_0.last_name,
        cp1_0.version
    from
        chess_player cp1_0
    where
        cp1_0.last_name=?
    order by
        cp1_0.last_name
    offset
        ? rows
    fetch
        first ? rows only
10:48:42.784+01:00 DEBUG 18942 --- [Pagination] [           main] org.hibernate.SQL                        :
    select
        count(*)
    from
        chess_player cp1_0
    where
        cp1_0.last_name=?
```

If you return a `Slice`, Spring Data JPA does not generate a count query. It only executes the query that fetches the data.

```sql
10:48:44.810+01:00 DEBUG 18942 --- [Pagination] [           main] org.hibernate.SQL                        :
    select
        cp1_0.id,
        cp1_0.birth_date,
        cp1_0.first_name,
        cp1_0.last_name,
        cp1_0.version
    from
        chess_player cp1_0
    where
        cp1_0.last_name=?
    order by
        cp1_0.last_name
    offset
        ? rows
    fetch
        first ? rows only
```

### Pagination in Custom Queries

If you prefer to define your own query with `@Query`, Spring Data JPA can still provide offset pagination. If the return type is a `Page`, Spring Data JPA generates and executes a count query.

Here is a simple example using a `@Query` annotation:

```java
public interface ChessPlayerRepository extends JpaRepository<ChessPlayer, Long> {

    @Query("SELECT p FROM ChessPlayer p WHERE upper(p.lastName) LIKE upper(:lastName)")
    Page<ChessPlayer> findByNamePage(String lastName, Pageable page);

    @Query("SELECT p FROM ChessPlayer p WHERE upper(p.lastName) LIKE upper(:lastName)")
    Slice<ChessPlayer> findByNameSlice(String lastName, Pageable page);
}
```

I skip the log output and usage example here because it’s identical to the previous ones.

### Pagination in Native Queries

Pagination for native queries works in almost the same way. The only difference is that Spring Data JPA can’t generate a count query for native SQL statements. So, if you want to get a `Page`, you must provide both the select query and a separate `countQuery`.

```java
public interface ChessPlayerRepository extends JpaRepository<ChessPlayer, Long> {

    @Query(value = "SELECT * FROM Chess_Player p WHERE upper(p.last_name) LIKE upper(:lastName)",
            countQuery = "SELECT count(p.id) FROM Chess_Player p WHERE upper(p.last_name) LIKE upper(:lastName)",
            nativeQuery = true)
    Page<ChessPlayer> findByNameNative(String lastName, Pageable page);
}
```

When you call the `findByNameNative` method, Spring Data JPA executes both queries and initializes the `Page` instance with the results.

```sql
10:43:12.574+01:00 DEBUG 10810 --- [Pagination] [           main] org.hibernate.SQL                        :
    SELECT
        *
    FROM
        Chess_Player p
    WHERE
        upper(p.last_name) LIKE upper(?)
    order by
        p.last_name asc
    offset
        ? rows
    fetch
        next ? rows only
10:43:12.605+01:00 DEBUG 10810 --- [Pagination] [           main] org.hibernate.SQL                        :
    SELECT
        count(p.id)
    FROM
        Chess_Player p
    WHERE
        upper(p.last_name) LIKE upper(?)
```

As you can see, Spring Data JPA provides the same offset pagination support for derived, custom JPQL, and native SQL queries.

## Keyset Pagination with Spring Data JPA

Unfortunately, Spring Data JPA doesn’t provide keyset pagination out of the box. But you can easily implement it yourself using a [composite repository](https://thorben-janssen.com/composite-repositories-spring-data-jpa/) and Hibernate’s keyset pagination support.

OK, let’s build this step by step, starting with the composite repository. It requires 3 things:

1. You have to define an interface with the method(s) you want to implement yourself. This is called a fragment repository.
2. You have to implement that interface. The name of that class should be the same as the interface with an `Impl` suffix. Spring Data will then pick it up automatically.
3. Your repository has to extend one of Spring Data’s standard repositories and your fragment repository.

So, for this article’s example, the fragment repository might look like this:

```java
public interface ChessPlayerKeysetPaginationRepository {
    PagedList<ChessPlayer> findByName(String lastName, int pageSize, PagedList<ChessPlayer> previousPage);
}
```

Thanks to Hibernate’s keyset pagination support, the implementation of that method is simple. You get the current `Session` and use it to create a query.

Then you call the `getKeyedResultList` method to define the pagination. If you’re requesting the first page, you have to specify the page size and the ordering of your query results. For the following pages, you can simply provide the return value of the `getNextPage` method of your current `KeyedResultList` object.

```java
@Component
public class ChessPlayerKeysetPaginationRepositoryImpl implements ChessPlayerKeysetPaginationRepository {

    @PersistenceContext
    private EntityManager em;

    @Override
    public KeyedResultList<ChessPlayer> findByName(String lastName, int pageSize, KeyedResultList<ChessPlayer> previousPage) {
        KeyedResultList<ChessPlayer> players;
        var query = em.unwrap(Session.class)
                .createQuery("from ChessPlayer where lastName=:lastName", ChessPlayer.class)
                .setParameter("lastName", lastName);
        if (previousPage == null) {
            players = query.getKeyedResultList(Page.first(pageSize)
                                                    .keyedBy(Order.asc(ChessPlayer.class, "id")));
        } else {
            players = query.getKeyedResultList(previousPage.getNextPage());
        }
        return players;
    }
}
```

Here is a simple test that loads the first and second page:

```java
var players = playerRepo.findByName("Doe", 5, null);

players = playerRepo.findByName("Doe", 5, players);
```

The following log output highlights the difference between offset and keyset pagination.
Keyset pagination inserts a predicate into the `WHERE` clause that excludes rows that have already been retrieved. This enables you to always use an offset of zero and fetch the first n rows.

```sql
16:04:30.029+01:00 DEBUG 56601 --- [Pagination] [           main] org.hibernate.SQL                        :
    select
        cp1_0.id,
        cp1_0.birth_date,
        cp1_0.first_name,
        cp1_0.last_name,
        cp1_0.version
    from
        chess_player cp1_0
    where
        cp1_0.last_name=?
    order by
        1
    offset
        ? rows
    fetch
        first ? rows only
16:04:30.033+01:00 TRACE 56601 --- [Pagination] [           main] org.hibernate.orm.jdbc.bind              : binding parameter (1:VARCHAR) <- [Doe]
16:04:30.033+01:00 TRACE 56601 --- [Pagination] [           main] org.hibernate.orm.jdbc.bind              : binding parameter (2:INTEGER) <- [0]
16:04:30.033+01:00 TRACE 56601 --- [Pagination] [           main] org.hibernate.orm.jdbc.bind              : binding parameter (3:INTEGER) <- [6]
16:04:30.055+01:00 DEBUG 56601 --- [Pagination] [           main] org.hibernate.SQL                        :
    select
        cp1_0.id,
        cp1_0.birth_date,
        cp1_0.first_name,
        cp1_0.last_name,
        cp1_0.version
    from
        chess_player cp1_0
    where
        cp1_0.last_name=?
        and cp1_0.id>?
    order by
        1
    fetch
        first ? rows only
16:04:30.055+01:00 TRACE 56601 --- [Pagination] [           main] org.hibernate.orm.jdbc.bind              : binding parameter (1:VARCHAR) <- [Doe]
16:04:30.055+01:00 TRACE 56601 --- [Pagination] [           main] org.hibernate.orm.jdbc.bind              : binding parameter (2:BIGINT) <- [9]
16:04:30.056+01:00 TRACE 56601 --- [Pagination] [           main] org.hibernate.orm.jdbc.bind              : binding parameter (3:INTEGER) <- [6]
```

This is the key difference. Offset pagination tells the database to create the entire result set and skip a specified number of rows. The higher that number gets, the more inefficient this offset pagination becomes.

Keyset pagination excludes records that have already been retrieved based on the last row of the previous page. As a result, it’s more efficient if you have to iterate over a large result set.

## Summary

Spring Data JPA makes offset pagination easy. It supports Page and Slice, works with derived, custom, and native queries, and handles count queries automatically.

But Offset pagination becomes inefficient when you use large offsets.

Keyset pagination avoids this problem. It requires a unique sort order and adds a predicate that excludes already processed rows. With a small fragment repository and an implementation using Hibernate’s keyset pagination support, you can easily add it to your repository.
