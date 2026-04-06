---
title: "An interactive intro to quadtrees"
source: "https://growingswe.com/blog/quadtrees?utm_source=substack&utm_medium=email"
author:
  - "[[growingSWE]]"
published: 2026-02-24
created: 2026-03-09
description: "An interactive exploration of quadtrees. Start with brute-force spatial search, build recursive space partitioning step by step, then use it for point lookups, range queries, nearest-neighbor search, collision detection, and image compression."
tags:
  - "clippings"
  - "data-structures"
  - "algorithms"
  - "system-design"
---

> [!summary]
> Interactive guide to quadtrees, progressing from brute-force spatial search to recursive partitioning. Covers point lookups, range queries, nearest-neighbor search, collision detection, and image compression.

*While reading system design blogs, I kept seeing that Uber uses quadtrees. So I try to understand why*

Suppose you're building a map application. You have millions of restaurants, gas stations, and landmarks, each with a latitude and longitude. A user taps the screen and asks: "What's near me?"

The simplest approach is to check every single point. Compute the distance from the user's location to every restaurant in the database, keep the ones that are close enough, and throw away the rest.

This works, but it's slow.

With a thousand points, you barely notice the delay. With a million, you're doing a million distance calculations for every single query. On a phone updating the map as the user scrolls, that's untenable.

Drag out a search region below and watch the brute-force approach check every point, one by one:

Scroll to load interactive demo

Every point gets examined, regardless of where it sits. Points on the opposite side of the map get the same treatment as points right next to the query region. We're doing a lot of unnecessary work.

We have no way to skip over points that are obviously too far away. What if we could organize the space itself so that when we search, we can immediately rule out entire regions?

## Dividing space

Think about how you'd search a large room for a lost key. You wouldn't examine every square inch sequentially. You'd split the room into sections (by the couch, near the door, under the table) and rule out entire sections at a glance. "I didn't go near the kitchen, so skip that."

A quadtree does the same thing for two-dimensional space. It takes a rectangular region and divides it into four equal quadrants: northwest, northeast, southwest, southeast. If a quadrant has too many points in it, it subdivides again and again. Each subdivision creates smaller and smaller cells where points are densely packed.

Step through the construction below. Each time a new point is inserted, watch the tree decide whether it needs to split a region:

Scroll to load interactive demo

The tree starts as a single region covering the whole space. As points arrive, they get dropped into the region that contains them. When a region exceeds its capacity (the maximum number of points it can hold before splitting), the region divides into four children, and the existing points get redistributed.

Regions with many nearby points keep subdividing. Regions with few or no points stay large. The tree adapts to the data: dense areas get fine-grained cells, sparse areas stay coarse. The split grid is predetermined (always at midpoints), but the tree only refines cells that need it. Sparse regions stay as single large nodes while dense regions subdivide deeply.

Click to place points and watch the tree respond in real time:

Scroll to load interactive demo

Add a cluster of points in one corner and watch that corner subdivide deeply while the rest of the space stays untouched. Then scatter a few points across the empty region and watch it split only where needed. The tree grows around the data.

Here's the insertion algorithm in Python. Step through the code and watch each line execute on the tree:

Scroll to load interactive demo

## The tree behind the grid

The grid lines on the visualization represent a tree structure underneath. Every region is a node. When a node splits, it creates four children. The root node covers the entire space. Leaf nodes (nodes with no children) hold the actual points.

Hover over nodes in the tree below to see which spatial region they correspond to:

Scroll to load interactive demo

The spatial view (the grid of rectangles) and the tree view (the hierarchy of nodes) represent the same structure. Searching for a point means walking down the tree: at each node, you check which of the four children contains your target coordinate and recurse into that child. You never visit the other three.

This is the same idea behind binary search. In a sorted array, you compare against the middle element and eliminate half the remaining candidates. In a quadtree, you choose one of four quadrants and ignore the other three regions. Each level narrows the search space by a factor of four instead of two.

## Tuning the split

The capacity of each node (how many points it can hold before splitting) controls the shape of the tree. A low capacity means nodes split early, producing a deep tree with many small cells. A high capacity means nodes tolerate more points before splitting, producing a shallow tree with larger cells.

Drag the slider to see how capacity changes the structure:

Scroll to load interactive demo

At capacity 1, every point gets its own cell, and the tree subdivides as deeply as possible. At capacity 10, many points coexist in the same node, and the tree stays shallow.

There's a tradeoff: a lower capacity means you can skip more space during queries (you zoom in faster), but the tree has more nodes and uses more memory. A higher capacity means fewer nodes but each node requires checking more points linearly. As a starting point, capacities between 4 and 16 are reasonable defaults, though the best value depends on your data distribution and query patterns.

## Drilling down to a point

Now that we can build the tree, let's use it to search. Finding a specific point means starting at the root and asking: which child quadrant contains this coordinate? Then you recurse into that child and ask again. Each level of the tree cuts the search space by roughly three-quarters.

Click any point below and step through the lookup path:

Scroll to load interactive demo

Notice how the highlighted region shrinks at each step. The algorithm never examines points outside the narrowing window. In a balanced tree with $n$ points, this takes about $\log_4(n)$ steps. For a million points, that's roughly 10 steps instead of a million comparisons.

## Finding everything in a region

Point lookups are useful, but the operation you'll reach for more often is a range query: give the tree a rectangular region and retrieve every point inside it, without scanning the entire dataset.

The algorithm walks the tree recursively. At each node, it checks: does this node's bounding box overlap with the query rectangle? If not, the entire subtree gets pruned (skipped). If it does overlap, it tests the node's points against the query and recurses into the children.

Drag to draw a query rectangle and watch which nodes get visited (blue) vs. pruned (red):

Scroll to load interactive demo

Step through the Python implementation. Watch the algorithm decide which branches to visit and which to prune:

Scroll to load interactive demo

The pruned nodes (in red) represent entire regions of space that the algorithm never examines. The points inside those regions are never checked. Compare the "Nodes Visited" count to the total number of points. The quadtree is doing far less work than a brute-force scan.

The efficiency depends on the query size relative to the data distribution. A small query in a sparse region prunes almost everything. A query that covers the whole space prunes nothing (because every node overlaps), degenerating to a brute-force scan. The quadtree gives you the most benefit when your queries are spatially local, which is exactly the common case for map applications, game physics, and spatial databases.

## Finding the closest point

Range queries ask "what's inside this box?" But sometimes the question is "what's nearest to this location?" This is the nearest neighbor problem, and you don't know how big your search radius should be. The nearest point might be right next to you or far away.

The algorithm maintains a running "best distance" that starts at infinity. As it walks the tree, it checks each visited point and updates the best distance if it finds something closer. Before recursing into a child node, it checks whether the closest possible point in that child's bounding box is farther than the current best. If so, the entire subtree gets pruned.

Click anywhere to set a query location and step through the search:

Scroll to load interactive demo

The dashed circle shows the current best distance. As the algorithm finds closer points, the circle shrinks, which causes more subtrees to fail the "could contain a closer point?" test and get pruned. The search usually gets cheaper as it progresses.

The algorithm also visits children in order of distance to the query point. This means it checks the most promising quadrants first, which tends to find a good candidate early and enables aggressive pruning of the remaining quadrants. Without this ordering, the algorithm would still produce the correct result, but it would prune fewer nodes.

For well-distributed points, nearest neighbor search is often near $O(\log n)$ in practice. In the worst case (all points clustered tightly or along a line), it can degrade to $O(n)$, but this is uncommon with typical spatial data.

## Collision detection

Games and physics simulations need to detect which objects are touching or overlapping. With $n$ objects, checking every pair is $O(n^2)$ comparisons, which gets expensive fast. A hundred objects means roughly 5,000 pair checks. A thousand means nearly 500,000.

A quadtree reduces this: rebuild the tree each frame, and for each object, query only the nearby region. Objects in distant quadrants are never compared.

Hit "Run" to watch particles bounce around with quadtree-accelerated collision detection:

The tree is rebuilt every frame. For scenes of this scale, quadtree construction is fast enough to rebuild from scratch each frame, though larger simulations may benefit from incremental updates. Each particle queries its neighborhood for potential collisions, typically checking only 5 to 15 candidates instead of all 40. Red highlights indicate colliding pairs.

Toggle "Show Grid" to see the quadtree adapting to where the particles cluster in real time. Dense clusters get finer subdivisions; empty space stays coarse.

Real game engines use this pattern (or its 3D cousin, the octree) for broad-phase collision detection: the quadtree quickly identifies candidate pairs, and a more expensive narrow-phase check tests the actual geometry.

## Compressing images

Quadtrees aren't limited to point data. They can also partition regions of continuous data, like the pixels of an image.

You look at a region of the image. If all the pixels are roughly the same color (below some threshold), you store the average color for the whole region as a single value. If the pixels vary too much, you split the region into four quadrants and try again.

Uniform regions (solid backgrounds, smooth gradients) get stored as large blocks. Detailed regions (edges, textures) get subdivided into smaller blocks. You end up with a compressed representation that preserves detail where it exists and simplifies where it can.

Adjust the threshold to control how aggressively the tree merges regions:

A low threshold preserves detail (more leaf nodes, less compression). A high threshold merges aggressively (fewer leaves, more compression, but the image gets blocky). The grid overlay shows the quadtree structure: large cells in uniform areas, small cells where detail is preserved.

Quadtree-based image compression formats and level-of-detail systems all work this way. Satellite imagery, terrain rendering, and geographic information systems use quadtree decomposition to serve data at varying resolutions: zoomed out, you see large coarse blocks; zoomed in, you see fine-grained tiles. The same principle extends to three dimensions (octrees) for volume rendering and 3D spatial indexing.

Real image compression (JPEG, PNG) uses different techniques (DCT, entropy coding), but quadtrees capture the same principle: spend your bits where the detail is, not uniformly across the whole image.

## Where quadtrees appear

Quadtrees are everywhere spatial data exists. Mapping services use quadtree-like tile pyramids to serve map tiles at different zoom levels (Bing's quadkey system, for example, addresses tiles as base-4 paths). Game engines use them for collision detection and visibility culling. Geographic information systems use spatial indexes to store and query spatial datasets. PostGIS uses GiST indexes (R-tree -style) for spatial queries on geometries, while PostgreSQL's core supports quadtree-like SP-GiST indexes for certain data types like points.

The quadtree is the two-dimensional case of a broader family of space-partitioning data structures. Octrees extend the same idea to three dimensions (splitting cubes into eight children), KD-trees use alternating axis-aligned splits (splitting along x, then y, then x again), and R-trees group nearby objects into bounding rectangles. Each variant makes different tradeoffs between construction time, query speed, and update cost.

They all organize data by location so you can skip irrelevant regions, replacing "check everything" with "check the things that could possibly matter." That's what took us from a million comparisons to ten.
