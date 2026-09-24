---
title: "Renovate: teaching an old dog new tricks • Marc Philipp"
source: "https://marcphilipp.de/blog/2026/08/16/renovate-teaching-an-old-dog-new-tricks/"
author:
published:
created: 2026-09-16
description: "Renovate is a super useful open-source tool that automatically keeps your project’s dependencies up to date (see also STF milestone 1 ). It has broad…"
tags:
  - "clippings"
---

> [!summary]
> Marc Philipp shows how to teach Renovate to update versions it does not recognize out of the box, using custom regex managers. The worked example keeps Node and npm versions in sync across a Gradle Kotlin build script, `.tool-versions`, and `package.json`. The cleaner final solution puts a `// renovate: datasource=... depName=...` comment above each assignment so one generic regex manager handles every annotated version — and the comment doubles as in-source documentation.

[Renovate](https://github.com/renovatebot/renovate) is a super useful open-source tool that automatically keeps your project’s dependencies up to date (see also [STF milestone 1](https://marcphilipp.de/blog/2025/01/19/stf-milestone-1-adopt-renovate/)). It has broad support for a lot of ecosystems, including Maven and Gradle dependencies, Docker files, GitHub Actions, and many more. Every now and then, I need to configure a version in a file that it does not support out of the box. While a bit fiddly, there’s a way of teaching Renovate to update that as well. Recently, I’ve come across an interesting pattern for doing so, which I’d like to share.

To work with a concrete example, let’s look at the configuration of the `html-report` subproject in the [open-test-reporting](https://github.com/ota4j-team/open-test-reporting) repository. Most of the project is written in Java, so it uses Gradle as its main build tool. However, the HTML report is a small Vue.js project and therefore requires Node and npm.

To make it easy for contributors to work with the project, the Gradle build uses the excellent [Gradle Plugin for Node](https://github.com/node-gradle/gradle-node-plugin) to download Node and install a certain version of npm:

```kotlin
plugins {
  id("com.github.node-gradle.node") version "7.1.0"
}

node {
  download = true // can be disabled via a property
  version = "24.19.0"
  npmVersion = "12.0.2"
}
```

For local development, I can disable the download via a Gradle property to avoid re-downloading a version of Node that I already have installed. To manage those versions, I use [mise-en-place](https://mise.jdx.dev/) which supports the `.tool-versions` file format of [asdf](https://asdf-vm.com/) (which is also understood by Renovate out of the box):

```plaintext
nodejs 24.19.0
```

Moreover, calling `npm install` requires a `package.json` file containing the project’s dependencies. Here, we also want to prescribe a certain version of npm to be used (which no longer calls install hooks by default):

```json
{
  ...
  "packageManager": "npm@12.0.2"
}
```

## Keeping versions in sync

As you can see, we have configured the version of both Node and npm in two places each. How can we keep these consistent? We could change the Gradle build to programmatically extract the version of Node from the `.tool-versions` file and that of npm from `package.json`. In fact, [an earlier version](https://github.com/ota4j-team/open-test-reporting/blob/15dd7d2bf93fa97c0ab1b9b2cb871058e1e6d6b3/html-report/build.gradle.kts#L13-L15) of the build script did just that (at least for the version of Node). However, doing so adds complexity to the build and – in this case – can also cause [issues](https://github.com/node-gradle/gradle-node-plugin/issues/350) with Gradle’s configuration cache.

To make matters worse, Renovate has no idea what `node.version` and `node.npmVersion` in the Gradle build script mean. Fortunately, there is a way to teach it by using a custom manager. The responsibility of a Renovate [(package) manager](https://docs.renovatebot.com/modules/manager/) is to detect and update the dependencies for a certain ecosystem. For example, there is one for [Gradle](https://docs.renovatebot.com/modules/manager/gradle/), one for [GitHub Actions](https://docs.renovatebot.com/modules/manager/github-actions/), and so on. Defining a [custom manager](https://docs.renovatebot.com/configuration-options/#custommanagers) is a way of extending the support of existing managers to detect versions in files or places that are not supported by default.

The [regex manager](https://docs.renovatebot.com/modules/manager/regex/) allows configuring a file pattern (which files it applies to) along with a string pattern to match inside those files. In our example above, we can define two custom managers for the Node and npm versions configured in the Gradle build script (in `renovate.json5`):

```json5
{
  $schema: 'https://docs.renovatebot.com/renovate-schema.json',
  customManagers: [
    {
      customType: 'regex',
      managerFilePatterns: ['/^html-report/build\\.gradle\\.kts$/'],
      matchStrings: [
        'version = "(?<currentValue>[^"]+)"',
      ],
      datasourceTemplate: 'node-version',
      depNameTemplate: 'node',
      versioningTemplate: 'node',
    },
    {
      customType: 'regex',
      managerFilePatterns: ['/^html-report/build\\.gradle\\.kts$/'],
      matchStrings: [
        'npmVersion = "(?<currentValue>[^"]+)"',
      ],
      datasourceTemplate: 'npm',
      depNameTemplate: 'npm',
    },
  ],
}
```

That will allow Renovate to update both Node and npm in the Gradle build script. Moreover, it will send a single PR updating the version in all files, which makes the duplication much less painful.

However, it also introduces a potential problem. If there’s any other Gradle DSL in that file with a `version = "..."` assignment, Renovate will think it’s holding the Node version and attempt updating it.

## A cleaner solution

There is a better way! Let’s change the build script to the following:

```kotlin
plugins {
  id("com.github.node-gradle.node") version "7.1.0"
}

node {
  download = true // can be disabled via a property
  // renovate: datasource=node-version depName=node versioning=node
  version = "24.19.0"
  // renovate: datasource=npm depName=npm
  npmVersion = "12.0.2"
}
```

This allows us to merge both custom managers into one:

```json5
{
  $schema: 'https://docs.renovatebot.com/renovate-schema.json',
  customManagers: [
    {
      customType: 'regex',
      managerFilePatterns: ['/^html-report/build\\.gradle\\.kts$/'],
      matchStrings: [
        '// renovate: datasource=(?<datasource>\\S+) depName=(?<depName>\\S+?)(?: versioning=(?<versioning>\\S+))?\\n\\s*\\w+ = "(?<currentValue>[^"]+)"',
      ],
    },
  ],
}
```

This regex will match all lines preceded by a `// renovate` comment that assign a value to a property. The comment in the build script also serves as documentation, clearly stating that this version is managed by Renovate. Moreover, it defines which data source (`datasource`), dependency (`depName`), and versioning scheme (`versioning`) should be used – right in the source code (see [Renovate docs](https://docs.renovatebot.com/modules/manager/regex/#required-capture-groups) for all supported capture groups). That avoids the problem of Renovate accidentally updating unrelated `version = "..."` assignments.

I’ve found this pattern to be really useful. It’s not only applicable to Gradle build scripts but all source files that support some form of line comment.
