---
title: "Microservices with Spring Cloud Gateway, OAuth2 and Keycloak"
source: "https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/"
author:
  - "[[piotr.minkowski]]"
published: 2024-03-01
created: 2026-02-16
description: "This article will teach you how to use Keycloak to enable OAuth2 for Spring Cloud Gateway and Spring Boot microservices."
tags:
  - "clippings"
---

> [!summary]
> A tutorial on using Keycloak as an OAuth2 authorization server with Spring Cloud Gateway acting as both OAuth2 Client and Resource Server. Covers gateway-mediated microservice communication with token relay, inter-service bearer token propagation via WebClient, and automated testing with Testcontainers.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-01.05.27.png?w=1984&ssl=1)

This article will teach you how to use Keycloak to enable OAuth2 for Spring Cloud Gateway and Spring Boot microservices. We will extend the topics described in my previous [article](https://piotrminkowski.com/2020/10/09/spring-cloud-gateway-oauth2-with-keycloak/) and analyze some of the latest features provided within the Spring Security project.

Our architecture consists of two Spring Boot microservices, an API gateway built on top of Spring Cloud Gateway, and a Keycloak authorization server. Spring Cloud Gateway acts here as an OAuth2 Client and OAuth2 Resource Server. For any incoming request, it verifies an access token before forwarding traffic to the downstream services. It initializes an authorization code flow procedure with Keycloak for any unauthenticated request. Our scenario needs to include the communication between internal microservices. They are both hidden behind the API gateway. The `caller` app invokes an endpoint exposed by the `callme` app. The HTTP client used in that communication has to use the access token sent by the gateway.

![spring-oauth2-keycloak-arch](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-00.33.36.png?resize=1024%2C672&ssl=1)

spring-oauth2-keycloak-arch

## Source Code

If you would like to try this exercise yourself, you may always take a look at my source code. In order to do that, you need to clone my GitHub [repository](https://github.com/piomin/sample-spring-security-microservices.git). Then switch to the  `oauth`  directory. You will find two Spring Boot microservices there: `callme`  and  `caller`. Of course, there is the `gateway` app built on top of Spring Cloud Gateway. After that, you should just follow my instructions. Let’s begin.

## Run and Configure Keycloak

We are running Keycloak as a Docker container. By default, Keycloak exposes API and a web console on the port `8080`. We also need to set an admin username and password with environment variables. Here’s the command used to run the Keycloak container:

Once the container starts, we can go to the UI admin console available under the `http://localhost:8080/admin` address. We will create a new realm. The name is that realm is `demo`. Instead of creating the required things manually, we can import the JSON resource file that contains the whole configuration of the realm. You can find such a resource file in my GitHub repository here: `oauth/gateway/src/test/resources/realm-export.json`. However, in the next parts of that section, we will use the Keycloak dashboard to create objects step by step. In case you import the configuration from the JSON resource file, you can just skip to the next section.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-11.06.23.png?resize=1024%2C628&ssl=1)

Then, we need to add a single OpenID Connect client to the `demo` realm. The name of our client is `spring-with-test-scope`. We should enable client authentication and put the right address in the *“Valid redirect URIs”* field (it can be the wildcard for testing purposes).

![spring-oauth2-keycloak-client](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-11.20.22.png?resize=1024%2C558&ssl=1)

spring-oauth2-keycloak-client

We need to save the name of the client and its secret. Those two settings have to be set on the application side.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-11.22.04.png?resize=1024%2C467&ssl=1)

Then, let’s create a new client scope with the `TEST` name.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-11.28.22.png?resize=1024%2C647&ssl=1)

Then, we have to add the TEST to the `spring-with-test-scope` client scopes.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-11.29.50.png?resize=1024%2C618&ssl=1)

We also need to create a user to authenticate against Keycloak. The name of our user is `spring`. In order to set the password, we need to switch to the *“Credentials”* tab. For my user, I choose the `Spring_123` password.

![spring-oauth2-keycloak-user](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-11.40.06.png?resize=1024%2C616&ssl=1)

spring-oauth2-keycloak-user

Once we finish with the configuration, we can export it to the JSON file (the same file we can use when creating a new realm). Such a file will be useful later, for building automated tests with Testcontainers.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-11.47.34.png?resize=1024%2C469&ssl=1)

Unfortunately, Keycloak doesn’t export realm users to the file. Therefore, we need to add the following JSON to the `users` section in the exported file.

## Create Spring Cloud Gateway with OAuth2 Support and Keycloak

As I mentioned before, our gateway app will act as an OAuth2 Client and OAuth2 Resource Server. In that case, we include both the Spring Boot Auth2 Client Starter and the `spring-security-oauth2-resource-server` dependency. We also need to include the `spring-security-oauth2-jose` to decode JWT tokens automatically. Of course, we need to include the Spring Cloud Gateway Starter. Finally, we add dependencies for automated testing with JUnit. We will use Testcontainers to run the Keycloak container during the JUnit test. It can be achieved with the `com.github.dasniko:testcontainers-keycloak` dependency.

Let’s begin with the Spring Security configuration. First, we need to annotate the `Configuration` bean with `@EnableWebFluxSecurity`. That’s because Spring Cloud Gateway uses the reactive version of the Spring web module. The `oauth2Login()` method is responsible for redirecting an unauthenticated request to the Keycloak login page. On the other hand, the `oauth2ResourceServer()` method verifies an access token before forwarding traffic to the downstream services.

That’s not all. We also need to provide several configuration settings with the `spring.security.oauth2` prefix. The Spring OAuth2 Resource Server module will use the Keycloak JWKS endpoint to verify incoming JWT tokens. In the Spring OAuth2 Client section, we need to provide the address of the Keycloak issuer realm. Of course, we also need to provide the Keycloak client credentials, choose the authorization grant type and scope.

The gateway exposes a single HTTP endpoint by itself. It uses `OAuth2AuthorizedClient` bean to return the current JWT access token.

That’s all about OAuth2 configuration in that section. We also need to configure routing on the gateway in the Spring `application.yml` file. Spring Cloud Gateway can forward OAuth2 access tokens downstream to the services it is proxying using the  `TokenRelay` `GatewayFilter`. It is possible to set it as a default filter for all incoming requests. Our gateway forwards traffic to both our `callme` and `caller` microservices. I’m not using any service discovery in that scenario. By default, the `callme` app listens on the `8040` port, while the `caller` app on the `8020` port.

## Verify Tokens in Microservices with OAuth2 Resource Server

The list of dependencies for the `callme` and `caller` is pretty similar. They are exposing HTTP endpoints using the Spring Web module. Since the `caller` app uses the `WebClient` bean we also need to include the Spring WebFlux dependency. Once again, we need to include the Spring OAuth2 Resource Server module and the `spring-security-oauth2-jose` dependency for decoding JWT tokens.

Here’s the configuration of the app security. This time we need to use the `@EnableWebSecurity` annotation since we have a Spring Web module. The `oauth2ResourceServer()` method verifies an access token with the Keyclock JWKS endpoint.

Here’s the OAuth2 Resource Server configuration for Keycloak in the Spring `application.yml` file:

Let’s take a look at the implementation of the REST controller class. It is a single `ping`  method. That method may be accessed only by the client with the  `TEST`  scope. It returns a list of assigned scopes taken from the  `Authentication` bean.

This method can be invoked directly by the external client through the API gateway. However, also the `caller` app calls that endpoint inside its own “ping” endpoint implementation.

If the WebClient calls the endpoint exposed by the second microservice, it also has to propagate the bearer token. We can easily achieve it with the `ServletBearerExchangeFilterFunction` as shown below. Thanks to that Spring Security will look up the current  `Authentication`  and extract the `AbstractOAuth2Token` credential. Then, it will propagate that token in the  `Authorization` header automatically.

## Testing with Running Applications

We can run all three Spring Boot apps using the same Maven command. Let’s begin with the `gateway` app:

Once we run the first app, we can check out the logs if everything works fine. Here are the logs generated by the `gateway` app. As you see, it listens on the `8060` port.

![spring-oauth2-keycloak-run-app](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-15.54.09.png?resize=1024%2C459&ssl=1)

spring-oauth2-keycloak-run-app

After that, we can run e.g. the `caller` app.

It listens on the `8020` port.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-15.57.10.png?resize=1024%2C402&ssl=1)

Of course, the order of starting apps doesn’t matter. As the last one, we can run the `callme` app.

Now, let’s call the `caller` app endpoint through the gateway. In that case, we need to go to the `http://localhost:8060/caller/ping` URL. The gateway app will redirect us to the Keycloak login page. We need to sign in there with the `spring` user and `Spring_123` password.

![spring-oauth2-keycloak-signin](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-16.02.11.png?resize=1024%2C573&ssl=1)

spring-oauth2-keycloak-signin

After we sign in, everything happens automatically. Spring Cloud Gateway obtains the access token from Keycloak and then sends it to the downstream service. Once the `caller` app receives the request, it invokes the `callme` app using the `WebClient` instance. Here’s the result:

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-16.05.15.png?resize=1024%2C257&ssl=1)

We can easily get the access token using the endpoint `GET /token` exposed by the `gateway` app.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-16.09.12.png?resize=1024%2C191&ssl=1)

Now, we can perform a similar call as before, but with the `curl` command. We need to copy the token string and put it inside the `Authorization` header as a bearer token.

Here’s my result:

![spring-oauth2-keycloak-curl](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-16.15.06.png?resize=1024%2C540&ssl=1)

spring-oauth2-keycloak-curl

Now, let’s do a similar thing, but in a fully automated way with JUnit and Testcontainers.

## Spring OAuth2 with Keycloak Testcontainers

We need to switch to the `gateway` module once again. We will implement tests that run the API gateway app, connect it to the Keycloak instance, and route the authorized traffic in the target endpoint. Here’s the `@RestController` in the `src/test/java` directory that simulates the `callme` app endpoint:

Here’s the required configuration to run the tests. We are starting the gateway app on the `8060` port and using the `WebTestClient` instance for calling it. In order to automatically configure Keycloak we will import the `demo` realm configuration stored in the `realm-export.json`. Since Testcontainers use random port numbers we need to override some Spring OAuth2 configuration settings. We also override the Spring Cloud Gateway route, to forward the traffic to our test implementation of the `callme` app controller instead of the real service. That’s all. We can proceed to the tests implementation.

Here’s our first test. Since it doesn’t contain any token it should be redirected into the Keycloak authorization mechanism.

In the second test, we use the `WebClient` instance to interact with the Keycloak container. We need to authenticate against Kecloak with the `spring` user and the `spring-with-test-scope` client. Keycloak will generate and return an access token. We will save its value for the next test.

Finally, we run a similar test as in the first step. However, this time, we provide an access token inside the `Authorization` header. The expected response is `200 OK` and the *“Hello!”* payload, which is returned by the test instance of the `CallmeController` bean.

Let’s run all the tests locally. As you see, they are all successfully finished.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2024/02/Screenshot-2024-02-29-at-23.24.57.png?resize=1024%2C370&ssl=1)

## Final Thoughts

After publishing my previous article about Spring Cloud Gateway and Keycloak I received a lot of comments and questions with a request for some clarifications. I hope that this article answers some of them. We focused more on automation and service-to-service communication than just on the OAuth2 support in the Spring Cloud Gateway. We considered a case where a gateway acts as the OAuth2 client and resource server at the same time. Finally, we used Testcontainers to verify our scenario with Spring Cloud Gateway and Keycloak.

[Share](https://www.addtoany.com/share#url=https%3A%2F%2Fpiotrminkowski.com%2F2024%2F03%2F01%2Fmicroservices-with-spring-cloud-gateway-oauth2-and-keycloak%2F&title=Microservices%20with%20Spring%20Cloud%20Gateway%2C%20OAuth2%20and%20Keycloak)

##### Written by:

#### piotr.minkowski

##### Ari

Amazing tutorial. How do you deploy this to the cloud/k8s?

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2334)

##### piotr.minkowski

Thanks! Because it’s Spring Boot it is not hard to deploy it to any cloud or k8s. For example, you can use Azure Spring Apps (like here [https://piotrminkowski.com/2023/12/07/getting-started-with-spring-cloud-azure/](https://piotrminkowski.com/2023/12/07/getting-started-with-spring-cloud-azure/)). For Kubernetes you can just build the image with \`mvn clean spring-boot:build-image\` then run the image there.

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2335)

##### Vengal

Hi PLease kindly let me know how to create apigateway to quarkus with out using spring boot

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2339)

##### piotr.minkowski

Hi. Well, there is no module provided by Quarkus similar to Spring Cloud Gateway.

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2340)

##### enthusiast

excellent article，works fine for me，explain clearly，thanks!

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2344)

##### piotr.minkowski

You’re welcome

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2348)

##### Anish

Great content. I love the effort that you keep in your each post. Thanks

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2345)

##### piotr.minkowski

Thanks!

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2347)

##### Vinit Patel

Thank you, Piotr for the excellent article. I always look forward to read your article. Very articulate, clear and concise. I would really appreciate if you could publish articles on Keycloak RESTful service for user management such as creating new users adding/updating custom attributes and roles via API.

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2346)

##### piotr.minkowski

Thanks for suggestion. I’ll think about it.

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2349)

##### Simon

A question that’s a little peripheral to this… what’s the recommended practice around verifying that when you’re a resource server receiving a token, you’re actually an intended recipient for that token?

For example, “callme”, “caller” and “gateway” all require a token… “callme” and “caller” also require that the token carry the TEST scope. But nothing in this picture seems to ensure that the token wasn’t created for some other application which happens to share the same auth server, and should not grant \_any\_ privileges within this set of services…

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2351)

##### piotr.minkowski

Well, you can have more scopes, also use roles, define multiple realms etc. Here, it is not important who generated the token, but what privileges it has. Of course, you can provide a logic e.g. on the app side to analyze more things in the JWT then just a scope

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2353)

##### Simon

Yeah, I’m aware of the options… more just wondering what best-practices are in that space. Custom “environment-unique” scopes are how we’re currently doing it, and it works, but no idea if I’m re-inventing wheels by doing so.

For perspective, I’m an architect working on an ageing monolith, and articles like this one are very helpful in understanding what a modern target architecture can look like. I understand that it’s a simplified example — but it’s one with enough complexity and moving parts to be meaningful, so thanks for that.

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2355)

##### Sławek

Hi,

Great article. There are some fixes required in the code though.
@PreAuthorize(“hasAuthority…
will is not actually executed. @EnableMethodSecurity annotation has to be added for it to work.
I forked your repo and may prepare a PR if you wish to include fixes and tests.

Regards

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2383)

##### piotr.minkowski

Hi,
Thanks. Yes, pleease prepare a PR

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2386)

##### Maksym

Hi!
This code does not work.
Basically, there is no logic for exchanging an authorization code after the user loggged in throw Keacloak page.

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2416)

##### piotr.minkowski

Hi,
Everything works here as expected. But, maybe you have different assumptions. Such logic is automatically priovided by Spring Security.

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2430)

##### Kris

Great blog.
I was getting error with tests (quickstart is similar to demo)
2024-08-04T23:24:04.309+01:00 INFO 17036 — \[gateway-app\] \[ream-1518476187\] tc.quay.io/keycloak/keycloak:24.0: STDOUT: 2024-08-04 22:24:04,308 WARN \[org.keycloak.events\] (executor-thread-1) type=”LOGIN\_ERROR”, realmId=”384d6b71-7c16-450c-9961-7cc02023d851″, clientId=”resource-server”, userId=”null”, ipAddress=”172.17.0.1″, error=”user\_not\_found”, auth\_method=”openid-connect”, grant\_type=”password”, client\_auth\_method=”client-secret”, username=”alice”

Added Users to the export as mentioned in the article. Wish keycloak updates their export to include users also.
Thank you

[Reply](https://piotrminkowski.com/2024/03/01/microservices-with-spring-cloud-gateway-oauth2-and-keycloak/#comment-2488)
