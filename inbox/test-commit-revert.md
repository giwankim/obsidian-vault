---
title: "test && commit || revert"
source: "https://medium.com/@kentbeck_7670/test-commit-revert-870bbd756864"
author:
  - "[[Kent Beck]]"
published: 2018-09-28
created: 2026-03-26
description: "test && commit || revert As part of Limbo on the Cheap, we invented a new programming workflow. I introduced “test && commit”, where every time the tests run correctly the code is committed …"
tags:
  - "clippings"
  - "testing"
  - "git"
  - "refactoring"
---

> [!summary]
> Kent Beck introduces the "test && commit || revert" (TCR) workflow: if tests pass, code is automatically committed; if they fail, all changes are reverted. This forces extremely small, incremental steps and counteracts the sunk cost fallacy, while keeping the test suite perpetually green.

[Sitemap](https://medium.com/sitemap/sitemap.xml)

Get unlimited access to the best of Medium for less than $1/week.[Become a member](https://medium.com/plans?source=upgrade_membership---post_top_nav_upsell-----------------------------------------)

[

Become a member

](https://medium.com/plans?source=upgrade_membership---post_top_nav_upsell-----------------------------------------)

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*aFiJbORxanPt-2QDtaUKPg.jpeg)

The new style versus test-driven development

As part of [Limbo on the Cheap](https://medium.com/@kentbeck_7670/limbo-on-the-cheap-e4cfae840330), we invented a new programming workflow. I introduced “test && commit”, where every time the tests run correctly the code is committed. Oddmund Strømme, the first programmer I’ve found as obsessed with symmetry as I am, suggested that if the tests failed the code should be reverted. ==I hated the idea so I had to try it.==

The full command then is “test && commit || revert”. If the tests fail, then the code goes back to the state where the tests last passed.

I’m not arguing for “test && commit || revert” nor even describing its trade-offs. I’m saying it seems like it shouldn’t work at all, it does, and I hope you try it (if you’re the sort of person who just tries new programming workflows).

## But, but…

I thought “test && commit || revert” wouldn’t work. How could you make progress if the tests always have to work? Don’t you make mistakes sometimes? What if you write a bunch of code and it just gets wiped out? Won’t you get frustrated?

The surprising answers are yes, you can actually write code this way. Yes, you make mistakes but actually it’s kind of nice to have incorrect code instantly deleted (counteracts Sunk Cost Fallacy). If you don’t want a bunch of code wiped out then don’t write a bunch of code between greens. Yes it can be frustrating to see code disappear but you almost always find a better, surer, more incremental way of doing the same thing.

## Increments

Limbo scales technical collaboration by propagating tiny changes instantly. TDD won’t work in Limbo because each of a hundred thousand programmers can’t saddle all the other programmers with even one failed test. If thousands of tests are failing, then nobody knows what’s going on. The tests all have to pass before changes can propagate.“Test && commit || revert” keeps all tests green. At the same time you can’t solve big problems in one small step, so what are the steps you take when using “test && commit || revert”?

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*X_Lre4eT2VOCnTKf2cwkqA.jpeg)

Increments in TCR

- Add test and pass. The goal here is to shorten the time between idea and *some* kind of test passing in *some* kind of way. ==Even writing part of the test is fine. Cheating is encouraged, as long as you don’t stop there.==
- Better passing. Once you have a test passing, replace the fake implementation with a real implementation, a little at a time if necessary.
- Make hard changes easy. Rather than change four places in the code, introduce a helper function (a little at a time, natch) so you can change one place.

Violating any of these strategies results in the changes being instantly reverted, so you don’t have to worry about enforcing small diffs.

## Try It

I don’t suggest you try “test && commit || revert” because it’s better than what you do now. I suggest you try it because:

- It’s cheap.
- You’re bound to learn something.

Pick a little project, even Fibonacci, and start developing. See how small you can make your changes. Some of those will still fail. See how to make those changes even smaller. Pay attention to the little bits of workflow you use frequently. See what you can apply to your “real” work.

Thanks again to Iterate for sponsoring this Code Camp, and to Oddmund Strømme, Lars Barlindhaug, and Ole Johannessen for digging in, thinking of TCR, trying it, and talking about it.

[![Kent Beck](https://miro.medium.com/v2/resize:fill:96:96/2*JAaDel4nA2PXn6UpDKQXvA.jpeg)](https://medium.com/@kentbeck_7670?source=post_page---post_author_info--870bbd756864---------------------------------------)

[![Kent Beck](https://miro.medium.com/v2/resize:fill:128:128/2*JAaDel4nA2PXn6UpDKQXvA.jpeg)](https://medium.com/@kentbeck_7670?source=post_page---post_author_info--870bbd756864---------------------------------------)

[218 following](https://medium.com/@kentbeck_7670/following?source=post_page---post_author_info--870bbd756864---------------------------------------)

Kent is a long-time programmer who also sings, plays guitar, plays poker, and makes cheese. He works at Gusto, the small business people platform.

## Responses (41)

gwk

What are your thoughts?

```c
Mind blowing post !
```

48

```c
Interesting idea, but how do you verify your test actually test what they’re supposed to? You’re leaving out the red in “red green refactor” or else they get reverted.
```

62

```c
Hmm, so I’ve picked the fibonacci project, and implemented it as best I can with a bunch of unit tests. The QA goes and tries it on a 16-bit machine and it fails when trying to generate a fibonacci series of 24 digits.Another programmer gets the bug…more
```

95
