---
title: "Continuous Development with Claude Code on GitHub"
source: "https://piotrminkowski.com/2026/07/02/continuous-development-with-claude-code-on-github/?utm_source=substack&utm_medium=email"
author:
  - "[[piotr.minkowski]]"
published: 2026-07-03
created: 2026-07-06
description: "In this article, you will learn how to set up continuous development with the Claude GitHub App and Claude Code."
tags:
  - "clippings"
---

> [!summary]
> Step-by-step guide to setting up the Claude GitHub App and Claude Code GitHub Actions so Claude acts as a permanent contributor to a repository — implementing features from `@claude`-mentioned issues and automatically reviewing every pull request. Demonstrated on a Spring Boot REST API, with modified workflow YAML showing how to switch models, allow the Renovate bot, and wire in the code-review plugin. Closes with a candid look at API costs, which added up quickly even for simple tasks.

In this article, you will learn how to set up continuous development with the Claude GitHub App and Claude Code. In this workflow, Claude acts as a permanent contributor to your repository, implementing features and reviewing pull requests automatically in response to issue descriptions. I have already covered how to use Claude Code from the terminal and how to leverage it during local development. This time, we go a step further and bring Claude directly into GitHub, closing the loop between issue creation and merged, tested code.

The sample project we use is a Spring Boot REST API bootstrapped from a Backstage template. It is simple enough that the code stays readable, but complete enough to demonstrate real-world patterns: JPA persistence, full CRUD endpoints, two layers of tests, CI pipelines, and OpenAPI documentation. Everything Claude does to that project — every commit, every pull request — is driven through GitHub issues using the `@claude` mention syntax.

You can combine the approach described in the article below with Claude Code’s repository structure template for development. I described how to create such a structure in this [article](https://piotrminkowski.com/2026/03/24/claude-code-template-for-spring-boot/).

## Source Code

Feel free to use my source code if you’d like to try it out yourself. To do that, you must clone my sample GitHub [repository](https://github.com/piomin/sample-spring-rhdh.git). Then you should only follow my instructions.

## Installing the Claude GitHub App

First, navigate to [github.com/apps/claude](https://github.com/apps/claude) in your browser. Click **Install**, choose the account or organization that owns your repository, and select which repositories the app can access. The app needs read access to repository contents, issues, and pull requests. Once the installation is complete, you’ll see the Claude app, as shown in the photo below.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/07/Screenshot-2026-07-01-at-13.06.35.png?w=2132&ssl=1)

Next, add all the repositories, or select some you want Claude to run on. We will work with the `sample-app-rhdh` repository.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/07/Screenshot-2026-07-01-at-13.11.49.png?w=2336&ssl=1)

Then, go to your repository and run Cluade Code. Choose the `install-github-app` action that Claude Code suggests.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/07/Screenshot-2026-07-01-at-13.19.31.png?w=2312&ssl=1)

Claude Code will guide you through the process of creating GitHub workflows in your repository that will automatically respond to comments on issues and review pull requests. You don’t have to choose both options—for example, you can opt to review pull requests only. This is a mandatory step. Without creating GitHub Actions for your repository, the entire process simply won’t work.

![claude-code-github-install](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/07/Screenshot-2026-07-01-at-13.22.40.png?w=2318&ssl=1)

claude-code-github-install

After you confirm your selections, Claude Code will generate YAML files with GitHub workflow definitions and create a secret containing the Anthropic API key. The changes will be submitted to your repository as a pull request, which you will then need to merge into the main branch.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/07/Screenshot-2026-07-01-at-13.29.06.png?w=2318&ssl=1)

This is what it looks like in the GitHub repository.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/07/Screenshot-2026-07-01-at-13.43.30.png?w=1816&ssl=1)

After running the PR, you should see two files in the `.github/workflows` directory. The first one (`claude.yml`) triggers an action when a comment containing `@claude` is posted on an issue, and the second one (`claude-code-review.yml`) triggers a review of a new pull request with code changes.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/07/Screenshot-2026-07-01-at-13.49.08.png?w=946&ssl=1)

## Configure Claude Code Actions

You can find the complete GitHub Actions documentation for the action that calls Claude Code [here](https://github.com/anthropics/claude-code-action/blob/main/docs/usage.md). The configuration generated by Claude Code is ready to use right away. I wanted to change the default model from Claude Opus to Sonnet and enable the Renovate bot, which automatically updates dependencies. Below is a modified version of `claude.yml`. You can make similar changes for code review in the `claude-code-review.yml` file.

```
name: Claude Code

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]
  pull_request_review:
    types: [submitted]

jobs:
  claude:
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review' && contains(github.event.review.body, '@claude')) ||
      (github.event_name == 'issues' && (contains(github.event.issue.body, '@claude') || contains(github.event.issue.title, '@claude')))
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
      issues: read
      id-token: write
      actions: read # Required for Claude to read CI results on PRs
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - name: Run Claude Code
        id: claude
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          claude_args: '--model claude-sonnet-4-6'
          allowed_bots: 'renovate'

          # This is an optional setting that allows Claude to read CI results on PRs
          additional_permissions: |
            actions: read
```

```
name: Claude Code

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]
  pull_request_review:
    types: [submitted]

jobs:
  claude:
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review' && contains(github.event.review.body, '@claude')) ||
      (github.event_name == 'issues' && (contains(github.event.issue.body, '@claude') || contains(github.event.issue.title, '@claude')))
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
      issues: read
      id-token: write
      actions: read # Required for Claude to read CI results on PRs
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - name: Run Claude Code
        id: claude
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          claude_args: '--model claude-sonnet-4-6'
          allowed_bots: 'renovate'

          # This is an optional setting that allows Claude to read CI results on PRs
          additional_permissions: |
            actions: read
```

Here, in turn, is the modified `claude-code-review.yml` file.

```
name: Claude Code Review

on:
  pull_request:
    types: [opened, synchronize, ready_for_review, reopened]
    # Optional: Only run on specific file changes
    # paths:
    #   - "src/**/*.ts"
    #   - "src/**/*.tsx"
    #   - "src/**/*.js"
    #   - "src/**/*.jsx"

jobs:
  claude-review:
    # Optional: Filter by PR author
    # if: |
    #   github.event.pull_request.user.login == 'external-contributor' ||
    #   github.event.pull_request.user.login == 'new-developer' ||
    #   github.event.pull_request.author_association == 'FIRST_TIME_CONTRIBUTOR'

    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
      issues: read
      id-token: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - name: Run Claude Code Review
        id: claude-review
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          claude_args: '--model claude-sonnet-4-6'
          allowed_bots: 'renovate'
          plugin_marketplaces: 'https://github.com/anthropics/claude-code.git'
          plugins: 'code-review@claude-code-plugins'
          prompt: '/code-review:code-review ${{ github.repository }}/pull/${{ github.event.pull_request.number }}'
```

```
name: Claude Code Review

on:
  pull_request:
    types: [opened, synchronize, ready_for_review, reopened]
    # Optional: Only run on specific file changes
    # paths:
    #   - "src/**/*.ts"
    #   - "src/**/*.tsx"
    #   - "src/**/*.js"
    #   - "src/**/*.jsx"

jobs:
  claude-review:
    # Optional: Filter by PR author
    # if: |
    #   github.event.pull_request.user.login == 'external-contributor' ||
    #   github.event.pull_request.user.login == 'new-developer' ||
    #   github.event.pull_request.author_association == 'FIRST_TIME_CONTRIBUTOR'

    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
      issues: read
      id-token: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - name: Run Claude Code Review
        id: claude-review
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          claude_args: '--model claude-sonnet-4-6'
          allowed_bots: 'renovate'
          plugin_marketplaces: 'https://github.com/anthropics/claude-code.git'
          plugins: 'code-review@claude-code-plugins'
          prompt: '/code-review:code-review ${{ github.repository }}/pull/${{ github.event.pull_request.number }}'
```

Now that the changes have been made, all that’s left to do is make a few modifications to the source code in our repository!

## Using Claude Code with GitHub issues and pull requests

All you have to do is create an issue on GitHub and start your comment with `@claude`. Below is a list of issues I created for testing purposes. These are very simple tasks, such as adding a new Spring Data entity or repository, or creating a CircleCI pipeline.

![claude-code-github-issues](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/07/Screenshot-2026-07-01-at-14.09.48.png?w=2294&ssl=1)

claude-code-github-issues

Let’s open the selected issue. As you can see, the description starts with `@claude`. After reviewing the content in the description, the agent completed the work and then summarized it below. The change is in a temporary branch, from which you can easily create a PR.

![claude-code-github-comment](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/07/Screenshot-2026-07-01-at-14.13.59.png?w=2294&ssl=1)

claude-code-github-comment

Every time a new issue is created or a comment is added, a GitHub action runs to analyze the content. It looks like this:

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/07/Screenshot-2026-07-01-at-14.15.25.png?w=2294&ssl=1)

Just for the record, here’s a pull request with the change made by Claude Code. Every pull request is automatically analyzed by the Claude Code action for review.

![claude-code-github-pr](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/07/Screenshot-2026-07-01-at-14.26.01.png?w=2060&ssl=1)

claude-code-github-pr

Here is a list of actions taken in response to the appearance of a new PR in the repository.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/07/Screenshot-2026-07-01-at-14.31.57-scaled.png?w=2560&ssl=1)

## Final Thoughts

So it doesn’t sound too sweet, let’s talk a little about costs. Below is a cost chart for a few issues I created on GitHub. Based on the very simple tasks I described, the total came out to be quite a bit. Of course, in addition to generating the changes, Claude Code also reviewed each PR.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2026/07/Screenshot-2026-07-01-at-14.44.36.png?w=1926&ssl=1)

In this article, I’ve described an approach in which development is performed fully automatically by AI agents based on a list of issues created in the source code repository. This is the most intuitive approach if you want to generate code continuously with minimal developer involvement. The Claude GitHub App allows you to trigger AI agent actions based on comments in GitHub issues, as well as after creating a pull request. You can differentiate between the models used to generate code and those used to review changes merged via a pull request.
