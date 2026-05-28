---
title: "Jujutsu megamerges for fun and profit"
source: "https://isaaccorbrey.com/notes/jujutsu-megamerges-for-fun-and-profit"
author:
published:
created: 2026-04-22
description: "A practical guide to creating and maintaining powerful megamerge workflows in Jujutsu for faster, conflict-free development."
tags:
  - "clippings"
---

> [!summary]
> The "megamerge" Jujutsu workflow builds an octopus merge commit on top of every branch you care about, so your working copy is always the combined state of all WIP — no branch-switching, no surprise merge conflicts at PR time, and drive-by fixes land wherever they belong via `jj absorb` or `jj squash --interactive`. A `restack` alias (`rebase --onto trunk() --source "roots(trunk()..) & mutable()"`) keeps the whole tree rebased onto trunk without rewriting commits you don't own, making multi-stream development with other people's branches ergonomic.

*This article is written both for intermediate Jujutsu users and for Git users who are curious about Jujutsu.*

I’m a big [Jujutsu](https://jj-vcs.github.io/jj/latest) user, and I’ve found myself relying more and more on what we in the JJ community colloquially call the “megamerge” workflow for my daily development. It’s surprisingly under-discussed outside of a handful of power users, so I wanted to share what that looks like and why it’s so handy, especially if you’re in a complex dev environment or tend to ship lots of small PRs.

*In a hurry? [Skip to the end](#tldr) for some quick tips.*

## Merge commits aren’t what you think they are

If you’re an average Git user (or even a Jujutsu user who hasn’t dug too deep into more advanced workflows), you may be surprised to learn that there is absolutely nothing special about a merge commit. It’s not some special case that has its own rules. It’s just a normal commit that has multiple parents. It doesn’t even have to be empty![^1]

```ansi
@  myzpxsys Isaac Corbrey 12 seconds ago 634e82e2
│  (empty) (no description set)
○    mllmtkmv Isaac Corbrey 12 seconds ago git_head() 947a52fd
├─╮  (empty) Merge the things
│ ○  vqsqmtlu Isaac Corbrey 12 seconds ago f41c796e
│ │  deps: Pin quantum manifold resolver
○ │  tqqymrkn Isaac Corbrey 19 seconds ago 0426baba
├─╯  storage: Align transient cache manifolds
◆  zzzzzzzz root() 00000000
```

Gotta put it all together!

You may be even more surprised to learn that merge commits are not limited to having two parents. We unofficially call merge commits with three or more parents “octopus merges”, and while you may be thinking to yourself “in what world would I want to merge more than two branches?”, this is actually a really powerful idea. Octopus merges power the entire megamerge workflow!

## So what the hell is a megamerge?

Basically, in the megamerge workflow you are rarely working directly off the tips of your branches. Instead, you create an octopus merge commit (hereafter referred to as “the megamerge”) as the child of every working branch you care about. This means bugfixes, feature branches, branches you’re waiting on PRs for, other peoples’ branches you need your code to work with, local environment setup branches, even private commits that may not be or belong in any branch. *Everything* you care about goes in the megamerge. It’s important to remember that **you don’t push the megamerge**, only the branches it composes.

```ansi
@  mnrxpywt Isaac Corbrey 25 seconds ago f1eb374e
│  (empty) (no description set)
○      wuxuwlox Isaac Corbrey 25 seconds ago git_head() c40c2d9c
├─┬─╮  (empty) megamerge
│ │ ○  ttnyuntn Isaac Corbrey 57 seconds ago 7d656676
│ │ │  storage: Align transient cache manifolds
│ ○ │  ptpvnsnx Isaac Corbrey 25 seconds ago 897d21c7
│ │ │  parser: Deobfuscate fleem tokens
│ ○ │  zwpzvxmv Isaac Corbrey 37 seconds ago 14971267
│ │ │  infra: Refactor blob allocator
│ ○ │  tqxoxrwq Isaac Corbrey 57 seconds ago 90bf43e4
│ ├─╯  io: Unjam polarity valves
○ │  moslkvzr Isaac Corbrey 50 seconds ago 753ef2e7
│ │  deps: Pin quantum manifold resolver
○ │  qupprxtz Isaac Corbrey 57 seconds ago 5332c1fd
├─╯  ui: Defrobnicate layout heuristics
○  wwtmlyss Isaac Corbrey 57 seconds ago 5804d1fd
│  test: Add hyperfrobnication suite
◆  zzzzzzzz root() 00000000
```

Scary! Too much merge!

It’s okay if this sounds like a lot. After all, you know how much effort you put into switching contexts if you have to revisit an old PR to get it reviewed, among other things. However, this enables a few really valuable things for you:

1. **You are always working on the combined sum of all of your work.** This means that if your working copy compiles and runs without issue, you know that your work will all interact without issue.
2. **You rarely have to worry about merge conflicts.** You already don’t need to worry about merge conflicts a ton since conflicts are a first-class concept in Jujutsu, but since you’re literally always merging your changes together you’ll never be struck with surprise merge conflicts on the forge side. There might be the occasional issue with contributors’ changes, but in my experience this hasn’t been a major problem.
3. **There’s way less friction when switching between tasks.** Since you’re always working on top of the megamerge, you never need to go to your VCS to switch tasks. You can just go edit what you need to. This also means it’s way easier to make small PRs for drive-by refactors and bugfixes.
4. **It’s easier to keep your branches up to date.** With a little magic, you can keep your entire megamerge up to date with your trunk branch with a single rebase command. I’ll show you how to do that later on.

## How do I make one?

Starting a megamerge is super simple: just make a new commit with each branch you want in the megamerge as a parent. I like to give that commit a name and leave it empty, like so:

```sh
jj new x y z
jj commit --message "megamerge"
```
<iframe src="https://asciinema.org/a/791783/iframe?" allowfullscreen="true" title="Terminal session recording"></iframe>

Making megamerges. It's not so hard after all!

You’re then left with an empty commit on top of this whole thing. This is where you do your work! Anything above the megamerge commit is considered WIP. You’re free to split things out as you need to, make multiple branches based on that megamerge commit, whatever you want to do. Everything you write will be based on the sum of everything within the megamerge, just like we wanted!

Of course, at some point you’ll be happy with what you have, and you’ll be left wondering:

## How do I actually submit my changes?

How you get your WIP changes into your megamerge depends on where they need to land. If you’re making changes that should land in existing changes, you can use the `squash` command with the `--to` flag to shuffle them into the right downstream commits. If your commit contains multiple commits’ worth of changes, you can either `split` it out into multiple commits before squashing them or (what I prefer) interactively squash with `squash --interactive` to just pick out the specific pieces to move.

```sh
# Squash an entire WIP commit (defaults to \`--from @\`)
jj squash --to x --from y

# Interactively squash part of a WIP commit (defaults to \`--from @\`)
jj squash --to x --from y --interactive
```
<iframe src="https://asciinema.org/a/791782/iframe?" allowfullscreen="true" title="Terminal session recording"></iframe>

Hunk, I choose you!

Of course, Jujutsu is a beautiful piece of software and has some automation for this! The `absorb` command will do a lot of this for you by identifying which downstream mutable commit each line or hunk of your current commit belong in and **automatically squashing them down for you**. This feels like magic every time I use it (and not the evil black box black magic kind of magic where nothing can be understood), and it’s one of the core pieces of Jujutsu’s functionality that make the megamerge workflow so seamless.

```sh
# Automagically autosquash your changes (defaults to \`--from @\`)
jj absorb --from x
```
<iframe src="https://asciinema.org/a/xYC1SQupOHOH2Y7i/iframe?" allowfullscreen="true" title="Terminal session recording"></iframe>

Ope, that was fast.

Absorbing won’t always catch everything in your commit, but it’ll usually get at least 90% of your changes. The rest are either easily squashable downstream or unrelated to any previous commit.

Conveniently, things aren’t much more complicated if I have changes that belong in a new commit. If the commit belongs in one of the branches I’m working on, I can just rebase it myself and move the bookmark accordingly.

```sh
jj commit
jj rebase --revision x --after y --before megamerge
jj bookmark move --from y --to x
```

Let’s break that rebase down to better understand how it works:

```ini
# We're gonna move some commits around!
jj rebase
    # Let's move our WIP commit(s) x...
    --revision x
        # so that they come after y (e.g. trunk())...
        --after y
            # and become a parent of the megamerge.
            --before megamerge
```
<iframe src="https://asciinema.org/a/954708/iframe?" allowfullscreen="true" title="Terminal session recording"></iframe>

A little bit of rocket surgery, as a treat.

If I’ve started work on an entirely new feature or found an unrelated bug to fix, then it’s even simpler! Using a few aliases, I can super easily include new changes in my megamerge:[^2]

```toml
[revset-aliases]
# Returns the closest merge commit to \`to\`
"closest_merge(to)" = "heads(::to & merges())"

[aliases]
# Inserts the given revset as a new branch under the megamerge.
stack = ["rebase", "--after", "trunk()", "--before", "closest_merge(@)", "--revision"]
```

Here’s a quick explanation of what `closest_merge(to)` is actually doing:

```ini
heads(                 # Return only the topologically tip-most commit within...
      ::to             # the set of all commits that are ancestors of \`to\`...
           & merges()) # ...that are also merge commits.
```

Using that revset alias, `stack` lets us target any revset we want and insert it between `trunk()` (your main development branch) and our megamerge commit:

```sh
jj stack x::y
```
<iframe src="https://asciinema.org/a/954709/iframe?" allowfullscreen="true" title="Terminal session recording"></iframe>

Whoa, that was neat!

This is more useful if I have *multiple* stacks of changes I want to include in parallel; if it’s just one, I have another alias that just gets the entire stack of changes after the megamerge:

```toml
[aliases]
stage = ["stack", "closest_merge(@)+:: ~ empty()"]
```
```ini
closest_merge(@)+::           # Return the descendants of the closest merge
                              # commit to the working copy...
                    ~ empty() # ...without any empty commits.
```

This one doesn’t require any input! Just have your commits ready and stage ‘em:

```sh
jj stage
```
<iframe src="https://asciinema.org/a/954710/iframe?" allowfullscreen="true" title="Terminal session recording"></iframe>

Wait, what? You can do that?

The last missing piece of this megamerge puzzle is (unfortunately) dealing with the reality that is *other people*:

## How do I keep all this crap up to date?

That’s a great question, and one I spent a couple months trying to answer in a general sense. Jujutsu has a really easy way of rebasing your entire working tree onto your main branch:

```sh
jj rebase --onto trunk()
```
<iframe src="https://asciinema.org/a/954717/iframe?" allowfullscreen="true" title="Terminal session recording"></iframe>

Nice.

However, this only works if your entire worktree is *your* changes. When you try to reference commits you don’t own (like untracked bookmarks or other people’s branches) Jujutsu will stop early to protect them from being rewritten.[^3]

<iframe src="https://asciinema.org/a/954718/iframe?" allowfullscreen="true" title="Terminal session recording"></iframe>

Wait, not so nice. How do I do this?

Let’s fix that by rebasing only the commits we actually control. I struggled with this one for a while, but thankfully the Jujutsu community is awesome. Kudos to [Stephen Jennings](https://jennings.io/) for coming up with this awesome revset:

```toml
[aliases]
restack = ["rebase", "--onto", "trunk()", "--source", "roots(trunk()..) & mutable()", "--simplify-parents"]
```
```ini
roots(                       # Get the furthest upstream commits...
      trunk()..)             # ...in the set of all descendants of ::trunk()...
                 & mutable() # ...and only return ones we're allowed to modify.
```

Rather than trying to rebase our entire working tree (like `jj rebase --onto trunk()` tries to do), this alias only targets commits we’re actually allowed to move. This leaves behind branches that we don’t control as well as work that’s stacked on top of other people’s branches. With `--simplify-parents` we also can clean up any gross edges left behind by this process. It has yet to fail me, even with monster ninefold mixed-contributor megamerges! (Say that five times fast.)

<iframe src="https://asciinema.org/a/954721/iframe?" allowfullscreen="true" title="Terminal session recording"></iframe>

There we go, that's better!

## TL;DR

Jujutsu megamerges are super cool and let you work on many different streams of work simultaneously. Read the whole article for an in-depth explanation of how they work. For a super ergonomic setup, add these to your config with `jj config edit --user`:

```toml
[revset-aliases]
"closest_merge(to)" = "heads(::to & merges())"

[aliases]
# \`jj stack <revset>\` to include specific revs
stack = ["rebase", "--after", "trunk()", "--before", "closest_merge(@)", "--revision"]

# \`jj stage\` to include the whole stack after the megamerge
stage = ["stack", "closest_merge(@)+:: ~ empty()"]

# \`jj restack\` to rebase your changes onto \`trunk()\`
restack = ["rebase", "--onto", "trunk()", "--source", "roots(trunk()..) & mutable()", "--simplify-parents"]
```

Use `absorb` and/or `squash --interactive` to get new changes into existing commits, `commit` and `rebase` to make new commits under your megamerge, and `commit` with `stack` or `stage` to move entire branches into your megamerge.[^4]

```sh
# Changes that belong in existing commits
jj absorb
jj squash --to x --interactive

# Changes that belong in new commits
jj rebase --revision y --after x

# Stack anything on top of the megamerge into it
jj stage

# Stack specific revsets into the megamerge
jj stack w::z
```

Remember that megamerges aren’t really meant to be pushed to your remote; they’re just a convenient way of showing yourself the whole picture. You’ll still want to publish branches individually as usual.

<iframe src="https://asciinema.org/a/954722/iframe?" allowfullscreen="true" title="Terminal session recording"></iframe>

I live in this constantly, and you can too.

Megamerges may not be everyone’s cup of tea – I’ve certainly gotten a few horrified looks after showing my working tree – but once you try them, you’ll likely find they let you bounce between tasks with almost no effort. Give them a try!

## Errata

- I completely forgot about `--simplify-parents` on `restack`! This makes it so you can get a clean log after restacking your commits by eliminating redundant edges (e.g. if A-B-C and A-C exist, `simplify-parents` will eliminate A-C).
- `stage` should be using `closest_merge(@)+::`, not `closest_merge(@)..` as you don’t want to pull in everything from all time! `x..` does technically include `x+::`, but it’s equivalent to `~::x`, which includes **anything that isn’t a direct ancestor of `x`!**

Special thanks to [msmetko](https://terra-incognita.blog/), [Cole Helbling](https://github.com/cole-h), [Hardy Jones](https://github.com/joneshf), [Alpha Chen](https://git.kejadlen.dev/alpha), Jeremy Brown, [Luke Randall](https://hachyderm.io/@ldrndll), 789.ha, and [Philip Metzger](https://philipmetzger.github.io/) for reading early drafts and sharing their feedback! We all see further by standing on the shoulders of giants.

I like building tools, breaking workflows, and putting them back together better. If you enjoy my work and want to support it, you can [buy me a coffee ☕](https://ko-fi.com/icorbrey) or [support me on Liberapay 💛](https://liberapay.com/isaaccorbrey.com).

## 9 Comments

Join the conversation [over on BlueSky!](https://bsky.app/profile/did:plc:zviscnpwyvj6y32agi5davn5/post/3mjxfw4kvuc2f)

- [![chrisvanderloo.com](https://cdn.bsky.app/img/avatar/plain/did:plc:3u26lcxyhiyq3ygsfyrc7xx2/bafkreie2gr6u2ifdqgfmesp2xl2pznxgvzhmvkchw7l2x7utqvtvetffn4)](https://bsky.app/profile/did:plc:3u26lcxyhiyq3ygsfyrc7xx2)
	[Chris van der Loo @chrisvanderloo.com](https://bsky.app/profile/did:plc:3u26lcxyhiyq3ygsfyrc7xx2)
	Really well written post, Isaac! I did not know about the absorb command, nor did I know you could just create a commit on top of a bunch of other commits like that. I will definitely be trying this out.
	- [![isaaccorbrey.com](https://cdn.bsky.app/img/avatar/plain/did:plc:zviscnpwyvj6y32agi5davn5/bafkreieaarw2nsnz5p352fnfbjk6ubkp6myav3fbjktdxq5y6t5wkecizm)](https://bsky.app/profile/did:plc:zviscnpwyvj6y32agi5davn5)
		[Isaac Corbrey @isaaccorbrey.com](https://bsky.app/profile/did:plc:zviscnpwyvj6y32agi5davn5)
		Thank you! Absorb is awesome, and yep! Commits in JJ are way more flexible than some people realize 😁
		- [![caleb.jasik.xyz](https://cdn.bsky.app/img/avatar/plain/did:plc:3tkrsjzdao4vqjrxwzynbfnu/bafkreieznlkmdqdhbxo6mm6d2kh6d37xesh3hyward4v2mgmk627yqgz2y)](https://bsky.app/profile/did:plc:3tkrsjzdao4vqjrxwzynbfnu)
			[caleb @caleb.jasik.xyz](https://bsky.app/profile/did:plc:3tkrsjzdao4vqjrxwzynbfnu)
			it really is nice being able to interact with my commit graph as if I was using refactor tools on regular code
- [![quicksnap-bsky.bsky.social](https://cdn.bsky.app/img/avatar/plain/did:plc:d3oqwxoact6yymphduc2ls72/bafkreibopwzjxffj3fvimxwtaze7gnt3f2lmfylgr6pb6iaraa55wjxpf4)](https://bsky.app/profile/did:plc:d3oqwxoact6yymphduc2ls72)
	[@quicksnap-bsky.bsky.social](https://bsky.app/profile/did:plc:d3oqwxoact6yymphduc2ls72)
	Thanks for the awesome article! One more step for JJ taking over the industry:)
	- [![isaaccorbrey.com](https://cdn.bsky.app/img/avatar/plain/did:plc:zviscnpwyvj6y32agi5davn5/bafkreieaarw2nsnz5p352fnfbjk6ubkp6myav3fbjktdxq5y6t5wkecizm)](https://bsky.app/profile/did:plc:zviscnpwyvj6y32agi5davn5)
		[Isaac Corbrey @isaaccorbrey.com](https://bsky.app/profile/did:plc:zviscnpwyvj6y32agi5davn5)
		Of course!
- [![canoewithwheels.bsky.social](https://cdn.bsky.app/img/avatar/plain/did:plc:6aoxcmaccqn6kl6rgt3vhorl/bafkreie7y2d4gcob5ujiuk7eyz554zsvpmspnhji227l6vaw2xkx77wxli)](https://bsky.app/profile/did:plc:6aoxcmaccqn6kl6rgt3vhorl)
	[CanoeWithWheels @canoewithwheels.bsky.social](https://bsky.app/profile/did:plc:6aoxcmaccqn6kl6rgt3vhorl)
	I’ve used jj and [@gitbutler.com](https://bsky.app/profile/did:plc:34rtbtb3dyhcdkevur5zvvzu) over the last year. Both have nice, ergonomic workflows. Both have corrupted history several times (gh at least twice a week). I think jj wins in its ability to solve merge conflicts repeatedly but I really like the polish of gb.
- huh,
	\`jj log -r "closest\_merge(@)+.. ~ empty()"\`
	returns a bunch of branches of coworkers for me, and
	\`jj log -r "closest\_merge(@)+:: ~ empty()"\`
	(:: vs..)
	returns only my changes on top of the megamerge.
	am i missing something? it seems to me like:: is more what i'd want
	- [![isaaccorbrey.com](https://cdn.bsky.app/img/avatar/plain/did:plc:zviscnpwyvj6y32agi5davn5/bafkreieaarw2nsnz5p352fnfbjk6ubkp6myav3fbjktdxq5y6t5wkecizm)](https://bsky.app/profile/did:plc:zviscnpwyvj6y32agi5davn5)
		[Isaac Corbrey @isaaccorbrey.com](https://bsky.app/profile/did:plc:zviscnpwyvj6y32agi5davn5)
		Yeah the latter is what you want. Will you check the article and see if what's in there right now matches that? I thought I had updated this.

[^1]: In Git, merge commits that contain new changes outside of conflict resolution are called an “evil merge”. Evil merges [aren’t really “evil” in Jujutsu](https://jj-vcs.github.io/jj/latest/conflicts/#advantages) since it has a more consistent model than Git.[^5]

```ansi
Commit ID: b976b2a9c6ebbaada7fcd9d112a8390f2cb75b54
Change ID: tqxoxrwqqqtmxvywmzmspstupqqkskqk
Author   : Isaac Corbrey <isaac@isaaccorbrey.com> (28 minutes ago)
Committer: Isaac Corbrey <isaac@isaaccorbrey.com> (24 minutes ago)
Parent   : ttnyuntn storage: Align transient cache manifolds
Parent   : qupprxtz ui: Defrobnicate layout heuristics

    io: Unjam polarity valves

Added regular file two.txt:
        1: # Sphinx of black quartz, judge my vow
```

Bubble, bubble, toil and trouble.

Definitely tangential, but I felt it necessary to mention.

[^2]: Aliases are a super powerful part of Jujutsu. There are two types you should look into: [revset aliases](https://jj-vcs.github.io/jj/latest/revsets/#aliases), which allow you to create custom functions which return one or more commits with the [revset language](https://jj-vcs.github.io/jj/latest/revsets), and [command aliases](https://jj-vcs.github.io/jj/latest/config/#aliases), which let you extend Jujutsu’s default functionality and add your own.

There are also template aliases which let you change how Jujutsu logs to the terminal using the [templating language](https://docs.jj-vcs.dev/latest/templates), and fileset aliases, which act similarly to revset aliases but act on files instead of revisions using the [fileset language](https://docs.jj-vcs.dev/latest/filesets)

[^3]: Jujutsu has a concept of *mutable* and *immutable* commits, which basically dictates what commits you’re allowed to modify on a normal basis. It’s largely just a lint since you can override this with `--ignore-immutable`, but it’s good at keeping you out of trouble. You can use the [`mutable()` and `immutable()` aliases](https://jj-vcs.github.io/jj/latest/revsets/#built-in-aliases) to select only mutable and immutable commits respectively.

[^4]: If `restack` doesn’t quite work the way you like, try incorporating [this config from Austin Seipp](https://github.com/thoughtpolice/a/blob/2f768e1b0407bc63d6dd01097ff1c5210e48d8f6/tilde/aseipp/dotfiles/jj/config.toml#L98-L104). My default setup restacks every mutable commit in your repo, which behaves poorly when you have lots of mutable branches from the past you haven’t had time to clean up yet.

```toml
[revset-aliases]
'stack()' = 'stack(@)'
'stack(x)' = 'stack(x, 2)'
'stack(x, n)' = 'ancestors(reachable(x, mutable()), n)'

[aliases]
restack = ["rebase", "--onto", "trunk()", "--source", "roots(trunk()..) & stack()"]
```

Thanks for the tip Cole!

[^5]: Thanks to [Andrew Hoog](https://www.andrewhoog.com/posts/how-to-annotate-blog-posts-with-footnotes-in-astro) for helping me figure out footnotes in Astro. Did you know that you can reference footnotes from other footnotes?
