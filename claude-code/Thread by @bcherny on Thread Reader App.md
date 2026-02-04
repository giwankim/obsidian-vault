---
title: "Thread by @bcherny on Thread Reader App"
source: "https://threadreaderapp.com/thread/2007179832300581177.html?utm_source=tldrnewsletter"
author:
  - "[[@bcherny]]"
published:
created: 2026-01-28
description: "@bcherny: I'm Boris and I created Claude Code. Lots of people have asked how I use Claude Code, so I wanted to show off my setup a bit. My setup might be surprisingly vanilla! Claude Code works..."
tags:
  - "clippings"
---
## Enter URL or ID to Unroll

18,904 views

I'm Boris and I created Claude Code. Lots of people have asked how I use Claude Code, so I wanted to show off my setup a bit.  
  
My setup might be surprisingly vanilla! Claude Code works great out of the box, so I personally don't customize it much. There is no one correct way to use Claude Code: we intentionally build it in a way that you can use it, customize it, and hack it however you like. Each person on the Claude Code team uses it very differently.  
  
So, here goes.

1/ I run 5 Claudes in parallel in my terminal. I number my tabs 1-5, and use system notifications to know when a Claude needs input [code.claude.com/docs/en/termin…](https://code.claude.com/docs/en/terminal-config#iterm-2-system-notifications) ![Image](https://pbs.twimg.com/media/G9rtc4EasAELEzh.jpg)

[![](https://threadreaderapp.com/thread/this.src='/images/sticky-note-regular.png')](https://code.claude.com/docs/en/terminal-config#iterm-2-system-notifications)

[**Optimize your terminal setup - Claude Code Docs** Claude Code works best when your terminal is properly configured. Follow these guidelines to optimize your experience.](https://code.claude.com/docs/en/terminal-config#iterm-2-system-notifications) [https://code.claude.com/docs/en/terminal-config#iterm-2-system-notifications](https://code.claude.com/docs/en/terminal-config#iterm-2-system-notifications)

2/ I also run 5-10 Claudes on [claude.ai/code](http://claude.ai/code), in parallel with my local Claudes. As I code in my terminal, I will often hand off local sessions to web (using &), or manually kick off sessions in Chrome, and sometimes I will --teleport back and forth. I also start a few sessions from my phone (from the Claude iOS app) every morning and throughout the day, and check in on them later.![Image](https://pbs.twimg.com/media/G9reZjqaYAA9btU.jpg)

3/ I use Opus 4.5 with thinking for everything. It's the best coding model I've ever used, and even though it's bigger & slower than Sonnet, since you have to steer it less and it's better at tool use, it is almost always faster than using a smaller model in the end.

4/ Our team shares a single [CLAUDE.md](http://claude.md/) for the Claude Code repo. We check it into git, and the whole team contributes multiple times a week. Anytime we see Claude do something incorrectly we add it to the [CLAUDE.md](http://claude.md/), so Claude knows not to do it next time.  
  
Other teams maintain their own [CLAUDE.md](http://claude.md/) 's. It is each team's job to keep theirs up to date.![Image](https://pbs.twimg.com/media/G9rfKYRbkAA6Q3w.jpg)

5/ During code review, I will often tag @.claude on my coworkers' PRs to add something to the as part of the PR. We use the Claude Code Github action (/install-github-action) for this. It's our version of @danshipper's Compounding Engineering [CLAUDE.md](http://claude.md/) ![Image](https://pbs.twimg.com/media/G9rhsVFasAIUCYj.jpg)

[![](https://threadreaderapp.com/thread/this.src='/images/sticky-note-regular.png')](http://claude.md/)

[**Claude Code overview - Claude Code Docs** Learn about Claude Code, Anthropic's agentic coding tool that lives in your terminal and helps you turn ideas into code faster than ever before.](http://claude.md/) [http://CLAUDE.md](http://claude.md/)

6/ Most sessions start in Plan mode (shift+tab twice). If my goal is to write a Pull Request, I will use Plan mode, and go back and forth with Claude until I like its plan. From there, I switch into auto-accept edits mode and Claude can usually 1-shot it. A good plan is really important!![Image](https://pbs.twimg.com/media/G9rjZcwasAQpPN6.png)

7/ I use slash commands for every "inner loop" workflow that I end up doing many times a day. This saves me from repeated prompting, and makes it so Claude can use these workflows, too. Commands are checked into git and live in.claude/commands/.  
  
For example, Claude and I use a /commit-push-pr slash command dozens of times every day. The command uses inline bash to pre-compute git status and a few other pieces of info to make the command run quickly and avoid back-and-forth with the model ([code.claude.com/docs/en/slash-…](https://code.claude.com/docs/en/slash-commands#bash-command-execution)) ![Image](https://pbs.twimg.com/media/G9rj3eFasAEK_8J.jpg)

8/ I use a few subagents regularly: code-simplifier simplifies the code after Claude is done working, verify-app has detailed instructions for testing Claude Code end to end, and so on. Similar to slash commands, I think of subagents as automating the most common workflows that I do for most PRs.  
  
[code.claude.com/docs/en/sub-ag…](https://code.claude.com/docs/en/sub-agents) ![Image](https://pbs.twimg.com/media/G9rnUzEasAElFcN.png)

[![](https://threadreaderapp.com/thread/this.src='/images/sticky-note-regular.png')](https://code.claude.com/docs/en/sub-agents)

[**Create custom subagents - Claude Code Docs** Create and use specialized AI subagents in Claude Code for task-specific workflows and improved context management.](https://code.claude.com/docs/en/sub-agents) [https://code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents)

9/ We use a PostToolUse hook to format Claude's code. Claude usually generates well-formatted code out of the box, and the hook handles the last 10% to avoid formatting errors in CI later. ![Image](https://pbs.twimg.com/media/G9rrnTxasAAMoZ_.jpg)

10/ I don't use --dangerously-skip-permissions. Instead, I use /permissions to pre-allow common bash commands that I know are safe in my environment, to avoid unnecessary permission prompts. Most of these are checked into.claude/settings.json and shared with the team. ![Image](https://pbs.twimg.com/media/G9rlDa-asAAXlHx.jpg)

11/ Claude Code uses all my tools for me. It often searches and posts to Slack (via the MCP server), runs BigQuery queries to answer analytics questions (using bq CLI), grabs error logs from Sentry, etc. The Slack MCP configuration is checked into our.mcp.json and shared with the team.![Image](https://pbs.twimg.com/media/G9rl_pQb0AAILz8.jpg)

12/ For very long-running tasks, I will either (a) prompt Claude to verify its work with a background agent when it's done, (b) use an agent Stop hook to do that more deterministically, or (c) use the ralph-wiggum plugin (originally dreamt up by @GeoffreyHuntley). I will also use either --permission-mode=dontAsk or --dangerously-skip-permissions in a sandbox to avoid permission prompts for the session, so Claude can cook without being blocked on me.  
  
[github.com/anthropics/cla…](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-wiggum)  
  
[code.claude.com/docs/en/hooks-…](https://code.claude.com/docs/en/hooks-guide) ![Image](https://pbs.twimg.com/media/G9ro4W5bEAAQ3ug.jpg)

13/ A final tip: probably the most important thing to get great results out of Claude Code -- give Claude a way to verify its work. If Claude has that feedback loop, it will 2-3x the quality of the final result.  
  
Claude tests every single change I land to [claude.ai/code](http://claude.ai/code) using the Claude Chrome extension. It opens a browser, tests the UI, and iterates until the code works and the UX feels good.  
  
Verification looks different for each domain. It might be as simple as running a bash command, or running a test suite, or testing the app in a browser or phone simulator. Make sure to invest in making this rock-solid.  
  
[code.claude.com/docs/en/chrome](https://code.claude.com/docs/en/chrome)

I hope this was helpful! What are your tips for using Claude Code? What do you want to hear about next?

• • •

Missing some Tweet in this thread? You can try to [force a refresh](https://threadreaderapp.com/thread/?utm_source=tldrnewsletter#)

**Keep Current with [Boris Cherny](https://threadreaderapp.com/user/bcherny)**

![Boris Cherny Profile picture](https://pbs.twimg.com/profile_images/1902044548936953856/J2jeik0t_bigger.jpg)

Stay in touch and get notified when new unrolls are available from this author!

**This Thread may be Removed Anytime!**

![PDF](https://threadreaderapp.com/assets/icon-pdf-ceb3626bf7a8daddf0ed92c9f804942d567013f5556e880d9c5e2c234ebe021d.png)

Twitter may remove this content at anytime! Save it as PDF for later use!

## More from @bcherny

Jan 13

It's late 2024, a few days after I launched the first version of Claude Code (then called Claude CLI) to team dogfooding. I walked into the office and saw my coworker Robert with a terminal up on his computer, Claude CLI running and a red/green diff view on screen.  
  
I was surprised. This was back in the Sonnet 3.5 days, before the model was good at agentic coding. I had just given it a FileEdit tool the day before. Claude CLI was a prototype that I thought it wasn't useful for anything yet. But Robert was already starting to use it to write code & use git for him. I was still using the CLI as a note taker mostly, but I also started making it my go-to tool for using git as a result.

A couple months later, many engineers & researchers at Anthropic were using Claude daily. There was one day I remember walking into the office and saw a Claude Code terminal up on our data scientist's computer monitor! I asked if he was trying out Claude Code, and was shocked to learn that he was using it to do his work, to write and run SQL queries for an analysis, and to make little ascii plots in the terminal and using matplotlib.  
  
We built Claude Code for engineers, and here was a data scientist using it to do his work too. The next week, the entire row of data scientists had Claude Code up on their screens.

Over the next few months, this happened over and over. First our designer started using Claude Code for prototypes and content fixes, then our finance person used it to build models and do financial forecasting, Sales used it to analyze data from Salesforce and bigquery, our user researcher used it to crunch survey results.  
  
Fast forward to today, and people are using Claude Code to control their oven, recover wedding photos from a busted hard drive, analyze their DNA and medical records, haggle with customer support.

## Send Email!

Email the whole thread instead of just a link!

![email this](https://threadreaderapp.com/assets/emailthisv3-19db7e62925577c40531c0104134c2d93d1434dc7b3d7b20b761bea35c595420.gif)