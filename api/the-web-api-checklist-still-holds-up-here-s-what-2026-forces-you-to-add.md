---
title: "The Web API Checklist Still Holds Up. Here's What 2026 Forces You to Add."
source: "https://lgsreal.substack.com/p/the-web-api-checklist-still-holds"
author:
  - "[[Luiz Real]]"
published: 2026-05-25
created: 2026-07-08
description: "Fenniak's 2013 \"Web API Checklist\" became required reading for a generation of API teams. A walkthrough of what still works and what 2026 forces you to add."
tags:
  - "clippings"
---

> [!summary]
> Revisits Mathieu Fenniak's 2013 "Web API Checklist" through a 2026 lens and finds the HTTP-semantics bedrock (status codes, caching, pagination, versioning, statelessness) still sound. Layers on modern additions — idempotency keys, HTTP/2-3, RFC 9457 error bodies, cursor pagination, OAuth2/OIDC and careful JWT handling, the OWASP API Security Top 10 (2023), OpenAPI-driven contracts, and observability — while pushing back on header-based versioning and full HATEOAS. Also extends beyond REST to GraphQL, gRPC, webhooks, and CI/CD contract/security/lint testing.

When Mathieu Fenniak published “ [The Web API Checklist – 43 Things To Think About When Designing, Testing, and Releasing a Web API](https://mathieu.fenniak.net/the-api-checklist/) “ in 2013, it became the document a lot of us quietly copied into wikis and onboarding decks. Shortly afterward, he followed it with “ [Stop Designing Fragile Web APIs](https://mathieu.fenniak.net/stop-designing-fragile-web-apis/),” a companion piece that pushed harder on stability, versioning, and treating APIs as explicit contracts rather than vague intent surfaces. Together, those two posts captured both the practical mechanics of HTTP-centric design and a strong stance on long-term compatibility: design clear, semantic endpoints up front, and evolve them carefully instead of silently changing behavior.

More than a decade later, the surprising thing about that checklist is how little of it is wrong. The bedrock items (HTTP semantics, status codes, caching, pagination, error handling, versioning) are still the bedrock items. What changed isn’t the foundation. It’s everything built on top of it: JSON crowded out every other format, OpenAPI and generated SDKs became standard, OAuth 2.0 and OpenID Connect replaced ad-hoc auth, GraphQL and gRPC became mainstream, and OWASP’s API Security Top 10 now reflects a much harsher attack landscape.

This article walks through Fenniak’s checklist with a 2026 lens. Some sections need barely a footnote. Others need significant additions. And a few common modern practices are worth pushing back on. Not everything new is an improvement.

## HTTP: Still the Foundation, With New Expectations

Items #1–#19 of the original checklist are entirely about HTTP/1.1: idempotent methods, proper use of 201/202, 4xx vs 5xx, 410 Gone, caching, compression, keep-alive, chunked encoding, and details like `Expect: 100-continue` and absolute redirects. All of that remains valid because HTTP semantics did not change with HTTP/2 or HTTP/3 (those newer versions add framing, multiplexing, and better performance, not new application-level behavior). Mostly.

**What stays the same:**

- Treat method idempotency seriously: design `PUT` and `DELETE` to be safely retryable and avoid side effects in `GET`, especially in systems that use automatic retries (clients, proxies, service meshes).
- Use status codes precisely: 201 for resource creation with a `Location` header, 202 for accepted-but-asynchronous work, 4xx for client faults, 5xx for server faults, and 410 Gone when a previously existing resource is intentionally removed.

**What to update:**

- **Adopt the Idempotency-Key convention for unsafe POSTs.** For “create” actions that cannot be retried safely (payments, orders, anything that costs money or has side effects downstream), expose an `Idempotency-Key` header and guarantee that repeated requests with the same key do not create duplicates. Note this is a *convention*, popularized by Stripe and now widely copied, the IETF draft is still a draft. That’s fine. Pick the semantics, document them clearly, and don’t wait for an RFC to ship.
- **Embrace HTTP/2 and HTTP/3 at the transport layer.** Application semantics are unchanged, so keep designing for HTTP/1.1 correctness. But there’s one thing worth knowing: HTTP/3 over QUIC removes TCP head-of-line blocking and supports connection migration, which materially changes the calculus for long-lived connections, server-sent events, and mobile clients on flaky networks. If you’re designing streaming or long-polling endpoints in 2026, it’s worth thinking about HTTP/3 explicitly rather than assuming HTTP/1.1 mental models still apply.
- **Standardize error bodies on RFC 9457.** Combine status codes with a consistent JSON error envelope based on RFC 9457 (”Problem Details for HTTP APIs”), which obsoleted RFC 7807 in July 2023. The fields most teams already use (`type`, `title`, `detail`, `instance`, plus your own `trace_id`) are unchanged; 9457’s improvements are mostly clarifications and stricter rules for extension members. If you have an existing 7807-based envelope, you’re already compliant with 9457 in practice, just update the reference.

Fenniak’s guidance on caching headers (`Cache-Control`, `ETag`, `Last-Modified`) is still best practice. The 2026 addition is to actually *use* it. Most teams I see have correct caching headers and zero CDN configuration to take advantage of them. Cache-friendly URLs and an edge cache in front of safe GET endpoints is one of the highest-leverage performance wins available, and it’s almost free if you’ve already done the header work.

## API Design: Resource Modeling, Versioning, Pagination

The original “API Design” section (#20–#29) covers statelessness, content negotiation, URI templates, “design for intent,” versioning, authorization, bulk operations, pagination, Unicode, and error logging. Most of those ideas have been reinforced by every major REST style guide since.

### Statelessness and Scalability

Fenniak insists that application servers should be stateless to scale easily. In 2026, that advice is even more important in containerized, serverless, and auto-scaled environments where any instance can disappear at any moment. Session and user context belongs in tokens (typically JWTs) or external stores, never in in-process memory on a single node. If you’re still keeping session state in a server’s local cache because “it’s faster,” you’re optimizing for a deployment model that doesn’t exist anymore.

### Resource-Oriented URIs and Semantics

Modern REST guidance is consistent on:

- Noun-based, plural resource paths: `/customers`, `/customers/{id}`, `/customers/{id}/orders`.
- No verbs in URLs: use HTTP methods to represent actions rather than `/createCustomer` or `/deleteInvoice`.
- No file extensions in URLs (`.json`, `.xml`); negotiate representation via Accept and `Content-Type` headers.

Fenniak’s “design for intent” piece effectively foreshadows the domain-model-driven endpoint design that more recent checklists advocate: endpoints should map to business concepts and workflows, not leak internal object models or database tables. The fact that this is still worth saying, thirteen years later, tells you how often teams still get it wrong. If your API has an endpoint named `/users/{id}/userAccountSettings/update`, you’ve smuggled at least three implementation details into your public contract.

### Pagination, Filtering, Sorting

Pagination is one of those things every API needs and most APIs do badly. Fenniak correctly emphasized consistent, monotonic pagination to avoid duplicates when data changes mid-page. The modern guidance extends this:

- Use **cursor-based pagination** (`limit` + opaque cursor) for any collection that changes frequently. Page-number pagination is fine for static-ish data, but for anything where rows are being inserted between requests, it produces duplicates and gaps that drive client teams insane.
- Return pagination metadata and navigation links (`next`, `prev`, `self`) in the response body or `Link` header. Don’t make clients reconstruct URLs.
- Define hard upper limits on filtering and sorting query parameters, and reject requests that exceed them. An unbounded `?sort=` parameter is an availability incident waiting to happen.

### Versioning: A Place to Push Back

In 2013, using a `/v1/` prefix was the pragmatic answer to versioning, and Fenniak said so explicitly. That pattern is still common for public APIs because it’s visible, easy to document, and trivial to route at the gateway.

What’s changed is the conversation around evolution without breaking changes:

- Many internal and SaaS APIs prefer **additive evolution** (adding fields and endpoints, never removing or changing) combined with explicit deprecation policies and grace periods.
- Some teams use **header-based versioning** (`Accept: application/vnd.example+json;version=2`) to keep URLs stable.

Here’s where I’d push back on modern fashion: header-based versioning sounds elegant and is, in my experience, almost always the wrong choice for public APIs. It breaks the most basic debugging workflow: pasting a URL into a browser or curl and getting back what the customer is seeing. It makes CDN caching harder. It hides version information in places ops engineers don’t think to look. Stick with `/v1/`, `/v2/` for anything externally consumed. The slight loss of URL purity is worth the massive gain in operational legibility.

The harder question, and the one worth more thought than the URL-vs-header debate, is *when a breaking change is justified at all*. The honest answer is: rarely. Most “we need v2” conversations are really “we want to clean up the design,” which is not the same thing as “the old design is causing real harm.” If you can solve it additively, solve it additively. New major versions are expensive for every customer who has to migrate, and that cost rarely shows up in the team that owns the API.

## Content and Hypermedia: JSON Everywhere, Pragmatic Links

The original “Content” section (#30–#32) focused on content types, HATEOAS, and date/time formats. At the time, Atom, Collection+JSON, HAL, and XHTML were still in the conversation. They aren’t anymore. JSON won.

### JSON Conventions and Envelopes

A modern checklist:

- Default to `application/json` or a vendor-specific JSON media type (like `application/vnd.api+json` if you’re using JSON:API).
- Pick a single field-naming convention (camelCase or snake\_case) and enforce it across every endpoint. The convention itself matters less than the consistency. Mixed conventions across endpoints are a tell that your API was built by accretion rather than design.
- Use consistent envelopes for collections (`items`, `total`, `next`) and errors (RFC 9457).

Fenniak’s recommendation to use RFC 3339 / ISO 8601 date-times with explicit time zones still stands. The 2026 update: be explicit that timestamps should be UTC. Local times in API responses are a footgun that will eventually cause an incident, especially around DST transitions. If a client needs local time, they can format it locally from the UTC value.

### Hypermedia and the Link Header

HATEOAS remains part of the original REST constraints, and Fenniak mentions using the Link header (RFC 5988, since obsoleted by RFC 8288) to expose navigation relationships. In practice, most production teams adopt partial hypermedia rather than full HATEOAS:

- Include `self`, `next`, `prev`, and related resource links in JSON responses where they help clients navigate.
- Use the `Link` header for global relationships like documentation, canonical URLs, and pagination.

Full HATEOAS (the kind where clients discover the entire API by following links) has effectively lost. Almost no production API does it, almost no client wants to consume it that way, and the cost-benefit never made sense outside academic discussions. Partial hypermedia, used pragmatically, is fine. Going further is rarely worth it.

## Security: From “Use SSL” to OWASP API Top 10

Security is the section that has changed the most since 2013. Fenniak’s original “Security” section (#33–#36) emphasized SSL, CSRF risks from reused browser sessions, throttling, and subtle DoS attacks. All still relevant. But the baseline has shifted dramatically, and this is the section where a 2013 checklist applied literally would leave you dangerously exposed.

### HTTPS-Only and Zero-Trust

“Consider whether you should offer HTTP and HTTPS, or just HTTPS” in 2013 becomes “HTTPS-only with HSTS and modern TLS” in 2026. For internal service-to-service traffic, mutual TLS enforced by a service mesh or gateway is increasingly the norm. The updated checklist:

- Require HTTPS for all public APIs. Forbid plain HTTP in production environments. If you need to support legacy clients, do it at a separate edge with logging, not by relaxing the policy across the board.
- Promote zero-trust principles: authenticate and authorize every request, including those on internal networks. The “trusted internal network” was always a fiction. By 2026 it’s an embarrassing one.

### Modern Authentication and Authorization

Fenniak framed HTTP Basic Authentication with API keys as a simple and effective mechanism. It’s still used in some B2B integrations, but for user-centric and public APIs the dominant patterns are OAuth 2.0 and OpenID Connect. An updated checklist:

- Use OAuth 2.0 for delegated access scenarios; OpenID Connect for login and identity on top of OAuth.
- Use short-lived JWTs or opaque tokens as Bearer tokens. Enforce scopes, audiences, and expiration rigorously. JWTs in particular get implemented sloppily: verifying the signature is necessary but not sufficient, and a surprising number of production systems forget to check `aud`, `iss`, or expiration.
- Reserve long-lived API keys for strictly server-to-server use, protected by IP allowlists or mutual TLS. Never embed secrets in mobile apps or frontends. The number of API keys discoverable by decompiling popular Android apps is a permanent embarrassment to our industry.

### OWASP API Security Top 10 (2023) and Hardening

OWASP published the API Security Top 10 in 2019 and updated it in 2023. The 2023 list is the current standard, and a few of the changes are worth knowing:

- **API1:2023 - Broken Object Level Authorization (BOLA)** remains the #1 risk and represents an enormous share of real-world API attacks. If you build only one automated security check, build one for BOLA.
- **API3:2023 - Broken Object Property Level Authorization (BOPLA)** is a merger of the 2019 categories “Excessive Data Exposure” and “Mass Assignment.” Same underlying issue: the server returning or accepting fields it shouldn’t, based on the requesting user’s permissions.
- **API6:2023 - Unrestricted Access to Sensitive Business Flows** is new and overdue. This is the “attacker abuses your perfectly-functioning API to scrape inventory / scalp tickets / brute-force coupon codes” category.
- **API7:2023 - Server-Side Request Forgery (SSRF)** is new to the API list and increasingly common as APIs accept user-provided URLs for webhooks, image processing, and integrations.
- **API10:2023 - Unsafe Consumption of APIs** flips the usual perspective: it’s about the risk your *own* API takes when calling third-party APIs whose responses you trust too much.

The practical hardening checklist that follows from this:

- Systematic input validation and output filtering, ideally via schema-driven validation (JSON Schema, OpenAPI schemas) generated from the same spec the docs are built from.
- Principle of least privilege for tokens, rate limits, and data fields. Never expose more fields than clients actually need.
- WAFs and API gateways configured with policies for common patterns (SQL injection, XSS, path traversal, SSRF target lists).
- Treat *every* endpoint that accepts a URL as a potential SSRF vector. Allowlist destinations, don’t blocklist them.

### Rate Limiting, Quotas, and Abuse Protection

Fenniak called out throttling and subtle DoS attacks. Modern practice:

- Per-consumer rate limits with clear `429 Too Many Requests` responses and `Retry-After` hints.
- Adaptive or dynamic rate limiting based on usage patterns, user tier, or anomaly detection.
- Coordinated protection across gateway-level rate limits, application-level guards, and WAF rules.

One thing worth being honest about: most rate limiting in the wild is configured once and never tuned. The default `100 requests/minute` you set in 2022 is probably wrong now in both directions: too generous for some endpoints, too tight for others. Rate limits are a living configuration, not a set-and-forget header.

## Documentation, Developer Experience, and Governance

Items #40–#43 cover documentation, “design with a customer,” feedback channels, and automated testing. Those themes matured into the API-as-a-product discipline.

### OpenAPI, Interactive Docs, and SDKs

The original article mentions Swagger and Mashery I/O Docs when those tools were new. Today, OpenAPI is the default machine-readable description format for REST APIs, and many teams generate documentation, mocks, and SDKs from the spec.

A 2026 checklist:

- Maintain an up-to-date OpenAPI document and treat it as a contract between teams, not as documentation that happens to be machine-readable.
- Publish interactive documentation (Swagger UI, Redoc, Stoplight, Scalar) directly from the spec, with examples and “try it” consoles.
- Generate client SDKs from the spec, but wrap generated code with idiomatic convenience methods. Raw generated SDKs ship the awkward parts of the spec straight to your customers, and “we use code generation” is not an excuse for handing developers an unusable client library.

A piece of contrarian advice: spec-first vs. code-first is a real debate, and the spec-first crowd is louder than they should be. Code-first OpenAPI generation works fine for most teams, as long as the generated spec gets validated in CI and reviewed like documentation. The dogma matters less than the discipline.

### Developer Portals and Feedback Channels

Fenniak’s point about “Design with a customer!” anticipates today’s developer-experience focus:

- A developer portal that centralizes docs, API key management, usage analytics, changelogs, and support.
- Clear onboarding flows with tutorials, quickstarts, and test credentials.
- Versioned documentation, release notes, and deprecation notices visible in the portal.

The portal itself isn’t the win, the win is having a single place where a developer can go from “I want to integrate” to “I’ve made my first successful call” in under fifteen minutes. If your onboarding takes longer than that, the docs aren’t the problem, the design is.

### Observability and Operational Readiness

Fenniak already recommended distinguishing client-side and server-side errors in logging. Modern production APIs treat observability as a first-class concern:

- Structured, centralized logs with correlation IDs that follow a request through gateways and microservices.
- Metrics on latency, error rates, throughput, and saturation per endpoint and per consumer, feeding into SLOs and alerts.
- Distributed tracing (OpenTelemetry is the de facto standard now; Zipkin and Jaeger are still in use as backends).

An updated checklist would treat observability and SLOs as design requirements, not operational add-ons. If you can’t tell me your p99 latency per endpoint by tier, you’re flying blind.

## Beyond REST: GraphQL, gRPC, and Event-Driven APIs

Fenniak’s checklist assumes HTTP/REST as the model. Since then, GraphQL and gRPC have become mainstream, and many systems combine all three.

### GraphQL for Flexible Frontends

GraphQL offers a single endpoint where clients specify exactly the fields they need, which reduces over- and under-fetching and helps complex or rapidly evolving client UIs.

An updated article wouldn’t replace REST with GraphQL, it would add guidance:

- Use REST for stable, coarse-grained service contracts (especially across organizational boundaries). Add GraphQL as a Backend-for-Frontend layer when clients need flexibility.
- Implement query cost and depth limiting, timeouts, and caching strategies. An unconstrained GraphQL endpoint is one carefully-crafted query away from a database outage.
- Apply the same security and governance rigor to GraphQL schemas and resolvers as to REST endpoints. BOLA is just as much a GraphQL problem as a REST problem. Possibly more, since resolvers make it easy to skip authorization checks in one place and have it cascade.

### gRPC and Internal APIs

gRPC, built on HTTP/2 (and increasingly HTTP/3) with Protocol Buffers, has become a popular choice for low-latency, strongly-typed internal APIs between microservices.

A 2026 checklist:

- Recognize that REST is often the external/public protocol, while gRPC is used internally for service-to-service communication, especially in polyglot backends.
- Emphasize that governance, observability, and security controls must apply consistently across REST and gRPC. It’s easy to be rigorous about the public REST API and sloppy about the internal gRPC mesh. Attackers who get a foothold love internal sloppiness.

### Async, Long-Running Operations, and Events

Fenniak already recommended `202 Accepted` for queued work. Since then, event-driven and asynchronous patterns have expanded:

- Long-running operations modeled as operation resources `(/operations/{id}`) that clients poll, or webhooks/callbacks for completion events.
- Webhook endpoints as first-class APIs: with clear schemas, signed payloads (HMAC or asymmetric signatures), documented retry semantics, and security guidance for consumers.

Webhooks deserve a stronger callout than they usually get. They’re the part of your API where *you* are the client and your *user* is the server. That inversion changes everything about how you handle retries, authentication, and failure modes, and most webhook implementations I see in the wild are sloppy because the team treats them as a side feature.

## Testing, CI/CD, and Quality Gates

Fenniak’s final item is “Automated Testing.” In 2026, this extends to:

- Contract tests between services (Pact and similar) to ensure interface compatibility as services evolve.
- Security tests in CI/CD: static analysis, dynamic scanning, fuzzing targeted at API endpoints.
- Performance and load testing of critical endpoints before major releases.
- API linting and style checks (Spectral is the common tool) on OpenAPI files, enforcing naming conventions, pagination patterns, and error shapes consistently across teams.

The point of API linting isn’t to catch big mistakes, it’s to make consistency cheap. If every PR that touches the OpenAPI spec gets automatically linted, you stop having the “should we use camelCase?” argument every six months in a different team.

## What a 2026 “Web API Checklist” Would Emphasize

If Fenniak rewrote his checklist today, much of the original content (HTTP semantics, status codes, caching, pagination, statelessness, documentation) would survive nearly unchanged. The biggest shifts would be in emphasis and in new sections:

- **Security first:** HTTPS-only, OAuth 2.0/OIDC, JWT done correctly, OWASP API Security Top 10 (2023), rate limiting, WAFs, secret management, zero-trust internal networks.
- **API as product:** OpenAPI-driven contracts, interactive docs, SDK generation, developer portals, lifecycle governance, deprecation policies, consistent style guides.
- **Multi-protocol reality:** when to use REST, when to add GraphQL, where gRPC fits, how to keep cross-protocol governance coherent.
- **Observability and reliability:** structured logs, metrics, traces, SLOs as design-time concerns.
- **Automation and CI/CD:** contract, security, and performance testing baked into pipelines; linting of API contracts before merges.

A decade after Fenniak’s checklist first circulated, the hard part is no longer discovering best practices. It’s applying them consistently as your APIs, teams, and systems evolve. Used together, the original checklist, “Stop Designing Fragile Web APIs,” and the updates here are less a snapshot of “how to design a REST API” and more a living set of constraints — a way to say no to insecure shortcuts, accidental breaking changes, and ad-hoc endpoints that feel convenient today and painful tomorrow.

If you keep using that lens as your APIs grow, treating them as products, contracts, and long-lived infrastructure, you’ll stay aligned with the spirit of Fenniak’s work, even as the ecosystem around HTTP keeps shifting underneath it.
