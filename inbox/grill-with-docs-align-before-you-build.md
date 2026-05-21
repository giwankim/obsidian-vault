---
title: "grill-with-docs: Align Before You Build"
source: "https://www.aihero.dev/grill-with-docs"
author:
  - "[[Matt Pocock]]"
published: 2026-05-05
created: 2026-05-21
description: "Learn /grill-with-docs: combine AI interviewing with domain-driven design to build better codebases with shared language and less repetition."
tags:
  - "clippings"
---

> [!summary]
> Matt Pocock introduces `/grill-with-docs`, an evolution of his popular `/grill-me` AI-interviewing skill that folds in domain-driven design's concept of "ubiquitous language." The skill reads and maintains a `CONTEXT.md` glossary, actively challenges and sharpens fuzzy terminology as you design, and captures non-obvious, hard-to-reverse choices as Architectural Decision Records (ADRs). The payoff is more concise AI replies and code that mirrors the documented domain language — making it the go-to over `/grill-me` whenever you have a codebase.

Matt Pocock

[Next lesson](https://www.aihero.dev/skills-to-prd)

A few months ago, I wrote four sentences that became the most influential thing I've ever written. I packaged them into the `/grill-me` skill, a technique for getting an LLM to interview you relentlessly.

The skill walks down each branch of your design tree, resolving dependencies one by one until you reach a shared understanding. Every single day, [I](https://x.com/jonathan_wilke/status/2047626114856538559) [receive](https://x.com/reactive_dude/status/2040419885071642760) [about](https://x.com/housecor/status/2049460814143164585) [five](https://x.com/therealoliulv/status/2049078583256105250) [messages](https://x.com/glaucia_lemos86/status/2051171722062110870) from people saying they've tried it and love it.

Despite all that praise, I've actually built something better.

I'm never happy resting on my laurels. I always feel there's room for improvement in every part of my process. So I started noticing patterns where `/grill-me` was showing its limits.

As I used the skill more, I'd hit moments where the AI got really verbose. I'd have to remind it: "There's already a term for that." But often, there wasn't a term, or I was thinking about things verbosely myself, and the AI wasn't pushing back.

Sometimes we'd land on really good shared language, but then we'd never document it anywhere.

The core problem? We could communicate about the code effectively, but I had to re-explain all the non-obvious things about the codebase and domain before doing anything productive. There was a missing piece: documentation.

I started asking myself: **What's the thinnest layer of documentation I could use to give the AI a head start?**

## Introducing /ubiquitous-language

That question led me to **ubiquitous language**, a concept from [domain-driven design](https://en.wikipedia.org/wiki/Domain-driven_design), popularized in Eric Evans' *Domain Driven Design* (the big blue book).

The idea is simple: create shared language used by three groups:

1. **The codebase**
2. **Developers** building it
3. **Domain experts** who understand the problem (but not the implementation)

When all three groups speak the same language, something magical happens. A domain expert can say "there's something wrong with this part of the app," and the developer knows exactly what they mean. The code reflects it too.

So during my grilling sessions, whenever I noticed fuzzy language, I'd use the `/ubiquitous-language` skill to sharpen terms and create a `UBIQUITOUS_LANGUAGE.md` file as we went.

But I was using two skills in parallel: `/grill-me` and `/ubiquitous-language`. This felt inefficient.

## The New Skill: /grill-with-docs

Why not combine them into one?

The new skill is called `/grill-with-docs`.

It starts with the same core as `/grill-me`, but adds a few critical pieces.

### Looking for CONTEXT.md

The skill now searches for a `CONTEXT.md` file that documents all the shared language in that context. A "context" (in [domain-driven design](https://en.wikipedia.org/wiki/Domain-driven_design) terms) is a bounded area of your app where you speak a shared language.

If you have a massive monorepo, you can have a **context map** and multiple contexts inside. But if you have one large repo where everything speaks the same language, a single `CONTEXT.md` works fine.

### Active Language Refinement

During the session, the skill does extra work:

- **Challenge language usage** against the existing glossary
- **Sharpen fuzzy language** that's imprecise
- **Discuss concrete scenarios** to clarify edge cases
- **Cross-reference with code** to ground terms in reality
- **Update the glossary** as you go

This helps you build progressively better language with each session.

### Architectural Decision Records (ADRs)

There's one more piece: some fuzzy language can't be resolved just by sharpening terms. Some decisions are **non-obvious**, and they need explanation.

That's where **Architectural Decision Records (ADRs)** come in.

ADRs are simple markdown files that document non-obvious decisions. You only create an ADR when:

- The decision is **hard to reverse**
- The decision would be **surprising without context**
- The decision involved a **real trade-off** with consequences down the line

For example: "We use this library instead of that library" probably doesn't need an ADR if they're interchangeable. But "We chose ON DELETE RESTRICT instead of CASCADE for pitch deletion" might, because it forces conscious user actions and affects the deletion experience.

## Seeing It In Action

Let me show you how this works in practice. I'll paste in a real prompt and walk through the grilling session.

![Claude Code showing the pitch feature request](https://res.cloudinary.com/total-typescript/image/upload/c_limit,w_3840/f_auto/q_auto/v1777978765/ai-hero-images/baevxra2h9csq2hibmmj?_a=BAVAZGDY0)

Claude Code showing the pitch feature request

Here's my feature idea: I want to add a concept of **pitches** to my course management system.

A **pitch** is the packaging around a video: the title, description, and how I frame it to people. It's inspired by the MrBeast philosophy: work out the packaging before you create the video. I create a bunch of pitches, pick the best ones, and turn those into videos.

### Question 1: Cardinality

![Claude asking about the cardinality between pitch and standalone video](https://res.cloudinary.com/total-typescript/image/upload/c_limit,w_3840/f_auto/q_auto/v1777978766/ai-hero-images/j3uusotofz5ojqqsalsp?_a=BAVAZGDY0)

Claude asking about the cardinality between pitch and standalone video

The AI immediately surfaces a tension with the glossary. My `CONTEXT.md` already defines a **Standalone Video** as "a video with `lessonId = NULL`."

But I said pitches relate to standalone videos. The AI asks: **What's the relationship?**

- Does one pitch hold many videos? (1:N)
- Does one pitch correspond to exactly one video? (1:1)
- Can a video be in multiple pitches? (N:N)

The AI recommends **(a) 1:N**: a pitch as a "release container" likely holds multiple videos (a teaser + main video, or variants). Adding a nullable `pitchId` to the video table is cheap to implement and easy to relax later.

I agree. **Decision: 1:N, foreign key `pitchId` on video.**

### Question 2: Terminology Collision

![Claude surfacing a terminology collision with standalone video](https://res.cloudinary.com/total-typescript/image/upload/c_limit,w_3840/f_auto/q_auto/v1777978766/ai-hero-images/sxrcti5efumdstcbk1ju?_a=BAVAZGDY0)

Claude surfacing a terminology collision with standalone video

Now there's a problem. My `CONTEXT.md` says:

> Standalone Video: A video with no lesson association (lessonId = NULL)

But I just said videos can be related to pitches. A pitched video still has `lessonId = NULL`, so under the current definition, it's still a **Standalone Video**, just one with a pitch attached.

The AI offers two solutions:

| Option | Approach |
| --- | --- |
| **(a) Keep "Standalone Video" = lessonId IS NULL** | Pitch becomes orthogonal metadata. Introduce sub-terms: **Unattached Standalone Video** (no pitch) vs **Pitched Standalone Video** (has pitch). |
| **(b) Redefine "Standalone Video" as unpitched** | Introduce a new top-level term **Pitched Video** as a sibling. Standalone and Pitched become different categories. |

The AI recommends **(a)**. It's cleaner because "Standalone" answers a structural question ("Is it in a lesson?"), while "Pitched" describes packaging metadata. Pitch is orthogonal.

I agree. This distinction matters because it will affect every variable name and file name the AI generates.

### Question 3: Status Semantics

![Claude asking about status semantics and transitions](https://res.cloudinary.com/total-typescript/image/upload/c_limit,w_3840/f_auto/q_auto/v1777978767/ai-hero-images/qkmbudtwl9e2ggtj78ks?_a=BAVAZGDY0)

Claude asking about status semantics and transitions

What does `idle | scheduled | shipped` actually mean?

- Are statuses **manual** or **derived** from timestamps?
- Are transitions **linear** (idle → scheduled → shipped) or **free-form**?
- What do the statuses represent?

The AI recommends: **Hybrid approach**. Store timestamps (`scheduledFor`, `shippedAt`), compute status from them. Allow free-form transitions.

I decide differently: **I want manual, free-form transitions, no automation yet.**

**Decision: status as a plain column, manual transitions, no dates.**

### Question 4: Empty Pitches

Can a pitch exist with zero videos?

The AI recommends **yes** (pitch-first workflow): create the pitch as a planning artifact, attach videos later. This matches the MrBeast philosophy and the `idle` status.

I agree. **Decision: Pitches can exist with zero videos.**

### Question 5: Deletion Behavior

![Claude discussing deletion cascade behavior](https://res.cloudinary.com/total-typescript/image/upload/c_limit,w_3840/f_auto/q_auto/v1777978769/ai-hero-images/ds5tnmyexzck63cson98?_a=BAVAZGDY0)

Claude discussing deletion cascade behavior

When a pitch is deleted, what happens to its videos?

| Option | Behavior |
| --- | --- |
| ON DELETE SET NULL | Videos return to "totally standalone" |
| ON DELETE CASCADE | Deleting a pitch deletes its videos too |
| ON DELETE RESTRICT | Can't delete a pitch while it has videos |

The AI recommends **SET NULL**. Pitches are packaging metadata, not the source of truth. Videos have independent value.

I choose **RESTRICT**. This forces conscious detachment before deletion, which matches my preference for restrictive deletions (I archive instead of delete).

### Saving to CONTEXT.md

At this point, I ask the AI to save everything into `CONTEXT.md`. It surfaces two more open items:

1. **Title/description nullability** - Should titles be required? (AI recommends required with "Untitled" default)
2. **Archive support** - Should pitches have an `archived` boolean like other entities? (AI recommends yes)

I agree with both.

The AI then updates `CONTEXT.md`:

```markdown
### Pitches

**Pitch**:
A packaging artifact around one or more **Standalone Videos**: a title, an optional
description, and a **Pitch Status**. Independent of the course/lesson hierarchy -
pitches do not interact with lessons.

**Pitch Status**:
One of \`idle\`, \`scheduled\`, or \`shipped\`. Set manually; transitions are free-form
(any status to any status). No timestamps are derived from or attached to status changes.

**Pitched Standalone Video**:
A **Standalone Video** whose \`pitchId\` is non-null. Still a Standalone Video - \`pitchId\`
is orthogonal metadata layered on top of the lesson-less structural fact.

**Unattached Standalone Video**:
A **Standalone Video** with no pitch (\`pitchId IS NULL\`). The "totally standalone" case.
```

And updates the relationships section:

```markdown
- A **Standalone Video** is either an **Unattached Standalone Video** (pitchId IS NULL)
  or a **Pitched Standalone Video** (pitchId references a Pitch)
- A **Pitch** has zero or more **Pitched Standalone Videos**; deleting a pitch is
  restricted while it has attached videos (the user must detach them first)
- A **Pitch** never references a **Lesson**, directly or transitively
```

[

AI Hero · Skill System

### /grill-with-docs is one. Here are the rest.

The full skill set I keep running while shipping with agents — slash commands, hooks, the works.

See the skill set](https://www.aihero.dev/skills)

## The Real Benefits

### 1\. Concise Replies

With shared language documented, the AI uses fewer tokens. Instead of verbosely re-describing everything, it says:

> "Standalone videos are changing, we need to make a change to the pitches and how the pitches display."

That's it. No repetition, no re-explanation.

### 2\. Better Thinking & Easier Navigation

AI uses language to think to itself (in chain-of-thought). With shared language, its internal reasoning becomes more efficient too. Fewer tokens, better alignment.

And because your planning documents align with how the code looks, the code becomes easier to navigate. You search for "pitches," and everything related is right there.

This is the same reason [domain-driven design](https://en.wikipedia.org/wiki/Domain-driven_design) works with humans, and it turns out, **it works just as well with AI.**

## Is /grill-me Dead?

No. Absolutely not.

`/grill-me` is still excellent, but `/grill-with-docs` is **better when you have a codebase.**

I've reorganized my skills:

- **`/grill-me`** lives in the "Productivity" section for general use cases *without* a codebase
- **`/grill-with-docs`** is the go-to skill when you have code

Someone told me they used `/grill-me` to write a eulogy for their mom - it surfaced all these amazing stories through AI-driven questioning. That's an incredible use case that `/grill-with-docs` isn't designed for.

The rule is simple:

| Situation | Use This |
| --- | --- |
| You have a codebase | `/grill-with-docs` |
| You don't have a codebase | `/grill-me` |

Even early in a project, I'd recommend `/grill-with-docs` because that's when you're establishing shared language.

## Staying Updated

I update these skills constantly. I'm always thinking of new improvements or better ways to use them.

Thanks for following along. If you try `/grill-with-docs`, let me know how it goes in the comments. And if you spot something I could improve, raise an issue [in the skills repo](https://github.com/mattpocock/skills).
