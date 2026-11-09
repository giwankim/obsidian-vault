---
title: "How to Call REST APIs with RestClient in Spring Boot 4"
source: "https://alexanderobregon.substack.com/p/how-to-call-rest-apis-with-restclient?utm_source=substack&utm_medium=email"
author:
  - "[[Alexander Obregon]]"
published: 2026-11-03
created: 2026-11-09
description: "Calling external REST APIs allows a Spring Boot application to retrieve information, submit data, and communicate with other services over HTTP."
tags:
  - "clippings"
---

> [!summary]
> A walkthrough of synchronous HTTP calls with `RestClient` in Spring Boot 4, using the new `spring-boot-starter-restclient` starter, the auto-configured `RestClient.Builder`, and global (`spring.http.clients.*`) or per-client timeouts. It covers GET/POST requests, headers, JSON mapping to records, and `ParameterizedTypeReference` for generic responses. Error handling separates HTTP failures (`RestClientResponseException`, `onStatus()`) from I/O failures (`ResourceAccessException`), and the article warns that retrying a `POST` after a read timeout can create duplicates.

Calling external REST APIs allows a Spring Boot application to retrieve information, submit data, and communicate with other services over HTTP. Spring Boot 4 supports `RestClient` for making these synchronous requests, providing methods to specify endpoints, add HTTP headers, and send JSON request bodies. When a response comes back, Spring can convert the JSON into a Java object, allowing us to access the returned data without manually parsing it. We can also configure connection and read timeouts, handle HTTP errors, and control how the application responds when an external service encounters a problem.

### Preparing RestClient for API Communication

Before sending HTTP requests to an external API, we need to give Spring Boot the necessary dependencies and configure the client that will handle communication. Spring Boot 4 provides an auto-configured `RestClient.Builder` that we can customize for a particular service, including its base URL and network timeouts. Keeping these settings in a dedicated client also means we don’t have to repeat the same configuration for every request. With the client configured, the application has a consistent point of communication with the external service.

#### Adding the RestClient Dependency

Spring Boot 4 includes a dedicated starter called `spring-boot-starter-restclient` for synchronous HTTP communication. It provides the Spring components needed to create REST clients, along with support for converting JSON data through Jackson. Rather than adding individual HTTP libraries and configuring their integration manually, we can add the starter and let Spring Boot handle the default configuration.

For a Maven project, we’ll add the following dependency to the existing `pom.xml` file:

```markup
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-restclient</artifactId>
</dependency>
```

Maven retrieves the dependency and its required libraries during the next project build. We don’t need to specify the version individually when the project already inherits Spring Boot’s dependency management through its parent POM or an imported BOM. This keeps the REST client libraries aligned with the Spring Boot version configured for the application, without requiring us to manage their versions individually.

The dedicated starter is part of Spring Boot 4’s more modular dependency structure. Earlier Spring Boot applications commonly obtained REST client support through broader web starters that also provided components for building HTTP endpoints. With Spring Boot 4, an application that only communicates with external APIs can include `spring-boot-starter-restclient` without adding Spring MVC or an embedded web server. If the application also exposes HTTP endpoints through Spring MVC, `spring-boot-starter-webmvc` provides the components needed for that functionality.

Within the starter, Spring supplies `RestClient`, which was introduced in Spring Framework 6.1 and remains the recommended synchronous HTTP client for new imperative code. Spring Framework 7 also deprecated the older `RestTemplate` API in favor of `RestClient`. Both clients communicate over HTTP, but `RestClient` provides a fluent API where request configuration follows a sequence of method calls such as `get()`, `post()`, `retrieve()`, and `body()`.

The synchronous behavior is important because the calling thread waits for the HTTP operation to finish before execution continues. If we request information from an external service, the method calling `RestClient` remains occupied until the request completes or fails. This behavior works well in traditional Spring MVC applications and other imperative Java code where operations execute in sequence.

Spring Boot also configures the supporting components needed for the client. Its HTTP message converters handle transformations between Java objects and supported content formats, while a `ClientHttpRequestFactory` provides the underlying HTTP communication. Spring Boot selects the request factory according to the HTTP libraries available on the application’s classpath, allowing different projects to rely on different HTTP implementations without changing the methods called through `RestClient`.

An important part of this integration is Spring Boot’s `RestClient.Builder` bean. Rather than constructing every client directly through `RestClient.create()`, we can inject the auto-configured builder into a Spring-managed component and customize it for the service we’re contacting. This allows our client to inherit Spring Boot’s existing HTTP configuration, including registered customizations and supported request factory settings.

#### Configuring the Base URL

External REST APIs generally provide a common server address followed by endpoint locations for particular resources. Instead of repeating the entire address for every operation, `RestClient` allows us to define a base URL that becomes the starting address for requests made through that client.

For the examples we will be using today, we’ll communicate with JSONPlaceholder, a public testing API that provides sample resources such as posts, users, and comments. Its address is https://jsonplaceholder.typicode.com, and individual resources are available through endpoints like `/posts` and `/users`. Because JSONPlaceholder doesn’t require authentication for these operations, we can concentrate on configuring the client before introducing request-specific behavior.

The base URL can be stored in Spring Boot’s `application.properties` file:

```markup
posts.api.base-url=https://jsonplaceholder.typicode.com
```

Spring Boot loads this property when the application starts, making its value available to components managed by the Spring container. The `posts.api.base-url` name is a custom application property rather than a predefined Spring Boot setting, so we can give it a name that identifies the external service we’re contacting.

Keeping the address in configuration is helpful because the remote API location can differ between environments. During development, we may communicate with a testing server, while a production deployment communicates with another address. Each environment can supply its own property value without requiring changes to the Java class responsible for creating the client.

Next, we’ll create a service named `PostClient` that receives the configured address and builds a reusable `RestClient` instance:

```markup
package com.example.apiclient;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class PostClient {

    private final RestClient restClient;

    public PostClient(
            RestClient.Builder builder,
            @Value("${posts.api.base-url}") String baseUrl) {

        this.restClient = builder
                .baseUrl(baseUrl)
                .build();
    }
}
```

We register `PostClient` as a Spring-managed component through the `@Service` annotation, allowing Spring to create the class and supply its constructor dependencies. During construction, Spring injects the auto-configured `RestClient.Builder` and resolves the `${posts.api.base-url}` placeholder through `@Value`. The constructor receives the configured address as a string, so the class doesn’t need to contain the actual server address.

Calling `baseUrl()` assigns that address to the builder, while the following `build()` call creates the `RestClient` instance with the selected configuration. We then store the client in the final `restClient` field, allowing methods inside the service to access the same instance without rebuilding it for every HTTP operation.

With the configured address, requesting the endpoint `/posts/1` targets `https://jsonplaceholder.typicode.com/posts/1`. The base URL supplies the common server address, while the request supplies the location of the resource being accessed. For an API with multiple endpoints, this reduces repeated URL text and keeps the remote server configuration in a single location.

The `RestClient.Builder` is stateful, meaning changes made to the builder affect clients subsequently created from that builder. Spring Boot provides prototype-scoped builder instances, so a component receiving its own injected builder can configure it without changing the builders injected into other components. If we need to create several clients from the same builder instance, we can also call `clone()` to obtain an independent builder before applying further configuration.

After construction, the `RestClient` instance can safely be shared across multiple threads. We don’t need to create a new instance for every HTTP operation, and storing it as a field allows the service to retain the same client configuration throughout its lifetime.

There’s also a distinction between configuring a client through Spring Boot’s injected builder and creating one directly through Spring Framework’s static factory methods. Although `RestClient.create()` is supported, a client created that way doesn’t automatically inherit the customizations applied to Spring Boot’s injected builder. By receiving the builder through dependency injection, we retain the HTTP configuration already supplied by the application.

At this point, our service has a reusable REST client associated with a particular external API. Before adding the methods that communicate with its endpoints, we can configure how long the client waits when establishing a connection or receiving data from the server.

#### Configuring Connection Timeouts

Network communication introduces delays that aren’t completely controlled by the application. The remote server could be temporarily unavailable, the network connection could be interrupted, or the service could take longer than expected to respond. Because `RestClient` performs synchronous requests, the calling thread remains occupied while the HTTP operation is waiting, making timeout configuration an important part of preparing the client. Spring Boot 4 provides configuration properties for controlling connection and read timeouts. These settings determine how long certain network operations are allowed to wait before the HTTP client reports a timeout, giving us control over delays that could leave requests waiting longer than intended.

We can configure both values through `application.properties`:

```markup
spring.http.clients.connect-timeout=3s
spring.http.clients.read-timeout=5s
```

The `connect-timeout` property controls the time allowed to establish a connection with the remote server. With a value of three seconds, the client applies that connection limit through its underlying HTTP implementation. If establishing the connection exceeds the permitted duration, the operation can fail with a connection timeout rather than continuing to wait indefinitely.

The `read-timeout` property controls how long the HTTP client waits for response data according to the selected HTTP library. In our configuration, the read timeout is five seconds, which becomes relevant when communication has begun but the server hasn’t delivered the expected data within the permitted interval.

Connection and read timeouts apply to different stages of HTTP communication. Establishing a connection involves contacting the remote host and opening the connection needed to communicate, while reading occurs during the exchange of response data. The exact behavior of these settings depends on the underlying HTTP client library, including how it measures waiting periods during network activity.

We also need to distinguish a read timeout from a total request duration limit. Some HTTP implementations apply read timeouts to periods spent waiting for network data rather than the complete duration of an operation. Consequently, setting a five-second read timeout doesn’t necessarily mean that every HTTP request will finish within five seconds, as the complete operation can involve multiple stages of communication.

The `spring.http.clients` property group is the current Spring Boot 4 location for global HTTP client settings. Earlier Spring Boot versions exposed imperative client configuration through `spring.http.client`, but Spring Boot 4 introduced the plural `spring.http.clients` group for shared HTTP client configuration.

These properties apply to Spring Boot’s auto-configured HTTP clients, including those created through the injected `RestClient.Builder`. If we’re communicating with several external APIs through different clients, they can inherit the same timeout values without requiring us to configure each service individually.

Spring Boot selects the underlying HTTP request factory based on the libraries available to the application. Supported implementations include Apache HttpClient, Jetty HttpClient, Reactor Netty, the JDK HTTP client, and the JDK’s `HttpURLConnection` implementation. The selected factory determines how HTTP operations are performed and can affect the exact behavior of the configured timeouts. For some applications, shared timeout values are sufficient, while others communicate with external services that have different response characteristics. An API that typically responds within a few hundred milliseconds may benefit from shorter limits than a service that performs longer processing before returning data. We can account for these differences by configuring individual clients rather than assigning the same timeout values to every external connection.

Spring Boot provides `HttpClientSettings` and `ClientHttpRequestFactoryBuilder` for creating a request factory with settings selected for a particular client. These classes allow us to specify timeout durations directly in Java when the global properties aren’t appropriate for every service.

To give our existing `PostClient` its own timeout configuration, we can replace its constructor with the following version:

```markup
public PostClient(
        RestClient.Builder builder,
        @Value("${posts.api.base-url}") String baseUrl) {

    HttpClientSettings settings = HttpClientSettings.defaults()
            .withConnectTimeout(Duration.ofSeconds(3))
            .withReadTimeout(Duration.ofSeconds(5));

    ClientHttpRequestFactory requestFactory =
            ClientHttpRequestFactoryBuilder.detect().build(settings);

    this.restClient = builder
            .baseUrl(baseUrl)
            .requestFactory(requestFactory)
            .build();
}
```

We begin by calling `HttpClientSettings.defaults()` to create an object containing the default HTTP client settings. From there, `withConnectTimeout()` and `withReadTimeout()` return updated settings containing the durations we’ve specified. These methods accept Java `Duration` values, so we can express the time limits through methods such as `Duration.ofSeconds()` without manually converting between time units.

After defining the settings, we call `ClientHttpRequestFactoryBuilder.detect()` to select an appropriate HTTP request factory builder according to the libraries available on the classpath. The following `build(settings)` call creates a request factory configured with those timeout values. Finally, we pass the factory into `requestFactory()` before constructing the `RestClient`, giving this particular client its own HTTP communication settings.

The replacement constructor requires the following imports alongside those already present in `PostClient`:

```markup
import java.time.Duration;

import org.springframework.boot.http.client.ClientHttpRequestFactoryBuilder;
import org.springframework.boot.http.client.HttpClientSettings;
import org.springframework.http.client.ClientHttpRequestFactory;
```

The `Duration` class represents the timeout intervals, while `HttpClientSettings` stores the configuration we want to apply. We then rely on `ClientHttpRequestFactoryBuilder` to construct the request factory, which implements the `ClientHttpRequestFactory` interface expected by `RestClient.Builder`. These imports complete the constructor’s dependencies without requiring changes to the service’s existing class declaration or its `restClient` field.

This configuration allows an individual client to have timeout values that differ from the global properties. If we’re communicating with several external services, we can give each client settings appropriate for the expected response time without changing the configuration of the others.

There is an important distinction when assigning an explicit request factory. The custom factory replaces the factory Spring Boot would normally configure for that client, so other HTTP settings that need to remain active must also be accounted for when constructing the replacement. For most applications, configuring the global `spring.http.clients` properties and retaining the auto-configured request factory requires fewer individual settings.

Neither connection nor read timeouts automatically cause `RestClient` to retry a failed operation. If the client exceeds the configured connection or read timeout, the affected HTTP operation can fail with an exception that the calling application needs to handle. The timeout itself doesn’t instruct the client to repeat the request, and any retry behavior would need its own configuration.

Keeping timeout settings at the HTTP client level allows us to control how long network operations wait without adding timing logic to individual request methods. Our `PostClient` now has a configured base URL, a reusable `RestClient` instance, and connection settings that govern how communication with the external API is performed.

### Making HTTP Requests with RestClient

With our client configured for JSONPlaceholder, we can start communicating with its endpoints through HTTP requests. `RestClient` provides methods for selecting an HTTP operation, specifying the resource address, supplying request information, and processing the response returned by the server. Spring Boot also handles JSON conversion between Java objects and HTTP content, so we can concentrate on the data being exchanged. The same client can perform different operations depending on the HTTP method and the information required by the external API.

#### Reading API Responses

Retrieving information from an external API commonly involves sending an HTTP `GET` request to an endpoint that identifies the resource we want. The server processes that request and returns an HTTP response containing a status code, headers, and potentially a body with the requested information. When the response contains JSON, `RestClient` can convert that content into a Java object through Spring’s configured HTTP message converters.

JSONPlaceholder provides a `/posts/{id}` endpoint for retrieving individual posts. Each post contains a user ID, post ID, title, and body, which we can represent through a Java record. This gives Spring a defined type for converting the JSON response into data we can access directly from our application.

We’ll begin by creating a record named `Post` in its own `Post.java` file:

```markup
package com.example.apiclient;

public record Post(
        int userId,
        int id,
        String title,
        String body
) {}
```

The record defines four components matching the property names returned by JSONPlaceholder. When Spring receives the JSON response, its configured Jackson converter maps those properties to the corresponding record components. Spring Boot 4 uses Jackson 3 by default, providing JSON conversion without requiring us to manually read or parse the response content.

Java records are well suited for representing API responses because they provide an immutable data carrier with generated accessors, a constructor, and standard object methods. We can access the returned values through methods such as `id()`, `title()`, and `body()` without writing additional accessor methods.

With the record available, we’ll add a method to our existing `PostClient` service that retrieves a particular post:

```markup
public Post getPost(int id) {
    return restClient.get()
            .uri("/posts/{id}", id)
            .retrieve()
            .body(Post.class);
}
```

We begin the request with `get()`, which selects the HTTP `GET` method. The following `uri()` call specifies the endpoint relative to the base URL configured earlier. Spring replaces the `{id}` placeholder with the value passed into `getPost()`, allowing the same method to retrieve different posts without manually constructing a complete URL.

Calling `retrieve()` prepares the request for response processing. The HTTP operation is executed when we call a terminal method such as `body(Post.class)`, which reads the response content and converts it into the specified Java type. If we call `getPost(1)`, the client requests `https://jsonplaceholder.typicode.com/posts/1` and returns the post information as a `Post` record. From there, we can access its values through the record’s generated methods, while the HTTP communication and JSON conversion remain within `PostClient`.

The `body()` method returns `null` if the response doesn’t contain a body. For successful responses that contain data, the JSON must also be compatible with the requested Java type. If Spring cannot convert the returned content, the operation fails rather than returning an incorrectly populated object.

External APIs also commonly return collections of resources rather than individual records. JSONPlaceholder’s `/posts` endpoint returns a JSON array containing multiple posts, so we need a Java type that can represent a collection of `Post` objects.

We can add a second method to `PostClient` for retrieving the collection:

```markup
public List<Post> getPosts() {
    return restClient.get()
            .uri("/posts")
            .retrieve()
            .body(new ParameterizedTypeReference<List<Post>>() {});
}
```

For this method, we’ll import `java.util.List` and `org.springframework.core.ParameterizedTypeReference`.

The request follows the same sequence as our individual post retrieval, but the response conversion differs. Instead of requesting a single `Post`, we’re requesting a `List<Post>` containing the objects returned by the API.

Java’s type erasure means that passing `List.class` wouldn’t preserve the information needed to identify the type of objects inside the collection. `ParameterizedTypeReference<List<Post>>` retains that generic type information, allowing Spring to convert the JSON array into a list containing `Post` records.

Each record corresponds to an entry in the returned JSON array, and we can access those records through ordinary Java collection operations. The same technique applies to other parameterized response types when an API returns collections or data structures containing generic types.

Sometimes we need more information from the HTTP response than the converted body. External services can include headers containing caching instructions, content information, or other metadata, while the HTTP status tells us how the server handled the request.

For these situations, `RestClient` provides `toEntity()`, which returns a `ResponseEntity` containing the body along with the HTTP status and headers.

We’ll retrieve that information through the following method in `PostClient`:

```markup
public ResponseEntity<Post> getPostResponse(int id) {
    return restClient.get()
            .uri("/posts/{id}", id)
            .retrieve()
            .toEntity(Post.class);
}
```

We need to import `org.springframework.http.ResponseEntity` for this method. The request still targets an individual post, but calling `toEntity(Post.class)` changes the returned type from `Post` to `ResponseEntity<Post>`. We can retrieve the converted record through `getBody()`, inspect the HTTP status through `getStatusCode()`, and access the response headers through `getHeaders()`.

This becomes helpful when the response metadata influences what we do next. An API may provide pagination information, caching instructions, or other information through headers, and we can inspect those values while retaining access to the converted response body.

`body()` and `toEntity()` follow the default HTTP error handling behavior of `RestClient`. If the remote API returns an error status, the client normally throws an exception instead of returning the response as an ordinary successful result. We can account for those failures when configuring error handling later in the service.

#### Sending Request Headers

Request headers allow us to include information about an HTTP operation beyond its URL and body. External APIs commonly inspect headers to determine which response format the client accepts, identify the calling application, or validate authentication credentials. Spring’s `RestClient` provides methods for setting these values directly within the request chain, allowing us to supply the information required by a particular endpoint.

The `Accept` header tells the server which content types the client can receive. For a REST API returning JSON, we can specify `application/json` through the `accept()` method rather than constructing the header value ourselves.

Custom headers can also carry information associated with an individual request. Some services support request identifiers that allow requests to be traced across application logs and service boundaries. The exact header names and accepted values depend on the API we’re contacting.

To include both a JSON preference and a request identifier, we’ll add the following method to `PostClient`:

```markup
public Post getPostWithHeaders(int id, String requestId) {
    return restClient.get()
            .uri("/posts/{id}", id)
            .accept(MediaType.APPLICATION_JSON)
            .header("X-Request-ID", requestId)
            .retrieve()
            .body(Post.class);
}
```

The method requires `org.springframework.http.MediaType`, which provides constants for common HTTP media types. We start by selecting the post endpoint, then call `accept(MediaType.APPLICATION_JSON)` to request a JSON response. The `header()` method adds `X-Request-ID` with the identifier passed into the method, allowing each call to provide its own value without changing the client configuration.

When the request is sent, Spring includes these headers alongside the other HTTP request information. JSONPlaceholder accepts requests without requiring custom identification headers, so the request identifier doesn’t change the returned post data. APIs that support request tracing can read the identifier and associate it with their own processing records.

There are situations where multiple headers need to be configured within the same request. `RestClient` provides `headers()`, which accepts a callback that gives us access to the request’s `HttpHeaders` collection. Through that callback, we can set, replace, or inspect header values before sending the request.

Authentication is a common reason to use this method. For APIs that require bearer tokens, the `HttpHeaders` class provides `setBearerAuth()`, which accepts an access token and places it in the HTTP `Authorization` header with the expected bearer scheme.

We can call `headers(headers -> headers.setBearerAuth(accessToken))` within the request chain, provided that `accessToken` contains a token obtained through the external service’s authentication process.

The token must already be available to the application before the request is made. `RestClient` doesn’t obtain or refresh authentication credentials automatically merely because we’ve configured an authorization header. Authentication requirements and token management depend on the service being contacted.

JSONPlaceholder doesn’t require bearer authentication for its public endpoints, but the same header configuration applies to services that validate access tokens.

When a header value should be included in every request made through a particular client, we can configure it through `defaultHeader()` on `RestClient.Builder`. For values that change between calls, setting the header directly within the request method keeps those values associated with the operation that needs them.

We also need to distinguish the `Accept` header from `Content-Type`. The first communicates which response formats the client can receive, while the second identifies the format of content being sent to the server. For requests that submit JSON data, we’ll provide the content type alongside the request body.

#### Submitting JSON Request Bodies

External APIs frequently accept information through HTTP requests that create or modify resources. HTTP `POST` requests commonly submit data to collection endpoints, while `PUT` and `PATCH` are generally used for resource updates. These operations can include a request body containing the information the server needs to process the request. `RestClient` allows us to provide that body as a Java object, with Spring converting it into the appropriate HTTP content through its configured message converters. When the server expects JSON, we can declare `application/json` as the request content type and provide an object containing the values we want to submit.

JSONPlaceholder provides a `POST /posts` endpoint that accepts information for a new post. The expected request contains a user ID, title, and body, while the server’s response includes an assigned post ID.

We’ll represent the information being submitted through a record named `CreatePostRequest`, stored in its own `CreatePostRequest.java` file:

```markup
package com.example.apiclient;

public record CreatePostRequest(
        int userId,
        String title,
        String body
) {}
```

This record contains the three values required for the request, without including an ID that would normally be assigned by the server. Its component names correspond to the JSON property names expected by the endpoint, allowing Jackson to serialize the record without custom property mappings.

The request record and response record serve different purposes. `CreatePostRequest` represents the information we want to submit, while the existing `Post` record represents the server’s response after the operation completes. Keeping these two types distinct also means callers don’t have to provide a post ID when creating a resource.

Next, we’ll add a method to `PostClient` that accepts the request record and submits it through HTTP:

```markup
public Post createPost(CreatePostRequest request) {
    return restClient.post()
            .uri("/posts")
            .contentType(MediaType.APPLICATION_JSON)
            .accept(MediaType.APPLICATION_JSON)
            .body(request)
            .retrieve()
            .body(Post.class);
}
```

We begin with `post()` to select the HTTP `POST` method, followed by `uri("/posts")` to identify the collection endpoint receiving the request. The `contentType()` call declares that we’re sending JSON, while `accept()` communicates that we expect JSON in the response.

Calling `body(request)` supplies the `CreatePostRequest` record as the outgoing content. Spring selects a compatible HTTP message converter and serializes the record into JSON before sending the request.

Notice that `body()` appears twice in the method, with each occurrence serving a different purpose. The first call belongs to the request specification and supplies the object we’re submitting. The second follows `retrieve()` and reads the response body, converting the returned JSON into a `Post` record.

This distinction is important because the object submitted to the API doesn’t always have the same structure as the object returned by the server. The request may contain only the information required to create a resource, while the response can include additional values such as an assigned identifier.

To submit a post, we can create a `CreatePostRequest` and pass it to the service method from code that already has an injected `PostClient` instance:

```markup
CreatePostRequest request = new CreatePostRequest(
,
        "Calling REST APIs",
        "Submitting a post through Spring Boot RestClient"
);

Post created = postClient.createPost(request);
```

We supply the user ID, title, and body in the same order they’re declared in `CreatePostRequest`. The record is then passed into `createPost()`, which sends the information to the external endpoint and returns the converted response.

During serialization, Jackson produces a JSON object containing the `userId`, `title`, and `body` properties. We don’t need to create a JSON string manually or assign those values individually to the HTTP request content.

JSONPlaceholder responds to a successful creation request with HTTP status `201 Created` and a JSON object containing the submitted information along with an assigned ID. Its documented POST behavior returns ID `101` for the simulated resource, which we can read through the `id()` method on the returned `Post` record.

The service doesn’t permanently store resources submitted through this endpoint. JSONPlaceholder simulates the creation operation, so requesting the newly assigned post ID afterward doesn’t retrieve a persisted record. The HTTP request and response behavior still follows the documented endpoint contract.

For APIs that modify existing resources, `RestClient` also provides `put()` and `patch()`. The general request construction remains similar, but the HTTP method communicates the intended operation. `PUT` commonly replaces the representation of a resource, while `PATCH` submits modifications to part of an existing resource according to the patch format supported by the API.

We should follow the remote API’s endpoint contract when deciding which HTTP method to call and which fields to include in the request body. The Java object must represent the data the endpoint accepts, and the submitted content type must match the format expected by the server.

Response bodies aren’t required for every successful operation, either. Some endpoints return an HTTP status without any content, such as `204 No Content`, while others return a newly created or updated resource.

For operations where we don’t need to deserialize a response body, `retrieve().toBodilessEntity()` completes the request and returns a `ResponseEntity<Void>` containing the status and response headers. This allows us to inspect the result without expecting JSON content that the server never supplied.

When a response body is expected, methods such as `body(Post.class)` and `toEntity(Post.class)` remain available, allowing us to select the method that provides the information needed by the caller.

#### Handling HTTP Errors

External HTTP requests can fail for reasons related to the request itself, the remote server, or the connection between services. Invalid resource identifiers, rejected credentials, unavailable endpoints, and server failures can all prevent an operation from completing successfully. `RestClient` provides default exception handling for HTTP error responses, along with methods for customizing how particular statuses are handled.

HTTP status codes identify how the server processed a request. Responses in the `2xx` range indicate successful processing, while `4xx` responses generally identify request-related problems and `5xx` responses indicate server-side failures. For example, an API may return `404 Not Found` when a requested resource doesn’t exist or `401 Unauthorized` when valid authentication credentials haven’t been provided. Server-side failures can produce responses such as `500 Internal Server Error` or `503 Service Unavailable`.

When we call `retrieve()`, `RestClient` applies default status handling as the response is processed. For HTTP responses with status codes from `400` through `599`, it normally throws an exception rather than treating the response as a successful result.

The exact exception depends on the returned status. Client errors produce `HttpClientErrorException` or an applicable subclass, while server errors produce `HttpServerErrorException` or a corresponding subclass. These exceptions belong to the `RestClientResponseException` hierarchy, which gives us access to information about the failed response. Through `getStatusCode()`, we can inspect the HTTP status returned by the server. The `getResponseBodyAsString()` method provides the response content as text, which can help when an API includes diagnostic information or a service-specific error response.

Spring also supports custom handling for particular status codes through `onStatus()`. This method accepts a condition that identifies matching responses and a handler that determines what should happen when the condition is met.

For another example, we may want to distinguish a missing post from other failures by throwing an exception with information about the requested resource.

We’ll add a `findPost()` method to `PostClient` that handles HTTP `404` responses:

```markup
public Post findPost(int id) {
    return restClient.get()
            .uri("/posts/{id}", id)
            .retrieve()
            .onStatus(
                    status -> status.value() == 404,
                    (request, response) -> {
                        throw new IllegalArgumentException(
                                "Post " + id + " was not found"
                        );
                    }
            )
            .body(Post.class);
}
```

We begin with the same GET operation we’ve already established, but the response handling now includes a condition that checks the HTTP status code. When the server returns `404`, the custom handler throws an `IllegalArgumentException` identifying the requested post.

The `status.value()` call retrieves the numeric HTTP status code so we can compare it with `404`. The handler also receives access to the outgoing request and incoming response, allowing more detailed error processing when the application needs it.

If the server returns a successful response, the custom handler doesn’t run, and `body(Post.class)` converts the returned JSON into a `Post` record as usual. Other HTTP error responses that don’t match the condition continue through the default error handling behavior.

The exception type selected for custom handling depends on what the surrounding application expects. `IllegalArgumentException` provides a familiar Java exception for this example, but we can define a custom exception class when callers need to identify a particular API failure.

`onStatus()` applies to the individual request where it’s declared. If several methods need identical error handling, `RestClient.Builder` also supports `defaultStatusHandler()` for registering a handler that applies across requests made through the resulting client. Request-level handlers take precedence over builder-level default handlers.

We also need to distinguish HTTP error responses from failures that occur before the client receives a usable HTTP response.

Network interruptions, connection failures, and read timeouts don’t necessarily produce HTTP status codes. If the remote server cannot be reached or communication fails during the operation, Spring can report the problem through `ResourceAccessException`, which represents an I/O failure during client communication.

These failures are different from a server deliberately responding with an HTTP error. Receiving `500 Internal Server Error` means an HTTP response reached the client, while a connection timeout means the client couldn’t complete the affected connection operation within its configured limit.

When we need different behavior for these conditions, we can catch their exceptions individually.

We’ll add the following method to `PostClient` to distinguish HTTP response failures from connection-related failures:

```markup
public Post getPostWithFailureDetails(int id) {
    try {
        return getPost(id);
    } catch (RestClientResponseException ex) {
        throw new IllegalStateException(
                "Post API returned HTTP " + ex.getStatusCode().value(),
                ex
        );
    } catch (ResourceAccessException ex) {
        throw new IllegalStateException(
                "Unable to communicate with the Post API",
                ex
        );
    }
}
```

For this method, we’ll import `org.springframework.web.client.RestClientResponseException` and `org.springframework.web.client.ResourceAccessException`.

We call the existing `getPost()` method inside a `try` block, allowing successful responses to return their converted `Post` records. If the API returns an HTTP error, the first `catch` block receives the `RestClientResponseException` and retrieves the status code through `getStatusCode()`.

The method then throws an `IllegalStateException` containing the HTTP status and preserves the original exception as its cause. Retaining that cause allows the underlying response exception to remain available for logging or further inspection by the calling application. If communication fails because of an I/O problem, the second `catch` block handles `ResourceAccessException`. We can report that condition independently of HTTP status errors because there may be no completed response from which to obtain a status code.

Other failures can occur during response processing, including situations where the server returns content that cannot be converted into the requested Java type. Those failures aren’t automatically classified as HTTP status errors or network access failures, so the surrounding application may need to account for other exception types depending on the operation being performed.

HTTP error responses may also contain JSON with error codes or descriptions defined by the remote API. When those details are needed, we can inspect the response body through the exception or configure a status handler to process the returned content. The exact structure depends on the API’s error response contract.

Retry behavior requires attention as well. `RestClient` doesn’t automatically repeat a failed operation solely because the server returned an error or the request exceeded its timeout. Retrying can be appropriate for temporary communication problems, but repeated requests can have consequences for operations that create or modify resources.

Repeating a `POST` request after a read timeout could create a duplicate resource if the server completed the original operation before the response was lost. We therefore need to account for the HTTP method and the remote service’s behavior before adding automatic retries.

With the default exception hierarchy, custom status handlers, and network exception handling, we can distinguish successful responses from different failures that occur during external API communication. The methods in `PostClient` can return converted Java records when requests succeed, while callers can respond to HTTP errors and communication failures according to the operation being performed.

### Conclusion

With `RestClient` in Spring Boot 4, we can make HTTP requests to external APIs, send headers and JSON data, and read the responses as Java objects. Configuring the base URL and timeouts gives us control over how the client communicates with each service, while methods such as `retrieve()` and `body()` handle response processing. We can also handle HTTP errors and connection failures, allowing the application to respond appropriately when a request doesn’t complete as expected.

![](https://substackcdn.com/image/fetch/$s_!APSi!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F4ccdb2fd-411f-44fc-9081-abc7b4b4ad0d_276x276.png)

Spring Boot icon by Icons8
