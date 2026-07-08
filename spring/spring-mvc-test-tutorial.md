---
title: "Spring MVC Test Tutorial"
source: "https://www.petrikainulainen.net/spring-mvc-test-tutorial/"
author:
published: 2013-01-20
created: 2026-07-08
description: "My Spring MVC Test (aka MockMvc) tutorial helps you to write both unit and integration tests for Spring Boot web applications and REST APIs."
tags:
  - "clippings"
---

> [!summary]
> An index page for Petri Kainulainen's multi-part tutorial on writing both unit and integration tests for Spring MVC controllers and REST APIs using the Spring MVC Test framework (MockMvc / MockMvcTester) and JUnit 5. It links out to posts grouped into unit testing (configuration, rendering single items and lists, form submissions, JSON API endpoints), integration testing (build setup, Spring profiles, tooling), and a series on writing MockMvc tests without ObjectMapper.

I started to write a new version of my Spring MVC Test tutorial. When this tutorial is finished, it describes how you can write both unit and integration tests for Spring MVC controllers by using the Spring MVC Test framework (aka Spring MockMvc) and [JUnit 5](https://www.petrikainulainen.net/junit-5-tutorial/). At the moment, my new Spring MVC Test tutorial consists of these blog posts:

## Introduction and Unit Testing

- [Introduction to Spring MVC Test Framework](https://www.petrikainulainen.net/programming/testing/introduction-to-spring-mvc-test-framework/) provides a quick introduction to Spring MVC Test framework. After you have read this blog post, you can identify the key components of the Spring MVC Test framework, and get the required dependencies with Maven and Gradle.
- [The Best Way to Configure the Spring MVC Test Framework, Part One](https://www.petrikainulainen.net/programming/testing/the-best-way-to-configure-the-spring-mvc-test-framework-part-one/) helps you to select the best way to configure the Spring MVC Test framework when you are writing unit tests.
- [Writing Unit Tests for "Normal" Spring MVC Controllers: Configuration](https://www.petrikainulainen.net/programming/testing/writing-unit-tests-for-normal-spring-mvc-controllers-configuration/) describes how you can configure the system under test by using the standalone configuration when you are writing unit tests for controller methods that render data or process form submissions.
- [Writing Tests for Spring MVC Controllers: Test Case 101](https://www.petrikainulainen.net/testing/writing-tests-for-spring-mvc-controllers-test-case-101/) provides a very quick introduction to sending HTTP requests to the system under test when you are using the Spring MVC Test framework.
- [Writing Unit Tests for Spring MVC Controllers: Rendering a Single Item](https://www.petrikainulainen.net/programming/testing/writing-unit-tests-for-spring-mvc-controllers-rendering-a-single-item/) describes how you can write unit tests for a Spring MVC controller which renders the information of a single item.
- [Writing Unit Tests for Spring MVC Controllers: Rendering a List](https://www.petrikainulainen.net/programming/testing/writing-unit-tests-for-spring-mvc-controllers-rendering-a-list/) describes how you can write unit tests for a Spring MVC controller that renders a list.
- [Writing Unit Tests for Spring MVC Controllers: Forms](https://www.petrikainulainen.net/programming/testing/writing-unit-tests-for-spring-mvc-controllers-forms/) describes how you can write unit tests for a Spring MVC controller that submits a form.
- [Writing Unit Tests for a Spring MVC REST API: Configuration](https://www.petrikainulainen.net/programming/testing/writing-unit-tests-for-a-spring-mvc-rest-api-configuration/) describes how you can configure the system under test by using the standalone configuration when you are writing unit tests for a Spring MVC REST API.
- [Writing Unit Tests for a Spring MVC REST API: Returning a Single Item](https://www.petrikainulainen.net/programming/testing/writing-unit-tests-for-a-spring-mvc-rest-api-returning-a-single-item/) describes how you can write unit tests for a Spring MVC API endpoint which returns the information of a single item as JSON.
- [Writing Unit Tests for a Spring MVC REST API: Returning a List](https://www.petrikainulainen.net/programming/testing/writing-unit-tests-for-a-spring-mvc-rest-api-returning-a-list/) describes how you can write unit tests for a Spring MVC API endpoint which returns a list as JSON.
- [Writing Unit Tests for a Spring MVC REST API: Writing Data](https://www.petrikainulainen.net/programming/testing/writing-unit-tests-for-a-spring-mvc-rest-api-writing-data/) describes how you can write unit tests for a Spring MVC API endpoint which inserts data into a database and returns data as JSON.
- [Introduction to MockMvcTester](https://www.petrikainulainen.net/programming/testing/introduction-to-mockmvctester/) describes what `MockMvcTester` is and explains why you should use it. You will also learn to configure `MockMvcTester`, send HTTP requests to the system under test, and write assertions for the returned HTTP response.
- [Writing Unit Tests With MockMvcTester: Returning a List as JSON](https://www.petrikainulainen.net/programming/testing/writing-unit-tests-with-mockmvctester-returning-a-list-as-json/) describes how you can write unit tests for a Spring MVC REST API endpoint that returns a list as JSON. It identifies the tests you must write, helps you to eliminate duplicate request building code from your test class, and explains how you can write the required tests with `MockMvcTester`.
- [Writing Unit Test With MockMvcTester: Returning an Object as JSON](https://www.petrikainulainen.net/programming/testing/writing-unit-test-with-mockmvctester-returning-an-object-as-json/) describes how you can write unit tests for a Spring MVC REST API endpoint that returns an object as JSON. It identifies the tests you must write, helps you to eliminate duplicate request building code from your test class, and explains how you can write the required tests with `MockMvcTester`.

## Integration Testing

- [The Best Way to Configure the Spring MVC Test Framework, Part Two](https://www.petrikainulainen.net/programming/testing/the-best-way-to-configure-the-spring-mvc-test-framework-part-two/) helps you to select the best way to configure the Spring MVC Test framework when you are writing integration tests.
- [The Best Tools for Writing Integration Tests for Spring Boot Web Applications](https://www.petrikainulainen.net/programming/testing/the-best-tools-for-writing-integration-tests-for-spring-boot-web-applications/) highlights six testing tools which we should use when we are writing integration tests for Spring Boot web applications.
- [Writing Integration Tests for Spring Boot Web Applications: Build Setup](https://www.petrikainulainen.net/programming/testing/writing-integration-tests-for-spring-boot-web-applications-build-setup/) describes how you can keep your feedback loop as short as possible when you are writing integration tests for Spring Boot web applications and you build your project with Maven.
- [Writing Integration Tests for Spring Boot Web Applications: Spring Profiles](https://www.petrikainulainen.net/programming/testing/writing-integration-tests-for-spring-boot-web-applications-spring-profiles/) describes how you can leverage Spring profiles when you have to create a separate configuration for your integration tests.

## Other

- [How to Write MockMvc Tests Without ObjectMapper, Part One - The Simplest Possible Solution](https://www.petrikainulainen.net/programming/testing/how-to-write-mockmvc-tests-without-objectmapper-part-one/) describes how we can build the request body that's send to the system under test if we cannot use `ObjectMapper`, we must use the simplest possible solution, and we must use Java.
- [How to Write MockMvc Tests Without ObjectMapper, Part Two - Using a Template Engine](https://www.petrikainulainen.net/programming/testing/how-to-write-mockmvc-tests-without-objectmapper-part-two-using-a-template-engine/) describes how we can build the request body that's send to the system under test if we cannot use `ObjectMapper`, we cannot hard-code the request body, and we must use Java.
- [How to Write MockMvc Tests Without ObjectMapper, Part Three - Should We Do It?](https://www.petrikainulainen.net/programming/testing/how-to-write-mockmvc-tests-without-objectmapper-part-three-should-we-do-it/) evaluates if we should get rid of `ObjectMapper` when we are writing MockMvc tests for Spring MVC REST APIs.
