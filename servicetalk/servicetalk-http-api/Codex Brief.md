# servicetalk-http-api brief

**Overview**
This subproject defines ServiceTalk's public HTTP API surface for both client and server. It provides request/response models, headers, serialization helpers, execution/offload strategy, filters, and adapters across streaming, aggregated, and blocking paradigms. Concrete network implementations live in other modules (notably `servicetalk-http-netty`). Primary entry docs are `servicetalk-http-api/README.adoc` and `servicetalk-http-api/docs/modules/ROOT/pages/index.adoc`.

**Key Entry Points**
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpClient.java`  Core async aggregated client API. Can reserve connections and convert to streaming/blocking.
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/StreamingHttpClient.java`  Core async streaming client API; converts to aggregated and blocking variants.
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpServerBuilder.java`  Server configuration contract: protocols, TLS, socket options, filters, lifecycle observer, wire logging.
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpService.java`  Aggregated server-side handler contract.
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/StreamingHttpService.java`  Streaming server-side handler contract.
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpRequest.java`  Aggregated request model (payload as `Buffer`, trailers, serializers).
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/StreamingHttpRequest.java`  Streaming request model (payload as `Publisher<Buffer>`, message-body with trailers).
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpResponse.java`  Aggregated response model.
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/StreamingHttpResponse.java`  Streaming response model.
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpRequestFactory.java`  Convenience constructors for standard HTTP methods.
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/SingleAddressHttpClientBuilder.java`  Client builder for a single target; supports TLS, proxy, filters, wire logging.
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/MultiAddressHttpClientBuilder.java`  Client builder that resolves address per-request.
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpExecutionStrategy.java`  Offload strategy model for client/server callbacks.
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/StreamingHttpClientFilter.java`  Base class for client filters (interception around request/response).
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpApiConversions.java`  Adapters between streaming, aggregated, blocking, and reserved connection APIs.
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api/HttpSerializers.java`  Factory for common serializer/deserializer pairs (text, form-url-encoded, framed streaming).

**Call Graph and Dependencies**
- Client flow:
  - Builders (`SingleAddressHttpClientBuilder`, `MultiAddressHttpClientBuilder`, `PartitionedHttpClientBuilder`) configure and build a `StreamingHttpClient`.
  - `StreamingHttpClient.request(StreamingHttpRequest)` returns `Single<StreamingHttpResponse>`.
  - Aggregated and blocking clients are adapters over streaming (`asClient()`, `asBlockingClient()`).
  - Conversions and reserved-connection adapters are in `HttpApiConversions` and `StreamingHttpClientTo*` classes.
- Server flow:
  - `HttpServerBuilder` is configured and a `StreamingHttpService` is supplied.
  - Service filters (`StreamingHttpServiceFilterFactory`) wrap the service.
  - The transport layer (in `servicetalk-http-netty`) handles IO and drives the service.
- Execution/offload strategy:
  - Strategy influence is expressed via `HttpExecutionStrategyInfluencer` and merged by `HttpExecutionStrategy.merge(...)` or `StrategyInfluencerChainBuilder`.
- External libs and modules:
  - Module dependencies: `servicetalk-buffer-api`, `servicetalk-concurrent-api`, `servicetalk-client-api`, `servicetalk-transport-api`, `servicetalk-encoding-api`, `servicetalk-serialization-api`, `servicetalk-serializer-api`, `servicetalk-logging-api`.
  - Runtime logging via SLF4J (`org.slf4j:slf4j-api`).
  - Tests use Netty BOM, JUnit 5, Mockito, Hamcrest (see `servicetalk-http-api/build.gradle`).

**File and Directory Structure**
- `servicetalk-http-api/src/main/java/io/servicetalk/http/api`  All public HTTP API types and default implementations.
- `servicetalk-http-api/src/test/java/io/servicetalk/http/api`  Behavioral tests for headers, URI parsing, conversions, execution strategy, codecs.
- `servicetalk-http-api/src/testFixtures/java/io/servicetalk/http/api`  Reusable test fixtures for filters, contexts, and test clients.
- `servicetalk-http-api/docs`  Module documentation and diagrams.
- `servicetalk-http-api/build.gradle`  Dependencies and `testProps` source set for strict cookie parsing.

**Data Flow and State**
- Streaming request/response payloads are managed by `StreamingHttpPayloadHolder` in `DefaultStreamingHttpRequest` and `DefaultStreamingHttpResponse`. It owns:
  - `Publisher<?> messageBody`, headers, allocator, and `DefaultPayloadInfo` flags (empty, safe-to-aggregate, trailers, buffer-typed).
- Aggregation (`StreamingHttpRequest.toRequest()`, `StreamingHttpResponse.toResponse()`) uses:
  - `StreamingHttpPayloadHolder.aggregate()` and `HttpDataSourceTransformations.aggregatePayloadAndTrailers(...)` to produce a single `Buffer` plus trailers.
- Headers are represented by `HttpHeaders` and built by `HttpHeadersFactory`; constants live in `HttpHeaderNames` and `HttpHeaderValues`.
- Contextual metadata uses `ContextMap`, with shared keys in `HttpContextKeys` (execution strategy override, force-new-connection, http.route, stream id).
- Side effects: header mutation, context mutation, payload transformation, serialization/deserialization, close semantics; actual network IO is outside this module.

**Tests and Fixtures Skim**
- `servicetalk-http-api/src/test/java/io/servicetalk/http/api/RequestConversionTests.java`  Validates conversions between streaming/aggregated/blocking and payload info propagation.
- `servicetalk-http-api/src/test/java/io/servicetalk/http/api/StreamingHttpPayloadHolderTest.java`  Exercises payload transforms, trailers handling, backpressure semantics.
- `servicetalk-http-api/src/test/java/io/servicetalk/http/api/DefaultHttpHeadersTest.java`  Validates header behavior and edge cases.
- `servicetalk-http-api/src/testFixtures/java/io/servicetalk/http/api/AbstractHttpRequesterFilterTest.java`  Reusable harness for filter behavior tests.

**Setup Notes (Not Executed)**
- Typical local tasks:
  - `./gradlew :servicetalk-http-api:test`
  - `./gradlew :servicetalk-http-api:testProps` (enables strict RFC6265 cookie parsing via system property).
