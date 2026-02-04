---
title: "Formation"
source: "https://formation.dev/guide/"
author:
published:
created: 2026-01-25
description:
tags:
  - "clippings"
---
### 👋 Welcome

Formation helps software engineers prepare for FAANG-level interviews by combining proven curriculum with feedback from senior mentors. This guide distills the core data structures, algorithms, and interview habits you should be fluent in before you meet with a top-tier team. If anything is unclear, ask in this [LinkedIn thread](https://fm.dev/jg8); one of our engineers will reply.

### 📋 How to Use This Guide

Move through the topics in order and deliberately practice each technique before advancing. Pair every study block with hands-on coding (LeetCode, freeCodeCamp, HackerRank) and speak your thoughts out loud as if you were in an interview.

**Beginner (start here):** Arrays, sorting basics, stacks & queues, recursion foundations, hash tables, linked lists.

**Intermediate:** Binary trees & BSTs, binary search patterns, two pointers & sliding window, heaps, basic dynamic programming, backtracking starter problems.

**Advanced:** Tries, advanced DP & greedy patterns, graphs, bit manipulation, optimization problems.

**Expert / nice-to-have:** Advanced graph algorithms, complex optimizations, specialized data structures. Only tackle these if the earlier material feels automatic.

Every section follows the same rhythm:

1. **Concept:** Understand what problem the tool solves and its runtime profile.
2. **Watch or read:** Use the linked resources to internalize the idea quickly.
3. **Practice:** Code the recommended problems without copying a solution. Reflect on mistakes and re-solve later.

### 🎯 Formation Engineering Method

Lean on Formation’s [Engineering Method](https://formation.dev/blog/the-engineering-method/) for every interview or production problem. It replaces panic with a deliberate feedback loop:

1. **Thoroughly understand the problem** – Clarify requirements, generate your own “happy path” examples, and stress-test edge cases until the goal is unambiguous.
2. **Identify and explore possible solutions** – Surface multiple patterns or data structures, sketch how each would work, and note risks or prerequisites.
3. **Choose a solution** – Pick the approach that best satisfies constraints, then articulate why you’re choosing it (and why you’re not choosing the others).
4. **Make a plan** – Break the solution into ordered steps or helper functions so implementation becomes execution, not ideation.
5. **Build it** – Code intentionally, narrate invariants, and keep the plan in view so you notice when reality drifts.
6. **Test it** – Validate with baseline, edge, and stress cases, analyze complexity, and capture follow-up improvements for the next iteration.

**Reflection prompts:**

- Which step do you tend to rush under pressure, and what reminder will keep you honest in the next session?
- How will you capture learnings from each iteration so your future self starts further along the loop?

Treat these steps as a loop: if testing exposes a gap, rewind to the step where the assumption broke and iterate forward again.

#### Complexity Primer

- Review Big-O intuition with [this video](https://www.youtube.com/watch?v=D6xkbGLQesk) and [this article](https://www.freecodecamp.org/news/big-o-notation-why-it-matters-and-why-it-doesnt-1674cfa8a23c/).
- Know the common classes: O(1), O(log n), O(n), O(n log n), O(n²), and when exponential or factorial growth appears.
- Practice communicating complexity out loud for each solution you implement.

### 🗒 Arrays & Searching

Arrays are the foundation for most interview questions. Master them before anything else.

1. **O(n²) Sorting (Insertion, Selection, Bubble):** Watch quick refreshers on [Insertion Sort](https://www.youtube.com/watch?v=JU767SDMDvA), [Selection Sort](https://www.youtube.com/watch?v=g-PGLbMth_g&feature=youtu.be), and [Bubble Sort](https://www.youtube.com/watch?v=xli_FI7CuzA). Compare runtimes via [this chart](https://www.geeksforgeeks.org/comparison-among-bubble-sort-selection-sort-and-insertion-sort/) and implement each on [LeetCode #912](https://leetcode.com/problems/sort-an-array/).
2. **Binary Search:** Internalize the pattern with [this walkthrough](https://www.youtube.com/watch?v=P3YID7liBug), solve [Binary Search](https://leetcode.com/problems/binary-search/), then tackle [First Bad Version](https://leetcode.com/problems/first-bad-version/).
3. **Sliding Window & Two Pointers:** Learn the technique through [this guide](https://www.youtube.com/watch?v=MK-NZ4hN7rs). Apply it to [Longest Substring Without Repeating Characters](https://leetcode.com/problems/longest-substring-without-repeating-characters/) and stretch with [Minimum Swaps to Group All 1's II](https://leetcode.com/problems/minimum-swaps-to-group-all-1s-together-ii/).
4. **Prefix Sums & Kadane's Algorithm:** Review [Kadane's explanation](https://www.youtube.com/watch?v=86CQq3pKSUw), solve [Maximum Subarray](https://leetcode.com/problems/maximum-subarray/), and use prefix sums for [Subarray Sum Equals K](https://leetcode.com/problems/subarray-sum-equals-k/).
5. **Divide & Conquer Sorting:** Learn [Merge Sort](https://youtu.be/4VqmGXwpLqc) and [Quick Sort](https://youtu.be/Hoixgm4-P4M), then practice on [LeetCode #912](https://leetcode.com/problems/sort-an-array/). Focus on explaining why quicksort's average vs. worst-case differs.

**Reflection prompts:**

- Which array technique do you overuse, and what signal tells you to switch patterns?
- How would you teach someone else to pick between prefix sums, two pointers, and sliding window for a new problem?

### 📚 Stacks & Queues

These structures power parsing, undo systems, scheduling, and BFS.

1. **Stacks (LIFO):** Watch [this overview](https://www.youtube.com/watch?v=wjI1WNcIntg), skim [the article](https://www.geeksforgeeks.org/stack-data-structure/), then solve [Valid Parentheses](https://leetcode.com/problems/valid-parentheses/) and [Evaluate Reverse Polish Notation](https://leetcode.com/problems/evaluate-reverse-polish-notation/).
2. **Queues (FIFO):** Learn the model via [this video](https://www.youtube.com/watch?v=XuCbpw6Bj1U) and [article](https://www.geeksforgeeks.org/queue-data-structure/). Practice with [Design Circular Queue](https://leetcode.com/problems/design-circular-queue/) and [Implement Stack Using Queues](https://leetcode.com/problems/implement-stack-using-queues/).
3. **Deques:** Understand double-ended operations with [this primer](https://www.geeksforgeeks.org/deque-set-1-introduction-applications/) and apply it to [Sliding Window Maximum](https://leetcode.com/problems/sliding-window-maximum/).

**Reflection prompts:**

- When does a queue-like solution beat recursion or DFS, and how can you justify that choice quickly?
- Which monotonic stack or deque invariant do you rely on to stay correct while coding?

### 🔄 Recursion Fundamentals

Recursion underpins tree traversals, divide-and-conquer, and backtracking. Focus on base cases, progress toward termination, and state passed between calls.

1. Build intuition with [this video](https://www.youtube.com/watch?v=IJDJ0kBx2LM) and [this article](https://www.freecodecamp.org/news/how-recursion-works-explained-with-flowcharts-and-a-video-de61f40cb7f9/).
2. Practice classic problems: compute factorial via [this exercise](https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/basic-algorithm-scripting/factorialize-a-number), implement power with [Pow(x, n)](https://leetcode.com/problems/powx-n/), and revisit Fibonacci when you reach dynamic programming.
3. Convert recursion to iteration when needed by simulating a call stack (see [this article](https://www.geeksforgeeks.org/iterative-approach-to-check-for-children-sum-property-in-a-binary-tree/)).

**Reflection prompts:**

- What signal tells you a recursive solution is spinning out of control and needs memoization or a different pattern?
- How do you communicate the base case and recursive step succinctly to an interviewer?

### ⭕️ Node-Based Data Structures

#### Linked Lists

- Watch Sophie Novati explain *why linked lists matter* [here](https://www.youtube.com/watch?v=9SNZqQrQutA).
- Learn the fundamentals with [this overview](https://www.youtube.com/watch?v=WwfhLC16bis) and compare arrays vs. lists via [this article](https://www.geeksforgeeks.org/programmers-approach-looking-array-vs-linked-list/).
- Drill core operations on freeCodeCamp (create, insert, delete, search) and solve [Delete Node in a Linked List](https://leetcode.com/problems/delete-node-in-a-linked-list/).
- Understand cycle detection using the tortoise & hare approach with [this video](https://www.youtube.com/watch?v=-YiQZi3mLq0) and practice [Linked List Cycle](https://leetcode.com/problems/linked-list-cycle/).
- Master list intersections with [this explanation](https://www.youtube.com/watch?v=_7byKXAhxyM) and [Intersection of Two Linked Lists](https://leetcode.com/problems/intersection-of-two-linked-lists/).

#### Binary Trees & BSTs

- Preview the structure with [this overview](https://www.youtube.com/watch?v=oSWTXtMglKE) and contrast BFS vs. DFS using [this article](https://www.geeksforgeeks.org/bfs-vs-dfs-binary-tree/) plus [this explanation](https://www.youtube.com/watch?v=9RHO6jU--GU).
- Practice traversal, height, and inversion problems on freeCodeCamp.
- Learn BST operations via [this video](https://www.youtube.com/watch?v=cySVml6e_Fc), then add/search/delete nodes on freeCodeCamp and review [search walkthrough](https://www.youtube.com/watch?v=zm83jPHZ-jA).
- Deepen with balancing concepts ([video](https://www.youtube.com/watch?v=LU4fGD-fgJQ)) and why balance matters ([video](https://www.youtube.com/watch?v=1O5oaomE__M)).
- Solve classics: [Invert Binary Tree](https://leetcode.com/problems/invert-binary-tree/), [Validate BST](https://www.youtube.com/watch?v=MILxfAbIhrE) followed by [LeetCode #98](https://leetcode.com/problems/validate-binary-search-tree/), and [Lowest Common Ancestor](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/).
- Cover serialization with [this guide](https://www.geeksforgeeks.org/serialize-deserialize-binary-tree/) and [Serialize and Deserialize Binary Tree](https://leetcode.com/problems/serialize-and-deserialize-binary-tree/).

**Reflection prompts:**

- How quickly can you redraw the pointer diagram for the last linked-list bug you hit?
- Which tree traversal feels most natural to you, and how would you defend that choice when designing an API?

### #️⃣ Hashing

Hash tables turn many problems into O(1) operations when designed well.

1. Refresh hash table fundamentals with [this video](https://www.youtube.com/watch?v=KyUTuwz_b7Q).
2. Study what makes a good hash function via [this explanation](https://www.youtube.com/watch?v=4ZJQ6ehmAsg), then understand collision strategies ([separate chaining](https://www.youtube.com/watch?v=zeMa9sg-VJM), [quadratic probing](https://www.youtube.com/watch?v=dxrLtf-Fybk)).
3. Learn how resizing works ([video](https://www.youtube.com/watch?v=AA0KuKV3ARU)) and why averages stay O(1) through amortized analysis ([video](https://www.youtube.com/watch?v=MTl8djZFWE0)).

**Reflection prompts:**

- How do collisions show up in real systems you’ve worked on, and what trade-offs did you negotiate to mitigate them?
- Can you explain amortized analysis in under a minute to a non-expert teammate?

### 🔤 String Algorithms

Strings combine array techniques with hashing.

- Recognize patterns: two pointers (palindromes, in-place edits), sliding windows (longest substring, anagrams), and frequency counting (hash maps or arrays).
- Practice: [Valid Palindrome](https://leetcode.com/problems/valid-palindrome/), [Find All Anagrams in a String](https://leetcode.com/problems/find-all-anagrams-in-a-string/), [Longest Palindromic Substring](https://leetcode.com/problems/longest-palindromic-substring/), and [String Compression](https://leetcode.com/problems/string-compression/).
- Explore advanced pattern matching with the KMP overview [here](https://www.youtube.com/watch?v=qQ8vS2btsxI).

**Reflection prompts:**

- When you debug string problems, which representation (raw strings, arrays, frequency maps) helps you reason fastest?
- How would you explain the trade-off between a hash-based and a two-pointer string solution to a teammate?

### 🌳 Tries (Prefix Trees)

Use tries when you need fast prefix lookups.

1. Understand the structure via [this video](https://www.youtube.com/watch?v=AXjmTQ8LEoI) and [article](https://www.geeksforgeeks.org/trie-insert-and-search/).
2. Implement the core operations in [Implement Trie (Prefix Tree)](https://leetcode.com/problems/implement-trie-prefix-tree/).
3. Stretch with autocomplete ([problem](https://leetcode.com/problems/design-search-autocomplete-system/)) or combine with backtracking in [Word Search II](https://leetcode.com/problems/word-search-ii/).

**Reflection prompts:**

- Where have you seen prefix lookup in products you use daily, and how would a trie improve latency there?
- How do you keep trie solutions readable when the alphabet or branching factor explodes?

### 🔀 Backtracking

Backtracking explores a search space with pruning—think of it as structured brute force.

1. Build intuition with [this overview](https://www.youtube.com/watch?v=Zq4upTEaQyM) and [article](https://www.geeksforgeeks.org/backtracking-algorithms/).
2. Practice staples: [Permutations](https://leetcode.com/problems/permutations/), [Combinations](https://leetcode.com/problems/combinations/), [Subsets](https://leetcode.com/problems/subsets/) plus the duplicate variant, [N-Queens](https://leetcode.com/problems/n-queens/), [Sudoku Solver](https://leetcode.com/problems/sudoku-solver/), and [Word Search](https://leetcode.com/problems/word-search/).
3. Use the general template when you implement solutions:

`function backtrack(path, choices) {   if (goalReached(path)) {     results.push(path);     return;   }    for (const choice of choices) {     if (!isValid(choice, path)) continue;     apply(choice, path);     backtrack(path, updatedChoices);     undo(choice, path);   } }`

**Reflection prompts:**

- What pruning condition saved you the most time on your last backtracking problem, and how could you spot it sooner next time?
- How do you communicate the branching factor and depth so an interviewer trusts your complexity analysis?

### 🍱 Dynamic Programming

1. Start with [Fibonacci via DP](https://youtu.be/vYquumk4nWw) and [LeetCode #509](https://leetcode.com/problems/fibonacci-number/).
2. Learn 0-1 Knapsack from [this video](https://youtu.be/8LusJS5-AGo) and [visual walkthrough](https://algorithm-visualizer.org/dynamic-programming/knapsack-problem).
3. Practice coin change ([video](https://www.youtube.com/watch?v=L27_JpN6Z1Q), [LeetCode #322](https://leetcode.com/problems/coin-change/)) and subset sum variations ([video](https://www.youtube.com/watch?v=s6FhG--P7z0), [Partition Equal Subset Sum](https://leetcode.com/problems/partition-equal-subset-sum/)).
4. Recognize patterns: 1D DP (House Robber, Climbing Stairs), 2D DP (Edit Distance, Longest Common Subsequence), and the distinction between top-down vs. bottom-up approaches.

**Reflection prompts:**

- How do you know when a recurrence is fully specified versus hiding an implicit dependency?
- Which DP transition have you struggled to derive, and what diagram or table helped it click?

### 💰 Greedy Algorithms

Greedy solutions make locally optimal choices that hold up globally—when they work, they're simpler than DP.

1. Learn when greedy applies via [this intro](https://www.youtube.com/watch?v=ARvQcqJ_-NY) and [article](https://www.geeksforgeeks.org/greedy-algorithms/).
2. Practice classics: Activity Selection ([video](https://www.youtube.com/watch?v=poWB2UCuozA), [Meeting Rooms](https://leetcode.com/problems/meeting-rooms/) & [Meeting Rooms II](https://leetcode.com/problems/meeting-rooms-ii/)), [Jump Game I](https://leetcode.com/problems/jump-game/) & [II](https://leetcode.com/problems/jump-game-ii/), [Gas Station](https://leetcode.com/problems/gas-station/), and the [Fractional Knapsack](https://www.geeksforgeeks.org/fractional-knapsack-problem/) variant.
3. Contrast greedy vs. DP trade-offs for each solution you ship.

**Reflection prompts:**

- What invariant convinces you a greedy choice is safe, and how do you articulate it without hand-waving?
- When a greedy attempt fails, how do you analyze the counterexample to upgrade your approach?

### 📚 Heaps

Heaps optimize scenarios where you repeatedly access extremes (min or max) or need partial sorting.

1. Understand the data structure with [this video](https://youtu.be/t0Cq6tVNRBA).
2. Learn heap sort mechanics via [this overview](https://youtu.be/2DmK_H7IdTo) and the deeper [walkthrough](https://www.youtube.com/watch?v=Q_eia3jC9Ts), then implement on [LeetCode #912](https://leetcode.com/problems/sort-an-array/).
3. Apply heaps to streaming medians, priority queues, and k-largest problems (explore LeetCode's heap tag once basics feel comfortable).

**Reflection prompts:**

- Which priority queue use case shows up in your day job, and how would a heap improve it?
- When does the cost of heapifying outweigh its benefits compared to a simpler data structure?

### ፨ Graphs

Only push into graphs after earlier sections feel automatic; most interviews never reach this depth. If you do need them, approach in this order:

1. **Foundations:** Skim [Stanford's overview](https://web.stanford.edu/class/cs97si/06-basic-graph-algorithms.pdf) to learn vocabulary (directed vs. undirected, weighted, adjacency representations).
2. **Traversal:** Watch [this introduction](https://www.youtube.com/watch?v=gXgEDyodOJU), then study BFS & DFS with [this traversal video](https://www.youtube.com/watch?v=pcKY4hjDrxk). Practice converting problems into graphs before coding.
3. **Topological Sort:** Understand the algorithm via [this video](https://www.youtube.com/watch?v=ddTC4Zovtbc) and compare against [this article](https://www.interviewcake.com/concept/java/topological-sort#:~:text=The%20topological%20sort%20algorithm%20takes,is%20called%20a%20topological%20ordering.).
4. **Minimum Spanning Trees:** Learn Disjoint Set basics ([video](https://www.youtube.com/watch?v=ID00PMy0-vE)), then Kruskal's ([video](https://www.youtube.com/watch?v=fAuF0EuZVCk)) and Prim's ([overview](https://www.youtube.com/watch?v=cplfcGZmX7I), [deep dive](https://www.youtube.com/watch?v=oP2-8ysT3QQ)).
5. **Shortest Paths:** Understand Dijkstra's algorithm ([video](https://www.youtube.com/watch?v=lAXZGERcDf4)), why it needs a heap, and how Bellman-Ford differs ([video](https://www.youtube.com/watch?v=-mOEd_3gTK0)).
6. **Practice:** Tackle [Alien Dictionary](https://leetcode.com/problems/alien-dictionary/) and [Cheapest Flights Within K Stops](https://leetcode.com/problems/cheapest-flights-within-k-stops/) to apply topological sort and shortest paths.

**Reflection prompts:**

- How do you map a non-obvious real-world problem into nodes and edges before you touch code?
- Which signal tells you to invest in a graph representation instead of forcing an array or tree abstraction?

### 🔢 Bit Manipulation

Bit tricks unlock elegant solutions for parity checks, subsets, and low-level optimizations.

1. Learn bit operations with [this primer](https://www.youtube.com/watch?v=NLKQEOgBAnw) and [tactics article](https://www.geeksforgeeks.org/bits-manipulation-important-tactics/).
2. Master XOR identities (useful for single-number problems) and power-of-two checks (`n & (n - 1) === 0`).
3. Practice: [Single Number](https://leetcode.com/problems/single-number/), [Missing Number](https://leetcode.com/problems/missing-number/), [Number of 1 Bits](https://leetcode.com/problems/number-of-1-bits/), [Reverse Bits](https://leetcode.com/problems/reverse-bits/), and [Sum of Two Integers](https://leetcode.com/problems/sum-of-two-integers/).

**Reflection prompts:**

- Which invariants become clearer when you look at the binary representation instead of decimal?
- When you reach for bit tricks, how do you ensure readability and explainability for your reviewer?

### 💡 Interview Habits

- **Clarify first:** Nail down constraints, edge cases, and definitions before you touch the keyboard.
- **Narrate continuously:** Share trade-offs, alternatives, and why you pick a pattern. Silence is rarely helpful.
- **Start simple:** Outline or code the brute-force approach, analyze it, then iterate toward optimal.
- **Code cleanly:** Favor descriptive names, helper functions, and guard clauses. Mention potential tests as you finish each block.
- **Self-test:** Run through representative inputs (normal case, edge case, failure case) and verbalize the state at each step.
- **Reflect:** After every mock or real interview, log what went well, what failed, and how you'll adjust.

**Reflection prompts:**

- Which communication habit gives interviewers the most confidence in you, and how can you double down on it?
- After a tough session, what single behavior would have changed the outcome, and how will you practice it this week?

#### Avoid These Pitfalls

1. Jumping straight into coding without alignment.
2. Writing silently or ignoring interviewer hints.
3. Forgetting edge cases or error handling.
4. Overshooting time on a brute-force approach without pivoting.
5. Getting defensive when challenged.
6. Giving up when stuck—explain what you're trying instead.

#### Complexity Conversations

Always close solutions with big-O time and space, plus context on best/average/worst cases where it matters. Offer follow-up ideas such as parallelization, space-time trade-offs, or alternate data structures.

### 🗓 Study Plans

**Three-month ramp (1–2 hrs/day):**

- Weeks 1–2: Arrays, strings, hash tables, two pointers.
- Weeks 3–4: Linked lists, stacks, queues, recursion.
- Weeks 5–6: Binary trees/BST, BFS/DFS.
- Weeks 7–8: Dynamic programming fundamentals.
- Weeks 9–10: Backtracking, greedy, tries.
- Weeks 11–12: Heaps, graphs, targeted review + mocks.

**One-month sprint:** Focus on arrays, strings, trees, hash tables, and core DP. Solve 2–3 problems daily and schedule a weekly mock interview.

**Two-week refresher:** Review arrays, strings, trees, and hash tables. Drill the top 50 interview questions and run a mock every 2–3 days.

Consistency beats cramming—track patterns you miss, revisit them, and celebrate small wins to keep momentum.

**Reflection prompts:**

- Which study cadence actually fits your calendar, and what commitments do you need to renegotiate to protect it?
- How will you measure whether a week of practice moved you closer to readiness (beyond raw problem count)?

### FAQ

#### Do I need every topic?

Probably not. Most companies emphasize arrays, strings, hash tables, and trees. Dynamic programming appears occasionally; advanced graphs are niche. Calibrate with job level and company expectations.

#### What does Formation expect for admission?

Basic fluency with arrays, linked lists, and binary trees is enough—we teach the rest inside the program. The earlier you can articulate your reasoning, the faster you'll progress once enrolled.

#### How long will prep take?

- Strong CS background with recent practice: ~1–2 months.
- CS background but rusty: ~2–3 months.
- Self-taught with limited DSA exposure: ~3–6 months.

Daily consistency matters more than marathon sessions.

#### Should I memorize solutions?

No. Focus on recognizing patterns and explaining why an approach works. Build a personal library of patterns so you can adapt to new twists in real time.

#### Which language should I interview in?

Choose the language you write best under pressure. Python, JavaScript/TypeScript, Java, and C++ are widely accepted. Fluency beats theoretical efficiency.

#### How many problems should I solve?

Aim for depth over raw count. Fully work through 150–300 problems, revisit tough ones, and compare alternative solutions once you submit an answer.

#### What if I get stuck mid-interview?

Stay calm. Restate the problem, work a small example, consider simpler variants, and invite hints. Narrating what you tried and why it failed helps interviewers guide you.

#### Do I need an optimal answer every time?

Delivering a correct solution with clear reasoning is better than hand-waving an optimal but incomplete idea. Aim to reach optimal approaches, but never sacrifice correctness or communication.Copyright © 2026 Formation Labs Inc. All rights reserved.