# Overview
`DefaultAroundAdvisorChain` is the default implementation of the `BaseAdvisorChain` interface, part of Spring AI's advisor pattern for intercepting and modifying client requests/responses. It implements a Chain of Responsibility pattern for processing AI chat requests.
# Purpose
Implements the Chain of Responsibility pattern for `ChatClient` advisors, managing execution of `CallAdvisor` (sync) and `StreamAdvisor` (reactive) interceptors.
# Class Structure
Location:  `spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/DefaultAroundAdvisorChain.java`
## Key Fields
| Field                    | Type                           | Purpose                                                         |
| ------------------------ | ------------------------------ | --------------------------------------------------------------- |
| `callAdvisors`           | `Deque<CallAdvisor>`           | Mutable stack of synchronous advisors (popped during execution) |
| `streamAdvisors`         | `Deque<StreamAdvisors>`        | Mutable stack of streaming advisors                             |
| `originalCallAdvisors`   | `List<CallAdvisor`             | Immutable copy for `getCallAdvisors()`                          |
| `originalStreamAdvisors` | `List<StreamAdvisor>`          | Immutable copy for `getStreamAdvisors()`                        |
| `observationRegistry`    | `ObservationRegistry`          | Micrometer observability support                                |
| `observationConvention`  | `AdvisorObservationConvention` | Naming convention for observations                              |
## Core Methods
#### `nextCall(ChatClientRequest)` (lines 95-118)
Synchronous advisor chain execution:
1. Pops the next `CallAdvisor` from the deque
2. Creates an `AdvisorObservationContext` for observability
3. Wraps the advisor execution in Micrometer observation
4. Calls `advisor.adviseCall()` passing this as the chain (for recursive chaining)
#### `nextStream(ChatClientRequest)` (lines 121-151
1. Uses `Flux.deferContextual` for reactive context propagation
2. Pops the next `StreamAdvisor`
3. Sets up observation with proper parent context handling
4. Aggregates streaming responses via `ChatClientMessageAggregator`
#### `copy(CallAdvisor after)` (lines 154-169)
Creates a new chain containing only advisors that come after the specified advisor. This is useful for:
- Restarting chain execution from a specific point
- Creating sub-chains for parallel processing
#### Builder Pattern
The `Builder` class (lines 186-259) provides:
- `push(Advisor)/pushAll(List<Advisor>)` - adds advisors to both deques based on type
- `reOrder()` - sorts advisors by `Ordered` interface priority
-  Type filtering - separates `CallAdvisor` and `StreamAdvisor` implementations
# Key Components
- Deque-based advisor stacks (L66-68): Uses `ConcurrentLinkedDeque` to pop advisors one-by-one during execution
- Original lists (L62-64): Immutable copies for introspection via `getCallAdvisors()/getStreamAdvisors()`
- Observation support (L104-117): Wraps each advisor call with Micrometer observations for tracing
- Builder pattern (L186-258): `pushAll()`filters advisors by type and `reOrder()`sorts by Spring's `OrderComparator`
- `copy()` method (L153-169): Creates a new chain containing only advisors after the specified one
