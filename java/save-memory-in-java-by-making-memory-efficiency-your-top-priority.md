---
title: "Save Memory in Java by Making Memory Efficiency Your Top Priority"
source: "https://donraab.medium.com/save-memory-in-java-by-making-memory-efficiency-your-top-priority-32fe9443eb8d"
author:
  - "[[Donald Raab]]"
published: 2026-06-29
created: 2026-07-06
description: "More"
tags:
  - "clippings"
---

> [!summary]
> Donald Raab (creator of Eclipse Collections) argues memory-efficient Java programming is becoming a critical skill again. He details how Java Stream's single `ReferencePipeline` implementation makes every serial stream pay the startup memory cost of parallel processing — measurable overhead on small collections — with links to his JOL/JMH-validated benchmark posts. Recommends Eclipse Collections' primitive collections, "fat-free" stateless lambdas, and object pooling (Guava Interners, EC Pool) as practical memory-saving tools.

Leverage Java libraries and frameworks which focus on memory efficiency.

![](https://miro.medium.com/v2/resize:fit:2000/format:webp/0*OSUnCdGc6GVKssZX)

Photo by Markus Winkler on Unsplash

## Code in Java like it’s 2004

If you’re worried about the impending RAM Supply Apocalypse, and concerned that you won’t be able to afford to upgrade hardware to scale your memory hungry Java applications, then it’s time you pay attention to memory efficiency.

Wasting memory because it saves you time building something will sometimes come back to haunt you. Memory-efficient programming has become a lost art in Java because we have been spoiled with copious amounts of memory. Agentic AI may be ushering in a new age of memory-efficient programming. This may make this kind of programming a highly sought after skill again. If you want to enhance this skill set in Java, then keep reading.

## The Memory Efficiency of Java Stream

Java `Stream` is not memory-efficient at startup. `Stream` has a nice interface, let’s you write fluent declarative code, and can save you memory when applying multiple lazy operations to large datasets. `Stream` is wasteful, in ways it really doesn’t need to be, when used with serial processing of small collections. Serial processing of small collections is a common use case for Java `Stream`, and if you read some of the resources I have linked below you will find that this is the worst use case possible for Java `Stream`.

Java `Stream` suffers from a core design problem in its implementation, that can be summed up as follows.

> One Stream to rule them all.
> One Stream to find them.
> One Stream to bring them all
> and in the darkness bind them.
>
> (with apologies to Lord of the Rings)

The Java `Stream` interface is pretty good. The problems begin with ***the One*** abstract implementation of `Stream` named `ReferencePipeline`. `ReferencePipeline` is the one `Stream` that binds together both serial and parallel code paths. For a long time, I considered `ReferencePipeline` to be an unfortunate design decision because it made the reading and debugging of `Stream` code next to impossible for humans. This complication was later validated when JetBrains added a `Stream` [specific visual debugging tool to IntelliJ IDEA](https://www.jetbrains.com/help/idea/analyze-java-stream-operations.html).

I was not aware until this year how bad Java `Stream` is in terms of startup memory consumption because of the “there can be only one” design decision. The simple way to think about the problem is that we all pay the startup memory cost for parallel processing when using a serial `Stream`, which is the most common case.

## Agentic AI Finds Needles in the Haystack

I have been using Agentic AI the past few months at work to discover, identify, and correlate memory and performance issues with Java `Stream`. I have been comparing Java `Stream` alternatives to equivalent Eclipse Collections alternatives for memory consumption and performance. The discoveries have been surprising. I have blogged about many of these discoveries publicly.

I have been looking at Java `Stream` performance since before Java `Stream` was released in Java 8 in 2014. I [blogged about one parallel Stream performance problem](https://donraab.medium.com/traveling-the-road-from-idea-all-the-way-to-openjdk-fc7ae04371a5?sk=dee025810df6a898e0796dd2586287d7) I discovered and reported that resulted in a class called `RandomAccessSpliterator` being added to the JDK. If you use `List.of()` in your code bases, then you are using this `Spliterator` implementation without knowing it.

I have not previously looked at the memory footprint of Java `Stream` or Eclipse Collections `LazyIterable` / `ParallelIterable`. I never thought to look at startup memory cost of Java `Stream`, because I assumed it was always a short-lived object and would never be detectable on a Java heap and wouldn’t noticeably impact performance. Using Agentic AI I was able to discover a correlation between the startup memory cost of `Stream` and measurable performance differences for serial `Stream` on small collections, where small is defined as a collection of less than 100 elements.

## Show Your work

I’ve been blogging for several months after making a batch of discoveries using Agentic AI. I validated each individual discovery by writing code by hand using [Java Object Layout](https://github.com/openjdk/jol) (JOL) and [Java Microbenchmark Harness](https://github.com/openjdk/jmh) (JMH), and then blogged about them. I am going to share the list of blogs I wrote below so you have an index of content to research on your own if you are interested in learning more.

> 🫙 [Empty Should be Empty](https://donraab.medium.com/empty-should-be-empty-c09e21edc205?sk=c7809f108441527f48b2ef173bc7fbda)
>
> 🔄 [Performance of Lazy and Eager Iteration Patterns on Small Lists in Java](https://donraab.medium.com/performance-of-lazy-and-eager-iteration-patterns-on-small-lists-in-java-f4234bef50a5?sk=7bcfc9eabedfecf965b6566eb082ee04)
>
> 🚗 [Some Benefits of Enabling Compacy Object Headers in Java 25 for Streams](https://donraab.medium.com/some-benefits-of-enabling-compact-object-headers-in-java-25-for-streams-8df8b2037e05?sk=b949a7c0d75e4f6cdadebffc7227b3d2)
>
> 🏁 [Measuring the Startup Memory Cost for Lazy Iteration Patterns in Java](https://donraab.medium.com/measuring-the-startup-memory-cost-for-lazy-iteration-patterns-in-java-be24f4dd5b64?sk=0b55abdfa22143ef22d34048c7c2a48e)
>
> 🧮 [Counting and Collecting Collectors](https://donraab.medium.com/counting-and-collecting-collectors-d69b7c9aaca0?sk=ef73f56026d1afcf97e869f8ae990ea9)
>
> 🆓 [“Fat-Free” Lambdas in Java](https://donraab.medium.com/fat-free-lambdas-in-java-bf228da0613b?sk=a4280feb264939feeb7db9e9edca5663)
>
> 🐆 [Snow Leopards and Tribbles in Java Heaps](https://donraab.medium.com/snow-leopards-and-tribbles-in-java-heaps-a3f20fd5520c?sk=f82a9c0eed80bcc1330ce94781f48ae7)

**Note:** Where I identify memory inefficiencies in Java Stream, they are potential opportunities for future improvements that can help everyone using the API. They just need to be verified, assessed, and prioritized based on cost and benefit.

## Memory-Efficient By Design

Eclipse Collections started out its existence solving memory efficiency problems in 32-bit Java 4 in 2004. Memory-efficiency has been prioritized first in the Eclipse Collections design and implementation for the past 22 years. A Feature Rich API was prioritized second, and performance was prioritized third. Eclipse Collections often excels at all three, but sometimes there are necessary tradeoffs.

For the original story of how memory efficiency became the initial design priority of Eclipse Collections, the following is the blog to read.

## [Sweating the small stuff in Java](https://medium.com/better-programming/sweating-the-small-stuff-in-java-dbd695166d13?source=post_page-----32fe9443eb8d---------------------------------------)

### The story of small FixedSizeCollection types in Eclipse Collections

medium.com

## Java is Memory-Efficient, if You Know How to Use it

Java is a very memory-efficient programming language, if you know how to leverage the features it provides you. The JVM and language have added many great memory enabling features over the years, some which wind up eventually being enabled by default, benefitting everyone without them having to do anything. Compressed Oops and Compact Object Headers are great examples of memory-efficient features which show up initially as optional features and then eventually enabled by default. Compressed Oops have been enabled by default since Java 7. Compact Object Headers will be enabled by default starting in Java 27.

### Primitive Support FTW

Java’s support for eight primitives has been a memory and performance benefit and curse since the beginning. Valhalla has plans to eventually solve the original sin of Java having Object and primitive types not able to play nicely together in language features like Generics.

Eclipse Collections has full support for all eight Java primitives across many collection types. You can wait for Valhalla to solve the problem of being able to use `List<int>` in code, or you can use Eclipse Collections `IntList` (and seven other primitive lists) today. It’s your choice to either leverage a library that enables you to get full use of Java’s memory-efficient and performant primitives with collections, or to continue to go in a box.

## [Go Primitive in Java, or Go in a Box](https://donraab.medium.com/go-primitive-in-java-or-go-in-a-box-c26f5c6d7574?source=post_page-----32fe9443eb8d---------------------------------------&sk=becde45bd28f2284de5cd27202e8ee1e)

### Go Primitive in Java, or Go in a Box. We can have our eight Java primitives and travel light in collections too.

donraab.medium.com

### Stateless Lambdas FTW

The Java language has had support for hoisting stateless lambdas as statics since lambdas were first introduced in Java 8. Java `Stream`, other Java collections libraries, or other JVM language probably don’t give you the features you need to make more stateless lambdas static. You may be generating lambda garbage in your code without knowing it, if you are capturing state in a closure.

Eclipse Collections has had support for an additional level of “fat-free” lambdas since around 2007. This was seven years before Java 8 had lambda support added. We needed this “fat-free” lambda support in Goldman Sachs to make using functional APIs less painful in memory-sensitive high-performance coding paths.

## ["Fat-Free" Lambdas in Java](https://donraab.medium.com/fat-free-lambdas-in-java-bf228da0613b?source=post_page-----32fe9443eb8d---------------------------------------&sk=a4280feb264939feeb7db9e9edca5663)

### "Fat-Free" Lambdas in Java. From static anonymous inner classes to lambdas and method references.

donraab.medium.com

The Apache Groovy programming language has recently added an additional level of “fat-free” lambda support in its API targeted for release in [Groovy 6.0](https://groovy-lang.org/releasenotes/groovy-6.0.html). The blog above is the resource that make the Groovy development team aware of the need to have library features provided to enable more use of stateless lambdas.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*L7-y14_nw6Ty0TEXE01ELA.png)

Groovy 6.0 release note on “fat-free” lambda API support

### Object Pooling

If you’re deploying Java applications that run for a long time between restarts and cache a lot of state, then you need to know about object pooling. In my experience, the largest memory savings for large memory JVM heaps can sometimes be achieved through object pooling. Many developers I have met know about the built in `String` pooling in Java, and have heard of or used the `String.intern()` method. Many developers I have met have also not thought to pool their own immutable domain objects. If you wind up creating a lot of duplicate objects in memory over time, then using object pooling can be helpful.

Both Google Guava and Eclipse Collections have options for pooling. In Guava, look for the [Interners](https://guava.dev/releases/snapshot-jre/api/docs/com/google/common/collect/Interners.html) class which supports both strong and weak pools. In Eclipse Collections, which only supports a strong pool by default, look in this [blog for information about the Pool interface](https://medium.com/javarevisited/how-to-get-an-item-from-a-set-in-java-c6c82de729ab?sk=163b56070aabbc7b0b08ad0c2f77e854).

## Final Thoughts

I have helped folks I have worked with for years, make their Java applications and libraries more memory-efficient. I have provided the entire Java community, via the open source Eclipse Collections library, access to many of the tools and tricks I have learned and used over the years to fine tune memory savings in banks like Goldman Sachs.

The only thing I am unable to provide you with is the incentive to make your code more memory-efficient. Agentic AI may soon do this for you. If you have read this far, then maybe you have some new tools you were unaware of previously that can help you in the new memory-constrained environment we all find ourselves in again.

Thanks for reading! If you want to know more about Eclipse Collections, I wrote a book about it that you can find linked below.

*I am the creator of and committer for the* [*Eclipse Collections*](https://github.com/eclipse/eclipse-collections) *OSS project, which is managed at the* [*Eclipse Foundation*](https://projects.eclipse.org/projects/technology.collections)*. Eclipse Collections is open for* [*contributions*](https://github.com/eclipse/eclipse-collections/blob/master/CONTRIBUTING.md)*. I am the author of the book,* [*Eclipse Collections Categorically: Level up your programming game*](https://a.co/d/eONZCR7)*.*
