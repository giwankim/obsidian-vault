---
title: "Secure Your APIs: OAuth2 and JWT for Beginners"
source: "https://blog.jetbrains.com/kotlin/2026/07/secure-your-apis-oauth2-and-jwt-for-beginners/"
author:
  - "[[Alina Dolgikh]]"
  - "[[Website]]"
published: 2026-07-29
created: 2026-09-16
description: "Learn how OAuth2 and JWT work together to secure Spring Boot APIs with token validation, scopes, roles, and fine-grained access control."
tags:
  - "clippings"
---

> [!summary]
> JetBrains tutorial on securing Spring Boot APIs as an OAuth2 resource server with JWT bearer tokens. Covers the authentication-vs-authorization distinction, JWT structure, resource server configuration, mapping custom claims onto Spring Security authorities for `@PreAuthorize` checks, and hardening validation through issuer and audience enforcement. A companion Ktor version is planned.

[Backend](https://blog.jetbrains.com/kotlin/category/backend/) [News](https://blog.jetbrains.com/kotlin/category/news/)

*This tutorial was written by an external contributor.*

APIs are frequent targets for bad actors since they expose data and functionality. Securing them while maintaining usability is often one of the most challenging and time-consuming parts of API development. [OAuth 2.0](https://oauth.net/2/) and [JSON Web Tokens](https://jwt.io/) (JWT) help make these processes more manageable and reliable. They allow developers to represent and verify identity and manage access by safely transmitting claims and enabling delegated authorization.

This article discusses these technologies and the most efficient ways you can use them to secure your Spring Boot-built APIs and backends. If you’re interested in a coroutine‑driven solution, a companion tutorial using [Ktor](https://ktor.io/) is also planned and will be published soon.

## OAuth2 and JWT Primer

OAuth2 and JWT(s) aren’t competing technologies. They’re complementary pieces of the puzzle, with one handling the delegation of authorization and the other serving as the compact, verifiable token format that carries secure information.

### Authentication vs. Authorization

Authentication verifies identity (who you are), usually through credentials like passwords, tokens, or certificates. JWTs can carry identity information and act like a form of ID once issued. Roles and other claims within a JWT are then used for authorization.

Authorization helps control what a user has access to (what they can do). This includes the scopes or resources that they can “touch” and how those permissions are managed. In a system that uses OAuth2 and JWT, the access badge is bundled into your ID card. OAuth2 oversees and manages this process.

### The Role of OAuth2

OAuth2 is a framework for delegated access. Instead of sharing passwords directly, users grant applications a token that represents their permissions. This means that your backend (acting as a [Resource Server](https://www.oauth.com/oauth2-servers/the-resource-server/)) doesn’t have to issue tokens. Instead, it trusts and validates the ones coming from the Authorization Server within OAuth2’s framework. This decoupling of duties allows you to simplify your APIs while reducing security risks and ensuring all tokens follow a clear, consistent, centralized policy.

You don’t have to worry about implementing user logins or browser redirects within your API. As far as validation and authorization are concerned, your backend or API’s job is to receive the [Bearer Token](https://blog.postman.com/what-is-a-bearer-token/), authenticate the signature, check expiration, and enforce scopes/roles.

Your API just checks badges; it’s not responsible for printing them. So how do JWTs fit into the equation?

### What Is a JWT?

A JWT is a small, web-friendly piece of text (string) that securely transports information between systems. Their compactness makes them easy to pass around in [HTTP headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers) or URLs. Each token uses [Base64URL encoding](https://nshielddocs.entrust.com/wsop-docs/user-guide/base64url-encoding.html), making them safe to include in query strings or headers.

JWTs are signed (and sometimes encrypted), so that recipients can verify that they weren’t tampered with. They’re also self-contained, carrying details like user ID, roles, or permissions. These elements (especially self-containment and signing) allow for [stateless authentication](https://www.descope.com/learn/post/stateless-authentication) without [Session Storage](https://dev.to/aneeqakhan/a-developers-guide-to-browser-storage-local-storage-session-storage-and-cookies-4c5f#:~:text=2.%20Session%20Storage%20%E2%8F%B3). This means that you don’t need a database or cache to track active sessions. It also encourages fewer lookups and less infrastructure complexity, which reduces your system’s overhead.

JWTs have a very simple, standardized structure made up of three parts, separated by dots:

- **The Header** contains metadata about the token, such as the type (`JWT`) and the signing algorithm (`HS256`, `RS256`).
- **The Payload** features the claims, which are statements about the user or system (like user ID, roles, or token expiry).
- **The Signature** is a cryptographic signature created using the header, payload, and a secret or private key. This ensures the token has not been tampered with.

The basic structure of a JWT looks like this:

xxxxx.yyyyy.zzzzz

xxxxx.yyyyy.zzzzz

```
xxxxx.yyyyy.zzzzz
```

A real-world Base64URL-encoded token typically resembles the following:

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9

.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ

.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV\_adQssw5c

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV\_adQssw5c

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ
.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

### When OAuth2 meets JWT

There are four key roles in OAuth2’s implementation:

- **Resource Owner:** The entity (usually the user) granting access to the protected resources.
- **Client:** The application requesting access to the resource on behalf of the resource owner.
- **Authorization Server:** The server that authenticates the resource owner and issues access tokens to the client.
- **Resource Server:** The server hosting the protected resources, which accepts and validates tokens.

The Resource Owner grants permission (*e.g.*, you click “Allow” when an app requests access), the Client then requests authorization from the Authorization Server, which issues an access token (JWT) if the Resource Owner approves. The Client uses this access token to access data from the Resource Server.

## How to Implement OAuth2 and JWT

Imagine you’re building a simple document management system with a Kotlin and Spring-based backend that exposes a REST API. This implementation lets clients upload documents, list them, view specific ones, etc. Some potential endpoints the API can expose include:

- `GET /documents`: Lists all documents.
- `GET /documents/{id}`: View a specific document.
- `POST /documents`: Upload a new document.

You want to restrict access so that only authenticated users can view or upload documents, but you don’t want to manage passwords in your backend. You also don’t have to maintain sessions or deal with login forms.

### Prerequisites

If you want to follow along, you’ll need:

- [IntelliJ IDEA](https://www.jetbrains.com/idea/download/)
- [JDK 17+](https://jdk.java.net/17/)
- [Google Cloud Console](https://console.cloud.google.com/welcome/new)
- A basic understanding of [Kotlin](https://kotlinlang.org/docs/getting-started.html), Spring Boot, and Spring Security

All the code used in this tutorial is available on [GitHub repository](https://github.com/OrigamiFolds/doc-manager-kotlin-demo).

### Initial Application Setup

To start, run IntelliJ IDEA and create a new project (**File** > **New** > **Project**):

![](https://blog.jetbrains.com/wp-content/uploads/2026/04/HTiRGsQ.png)

Select **Spring Boot** under the Generators section on the left panel. Give your project a name (like `doc-manager`), select **Kotlin** as the Language, **Gradle – Kotlin** as the Type, **17** as the Java version, **Jar** as the packaging, and **Properties** as the configuration. Leave all other properties in their default state and then click **Next**.

![](https://blog.jetbrains.com/wp-content/uploads/2026/04/3uVKXW9.png)

On the next screen, select dependencies for your project. Make sure you’re using the latest stable version of Spring Boot (4.0.3 at the time of writing) and then use the search bar to find and add the following dependencies:

- Spring Security
- OAuth2 Authorization Server
- OAuth2 Resource Server
- Spring Web

Once that’s done, click **Create**.

![](https://blog.jetbrains.com/wp-content/uploads/2026/04/niTrboS.png)

After your project’s done importing and loading, expand your project, scroll down, and find the `application.properties` file under the resources folder (**src** > **main** > **resources**). Add the following lines to it:

spring.application.name=doc-manager-kotlin-demo

spring.security.oauth2.resourceserver.jwt.public-key-location=classpath:public.pem

spring.application.name=doc-manager-kotlin-demo spring.security.oauth2.resourceserver.jwt.public-key-location=classpath:public.pem

```
spring.application.name=doc-manager-kotlin-demo

spring.security.oauth2.resourceserver.jwt.public-key-location=classpath:public.pem
```

In most cases, you’d specify an [Authorization Server](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html#_specifying_the_authorization_server) (`issuer-uri`) here. But to keep things simple, you won’t be using a real Authorization Server for this part of the implementation (this will come in later). So you need to supply your application with a public key to verify signed tokens. You can generate your own `publickey.pem` using [OpenSSL](https://www.scottbrady.io/openssl/creating-rsa-keys-using-openssl) or use the ones provided in this project’s [resources folder](https://github.com/OrigamiFolds/doc-manager-kotlin-demo/tree/master/src/main/resources). Make sure to save and store the `private.pem`. You’ll need it for JWT generation.

### Configure Your Resource Server

Create a resource controller for your endpoint:

// Insert Your Package Name Here +.controller

import org.springframework.web.bind.annotation.GetMapping

import org.springframework.web.bind.annotation.RequestMapping

import org.springframework.web.bind.annotation.RestController

@RestController

@RequestMapping("/api")

class ResourceController {

@GetMapping("/fetchDocuments")

fun fetchDocumentsEndpoint(): String {

return "Here are your documents"

}

}

// Insert Your Package Name Here +.controller import org.springframework.web.bind.annotation.GetMapping import org.springframework.web.bind.annotation.RequestMapping import org.springframework.web.bind.annotation.RestController @RestController @RequestMapping("/api") class ResourceController { @GetMapping("/fetchDocuments") fun fetchDocumentsEndpoint(): String { return "Here are your documents" } }

```
// Insert Your Package Name Here + .controller

import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api")
class ResourceController {
    @GetMapping("/fetchDocuments")
    fun fetchDocumentsEndpoint(): String {
        return "Here are your documents"
    }
}
```

For now, the `ResourceController` class contains only one endpoint.

Next, create a security configuration for your Resource Server:

// Insert Your Package Name Here +.config

import org.springframework.context.annotation.Bean

import org.springframework.context.annotation.Configuration

import org.springframework.http.HttpMethod

import org.springframework.security.config.annotation.web.builders.HttpSecurity

import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity

import org.springframework.security.config.http.SessionCreationPolicy

import org.springframework.security.web.SecurityFilterChain

@Configuration

@EnableWebSecurity

class OAuth2ResourceServerSecurityConfiguration {

@Bean

@Throws(Exception::class)

fun securityFilterChain(http: HttpSecurity): SecurityFilterChain =

http

.httpBasic { it.disable() }

.formLogin { it.disable() } // Disables Spring's default form-based login

.csrf { it.disable() }

.authorizeHttpRequests {

it.requestMatchers(HttpMethod.GET, "/api/fetchDocuments").hasAuthority("SCOPE\_read:documents") // Verifies that client has read access

it.anyRequest().authenticated()

}

.oauth2ResourceServer { // Enables JWT‑based authentication for an OAuth2 Resource Server.

it.jwt { }

}

.sessionManagement { it.sessionCreationPolicy(SessionCreationPolicy.STATELESS) }

.build()

}

// Insert Your Package Name Here +.config import org.springframework.context.annotation.Bean import org.springframework.context.annotation.Configuration import org.springframework.http.HttpMethod import org.springframework.security.config.annotation.web.builders.HttpSecurity import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity import org.springframework.security.config.http.SessionCreationPolicy import org.springframework.security.web.SecurityFilterChain @Configuration @EnableWebSecurity class OAuth2ResourceServerSecurityConfiguration { @Bean @Throws(Exception::class) fun securityFilterChain(http: HttpSecurity): SecurityFilterChain = http.httpBasic { it.disable() }.formLogin { it.disable() } // Disables Spring's default form-based login.csrf { it.disable() }.authorizeHttpRequests { it.requestMatchers(HttpMethod.GET, "/api/fetchDocuments").hasAuthority("SCOPE\_read:documents") // Verifies that client has read access it.anyRequest().authenticated() }.oauth2ResourceServer { // Enables JWT‑based authentication for an OAuth2 Resource Server. it.jwt { } }.sessionManagement { it.sessionCreationPolicy(SessionCreationPolicy.STATELESS) }.build() }

```
// Insert Your Package Name Here + .config

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.http.HttpMethod
import org.springframework.security.config.annotation.web.builders.HttpSecurity
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity
import org.springframework.security.config.http.SessionCreationPolicy
import org.springframework.security.web.SecurityFilterChain

@Configuration
@EnableWebSecurity
class OAuth2ResourceServerSecurityConfiguration {

    @Bean
    @Throws(Exception::class)
    fun securityFilterChain(http: HttpSecurity): SecurityFilterChain =
        http
            .httpBasic { it.disable() }
            .formLogin { it.disable() }     // Disables Spring's default form-based login
            .csrf { it.disable() }
            .authorizeHttpRequests {
                it.requestMatchers(HttpMethod.GET, "/api/fetchDocuments").hasAuthority("SCOPE_read:documents") // Verifies that client has read access
                it.anyRequest().authenticated()
            }
            .oauth2ResourceServer {  // Enables JWT‑based authentication for an OAuth2 Resource Server.
                it.jwt { }
            }
            .sessionManagement { it.sessionCreationPolicy(SessionCreationPolicy.STATELESS) }
            .build()
}
```

If you’ve worked with Spring Security in Java before, you’ll likely notice how clean the Kotlin DSL looks in comparison. References to `OAuth2LoginConfigurer`, wrapping lambdas in `Customizer`, or even annotations like `@Throws(Exception::class)` aren’t strictly necessary (unless you’re working with a mix of Java and Kotlin). Kotlin’s DSL trims that away and lets you express the rules directly.

Now, generate the JWT using the private key (found in the `private.pem`). Make sure to encode it using the `RS256` and that the claims are set and formatted correctly:

![](https://blog.jetbrains.com/wp-content/uploads/2026/04/3I6kIgA.webp)

Run your Spring Boot application and then initiate an authenticated request to the `/fetchDocuments` API endpoint with your generated JWT as the bearer token:

GET http://localhost:8080/api/fetchDocuments

Bearer Token \<JWT>

GET http://localhost:8080/api/fetchDocuments Bearer Token \<JWT>

```
GET http://localhost:8080/api/fetchDocuments
Bearer Token <JWT>
```
![](https://blog.jetbrains.com/wp-content/uploads/2026/04/N91Ktiq.png)

If it works as it should, you should see “Here are your documents” as a response. This implementation enables you to simulate a client sending a request with a Bearer token (JWT). Upon receiving the token, your Resource Server (backend) checks the expiry date and signature using the details in your application’s properties file. It also looks for the `read:documents` scope before granting access to the `fetchDocument` endpoint.

## Handling Advanced Patterns and Validations

In a document management API (and most complex systems), simple scope checks aren’t enough. They can grant coarse permissions, but they often fail to capture the nuance of real-world access control. To address this, the system must separate token validation (ensuring the JWT is authentic) from business authorization (deciding what actions a user can perform).

Scopes alone can’t enforce ownership or hierarchical rules, and they don’t capture organizational roles. That’s why you need a combination of scope and role-based access, where administrators can access all features, while lower-level users are granted only a few. By layering roles, scopes, and resource checks, the API achieves fine-grained, context-aware authorization that balances security with usability.

Hardcoding security decisions in such systems should be avoided at all costs. Practices like embedding role checks or scope logic directly into controller methods may seem convenient at first, but it introduces significant risks as your system grows. A developer might forget to update one of these hardcoded checks when business requirements change, leaving certain endpoints exposed or inconsistent. Hardcoding also undermines separations of concerns. Security decisions should be modeled in a dedicated layer, not mixed into business logic.

### Using Custom Claim Extraction and Spring Security’s PreAuthorize

Like most token formats, JWTs can carry custom claims in their payloads. A JWT with custom claims for roles and permissions would look something like this:

{

"iss": "https://myapp.com/auth",

"sub": "mdu",

"iat": 1773754406,

"exp": 1773840838,

"scope": "read:documents",

"roles": \["admin", "editor"\],

"permissions": \["documents:read:all", "documents:write:own"\]

}

{ "iss": "https://myapp.com/auth", "sub": "mdu", "iat": 1773754406, "exp": 1773840838, "scope": "read:documents", "roles": \["admin", "editor"\], "permissions": \["documents:read:all", "documents:write:own"\] }

```
{
  "iss": "https://myapp.com/auth",
  "sub": "mdu",
  "iat": 1773754406,
  "exp": 1773840838,
  "scope": "read:documents",
  "roles": ["admin", "editor"],
  "permissions": ["documents:read:all", "documents:write:own"]
}
```

Spring handles authority mapping for scopes out of the box and provides a `hasRole` function. However, roles aren’t automatically extracted from JWTs because there is no universal standard for how identity providers represent them. Scopes are standardized in OAuth2 and OpenID Connect, so Spring can safely map them into authorities. Roles often appear under custom claims and require a custom converter to translate them into Spring’s expected format before they can be used effectively.

Let’s say you want to authenticate and authorize based on roles and scope. Navigate to your security config and add the following function:

@Bean

fun jwtAuthenticationConverter(): JwtAuthenticationConverter {

val converter = JwtAuthenticationConverter()

converter.setJwtGrantedAuthoritiesConverter { jwt ->

val authorities = mutableListOf\<GrantedAuthority>()

// Map scopes

val scopes = (jwt.claims\["scope"\] as? String)?.split(" ")?: emptyList()

authorities.addAll(scopes.map { SimpleGrantedAuthority("SCOPE\_$it") })

// Map roles

val roles = jwt.claims\["roles"\] as? Collection<\*>?: emptyList\<Any>()

authorities.addAll(roles.map { SimpleGrantedAuthority("ROLE\_$it") })

// Map permissions

val permissions = jwt.claims\["permissions"\] as? Collection<\*>?: emptyList\<Any>()

authorities.addAll(permissions.map { SimpleGrantedAuthority(it.toString()) })

authorities

}

return converter

}

@Bean fun jwtAuthenticationConverter(): JwtAuthenticationConverter { val converter = JwtAuthenticationConverter() converter.setJwtGrantedAuthoritiesConverter { jwt -> val authorities = mutableListOf\<GrantedAuthority>() // Map scopes val scopes = (jwt.claims\["scope"\] as? String)?.split(" ")?: emptyList() authorities.addAll(scopes.map { SimpleGrantedAuthority("SCOPE\_ $it") })

        // Map roles
        val roles = jwt.claims["roles"] as? Collection<*> ?: emptyList<Any>()
        authorities.addAll(roles.map { SimpleGrantedAuthority("ROLE_$ it") }) // Map permissions val permissions = jwt.claims\["permissions"\] as? Collection<\*>?: emptyList\<Any>() authorities.addAll(permissions.map { SimpleGrantedAuthority(it.toString()) }) authorities } return converter }

```
@Bean
fun jwtAuthenticationConverter(): JwtAuthenticationConverter {
    val converter = JwtAuthenticationConverter()
    converter.setJwtGrantedAuthoritiesConverter { jwt ->
        val authorities = mutableListOf<GrantedAuthority>()

        // Map scopes
        val scopes = (jwt.claims["scope"] as? String)?.split(" ") ?: emptyList()
        authorities.addAll(scopes.map { SimpleGrantedAuthority("SCOPE_$it") })

        // Map roles
        val roles = jwt.claims["roles"] as? Collection<*> ?: emptyList<Any>()
        authorities.addAll(roles.map { SimpleGrantedAuthority("ROLE_$it") })

        // Map permissions
        val permissions = jwt.claims["permissions"] as? Collection<*> ?: emptyList<Any>()
        authorities.addAll(permissions.map { SimpleGrantedAuthority(it.toString()) })

        authorities
    }
    return converter
}
```

This changes the behaviour of the `JwtAuthenticationConverter` so that it no longer relies solely on Spring Security’s default scope mapping. Instead, it explicitly maps both scopes and roles from the JWT into Spring authorities. If you mapped only roles, then Spring Security would ignore the `scope` claim entirely.

Kotlin ensures the safe extraction of custom claims thanks to its null-safety. For instance, take a look at the scope mapping section of the code. The safe call operator (`?.`) ensures that if `jwt.claims["scope"]` is `null`, the chain stops gracefully instead of throwing a `NullPointerException`. The safe cast operator (`as? String`) attempts to convert the value returned from the `jwt.claims["scope"]` operation into a `String` from an `Any?` (could be anything or null). If the safe cast operator fails, it returns `null` instead of throwing a `ClassCastException`. This allows for type-safe conversions that won’t interrupt or break your code. The Elvis operator (`?:`) provides a fallback value when the left-hand side is `null`. So if the role is missing for whatever reason, the function returns an empty list as a default value.

The tricky part is adding validations for all these claims. If you were checking these claims individually, you could use the `hasRole` function for roles, and `hasAuthority` for scopes and permissions. One way to chain these validations together would be to use the [access](https://docs.spring.io/spring-security/reference/api/java/org/springframework/security/config/annotation/web/configurers/AuthorizeHttpRequestsConfigurer.AuthorizedUrl.html#access\(org.springframework.security.authorization.AuthorizationManager\)) function. Here, you’ll use \[Spring’s Method Security\]([Spring @EnableMethodSecurity Annotation | Baeldung](https://www.baeldung.com/spring-enablemethodsecurity)) (`@PreAuthorize`) because it offers a more fine-grained and cleaner approach.

Return to your Security Config file and place the `@EnableMethodSecurity(prePostEnabled = true)` above the class definition:

...

import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity

@Configuration

@EnableWebSecurity

@EnableMethodSecurity(prePostEnabled = true)

class OAuth2ResourceServerSecurityConfiguration {

class SecurityConfig(

...

... import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity @Configuration @EnableWebSecurity @EnableMethodSecurity(prePostEnabled = true) class OAuth2ResourceServerSecurityConfiguration { class SecurityConfig(...

```
...
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity

@Configuration
@EnableWebSecurity
@EnableMethodSecurity(prePostEnabled = true)
class OAuth2ResourceServerSecurityConfiguration {
    class SecurityConfig(
...
```

You can keep your security filter chain as is for now. Navigate to your resource controller, and add the `@PreAuthorize` annotation to it:

...

@GetMapping("/fetchDocuments")

@PreAuthorize("hasRole('admin') and hasAuthority('documents:read:all')")

fun fetchDocumentsEndpoint(): String {

return "Here are your documents"

}

...

... @GetMapping("/fetchDocuments") @PreAuthorize("hasRole('admin') and hasAuthority('documents:read:all')") fun fetchDocumentsEndpoint(): String { return "Here are your documents" }...

```
...
@GetMapping("/fetchDocuments")
@PreAuthorize("hasRole('admin') and hasAuthority('documents:read:all')")
fun fetchDocumentsEndpoint(): String {
    return "Here are your documents"
}
...
```

This ensures that only admins with read-all permissions can access the `fetchDocuments` endpoint. You can create more endpoints, like `getDocument` and `deleteDocument` to test the combination of your roles and permissions. The `@PreAuthorize` annotation helps you avoid embedding role checks or scope logic directly inside controller methods (for example, writing `if (user.hasRole("admin")) { ... }` in the body of a controller). Alternatively, you can perform your role checks in your filter chain and your scope and permission checks on the method level.

### Strengthening Token Trust: Issuer and Audience Enforcement

Under most normal circumstances, you’d supply Spring Security with an issuer URI in your application properties file. Then Spring would do the work of finding the [Provider Configuration](https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderConfig) or [Authorization Server Metadata](https://tools.ietf.org/html/rfc8414#section-3) and using them to decode your JWT. But as you learned here, these can be bypassed when you’re using custom-generated keys.

Regardless of whether you’ve configured an issuer URI or not, it’s important to explicitly verify the issuer (`iss`) in your code to ensure that every incoming token actually claims the same issuer and prevent token replay across apps. This adds defense in depth and makes your security posture clear in code. Likewise, audience (`aud`) ensures that the token is meant for your API, not for some other application. When both the issuer and the audience are checked, it prevents tokens from other apps or environments from being accepted by your API.

To validate these claims, you’ll need to create a custom [JwtDecoder](https://docs.spring.io/spring-security/reference/api/java/org/springframework/security/oauth2/jwt/JwtDecoder.html). But, because Spring doesn’t have a dedicated [OAuth2TokenValidator](https://docs.spring.io/spring-security/reference/api/java/org/springframework/security/oauth2/core/OAuth2TokenValidator.html) for its audience, you’ll need to create one. Re-open your Security Configuration file and add the following class (nested):

class AudienceValidator(private val audience: String): OAuth2TokenValidator\<Jwt> {

override fun validate(token: Jwt): OAuth2TokenValidatorResult =

if (token.audience.contains(audience)) {

OAuth2TokenValidatorResult.success()

} else {

OAuth2TokenValidatorResult.failure(OAuth2Error("invalid\_token", "The required audience is missing", null))

}

}

class AudienceValidator(private val audience: String): OAuth2TokenValidator\<Jwt> { override fun validate(token: Jwt): OAuth2TokenValidatorResult = if (token.audience.contains(audience)) { OAuth2TokenValidatorResult.success() } else { OAuth2TokenValidatorResult.failure(OAuth2Error("invalid\_token", "The required audience is missing", null)) } }

```
class AudienceValidator(private val audience: String) : OAuth2TokenValidator<Jwt> {
    override fun validate(token: Jwt): OAuth2TokenValidatorResult =
        if (token.audience.contains(audience)) {
            OAuth2TokenValidatorResult.success()
        } else {
            OAuth2TokenValidatorResult.failure(OAuth2Error("invalid_token", "The required audience is missing", null))
        }
}
```

> [!warning] Warning
> **Warning:** Don’t forget to import all necessary classes and interfaces

Then, add the following method:

@Bean

fun jwtDecoder(): JwtDecoder {

val issuer = "https://myapp.com/auth" // Replace with your own official issuer URI

val audience = "http://localhost:8080/api/"

val decoder = JwtDecoders.fromIssuerLocation\<NimbusJwtDecoder>(issuer)

// Add audience validation

val audienceValidator = AudienceValidator(audience)

val issuerValidator = JwtValidators.createDefaultWithIssuer(issuer)

val validator = DelegatingOAuth2TokenValidator(listOf(issuerValidator, audienceValidator))

(decoder as NimbusJwtDecoder).setJwtValidator(validator)

return decoder

}

@Bean fun jwtDecoder(): JwtDecoder { val issuer = "https://myapp.com/auth" // Replace with your own official issuer URI val audience = "http://localhost:8080/api/" val decoder = JwtDecoders.fromIssuerLocation\<NimbusJwtDecoder>(issuer) // Add audience validation val audienceValidator = AudienceValidator(audience) val issuerValidator = JwtValidators.createDefaultWithIssuer(issuer) val validator = DelegatingOAuth2TokenValidator(listOf(issuerValidator, audienceValidator)) (decoder as NimbusJwtDecoder).setJwtValidator(validator) return decoder }

```
@Bean
fun jwtDecoder(): JwtDecoder {
        val issuer = "https://myapp.com/auth"           // Replace with your own official issuer URI
        val audience = "http://localhost:8080/api/"

        val decoder = JwtDecoders.fromIssuerLocation<NimbusJwtDecoder>(issuer)

        // Add audience validation
        val audienceValidator = AudienceValidator(audience)
        val issuerValidator = JwtValidators.createDefaultWithIssuer(issuer)

        val validator = DelegatingOAuth2TokenValidator(listOf(issuerValidator, audienceValidator))
        (decoder as NimbusJwtDecoder).setJwtValidator(validator)

        return decoder
}
```

This function builds a custom `JwtDecoder` that enforces stricter validation on incoming JWTs. It starts by creating a decoder from the configured issuer, then defines two validators: one to ensure the token’s `aud` claim matches the expected audience, and another to ensure the `iss` claim matches the trusted issuer. These validators are combined into a `DelegatingOAuth2TokenValidator` and applied to the decoder, so that only tokens issued by the correct identity provider and intended for your application are accepted.

Add the validation to your security filter chain:

@Bean

@Throws(Exception::class)

fun securityFilterChain(http: HttpSecurity): SecurityFilterChain =

http

.httpBasic { it.disable() }

.formLogin { it.disable() }

.csrf { it.disable() }

.authorizeHttpRequests {

it.requestMatchers("/api/fetchDocuments").hasAuthority("SCOPE\_read:documents")

it.anyRequest().authenticated()

}

.oauth2ResourceServer {

it.jwt { jwt ->

jwt.jwtAuthenticationConverter(jwtAuthenticationConverter())

jwt.decoder(jwtDecoder()) // Add custom JwtDecoder

}

}

.sessionManagement { it.sessionCreationPolicy(SessionCreationPolicy.STATELESS) }

.build()

@Bean @Throws(Exception::class) fun securityFilterChain(http: HttpSecurity): SecurityFilterChain = http.httpBasic { it.disable() }.formLogin { it.disable() }.csrf { it.disable() }.authorizeHttpRequests { it.requestMatchers("/api/fetchDocuments").hasAuthority("SCOPE\_read:documents") it.anyRequest().authenticated() }.oauth2ResourceServer { it.jwt { jwt -> jwt.jwtAuthenticationConverter(jwtAuthenticationConverter()) jwt.decoder(jwtDecoder()) // Add custom JwtDecoder } }.sessionManagement { it.sessionCreationPolicy(SessionCreationPolicy.STATELESS) }.build()

```
@Bean
@Throws(Exception::class)
fun securityFilterChain(http: HttpSecurity): SecurityFilterChain =
    http
        .httpBasic { it.disable() }
        .formLogin { it.disable() }
        .csrf { it.disable() }
        .authorizeHttpRequests {
            it.requestMatchers("/api/fetchDocuments").hasAuthority("SCOPE_read:documents")

            it.anyRequest().authenticated()
        }
        .oauth2ResourceServer {
            it.jwt { jwt ->
                jwt.jwtAuthenticationConverter(jwtAuthenticationConverter())
                jwt.decoder(jwtDecoder())         // Add custom JwtDecoder
            }
        }
        .sessionManagement { it.sessionCreationPolicy(SessionCreationPolicy.STATELESS) }
        .build()
```

This allows the strict enforcement of the rules by the backend, never leaving it up to frontend logic to authorize or validate sensitive information.

## What’s Next?

Strong security requires fine-grained control and layered safeguards beyond basic authentication. Use short-lived tokens with clear refresh and revocation strategies to limit exposure and prevent compromised tokens from persisting. Avoid using JWTs for session storage, as this leads to token bloat, complicates revocation, and increases the risk of exposing sensitive data. Instead, keep JWTs focused on authentication and authorization claims, and enforce validation of issuer, audience, signature, and expiry to ensure tokens are trustworthy and intended for your application.

Ultimately, securing Spring Boot APIs with OAuth2 and JWT depends on careful design, explicit configuration, and a clear understanding of how tokens, scopes, and identities are validated and enforced. Kotlin complements this by promoting null safety, immutability, and concise configuration, helping reduce misconfigurations and overlooked edge cases.
