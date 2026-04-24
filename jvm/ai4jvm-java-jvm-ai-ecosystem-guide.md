---
title: "AI4JVM — Java & JVM AI Ecosystem Guide"
source: "https://ai4jvm.com/?utm_source=substack&utm_medium=email"
author:
published:
created: 2026-04-12
description: "The curated guide to AI on the JVM — Spring AI, LangChain4j, Kotlin AI frameworks, inference engines, and more. Compare Java AI agent frameworks, find learning resources, and follow key people building the Java AI ecosystem."
tags:
  - "clippings"
---

> [!summary]
> A curated directory of the AI-on-JVM ecosystem: agent frameworks (Spring AI, LangChain4j, Embabel, Google ADK, Akka Agents, Koog), MCP/A2A SDKs, inference engines (Jlama, GPULlama3.java, ONNX Runtime Java), and learning resources. Frames Java as a first-class platform for building AI agents without leaving the JVM — including local LLM inference with no Python at serving time.

## Latest Headlines

- [Announcing ADK for Java 1.0.0: Building the Future of AI Agents in Java](https://developers.googleblog.com/announcing-adk-for-java-100-building-the-future-of-ai-agents-in-java/) — Google’s Agent Development Kit for Java hits 1.0 with new tools, plugin architecture, context compaction, and human-in-the-loop support
- [AI-Assisted Java Application Development with Agent Skills](https://blog.jetbrains.com/idea/2026/03/ai-assisted-java-application-development-with-agent-skills/) — how Agent Skills enable AI agents to extend their capabilities with specialized knowledge for Java development
- [Spring AI 2.0.0-M4, 1.1.4, and 1.0.5 Available](https://spring.io/blog/2026/03/26/spring-ai-2-0-0-M4-and-1-1-4-and-1-0-5-available) — JSpecify null-safety completion, new features, and maintenance releases with bug fixes
- [Introducing Tracy: The AI Observability Library for Kotlin](https://blog.jetbrains.com/kotlin/2026/03/introducing-tracy-the-ai-observability-library-for-kotlin/) — production-grade AI observability for Kotlin apps, debug failures and track LLM usage with OpenTelemetry
- [Multi-Language MCP Server Performance Benchmark](https://www.tmdevlab.com/mcp-server-performance-benchmark.html) — comparative analysis across Go, Java, Python, and TypeScript
- [2026 Java AI Apps](https://thenewstack.io/2026-java-ai-apps/) — building AI applications with Java in 2026
- [Agent Memory Is Not a Greenfield Problem](https://medium.com/embabel/agent-memory-is-not-a-greenfield-problem-ground-it-in-your-existing-data-9272cabe1561) — ground it in your existing data
- [Production LangChain4j at Devoxx Belgium](https://inside.java/2026/02/01/devoxxbelgium-production-langchain4j/) — advanced RAG, agentic workflows, and production tips

---

## Agent Frameworks & Libraries

Open-source frameworks and SDKs for building AI-powered applications on the JVM — from full agent platforms to Model Context Protocol implementations.

Framework

### Spring AI

The Spring ecosystem's official AI framework. Portable abstractions across 20+ model providers, tool calling, RAG, chat memory, vector stores, and MCP support. Built by the Spring team at Broadcom.

Framework

### LangChain4j

The most popular Java LLM library. Unified API across 20+ LLM providers and 20+ embedding stores. Three levels of abstraction from low-level prompts to high-level AI Services. Supports RAG, tool calling, MCP, and agents.

Framework

### Embabel

Created by Rod Johnson (Spring Framework creator). JVM agent framework using Goal-Oriented Action Planning (GOAP) for dynamic replanning. Strongly typed, Spring-integrated, MCP support. Written in Kotlin with full Java interop.

Framework

### Google ADK for Java

Google's Agent Development Kit — code-first Java toolkit for building, evaluating, and deploying AI agents. Supports Gemini natively plus third-party models via LangChain4j integration. A2A protocol for agent-to-agent communication.

Framework

### Quarkus LangChain4j

Enterprise-grade Quarkus extension for LangChain4j. Native compilation with GraalVM, built-in observability (metrics, tracing, auditing), and Dev UI tooling. Maintained by Red Hat & IBM.

Framework

### Helidon LangChain4j

Oracle's Helidon framework integration with LangChain4j. Declarative AI Services via Helidon Inject, build-time code generation for GraalVM native images, streaming chat over Java Streams, guardrails, built-in metrics, and agentic support (workflows and dynamic agents). Runs on virtual threads.

Framework

### Helidon MCP

Helidon's Model Context Protocol server and client implementation. Declarative and imperative APIs for building MCP servers with tools, resources, and prompts. Streamable HTTP and SSE transports, virtual threads, build-time processing. From Oracle's Helidon team.

Framework

### LangChain4j-CDI

CDI extension for LangChain4j (part of the LangChain4j project) that brings AI services to Jakarta EE and MicroProfile applications. Inject AI services as CDI beans with `@RegisterAIService`, configure via MicroProfile Config, and add resilience with Fault Tolerance. Supports Quarkus, Helidon, WildFly, Payara, GlassFish, Liberty, and any CDI-capable runtime.

Framework

### LangGraph4j

Build stateful, multi-agent applications with cyclical graphs. Inspired by Python's LangGraph, works with both LangChain4j and Spring AI. Persistent checkpoints, deep agent architectures, and a Studio web UI.

Framework

### Akka Agents

Agentic AI platform built on Akka's actor model for distributed, resilient systems. Declarative Effects API for building goal-directed agents with durable memory, multi-agent orchestration, and automatic scaling. MCP and A2A protocol support, pluggable LLM providers, runtime prompt updates, and agents auto-exposed as HTTP, gRPC, or MCP endpoints. Java and Scala SDKs.

Framework

### Koog (JetBrains)

Kotlin-native agent framework from JetBrains. Type-safe DSL, multiplatform (JVM, JS, WasmJS, Android, iOS), A2A protocol support, fault tolerance with persistence, and multi-LLM support.

Framework

### Semantic Kernel (Java)

Microsoft's AI orchestration SDK with first-class Java support. Provides prompt chaining, planning, memory, and agent framework abstractions with deep Azure integration.

Framework

### JamJet

Production-grade agent runtime with native Java SDK. Rust core (Tokio) for performance, graph-based durable workflow orchestration with event-sourced state, automatic crash recovery, audit trails, and first-class human-in-the-loop. Native MCP client/server and A2A protocol support. Java SDK uses records, virtual threads, and fluent builder API. Apache 2.0.

SDK

### MCP Java SDK

The official Java SDK for Model Context Protocol servers and clients. Maintained by the Spring AI team. Sync/async, STDIO/SSE/Streamable HTTP transports, OAuth support via Spring integration.

SDK

### Anthropic Java SDK

Official Java SDK for the Claude Messages API. Streaming, retries, structured outputs, extended thinking, code execution, and files API. Build Java apps powered by Claude.

SDK

### GitHub Copilot SDK for Java

Official Java SDK for embedding the GitHub Copilot agentic engine directly into Java applications. Uses the same agentic harness that powers the Copilot CLI — exposes planning, tool calling, file editing, and MCP integration via a simple Java API. Currently in technical preview.

Library

### Tracy (JetBrains)

AI tracing library for Kotlin and Java. Captures structured traces from LLM interactions — messages, cost, token usage, and execution time. Implements OpenTelemetry Generative AI Semantic Conventions with exports to Langfuse, Weights & Biases, and more.

Library

### Docling Java

Official Java client for Docling Serve — invoke document conversion, table detection, formula recognition, reading order analysis, OCR, and more from Java via the Docling Serve backend.

Library

### OmniHai

Unified Java AI utility library for Jakarta EE and MicroProfile. Single API across 10 providers with zero external runtime dependencies — just java.net.http.HttpClient. Chat, streaming, structured outputs, web search, translation, and moderation in a lightweight JAR.

Library

### ACP Langchain4j bridge

An ACP client bridging the official [Kotlin ACP sdk](https://agentclientprotocol.com/libraries/kotlin) to [LangChain4j](https://docs.langchain4j.dev/intro/) and [LangGraph4j](https://github.com/langgraph4j/langgraph4j).

SDK

### A2A Java SDK

The official Java SDK for [Agent-2-Agent Protocol (A2A)](https://a2a-protocol.org/) servers and clients. Reference implementation based on Quarkus.

SDK

### A2A Java SDK for Jakarta Servers

Integration of the [A2A Java SDK](https://github.com/a2aproject/a2a-java) for use in Jakarta EE servers (WildFly, Tomcat, Jetty, OpenLiberty, and others).

Framework

### WildFly AI Feature Pack

A feature pack for WildFly, providing seamless LangChain4j-CDI integration and exposing Jakarta EE code as MCP tools via MCP\_JAVA Annotations.

Library

### MCP\_JAVA Annotations

A framework-agnostic Java library providing core annotations and APIs for implementing Model Context Protocol (MCP) servers and clients. Used by WildFly AI Feature Pack and LangChain4j-CDI. Compatible with OpenLiberty, Quarkus, and other Java frameworks.

Framework

### Atmosphere

A portable layer across Java AI runtimes. Write `@Agent` once against a unified API (tool calling, memory, streaming, structured output); swap the runtime — Spring AI, LangChain4j, Google ADK, Embabel, Koog, or built-in OpenAI — by changing one dependency. `@Coordinator` orchestrates multi-agent fleets with parallel, sequential, and conditional routing. Served over transports (WebTransport/HTTP3, WebSocket, SSE, long-polling, gRPC) and protocols (MCP, A2A, AG-UI). Built by Async-IO.

---

## Java with Code Assistants

Technologies that supercharge Java development when paired with AI code assistants — from MCP servers that give agents live Javadoc access, to reusable skill packages and IDE integrations.

MCP Server

### [Javadocs.dev MCP Server](https://www.javadocs.dev/)

Gives AI assistants live access to Java, Kotlin, and Scala library documentation from Maven Central. Six tools including latest-version lookup, Javadoc symbol browsing, and source file retrieval. Connect any MCP client via Streamable HTTP.

Assistant

### JetBrains AI

AI-powered coding assistance built into IntelliJ IDEA and all JetBrains IDEs. Context-aware code completion, next-edit suggestions, and an agent-mode chat for refactoring, test generation, and complex tasks. Deep understanding of Java, Kotlin, and Scala project conventions. Supports cloud LLMs (Gemini, OpenAI, Anthropic) plus bring-your-own-key.

Skills

### [SkillsJars](https://www.skillsjars.com/)

A packaging format and registry for distributing reusable AI agent skills as Maven/Gradle JARs. Skills are Markdown files (`SKILL.md`) under `META-INF/skills/` that teach AI agents domain-specific patterns. Discover and load skills on demand in Claude Code, Kiro, and Spring AI apps.

Skills

### jvm-skills

Curated directory of AI coding skills from JVM ecosystem engineers. Opinionated best-practice guides that AI tools (Claude Code, Cursor, Copilot) use as context — covering Spring Boot, jOOQ, Testcontainers, Docker, and more. Only lists skills that teach AI something it wouldn't know on its own.

Skills

### Awesome GitHub Copilot

Awesome Copilot Skills is a curated registry of reusable AI agent skills that developers can plug into agents, providing ready-made capabilities, prompts, and workflows. It helps Java AI developers quickly extend agent functionality without building everything from scratch.

---

## Inference & Training

Run models, train classifiers, and do ML inference directly on the JVM — no Python required.

Inference

### Deliverance

Deliverance is a Java inference engine capable of generating text, tokenizing input, computing embeddings, and more. Can be used as embedded library inside your Java application or as an HTTP server /chat/completion). Deliverance also provides chat and Rag Chat through vibrant-maven-plugin allowing you to chat with your code!

Inference

### Jlama

⚠️ No longer actively maintained. Modern LLM inference engine written in pure Java. Runs Llama, Gemma, Mistral, and more locally on CPU. Uses Java's Vector API (Project Panama) for SIMD-accelerated matrix math. Supports SafeTensors format, quantized models, and distributed inference.

Inference

### Deep Java Library (DJL)

AWS's high-level, engine-agnostic deep learning framework. Supports PyTorch, TensorFlow, ONNX Runtime, and XGBoost backends. DJLServing provides high-performance model serving.

Inference

### ONNX Runtime Java

Run transformer and classical ML models directly on the JVM. Hardware acceleration via CUDA, DirectML, CoreML, and more. Enables deploying scikit-learn, PyTorch, and HuggingFace models as ONNX in Java without Python at inference time.

Training

### Tribuo

Oracle Labs' ML library for classification, regression, clustering, and anomaly detection. Strong typing, provenance tracking for reproducibility, and integrations with XGBoost, ONNX Runtime, TensorFlow, and LibSVM.

Inference

### [GPULlama3.java](https://www.infoq.com/news/2025/06/gpullama3-java-gpu-llm/)

Java-native LLM inference with automatic GPU acceleration via TornadoVM. Supports Llama 3, Mistral, Qwen, Phi-3, and IBM Granite models in GGUF format. TornadoVM translates Java bytecode to GPU kernels (OpenCL, PTX, SPIR-V). From the University of Manchester's Beehive Lab.

Training

### TensorFlow Java

Java bindings for TensorFlow, maintained by the TensorFlow JVM SIG. Train and deploy TF models entirely in Java. Available as an optional Tribuo integration. Suitable for teams that want to stay within the JVM ecosystem while using TensorFlow's model formats.

---

## People to Follow

Key voices at the intersection of Java and AI.

---

## FAQ

Frequently asked questions about AI development on the JVM.

What is the best Java framework for building AI agents?

The most popular choices are [Spring AI and LangChain4j](#frameworks). Spring AI is ideal if you’re already in the Spring ecosystem, offering portable abstractions across 20+ model providers. LangChain4j provides a standalone library with three levels of abstraction, from low-level prompts to high-level AI Services. Other options include Google ADK for Java, Embabel, and Akka Agents — each with different strengths for specific use cases.

Can Java run LLMs locally?

Yes. Projects like [Jlama and GPULlama3.java](#inference) run Llama, Mistral, and other models directly on the JVM. Jlama uses Java’s Vector API for SIMD-accelerated inference on CPU, while GPULlama3.java leverages TornadoVM for GPU acceleration. For production deployments, ONNX Runtime Java supports hardware-accelerated inference across CUDA, DirectML, and CoreML.

What is MCP and how does it work with Java?

The Model Context Protocol (MCP) is an open standard that lets AI assistants interact with external tools and data sources. The official MCP Java SDK, maintained by the Spring AI team, provides both client and server implementations with sync/async support and multiple transports (STDIO, SSE, Streamable HTTP). Helidon MCP and several frameworks also offer MCP support.

Is Kotlin supported by Java AI frameworks?

Yes. Most Java AI frameworks run on any JVM language. Embabel is written in Kotlin with full Java interop, Koog from JetBrains is a Kotlin-native agent framework, and Tracy provides AI observability for Kotlin. LangChain4j and Spring AI work seamlessly from Kotlin code.

---

## Recent & Noteworthy Content, Communities, and Resources

Community

### [Java Conferences Tracker](https://javaconferences.org/)

Community-maintained calendar of all Java conferences worldwide

Blog

### [Java Relevance in the AI Era](https://redmonk.com/jgovernor/java-relevance-in-the-ai-era-agent-frameworks-emerge/)

RedMonk analysis of Java's position as agent frameworks emerge

Resource

### [Awesome Spring AI](https://github.com/spring-ai-community/awesome-spring-ai)

Curated list of Spring AI resources, tools, and tutorials

Book

### [Spring AI in Action (Manning)](https://www.manning.com/books/spring-ai-in-action)

Book by Craig Walls — comprehensive guide to building AI apps with Spring

Book

### [Understanding LangChain4j](https://www.amazon.com/Understanding-LangChain4j-2nd-agoncal-fascicles-ebook/dp/B0FDQVSLXK)

Book by Antonio Goncalves — explore the fundamentals of AI, learn the history and evolution of AI models, and understand the core concepts of LangChain4j

Resource

### [Production LangChain4j — Inside.java](https://inside.java/2026/02/01/devoxxbelgium-production-langchain4j/)

Advanced RAG, agentic workflows, and production tips from Devoxx Belgium

Resource

### [Google ADK Java Codelab](https://codelabs.developers.google.com/adk-java-getting-started)

Hands-on: build AI agents in Java with Google's ADK

Videos

### [Devoxx YouTube](https://www.youtube.com/@DevoxxForever)

Thousands of conference talks on Java, AI, cloud, and architecture

Videos

### [Coffee + Software](https://youtube.com/@coffeesoftware)

Spring ecosystem, AI integration, and Java community

Resource

### [Foojay Podcast: Java AI Revolution](https://foojay.io/today/foojay-podcast-86/)

Agents, MCP, graph databases — developers navigate the AI revolution

Workshop

### [Building Java AI Agents with Spring AI (AWS)](https://catalog.workshops.aws/java-spring-ai-agents/en-US)

Hands-on AWS workshop for building intelligent AI agents with Spring AI and AWS services, including deployment to EKS

Livestream

### [AI & Java on Serverless Office Hours](https://www.youtube.com/watch?v=my2bQtHBUeY)

James Ward and Julian Wood explore building AI-powered Java apps — MCP integration, agent architectures with AgentCore, GraalVM optimization for AI workloads, and secure auth patterns for AI services on serverless
