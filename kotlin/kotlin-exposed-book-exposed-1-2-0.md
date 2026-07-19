---
title: "Kotlin Exposed Book (Exposed 1.2.0)"
source: "https://debop.notion.site/Kotlin-Exposed-Book-Exposed-1-2-0-1ad2744526b080428173e9c907abdae2"
author:
  - "[[debop]]"
created: 2026-07-19
description: "Index page of debop's Kotlin Exposed Book covering Exposed 1.2.0 — chapters on SQL DSL, DDL/DML, entities, JPA feature conversion, coroutines/virtual threads, Spring Boot integration, multi-tenancy, and high performance, each linking to Notion articles and exposed-workshop GitHub examples."
tags:
  - "clippings"
---

> [!summary]
> Index page of debop's Kotlin Exposed Book covering Exposed 1.2.0, organized as linked tables of Notion chapters with matching example code in the exposed-workshop GitHub repository. Chapters span the SQL DSL (DDL and DML), DAO entities, converting JPA features to Exposed, async/non-blocking alternatives (Hibernate Reactive, Vert.x SQL Client, R2DBC), coroutines and virtual threads, Spring Boot integration, multi-tenancy, and high-performance techniques.

%% Notion 데이터베이스 표를 마크다운 표로 재구성한 클리핑. 원본의 상태 컬럼은 전 항목 '완료'라서 생략함. %%

# Kotlin Exposed Book (Exposed 1.2.0)

> 🇬🇧 영문판: [📗 Kotlin Exposed Book — English](https://www.notion.so/33e2744526b0811a9dccd1629db044eb)

## 1. Kotlin Exposed 소개

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| Kotlin Exposed 소개 | — | March 16, 2025 | [Notion](https://debop.notion.site/Kotlin-Exposed-1b82744526b080f3ace2e7599c7d8cd6) |

## 2. Quick Started

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| Spring Boot Web with Exposed | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/develop/01-spring-boot/spring-mvc-exposed) | March 15, 2025 | [Notion](https://debop.notion.site/Spring-Boot-Web-with-Exposed-1ad2744526b0807f86a1eaaeb4c6baae) |
| Spring Boot Webflux with Exposed | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/develop/01-spring-boot/spring-webflux-exposed) | March 15, 2025 | [Notion](https://debop.notion.site/Spring-Boot-Webflux-with-Exposed-1ad2744526b080db95adc241f749db58) |

## 3. Async/Non-Blocking 지원 DB 라이브러리

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| Async/Non-Blocking 지원 DB 라이브러리 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/develop/02-alternatives-to-jpa) | March 17, 2025 | [Notion](https://debop.notion.site/Async-Non-Blocking-DB-1ad2744526b080608767e69344793e60) |
| Hibernate Reactive | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/develop/02-alternatives-to-jpa/hibernate-reactive-example) | March 27, 2025 | [Notion](https://debop.notion.site/Hibernate-Reactive-1b92744526b080eb8d1dfd93654a16b3) |
| Vert.x SQL Client 소개 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/develop/02-alternatives-to-jpa/vertx-sqlclient-example) | March 29, 2025 | [Notion](https://debop.notion.site/Vert-x-SQL-Client-1ad2744526b08072b431f5b00e0874d9) |
| R2DBC + Spring Data R2DBC | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/develop/02-alternatives-to-jpa/r2dbc-example) | March 29, 2025 | [Notion](https://debop.notion.site/R2DBC-Spring-Data-R2DBC-1ad2744526b080adadc7c737672f32a1) |
| 맺음말 | — | March 29, 2025 | [Notion](https://debop.notion.site/1ad2744526b08050b6b6d8292ccd838b) |

## 4. 준비 및 환경 설정

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| 학습을 위한 테스트를 위한 준비 | — | March 29, 2025 | [Notion](https://debop.notion.site/1ba2744526b080dbb756f4818dc02ae9) |
| bluetape4k 소개 및 활용 방법 | — | March 29, 2025 | [Notion](https://debop.notion.site/bluetape4k-1ba2744526b080ac9165ec59b845dfb8) |
| bluetape4k-exposed-jdbc-tests | — | March 29, 2025 | [Notion](https://debop.notion.site/bluetape4k-exposed-tests-1c52744526b0800d8210dd7121affcbf) |

## 5. Exposed 기본 예제

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| 들어가는 말 | — | March 29, 2025 | [Notion](https://debop.notion.site/1c32744526b080d9b34aca58e3f06d68) |
| Exposed SQL DSL 예제 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/develop/03-exposed-basic/exposed-sql-example) | March 30, 2025 | [Notion](https://debop.notion.site/Exposed-SQL-1c32744526b080e5bbf8e97954a0b04d) |
| Exposed DAO 예제 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/develop/03-exposed-basic/exposed-dao-example) | March 30, 2025 | [Notion](https://debop.notion.site/Exposed-DAO-1c32744526b08037a717cf759d5e4e08) |
| 맺은 말 | — | March 30, 2025 | [Notion](https://debop.notion.site/1c32744526b0805ba414dfb54ec31f92) |

## 6. Exposed DDL by DSL

### 6.1 Connection & Transaction

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| Database 작업 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/04-exposed-ddl/01-connection) | March 30, 2025 | [Notion](https://debop.notion.site/Database-1c32744526b0800bbd68fb65765f10a6) |
| Transaction | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/04-exposed-ddl/01-connection) | March 30, 2025 | [Notion](https://debop.notion.site/Transaction-1c62744526b080b7a0e1ca5bdc22edb4) |
| Connection Pool 사용 | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/04-exposed-ddl/01-connection/src/test/kotlin/exposed/examples/connection/h2/Ex01_H2_ConnectionPool.kt) | March 30, 2025 | [Notion](https://debop.notion.site/Connection-Pool-1c62744526b0805da52cf0913afb9b37) |
| MultiDatabase 사용 | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/04-exposed-ddl/01-connection/src/test/kotlin/exposed/examples/connection/h2/Ex02_H2_MultiDatabase.kt) | March 30, 2025 | [Notion](https://debop.notion.site/MultiDatabase-1c62744526b080b7b741c24cda62ddae) |

### 6.2 DDL

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| 0. 들어가는 말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/04-exposed-ddl/02-ddl) | March 31, 2025 | [Notion](https://debop.notion.site/1ad2744526b080b49844d5d9b3f53584) |
| 1. Database 생성 | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/develop/04-exposed-ddl/02-ddl/src/test/kotlin/exposed/examples/ddl/Ex01_CreateDatabase.kt) | March 31, 2025 | [Notion](https://debop.notion.site/Database-1ad2744526b080de8524df2f0cf58931) |
| 2. Table | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/develop/04-exposed-ddl/02-ddl/src/test/kotlin/exposed/examples/ddl/Ex02_CreateTable.kt) | March 31, 2025 | [Notion](https://debop.notion.site/Create-Table-1ad2744526b0807c93e1c7cb88370c93) |
| 3. Column | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/develop/04-exposed-ddl/02-ddl/src/test/kotlin/exposed/examples/ddl/Ex04_ColumnDefinition.kt) | March 31, 2025 | [Notion](https://debop.notion.site/Column-1ad2744526b0803db345dcba84481bb6) |
| 4. Index | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/develop/04-exposed-ddl/02-ddl/src/test/kotlin/exposed/examples/ddl/Ex05_CreateIndex.kt) | March 31, 2025 | [Notion](https://debop.notion.site/Index-1c32744526b080a7ab0edeacd105cc8e) |
| 5. Sequence | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/develop/04-exposed-ddl/02-ddl/src/test/kotlin/exposed/examples/ddl/Ex06_Sequence.kt) | April 1, 2025 | [Notion](https://debop.notion.site/Sequence-1c32744526b080c49d55d2acee1808e1) |
| 6. Enumeration | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/develop/04-exposed-ddl/02-ddl/src/test/kotlin/exposed/examples/ddl/Ex07_CustomEnumeration.kt) | April 1, 2025 | [Notion](https://debop.notion.site/6-Enumeration-1c32744526b08098abd9f16554fc679b) |
| 8. 맺음말 | — | April 1, 2025 | [Notion](https://debop.notion.site/8-1ad2744526b080328461eed8cd845097) |

## 7. Exposed DML by SQL DSL

### 7.1 DML 함수

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| 들어가는 말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/05-exposed-dml/01-dml) | April 2, 2025 | [Notion](https://debop.notion.site/1ad2744526b0801f8f26ed673c066607) |
| SELECT | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex01_Select.kt) | April 1, 2025 | [Notion](https://debop.notion.site/SELECT-1ad2744526b08022ab21f459db186ae0) |
| INSERT | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex02_Insert.kt) | April 1, 2025 | [Notion](https://debop.notion.site/INSERT-1ad2744526b0805798b9fa34954db83e) |
| UPDATE | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex03_Update.kt) | April 1, 2025 | [Notion](https://debop.notion.site/UPDATE-1ad2744526b0804dbf6efb70ffaf6ccf) |
| Upsert | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex04_Upsert.kt) | April 2, 2025 | [Notion](https://debop.notion.site/Upsert-1c82744526b0805db787d78cfaa2ecb6) |
| DELETE | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex05_Delete.kt) | April 2, 2025 | [Notion](https://debop.notion.site/DELETE-1ad2744526b08085a2c0ed9d22068984) |
| Exists | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex06_Exists.kt) | April 2, 2025 | [Notion](https://debop.notion.site/Exists-1c32744526b080398c06e51680986ab9) |
| DISTINCT | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex07_DistinctOn.kt) | April 2, 2025 | [Notion](https://debop.notion.site/DistinctOn-1c32744526b080bca40fc48ceb22d274) |
| COUNT | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex08_Count.kt) | April 2, 2025 | [Notion](https://debop.notion.site/Count-1c32744526b080a8918df52255e3e508) |
| GROUP BY | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex09_GroupBy.kt) | April 2, 2025 | [Notion](https://debop.notion.site/Group-By-1c32744526b0804b9bece054f7b4722c) |
| ORDER BY | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex10_OrderBy.kt) | April 2, 2025 | [Notion](https://debop.notion.site/ORDER-BY-1c32744526b0807ab091ceaec94dd7d6) |
| JOIN | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex11_Join.kt) | April 3, 2025 | [Notion](https://debop.notion.site/Join-1c32744526b080048b42e5cfb8edad78) |
| INSERT INTO … SELECT | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex12_InsertInto_Select.kt) | April 3, 2025 | [Notion](https://debop.notion.site/INSERT-INTO-SELECT-1c32744526b0803a8a41f02dd3b98d5f) |
| REPLACE | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex13_Replace.kt) | April 3, 2025 | [Notion](https://debop.notion.site/REPLACE-1c32744526b080ff8b5ad25bbbd9705d) |
| MERGE INTO | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex14_MergeSelect.kt) | April 4, 2025 | [Notion](https://debop.notion.site/MERGE-INTO-1c32744526b08065993acc4ac4f455f6) |
| Returning | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex15_Returning.kt) | April 4, 2025 | [Notion](https://debop.notion.site/Returning-1c32744526b0800b9a51f2de2107d6ce) |
| FetchBatchResults | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex16_FetchBatchedResults.kt) | April 4, 2025 | [Notion](https://debop.notion.site/FetchBatchResults-1c32744526b080928660e5a33422c9f6) |
| 집합 연산 (Union, Intersect, Except) | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex17_Union.kt) | April 4, 2025 | [Notion](https://debop.notion.site/Union-1c32744526b080c28ceaf9a3524a427a) |
| Adjust Query | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex20_AdjustQuery.kt) | April 4, 2025 | [Notion](https://debop.notion.site/Adjust-Query-1c32744526b080708913d8b5874adbda) |
| 사칙 연산자 | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex21_Arithmetic.kt) | April 4, 2025 | [Notion](https://debop.notion.site/1c32744526b08052af33d220edd14028) |
| ColumnTransformer | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex22_ColumnWithTransform.kt) | April 4, 2025 | [Notion](https://debop.notion.site/ColumnTransformer-1c32744526b080e6803ee8d22c078375) |
| Conditions | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex23_Conditions.kt) | April 5, 2025 | [Notion](https://debop.notion.site/Conditions-1c32744526b0805ab134e194f6ad860b) |
| Explain | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex30_Explain.kt) | April 5, 2025 | [Notion](https://debop.notion.site/Explain-1c32744526b08065b2cbef1f09aed2b1) |
| Lateral Join | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex40_LateralJoin.kt) | April 5, 2025 | [Notion](https://debop.notion.site/Lateral-Join-1c32744526b080dfb81aeca4c29b5082) |
| CTE (Common Table Expression) | [GitHub](https://github.com/debop/exposed-workshop/tree/main/07-jpa/02-convert-jpa-advanced/src/test/kotlin/exposed/examples/jpa/ex06_cte) | March 10, 2026 | [Notion](https://debop.notion.site/CTE-Common-Table-Expression-1c32744526b0801798f4dd4b5b195986) |
| Dual | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/01-dml/src/test/kotlin/exposed/examples/dml/Ex99_Dual.kt) | April 5, 2025 | [Notion](https://debop.notion.site/Dua-1c32744526b0805c8ef8d45e67a0b83e) |
| 맺음말 | — | April 5, 2025 | [Notion](https://debop.notion.site/1ad2744526b0804fada2da9a513b783b) |

### 7.2 Column Types

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| 들어가는 말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/05-exposed-dml/02-types) | April 9, 2025 | [Notion](https://debop.notion.site/1c32744526b080f59050c875404a0ab6) |
| Boolean Column Type | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/02-types/src/test/kotlin/exposed/examples/types/Ex01_BooleanColumnType.kt) | April 9, 2025 | [Notion](https://debop.notion.site/Boolean-Column-Type-1c32744526b080e6af07eb0af5e14724) |
| Char Column Type | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/02-types/src/test/kotlin/exposed/examples/types/Ex02_CharColumnType.kt) | April 9, 2025 | — |
| Numeric Column Type | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/02-types/src/test/kotlin/exposed/examples/types/Ex03_NumericColumnType.kt) | April 9, 2025 | [Notion](https://debop.notion.site/Numeric-Column-Type-1c32744526b080119d1fca862d6870da) |
| Array Column Type | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/02-types/src/test/kotlin/exposed/examples/types/Ex05_ArrayColumnType.kt) | April 9, 2025 | [Notion](https://debop.notion.site/Array-Column-Type-1c32744526b0805e9934e4f2974e6574) |
| Multi Array Column Type | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/03-types/src/test/kotlin/exposed/examples/types/Ex06_MultiArrayColumnType.kt) | April 9, 2025 | [Notion](https://debop.notion.site/Multi-Array-Column-Type-1c32744526b080648ff3c151008e0b07) |
| Blob Column Type | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/03-types/src/test/kotlin/exposed/examples/types/Ex08_BlobColumnType.kt) | April 9, 2025 | [Notion](https://debop.notion.site/Blob-Column-Type-1c32744526b080d4964dcc0c2833dc38) |
| 맺음말 | — | April 9, 2025 | [Notion](https://debop.notion.site/1c32744526b0804ebba9f2f7527384e5) |

### 7.3 SQL Functions

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| 들어가는 말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/04-functions/src/test/kotlin/exposed/examples/functions/Ex00_FunctionBase.kt) | April 9, 2025 | [Notion](https://debop.notion.site/1ca2744526b080459c76cc551d3be888) |
| Functions | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/03-functions/src/test/kotlin/exposed/examples/functions/Ex01_Functions.kt) | April 9, 2025 | [Notion](https://debop.notion.site/Functions-1ca2744526b08029b4e4e26be5fdb089) |
| Math Functions | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/04-functions/src/test/kotlin/exposed/examples/functions/Ex02_MathFunction.kt) | April 9, 2025 | [Notion](https://debop.notion.site/Math-Functions-1ca2744526b0800e98a7fdafeca32612) |
| 통계를 위한 집계 함수 | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/03-functions/src/test/kotlin/exposed/examples/functions/Ex03_StatisticsFunction.kt) | April 10, 2025 | [Notion](https://debop.notion.site/Statistics-Functions-1ca2744526b08042b4adea861a1218c8) |
| 삼각함수 | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/04-functions/src/test/kotlin/exposed/examples/functions/Ex04_TrigonometricalFunction.kt) | April 10, 2025 | [Notion](https://debop.notion.site/1ca2744526b08078b69aee5e7decad5e) |
| Window Functions | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/04-functions/src/test/kotlin/exposed/examples/functions/Ex05_WindowFunction.kt) | April 10, 2025 | [Notion](https://debop.notion.site/Window-Functions-1ca2744526b0804ea7d1cf4ee189a6d0) |

### 7.4 Transactions

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| Transaction Isolation Level | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/04-transactions/src/test/kotlin/exposed/examples/transactions/Ex01_TransactionIsolation.kt) | April 10, 2025 | [Notion](https://debop.notion.site/Transaction-Isolation-Level-1ca2744526b0809c8f4feb833c9eddb8) |
| Transaction.exec 메소드 | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/04-transactions/src/test/kotlin/exposed/examples/transactions/Ex02_TransactionExec.kt) | April 11, 2025 | [Notion](https://debop.notion.site/Transaction-exec-1ca2744526b0805ca85df3a7fea47975) |
| Parameterized Statement | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/04-transactions/src/test/kotlin/exposed/examples/transactions/Ex03_Parameterization.kt) | April 11, 2025 | [Notion](https://debop.notion.site/Parameterized-Statement-1ca2744526b0803e943feb5462c65eee) |
| Query timeout | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/04-transactions/src/test/kotlin/exposed/examples/transactions/Ex04_QueryTimeout.kt) | April 11, 2025 | [Notion](https://debop.notion.site/Query-timeout-1ca2744526b080029e9fd8d6273d3de8) |
| Rollback Transaction | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/04-transactions/src/test/kotlin/exposed/examples/transactions/Ex06_RollbackTransaction.kt) | April 11, 2025 | [Notion](https://debop.notion.site/Rollback-Transaction-1ca2744526b0803db8a0fb2895802bb1) |
| Nested Transactions | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/04-transactions/src/test/kotlin/exposed/examples/transactions/Ex05_NestedTransactions_Coroutines.kt) | April 11, 2025 | [Notion](https://debop.notion.site/Nested-Transactions-1ca2744526b0803f8a44f44de0595852) |

### 7.5 Exposed Entities

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| 들어가는 말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/05-exposed-dml/02-entities) | April 5, 2025 | [Notion](https://debop.notion.site/1c32744526b08067acacd6f2cd6057a9) |
| Entity | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/05-entities/src/test/kotlin/exposed/examples/entities/Ex01_Entity.kt) | April 6, 2025 | [Notion](https://debop.notion.site/Entity-1c32744526b08033acbaf6ebd2272988) |
| EntityHook | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/05-entities/src/test/kotlin/exposed/examples/entities/Ex02_EntityHook.kt) | April 6, 2025 | [Notion](https://debop.notion.site/EntityHook-1c32744526b080a19e8cf9529df877e4) |
| EntityCache | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/05-entities/src/test/kotlin/exposed/examples/entities/Ex03_EntityCache.kt) | April 7, 2025 | [Notion](https://debop.notion.site/EntityCache-1c32744526b080f1be0dd35ea15f39a6) |
| Entity with Long ID | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/05-entities/src/test/kotlin/exposed/examples/entities/Ex04_LongIdTableEntity.kt) | April 5, 2025 | [Notion](https://debop.notion.site/Entity-with-Long-ID-1c32744526b080c48a4ddc20b29b0d79) |
| Entity with UUID ID | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/05-entities/src/test/kotlin/exposed/examples/entities/Ex05_UUIDTableEntity.kt) | April 5, 2025 | [Notion](https://debop.notion.site/Entity-with-UUID-ID-1c32744526b080b285f3d67d88d983a9) |
| Entity with Non AutoIncrement | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/05-entities/src/test/kotlin/exposed/examples/entities/Ex05_UUIDTableEntity.kt) | April 7, 2025 | [Notion](https://debop.notion.site/Entity-with-Non-AutoIncrement-1c32744526b08032aa08fe62292874c5) |
| Entity with Blob | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/05-entities/src/test/kotlin/exposed/examples/entities/Ex07_EntityWithBlob.kt) | April 7, 2025 | [Notion](https://debop.notion.site/Entity-with-Blob-1c32744526b0802d96d8d6969dade16b) |
| Entity field with transform | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/05-entities/src/test/kotlin/exposed/examples/entities/Ex08_EntityFieldWithTransform.kt) | April 7, 2025 | [Notion](https://debop.notion.site/Entity-field-with-transform-1c32744526b080c9b558e0ace67df99a) |
| Immutable Entity | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/05-entities/src/test/kotlin/exposed/examples/entities/Ex09_ImmutableEntity.kt) | April 6, 2025 | [Notion](https://debop.notion.site/Immutable-Entity-1c32744526b080f29f89d75ec6126f8c) |
| Composite ID Table & Entity | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/05-entities/src/test/kotlin/exposed/examples/entities/Ex10_CompositeIdTableEntity.kt) | April 8, 2025 | [Notion](https://debop.notion.site/Composite-ID-Table-Entity-1c32744526b0806a9ec0e64212588f6a) |
| Foreign ID Entity | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/05-entities/src/test/kotlin/exposed/examples/entities/Ex11_ForeignIdEntity.kt) | April 8, 2025 | [Notion](https://debop.notion.site/Foreign-ID-Entity-1c32744526b08062a65af226f6cf4587) |
| Via | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/05-entities/src/test/kotlin/exposed/examples/entities/Ex12_Via.kt) | April 8, 2025 | [Notion](https://debop.notion.site/Via-1c32744526b080af9e3ecc5b109cad32) |
| 참조 엔티티 정렬 방식 | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/05-entities/src/test/kotlin/exposed/examples/entities/Ex13_OrderedReference.kt) | April 8, 2025 | [Notion](https://debop.notion.site/1c32744526b080c5a580ff2d0d21a6cd) |
| 맺음말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/05-exposed-dml/05-entities) | April 8, 2025 | [Notion](https://debop.notion.site/1c32744526b080db94b7c6291c0679a6) |

## 8. Advanced Features

### 8.1 Exposed 확장 모듈

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| 들어가는 말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/develop/06-advanced) | April 11, 2025 | [Notion](https://debop.notion.site/1c32744526b0803a9babe49810a07a81) |
| Exposed Crypt | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/06-advanced/01-exposed-crypt) | April 12, 2025 | [Notion](https://debop.notion.site/Exposed-Crypt-Module-1c32744526b0802da419d5ce74d2c5f3) |
| Exposed Java Time | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/06-advanced/02-exposed-javatime) | April 12, 2025 | [Notion](https://debop.notion.site/Exposed-Java-Time-1c32744526b0809d85e1d0425038dfdd) |
| Exposed Kotlin DateTime | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/06-advanced/03-exposed-kotlin-datetime) | April 12, 2025 | [Notion](https://debop.notion.site/Exposed-Kotlin-DateTime-Module-1c32744526b0807bb3e8f149ef88f5f5) |
| Exposed Json | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/06-advanced/04-exposed-json) | April 13, 2025 | [Notion](https://debop.notion.site/Exposed-Json-1c32744526b080a9bee3d7b92463e90c) |
| Exposed Money | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/06-advanced/05-exposed-money) | April 13, 2025 | [Notion](https://debop.notion.site/Exposed-Money-1c32744526b08051a216d87ca750d73f) |
| Exposed Jackson 3.x JSON 컬럼 | [GitHub](https://github.com/debop/exposed-workshop/tree/main/06-advanced/11-exposed-jackson3) | March 10, 2026 | — |
| Exposed Google Tink 컬럼 암호화 | [GitHub](https://github.com/debop/exposed-workshop/tree/main/06-advanced/12-exposed-tink) | March 10, 2026 | — |
| 맺음말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/06-advanced) | April 13, 2025 | [Notion](https://debop.notion.site/1c32744526b080968165fe6bf01194ef) |
| Exposed 버전 히스토리 (0.61.0 → 1.1.1) | [GitHub](https://github.com/JetBrains/Exposed/releases) | March 19, 2026 | — |

### 8.2 사용자 정의 컬럼, 테이블, 모듈

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| 들어가는 말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/06-advanced) | April 13, 2025 | [Notion](https://debop.notion.site/1c32744526b0803e81f9cda7332380e3) |
| Custom ColumnTypes | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/06-advanced/06-custom-columns) | April 13, 2025 | [Notion](https://debop.notion.site/Custom-ColumnTypes-1c32744526b0802aa7a8e2e5f08042cb) |
| Custom IdTable & Entities | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/06-advanced/07-custom-entities) | April 13, 2025 | [Notion](https://debop.notion.site/Custom-Table-Entities-1c32744526b0804bad10ea3a0dce6c13) |
| Exposed Jackson | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/06-advanced/08-exposed-jackson) | April 13, 2025 | [Notion](https://debop.notion.site/Exposed-Jackson-1c32744526b0809599a7db2e629a597a) |
| Exposed Fastjson2 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/06-advanced/09-exposed-fastjson2) | April 13, 2025 | [Notion](https://debop.notion.site/Exposed-Fastjson2-1c32744526b08050a9d4de947c3b3f0d) |
| Exposed Jasypt | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/06-advanced/10-exposed-jasypt) | April 14, 2025 | [Notion](https://debop.notion.site/Exposed-Jasypt-1c32744526b080f08ab2f3e21149e9d7) |
| 맺음말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/06-advanced) | April 14, 2025 | [Notion](https://debop.notion.site/1c32744526b0806da6e1d4ccd7f0d532) |

## 9. JPA Features 구현

### 9.1 JPA 기본 기능 구현

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| 들어가는 말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/01-convert-jpa-basic) | April 14, 2025 | [Notion](https://debop.notion.site/1c32744526b080f4b8ced8802c6c9610) |
| Simple Entity | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/01-convert-jpa-basic/src/test/kotlin/exposed/examples/jpa/ex01_simple) | April 14, 2025 | [Notion](https://debop.notion.site/Simple-Entity-1c32744526b08034a4d4c7f1c6ede7b9) |
| Simple Entities | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/01-convert-jpa-basic/src/test/kotlin/exposed/examples/jpa/ex02_entities) | April 14, 2025 | [Notion](https://debop.notion.site/Simple-Entities-1c32744526b080b083f4c6f3c54f1604) |
| Custom Type ID | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/01-convert-jpa-basic/src/test/kotlin/exposed/examples/jpa/ex03_customId) | April 14, 2025 | [Notion](https://debop.notion.site/Custom-Type-ID-1c32744526b080089d20f5f07a4d4f89) |
| Composite ID | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/01-convert-jpa-basic/src/test/kotlin/exposed/examples/jpa/ex04_compositeId) | April 14, 2025 | [Notion](https://debop.notion.site/Composite-ID-1c32744526b0800da40acbee1cbb810c) |
| Relations : one-to-one | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/01-convert-jpa-basic/src/test/kotlin/exposed/examples/jpa/ex05_relations/ex01_one_to_one) | April 14, 2025 | [Notion](https://debop.notion.site/Relations-one-to-one-1ca2744526b080b79134ed0205c83fc6) |
| Relations: one-to-many | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/01-convert-jpa-basic/src/test/kotlin/exposed/examples/jpa/ex05_relations/ex02_one_to_many) | April 15, 2025 | [Notion](https://debop.notion.site/Relations-one-to-many-1ca2744526b080409fe7d3fb20702b4f) |
| Relations: many-to-one | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/01-convert-jpa-basic/src/test/kotlin/exposed/examples/jpa/ex05_relations/ex03_many_to_one) | April 15, 2025 | [Notion](https://debop.notion.site/Relations-many-to-one-1ca2744526b080369a7bd84b22d160b3) |
| Relations: many-to-many | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/01-convert-jpa-basic/src/test/kotlin/exposed/examples/jpa/ex05_relations/ex04_many_to_many) | April 15, 2025 | [Notion](https://debop.notion.site/Relations-many-to-many-1ca2744526b080ad81ace2af9e5f6971) |
| 맺음말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/01-convert-jpa-basic) | April 15, 2025 | [Notion](https://debop.notion.site/1c32744526b0808fb46fc1fa7f3c9333) |

### 9.2 JPA 고급기능 구현

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| 들어가는 말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/02-convert-jpa-advanced) | April 16, 2025 | [Notion](https://debop.notion.site/1c32744526b080a4895dc346e8a83d00) |
| Joins | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/02-convert-jpa-advanced/src/test/kotlin/exposed/examples/jpa/ex01_joins) | April 16, 2025 | [Notion](https://debop.notion.site/Joins-1c32744526b0803f8b84e5dd2d50914c) |
| JPA Inheritance | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/02-convert-jpa-advanced/src/test/kotlin/exposed/examples/jpa/ex03_inheritance) | April 17, 2025 | [Notion](https://debop.notion.site/JPA-Inheritance-1c32744526b08000b202c2f2ada0e736) |
| Auditable Entity | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/07-jpa/02-convert-jpa-advanced/src/test/kotlin/exposed/examples/jpa/ex05_auditable) | April 17, 2025 | [Notion](https://debop.notion.site/Auditable-Entity-1d72744526b080c98328eaddc992c318) |
| Optimistic Lock (@Version) | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/07-jpa/02-convert-jpa-advanced/src/test/kotlin/exposed/examples/jpa/ex07_version/Ex01_Version.kt) | April 17, 2025 | [Notion](https://debop.notion.site/Optimistic-Lock-Version-1d82744526b08017b381e94e8efa5162) |
| 맺음말 | — | April 18, 2025 | [Notion](https://debop.notion.site/1c32744526b0803da45fee1e30469513) |

## 10. Exposed with Async/Non-Blocking

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| 들어가는 말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/08-coroutines) | April 18, 2025 | [Notion](https://debop.notion.site/1c32744526b080369fd4ea57dfb3f4f8) |
| Exposed with Coroutines | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/08-coroutines/01-coroutines-basic) | April 18, 2025 | [Notion](https://debop.notion.site/Exposed-with-Coroutines-1c32744526b080298028e39a7a16c29a) |
| Exposed with Virtual Threads | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/4d89f72e62bc5a65a4d31d6cb599a5c1b978aa46/08-coroutines/02-virtualthreads-basic) | April 18, 2025 | [Notion](https://debop.notion.site/Exposed-with-Virtual-Threads-1c32744526b080bab873c92e8c72f66d) |
| 맺음말 | — | April 18, 2025 | [Notion](https://debop.notion.site/1c32744526b080fd977fdf184569ea34) |

## 11. Exposed with Spring Boot

| 이름 | GitHub | 작성일 | Web | Tag |
| --- | --- | --- | --- | --- |
| 들어가는 말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring) | April 19, 2025 | [Notion](https://debop.notion.site/1c32744526b080bc92ace4a0231f0a02) | |
| Spring Boot AutoConfiguration | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring/01-springboot-autoconfigure) | April 19, 2025 | [Notion](https://debop.notion.site/Spring-Boot-AutoConfiguration-1c32744526b080079af9eb44b62466d0) | |
| Spring TransactionTemplate with Exposed Transaction | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring/02-transactiontemplate) | April 21, 2025 | [Notion](https://debop.notion.site/Spring-TransactionTemplate-with-Exposed-Transaction-1c32744526b080959c0fcf671247e082) | |
| ExposedRepository with Spring Web | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring/04-exposed-repository) | April 21, 2025 | [Notion](https://debop.notion.site/ExposedRepository-with-Spring-Web-1c32744526b080208e5ee03b900d2c5e) | |
| ExposedRepository with Coroutines | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring/05-exposed-repository-coroutines) | April 21, 2025 | [Notion](https://debop.notion.site/ExposedRepository-with-Coroutines-1c32744526b080a1a6cbe2c86c2cb889) | |
| Exposed with Spring Cache | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring/06-spring-cache) | April 20, 2025 | [Notion](https://debop.notion.site/Exposed-with-Spring-Boot-Cache-1d82744526b08062bfcce52d6aab3ef7) | |
| Exposed with Suspended Spring Cache | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring/07-spring-suspended-cache) | April 20, 2025 | [Notion](https://debop.notion.site/Exposed-with-Reactive-Spring-Cache-1db2744526b080769d2ef307e4a3c6c9) | |
| 맺음말 | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring) | April 21, 2025 | [Notion](https://debop.notion.site/1c32744526b0805b89dac4a47017e267) | |
| ⚡ Spring Batch + Exposed + Virtual Threads: Java 21 Kotlin 배치 처리 완전 가이드 | [GitHub](https://github.com/bluetape4k/bluetape4k-projects/tree/main/spring-boot3/batch-exposed) | April 10, 2026 | — | Spring Batch, Exposed, Virtual Threads |

## 12. 실전 Multi tenant Application 제작

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| Multi-tenant App | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/10-multi-tenant) | April 21, 2025 | [Notion](https://debop.notion.site/Multi-tenant-App-1dc2744526b0804a8c65c15312daa59b) |
| Muti-tenant App with Spring Web | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/10-multi-tenant/01-multitenant-spring-web) | April 21, 2025 | [Notion](https://debop.notion.site/Muti-tenant-App-with-Spring-Web-1dc2744526b08084aad8d2cf6c9c055f) |
| Multi-tenant App with Virtual Thread | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/10-multi-tenant/02-mutitenant-spring-web-virtualthread) | April 21, 2025 | [Notion](https://debop.notion.site/Multi-tenant-App-with-Virtual-Threads-1dc2744526b080ff9570cdb59f4a81b5) |
| Multi-tenant App with Spring Webflux and Coroutines | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/10-multi-tenant/03-multitenant-spring-webflux) | April 21, 2025 | [Notion](https://debop.notion.site/Multi-tenant-App-with-Spring-Webflux-and-Coroutines-1dc2744526b0802e926de76e268bd2a8) |
| 맺음말 | — | April 22, 2025 | [Notion](https://debop.notion.site/1dc2744526b080d8bd13e71a678ebf30) |

## 13. High Performance

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| 13.1 Cache Strategies (Blocking) | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/11-high-performance/01-cache-strategies) | March 10, 2026 | — |
| 13.2 Cache Strategies (Coroutines) | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/11-high-performance/02-cache-strategies-coroutines) | March 10, 2026 | — |
| 13.3 Routing DataSource | [GitHub](https://github.com/bluetape4k/exposed-workshop/tree/main/11-high-performance/03-routing-datasource) | March 10, 2026 | — |

## 14. 부록: Exposed 사용 시 대표적 오류 및 개선

| 이름 | GitHub | 작성일 | Web |
| --- | --- | --- | --- |
| Exposed 사용 시 대표적 실수와 개선 방법 | — | April 21, 2025 | [Notion](https://debop.notion.site/Exposed-1da2744526b080798d36cfa73501d06e) |

## 15. Resources

| 이름 | GitHub | 작성일 |
| --- | --- | --- |
| DMLTestData | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/dml/DMLTestData.kt) | April 5, 2025 |
| EntityTestData | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/02-entities/src/test/kotlin/exposed/examples/entities/EntityTestData.kt) | April 5, 2025 |
| Movie and Actors | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/repository/MovieSchema.kt) | April 5, 2025 |
| Board Posts Categories | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/entities/BoardSchema.kt) | April 5, 2025 |
| BlogSchema | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/07-jpa/01-convert-jpa-basic/src/test/kotlin/exposed/examples/jpa/ex02_entities/BlogSchema.kt) | April 5, 2025 |
| OrderSchema | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/mapping/OrderSchema.kt) | April 5, 2025 |
| Bank Entites | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/samples/BankEntities.kt) | April 5, 2025 |
| BookSchema | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/mapping/compositeId/BookSchema.kt) | April 5, 2025 |
| PersonSchema | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/07-jpa/01-convert-jpa-basic/src/test/kotlin/exposed/examples/jpa/ex02_entities/PersonSchema.kt) | April 5, 2025 |
| UserCities | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/samples/UserCities.kt) | April 6, 2025 |

| 이름 | GitHub | 작성일 |
| --- | --- | --- |
| TestDB | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/tests/TestDB.kt) | April 11, 2025 |
| withDb | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/tests/TestDB.kt) | April 11, 2025 |
| withTables | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/tests/WithTables.kt) | April 11, 2025 |
| withSchema | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/tests/WithSchemas.kt) | April 11, 2025 |
| TestUtils | [GitHub](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/tests/TestUtils.kt) | April 11, 2025 |

### 15.3 Exposed R2DBC Workshop

Exposed R2DBC 버전의 별도 워크샵 프로젝트입니다. JDBC 버전과 동일한 모듈 구조로, R2DBC 기반 non-blocking 패턴을 학습할 수 있습니다.

GitHub: [exposed-r2dbc-workshop](https://github.com/debop/exposed-r2dbc-workshop)

모듈 구성: Spring WebFlux, R2DBC DDL/DML, JSON/암호화, JPA 변환, Coroutines, Repository 패턴, 멀티테넌시, 캐시 전략
