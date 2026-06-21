---
title: "Technical presentations with Slidev"
source: "https://www.wimdeblauwe.com/blog/2024/11/05/technical-presentations-with-slidev/"
author:
published: 2024-11-05
created: 2026-06-21
description: "I recently started using Slidev for creating presentations.It is a tool to create a Powerpoint/Keynote/Google Slides like presentation, but using Markdown instead.In this blog post, I will explain the basics and share some of my favorite tips and tricks."
tags:
  - "clippings"
---

> [!summary]
> Slidev is a developer-friendly tool for building Powerpoint/Keynote-style presentations from Markdown, with a live-reload dev server. It supports built-in and custom Vue layouts, UnoCSS styling, Iconify icon packs, code highlighting, line-by-line reveals, Magic Move animations, Markdown tables, and PlantUML/Mermaid diagrams. The post walks through getting started and shares practical tips for technical presentations.

I recently started using [Slidev](https://sli.dev/) for creating presentations. It is a tool to create a Powerpoint/Keynote/Google Slides like presentation, but using Markdown instead. In this blog post, I will explain the basics and share some of my favorite tips and tricks.

## Getting started

To get started, you need to have Node installed on your system. After that, you can create a new presentation like this:

```
npm init slidev@latest
```

Run `npm install` to install all dependencies.

Finally, run `npm run dev` to start a live reload server that shows the presentation in your browser. By editing `slides.md`, you change the presentation.

Now that we have our project set up, let’s explore the different ways we can structure our slides using Slidev’s built-in layouts.

## Built-in Layouts

The simplest presentation that you can have is something like this:

```markdown
---
theme: default
---

# Welcome to Slidev

---

# This is the second slide

* You can add some bullet points
* Here is another one
```

It will generate a presentation with a title slide that shows "Welcome to Slidev" and a second slide with a title and some bullet points.

![slidev title slide](https://www.wimdeblauwe.com/images/2024/11/slidev-title-slide.png) ![slidev second slide](https://www.wimdeblauwe.com/images/2024/11/slidev-second-slide.png)

Each slide is separated by 3 dashes (`---`) in the markdown file.

The layout of the first slide is `cover` and the rest are `default`. You can choose the layout per slide by selecting one of the [built-in layouts](https://sli.dev/builtin/layouts) and apply it with the `layout` option in the frontmatter:

```markdown
---
layout: image-right
image: images/tools.jpg
---

# This is a slide with an image on the right

* Bullet points will be properly wrapped on the left side of the slide
```

![slidev slide with image right](https://www.wimdeblauwe.com/images/2024/11/slidev-slide-with-image-right.png)

The build-in layouts already go a long way, but you are not restricted to those. Some themes will add additional layouts that you can use. As an example, the [Penguin theme](https://github.com/alvarosaburido/slidev-theme-penguin) has a [two-thirds](https://github.com/alvarosabu/slidev-theme-penguin/blob/main/layouts/two-thirds.vue) layout option that allows to have a 2/3 and 1/3 split on the slide. And if you want something custom, you can [create your own layout](https://sli.dev/guide/write-layout) inside your presentation project as well.

While layouts determine the overall structure of your slides, you’ll often want to fine-tune the appearance of individual elements. This is where Slidev’s styling capabilities come into play.

## Styling

The HTML is styled via [UnoCSS](https://unocss.dev/) which is an Atomic CSS framework similar to Tailwind CSS. You can write HTML inside the markdown and use the UnoCSS classes to style that HTML.

For example:

```markdown
---

# Styling with UnoCSS

<div class="grid grid-cols-2">
    <div class="text-green-600 text-2xl">Left</div>
    <div class="text-red-400 text-2xl">Right</div>
</div>

---
```

This renders to:

![slidev styling](https://www.wimdeblauwe.com/images/2024/11/slidev-styling.png)

## Icons

To enable [icon support](https://sli.dev/features/icons), you need to install the [UnoCSS icon preset](https://unocss.dev/presets/icons) and then also the icon pack of your choice.

Run the following command to add the icon support and install the [Solar](https://icon-sets.iconify.design/solar/) and [Devicon](https://icon-sets.iconify.design/devicon/) icon packs:

```
npm install -D @unocss/preset-icons @iconify-json/solar @iconify-json/devicon
```

You can search for icons via [https://icones.js.org/collection/all](https://icones.js.org/collection/all).

To add an icon to your slide, you can either use a CSS class or use them directly as components.

Let’s, for example, render the [bag-music-outline](https://icones.js.org/collection/solar?icon=solar:bag-music-outline) icon from the Solar set:

```markdown
---

# Icons

## As CSS class

<div class="flex items-center gap-4 mb-8">
    <div class="i-solar-bag-music-outline" ></div>
    <div class="i-solar-bag-music-outline text-4xl" ></div>
</div>

## As component

<div class="flex items-center gap-4">
    <solar-bag-music-outline />
    <solar-bag-music-outline class="text-red-600 text-4xl" />
</div>

---
```

This creates a slide like this:

![slidev icons](https://www.wimdeblauwe.com/images/2024/11/slidev-icons.png)

The built-in features we’ve covered so far are powerful, but sometimes you need something more specific to your needs. Let’s look at how custom layouts can provide this customization.

## Custom layouts

With this basic knowledge, we can create a custom layout. To create a custom layout, you create a Vue component in the `layouts` directory.

As an example, we will create a layout that shows a slide title and 3 icons with text below each icon. Start by creating `layouts/three-icons.vue`:

```vue
<template>
  <div class="slidev-layout">
    <slot name="default"></slot>
    <div class='grid grid-cols-3 grid-rows-1 gap-20 mt-32'>
      <div class="flex flex-col justify-center items-center gap-4">
        <div class="text-6xl" :class="$attrs.firstIcon"/>
        <slot name="first"></slot>
      </div>
      <div v-click class="flex flex-col justify-center items-center gap-4">
        <div class="text-6xl" :class="$attrs.secondIcon"/>
        <slot name="second"></slot>
      </div>
      <div v-click class="flex flex-col justify-center items-center gap-4">
        <div class="text-6xl" :class="$attrs.thirdIcon"/>
        <slot name="third"></slot>
      </div>
    </div>
  </div>
</template>
```

The layout uses 4 slots: `default`, `first`, `second` and `third`. The default slot is used to place the slide title. The other slots represent the places where the icons and text will be placed. There are also the `firstIcon`, `secondIcon` and `thirdIcon` attributes that need to be set so the layout knows what components to render.

There is also the `v-click` attribute on the second and third div so that only the first icon is visible initially. Advance the presentation to reveal the other icons. If you want everything visible at once, just remove the `v-click` attribute in the custom layout.

We can use our custom layout to render something like this:

```markdown
---
layout: three-icons
firstIcon: i-solar-server-2-linear
secondIcon: i-solar-leaf-line-duotone
thirdIcon: i-devicon-html5
---

# Thymeleaf

::first::

Server-side rendering

::second::

Natural templating

::third::

Generates HTML
```

Result:

![slidev custom layout](https://www.wimdeblauwe.com/images/2024/11/slidev-custom-layout.png)

## Code

A lot of technical presentations will show code on the screen. Slidev makes this trivial by using Markdown code blocks.

```
---

# Some code blocks

* Java
\`\`\`java
public record User(String name, LocalDate birthday) {
}
\`\`\`

* HTML
\`\`\`html
<div class="flex gap-4">
  <div>Syntax highlighting is built-in</div>
</div>
\`\`\`

* JavaScript
\`\`\`javascript
export function sayHello() {
  console.log('Hello')
}
\`\`\`
---
```

Rendered, this looks like this:

![slidev code](https://www.wimdeblauwe.com/images/2024/11/slidev-code.png)

One neat trick I have found convenient is when you have some bullet items with each item having a small code block associated. Suppose now you want to bring in the bullet item with the associated code block one by one. For that case, you can use `<v-clicks every="2">` like this:

```
---

# Some code blocks

<v-clicks every="2">

* Java
\`\`\`java
public record User(String name, LocalDate birthday) {
}
\`\`\`

* HTML
\`\`\`html
<div class="flex gap-4">
  <div>Syntax highlighting is built-in</div>
</div>
\`\`\`

* JavaScript
\`\`\`javascript
export function sayHello() {
  console.log('Hello')
}
\`\`\`
</v-clicks>
---
```

If you cycle through the presentation, it will show each code block with the bulleted item in turn.

Another Slidev feature is highlighting of lines. This is especially useful to explain slightly longer code blocks.

```
---

# Code highlighting

\`\`\`java {7,13|5|6|9-12|*}
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
@RequestMapping("/")
public void HomeController {

  @GetMapping
  public String index() {
    return "index";
  }
}
\`\`\`

---
```

Note the sequence `{7,13|5|6|9-12|*}` after the language selection in the code block. This will instruct the highlighter to:

- First highlight lines 7 and 13
- Highlight line 5
- Highlight line 6
- Highlight lines 9 to 12
- Finally, show the complete code block

![slidev code highlight](https://www.wimdeblauwe.com/images/2024/11/slidev-code-highlight.png)

Another very nice thing you can do with code block is [Magic Move](https://sli.dev/features/shiki-magic-move). It will animate code blocks to bring in or remove lines of code.

A small example:

```
---

# Code Magic Move

\`\`\`\`md magic-move
\`\`\`js
console.log(\`Step ${1}\`)
\`\`\`
\`\`\`js
console.log(\`Step ${1 + 1}\`)
\`\`\`
\`\`\`ts
console.log(\`Step ${1 + 1}\`)
console.log('Done')
\`\`\`
\`\`\`\`
---
```

Note that you need to have 4 backticks with the `md magic-move` text. Then, you add a normal Markdown code block for each part that you want to show. The magic move will do its magic and animate automatically between the code blocks.

![slidev magic move](https://www.wimdeblauwe.com/images/2024/11/slidev-magic-move.gif)

## Tables

Standard Markdown tables are rendered nicely:

```
---

# Table

Here's a simple markdown table with 5 NBA stars and some fictional statistics:

| Player                | Points per Game | Rebounds per Game |
|-----------------------|-----------------|-------------------|
| LeBron James          | 28.4            | 8.7               |
| Giannis Antetokounmpo | 31.2            | 12.5              |
| Kevin Durant          | 29.8            | 7.3               |
| Joel Embiid           | 33.1            | 11.8              |
| Luka Doncic           | 32.6            | 9.4               |

---
```

![slidev table](https://www.wimdeblauwe.com/images/2024/11/slidev-table.png)

You can also combine tables with icons like this:

```
# Features

| Feature            | Slidev                                                                         | PowerPoint                                                                                          |
|--------------------|--------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| Developer-Friendly | <solar-clipboard-check-linear class="text-green-700" /> Markdown               | <solar-clipboard-remove-linear class="text-red-700"/>                                               |
| Version Control    | <solar-clipboard-check-linear class="text-green-700" /> Git-friendly           | <solar-clipboard-remove-linear class="text-red-700"/> Binary files                                  |
| Animations         | <solar-shield-warning-linear class="text-orange-700"/> CSS animations          | <solar-clipboard-check-linear class="text-green-700" /> Rich animation library                      |
| Customization      | <solar-clipboard-check-linear class="text-green-700" /> CSS and Vue components | <solar-shield-warning-linear class="text-orange-700"/> Built-in themes                              |
```

![slidev table icons](https://www.wimdeblauwe.com/images/2024/11/slidev-table-icons.png)

## Diagrams

Slidev supports [PlantUML and Mermaid diagrams](https://sli.dev/guide/syntax#diagrams). This is an example of a PlantUML diagram:

```
---

# PlantUML sequence diagram

<style>
    img {
        height: 80%;
        margin: auto;
    }
</style>

\`\`\`plantuml
@startuml

@startuml
    Alice -> Bob: Authentication Request
    Bob --> Alice: Authentication Response
    Alice -> Bob: Another authentication Request
    Alice <-- Bob: another authentication Response
@enduml

@enduml

\`\`\`

---
```

Note how we use the `<style>` section to make the diagram a proper size for the slide.

![slidev plantuml](https://www.wimdeblauwe.com/images/2024/11/slidev-plantuml.png)

And an example with Mermaid:

```
---

# Mermaid diagram

\`\`\`mermaid
pie title Pets adopted by volunteers
    "Dogs" : 386
    "Cats" : 85
    "Rats" : 15
\`\`\`
```

![slidev mermaid](https://www.wimdeblauwe.com/images/2024/11/slidev-mermaid.png)
