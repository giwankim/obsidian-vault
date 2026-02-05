# servicetalk-http-api Briefing

## Overview

This module defines ServiceTalk's core HTTP client and server API abstractions. It provides interfaces for HTTP/1.x and HTTP/2 with three programming models: **asynchronous streaming** (reactive), **blocking**, and **non-streaming** (aggregated). ~32K lines across 207 files in `io.servicetalk.http.api`.

---

## Key Entry Points

| Interface | Path | Purpose |
|-----------|------|---------|
| `StreamingHttpClient` | `src/.../StreamingHttpClient.java` | Async client with `Publisher<Buffer>` payloads |
| `HttpClient` | `src/.../HttpClient.java` | Non-streaming client (aggregated Buffer) |
| `BlockingHttpClient` | `src/.../BlockingHttpClient.java` | Synchronous blocking API |
| `StreamingHttpService` | `src/.../StreamingHttpService.java` | Server-side request handler (async) |
| `HttpServerBuilder` | `src/.../HttpServerBuilder.java` | Server configuration |
| `SingleAddressHttpClientBuilder` | `src/.../SingleAddressHttpClientBuilder.java` | Client builder for single target |

---

## Request/Response Hierarchy

```
HttpMetaData
├── HttpRequestMetaData → HttpRequest, StreamingHttpRequest
└── HttpResponseMetaData → HttpResponse, StreamingHttpResponse
```

- **Streaming**: payload via `Publisher<Buffer>`, supports transformation
- **Non-streaming**: payload as single `Buffer`
- **Blocking streaming**: `BlockingIterable<Buffer>`

All models are interconvertible via `.asStreamingClient()`, `.toStreamingRequest()`, etc.

---

## Dependencies (from build.gradle)

- `servicetalk-buffer-api` – Buffer abstraction
- `servicetalk-concurrent-api` – `Single`, `Publisher` reactive types
- `servicetalk-client-api` – Base client contracts
- `servicetalk-transport-api` – Transport layer
- `servicetalk-encoding-api` – Content encoding

---

## Directory Structure

```
src/main/java/io/servicetalk/http/api/
├── Http{Request,Response}.java        # Core request/response
├── Streaming*.java                     # Streaming variants
├── Blocking*.java                      # Blocking variants
├── Http{Client,Server}Builder.java    # Builders
├── Http{Connection,ServiceContext}.java # Connection/context
├── StreamingHttp{Client,Service}Filter.java # Filter chain
├── HttpExecutionStrategy.java         # Thread offloading config
├── HttpHeaders.java                    # Header management
├── HttpSerializer2.java               # Serialization contracts
└── [~200 more files]
```

---

## Core Patterns

1. **Factory Pattern** – `HttpRequestFactory`, `HttpResponseFactory` for creating objects
2. **Builder Pattern** – Fluent builders for clients/servers with type-safe generics
3. **Filter/Decorator** – `StreamingHttpClientFilter`, `StreamingHttpServiceFilter` for middleware
4. **Strategy** – `HttpExecutionStrategy` controls thread offloading (metadata, data, send)
5. **Adapter** – Conversions between streaming/blocking/aggregated via adapter classes

---

## Data Flow

```
Client:
  HttpRequest → StreamingHttpRequest → [Filters] → Transport → Network  Network → Transport → [Filters] → StreamingHttpResponse → HttpResponse
Server:
  Network → StreamingHttpRequest → [Filters] → StreamingHttpService.handle()  StreamingHttpResponse → [Filters] → Network
```

Key context objects:
- `HttpExecutionContext` – executor, ioExecutor, bufferAllocator
- `HttpServiceContext` – server-side context (connection info, response factory)
- `ContextMap` – per-request key-value storage

---

## Notable Files

- `HttpContextKeys.java:30-53` – Request context keys (execution strategy, stream ID)
- `HttpExecutionStrategies.java` – Factory for execution strategies (`offloadAll()`, `offloadNone()`)
- `HttpHeaderNames.java` / `HttpHeaderValues.java` – Standard header constants
- `HttpResponseStatus.java` – Status code constants (200, 404, etc.)

---

## Tests/Examples

Tests are in `src/test/java/` – useful for seeing intended usage patterns. The module itself is an API-only layer; actual HTTP wire protocol implementation lives in `servicetalk-http-netty`.
