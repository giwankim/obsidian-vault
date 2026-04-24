---
title: "Laws of Software Engineering"
source: "https://lawsofsoftwareengineering.com/"
author:
  - "[[Dr. Milan Milanović]]"
published:
created: 2026-04-22
description: "A collection of principles and patterns that shape software systems, teams, and decisions."
tags:
  - "clippings"
---

> [!summary]
> A curated index of ~40 named "laws" of software engineering — Conway's, Hyrum's, Gall's, CAP, Brooks's, Postel's, Hanlon's, Cunningham's, and others — grouped by domain (Teams, Architecture, Planning, Quality, Design, Decisions). Each entry is a one-line statement of the principle with a link out to a dedicated page; useful as a reference shelf or as conversation vocabulary rather than as a standalone read.

Level

Category

Teams

## [Conway's Law](https://lawsofsoftwareengineering.com/laws/conways-law/)

Organizations design systems that mirror their own communication structure.

Planning

## [Premature Optimization (Knuth's Optimization Principle)](https://lawsofsoftwareengineering.com/laws/premature-optimization/)

Premature optimization is the root of all evil.

Architecture

## [Hyrum's Law](https://lawsofsoftwareengineering.com/laws/hyrums-law/)

With a sufficient number of API users, all observable behaviors of your system will be depended on by somebody.

Quality

## [The Boy Scout Rule](https://lawsofsoftwareengineering.com/laws/boy-scout-rule/)

Leave the code better than you found it.

Design

## [YAGNI (You Aren't Gonna Need It)](https://lawsofsoftwareengineering.com/laws/yagni/)

Don't add functionality until it is necessary.

Teams

## [Brooks's Law](https://lawsofsoftwareengineering.com/laws/brooks-law/)

Adding manpower to a late software project makes it later.

Architecture

## [Gall's Law](https://lawsofsoftwareengineering.com/laws/galls-law/)

A complex system that works is invariably found to have evolved from a simple system that worked.

Architecture

## [The Law of Leaky Abstractions](https://lawsofsoftwareengineering.com/laws/law-of-leaky-abstractions/)

All non-trivial abstractions, to some degree, are leaky.

Architecture

## [Tesler's Law (Conservation of Complexity)](https://lawsofsoftwareengineering.com/laws/teslers-law/)

Every application has an inherent amount of irreducible complexity that can only be shifted, not eliminated.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#2563EB" opacity=".2"></circle><path d="M60 30 90 80H30z" stroke="#2563EB" stroke-width="3" fill="none"></path><circle cx="60" cy="30" r="5" fill="#2563EB"></circle><circle cx="30" cy="80" r="5" fill="#2563EB"></circle><circle cx="90" cy="80" r="5" fill="#2563EB"></circle><text x="60" y="38" text-anchor="middle" fill="#2563EB" font-size="8" font-weight="bold">C</text> <text x="28" y="92" text-anchor="middle" fill="#2563EB" font-size="8" font-weight="bold">A</text> <text x="92" y="92" text-anchor="middle" fill="#2563EB" font-size="8" font-weight="bold">P</text></svg> Architecture

## [CAP Theorem](https://lawsofsoftwareengineering.com/laws/cap-theorem/)

A distributed system can guarantee only two of: consistency, availability, and partition tolerance.

Architecture

## [Second-System Effect](https://lawsofsoftwareengineering.com/laws/second-system-effect/)

Small, successful systems tend to be followed by overengineered, bloated replacements.

Architecture

## [Fallacies of Distributed Computing](https://lawsofsoftwareengineering.com/laws/fallacies-of-distributed-computing/)

A set of eight false assumptions that new distributed system designers often make.

Architecture

## [Law of Unintended Consequences](https://lawsofsoftwareengineering.com/laws/law-of-unintended-consequences/)

Whenever you change a complex system, expect surprise.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#2563EB" opacity=".2"></circle><rect x="30" y="42" width="60" height="40" rx="3" stroke="#2563EB" stroke-width="2" fill="none"></rect><path d="M30 45 60 65 90 45" stroke="#2563EB" stroke-width="2" fill="none"></path><text x="22" y="38" fill="#2563EB" font-size="14" font-weight="bold">+</text> <text x="92" y="38" fill="#2563EB" font-size="14" font-weight="bold">+</text> <text x="22" y="92" fill="#2563EB" font-size="14" font-weight="bold">+</text> <text x="92" y="92" fill="#2563EB" font-size="14" font-weight="bold">+</text> <text x="57" y="98" fill="#2563EB" font-size="12" font-weight="bold">+</text></svg> Architecture

## [Zawinski's Law](https://lawsofsoftwareengineering.com/laws/zawinskis-law/)

Every program attempts to expand until it can read mail.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#D97706" opacity=".2"></circle><circle cx="60" cy="45" r="8" fill="#D97706"></circle><path d="M50 70q10-10 20 0" stroke="#D97706" stroke-width="3" fill="none"></path><circle cx="35" cy="40" r="5" fill="#D97706" opacity=".7"></circle><circle cx="85" cy="40" r="5" fill="#D97706" opacity=".7"></circle><circle cx="30" cy="60" r="5" fill="#D97706" opacity=".6"></circle><circle cx="90" cy="60" r="5" fill="#D97706" opacity=".6"></circle><circle cx="35" cy="80" r="5" fill="#D97706" opacity=".5"></circle><circle cx="85" cy="80" r="5" fill="#D97706" opacity=".5"></circle><circle cx="60" cy="85" r="5" fill="#D97706" opacity=".5"></circle><text x="60" y="105" text-anchor="middle" fill="#D97706" font-size="12" font-weight="bold">150</text></svg> Teams

## [Dunbar's Number](https://lawsofsoftwareengineering.com/laws/dunbars-number/)

There is a cognitive limit of about 150 stable relationships one person can maintain.

Teams

## [The Ringelmann Effect](https://lawsofsoftwareengineering.com/laws/ringelmann-effect/)

Individual productivity decreases as group size increases.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#D97706" opacity=".2"></circle><path d="M25 65H35L45 85 65 35H95" stroke="#D97706" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"></path><text x="78" y="55" fill="#D97706" font-size="18" font-weight="bold">N</text> <circle cx="40" cy="95" r="4" fill="#D97706"></circle><circle cx="52" cy="95" r="4" fill="#D97706"></circle><circle cx="64" cy="95" r="4" fill="#D97706" opacity=".5"></circle><circle cx="76" cy="95" r="4" fill="#D97706" opacity=".3"></circle><circle cx="88" cy="95" r="4" fill="#D97706" opacity=".2"></circle></svg> Teams

## [Price's Law](https://lawsofsoftwareengineering.com/laws/prices-law/)

The square root of the total number of participants does 50% of the work.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#D97706" opacity=".2"></circle><circle cx="60" cy="30" r="8" fill="#D97706"></circle><text x="60" y="34" text-anchor="middle" fill="#fff" font-size="10" font-weight="bold">?</text><line x1="60" y1="38" x2="40" y2="55" stroke="#D97706" stroke-width="2"></line> <line x1="60" y1="38" x2="80" y2="55" stroke="#D97706" stroke-width="2"></line><circle cx="40" cy="65" r="7" fill="#D97706"></circle><circle cx="80" cy="65" r="7" fill="#D97706"></circle><text x="40" y="69" text-anchor="middle" fill="#fff" font-size="9" font-weight="bold">⚙</text> <text x="80" y="69" text-anchor="middle" fill="#fff" font-size="9" font-weight="bold">⚙</text> <circle cx="30" cy="90" r="5" fill="#D97706" opacity=".7"></circle><circle cx="50" cy="90" r="5" fill="#D97706" opacity=".7"></circle><circle cx="70" cy="90" r="5" fill="#D97706" opacity=".7"></circle><circle cx="90" cy="90" r="5" fill="#D97706" opacity=".7"></circle></svg> Teams

## [Putt's Law](https://lawsofsoftwareengineering.com/laws/putts-law/)

Those who understand technology don't manage it, and those who manage it don't understand it.

Teams

## [Peter Principle](https://lawsofsoftwareengineering.com/laws/peter-principle/)

In a hierarchy, every employee tends to rise to their level of incompetence.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#D97706" opacity=".2"></circle><rect x="25" y="45" width="50" height="30" rx="3" fill="#D97706"></rect><rect x="30" y="50" width="10" height="10" fill="#fff" opacity=".8"></rect><rect x="45" y="50" width="10" height="10" fill="#fff" opacity=".8"></rect><rect x="60" y="50" width="10" height="10" fill="#fff" opacity=".8"></rect><circle cx="35" cy="75" r="5" fill="#D97706"></circle><circle cx="65" cy="75" r="5" fill="#D97706"></circle><circle cx="90" cy="50" r="8" fill="#D97706"></circle><text x="90" y="54" text-anchor="middle" fill="#fff" font-size="10" font-weight="bold">1</text> <path d="M85 70l5-8 5 8z" stroke="#D97706" stroke-width="2" fill="none"></path><line x1="90" y1="65" x2="90" y2="67" stroke="#D97706" stroke-width="2"></line><circle cx="90" cy="68.5" r=".5" fill="#D97706"></circle></svg> Teams

## [Bus Factor](https://lawsofsoftwareengineering.com/laws/bus-factor/)

The minimum number of team members whose loss would put the project in serious trouble.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#D97706" opacity=".2"></circle><path d="M25 45V85H95V45" stroke="#D97706" stroke-width="2" fill="none"></path><line x1="60" y1="45" x2="60" y2="85" stroke="#D97706" stroke-width="2"></line><circle cx="42" cy="58" r="6" fill="#D97706"></circle><rect x="35" y="68" width="14" height="12" rx="1" fill="#D97706" opacity=".6"></rect><text x="42" y="62" text-anchor="middle" fill="#fff" font-size="6" font-weight="bold">✓</text> <circle cx="78" cy="38" r="8" fill="#D97706"></circle><text x="78" y="42" text-anchor="middle" fill="#fff" font-size="8" font-weight="bold">?</text><path d="M78 50V62" stroke="#D97706" stroke-width="2"></path> <path d="M74 54l4-6 4 6" stroke="#D97706" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"></path><rect x="71" y="68" width="14" height="12" rx="1" stroke="#D97706" stroke-width="1.5" fill="none" stroke-dasharray="3 2"></rect></svg> Teams

## [Dilbert Principle](https://lawsofsoftwareengineering.com/laws/dilbert-principle/)

Companies tend to promote incompetent employees to management to limit the damage they can do.

Planning

## [Parkinson's Law](https://lawsofsoftwareengineering.com/laws/parkinsons-law/)

Work expands to fill the time available for its completion.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#7C3AED" opacity=".2"></circle><rect x="25" y="52" width="70" height="16" rx="8" stroke="#7C3AED" stroke-width="2" fill="none"></rect><rect x="27" y="54" width="58" height="12" rx="6" fill="#7C3AED" opacity=".7"></rect><text x="60" y="42" text-anchor="middle" fill="#7C3AED" font-size="14" font-weight="bold">90%</text> <text x="60" y="85" text-anchor="middle" fill="#7C3AED" font-size="12" font-weight="bold">+90%</text> <path d="M85 60h7" stroke="#7C3AED" stroke-width="2" stroke-linecap="round"></path><path d="M89 57l3 3-3 3" stroke="#7C3AED" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></svg> Planning

## [The Ninety-Ninety Rule](https://lawsofsoftwareengineering.com/laws/ninety-ninety-rule/)

The first 90% of the code accounts for the first 90% of development time; the remaining 10% accounts for the other 90%.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#7C3AED" opacity=".2"></circle><rect x="40" y="30" width="40" height="5" rx="1" fill="#7C3AED"></rect><rect x="40" y="85" width="40" height="5" rx="1" fill="#7C3AED"></rect><path d="M45 35V52L60 62 75 52V35" stroke="#7C3AED" stroke-width="2" fill="none"></path><path d="M45 85V68L60 58 75 68V85" stroke="#7C3AED" stroke-width="2" fill="none"></path><path d="M50 40v8l10 7 10-7V40" fill="#7C3AED" opacity=".4"></path><path d="M48 80V72l12-7 12 7v8" fill="#7C3AED" opacity=".7"></path><line x1="60" y1="58" x2="60" y2="65" stroke="#7C3AED" stroke-width="1.5"></line><path d="M85 45c10 0 10 30 0 30" stroke="#7C3AED" stroke-width="2" fill="none"></path><path d="M85 75l3-5m-3 5-4-5" stroke="#7C3AED" stroke-width="2" stroke-linecap="round"></path><text x="92" y="62" fill="#7C3AED" font-size="14" font-weight="bold">+</text></svg> Planning

## [Hofstadter's Law](https://lawsofsoftwareengineering.com/laws/hofstadters-law/)

It always takes longer than you expect, even when you take into account Hofstadter's Law.

Planning

## [Goodhart's Law](https://lawsofsoftwareengineering.com/laws/goodharts-law/)

When a measure becomes a target, it ceases to be a good measure.

Planning

## [Gilb's Law](https://lawsofsoftwareengineering.com/laws/gilbs-law/)

Anything you need to quantify can be measured in some way better than not measuring it.

Quality

## [Murphy's Law / Sod's Law](https://lawsofsoftwareengineering.com/laws/murphys-law/)

Anything that can go wrong will go wrong.

Quality

## [Postel's Law](https://lawsofsoftwareengineering.com/laws/postels-law/)

Be conservative in what you do, be liberal in what you accept from others.

Quality

## [Broken Windows Theory](https://lawsofsoftwareengineering.com/laws/broken-windows-theory/)

Don't leave broken windows (bad designs, wrong decisions, or poor code) unrepaired.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#047857" opacity=".2"></circle><rect x="30" y="40" width="60" height="40" rx="4" stroke="#047857" stroke-width="2" fill="none"></rect><rect x="30" y="50" width="60" height="8" fill="#047857" opacity=".4"></rect><text x="60" y="75" font-family="Arial" font-size="16" font-weight="bold" fill="#047857" text-anchor="middle">$</text> <path d="M60 25V35" stroke="#047857" stroke-width="2" stroke-linecap="round"></path><path d="M55 32l5 6 5-6" stroke="#047857" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path><path d="M85 55l10-5" stroke="#047857" stroke-width="1.5" stroke-linecap="round"></path><path d="M85 60H95" stroke="#047857" stroke-width="1.5" stroke-linecap="round"></path><path d="M85 65l10 5" stroke="#047857" stroke-width="1.5" stroke-linecap="round"></path><text x="60" y="100" font-family="Arial" font-size="10" fill="#047857" text-anchor="middle">%</text></svg> Quality

## [Technical Debt](https://lawsofsoftwareengineering.com/laws/technical-debt/)

Technical Debt is everything that slows us down when developing software.

Quality

## [Linus's Law](https://lawsofsoftwareengineering.com/laws/linuss-law/)

Given enough eyeballs, all bugs are shallow.

Quality

## [Kernighan's Law](https://lawsofsoftwareengineering.com/laws/kernighans-law/)

Debugging is twice as hard as writing the code in the first place.

Quality

## [Testing Pyramid](https://lawsofsoftwareengineering.com/laws/testing-pyramid/)

A project should have many fast unit tests, fewer integration tests, and only a small number of UI tests.

Quality

## [Pesticide Paradox](https://lawsofsoftwareengineering.com/laws/pesticide-paradox/)

Repeatedly running the same tests becomes less effective over time.

Quality

## [Lehman's Laws of Software Evolution](https://lawsofsoftwareengineering.com/laws/lehmans-laws/)

Software that reflects the real world must evolve, and that evolution has predictable limits.

Quality

## [Sturgeon's Law](https://lawsofsoftwareengineering.com/laws/sturgeons-law/)

90% of everything is crap.

Scale

## [Amdahl's Law](https://lawsofsoftwareengineering.com/laws/amdahls-law/)

The speedup from parallelization is limited by the fraction of work that cannot be parallelized.

Scale

## [Gustafson's Law](https://lawsofsoftwareengineering.com/laws/gustafsons-law/)

It is possible to achieve significant speedup in parallel processing by increasing the problem size.

Scale

## [Metcalfe's Law](https://lawsofsoftwareengineering.com/laws/metcalfes-law/)

The value of a network is proportional to the square of the number of users.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#0E7490" opacity=".2"></circle><circle cx="60" cy="60" r="14" fill="#0E7490"></circle><line x1="60" y1="46" x2="60" y2="28" stroke="#0E7490" stroke-width="2"></line><line x1="72" y1="52" x2="85" y2="38" stroke="#0E7490" stroke-width="2"></line><line x1="74" y1="60" x2="92" y2="60" stroke="#0E7490" stroke-width="2"></line><line x1="72" y1="68" x2="85" y2="82" stroke="#0E7490" stroke-width="2"></line><line x1="60" y1="74" x2="60" y2="92" stroke="#0E7490" stroke-width="2"></line><line x1="48" y1="68" x2="35" y2="82" stroke="#0E7490" stroke-width="2"></line><line x1="46" y1="60" x2="28" y2="60" stroke="#0E7490" stroke-width="2"></line><line x1="48" y1="52" x2="35" y2="38" stroke="#0E7490" stroke-width="2"></line><circle cx="60" cy="25" r="5" fill="#0E7490" opacity=".6"></circle><circle cx="88" cy="35" r="5" fill="#0E7490" opacity=".6"></circle><circle cx="95" cy="60" r="5" fill="#0E7490" opacity=".6"></circle><circle cx="88" cy="85" r="5" fill="#0E7490" opacity=".6"></circle><circle cx="60" cy="95" r="5" fill="#0E7490" opacity=".6"></circle><circle cx="32" cy="85" r="5" fill="#0E7490" opacity=".6"></circle><circle cx="25" cy="60" r="5" fill="#0E7490" opacity=".6"></circle><circle cx="32" cy="35" r="5" fill="#0E7490" opacity=".6"></circle><text x="60" y="64" text-anchor="middle" fill="#fff" font-size="12" font-weight="bold">1</text></svg> Design

## [DRY (Don't Repeat Yourself)](https://lawsofsoftwareengineering.com/laws/dry-principle/)

Every piece of knowledge must have a single, unambiguous, authoritative representation.

Design

## [KISS (Keep It Simple, Stupid)](https://lawsofsoftwareengineering.com/laws/kiss-principle/)

Designs and systems should be as simple as possible.

Design

## [SOLID Principles](https://lawsofsoftwareengineering.com/laws/solid-principles/)

Five main guidelines that enhance software design, making code more maintainable and scalable.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#0E7490" opacity=".2"></circle><circle cx="30" cy="60" r="12" fill="#0E7490"></circle><text x="27" y="64" font-size="10" font-weight="bold" fill="#fff" font-family="system-ui">A</text> <circle cx="60" cy="60" r="12" fill="#0E7490"></circle><text x="57" y="64" font-size="10" font-weight="bold" fill="#fff" font-family="system-ui">B</text> <circle cx="90" cy="60" r="12" fill="#0E7490" opacity=".4"></circle><text x="87" y="64" font-size="10" font-weight="bold" fill="#fff" font-family="system-ui" opacity=".6">C</text> <line x1="42" y1="60" x2="46" y2="60" stroke="#0E7490" stroke-width="3"></line><polygon points="48,55 48,65 54,60" fill="#0E7490"></polygon><line x1="72" y1="60" x2="76" y2="60" stroke="#0E7490" stroke-width="2" stroke-dasharray="2,2" opacity=".5"></line><path d="M42 45H78" stroke="#0E7490" stroke-width="1.5" stroke-dasharray="3,2" opacity=".3"></path><path d="M56 40l8 10" stroke="#0E7490" stroke-width="2.5" opacity=".6"></path><path d="M64 40 56 50" stroke="#0E7490" stroke-width="2.5" opacity=".6"></path></svg> Design

## [Law of Demeter](https://lawsofsoftwareengineering.com/laws/law-of-demeter/)

An object should only interact with its immediate friends, not strangers.

Design

## [Principle of Least Astonishment](https://lawsofsoftwareengineering.com/laws/principle-of-least-astonishment/)

Software and interfaces should behave in a way that least surprises users and other developers.

Decisions

## [Dunning-Kruger Effect](https://lawsofsoftwareengineering.com/laws/dunning-kruger-effect/)

The less you know about something, the more confident you tend to be.

Decisions

## [Hanlon's Razor](https://lawsofsoftwareengineering.com/laws/hanlons-razor/)

Never attribute to malice that which is adequately explained by stupidity or carelessness.

Decisions

## [Occam's Razor](https://lawsofsoftwareengineering.com/laws/occams-razor/)

The simplest explanation is often the most accurate one.

Decisions

## [Sunk Cost Fallacy](https://lawsofsoftwareengineering.com/laws/sunk-cost-fallacy/)

Sticking with a choice because you've invested time or energy in it, even when walking away helps you.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#64748B" opacity=".2"></circle><rect x="20" y="40" width="32" height="24" rx="1" fill="#64748B" opacity=".3"></rect><rect x="20" y="40" width="10" height="24" fill="#64748B" opacity=".15"></rect><rect x="42" y="40" width="10" height="24" fill="#64748B" opacity=".15"></rect><line x1="24" y1="48" x2="48" y2="48" stroke="#64748B" stroke-width="1.5"></line><line x1="24" y1="54" x2="48" y2="54" stroke="#64748B" stroke-width="1.5"></line><circle cx="36" cy="58" r="2" fill="#64748B"></circle><text x="60" y="58" text-anchor="middle" fill="#64748B" font-size="20" font-weight="bold">≠</text> <path d="M72 64 82 40 92 52l8-16V64z" fill="#64748B"></path><line x1="76" y1="64" x2="76" y2="56" stroke="#64748B" stroke-width="2"></line><circle cx="76" cy="54" r="4" fill="#64748B" opacity=".7"></circle><text x="36" y="78" text-anchor="middle" fill="#64748B" font-size="9" font-weight="bold">MAP</text> <text x="86" y="78" text-anchor="middle" fill="#64748B" font-size="9" font-weight="bold">REAL</text></svg> Decisions

## [The Map Is Not the Territory](https://lawsofsoftwareengineering.com/laws/map-is-not-the-territory/)

Our representations of reality are not the same as reality itself.

Decisions

## [Confirmation Bias](https://lawsofsoftwareengineering.com/laws/confirmation-bias/)

A tendency to favor information that supports our existing beliefs or ideas.

Decisions

## [The Hype Cycle & Amara's Law](https://lawsofsoftwareengineering.com/laws/hype-cycle-amaras-law/)

We tend to overestimate the effect of a technology in the short run and underestimate the impact in the long run.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#64748B" opacity=".2"></circle><path d="M35 30H85v5L65 55V65L85 85v5H35V85L55 65V55L35 35z" stroke="#64748B" stroke-width="2.5" fill="none"></path><path d="M42 35H78L62 50H58z" fill="#64748B" opacity=".4"></path><path d="M40 85H80L65 72H55z" fill="#64748B" opacity=".7"></path><path d="M88 60h12" stroke="#64748B" stroke-width="2.5" stroke-linecap="round"></path><path d="M96 55l5 5-5 5" stroke="#64748B" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"></path><text x="22" y="64" fill="#64748B" font-size="16" font-weight="bold">+</text></svg> Decisions

## [The Lindy Effect](https://lawsofsoftwareengineering.com/laws/lindy-effect/)

The longer something has been in use, the more likely it is to continue being used.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#64748B" opacity=".2"></circle><rect x="45" y="25" width="30" height="18" rx="2" stroke="#64748B" stroke-width="2" stroke-dasharray="3 2" opacity=".5"></rect><path d="M60 48V58" stroke="#64748B" stroke-width="2" stroke-linecap="round"></path><path d="M55 54l5 6 5-6" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"></path><rect x="25" y="70" width="20" height="20" rx="2" fill="#64748B" opacity=".8"></rect><rect x="50" y="70" width="20" height="20" rx="2" fill="#64748B" opacity=".8"></rect><rect x="75" y="70" width="20" height="20" rx="2" fill="#64748B" opacity=".8"></rect><text x="55" y="40" fill="#64748B" font-size="14" font-weight="bold">?</text></svg>Decisions

## [First Principles Thinking](https://lawsofsoftwareengineering.com/laws/first-principles-thinking/)

Breaking a complex problem into its most basic blocks and then building up from there.

Decisions

## [Inversion](https://lawsofsoftwareengineering.com/laws/inversion/)

Solving a problem by considering the opposite outcome and working backward from it.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#64748B" opacity=".2"></circle><circle cx="60" cy="60" r="30" fill="#64748B" opacity=".3"></circle><path d="M60 60V30A30 30 0 0188 50z" fill="#64748B"></path><text x="38" y="75" fill="#64748B" font-size="14" font-weight="bold">80%</text> <text x="62" y="48" fill="#fff" font-size="11" font-weight="bold">20%</text></svg> Decisions

## [Pareto Principle (80/20 Rule)](https://lawsofsoftwareengineering.com/laws/pareto-principle/)

80% of the problems result from 20% of the causes.

<svg width="120" height="120" viewBox="0 0 120 120" fill="none" style="width: 96px !important; height: 96px !important;"><circle cx="60" cy="60" r="50" fill="#64748B" opacity=".2"></circle><path d="M25 30H85q5 0 5 5V60q0 5-5 5H55L45 78V65H30q-5 0-5-5z" stroke="#64748B" stroke-width="2" fill="none"></path><text x="50" y="54" fill="#64748B" font-size="22" font-weight="bold">✗</text> <path d="M75 68l7 7" stroke="#64748B" stroke-width="2" stroke-linecap="round"></path><path d="M78 75h4V71" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"></path><circle cx="88" cy="82" r="12" fill="#64748B" opacity=".3"></circle><path d="M82 82l4 4 8-9" stroke="#64748B" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"></path></svg> Decisions

## [Cunningham's Law](https://lawsofsoftwareengineering.com/laws/cunninghams-law/)

The best way to get the correct answer on the Internet is not to ask a question, it's to post the wrong answer.
