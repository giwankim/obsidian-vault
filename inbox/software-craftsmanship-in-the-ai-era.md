---
title: "Software Craftsmanship in the AI Era"
source: "https://www.codurance.com/publications/software-craftsmanship-in-the-ai-era"
author:
  - "[[Sandro Mancuso]]"
  - "[[Co-founder and Group CEO]]"
  - "[[Matt Belcher]]"
published: 2026-02-09
created: 2026-02-12
description: "Explore how AI tools are transforming software development and the importance of maintaining Software Craftsmanship for quality and maintainability."
tags:
  - "clippings"
---
Prefer listening over reading? Press play and enjoy

Software Craftsmanship in the AI Era

24:44

<audio xmlns="http://www.w3.org/1999/xhtml" src="https://www.codurance.com/hubfs/AI-Generated%20Media/Post%20Narration%20Audio/207043618688-TTS-1770397736657.mp3"></audio>

## AI is Changing How We Code

AI coding tools are completely changing the software development landscape. Developers now rely on tools like GitHub Copilot, Amazon CodeWhisperer, and ChatGPT to generate code, fix bugs, scaffold tests, and accelerate routine tasks. Code that once took hours can now be produced in minutes; sometimes seconds. Prompting is quickly becoming a core developer skill.

**AI is here to stay**. The promise is undeniable: **higher output, faster delivery, and fewer repetitive tasks**. But with this leap in speed, a deeper question emerges:

**Are we building well - or just fast?**

This article explores that question through the lens of Software Craftsmanship, offering a pragmatic perspective on how to embrace AI without sacrificing the principles that make great software possible.

## 1\. Productivity is More Than Fast Code Generation

True productivity in software isn’t about how many lines of code are produced, or how quickly they’re typed. It's about how effectively developers **solve meaningful problems**, ensure their solutions are correct, and leave the codebase in a better state than they found it.

Productivity is the ability to **consistently deliver valuable, maintainable software** with minimal friction, rework, or risk. That requires far more than rapid output. It demands **clarity, correctness, and changeability**.

AI gives us a powerful new engine. But productivity still requires a steering wheel. When speed is mistaken for progress, teams end up shipping more low-quality code, creating more rework, and compounding long-term risks.

In fact, many teams are now experiencing a paradox:

*Features are delivered faster…**...but bugs, regressions, and entropy increase.*

This isn't because AI is bad at coding. It’s because **code quality, modularity, testability, and team knowledge** are systemic factors that AI doesn't automatically account for.

And that's the real point:

*Software productivity is a property of the system, not of the speed of an individual developer.*

Generating code faster doesn’t necessarily reduce delivery time, maintenance effort, or rework. If the generated code is misaligned with business intent or poorly designed, it can increase downstream costs. Speed is productive only when it supports clarity, correctness, and adaptability.

When paired with strong engineering principles, AI can amplify not just speed but also effectiveness, helping teams deliver better software, faster.

## 2\. Where is Time Really Spent?

When people talk about productivity in software development, they often think of it in terms of how fast developers can write code. But research and real-world experience suggest a very different picture.

According to a 2019 study by Microsoft Research titled " [Today was a Good Day: The Daily Life of Software Developers](https://www.microsoft.com/en-us/research/wp-content/uploads/2019/04/devtime-preprint-TSE19.pdf) " and based on analyses of other cited studies, it's safe to estimate that less than **25% of a developer’s time is spent editing source code**. The majority is spent on activities such as reading code, navigating through the codebase, understanding system behaviour, meetings, refining requirements, etc. While AI can also help with these tasks, it doesn't replace the intimate understanding of the internal structure required to truly understand the design, intent, and complexity of the codebase.

This tells a clear story: the bottleneck in software development isn’t how fast code can be typed, but it’s how quickly a developer can understand what needs to change and where.

And here’s where things get complicated.

Even with AI accelerating code generation, developers still need to **navigate and reason about the existing system**. But when that system is messy, with poor modular boundaries, inconsistent naming, duplicated logic, or missing tests, the cost of understanding rises significantly.

AI doesn’t remove that cost. In many cases, it amplifies it.

**The problem isn’t how fast we can write new code, it’s how fast we can safely change and understand the code we already have.**

What makes this understanding difficult?

- **Poor modularisation**: When code is scattered across poorly defined or overlapping domains, developers have to trace logic across multiple files or services to understand behaviour.
- **Inconsistent or vague naming**: Bad names at any level (packages, classes, functions, variables) increase the mental load required to decipher what code does.
- **High complexity**: Deeply nested logic, long methods, or tangled conditionals increase both **cyclomatic** and **cognitive** complexity, making the code harder to read and change safely.
- **Lack of test coverage**: Without meaningful, up-to-date tests, it’s difficult to understand the intended behaviour or to know whether a change will break something.
- **Verbose or poor-quality tests**: Ironically, bad tests can be worse than no tests; they introduce noise and false confidence, rather than clarity and safety.
- **Duplication**: Copy-pasted logic spread across the codebase requires multiple changes to fix a single issue, increasing the risk of regression and wasted effort.

These issues compound when multiple developers, potentially using AI tools, are generating code at high speed without improving the underlying structure. More code doesn't equate to more value if the surrounding system is becoming harder to understand and to evolve. These are not just code hygiene issues. They’re **systemic blockers of productivity**. And if they’re not addressed, no amount of AI acceleration will help. In fact, it’ll likely just bury teams in more code they don’t fully understand.

In this context, **Software Craftsmanship practices like modular design, naming discipline, and clean code principles are not luxuries but time-saving mechanisms.** They reduce the cognitive friction developers experience every day and increase the ROI of every minute spent navigating or modifying a codebase.

Typing is not where most developers spend their time. Instead, it’s spent reading, understanding, fixing, clarifying, and adapting code. The harder the code is to read and reason about, the longer it takes to build anything new. Accelerating generation without improving the structure only makes future work slower and riskier.

**AI can dramatically reduce effort** but only when it helps clarify and simplify, not obscure. Craftsmanship ensures that acceleration doesn’t come at the cost of comprehension.

## 3\. From Imprecise Language to Precise Code

Programming is one of the most precise forms of communication humans engage in. Unlike natural language, where ambiguity, metaphor, and nuance are expected, source code must be explicit, unambiguous, and logically consistent. Every character matters. That’s why the transition from human intent to working software has always been challenging and it's also where generative AI faces its greatest friction.

Large Language Models (LLMs) such as Copilot and ChatGPT are designed to predict and generate plausible text sequences, including code. However, the inputs they receive - our prompts, are written in the same imprecise, incomplete natural language we use in conversation. Even when a developer has a clear goal, the prompt they write often lacks context, clarity, or precision. And worse, the AI may be drawing from a codebase that’s already poorly structured.

So we now have a situation where:

- **Developers write vague prompts** based on an incomplete understanding of the code or system.
- **AI-generated code can be** influenced by poor-quality patterns in the surrounding codebase or public training data.
- **The generated code is accepted and merged**, sometimes without a clear understanding of what it does or whether it introduces inconsistencies, technical debt, or subtle bugs.

This feedback loop can rapidly degrade system quality, particularly when codebases lack strong semantic structure, as demonstrated by a [Stanford University study](https://www.youtube.com/watch?v=JvosMkuNxF8). A poorly modularised system with weak domain boundaries, unclear naming, and inconsistent architectural patterns provides little guidance to an LLM. The AI has no business context, and its only reference is the code that came before, which may itself be a patchwork of inconsistent practices.

Without solid foundations in software design and modularisation, AI tools tend to **amplify existing flaws** in the codebase. For example:

- A bloated class gets even bigger.
- A poorly named method is copied and modified elsewhere.
- A missing abstraction remains missing, repeatedly duplicated across different files.

In this scenario, **Software Craftsmanship becomes even more important**, not less. Well-modularised, well-named, and well-tested code doesn’t just help humans navigate the system, it gives AI tools better patterns to work with, as demonstrated by the same [Stanford University study](https://www.youtube.com/watch?v=JvosMkuNxF8). Prompting a change within a cleanly defined module with good test coverage is far more likely to produce correct, maintainable code.

LLMs operate in a grey zone between fuzzy language and deterministic code. If the base code is poor and the prompts are vague, even the most powerful models will generate subpar solutions. Bad code tends to propagate more bad code.

**Craftsmanship brings the precision AI needs.** If AI is the power tool, then Software Craftsmanship is the blueprint. Without the latter, we’re just generating code faster, not better.

## 4\. Speeding up Knowledge Loss

One often-overlooked consequence of generative AI in software development is **the acceleration of knowledge loss**.

Traditionally, when a developer wrote a piece of code, they spent time thinking through the logic, making design choices, naming things, and understanding how it fit within the system. This process, though sometimes slow, helped developers internalise the business rules, technical constraints, and trade-offs behind the code they were writing.

But when AI generates that code in seconds, **the developer becomes a passive editor, not an active author**. The mental model and the deep understanding that comes from wrestling with a problem, is often missing.

In one of our recent coaching engagements, a developer submitted a large pull request with changes to dozens of files. When asked to explain the business logic behind the update or how specific edge cases were handled, the response was startling: “I’m not sure. I’d have to look at the code again.” Yet they had just "written" it. In reality, the AI had generated most of the changes, and the developer had merely prompted, copied, pasted, and lightly edited.

This isn’t an isolated case. We’re seeing a growing pattern:

- **Developers can no longer explain their own code**.
- **Codebases grow faster than teams can understand them**.
- **Knowledge is not transferred, it's outsourced to the tool**.

Even worse, this isn't just happening at the individual level. In modern organisations, systems are often large and distributed, built by **multiple developers, working in parallel**, often across **multiple microservices**. Each developer brings a different understanding of the system, of the domain, and of good design practices. Their prompts vary. Their context differs. And the only thing the AI has to go by is the codebase, which might already be inconsistent or poorly structured.

The result? A mess of overlapping logic, duplicated effort, diverging implementations, and **semantic drift** across services. A single AI-generated change, if not carefully reviewed and understood, can introduce subtle inconsistencies that ripple across the system. As these accumulate, teams spend more time reverse-engineering the intent behind code they never fully **understood in the first place**.

**Software Craftsmanship** offers a counterbalance. It values shared understanding, semantic clarity, and intentional design. In an ever-increasingly fast-paced world, these principles **protect long-term maintainability and developer effectiveness**. Without them, we’re building systems we don’t fully understand, at a speed we can’t keep up with.

When developers generate large volumes of code without understanding it, or without discussing design intent, team-wide knowledge erodes. Code becomes a black box, even to those who “wrote” it. Over time, systems evolve in unpredictable and risky ways.

**Craftsmanship helps teams stay close to the code, ensuring that AI accelerates delivery without disconnecting developers from what’s being built.**

## 5\. Size of Changes and Review Discipline

***"Over-dependence on AI assistance could erode core engineering competencies"***

Code review has always been one of the most important quality gates and knowledge-sharing activities in a professional software development process. A good review catches design flaws, bugs, and misunderstandings before they reach production. But for reviews to be effective, the changes under review must be **understandable**, **contextual**, and, critically, **small enough to reason about**.

AI-generated code is disrupting this balance.

Developers, empowered by fast, powerful assistants, can now make sweeping changes across dozens of files in minutes. What once might have taken days of careful thought, design, and iteration can now be generated by a few prompts and pasted into the codebase. The speed is intoxicating but it comes with serious downsides:

- **The size of pull requests is growing** dramatically.
- **The complexity of changes is increasing**, often with inconsistent design decisions across the modified files.
- **Reviewers are overwhelmed** and unable to meaningfully assess what changed and why.

The natural response to a massive pull request? Skimming, or worse, rubber-stamping.

And when reviews become superficial, **quality declines**. Bugs slip through. Inconsistencies grow. Design debt piles up. Worse still, the opportunity for shared learning disappears. Code review isn't just about approval; it's about **building shared understanding** within the team.

This isn’t just an AI problem; large, unreviewable pull requests have always been an anti-pattern. But the rapid code-generation capabilities of modern tools have exacerbated the issue. It’s now easier than ever to bypass healthy development discipline in the name of speed.

Software Craftsmanship calls for a different approach:

- **Frequent, small, well-scoped commits**.
- **Intentional design choices**, not just functional outputs.
- **Meaningful reviews**, where both the author and the reviewer learn and improve together.
- **Pair-Programming**, where knowledge-sharing and better naming and design decisions are a direct byproduct, minimises the need for formal code reviews.

AI can assist in this process, generating boilerplate, suggesting improvements, and accelerating menial tasks, but only if we maintain control over **the pace and scale of change**. Otherwise, we risk turning development into a fast-moving conveyor belt of unreviewed code, where the cost of each mistake is only revealed months down the line.

AI makes large, sweeping changes easy. But reviewing and validating those changes, especially when they span multiple files or services, becomes more difficult. When reviews are superficial or skipped entirely, code quality suffers, and bugs slip through.

**Used thoughtfully, AI can still support small, meaningful changes. Developers can prompt in small steps, keeping reviewability and modularity intact.**

***Note:*** *We are now evaluating AI code review tools to review PRs against our own code and design quality guidelines. Initial tests are very promising. More on that in a future post.*

## 6\. The Loss of Semantics

In software development, structure is *meaning*.

We rely on **semantic modularisation** \- clear architectural boundaries, meaningful naming, and well-defined responsibilities to make systems understandable and maintainable. When a codebase is semantically structured, developers can quickly answer critical questions:

*What does this module do? What business domain does it represent? Where should this change go?*

Unfortunately, most codebases are already far from ideal. Semantic boundaries (or bounded contexts, if you prefer the *Domain Driven Design (DDD)* terminology) are blurry or non-existent. Business logic is scattered across layers and services. Naming is inconsistent or generic. Modularisation decisions, if they existed at all, are buried under years of technical debt.

And now, AI tools are learning and building on top of this mess.

Without a solid semantic foundation, even the most powerful AI assistant struggles to generate high-quality solutions. Instead, it reinforces existing inconsistencies, introduces additional duplication, and expands already oversized classes and methods. Each new change chips away at clarity.

Semantic deterioration **accelerates over time**:

- AI-generated changes are based on **the available context,** often a poorly structured codebase.
- Different developers provide **different prompts**, based on their own mental models.
- AI-generated code across services or repositories introduces **naming collisions, duplicated logic, and divergent implementations,** a form of **semantic drift** that makes large systems harder to evolve cohesively.**”**

What emerges is a system that technically works, but is conceptually incoherent; a patchwork of ideas, styles, and assumptions. Understanding it becomes more difficult with each new line added.

**Craftsmanship**, on the other hand, places semantics at the core:

- Code should **express intent**.
- Modules should reflect **business capabilities and change boundaries**.
- Names should reveal purpose, not just implementation.

When we lose semantics, we lose the very things that make change safe, fast, and cost-effective. **AI can help here**, but only when guided by developers who understand semantic boundaries and can prompt with intent. Combining AI’s speed with the design awareness of Software Craftsmanship can help teams preserve meaning and structure at scale.

## 7\. Rethinking Testing with AI: From Verification to Design Partner

One of the most powerful practices in Software Craftsmanship is **Test-Driven Development (TDD)**, not only for ensuring correctness but also for guiding design. Starting with a test helps developers clarify expectations, break down complex behaviours, and produce cleaner, more modular code. Good tests act as both documentation and design feedback.

TDD is not just about correctness,it's about writing better code.

AI is changing how we write code and, with it, how we write tests. Many developers now generate production code first and then ask AI to create tests afterwards. While convenient, this reverses the flow of intent. Instead of tests defining behaviour, they become a rubber stamp for whatever the code currently does, even if it’s wrong, inefficient, or misaligned with business goals.

This flips testing on its head:

- **Tests conform to code**, rather than code conforming to tests.
- Bugs and design flaws become *cemented* in place, with tests reinforcing the problem rather than preventing it.
- Test coverage might look impressive, but the value those tests provide is often low.
- When tests break, developers ask the AI to fix them, often without understanding the underlying problem.

We're increasingly seeing test suites filled with:

- Weak or redundant assertions
- Loads of duplicated test setup and assertions for small behaviour variations
- Tests that don’t clarify intent or edge cases
- Verbose code that’s difficult to read or maintain

That said, **AI can be a powerful ally** in testing when properly guided. Developers can use a TDD mindset to prompt AI in a more structured way. Rather than asking for “code that does X,” they can provide the overall context to the AI and then work in small steps, describing for each step the behaviour they expect a specific module to exhibit, the constraints involved, and relevant design guidelines. Developers can even be very precise in the names of classes, methods, parameters and return types they expect. They can then describe the different scenarios (test variations) they want for that behaviour, ranging from a sunny-day scenario to a list of edge cases. They can also ask AI to check if they are missing any test scenarios or if there are vulnerabilities in their design. Even if the AI generates code first, the thinking behind TDD still helps frame better prompts, better designs, and more useful tests.

Some teams even ask AI to write the test first, or help refine an existing one, before coding begins. While this approach is still evolving, it points to a valuable future: AI as a design *partner*, not just a code generator.

In the end, **testing isn’t just about validating correctness, it’s about protecting quality**. The more we embrace AI as a tool that augments human judgment, the more we can preserve the essence of Craftsmanship, even as we build faster and at greater scale than ever before.

## 8\. How Software Craftsmanship Helps

AI is revolutionising how we write code, but without guidance, it may erode the very qualities that make software valuable.

That’s where Software Craftsmanship comes in.

Craftsmanship is not about resisting change or romanticising the past. It’s about upholding timeless principles that ensure software remains **an asset, not a liability**, no matter how it’s built.

At its core, Craftsmanship is a commitment to:

- **Well-crafted software** – code that is clear, testable, maintainable, and aligned with business needs.
- **Professionalism** – practices that ensure long-term sustainability, team growth, and business agility.
- **Productive partnerships** – between developers and stakeholders, grounded in trust and shared understanding.

These principles are more important than ever in the AI era.

Large language models don’t understand your business. They don’t care about your architecture. They don’t recognise the trade-offs you're making. Without thoughtful prompts and high-quality context, they will generate plausible code, fast, that could just as easily create **long-term friction** as short-term progress.

Software Craftsmanship helps by:

- **Framing the role of AI**: not as an autonomous coder, but as a powerful assistant that must be guided.
- **Emphasising intent**: ensuring that every change reinforces modularity, clarity, and business meaning.
- **Safeguarding correctness**: by embedding tests, design thinking, and review into the workflow.
- **Slowing entropy**: through consistent practices, naming conventions, and architectural discipline.

Most importantly, Craftsmanship **embraces AI while upholding standards**. It recognises that typing has never been the bottleneck; comprehension, decision-making, and quality have. AI can help accelerate delivery, but only when the foundation is solid.

That’s the challenge, and the opportunity for today’s software teams:
Use AI to go faster, but make sure you’re going in the right direction.

Software Craftsmanship ensures your code isn’t just delivered quickly but also **stays valuable over time**.

## 9\. Closing: Crafting Code in the Age of AI

AI is transforming the software development landscape, helping us code faster, automate the mundane, and explore solutions we might not have considered on our own.

But speed is not the same as productivity. And volume is not the same as value.

If we embrace AI blindly, we risk flooding our systems with hard-to-maintain, disconnected code, generated rapidly, poorly understood, and halfheartedly reviewed.

What we need now is **intentionality**. A mindset that values clarity, structure, and continuous improvement. A commitment to practices that **preserve business agility**, not just accelerate short-term delivery.

That’s the role of Software Craftsmanship in the AI era. Not to resist change but to **guide it**. To ask better questions. To set better constraints. To ensure the software we build remains **robust, understandable, and adaptable**, even as the tools we use evolve.

Craftsmanship turns AI into a powerful ally. Not by handing over control, but by **raising the standard of what “good” looks like** and ensuring that every line of code, AI-written or human-written, contributes to long-term success.

The future of software won’t be written by AI alone, but by those who know how to wield it with craft.

AI is the engine. Craftsmanship is the compass.
