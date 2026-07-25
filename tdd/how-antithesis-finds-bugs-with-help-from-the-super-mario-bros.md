---
title: "How Antithesis finds bugs (with help from the Super Mario Bros.)"
source: "https://antithesis.com/blog/sdtalk/?utm_source=ghuntley"
author:
  - "[[Will Wilson]]"
published:
created: 2026-07-24
description: "Can solving Super Mario Bros. help solve your distributed systems issues?"
tags:
  - "clippings"
---

> [!summary]
> Antithesis publishes a previously unreleased Systems Distributed talk explaining how its platform explores the state spaces of complex systems, using Super Mario Bros. as the illustration. The key point is that their deterministic hypervisor isn't only about reproducing bugs — it's what makes finding them efficient in the first place. Their platform autonomously beats Mario in about 45 minutes on a 2018-era CPU given only the memory locations of Mario's coordinates and level, plays a Kaizo ROM hack with zero tuning on the first try, and reaches the Minus World; the same state-space exploration is what finds bugs in customers' distributed systems.

A year and a half ago, our friends at [TigerBeetle](https://tigerbeetle.com/) invited me to give a sneak preview of Antithesis at [Systems Distributed](https://systemsdistributed.com/). This talk was recorded, but never published (since we were in stealth at the time).

We’re publishing it now because it answers one of the most common questions we get: how exactly does Antithesis explore the state spaces of complex systems, and how does it find bugs so quickly? It also explains something Alex alluded to in [his post](https://antithesis.com/blog/deterministic_hypervisor/): our deterministic hypervisor isn’t just about getting perfect reproducibility of the bugs we find, it also helps us find the bugs in the first place.

And it explains all of this using everybody’s favorite Italian plumber. Check it out:

![](https://www.youtube.com/watch?v=zc4cqtibTzs)

As we announced before, our platform has been [playing and beating Nintendo games for many years](https://antithesis.com/blog/ag8bi/). Hopefully you now have some idea of why we use these programs for our bug-finding research. Far from being simple toy problems, they’re actually strictly harder to explore than “real” software in several important ways.

In the talk above I skipped to the end of the Super Mario Brothers solution that our platform autonomously discovered, but we’ve embedded the full video below (sped up so you can enjoy the whole thing). Antithesis can find this solution in about forty-five minutes on a 2018-era workstation CPU. The only hints our platform received were the locations in memory that hold Mario’s X and Y coordinates in a level, and which level he’s on.

![](https://www.youtube.com/watch?v=UxGX5gmnVwk)

Along the way, we can draw heatmaps of where Antithesis spends most of its time in the game. Since clipping through a wall is a relatively rare event, these heatmaps end up visibly reproducing some very recognizable level outlines:

![The heatmap of our fuzzer's path through Mario](https://antithesis.com/_astro/marioheatmap.CRgVNa5w_ZmBauH.webp)

The heatmap of our fuzzer's path through Mario

And here we are (sped up) playing a [Kaizo](https://en.wikipedia.org/wiki/Kaizo) ROM hack with the exact same configuration – zero tweaking, zero hyperparameter tuning, and zero iteration on the platform. This happened literally the first time we turned the system on with the new levels. Notice that we actually get stuck at the end, but we do play the game pretty well (and we find a bug!).

![](https://www.youtube.com/watch?v=rxJGOWdDONg)

Finally, the answer to the question I’m sure you’ve all been wondering about this whole time! Does Antithesis make it to the [Minus World](https://en.wikipedia.org/wiki/Minus_World)? You better believe it does:

![](https://www.youtube.com/watch?v=QSSFSLA_vxs)

Super Mario Bros. is a simple game, but its state space is inconceivably vast. As far as we know, we’re the first autonomous system to explore that state space efficiently enough to beat the game (albeit with one or two hints).

That same capability for efficient state space exploration is what enables us to find bugs and deliver value to [our customers](https://antithesis.com/learn/?category=Customer+stories#resources). If you’re interested in learning whether Antithesis can improve your software quality or development velocity, [contact us!](https://antithesis.com/company/contact/)
