---
title: "A practical guide to shipping with Claude Code"
source: "https://claude.dev/blog/the-work-after-you-open-a-pr/"
author:
  - "[[Addy Osmani]]"
published: 2026-11-24
created: 2026-11-25
description: "After you open a pull request, hand the follow up to Claude Code using /ship. Here's how to dial in your preferences to stay in flow."
tags:
  - "clippings"
---

> [!summary]
> Addy Osmani explains how to hand post-PR follow-up work (failing CI, review comments, merge conflicts) to Claude Code using the three Claude Ship agents: Code Review, PR Steward, and Claude Approvals. It covers `/code-review`, `/ship` (commit, push, open the PR, review it, then watch it for up to seven days) and `/steward` for existing PRs. It also shows how to turn repeated review comments into REVIEW.md rules, repeated setup into verify skills, and repeated PR maintenance into steward rules, and how a team can roll out an approval policy from monitoring to enforcement.

After you open a pull request, hand the follow up to Claude Code using /ship. Here's how to dial in your preferences to stay in flow.

When you open a pull request, there's usually a bunch of follow-up work to be done:

- CI fails
- A review comes back with six comments
- A main merge creates a conflict

They're all tiny little tasks, but each one takes you off your focus work.

On the Claude Code team, an agent commonly does this follow-up work. For example, it can pick up an issue a reviewer found, so when the author gets back, the PR has already been updated once.

In my experience this is a more productive and enjoyable way to code. It minimizes context switching and keeps me in a flow state.

We've talked about the process the Claude Code team uses for code review [here](https://claude.dev/blog/solving-code-review-at-anthropic/), and about the verification process underneath it [here](https://claude.dev/blog/how-the-claude-code-team-thinks-about-verification/). **This post is about getting your own repository set up to do this** using some of the new functionality we recently added with the [Claude Ship launch](https://claude.com/resources/articles/introducing-claude-ship).

It's for a developer or tech lead whose team works on GitHub and who doesn't have admin privileges. You can start on your own right now by running a few commands, and save what you learn to files in your repo for the team to review. Admins only need to get involved if your team wants agents doing this automatically on the team's PRs.

You're still the architect of the process, so you're defining what to build, how to build it, and what the bar for merging is.

## THE POST-PR PROCESS

After you've opened a PR, you want to find issues, address issues, and make a final decision on if the change can be merged.

Claude Ship is three agents that tackle this work: Code Review, PR Steward (beta), and Claude Approvals (beta). Code Review is generally available, and the other two are in beta. `/ship` is a command you run yourself in Claude Code to try Claude Ship on your own pull requests. It comes with the latest version of Claude Code, and it works even before an admin has turned on any of the agents. You can partially automate the first two steps today. The last step is a decision that you set in your branch protections and (if your team adopts one) your policy file. Here is how it breaks down using the three agents that are part of Claude Ship:

| You want Claude to | Run | Where it runs |
| --- | --- | --- |
| Find bugs before anyone else looks | `/code-review` | Your session |
| Open a PR, review it and keep working on what comes back | `/ship` | Your session |
| Look after a PR you already opened | `/steward` | Your session |
| Do this across a team's PRs automatically | Claude Ship | Anthropic's cloud by default, set up by your team |

## ON YOUR OWN PRS

### Getting started today with /code-review

If you only do one thing from this post, review your branch before you push it. Bugs you catch here are less likely to come back as review comments or failed checks that pull you off your next task. At the Claude Code prompt, enter this command:

```
/code-review
```

It reviews the commits on your branch and your uncommitted changes for correctness bugs. A few variations to keep in mind:

```
/code-review high 1234       # review PR 1234 at high effort
/code-review --fix           # apply the findings to your working tree
/code-review --comment 1234  # post the findings on the PR
/code-review ultra           # run a deeper review in the cloud
```

The effort goes from low to max. At low you only see the findings the review is most sure about. Go higher and you see more, including some it's less sure about. Claude remembers the last level you used, so if the risk changes, set it again.

A few caveats:

- You will want to take extra care when using the ultra setting, which runs in the cloud, needs a login at claude.ai, and can be billed separately from your plan. Read the [ultrareview docs](https://code.claude.com/docs/en/ultrareview) before trying it.
- Edits made by `--fix` during a background review may not be caught by `/rewind`. Commit first if you want an easy way back.
- Local `/code-review` reads your `CLAUDE.md` files, but not `REVIEW.md`. This matters later.

The first thing you should do is run `/code-review` a few times to understand what it catches and where it gets things wrong. You'll use this later.

### Run /ship for your next PR

Once you're ready, type:

```
/ship
```

If you don't have a PR for your branch yet, `/ship` will:

1. Commit your pending changes. It behaves as if you had run `git add -A`, so it will respect your `.gitignore`. It will create a branch if necessary, and it will use your session to write the commit message. You will be notified of this before the commit, and can abort by hitting Esc.
2. Push and create the PR as you.
3. Perform a code review using `/code-review`, unless the commit has already been reviewed by Code Review. If the code review reports any issues, it will fix the ones it judges as valid for you.
4. Watch the PR for up to seven days. It will work on failing checks, conflicts, and review comments, and will exit if the PR is merged or closed.

The first step, where `/ship` commits your pending changes as if you had run `git add -A`, sometimes catches people by surprise, so be sure to run `git status` before running `/ship`.

The command will not commit changes that touch files with names that look like secrets, or files that set rules, like `CLAUDE.md`, `REVIEW.md`, or anything in the `.claude/` or `.github/` directories. You will need to make these commits manually beforehand.

Also, if you are working in a public repository, the command will not commit any changes for you. You will need to commit any pending changes manually before you can proceed, and if the PR already exists, it won't include your pending changes.

**Optional: specifying effort level, PR, or bot**

```
/ship high            # run at high effort
/ship 41              # work on pull request #41
/ship +my-lint-bot    # also read comments from my-lint-bot
/ship stop            # end the watch
```

The command will by default read comments by you, people with write access, and the Claude GitHub App. You can specify additional bots in the form `+name`. If that bot comments, it will be treated as an assertion to check against the code.

#### Letting Claude watch the PR

Claude watches the PR as you, on your machine, and uses your quota. Closing your laptop stops it, so keep the session open and the machine awake. You'll also need to be logged in to the GitHub CLI (run `gh auth login` first), and it only watches a PR that you opened.

For anything other than [auto mode](https://code.claude.com/docs/en/permission-modes), [the watch](https://code.claude.com/docs/en/ship-command#what-claude-does-during-a-watch) stops at every prompt and requires your response. It won't watch in bypass-permissions mode. Note that on Windows, `/ship` opens the PR and reviews, but the watch doesn't start.

Ensure that the watch has its own checkout. You need to leave the branch checked out. If you're just going to jump straight into your next task, then make sure to use a separate worktree for one of them.

If the watch fails to start, Claude will explain why but still review the PR. For example, you can't run a watch if you have a `PreToolUse` or `PermissionRequest` hook on Bash in the `.claude/settings.json` of your repo.

Additionally, the watch uses up model turns while you're away, so it counts against your plan usage or API bill. The first time you use it, it's a good idea to be near your machine to make sure usage is within your expectations.

#### Only run the watch on repos you trust

The watch will merge the base branch into yours when necessary and then run commands like your tests. In other words, anyone who has the ability to land changes on the base branch has the ability to run commands on your machine during the watch. **Only run the watch locally on a repo where you trust everyone who can land changes on the base branch.**

Claude is told never to merge the PR, and Claude Code also constrains the gh and git commands it can run during an unattended turn, preventing direct merging or force-pushing. The watch's own commits also leave out the files that set the rules: `.github/`, `CODEOWNERS`, `CLAUDE.md`, `.claude/`, git hooks, etc.

However, this doesn't protect against all vectors. For example, the test script also runs under your credentials, and if you type a message during a turn, that will allow the constraints to be lifted for that turn. Additionally, if auto-merge is enabled, a fix from the watch could end up being what allows GitHub to merge.

Furthermore, the commits and pushes made by Claude during the watch are not affected by git hooks in your repo, so make sure any checks that need to be present are added to CI and branch rules.

For the full terms of the watch, run `/ship terms` in the product before your first time using it.

### /steward for existing PRs

Many PRs don't need another review, but need someone to see them through to merge. If you have such a PR, check out the branch and run:

```
/steward 41
```

It will run just the watch component of `/ship`. It will watch the PR you opened and do things like fix failing checks, resolve conflicts, and address comments, without reviewing it first.

If you don't specify a PR number, it will watch the PR for the current branch. It will take the same `+name` bots, and the same caveats as before apply.

However, if a PR is already labeled Steward, it will not run the local watch. And if it is unable to run a watch, `/steward` will not do anything.

If you want to stop the watch, you can use either `/steward stop` or `/ship stop`. Since a session can only run one watch at a time, starting a new one will terminate the previous one.

Don't confuse `/steward` with PR Steward, which is a team service that runs as `claude[bot]` after being enabled by an admin. The `/steward` command runs as you, in your session.

A PR that has red checks is a good place to start. A PR that gets stuck in a conflict loop is also a good candidate. On the flip side, a PR that's in the middle of a design debate is a bad one because that's your debate to settle.

### Claude escalates bigger calls to you

As part of the watch, Claude is told to make small changes and elevate the bigger ones. Things like:

- A request to redesign something, like a new API or a bigger scope
- A security issue it wasn't able to resolve

It also pushes at most 3 times for a given issue, and then reports the attempted solutions.

That's roughly equivalent to our claim in the [verification blog post](https://claude.dev/blog/how-the-claude-code-team-thinks-about-verification/): if we keep running the same check and it keeps failing after three rounds, then the approach is probably wrong.

At this point, it escalates to the author of the code.

## IN YOUR REPO

As you get a few PRs under your belt, you'll start to notice patterns. For instance:

- The same comment from the same reviewer
- A setup instruction that Claude has to figure out
- A flaky check

You can start to write these down for your team, in one of a few files, depending on which tool needs to read it:

| What keeps repeating | Put it in | Read by |
| --- | --- | --- |
| A convention that code should follow | `CLAUDE.md` | Claude Code, local `/code-review`, Code Review and PR Steward |
| A rule about how PRs get reviewed | `REVIEW.md` | Code Review and PR Steward, not local `/code-review` |
| How to start and exercise the app | `.claude/skills/verify/SKILL.md` | Claude Code when it verifies a change |
| How PRs here should be looked after | `.claude/skills/steward/SKILL.md` | `/ship`, `/steward` and PR Steward |

### Repeat comments become review rules

Let's say you get asked by a peer twice to make sure a new query contains a tenant check. If you use local review, you can write this down in `CLAUDE.md`, since `/ship` uses `/code-review` to review. If you have Code Review on your repository, you can write review-only rules in the root `REVIEW.md`:

```
# Review instructions

## What Important means here
Wrong results, leaked data or anything that blocks a rollback.
Style and naming are Nit at most.

## Always check
- Database queries are scoped to the caller's tenant.
- New API routes have an integration test.

## Keep it quiet
- Report at most five Nits.
- Skip generated files and lockfiles.
- Behavior claims need a file and line.
```

Code Review won't read the `REVIEW.md` file from the PR being reviewed. It will also only respect some instructions, like excluding paths and limiting nits, when the default branch is protected.

Not every comment should be elevated. On our team, we have a principle that a pattern has to be repeated on at least 2 PRs to be considered for a rule. A person then approves the PR that adds the rule. That's a good bar to adopt. You should also be deleting rules as needed.

### Repeat setup becomes verify skills

If you find yourself constantly telling Claude how to boot up the app and navigate to specific pages, you should just write it down. Create `.claude/skills/verify/SKILL.md`. This can be in the root or in the directory of the code.

```
---
name: verify
description: Run the web app and exercise a change end to end. Use before committing.
---

1. Start the stack with npm run dev:stack.
2. Wait for /healthz on port 3000 to return 200.
3. Sign in with the seeded test account.
4. Exercise the changed flow in the browser and take a screenshot.
5. Report the steps you ran and what you saw. Don't report success without them.
```

Be sure to customize the commands.

Have Claude run it a few times, and fix any flaky behaviors. People ignore verification they don't trust.

### Repeat PR maintenance becomes steward rules

This one can be easy to miss. The local watch reads the `.claude/skills/steward/SKILL.md` file from your working directory.

PR Steward, which runs in Anthropic's cloud, reads it from the default branch.

```
---
name: steward
description: House rules for looking after PRs in this repository
user-invocable: false
disable-model-invocation: true
---

- Regenerate the lockfile with npm install; don't edit it by hand.
- `e2e-nightly` is flaky. Re-run it once before looking for a cause.
- Run npm test and npm run lint before pushing a fix.
- Leave comments about API design to the author.
```

In the example above, the two settings keep it out of the / menu and out of the skills Claude picks on its own.

The steward file can't change the watch's restrictions. However, anyone who can merge to the repository can edit the file, so review changes to it as carefully as you would review any changes to CI.

If your team turns on PR Steward later, those guidelines will apply in Anthropic's cloud once they're on the default branch.

## ACROSS YOUR TEAM'S PRS

### Standardizing the post-PR process

Once you've run `/ship` on a few of your own PRs, you'll have a good sense of what Claude Ship could do across your team's PRs. The rest of this post is for that conversation with your admins: what to ask for, and how to roll it out safely.

To [get started](https://code.claude.com/docs/en/claude-ship#who-can-use-claude-ship), you'll need to ask your administrators for a single repository, a few volunteers, and a limited amount of time to test Claude Ship on your own pull requests.

1. **Agree on your budget constraints ahead of time.**
2. **Protect the default branch of the repository.** A repository admin can set up this requirement, ensuring that any updates require a PR with an approval on the latest push, and that the Claude GitHub App is not on the bypass list.
3. **Enable Code Review for this repository.** An Owner, the admin role in your Claude organization, can enable Code Review.
4. **Enable PR Steward in Manual mode.** The same Owner can enable PR Steward to kick in when a user with write access comments `@claude steward`, or when authors opt in for it to kick in automatically. Comment `@claude stop` to stop Steward.
5. **Create an observe mode approval policy.** This file acts like any other file; you can create it in your own PR, but since merging this file enables Approvals for the repository, clear it with an Owner first.

PR Steward is designed not to approve or merge pull requests, so make sure you use branch protection to require the approvals you want before merging.

PR Steward reads the comments from reviewers and performs some actions based on them. Like any text-parsing agent, it can be fooled by what people say. Make sure you use it only in repositories with trusted collaborators, and check the changes made by PR Steward on comments from untrusted users.

### Configure your first approval policy

For approval policies, Claude Approvals reads from the `.claude/approvals.yml` file on the default branch. A simple first policy could be:

```
# .claude/approvals.yml
version: 1
mode: observe
rules:
  - purpose: "A change takes two people."
    paths: ["**"]
    verdict: { claude: comments, seats: 2 }
    advisory: [claude/code_review]
  - purpose: "A change to the review rules takes two people."
    paths: ["**/.claude/**", "**/REVIEW.md", "**/CLAUDE.md", "**/CODEOWNERS", ".github/**"]
    nested: inherit
    verdict: { claude: comments, seats: 2 }
```

`seats` is the number of people who have to approve, and the author can take one of those seats.

There's one catch. After the watch has merged the base branch, the most recent commit will be a merge commit, and nobody sits in the author's seat for it, so the PR author should comment `@claude approve`.

When a rule's verdict is `claude: comments`, Claude won't approve. If more than one rule matches, the strictest one wins. In observe mode the check just tells you what it would have decided. Claude doesn't approve anything.

Don't drop the advisory line. Once the policy file is on the default branch, Code Review only kicks off automatically on PRs that match a rule naming it. Without that line, your automatic reviews just stop. Advisory reviews don't change the verdict, and they run on whatever settings you already have. A policy that names Code Review can start billed reviews, even where Code Review is turned off.

If you want to see where a passing Claude review could lower what a path needs, swap the advisory line for an override, and update the rule's purpose to match, for example "When Claude's review passes, one is enough and Claude approves."

```
override:
  - { if: "claude/code_review = pass", verdict: { claude: approves, seats: 1 } }
```

The override names Code Review too, so those pull requests still get automatic reviews. When a review passes, the override swaps the rule's decision for one seat plus Claude's approval. The author can fill that one seat, so the check can now report that Claude would have approved. But text in a pull request can sway Claude's review, and when it does, this override lowers what that pull request needs.

If there are some paths that need to always require a human, put them in a rule without an override (next section, step 1). Before you merge this, tell the budget owner. **A policy that uses Claude's review this way starts billing Code Reviews, even in observe mode.** It can bill whenever you push, regardless of your Code Review settings.

You can also build your own classifiers for questions like "is this PR related to a migration?" [Custom classifiers](https://code.claude.com/docs/en/approvals-classifiers#add-a-custom-classifier) live in `.claude/classifiers/<name>/def.yml` on the default branch, and each run is billed, even in observe mode. Start out by focusing on paths and the Code Review result.

### Monitoring and transitioning to enforcement

Our team uses the same process as observe mode for our own internal commit gate. It logs the decisions it would have made in observe mode, so we can analyze false positives before making them mandatory. You will see the decisions in the Claude Approvals check and the associated comment.

Keep in mind that you only get the value of observe mode if you actually monitor it. After a week or two of having it in place, revisit the merged PRs and see how the decisions compare to your reviewers' behavior.

The first two rows apply once you've added the override.

| The policy said | Your reviewers | What to do |
| --- | --- | --- |
| Would approve | Approved with nothing to add | Keep the rule |
| Would approve | Asked for changes | Add a path rule that needs a person, or fix `REVIEW.md` if review should have caught it |
| Needs two people | Approved at a glance every time | Consider narrowing the rule once you've seen enough examples |
| Needs two people | Had real questions | Keep the rule |

Go through a few example PRs. How would you have decided? Which rule made the decision? What would you change? Pay the most attention to the second row, and fix those before you relax any rules.

One thing to know before you enforce: Claude's approvals count as real approvals on GitHub. If a ruleset only needs one approval, Claude's can be enough on its own. So read your policy and your branch rules together.

If you use auto-merge, and have policies that only the author can fulfill (like the override above), you can have PRs that get merged without anyone doing anything. Decide explicitly whether that's OK for each path, and write it down.

Then lock it down in this order:

1. Use a rule without an if or override for paths where you always need a second set of eyes. No classifier result can override it, and `nested: inherit` carries it into subdirectories that have their own policies.

	```
	- purpose: "Auth, billing and CI take a person who isn't an author."
	  paths: ["src/auth/**", "src/billing/**", ".github/**"]
	  nested: inherit
	  verdict:
	    claude: comments
	    seats: [{ count: 1, from: [humans, "!pr/authors"] }]
	```
2. Remove `mode: observe` and merge. Now Claude can approve wherever the rules say it approves.
3. About five minutes later, comment `@claude approvals rerun` on open PRs, so any stale results get cleaned up. Reruns can charge for classifiers again.
4. Ask a repository admin to make the Claude Approvals check required, and to pick the Claude app as its source. Until then, your PR can get merged regardless of what the check says.

Claude Ship and the local commands use AI, and they can miss bugs, security problems, and other issues, so keep all your existing tests, scanners, and reviewers.

## THINGS TO TRY THIS WEEK

I'd like to make it clear that for the Claude Code team, the person who called the agent is responsible for a change. It's as if they typed it themselves.

Your team should still be responsible for the PR scope, design, evidence, and rules for when it can merge. With these principles in mind, here is where you can get started:

1. **Today:** Run `/code-review` on your current branch. Make a note of what it got wrong and what it missed.
2. **Next PR:** In a repository where you trust everyone who can merge, try `/ship`, and stick around. Try `/steward` on an existing PR, in a different terminal and git checkout.
3. **By Friday:** Create a small PR with the rule you repeated most, in your `CLAUDE.md`, `REVIEW.md`, or a skill. Do the commit yourself, since `/ship` will not commit rule files. Share the PR and the example observe-mode policy with your team.

If you do so, I would love to know which rule file was most impactful, and which tasks you chose to keep doing yourself.

FINDER

guest@claude.devs·/>

ALLPAGESAGENTSENGINEERINGPLAYBOOKSSKILLSTUTORIALS

01Home PAGE

02Changelog PAGE

03Terminal PAGE

04Mods PAGE

05Clawd’s Quest GAME

06A practical guide to shipping with Claude Code 16 minARTICLE

07Using a "chaos loop" to harden the Claude Docs launch: 60 server errors across billions of requests 9 minARTICLE

08How the Claude Code team thinks about verification 10 minARTICLE

09Safely scaling multi-agent teams with Claude Fable 5.2 12 minARTICLE

10Which Claude model should you build with? Fable, Opus, Sonnet, or Haiku 15 minARTICLE

11How the Claude Code team does code review 14 minARTICLE

↑↓ navigate↵ open⌘K toggles21 posts
