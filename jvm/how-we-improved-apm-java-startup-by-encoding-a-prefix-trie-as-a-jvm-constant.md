---
title: "How we improved APM Java startup by encoding a prefix trie as a JVM constant"
source: "https://www.datadoghq.com/blog/engineering/improving-apm-java-startup-with-a-prefix-trie/"
author:
  - "[[Stuart McCulloch]]"
published: 2026-08-11
created: 2026-08-17
description: "Learn how the Datadog APM team improved Java startup performance by encoding a prefix trie as a JVM string constant."
tags:
  - "clippings"
---

> [!summary]
> Datadog's APM Java team needs fast class-name prefix matching during premain, a JVM phase where the JIT is cold (and on Java 8, absent entirely) and building a conventional trie would cost resource lookups, I/O, and parsing.
> Their solution, ClassNameTrie, encodes the entire trie into a single JVM string constant, packing control information and content into each 2-byte char, so the whole structure loads with one ldc bytecode instruction and no I/O.
> Cold-start benchmarks show it is nearly 5x faster than the old code-based matcher on Java 8 and beats a classic radix trie thanks to compact representation and cache locality, contributing to a 24% total cut in class-matching overhead.

![Stuart McCulloch](https://web-assets.dd-static.net/42588/1785784309-stuart-mcculloch.jpeg?format=auto&fit=bounds&quality=75&disable=upscale&width=767&dpr=1)

Stuart McCulloch

Stuart McCulloch

Staff Engineer

Startup time affects everyone—users waiting for responses, developers testing features, and teams watching cloud costs. [Datadog Application Performance Monitoring (APM)](https://docs.datadoghq.com/tracing/) helps engineers understand performance throughout an application, including during startup. For Java, using APM involves attaching an agent to the JVM that automatically transforms classes to add observability, an approach known as instrumentation. Instrument too few places and you miss key details. Instrument too many and startup suffers. APM has to balance that trade-off, and the first step is deciding which classes to instrument—a problem called class matching.

Over the past 4 years, the Datadog APM team has reduced class-matching overhead by 30%. Optimizing class matching during startup is particularly challenging because the just-in-time (JIT) compiler has not yet optimized the matcher code, and profilers have not captured enough samples to identify hot spots. Instead, we relied on our knowledge of JVM internals to identify promising ideas and ran multiple experiments to validate our intuition.

One speculative optimization that paid off was encoding multiple class-name prefix matches ahead of time as a single JVM constant, loaded with a single bytecode instruction. In this post, we’ll explain how we developed that encoding and used it to replace a hand-rolled matcher of “uninteresting” classes.

## Observing Java applications by instrumentation

Java provides several APIs for observing application behavior. [Java Management Extensions](https://docs.oracle.com/en/java/javase/25/jmx/introduction-jmx-technology.html) (JMX) expose metrics such as memory levels and CPU load. But often you need a different perspective, such as measuring the time spent in a particular library or method call. The [JVM Tool Interface](https://docs.oracle.com/en/java/javase/25/docs/specs/jvmti.html#whatIs) (JVMTI) provides this level of detail, but it requires writing native code and a separate binary for each platform you want to support.

The [Java Instrumentation API](https://docs.oracle.com/en/java/javase/25/docs/api/java.instrument/java/lang/instrument/package-summary.html) provides an alternative to JVMTI that can be implemented entirely in Java. It lets you intercept class definitions and transform them before the JVM finishes loading the class. APM Java uses this mechanism to add method advice that records when a method starts and ends, as well as propagating context from one method to another.

While a single piece of method advice only adds a small amount of overhead, instrumenting every method of every class would quickly become expensive. Instead, we need to identify the classes that provide the most observability value and focus our instrumentation there.

A typical Java application defines tens of thousands of classes, and a large enterprise application may load more than 100,000. This creates a large search space that we must narrow down to find the relatively small number of classes that require instrumentation. Class names provide a cheap way to prune classes and packages compared to structural and class hierarchy matches, which need to parse the class file and may require parsing of additional class files to inspect related types.

That’s why our first step is always to compare the class name against a curated ignore list of class and package prefixes. This significantly reduces the search space before we perform more detailed structural and hierarchy-based checks. Even then, the sheer number of classes involved means that small improvements to the prefix-matching algorithm can have a measurable impact on startup performance.

## Optimizing prefix matching during JVM startup

Prefix matching is largely considered a solved problem. But prefix matching during JVM startup introduces unexpected constraints.

Some instrumentation, such as adding context fields, must happen before a class is first loaded. To do this for Java Development Kit (JDK) classes, we need to register our class transformer during a little-known JVM phase called `premain`. When you attach an [agent on the command line](https://docs.oracle.com/en/java/javase/25/docs/api/java.instrument/java/lang/instrument/package-summary.html#starting-an-agent-from-the-command-line-interface-heading), the JVM calls the agent’s `premain` method before it calls the application’s `main` method.

At this point, hardly any classes have been loaded and the JIT compiler is cold. We have to be careful what we load and call because some JDK methods have unexpected side effects that can affect the application. For example, anything that uses `java.util.logging` (JUL) will initialize the `LogManager` singleton, and that initialization is irreversible. If an application needs a custom `LogManager` and sets the `java.util.logging.manager` system property in `main`, triggering JUL initialization in `premain` will break the application.

Java 8 adds a further constraint: It does not start the JIT compiler until after `premain`, so code there is interpreted and unoptimized.

Back in 2020, APM Java used code to define a complex nested structure of prefix matches. This was flexible but hard to maintain. We also needed several optimizations to make it perform well on Java 8, where it could not benefit from JIT compilation during `premain`.

After analyzing the existing prefix matches, the most obvious replacement was a **trie**. Tries are tree-based data structures that distribute elements of the key across several nodes. For example, a trie that matches `ball`, `bat`, `car`, `care`, and `cat` could look like the following:

![Prefix trie with branches for b and c, matching the strings ball, bat, car, care, and cat.](https://web-assets.dd-static.net/42588/1785784597-f1-improving-apm-java-startup-with-a-prefix-trie.png?format=auto&fit=bounds&quality=75&disable=upscale&width=767&dpr=1)

This trie represents the strings ball, bat, car, care, and cat. Green leaf nodes end the search with a result, while the purple bud node updates the result and allows matching to continue.

But how should we store the trie data? One benefit of the code-based approach was that the JVM handled finding and loading the classes from the agent. With a conventional trie, we would need to look up a resource, read the file, parse the content, and construct the trie nodes. And we would need to do all of that in the constrained environment of `premain`, where the JIT is cold or absent, we cannot touch certain classes, and we cannot load external dependencies that might later conflict with the application.

We needed the lookup performance of a trie without the startup cost of building one.

## Encoding a trie as a single string constant

The result was [ClassNameTrie](https://github.com/DataDog/dd-instrument-java/blob/v0.0.4/utils/src/main/java/datadog/instrument/utils/ClassNameTrie.java), a prefix trie encoded as a JVM constant.

Storing trie data as a JVM constant has a number of benefits. The JVM loads the string constant as part of class loading, making the encoded trie accessible through a single bytecode instruction (`ldc`). There is no need to look up resources or perform I/O. Because the string constant is embedded directly in the class that uses it, it survives repackaging. The compact encoding also improves cache locality.

So how does it work?

Java string constants are defined as a sequence of chars. Each char can hold 2 bytes, giving us 65,536 unique values. How those values are interpreted is entirely up to us, which means we can store both control information and content in the same string.

Let’s start by defining an individual node:

![Layout of a ClassNameTrie node with fields for branch count, branch characters, branch values, and jump offsets.](https://web-assets.dd-static.net/42588/1785784688-f2-improving-apm-java-startup-with-a-prefix-trie.png?format=auto&fit=bounds&quality=75&disable=upscale&width=767&dpr=1)

Each node begins with the number of branches, followed by branch characters, branch values, and jump offsets. Together, these fields encode both the trie structure and the matching behavior inside a single string constant.

The first character in a node gives the number of branches. It is immediately followed by the individual branch characters. These are sorted to allow for quick binary search. After the branch characters there is an equal number of value characters, one for each branch.

Values have three possible meanings, identified by the top bits of the value:

- A leaf, which provides a definitive result and stops the search
- A bud, which provides a potential result but allows the search to continue
- The length of the inline segment string for that branch

![Bit layout of a 16-bit branch value, with flag bits and remaining bits used for a result value or segment length.](https://web-assets.dd-static.net/42588/1785784760-f3-improving-apm-java-startup-with-a-prefix-trie.png?format=auto&fit=bounds&quality=75&disable=upscale&width=767&dpr=1)

A branch value uses the three highest-order bits to distinguish between leaves, buds, glob matches, and inline segment lengths. The remaining bits store either the result value or the segment length.

Buds and leaves may also have the glob bit set. Normally a value only applies if the key ends exactly at the bud or leaf node. If the glob bit is set, the value applies even when there are more characters left in the key. This leaves 8,191 as the maximum value that can be stored in a ClassNameTrie branch, which is more than enough for our needs.

At the end of the node are the jump offsets for each branch, each stored in a single character. These give the offset to the inline segment string for each branch, or its child node if the branch has no segment, relative to the end of the current node. There is always one fewer jump than the number of branches because the offset for the first branch is guaranteed to be zero.

Large tries may contain jump offsets that don’t fit into a character. Jump offsets larger than 61,439 (0xEFFF) are stored in a separate long-jump table. The index into that table is stored in the trie with the long-jump marker set, so the real offset can be retrieved from the table when required.

![Bit layouts for short and long jump values, with long jumps storing an index into a separate offset table.](https://web-assets.dd-static.net/42588/1785785381-f4-encoding-a-prefix-trie-as-a-jvm-constant.png?format=auto&fit=bounds&quality=75&disable=upscale&width=767&dpr=1)

Most jump offsets can be stored directly in the trie. Larger offsets are stored in a separate long-jump table, and the trie stores an index into that table with the long-jump marker set.

Each node is followed by its child nodes, one for every non-leaf branch. A child node may be preceded by an inline segment string, which the key must match if that branch is taken. As an additional space optimization, segment strings that end in a single leaf node can replace the three-character child node with a single leaf value.

Let’s look at a ClassNameTrie that matches `ball`, `bat`, `car`, `care`, and `cat`:

![Encoded ClassNameTrie for the strings ball, bat, car, care, and cat, including nodes, segments, and jump offsets.](https://web-assets.dd-static.net/42588/1785854339-f5-improving-apm-java-startup-with-a-prefix-trie.png?format=auto&fit=bounds&quality=75&disable=upscale&width=767&dpr=1)

This encoded ClassNameTrie matches ball, bat, car, care, and cat. The layout shows branch counts, branch characters, inline segment lengths, leaf and bud values, segment characters, and jump offsets.

We start each match with a default result of `-1`.

The first node has two branches, `b` and `c`, each leading to an inline segment of one character. If the key matches `b`, it must then match its segment `a` before we can move onto the `ba…` node. At that node, matching `t` stops the match with a result of `0`, while matching `l` leads to another inline segment `l`. This segment ends in a single collapsed leaf, so if we match the second `l`, we again stop with a result of `0`.

If the key matches `c`, we jump over the `b` portion of the trie and must match the inline segment `a` before moving on to the `ca…` node. This node contains both a leaf and a bud. Matching `t` stops the match with a result of `0`, while matching `r` updates the result and continues the search. Buds cannot have inline segments, so the final `e` is wrapped in a child node.

Note both `ba…` and `ca…` nodes contain jump offsets that are technically never used because their branches are leaves. They are retained to preserve the node layout, allowing us to move from branch character to value to jump offset, and then past the node itself using simple arithmetic based only on the branch count.

In pseudocode, the matching process looks like:

1. Read the next key character.
2. Read the branch count for the current node.
3. Binary search the branch characters.
	- If no branch matches, then stop.
4. If the matched value is a leaf or bud:
	- If there are no more key characters, or the value is a glob, update result.
		- If there are no more key characters, or the value is a leaf, stop.
5. Treat the remaining value as a segment-length (0 for leaf or bud).
6. Apply the branch’s jump offset from the end of the node.
7. Match the `segment-length` key characters against the inline segment.
	- If the segment does not match, stop.
		- Check whether a collapsed leaf follows the segment.
		- If there are no more key characters, or the collapsed leaf is a glob, update the result and stop.
8. Repeat from step 1.

This is implemented as a single static, thread-safe method.

Want to see how ClassNameTrie behaves with your own data? Try our [interactive demo](https://datadoghq.dev/dd-instrument-java/demos/ClassNameTrieDemo.html).

## Measuring cold-start performance

We want to measure cold-start performance because we’re most interested in how the trie behaves during `premain` and initial loading of the application. This differs from most benchmarks, which use warm-up runs to get the JVM into a steady state. To approximate startup conditions, we use the Java Microbenchmark Harness (JMH)’s `SingleShotTime` mode to measure how long it takes to match 32,000 common class names, forking multiple JVMs to produce stable results.

The following chart shows the cold-start time required to prefix-match 32,000 common class names against the same set of prefix mappings encoded using Java code, a classic radix trie, and ClassNameTrie. The benchmark was run on a 2021 MacBook Pro with an M1 Max CPU and 64 GB of memory.

The results confirm that ClassNameTrie is much faster than the old code-based approach, especially on Java 8, where it is **nearly 5x faster**. It’s even faster than a classic radix trie during cold start, due to its compact representation and cache locality.

![Comparison of cold-start prefix-matching times for Java code, a radix trie, and ClassNameTrie across Java 8, 17, and 25.](https://web-assets.dd-static.net/42588/1785785563-f6-improving-apm-java-startup-with-a-prefix-trie.png?format=auto&fit=bounds&quality=75&disable=upscale&width=767&dpr=1)

Time required to prefix-match 32,000 common class names during cold startup. ClassNameTrie consistently outperforms both the original code-based matcher and a classic radix trie across Java 8, Java 17, and Java 25.

In a real-world Spring Boot application, ignoring uninteresting classes by name reduced instrumented startup time by 20%. Switching from the code-based approach to ClassNameTrie saved a further 1% while making the ignore list much easier to maintain and grow.

We then realized we had an efficient way to map class names to integers. That insight led us to another optimization: a known types index that maps class names directly to numbered instrumentations. This shortcut saved another 3%, bringing the total savings to more than 24% compared to not filtering by class name.

We’ve found that these incremental improvements, especially along the critical path, build into meaningful gains—not a single breakthrough. ClassNameTrie is a good example. Initially built with one optimization in mind, it’s now used in other APM features, including [Live Debugger](https://docs.datadoghq.com/tracing/live_debugger/) and [Continuous Integration (CI) Visibility](https://docs.datadoghq.com/continuous_integration/), to filter and classify class names.

## When data is cheaper than code

We’ve shown how it’s possible to encode a prefix trie as a string constant, and the advantages of storing data as constants in the JVM. This is especially important during early JVM startup, where code can be more expensive than data.

Yet pruning by name is just one aspect of class matching. Structural matches rely on parsing the class files. To speed this up, we developed our own class-file parser that extracts only the elements needed for matching. More complex hierarchy matches require finding and loading class files outside of the current class. This can be costly and produce a lot of data, so we applied dynamic programming to combine matches and avoid repeated loops over the class hierarchy.

All code discussed in this post is available from our [open source instrumentation helper library](https://github.com/DataDog/dd-instrument-java).

If solving JVM performance and observability challenges at scale sounds interesting, check out our [open engineering roles at Datadog](https://careers.datadoghq.com/all-jobs/?s=apm&parent_department_Engineering%5B0%5D=Engineering&utm_source=engblog&utm_medium=corpsite&utm_campaign=engcommunity-2025-java-apm&gh_src=hm4uekgj1us).
