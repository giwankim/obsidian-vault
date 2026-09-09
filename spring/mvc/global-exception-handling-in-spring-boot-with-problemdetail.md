---
title: "Global Exception Handling in Spring Boot with ProblemDetail"
source: "https://alexanderobregon.substack.com/p/global-exception-handling-in-spring?utm_source=substack&utm_medium=email"
author:
  - "[[Alexander Obregon]]"
published: 2026-09-03
created: 2026-09-07
description: "Consistent error responses make REST APIs more predictable for clients because every failure follows the same general structure."
tags:
  - "clippings"
---

> [!summary]
> Centralizes REST error handling with `@RestControllerAdvice` returning RFC 9457 `ProblemDetail` bodies, so every failure shares the same `type`/`title`/`status`/`detail`/`instance` shape and Spring MVC serves it as `application/problem+json`. Walks through mapping not-found exceptions, turning bean-validation failures into structured field-level details, and masking unexpected internal errors behind a generic 500 without leaking stack traces. Ends with a tangent on Caffeine/Redis cache expiration and `@CacheEvict` around resource lookups so cache misses fall back to the service instead of surfacing as API errors.

Consistent error responses make REST APIs more predictable for clients because every failure follows the same general structure. Spring Framework represents RFC 9457 problem details through `ProblemDetail`, giving an API standard fields like `type`, `title`, `status`, `detail`, and `instance`. `@RestControllerAdvice` provides one shared place for exception mapping across controllers, which keeps controller methods centered on request handling while the advice translates exceptions into HTTP responses. Spring MVC support can also take the HTTP status directly from `ProblemDetail`, populate `instance` from the current request location when it hasn’t been set, and prefer `application/problem+json` for JSON problem responses.

### Building the Global Error Layer

Incoming requests can fail at several points before a controller has anything meaningful to return, from request conversion and validation to a service reporting that a requested resource does not exist. Handling those cases inside every controller quickly repeats the same HTTP decisions across multiple endpoints, while a shared exception layer keeps those decisions in a common place. `@RestControllerAdvice` gives Spring MVC a global location for exception handlers, and `ProblemDetail` supplies the RFC 9457 response body that those handlers can return. Controllers can then stay centered on request handling, while exceptions move through Spring MVC’s resolution process and become consistent HTTP responses.

#### ProblemDetail as the Response Contract

Consistent error bodies give clients a stable structure to read regardless of which endpoint reported the failure. Spring Framework represents RFC 9457 problem details through `ProblemDetail`, which carries the standard `type`, `title`, `status`, `detail`, and `instance` fields. Each field answers a different question about the response, so the client does not have to interpret a custom JSON layout for every failure category.

The `status` field carries the HTTP status code associated with the problem, while `title` gives the broader problem category a short name. `detail` explains the particular occurrence. For a missing book, `Book Not Found` can serve as the title while the detail identifies the requested id. That split lets repeated failures share the same broad category while still giving the client information about the request that failed.

The `type` field is a URI that identifies the problem category. If the application does not assign one, RFC 9457 treats the type as `about:blank`, which links the problem to the meaning of its HTTP status rather than a custom problem definition. APIs that publish stable error categories can assign their own type URIs, giving clients an identifier that does not depend on parsing the title or detail text.

The `instance` field points to the particular occurrence of the problem. When an `@ExceptionHandler` returns a `ProblemDetail` without setting `instance`, Spring MVC can populate it from the current request location. Requests to `/books/18` can therefore identify `/books/18` as the failing request without requiring every handler to copy that location into the response manually.

We can create a problem response from an HTTP status and a detail message, then add a title and type URI:

```markup
import java.net.URI;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;

ProblemDetail problem = ProblemDetail.forStatusAndDetail(
        HttpStatus.NOT_FOUND,
        "Book 18 was not found."
);

problem.setTitle("Book Not Found");
problem.setType(
        URI.create("https://api.example.com/problems/book-not-found")
);

return problem;
```

`ProblemDetail.forStatusAndDetail` creates the response body with status 404 and the supplied detail, while `setTitle` gives the category a readable name. `setType` adds a stable identifier for that category, which can point to API documentation if the application publishes documentation for its problem types. Returning this object from an `@ExceptionHandler` lets Spring MVC take the HTTP status from the `ProblemDetail` itself, and JSON problem responses are represented through `application/problem+json`.

The response contract can also carry fields beyond the five defined by RFC 9457. `ProblemDetail` has a properties map for application-specific data, and `setProperty` adds values to that map. With Jackson available, Spring expands those entries into top-level JSON fields. Validation responses benefit from this because several rejected fields can be returned as structured entries while the standard problem fields remain unchanged. Keeping the standard fields stable also gives API clients a predictable baseline. Code that only cares about status and detail can read those fields for every problem response, while a client that recognizes a custom `type` or an extra property can react to the richer information. The server does not need a different top-level error class for every endpoint, and the client does not need endpoint-specific parsing rules for the common problem fields.

#### Controller Code Without Repeated Handlers

Repeated `try` and `catch` blocks inside REST controllers duplicate status selection, response creation, and exception translation. The controller already maps incoming HTTP requests to application operations, so copying the same error conversion logic across endpoint methods adds noise and creates more places where the same failure can accidentally produce different response bodies.

Request validation can begin with a normal request model. Spring Boot 4 applications rely on Jakarta Validation APIs, so constraints come from the `jakarta.validation` packages:

```markup
import java.math.BigDecimal;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record CreateBookRequest(
        @NotBlank String title,
        @NotBlank String author,
        @NotNull @Positive BigDecimal price
) {
}
```

The record defines the data expected from the request body and places the validation rules beside the fields they govern. `@NotBlank` rejects blank titles and authors, while `@NotNull` and `@Positive` require a price value greater than zero. Those annotations state what qualifies as acceptable input, but they do not decide the JSON body returned after validation fails. That HTTP representation belongs in the global exception layer.

With the request model defined, the controller can accept validated input and call its service without surrounding every operation with local exception handling:

```markup
import jakarta.validation.Valid;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/books")
public class BookController {

    private final BookService bookService;

    public BookController(BookService bookService) {
        this.bookService = bookService;
    }

    @GetMapping("/{id}")
    public Book getBook(@PathVariable long id) {
        return bookService.getBook(id);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Book createBook(
            @Valid @RequestBody CreateBookRequest request) {

        return bookService.createBook(request);
    }
}
```

`getBook` delegates the lookup to the service and returns the result when the lookup succeeds. `createBook` asks Spring MVC to validate the request body before normal controller processing continues, then passes the accepted request to the service. Neither method needs to know how a missing book or rejected request becomes an RFC 9457 response because Spring MVC can route the resulting exception through its exception resolution process.

Resource lookup logic can report the domain failure at the point where the service learns that the requested data is absent:

```markup
public Book getBook(long id) {
    return bookRepository.findById(id)
            .orElseThrow(() ->
                    new BookNotFoundException(
                            "Book " + id + " was not found."
                    )
            );
}
```

The repository returns the book when the id exists, while the empty result becomes `BookNotFoundException`. The service communicates what happened through the exception type and message rather than selecting status 404 or constructing `ProblemDetail`. HTTP translation takes place later in the MVC layer, where the same mapping can cover every controller that encounters this exception. That division becomes more valuable as more endpoints call the same service operations. Several controllers can encounter `BookNotFoundException`, yet the status, title, type URI, and body structure still come from a single handler. Changing the public error representation then means changing the handler rather than tracking down copies of response-building code across controller classes.

Local `@ExceptionHandler` methods still remain available for controller-specific behavior. Spring MVC checks applicable handlers declared on the controller before global handlers declared through advice. Global advice therefore acts as the shared API policy, while a controller can still provide its own handler when a failure genuinely needs different HTTP semantics for that controller.

#### Central Exception Mapping

Cross-controller exception handling starts with exception types that state what happened without tying domain code to HTTP response creation. Domain exceptions can remain regular Java exceptions that carry a message or other application data, while the advice class translates those exceptions into status codes and `ProblemDetail` bodies.

Missing resources can be represented by a small exception class:

```markup
public class BookNotFoundException extends RuntimeException {

    public BookNotFoundException(String message) {
        super(message);
    }
}
```

`BookNotFoundException` gives the failure a distinct Java type that can be matched by `@ExceptionHandler`. The class does not need `@ResponseStatus`, `ProblemDetail`, or MVC imports because its job is to report the domain event, not decide the public HTTP response. Keeping that HTTP decision in the advice also prevents service code from becoming tied to a particular transport format.

`@RestControllerAdvice` combines controller advice behavior with response-body handling, so exception handlers declared there can return objects that Spring writes to the HTTP response body. Extending `ResponseEntityExceptionHandler` places custom handlers beside Spring MVC’s built-in exception handling and provides protected methods for tailoring several framework-generated failures.

We can map the missing-resource exception directly in the advice:

```markup
import java.net.URI;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

@RestControllerAdvice
public class GlobalExceptionHandler
        extends ResponseEntityExceptionHandler {

    @ExceptionHandler(BookNotFoundException.class)
    public ProblemDetail handleBookNotFound(
            BookNotFoundException ex) {

        ProblemDetail problem =
                ProblemDetail.forStatusAndDetail(
                        HttpStatus.NOT_FOUND,
                        ex.getMessage()
                );

        problem.setTitle("Book Not Found");
        problem.setType(
                URI.create(
                        "https://api.example.com/problems/book-not-found"
                )
        );

        return problem;
    }
}
```

The handler maps `BookNotFoundException` to status 404 and gives that problem category its own title and type URI while retaining the RFC 9457 response structure used throughout the exception layer.

Extending `ResponseEntityExceptionHandler` also preserves Spring MVC handling for framework exceptions such as unreadable request bodies, unsupported HTTP methods, missing parameters, type mismatches, and validation failures. Spring MVC represents its web exceptions through the `ErrorResponse` contract, and `ResponseEntityExceptionHandler` provides a central base for turning those exceptions into HTTP responses with RFC 9457 bodies.

Handler specificity becomes relevant when exception types have an inheritance relationship. Declaring a handler for a particular domain exception gives Spring a more precise match than declaring one for a broad parent type. This lets the advice assign the status and problem information that correspond to the actual failure category instead of treating unrelated failures as though they were the same problem.

#### Validation Errors as Structured Details

Request validation can fail through different MVC mechanisms, so the global error layer needs to account for the exception Spring raises for the validation taking place. `@Valid` on a request body commonly results in `MethodArgumentNotValidException` when Bean Validation rejects fields inside the bound object. Constraints placed directly on controller method parameters can instead result in `HandlerMethodValidationException` through MVC method validation.

Direct parameter constraints are helpful for values that arrive outside a request body, such as query parameters. We can place those constraints beside the parameters they govern:

```markup
import java.util.List;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

@GetMapping
public List<Book> findBooks(
        @RequestParam
        @Size(min = 2, max = 80)
        String title,

        @RequestParam(defaultValue = "20")
        @Min(1)
        @Max(100)
        int limit) {

    return bookService.findBooks(title, limit);
}
```

The `title` parameter must contain between 2 and 80 characters, while `limit` must remain between 1 and 100. Spring MVC can validate those method parameters as part of controller invocation, and failures can surface as `HandlerMethodValidationException`. Current MVC method validation does not require class-level `@Validated` on the controller. If that annotation is present at class level, removing it lets Spring MVC’s built-in method validation handle controller constraints rather than sending the call through method-validation AOP.

Request-body validation gives us richer field information through `MethodArgumentNotValidException`. Its binding result contains the rejected fields and their validation messages, so the advice can add those entries to the problem body while retaining the standard RFC fields:

```markup
import java.util.Map;
import java.util.Objects;

import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.context.request.WebRequest;

@Override
protected ResponseEntity<Object> handleMethodArgumentNotValid(
        MethodArgumentNotValidException ex,
        HttpHeaders headers,
        HttpStatusCode status,
        WebRequest request) {

    ProblemDetail problem =
            ProblemDetail.forStatusAndDetail(
                    status,
                    "One or more request fields failed validation."
            );

    problem.setTitle("Validation Failed");

    var errors = ex.getBindingResult()
            .getFieldErrors()
            .stream()
            .map(error -> Map.of(
                    "field", error.getField(),
                    "message", Objects.requireNonNullElse(
                            error.getDefaultMessage(),
                            "Invalid value"
                    )
            ))
            .toList();

    problem.setProperty("errors", errors);

    return handleExceptionInternal(
            ex,
            problem,
            headers,
            status,
            request
    );
}
```

The override receives the validation exception, response headers, selected status, and current request from `ResponseEntityExceptionHandler`. We build a `ProblemDetail` with the status Spring already selected, give it a validation-specific title, then transform each field error into a small map containing the field name and message. `setProperty` adds the resulting collection as `errors`, while `handleExceptionInternal` completes the response through the base handler.

Rejected requests can then produce JSON in this form:

```markup
{
  "type": "about:blank",
  "title": "Validation Failed",
  "status": 400,
  "detail": "One or more request fields failed validation.",
  "instance": "/books",
  "errors": [
    {
      "field": "title",
      "message": "must not be blank"
    },
    {
      "field": "price",
      "message": "must be greater than 0"
    }
  ]
}
```

The standard problem fields remain available to every client, while `errors` provides field-level information for clients that need to associate messages with form controls or request properties. Jackson expands the custom property at the top level when it serializes the `ProblemDetail`, so the client receives `errors` beside `type`, `title`, `status`, `detail`, and `instance`.

Method-parameter validation can receive its own customization through the protected handler supplied by `ResponseEntityExceptionHandler`. When the client only needs a shared validation title and detail, the existing problem body carried by `HandlerMethodValidationException` can be adjusted before it is returned:

```markup
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.method.annotation.HandlerMethodValidationException;

@Override
protected ResponseEntity<Object>
        handleHandlerMethodValidationException(
                HandlerMethodValidationException ex,
                HttpHeaders headers,
                HttpStatusCode status,
                WebRequest request) {

    ProblemDetail problem = ex.getBody();
    problem.setTitle("Validation Failed");
    problem.setDetail(
            "One or more request values failed validation."
    );

    return handleExceptionInternal(
            ex,
            problem,
            headers,
            status,
            request
    );
}
```

`HandlerMethodValidationException` already exposes a `ProblemDetail` body through the `ErrorResponse` contract, so the handler can adjust the title and detail without rebuilding the entire response from the beginning. Passing that body through `handleExceptionInternal` keeps the response inside the same base-handler flow as the other MVC exceptions.

Supporting both validation exception types gives the API one problem-response family across request-body validation and controller method validation. Controllers can declare constraints where they belong, while the advice controls how those failures appear over HTTP. Clients receive the same standard RFC 9457 fields in either case, with richer field data added where the validation exception provides it.

### Protecting Server Behavior

Unexpected failures and cached lookups need boundaries that preserve the API contract without exposing details that belong inside the server. The global error layer can return a restrained response to the client while logging enough information to investigate what happened. Caching introduces a different concern near resource lookups because an absent cache entry does not mean the requested resource is gone. Keeping those responsibilities distinct prevents internal exception details from reaching clients and prevents normal cache expiration from becoming an incorrect 404 response.

#### Internal Server Failures

Unexpected exceptions belong in a final MVC fallback after known domain failures and framework exceptions have had a chance to reach their more specific handlers. Missing books already have a defined 404 response, while rejected input has its validation response, so those cases should never arrive at a generic 500 handler. The fallback exists for failures that do not belong to a known public API error category, such as an unchecked exception raised while Spring MVC is processing a request.

Clients should receive restrained information for these failures. Returning `ex.getMessage()` directly can expose class names, SQL fragments, file locations, connection details, or messages produced by lower-level libraries. Server logs can retain the exception and stack trace for diagnosis, while the response body stays limited to information that is appropriate for an HTTP client.

We can add a final handler to the existing advice class:

```markup
private static final Logger log =
        LoggerFactory.getLogger(GlobalExceptionHandler.class);

@ExceptionHandler(Exception.class)
public ProblemDetail handleUnexpectedException(Exception ex) {
    log.error("Unhandled exception while processing request", ex);

    ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.INTERNAL_SERVER_ERROR,
            "The server could not complete the request."
    );

    problem.setTitle("Internal Server Error");
    return problem;
}
```

Passing `ex` as the final argument to `log.error` lets the logging framework record the exception and its stack trace. The returned `ProblemDetail` carries status 500 with a fixed public message, so information intended for diagnosis stays in the server logs rather than crossing the HTTP boundary. Clients still receive the RFC 9457 structure established earlier, which means an unexpected failure does not require a new error-body format.

The broad `@ExceptionHandler(Exception.class)` mapping belongs behind the more specific exception handling already defined in the advice. Spring MVC resolves exceptions through its handler infrastructure and selects a matching handler according to the exception type and the available mappings. `BookNotFoundException` can therefore continue through its 404 handler, while Spring MVC exceptions handled through `ResponseEntityExceptionHandler` retain their framework-specific handling instead of being flattened into status 500.

Logging and HTTP responses serve different audiences, which is why keeping their contents distinct is valuable. Server logs can contain stack traces and diagnostic context that help trace a failure back to the code location, while clients generally need the status, problem category, and a message that explains the request could not be completed. Existing request identifiers from logging or tracing infrastructure can also connect a response to its server record without exposing the underlying exception.

Broad exception handling is best kept at the web boundary rather than repeated throughout service methods. Known domain conditions can still receive dedicated exception types, while unexpected failures can travel upward until Spring MVC reaches the global fallback. This keeps status 500 reserved for failures that truly have no more specific HTTP mapping and prevents the fallback handler from swallowing meaningful domain errors that already have established responses.

#### Cache Expiration Near Resource Lookups

Cached resource lookups introduce a second layer between the controller and the backing data source, but the meaning of a missing cache entry remains very different from the meaning of a missing resource. Spring caching annotations need to be activated with `@EnableCaching` on a configuration class before `@Cacheable` and `@CacheEvict` take effect. After caching is enabled, Spring’s cache abstraction can check a cache before an annotated method executes. When the requested entry is already cached, Spring can return that value without invoking the method. When the cache has no matching entry, normal method execution continues and the backing repository gets a chance to retrieve the resource.

We can apply `@Cacheable` to the existing book lookup while preserving the same not-found behavior:

```markup
@Cacheable(cacheNames = "books")
public Book getBook(long id) {
    return bookRepository.findById(id)
            .orElseThrow(() ->
                    new BookNotFoundException(
                            "Book " + id + " was not found."
                    )
            );
}
```

Spring checks the `books` cache before executing `getBook` for that id. A cached book can be returned without running the repository query, while a cache miss allows the method body to continue normally. If the repository also has no matching book, `BookNotFoundException` travels to the global advice and becomes the same 404 problem response defined earlier. Because the method ends by throwing an exception rather than returning a `Book`, there is no successful result for `@Cacheable` to store.

Expiration follows the same distinction. Removing a cached copy does not remove the original book from the repository, so the next request should return to the service method rather than immediately report 404. If the repository still contains the book, the retrieved value can be cached again. If the repository no longer contains it, the existing domain exception reports that condition and the global handler handles the HTTP response.

Expiration duration controls how long cached data can remain before a later request reaches the backing data source again. Shorter durations result in more repository reads while reducing the period that an older cached value can remain available. Longer durations reduce repeated reads but allow cached data to remain for a greater period. Data that changes frequently will generally need a different expiration policy from data that rarely changes, so cache lifetime belongs to the caching policy rather than the exception format.

Caffeine stores cached entries inside the application process. Spring Boot 4 can auto-configure `CaffeineCacheManager` when Caffeine is available, while `spring.cache.caffeine.spec` supplies options such as entry count limits and expiration rules. Caffeine supports policies based on time after a write or time after access, which lets the cache lifetime follow how the application expects the data to be read.

For book data that should return to the backing source after five minutes, we can configure write-based expiration:

```markup
spring.cache.type=caffeine
spring.cache.cache-names=books
spring.cache.caffeine.spec=maximumSize=1000,expireAfterWrite=5m
```

`maximumSize=1000` limits the cache to 1,000 entries, while `expireAfterWrite=5m` gives each entry five minutes from creation or replacement before expiration. Reading an entry does not restart an `expireAfterWrite` duration, so repeated reads do not keep that entry alive indefinitely. The cache can therefore serve repeated requests quickly during that interval, then allow a later request to retrieve fresh data after the cached entry expires.

Caffeine works well when local cache state inside each application instance is acceptable. Cache reads stay within the JVM, but two application instances can hold different cached copies because each process owns its own Caffeine cache. That distinction becomes important when an API runs across several instances and shared cache state is desired.

Redis stores the cached data outside the JVM. Several Spring Boot instances can point to the same Redis cache, allowing them to read shared entries rather than holding independent local copies. Spring Boot can auto-configure `RedisCacheManager` when Redis is available and configured, while properties under `spring.cache.redis` control defaults such as entry lifetime.

We can give the `books` cache a five-minute Redis TTL through configuration:

```markup
spring.cache.type=redis
spring.cache.cache-names=books
spring.cache.redis.time-to-live=5m
```

The configured TTL starts when a cache entry is created and resets when that entry is updated. Normal reads do not reset a standard Redis cache TTL, so repeatedly reading the same book does not keep extending its lifetime. After the five-minute period passes without an update, the entry can expire and the next request goes back through the service lookup. Spring Data Redis can also support time-to-idle behavior through explicit configuration, but ordinary TTL behavior remains based on writes rather than reads.

Choosing Caffeine or Redis largely depends on where the cached data needs to live. Caffeine keeps entries inside each JVM and avoids a network request for cache reads, while Redis keeps them outside the application process and can share them across multiple instances. Both still participate in the same service flow, so neither changes the meaning of `BookNotFoundException` or requires a different `ProblemDetail` response.

Expiration is only part of cache freshness because some data changes are already known at the time they happen. Deleting a book is a good case because leaving its old value cached until the expiration period ends could let later requests retrieve data that no longer exists. Spring’s `@CacheEvict` can tie cache removal to the service operation that changes the backing data.

We can evict the cached book after a successful delete:

```markup
@CacheEvict(cacheNames = "books")
public void deleteBook(long id) {
    if (!bookRepository.existsById(id)) {
        throw new BookNotFoundException(
                "Book " + id + " was not found."
        );
    }

    bookRepository.deleteById(id);
}
```

Both `getBook` and `deleteBook` receive a single `id` argument, so Spring’s default cache identifier generation produces the same identifier for these calls. After `deleteBook` finishes successfully, `@CacheEvict` removes the corresponding entry from `books`. The default eviction timing happens after successful method invocation, which means an exception prevents the eviction from running.

Timed expiration and explicit eviction address different freshness cases. Expiration removes cached values according to elapsed time, while eviction responds to a known change such as deletion. Caffeine and Redis can both support the surrounding service flow, and cache misses still return to the backing lookup rather than becoming API errors on their own.

### Conclusion

Global exception handling in Spring Boot keeps API failure mechanics in a shared MVC layer, where `@RestControllerAdvice` maps exceptions and `ProblemDetail` carries consistent RFC 9457 responses back to clients. Controllers and services can stay centered on request processing, while validation failures, missing resources, and unexpected exceptions follow their defined HTTP handling. Cache misses still return to the backing lookup, with Caffeine or Redis controlling how long cached values remain available without changing the exception flow around the resource itself.

![](https://substackcdn.com/image/fetch/$s_!nnl7!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fd64ee46c-052c-4233-a995-6f8afcf65602_276x276.png)

Spring Boot icon by Icons8
