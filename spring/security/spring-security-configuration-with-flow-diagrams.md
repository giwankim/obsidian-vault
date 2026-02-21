---
title: "Spring Security Configuration with Flow Diagrams"
source: "https://www.infoq.com/articles/spring-security-flow-diagrams/?utm_source=linkedin&utm_medium=link&utm_campaign=calendar"
author:
  - "[[Alexandr Manunin]]"
published: 2025-01-16
created: 2026-02-16
description: "Spring Security is widely used, offering numerous settings for various scenarios. The article shows basic configurations with component analysis through diagrams and code examples beyond the defaults."
tags:
  - "clippings"
---

> [!summary]
> Walks through Spring Security's filter chain configuration for user registration, login authentication, token-based authorization, and token refresh using flow diagrams. Demonstrates how custom filters, authentication providers, and AuthenticationManager collaborate, plus client-side Axios interceptor patterns for token management.

[BT](https://www.infoq.com/int/bt/ "bt")

[InfoQ Homepage](https://www.infoq.com/ "InfoQ Homepage") [Articles](https://www.infoq.com/articles "Articles") Spring Security Configuration with Flow Diagrams

[Java](https://www.infoq.com/java/ "Java")

[QCon San Francisco (Nov 16-20): Deep technical sessions. Peer conversations that change how you think.](https://qconsf.com/?utm_source=infoq&utm_medium=referral&utm_campaign=infoqyellowbox_qsf26)

Listen to this article - 25:32

### Key Takeaways

- Spring Security is a Java/Jakarta EE framework that provides authentication, authorization and other security features for enterprise applications.
- Developers can implement comprehensive configurations within Spring Security's `SecurityFilterChain` interface to manage CORS, CSRF protections, and authentication filters while allowing specific endpoints such as sign-up and login.
- Access and refresh tokens can be strategically used to balance security concerns with user convenience, minimizing the risks of token compromise while enhancing user experience.
- Axios can be used within client-side applications to handle token-based requests efficiently, with interceptors that manage token insertion and refresh scenarios, ensuring robust and seamless user interactions.
- Flow diagrams can be used to better understand the API calls that Spring Security orchestrates under the hood.

In this article, we will examine a solution for registering and authenticating a user through a client-side JavaScript application using the [Spring Security](https://spring.io/projects/spring-security) infrastructure, access and refresh tokens.

There are plenty of basic examples using Spring Security, so the goal of this article is to describe the possible process in a bit more detail using flow diagrams.

You can find the source code of the example in this GitHub [repository](https://github.com/manunin/auth-module).

**Note**: This article will focus on basic successful scenarios. Error handling and exception handling are omitted here.

## Terminology

- **Authentication** is the process of verifying a user's identity.
- **Authorization** is the process of determining what resources or actions a user is allowed to access.
- **Token** (Access Token) is a data entity containing information necessary to identify a user or grant access to restricted resources.
- **Refresh Token** is a credential that enables a client application to obtain new access tokens without requiring the user to log in again. The concept of the refresh token involves a **trade-off** between security and user convenience. While keeping a long-lived access token poses the risk of compromise, prompting the user to log in frequently diminishes user experience. Refresh tokens address this issue by:
	- Allowing the client application to obtain a new pair of tokens after the expiration of the access token, without requiring the user to log in again.
	- Reducing the window during which the access token is susceptible to compromise.

## List of Basic Processes and Spring Security Configuration

The system supports the following basic scenarios:

1. User registration.
2. User Authentication and Authorization through a login form, followed by redirection to the user's page.
3. Business Process - Requesting the count of registered users.
4. Token refresh.

The overall configuration of Spring Security can be achieved in the `filterChain()` method defined in the [`SecurityConfiguration`](https://github.com/manunin/auth-module/blob/main/src/main/java/com/manunin/auth/configuration/SecurityConfiguration.java) class:

```java
@Bean
SecurityFilterChain filterChain(final HttpSecurity http) throws Exception {
    http
       .cors(cors ->  cors.configurationSource(corsConfigurationSource()))
       .csrf(AbstractHttpConfigurer::disable)
       .exceptionHandling(configurer -> configurer
           .accessDeniedHandler(accessDeniedHandler))
       .sessionManagement(configurer -> configurer
           .sessionCreationPolicy(SessionCreationPolicy.STATELESS))
       .authorizeHttpRequests(authorize -> authorize
           .requestMatchers(SIGNIN_ENTRY_POINT).permitAll()
           .requestMatchers(SIGNUP_ENTRY_POINT).permitAll()
           .requestMatchers(SWAGGER_ENTRY_POINT).permitAll()
           .requestMatchers(API_DOCS_ENTRY_POINT).permitAll()
           .requestMatchers(TOKEN_REFRESH_ENTRY_POINT).permitAll()
           .anyRequest().authenticated()
       )
       .addFilterBefore(buildLoginProcessingFilter(), UsernamePasswordAuthenticationFilter.class)
       .addFilterBefore(buildTokenAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class)
       .addFilterBefore(buildRefreshTokenProcessingFilter(), UsernamePasswordAuthenticationFilter.class);
http.oauth2Login(configurer -> configurer
       .authorizationEndpoint(config -> config
               .authorizationRequestRepository(authorizationRequestRepository()))
       .failureHandler(failureHandler)
       .successHandler(oauth2AuthenticationSuccessHandler));

return http.build();
}
```

Let's individually break down each scenario.

## User Registration

When a user fills out the registration form with all the required fields and submits the request, the following steps occur as shown in Figure 1:

![](https://www.infoq.com/articles/spring-security-flow-diagrams/articles/spring-security-flow-diagrams/en/resources/16figure1-1736844060430.jpg)

**Figure 1: User Registration**

To allow access to the `/signup` endpoint and permit requests to bypass Spring Security's default authentication requirement, you need to configure Spring Security to permit unauthenticated access to this specific endpoint. This can be achieved by modifying the security configuration to exclude the `/signup` endpoint from the authentication requirement.

Here's how you can configure Spring Security to allow access to the `/signup` endpoint using this section of the aforementioned `filterChain()` method defined in the `SecurityConfiguration` class:

```java
.authorizeHttpRequests(authorize -> authorize
   .requestMatchers(SIGNIN_ENTRY_POINT).permitAll()
   .requestMatchers(SIGNUP_ENTRY_POINT).permitAll()
   .requestMatchers(SWAGGER_ENTRY_POINT).permitAll()
   .requestMatchers(API_DOCS_ENTRY_POINT).permitAll()
   .requestMatchers(TOKEN_REFRESH_ENTRY_POINT).permitAll()
   .anyRequest().authenticated()
)
```

The next important point is that the configuration includes a token filter, which intercepts all requests and checks the token within them as shown in this section of the `filterChain()` method:

```java
.addFilterBefore(buildLoginProcessingFilter(), UsernamePasswordAuthenticationFilter.class)
.addFilterBefore(buildTokenAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class)
.addFilterBefore(buildRefreshTokenProcessingFilter(), UsernamePasswordAuthenticationFilter.class);
```

To exclude this verification for the registration request, you need to specify the mechanism for recognizing paths with which this filter will work when constructing the token filter. Let’s look at the `buildTokenAuthenticationFilter()` method defined in the `SecurityConfiguration` class:

```java
protected TokenAuthenticationFilter buildTokenAuthenticationFilter() {
    List<String> pathsToSkip = new ArrayList<>(Arrays.asList(SIGNIN_ENTRY_POINT, SIGNUP_ENTRY_POINT, SWAGGER_ENTRY_POINT, API_DOCS_ENTRY_POINT, TOKEN_REFRESH_ENTRY_POINT));
    SkipPathRequestMatcher matcher = new SkipPathRequestMatcher(pathsToSkip);
    TokenAuthenticationFilter filter = new TokenAuthenticationFilter(jwtTokenProvider, matcher, failureHandler);
    filter.setAuthenticationManager(this.authenticationManager);
    return filter;
}
```

Here we use the [`SkipPathRequestMatcher`](https://github.com/manunin/auth-module/blob/main/src/main/java/com/manunin/auth/secutiry/matcher/SkipPathRequestMatcher.java) class (as shown below) which excludes paths specified in the `pathsToSkip` parameter from the filter's paths (in our case, we added `SIGNUP_ENTRY_POINT` to this array).

```java
public class SkipPathRequestMatcher implements RequestMatcher {
    private final OrRequestMatcher matchers;

    public SkipPathRequestMatcher(final List<String> pathsToSkip) {
        Assert.notNull(pathsToSkip, "List of paths to skip is required.");
        List<RequestMatcher> m = pathsToSkip.stream()
            .map(AntPathRequestMatcher::new)
            .collect(Collectors.toList());
        matchers = new OrRequestMatcher(m);
        }

    @Override
    public boolean matches(final HttpServletRequest request) {
        return !matchers.matches(request);
        }
    }
```

## User Authentication and Authorization through a Login Form

Once the request successfully bypasses the token filter, it proceeds to be handled by the business controller as shown in Figure 2:

![](https://www.infoq.com/articles/spring-security-flow-diagrams/articles/spring-security-flow-diagrams/en/resources/11figure2-1736844060430.jpg)

**Figure 2: User authentication and authorization through a Login Form**

1\. The client sends the username and password to the server's endpoint, `/login`.

2\. To make the [`LoginAuthenticationFilter`](https://github.com/manunin/auth-module/blob/main/src/main/java/com/manunin/auth/secutiry/login/LoginAuthenticationFilter.java) intercept the request, you need to configure Spring Security accordingly:

- define this filter and specify the URI for filtering requests using the `buildLoginProcessingFilter()` method defined in the `SecurityConfiguration` class:
```java
@Bean
protected LoginAuthenticationFilter buildLoginProcessingFilter() {
    LoginAuthenticationFilter filter = new LoginAuthenticationFilter(SIGNIN_ENTRY_POINT, authenticationSuccessHandler, failureHandler);
    filter.setAuthenticationManager(this.authenticationManager);
    return filter;
}
```

Note that in addition to the URI, when creating the filter, we also specify handlers for successful and unsuccessful authorizations, as well as an Authentication Manager. Details about them will be discussed below.

- add this URI to the list of exclusions for the token filter using the buildTokenAuthenticationFilter() method defined in the SecurityConfiguration class:
```java
List<String> pathsToSkip = new ArrayList<>(Arrays.asList(SIGNIN_ENTRY_POINT, SIGNUP_ENTRY_POINT, SWAGGER_ENTRY_POINT, API_DOCS_ENTRY_POINT, TOKEN_REFRESH_ENTRY_POINT));
```
- add the created filter to the configuration via the `filterChain()` method:
```java
@Bean
SecurityFilterChain filterChain(final HttpSecurity http) throws Exception {
     http
             .cors(cors -> cors.configurationSource(corsConfigurationSource()))

// our builder configuration

        .addFilterBefore(buildLoginProcessingFilter(), UsernamePasswordAuthenticationFilter.class)
.addFilterBefore(buildTokenAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class)
.addFilterBefore(buildRefreshTokenProcessingFilter(), UsernamePasswordAuthenticationFilter.class);

// our builder configuration

return http.build();
}
```

In the `LoginAuthenticationFilter` class, we override two methods that Spring calls during the execution of the filter. The first method is `attemptAuthentication()`, where we initiate an authentication request to the `AuthenticationManager` method we provided during the creation of the filter. However, the manager itself does not perform authentication; it serves as a container for providers that handle this task. The [`AuthenticationManager`](https://docs.spring.io/spring-security/site/docs/current/api/org/springframework/security/authentication/AuthenticationManager.html) interface takes on the responsibility of locating the appropriate provider and passing the request to it. Here's how the manager is created and providers are registered:

```java
@Bean
public AuthenticationManager authenticationManager(final ObjectPostProcessor<Object> objectPostProcessor) throws Exception {
        var auth = new AuthenticationManagerBuilder(objectPostProcessor);
        auth.authenticationProvider(loginAuthenticationProvider);
        auth.authenticationProvider(tokenAuthenticationProvider);
        auth.authenticationProvider(refreshTokenAuthenticationProvider);
        return auth.build();
}
```

Next, this manager is specified as a parameter for each created filter.

3\. To enable the `AuthenticationManager` to find the required provider (in our case, the [`LoginAuthenticationProvider`](https://github.com/manunin/auth-module/blob/main/src/main/java/com/manunin/auth/secutiry/login/LoginAuthenticationProvider.java)), it's necessary to specify which type it supports within the provider itself as shown in the `supports()` method below:

```java
@Override
public boolean supports(final Class<?> authentication) {
   return (UsernamePasswordAuthenticationToken.class.isAssignableFrom(authentication));
}
```

In our example, we specify that the provider supports the [`UsernamePasswordAuthenticationToken`](https://docs.spring.io/spring-security/site/docs/current/api/org/springframework/security/authentication/UsernamePasswordAuthenticationToken.html) class. When we create an object of type `UsernamePasswordAuthenticationToken` in the filter and pass it to the `AuthenticationManager`, it can correctly find the required provider based on the object type using the `attemptAuthentication()` method defined in the `LoginAuthenticationFilter` class:

```java
@Override
public Authentication attemptAuthentication(final HttpServletRequest request, final HttpServletResponse response) throws AuthenticationException {
    // some code above
    UsernamePasswordAuthenticationToken token = new UsernamePasswordAuthenticationToken(loginDto.getUsername(), loginDto.getPassword());
    token.setDetails(authenticationDetailsSource.buildDetails(request));
    return this.getAuthenticationManager().authenticate(token);
}
```

4\. After the `AuthenticationManager` finds the required provider, it calls the `authenticate()` method, and the provider directly performs the validation of the user's login and password. Then, the result is returned to the filter.

5\. The second method we override in the filter is `successfulAuthentication()`, which Spring calls upon successful authentication. The role of handling successful authentication falls on the Spring Security [`AuthenticationSuccessHandler`](https://docs.spring.io/spring-security/site/docs/current/api/org/springframework/security/web/authentication/AuthenticationSuccessHandler.html) interface, which we specified when creating the filter (as mentioned above). This handler has one overridden method, `onAuthenticationSuccess()`, where we typically record the generated tokens and set the successful response code for the request.

```java
// LoginAuthenticationSuccessHandler

@Override
public void onAuthenticationSuccess(final HttpServletRequest request, final HttpServletResponse response, final Authentication authentication) throws IOException {
    UserDetails userDetails = (UserDetails) authentication.getPrincipal();

    JwtPair jwtPair = tokenProvider.generateTokenPair(userDetails);

    response.setStatus(HttpStatus.OK.value());
    response.setContentType(MediaType.APPLICATION_JSON_VALUE);
    JsonUtils.writeValue(response.getWriter(), jwtPair);
}
```

Next, Spring's infrastructure, having a successful response at its disposal, forwards it to the client.

## Business Process - Requesting the Count of Registered Users

In our example, for the business request, we will consider a request to retrieve the number of users in the database. The expected behavior is that, for any request initiated by a logged-in user, we check the token. The process of token verification is initiated by the [`TokenAuthenticationFilter`](https://github.com/manunin/auth-module/blob/main/src/main/java/com/manunin/auth/secutiry/jwt/TokenAuthenticationFilter.java), and then, following a similar process described above, the request is delegated to the [`TokenAuthenticationProvider`](https://github.com/manunin/auth-module/blob/main/src/main/java/com/manunin/auth/secutiry/jwt/TokenAuthenticationProvider.java). After successful verification, the filter redirects the request to the standard filter chain of the web application, and as a result, the request reaches the business controller [`AuthController`](https://github.com/manunin/auth-module/blob/main/src/main/java/com/manunin/auth/controller/AuthController.java) as shown in Figure 3.

![](https://www.infoq.com/articles/spring-security-flow-diagrams/articles/spring-security-flow-diagrams/en/resources/11figure3-1736844060430.jpg)

**Figure 3. Requesting the count of registered users**

1\. The client sends a request to the server's endpoint, `/users/count`, along with the token.

2\. To allow the `TokenAuthenticationFilter` to intercept the request, you need to configure it within the Spring Security configuration:

- create this filter (we already saw this filter in the processes above) and specify the URI for filtering requests (in this case, all requests except those excluded in the [`SkipPathRequestMatcher`](https://github.com/manunin/auth-module/blob/main/src/main/java/com/manunin/auth/secutiry/matcher/SkipPathRequestMatcher.java) class), you need to configure it within the Spring Security configuration with the `buildTokenAuthenticationFilter()` method as shown below:
```java
protected TokenAuthenticationFilter buildTokenAuthenticationFilter() {
    List<String> pathsToSkip = new ArrayList<>(Arrays.asList(SIGNIN_ENTRY_POINT, SIGNUP_ENTRY_POINT, SWAGGER_ENTRY_POINT, API_DOCS_ENTRY_POINT, TOKEN_REFRESH_ENTRY_POINT));
    SkipPathRequestMatcher matcher = new SkipPathRequestMatcher(pathsToSkip);
    TokenAuthenticationFilter filter = new TokenAuthenticationFilter(jwtTokenProvider, matcher, failureHandler);
    filter.setAuthenticationManager(this.authenticationManager);
    return filter;
}
```

As with the previous filter, we specify the `AuthenticationManager`, which will be called to find the provider.

- add the created filter to the configuration with our `filterChain()` method:
```java
@Bean
SecurityFilterChain filterChain(final HttpSecurity http) throws Exception {
    http
        .cors(cors -> cors.configurationSource(corsConfigurationSource()))

// our builder configuration

        .addFilterBefore(buildLoginProcessingFilter(), UsernamePasswordAuthenticationFilter.class)
.addFilterBefore(buildTokenAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class)
.addFilterBefore(buildRefreshTokenProcessingFilter(), UsernamePasswordAuthenticationFilter.class);

// our builder configuration
    return http.build();
}
```

In order for the `AuthenticationManager` to find the required provider, we use the `authenticationManager()` method:

```java
@Bean
public AuthenticationManager authenticationManager(final ObjectPostProcessor<Object> objectPostProcessor) throws Exception {
    var auth = new AuthenticationManagerBuilder(objectPostProcessor);
    auth.authenticationProvider(loginAuthenticationProvider);
    auth.authenticationProvider(tokenAuthenticationProvider);
    auth.authenticationProvider(refreshTokenAuthenticationProvider);
    return auth.build();
}
```
- in the provider itself, specify the type by which requests should be filtered via the `supports()` method defined in the `TokenAuthenticationProvider` class:
```java
@Override
public boolean supports(final Class<?> authentication) {
   return (JwtAuthenticationToken.class.isAssignableFrom(authentication));
}
```

As a result, the filter should construct a [`JwtAuthenticationToken`](https://github.com/manunin/auth-module/blob/main/src/main/java/com/manunin/auth/secutiry/jwt/JwtAuthenticationToken.java) object. The AuthenticationManager will then find the appropriate provider based on its type and send the object for authentication via the `attemptAuthentication()` defined in the `TokenAuthenticationFilter` class.

```java
@Override
public Authentication attemptAuthentication(HttpServletRequest request, HttpServletResponse response) throws AuthenticationException {
    return getAuthenticationManager().authenticate(new JwtAuthenticationToken(tokenProvider.getTokenFromRequest(request)));
}
```

3\. After successful authentication, the `successfulAuthentication()` method forwards the original request to the chain of standard filters, where it eventually reaches the business controller `AuthController`.

## Token Refresh

The token refresh process is shown in Figure 4.

![](https://www.infoq.com/articles/spring-security-flow-diagrams/articles/spring-security-flow-diagrams/en/resources/8figure4-1736844060430.jpg)

**Figure 4. Token refresh**

The token refresh process is analogous to the login process:

1. The client sends a token refresh request to the `/refreshToken` endpoint.
2. The request is intercepted by the [`RefreshTokenAuthenticationFilter`](https://github.com/manunin/auth-module/blob/main/src/main/java/com/manunin/auth/secutiry/jwt/RefreshTokenAuthenticationFilter.java) because the specified URI of the endpoint is included in the list of allowed URIs for the filter.
3. The filter attempts authentication using the attemptAuthentication() method, accessing the `AuthenticationManager`, which in turn calls the [`RefreshTokenAuthenticationProvider`](https://github.com/manunin/auth-module/blob/main/src/main/java/com/manunin/auth/secutiry/jwt/RefreshTokenAuthenticationProvider.java). As described in the two examples above, this provider is selected because it supports a specific type, which is the object we construct in the filter - [`RefreshJwtAuthenticationToken`](https://github.com/manunin/auth-module/blob/main/src/main/java/com/manunin/auth/secutiry/jwt/RefreshJwtAuthenticationToken.java):
	```java
	@Override
	public boolean supports(final Class<?> authentication) {
	    return (RefreshJwtAuthenticationToken.class.isAssignableFrom(authentication));
	}
	```
4. After successful authentication, the `successAuthentication()` method calls the same handler, `LoginAuthenticationSuccessHandler`, as in the login process, which records the generated token pair in the response.

## Description of the Process on the Client Side

To illustrate the process on the JavaScript application side using a flow diagram seems quite cumbersome due to the branching of the process depending on the server response. Therefore, let's focus directly on the code, which is concise, and describe step by step what happens in it. Consider the `apiClient.js` file:

```java
// import statements

const userStore = useUserStore();

// axios client init
const apiClient = axios.create({
  baseURL: process.env.API_URL
});

// add token from userStore
function authHeader() {
  let token = userStore.getToken;
  if (token) {
    return {Authorization: 'Bearer ' + token};
  } else {
    return {};
  }
}

// add an interceptor that includes a token to each request
apiClient.interceptors.request.use(function (config) {
  config.headers = authHeader();
  return config;
});

//add an interceptor that processes each response
apiClient.interceptors.response.use(function (response) {
  return response;  //successful response
}, function (error) { //unsuccessful response
  const req = error.config;
  if (isTokenExpired(error)) {
    if (isRefreshTokenRequest(req)) {
      //refreshToken is expired, clean token info and redirect to login page
      clearAuthCache();
      window.location.href = '/login?expired=true';
    }
    // token is expired, token refresh is required
    return authService.refreshToken(userStore.getRefreshToken).then(response => {
      //save new token pair to store
      userStore.login(response);
      //repeat original business request
      return apiClient.request(req);
    });
  }
  //the code 401 we set on backend side in any unsuccessful authentication
  // including incorrect or empty tokens
  if (error.response?.status === 401) {
    clearAuthCache();
  }
  return Promise.reject(error);
});

export default apiClient;
```
1. We use the [Axios](https://axios-http.com/docs/intro) library to send requests to the server.
2. We register a request interceptor in Axios, which intercepts all requests and adds a token to them (using the `authHeader()` method).
3. We register a response interceptor in Axios, which intercepts all responses and executes the following logic:
	1. If the response is unsuccessful, we check the status code:
		1. If the response contains a `401` status code (for example, in case of an invalid or missing token), we delete all information about existing tokens and redirect to the login page.
		2. If the response contains a token expiration code (this code is generated by the server during token validation in the `TokenAuthenticationProvider` and `RefreshTokenAuthenticationProvider`), we additionally check if the original request was a token refresh request:
			1. If the original request was a regular business request, the token expiration message indicates that the access token has expired. To refresh the access token, we send a token refresh request with the `refreshToken`. Then, we save the new token pair from the response and repeat the original business request with the updated token.
			2. If the original request was a token refresh request, the token expiration message indicates that the `refreshToken` has also expired. This requires the user to log in again. Therefore, we delete all information about existing tokens and redirect to the login page.
	2. If the response is successful, we forward it to the client.

## Conclusion

In this example, we have examined several key processes of working with Spring Security and tokens in detail using flow diagrams. Beyond the scope of this article are exception handling and OAuth2, which we will cover separately in the other articles.

## About the Author

### Related Sponsors

- Sponsored by

### Related Sponsors

### The InfoQ Newsletter

A round-up of last week’s content on InfoQ sent out every Tuesday. Join a community of over 250,000 senior developers. [View an example](https://assets.infoq.com/newsletter/regular/en/newsletter_sample/newsletter_sample.html)

[BT](https://www.infoq.com/int/bt/ "bt")
