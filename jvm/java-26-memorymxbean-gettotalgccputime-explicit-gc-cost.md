---
title: "Java 26: MemoryMXBean.getTotalGcCpuTime() — Explicit GC Cost"
source: "https://norlinder.nu/posts/GC-Cost-CPU-vs-Memory/"
author:
  - "[[Jonas Norlinder]]"
published: 2026-02-23
created: 2026-04-29
description: "The author of Java 26's MemoryMXBean.getTotalGcCpuTime() analyzes the CPU-memory trade-off and why pause times fail to capture explicit GC cost."
tags:
  - "clippings"
---

> [!summary]
> Jonas Norlinder, the author of Java 26's new `MemoryMXBean.getTotalGcCpuTime()` API, argues that GC pause time has become a misleading proxy for GC cost in modern multi-core, concurrent collectors. He decomposes GC cost into explicit (dedicated GC threads), implicit (in-application barriers), and microarchitectural (cache effects) dimensions, and traces how the "pause = overhead" mental model fractures once collectors run alongside the application. The new JDK 26 API surfaces explicit GC CPU time directly, giving developers a measurable handle on the CPU-vs-memory trade-off that pause-time dashboards obscure.

## 1\. Background

Since the popularization of garbage collection (GC) in [Lisp](https://en.wikipedia.org/wiki/Lisp_\(programming_language\)) almost 70 years ago, managed runtimes have provided developers a with kind of magic: automatic memory management. This freed programmers from managing complex lifecycle management. This, along with many other ideas, influenced the design of [Smalltalk](https://en.wikipedia.org/wiki/Smalltalk). Following this lineage, Smalltalk was also one of several languages that inspired the authors of [Java](https://www.oracle.com/java/technologies/introduction-to-java.html), the language and runtime I spend my days improving.

While the programmer was liberated, the CPU was not. The GC now sat on the critical path to reclaim memory, accruing a debt that could not be deferred forever. For decades, settling this debt meant pausing the application entirely, or “stopping the world” in GC parlance. The collector would stop the application, scan the heap to identify and reclaim reusable memory. In the single-core era, the pause time served as a reliable proxy for machine load.

### 1.1. The GC Cost Taxonomy

To reason about the performance implications of GC, we need to decompose it into three dimensions as depicted in [Figure 1](#figure-gc-cost-taxonomy).

1. Explicit GC cost
	The CPU cycles consumed by dedicated GC threads performing tasks such as: traversing the object graph to find live data, relocating memory to free space, or updating references.
2. Implicit GC cost
	Code may be injected directly into the application to support specific GC capabilities. These are often referred to as barriers and are required for features such as reference counting, tracking object age (generations), or ensuring heap consistency when objects move concurrently.
3. Microarchitectural effects
	GC also impacts the memory subsystem. It can degrade performance by evicting application data from CPU caches or, alternatively, enhance it by rearranging objects to improve spatial locality.

Measuring the implicit GC cost is difficult. Blackburn and Hosking (2004) [\[1\]](#blackburn2004) augmented [Jikes RVM](https://en.wikipedia.org/wiki/Jikes_RVM) (a VM optimized for research) to establish a baseline without barriers for comparison. However, such approaches do not easily lend themselves to a performance-optimized VM like OpenJDK.

As I will show next, the components of explicit GC cost have expanded, making GC pauses a less powerful proxy for computational efficiency, while our tools to measure them have not. In [Section 2](#explicit-gc-cost-accounting-via-memorymxbeangettotalgccputime), I present the new Java API in JDK 26 for querying a GC’s explicit cost.

### 1.2. The Single-Threaded Pause

In OpenJDK, Serial GC exemplifies the classical single-core approach: when the heap is full, application execution halts entirely while the collector reclaims space. As [Figure 2](#figure-serial-gc) illustrates, this mechanism effectively converts memory pressure into paused time.

> **Computer Science 101: Wall-Clock vs. CPU Time**
>
> Wall-clock time measures the elapsed duration of execution. CPU time quantifies the aggregate time the CPU was actively executing the application.
>
> In a single-threaded, compute-bound scenario, these metrics converge. Conversely, in multi-core environments, they decouple. The ratio $\frac{\text{CPU time}}{\text{wall}-\text{clock time}}$ approximates the average number of cores utilized during execution. This distinction is critical for performance analysis: it decouples responsiveness from efficiency.

[Figure 2: Serial GC halting execution to reclaim memory](#figure-serial-gc)

Heap

Limit

16GB 3.5GB

**Thread**

Main

t (s)

Wall Clock

App: 9.0s (90.0%) GC Pause: 1.0s (10.0%)

CPU Time

App: 9.0s (90.0%) GC Pause: 1.0s (10.0%)

This visible cost drove an obsession with pause times across both industry and academia. Because long pauses were so destructive, we spent decades engineering them away. We leveraged the generational hypothesis to segment objects by age [\[2\]](#ungar1984) and built dashboards to alert on every pause time spike. The definition was strict: application time is productive; pause time is overhead. This mental model enabled developers to reason about performance costs as a batch processing equation.

The *batch processing mental model* also clarified the fundamental trade-off: memory buys throughput. Expanding the heap allows the JVM to defer collection, reducing the cumulative cost of pauses. Conversely, constraining memory forces the collector to intervene more frequently, burning CPU cycles just to keep the application afloat ([Figure 3](#figure-serial-gc-tight-heap)).

However, [Figure 3](#figure-serial-gc-tight-heap) reveals where this abstraction fractures. First, throughput is not determined solely by pause time. Every entry into a GC cycle incurs a safepoint penalty—the CPU cost of synchronizing threads to a halt. At high frequencies, this administrative overhead accumulates, leading to observable overhead in application execution. Second, the mapping between pause time and user latency breaks down. As the interval between GC cycles shrinks, an application’s function is statistically more likely to be interrupted multiple times. As noted by [\[3\]](#cheng2001), this compounding latency means a user’s experience is no longer bounded by the duration of a single stop, but by the sum of a chain of interruptions.

To see what this means in practice, imagine a web server handling requests during a busy period. When memory pressure is high and GC cycles are frequent, even short pauses can accumulate. A single HTTP request may arrive just before a GC pause starts and then, before it finishes processing, be interrupted again by the next pause. This chain of brief stutters can turn what should be a smooth interaction into a frustrating wait for the user, as their request is repeatedly delayed behind internal housekeeping. Suddenly, the user’s experience isn’t limited by pause time, but by unpredictable total disruption caused by these overlapping safepoint costs.

[Figure 3: Trading CPU for memory](#figure-serial-gc-tight-heap)

Heap

Limit

4GB 3.5GB

**Thread**

Main

t (s)

Wall Clock

App: 9.6s (60.0%) GC Pause: 6.4s (40.0%)

CPU Time

App: 9.6s (60.0%) GC Pause: 6.4s (40.0%)

### 1.3. The Multi-Threaded Pause

The arrival of multi-core CPUs provided more workers, presenting two fundamental design options: brute-force the pause (parallelism) or run alongside the application (concurrency). While more cores offer the potential for better performance, any cores that remain idle during parts of the application’s execution *still incur costs*, especially in a cloud environment where billing is based on provisioned resources. Hence, provisioning inefficiency directly translates into higher operational expenses, as organizations pay for the time extra CPUs spend waiting for the next burst of work. Making efficient use of every core is a technical concern as well as a budgetary one.

Parallel GC uses parallelism to reduce the pause time. It is essentially a multi-threaded evolution of Serial GC, defaulting to utilize all available cores to minimize the pause duration. This effectively allowed developers to apply a *parallelized batch processing mental model* to reason about how the GC trades CPU cycles for memory.

Consider the single-threaded workload from [Figure 2](#figure-serial-gc), re-deployed on a dual-core instance using Parallel GC in [Figure 4](#figure-parallel-gc). By distributing reclamation work across both cores, the collector halves the pause duration, yielding a 5% net boost in throughput.

The trade is explicit: we leverage hardware parallelism to reduce the stop-the-world window. Crucially, the total CPU time for GC remains constant; the work is simply parallelized, not eliminated. However, this introduces a provisioning inefficiency: the second core remains idle during the single-threaded application phase, utilized only to accelerate the cleanup.

[Figure 4: Reducing the GC pause through parallel scaling](#figure-parallel-gc)

Heap

Limit

16GB 4GB

**Thread**

Main

GC-0

GC-1

t (s)

Wall Clock

App: 9.0s (94.6%) GC Pause: 513ms (5.4%)

CPU Time

App: 9.0s (89.8%) GC Pause: 1.0s (10.2%)

### 1.4. From Batch Processing to Background Work

While Parallel GC reduced the pause, its pause time remains bounded by the size of the live set and Amdahl’s Law. Amdahl’s Law [\[4\]](#amdahl1967), depicted in [Figure 5](#figure-amdahl), defines the theoretical upper bound on speedup. In an ideal world (100% parallel), 20 cores purchase a 20x speedup. But introduce just 1% serial execution (99% parallel), and the currency devalues: 20 cores yield only 17x. At 64 cores, the return collapses to just 39x.

Think of this as hardware inflation. You are paying for 64 cores, but the purchasing power of that silicon has eroded by nearly 40%. The cost of speed inflates until the currency—additional cores—becomes practically worthless. Consequently, relying solely on parallelizing the GC pause is a dead end. Physics dictates that the serial bottleneck will eventually dominate; the pause time problem cannot be solved by simply buying more hardware.

For a workload that is 50% parallelizable, the speedup is bounded at 2x, with drastic diminishing returns visible after just three additional cores. Even with 90% parallelizability, the theoretical speedup is bounded by 10x regardless of hardware capacity. As the plot demonstrates, at 64 cores, the realized speedup remains below these theoretical limits, underscoring the penalty of the non-parallelizable logic.

### 1.5. G1: Shifting to Background Work

To further minimize pause times, G1 [\[5\]](#detlefs2004) (among other strategies) shifts work from the pause to run concurrently with the application, i.e., in the background. [Figure 6](#figure-g1) shows the result: the pause duration is significantly reduced. However, if we estimate the explicit GC cost by only measuring CPU usage during the pause, we overlook the total cost. In this workload, 79% of the GC’s CPU time was spent during concurrent phases, consuming resources while the application was running.

While Parallel GC relies solely on the parallelized batch processing model, G1 is a hybrid. It combines parallelized batch processing with background work. Because of this split, the pause time metric becomes an incomplete measure of a GC’s explicit cost. It no longer fails only in edge cases (such as high GC frequency in [Figure 3](#figure-serial-gc-tight-heap)); it now systematically underestimates the collector’s explicit cost.

[Figure 6: G1—A mostly concurrent GC](#figure-g1)

Heap

Limit

16GB 4GB

**Thread**

Main

GC-0

GC-1

t (s)

Wall Clock

App: 9.1s (81.0%) Concurrent GC: 1.4s (15.0%) GC Pause: 380ms (4.0%)

CPU Time

App: 9.1s (71.6%) Concurrent GC: 2.9s (22.4%) GC Pause: 760ms (6.0%)

### 1.6. ZGC: Decoupling GC Pause from Overhead

As [Figure 7](#figure-zgc) indicates, ZGC performs virtually all heavy lifting concurrently, including object relocation, and achieves sub-millisecond pauses regardless of heap size.

With ZGC, the correlation between pause duration and GC overhead is effectively decoupled. The work has not vanished; it has been amortized across background threads and the application threads themselves (via load barriers). Consequently, relying on pause time to quantify ZGC’s cost is incorrect.

[Figure 7: ZGC](#figure-zgc)

Heap

Limit

16GB 4GB

**Thread**

Main

GC-0

GC-1

t (s)

Wall Clock

App: 11.0s (40.0%) Concurrent GC: 6.6s (60.0%) GC Pause: 1ms (0.0%)

CPU Time

App: 11.0s (45.4%) Concurrent GC: 13.2s (54.5%) GC Pause: 2ms (0.0%)

### 1.7. Summary

The correlation between GC pause time and machine resources has weakened with every generation, creating an operational blind spot. Parallel GC introduces provisioning inefficiency, halving the pause only by doubling the CPU cost ([Figure 4](#figure-parallel-gc)), while G1 conceals throughput overhead by ignoring the 79% of cycles shifted to background threads ([Figure 6](#figure-g1)). ZGC effectively decouples the metrics entirely; sub-millisecond latency no longer implies low computational effort.

As noted by Kanev et al. [\[6\]](#kanev2015), in data centers, a substantial fraction of CPU cycles is spent on low-level operations, such as serialization and memory allocation. In managed runtimes, the GC is a dominant driver of this tax. Hassanein [\[7\]](#hassanein2016) corroborated this in Google’s production Java fleet (powering latency-critical services such as Gmail), demonstrating that GC CPU utilization directly translates into substantial hardware and power costs.

Crucially, merely measuring the process’s total CPU time is insufficient. While standard tools capture the aggregate bill, they lack *attribution*. They cannot distinguish between a compute-intensive application, an aggressive JIT compiler, or a struggling GC. Without isolating the GC’s specific contribution, we cannot understand the efficiency of our memory configuration. Not as a developer debugging performance or as researchers trying to develop the next generation of GC algorithms. We need a precise, internal accounting of the collector’s work.

This brings us to OpenJDK 26.

## 2\. Explicit GC Cost Accounting via MemoryMXBean.getTotalGcCpuTime()

With OpenJDK 26, I have introduced two new mechanisms to quantify explicit GC costs: unified logging via `-Xlog:cpu` (printed during JVM exit) and the Java API method `MemoryMXBean.getTotalGcCpuTime()`. Underlying both is the new [`cpuTimeUsage.hpp`](https://github.com/openjdk/jdk/blob/jdk-26%2B35/src/hotspot/share/services/cpuTimeUsage.hpp) framework, which provides support for any GC implementation within OpenJDK.

Researchers and engineers performing performance analysis/benchmarks can implement the pattern demonstrated below to extract this new telemetry. Measuring GC overhead on a per-iteration basis isolates the workload, effectively disregarding irrelevant noise generated during JVM startup (unless startup latency is the active subject of analysis). Below is an example of how it can be utilized.

```java
import com.sun.management.OperatingSystemMXBean;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.util.concurrent.Executors;
import java.util.stream.IntStream;

public class Main {
    static final MemoryMXBean memoryBean = ManagementFactory.getPlatformMXBean(MemoryMXBean.class);
    static final OperatingSystemMXBean osBean = ManagementFactory.getPlatformMXBean(OperatingSystemMXBean.class);

    static void main(){
        // Run 10 iterations to account for JIT warmup etc.
        for (int i = 0; i < 10; i++) {
            long start = System.nanoTime();
            long startGC = memoryBean.getTotalGcCpuTime();
            long startProcess = osBean.getProcessCpuTime();

            try (var executor = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors())) {
                IntStream.range(0, 100000).forEach(_ -> {
                    App app = new App();
                    executor.submit(app::critical);
                });
            }

            long end = System.nanoTime();
            long endGC = memoryBean.getTotalGcCpuTime();
            long endProcess = osBean.getProcessCpuTime();

            long duration = end - start;
            long gcCPU = endGC - startGC;
            long processCPU = endProcess - startProcess;

            System.out.println("GC used " + String.format("%.2f", 1.0 * gcCPU / duration) + " cores");
            System.out.println("Process used " + String.format("%.2f", 1.0 * processCPU / duration) + " cores");
            System.out.println("GC used " + (int)(100.0 * gcCPU / processCPU) + " % of total CPU spend");
            System.out.println("---------------------------------");
        }

    }
}

class App {
    byte[] a;
    void critical() {
        a = new byte[100000];
    }
}
```

Sampling `getTotalGcCpuTime` and `getProcessCpuTime` twice provides the deltas. The ratio of these deltas (`gcCPU` / `processCPU`) yields the explicit GC cost as a percentage of total CPU time.

> **Measuring CPU Time on Short-Running Applications**
>
> The JVM relies on the operating system’s CPU time accounting. Consequently, for very short-running processes (e.g., a few milliseconds), the results may be unreliable.

## 3\. Applying CPU Cost Accounting to xalan and Spring

To contextualize these metrics, the xalan and Spring workloads from the [DaCapo benchmark suite](https://github.com/dacapobench/dacapobench) were instrumented using the telemetry pattern demonstrated above. Evaluations were performed on an [Intel Xeon Gold 6354](https://www.intel.com/content/www/us/en/products/sku/212460/intel-xeon-gold-6354-processor-39m-cache-3-00-ghz/specifications.html) (18 cores, 36 hardware threads, 39 MB LLC), applying the default workload provisioning in DaCapo of one application thread per hardware thread. As will become evident, neither application saturates all 36 available hardware threads. Process utilization at smaller heap sizes indicates the opposite of a stressed system: a low number of cores in use. This is due to GC occupying the critical path. In these situations, pause times have historically served as a proxy for GC stress, but the true computational cost can finally be revealed.

[Figure 8](#figure-xalan) illustrates the CPU-memory tradeoff in xalan. Performance correlates with memory scarcity. We observe a performance cliff at 39 MB, with massive gains, followed by rapidly diminishing returns. Beyond this threshold, Amdahl’s Law dominates: process CPU usage continues to climb, yet throughput improvements are negligible. There is no universally “correct” GC CPU overhead—spending 79% of your CPU on GC (like Parallel in a 19 MB heap) might be perfectly acceptable if your primary constraint is memory footprint and you are willing to accept a low resilience to any increase in load. But now, that is a conscious business decision rather than a silent operational leak.

G1 utilization follows a non-linear relationship here. Interestingly, at the smallest heap size, G1 requires 65% less CPU than Parallel GC while delivering equivalent throughput. While ZGC requires more baseline memory headroom at these constrained heap sizes, it achieves parity with G1 and Parallel when given sufficient memory. This is not a deficiency, but a deliberate design tradeoff: we have exchanged memory footprint for minimal application latency.

At the smallest heap size, Parallel GC consumes 8.3 out of 10.5 active cores, meaning 79% of total CPU effort is spent on GC. Conversely, G1 is substantially more efficient, dedicating only 58% of active cores to GC.

In [Figure 9](#figure-spring), analyzing the Spring PetClinic application, the dynamic shifts are shown. At heap sizes of 202 MB and 405 MB, G1 consumes approximately 3.5x more CPU to maintain throughput—a stark contrast to the efficiency seen in xalan. ZGC again approaches the performance of Parallel and G1 as heap size increases. However, at 405 MB, ZGC’s CPU utilization is capped by a “storm” of allocation stalls. This represents a known anti-pattern for concurrent collectors: insufficient headroom forces the linearization of relocation work, stalling application threads.

## 4\. Conclusion

For too long, understanding the explicit CPU overhead of GC has required invasive profiling, custom builds, or educated guessing. With OpenJDK 26, we have democratized this data. The inclusion of `MemoryMXBean.getTotalGcCpuTime()` and `-Xlog:cpu` exposes the explicit GC cost as a tangible, observable metric.

I urge both the academic and engineering communities to adopt these standard APIs.

For researchers, this offers a standardized baseline for reporting overhead, reducing the noise in comparative studies. For engineers, it provides the observability needed to tune the application heap and to detect when you have hit the wall of Amdahl’s Law—before you throw more hardware at a software problem.

The tools are now in the JDK. Let’s use them to bring rigorous accounting to our production systems and our papers.

## 5\. References

\[1\] S. M. Blackburn and A. L. Hosking, “Barriers: Friend or Foe?,” in *ISMM*, 2004.

\[2\] D. Ungar, “Generation Scavenging: A Non-Disruptive High Performance Storage Reclamation Algorithm,” in *SDE 1*, 1984.

\[3\] P. Cheng and G. E. Blelloch, “A Parallel, Real-Time Garbage Collector,” in *PLDI*, 2001.

\[4\] G. M. Amdahl, “Validity of the single processor approach to achieving large scale computing capabilities,” in *AFIPS*, 1967.

\[5\] D. Detlefs, C. Flood, S. Heller, and T. Printezis, “Garbage-first garbage collection,” in *ISMM*, 2004.

\[6\] S. Kanev, J. P. Darago, K. Hazelwood, P. Ranganathan, T. Moseley, G.-Y. Wei, and D. Brooks, “Profiling a warehouse-scale computer,” in *ISCA*, 2015.

\[7\] W. Hassanein, “Understanding and Improving JVM GC Work Stealing at the Data Center Scale,” in *ISMM*, 2016.
