---
title: "The Complete Guide to CLAUDE.md"
source: "https://www.builder.io/blog/claude-md-guide"
author:
  - "[[Vishwas Gopinath]]"
published: 2026-01-14
created: 2026-01-30
description: "Learn how to create, structure, and maintain CLAUDE.md files for Claude Code. Save hours by documenting project conventions that persist across sessions."
tags:
  - "clippings"
---
[‹ Back to blog](https://www.builder.io/blog)

#### AI

#### January 14, 2026

#### Written By

![](https://cdn.builder.io/api/v1/image/assets%2FYJIGb4i01jvw0SRdL5Bt%2Fc46f9083ec71424d8b2c6ae0820a148e?format=webp&width=100)

One file. Loaded before every conversation. If you're using [Claude Code](https://claude.com/product/claude-code), this is where your setup time pays off most.

`CLAUDE.md` is a markdown file that Claude automatically reads at the start of each session. It holds project-specific instructions you'd otherwise repeat in every prompt. Structure, conventions, workflows, style.

I've been iterating on my `CLAUDE.md` setup for a while now. This guide covers everything I've learned about creating, structuring, maintaining, and evolving these files. If you're using other AI coding tools, the same concepts apply to [AGENTS.md](https://www.builder.io/blog/agents-md) (the equivalent file for Cursor, Zed, OpenCode, and other [AI coding tools](https://www.builder.io/blog/best-ai-tools-2026)).

## Why you need a CLAUDE.md file

Claude starts every session with no memory of the last one. It doesn't know your code style preferences. It doesn't know how to run your tests. It doesn't know that your team uses a specific branch naming convention or that there's a quirky workaround in your authentication module.

You end up repeating yourself. Or worse, you forget to mention something important and spend time fixing code that didn't follow your conventions.

`CLAUDE.md` fixes that. Claude reads it automatically, so your preferences persist across sessions.

The fastest way to start is the `/init` command. Run it in your project directory and Claude generates a starter `CLAUDE.md` based on your project structure and detected tech stack.

Some people recommend writing it from scratch, but I use `/init` as a starting point and delete what I don't need. Deleting is easier than creating from scratch. The generated file often includes obvious things you don't need spelled out, or filler that doesn't add value.

You might be thinking, why not just keep everything the generator includes? Because context is precious. Every line in your `CLAUDE.md` competes for attention with the actual work you're asking Claude to do.

You can place `CLAUDE.md` in a few locations:

- **Project root**: The most common location. Commit it to version control so your team shares the same context.
- **`.claude/CLAUDE.md`**: An alternative if you prefer keeping config files in a subdirectory.
- **`~/.claude/CLAUDE.md`**: User-level defaults that apply to all your projects.

For personal preferences that shouldn't be version controlled (your editor quirks, your preferred verbosity level), use `CLAUDE.local.md` instead. Add it to your `.gitignore` to keep it out of version control.

The filename is case-sensitive. It must be exactly `CLAUDE.md` (uppercase CLAUDE, lowercase.md). Claude Code looks for this specific filename when loading memory files. This isn't explicitly stated in the documentation, but when I asked the official docs AI assistant, it confirmed case sensitivity applies to memory files the same way it does to skill files.

This is the meat of it. What actually belongs in the file?

### The essentials

**Project context**: What is this project? A one-liner that orients Claude. "This is a Next.js e-commerce app with Stripe integration" tells Claude more than you might think.

**Code style**: Your formatting and pattern preferences. Use ES modules or CommonJS? Prefer named exports? Be specific. "Format code properly" is vague.

**Commands**: How to run tests, build, lint, deploy. Claude will use these exact commands when you ask it to run things.

**Gotchas**: Project-specific warnings. That authentication module with the weird retry logic. The API endpoint that requires a specific header format. The file that should never be modified directly.

### A complete example

Here's what a `CLAUDE.md` might look like for a Next.js project:

```markdown
# Project: ShopFront

Next.js 14 e-commerce application with App Router, Stripe payments, and Prisma ORM.

## Code Style

- TypeScript strict mode, no \`any\` types
- Use named exports, not default exports
- CSS: Tailwind utility classes, no custom CSS files

## Commands

- \`npm run dev\`: Start development server (port 3000)
- \`npm run test\`: Run Jest tests
- \`npm run test:e2e\`: Run Playwright end-to-end tests
- \`npm run lint\`: ESLint check
- \`npm run db:migrate\`: Run Prisma migrations

## Architecture

- \`/app\`: Next.js App Router pages and layouts
- \`/components/ui\`: Reusable UI components
- \`/lib\`: Utilities and shared logic
- \`/prisma\`: Database schema and migrations
- \`/app/api\`: API routes

## Important Notes

- NEVER commit .env files
- The Stripe webhook handler in /app/api/webhooks/stripe must validate signatures
- Product images are stored in Cloudinary, not locally
- See @docs/authentication.md for auth flow details
```

Claude processes this efficiently because it's organized with clear headings, bullet points for scannability, and specific commands rather than vague instructions.

### How long should it be?

The general advice is under 300 lines. Shorter is better. Context tokens are precious.

But I've seen projects where a longer file makes sense. If your codebase has complex conventions or unusual patterns, front-loading that context can prevent Claude from making wrong assumptions and wasting time on corrections.

What works for me is including what Claude needs to know before it starts working. If something only matters in specific situations, I keep it in a separate file and reference it.

### The @imports system

`CLAUDE.md` supports importing other files with the `@path/to/file` syntax:

```markdown
See @README.md for project overview
See @docs/api-patterns.md for API conventions
See @package.json for available npm scripts
```

This is powerful for keeping your main file lean. Put detailed instructions in separate markdown files, then reference them. Claude pulls in the content when relevant.

You can reference files from anywhere:

- Relative paths: `@docs/style-guide.md`
- Absolute paths work too
- Even user-level files: `@~/.claude/my-preferences.md`

Imports can be recursive, so your referenced files can reference other files. Use this sparingly to avoid creating a maze of references.

The pattern I've landed on is keeping the essentials in `CLAUDE.md` and moving detailed topic-specific guidance to separate files, referenced with `@imports`.

### Modular rules with.claude/rules/

For larger projects, there's another option: the `.claude/rules/` directory. Instead of one large file with everything, you can split instructions into focused rule files.

```javascript
your-project/
├── .claude/
│   ├── CLAUDE.md           # Main project instructions
│   └── rules/
│       ├── code-style.md   # Code style guidelines
│       ├── testing.md      # Testing conventions
│       └── security.md     # Security requirements
```

All markdown files in `.claude/rules/` are automatically loaded with the same priority as your main `CLAUDE.md`. No imports needed. Just drop files in and they're included.

This works well when different team members own different rule sets. The frontend team maintains `code-style.md`. The security team maintains `security.md`. Nobody has to merge conflicts in one giant file.

I haven't needed this yet. My projects haven't been large enough to warrant splitting rules across multiple files. But if you're on a bigger team with distinct domains, this structure makes sense.

### Subdirectory CLAUDE.md files

There's one more layer to the hierarchy: `CLAUDE.md` files in subdirectories of your project.

When Claude reads files in a subdirectory, it automatically picks up any `CLAUDE.md` in that subtree. These aren't loaded at launch. They're only included when Claude is actively working in that part of the codebase.

This is useful for monorepos or projects with distinct modules. Your `/api` folder can have its own `CLAUDE.md` with API-specific conventions. Your `/packages/ui` folder can have different rules for component development. Claude loads the relevant context based on where it's working.

## How to maintain your CLAUDE.md file

A `CLAUDE.md` isn't a "set and forget" artifact. Your project evolves. Your preferences change. The file should too.

When Claude makes an assumption you want to correct, don't just fix it in the moment. Tell Claude to add it to your `CLAUDE.md`.

I do this constantly. Claude suggests console.log for debugging, but I want the logger. Instead of just correcting it once, I say "add to my `CLAUDE.md`: always use the logger instead of console.log." The instruction persists for future sessions.

This builds your `CLAUDE.md` organically. Instead of trying to anticipate everything upfront, you capture learnings as they happen. It's like taking notes during a meeting, except the notes actually get used.

Note: Earlier versions of Claude Code had a # keyboard shortcut for adding instructions. This was [removed in version 2.0.70](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md). The current approach is to ask Claude directly to edit your CLAUDE.md.

### Periodic review

Every few weeks, I ask Claude to review and optimize my `CLAUDE.md`. Over time, instructions accumulate. Some become redundant. Others conflict with newer additions.

A quick "review this `CLAUDE.md` and suggest improvements" surfaces these issues. Delete what's obsolete. Consolidate what's redundant. Clarify what's ambiguous.

This sounds like maintenance overhead. It is. But it's less overhead than repeating yourself in every session or fixing code that ignored your conventions.

### Emphasis for critical instructions

For rules that absolutely must be followed, emphasis words can help draw attention. "IMPORTANT: Never modify the migrations folder directly" or "YOU MUST run tests before committing."

Don't expect this to be foolproof. Claude might still cross these lines, especially as conversations grow longer and context gets crowded. In my experience, it increases the odds Claude pays attention, but it's not a lock.

Use it sparingly. If everything is marked IMPORTANT, nothing is.

## How to improve your CLAUDE.md over time

The most valuable updates often come from code reviews.

When a PR reveals a convention that wasn't documented, or a reviewer catches a pattern violation, that's a signal. Add it to `CLAUDE.md`. The mistake won't repeat.

If you're using the Claude Code GitHub action (set up with `/install-github-action`), you can tag @claude directly in PR comments to make these updates. Something like "@claude add to CLAUDE.md: never use enums, always prefer string literal unions." Claude updates the file and commits the change as part of the PR. [Boris Cherny shared this workflow](https://x.com/bcherny/status/2007179842928947333) and it's become part of how I think about `CLAUDE.md` maintenance.

This creates a feedback loop: real-world issues inform your instructions, which prevent future issues. Your `CLAUDE.md` becomes a living document that captures your team's accumulated knowledge.

I think of it like a codebase itself. You don't write perfect code on the first try. You refactor. You improve. Your `CLAUDE.md` deserves the same treatment.

## CLAUDE.md best practices

- Open with a one-liner explaining what the project is
- Make code style preferences specific and actionable
- Include key commands (test, build, lint, deploy)
- Detail gotchas enough to actually prevent mistakes
- Keep it under 300 lines, or make sure every line earns its place
- Move detailed guidance to @imported files
- Remove anything outdated or conflicting with newer instructions
- Mark critical rules with emphasis, but only the truly critical ones
- Add instructions as you work, not just upfront
- Update from PR reviews when conventions surface
- Review periodically for outdated or conflicting rules

For larger projects:

- Subdirectories with distinct conventions might need their own `CLAUDE.md`
- Splitting rules into `.claude/rules/` files can make ownership clearer across teams

## Start today

If you don't have a `CLAUDE.md` yet, run `/init` right now. Review what it generates. Delete what doesn't apply. Add your code style preferences.

If you already have one, tell Claude to update it next time it makes an assumption you want to correct. Watch your file grow organically from real usage.

One file. A few minutes of setup. Hours saved over time.

### Design and code in one platform

Builder.io visually edits code, uses your design system, and sends pull requests.

[Try Builder](https://builder.io/signup) [Get a demo](https://builder.io/m/demo)

<video controls=""><source type="video/mp4" src="https://cdn.builder.io/o/assets%2FYJIGb4i01jvw0SRdL5Bt%2F7736ea4be7394905a36a1eb3d9e97902?alt=media&amp;token=1a25a461-a21c-4df1-9a01-6c221531e9c6&amp;apiKey=YJIGb4i01jvw0SRdL5Bt"></video>

NEW! Fusion

What should we build?

Ask Visual Copilot to build Metrics dashboard |

[Connect a Repo](https://builder.io/app/projects/github/connect?fusion=true)