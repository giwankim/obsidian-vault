---
title: "How Notion handles concurrent editing with CRDTs"
source: "https://www.notion.com/en-gb/blog/how-notion-handles-concurrent-editing-with-crdts?utm_source=theconsensus.dev&utm_medium=email"
author:
  - "[[Angelique Nehmzow]]"
  - "[[Emma Guo]]"
published: 2026-09-19
created: 2026-09-21
description: "Building a CRDT-based rich-text system that merges concurrent edits across Notion blocks—without losing anyone’s work"
tags:
  - "clippings"
---

> [!summary]
> Notion replaced last-write-wins block updates with a CRDT based on the Replicated Growable Array, using tombstones and Lamport-clock IDs so concurrent edits merge without data loss, plus Peritext-style anchored annotations for rich-text formatting. To handle text moving between blocks when a user presses Enter mid-block, they introduced text slices, text instances, and L/R "search labels" that route an edit to the right block even after concurrent splits. The system shipped in July 2025, processes millions of CRDT operations per minute, and underpins Offline Mode and agent collaboration.

Published in [Tech](https://www.notion.com/en-gb/blog/topic/tech)

Notion’s editor is commonly used in a collaborative setting, as teams of hundreds and thousands write and work together. But until 2025, Notion wasn’t *really* collaborative. To help people work more seamlessly, we redesigned our underlying system and data model for text editing. This involved implementing a system for conflict-free rich-text editing and developing techniques to support unique cases with Notion’s [block](https://www.notion.com/blog/data-model-behind-notion) -based document model.

To start, let’s imagine we have two users, Emma and Charlie, who are editing this block:

Build things

Version: 1

Emma updates the text to:

Build cool things

Version: 2, Emma

while Charlie updates the text to:

Build things quickly

Version: 2, Charlie

Emma and Charlie both have a version of the block that is *unaware* of the other person’s edits. They are making “concurrent” edits.

Ideally, the server would merge the two updates:

Build cool things quickly

Version: 3

However, the server processed each update to the block record as it arrived and whichever came last determined the result: “Build things quickly” or “Build cool things.” In this “last write wins” (LWW) system, one person’s edits would be *completely lost*. As the number of collaborators grows, the chance that one person’s change gets overwritten by someone else’s increases.

Notion pages still felt fairly collaborative because they typically consist of several blocks, each stored as a separate database record. People could edit separate blocks concurrently without overwriting one another, but edits to the same block could still conflict which would cause users to lose their changes. Furthermore, shipping [Offline Mode](https://www.notion.com/en-gb/blog/how-we-made-notion-available-offline) would increase the risk of this data loss occurring. Someone editing a page offline could lose all their changes if others edited the same blocks before they reconnected.

So, how did we fix this? We used a **Conflict-free Replicated Data Type,** or CRDT, to support rich text editing across Notion blocks, allowing users to concurrently edit, split and merge text.

## An intro to CRDTs

CRDTs are data structures that let multiple clients keep local copies of the same data and merge simultaneous changes deterministically. The main reason to use CRDTs is to make sure concurrent edits can be merged without losing anyone’s changes. Even if changes are not lost, each collaborator’s intent is not always preserved perfectly. If Emma wanted the text to be *exactly* “Build cool things,” the merged result would not meet that goal. But in longer documents, people are often changing more distant parts of the same text, and CRDTs work well to preserve intent in those cases.

The CRDT we use is based on a classic sequence CRDT called **Replicated Growable Array.** RGA is a tree data structure which contains all the characters ever inserted into it, each represented as a node with a unique and stable ID. Operations to insert or delete text can reference those IDs. We call these nodes “text items,” and the referenced IDs “origins.” The tree is initialized with `start` and `end` items. Let’s take a look at our original example:

Build things

Version: 1

The inserted characters are represented like this:

This is an insert operation to place “c” after origin `A@6`:

{

```
"operation": "insertText",
"textItemId": "E@13",
"originId": "A@6",
"content": "c",
"blockId": "A",
```

}

We see that the item with ID `A@6` is a space character:

This is the tree we would get from applying Emma operation to insert “cool”, and Charlie’s operation to insert “quickly”:

A deletion operation marks an item as removed but keeps it around as a "tombstone." This is because there may be in-flight or offline operations that depend on the IDs of the deleted characters. Removing those items from the tree would mean that we wouldn’t know where to apply the operations.

These are the tombstones we would get after deleting “cool”:

In our examples above we use IDs like `A@1`, where `A` is a simplified version of the “session ID,” which differentiates client sessions, and `1` is the Lamport clock, which is an increasing logical timestamp. Together, the session ID and Lamport clock make the ID unique: two clients may collide on Lamport clock but not on session ID, and a single client always increments the Lamport clock based on its knowledge of the highest (technically, the most recent) clock value.

Items that point to the same origin are sorted so the one with the most recent logical timestamp comes first, with session ID used as tie-breaker.

These operations to insert after `A@12` have ID `E@18` and `C@13`:

Since `18` is greater than `13`, these would always resolve to:

Build things! quickly

We can improve storage efficiency by not assigning *every single* character its own ID. Characters are usually grouped into words, so we can instead assign an ID to a contiguous run of characters from the same session and Lamport clock, and additionally store the run length.

Our example where “cool” gets deleted simplifies to:

## Supporting rich text

Notion docs are rich with formatting such as bold, italics, and page mentions. This means we need to resolve conflicts not just from text edits, but also from applying rich text annotations.

Build cool things quickly

Version: 3

Now, let’s say Charlie applies bold:

Build **cool things** quickly

Version: 4, Charlie

and Emma simultaneously applies italics:

Build *cool things* quickly

Version: 4, Emma

We want the final text to include both annotations:

Build ***cool things*** quickly

Version: 5

To support rich text, we introduced operations based on the [Peritext](https://www.inkandswitch.com/peritext/) algorithm. Our CRDT trees store operations to add and remove annotations on text items. We can then apply those annotations when we parse a tree.

Bolding “cool things” would create an operation like this, where “start” and “end” define the annotated range:

{

```
"operation": "addAnnotation",
"annotation": "bold",
"start": { "textItemId": "E@13", "anchor": "before" },
"end": { "textItemId": "C@13", "anchor": "before" },
```

}

“Start” and “end” define an anchor point that is right before or right after the boundary of an item. In this case, the anchor points are right before `E@13` and `C@13`:

These anchor points allow us to specify whether an annotation is “extendable” or not. Bold is an extendable annotation, meaning if someone types at the end of some bold text, the new text is also bold. This is why the end anchor is “before `C@13`,” because text after `A@12` (but before `C@13`) is still bold.

By contrast, a hyperlink is not an extendable annotation. If “cool things” were hyperlinked, the end anchor would be “after `A@12`.” This is because when a user types right after the “s” character, we would *not* want subsequent text to also be hyperlinked.

One text item may have multiple annotations attached to it. To support overlapping annotations, each text item can store an array of annotation operations. An annotation may span several items, but we store its operation only on the first; the ID range identifies the rest.

## Splitting text concurrently

In Notion, when a user presses “Enter” in the middle of a block, this creates a new block after it, and the text is split up across the two blocks.

In this next example, Emma splits the block after “Build”:

Build things

Build

things

while Charlie simultaneously appends a space and the word “quickly”:

Build things quickly

The result should be:

Build

things quickly

If Emma’s split is applied first, Charlie’s addition should land in the new block (Block B), *even though* Charlie made it in the original block (Block A). This means that we need a way to identify which block a user is editing, since concurrent edits mean a user’s edit could point to an origin that is no longer in the same database record.

In order support edits for text that may be moving between blocks simultaneously, we needed to develop a few new concepts.

The first is what we call a “text slice.” The text items in a block belong to a text slice, and every block is initialized with an empty text slice. When Emma splits Block A, the text slice in it is divided into two, and the second text slice is moved into Block B.

Text slices that belong to the same block are organized into a tree, which we call a “text slice tree,” and represent the text in that block. A text slice tree can contain slices that originated from different blocks.

When Emma splits Block A, the two blocks’ text slice trees change like this. Reconstructing each tree gives us the text in its block:

Text slices also belong to a “text instance,” which is a conceptual grouping for slices that descended from the same initial slice, with the ID of the block that originated it. While a slice may be split or moved around, it always keeps the same text instance. This means a block can contain text slices from multiple text instances:

We can use the text instance as a stable identifier to reference in operations. This lets us maintain a mapping of text instances to blocks that contain any text slice from that instance. Whenever a block receives a text slice from a new text instance, we update the mapping. When we receive an operation for a given text instance, we use this mapping to determine which blocks to fetch to locate and edit the target slice.

After Emma’s split is applied, the mapping shows that slices from instance A are in both Block A and Block B:

Charlie’s operations to insert “quickly” can still reference Block A, but as a text instance ID rather than as a block ID:

{

```
"operation": "insertText",
"textItemId": "C@13",
"originId": "A@12",
"content": " ",
"textInstanceId": "A",
```

}

We can then use the text instance ↔ block mapping to fetch the relevant blocks—in this case both Block A *and Block B* —to find the text slice to edit.

A limitation of this design is that you may need to potentially fetch *many* blocks in order to find a particular text slice, because there is no way to directly look up a block by text slice. The server loads *all* blocks that have *any* slice from the relevant text instance. Split a block 99 times, and you end up with 100 blocks, each of which contain a slice from the same text instance. That means in order to insert a character into one of those slices, your instance ↔ block mapping will tell you there are 100 blocks to fetch, and you then have to traverse their text slice trees to find your target text slice.

To address this problem, we devised what we call a “search label.” Every text slice has a search label which uniquely identifies it within a text instance. A text slice starts with an empty label, and every time it is split, we append the label with `L` or `R`.

These are the search labels after Emma splits Block A:

If she were to continue to split “things” into “thing” and “s,” then the label for “thing” would become `RL` and the label for “s” would become `RR`:

We can add the search label to our text instance ↔ block mapping and include it in operations, then use it to limit how many blocks are returned when we query the mapping.

Let’s return to our example. Emma splits “Build things”:

Build

things

And the mapping table includes these labels:

Let’s say Charlie’s client is aware of the update, and he inserts “quickly.” His operation will include the label R:

{

```
"operation": "insertText",
"textItemId": "C@13",
"originId": "A@12",
"content": " ",
"textInstanceId": "A",
"searchLabel": "R",
```

}

When we query the mapping, we search for blocks for instance A that also start with the label `R`, and there is actually only one block to fetch (where previously there were two).

The reason we look for block matches with a label that *starts with* the provided label, rather than exactly match it, is that the target slice may have been concurrently split. If Emma split “things” while Charlie was appending to it (and her change landed first), his operation would still include the label `R` even though the target slice is now labeled `RR`.

In practice, we are not literally storing labels like `LRL` on text slices and searching for them in Postgres with `.. label LIKE 'LR%'`. Instead, we use a compact encoding that improves storage efficiency fivefold.

While we haven’t validated this, we suspect this approach to handling splitting blocks may also be useful for other text editing systems that model chunks of text as independent nodes. For example, in a ProseMirror editor using Yjs, splits are modeled as a deletion in the first block and an insertion in the second. A concurrent edit may therefore remain in the original node, whereas our approach preserves its intended position across the split.

## Try it

We put together this widget to illustrate some of the ideas introduced in this blog post. We hope you have fun playing around with it, and that it helps grow your understanding our CRDT system.

<iframe src="https://www.notion.com/front-static/crdt-demo/index.html?embed=1" title="How Notion handles concurrent editing with CRDTs | Interactive demo" sandbox="allow-scripts allow-same-origin"></iframe>

At Notion, our scale and flexible data model introduced fun and practical challenges in bringing ideas from CRDT research into a real-world collaborative editor.

In July 2025, we deployed this system to production, making it one of the largest CRDT deployments in the world, as we process millions of CRDT operations every minute.

Our CRDT data model also supports Offline Mode and agent collaboration, and gives us a useful foundation for future features. We’re excited to use this foundation to improve how we real-time collaborators presence, or to batch suggestions such that they can be published and accepted together.

Editors are central to how we work and collaborate, yet it’s easy to overlook what makes them possible. We hope this post gave you a peek at some of the complexity involved in something as simple as typing together, and sparks some curiosity in how your everyday tools are built.

*This work wouldn't have been possible without the contributions of Angelique Nehmzow, Atul Varma, Ben Hughes, Charlie Andrews-Jubelt, Emma Guo, Fabricio Pontes Harsich, Jake Peyser, Kathleen Gao, Matthew Weidner, Michael Kuo, Rohit Valiveti, Ryan Billard, Shahan Khan, Slim Lim, Stephan Boyer, and Yifei Shen.*

*Interested in working on problems like this? We're always looking for talented engineers who want to build the future of collaborative software. Check out our open positions at* [notion.com/careers](https://notion.com/careers)*.*
