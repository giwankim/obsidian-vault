---
title: "AI Coding Skills from JVM Ecosystem Engineers"
source: "https://jvmskills.com/"
author:
  - "[[jvm-skills]]"
published:
created: 2026-03-28
description: "AI coding skills from the engineers who build the JVM ecosystem. Expert-maintained, battle-tested guides for Claude Code, Cursor, Copilot and more. Spring Boot, jOOQ, Testcontainers, PostgreSQL — Java, Kotlin, and beyond."
tags:
  - "clippings"
---

> [!summary]
> A catalog of 22 expert-maintained AI coding skills for the JVM ecosystem, covering Spring Boot scaffolding, Java/Kotlin code quality, PostgreSQL and jOOQ database patterns, Gradle testing, and development workflows. Skills are designed for use with AI coding agents like Claude Code, Cursor, and Copilot.

jvmskills.com

$ cat README.md AI coding skills from the engineers who build the JVM ecosystem. Expert-maintained. Battle-tested. JVM-native. $ ls -la skills/ framework/ language/ database/ testing/ fullstack/ web/ workflow/ tool/ $

\--lang

\--tech

22 skills found

Opinionated by default — tell your agent to adjust any skill to your stack.

## ~/skills/framework/ ls

### Dr-JSkill Spring Boot Scaffolding

Scaffold Spring Boot projects via start.spring.io with fullstack frontend support (Vue, React, Angular, vanilla JS), PostgreSQL, Docker Compose, and Testcontainers. Follows Julien Dubois' defaults.

by Julien Dubois

kotlinjava

spring-boot

spring-bootscaffoldingproject-structurebootstrapping

### Restart Spring Boot

Restart the app via IntelliJ run configuration and wait until ready. Skips restart for template changes where LiveReload handles it automatically.

by jvm-skills

kotlinjava

spring-boot

spring-bootdevelopmenthot-reload

### Spring Boot 3.x Enterprise

Enterprise Spring Boot 3.x patterns: layered architecture with constructor injection, Spring Security with OAuth2, Spring Data JPA repositories, Actuator health checks, and integration testing with @SpringBootTest.

by Piotr Minkowski

java

spring-bootspring-securityspring-data

spring-bootrest-apispring-securityspring-datamicroservicesactuator

### Spring Boot 4.x

Spring Boot 4.x with Spring Modulith boundaries, Thymeleaf server-side rendering, ArchUnit architecture tests, and Docker Compose dev services. Opinionated package structure and Maven configuration.

by K. Siva Prasad Reddy

javakotlin

spring-bootspring-datathymeleafmavendocker

spring-bootspring-mvcspring-dataspring-moduliththymeleaftestingarchunitdocker-compose

## ~/skills/language/ ls

### Java Code Quality Review

Java code review checklist: DRY violations, null-safety gaps, exception anti-patterns, REST API contract issues, and performance pitfalls. Findings ranked by severity (Critical to Minor).

by Piotr Minkowski

java

code-reviewclean-coderefactoringapi-designnull-safety

### Java Design Patterns

When-to-use guide for Java design patterns with implementation templates. Covers Builder, Factory, Strategy, Observer, Decorator, and Adapter with problem-to-pattern mapping.

by Piotr Minkowski

java

design-patternsfactorybuilderstrategydecorator

### Java Logging Patterns

Logging best practices with SLF4J, structured JSON logging, and MDC for request tracing. Includes AI-friendly log formats optimized for Claude Code debugging and correlation ID patterns.

by Piotr Minkowski

java

slf4j

loggingslf4jstructured-loggingmdcjson-loggingdebugging

## ~/skills/database/ ls

### Design PostgreSQL Tables

Comprehensive reference covering PostgreSQL table design, data types, indexing strategies, constraints, JSONB patterns, partitioning, and PostgreSQL-specific best practices. Covers update-heavy, upsert-heavy, and OLTP-style table patterns.

by TimescaleDB

kotlinjava

postgresql

postgresschematable-designindexingjsonbconstraintspartitioning

### jOOQ Best Practices

Comprehensive jOOQ DSL best practices for Kotlin/Java. Expert knowledge base covering SQL patterns, transactions, multiset nesting, code generation, Spring Boot integration, and PostgreSQL-specific features.

by jvm-skills

kotlinjava

spring-bootjooqpostgresql

jooqsqldsldatabasepostgrestransactionsmultiset

### JPA/Hibernate Patterns

JPA/Hibernate patterns and common pitfalls including N+1 queries, lazy loading, transaction management, fetch strategies, and query optimization. Covers entity relationships, projections, and optimistic locking.

by Piotr Minkowski

java

spring-bootjpahibernate

jpahibernaten-plus-onelazy-loadingtransactionsentity-graph

### pgvector Semantic Search

Setting up vector similarity search with pgvector for AI/ML embeddings, RAG applications, or semantic search. Covers halfvec storage, HNSW index configuration, quantization strategies, filtered search, and performance tuning.

by TimescaleDB

kotlinjava

postgresqlpgvector

pgvectorembeddingssemantic-searchvector-similarityhnswragllm

### PostgreSQL Hybrid Text Search

Implementing hybrid search combining BM25 keyword search with semantic vector search using Reciprocal Rank Fusion (RRF). Covers pg\_textsearch BM25 index setup, parallel query patterns, client-side RRF fusion, and optional ML reranking.

by TimescaleDB

kotlinjava

postgresqlbm25

hybrid-searchbm25pg\_textsearchrrfkeyword-searchfull-text-searchreranking

## ~/skills/testing/ ls

### Kover Gradle Coverage

Run Kover coverage via Gradle, identify packages and classes below coverage thresholds, and generate a prioritized test improvement plan.

by jvm-skills

kotlinjava

gradlekover

gradlekovercoveragetest-analysis

### JDB Agentic Debugger

Multi-agent debugger orchestrator that drives JDB CLI to set breakpoints, step through code, and collect thread dumps. Each capability is packaged as a reusable agent skill, making the toolkit readily callable from AI coding agents.

by Bruno Borges

kotlinjava

jdb

debuggingjdbbreakpointsthread-dumps

### Gradle Test Runner

Run Gradle tests headlessly with optional filter patterns. Returns only failing output, grouped by unique exception, for fast diagnosis.

by jvm-skills

kotlinjavagroovy

gradle

gradletestingtddtest-runner

## ~/skills/fullstack/ ls

### Fullstack Fix

TDD-driven bug fixing: write a failing test first, implement the fix, refactor, then verify. Automatically picks the right test type — integration with DB, mocks/stubs, or end-to-end browser.

by jvm-skills

kotlinjava

spring-boot

tddspring-boottestingbug-fixing

## ~/skills/web/ ls

### Frontend Design

Break out of generic AI-generated UIs. Opinionated design system covering typography scales, color themes, motion choreography, spatial composition, and layered background effects.

by Anthropic

html

frontenddesignuiuxanimationstypographycss

### Web Performance Optimization

Optimize web performance for faster loading and better user experience. Covers Core Web Vitals, critical rendering path, image optimization, font loading strategies, caching, and third-party script management.

by Addy Osmani

html

performancewebcore-web-vitalsoptimization

## ~/skills/workflow/ ls

### Commit

Group uncommitted changes into logical feature commits with concise, action-oriented messages. Avoids conventional commit prefixes.

by jvm-skills

kotlinjavagroovy

gitcommitversion-control

### Feature Interview

Interview user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Outputs a spec with user stories that cover all roles, entry points, and edge cases.

by jvm-skills

kotlinjava

planninginterviewuser-storiesrequirements

### Spec to Plan

Turn a spec into a multi-phase implementation plan using tracer-bullet vertical slices with TDD. Each phase is a thin end-to-end slice delivering user-visible behavior through all layers.

by jvm-skills

kotlinjava

planningtddvertical-slicesimplementation

## ~/skills/tool/ ls

### JSpecify Nullability

JSpecify provides annotations to explicitly declare nullness expectations of Java code. Adds jspecify dependency and configures Maven or Gradle builds with ErrorProne/NullAway for compile-time nullability checking. Helps prevent NullPointerExceptions.

by K. Siva Prasad Reddy

java

jspecifyerrorprone

nullabilityerrorpronenullawaynpe-prevention

$ grep: no matches found

Try adjusting your filters or search term.
