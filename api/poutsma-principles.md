---
title: "Poutsma Principles"
source: "https://poutsma-principles.com/blog/"
author:
published:
created: 2026-08-10
description:
tags:
  - "clippings"
---

> [!summary]
> A collection of posts on API design, anchored by the idea that good APIs have layers: a friendly annotation surface (`@Controller`, `@RequestMapping`), extension points like `HandlerMethodArgumentResolver` beneath it, and the raw Servlet API at the bottom — and higher layers must always let you peel back to the lower ones, or the API becomes *simplistic* rather than *simple*. Other entries cover retrieving method parameter names for convention-over-configuration frameworks (`-parameters`, `-java-parameters`, and Kotlin's `@Metadata`-based reflection, with a documented fallback chain), why an API should borrow its ecosystem's conventions instead of inventing its own, and how `RestClient`'s fluent surface is really a state machine backed by self-referencing generics like `RequestHeadersUriSpec<S extends RequestHeadersSpec<S>>`. Examples come throughout from Spring MVC, WebMvc.fn, and the Embabel JVM agent framework.

Good APIs are like [ogres](https://www.youtube.com/shorts/LEmFWRWLeGU): they have layers.

However, where an ogre hides its gentle core behind a rough exterior, an API should do the reverse: presenting a friendly surface while hiding its complexity within.

The outermost layer should be the most approachable, offering convenient shortcuts for common tasks. The innermost layer should be the most powerful, exposing all capabilities at the cost of verbosity or complexity.

![An Ogre](https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/DnD_Ogre.png/500px-DnD_Ogre.png)

---

### Layers in Spring MVC

An example of layering can be found in [Spring MVC](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller.html). Each layer is public and designed for user consumption, but they differ in abstraction, convenience, and scope.

1. **Annotation-based layer:** `@Controller`, `@RequestMapping`, and friends.
	The most user-friendly entry point: concise and expressive, though not suited for every edge case.
2. **Extension points:** such as `HandlerMethodArgumentResolver` and `HandlerMethodReturnValueHandler`. These allow customization and integration while keeping the annotation model intact.
3. **Servlet API:** the foundation. It defines the raw HTTP abstraction for Java web applications. If something is not possible here, it cannot be done in higher layers either.

Each layer offers a different “view” of the web programming model at its own abstraction level. You can write a Servlet that accomplishes the same as a `@Controller`, but it will require much more code.

### Layers in WebMvc.fn

The [WebMvc.fn](https://docs.spring.io/spring-framework/reference/web/webmvc-functional.html) functional API follows a similar pattern:

1. **Builders:** `RouterFunctions.route` and related helpers.
	These provide a fluent and readable way to define routes and handlers.
2. **Component model:** `HandlerFunction` and `RouterFunction`.
	A composable core that allows for extension and reuse.
3. **Servlet API:** again, the foundation underneath.

### Simple, Not Simplistic

The most important design rule is that higher layers must be able to reach the lower ones. Otherwise, the API becomes *simplistic* rather than *simple*: pleasant for trivial cases, but too limited for anything beyond them.

Spring provides many examples of this principle:

- In Spring MVC, a controller method can declare a `HttpServletRequest` or `HttpServletResponse` parameter, giving access to the Servlet API when needed.
- In WebMvc.fn, you can use a [`WriteFunction`](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/servlet/function/ServerResponse.HeadersBuilder.WriteFunction.html) to directly interact with the request and response.

This ability to “peel back the layers” ensures that convenience never comes at the cost of capability.

---

### The Broader Lesson

Every mature API should have layers. The top layers express the most common workflows in the most user-friendly terms. The lower layers expose the raw capabilities for edge cases. Higher layers should offer access to the lower layers, enabling more complex use cases.

Whether it is [Spring MVC](https://docs.spring.io/spring-framework/reference/web/webmvc.html), [Embabel](https://github.com/embabel/embabel-agent), or any other framework that invokes methods reflectively, parameter names often play an important role.
This is especially true in the context of [convention over configuration](https://en.wikipedia.org/wiki/Convention_over_configuration), which reduces the number of explicit decisions a user must make.

For example:

- In Spring MVC, a controller method parameter name can be used to resolve a request parameter (`@RequestParam`).
- In Embabel, an action method parameter name can indicate a blackboard value.

Retrieving parameter names in Java or Kotlin is less straightforward than it first appears. In this post, I will summarize the options.

---

### Java

Before Java 8, the only way to retrieve parameter names was to compile with debug information (`-g`). Even then, names were stored only in the local variable table, an attribute intended for debugging, not reflection.

For years, Spring Framework included a fallback that read parameter names from this table. This worked, but only when debug information was preserved.

Java 8 introduced a proper solution: the `-parameters` compiler flag, along with the `java.lang.reflect.Parameter` API. With the flag enabled, the compiler emits a dedicated `MethodParameters` attribute in the bytecode, which the Java reflection API can read reliably. Without the flag, reflection falls back to synthetic names like `arg0`, `arg1`, and so on.

---

### Kotlin

Kotlin complicates the picture further. The Kotlin compiler has a `-java-parameters` flag that behaves like `-parameters` for `javac`: it allows the Java reflection API to expose real parameter names instead of synthetic ones.

At the same time, Kotlin has its own reflection API, where parameter names are stored in the `@Metadata` annotation that the Kotlin compiler adds automatically. This means that with the Kotlin reflection (`KFunction.parameters`), you always see parameter names without extra flags. Two caveats apply:

1. Kotlin reflection lives in a separate dependency (`kotlin-reflect`). Unless you make it mandatory, you need to treat it as optional.
2. If you need to reflect on Java methods from Kotlin, those Java classes still need to be compiled with `-parameters` for names to be available.

---

### Fallback strategy

Depending on whether you are calling Kotlin from Java, or Java from Kotlin, you need a fallback strategy for retrieving parameter names.

For Embabel, which is written in Kotlin but needs to invoke both Kotlin functions and Java methods, I use the following approach:

1. If `kotlin-reflect` is on the classpath, use it (`KParameter::name`).
2. Otherwise, if the code was compiled with `-parameters` or `-java-parameters` (`Parameter::isNamePresent` is `true`), use Java reflection.
3. Otherwise, fail with an exception that instructs the user to enable one of the flags.

Spring follows a very similar approach, but from the opposite direction: it is a Java framework that can interact with Kotlin code.

---

### The Broader Lesson

Parameter names are a small detail, but they have a big impact on developer experience. Whether you are writing Java or Kotlin, frameworks often rely on them to make convention-based APIs feel natural.

Knowing when to enable `-parameters` or `-java-parameters`, and when to use Kotlin reflection, makes it easier to build frameworks that work seamlessly across both languages.

---

One of the promises of Java, when it was introduced, was *Write Once, Run Anywhere*. This promise applied as much to user interfaces as it did to other code. With [Java AWT](https://en.wikipedia.org/wiki/Abstract_Window_Toolkit), developers could create applications that offered a reasonable degree of fidelity to the underlying native windowing toolkit.

AWT was not alone. In the mid-to-late nineties, several frameworks emerged to offer cross-platform graphical user interfaces: [Qt](https://en.wikipedia.org/wiki/Qt_\(software\)), [wxWindows](https://en.wikipedia.org/wiki/WxWidgets), and later [Swing](https://en.wikipedia.org/wiki/Swing_\(Java\)).

The upside was that these frameworks allowed desktop GUI applications to be distributed beyond Windows, which dominated the nineties, to less common platforms such as the Mac.
The downside was that applications built this way were never able to perfectly simulate the native look and feel of the operating system. At worst, you got a Frankenstein of user interface design.

There are exceptions—JetBrains’ IntelliJ being the obvious one. But nowadays even IntelliJ no longer tries to mimic a native desktop application. Instead, it embraces a consistent, custom look and feel across platforms.

Why? Because web and mobile apps have changed expectations. Despite the continued existence of [design guidelines](https://developer.apple.com/design/human-interface-guidelines), most phone apps no longer rely on native widgets. Instead they introduce their own, consistent across iPhone and Android. The same holds even more true for the web. Seen in that light, it is not surprising that the modern way to create a cross-platform desktop app is simply to build a web app and bundle it with a browser engine, i.e. [Electron](https://en.wikipedia.org/wiki/Electron_\(software_framework\)).

I have [written previously](https://poutsma-principles.com/blog/blog/2025/06/11/making-api-feel-like-home/) about treating APIs as a kind of user interface, and I am going to make another comparison in this post.

---

The Java Virtual Machine was not designed to run polyglot code, but it grew into that role with [Jython](https://www.jython.org/) (1997), [JRuby](https://www.jruby.org/) (2001), [Groovy](https://groovy-lang.org/) (2003), [Scala](https://www.scala-lang.org/) (2004), [Clojure](https://clojure.org/) (2007), and [Kotlin](https://kotlinlang.org/) (2010).
Some of these were attempts to bridge the JVM with other languages, while others—Scala and Kotlin—were designed specifically for the JVM.

Of the two, Kotlin has embraced the Java ecosystem much more than Scala. In my experience, while you *can* use Java libraries in Scala, it is often frowned upon. A “pure Scala” library such as [Slick](https://scala-slick.org/) is generally preferred over a Java library like [Hibernate](https://hibernate.org/).

Kotlin, by contrast, was designed with Java interoperability in mind and feels much more at home on the platform. It is common to use a popular Java library such as [Spring](https://spring.io/), even when a Kotlin-native alternative exists ([Ktor](https://ktor.io/)).

Despite starting as a JVM language, Kotlin has since become cross-platform, targeting JavaScript and native code as well. The goal is to let developers use one language consistently across platforms—just as IntelliJ now delivers one consistent look and feel across operating systems.

Still, Kotlin and Java continue to evolve in parallel. The Kotlin team must bridge the gap between features—for example, mapping Kotlin data classes to Java records, or aligning Kotlin coroutines with Java Virtual Threads. It will be interesting to see how the relationship develops, knowing that each new feature Kotlin pioneers risks drifting away from a similar future feature on the JVM itself.

---

For the last couple of months, I have been working on [Embabel](https://embabel.com/), an agent framework on the JVM that mixes LLM-prompted interactions with code and domain models.

Although written in Kotlin, Embabel is designed to work just as well in Java environments. In future posts, I plan to share what it takes to build a framework that feels at home everywhere: usable, and idiomatic in both Java and Kotlin.

One of the most important properties of a good API is its level of consistency.

“Consistency” can mean many things in computer science, but in the context of API design, it typically refers to the [consistency of user interfaces](https://en.wikipedia.org/wiki/Consistency_\(user_interfaces\)). In other words: once part of the API has been learned, how easily can the rest be guessed? Can users successfully combine known elements in new ways, or apply familiar patterns to unfamiliar elements?

[![xkcd on Consistency](https://imgs.xkcd.com/comics/donald_knuth.png)](https://xkcd.com/163/ "XKCD comic on Donald Knuth and consistency")

Even within that definition, consistency applies to many aspects of an API:

- **Naming**: do types, methods, and parameters that serve similar roles also have similar names?
- **Parameter order**: are similar arguments presented in a consistent sequence?
- **Usage patterns**: for example, are objects thread-safe, immutable, or do they follow a common lifecycle?

All of these contribute to the overall learnability and usability of your API.

---

Thinking about your API as a kind of user interface opens up useful comparisons.

For example, it reminded me of a [blog post by Joel Spolsky](https://www.joelonsoftware.com/2000/04/22/consistency-and-other-hobgoblins/) —former CEO of Stack Overflow and, before that, an avid blogger—who wrote:

> In most UI decisions, before you design anything from scratch, you absolutely have to look at what other popular programs are doing and emulate that as closely as possible. If you’re creating a document editing program of some sort, it better look an awful lot like Microsoft Word \[…\]

That post was written in 2000, when desktop programs like Microsoft Word were the gold standard for rich user experiences. Today, that role has largely shifted to the Web. But the underlying idea still holds: *be consistent with your ecosystem*.

---

If you are designing a Java API, align with the conventions of the Java standard library. If your library builds on Spring, follow the way Spring does things. Borrowing from established APIs makes your own API feel familiar, predictable, and comfortable to use.

Even if you personally disagree with some design decisions—for instance, if you believe that [prefixing all interfaces with an `I` is preferable](https://wiki.eclipse.org/Naming_Conventions#Classes_and_Interfaces) —you are working in an ecosystem where millions of developers have internalized a different convention. That makes it *effectively* the right one.

---

## The Broader Lesson

When designing an interface meant for human consumption—whether a graphical UI or a programming API—there is value in following established patterns. Copying popular idioms and styles helps users feel at home. They do not have to learn everything from scratch. Instead, they can transfer what they already know.

Part 4 of Crafting Fluent APIs

So far in this series on *Crafting Fluent APIs*, I have focused on the *surface* of the API. In this post, I want to show how that surface is *designed*, using `RestClient` as an example.

This is Part 4 of a series where I explore various design considerations behind [fluent API](https://en.wikipedia.org/wiki/Fluent_interface) design. You can find an [overview of the series here](https://poutsma-principles.com/blog/2025/06/03/fluent-apis-overview/).

---

When reading through the [Javadoc for `RestClient`](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/client/RestClient.html), you may notice a large number of internal types that support the fluent API:

- [`RequestHeadersUriSpec`](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/client/RestClient.RequestHeadersUriSpec.html)
- [`RequestBodyUriSpec`](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/client/RestClient.RequestBodyUriSpec.html)
- [`RequestHeadersSpec`](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/client/RestClient.RequestHeadersSpec.html)
- [`RequestBodySpec`](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/client/RestClient.RequestBodySpec.html)
- [`ResponseSpec`](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/client/RestClient.ResponseSpec.html)

Some of these types have intimidating signatures, such as:

```java
interface RequestHeadersUriSpec<S extends RequestHeadersSpec<S>>
    extends UriSpec<S>, RequestHeadersSpec<S>
```

In the [previous post](https://poutsma-principles.com/blog/2025/05/28/responding-to-real-world-usage/), I argued that a fluent API’s *surface* is more important than the complexity of the internal types that support it. That trade-off becomes clear when browsing the Javadoc. Fluent APIs are designed to be *used* through Ctrl + Space, not *read* through documentation. (Though usage examples do help.)

---

Instead of Javadoc, it can be more helpful to visualize the fluent flow with a [state diagram](https://en.wikipedia.org/wiki/State_diagram). Here is a simplified version for `RestClient`:

![State Diagram for RestClient](https://poutsma-principles.com/assets/state-restclient.png)

This diagram highlights a few key points:

- Creating a request that cannot have a body takes you to `RequestHeadersUriSpec`; if it *can* have a body, you go to `RequestBodyUriSpec`.
- From either state, you can specify a URI, or [skip it](https://poutsma-principles.com/blog/2025/05/28/responding-to-real-world-usage/) if a base URL is already configured.
- You can repeatedly specify headers (and/or a body) until you call `retrieve` or `exchange`.
- `exchange` ends the chain immediately, while `retrieve` gives you several response-handling options first.

---

Let us now return to that earlier type signature:

```java
interface RequestHeadersUriSpec<S extends RequestHeadersSpec<S>>
    extends UriSpec<S>, RequestHeadersSpec<S>
```

This expresses that you can set both a URI and headers at this stage. The type parameter `S` is used as the return type for most methods in `UriSpec` and `RequestHeadersSpec`, like:

```java
S uri(URI uri);
S header(String headerName, String... headerValues);
```

This is a form of self-referencing generic. It ensures that methods inherited from different interfaces consistently return the correct type—in this case, a subtype of `RequestHeadersSpec`. A similar pattern is used in Java itself, in the declaration of [`java.lang.Enum`](https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/lang/Enum.html).

---

## The Broader Lesson

The proof of an API is not in its documentation; it is in how it *feels* when a developer navigates it with Ctrl + Space.

Creating that feeling often requires complex internal types and generic gymnastics, but that complexity should always serve one purpose: a clean, intuitive, and discoverable surface.

Behind every fluent API that feels obvious is a careful type design that models allowed states and transitions. Done well, the result is something that feels simple—even when it is not.
