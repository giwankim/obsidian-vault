---
title: "e-means: 10x faster k-means at equal loss"
source: "https://e-means.github.io/?utm_source=substack&utm_medium=email"
author:
published:
created: 2026-11-13
description: "Modern optimization and scaling laws for k-means clustering"
tags:
  - "clippings"
---

> [!summary]
> Meta FAIR open-sources e-means, a replacement for Lloyd's k-means algorithm that uses mini-batch exponential-moving-average centroid updates and reaches lower loss in about a tenth of the epochs. Batch size and step size come from scaling laws, so no hyperparameter tuning is needed, and new initialization, cosine scheduling, and dead-cluster revival help it escape local minima. Benchmarks report 10-45x wall-clock speedups on GPU against Flash-KMeans and 8-15x on CPU, with code shipped in FAISS contrib.

## e-means: outperforming k-means in one-tenth the epochs

I’m excited to open-source e-means: a modern, robust k-means algorithm developed at Meta FAIR. A replacement of Lloyd's algorithm, e-means delivers a ~10× speedup in both epochs and wall-clock time while achieving lower loss.

**[Try e-means in your browser](https://e-means.github.io/playground.html)**

[\[Paper\]](https://arxiv.org/abs/2611.09501) · [\[Code\]](https://github.com/facebookresearch/faiss/tree/main/contrib/e_means) · [\[Cite\]](#citing-this-work) · \[Coauthors\]

Lloyd (full batch)

Training MSE **0.03571** after 1 epoch

e-means (batch and step from the scaling laws)

Training MSE **0.02518**

Training MSE

e-means Lloyd

epochs: 1.9

100,000 datapoints in 200 clusters, two wide Gaussians and three small ones, cut off at a box, on a light uniform background. Lloyd has 1 update against 97 per epoch for e-means.

## An order of magnitude less epochs

Across a [large range of scales and datasets](#validation), e-means reaches a test loss below Lloyd's at 25 epochs, in 1.2 to 3 epochs. Measured end to end, that is a 10–45× wall-clock reduction on GPU against the state-of-the-art Lloyd implementation (Flash-KMeans [^2]), and 8–15× on CPU against Faiss [^1]. Speed and quality usually trade against each other in k-means, while e-means achieves both better speed and loss.

![e-means against Lloyd’s k-means, in epochs, CPU time and GPU time](https://e-means.github.io/assets/emeans_vs_lloyd_readme_v9.png)

e-means against Lloyd’s k-means, in epochs, CPU time and GPU time

## The k-means problem

Given a fixed dataset of n points X = {x <sub>1</sub>,..., x <sub>n</sub> } ⊂ R <sup>d</sup> and an integer k, the k-means problem is to find k centroids C = (c <sub>1</sub>,..., c <sub>k</sub>) minimizing the mean squared distance between each point and its nearest centroid:

$$
\mathrm{MSE}(X, C) = \frac{1}{n} \sum_{i=1}^{n} \|x_i - c_{a(i)}\|^2, \qquad a(i) = \arg\min_{j \in \{1,\dots,k\}} \|x_i - c_j\|^2
$$

$$
\mathrm{MSE}(X, C) = \frac{1}{n} \sum_{i=1}^{n} \|x_i - c_{a(i)}\|^2
$$

$$
a(i) = \arg\min_{j \in \{1,\dots,k\}} \|x_i - c_j\|^2
$$

It's a static dataset, unlike codebook learning inside VQ-VAEs, where the distribution to cluster is constantly moving.

## The e-means project

The goal of e-means is to provide a modern optimization rule for the k-means problem. We started this project from the following observations:

For e-means, we chose to do mini-batch updates with exponential moving averages [^6], which we found to be most efficient for the k-means problem. Contrary to previous mini-batch approaches, e-means requires no hyperparameter tuning because it automatically sets the batch size and step size with scaling laws (see [Automatic hyperparameter tuning with scaling laws](#scaling-laws)). In addition, e-means improves the initialization and the dead-cluster revival strategy, adds a cosine-scheduled decay rate, and introduces a finalization stage that reduces the training loss for a negligible runtime penalty at the end of training. e-means is highly parallelizable, and comes with specialized kernels that translate its algorithmic advantage into wall-clock speedups.

Moving-average updates

Each mini-batch updates every cluster's count and sum. The centroid is their ratio.

<svg viewBox="0 0 420 120" style="overflow: visible;"><circle cx="40" cy="56" r="11" fill="none" stroke="#a7b3bf" stroke-width="2" stroke-dasharray="4 3"></circle><circle cx="40" cy="56" r="2.5" fill="#a7b3bf"></circle><text x="40" y="100" font-size="15" fill="#67788a" text-anchor="middle" font-family="Space Grotesk, sans-serif">old centroid</text> <line x1="54" y1="56" x2="322" y2="56" stroke="#c9c9ce" stroke-width="2" stroke-dasharray="3 4"></line><path d="M54 56 L150 56" fill="none" stroke="#1f77b4" stroke-width="3"></path><path d="M144 50 L151 56 L144 62" fill="none" stroke="#1f77b4" stroke-width="3"></path><circle cx="153" cy="56" r="6" fill="#1f77b4"></circle><text x="153" y="100" font-size="15" fill="#67788a" text-anchor="middle" font-family="Space Grotesk, sans-serif">new centroid</text> <circle cx="340" cy="56" r="40" fill="#e8f1f9" stroke="#1f77b4" stroke-width="2"></circle><g fill="#1f77b4"><circle cx="318" cy="40" r="3"></circle><circle cx="352" cy="34" r="3"></circle><circle cx="364" cy="60" r="3"></circle><circle cx="326" cy="72" r="3"></circle><circle cx="356" cy="76" r="3"></circle><circle cx="312" cy="58" r="3"></circle></g><circle cx="340" cy="56" r="4.5" fill="#1c2b33"></circle><text x="340" y="112" font-size="15" fill="#67788a" text-anchor="middle" font-family="Space Grotesk, sans-serif">batch mean</text></svg>

No hyperparameter tuning

Everything is derived from scaling laws.

<svg viewBox="0 0 420 120" style="overflow: visible;"><line x1="10" y1="10" x2="10" y2="110" stroke="#c9c9ce" stroke-width="1.5"></line><line x1="10" y1="110" x2="410" y2="110" stroke="#c9c9ce" stroke-width="1.5"></line><path d="M24.0 90.8 L396.0 29.2" fill="none" stroke="#1f77b4" stroke-width="3.4"></path><circle cx="24.0" cy="87.6" r="5" fill="#ffffff" stroke="#6b6b70" stroke-width="2"></circle><circle cx="70.5" cy="79.0" r="5" fill="#ffffff" stroke="#6b6b70" stroke-width="2"></circle><circle cx="117.0" cy="76.0" r="5" fill="#ffffff" stroke="#6b6b70" stroke-width="2"></circle><circle cx="163.5" cy="62.2" r="5" fill="#ffffff" stroke="#6b6b70" stroke-width="2"></circle><circle cx="210.0" cy="62.1" r="5" fill="#ffffff" stroke="#6b6b70" stroke-width="2"></circle><circle cx="256.5" cy="51.8" r="5" fill="#ffffff" stroke="#6b6b70" stroke-width="2"></circle><circle cx="303.0" cy="44.1" r="5" fill="#ffffff" stroke="#6b6b70" stroke-width="2"></circle><circle cx="349.5" cy="40.2" r="5" fill="#ffffff" stroke="#6b6b70" stroke-width="2"></circle><circle cx="396.0" cy="27.9" r="5" fill="#ffffff" stroke="#6b6b70" stroke-width="2"></circle><text x="230" y="104" style="font:400 20px 'Space Grotesk';fill:#6b6b70">log n, log k, log T</text></svg>

Start and finish

Novel initialization and finalization methods. The run ends on each cluster's exact last-epoch mean.

<svg viewBox="0 0 420 120" style="overflow: visible;"><line x1="10" y1="10" x2="10" y2="110" stroke="#c9c9ce" stroke-width="1.5"></line><line x1="10" y1="110" x2="410" y2="110" stroke="#c9c9ce" stroke-width="1.5"></line><path d="M28.0 23.0 L31.2 52.8 L34.3 54.3 L37.5 55.8 L40.7 57.1 L43.8 58.4 L47.0 59.5 L50.2 60.6 L53.3 61.7 L56.5 62.7 L59.6 63.6 L62.8 64.4 L66.0 65.2 L69.1 66.0 L72.3 66.7 L75.5 67.4 L78.6 68.0 L81.8 68.6 L85.0 69.2 L88.1 69.7 L91.3 70.2 L94.5 70.6 L97.6 71.0 L100.8 71.4 L103.9 71.8 L107.1 72.2 L110.3 72.5 L113.4 72.8 L116.6 73.1 L119.8 73.4 L122.9 73.6 L126.1 73.9 L129.3 74.1 L132.4 74.3 L135.6 74.5 L138.8 74.7 L141.9 74.9 L145.1 75.1 L148.3 75.2 L151.4 75.4 L154.6 75.5 L157.7 75.6 L160.9 75.8 L164.1 75.9 L167.2 76.0 L170.4 76.1 L173.6 76.2 L176.7 76.3 L179.9 76.3 L183.1 76.4 L186.2 76.5 L189.4 76.6 L192.6 76.6 L195.7 76.7 L198.9 76.7 L202.1 76.8 L205.2 76.8 L208.4 76.9 L211.5 76.9 L214.7 77.0 L217.9 77.0 L221.0 77.0 L224.2 77.1 L227.4 77.1 L230.5 77.1 L233.7 77.2 L236.9 77.2 L240.0 77.2 L243.2 77.2 L246.4 77.3 L249.5 77.3 L252.7 77.3 L255.8 77.3 L259.0 77.3 L262.2 77.4 L265.3 77.4 L268.5 77.4 L271.7 77.4 L274.8 77.4 L278.0 77.4" fill="none" stroke="#1f77b4" stroke-width="3.4"></path><circle cx="28.0" cy="23.0" r="6" fill="#ffffff" stroke="#6b6b70" stroke-width="2"></circle><line x1="278.0" y1="77.4" x2="278.0" y2="88.2" stroke="#1f77b4" stroke-width="2.4" stroke-dasharray="4 3"></line><circle cx="278.0" cy="88.2" r="6" fill="#1f77b4"></circle><text x="42" y="30" style="font:400 20px 'Space Grotesk';fill:#6b6b70">start</text> <text x="290" y="95" style="font:400 20px 'Space Grotesk';fill:#6b6b70">exact mean</text></svg>

Cosine scheduling

The step α anneals from α <sub>0</sub> to 0.1α <sub>0</sub>, as a learning rate does.

<svg viewBox="0 0 420 120" style="overflow: visible;"><line x1="10" y1="10" x2="10" y2="110" stroke="#c9c9ce" stroke-width="1.5"></line><line x1="10" y1="110" x2="410" y2="110" stroke="#c9c9ce" stroke-width="1.5"></line><path d="M16.0 20.4 L18.8 20.4 L21.5 20.5 L24.3 20.5 L27.1 20.6 L29.9 20.7 L32.6 20.9 L35.4 21.0 L38.2 21.2 L41.0 21.5 L43.7 21.7 L46.5 22.0 L49.3 22.3 L52.1 22.6 L54.8 22.9 L57.6 23.3 L60.4 23.7 L63.1 24.1 L65.9 24.6 L68.7 25.0 L71.5 25.5 L74.2 26.0 L77.0 26.6 L79.8 27.1 L82.6 27.7 L85.3 28.3 L88.1 28.9 L90.9 29.6 L93.6 30.2 L96.4 30.9 L99.2 31.6 L102.0 32.3 L104.7 33.0 L107.5 33.8 L110.3 34.6 L113.1 35.3 L115.8 36.1 L118.6 37.0 L121.4 37.8 L124.2 38.6 L126.9 39.5 L129.7 40.4 L132.5 41.3 L135.2 42.1 L138.0 43.1 L140.8 44.0 L143.6 44.9 L146.3 45.8 L149.1 46.8 L151.9 47.7 L154.7 48.7 L157.4 49.6 L160.2 50.6 L163.0 51.6 L165.7 52.6 L168.5 53.6 L171.3 54.5 L174.1 55.5 L176.8 56.5 L179.6 57.5 L182.4 58.5 L185.2 59.5 L187.9 60.5 L190.7 61.5 L193.5 62.5 L196.3 63.5 L199.0 64.4 L201.8 65.4 L204.6 66.4 L207.3 67.4 L210.1 68.3 L212.9 69.3 L215.7 70.2 L218.4 71.1 L221.2 72.1 L224.0 73.0 L226.8 73.9 L229.5 74.8 L232.3 75.7 L235.1 76.5 L237.8 77.4 L240.6 78.2 L243.4 79.1 L246.2 79.9 L248.9 80.7 L251.7 81.5 L254.5 82.2 L257.3 83.0 L260.0 83.7 L262.8 84.4 L265.6 85.1 L268.4 85.8 L271.1 86.5 L273.9 87.1 L276.7 87.7 L279.4 88.3 L282.2 88.9 L285.0 89.5 L287.8 90.0 L290.5 90.5 L293.3 91.0 L296.1 91.5 L298.9 91.9 L301.6 92.3 L304.4 92.7 L307.2 93.1 L309.9 93.4 L312.7 93.8 L315.5 94.1 L318.3 94.3 L321.0 94.6 L323.8 94.8 L326.6 95.0 L329.4 95.2 L332.1 95.3 L334.9 95.4 L337.7 95.5 L340.5 95.6 L343.2 95.6 L346.0 95.6" fill="none" stroke="#1f77b4" stroke-width="3.4"></path><text x="24" y="10" style="font:400 20px 'Space Grotesk';fill:#6b6b70">α₀</text> <text x="352" y="102" style="font:400 20px 'Space Grotesk';fill:#6b6b70">0.1 α₀</text></svg>

Dead-cluster revival

Clusters with size below a threshold are revived by splitting a large cluster.

<svg viewBox="0 0 420 120" style="overflow: visible;"><circle cx="34" cy="56" r="11" fill="none" stroke="#a7b3bf" stroke-width="2" stroke-dasharray="4 3"></circle><circle cx="34" cy="56" r="2.5" fill="#a7b3bf"></circle><text x="34" y="100" font-size="15" fill="#67788a" text-anchor="middle" font-family="Space Grotesk, sans-serif">below threshold</text> <path d="M60 56 L96 56" stroke="#a7b3bf" stroke-width="2"></path><path d="M90 50 L97 56 L90 62" fill="none" stroke="#a7b3bf" stroke-width="2"></path><circle cx="160" cy="56" r="44" fill="#e8f1f9" stroke="#1f77b4" stroke-width="2"></circle><g fill="#1f77b4"><circle cx="140" cy="44" r="3"></circle><circle cx="168" cy="36" r="3"></circle><circle cx="182" cy="62" r="3"></circle><circle cx="150" cy="72" r="3"></circle><circle cx="172" cy="80" r="3"></circle><circle cx="134" cy="64" r="3"></circle><circle cx="160" cy="56" r="4.5" fill="#1c2b33"></circle></g><text x="160" y="116" font-size="15" fill="#67788a" text-anchor="middle" font-family="Space Grotesk, sans-serif">large cluster</text> <path d="M214 56 L250 56" stroke="#1f77b4" stroke-width="2"></path><path d="M244 50 L251 56 L244 62" fill="none" stroke="#1f77b4" stroke-width="2"></path><circle cx="296" cy="56" r="31" fill="#e8f1f9" stroke="#1f77b4" stroke-width="2"></circle><circle cx="370" cy="56" r="31" fill="#e8f1f9" stroke="#1f77b4" stroke-width="2"></circle><circle cx="296" cy="56" r="4.5" fill="#1c2b33"></circle><circle cx="370" cy="56" r="4.5" fill="#1c2b33"></circle><text x="333" y="116" font-size="15" fill="#67788a" text-anchor="middle" font-family="Space Grotesk, sans-serif">split in two</text></svg>

Specialized kernels

GPU kernels fuse the nearest-centroid assignment, turning the epoch savings above into matching wall-clock speedups.

<svg viewBox="0 0 420 120" style="overflow: visible;"><line x1="10" y1="10" x2="10" y2="110" stroke="#c9c9ce" stroke-width="1.5"></line><line x1="10" y1="110" x2="410" y2="110" stroke="#c9c9ce" stroke-width="1.5"></line><rect x="24" y="30" width="360" height="22" rx="4" fill="#e8f1f9" stroke="#a7b3bf" stroke-width="1.5"></rect><text x="30" y="46" font-size="15" fill="#67788a" font-family="Space Grotesk, sans-serif">naive PyTorch</text> <rect x="24" y="68" width="60" height="22" rx="4" fill="#1f77b4"></rect><text x="94" y="84" font-size="15" fill="#67788a" font-family="Space Grotesk, sans-serif">fused kernel</text></svg>

## The centroid update rules

The centroid update rule is the central component of e-means. This section aims to provide an overview of update rules for k-means clustering. All methods maintain, for each cluster j, a sum S <sub>j</sub> and a count N <sub>j</sub> of the points assigned to it, and take the centroid as their ratio:

$$
c_j = S_j / N_j
$$

They differ only in how S <sub>j</sub> and N <sub>j</sub> are updated. Below, s <sub>j</sub> and n <sub>j</sub> denote the sum and the count of the points in the current batch that are assigned to cluster j (both zero if none are).

**Lloyd’s algorithm** [^7] assigns every point to its nearest centroid and recomputes the statistics from scratch, using the full dataset as the batch:

$$
S_j \leftarrow s_j, \qquad\quad N_j \leftarrow n_j
$$

so c <sub>j</sub> is the exact mean of the points currently assigned to it. Each update costs one full pass over the data, and the procedure is repeated a fixed number of times (typically 20 to 50 iterations).

**MacQueen’s update** [^3] accumulates the statistics without ever discarding them:

$$
S_j \leftarrow S_j + s_j, \qquad\quad N_j \leftarrow N_j + n_j
$$

so c <sub>j</sub> is the uniform mean of every point assigned to cluster j since the start of training, including points assigned under earlier, possibly poor, centroid positions. This was later partially addressed by Staleness-Reduction Mini-Batch K-Means [^8], a hybrid method between k-means and MacQueen. They obtained important speedups, but only on very low numbers of clusters.

**e-means** works on mini-batches and replaces this sum with an exponential moving average:

$$
S_j \leftarrow (1-\alpha)\,S_j + \alpha\, s_j, \qquad\quad N_j \leftarrow (1-\alpha)\,N_j + \alpha\, n_j
$$

$$
S_j \leftarrow (1-\alpha)\,S_j + \alpha\, s_j
$$

$$
N_j \leftarrow (1-\alpha)\,N_j + \alpha\, n_j
$$

so older assignments are forgotten at rate α, and the centroid tracks recent assignments rather than the whole history. This update rule is typically used for moving distributions, hence their adoption for training VQ-VAEs [^6]. What we found is that it’s also extremely efficient for static datasets if it’s combined with e-means’ other components, and hyperparameters are properly tuned.

## e-means better escapes local minima

To better understand why e-means reaches better losses than Lloyd at convergence, we plotted a few trainings on toy datasets to evaluate their ability to escape local minima. Repeating trainings over 200 seeds, we found that e-means is much less likely to fall in pathological configurations compared to Lloyd.

Lloyd (full batch)

Training MSE **0.5124** after **1** epoch

e-means (mini-batches of 256)

Training MSE **0.4047** after **1.35** epochs

Two blobs of very different sizes, k = 8. Lloyd puts two centroids on the small blob and leaves the large one short. e-means starts in the same trap and leaves it within its first epochs, ending with seven centroids on the large blob and one on the small. Over 200 starts Lloyd stays stuck on 26% of starts, while e-means stays stuck on 3.5% of times.

Lloyd (full batch)

Training MSE **0.2332** after **0** epochs

e-means (mini-batches of 256)

Training MSE **0.09852** after **0.58** epochs

Nine blobs in a 3×3 grid with heavier corners, k = 10. Lloyd leaves the centre blob without a centroid and crowds three into a corner. e-means falls into the same arrangement, then climbs out around epoch 10. Over 200 starts Lloyd stays stuck more than 1% worse on 43% of starts, while e-means is more than 1% worse on 4%.

Lloyd (full batch)

Training MSE **2.046** after **0** epochs

e-means (mini-batches of 256)

Training MSE **2.046** after **0.00** epochs

Four blobs on a square around a heavier centre blob, k = 5. Lloyd puts two centroids on one corner blob and strands one in the gap between two others, which then share it. e-means, from the same start, gives every blob one. Over 200 starts Lloyd stays stuck on 15.5% of starts, while e-means stays stuck on 0%.

Lloyd (full batch)

Training MSE **0.2269**

after **0** epochs

e-means (mini-batches of 256)

Training MSE **0.09724**

after **0.87** epochs

Five blobs on a line, k = 5. Lloyd leaves a light middle blob without a centroid and gives an end blob two. e-means, from the same start, gives every blob one. Over 200 starts Lloyd stays stuck on 46% of starts, while e-means stays stuck on 0%.

Our explanation for that is that mini-batches provide more noisy updates that are more likely to explore the optimization landscape and escape local minima. Lloyd, with its always decreasing loss, is more likely to exploit found local minima and never escape them.

## Automatic hyperparameter tuning with scaling laws

An essential property of e-means is that practitioners don't need to set any additional hyperparameter compared to Lloyd's algorithm. We fitted two scaling laws to set the batch size `B` and step size α <sub>0</sub> from any problem's characteristics `(n, k, T)`, and found them to exhibit strong generalization on unseen datasets and problem scales.

$$
B = c_B \, k^{b_k} \, n^{b_n} \, T^{b_T}
$$

$$
\alpha_0 = \min\!\Big(c_\alpha \, k^{a_k} \, B^{a_B} \, n^{a_n} \, T^{a_T},\; 1\Big)
$$

<table><thead><tr><th rowspan="2">law</th><th rowspan="2">constant</th><th colspan="4">exponent of</th><th rowspan="2">regret,<br>held-out datasets</th><th rowspan="2">regret,<br>held-out size</th><th rowspan="2">R²</th></tr><tr><th>k</th><th>B</th><th>n</th><th>T</th></tr></thead><tbody><tr><td>step α <sub>0</sub></td><td>0.824</td><td>−0.46</td><td>0.90</td><td>−0.45</td><td>−0.11</td><td>0.07%</td><td>0.07%</td><td>0.95</td></tr><tr><td>batch B, default</td><td>0.035</td><td>0.13</td><td>n/a</td><td>0.88</td><td>0.81</td><td>0.19%</td><td>0.20%</td><td>0.96</td></tr><tr><td>batch B, quality law</td><td>0.0044</td><td>0.13</td><td>n/a</td><td>0.88</td><td>0.81</td><td>0.07%</td><td>0.06%</td><td>n/a</td></tr></tbody></table>

Regret = (MSE with the law − best MSE over the grid) / best MSE, median over configurations. Held-out datasets: SIFT, SPACEV, and the VIBE [^9] datasets arXiv and AG-News. Held-out size: one value of n left out of the fit and predicted.

We propose two equations to choose the batch, the default law and the quality law. The “quality law” trades off throughput for better clustering quality against the “default” law. Below we plot the training data for our scaling laws: validation MSE against step size α <sub>0</sub> (left) and batch size B (right).

![The two scaling laws fit on deep1b](https://e-means.github.io/assets/paper_laws.svg)

The two scaling laws fit on deep1b

## The importance of dead-cluster revival

Revival off

dead clusters: **0** of 25

Revival on (e-means)

dead clusters: **0** of 25

centroid dead cluster (no points) cluster boundaries

epochs: 0.00 · update 0 of 157

Toy example showing the importance of dead-cluster revival.

The main issue with mini-batch k-means is that it is prone to “dead” clusters, centroids that end up with zero assigned points during optimization. This reduces the effective size of the codebook, which is especially problematic for the large codebooks increasingly used today.

A common mitigation is to reinitialize clusters that fall below a certain size threshold, as done in EnCodec [^10], where dead centroids are simply replaced by random samples drawn from the incoming batch. While this helps, it does not fully resolve the issue. Instead of sampling arbitrary points from the batch, we revive dead clusters by splitting large, existing ones: we sample an active cluster with probability proportional to its size and split it into two. We found this approach, adapted from Faiss k-means, to be significantly more effective at eliminating dead clusters and preserving codebook capacity.

<table><thead><tr><th>dataset</th><th>revival policy</th><th>dead clusters</th><th>of codebook</th><th>imbalance</th><th>test MSE</th></tr></thead><tbody><tr><td rowspan="3">DEEP</td><td><strong>proportional split</strong></td><td><strong>47</strong></td><td><strong>0.3%</strong></td><td><strong>1.194</strong></td><td><strong>0.38762</strong></td></tr><tr><td>resample from batch (EnCodec)</td><td>2,343</td><td>14.3%</td><td>1.423</td><td>0.39124</td></tr><tr><td>off</td><td>4,313</td><td>26.3%</td><td>1.647</td><td>0.39448</td></tr><tr><td rowspan="3">SIFT</td><td><strong>proportional split</strong></td><td><strong>10</strong></td><td><strong>0.1%</strong></td><td><strong>1.186</strong></td><td><strong>0.19623</strong></td></tr><tr><td>resample from batch (EnCodec)</td><td>750</td><td>4.6%</td><td>1.233</td><td>0.19684</td></tr><tr><td>off</td><td>2,080</td><td>12.7%</td><td>1.404</td><td>0.19797</td></tr></tbody></table>

1 million vectors, k = 16,384, 5 epochs, mean over 5 seeds; only the revival policy varies. A cluster counts as dead when fewer than ten vectors are assigned to it at the end, a thousandth of an average cluster. Imbalance: how uneven the cluster sizes are (1 = all equal). From the [paper](https://arxiv.org/abs/2611.09501) ’s revival ablation table.

## Extensive experimental validation

We validated e-means on 24 different embedding and synthetic datasets and configurations (see [paper](https://arxiv.org/abs/2611.09501)). For the video we ran 234 configurations of e-means against k-means (16 datasets, 100k to 100M points): explore every curve in the [results map](https://e-means.github.io/results-map.html).

![Convergence curves vs Lloyd at 25 iterations](https://e-means.github.io/assets/paper_epochs_3arm.png)

Train (top) and test (bottom) MSE, divided by Lloyd’s after 25 epochs. Initialized from random vectors.

![Test error against wall-clock time on GPU, 10 million vectors, k=65,536](https://e-means.github.io/assets/paper_gpu_10m.svg)

Test MSE against wall-clock time on one H100, 10 million vectors, 65,536 clusters. 25 epochs of a plain PyTorch Lloyd (data on the GPU, bf16) take 142 to 155 seconds, against 14 to 22 seconds for Flash-KMeans 2. Labels on the curves mark the number of epochs.

![Epochs e-means needs to reach Lloyd's 25-epoch test error on the 11 VIBE embedding datasets: 1.6 to 2.4](https://e-means.github.io/assets/vibe_epochs_bar.svg)

Epochs e-means needs to reach the test error Lloyd reaches in 25 epochs, on the 11 datasets of the VIBE embedding benchmark (text, code, image and multimodal embeddings, d = 200 to 3,072, k = 8,192 or 16,384). Budgets spaced 0.2 epochs apart, median over five seeds. Every dataset needs between 1.6 and 2.4 epochs, against Lloyd’s 25.

## Library and code

from faiss.contrib.e\_means import Emeans # NumpyEmeans for NumPy em = Emeans(d, k, nepochs=T) # T epochs (5 by default) centroids, labels = em.train(x) # x: a PyTorch tensor (n, d) # labels: each vector's cluster in the last epoch

Repo: [faiss/contrib/e\_means](https://github.com/facebookresearch/faiss/tree/main/contrib/e_means).

### Citing this work

If you use e-means, please cite the paper ([arXiv:2611.09501](https://arxiv.org/abs/2611.09501)):

@misc{bessa2026emeansoutperformingkmeansin, title={e-means: outperforming k-means (in one-tenth the epochs)}, author={Swann Bessa and Pierre-Emmanuel Mazaré and Gergely Szilvasy and Hugo Touvron and David Picard and Matthijs Douze and Hervé Jégou}, year={2026}, eprint={2611.09501}, archivePrefix={arXiv}, primaryClass={cs.LG}, url={https://arxiv.org/abs/2611.09501}, }

## References

[^1]: M. Douze, A. Guzhva, C. Deng, J. Johnson, G. Szilvasy, P.-E. Mazaré, M. Lomeli, L. Hosseini, H. Jégou. "The Faiss library." *arXiv:2401.08281*, 2024.

[^2]: S. Yang, H. Xi, Y. Zhao, M. Li, X. Fan, J. Zhang, H. Cai, Y. Lin, X. Li, K. Keutzer, S. Han, C. Xu, I. Stoica. "Flash-KMeans: Fast and Memory-Efficient Exact K-Means." *arXiv:2603.09229*, 2026.

[^3]: J. MacQueen. "Some Methods for Classification and Analysis of Multivariate Observations." *Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability*, 1:281–297, 1967.

[^4]: D. Sculley. "Web-Scale K-Means Clustering." *WWW*, 2010.

[^5]: J. Newling, F. Fleuret. "Nested Mini-Batch K-Means." *NeurIPS*, 2016.

[^6]: A. van den Oord, O. Vinyals, K. Kavukcuoglu. "Neural Discrete Representation Learning." *NeurIPS*, 2017.

[^7]: S. Lloyd. "Least squares quantization in PCM." *IEEE Transactions on Information Theory*, 28(2):129–137, 1982 (circulated as a Bell Labs technical note since 1957).

[^8]: X. Zhu, J. Sun, Z. He, J. Jiang, Z. Wang. "Staleness-Reduction Mini-Batch K-Means." *IEEE Transactions on Neural Networks and Learning Systems*, 35(10):14424–14436, 2024.

[^9]: E. Jääsaari, V. Hyvönen, M. Ceccarello, T. Roos, M. Aumüller. "VIBE: Vector Index Benchmark for Embeddings." *arXiv:2505.17810*, 2025.

[^10]: A. Défossez, J. Copet, G. Synnaeve, Y. Adi. "High Fidelity Neural Audio Compression." *Transactions on Machine Learning Research*, 2023. arXiv:2210.13438.
