---
title: "Engineering AI Agents"
source: "https://cs329z.stanford.edu/"
author:
published:
created: 2026-09-16
description: "Official course website for Stanford CS329Z: Engineering AI Agents — schedule, deadlines, coursework, project, and logistics."
tags:
  - "clippings"
---

> [!summary]
> Course site for Stanford CS329Z (Autumn 2026), on engineering compound AI systems and agents: RAG, tool use and MCP, agent loops, memory architectures, multi-agent orchestration, prompt/weight optimization (DSPy, GEPA), evaluation, and safety. Students build each component from scratch before seeing how frameworks abstract it, across two applied homeworks and a quarter-long project. Includes the full week-by-week schedule with per-lecture paper readings, deadlines, and the grading breakdown.

## Instructors

## Welcome!

The shift from monolithic language models to **compound AI systems** — systems with multiple interacting components including LLMs, retrievers, tools, and optimizers — represents a fundamental change in how AI applications are built for people. This course teaches students how to engineer agentic systems: the full spectrum from simple LLM pipelines to compound AI systems to autonomous agents. Students will learn to pick what types of problems to focus on, decompose problems, select appropriate components, collect and curate data, build evaluations, and reason about the design tradeoffs that arise when building these systems in practice.

Students first build core components (RAG, tool use, agent loops) from scratch, then learn how frameworks like DSPy abstract these patterns. Through two fully applied homework assignments and a quarter-long project, students gain hands-on experience building, optimizing, and evaluating agentic systems.

## Class Schedule

Note: the schedule is tentative and subject to change. Classes meet Mondays and Wednesdays, 1:30–2:50 p.m., in Packard 101. Lecture materials will be linked here as they are released.

| Week | Date | Lecture | Course Material |
| --- | --- | --- | --- |
| 1 | Wed Sep 23 | Foundations & Landscape Introduction — What Are Agentic Systems? The spectrum from monolithic models to compound AI systems to agents; when compound systems win; the three engineering challenges (decomposition, data, evaluation); course logistics. | **Readings**: - [Zaharia et al. "The Shift from Models to Compound AI Systems." BAIR Blog (2024).](https://bair.berkeley.edu/blog/2024/02/18/compound-ai-systems/) |
| 2 | Mon Sep 28 | LLMs for Builders APIs & SDKs (litellm), structured I/O and constrained generation, decoding strategies and test-time compute, context engineering, model selection, and cost/latency tradeoffs. | **Readings**: - [Schluntz & Zhang. "Building Effective Agents." Anthropic (2024).](https://www.anthropic.com/engineering/building-effective-agents) |
| 2 | Wed Sep 30 | Building Blocks Retrieval-Augmented Generation (RAG) Grounding and hallucination, embeddings and vector stores, chunking strategies, hybrid search, cross-encoders and late interaction (ColBERT). Hands-on: build a RAG pipeline from scratch. | **Readings**: - [Lewis et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS (2020).](https://arxiv.org/abs/2005.11401) |
| 3 | Mon Oct 5 | Tool Use & Function Calling The REPL, function-calling APIs, the Model Context Protocol (MCP), designing good tools, code-execution sandboxes, error handling and retries. Hands-on: build a tool-using system from scratch. | **Readings**: - [Model Context Protocol Specification. The Linux Foundation (2025).](https://modelcontextprotocol.io/specification/2025-06-18) |
| 3 | Wed Oct 7 | Frameworks & Agent Design Frameworks & Orchestration DSPy (signatures, modules, optimizers), LangChain/LangGraph, LlamaIndex; what frameworks abstract vs. what you built from scratch; choosing the right level of abstraction. | **Readings**: - [Khattab et al. "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines." ICLR (2024).](https://arxiv.org/abs/2310.03714) |
| 4 | Mon Oct 12 | Agent Design Patterns & Scaffolds The workflows-vs-agents taxonomy, five composable workflow patterns, agent patterns (ReAct, plan-and-execute, reflection), and scaffolds as design decisions. | **Readings**: - [Yao et al. "ReAct: Synergizing Reasoning and Acting in Language Models." ICLR (2023).](https://arxiv.org/abs/2210.03629) |
| 4 | Wed Oct 14 | Memory & Multi-Agent Systems Agent Memory Architectures Short- vs. long-term memory, memory as tool-based actions, the file system as externalized memory, structured memory paradigms, and cross-agent memory. | **Readings**: - [Packer et al. "MemGPT: Towards LLMs as Operating Systems." arXiv (2023).](https://arxiv.org/abs/2310.08560) |
| 5 | Mon Oct 19 | Multi-Agent Systems Single vs. multi-agent architectures, orchestration patterns, handoffs and state transfer, delegation and collaboration patterns, and the challenges of coordination and error propagation. | **Readings**: - [Wu et al. "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation." COLM (2024).](https://arxiv.org/abs/2308.08155) |
| 5 | Wed Oct 21 | Optimization Optimization The landscape from prompts to fine-tuning; prompt optimization (GEPA, MIPROv2, OPRO, TextGrad); test-time compute scaling; LoRA/QLoRA; distillation; RLHF/DPO at a high level; and when to optimize prompts vs. weights vs. inference compute. | **Readings**: - [Snell et al. "Scaling LLM Test-Time Compute Optimally…" ICLR (2025).](https://arxiv.org/abs/2408.03314) - [Agrawal et al. "GEPA: Reflective Prompt Evolution Can Outperform RL." arXiv (2026).](https://arxiv.org/abs/2507.19457) |
| 6 | Mon Oct 26 | 📺 Guest Lecture (TBA) |  |
| 6 | Wed Oct 28 | Data for Agentic Systems What Data Do Agents Need? Traces, demonstrations, and feedback; data for optimization vs. evaluation; data flywheels; synthetic data generation; collecting data from human-agent interaction. | **Readings**: - [Shankar. "Data Flywheels for LLM Applications." (2024).](https://www.sh-reya.com/blog/ai-engineering-flywheel/) |
| 7 | Mon Nov 2 | Data Selection & Quality Finding maximally informative data, filtering and selection strategies, tiny-but-targeted benchmarks, annotation practices, quality assessment, and building datasets from agent traces. | **Readings**: - [Yang et al. "SWE-smith: Scaling Data for Software Engineering Agents." NeurIPS D&B (2025).](https://arxiv.org/abs/2504.21798) - [Shankar et al. "Who Validates the Validators? Aligning LLM-Assisted Evaluation with Human Preferences." UIST (2024).](https://arxiv.org/abs/2404.12272) |
| 7 | Wed Nov 4 | Evaluation for Agentic Systems Evaluation Fundamentals & Benchmark Design Why evals are hard, the 4-tuple framework (request, environment, stopping criteria, scorer), designing each component, properties of good benchmarks, realistic scaffolding, and reliability dimensions. | **Readings**: - [Zhu et al. "Establishing Best Practices for Building Rigorous Agentic Benchmarks." (2025).](https://arxiv.org/abs/2507.02825) |
| 8 | Mon Nov 9 | LLM-as-Judge & Evaluation Infrastructure The three grader types, designing judge prompts, known biases, pairwise vs. pointwise evaluation, non-determinism metrics (pass@k vs. pass^k), harness design, and Anthropic's 8-step roadmap. | **Readings**: - [Grace et al. "Demystifying Evals for AI Agents." Anthropic (2026).](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) - [Zheng et al. "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." NeurIPS (2023).](https://arxiv.org/abs/2306.05685) - [Ryan et al. "AutoMetrics: Approximate Human Judgements with Automatically Generated Evaluators." ICLR (2026).](https://arxiv.org/abs/2512.17267) |
| 8 | Wed Nov 11 | Safety Agent Safety & Guardrails Privacy risks of tool access, prompt injection (including indirect injection), red-teaming, sandboxing and permission models, output guardrails, liability considerations, responsible deployment, and human-in-the-loop patterns. | **Readings**: - [Shao et al. "PrivacyLens: Evaluating Privacy Norm Awareness of LMs in Action." NeurIPS D&B (2024).](https://arxiv.org/abs/2409.00138) - [Zhang & Yang. "Searching for Privacy Risks in LLM Agents via Simulation." arXiv (2025).](https://arxiv.org/abs/2508.10880) - [Li. "Agentic LLMs as Powerful Deanonymizers." arXiv (2026).](https://arxiv.org/abs/2601.05918) |
| 9 | Mon Nov 16 | 📺 Guest Lecture (TBA) |  |
| 9 | Wed Nov 18 | Coding Agents & Proactive Agents Coding & Software Agents How coding agents work end-to-end; SWE-agent, Claude Code, and OpenHands architectures; scaffolds as design decisions; SWE-bench and the 4-tuple framework in practice; the future of software development with agents. | **Readings**: - [Yang et al. "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering." NeurIPS (2024).](https://arxiv.org/abs/2405.15793) - [Wang et al. "OpenHands: An Open Platform for AI Software Developers." ICLR (2025).](https://arxiv.org/abs/2407.16741) |
| 10 | Mon Nov 23 | No Class — Thanksgiving Recess |  |
| 10 | Wed Nov 25 | No Class — Thanksgiving Recess |  |
| 11 | Mon Nov 30 | Proactive Agents From reactive to proactive; General User Models (GUM); Next Action Prediction; open-source proactive personal agents; privacy and trust implications; and when agents should initiate vs. wait (mixed initiative). | **Readings**: - [Shaikh et al. "Creating General User Models from Computer Use." UIST (2025).](https://arxiv.org/abs/2505.10831) |
| 11 | Wed Dec 2 | Open Problems & Final Demos Frontiers & Open Problems Multimodal agents, web agents and computer use, science agents, long-running agent architectures, production and observability (tracing, monitoring, cost management), and open problems in reliability, scalability, and interpretability. |  |
| — | Finals Week (Dec 7–11) | Final Project Demo Day Held during the end-quarter examination period; exact time and location TBA. |  |

## Deadlines

All times are Pacific. Deadlines are subject to change; any changes will be announced in class and posted here.

| Week | Deadline | Date | Time |
| --- | --- | --- | --- |
| 3 | HW1 Released | Mon Oct 5 | — |
| 3 | Project Proposal Due | Fri Oct 9 | 11:59 p.m. |
| 6 | HW2 Released | Mon Oct 26 | — |
| 6 | HW1 Due | Fri Oct 30 | 11:59 p.m. |
| 7 | Midpoint Demo | Wed Nov 4 | In class |
| 7 | Midway Report Due | Fri Nov 6 | 11:59 p.m. |
| 8 | Paper Video Due (10 min) | Fri Nov 13 | 11:59 p.m. |
| 9 | HW2 Due | Fri Nov 20 | 11:59 p.m. |
| 11 | Peer Reviews Due (3 videos) | Mon Nov 30 | 11:59 p.m. |
| Finals | Final Submission & Final System Demo | Dec 7–11 | TBA |

## Coursework

Two fully applied homework assignments build on the components covered in lecture. Each homework is followed by a **10-minute HW-based quiz** where students explain their design decisions and tradeoffs and demonstrate understanding.

- **HW1: Build an Agentic Harness** (Weeks 3–6). Build a company's internal AI assistant from scratch, with no agent frameworks: just a chat-completion call and code you write yourself. Start with LLM pipelines that retrieve and reason over a real corporate email archive, then grow them into a full agent harness with tools, a terminal, memory, and a human in the loop.
- **HW2: Evaluate an Agent** (Weeks 6–9). Given a pre-built agent, design a comprehensive evaluation suite with code-based graders, at least one LLM-as-judge eval, benchmark tasks built with the 4-tuple framework (request, environment, stopping criteria, scorer), and error analysis.

### Paper Video & Peer Reviews

Each student records a **10-minute video** about a recent agent paper of their choosing (due Week 8), then watches and reviews **three** videos from other students (due after Thanksgiving).

- **Video (7%).** 2% selection of a substantive recent paper and a solid explanation of it; 2% your own critique or insight — what you agree/disagree with, limitations, or an interesting question it raises; 2% added value, e.g. reproduce a result, run a small experiment, compare with another method, demo an implementation, or connect it to a real agent; 1% clear and engaging presentation.
- **Peer reviews (3%).** 1% each for specific, thoughtful feedback that goes beyond "good presentation" — identify one strength, one weakness or question, and one concrete suggestion.

### Grading

- **Project \[50%\]**
	- Proposal \[5%\]
		- Midway report \[5%\]
		- Midpoint demo \[7%\]
		- Final submission \[15%\]
		- Final system demo \[18%\]
- **Homework \[20%\]**
	- HW1: Build an Agentic Harness \[10%\]
		- HW2: Evaluate an Agent \[10%\]
- **HW-based quizzes \[15%\]**
	- Quiz 1 (after HW1) \[7.5%\]
		- Quiz 2 (after HW2) \[7.5%\]
- **Paper video & peer reviews \[10%\]**
	- Paper video \[7%\]
		- Peer reviews (3 × 1%) \[3%\]
- **Participation \[5%\]**
	- In-class discussion, project teamwork, and recitations

## Course Project

Students work in groups on a quarter-long project on the theme **"Making Life at Stanford Better with Agents."** The goal is to build an agentic system that helps with some aspect of Stanford life. Example project ideas:

- A syllabus reader that extracts deadlines and adds them to your calendar
- A course-schedule optimizer for next quarter
- A research-paper discovery and summarization agent
- A campus-event aggregator and recommender

### Milestones

- **Week 3:** Project proposal (1-page)
- **Week 6:** Midway report (1-page) + midpoint demo — a working prototype is expected
- **Week 10:** Final submission (1-page) + final system demo (Demo Day)

Reports are brief (1–2 pages of writing, with an appendix for required structured content such as examples of your agent's failure modes).

## Logistics

### Course Info

- **Units:** 3
- **Class number:** 27855
- **Grading:** Letter or Credit/No Credit
- **Session:** 2026–2027 Autumn 1
- **Meeting time:** Mondays and Wednesdays, 1:30–2:50 p.m.
- **Location:** Packard 101
- **Contact:** [cs329z-staff@lists.stanford.edu](mailto:cs329z-staff@lists.stanford.edu)

### Office Hours

- TBA — posted here and in the course forum before the first week of class.

### Prerequisites

- **Any of [CS224N](https://web.stanford.edu/class/cs224n/), [CS224U](https://web.stanford.edu/class/cs224u/), [CS224V](https://web.stanford.edu/class/cs224v/), [CS336](https://stanford-cs336.github.io/), or equivalent background in natural language processing.**

### Honor Code & AI Tools

Like every class at Stanford, we take the [Honor Code](https://ed.stanford.edu/academics/masters-handbook/honor-code) seriously. Write your own solutions, and don't look up solutions or existing implementations of the assignments online. We sometimes use automated methods to detect overly similar submissions.

This is a course about building with AI, so we expect you to use it. Treat generative AI tools as collaborators you think alongside — asking them to explain a concept, debug your code, or critique a design is fair game and encouraged. What isn't: soliciting finished answers or copying solutions, whether from a model, a classmate, or the web. Using AI tools to substantially complete an assignment is an Honor Code violation. HW-based quizzes are individual and closed-book. When in doubt, ask us; see Stanford's [Generative AI Policy Guidance](https://communitystandards.stanford.edu/policies-guidance/bca-guidance-recommendations#generative-ai-policy-guidance) for the university-wide baseline.

### Lecture Recordings

Video cameras located in the back of the room will capture the instructor presentations in this course. For your convenience, you can access these recordings by logging into the course Canvas site. These recordings might be reused in other Stanford courses, viewed by other Stanford students, faculty, or staff, or used for other education and research purposes. Note that while the cameras are positioned with the intention of recording only the instructor, occasionally a part of your image or voice might be incidentally captured. If you have questions, please contact a member of the teaching team.

### Academic Accommodations

From [Stanford's Office of Accessible Education](https://oae.stanford.edu/faculty-teaching-staff/syllabus-statement): Students who may need an academic accommodation based on the impact of a disability must initiate the request with the Office of Accessible Education (OAE). Professional staff will evaluate the request with required documentation, recommend reasonable accommodations, and prepare an Accommodation Letter for faculty dated in the current quarter in which the request is being made. Students should contact the OAE as soon as possible since timely notice is needed to coordinate accommodations.

If you already have an Academic Accommodation Letter, we invite you to share your letter with us. Letters should be shared at the earliest possible opportunity so we may partner with you and the OAE to identify any barriers to access and inclusion.

### Well-Being, Stress Management, & Mental Health

If you are experiencing personal, academic, or relationship problems and would like someone to talk to, reach out to Counseling and Psychological Services (CAPS) on campus. CAPS is the university's counseling center dedicated to student mental health and wellbeing. Phone assessment appointments can be made at CAPS by calling 650-723-3785, or by accessing the Vaden Patient portal. For more information, visit [vaden.stanford.edu/caps-and-wellness](https://vaden.stanford.edu/caps-and-wellness).
