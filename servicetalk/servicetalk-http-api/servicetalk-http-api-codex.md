# ServiceTalk HTTP API (`servicetalk-http-api`)

## Overview

`servicetalk-http-api` is the HTTP contract layer for ServiceTalk. It defines:

- Client/server builder interfaces.
- Request/response models (streaming, aggregated, blocking, blocking-streaming).
- Filter contracts (client, connection, service).
- Execution strategy/offloading contracts.
- Header/cookie/URI utilities.
- Serialization interfaces and default serializer factories.

The central design choice is: **streaming async is the core model**, and other paradigms are adapter layers around it.

Concrete network implementations are mostly in `servicetalk-http-netty` (for example `HttpClients`/`HttpServers` factories), while this module provides the API and conversion machinery.

## Key Entry Points

| File | What it does |
|---|---|
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/SingleAddressHttpClientBuilder.java` | Main client builder contract for one logical target; configures TLS, proxy, filters, SD/LB, execution strategy. |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/MultiAddressHttpClientBuilder.java` | Browser-style client contract: selects target per request URI; supports redirect config and per-address initializer. |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpServerBuilder.java` | Main server builder contract: protocols/TLS/socket opts, acceptors, service filters, offloading strategy, `listen*` APIs. |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/StreamingHttpClient.java` | Core async streaming client contract. |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/StreamingHttpService.java` | Core async streaming service contract (`handle(...) -> Single<StreamingHttpResponse>`). |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpClient.java` | Aggregated async client contract (adapts from streaming). |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpService.java` | Aggregated async service contract (adapts to streaming). |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpApiConversions.java` | Main conversion hub between streaming/aggregated/blocking client+service+connection types. |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/StreamingHttpRequests.java` | Factory for streaming requests (user-created and transport-created). |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/StreamingHttpResponses.java` | Factory for streaming responses (user-created and transport-created). |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/StreamingHttpPayloadHolder.java` | Core payload state holder: payload/trailers storage, transforms, aggregation, flow-control bridging. |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/DefaultHttpRequestMetaData.java` | Request-target parsing/mutation, query-param state, effective host/port resolution. |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpExecutionStrategies.java` | Offload strategy factory (`default`, `none`, `all`, custom, diff/missing logic). |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/StreamingHttpServiceToOffloadedStreamingHttpService.java` | Applies required offloading delta around a streaming service. |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/ContentEncodingHttpRequesterFilter.java` | Client filter for request compression + response decompression (`Content-Encoding`/`Accept-Encoding`). |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/ContentEncodingHttpServiceFilter.java` | Server filter for request decompression + response compression. |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpExceptionMapperServiceFilter.java` | Maps known exceptions to HTTP statuses (503/415/413/500). |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpSerializers.java` | Current serializer/deserializer factory surface (text/json/form, streaming and aggregated). |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/DefaultHttpHeaders.java` | Header storage implementation plus cookie/set-cookie accessors and mutation logic. |
| `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpProviders.java` | `ServiceLoader` provider hooks for builder customization. |

## Major Call Graph / Dependencies

### 1) Paradigm adaptation flow

Typical client build chain:

`buildStreaming()` -> `StreamingHttpClient` (core)
`build()` -> `asClient()` -> `StreamingHttpClientToHttpClient`
`buildBlocking()` -> `StreamingHttpClientToBlockingHttpClient`
`buildBlockingStreaming()` -> `StreamingHttpClientToBlockingStreamingHttpClient`

Typical server/service chain:

`HttpServerBuilder.listen*` accepts multiple service types, then internally converges to streaming via:

- `ServiceToStreamingService`
- `BlockingToStreamingService`
- `BlockingStreamingToStreamingService`

and offloading wrapper:

- `StreamingHttpServiceToOffloadedStreamingHttpService`

### 2) Request/response execution path (core concepts)

1. Request metadata may carry strategy hints via `HttpContextKeys.HTTP_EXECUTION_STRATEGY_KEY`.
2. Adapter layer calls `HttpApiConversions.assignStrategy(...)`.
3. Aggregated/blocking requests are converted to streaming (`toStreamingRequest()`).
4. Streaming request goes through filter chains (`StreamingHttpClientFilter`, `StreamingHttpConnectionFilter`, `StreamingHttpServiceFilter`).
5. Response path may aggregate (`toResponse()`) or block (`toBlockingStreamingResponse()`), depending on API variant.

### 3) Payload path

- `DefaultStreamingHttpRequest`/`DefaultStreamingHttpResponse` delegate payload work to `StreamingHttpPayloadHolder`.
- `StreamingHttpPayloadHolder` maintains:
  - `messageBody` as `Publisher<?>` (Buffer and optional trailers).
  - `DefaultPayloadInfo` flags (`isEmpty`, `mayHaveTrailers`, `isSafeToAggregate`, `isGenericTypeBuffer`).
- Aggregation uses `HttpDataSourceTransformations.aggregatePayloadAndTrailers(...)`.
- Replacing payload preserves/discards old stream with bridge operators to avoid stalling upstream flow control.

### 4) Dependencies and external integrations

From `servicetalk-http-api/build.gradle`:

- Core module dependencies: buffer/client/concurrent/context/encoding/logging/oio/serialization/transport ServiceTalk modules.
- Runtime external lib: `org.slf4j:slf4j-api`.
- Test externals: Netty, JUnit 5, Mockito, Hamcrest.

Service dependencies are abstracted via APIs (no hard-coded external service):

- `ServiceDiscoverer`, `LoadBalancer`, `ConnectionFactory`, `TransportObserver`, etc.

## File/Directory Structure

Module layout:

- `servicetalk-http-api/src/main/java/io/servicetalk/http/api`
  All production APIs and default implementations (single package, 205 Java files).
- `servicetalk-http-api/src/test/java/io/servicetalk/http/api`
  Unit tests and behavior/regression tests (40 Java files).
- `servicetalk-http-api/src/testFixtures/java/io/servicetalk/http/api`
  Reusable test scaffolding for requester/service/filter tests (8 Java files).
- `servicetalk-http-api/docs/modules/ROOT/pages`
  User docs (programming paradigms, offloading model, migration guidance).

Organization is functional by class naming rather than nested packages (for example `*Client*`, `*Service*`, `*Filter*`, `*Serializer*`, `*ExecutionStrategy*`).

## Data Flow and State

### Metadata state

- `HttpRequestMetaData`/`HttpResponseMetaData` hold protocol/version/headers/context.
- `DefaultHttpRequestMetaData` lazily parses URI via `Uri3986` or `HttpAuthorityFormUri`.
- Query params are mutable via `HttpQuery`; a dirty flag rebuilds `requestTarget` when needed.

### Payload and trailers state

- Streaming models carry `Publisher` payload; aggregated models carry one `Buffer` + optional trailers.
- Conversion classes preserve payload info flags as much as possible (`PayloadInfo`, `DefaultPayloadInfo`).
- Trailer-aware transforms are done through `TrailersTransformer` APIs and mapped via `StreamingHttpPayloadHolder`.

### Execution/offloading state

- `HttpExecutionStrategy` flags model offloads for send/receive/event/close.
- `defaultStrategy()` is “safe” and context-dependent; custom strategies use `HttpExecutionStrategies.Builder`.
- Request-level override key: `HttpContextKeys.HTTP_EXECUTION_STRATEGY_KEY`.
- Service wrappers compute additional offloads with `missing(...)` and apply only the delta.

### Side effects to watch

- Content encoding filters remove `Content-Length` when (de)compression changes payload size.
- Some operations mutate headers/message-body in place (for example request/response payload transforms).
- Header and metadata objects are generally mutable and not thread-safe for arbitrary concurrent mutation.

## Behavior Seen in Tests (intent)

Representative tests show these intended guarantees:

- `RequestConversionTests` / `ResponseConversionTests`: conversions preserve payload info and payload/trailer semantics.
- `StreamingHttpPayloadHolderDrainTest`: replacing payload drains original source once and avoids leaks/stalls.
- `ContentEncodingHttpRequesterFilterTest` / `ContentEncodingHttpServiceFilterTest`: `Content-Length` is corrected and encoding headers are negotiated/validated.
- `DefaultHttpExecutionStrategyTest` and related tests: offload flags affect execution points as expected.
- Cookie tests (`LegacyCookieParsingTest`, `DefaultHttpSetCookiesRfc6265Test`): compatibility + strict RFC6265 mode support.

## Setup / Repro Notes (not executed)

- Main module test run:
  - `./gradlew :servicetalk-http-api:test`
- Strict cookie parsing suite is wired through a dedicated task in `build.gradle`:
  - `./gradlew :servicetalk-http-api:testProps`
  - This runs selected tests with system property
    `io.servicetalk.http.api.headers.cookieParsingStrictRfc6265=true`.
- Concrete end-to-end usage examples are in:
  - `servicetalk-examples/http/helloworld/...`
- Concrete HTTP client/server implementations live outside this module, primarily in:
  - `servicetalk-http-netty`
