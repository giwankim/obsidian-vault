---
title: "How to Improve Validation in Spring Boot REST APIs"
source: "https://medium.com/@AlexanderObregon/how-to-improve-validation-in-spring-boot-rest-apis-a14b40654d8d"
author:
  - "[[Alexander Obregon]]"
published: 2026-09-08
created: 2026-09-09
description: "More"
tags:
  - "clippings"
---

> [!summary]
> Layers Jakarta Bean Validation across a Spring Boot REST request flow: constraints on DTOs where data enters, validation groups (with `@Validated` and `@GroupSequence`) to apply create-versus-update rules, `@Valid` cascading into nested DTOs, and custom `@Constraint`/`ConstraintValidator` classes for cross-field domain rules. Then shows an `@RestControllerAdvice` that turns `MethodArgumentNotValidException` (bound request bodies) and `HandlerMethodValidationException` (direct controller parameters) into RFC 9457 `ProblemDetail` responses with per-field error properties, so clients get structured feedback instead of a bare 400.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*o5FmjKTPdJTbhGE2MIjo6w.jpeg)

Image Source

Validation becomes more important as a REST API grows and starts accepting more request types, serving more callers, and enforcing more business rules. Adding `@Valid` to a controller parameter is a good starting point because it tells Spring to run Bean Validation against the request object, but there is more to validation than triggering that first check. Good validation means deciding which rules belong on a DTO, how nested objects should be checked, which constraints apply during create or update requests, how custom constraints can express domain rules, and what clients receive when validation fails. Spring Boot 4 supports these pieces through the Jakarta Validation API and Hibernate Validator, allowing an existing DTO-based API to keep validation close to incoming data while controller code stays small and callers receive field-level feedback they can act on.

*You can also check out my* [*Substack*](https://alexanderobregon.substack.com/)*, where I post more articles like this and keep a* [*Java/JVM section*](https://alexanderobregon.substack.com/s/java) *with related posts. I publish my weekly recaps there too!*

## How to Strengthen the Request Model

Request DTOs give validation a natural place to protect the boundary of a REST API. By the time request data reaches service logic, values such as names, email addresses, identifiers, dates, and nested objects can already have rules attached to them. This keeps controllers from filling up with repeated `if` checks and keeps the request contract close to the fields it accepts. Jakarta Validation annotations can handle individual values, groups can select rules for a particular operation, cascaded validation can reach nested object graphs, and custom constraints can cover relationships that a field-level annotation cannot express.

### Put Constraints Where Data Enters

Incoming data is easiest to validate when each DTO carries the rules that belong to its own fields. Requirements such as a required name, valid email syntax, maximum text length, or positive quantity can live directly beside the value they apply to. Spring then has enough information to reject invalid input before service logic starts making business decisions or changing stored data.

Java records work well here because request DTOs the fields and validation rules stay close to each other without adding accessor boilerplate. We can start with a customer registration request that requires a name, an email address, and a mailing address:

```rb
import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record CustomerRegistrationRequest(
        @NotBlank
        @Size(max = 100)
        String name,

        @NotBlank
        @Email
        String email,

        @NotNull
        @Valid
        MailingAddressRequest mailingAddress
) {
}
```

Several annotations in that record have different responsibilities. `@NotBlank` rejects null text, empty text, and text made entirely from whitespace, while `@Size(max = 100)` places an upper limit on the name. `@Email` checks email syntax, and pairing it with `@NotBlank` also rejects a missing or blank email value.

That distinction is important because constraints such as `@Email` and `@Size` treat null as valid. Their job is to check a value that is present, while `@NotNull`, `@NotBlank`, and related constraints state that input has to exist. Keeping those responsibilities distinct makes the DTO more readable because each annotation expresses a specific rule.

The mailing address can carry its own requirements without repeating them on `CustomerRegistrationRequest`:

```rb
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record MailingAddressRequest(
        @NotBlank
        @Size(max = 120)
        String street,

        @NotBlank
        @Size(max = 80)
        String city,

        @NotBlank
        @Size(min = 2, max = 2)
        String stateCode,

        @NotBlank
        @Size(max = 12)
        String postalCode
) {
}
```

Now the address DTO owns the length and presence rules for its fields. The two-character state code check only verifies length, so an application that accepts only recognized codes would need a rule that matches that requirement rather than treating length as a complete state-code check. Keeping that distinction explicit prevents a formatting constraint from being mistaken for a business rule.

The controller still has to request validation when Spring binds the HTTP body to the DTO:

```rb
@PostMapping("/customers")
public ResponseEntity<CustomerResponse> register(
        @Valid @RequestBody CustomerRegistrationRequest request) {

    CustomerResponse customer = customerService.register(request);
    return ResponseEntity.status(HttpStatus.CREATED).body(customer);
}
```

Spring deserializes the request body into `CustomerRegistrationRequest`, then Jakarta Validation evaluates the DTO because the parameter carries `@Valid`. We do not need to call a validator manually for this normal request-body flow, and the controller stays focused on receiving the request and passing accepted data into the application layer.

Input validation also has a boundary of its own. Email syntax belongs naturally on the DTO because the answer depends only on the submitted value, while checking that the email is not already registered requires stored application data. That second check belongs in service logic where customer records can be queried. Keeping those concerns apart prevents request validation from growing into database-dependent logic.

### Apply Groups by Operation

Creation and update requests can share nearly all of their fields while applying different rules to a small number of values. Resource identifiers are a common case because a new customer normally should not submit an existing database identifier, while an update can require that identifier. Jakarta Validation groups let us select those operation-specific rules without duplicating the rest of the request contract.

Group types are marker interfaces. They contain no validation logic and exist only to name sets of constraints. We can define create and update groups that inherit from the standard `Default` group, then assign those groups only where the rule changes:

```rb
import jakarta.validation.groups.Default;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Null;
import jakarta.validation.constraints.Size;

public interface CreateChecks extends Default {
}

public interface UpdateChecks extends Default {
}

public record CustomerWriteRequest(
        @Null(groups = CreateChecks.class)
        @NotNull(groups = UpdateChecks.class)
        Long id,

        @NotBlank
        @Size(max = 100)
        String name,

        @NotBlank
        @Email
        String email
) {
}
```

Extending `Default` changes which constraints participate when either custom group is selected. Constraints without an explicit group belong to `Default`, so inheriting from it lets ordinary field rules run alongside the create-specific or update-specific rules. During creation, `id` has to be null because `@Null` belongs to `CreateChecks`, while an update requires a value through `@NotNull` and `UpdateChecks`. The name and email annotations remain in `Default`, which lets them participate in both operations through group inheritance.

Spring’s `@Validated` annotation can then select the requested group at the controller boundary:

```rb
@PostMapping("/customers")
public ResponseEntity<CustomerResponse> create(
        @Validated(CreateChecks.class)
        @RequestBody CustomerWriteRequest request) {

    CustomerResponse customer = customerService.create(request);
    return ResponseEntity.status(HttpStatus.CREATED).body(customer);
}

@PutMapping("/customers")
public CustomerResponse update(
        @Validated(UpdateChecks.class)
        @RequestBody CustomerWriteRequest request) {

    return customerService.update(request);
}
```

Both endpoints accept the same DTO, but they ask Jakarta Validation to evaluate different group-specific constraints. `@Valid` can trigger cascaded Bean Validation, while `@Validated` adds Spring's ability to select validation groups, which is why it appears on these request parameters. Groups are most helpful when create and update requests still represent nearly the same contract. If the operations begin accepting very different fields, distinct DTO types can become more readable than a large collection of group assignments. Groups are best kept for genuine rule differences within closely related request data.

Normal group selection also does not promise evaluation order. If validation must proceed through groups in a defined sequence, Jakarta Validation provides `@GroupSequence` for that purpose. Most REST request DTOs do not need ordered evaluation, so regular group inheritance is enough for create and update differences.

### Cascade Validation Through Nested DTOs

Nested request objects need an explicit instruction before validation travels into them. Constraints on a parent DTO do not automatically cause every referenced object to be inspected, so `@Valid` marks a nested value for cascaded validation and lets its own annotations participate in the same validation pass.

We can see the cascade in an order request that contains a shipping destination and a collection of line items:

```rb
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;

import java.util.List;

public record OrderRequest(
        @NotNull
        @Valid
        ShippingAddressRequest shippingAddress,

        @NotEmpty
        List<@Valid OrderItemRequest> items
) {
}
```

The two placements of `@Valid` cover different locations in the object graph. `shippingAddress` refers directly to a nested DTO, so `@Valid` is attached to that component. `items` is a container, so `@Valid` is placed on `OrderItemRequest` within the `List<OrderItemRequest>` declaration, telling Hibernate Validator to cascade into every line-item element.

Current Hibernate Validator guidance favors that element-level form for container contents because the type argument states directly that the contained DTO is the value that receives cascaded validation.

The line-item DTO can own its own requirements:

```rb
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.math.BigDecimal;

public record OrderItemRequest(
        @NotBlank
        String productCode,

        @Min(1)
        int quantity,

        @NotNull
        BigDecimal unitPrice
) {
}
```

Every `OrderItemRequest` in the collection is now evaluated through the cascade started by the parent DTO. The parent does not need copies of the product code, quantity, or price annotations, and the child DTO does not need any controller-specific knowledge. Each DTO keeps responsibility for the values it owns.

Container elements can also carry constraints directly when the elements are scalar values rather than nested DTOs:

```rb
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;

import java.util.Set;

public record ProductRequest(
        @NotEmpty
        @Size(max = 10)
        Set<@NotBlank String> tags
) {
}
```

In that record, `@NotEmpty` rejects an empty or null set, `@Size(max = 10)` limits the number of tags, and `@NotBlank` is evaluated against every string stored in the set. No `@Valid` is needed for the strings because the constraint already appears directly on the element type.

Cascading and null checks also answer a few different questions, `@Valid` tells the validator to inspect a nested object if a value is present, but it does not require that value to exist. Pairing `@NotNull` with `@Valid` states both requirements for `shippingAddress`, so the address must be present and its internal fields must pass validation as well.

Deeper request structures can follow the same rule. For an order, the shipping DTO can contain its own nested DTO, and validation can follow every reference marked with `@Valid`. We still want the object graph to reflect the request data itself rather than adding extra layers only for validation, because cascading is most valuable when each DTO already represents a meaningful portion of the submitted request.

### Add Domain Rules With Custom Constraints

Built-in Jakarta Validation annotations cover field-level requirements well, but some rules depend on a relationship between multiple values. Date ranges are a common case because both dates can be individually valid while the pair is invalid if the ending date comes before the starting date.

Custom constraints let us give that rule its own annotation, the annotation carries `@Constraint` and points to the `ConstraintValidator` class that performs the check:

```rb
import jakarta.validation.Constraint;
import jakarta.validation.Payload;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = ValidDateRangeValidator.class)
public @interface ValidDateRange {

    String message() default "endDate must be on or after startDate";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}
```

Jakarta Validation custom constraint annotations expose `message`, `groups`, and `payload`, while the `validatedBy` value connects the annotation to its validator class. Because the date rule depends on two fields, the annotation targets the DTO type rather than either date by itself.

The request record can combine the class-level rule with field-level null checks:

```rb
import jakarta.validation.constraints.NotNull;

import java.time.LocalDate;

@ValidDateRange
public record SubscriptionRequest(
        @NotNull
        LocalDate startDate,

        @NotNull
        LocalDate endDate
) {
}
```

Both dates must be present before the relationship between them has meaning, `@NotNull` handles missing values, while `@ValidDateRange` owns only the comparison between two dates that are available.

The validator receives the full `SubscriptionRequest`, which gives it access to both components:

```rb
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;

public class ValidDateRangeValidator
        implements ConstraintValidator<ValidDateRange, SubscriptionRequest> {

    @Override
    public boolean isValid(
            SubscriptionRequest value,
            ConstraintValidatorContext context) {

        if (value == null
                || value.startDate() == null
                || value.endDate() == null) {
            return true;
        }

        if (!value.endDate().isBefore(value.startDate())) {
            return true;
        }

        context.disableDefaultConstraintViolation();
        context.buildConstraintViolationWithTemplate(
                        context.getDefaultConstraintMessageTemplate())
                .addPropertyNode("endDate")
                .addConstraintViolation();

        return false;
    }
}
```

Returning `true` when either date is null keeps this validator focused on the relationship it owns. The field-level `@NotNull` annotations already reject missing dates, so repeating the same failure inside `ValidDateRangeValidator` would produce overlapping violations for the same input.

For present dates, the validator accepts an end date that is equal to or later than the start date. If the end date comes first, the default class-level violation is replaced with a violation attached to `endDate` through `addPropertyNode`. That leaves the rule on the full request object while associating the failed comparison with the field a caller can correct.

Custom validators should inspect submitted values without changing them during validation. Their responsibility is to decide if the supplied value satisfies the constraint and report a violation when it does not. Request-based rules such as date relationships, text formats, ranges, and cross-field comparisons belong naturally in this layer because the answer comes entirely from the submitted data.

Checks that depend on stored application state belong elsewhere. Determining if an email is already registered, if an account exists, or if inventory is available requires application data beyond the DTO itself, so those checks belong in service logic rather than inside a request validator. Keeping custom constraints focused on the submitted request prevents validation from becoming a hidden database access layer while still giving domain rules a reusable place when several fields need to be evaluated as a unit.

## Return Validation Errors Clients Can Read

Failed requests become much more helpful to API callers when the response identifies the input that was rejected and keeps the same overall structure across endpoints. Spring MVC already exposes detailed validation information through its exception types, so we can turn those details into a client-facing body without leaking internal class names, stack traces, or submitted values that do not belong in the response. `ProblemDetail` gives us the RFC 9457 fields for the overall error, while a compact collection of field entries can carry the location and message tied to each validation failure.

### Turn Binding Errors Into Field Details

Request-body validation commonly reaches Spring MVC through `MethodArgumentNotValidException`. The exception carries a `BindingResult`, and that result contains the field errors and object errors produced while Spring validated the bound request object. Rather than returning the exception text, we can pull out the pieces a client can act on, such as the property location and the resolved validation message.

It helps to give each entry a small response type before building the handler:

```rb
public record ValidationIssue(
        String field,
        String message
) {
}
```

The `field` component identifies the property tied to the failure, while `message` carries the validation message for that location. Nested DTOs retain their nested property name in the field entry, so a failure deeper in a request can appear as `shippingAddress.postalCode` or `items[0].quantity`. Object-level constraints can also produce an error without a property location, which is why `field` can remain null rather than forcing every violation onto a property.

We can then collect the binding errors inside a controller advice and place them on a `ProblemDetail` response:

```rb
@RestControllerAdvice
public class ApiValidationHandler extends ResponseEntityExceptionHandler {

    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(
            MethodArgumentNotValidException ex,
            HttpHeaders headers,
            HttpStatusCode status,
            WebRequest request) {

        List<ValidationIssue> errors = ex.getBindingResult()
                .getAllErrors()
                .stream()
                .map(error -> {
                    if (error instanceof FieldError fieldError) {
                        return new ValidationIssue(
                                fieldError.getField(),
                                fieldError.getDefaultMessage());
                    }

                    return new ValidationIssue(
                            null,
                            error.getDefaultMessage());
                })
                .toList();

        return validationResponse(
                ex,
                headers,
                status,
                request,
                errors);
    }

    private ResponseEntity<Object> validationResponse(
            Exception ex,
            HttpHeaders headers,
            HttpStatusCode status,
            WebRequest request,
            List<ValidationIssue> errors) {

        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                status,
                "One or more request values failed validation.");

        problem.setTitle("Validation failed");
        problem.setProperty("errors", errors);

        return handleExceptionInternal(
                ex,
                problem,
                headers,
                status,
                request);
    }
}
```

The handler reads every validation error from `BindingResult`. Field failures become `ValidationIssue` entries with their property locations, while an object-level failure keeps a null field and still reaches the response. That distinction helps with class-level constraints that report against the request object itself. If a custom constraint attaches its violation to a property node, Spring exposes that failure as a field error and retains the property name.

Extending `ResponseEntityExceptionHandler` keeps this handler inside Spring MVC's standard exception flow. The override receives the status and headers Spring selected for `MethodArgumentNotValidException`, then `handleExceptionInternal` builds the final `ResponseEntity` from the body we provide. For request-body validation failures of this type, Spring MVC normally returns HTTP 400.

This exception route assumes the request body reached DTO binding far enough for Bean Validation to run. Malformed JSON or a value that cannot be deserialized into the requested Java type can fail earlier through `HttpMessageNotReadableException`, so those failures are not field violations produced by Jakarta Validation. Keeping that boundary in mind prevents JSON parsing errors from being treated as constraint failures.

`ProblemDetail` supplies the standard RFC 9457 members for the overall response. The status stored in the problem becomes the HTTP status, while Spring can populate `instance` from the current request URI when no instance has been assigned. Calling `setProperty` adds custom data to the problem body. With Jackson in Spring MVC, the `errors` property is serialized at the top level beside members such as `title`, `status`, `detail`, and `instance`, and JSON problem responses are represented with `application/problem+json`.

For a failed customer request, the body can look like this:

```rb
{
  "type": "about:blank",
  "title": "Validation failed",
  "status": 400,
  "detail": "One or more request values failed validation.",
  "instance": "/customers",
  "errors": [
    {
      "field": "email",
      "message": "must be a well-formed email address"
    },
    {
      "field": "mailingAddress.postalCode",
      "message": "must not be blank"
    }
  ]
}
```

The caller can now associate each entry with the submitted property that failed. Nested locations remain intact, so `mailingAddress.postalCode` tells the client exactly where the invalid value came from within the request body instead of reducing the location to `postalCode`.

Keeping the response focused on the information needed to correct the request also avoids echoing submitted values back to the caller. `FieldError` can retain a rejected value, but returning that value by default can expose passwords, tokens, personal data, or other sensitive input. Field location and message usually provide enough information for the client to correct the request without returning the original value.

Validation messages can later come from Spring’s `MessageSource` when an API needs localized or centrally managed text. Spring validation errors support message resolution through message codes and the active locale, so the outward `ValidationIssue` record can stay the same while the handler resolves different text before constructing the response.

### Cover Controller Method Validation

Direct constraints on controller method parameters follow a different Spring MVC validation route. Query parameters, request headers, URI variables, and other controller arguments can carry Jakarta Validation constraints directly, and Spring MVC applies method validation to those constraints before the controller body runs. Failures from that route are represented by `HandlerMethodValidationException` rather than always appearing as `MethodArgumentNotValidException`.

We can see that route with query parameters on a customer search endpoint:

```rb
@GetMapping("/customers")
public List<CustomerResponse> search(
        @RequestParam(name = "query")
        @Size(min = 2, max = 50)
        String query,

        @RequestParam(name = "limit", defaultValue = "20")
        @Min(1)
        @Max(100)
        int limit) {

    return customerService.search(query, limit);
}
```

The `query` parameter has a direct `@Size` constraint, while `limit` carries `@Min` and `@Max`. Spring MVC evaluates those method-parameter constraints before entering the method body, so a search term with fewer than two characters or a limit above 100 can fail at the controller boundary.

Current Spring MVC can raise either validation exception depending on the controller signature. `MethodArgumentNotValidException` represents validation associated with a bound method argument such as a request DTO, while `HandlerMethodValidationException` represents method validation across controller parameters. When direct constraints are present on the method signature, method validation takes precedence and can include results for object parameters as well.

`HandlerMethodValidationException` exposes validation results by method parameter. Nested object results can appear as `ParameterErrors`, while direct parameter constraints appear through `ParameterValidationResult`. That gives us enough information to keep the same outward response body while reading the internal failures differently.

The same controller advice can add a handler for that exception and pass the collected entries into the existing `validationResponse` method:

```rb
@Override
protected ResponseEntity<Object> handleHandlerMethodValidationException(
        HandlerMethodValidationException ex,
        HttpHeaders headers,
        HttpStatusCode status,
        WebRequest request) {

    List<ValidationIssue> errors = new ArrayList<>();

    for (ParameterValidationResult result
            : ex.getParameterValidationResults()) {

        if (result instanceof ParameterErrors parameterErrors) {
            parameterErrors.getFieldErrors().forEach(error ->
                    errors.add(new ValidationIssue(
                            error.getField(),
                            error.getDefaultMessage())));

            parameterErrors.getGlobalErrors().forEach(error ->
                    errors.add(new ValidationIssue(
                            null,
                            error.getDefaultMessage())));

            continue;
        }

        MethodParameter parameter = result.getMethodParameter();
        RequestParam requestParam =
                parameter.getParameterAnnotation(RequestParam.class);

        String parameterName =
                requestParam != null && !requestParam.name().isBlank()
                        ? requestParam.name()
                        : Optional.ofNullable(parameter.getParameterName())
                                .orElse("arg" + parameter.getParameterIndex());

        result.getResolvableErrors().forEach(error ->
                errors.add(new ValidationIssue(
                        parameterName,
                        error.getDefaultMessage())));
    }

    return validationResponse(
            ex,
            headers,
            status,
            request,
            errors);
}
```

The loop treats nested object failures and direct method-parameter failures according to the information Spring provides for each result. `ParameterErrors` exposes field errors and global errors for an object parameter, so those entries can be translated much like errors from `BindingResult`. Regular `ParameterValidationResult` values cover direct constraints on method arguments, which means the handler needs a client-facing parameter name to place beside the validation message.

Reading the explicit name from `@RequestParam` gives the response the same label the caller sent in the HTTP request. If that annotation does not provide a name, the code falls back to the Java parameter name and then to the parameter index. That final fallback prevents the error handler from failing if Java parameter metadata is unavailable. The handler above focuses its HTTP-facing name lookup on `@RequestParam` because that is what the search endpoint accepts. Constrained headers or URI variables can reach the same `HandlerMethodValidationException`, though an API that wants their exact external names in `ValidationIssue` can read the corresponding controller annotation in the same place where the request parameter name is resolved.

Both Spring MVC validation routes now feed the same `validationResponse` method. Clients therefore receive the same problem title, detail text, HTTP status, and `errors` collection without needing to know which exception Spring selected internally. The advice still retains enough information to identify nested fields, global object failures, and direct controller parameters.

Current Spring MVC also has built-in method validation for controller methods, so class-level `@Validated` should not be added merely to activate controller method validation. Placing `@Validated` on the controller class moves method validation to Spring's proxy-based method validation instead. Parameter-level `@Validated` still has a valid purpose when selecting Bean Validation groups for an individual request object.

For controller argument failures, `HandlerMethodValidationException` carries HTTP 400. The same exception type can also represent return-value validation, where the status is HTTP 500 because the server produced a return value that failed declared constraints. Passing through the status supplied to the handler rather than hard-coding 400 preserves that distinction without extra conditionals.

## Conclusion

Validation in a Spring Boot REST API becomes more consistent when the mechanics are handled across the full request flow. Constraints on DTOs handle incoming values, groups apply operation-specific rules, `@Valid` reaches nested data, custom constraints cover cross-field checks, and `ProblemDetail` gives clients structured feedback when validation fails. Spring MVC then handles bound request failures and direct controller parameter failures through its validation exception paths, keeping invalid data from moving deeper into the application.

**Thanks for reading! If you found this helpful, highlighting, clapping, or leaving a comment really helps me out.**

![](https://miro.medium.com/v2/resize:fit:1100/format:webp/1*7LCQHSwaBMSQIyaz83xAWg.png)

Spring Boot icon by Icons8
