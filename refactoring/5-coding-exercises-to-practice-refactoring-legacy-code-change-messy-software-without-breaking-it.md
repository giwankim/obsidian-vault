---
title: "5 coding exercises to practice refactoring Legacy Code - Change Messy Software Without Breaking It"
source: "https://understandlegacycode.com/blog/5-coding-exercises-to-practice-refactoring-legacy-code/?utm_source=convertkit&utm_medium=email&utm_campaign=%F0%9F%A4%BA%205+2%20Coding%20Exercises%20to%20Practice%20Refactoring%20on%20Legacy%20Code%20-%206440364"
author:
  - "[[Nicolas Carlo]]"
published:
created: 2026-02-18
description: "Feeling overwhelmed by your legacy codebase? These katas will help you learn how to tackle it."
tags:
  - "clippings"
---
> [!summary]
> Presents 5 coding katas for practicing legacy code refactoring, ordered by difficulty: Gilded Rose, Tennis, Trip Service, Expense Report, and Trivia Game, plus 2 bonus "realistic" katas for front-end and API refactoring. Each kata targets specific skills like adding tests to untested code, breaking problematic dependencies, and separating concerns using hexagonal architecture.

## 5 coding exercises to practice refactoring Legacy Code

*Struggling with Legacy Code and not enough time to clean it up?*
⛑️️ **[My First Aid Kit](https://understandlegacycode.com/first-aid-kit)** can help you rescue any codebase **quickly** and **safely**!

Learning to write clean code from scratch is great… but learning to deal with existing, undocumented, untested code may be even more useful.

**Problem: your daily job is not the best place to learn these skills**. You see, you can’t explore much when you are operating under short deadlines and pressure to ship. You fall back to the techniques you know, your comfort zone.

How can you get better at breaking dependencies and splitting huge classes that do far too much?

By practicing with Coding Katas! 🥋

## Exercises to practice your coding-fu

You may have come across coding katas.

If you never did, picture them as small coding exercises. They are meant to be practiced again and again and again. The goal is to solve a defined problem.

It’s very efficient to try out a new technique on something concrete. It’s also a good way to practice a technique you know until you master it.

It’s like building a Todo App every time you want to try out a new front-end framework.

### There are plenty of coding katas out there!

There are even [kata-logs](https://kata-log.rocks/) of exercises you can try out!

But if you tried a couple of katas, you might have realized they have one shortcoming: **none of them seem to allow you to practice refactoring bad code!**

That’s true, the vast majority of katas make you code from scratch…

However, there are a few which are specifically tailored for practicing refactoring Legacy Code. Katas where [Michael Feathers’ techniques](https://understandlegacycode.com/blog/key-points-of-working-effectively-with-legacy-code) would shine.

Here’s my shortlist of katas you should try out.

## 5 katas to practice refactoring

Real-life codebases generally have so many issues at the same time, it’s overwhelming. Where should you start when you’re dealing with 500k lines of spaghetti code?! You just want to *start* cleaning the code, but you’re already playing in hardcore mode.

What you need, is **dirty code at a smaller scale**.

It should still be complex, or you wouldn’t practice much. But it should be manageable, so you *can* practice. Your goal is to turn that little mess into clean code.

Whether you’re done or you’re stuck, you can throw it away and start over! No deadline. Nothing to ship. Just a playground to try things 👌

I sorted these katas in increasing difficulty order.

### 1\. The Gilded Rose

![](https://understandlegacycode.com/_astro/gilded-rose.BFNATdC6_Z15ox5V.webp)

This one is my favorite.

It’s **the perfect kata to get started** with refactoring Legacy Code.

👉 [github.com/emilybache/GildedRose-Refactoring-Kata](https://github.com/emilybache/GildedRose-Refactoring-Kata)

Your goal is to add a new feature to an existing codebase. The code is messy, but it’s “just” a bunch of nested conditionals. It surely can be improved, but nothing overwhelming.

There’s no HTTP call, no database request, no randomness. Just pure logic… that’s quite tangled!

That’s why I generally use this kata to train people who never did refactoring katas before 🎓

I like how [the requirements](https://github.com/emilybache/GildedRose-Refactoring-Kata/blob/master/GildedRoseRequirements.txt) give *too much information*. Just like a regular conversation with people. If you want to get this done, you need to focus on the 3 steps of working with Legacy Code:

1. Add the missing tests
2. Refactor the code
3. Implement the new feature

It’s also a great kata to try [the approval tests technique](https://understandlegacycode.com/blog/3-steps-to-add-tests-on-existing-code-when-you-have-short-deadlines/).

### 2\. The Tennis

![](https://understandlegacycode.com/_astro/tennis.DniyVtCG_15gkoT.webp)

This one is great to practice **an authentic time constraint**.

👉 [github.com/emilybache/Tennis-Refactoring-Kata](https://github.com/emilybache/Tennis-Refactoring-Kata)

You’re working for an imaginary consulting company. A colleague of yours spent 8.5h implementing a Tennis scoring software. This colleague is ill and you need to take over. You only have 1.5h left in the budget to clean the code and make it maintainable. What will you do?

Again: no HTTP, no database, no randomness. Just pure, tangled logic to refactor. Although the Tennis scoring rules are *a little bit* more complex than the Gilded Rose kata (in my opinion).

A few characteristics of this exercise:

- Tests are already here, so you can focus on **pure refactoring** techniques.
- There are 3 variants that showcase different code smells and challenges.
- At the end of the kata, do a retrospective to list what were the smells you spotted and how you refactored the design. Why is it better? How would that help?

### 3\. The Trip Service

![](https://understandlegacycode.com/_astro/trip-service.D1DbK0pv_Z1P5xEb.webp)

I like this one because **it adds nasty dependencies to the mix**.

👉 [github.com/sandromancuso/trip-service-kata](https://github.com/sandromancuso/trip-service-kata)

The logic of this one is not really complex. What makes it challenging are the problematic dependencies: the code you need to test depends on HTTP calls and database requests!

Well, actually, it *simulates* the problematic dependencies.

There’s no actual call to a third-party service, neither you’ll have to set up a database. But these “calls” will throw an error. So the whole thing is hard to test 😏

Databases, HTTP, randomness… These are difficult to test. That’s what makes your life miserable when dealing with real-life Legacy Code.

This kata is great because you’ll learn **how to break dependencies** when you don’t have tests!

I recommend you practice this one again and again. Practice until you feel confident enough to break a problematic dependency.

### 4\. The Expense Report

![](https://understandlegacycode.com/_astro/expense-report.CAjx2eFl_2fsE30.webp)

Similar to the Trip Service kata, this one adds annoying elements to the code.

👉 [github.com/christianhujer/expensereport](https://github.com/christianhujer/expensereport)

You will quickly realize that the code is printing directly into stdout, which makes it painful to test—at best, you would have noisy logs in the middle of your test reports.

It’s a good playground to learn how to break that kind of dependencies, so you can focus on refactoring the core logic.

### 5\. The Trivia Game

![](https://understandlegacycode.com/_astro/trivia-game.DByyLGDH_Z264ATY.webp)

*(Source: [“Christmas Story, the trivia game”](https://www.flickr.com/photos/sowrey/38594771684) by Geoff Sowrey)*

This is the typical kata people practice during a Legacy Code Retreat.

👉 [github.com/jbrains/trivia](https://github.com/jbrains/trivia)

It combines previous techniques into a very comprehensive exercise:

- No tests
- Non-trivial logic
- Usage of `stdout` and randomness to create problematic dependencies

I like how it looks more like an actual legacy codebase—except it’s not 600k lines long.

**I don’t recommend starting with this kata.**

Unless you have a mentor.

If you don’t, practice the previous exercises. Multiple times. When you can comfortably test, refactor and redesign existing code, then it’s a good time to tackle this one.

## 2 bonus “realistic” Katas

The coding katas I presented you so far are good sandboxes to practice your refactoring skills. However, they are simplified playgrounds. In my experience, they don’t look too much like code you would actually face in production—which is fine.

Except maybe for the Trivia kata.

Thus, if you are looking for more, I have two more coding exercises for you.

### 1\. The “Baby Steps” Timer (front-end)

![](https://understandlegacycode.com/_astro/baby-steps-timer.BqMQRcbc_Z1T4YWd.webp)

This one is not really famous, but I really like it.

If you want **to work with *front-end* Legacy Code, this is the best**.

👉 [github.com/dtanzer/babystepstimer](https://github.com/dtanzer/babystepstimer)

It’s an actual timer with a few characteristics:

- You can move the timer window around with your mouse.
- Once you start the timer, the window stays always on top.
- When the timer counts down to zero, it becomes red.
- Before the timer counts down to zero, you can press “Reset” in the timer window.

Therefore, if you try the TypeScript version, you’ll have to deal with the browser environment and API.

How do you write tests on such code? How can you break the dependency on the browser with minimal changes? Can you separate the pure logic from the browser stuff?

I’m sure you’ll learn a lot about modeling a front-end application, without relying on a modern framework—you won’t need it.

### 2\. The Lift Pass Pricing (API)

![](https://understandlegacycode.com/_astro/lift-pass-pricing.BiGv7avT_Z24BLbV.webp)

Finally, this is a one to practice refactoring back-end APIs.

👉 [github.com/martinsson/Refactoring-Kata-Lift-Pass-Pricing](https://github.com/martinsson/Refactoring-Kata-Lift-Pass-Pricing)

It exposes 2 routes and involves an actual (MariaDB) database. The app calculates the pricing for ski lift passes. There’s some intricate logic linked to what kind of lift pass you want, your age, and the specific date on which you’d like to ski.

There’s a new feature request: be able to get the price for several lift passes, not just one.

There typically are a few steps, you could do any of them:

1. Cover with high-level tests.
2. Refactor the code to maximize unit testability and reuse for the new feature
3. Pull down most of the high-level tests
4. Implement the new feature using unit tests and 1 or 2 high-level tests.

#### 💡 Tips for solving this one

Pretty much like the other ones involving annoying dependencies, the key here is to separate the core logic from its adherence to the HTTP/REST framework and from the SQL specificities. This is sometimes called **Hexagonal Architecture** and it facilitates respecting the **Testing Pyramid** which is not currently possible - there can be only top-level tests.

The typical workflow would be:

1. Cover everything from the HTTP layer, use a real DB
2. Separate request data extraction and sending the response from the logic
3. Extract a method with pure logic, move that method to an object (ex `PricingLogic`)
4. Now extract the SQL stuff from `PricingLogic`, first to some method with a signature that has nothing to do with SQL, then move these methods to a new class (ex `PricingDao`)
5. There should be ~3/4 elements, the HTTP layer should have the `PricingLogic` as an injected dependency and the `PricingLogic` should have the `PricingDao` as an injected dependency.
6. Move the bulk of the high-level tests down onto `PricingLogic` using a fake dao, and write some focused integration tests for the `PricingDao` using a real DB, there should be only a handful.

Now the HTTP layer and the integration of the parts can be tested with very few (one or two) high-level tests.

---

These are the few katas I use and recommend for developers who want to hone their refactoring skills.

So go ahead, pick one and start cleaning that Legacy Code 👊

---

Written by [**Nicolas Carlo**](https://bsky.app/profile/nicoespeon.com) who lives and works in Montreal, Canada 🍁
He founded the [Software Crafters Montreal](https://guild.host/software-crafters-montreal) community which cares about building maintainable softwares.

---

## Similar articles that will help you…

[← Find more tips to work with Legacy Code](https://understandlegacycode.com/)
