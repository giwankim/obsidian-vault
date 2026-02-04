---
title: "Consensus algorithms at scale: Part 1 - Introduction — PlanetScale"
source: "https://planetscale.com/blog/consensus-algorithms-at-scale-part-1"
author:
published: 2020-08-28
created: 2026-01-30
description: "This is a multi-part blog series and will be updated with links to the corresponding posts."
tags:
  - "clippings"
---
$50 Metal Postgres databases are here.[Learn more](https://planetscale.com/blog/50-dollar-planetscale-metal-is-ga-for-postgres)

[Blog](https://planetscale.com/blog) |

## Consensus algorithms at scale: Part 1 - Introduction

By Sugu Sougoumarane |

> Be sure to follow along with this eight part series. You will find all posts in the series linked at the [bottom of each article](https://planetscale.com/blog/#read-the-full-consensus-algorithms-series).

## Introduction

**Consensus algorithms** in their theoretical and applied forms can be difficult to reason about. Often, these algorithms are solutions that have stumbled upon some good problems to solve. Unfortunately, the problems are evolving. And I don’t think these solutions are going to remain relevant much longer. Let’s start with defining the problems they solve:

- **Distributed Durability:** In case of node failures, your data is guaranteed to be elsewhere.
- **Availability:** The ability for the system to continue serving if some nodes have become unavailable.
- **Automation:** If there is a failure, the system knows how to remedy itself without human intervention.

![](https://planetscale.com/assets/blog/content/consensus-algorithms-at-scale-part-1/114bf0e1707816cd6f18448e7f3fdeca37daf3c0-950x978.png)

Strictly speaking, one could argue that Automation is a different theoretical problem because it requires failure detection. But the reality is that today’s systems expect consensus systems to satisfy the above properties.

Let us now turn this around: If we had started out with these requirements, would we have ended up with something like Paxos or Raft as the best solution? Before we can answer this question, we need a better understanding of the requirements.

More importantly, cloud providers are coming up with complex topologies like zones and regions. They have pricing structures that encourage specific configurations. It is important that the systems we build are capable of adapting to these nuances. It is only a matter of time before these rigid algorithms start to run out of flexibility.

The spoiler here is that we are building this type of flexibility in Vitess: You specify what is important to you, and what (reasonable) trade-offs you are willing to make. And Vitess will have the knobs to exactly match these parameters without compromising on anything else.

However, we need to satisfy the skeptic’s concern: can you build such a system using vanilla MySQL? The short answer is yes.

## The approach

In this series of blog posts, I’ll take you through a journey where we will dissect consensus algorithms. We’ll break them up into smaller concerns, and we’ll build a new set of rules and principles using a variety of more flexible algorithms which can be built. We will conclude with how to achieve these objectives in Vitess.

As a disclaimer, this is an engineering approach. So, if you are expecting proof, you’ll likely be disappointed. I will instead be using and sharing intuitions developed from running storage systems at massive scale. Consequently, we will make two changes to how we approach this problem:

1. Use engineering terminology. This is more for my own sake, because it is hard to reason about how an academic concept maps to real-world scenarios.
2. Use an approach based on objectives to be achieved: approaching the problem top-down, identifying the concerns, and keeping them separate.

The second aspect is significant because most consensus algorithms perform orchestrated actions that achieve multiple objectives at the same time. It is hard to know why a decision was made a certain way and what the trade-offs are if a different approach was used.

With a better understanding of the concerns, we can make better trade-offs without being stuck with rigid implementations.

## Read the full Consensus Algorithms series

- **You just read**: [Consensus Algorithms at Scale: Part 1 — Introduction](https://planetscale.com/blog/consensus-algorithms-at-scale-part-1)
- **Next up**: [Consensus Algorithms at Scale: Part 2 — Rules of consensus](https://planetscale.com/blog/consensus-algorithms-at-scale-part-2)
- [Consensus Algorithms at Scale: Part 3 - Use cases](https://planetscale.com/blog/consensus-algorithms-at-scale-part-3)
- [Consensus Algorithms at Scale: Part 4 - Establishment and revocation](https://planetscale.com/blog/consensus-algorithms-at-scale-part-4)
- [Consensus Algorithms at Scale: Part 5 - Handling races](https://planetscale.com/blog/consensus-algorithms-at-scale-part-5)
- [Consensus Algorithms at Scale: Part 6 - Completing requests](https://planetscale.com/blog/consensus-algorithms-at-scale-part-6)
- [Consensus Algorithms at Scale: Part 7 - Propagating requests](https://planetscale.com/blog/consensus-algorithms-at-scale-part-7)
- [Consensus Algorithms at Scale: Part 8 — Closing thoughts](https://planetscale.com/blog/consensus-algorithms-at-scale-part-8)
