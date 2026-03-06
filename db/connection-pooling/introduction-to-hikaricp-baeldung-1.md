---
title: "Introduction to HikariCP | Baeldung"
source: "https://www.baeldung.com/hikaricp"
author:
  - "[[baeldung]]"
published: 2017-05-20
created: 2026-02-12
description: "We learn about the HikariCP JDBC connection pool project."
tags:
  - "clippings"
---
- [1\. Overview](https://www.baeldung.com/#bd-overview)
- [2\. Introduction](https://www.baeldung.com/#bd-introduction)
- [3\. Maven Dependency](https://www.baeldung.com/#bd-maven)
- [4\. Usage](https://www.baeldung.com/#bd-usage)
	- [4.1. Creating a DataSource](https://www.baeldung.com/#bd-1-creating-a-datasource)
	- [4.2. Using a Data Source](https://www.baeldung.com/#bd-2-using-a-data-source)
- [5\. Conclusion](https://www.baeldung.com/#bd-conclusion)

## 1\. Overview

In this introductory tutorial, we’ll learn about the [HikariCP JDBC](https://github.com/brettwooldridge/HikariCP) connection pool project. **This is a very lightweight (at roughly 130Kb) and lightning-fast JDBC connection pooling framework** developed by [Brett Wooldridge](https://github.com/brettwooldridge) around 2012.

## 2\. Introduction

There are several benchmark results available to compare the performance of HikariCP with other connection pooling frameworks, such as *[c3p0](http://www.mchange.com/projects/c3p0/)*, *[dbcp2](https://commons.apache.org/proper/commons-dbcp/)*, *[tomcat](https://tomcat.apache.org/tomcat-9.0-doc/jdbc-pool.html)*, and [*vibur*](http://www.vibur.org/). For example, the HikariCP team published the below benchmarks (original results available [here](https://github.com/brettwooldridge/HikariCP-benchmark)):

![HikariCP-bench-2.6.0](https://raw.githubusercontent.com/wiki/brettwooldridge/HikariCP/HikariCP-bench-2.6.0.png)

The framework is so fast because the following techniques have been applied:

- **Bytecode-level engineering –** some extreme bytecode level engineering (including assembly level native coding) has been done
- **Micro-optimizations –** although barely measurable, these optimizations combined boost the overall performance
- **Intelligent use of the Collections framework –** the *ArrayList<Statement>* was replaced with a custom class, *FastList,* that eliminates range checking and performs removal scans from head to tail

## 3\. Maven Dependency

First, let’s build a sample application to highlight its usage. HikariCP 7.x requires Java 11 or later. For Java 11+, we have:

```xml
<dependency>
    <groupId>com.zaxxer</groupId>
    <artifactId>HikariCP</artifactId>
    <version>7.0.2</version>
</dependency>
```

HikariCP also supports older JDK versions, like 6 and 7. The appropriate versions can be found [here](https://mvnrepository.com/artifact/com.zaxxer) and [here](https://mvnrepository.com/artifact/com.zaxxer), respectively. We can also check the latest versions in the [Central Maven Repository](https://mvnrepository.com/artifact/com.zaxxer).

## 4\. Usage

Now we can create a demo application. Please note that we need to include a suitable JDBC driver class dependency in the *pom.xml*. If no dependencies are provided, the application will throw a *ClassNotFoundException*.

### 4.1. Creating a DataSource

We’ll use HikariCP’s *DataSource* to create a single instance of a data source for our application:

```java
public class DataSource {

    private static HikariConfig config = new HikariConfig();
    private static HikariDataSource ds;

    static {
        config.setJdbcUrl( "jdbc_url" );
        config.setUsername( "database_username" );
        config.setPassword( "database_password" );
        config.addDataSourceProperty( "cachePrepStmts" , "true" );
        config.addDataSourceProperty( "prepStmtCacheSize" , "250" );
        config.addDataSourceProperty( "prepStmtCacheSqlLimit" , "2048" );
        ds = new HikariDataSource( config );
    }

    private DataSource() {}

    public static Connection getConnection() throws SQLException {
        return ds.getConnection();
    }
}
```

One point to note here is the initialization in the *static* block.

[HikariConfig](https://github.com/openbouquet/HikariCP/blob/master/src/main/java/com/zaxxer/hikari/HikariConfig.java) is the configuration class used to initialize a data source. It comes with four well-known, must-use parameters: *username*, *password*, *jdbcUrl*, and *dataSourceClassName*.

Out of *jdbcUrl* and *dataSourceClassName*, we generally use one at a time. However, when using this property with older drivers, we may need to set both properties.

In addition to these properties, there are several other properties available that we may not find offered by other pooling frameworks:

- *autoCommit*
- *connectionTimeout*
- *idleTimeout*
- *maxLifetime*
- *connectionTestQuery*
- *connectionInitSql*
- *validationTimeout*
- *maximumPoolSize*
- *poolName*
- *allowPoolSuspension*
- *readOnly*
- *transactionIsolation*
- *leakDetectionThreshold*

HikariCP stands out because of these database properties. It’s even advanced enough to detect connection leaks by itself.

A detailed description of the above properties can be found [here](https://github.com/brettwooldridge/HikariCP).

We can also initialize *HikariConfig* with a properties file placed in the *resources* directory:

```java
private static HikariConfig config = new HikariConfig(
    "datasource.properties" );
```

The properties file should look something like this:

```xml
dataSourceClassName= //TBD
dataSource.user= //TBD
//other properties name should start with dataSource as shown above
```

In addition, we can use *java.util.Properties-* based configuration:

```java
Properties props = new Properties();
props.setProperty( "dataSourceClassName" , //TBD );
props.setProperty( "dataSource.user" , //TBD );
//setter for other required properties
private static HikariConfig config = new HikariConfig( props );
```

Alternatively, we can initialize a data source directly:

```java
ds.setJdbcUrl( //TBD  );
ds.setUsername( //TBD );
ds.setPassword( //TBD );
```

### 4.2. Using a Data Source

Now that we have defined the data source, we can use it to obtain a connection from the configured connection pool, and perform JDBC related actions.

Suppose we have two tables, named ***dept*** and ***emp,*** to simulate an employee-department use case. We’ll write a class to fetch those details from the database using HikariCP.

Below we’ll list the SQL statements necessary to create the sample data:

```sql
create table dept(
  deptno numeric,
  dname  varchar(14),
  loc    varchar(13),
  constraint pk_dept primary key ( deptno )
);

create table emp(
  empno    numeric,
  ename    varchar(10),
  job      varchar(9),
  mgr      numeric,
  hiredate date,
  sal      numeric,
  comm     numeric,
  deptno   numeric,
  constraint pk_emp primary key ( empno ),
  constraint fk_deptno foreign key ( deptno ) references dept ( deptno )
);

insert into dept values( 10, 'ACCOUNTING', 'NEW YORK' );
insert into dept values( 20, 'RESEARCH', 'DALLAS' );
insert into dept values( 30, 'SALES', 'CHICAGO' );
insert into dept values( 40, 'OPERATIONS', 'BOSTON' );

insert into emp values(
 7839, 'KING', 'PRESIDENT', null,
 to_date( '17-11-1981' , 'dd-mm-yyyy' ),
 7698, null, 10
);
insert into emp values(
 7698, 'BLAKE', 'MANAGER', 7839,
 to_date( '1-5-1981' , 'dd-mm-yyyy' ),
 7782, null, 20
);
insert into emp values(
 7782, 'CLARK', 'MANAGER', 7839,
 to_date( '9-6-1981' , 'dd-mm-yyyy' ),
 7566, null, 30
);
insert into emp values(
 7566, 'JONES', 'MANAGER', 7839,
 to_date( '2-4-1981' , 'dd-mm-yyyy' ),
 7839, null, 40
);
```

Please note, if we use an in-memory database such as H2, we need to automatically load the database script before running the actual code to fetch the data. Thankfully, H2 comes with an *INIT* parameter that can load the database script from the classpath at runtime. The JDBC URL should look like:

```bash
jdbc:h2:mem:test;DB_CLOSE_DELAY=-1;INIT=runscript from 'classpath:/db.sql'
```

We need to create a method to fetch this data from the database:

```java
public static List<Employee> fetchData() throws SQLException {
    String SQL_QUERY = "select * from emp";
    List<Employee> employees = null;
    try (Connection con = DataSource.getConnection();
        PreparedStatement pst = con.prepareStatement( SQL_QUERY );
        ResultSet rs = pst.executeQuery();) {
            employees = new ArrayList<>();
            Employee employee;
            while ( rs.next() ) {
                employee = new Employee();
                employee.setEmpNo( rs.getInt( "empno" ) );
                employee.setEname( rs.getString( "ename" ) );
                employee.setJob( rs.getString( "job" ) );
                employee.setMgr( rs.getInt( "mgr" ) );
                employee.setHiredate( rs.getDate( "hiredate" ) );
                employee.setSal( rs.getInt( "sal" ) );
                employee.setComm( rs.getInt( "comm" ) );
                employee.setDeptno( rs.getInt( "deptno" ) );
                employees.add( employee );
            }
    }
    return employees;
}
```

Then we need to create a JUnit method to test it. Since we know the number of rows in the table *emp*, we can expect that the size of the returned list should be equal to the number of rows:

```java
@Test
public void givenConnection_thenFetchDbData() throws SQLException {
    HikariCPDemo.fetchData();

    assertEquals( 4, employees.size() );
}
```

## 5\. Conclusion

In this brief article, we learned the benefits of using HikariCP, and its configuration.

The code backing this article is available on GitHub. Once you're **logged in as a [Baeldung Pro Member](https://www.baeldung.com/members/)**, start learning and coding on the project.
