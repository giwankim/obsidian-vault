## 1.1 What are web APIs?

An API defines the way in which computer systems interact.

One special type of API that is built to be exposed over a network and used remotely by lots of different people, often called "web APIs."

Most interesting aspect of this category is the fact that those building the API have so much control while those using web APIs have relatively little.

## 1.2 Why do APIs matter?
APIs are interfaces specifically for computers with important properties to make it easy for computers to use them.

But this doesn't stop at automation. APIs also open door to composition, which allows us to treat functionality like Lego building blocks.

How can we make sure the APIs we build fit together like Lego bricks? Let's start by looking at one strategy for this, called *resource orientation.*

## 1.3 What are resource-oriented APIs?
Ordering another computer around by calling a preconfigured subroutine or method is often referred to as making a "remote procedure call" (RPC). The critical aspect of APIs like this is the primary focus on the actions being performed.

API calls can either be "stateful" or "stateless." It turns out that RPC-style APIs are great for stateless functionality, but they tend to be a much poorer fit when we introduce stateful API methods.

Resource-oriented APIs,
- Rely on the idea of "resources," which are the key concepts we store and interact with, standardizing the "things" that the API manages.
- Limit actions to a small standard set, which apply to each of the resources.

For some scenarios RPC-oriented APIs will be a better fit (particularly in the case where the API method is stateless).
## 1.4 What makes an API "good"?

Purpose of building an API:
- We have some functionality that some users want.
- Those users want to use this functionality programmatically.

### 1.4.1 Operational
It must do the thing users actually want: **operational**. Additionally, most systems are likely to have many **nonoperational** requirements. It's these two aspects together that we say constitute the operational aspects of a system.

### 1.4.2 Expressive
Important that the interface to a system allows users to express the thing they want to do clearly and simply.

APIs that support certain functionality but don't make it easy for users to access that functionality would not be very good. APIs that are expressive provide the ability for users to clearly dictate exactly what they want and even how they want it done.

### 1.4.3 Simple
Rather than trying to excessively reduce the number of RPCs, APIs should aim to expose the functionality that users want in the most straightforward way possible, making the API as simple as possible, but no simpler.

Another common position on simplicity: "make the common case awesome and the advanced case possible."

### 1.4.4 Predictable
Unsurprising APIs rely on repeated patterns applied to both the API surface definition and the behavior.

## Summary
- Interfaces are contracts that define how two systems should interact with one another.
- APIs are special types of interfaces that define how two computer systems interact with one another, coming in many forms, such as downloadable libraries and web APIs.
- Web APIs are special because they expose functionality over a network, hiding the specific implementation or computational requirements needed for that functionality.
- Resource-oriented APIs are a way of designing APIs to reduce complexity by relying on a standard set of actions, called *methods,* across a limited set of things, called *resources.*
- What makes APIs "good" is a bit ambiguous, but generally good APIs are operational, expressive
