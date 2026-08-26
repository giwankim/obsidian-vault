---
title: "Imos Method"
source: "https://imoz.jp/algorithms/imos_method.html"
author:
published:
created: 2026-06-09
description: "English translation of the introductory article on the Imos method (いもす法)"
tags:
  - "clippings"
aliases:
  - "いもす法 (English)"
---

> [!info]
> This is an English translation of [[いもす法]].

> [!summary]
> The Imos method extends the cumulative-sum (prefix-sum) algorithm to multiple dimensions and higher orders. Instead of updating every cell, it records differences only at the boundaries (e.g. +1 on entry, −1 on exit) and takes a cumulative sum once at the end, reducing the complexity from $O(CT)$ to $O(C+T)$. The article builds up step by step: from the basic 1-D order-0 case, to 2-D rectangle addition, to special coordinate systems such as triangles and hexagons, and finally to higher-order Imos methods that approximate quadratic and Gaussian functions.

The Imos method is an extension of the cumulative-sum algorithm to multiple dimensions and higher orders. In competitive programming, only problems up to the 2-dimensional, first-order case appear, but research from 2012 showed that applying higher-order Imos methods in higher-dimensional spaces is useful in the fields of signal processing and image processing.

## Basics of the Imos Method: 1-D, Order-0

The simplest form of the Imos method adds order-0 functions (functions with a flat top, such as rectangular or step functions) along a single dimension. ![](https://imoz.jp/data/imos_method/simple_figure1.png)

Figure 1: Adding an order-0 function in one dimension

### Example Problem

You run a coffee shop. For each customer $i$ ($0 \le i < C$) who visits your shop, you are given the entry time $S_i$ and the exit time $E_i$ ($0 \le S_i < E_i \le T$). What is the maximum number $M$ of customers who were in the shop at the same time? If an exit and an entry happen at the same moment, the exit occurs first. (The intended solution should run in $O(C + T)$ even when $C$ is very large.)

#### Naive Solution

A naive solution is to add 1 to the count for every time slot each customer was present. However, this takes $O(CT)$ time.
```cpp
for (int i = 0; i < T; i++) table[i] = 0;
for (int i = 0; i < C; i++) {
  // Increase the count by 1 for every time from S[i] to E[i] - 1
  for (int j = S[i]; j < E[i]; j++) {
    table[j]++;
  }
}
// Find the maximum
M = 0;
for (int i = 0; i < T; i++) {
  if (M < table[i]) M = table[i];
}
```

#### Solution with the Imos Method

The Imos method takes the view that we only need to count at the doorway: record +1 at the entry time and −1 at the exit time, then simulate the whole timeline just before computing the answer. Recording takes $O(C)$ and the simulation takes $O(T)$, so the total complexity is $O(C + T)$.
```cpp
for (int i = 0; i < T; i++) table[i] = 0;
for (int i = 0; i < C; i++) {
  table[S[i]]++;  // Entry: increase the count by 1
  table[E[i]]--;  // Exit: decrease the count by 1
}
// Simulate
for (int i = 0; i < T; i++) {
  if (0 < i) table[i] += table[i - 1];
}
// Find the maximum
M = 0;
for (int i = 0; i < T; i++) {
  if (M < table[i]) M = table[i];
}
```

## Extending the Dimensions

The greatest strength of the Imos method compared with the naive approach is how well it holds up as the number of dimensions grows. Since there is no escaping the curse of dimensionality, applying it in very high dimensions is difficult, but problems set in 2 or 3 dimensions are extremely common, and in those situations the Imos method is very useful.

### Example Problem

You are playing a game where you catch monsters of various kinds. You are standing in a grassy field made up of $W \times H$ tiles. $N$ kinds of monsters appear in this field. Monster $i$ only appears in the region $A_i \le x < B_i$, $C_i \le y < D_i$. To play the game efficiently, you want to know the maximum number of monster species that can appear on a single tile. (Assume $W \times H$ is small enough to compute over, while $N$ can be large.) ![](https://imoz.jp/data/imos_method/2d_imos0.png)

Figure 2: Rectangles where monsters appear (red), and
the number of monster species appearing on each tile

#### Naive Solution

A naive solution is to add 1 to every tile contained in each monster's rectangle. However, this takes $O(NWH)$ time.
```cpp
for (int y = 0; y < H; y++) {
  for (int x = 0; x < W; x++) {
    tiles[y][x] = 0;
  }
}
for (int i = 0; i < N; i++) {
  // Add 1 to the range [(A[i],C[i]), (B[i],D[i])) where monster i appears
  for (int y = C[i]; y < D[i]; y++) {
    for (int x = A[i]; x < B[i]; x++) {
      tiles[y][x]++;
    }
  }
}
// Find the maximum
int tile_max = 0;
for (int y = 0; y < H; y++) {
  for (int x = 0; x < W; x++) {
    if (tile_max < tiles[y][x]) {
      tile_max = tiles[y][x];
    }
  }
}
```

#### Solution with the Imos Method

With the Imos method, for each rectangle we add +1 at the top-left $(A[i], C[i])$, −1 at the top-right $(A[i], D[i])$, −1 at the bottom-left $(B[i], C[i])$, and +1 at the bottom-right $(B[i], D[i])$, then compute cumulative sums just before finding the answer. Recording takes $O(N)$ and the cumulative sums take $O(WH)$, so the total complexity is $O(N + WH)$.
```cpp
for (int y = 0; y < H; y++) {
  for (int x = 0; x < W; x++) {
    tiles[y][x] = 0;
  }
}
// Add the weights (Figure 3)
for (int i = 0; i < N; i++) {
  tiles[C[i]][A[i]]++;
  tiles[C[i]][B[i]]--;
  tiles[D[i]][A[i]]--;
  tiles[D[i]][B[i]]++;
}
// Cumulative sums in the horizontal direction (Figures 4, 5)
for (int y = 0; y < H; y++) {
  for (int x = 1; x < W; x++) {
    tiles[y][x] += tiles[y][x - 1];
  }
}
// Cumulative sums in the vertical direction (Figures 6, 7)
for (int y = 1; y < H; y++) {
  for (int x = 0; x < W; x++) {
    tiles[y][x] += tiles[y - 1][x];
  }
}
// Find the maximum
int tile_max = 0;
for (int y = 0; y < H; y++) {
  for (int x = 0; x < W; x++) {
    if (tile_max < tiles[y][x]) {
      tile_max = tiles[y][x];
    }
  }
}
```
![](https://imoz.jp/data/imos_method/2d_imos1.png)

Figure 3: Result of adding the weights

![](https://imoz.jp/data/imos_method/2d_imos2.png)

Figure 4: Accumulating in the horizontal direction

![](https://imoz.jp/data/imos_method/2d_imos3.png)

Figure 5: Result of accumulating horizontally

![](https://imoz.jp/data/imos_method/2d_imos4.png)

Figure 6: Accumulating in the vertical direction

![](https://imoz.jp/data/imos_method/2d_imos0.png)

Figure 7: Result of accumulating vertically

## Extending to Special Coordinate Systems

The Imos method can also be applied to triangular and hexagonal coordinate systems. To figure out where to add the weights and in which directions to accumulate, you take differences of the target shape in various directions, aiming to make the number of weighted cells as small as possible. ![](https://imoz.jp/data/imos_method/triangle.png)

Figure 8: A triangular coordinate system

### How to Take the Differences

Figure 9 shows the weights we want to fill in on the triangular coordinate system. The green lines indicate that the middle portion has been omitted (for a triangle with side length 4, ignoring the lines gives the same result in these figures). To perform this weighting with the Imos method, we need to keep taking differences until the number of weighted cells becomes small enough, which reveals where to place the weights and in which directions to take the cumulative sums.

Figures 9 through 12 show the process of taking differences. Along the way we took "a difference from top-left to bottom-right," "a difference from top-right to bottom-left," and "a difference from left to right." So to compute a triangular cumulative sum with the Imos method, place the values as in Figure 12 and perform the reverse operations in order: "a cumulative sum from left to right," "a cumulative sum from top-right to bottom-left," and "a cumulative sum from top-left to bottom-right." ![](https://imoz.jp/data/imos_method/triangle1.png)

Figure 9: The weights to fill in

![](https://imoz.jp/data/imos_method/triangle2.png)

Figure 10: Difference of Figure 9 from top-left to bottom-right

![](https://imoz.jp/data/imos_method/triangle3.png)

Figure 11: Difference of Figure 10 from top-right to bottom-left

![](https://imoz.jp/data/imos_method/triangle4.png)

Figure 12: Difference of Figure 11 from left to right

The same approach works not only for triangles but also for hexagons, and even for weights that are not constant but have a slope (as long as it is polynomial).

## Extending the Order

Problems in competitive programming go up to first order at most, but the Imos method can also be applied to higher-order piecewise polynomial functions. Functions that are usually considered hard to approximate well with polynomials can sometimes be expressed as piecewise polynomials, and exploiting this makes it possible to speed up the continuous wavelet transform.

### Differences of a Quadratic Function

Let us try the Imos method with a quadratic function in one dimension.

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 1 | 4 | 9 | 16 | 25 | 36 | 49 |

↓ difference　　　↑ cumulative sum

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 1 | 3 | 5 | 7 | 9 | 11 | 13 |

↓ difference　　　↑ cumulative sum

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 1 | 2 | 2 | 2 | 2 | 2 | 2 |

↓ difference　　　↑ cumulative sum

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |

Figure 13: Differences of the quadratic function $(x-2)_+^2$

From Figure 13, we can see that to add the quadratic function $(x-a)_+^2$, we add 1 to the table at positions $a+1$ and $a+2$, and at the end take the cumulative sum three times — so the Imos method can be applied with quadratic functions (where $(\cdot)_+ = \max(0, \cdot)$). In the same way, the Imos method can be applied to functions of even higher order.

### Gaussian Functions and the Imos Method

As an example of extending the order, let us look at the Gaussian function. To apply the Imos method, we approximate the Gaussian function on the left-hand side of Equation 1 with a piecewise polynomial like the right-hand side. As Figure 14 shows, this approximation is very close.

![](https://imoz.jp/data/imos_method/gaussian.tex.png)

Equation 1: A Gaussian function (left-hand side) and its approximation (right-hand side)

![](https://imoz.jp/data/imos_method/gaussian.png)

Figure 14: The Gaussian function (blue) and its polynomial approximation (red)

| \-12 | \-11 | \-10 | \-9 | \-8 | \-7 | \-6 | \-5 | \-4 | \-3 | \-2 | \-1 | 0 | 1 | 2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | \-11 | \-11 | 0 | 0 | 0 |

↓ cumulative sum　　　↑ difference

| \-12 | \-11 | \-10 | \-9 | \-8 | \-7 | \-6 | \-5 | \-4 | \-3 | \-2 | \-1 | 0 | 1 | 2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 3 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | \-5 | \-16 | \-16 | \-16 | \-16 |

↓ cumulative sum　　　↑ difference

| \-12 | \-11 | \-10 | \-9 | \-8 | \-7 | \-6 | \-5 | \-4 | \-3 | \-2 | \-1 | 0 | 1 | 2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 3 | 9 | 15 | 21 | 27 | 33 | 39 | 45 | 40 | 24 | 8 | \-8 | \-24 |

↓ cumulative sum　　　↑ difference

| \-12 | \-11 | \-10 | \-9 | \-8 | \-7 | \-6 | \-5 | \-4 | \-3 | \-2 | \-1 | 0 | 1 | 2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 3 | 12 | 27 | 48 | 75 | 108 | 147 | 192 | 232 | 256 | 264 | 256 | 232 |

Figure 15: The Gaussian function approximated by the Imos method

| \-12 | \-11 | \-10 | \-9 | \-8 | \-7 | \-6 | \-5 | \-4 | \-3 | \-2 | \-1 | 0 | 1 | 2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.49 | 3.42 | 7.28 | 14.41 | 26.57 | 45.58 | 72.76 | 108.08 | 149.41 | 192.20 | 230.09 | 256.31 | 265.70 | 256.31 | 230.09 |

Figure 16: The target Gaussian function being approximated

Furthermore, since a $d$-dimensional Gaussian function can be expressed as a product of 1-dimensional Gaussian functions, the $d$-dimensional Imos method can be applied. And because a Gaussian's weight is determined by Euclidean distance from the center (circular in 2-D, spherical in 3-D), it is very useful when you want values that are rotation-invariant.

If you would like to know more about this, see the [presentation slides from ICPR 2012](https://imoz.jp/documents/121112_icpr.pdf).

## Appendix

### Problems Where the Imos Method Applies

- \[Easy\] Osaki … 1-D order-0 Imos method, ACM-ICPC Japan Alumni Group Practice Contest for Japan Domestic 2007 - \[[AOJ](http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=2013)\]
- \[Easy\] Nails … order-0 Imos method on triangular coordinates, [Japanese Olympiad in Informatics 2012](http://www.ioi-jp.org/joi/2011/2012-ho-prob_and_sol/index.html) Final Round problem 4 - \[[AOJ](http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=0574)\]
- \[Medium\] Paint Colors … coordinate compression + 2-D order-0 Imos method + breadth-first search (depth-first search also works depending on stack capacity), [Japanese Olympiad in Informatics 2008](http://www.ioi-jp.org/joi/2007/2008-ho-prob_and_sol/index.html) Final Round problem 5 - \[[AOJ](http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=0531)\]
- \[Medium\] Plugs … 2-D order-0 Imos method + ad hoc, Japanese Olympiad in Informatics 2010, training camp day 4 problem 4
- \[Hard\] Pyramid … first-order Imos method on a special coordinate system, [Autumn Fest 2012: I](http://autumn_fest.contest.atcoder.jp/tasks/autumn_fest_09)
