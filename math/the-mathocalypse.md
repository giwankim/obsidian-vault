---
title: "The Mathocalypse"
source: "https://scottaaronson.blog/?p=10169"
author:
published: 2026-10-08
created: 2026-10-08
description: "… then they came for Navier–Stokes and I said nothing because I never worked on Navier–Stokes. But when they came for RL vs. L I realized that things are serious --friend-of-the-blog Omer Reingold (shared with permission) Last night my 9-year-old son was taunting my wife, complexity theorist Dana Moshkovitz, as follows: \"mommy, I heard you…"
tags:
  - "clippings"
---

> [!summary]
> Scott Aaronson reacts to OpenAI's release of hundreds of AI-generated proofs of long-open problems, which almost no human has understood yet. They include Khot's Unique Games Conjecture (a lifelong target of his wife, Dana Moshkovitz), L=BPL, integer multiplication and the FFT below n log n, and his own Unitary Synthesis Problem. He contrasts OpenAI's undigested dump with Anthropic's approach of letting Williams and Alman publish a digested 3SUM/APSP result, and asks how mathematicians keep caring about their craft now that the machine exists.

> … then they came for Navier–Stokes and I said nothing because I never worked on Navier–Stokes. But when they came for RL vs. L I realized that things are serious

–friend-of-the-blog [Omer Reingold](https://omereingold.wordpress.com/) (shared with permission)

---

Last night my 9-year-old son was taunting my wife, complexity theorist [Dana Moshkovitz](https://www.cs.utexas.edu/~danama/), as follows: “mommy, I heard you got *cooked*! I heard that a *robot* solved the math problem you worked on for your whole career! OOF!”

While my son was being a brat, he also wasn’t wrong. Whether you’re thrilled, depressed, angry, or whatever else about it, yesterday was surely one of the biggest days in mathematical history. And yes, among the 372 huge results [released yesterday by OpenAI](https://openai.com/index/sharing-ai-progress-in-mathematics/), on the recommendation of its [advisory group](https://agmai.org/) of Timothy Gowers, Edward Witten, and other distinguished mathematicians, was a [proof](https://github.com/openai/math/blob/main/preprints/The-Unique-Games-Theorem-September-23-2026/paper.pdf) of Subhash Khot’s [Unique Games Conjecture (UGC)](https://en.wikipedia.org/wiki/Unique_games_conjecture), a statement that my wife has worked toward proving for the entire time I’ve known her. (The UGC implies that a whole slew of optimization problems really are NP-hard, even if you just want an approximation that’s slightly better than what you get from semidefinite programming relaxation, which is one of our main tools.)

Or at least, we’re pretty sure that it’s a proof! There’s a [Lean certificate](https://github.com/openai/math/blob/main/lean/docs/102.md), as there are for some of the other 372 breakthrough results (not all of them). But it also appears that no human has understood just about *any* of these proofs yet; the race to do so has just started. If you want an on-the-ground sense of what that race is going to be like, here’s some of what Dana texted me last night:

> It feels like something written by someone who’s on psychedelics. So much unclear and doesn’t make sense. Lots of name dropping of previous work without discussing why it can be used despite impossibility results
>
> Basically the paper is so horribly written that it’s impossible to read it without AI help
>
> I asked Astra for reasonable completeness and soundness claims of the noise gadget and it gave them by combining claims from all over the paper
>
> They also have direct optimal NP hardness of approximation proofs for the main applications of the UGC (Max Cut and all CSP) that bypass the UGC.
>
> The UGC proof invents a completely new bizarre code with a noise test. It’s some crazy recursive construction.
>
> It’s not the long code, not the short code – some alien craziness
>
> I still think that there maybe is a proof that uses the half space code (which is natural)
>
> The citations are often irrelevant and confusing
>
> A possible future is a math world that’s heavenly if you have vision/creative ideas that AI could help check and implement.
>
> And of course there’s a lot for us to learn from the aliens

If you’re wondering what emotions Dana is feeling—well, probably all of them! Even while a central career aspiration has fallen to a robot, there are at least two mitigating factors for her. First, she can feel vindicated that the UGC was *true* after all, something she never doubted even while many of her colleagues did! Second, *all* of us in math and theoretical computer science and mathematical physics, at least those who cared about solving crisply-stated problems, are now in the same boat.

---

Besides the Unique Games Conjecture, here’s a small sampling of the treasures from Aladdin’s cave that I’ll probably be paying the most attention to over the coming weeks:

- [L=BPL](https://github.com/openai/math/blob/main/preprints/Exact-Derandomization-of-Logarithmic-Space-L-equals-RL-equals-BPL-September-23-2026/paper.pdf) (i.e., probabilistic logspace and deterministic logspace are the same thing), one of the great derandomization conjectures short of P=BPP. Though its truth was never in serious doubt, there was a whole subcommunity focused on proving this.
- The [Fourier Transform](https://github.com/openai/math/blob/main/preprints/An-explicit-power-saving-for-the-exact-discrete-Fourier-transform-September-25-2026/main.pdf) and [integer multiplication](https://github.com/openai/math/blob/main/preprints/Integer-multiplication-below-n-log-n-September-23-2026/paper.pdf) in less than O(n log n) time, breaking a barrier that had stood since the 1960s. The new running time, if you’re curious, is O(n log <sup>0.9999999999999</sup> n), give or take some 9’s.
- [Positive solution to the Unitary Synthesis Problem](https://github.com/openai/math/blob/main/preprints/Polynomial-Time-Unitary-Synthesis-from-a-Boolean-Oracle-October-5-2026/paper.pdf), which Greg Kuperberg and I [posed](https://arxiv.org/abs/quant-ph/0604056) back in 2007. For every n-qubit unitary transformation U, there exists a classical oracle A such that U can be implemented in quantum polynomial time with access to A. This is the opposite of what most of us expected, and could have implications for e.g. the computational problem of decoding Hawking radiation from a black hole and many other problems in quantum complexity theory— *if* we had an efficient way to construct the oracle A, which this paper doesn’t give.
- [Parity is not in QAC <sup>0</sup>](https://github.com/openai/math/blob/main/preprints/Product-projection-localization-and-the-QAC0-parity-lower-bound-September-24-2026/paper.pdf), one of the great questions of quantum complexity theory since 1999 that many of my colleagues had been closing in on.
- [Nearly 4 <sup>th</sup> -power separation between randomized and quantum query complexity for total Boolean functions](https://github.com/openai/math/blob/main/preprints/A-Nearly-Quartic-Separation-Between-Randomized-and-Quantum-Query-Complexity-October-5-2026/quartic-query-separation.pdf). A favorite problem of mine since 1998 (!), when we knew only that the optimal separating exponent was between 2 and 6. For the past few years, we knew it was between 3 and 4. So, this finally closes that story.
- A [superquadratic separation](https://github.com/openai/math/blob/main/preprints/A-superquadratic-separation-between-sensitivity-and-block-sensitivity-September-25-2026/paper.pdf) between sensitivity and block sensitivity.
- [Area law for 2D gapped Hamiltonians](https://github.com/openai/math/blob/main/preprints/A-two-dimensional-area-law-from-a-global-spectral-gap-September-24-2026/paper.pdf). One of the main open problems in Hamiltonian complexity.
- [Matrix multiplication in O(n <sup>9/4</sup>) time](https://github.com/openai/math/blob/main/preprints/Matrix-Multiplication-Nine-Fourths-October-2-2026/paper.pdf) —a *rational* exponent for once (!), and via a completely different approach than was used for O(n <sup>2.373</sup>) and so forth
- $\Omega(n^3)$ [lower bound on the determinantal complexity of the permanent](https://github.com/openai/math/blob/main/preprints/A-cubic-lower-bound-for-border-determinantal-complexity-of-the-permanent-September-24-2026/A-cubic-lower-bound-for-border-determinantal-complexity-of-the-permanent-September-24-2026.pdf), improving the previous best bound which was quadratic.
- A [randomized polytime algorithm](https://github.com/openai/math/blob/main/preprints/A-Fully-Polynomial-Randomized-Approximation-Scheme-for-Perfect-Matchings-in-General-Graphs-September-23-2026/main.pdf) to approximately count the number of perfect matchings in a general graph, as well as a [randomized nearly linear-time algorithm](https://github.com/openai/math/blob/main/preprints/Almost-Linear-Time-Maximum-Cardinality-Matching-in-Sparse-General-Graphs-September-24-2026/main.pdf) for *finding* a maximum matching in such a graph
- [Uncomputability of solving polynomial equations over the rational numbers](https://github.com/openai/math/blob/main/preprints/Hilberts-tenth-problem-over-the-rational-numbers-September-24-2026/main.pdf) —this was arguably the biggest open problem in computability theory (note that uncomputability of solving Diophantine equations, i.e. polynomial equations over the *integers*, was proved in the 1970s, giving a negative answer to Hilbert’s 10th Problem)

Any of the above, alone, could easily have been “result of the year” in some area (and in some cases, like Unique Games and L=BPL, in all of CS theory). And there’s a lot that I’ve left out—feel free to share in the comments whatever is making *your* eyes bug out! There are equally astounding wonders in number theory, combinatorics, algebraic geometry, analysis, and pretty much every other area of math, most of which I’ll never understand, although I’ll note that it includes partial [progress toward the Riemann hypothesis](https://github.com/openai/math/blob/main/preprints/The-Quasi-Riemann-Hypothesis-September-30-2026/paper.pdf) and the [Hodge Conjecture](https://github.com/openai/math/blob/main/preprints/The-rational-Hodge-conjecture-for-products-of-K3-surfaces-October-4-2026/hodge-conjecture-products-k3.pdf) and the [Birch-Swinnerton-Dyer Conjecture](https://github.com/openai/math/blob/main/preprints/Exact-Birch-Swinnerton-Dyer-Formula-from-Low-Selmer-Corank-October-3-2026/exact-bsd-low-selmer-corank.pdf) (i.e., the majority of the remaining Millennium Problems).

We can take solace in what’s missing from the list. P≠NP isn’t there, nor even P=BPP or NEXP⊄P/poly, and surely not for lack of trying. Apparently the greatest open problems of theoretical computer science are indeed pretty hard!

---

Oh, lest I forget: one day *before* the OpenAI dump, meaning Monday evening, Virginia Williams and Josh Alman [posted an arXiv preprint](https://arxiv.org/abs/2610.06783) that solves the 3SUM problem in O(n <sup>1.9992</sup>) time, and the All-Pairs Shortest Paths problem in O(n <sup>2.9995</sup>) time, refuting half-century-old conjectures that the correct answers were n <sup>2-o(1)</sup> and n <sup>3-o(1)</sup> respectively. In this case, it wasn’t an OpenAI model that supplied the crucial idea; it was an Anthropic one! But Anthropic then took a different approach from OpenAI: rather than post the undigested solutions to the world, it gave Virginia and Josh the opportunity to write and announce a digested version in exchange for compensation.

These have emerged as the two main models for communicating AI math breakthroughs, and they both have strengths and weaknesses. The “OpenAI model” sets up a crazy race among humans to digest and explain a messy AI proof (work that could easily be some combination of thankless, barely-credited, competitive, and unfun), while the “Anthropic model” puts a private company in the position of picking and choosing which human mathematicians get to be the emissaries of the AI. Dunno, what do you guys think?

---

For those who are wondering: apparently, the AI model that produced all these wonders was *not* bespoke contraption of 10,000 agents burning millions of dollars worth of compute, as was used for example to construct a finite-time blowup for the Navier-Stokes equations. Instead, it was simply the latest internal OpenAI model—one that might be released to paying ChatGPT customers within the next couple of months, depending on the recommendations of OpenAI’s safety board! (My 9-year-old son: “Oh they *definitely* shouldn’t release that. If it could solve all those math problems, it can’t *possibly* be safe.”) Apparently they used about 3 hours of GPT-Pro level compute on average per problem solved.

Also, if you were wondering: apparently they *tried* the model on about 8,000 problems. So, right now it “merely” solves ~5% of the longstanding open mathematical problems that it’s asked about, the problems that whole communities have spent years on, after a single 3-hour attempt on them.

---

I’ve been glad to see the CS theory community rising to the occasion. At the Simons Institute in Berkeley, here at UT Austin, and elsewhere, I’ve hearing stories of researchers rushing to pore over the manuscripts and *make sense of them and explain them* —because what else do we do? How else do we continue the craft to which we’ve devoted much of our lives?

If you want some sense of what things feel like now in math, imagine a hunter-gatherer who’s spent his entire life learning to survive deep in an unforgiving rainforest, then a giant resort hotel springs up right next to him with a helipad and heated pools and AirBnBs, and without missing a beat, the hunter-gatherer says: “alright fine, so now my new job is to run wilderness retreats for the tourists, or something.”

In *Quanta* magazine, Jordana Cepelewitz [attempted a different metaphor](https://www.quantamagazine.org/is-ai-the-end-of-math-as-we-know-it-20261005/):

It’s as if you were teleported to the peak of a tall mountain. Surrounded by fog, you have no idea where you are, or what’s around you. You do not know how your mountain connects to others, and you have no equipment to help you explore, no way to help someone else join you. If you had climbed the mountain yourself, you would have experienced how the human body adapts to altitude and changes in oxygen levels. You might have had to invent tools to navigate, to climb steep cliffs, or to make a shelter. You might have encountered a fellow explorer, gotten lost together in a hidden valley, and found a plant that could be turned into a life-saving medicine.

Instead you’re perched on the peak but in the dark, while the maker of the teleportation machine tells you that it can explore the wilderness better than any human.

For any one of these mountains, if we care enough, I feel optimistic that we can do as we always have: clear the fog and figure out the path, except now using the teleportation machine to help guide us. The bigger challenge will be to nurture a community that still *cares* about the heroic adventure of finding the paths up these mountains in the world with the machine. (Oh, and I think one place where the metaphor breaks is that we still *do* have each other, as much as we ever did before!)

---

Experience has shown that, *even now*, there will still be people explaining in patronizing tones why none of this is real and none of it counts. If such people were capable of being impressed by *anything* that happens in the empirical world, of updating on *anything*, they would’ve already been impressed and already updated several years ago, long before things had reached the point of an actual Mathocalypse.

So, they’ll say, maybe the alleged solutions are not solutions at all, but just “AI slop.” Or maybe none of the 372 well-known open problems that were solved were *real* math problems, they were all just glorified contest puzzles and trivialities. (After all, there’s still no Riemann Hypothesis!) Or maybe the entire 4000-year-old discipline of mathematics needs to be jettisoned: turns out that it was *all* just puzzle-solving and trivialities; all that’s different is that now the triviality stands unmasked. In any case, what really matters is that the *true* inner sanctum of human creativity hasn’t been breached and probably never will be, and also, that Sam Altman and Dario Amodei are contemptible little nerds.

If you’re still a proponent of that doomed worldview, still aboard the sinking ship, I encourage you in the strongest possible terms to read yesterday’s *other* great contribution to AI discourse, besides the OpenAI Mathocalypse dump: namely, [Scott Alexander’s open letter to Steven Pinker](https://www.astralcodexten.com/p/an-open-letter-to-steven-pinker-on). I feel some responsibility for this, as the person who first introduced Steven Pinker to the *existence* of the rationalist community, and who also first introduced Steven Pinker and Scott Alexander to one another (they had both been fans of each other’s writing). And now Scott is challenging Steve to a literal duel, with guns!

For whatever it’s worth: Steve is a lifelong intellectual hero of mine, just as he is for Scott, and I also have to privilege of calling Steve my friend. But I found Scott’s post to be one of the most devastating rejoinders to anything that I’ve ever read. And I thought Scott’s conclusion was exactly right: when it comes to AI risk, Steve’s great challenge is now to accept and start using a more “Pinkerite” epistemology.

---

Last night, while I should’ve been poring over some of OpenAI’s hundreds of papers and/or writing this post, I decided to spend some time with my kids instead. They wanted a movie night, so I suggested something they’d never seen before (and that I hadn’t seen for decades), and that seemed chock-full of no-nonsense, practical guidance for the world in which they’re going to grow up: *Terminator 2*.

---

**==Update:==** As several people have pointed out, cryptography is a subfield that’s extremely conspicuous by its absence from OpenAI’s list of 376 papers! But my sources tell me that the AI companies have now started, gingerly and discreetly, investigating whether their latest internal models can break important cryptographic protocols and primitives. If they *can*, then it would certainly be nice to get ahead of things before the rest of the world figures out the same.

**==Another Update:==** The [statement](https://agmai.org/#openai-release) put out the Advisory Group on Mathematics and Artificial Intelligence is very carefully phrased, neither endorsing nor condemning what OpenAI did, and is worth a read:

> As announced a few weeks ago, OpenAI has released a large collection of mathematical results generated by an internal model, reporting solutions to hundreds of open questions. This is an important event for mathematics, with consequences both for mathematics and for the mathematical community that extend far beyond the individual results.
>
> AGMAI’s advisory role should not be interpreted as a judgment of the impact of these results or an endorsement of the process by which OpenAI obtained them. We do not speak on behalf of the entire mathematical community, and only the mathematical community can undertake the assessment that is needed.
>
> Making this work public is a first step. This release is the beginning, not the completion, of the process of human understanding and the incorporation of the work into mathematical knowledge. At the same time, the future of mathematical research cannot consist only of understanding results produced by AI labs. Mathematicians must be able to formulate their own questions, develop their own approaches, and explore directions that have not been selected as examples of an AI system’s capabilities. Equitable access to powerful research tools and adequate computational resources are essential to that freedom.
>
> We reaffirm our [published recommendations](https://agmai.org/general-sep29/) on responsible release. We have discussed them with OpenAI and appreciate the company’s willingness to engage. While we consider these discussions constructive, it is ultimately up to the mathematical community to assess the extent to which our recommendations were followed successfully, and whether there are others we should suggest. We remain committed to engaging with any frontier AI lab on these questions and have already been in contact with several of them.
