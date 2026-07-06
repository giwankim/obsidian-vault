---
title: "CQRS Journey"
source: "https://learn.microsoft.com/en-us/previous-versions/msp-n-p/jj554200(v=pandp.10)"
author:
  - "[[Archiveddocs]]"
published:
created: 2026-07-05
description:
tags:
  - "clippings"
---

> [!summary]
> Microsoft patterns & practices project exploring CQRS and Event Sourcing for building highly scalable, available, and maintainable applications. Framed as a learning journey rather than a definitive guide: it journals a team with no prior CQRS experience building and deploying a real-world reference implementation to Azure, with input from industry experts. The written guidance is split into three independently readable sections — the journey itself, CQRS reference materials, and case studies from other teams.

![patterns & practices Developer Center](https://learn.microsoft.com/en-us/previous-versions/msp-n-p/images/ff921345.pnp-logo(en-us,pandp.10).png "patterns & practices Developer Center")

## Exploring CQRS and Event Sourcing

The project is focused on building highly scalable, highly available and maintainable applications with the **Command & Query Responsibility Segregation** and the **Event Sourcing** patterns.

The project was positioned as a learning journey. This guidance is designed to help you get started with the CQRS pattern and event sourcing. It is not intended to be the definitive guide to the CQRS pattern and event sourcing. Instead, it's a journal that describes the experiences of a development team with no prior CQRS proficiency in building, deploying (to Microsoft Azure), and maintaining a sample [real-world complex enterprise](https://blogs.msdn.com/b/agile/archive/2012/01/24/picking-a-domain-for-cqrs-journey-ri.aspx) system as a reference implementation (RI) to showcase various CQRS and ES concepts & techniques. The development team did not work in isolation; we actively sought input from industry experts and from a wider group of advisors to ensure that the guidance is both detailed and practical.

The CQRS pattern and event sourcing are not mere simplistic solutions to the problems associated with large-scale, distributed systems. By providing you with both a working application and written guidance, we expect you'll be well prepared to embark on your own CQRS journey.

This written guidance is itself split into three distinct sections that you can read independently: a description of the journey we took as we learned about CQRS, a collection of CQRS reference materials, and a collection of case studies that describe the experiences other teams have had with the CQRS pattern. The map below illustrates the relationship between the first two sections and our main milestones.

[![Follow link to expand image](https://learn.microsoft.com/en-us/previous-versions/msp-n-p/images/jj554200.a2ef80397de93e4ec87f497f9db020d2-thumb(en-us,pandp.10).png "Follow link to expand image")](https://msdn.microsoft.com/en-us/jj554200.a2ef80397de93e4ec87f497f9db020d2\(en-us,pandp.10\).png)
