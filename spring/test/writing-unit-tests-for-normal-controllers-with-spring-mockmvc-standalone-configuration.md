---
title: "Writing Unit Tests for \"Normal\" Controllers With Spring MockMvc: Standalone Configuration"
source: "https://www.petrikainulainen.net/programming/testing/writing-unit-tests-for-normal-spring-mvc-controllers-configuration/"
author:
  - "[[Petri Kainulainen]]"
published: 2026-10-21
created: 2026-10-21
description: "Learn to configure unit tests for view-rendering controllers by using JUnit Jupiter, Spring MockMvc standalone configuration, and HTTP request builders."
tags:
  - "clippings"
---

> [!summary]
> Petri Kainulainen shows how to configure unit tests for view-rendering Spring MVC controllers with JUnit Jupiter and MockMvc's standalone setup. An object-mother class (`WebTestConfig`) builds the few custom components worth including (a `SimpleMappingExceptionResolver` mapping exceptions to 404/500 error views, a `FixedLocaleResolver`, and an optional JSP `ViewResolver`), and a `MockMvcConfig` factory wires them into `MockMvcBuilders.standaloneSetup()`. A package-private request-builder class wraps `MockMvc` so test methods can send HTTP requests without duplicated code.

This blog post describes how we can configure the system under test by using the standalone configuration when we are writing unit tests for Spring MVC controllers which render data and process form submissions.

After we have finished this blog post, we:

- Know how we can get the required dependencies.
- Understand how we can create and configure the required components without adding duplicate code to our test suite.
- Know how we can send HTTP requests to the system under test without adding duplicate code to our test suite.
- Can configure Spring MockMvc when we are writing unit tests for view-rendering Spring MVC controllers with JUnit Jupiter.

Let's begin.

This blog post assumes that:
- [You are familiar with Spring MockMvc](https://www.petrikainulainen.net/programming/testing/introduction-to-spring-mvc-test-framework/)

## Introduction to System Under Test

The `TodoItemCrudController` class contains the controller methods which render the todo items queried from the database, create new todo items, and update existing todo items. It has two dependencies:

- The `org.springframework.context.MessageSource` provides the localized feedback messages which are displayed on the rendered view.
- The `TodoItemCrudService` class provides CRUD operations for todo items. The `TodoItemCrudController` class invokes its methods when it processes HTTP requests.

Both of these dependencies are injected into the controller class by using constructor injection. The relevant part of the `TodoItemCrudController` class looks as follows:

```java
importorg.springframework.beans.factory.annotation.Autowired;
importorg.springframework.context.MessageSource;
importorg.springframework.stereotype.Controller;
importorg.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("/todo-item")
publicclassTodoItemCrudController {

    privatefinalMessageSource messageSource;
    privatefinalTodoItemCrudService service;

    @Autowired
    publicTodoItemCrudController(MessageSource messageSource,
                                  TodoItemCrudService service) {
        this.messageSource = messageSource;
        this.service = service;
    }
}
```

Next, we will learn to get the required dependencies.

## Getting the Required Dependencies

The first thing that we have to do is to ensure that our build script declares the required testing dependencies. Our test suite uses the following testing tools:

- **JUnit Jupiter**. A new programming and extension model that is used to write both tests and extensions with JUnit.
- **Spring MockMvc**. A framework provided by Spring Test. Spring MockMvc allows us to send simulated HTTP requests to our controller without running a real servlet container.
- **Hamcrest**. An assertion library that's used to write assertions for the HTTP response returned by the system under test.
- **Mockito**. A mocking framework that's used to replace the dependencies of the system under test with test doubles.
- **AssertJ**. An assertion library that allows us to write readable assertions with its fluent API.

When we declare dependencies in our build script, we should use Spring Boot dependency management. The benefit of this approach is that we don't have to manage dependency versions and worry about the compatibility of individual dependencies. Spring Boot dependency management takes care of these things for us. If we use the Spring Boot dependency management, we can get the required testing dependencies by declaring the `spring-boot-starter-test` dependency in our build script.

This tutorial doesn't explain how we can use the Spring Boot dependency management. The Spring Boot user guide provides more information about this matter:
- [Spring Boot User Guide: Using the Maven Plugin](https://docs.spring.io/spring-boot/maven-plugin/using.html)
- [Spring Boot User Guide: Managing Dependencies With the Gradle Plugin](https://docs.spring.io/spring-boot/gradle-plugin/managing-dependencies.html)

**Additional Reading:**

- [AssertJ - Fluent testing assertions for Java and the JVM](https://assertj.github.io/doc/)
- [JavaHamcrest](https://github.com/hamcrest/JavaHamcrest)
- [JUnit Jupiter User Guide](https://docs.junit.org/6.1.3/overview.html)
- [Mockito Framework](https://site.mockito.org/)
- [Spring Framework User Guide: MockMvc](https://docs.spring.io/spring-framework/reference/testing/mockmvc.html)

Let's move on and find out how we can create the required components.

## Creating the Required Components

[As we remember](https://www.petrikainulainen.net/programming/testing/the-best-way-to-configure-the-spring-mvc-test-framework-part-one/), we should minimize the number of custom components which we include in the system under test. However, sometimes it's hard to identify the essential components. That's why I introduce three rules which help us to select the required components:

- We should configure the used `HandlerExceptionResolver` if our web application has error views which are rendered when a controller method throws an exception.
- We should specify the used `LocaleResolver` if a `Locale` object is injected into a method of the tested controller as a method parameter.
- We should specify the used `ViewResolver` if we don’t want our unit tests to use the `InternalResourceViewResolver` that's used by Spring MockMvc if no view resolver is configured.

We don't have to configure a custom `ViewResolver` because we will write assertions only for the name of the returned view. This means that we can use the `InternalResourceViewResolver`. However, this blog post describes how we can configure a custom `ViewResolver` because it's useful to know how we can do it.

We can create and configure these components by following these steps:

**First**, we have to create a `public` object mother class that contains the factory methods which create and configure the required components. After we have created our object mother class, we have to ensure that no one can instantiate it.

After we have created our object mother class, its source code looks as follows:

```java
publicfinalclassWebTestConfig {

    privateWebTestConfig() {}
}
```

There are two things I want to point out:
- Our object mother class is `public` because we don't want to put our test classes in the same package as our object mother class.
- We must use an object mother class because multiple test classes use the same components and we don't want to add duplicate code to our test suite.

**Second**, we have to write a factory method that creates and configures the used `HandlerExceptionResolver`. In other words, we have to add a `public` and `static` method to the `WebTestConfig` class. This method has no method parameters, and it returns a `SimpleMappingExceptionResolver` object.

After we have added this method to our object mother class, we have to implement it by following these steps:

1. Create a new `SimpleMappingExceptionResolver` object.
2. Ensure that the system under test renders the 404 view when the `TodoItemNotFoundException` is thrown by the tested controller method.
3. Ensure that the system under test renders the error view when the tested controller method throws either `Exception` or `RuntimeException`.
4. Ensure that the system under test returns the HTTP status code 404 when it renders the 404 view.
5. Ensure that the system under test returns the HTTP status code 500 when it renders the error view.
6. Return the created `SimpleMappingExceptionResolver` object.

After we have written our factory method, the source code of our object mother class looks as follows:

```java
importorg.springframework.web.servlet.handler.SimpleMappingExceptionResolver;

importjava.util.Properties;

publicfinalclassWebTestConfig {

    privateWebTestConfig() {}

    publicstaticSimpleMappingExceptionResolver exceptionResolver() {
        SimpleMappingExceptionResolver exceptionResolver =
                newSimpleMappingExceptionResolver();

        Properties exceptionMappings = newProperties();

        exceptionMappings.put(
                "net.petrikainulainen.springmvctest.todo.TodoItemNotFoundException",
                "error/404"
        );
        exceptionMappings.put("java.lang.Exception", "error/error");
        exceptionMappings.put("java.lang.RuntimeException", "error/error");

        exceptionResolver.setExceptionMappings(exceptionMappings);

        Properties statusCodes = newProperties();

        statusCodes.put("error/404", "404");
        statusCodes.put("error/error", "500");

        exceptionResolver.setStatusCodes(statusCodes);

        returnexceptionResolver;
    }
}
```

**Third**, we have to write a `public` and `static` factory method that creates and configures the used `LocaleResolver`. This method has no method parameters and it returns a `LocaleResolver` object. When we implement this method, we have to return a new `FixedLocaleResolver` object that returns `Locale.ENGLISH`. It's a good idea to use a fixed locale because it ensures that the environment in which our tests are run cannot cause false positives (aka test failures).

After we have written our factory method, the source code of our object mother class looks as follows:

```java
importorg.springframework.web.servlet.LocaleResolver;
importorg.springframework.web.servlet.handler.SimpleMappingExceptionResolver;
importorg.springframework.web.servlet.i18n.FixedLocaleResolver;

importjava.util.Locale;
importjava.util.Properties;

publicfinalclassWebTestConfig {

    privateWebTestConfig() {}

    publicstaticSimpleMappingExceptionResolver exceptionResolver() {
        SimpleMappingExceptionResolver exceptionResolver =
                newSimpleMappingExceptionResolver();

        Properties exceptionMappings = newProperties();

        exceptionMappings.put(
                "net.petrikainulainen.springmvctest.todo.TodoItemNotFoundException",
                "error/404"
        );
        exceptionMappings.put("java.lang.Exception", "error/error");
        exceptionMappings.put("java.lang.RuntimeException", "error/error");

        exceptionResolver.setExceptionMappings(exceptionMappings);

        Properties statusCodes = newProperties();

        statusCodes.put("error/404", "404");
        statusCodes.put("error/error", "500");

        exceptionResolver.setStatusCodes(statusCodes);

        returnexceptionResolver;
    }

    publicstaticLocaleResolver fixedLocaleResolver() {
        returnnewFixedLocaleResolver(Locale.ENGLISH);
    }
}
```

**Fourth**, we have to write a `public` and `static` factory method that creates and configures the used `ViewResolver`. This method has no method parameters and it returns a `ViewResolver` object. When we implement this method, we will create and return a new `InternalResourceViewResolver` object that uses JSP views.

After we have written our factory method, the source code of our object mother class looks as follows:

```java
importorg.springframework.web.servlet.LocaleResolver;
importorg.springframework.web.servlet.ViewResolver;
importorg.springframework.web.servlet.handler.SimpleMappingExceptionResolver;
importorg.springframework.web.servlet.i18n.FixedLocaleResolver;
importorg.springframework.web.servlet.view.InternalResourceViewResolver;
importorg.springframework.web.servlet.view.JstlView;

importjava.util.Locale;
importjava.util.Properties;

publicfinalclassWebTestConfig {

    privateWebTestConfig() {}

    publicstaticSimpleMappingExceptionResolver exceptionResolver() {
        SimpleMappingExceptionResolver exceptionResolver =
                newSimpleMappingExceptionResolver();

        Properties exceptionMappings = newProperties();

        exceptionMappings.put(
                "net.petrikainulainen.springmvctest.todo.TodoItemNotFoundException",
                "error/404"
        );
        exceptionMappings.put("java.lang.Exception", "error/error");
        exceptionMappings.put("java.lang.RuntimeException", "error/error");

        exceptionResolver.setExceptionMappings(exceptionMappings);

        Properties statusCodes = newProperties();

        statusCodes.put("error/404", "404");
        statusCodes.put("error/error", "500");

        exceptionResolver.setStatusCodes(statusCodes);

        returnexceptionResolver;
    }

    publicstaticLocaleResolver fixedLocaleResolver() {
        returnnewFixedLocaleResolver(Locale.ENGLISH);
    }

    publicstaticViewResolver jspViewResolver() {
        InternalResourceViewResolver viewResolver =
                newInternalResourceViewResolver();

        viewResolver.setViewClass(JstlView.class);
        viewResolver.setPrefix("/WEB-INF/jsp/");
        viewResolver.setSuffix(".jsp");

        returnviewResolver;
    }
}
```

If our application uses some other view technology, we should replace this method with a method that creates a `ViewResolver` object that supports the used view technology. Of course, we should do this only if we really need to configure a custom `ViewResolver`.
**Additional Reading:**
- [Spring Framework Documentation: Spring Web MVC - DispatcherServlet View Resolution](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet/viewresolver.html)
- [The Javadoc of the `ViewResolver` interface](https://docs.spring.io/spring/docs/7.1.x/javadoc-api/org/springframework/web/servlet/ViewResolver.html)
- [The Javadoc of the `InternalResourceViewResolver` class](https://docs.spring.io/spring/docs/7.1.x/javadoc-api/org/springframework/web/servlet/view/InternalResourceViewResolver.html)
- [The Javadoc of the `JstlView` class](https://docs.spring.io/spring/docs/7.1.x/javadoc-api/org/springframework/web/servlet/view/JstlView.html)

We can now create the required components by using an object mother class. Next, we will find out how we can create a request builder class which sends HTTP requests to the system under test.

## Creating the Request Builder Class

When we write unit tests for a real life web application or a REST API, we notice that every test method creates a new HTTP request and sends it to the system under test. If we create and send these HTTP requests by using the `MockMvc` API in our test methods, we add a lot of duplicate code to our test suite. This is a problem because duplicate code makes our tests hard to write and maintain.

We can solve this problem by using request builder classes. A request builder class is a class that fulfills these conditions:

- It contains methods which create and send HTTP requests to the system under test by using a `MockMvc` object.
- Every method must return a `ResultActions` object which allows us to write assertions for the returned HTTP response.

We can write our request builder class by following these steps:

1. Create a new class.
2. Add a `private MockMvc` field to the created class. Our request builder class will use this field when it creates and sends HTTP requests to the system under test.
3. Ensure that we can inject the used `MockMvc` object into the `mockMvc` field by using constructor injection.

After we have created our request builder class, its source code looks as follows:

```java
importorg.springframework.test.web.servlet.MockMvc;

classTodoItemRequestBuilder {

    privatefinalMockMvc mockMvc;

    TodoItemRequestBuilder(MockMvc mockMvc) {
        this.mockMvc = mockMvc;
    }
}
```

There are two things I want to point out:
- Our request builder class is package private because we should put it to the same package as the test class that uses it.
- This request builder class is useless because we didn’t write the methods which create and send HTTP requests to the system under test. We will talk more about request builder classes when we learn to write unit tests for view-rendering Spring MVC controllers.

**Additional Reading:**

- [Spring From the Trenches: Cleaning Up Our Test Code With HTTP Request Builders](https://www.petrikainulainen.net/programming/spring-framework/spring-from-the-trenches-cleaning-up-our-test-code-with-http-request-builders/)

Let's move on and find out how we can configure the system under test.

## Configuring the System Under Test

If our test suite has a lot of tests for Spring MVC controllers, there is a risk that we add a lot of duplicate configuration code to our test suite. That's why we should create a new `MockMvc` object by using an object mother class. We can create this class by following these steps:

**First**, we have to create a `public` object mother class. After we have created our object mother class, we have to ensure that no one can instantiate it.

After we have created our object mother class, its source code looks as follows:

```java
publicfinalclassMockMvcConfig {

    privateMockMvcConfig() {}
}
```

**Second**, we have to add a new factory method to the `MockMvcConfig` class. This method takes the tested controller object as a method parameter, creates and configures a new `MockMvc` object, and returns the created object.

After we have added this method to our object mother class, its source code looks as follows:

```java
importorg.springframework.test.web.servlet.MockMvc;

publicfinalclassMockMvcConfig {

    privateMockMvcConfig() {}

    publicstaticMockMvc mockMvcForController(Object controller) {

    }
}
```

**Third**, we have to write the code that creates a new `MockMvc` object, configures the required components, and returns the created `MockMvc` object.

After we have implemented our factory method, the source code of the `MockMvcConfig` class looks as follows:

```java
importorg.springframework.test.web.servlet.MockMvc;
importorg.springframework.test.web.servlet.setup.MockMvcBuilders;

importstaticnet.petrikainulainen.springmvctest.junit5.web.WebTestConfig.*;

publicfinalclassMockMvcConfig {

    privateMockMvcConfig() {}

    publicstaticMockMvc mockMvcForController(Object controller) {
        returnMockMvcBuilders.standaloneSetup(controller)
                .setHandlerExceptionResolvers(exceptionResolver())
                .setLocaleResolver(fixedLocaleResolver())
                .setViewResolvers(jspViewResolver())
                .build();
    }
}
```

We can now create a new test class and configure the system under test by following these steps:

**First**, we have to create a new test class and add the required fields to our test class. Our test class has three `private` fields:

- The `messageSource` field contains a `StaticMessageSource` object. Our setup methods will use this object when they configure the feedback messages that should be shown on the rendered view.
- The `requestBuilder` field contains the `TodoItemRequestBuilder` object that's used by our test methods when they send HTTP requests to the system under test.
- The `service` field contains a `TodoItemCrudService` mock. Our setup (and test) methods will use this field when they stub methods with Mockito. Also, our test methods will use this field when they verify the interactions that happened or didn't happen between the system under test and our mock.

After we have created our test class, its source code looks as follows:

```java
importorg.springframework.context.support.StaticMessageSource;

classTodoItemCrudControllerTest {

    privatefinalStaticMessageSource messageSource = newStaticMessageSource();
    privateTodoItemRequestBuilder requestBuilder;
    privateTodoItemCrudService service;
}
```

**Second**, we have to write a new setup method that's run before a test method is run, and implement this method by following these steps:

1. Create a new `TodoItemCrudService` mock and store the created mock in the `service` field.
2. Create a new `MockMvc` object by invoking the `static mockMvcForController()` method and passing the tested controller object as a method parameter.
3. Create a new `TodoItemRequestBuilder` object and store the created object in the `requestBuilder` field.

After we have implemented our setup method, the source code of our test class looks as follows:

```java
importnet.petrikainulainen.springmvctest.junit5.todo.TodoItemCrudService;
importorg.junit.jupiter.api.BeforeEach;
importorg.springframework.context.support.StaticMessageSource;

importstaticnet.petrikainulainen.springmvctest.junit5.web.MockMvcConfig.mockMvcForController;
importstaticorg.mockito.Mockito.mock;

classTodoItemCrudControllerTest {

    privatefinalStaticMessageSource messageSource = newStaticMessageSource();
    privateTodoItemRequestBuilder requestBuilder;
    privateTodoItemCrudService service;

    @BeforeEach
    voidconfigureSystemUnderTest() {
        service = mock(TodoItemCrudService.class);

        var mockMvc = mockMvcForController(
                newTodoItemCrudController(messageSource, service)
        );
        requestBuilder = newTodoItemRequestBuilder(mockMvc);
    }
}
```

We can now configure the system under test by using the standalone configuration. Let’s summarize what we learned from this blog post.

## Summary

This blog post has taught us that:

- We should use Spring Boot dependency management and get the required dependencies by declaring the `spring-boot-starter-test` dependency in our build script.
- We can create the required components without writing duplicate code by using an object mother class.
- We can send HTTP requests to the system under test without writing duplicate code by using a request builder class.
- The most common custom components which are included in the system under test are: `HandlerExceptionResolver`, `LocaleResolver`, and `ViewResolver`.
- We can create `MockMvc` objects without adding duplicate configuration code to our test suite by using an object mother class.
- If we want to configure the system under test by using the standalone configuration, we have to invoke the `standaloneSetup()` method of the `MockMvcBuilders` class.
- We can include custom components in the system under test by using the methods of the `StandaloneMockMvcBuilder` class.

**P.S. You can [get the example application of this blog post from GitHub](https://github.com/pkainulainen/spring-mvc-test-examples/tree/master/junit-5/unit-tests/normal-controllers)**.
