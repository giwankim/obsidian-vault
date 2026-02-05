# servicetalk-http-api

API-only module defining ServiceTalk's HTTP abstractions for HTTP/1.x and HTTP/2. Contains interfaces, value types, adapters, and filters — no transport implementation. All HTTP-based communication in the framework (HTTP, gRPC, JAX-RS routing) flows through types defined here.

## Package Structure

All ~253 Java source files live in a single package: `io.servicetalk.http.api`.

```
src/main/java/io/servicetalk/http/api/   # All production code
src/test/java/io/servicetalk/http/api/   # ~40 test files
src/testFixtures/java/io/servicetalk/http/api/  # 8 reusable test utilities
docs/                                     # AsciiDoc guides
```

No sub-packages. Files are organized by concern (request/response, filters, serialization, etc.) within the flat package.

## Three-Tier API Model

The central design decision: every HTTP concept (request, response, client, connection, service) exists in three variants:

| Tier | Request type | Payload type | Client interface |
|---|---|---|---|
| **Async streaming** | `StreamingHttpRequest` | `Publisher<Buffer>` | `StreamingHttpClient` |
| **Blocking streaming** | `BlockingStreamingHttpRequest` | `Iterable<Buffer>` | `BlockingStreamingHttpClient` |
| **Aggregated** | `HttpRequest` | `Buffer` | `HttpClient` / `BlockingHttpClient` |

Every tier can convert to every other tier via `.toRequest()`, `.toStreamingRequest()`, `.asClient()`, `.asStreamingClient()`, etc. Adapter classes (e.g. `StreamingHttpClientToBlockingHttpClient`) handle the bridging.

## Key Entry Points

### Request / Response

| Interface | File | Role |
|---|---|---|
| `HttpRequestMetaData` | `HttpRequestMetaData.java` | method, request-target, query params, headers |
| `HttpResponseMetaData` | `HttpResponseMetaData.java` | status code, headers |
| `HttpMetaData` | `HttpMetaData.java` | shared base — version, headers, context map |
| `HttpHeaders` | `HttpHeaders.java` | case-insensitive multi-valued header map, cookie access |
| `StreamingHttpRequest` | `StreamingHttpRequest.java` | async request with `Publisher<Buffer>` payload |
| `StreamingHttpResponse` | `StreamingHttpResponse.java` | async response with `Publisher<Buffer>` payload |
| `HttpRequest` / `HttpResponse` | `HttpRequest.java` / `HttpResponse.java` | aggregated (full payload in `Buffer`) |

### Value Types

| Type | Role |
|---|---|
| `HttpRequestMethod` | GET, POST, PUT, DELETE, PATCH, etc. Properties: safe, idempotent, cacheable. |
| `HttpResponseStatus` | 50+ constants (200 OK, 404 Not Found, …). `StatusClass` enum for category. |
| `HttpProtocolVersion` | HTTP_1_0, HTTP_1_1, HTTP_2_0 |
| `HttpHeaderNames` / `HttpHeaderValues` | Standard header name and value constants |
| `HttpCookiePair` / `HttpSetCookie` | Cookie interfaces; `DefaultHttpSetCookie` handles attributes (domain, path, SameSite, etc.) |

### Client Side

| Interface | Role |
|---|---|
| `StreamingHttpClient` | Primary async client. `request(req) → Single<StreamingHttpResponse>`. Supports connection reservation. |
| `HttpClient` | Aggregated variant. |
| `BlockingHttpClient` | Synchronous variant. |
| `StreamingHttpConnection` / `HttpConnection` / `BlockingHttpConnection` | Single fixed connection. |
| `ReservedStreamingHttpConnection` | Connection reserved from pool for multi-request use. |
| `HttpRequester` / `StreamingHttpRequester` / `BlockingHttpRequester` | Base request-sending interface (client and connection both extend this). |

### Server Side

| Interface | Role |
|---|---|
| `StreamingHttpService` | `@FunctionalInterface`: `handle(ctx, request, responseFactory) → Single<StreamingHttpResponse>` |
| `HttpService` | Aggregated variant. |
| `BlockingHttpService` / `BlockingStreamingHttpService` | Blocking variants. |
| `HttpServiceContext` | Exposes connection info + execution context to the service. |

### Builders & Factories

| Type | Role |
|---|---|
| `HttpServerBuilder` | Construct HTTP servers. |
| `HttpClientBuilder` / `SingleAddressHttpClientBuilder` / `MultiAddressHttpClientBuilder` / `PartitionedHttpClientBuilder` | Construct HTTP clients with varying address resolution strategies. |
| `HttpRequestResponseFactory` / `StreamingHttpRequestResponseFactory` | Create request/response instances. |
| `HttpLoadBalancerFactory` | Pluggable load balancer for clients. |

## Filters

Middleware pattern for cross-cutting concerns. Applied as a chain.

- **Client filters:** `StreamingHttpClientFilter` / `StreamingHttpClientFilterFactory`
- **Connection filters:** `StreamingHttpConnectionFilter`
- **Service filters:** `StreamingHttpServiceFilter` / `StreamingHttpServiceFilterFactory`
- `FilterableStreamingHttpClient` / `FilterableStreamingHttpConnection` — interfaces that accept filter appending.

Built-in filter examples: `ContentEncodingHttpRequesterFilter` (gzip), header-enriching filters.

## Execution Strategy

Controls which operations are offloaded to a thread pool vs. run on the event loop.

| Type | Role |
|---|---|
| `HttpExecutionStrategy` | Query flags: `isSendOffloaded()`, `isDataReceiveOffloaded()`, `isEventOffloaded()`, etc. |
| `HttpExecutionStrategies` | Factory: `defaultStrategy()`, `offloadNone()`, `offloadAll()`, builder. |
| `HttpExecutionStrategyInfluencer` | Filters/services declare required offloads via `requiredOffloads()`. |
| `HttpExecutionContext` | Runtime context carrying ioExecutor + strategy. |

## Serialization

| Type | Role |
|---|---|
| `HttpSerializerDeserializer<T>` | Combined serialize/deserialize for aggregated payloads. |
| `HttpStreamingSerializerDeserializer<T>` | Streaming variant. |
| `HttpSerializers` | Factory methods: `textSerializer()`, `formUrlEncodedSerializer()`, `appSerializerFixLen()`, `jsonSerializer()`, etc. |
| `HttpSerializationProvider` | Plugin for content-type negotiation. |

## URI & Query Handling

- `Uri3986` — RFC 3986 compliant URI parsing.
- `HttpRequestMetaData` exposes: `rawPath()`, `path()`, `queryParameter()`, `addQueryParameter()`, `appendPathSegments()`, `effectiveHostAndPort()`.

## Configuration

| Type | Role |
|---|---|
| `ProxyConfig` / `ProxyConfigBuilder` | HTTP proxy settings. |
| `RedirectConfig` / `RedirectConfigBuilder` | Redirect following policy. |
| `Http2Settings` / `Http2SettingsBuilder` | HTTP/2 frame settings. |
| `Http2ErrorCode` | HTTP/2 error code enum. |

## Exceptions

`Http2Exception`, `ProxyConnectException`, `ProxyConnectResponseException`, `PayloadTooLargeException`, `UnsupportedContentEncodingException`, `UnsupportedHttpChunkException`.

## Call Graph / Dependencies

### Upstream (this module depends on)

API-exported:
- `servicetalk-concurrent` / `servicetalk-concurrent-api` — `Single`, `Publisher`, `Completable`
- `servicetalk-buffer-api` — `Buffer`, `BufferAllocator`
- `servicetalk-transport-api` — `HostAndPort`, transport primitives
- `servicetalk-client-api` — client contracts
- `servicetalk-context-api` — `ContextMap`
- `servicetalk-encoding-api` — `BufferEncoder` / `BufferDecoder`
- `servicetalk-serialization-api` / `servicetalk-serializer-api`
- `servicetalk-oio-api` — blocking I/O
- `servicetalk-logging-api`

Implementation-only:
- `servicetalk-concurrent-internal`, `servicetalk-encoding-api-internal`, `servicetalk-utils-internal`

### Downstream (depends on this module) — 29 modules

- **Implementation:** `servicetalk-http-netty` (Netty-based HTTP/1.1 + HTTP/2)
- **Utilities:** `servicetalk-http-utils`
- **Routing:** `servicetalk-http-router-predicate`, `servicetalk-http-router-jersey` (×3 variants)
- **Security:** `servicetalk-http-security-jersey` (×3 variants)
- **gRPC stack:** `servicetalk-grpc-api`, `servicetalk-grpc-netty`, `servicetalk-grpc-internal`, `servicetalk-grpc-protobuf`, `servicetalk-grpc-utils`
- **Serialization:** `servicetalk-data-jackson-jersey` (×3), `servicetalk-data-protobuf-jersey` (×3)
- **Observability:** `servicetalk-opentelemetry-http`, `servicetalk-opentracing-http`, `servicetalk-opentracing-zipkin-publisher`
- **Traffic:** `servicetalk-traffic-resilience-http`, `servicetalk-loadbalancer-experimental-provider`

### Architectural Position

```
┌─────────────────────────────────────────────────┐
│  servicetalk-concurrent-api / buffer-api /       │
│  transport-api / client-api / context-api        │  Foundation
└──────────────────────┬──────────────────────────┘
                       │
              ┌────────▼────────┐
              │ servicetalk-    │
              │ http-api        │  ← This module (interfaces only)
              └────────┬────────┘
         ┌─────────┬───┴───┬──────────┐
         ▼         ▼       ▼          ▼
     http-netty  http-   routers   grpc-api
     (impl)      utils   (jersey)  (layers on HTTP/2)
```

## Data Flow

**Client path:** User code → `HttpClient.request(HttpRequest)` → filter chain → `StreamingHttpClient` adapter → transport (Netty) → wire.

**Server path:** Wire → transport → `StreamingHttpService.handle()` → filter chain → user service → response back through filters → transport → wire.

**Payload transformations:**
- `payloadBody()` / `payloadBody(deserializer)` — access/deserialize body.
- `transformPayloadBody(fn)` — map payload `Publisher`.
- `transformMessageBody(fn)` — map payload including trailers.
- `toRequest()` / `toStreamingRequest()` — convert between tiers (aggregates or streams).

## Test Coverage

48 test files covering: headers, query parameters, URI parsing (RFC 3986), cookies (RFC 6265), request/response conversions, execution strategy merging, filter chains, content encoding, form-url-encoded serialization, and payload streaming.

Test fixtures provide mock contexts (`TestHttpServiceContext`), mock clients (`TestStreamingHttpClient`), and parameterized filter testing infrastructure.
