---
title: "Bloom Filters: Theory, Engineering Trade‑offs, and Implementation in Go"
source: "https://www.infoq.com/articles/bloom-filters-practice-go-recommender/?utm_source=email&utm_medium=development&utm_campaign=newsletter&utm_content=04142026"
author:
  - "[[Gabor Koos]]"
published: 2026-04-07
created: 2026-04-14
description: "This article discuss the Go implementation of Bloom filters to optimize a recommender. It covers the architecture, filter mechanics, Go integration, parameter tuning,  and practical lessons learned."
tags:
  - "clippings"
---

> [!summary]
> Walks through adding a Bloom filter in front of an exact history lookup in a recommendation pipeline where ~97-98% of membership checks were negatives, covering the math for sizing `m` and `k`, a packed-bit Go implementation, and lifecycle concerns. In production: p95 feed latency dropped from ~140ms to ~96ms, exact lookups fell ~80%, and backend read traffic dropped ~65-70% while over-filtering stayed under ~0.5%.

[InfoQ Homepage](https://www.infoq.com/ "InfoQ Homepage") Bloom Filters: Theory, Engineering Trade‑offs, and Implementation in Go

[Development](https://www.infoq.com/development/ "Development")

[Online InfoQ Architect Certification (April 15): Peer conversations that change how you think.](https://certification.qconferences.com/?utm_source=infoq&utm_medium=referral&utm_campaign=infoqyellowbox_onlinecohortaprmayjun26)

Listen to this article - 31:42

### Key Takeaways

- Bloom filters provide efficient probabilistic membership testing with no false negatives and controlled false-positive rates.
- Bloom filters may reduce unnecessarily expensive lookups in storage systems by acting as fast pre-filters.
- Practical parameter selection (filter size and hash count) is essential for balancing memory and accuracy.
- Go’s low-level control makes implementation and reasoning about Bloom filters straightforward.
- Engineers should understand when Bloom filters are the right fit and when non-probabilistic data structures are a better choice.

## Introduction

In one of our recommendation pipelines, we had a simple requirement: don’t show users articles they had already viewed. At its peak, the feed service handled around 18,000 requests per second, with about 120 candidates evaluated per request. This meant roughly 2.16 million membership checks per second. However, the workload was heavily skewed, with around 97-98% of checks negatives.

Our initial design used exact lookups (cache plus backing store) for every candidate. This worked functionally, but when there were many lookups for items that didn’t exist, it became less efficient. Each miss still caused network and storage costs, which increased I/O. During peak traffic, this showed up as an increases p95 latency (from about 85ms to 140ms), backend read spikes, and steadily rising infrastructure cost.

To address this, we introduced a *Bloom filter* in front of the exact lookup path. The filter rejects definite negatives in memory and submits only likely positives for expensive verification. This change let us avoid unnecessary work for items that were definitely not present, reducing both latency and backend load. By filtering out obvious misses early, we could focus resources on the cases that actually needed verification.

This article walks you through that implementation end to end: the architectural problem, Bloom filter mechanics, Go integration, parameter tuning with math ($m$ and $k$), and the practical lessons learned from making it work under production constraints.

## Naive Solution: Exact Lookup for Every Candidate

As mentioned, before introducing Bloom filters, our recommendation service used a baseline "exact-first" architecture:

- In the candidate generation step, a ranked list of candidate article IDs is produced.
- In the history-check stage, each candidate is validated against the user’s seen set.
- The history-check stage used a cache-first logic, relying on backing storage for misses.
- Only candidates confirmed as unseen in the history-check proceeded to final ranking and response assembly.

From a correctness viewpoint, this was ideal: duplicate suppression was deterministic and easy to reason about. In a system perspective, however, this stage sat directly on the serving critical path and performed one remote membership check per candidate.

## Why Exact Lookup Alone Was Not Good Enough

The workload characteristics made the exact approach expensive by design. Around 97-98% of checks were negatives, so most lookups existed only to return "unseen" and move on. In other words, we were paying storage/network costs primarily for negative answers.

Three issues were dominant under peak traffic:

- Latency amplification: each request contained many candidate checks; p95 response latency grew from roughly 85ms to 140ms.
- Read amplification: backend and cache read volume scaled with the number of candidates checked per request ("candidate fanout"), not just request count.
- Cost pressure: infrastructure spend rose with traffic because exact checks dominated the serving path.

At that point, we needed a design that preserved correctness guarantees where it mattered but removed most of the unnecessarily expensive lookups from the negative-heavy path.

## The Solution: Bloom Filters

The change was to introduce a Bloom filter as a quick, in-memory check ("membership gate") before performing the more expensive history lookup. At a high level, a [Bloom filter](https://en.wikipedia.org/wiki/Bloom_filter) is a compact probabilistic data structure used for membership checks. It stores information in a bit array and uses multiple hash functions per key. A query has two possible outcomes:

- Definitely not present (guaranteed correct)
- Possibly present (may include false positives)

It never produces false negatives, which makes it well-suited for quickly rejecting items that are certainly unseen.

With the introduction of Bloom filters, the request path changes slightly:

1. Generate candidate article IDs.
2. Query the Bloom filter with (`user_id`, `article_id`) membership keys.
3. If the filter returns *definitely not present*, treat the candidate as unseen and keep it in the ranking pipeline.
4. If the filter returns *possibly present*, go on with exact history verification.

This design targets exactly the pain point from the previous section: the dominant negative path. Most candidates are unseen, so most checks can be resolved in-memory without remote I/O.

### Why a Probabilistic Approach Fits This Workload

The approach described here has several interesting properties:

- Negative-heavy query distribution: with ~97-98% negatives, fast negative rejection has a high impact.
- Strict correctness where needed: positives can still be verified against exact storage.
- Predictable memory footprint: Bloom filters compactly represent large membership sets.
- Tunable trade-off: as we will see later, we can control false-positive rate via m (bit array size) and k (hash count).

The next sections explain how Bloom filters work, how we implemented them in Go, and how we used the math to tune parameters for this recommendation workload.

## Bloom Filters in Practice

In our recommendation workload, the goal of a Bloom filter is to quickly identify likely unseen candidates and avoid unnecessary expensive history lookups. Because most candidate checks are negative, the filter helps remove a large amount of avoidable storage and network work from the serving path.

### Core Mechanics

A Bloom filter encodes membership information for a set of elements. Its core components are simple but powerful:

- A bit array of size *m*: each position stores a 0 or 1, representing whether it has been set by one or more elements.
- *k* hash functions: each element is mapped to *k* positions in the bit array. These hash functions should be independent and uniformly distribute elements across the array. Finding good hash functions is crucial for minimizing collisions and controlling the false-positive rate, making it an important engineering consideration. We’ll discuss practical hash function choices in the implementation section.

Bloom filters do not store the elements themselves, only the presence information is encoded in the bits.

### Insertion

To add an element E to the Bloom filter:

1. Apply the $k$ hash functions to E:
	$h_1(E), h_2(E), \dots, h_k(E)$ each produces a numeric hash.
2. Map the hashes into the bit array using modulo $m$:
	$index_i = h_i(E) \mod m$
	This gives $k$ positions in the array (it’s possible for some positions to be the same due to collisions).
3. Set the bits at these positions to 1:
	$\text{bit_array}[\text{index_i}] = 1$

Multiple elements may set the same bit. Bits are only ever set, never cleared. This is why standard Bloom filters cannot support deletions.

### Membership Queries

To check if an element is present:

1. Compute the same k hash values for the element.
2. Check the corresponding bits in the array.

If any bit is 0, the element is definitely not in the set, because it would have been set to 1 during insertion.

If all bits are 1, the element is possibly in the set. This is where false positives can occur: different elements may hash to the same positions, causing bits to be set even if the queried element was never added.

![](https://www.infoq.com/articles/bloom-filters-practice-go-recommender/articles/bloom-filters-practice-go-recommender/en/resources/198figure-1-1774950090560.jpg)

**Figure 1 - Bloom filter insertions and membership test**

In the diagram above, we insert three elements (*element1, element2, element3*) into the Bloom filter with 2 hash functions (*h1* and *h2*). Each element sets two bits in the array. When we query for element4, we find that not all bits are set, so we can confidently say it is not present. (Note that in the diagram we have *hash collisions*: for example, *element1* and *element3* both set the bit at *index 6*, which contributes to the possibility of false positives.)

### Key Properties

Bloom filters display several interesting properties:

- No false negatives: a "not present" result is always correct.
- False positives possible: an element may appear to exist even if it hasn’t been added.
- Deterministic: the same element always maps to the same bits.
- Efficient in memory and speed: the bit array and simple hash computations allow fast insertions and queries.
- Only stores membership information: it cannot retrieve the original elements.
- No deletions: once bits are set, they cannot be cleared without affecting other elements. This is a fundamental limitation of standard Bloom filters, and while there are variants that support deletions (like counting Bloom filters), they come with additional complexity and memory overhead.

While the mechanics described above explain *how* a Bloom filter operates, this understanding alone is no guarantee for a practical, ready-to-use filter. Without careful choices of the bit array size ($m$), the number of hash functions ($k$), and appropriate hash functions, a Bloom filter could be inefficient or produce too many false positives. In the next section, we will demonstrate how to implement a Bloom filter in Go, translating the mechanics into working code. The discussion of how to choose and tune these parameters will follow in the *Practical Considerations* section.

## Implementing a Bloom Filter in Go

Go is an ideal language for implementing a Bloom filter because it provides low-level control over memory, efficient slices and arrays, and fast, predictable execution. These characteristics make it easy to reason about the bit array, hash computations, and overall performance of the filter. These are all critical for production systems that need both speed and memory efficiency.

Translating the mechanics of a Bloom filter into Go is straightforward. The implementation uses a bit array and multiple hash functions, mirroring the step-by-step behavior we described in the *Core Mechanics* section. At this stage, we focus on the structure and basic operations; parameter tuning will be addressed in the *Practical Considerations* section.

### Defining the Bloom Filter Structure

The Bloom filter structure (`struct`) in Go consists of a packed bit array, the number of addressable bits, and the configured hash functions. Storing hash functions in the `struct` avoids per-call API mistakes and keeps usage ergonomic. Using a packed representation (64 bits per word) improves memory efficiency and cache behavior compared to storing one boolean per bit:

```
type BloomFilter struct {
  bits   []uint64             // packed bit array (64 bits per word)
  m      uint                 // number of addressable bits
  hashes []func([]byte) uint  // configured hash functions
}
```

### Creating a New Bloom Filter

The `NewBloomFilter` function initializes a new Bloom filter with the specified size and hash functions:

```
// NewBloomFilter creates a new Bloom filter with m bits and configured hash functions.
func NewBloomFilter(m uint, hashes []func([]byte) uint) *BloomFilter {
  if m == 0 {
    panic("bloom filter size m must be > 0")
  }
  if len(hashes) == 0 {
    panic("at least one hash function is required")
  }

  words := (m + 63) / 64 // ceil(m/64)
  return &BloomFilter{
    bits:   make([]uint64, words),
    m:      m,
    hashes: hashes,
  }
}
```

To operate on the packed bit array, we use helper methods for setting and reading individual bits:

```
func (bf *BloomFilter) setBit(i uint) {
  word := i >> 6   // i / 64
  offset := i & 63 // i % 64
  bf.bits[word] |= uint64(1) << offset
}
func (bf *BloomFilter) hasBit(i uint) bool {
  word := i >> 6
  offset := i & 63
  return (bf.bits[word] & (uint64(1) << offset)) != 0
}
```

### Adding an Element

The `Add` method takes a byte slice (the data to be added), computes configured hash values, maps them to indices in the bit array, and sets the corresponding packed bits:

```
func (bf *BloomFilter) Add(data []byte) {
  for _, hash := range bf.hashes {
    idx := hash(data) % bf.m
    bf.setBit(idx)
  }
}
```

Bits are only ever set; insertion mirrors the Bloom filter core mechanics exactly.

### Querying an Element

The `Contains` method checks if an element is possibly in the Bloom filter by verifying the bits corresponding to the hash values:

```
func (bf *BloomFilter) Contains(data []byte) bool {
  for _, hash := range bf.hashes {
    idx := hash(data) % bf.m
    if !bf.hasBit(idx) {
      return false // definitely not present
    }
  }
  return true // possibly present
}
```

This method returns false if any bit is not set, ensuring there are no false negatives. If all bits are set, it returns true, indicating a possible membership (with the possibility of false positives).

This implementation directly mirrors the core mechanics: multiple independent hashes, bit array updates, and membership checks. Let’s see a running example of how to use this Bloom filter in practice, including how to define hash functions and test the filter with some data:

```
package main
import (
  "Fmt"
  "hash/fnv"
)

// Simple hash functions
func hash1(data []byte) uint {
  h := fnv.New32a()
  h.Write(data)
  return uint(h.Sum32())
}

func hash2(data []byte) uint {
  h := fnv.New32()
  h.Write(data)
  return uint(h.Sum32())
}

func main() {
  // Define hash functions
  hashes := []func([]byte) uint{hash1, hash2}

  // Create a Bloom filter: size 20 bits
  bf := NewBloomFilter(20, hashes)

  // Add elements
  bf.Add([]byte("apple"))
  bf.Add([]byte("banana"))
  bf.Add([]byte("cherry"))

  // Query elements
  tests := []string{"apple", "banana", "cherry", "date", "fig"}

  for _, t := range tests {
    if bf.Contains([]byte(t)) {
      fmt.Printf("%s: possibly present\n", t)
    } else {
      fmt.Printf("%s: definitely not present\n", t)
    }
  }
}
```

In this example, we define two simple hash functions using the `FNV` hash algorithm. This is sufficient for demonstration, but production systems typically prefer higher-quality non-cryptographic hashes (for example [Murmur3](https://en.wikipedia.org/wiki/MurmurHash), [xxHash](https://xxhash.com/), [MetroHash](https://www.jandrewrogers.com/2015/05/27/metrohash/), or [HighwayHash](https://github.com/google/highwayhash)) and validate distribution behavior under real keysets. After defining the two hash functions, we create a Bloom filter with a size of 20 bits and 2 hash functions. We add three fruits to the filter and then test for their presence, along with two additional fruits that were not added. The output will indicate which fruits are possibly present (with potential false positives) and which are definitely not present:

```
apple: possibly present
banana: possibly present
cherry: possibly present
date: definitely not present
fig: definitely not present
```

## The Math Behind Bloom Filters

Bloom filters are easy to implement, but not so easy to use effectively: you need to understand their probabilistic behavior to get the most out of them. This allows engineers to predict false-positive rates and make informed choices about memory usage and the number of hash functions required to achieve the desired false-positive rate. The math behind Bloom filters is essential for tuning their parameters ($m$, $k$, and the hash functions) to achieve the desired balance between memory efficiency and accuracy.

Below, we quickly summarize the key formulas you’ll need in practice. For a deeper dive into the derivations and underlying theory, see the *Appendix: The Math Behind Bloom Filters*.
The false positive rate (p) is approximately:

$p = \left( 1 - e^{-\frac{kn}{m}} \right)^k$

The optimal number of hash functions ($k$):

$k = \frac{m}{n} \ln 2$

The required bit array size ($m$) for a target false positive rate:

$m = -\frac{n \ln p}{(\ln 2)^2}$

## Results Snapshot

After introducing Bloom-filter gating in our recommendation path and tuning $\frac{m}{k}$ using the formulae above, we observed three consistent outcomes in peak-window traffic:

- Lower tail latency: p95 feed latency improved from ~140ms to ~96ms (about 31% reduction).
- Fewer expensive checks: exact history lookups dropped from ~120 per request to ~24 on average (about 80% reduction).
- Lower backend pressure: read traffic to the history store dropped by ~65-70%, while measured Bloom false-positive over-filtering stayed under ~0.5%.

These numbers are workload-specific, but the pattern is general: when lookups are mostly negative and expensive, a well-tuned Bloom filter can remove a large portion of avoidable backend work.

## Practical Considerations & Best Practices

With the mechanics implemented and the math to choose $k$ and $m$, we can now translate theory into engineering decisions.

### Start with Product Constraints, Not with Bloom Filter Parameters

For our recommendation path, the product-level question was not "what $m$ and $k$ should we use?", but rather:

- how many duplicate recommendations are acceptable
- how much memory can we spend in the serving tier
- what latency budget remains for per-candidate filtering.

That gave us a concrete tuning target:

- keep false positives low enough to avoid visible over-filtering of unseen items
- while reducing expensive exact-history lookups on the negative-heavy path.

This is a general rule: start from service SLOs and user-impact tolerance, then calculate Bloom filter parameters.

### How We Chose n, m, and k in Our Case

In our implementation, we modeled $n$ as the expected number of viewed items represented in one filter over its lifecycle window (for example, per user over a rolling period).
We used the standard equations:

$m \approx -\frac{n \ln P}{(\ln 2)^2}, \quad k \approx \frac{m}{n} \ln 2$

Then we made three practical adjustments:

1. Headroom on $n$: we sized for growth, not current average, to avoid early saturation.
2. Rounded m for implementation efficiency: we rounded to word boundaries for packed $\texttt{[]uint64}$ storage.
3. Clamped $k$ for CPU cost: we treated the computed value as a starting point, then chose a value that kept per-request hash work within budget (hashing may be expensive).

In practice, this meant accepting slightly higher memory to protect false-positive behavior under growth, and avoiding an overly large k that would hurt hot-path latency.

In this specific recommendation use case, we also made an important serving decision: when the false-positive rate stayed within our product tolerance, we did not always route Bloom positives to exact lookup. A small false-positive rate means occasionally suppressing an unseen item, which was acceptable for feed quality, while skipping exact verification removed additional backend cost and latency. This approach worked for our use case because the occasional omission was acceptable, but in many systems, stricter guarantees are necessary.

This approach worked for our use case because the occasional omission was acceptable, but in many systems, stricter guarantees are necessary. In general, exact verification of Bloom positives is required when false positives are expensive or correctness-critical, but optional when product behavior can tolerate rare over-filtering.

### Hash Function Choice: Correctness First, Then Throughput

In this article, hash values are derived deterministically and mapped with modulo m. The important production lesson was that hash strategy is not a cosmetic detail:

- poor distribution inflates collisions
- collisions inflate false positives
- false positives raise exact-lookup pass-through
- pass-through erodes the benefit of the Bloom filter.

A general practical tradeoff applies across Bloom-filter deployments: fully independent hash families are rarely used in serving systems, because they increase CPU cost. A common approach is double [hashing](https://en.wikipedia.org/wiki/Double_hashing) (derive $k$ indices from two base hashes), which usually preserves good distribution while keeping hash computation cheaper.

What worked for us:

- deterministic, stable hashing across instances
- fast non-cryptographic hashes for serving path performance
- empirical validation of observed false-positive behavior under representative keys.

As a general guidance, treat hash quality as a measurable property in your workload, not as an assumption.

### Measure the Right Operational Signals

A Bloom filter can look correct while still being operationally wrong. We tracked:

- pass-through rate to exact history checks
- effective false-positive proxy (exact misses after Bloom "possibly present")
- latency impact in feed-serving stages
- memory footprint per filter scope
- saturation drift over time.

These metrics are generally useful in any production Bloom-filter deployment: they tell you when the filter is still saving work versus when it is decaying into overhead.

### Lifecycle Strategy Matters as Much as Initial Tuning

Even with good initial parameters, filters degrade if cardinality grows beyond assumptions. In our case, defining lifecycle policy early was critical to know:

- when to rebuild
- when to rotate
- how to recover if pass-through spikes.

Generalizing beyond recommendations: if your data is dynamic and grows continuously, you can’t rely on a one-time filter setup. Instead, you need a clear lifecycle policy: deciding when to rebuild or rotate the filter, and how to handle unexpected growth or spikes. Without this, filter accuracy and efficiency will degrade over time.

### Practical Checklist

Before shipping a Bloom filter in a high-throughput system:

- define acceptable false-positive impact in product terms
- estimate n with growth headroom
- compute m and k, then tune against latency and memory budgets
- validate hash behavior with real key distributions
- instrument pass-through and saturation metrics
- predefine rebuild/rotation policy

Applied this way, Bloom filters remain a high-leverage optimization rather than a fragile micro-optimization.

## Conclusion

Bloom filters solved the problem we actually had: too many expensive "is this seen?" checks on a negative-heavy path. By moving membership filtering into memory, we removed avoidable I/O from the feed-serving critical path and regained latency headroom without exploding memory usage.

The key lesson is not "always use Bloom filters". It is to treat them as a tunable systems component: set $m$ and $k$ from product tolerance and traffic shape, choose hash functions for both distribution and throughput, and monitor saturation before it silently erodes value.

In workloads like recommendation filtering, where rare false positives are acceptable, Bloom filters can be more than a textbook gimmick, they can be a practical, production-grade lever for performance and cost.

## Appendix Dive: The Math Behind Bloom Filters

If you’re interested in the detailed math behind these results, read on for a full derivation and explanation.

### Why False Positives Happen

To understand when false positives are possible, recall that:

- Each element is inserted by setting $k$ bits in a bit array of size $m$.
- Bits are never cleared, and different elements may set overlapping bits.

A false positive occurs when a query element happens to have all its $k$ hash bits already set by other elements, even though it was never inserted.

### Probability a Single Bit Is Still 0

As explained, Bloom filters’s behavior is determined by three parameters:

- $m$ = number of bits in the array
- $k$ = number of hash functions
- $n$ = number of inserted elements

When inserting a single element, each hash sets a bit. The probability that a particular bit remains 0 after one insertion is:

$p_0 = 1 - \frac{1}{m}$

After inserting n elements, with $k$ hashes each, the probability a bit is still 0 is:

$p_0 = \left( 1 - \frac{1}{m} \right)^{kn}$

Approximation: For large $m, \ (1 - 1/m)^{kn} \approx e^{-kn/m}$. This gives a simpler formula for reasoning about false positives.

### Probability of a False Positive

A query element is a false positive if all $k$ of its bits are 1. Using the previous step:

$P_{fp} = (1 - p_0)^k \approx (1 - e^{-kn/m})^k$

- More inserted elements → higher probability that bits are already set → higher false-positive rate.
- Larger bit array $m$ → reduces collisions → lower false-positive rate.
- Number of hash functions $k$ controls the balance: too few → high false positives; too many → higher CPU cost without much gain.

### Choosing m and k

These formulas allow engineers to compute practical parameters:

- For a desired false-positive rate $P$, given expected number of elements $n$:
	$m \approx -\frac{n \ln P}{(\ln 2)^2}, \quad k \approx \frac{m}{n} \ln 2$
- $m$ controls memory usage and saturation of the bit array.
- $k$ controls the number of hash operations per element.
- These formulas provide a starting point, which can later be refined based on the actual hash functions and workload.

As saturation increases (the fraction of bits set approaches 1), the false-positive rate approaches 1 as well, which is why sizing and lifecycle policy are both critical.
Without this analysis, a Bloom filter may either produce too many false positives or waste memory (we may not even know which). Understanding the math is crucial for configuring Bloom filters for real-world applications, ensuring they provide the intended performance benefits while managing trade-offs effectively.

### Related Sponsors

- Sponsored by
	[![Icon image](https://imgopt.infoq.com//fit-in/275x500/filters:quality(100)/filters:no_upscale()/sponsorship/topic/5aab5793-1aa2-43a6-9086-318627c6365a/PayaraLogo-1763716038782.png)](https://www.infoq.com/url/f/a30a7dce-63d3-462b-9160-dbe2672b779e/?ha=bW91c2Vtb3Zl)
