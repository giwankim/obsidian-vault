---
title: "Claude Cookbook"
source: "https://platform.claude.com/cookbook/"
author:
published:
created: 2026-07-25
description: "Practical guides and code examples for building with Claude. Learn prompting techniques, tool use, multimodal capabilities, and more."
tags:
  - "clippings"
---

> [!summary]
> Index page for Anthropic's Claude Cookbook — a catalog of ~80 practical guides and runnable notebooks for building with Claude, spanning tool use, agent patterns, RAG & retrieval, multimodal, evals, prompt caching, and third-party integrations (LlamaIndex, Pinecone, MongoDB, ElevenLabs, Wolfram Alpha). Recent entries cluster around agent infrastructure: the Claude Agent SDK series, Claude Managed Agents (sessions, file mounts, outcome graders, prompt versioning/rollback, production webhooks), and context engineering techniques like programmatic tool calling, tool search with embeddings, and automatic context compaction. Useful as a lookup table when you need a worked example for a specific capability rather than as a linear read.

[Programmatic tool calling (PTC)](https://platform.claude.com/cookbook/tool-use-programmatic-tool-calling-ptc)

[

Reduce latency and token consumption by letting Claude write code that calls tools programmatically in the code execution environment.

](https://platform.claude.com/cookbook/tool-use-programmatic-tool-calling-ptc)[

Tool search with embeddings

Scale Claude applications to thousands of tools using semantic embeddings for dynamic tool discovery.

](https://platform.claude.com/cookbook/tool-use-tool-search-with-embeddings)[

Automatic context compaction

Manage context limits in long-running agentic workflows by automatically compressing conversation history.

](https://platform.claude.com/cookbook/tool-use-automatic-context-compaction)[

Giving Claude a crop tool for better image analysis

Give Claude a crop tool to zoom into image regions for detailed analysis of charts, documents, and diagrams.

](https://platform.claude.com/cookbook/multimodal-crop-tool)[

Prompting for frontend aesthetics

Guide to prompting Claude for distinctive, polished frontend designs avoiding generic aesthetics.

](https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics)[

Introduction to Claude Skills

Create documents, analyze data, automate workflows with Claude's Excel, PowerPoint, PDF skills.

](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction)

## All Cookbooks

| Title | Categories | Author(s) | Date |
| --- | --- | --- | --- |
| [Reproduce Claude's agentic search benchmark scores in the Messages API  Build a Messages API harness that reproduces published DeepSearchQA and BrowseComp scores, using programmatic tool calling, server-side compaction, and task budgets.  ](https://platform.claude.com/cookbook/evals-agentic-search-reproduce-agentic-search-benchmarks) | EvalsTools | Mengting Li | Jun 2026 |
| [Classifier fallback and billing for Claude Fable 5  Detect safety classifier blocks on Fable 5 and fall back to Opus 4.8 with server-side or SDK-based client-side fallback, including streaming behavior and the new billing changes.  ](https://platform.claude.com/cookbook/fable-5-fallback-billing-guide) | ResponsesSafeguardsBilling | Alexander Bricken  Mahesh Murag  Mikaela Grace | Jun 2026 |
| [Async multi-agent orchestration  Two async multi-agent patterns — a fixed N-agent team with peer messaging through a shared hub, and dynamically spawned async subagents — reduced to their bare messaging and lifecycle mechanics.  ](https://platform.claude.com/cookbook/patterns-agents-async-multi-agent-orchestration) | Agent Patterns | Paul Chen | Jun 2026 |
| [Hosting your agent  Deploy the research agent from notebook 00 through three tiers of operational maturity (Docker, Modal, Kubernetes) with the same container image and HTTP interface at every tier.  ](https://platform.claude.com/cookbook/claude-agent-sdk-07-hosting-the-agent) | Claude Agent SDK | Kevin Tang  Anav Sharma | May 2026 |
| [Multiagent: coordinate a specialist team  Heterogeneous team via the multiagent coordinator config — a coordinator runs three specialists (web-search researcher, file-reading librarian, rules-based pricer) with scoped toolsets to assemble a sales proposal. Covers the multiagent field, the thread\_created / thread\_message\_received event types, and per-role tool scoping.  ](https://platform.claude.com/cookbook/managed-agents-cma-coordinate-specialist-team) | Claude Managed AgentsTools | Mark Nowicki | May 2026 |
| [Outcomes: agents that verify their own work  Build a grade-and-revise loop with Outcomes: a writer drafts a cited research brief, a stateless grader fetches every URL and checks every quote against a rubric, and feedback drives revisions until the brief passes. Covers user.define\_outcome, the span.outcome\_evaluation\_\* events, and how to write a rubric the grader can act on.  ](https://platform.claude.com/cookbook/managed-agents-cma-verify-with-outcome-grader) | Claude Managed AgentsEvals | Mark Nowicki  Gagan Bhat | May 2026 |
| [Build agents that remember your users  Give your Claude Managed Agents a Memory store so they learn and remember your users' preferences across multiple interactions.  ](https://platform.claude.com/cookbook/managed-agents-cma-remember-user-preferences) | Claude Managed AgentsTools | Gagan Bhat | Apr 2026 |
| [The vulnerability detection agent  Build a vulnerability-discovery agent with the Claude Agent SDK that threat-models a C target, hunts memory-safety bugs with built-in file tools, and triages findings into a structured report.  ](https://platform.claude.com/cookbook/claude-agent-sdk-06-the-vulnerability-detection-agent) | Claude Agent SDKCybersecurity | Eugene Yan | Apr 2026 |
| [Build an SRE incident response agent with Claude Managed Agents  Wire Claude into your on-call flow: when an alert fires, the agent reads logs and runbooks, pinpoints the root cause, opens a fix PR, and waits for your approval before merging.  ](https://platform.claude.com/cookbook/managed-agents-sre-incident-responder) | Claude Managed AgentsObservability | Gagan Bhat | Apr 2026 |
| [Build a data analyst agent with Claude Managed Agents  Build an analyst that turns a CSV into a narrative HTML report with interactive charts, using a sandboxed environment and file mounting.  ](https://platform.claude.com/cookbook/managed-agents-data-analyst-agent) | Claude Managed AgentsTools | Charmaine Lee  Jess Yan | Apr 2026 |
| [Build a Slack data analyst bot with Claude Managed Agents  Mention the bot with a CSV to get an analysis report in-thread, with multi-turn follow-ups on the same session.  ](https://platform.claude.com/cookbook/managed-agents-slack-data-bot) | Claude Managed AgentsIntegrations | Charmaine Lee | Apr 2026 |
| [Managed Agents tutorial: iterate on a failing test suite  Entry-point tutorial for the Claude Managed Agents API. Walks through agent / environment / session creation, file mounts, and the streaming event loop by getting an agent to fix three planted bugs in a calc.py package.  ](https://platform.claude.com/cookbook/managed-agents-cma-iterate-fix-failing-tests) | Claude Managed AgentsTools | Paul Yang | Apr 2026 |
| [Managed Agents tutorial: production setup  End-to-end production story for Managed Agents — vault-backed MCP credentials, the session.status\_idled webhook pattern for human-in-the-loop without long-lived connections, and the resource lifecycle CRUD verbs.  ](https://platform.claude.com/cookbook/managed-agents-cma-operate-in-production) | Claude Managed AgentsIntegrations | Paul Yang | Apr 2026 |
| [Managed Agents tutorial: prompt versioning and rollback  Server-side prompt versioning — create v1, evaluate against a labelled test set, ship v2, detect a regression, roll back by pinning sessions to version 1. Covers agents.update, version pinning on sessions.create, and where the review gate moves when prompts are not code.  ](https://platform.claude.com/cookbook/managed-agents-cma-prompt-versioning-and-rollback) | Claude Managed AgentsEvals | Mark Nowicki | Apr 2026 |
| [Threat intelligence enrichment agent  Build an agent that autonomously investigates IOCs by querying multiple threat intel sources, cross-referencing findings, mapping to MITRE ATT&CK, and producing structured reports for SIEM and SOAR integration.  ](https://platform.claude.com/cookbook/tool-use-threat-intel-enrichment-agent) | ToolsAgent PatternsCybersecurity | Jannet Park | Apr 2026 |
| [Building a session browser  List, read, rename, tag, and fork Agent SDK sessions on disk to build a conversation history sidebar without writing a transcript parser.  ](https://platform.claude.com/cookbook/claude-agent-sdk-05-building-a-session-browser) | Claude Agent SDKAgent Patterns | Qing Wang | Mar 2026 |
| [Knowledge graph construction with Claude  Build knowledge graphs from unstructured text using Claude for entity extraction, relation mining, deduplication, and multi-hop graph querying.  ](https://platform.claude.com/cookbook/capabilities-knowledge-graph-guide) | RAG & RetrievalTools | Anthropic | Mar 2026 |
| [Context engineering: memory, compaction, and tool clearing  Compare context engineering strategies for long-running agents and learn when each applies, what it costs, and how they compose.  ](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools) | ToolsAgent Patterns | Isabella He | Mar 2026 |
| [Migrating from the OpenAI Agents SDK  Port an OpenAI Agents SDK app to the Claude Agent SDK, mapping each primitive (tools, guardrails, sessions, handoffs) through a single expense-approval agent example.  ](https://platform.claude.com/cookbook/claude-agent-sdk-04-migrating-from-openai-agents-sdk) | Claude Agent SDKAgent Patterns | Preston Tuggle | Mar 2026 |
| [The site reliability agent  Build an incident response agent with read-write MCP tools for autonomous diagnosis, remediation, and post-mortem documentation.  ](https://platform.claude.com/cookbook/claude-agent-sdk-03-the-site-reliability-agent) | Claude Agent SDKAgent Patterns | Ben Lehrburger  Isabella He | Feb 2026 |
| [Session memory compaction  Manage long-running Claude conversations with instant session memory compaction using background threading and prompt caching.  ](https://platform.claude.com/cookbook/misc-session-memory-compaction) | Agent PatternsResponses | Joe Shamon | Jan 2026 |
| [Programmatic tool calling (PTC)  Reduce latency and token consumption by letting Claude write code that calls tools programmatically in the code execution environment.  ](https://platform.claude.com/cookbook/tool-use-programmatic-tool-calling-ptc) | Tools | Pedram Navid | Nov 2025 |
| [Tool search with embeddings  Scale Claude applications to thousands of tools using semantic embeddings for dynamic tool discovery.  ](https://platform.claude.com/cookbook/tool-use-tool-search-with-embeddings) | ToolsRAG & Retrieval | Henry Keetay | Nov 2025 |
| [Automatic context compaction  Manage context limits in long-running agentic workflows by automatically compressing conversation history.  ](https://platform.claude.com/cookbook/tool-use-automatic-context-compaction) | ToolsAgent Patterns | Pedram Navid | Nov 2025 |
| [Low latency voice assistant with ElevenLabs  Build a low-latency voice assistant using ElevenLabs for speech-to-text and text-to-speech combined with Claude.  ](https://platform.claude.com/cookbook/third-party-elevenlabs-low-latency-stt-claude-tts) | Integrations | Adriaan Engelbrecht | Nov 2025 |
| [Giving Claude a crop tool for better image analysis  Give Claude a crop tool to zoom into image regions for detailed analysis of charts, documents, and diagrams.  ](https://platform.claude.com/cookbook/multimodal-crop-tool) | MultimodalTools | Nadine Yasser | Nov 2025 |
| [Prompting for frontend aesthetics  Guide to prompting Claude for distinctive, polished frontend designs avoiding generic aesthetics.  ](https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics) | ResponsesSkills | Prithvi Rajasekaran | Oct 2025 |
| [Claude Skills for financial applications  Build financial dashboards and portfolio analytics using Claude's Excel, PowerPoint, PDF skills.  ](https://platform.claude.com/cookbook/skills-notebooks-02-skills-financial-applications) | Skills | Alex Notov | Oct 2025 |
| [Building custom Skills for Claude  Create, deploy, and manage custom skills extending Claude with specialized organizational workflows.  ](https://platform.claude.com/cookbook/skills-notebooks-03-skills-custom-development) | Skills | Alex Notov | Oct 2025 |
| [Introduction to Claude Skills  Create documents, analyze data, automate workflows with Claude's Excel, PowerPoint, PDF skills.  ](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction) | Skills | Alex Notov | Oct 2025 |
| [The one-liner research agent  Build a research agent using Claude Code SDK with WebSearch for autonomous research.  ](https://platform.claude.com/cookbook/claude-agent-sdk-00-the-one-liner-research-agent) | Claude Agent SDKAgent Patterns | Rodrigo Olivares  Jiri De Jonghe | Sep 2025 |
| [The chief of staff agent  Build multi-agent systems with subagents, hooks, output styles, and plan mode features.  ](https://platform.claude.com/cookbook/claude-agent-sdk-01-the-chief-of-staff-agent) | Claude Agent SDKAgent Patterns | Rodrigo Olivares  Jiri De Jonghe | Sep 2025 |
| [The observability agent  Connect agents to external systems via MCP servers for GitHub monitoring and CI workflows.  ](https://platform.claude.com/cookbook/claude-agent-sdk-02-the-observability-agent) | Claude Agent SDKAgent Patterns | Rodrigo Olivares  Jiri De Jonghe | Sep 2025 |
| [Tool evaluation  Run parallel agent evaluations on tools independently from evaluation task files.  ](https://platform.claude.com/cookbook/tool-evaluation-tool-evaluation) | Evals | Anthropic | Sep 2025 |
| [Usage & cost Admin API cookbook  Programmatically access and analyze your Claude API usage and cost data via Admin API.  ](https://platform.claude.com/cookbook/observability-usage-cost-api) | Observability | Anthropic | Aug 2025 |
| [Memory & context management with Claude Sonnet 4.6  Build AI agents with persistent memory using Claude's memory tool and context editing.  ](https://platform.claude.com/cookbook/tool-use-memory-cookbook) | ToolsAgent Patterns | Alex Notov | May 2025 |
| [Speculative prompt caching  Reduce time-to-first-token by warming cache speculatively while users formulate their queries.  ](https://platform.claude.com/cookbook/misc-speculative-prompt-caching) | Responses | Anthropic | May 2025 |
| [Parallel tool calls on Claude 3.7 Sonnet  Enable parallel tool calls on Claude 3.7 Sonnet using batch tool meta-pattern workaround.  ](https://platform.claude.com/cookbook/tool-use-parallel-tools) | Tools | Anthropic | Mar 2025 |
| [Extended thinking  Use Claude's extended thinking for transparent step-by-step reasoning with budget management.  ](https://platform.claude.com/cookbook/extended-thinking-extended-thinking) | Thinking | Alex Albert | Feb 2025 |
| [Extended thinking with tool use  Combine extended thinking with tools for transparent reasoning during multi-step workflows.  ](https://platform.claude.com/cookbook/extended-thinking-extended-thinking-with-tool-use) | ThinkingTools | Alex Albert | Feb 2025 |
| [Basic workflows  Three simple multi-LLM workflow patterns trading cost or latency for improved performance.  ](https://platform.claude.com/cookbook/patterns-agents-basic-workflows) | Agent Patterns | Anthropic | Dec 2024 |
| [Evaluator optimizer  Workflow pattern using one LLM for generation and another for evaluation feedback loop.  ](https://platform.claude.com/cookbook/patterns-agents-evaluator-optimizer) | Agent PatternsEvals | Anthropic | Dec 2024 |
| [Orchestrator workers  Central LLM dynamically delegates tasks to worker LLMs and synthesizes their combined results.  ](https://platform.claude.com/cookbook/patterns-agents-orchestrator-workers) | Agent Patterns | Anthropic | Dec 2024 |
| [Batch processing with Message Batches API  Process large volumes of Claude requests asynchronously with 50% cost reduction using batches.  ](https://platform.claude.com/cookbook/misc-batch-processing) | Responses | Alex Albert | Oct 2024 |
| [Text to SQL with Claude  Convert natural language queries to SQL using RAG, chain-of-thought, and self-improvement techniques.  ](https://platform.claude.com/cookbook/capabilities-text-to-sql-guide) | RAG & Retrieval | Mahesh Murag | Sep 2024 |
| [Enhancing RAG with contextual retrieval  Improve RAG accuracy by adding context to chunks before embedding with prompt caching.  ](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide) | RAG & Retrieval | Anthropic | Sep 2024 |
| [Finetuning Claude 3 Haiku on Bedrock  Step-by-step guide to finetuning Claude 3 Haiku on Amazon Bedrock for custom tasks.  ](https://platform.claude.com/cookbook/finetuning-finetuning-on-bedrock) | Fine-Tuning | David Hershey | Aug 2024 |
| [Generate synthetic test data for your prompt template  Generate synthetic test cases to evaluate and improve your Claude prompt templates effectively.  ](https://platform.claude.com/cookbook/misc-generate-test-cases) | Evals | Anthropic | Aug 2024 |
| [Prompt caching through the Claude API  Cache and reuse prompt context for cost savings and faster responses with detailed instructions.  ](https://platform.claude.com/cookbook/misc-prompt-caching) | Responses | Alex Albert | Aug 2024 |
| [Summarization with Claude  Comprehensive guide to summarizing legal documents with evaluation and advanced techniques.  ](https://platform.claude.com/cookbook/capabilities-summarization-guide) | RAG & RetrievalResponses | Alexander Bricken | Aug 2024 |
| [Retrieval augmented generation  Build and optimize RAG systems with Claude using summary indexing and reranking techniques.  ](https://platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide) | RAG & Retrieval | Anthropic | Jul 2024 |
| [Classification with Claude  Build classification systems with Claude using RAG and chain-of-thought for insurance tickets.  ](https://platform.claude.com/cookbook/capabilities-classification-guide) | RAG & Retrieval | Garvan Doyle | May 2024 |
| [Tool choice  Control how Claude selects tools using tool\_choice parameter for forced or auto selection.  ](https://platform.claude.com/cookbook/tool-use-tool-choice) | Tools | Alex Albert | May 2024 |
| [Using vision with tools  Combine Claude's vision with tools to extract structured data from images like nutrition labels.  ](https://platform.claude.com/cookbook/tool-use-vision-with-tools) | MultimodalTools | Alex Albert | May 2024 |
| [Sampling responses from Claude beyond the max tokens limit  Generate longer responses beyond max\_tokens limit using prefill technique with message continuation.  ](https://platform.claude.com/cookbook/misc-sampling-past-max-tokens) | Responses | Anthropic | May 2024 |
| [Best practices for using vision with Claude  Tips and techniques for optimal image processing performance with Claude's vision capabilities.  ](https://platform.claude.com/cookbook/multimodal-best-practices-for-vision) | Multimodal | Alex Albert | May 2024 |
| [Note-saving tool with Pydantic and Anthropic tool use  Create validated tools using Pydantic models for type-safe Claude tool use interactions.  ](https://platform.claude.com/cookbook/tool-use-tool-use-with-pydantic) | Tools | Alex Albert | Apr 2024 |
| [Transcribe an audio file with Deepgram & use Anthropic to prepare interview questions!  Transcribe audio with Deepgram and generate interview questions using Claude for preparation.  ](https://platform.claude.com/cookbook/third-party-deepgram-prerecorded-audio) | IntegrationsMultimodal | john-vajda | Apr 2024 |
| [Using the Wolfram Alpha LLM API as a tool with Claude  Integrate Wolfram Alpha LLM API as Claude tool for computational queries and answers.  ](https://platform.claude.com/cookbook/third-party-wolframalpha-using-llm-api) | IntegrationsTools | Alex Albert | Apr 2024 |
| [Using a calculator tool with Claude  Provide Claude with calculator tool for arithmetic operations and mathematical problem solving.  ](https://platform.claude.com/cookbook/tool-use-calculator-tool) | Tools | Alex Albert | Apr 2024 |
| [Creating a customer service agent with client-side tools  Build customer service chatbot with Claude using tools for customer lookup and order management.  ](https://platform.claude.com/cookbook/tool-use-customer-service-agent) | ToolsAgent Patterns | Alex Albert | Apr 2024 |
| [Extracting structured JSON using Claude and tool use  Extract structured JSON data from various inputs using Claude's tool use capabilities.  ](https://platform.claude.com/cookbook/tool-use-extracting-structured-json) | ResponsesTools | Alex Albert | Apr 2024 |
| [Metaprompt  Prompt engineering tool that generates starting prompts for your tasks to solve blank-page problem.  ](https://platform.claude.com/cookbook/misc-metaprompt) | Responses | Anthropic | Mar 2024 |
| [Citations  Enable Claude to provide detailed source citations when answering document-based questions for verification.  ](https://platform.claude.com/cookbook/misc-using-citations) | ResponsesRAG & Retrieval | Anthropic | Mar 2024 |
| [Claude 3 RAG agents with LangChain v1  Build RAG agents with Claude 3 using LangChain v1's updated agent framework patterns.  ](https://platform.claude.com/cookbook/third-party-pinecone-claude-3-rag-agent) | IntegrationsRAG & RetrievalAgent Patterns | james-briggs | Mar 2024 |
| [Summarizing web page content with Claude 3 Haiku  Fetch and summarize web page content using Claude 3 Haiku via URL extraction.  ](https://platform.claude.com/cookbook/misc-read-web-pages-with-haiku) | RAG & Retrieval | Alex Albert | Mar 2024 |
| [Using Haiku as a sub-agent  Analyze financial reports using Haiku sub-agents for extraction and Opus for synthesis.  ](https://platform.claude.com/cookbook/multimodal-using-sub-agents) | Agent Patterns | Alex Albert | Mar 2024 |
| [Multi-modal  Use LlamaIndex's Anthropic MultiModal LLM abstraction for image understanding and reasoning.  ](https://platform.claude.com/cookbook/third-party-llamaindex-multi-modal) | IntegrationsMultimodal | Ravi Theja | Mar 2024 |
| [How to build a RAG system using Claude 3 and MongoDB  Build chatbot RAG system with Claude and MongoDB using tech news as knowledge base.  ](https://platform.claude.com/cookbook/third-party-mongodb-rag-using-mongodb) | IntegrationsRAG & Retrieval | Richmond Alake | Mar 2024 |
| [Building evals  Build robust evaluation systems to measure and improve Claude's performance on key metrics.  ](https://platform.claude.com/cookbook/misc-building-evals) | Evals | Alex Albert | Mar 2024 |
| [Building a moderation filter with Claude  Build customizable content moderation filters by defining rules and categories in prompts.  ](https://platform.claude.com/cookbook/misc-building-moderation-filter) | Responses | Alex Albert | Mar 2024 |
| [Prompting Claude for "JSON mode"  Get reliable JSON output from Claude using effective prompting techniques without constrained sampling.  ](https://platform.claude.com/cookbook/misc-how-to-enable-json-mode) | Responses | Alex Albert | Mar 2024 |
| [How to make SQL queries with Claude  Generate SQL queries from natural language questions using Claude with database schema context.  ](https://platform.claude.com/cookbook/misc-how-to-make-sql-queries) | RAG & Retrieval | Alex Albert | Mar 2024 |
| [Getting started - how to pass images into Claude  Tutorial on passing images to Claude 3 API for vision-based text analysis.  ](https://platform.claude.com/cookbook/multimodal-getting-started-with-vision) | Multimodal | Alex Albert | Mar 2024 |
| [How to transcribe documents with Claude  Extract and structure unstructured text from images and PDFs using Claude 3's vision.  ](https://platform.claude.com/cookbook/multimodal-how-to-transcribe-text) | Multimodal | Alex Albert | Mar 2024 |
| [Working with charts, graphs, and slide decks  Extract insights from charts, graphs, and presentations using Claude's vision analysis capabilities.  ](https://platform.claude.com/cookbook/multimodal-reading-charts-graphs-powerpoints) | Multimodal | Alex Albert | Mar 2024 |
| [Multi-document agents  Build RAG for large document collections using DocumentAgents with ReAct Agent pattern.  ](https://platform.claude.com/cookbook/third-party-llamaindex-multi-document-agents) | IntegrationsRAG & RetrievalAgent Patterns | Ravi Theja | Mar 2024 |
| [ReAct agent  Create ReAct agents with LlamaIndex for tool-based reasoning and action workflows.  ](https://platform.claude.com/cookbook/third-party-llamaindex-react-agent) | IntegrationsAgent PatternsTools | Ravi Theja | Mar 2024 |
| [RAG pipeline with LlamaIndex  Build basic RAG pipeline with LlamaIndex for document retrieval and question answering.  ](https://platform.claude.com/cookbook/third-party-llamaindex-basic-rag-with-llamaindex) | IntegrationsRAG & Retrieval | Ravi Theja | Mar 2024 |
| [RouterQuery engine  Route queries to different indices using LlamaIndex RouterQueryEngine for multi-document search.  ](https://platform.claude.com/cookbook/third-party-llamaindex-router-query-engine) | IntegrationsRAG & Retrieval | Ravi Theja | Mar 2024 |
| [SubQuestionQueryEngine  Decompose complex queries into sub-questions across multiple documents using LlamaIndex engine.  ](https://platform.claude.com/cookbook/third-party-llamaindex-subquestion-query-engine) | IntegrationsRAG & Retrieval | Ravi Theja | Mar 2024 |
| [Retrieval-augmented generation using Pinecone  Connect Claude with Pinecone vector database for retrieval-augmented generation and semantic search.  ](https://platform.claude.com/cookbook/third-party-pinecone-rag-using-pinecone) | IntegrationsRAG & Retrieval | Alex Albert | Feb 2024 |
| ["Uploading" PDFs to Claude via the API  Process and summarize PDF documents using Claude API with text extraction and encoding.  ](https://platform.claude.com/cookbook/misc-pdf-upload-summarization) | RAG & Retrieval | Anthropic | Aug 2023 |
| [Iteratively searching Wikipedia with Claude  Legacy notebook showing iterative Wikipedia searches with Claude 2 for research workflows.  ](https://platform.claude.com/cookbook/third-party-wikipedia-wikipedia-search-cookbook) | Integrations | Anthropic | Aug 2023 |

### Contributions welcome

Have an idea for a cookbook? We welcome community contributions.

[Contribution guide](https://github.com/anthropics/claude-cookbooks/blob/main/CONTRIBUTING.md)
