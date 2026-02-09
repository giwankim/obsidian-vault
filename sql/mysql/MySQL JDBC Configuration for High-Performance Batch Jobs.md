---
title: "MySQL JDBC Configuration for High-Performance Batch Jobs"
source: "https://gist.github.com/benelog/e7560ccf29c4365d939e9c3d210f9086"
author:
  - "[[benelog]]"
published:
created: 2026-02-09
description: "MySQL JDBC Configuration for High-Performance Batch Jobs - mysql-options.adoc"
tags:
  - "clippings"
---
MySQL JDBC Configuration for High-Performance Batch Jobs

Table of Contents

- [Using Server-Side Prepared Statements](https://gist.github.com/benelog/#using-server-side-prepared-statements)
- [Improving Batch Update Performance](https://gist.github.com/benelog/#improving-batch-update-performance)
- [Options for Large-Scale Data Retrieval](https://gist.github.com/benelog/#options-for-large-scale-data-retrieval)
	- [Streaming Results One Row at a Time](https://gist.github.com/benelog/#streaming-results-one-row-at-a-time)
	- [Using Server-side Cursors](https://gist.github.com/benelog/#using-server-side-cursors)

PreparedStatement helps optimize repeated query execution. Instead of declaring the entire SQL string such as `SELECT * FROM CITY WHERE COUNTRY = 'KOREA' AND POPULATION > 10000`, it separates the static SQL structure `SELECT * FROM CITY WHERE COUNTRY = ? AND POPULATION > ?` from the dynamic parameters.

When a query is executed repeatedly, the server only needs to parse and create an execution plan once, cache it, and reuse it with different parameters. This reduces CPU and other resource usage on the server. If the JDBC driver sends only the varying parameters instead of transmitting the entire query for each execution, the amount of network traffic can also be reduced. Whether such optimizations actually occur depends on the DBMS and configuration options.

MySQL provides the `useServerPrepStmts` option to control whether PreparedStatement optimization is performed on the server side.

Since the default value is `false`, the JDBC driver sends the fully substituted SQL string to the server for every execution when no additional configuration is applied. This is referred to as **client-side PreparedStatement** or **emulated PreparedStatement**. This default behavior has the advantage of requiring only one network round-trip per query, but server-side optimizations are not applied.

In environments such as typical web applications, where a variety of queries are executed, it may be more efficient to keep the default behavior while enabling `cachePrepStmts=true` and increasing related cache sizes. <sup>[<a href="https://gist.github.com/benelog/#_footnotedef_1" title="View footnote.">1</a>]</sup>

Setting `useServerPrepStmt=true` enables PreparedStatement parsing on the server side. When a `PreparedStatement` object is created, the template query containing `?` placeholders is first sent to the server, parsed, and prepared. Each time `execute()` is called, only the parameter values are transmitted, and the already-prepared query is executed. If the same query is executed repeatedly, SQL parsing and execution-plan creation occur only once, improving performance and reducing network bandwidth. On the other hand, since at least two network round-trips (prepare, execute) are required to execute a query, performance may actually degrade for queries that are executed only once.

If your application repeatedly executes the same query in MySQL, consider actively enabling useServerPrepStmt=true. In batch jobs where a small number of queries are executed tens of thousands of times, this option can yield significant performance improvements.

In MySQL versions prior to 5.1, using this option prevented the use of the query cache, but from 5.1 onwards, it can be used in conjunction with the server cache. In MariaDB 10.6 and later, additional optimizations reduce metadata retransmission when using `useServerPrepStmts=true`, resulting in even better performance. <sup>[<a href="https://gist.github.com/benelog/#_footnotedef_2" title="View footnote.">2</a>]</sup>

When inserting or updating multiple rows, using the JDBC `Statement.batchUpdate()` method can execute them faster than repeatedly calling `executeUpdate()` for single statements. MySQL can further optimize batchUpdate performance by enabling the rewriteBatchedStatements=true option in the JDBC connection URL.

Since the default value is `false`, it must be explicitly enabled. When enabled, the MySQL JDBC driver combines multiple individual queries into a single statement. For example, let’s look at inserting three rows using batchUpdate with the following INSERT query:

Single INSERT form

```
INSERT INTO access_log(access_date_time, ip, username) VALUES (?, ?, ?);
```

Without `rewriteBatchedStatements=true`, the driver executes the above statement three times. With the option enabled, the driver merges them into a single statement:

Merged INSERT form

```
INSERT INTO access_log(access_date_time, ip, username) VALUES
  (?, ?, ?),
  (?, ?, ?),
  (?, ?, ?);
```

Even when multi-value `VALUES` clauses are not possible, the driver combines multiple INSERT or UPDATE statements separated by `;` into a single transmission. This reduces network round-trips and causes the server to parse and execute the combined query once, improving performance and reducing CPU load. However, since the combined statement takes longer to execute, replication lag may worsen in replicated environments.

Be aware that `rewriteBatchedStatements=true` may conflict with other JDBC options. Using `useServerPrepStmts=true` simultaneously can cause errors. Similarly, specifying `useCursorFetch=true` implicitly enables `useServerPrepStmts=true`, so the same caution applies.

Up to Connector/J 8.0.29, `rewriteBatchedStatements` was documented as ignored when used with `useCursorFetch=true` or `useServerPrepStmts=true`; this restriction was removed in 8.0.30. If the combined batch query exceeds the `max_allowed_packet` limit, an error will occur. To insert or update large volumes at once, increase this setting.

`max_allowed_packet` can be configured in MySQL server settings or per session. You can check it with: `SHOW VARIABLES LIKE 'max%';`Note that the `bulk_insert_buffer_size` setting is only referenced by the MyISAM engine—which is rarely used today—and can be ignored when using InnoDB.

Due to such conflicts and interactions among options, it may be difficult to find a single DB configuration optimized for both reads and writes. Another possible approach is to declare separate data sources in the application for large-scale read and write operations.

In Connector/J versions up to 8.0.28, inserting BLOB (Binary Large Object) values using `batchUpdate` could cause a `NullPointerException`, but this has been fixed in newer versions.<sup>[<a href="https://gist.github.com/benelog/#_footnotedef_3" title="View footnote.">3</a>]</sup>

If an application using Spring Batch with MySQL executes queries through `JdbcCursorItemReader` with default settings, the entire result set will be fetched at once and loaded into the application’s memory. When querying large datasets, this can cause Out Of Memory (OOM) errors. To avoid this, you must use ResultSet streaming or server-side cursors.

ResultSet streaming retrieves query results gradually instead of receiving them all at once.

To use this approach, configure the PreparedStatement as follows:

Creating PreparedStatement for streaming

```
PreparedStatement statement = con.prepareStatement(
    sql,
    ResultSet.TYPE_FORWARD_ONLY,
    ResultSet.CONCUR_READ_ONLY
);

statement.setFetchSize(Integer.MIN_VALUE);
```

Note that calling `setFetchSize(Integer.MIN_VALUE)` is not technically valid per JDBC specification. The Javadoc for the java.sql.Statement interface states that if a value less than 0 is passed to the `setFetchSize(int)` method, it should throw a SQLException. However, since MySQL Connector/J enables streaming mode by passing `Integer.MIN_VALUE` to this method, developers have no choice but to use it that way.

While the streaming mode reduces memory usage, it results in as many network calls as the number of rows. For example, fetching one million rows results in one million network transmissions. Another drawbacks are that you cannot directly control batch size, and no other queries can be executed on the same connection until the ResultSet is closed. <sup>[<a href="https://gist.github.com/benelog/#_footnotedef_4" title="View footnote.">4</a>]</sup>

In Spring Batch, calling `JdbcCursorItemReader.setFetchSize(Integer.MIN_VALUE)` enables the streaming mode.`Statement` creation options such as `ResultSet.TYPE_FORWARD_ONLY` are applied internally within `JdbcCursorItemReader`. If the `JdbcCursorItemReader.verifyCursorPosition` property remains at its default `true`, it conflicts with `TYPE_FORWARD_ONLY` and produces the following error:

Error caused by verifyCursorPosition=true

```
Operation not allowed for a result set of type ResultSet.TYPE_FORWARD_ONLY.; nested exception is java.sql.SQLException:
```

Accordingly, a `JdbcCursorItemReader` configured for per-row streaming should be created as follows:

JdbcCursorItemReader for streaming queries in MySQL

```
return new JdbcCursorItemReaderBuilder<T>()
  .dataSource(this.dataSource)
  .sql(sql)
  .rowMapper(rowMapper)
  .fetchSize(Integer.MIN_VALUE)
  .verifyCursorPosition(false);
```

MySQL server-side cursors work by storing results in a temporary table and allowing the client to fetch the data in configurable chunks. Supported in MySQL 5.0.2 and later, they can be enabled by adding `useCursorFetch=true` to the JDBC URL. Since the default value is `false`, this option must be explicitly enabled if client-side cursors are not desired.

Even with `useCursorFetch=true`, server-side cursors will not be used unless a positive fetch size is specified. This can be configured per query using the `Statement.setFetchSize(int)` method in the JDBC API, or a default value can be set via the `defaultFetchSize` property in the JDBC connection URL. <sup>[<a href="https://gist.github.com/benelog/#_footnotedef_5" title="View footnote.">5</a>]</sup>

As mentioned earlier, enabling the `useCursorFetch=true` option also automatically enables `useServerPrepStmt=true`, so care must be taken to avoid conflicts with the `rewriteBatchedStatements=true` option.

---

[1](https://gist.github.com/benelog/#_footnoteref_1). For performance test cases combining `useServerPrepStmts` and `cachePrepStmts`, see the following articles: [https://vladmihalcea.com/mysql-jdbc-statement-caching/](https://vladmihalcea.com/mysql-jdbc-statement-caching/), [https://tech.kakaopay.com/post/how-preparedstatement-works-in-our-apps/](https://tech.kakaopay.com/post/how-preparedstatement-works-in-our-apps/)

[2](https://gist.github.com/benelog/#_footnoteref_2). This improvement is tracked in [https://jira.mariadb.org/browse/MDEV-19237](https://jira.mariadb.org/browse/MDEV-19237)

[3](https://gist.github.com/benelog/#_footnoteref_3). See release notes: [https://dev.mysql.com/doc/relnotes/connector-j/en/news-8-0-29.html](https://dev.mysql.com/doc/relnotes/connector-j/en/news-8-0-29.html)

[4](https://gist.github.com/benelog/#_footnoteref_4). See: [https://dev.mysql.com/doc/connector-j/en/connector-j-reference-implementation-notes.html](https://dev.mysql.com/doc/connector-j/en/connector-j-reference-implementation-notes.html)

[5](https://gist.github.com/benelog/#_footnoteref_5). See: [https://dev.mysql.com/doc/connector-j/en/connector-j-connp-props-performance-extensions.html](https://dev.mysql.com/doc/connector-j/en/connector-j-connp-props-performance-extensions.html)
