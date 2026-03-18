---
title: "Inside Terraform: A series about the internals of Terraform | DanielMSchmidt.de"
source: "https://danielmschmidt.de/posts/2025-11-21-inside-terraform/"
author:
  - "[[Daniel Schmidt]]"
published: 2025-11-21
created: 2026-03-12
description: "A series about the internals of Terraform and how different parts of Terraform work under the hood."
tags:
  - "clippings"
---

> [!summary]
> A blog series index by Daniel Schmidt (HashiCorp/IBM Terraform Core team member) that deep-dives into Terraform internals including address systems, references, go-cty evaluation, error handling, and for_each/count expansion. The series aims to help readers understand the codebase well enough to contribute to Terraform itself.

[Go back](https://danielmschmidt.de/)

## Inside Terraform: A series about the internals of Terraform

***Disclaimer:** I am working at HashiCorp (now IBM) as part of the Terraform Core team. The postings on this site are my own and don’t necessarily represent IBM’s positions, strategies or opinions.
Since I am involved in Terraform my opinions can sometimes be (unconsciously) biased. I hope you enjoy the post anyway.*

This is the start/index post for a series of blog posts about the internals of Terraform. In this series, I will deep dive into different parts of Terraform and explain how they work under the hood.

The end-goal of this is to enable the reader to develop a deeper understanding of Terraform and how it works. After reading this, I would hope you are able to contribute to Terraform itself, add a new block to the language, or change existing behavior. I will not try to cover every single detail of Terraform, but I will try to cover the most important parts and give you a good overview of how different parts of Terraform work together.

My hope is that this series helps the reader to at least get a step closer to understanding the internals of Terraform. I won’t be covering anything related to language design and graph theory here; there are too many holes in my knowledge there as well. Maybe I’ll write something to that end in the future as well, probably not.

## Series Content

- [Part 1: `addrs` - Everything Needs an Address](https://danielmschmidt.de/posts/2025-11-21-inside-terraform-addrs)
- [Part 2: References - How Terraform Connects the Dots](https://danielmschmidt.de/posts/2025-11-26-inside-terraform-references)
- [Part 3: `go-cty` and Evaluation - Values in Terraform](https://danielmschmidt.de/posts/2025-12-03-inside-terraform-evaluation)
- [Part 4: `tfdiags` - Error handling in Terraform](https://danielmschmidt.de/posts/2026-01-28-inside-terraform-tfdiags)
- [Part 5: Expanding for\_each and count](https://danielmschmidt.de/posts/2026-02-26-inside-terraform-expanding-for-each-and-count)

## Why?

I have been reflecting on my past (almost) two years as part of the Terraform Core team at HashiCorp (now IBM). Our team builds new language features, maintains the Terraform language and runtime, and is part of most major changes to Terraform itself.

The codebase is vast and complex because the domain we cover (a programming language) is complex itself. If you used Terraform before you know how many things can be expressed with it, how many different styles of writing Terraform code there are and how many different use-cases Terraform has to cover.

I was relying heavily on my colleagues to gain an understanding of the codebase over time (and my gaps are still quite severe), and I wanted to take this opportunity to document my learnings and share them with the community. It might only be truly useful to a few people, but I hope others find it interesting as well. At least to me, this project is quite an interesting one with a lot of learning opportunities.

---

---

---[Previous Post

Inside Terraform: addrs - Everything Needs an Address

](https://danielmschmidt.de/posts/2025-11-21-inside-terraform-addrs)

[

Next Post

Terraform Actions Usage Patterns

](https://danielmschmidt.de/posts/2025-10-24-terrafrom-action-usage-patterns)

Inside Terraform: A series about the internals of Terraform | DanielMSchmidt.de
