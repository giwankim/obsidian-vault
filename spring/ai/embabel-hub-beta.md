---
title: "Embabel Hub (beta)"
source: "https://hub.embabel.com/"
author:
published:
created: 2026-07-16
description: "Learn what you need to know in order to be successful with Embabel - the Agentic AI framework for the JVM."
tags:
  - "clippings"
---

> [!summary]
> Landing page for Embabel, an agentic AI framework for the JVM built by a team that includes Spring Framework founder Rod Johnson. It argues that Java and Kotlin's strong typing, mature tooling, and enterprise track record make the JVM better suited than Python for production-scale AI, showcasing typesafe prompt code in Kotlin. Links out to the quickstart, reference guide, and blog posts on MCP tools, context engineering, and an Embabel vs Pydantic AI comparison.

## Agentic AI for the JVM

Embabel is an Agentic AI framework for the JVM. Python has long been the go-to for machine learning experiments, thanks to its ease, ecosystem richness, and data scientist-friendly tools. However, it often struggles when you try to move from experiment to real-world, production-scale AI.

As AI adoption becomes more mission critical, what matters is not just model training or computation. It is context, reliability, type safety, performance, observability, and integration with existing enterprise systems. Java and Kotlin offer these strengths. Strong typing, mature tooling, and proven track records in resilient, scalable systems make them a compelling choice for serious AI. It is time to move beyond proofs of concept.

[Quickstart](https://hub.embabel.com/getting-started/quickstart) [Reference Guide](https://hub.embabel.com/reference/flow)

## As modern as Kotlin, as proven as Java

The JVM has evolved. It is now modern and feature-rich, while remaining one of the fastest platforms and carrying the reliability of decades of enterprise use. What's stopping your from writing applied AI code that look like this?

```kotlin
@Action
fun extractPerson(userInput: UserInput, context: OperationContext): Person? =
    // All prompts are typesafe
    context.ai().withDefaultLlm().createObjectIfPossible(
        """
        Create a person from this user input, extracting their name:
        ${userInput.content}
        """
    )
```

## The Team Behind Embabel

Alongside **Spring Framework founder** Rod Johnson and other alumni, Embabel is built by a team of high-achieving engineers with a proven record not only in applied AI, but also in designing, scaling, and delivering large, complex systems.

[Join the Embabel Community on Discord](https://discord.gg/t6bjkyj93q)

## Featured Blog Posts

Embabel team and community members share their guides, experiences, best practices and opinions on Embabel.

### Building MCP Tools

How to Create Interactive MCP Tools with Embabel.

[Read more](https://medium.com/@springrod/building-stateful-ai-agents-how-to-create-interactive-mcp-tools-with-embabel-0dfbd3037cf7)

### DICE

Context Engineering Needs Domain Understanding.

[Read more](https://medium.com/@springrod/context-engineering-needs-domain-understanding-b4387e8e4bf8)

### Embabel vs Pydantic AI

Like for like comparison of a Pydantic AI application vs Embabel

[Read more](https://medium.com/@springrod/build-better-agents-in-java-than-python-embabel-vs-pydantic-ai-ab373c149108)

### Add AI to Existing Apps

Ground Your AI Transformation on What Works Today

[Read more](https://medium.com/@springrod/ground-your-ai-transformation-on-what-works-today-bfc525418118)
