---
title: "Kotlin Exposed Book"
source: "https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2"
author:
  - "[[debop on Notion]]"
published:
created: 2026-01-27
description: "A tool that connects everyday work into one space. It gives you and your teams AI tools—search, writing, note-taking—inside an all-in-one, flexible workspace."
tags:
  - "clippings"
  - "kotlin"
  - "database"
  - "spring-boot"
---

> [!summary]
> A comprehensive online book covering Kotlin Exposed, the lightweight SQL framework for Kotlin. It walks through DSL and DAO approaches, DDL/DML operations, column types, transactions, Spring Boot integration, async/non-blocking support, multi-tenant application development, and common pitfalls with their solutions.

![](https://debop.notion.site/image/attachment%3A3542e622-a944-4ea9-95d5-16f5ca070414%3Aexposed-text-light.png?table=block&id=1ad27445-26b0-8042-8173-e9c907abdae2&spaceId=c001cd20-7e4a-4a18-b09b-dde2c58f28fd&width=2000&userId=&cache=v2)

📕

목차[1\. Kotlin Exposed 소개](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1ad2744526b080f48ad9e19573384f0e)[2\. Quick Started](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1ad2744526b0805f9237c634967d1162)[3\. Async/Non-Blocking 지원 DB 라이브러리](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1ad2744526b080dda678f126c07237db)[4\. 준비 및 환경 설정](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1ad2744526b080d088d8ecc1e590a985)[5\. Exposed 기본 예제](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1ad2744526b0800aab80ec7f57d80a27)[6\. Expsoed DDL by DSL](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1ad2744526b08010bc1cc2cda4f2f48a)[6.1 Connection & Transaction](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1c32744526b080bf9adcf82f9275ecaa)[6.2 DDL](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1c32744526b080089523e259f8e8a1d8)[7\. Exposed DML by SQL DSL](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1ad2744526b080b88b0fdc389b95f736)[7.1 DML 함수](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1c32744526b080e3ae6adc60fffeb210)[7.2 Column Types](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1c32744526b080ee8257fc1da9d8f519)[7.3 SQL Functions](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1ca2744526b08064bc02d6f00e1fbae2)[7.4 Transactions](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1ca2744526b080e78341f4b295a7a5b9)[7.5 Exposed Entities](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1ad2744526b080e48139d3ed99f24893)[8\. Advanced Features](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1ad2744526b08020a193c9449102990b)[8\. 1 Exposed 확장 모듈](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1c32744526b08033b7ace2fc9a436dda)[8.2 사용자 정의 컬럼, 테이블, 모듈](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1c32744526b0802f8812e4c4039ee319)[9\. JPA Features 구현](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1c32744526b08034b647e39f48192290)[9.1 JPA 기본 기능 구현하기](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1c32744526b080b888f1fef3f60c80c5)[9.2 JPA 고급기능 구현하기](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1c32744526b08033967af973bef1d841)[10\. Exposed with Async/Non-Blocking](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1c32744526b080e08d88e0c66a6fe479)[11\. Exposed with Spring Boot](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1c32744526b08077af4fe185e4d1d691)[12\. 실전 Multi tenant Application 제작](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1dc2744526b0808fae1de0dfc433f1cb)[13\. 부록: Exposed 사용 시 대표적 오류 및 개선](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1da2744526b080fdaabbef040cef9d9a)[14\. Resources](https://debop.notion.site/Kotlin-Exposed-Book-1ad2744526b080428173e9c907abdae2?pvs=25#1c72744526b080f58642f64a2d14afe8)

## 1\. Kotlin Exposed 소개

표

이름

상태

작성일

Web

Kotlin Exposed 소개

완료

March 16, 2025

[debop.notion.site /Kot…7d8cd6](https://debop.notion.site/Kotlin-Exposed-1b82744526b080f3ace2e7599c7d8cd6)

## 2\. Quick Started

표

갤러리

이름

상태

Github

작성일

Web

Spring Boot Web with Exposed

완료

[github.com /blu…xposed](https://github.com/bluetape4k/exposed-workshop/tree/develop/01-spring-boot/spring-mvc-exposed)

March 15, 2025

[debop.notion.site /Spr…c6baae](https://debop.notion.site/Spring-Boot-Web-with-Exposed-1ad2744526b0807f86a1eaaeb4c6baae)

Spring Boot Webflux with Exposed

완료

[github.com /blu…xposed](https://github.com/bluetape4k/exposed-workshop/tree/develop/01-spring-boot/spring-webflux-exposed)

March 15, 2025

[debop.notion.site /Spr…49db58](https://debop.notion.site/Spring-Boot-Webflux-with-Exposed-1ad2744526b080db95adc241f749db58)

## 3\. Async/Non-Blocking 지원 DB 라이브러리

표

Gallery

이름

상태

Github

작성일

Web

Async/Non-Blocking 지원 DB 라이브러리

완료

[github.com /blu…to-jpa](https://github.com/bluetape4k/exposed-workshop/tree/develop/02-alternatives-to-jpa)

March 17, 2025

[debop.notion.site /Asy…793e60](https://debop.notion.site/Async-Non-Blocking-DB-1ad2744526b080608767e69344793e60)

Hibernate Reactive

완료

[github.com /blu…xample](https://github.com/bluetape4k/exposed-workshop/tree/develop/02-alternatives-to-jpa/hibernate-reactive-example)

March 27, 2025

[debop.notion.site /Hib…4a16b3](https://debop.notion.site/Hibernate-Reactive-1b92744526b080eb8d1dfd93654a16b3)

Vert.x SQL Client 소개

완료

[github.com /blu…xample](https://github.com/bluetape4k/exposed-workshop/tree/develop/02-alternatives-to-jpa/vertx-sqlclient-example)

March 29, 2025

[debop.notion.site /Ver…0874d9](https://debop.notion.site/Vert-x-SQL-Client-1ad2744526b08072b431f5b00e0874d9)

R2DBC + Spring Data R2DBC

완료

[github.com /blu…xample](https://github.com/bluetape4k/exposed-workshop/tree/develop/02-alternatives-to-jpa/r2dbc-example)

March 29, 2025

[debop.notion.site /R2D…2f32a1](https://debop.notion.site/R2DBC-Spring-Data-R2DBC-1ad2744526b080adadc7c737672f32a1)

맺음말

완료

March 29, 2025

[debop.notion.site /1ad…cd838b](https://debop.notion.site/1ad2744526b08050b6b6d8292ccd838b)

## 4\. 준비 및 환경 설정

표

Gallery

이름

상태

작성일

Web

학습을 위한 테스트를 위한 준비

완료

March 29, 2025

[debop.notion.site /1ba…c02ae9](https://debop.notion.site/1ba2744526b080dbb756f4818dc02ae9)

bluetape4k 소개 및 활용 방법

완료

March 29, 2025

[debop.notion.site /blu…45dfb8](https://debop.notion.site/bluetape4k-1ba2744526b080ac9165ec59b845dfb8)

bluetape4k-exposed-tests

완료

March 29, 2025

[debop.notion.site /blu…affcbf](https://debop.notion.site/bluetape4k-exposed-tests-1c52744526b0800d8210dd7121affcbf)

## 5\. Exposed 기본 예제

표

Gallery

이름

상태

Github

작성일

Web

들어가는 말

완료

March 29, 2025

[debop.notion.site /1c3…f06d68](https://debop.notion.site/1c32744526b080d9b34aca58e3f06d68)

Exposed SQL DSL 예제

완료

[github.com /blu…xample](https://github.com/bluetape4k/exposed-workshop/tree/develop/03-exposed-basic/exposed-sql-example)

March 30, 2025

[debop.notion.site /Exp…a0b04d](https://debop.notion.site/Exposed-SQL-1c32744526b080e5bbf8e97954a0b04d)

Exposed DAO 예제

완료

[github.com /blu…xample](https://github.com/bluetape4k/exposed-workshop/tree/develop/03-exposed-basic/exposed-dao-example)

March 30, 2025

[debop.notion.site /Exp…5e4e08](https://debop.notion.site/Exposed-DAO-1c32744526b08037a717cf759d5e4e08)

맺은 말

완료

March 30, 2025

[debop.notion.site /1c3…c31f92](https://debop.notion.site/1c32744526b0805ba414dfb54ec31f92)

## 6\. Expsoed DDL by DSL

### 6.1 Connection & Transaction

### 6.2 DDL

## 7\. Exposed DML by SQL DSL

### 7.1 DML 함수

### 7.2 Column Types

표

이름

상태

Github

작성일

Web

들어가는 말

완료

[github.com /blu…-types](https://github.com/bluetape4k/exposed-workshop/tree/main/05-exposed-dml/02-types)

April 9, 2025

[debop.notion.site /1c3…4a0ab6](https://debop.notion.site/1c32744526b080f59050c875404a0ab6)

Boolean Column Type

완료

[github.com /blu…ype.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/02-types/src/test/kotlin/exposed/examples/types/Ex01_BooleanColumnType.kt)

April 9, 2025

[debop.notion.site /Boo…e14724](https://debop.notion.site/Boolean-Column-Type-1c32744526b080e6af07eb0af5e14724)

Char Column Type

완료

[github.com /blu…ype.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/03-types/src/test/kotlin/exposed/examples/types/Ex02_CharColumnType.kt)

April 9, 2025

[github.com /blu…ype.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/02-types/src/test/kotlin/exposed/examples/types/Ex02_CharColumnType.kt)

Numeric Column Type

완료

[github.com /blu…ype.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/02-types/src/test/kotlin/exposed/examples/types/Ex03_NumericColumnType.kt)

April 9, 2025

[debop.notion.site /Num…6870da](https://debop.notion.site/Numeric-Column-Type-1c32744526b080119d1fca862d6870da)

Array Column Type

완료

[github.com /blu…ype.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/02-types/src/test/kotlin/exposed/examples/types/Ex05_ArrayColumnType.kt)

April 9, 2025

[debop.notion.site /Arr…4e6574](https://debop.notion.site/Array-Column-Type-1c32744526b0805e9934e4f2974e6574)

Multi Array Column Type

완료

[github.com /blu…ype.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/03-types/src/test/kotlin/exposed/examples/types/Ex06_MultiArrayColumnType.kt)

April 9, 2025

[debop.notion.site /Mul…8e0b07](https://debop.notion.site/Multi-Array-Column-Type-1c32744526b080648ff3c151008e0b07)

Blob Column Type

완료

[github.com /blu…ype.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/03-types/src/test/kotlin/exposed/examples/types/Ex08_BlobColumnType.kt)

April 9, 2025

[debop.notion.site /Blo…33dc38](https://debop.notion.site/Blob-Column-Type-1c32744526b080d4964dcc0c2833dc38)

맺음말

완료

April 9, 2025

[debop.notion.site /1c3…7384e5](https://debop.notion.site/1c32744526b0804ebba9f2f7527384e5)

### 7.3 SQL Functions

### 7.4 Transactions

### 7.5 Exposed Entities

## 8\. Advanced Features

### 8\. 1 Exposed 확장 모듈

### 8.2 사용자 정의 컬럼, 테이블, 모듈

## 9\. JPA Features 구현

### 9.1 JPA 기본 기능 구현하기

### 9.2 JPA 고급기능 구현하기

## 10\. Exposed with Async/Non-Blocking

## 11\. Exposed with Spring Boot

표

이름

상태

Github

작성일

Web

들어가는 말

완료

[github.com /blu…spring](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring)

April 19, 2025

[debop.notion.site /1c3…1f0a02](https://debop.notion.site/1c32744526b080bc92ace4a0231f0a02)

Spring Boot AutoConfiguration

완료

[github.com /blu…figure](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring/01-springboot-autoconfigure)

April 19, 2025

[debop.notion.site /Spr…2466d0](https://debop.notion.site/Spring-Boot-AutoConfiguration-1c32744526b080079af9eb44b62466d0)

Spring TransactionTemplate with Exposed Transaction

완료

[github.com /blu…mplate](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring/02-transactiontemplate)

April 21, 2025

[debop.notion.site /Spr…47e082](https://debop.notion.site/Spring-TransactionTemplate-with-Exposed-Transaction-1c32744526b080959c0fcf671247e082)

ExposedRepository with Spring Web

완료

[github.com /blu…sitory](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring/04-exposed-repository)

[debop.notion.site /Exp…0d2c5e](https://debop.notion.site/ExposedRepository-with-Spring-Web-1c32744526b080208e5ee03b900d2c5e)

ExposedRepository with Coroutines

완료

[github.com /blu…utines](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring/05-exposed-repository-coroutines)

April 21, 2025

[debop.notion.site /Exp…2cb889](https://debop.notion.site/ExposedRepository-with-Coroutines-1c32744526b080a1a6cbe2c86c2cb889)

Exposed with Spring Cache

완료

[github.com /blu…-cache](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring/06-spring-cache)

April 20, 2025

[debop.notion.site /Exp…ab3ef7](https://debop.notion.site/Exposed-with-Spring-Boot-Cache-1d82744526b08062bfcce52d6aab3ef7)

Exposed with Suspended Spring Cache

완료

[github.com /blu…-cache](https://github.com/bluetape4k/exposed-workshop/tree/main/09-spring/07-spring-suspended-cache)

April 20, 2025

[debop.notion.site /Exp…a3c6c9](https://debop.notion.site/Exposed-with-Reactive-Spring-Cache-1db2744526b080769d2ef307e4a3c6c9)

## 12\. 실전 Multi tenant Application 제작

표

이름

상태

Github

작성일

Web

Multi-tenant App

완료

[github.com /blu…tenant](https://github.com/bluetape4k/exposed-workshop/tree/main/10-multi-tenant)

April 21, 2025

[debop.notion.site /Mul…daa59b](https://debop.notion.site/Multi-tenant-App-1dc2744526b0804a8c65c15312daa59b)

Muti-tenant App with Spring Web

완료

[github.com /blu…ng-web](https://github.com/bluetape4k/exposed-workshop/tree/main/10-multi-tenant/01-multitenant-spring-web)

April 21, 2025

[debop.notion.site /Mut…9c055f](https://debop.notion.site/Muti-tenant-App-with-Spring-Web-1dc2744526b08084aad8d2cf6c9c055f)

Multi-tenant App with Virtual Thread

완료

[github.com /blu…thread](https://github.com/bluetape4k/exposed-workshop/tree/main/10-multi-tenant/02-mutitenant-spring-web-virtualthread)

April 21, 2025

[debop.notion.site /Mul…4a81b5](https://debop.notion.site/Multi-tenant-App-with-Virtual-Threads-1dc2744526b080ff9570cdb59f4a81b5)

Multi-tenant App with Spring Webflux and Coroutines

완료

[github.com /blu…ebflux](https://github.com/bluetape4k/exposed-workshop/tree/main/10-multi-tenant/03-multitenant-spring-webflux)

April 21, 2025

[debop.notion.site /Mul…8bd2a8](https://debop.notion.site/Multi-tenant-App-with-Spring-Webflux-and-Coroutines-1dc2744526b0802e926de76e268bd2a8)

맺음말

완료

[debop.notion.site /1dc…8ebf30](https://debop.notion.site/1dc2744526b080d8bd13e71a678ebf30)

## 13\. 부록: Exposed 사용 시 대표적 오류 및 개선

표

이름

상태

Github

작성일

Web

Exposed 사용 시 대표적 실수와 개선 방법

완료

April 21, 2025

[debop.notion.site /Exp…01d06e](https://debop.notion.site/Exposed-1da2744526b080798d36cfa73501d06e)

## 14\. Resources

Table

이름

상태

Github

작성일

DMLTestData

완료

[github.com /blu…ata.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/dml/DMLTestData.kt)

April 5, 2025

EntityTestData

완료

[github.com /blu…ata.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/05-exposed-dml/02-entities/src/test/kotlin/exposed/examples/entities/EntityTestData.kt)

April 5, 2025

Movie and Actors

완료

[github.com /blu…ema.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/repository/MovieSchema.kt)

April 5, 2025

Board Posts Categories

완료

[github.com /blu…ema.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/entities/BoardSchema.kt)

April 5, 2025

BlogSchema

완료

[github.com /blu…ema.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/07-jpa/01-convert-jpa-basic/src/test/kotlin/exposed/examples/jpa/ex02_entities/BlogSchema.kt)

April 5, 2025

OrderSchema

완료

[github.com /blu…ema.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/mapping/OrderSchema.kt)

April 5, 2025

Bank Entites

완료

[github.com /blu…ies.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/samples/BankEntities.kt)

April 5, 2025

BookSchema

완료

[github.com /blu…ema.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/mapping/compositeId/BookSchema.kt)

April 5, 2025

PersonSchema

완료

[github.com /blu…ema.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/07-jpa/01-convert-jpa-basic/src/test/kotlin/exposed/examples/jpa/ex02_entities/PersonSchema.kt)

April 5, 2025

UserCities

완료

[github.com /blu…ies.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/samples/UserCities.kt)

April 6, 2025

Table

이름

상태

Github

작성일

TestDB

완료

[github.com /blu…tDB.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/tests/TestDB.kt)

April 11, 2025

withDb

완료

[github.com /blu…tDB.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/tests/TestDB.kt)

April 11, 2025

withTables

완료

[github.com /blu…les.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/tests/WithTables.kt)

April 11, 2025

withSchema

완료

[github.com /blu…mas.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/tests/WithSchemas.kt)

April 11, 2025

TestUtils

완료

[github.com /blu…ils.kt](https://github.com/bluetape4k/exposed-workshop/blob/main/00-shared/exposed-shared-tests/src/main/kotlin/exposed/shared/tests/TestUtils.kt)

April 11, 2025

Gallery
