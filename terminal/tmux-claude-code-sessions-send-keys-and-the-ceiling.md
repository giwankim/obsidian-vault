---
title: "tmux + Claude Code: Sessions, send-keys, and the Ceiling"
source: "https://crystl.dev/guides/tmux-for-ai-agents/"
author:
  - "[[crystl]]"
published: 2026-07-31
created: 2026-10-20
description: "A working tmux setup for running Claude Code and other AI agents: session-per-project naming, pane layouts, send-keys for scripting an agent, capture-pane for reading one back, and the status-line monitor. Plus the limits you hit at four agents."
tags:
  - "clippings"
---

> [!summary]
> A crystl guide to running AI coding agents in tmux, starting with Claude Code's built-in `claude --worktree --tmux` (`--tmux=classic` gets real tmux on iTerm2) and then covering session-per-project naming, pane layouts, an agent-focused `.tmux.conf`, scripting agents with `send-keys` (`-l` for literal text, a short sleep before Enter), and reading them back with `capture-pane -J` and `pipe-pane`. It builds a status-line monitor that scrapes panes for agent state and lays out what survives detaching, dropped SSH links, and reboots. It ends by listing tmux's limits for multi-agent work (no view of which agent is waiting, brittle scraping, no shared state) as the pitch for the crystl terminal.

tmux runs your AI coding agents in named, detachable sessions that survive a closed terminal or a dropped SSH connection. You get one window holding many agents, `send-keys` to type into any of them from a script, and `capture-pane` to read one back. That combination is why people use it.

Before you build any of it by hand, check the built-in path: recent versions of Claude Code can create the worktree and the tmux session for you with `claude --worktree --tmux`. This guide covers that first, then everything it doesn’t reach, then the point where tmux itself stops.

## Why tmux and agents go together

A coding agent is a long-running process that wants to keep talking to a terminal. Three properties of tmux match that shape:

**It survives disconnection.** The tmux server owns the pty, not your terminal window. Close the window, lose your SSH link, put the laptop to sleep: the agent keeps working and is still there when you reattach.

**It holds many sessions in one window.** Four agents become four named sessions you switch between with a keystroke, instead of four windows you hunt for in the app switcher.

**It’s scriptable from outside.** Any shell, anywhere, can type into a running agent or read its screen. No IPC to build, no API to wire up. This is the property people build on, and it’s why tmux keeps showing up in agent-orchestration scripts.

## The built-in flag, before you build anything

Claude Code ships with this wired up for the single-agent-on-a-branch case. Two flags, from `claude --help` on a recent version:

```plaintext
-w, --worktree [name]   Create a new git worktree for this session
                        (optionally specify a name)
    --tmux              Create a tmux session for the worktree
                        (requires --worktree). Uses iTerm2 native panes
                        when available; use --tmux=classic for
                        traditional tmux.
```

So the whole “isolate this task, give it its own session” move is one command:

```bash
claude --worktree --tmux

# or name the worktree
claude --worktree auth-refactor --tmux
```

Two details matter before you rely on it. `--tmux` errors without `--worktree`, so it’s a worktree feature that happens to make a session, not a general session flag. And on iTerm2 it uses native panes instead of tmux, which is nicer to look at and means the tmux commands in the rest of this page have nothing to attach to. Pass `--tmux=classic` when you want real tmux underneath, which you do if you plan to script against the session.

For a single agent on a single branch, that’s the answer. Use it and skip ahead.

What it doesn’t do: run several agents in one session, lay out panes so you can watch them, let you type into a running agent from a script, tell you which agent is waiting on you, or set any of this up on a remote box over SSH. Those are the rest of this guide, and each one is where people end up writing tmux by hand.

More on the worktree half of that flag in [git worktrees for parallel development](https://crystl.dev/guides/git-worktrees-parallel-development/).

## Session per project, named by project

The organizing rule that keeps this usable: one tmux session per repo, named after the repo. Not per task, not per agent. Tasks come and go; the project is the stable thing.

```bash
# start a detached session in a project directory
tmux new-session -d -s api -c ~/code/api

# attach to it (creates it if it doesn't exist)
tmux new-session -A -s api -c ~/code/api
```

`-A` is attach-or-create. It makes a single command safe to run repeatedly, which is what you want in a shell function:

```bash
# ~/.zshrc
agent() {
  local dir="${1:-$PWD}"
  local name="$(basename "$dir" | tr . -)"
  tmux new-session -A -s "$name" -c "$dir"
}
```

Session names can’t contain `.` or `:` (tmux uses them as target separators), hence the `tr`.

Then `tmux ls` becomes a real inventory:

```bash
$ tmux ls
api: 3 windows (created Fri Jul 31 09:12:04 2026)
web: 2 windows (created Fri Jul 31 09:40:11 2026)
infra: 1 windows (created Fri Jul 31 11:02:55 2026)
```

Add a bit more with a format string:

```bash
tmux list-sessions -F '#{session_name}  windows=#{session_windows}  attached=#{session_attached}'
```

## A layout for watching several agents

Inside a session, give each agent its own window, named for the task:

```bash
tmux new-window -t api -n auth   -c ~/code/api
tmux new-window -t api -n tests  -c ~/code/api
```

Windows are better than panes for agents you’re not actively watching, because a window costs no screen space. Panes are for the two or three you want side by side right now:

```bash
# split the current window and tile whatever is in it
tmux split-window -h -c '#{pane_current_path}'
tmux split-window -v -c '#{pane_current_path}'
tmux select-layout tiled
```

`#{pane_current_path}` is easy to leave off. Without it a new pane opens in the directory the session started in, not the directory you’re actually in, and the agent you launch there is pointed at the wrong repo.

Two layouts by name: `tiled` for an even grid of agents, and `main-vertical` for one big pane (the agent you’re driving) with the rest stacked beside it.

```bash
tmux select-layout main-vertical
tmux set-window-option main-pane-width 60%
```

Percentage values for `main-pane-width` need tmux 3.2 or newer. On older builds use an absolute column count (`main-pane-width 120`). Check with `tmux -V`.

## A.tmux.conf worth having

These are the lines that matter for agent work specifically. They’re not a full config, they’re the delta from defaults that a fleet of agents makes you want.

```plaintext
# agents produce a lot of output, and you will want to scroll back through it
set -g history-limit 100000

# 24-bit colour, so agent TUIs render the way they were designed to
set -g default-terminal "tmux-256color"
set -ga terminal-overrides ",*256col*:Tc"

# scroll and click between panes with the mouse
set -g mouse on

# don't let a running process rename the window out from under you
set -g allow-rename off
set-window-option -g automatic-rename off

# 1-indexed windows match the number keys on your keyboard
set -g base-index 1
set-window-option -g pane-base-index 1
set -g renumber-windows on

# flag windows whose agent produced output while you were elsewhere
set-window-option -g monitor-activity on
set -g visual-activity off

# status line refreshes often enough to be a monitor
set -g status-interval 5

# no delay when an agent's TUI reads an escape sequence
set -sg escape-time 10

# jump panes without the prefix key
bind -n M-h select-pane -L
bind -n M-j select-pane -D
bind -n M-k select-pane -U
bind -n M-l select-pane -R

# reload without restarting the server
bind r source-file ~/.tmux.conf \; display-message "config reloaded"
```

Agent TUIs like to set the terminal title, so without `allow-rename off` your carefully named `auth` window becomes whatever the agent felt like calling itself.

`escape-time 10` fixes the “my arrow keys are laggy inside the agent” complaint. The default delay exists to disambiguate a real Escape key from an escape sequence, and it makes interactive TUIs feel mushy.

## Driving an agent with send-keys

`send-keys` types into a pane as if you were at the keyboard. This is how you script an agent from cron, from a git hook, or from another agent.

```bash
# target syntax: session:window.pane
tmux send-keys -t api:auth "run the test suite and fix what fails" Enter
```

Three things go wrong here, in order of how often:

**Bare arguments get interpreted as key names.** `Enter`, `C-c`, `Escape`, and `Space` are keys, not text. If your prompt contains one of those words as a standalone argument it gets sent as a keypress. Use `-l` to send a literal string:

```bash
tmux send-keys -t api:auth -l "press Enter to continue was the old flow"
tmux send-keys -t api:auth Enter
```

`-l` disables key-name lookup entirely, so the newline has to be a second call.

**Semicolons end the tmux command.** A trailing `;` in your text is read as a command separator. Escape it as `\;`.

**Agent TUIs need a beat between the text and the newline.** Many agent input boxes debounce or re-render on paste, and an Enter arriving in the same frame as the text gets swallowed. The reliable pattern:

```bash
tmux send-keys -t api:auth -l "$PROMPT"
sleep 0.3
tmux send-keys -t api:auth Enter
```

Interrupting a runaway agent is the same mechanism:

```bash
tmux send-keys -t api:auth C-c
```

## Reading an agent back with capture-pane

`capture-pane` dumps a pane’s contents to stdout. It’s the read half of the pair.

```bash
# the visible screen
tmux capture-pane -p -t api:auth

# the last 200 lines, with wrapped lines joined back together
tmux capture-pane -p -J -S -200 -t api:auth

# the entire scrollback
tmux capture-pane -p -J -S - -t api:auth

# keep the colour escape sequences
tmux capture-pane -p -e -t api:auth
```

`-J` matters more than it looks. Without it, a line that wrapped at your terminal width comes back as two lines, and every grep you write against the output is wrong at the seams.

For a continuous log rather than a snapshot, `pipe-pane` streams everything a pane produces to a command:

```bash
tmux pipe-pane -o -t api:auth 'cat >> ~/agent-logs/api-auth.log'

# stop it
tmux pipe-pane -t api:auth
```

`-o` toggles, so running it twice turns it off. The output is raw, escape sequences and all, so pipe it through something like `sed -E 's/\x1b\[[0-9;]*[a-zA-Z]//g'` if you want it readable later.

## The status-line monitor

Every person who runs several agents in tmux eventually builds this: a status line that tells you which agents are working and which are waiting.

The mechanism is `#()` in the status line, which runs a shell command and interpolates its output, refreshed every `status-interval` seconds.

```plaintext
set -g status-interval 5
set -g status-right '#(~/bin/tmux-agent-status) | %H:%M'
set -g status-right-length 100
```

And the script, which capture-scrapes each pane for a sign of life:

```bash
#!/usr/bin/env bash
# ~/bin/tmux-agent-status
out=""
while read -r target; do
  screen="$(tmux capture-pane -p -J -S -8 -t "$target" 2>/dev/null)"
  name="${target%%:*}"
  case "$screen" in
    *"Do you want"*|*"❯ 1."*) out+="⏸ $name " ;;   # parked on a prompt
    *"esc to interrupt"*)      out+="● $name " ;;   # working
    *)                         out+="○ $name " ;;   # idle
  esac
done < <(tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index}')
printf '%s' "$out"
```

It works, and it’s worth building. Be clear-eyed about what it’s doing: string matching against a TUI’s rendered frame, on a five-second poll, for every pane you have open. The match strings are whatever your agent version happens to print this week.

The lighter-weight version uses tmux’s own activity tracking instead of scraping. `monitor-silence` fires an alert when a pane produces no output for N seconds, which is the closest native signal to “this agent stopped”:

```plaintext
set-window-option -g monitor-silence 30
set -g visual-silence on
```

You can hang an action off it:

```plaintext
set-hook -g alert-silence 'run-shell "osascript -e \"display notification \\\"agent idle\\\"\""'
```

Silence is a proxy for done, not a report of it. An agent thinking hard about a large file is silent too.

## Detach, reattach, and what survives what

```bash
tmux detach-client            # or the prefix, then d
tmux attach -t api
tmux switch-client -t web     # from inside another session
tmux kill-session -t api
```

What survives:

| Event | Agents keep running? |
| --- | --- |
| Close the terminal window | yes |
| Detach the client | yes |
| SSH connection drops | yes |
| `tmux kill-session` | no |
| `tmux kill-server` | no |
| Reboot | no |
| macOS “Reopen windows” after restart | no |

The tmux server is just a process owned by your user. Nothing about tmux makes it survive a reboot, and a session’s scrollback is lost when the server stops. If the transcript matters, `pipe-pane` it to a file or use a tool that persists history on its own.

One detail people trip on: a detached session’s panes are sized to the last client that was attached, or to 80x24 if there never was one. An agent TUI rendering into an 80-column pane while you’re away will look wrong when you reattach at 200 columns, until it redraws. `set-window-option -g aggressive-resize on` helps when several clients are attached at different sizes.

## tmux over SSH

This is where tmux is genuinely hard to replace. Running agents on a remote box, over a link you don’t trust:

```bash
# attach or create, in one command, with a tty allocated
ssh devbox -t tmux new-session -A -s agents
```

Your connection drops mid-task, you run the same command again, and you’re back in the same session with the agent still going. Pair it with `mosh` if your link is bad enough that SSH itself keeps dying.

The nested-tmux problem: if you run tmux locally and also on the remote box, both grab the same prefix. The two fixes are a different prefix on the remote (`set -g prefix C-a`), or pressing the prefix twice, which `bind C-b send-prefix` gives you.

For running agents on a machine that isn’t the one in front of you, see [remote development](https://crystl.dev/features/remote-development/).

## Where tmux stops

tmux is good software. It solves multiplexing and persistence about as well as those can be solved, and it has been doing it since 2007. What it doesn’t do is anything specific to agents, because agents didn’t exist when its model was designed.

**No visibility into which agent is parked.** An agent waiting on an approval prompt looks exactly like an agent thinking, which looks exactly like an agent that finished twenty minutes ago. All three are “a pane with some text in it”. The status-line hack above exists to paper over this, and it papers by scraping.

**No notification when one finishes.** `monitor-silence` is the nearest thing, and it fires on any quiet pane for any reason. There is no event for “the agent is done” because tmux has no idea what an agent is.

**Screen scraping is brittle by construction.** `capture-pane` gives you the rendered frame: spinners, box drawing, truncated columns, ANSI. Not what the agent said, not which tool it called, not whether that call succeeded. Every parser you write against it breaks when the agent ships a UI change.

**No shared state across sessions.** Two agents in two tmux sessions have no way to see each other. If you want one to read another’s transcript or hand off work, you build that yourself, out of files and locks and polling.

**Scrollback for several streaming agents is expensive.** `history-limit 100000` across a dozen panes of agent output is real memory, held per pane for as long as the server lives, and gone the moment it does. See [terminal emulators for AI agents](https://crystl.dev/guides/terminal-emulators-for-ai-agents/) for why the rendering side of this gets costly too.

**Nothing survives a reboot.** Every session, every transcript, gone.

None of these are flaws. They are the edge of a tool built to multiplex shells for one person at a keyboard.

## Where crystl picks up

[crystl](https://crystl.dev/) is a macOS terminal built for the workload tmux was not shaped for: many agents at once, most of them off-screen, each one occasionally needing you.

The differences map almost one-to-one onto the list above.

- **Approvals surface instead of getting buried.** When any agent pauses for permission, crystl floats it as a card, colour-coded by project, and you answer without switching sessions. No scraping, no polling. See [floating cards](https://crystl.dev/features/floating-cards/).
- **Agent state is a first-class signal.** The [agent activity panel](https://crystl.dev/features/agent-activity-panel/) shows every session’s state at once: working, waiting on you, idle, done. That’s the thing the status-line script was approximating.
- **Output is structured, not scraped.** crystl captures each turn, tool call, and result as typed records, so [history](https://crystl.dev/docs/conversation-history/) is searchable across every session and agents can read each other’s transcripts without parsing ANSI.
- **Sessions are organized by project, and they persist.** Projects are gems, sessions inside them are shards, and history survives closing a window or restarting the Mac. More in [multitasking](https://crystl.dev/features/multitasking/).
- **Parallel work on one repo is isolated.** Isolated shards are backed by real git worktrees, so two agents on the same repo don’t collide. See [parallel sessions](https://crystl.dev/features/parallel-sessions/).

The recommendation: keep tmux. It’s still the right answer for remote boxes, for long-running processes on servers, and for anything where the SSH link is the fragile part. Use it for that. When the thing you’re managing is six agents that each need a decision from you at an unpredictable moment, the problem stopped being multiplexing.

More on the organizing side of this in [managing multiple AI coding sessions](https://crystl.dev/guides/managing-multiple-ai-sessions/), and on keeping agents working rather than idle in [running AI coding agents for longer](https://crystl.dev/guides/run-ai-coding-agents-longer/).
