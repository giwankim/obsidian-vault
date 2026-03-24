---
title: "Inside the JVM: The Engineering Behind Enterprise Performance"
source: "https://www.tmdevlab.com/jvm-engineering-enterprise-performance.html"
author:
  - "[[Thiago Mendes]]"
published: 2026-03-22
created: 2026-03-23
description: "A deep dive into the JVM's adaptive architecture: class loading, JIT compilation, garbage collection, virtual threads, and how they work together. What it costs, what it buys, and why it still leads in sustained production workloads."
tags:
  - "clippings"
---

> [!summary]
> A deep technical dive into the HotSpot JVM's adaptive architecture, covering class loading, JIT compilation tiers, garbage collection algorithms (including sub-millisecond ZGC/Shenandoah), virtual threads, and diagnostics. Traces each subsystem to its OpenJDK C++ source code and explains the tradeoffs between startup cost and sustained production performance.

**For** engineers, architects, and SREs responsible for JVM workloads in production who want to understand what drives performance, throughput, and latency under concurrency.

## Why Should You Care?

In a landscape of native binaries that start in milliseconds and interpreted languages that prioritize developer velocity, the JVM chose a third path: an adaptive runtime that pays a cost at startup and earns it back, with interest, in sustained production workloads.

Your Java code is not simply "interpreted" or "compiled." It is interpreted first, then compiled with lightweight optimizations while the JVM observes how your application actually behaves, then recompiled with aggressive speculative optimizations based on that observed behavior, then deoptimized back to the interpreter when those speculations turn out wrong, then recompiled again with better data. This cycle runs continuously while your application serves traffic. AOT-compiled runtimes produce native code at build time, and that code is final. The JVM produces native code that evolves.

This is a runtime that ships five production garbage collectors, including two that deliver sub-millisecond pauses on terabyte-scale heaps. A runtime that implements virtual threads with native M:N scheduling, where millions of concurrent tasks share a handful of OS threads. A runtime with a built-in diagnostic engine (JFR) that records 150+ event types with less than 1% overhead. All of this implemented in roughly 1.2 million lines of C++ in the OpenJDK repository.

These capabilities come at a price. The JVM consumes more memory at baseline than a statically compiled binary. It needs time to reach peak performance. Its operational surface is larger. This study does not hide those trade-offs. It explains them, shows where they come from in the source code, and describes how the OpenJDK community is actively addressing each one.

This study opens the box. It walks through every major subsystem of the JVM, explains what it does, how it works, and points to the exact C++ source files where each mechanism is implemented. Along the way, it draws comparisons with other runtime models to give you a clear picture of what the JVM's adaptive architecture buys and what it costs. The goal is not to turn you into a JVM contributor. It is to give you the mental model that separates an engineer who writes code that runs on the JVM from one who understands *why* it runs the way it does.

## 1\. Overview: The Major Building Blocks

### What and why

The HotSpot JVM is the reference implementation of OpenJDK, the virtual machine that runs your Java (and Kotlin, Scala, Groovy, Clojure) code. The name HotSpot comes from its core strategy: identify frequently executed code paths and compile them to native machine code at runtime.

HotSpot is composed of five subsystems that cooperate with each other:

| Subsystem | Responsibility |
| --- | --- |
| **Class Loading** | Find, load, verify, and prepare classes for execution |
| **Execution Engine** | Execute bytecode through interpretation and JIT compilation |
| **Memory Management** | Allocate objects, manage metadata, and reclaim memory (GC) |
| **Runtime** | Manage threads, synchronization, JNI, and cross-subsystem coordination |
| **Diagnostics** | Instrumentation, profiling, and monitoring (JFR, JVMTI) |

### How it works: the lifecycle of a program

When you run `java MyApp`, the following happens:

```
#mermaid-1774232626478{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;fill:#ccc;}#mermaid-1774232626478 .error-icon{fill:#a44141;}#mermaid-1774232626478 .error-text{fill:#ddd;stroke:#ddd;}#mermaid-1774232626478 .edge-thickness-normal{stroke-width:2px;}#mermaid-1774232626478 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-1774232626478 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-1774232626478 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-1774232626478 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-1774232626478 .marker{fill:#6366f1;stroke:#6366f1;}#mermaid-1774232626478 .marker.cross{stroke:#6366f1;}#mermaid-1774232626478 svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;}#mermaid-1774232626478 .label{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;color:#ccc;}#mermaid-1774232626478 .cluster-label text{fill:#F9FFFE;}#mermaid-1774232626478 .cluster-label span,#mermaid-1774232626478 p{color:#F9FFFE;}#mermaid-1774232626478 .label text,#mermaid-1774232626478 span,#mermaid-1774232626478 p{fill:#ccc;color:#ccc;}#mermaid-1774232626478 .node rect,#mermaid-1774232626478 .node circle,#mermaid-1774232626478 .node ellipse,#mermaid-1774232626478 .node polygon,#mermaid-1774232626478 .node path{fill:#1e293b;stroke:#6366f1;stroke-width:1px;}#mermaid-1774232626478 .flowchart-label text{text-anchor:middle;}#mermaid-1774232626478 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-1774232626478 .node .label{text-align:center;}#mermaid-1774232626478 .node.clickable{cursor:pointer;}#mermaid-1774232626478 .arrowheadPath{fill:lightgrey;}#mermaid-1774232626478 .edgePath .path{stroke:#6366f1;stroke-width:2.0px;}#mermaid-1774232626478 .flowchart-link{stroke:#6366f1;fill:none;}#mermaid-1774232626478 .edgeLabel{background-color:hsl(0, 0%, 34.4117647059%);text-align:center;}#mermaid-1774232626478 .edgeLabel rect{opacity:0.5;background-color:hsl(0, 0%, 34.4117647059%);fill:hsl(0, 0%, 34.4117647059%);}#mermaid-1774232626478 .labelBkg{background-color:rgba(87.75, 87.75, 87.75, 0.5);}#mermaid-1774232626478 .cluster rect{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#8b5cf6;stroke-width:1px;}#mermaid-1774232626478 .cluster text{fill:#F9FFFE;}#mermaid-1774232626478 .cluster span,#mermaid-1774232626478 p{color:#F9FFFE;}#mermaid-1774232626478 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:12px;background:#1e293b;border:1px solid #8b5cf6;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-1774232626478 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#ccc;}#mermaid-1774232626478 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}NoYesNoYesjava MyAppLauncher creates JVMClassLoader loads MyApp.classInterpreter executes mainHot method?JIT compiles to native codeOptimized native executionAssumption invalidated?
```

Each step involves a different subsystem, and they exchange information constantly. Profiling in the interpreter feeds the JIT. Write barriers from the JIT serve the GC. Safepoints coordinate everyone. Understanding these interconnections is as important as understanding each subsystem in isolation.

### Where it lives in the code: repository structure

The HotSpot code resides in `src/hotspot/` with a platform abstraction in layers:

| Directory | Purpose |
| --- | --- |
| `share/` | Portable C++ code (~95% of HotSpot) |
| `share/interpreter/` | Template interpreter |
| `share/c1/` | C1 compiler (Client) |
| `share/opto/` | C2 compiler (Server/Opto) |
| `share/gc/` | Garbage collectors (g1, z, shenandoah, serial, parallel) |
| `share/oops/` | Object model (oop, Klass, Method, ConstantPool) |
| `share/classfile/` | Class loading, parsing, verification |
| `share/runtime/` | Threads, safepoints, synchronization |
| `share/compiler/` | Shared compilation infrastructure |
| `share/code/` | Code cache (the memory region where JIT-compiled code is stored) and nmethods (the JVM's internal representation of a compiled Java method) |
| `share/memory/` | Metaspace, internal allocation |
| `share/prims/` | JNI, JVMTI, jvm.cpp |
| `share/jfr/` | Java Flight Recorder |
| `share/jvmci/` | Interface for external compilers (Graal) |
| `cpu/<arch>/` | CPU-specific code (x86, aarch64, riscv,..) |
| `os/<os>/` | OS-specific code (linux, windows, bsd,..) |
| `os_cpu/<os>_<cpu>/` | OS + CPU combination |

The core Java code lives in `src/java.base/`, and the bridge between them happens primarily in `prims/jvm.cpp`, which implements ~200 `JVM_*` functions called by the native code in `java.base`.

## 2\. Class Loading: From.class to Execution

### What and why

Before executing any code, the JVM needs to transform the `.class` file (a sequence of bytes) into internal structures it can work with. This process has three formal phases defined by the JVM specification: **loading**, **linking**, and **initialization**.

### How it works

**The.class file** is a binary container with sequential structure: magic number (`0xCAFEBABE`), version, constant pool (an indexed table with all constants including strings, class names, method and field references), class information, fields, methods, and attributes. The constant pool works as a symbolic dictionary: bytecode contains no literal names, only indices into this pool.

The most important attribute of each method is **Code**, which contains the actual bytecode, stack and local variable limits, exception handler table, and the **StackMapTable** (used during verification).

**Phase 1, Loading:** The ClassLoader locates the binary representation of the class, reads its bytes, and creates the internal `Klass` structure. The JVM automatically loads all superclasses and superinterfaces first.

**Phase 2, Linking:**

- *Verification:* the JVM verifies that the bytecode is structurally valid and type-safe. The verifier uses the StackMapTable, type states precomputed by javac. It makes a single pass confirming that each instruction operates on correct types.
- *Preparation:* allocates memory for static fields (initialized to zero/null/false) and prepares the vtable (virtual dispatch) and itable (interface dispatch).
- *Resolution:* transforms symbolic references in the constant pool (textual names) into direct references (pointers). Can be lazy and happens on first use.

**Phase 3, Initialization:** executes the `<clinit>` method (static initializers). The JVM guarantees thread-safety, each class is initialized exactly once.

**ClassLoader Hierarchy:**

```
#mermaid-1774232627186{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;fill:#ccc;}#mermaid-1774232627186 .error-icon{fill:#a44141;}#mermaid-1774232627186 .error-text{fill:#ddd;stroke:#ddd;}#mermaid-1774232627186 .edge-thickness-normal{stroke-width:2px;}#mermaid-1774232627186 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-1774232627186 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-1774232627186 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-1774232627186 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-1774232627186 .marker{fill:#6366f1;stroke:#6366f1;}#mermaid-1774232627186 .marker.cross{stroke:#6366f1;}#mermaid-1774232627186 svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;}#mermaid-1774232627186 .label{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;color:#ccc;}#mermaid-1774232627186 .cluster-label text{fill:#F9FFFE;}#mermaid-1774232627186 .cluster-label span,#mermaid-1774232627186 p{color:#F9FFFE;}#mermaid-1774232627186 .label text,#mermaid-1774232627186 span,#mermaid-1774232627186 p{fill:#ccc;color:#ccc;}#mermaid-1774232627186 .node rect,#mermaid-1774232627186 .node circle,#mermaid-1774232627186 .node ellipse,#mermaid-1774232627186 .node polygon,#mermaid-1774232627186 .node path{fill:#1e293b;stroke:#6366f1;stroke-width:1px;}#mermaid-1774232627186 .flowchart-label text{text-anchor:middle;}#mermaid-1774232627186 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-1774232627186 .node .label{text-align:center;}#mermaid-1774232627186 .node.clickable{cursor:pointer;}#mermaid-1774232627186 .arrowheadPath{fill:lightgrey;}#mermaid-1774232627186 .edgePath .path{stroke:#6366f1;stroke-width:2.0px;}#mermaid-1774232627186 .flowchart-link{stroke:#6366f1;fill:none;}#mermaid-1774232627186 .edgeLabel{background-color:hsl(0, 0%, 34.4117647059%);text-align:center;}#mermaid-1774232627186 .edgeLabel rect{opacity:0.5;background-color:hsl(0, 0%, 34.4117647059%);fill:hsl(0, 0%, 34.4117647059%);}#mermaid-1774232627186 .labelBkg{background-color:rgba(87.75, 87.75, 87.75, 0.5);}#mermaid-1774232627186 .cluster rect{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#8b5cf6;stroke-width:1px;}#mermaid-1774232627186 .cluster text{fill:#F9FFFE;}#mermaid-1774232627186 .cluster span,#mermaid-1774232627186 p{color:#F9FFFE;}#mermaid-1774232627186 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:12px;background:#1e293b;border:1px solid #8b5cf6;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-1774232627186 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#ccc;}#mermaid-1774232627186 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}delegates todelegates todelegates toCustom ClassLoadersApplication ClassLoaderPlatform ClassLoaderBootstrap ClassLoader
```

| ClassLoader | Scope |
| --- | --- |
| **Bootstrap** | VM internal, represented as `null` in Java. Loads `java.lang.*`, `java.util.*`, etc. |
| **Platform** | Platform modules (formerly Extension ClassLoader) |
| **Application** | Classpath / module path |
| **Custom** | Hot-reload, plugins, isolation |

The parent-first delegation model ensures that fundamental classes are always loaded by Bootstrap. Internally, the **SystemDictionary** is the central registry. It maps (class name + ClassLoader) to `Klass*`.

### Where it lives in the code

The.class parsing happens in `classFileParser.cpp`. Here is the main entry point:

```
// src/hotspot/share/classfile/classFileParser.cpp

void ClassFileParser::parse_stream(const ClassFileStream* const stream, TRAPS) {
 // Magic value
 const u4 magic = stream->get_u4_fast();
 guarantee_property(magic == JAVA_CLASSFILE_MAGIC, "Incompatible magic value");

 // Version numbers
 _minor_version = stream->get_u2_fast();
 _major_version = stream->get_u2_fast();

 // Constant pool
 parse_constant_pool(stream, CHECK);

 // Access flags, this class, super class
 _access_flags.set_flags(stream->get_u2_fast() & JVM_RECOGNIZED_CLASS_MODIFIERS);
 // ..
}
```

[`src/hotspot/share/classfile/classFileParser.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/classfile/classFileParser.cpp#L5447-L5500)

The resolution entry point is in `LinkResolver::resolve_invoke`, which decides whether the call is virtual, interface, static, or special:

[`src/hotspot/share/interpreter/linkResolver.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/interpreter/linkResolver.cpp#L1701-L1710)

The SystemDictionary, the central class registry:

[`src/hotspot/share/classfile/systemDictionary.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/classfile/systemDictionary.cpp#L333-L380)

### Why this matters in practice

**Late class loading in production:**

Class loading is not just a startup concern. **Late class loading** (classes loaded for the first time during normal operation via reflection, service loaders, serialization frameworks, or plugin systems) can trigger cascading effects: new classes invalidate JIT-compiled code dependencies, causing deoptimization of previously optimized methods.

If you have ever seen a latency spike 30 minutes into a running service that correlates with a new code path being hit for the first time, class loading is a likely culprit. Tools: `-verbose:class` shows every class loaded and when. `-Xlog:class+load` gives timestamps. CDS/AppCDS pre-loads classes to eliminate this cost at startup.

## 3\. The Object Model: oops and Klass

### What and why

The JVM needs two things: to represent *types* (classes) and to represent *instances* (objects). In HotSpot, types are represented by `Klass` structures that live in Metaspace (native memory), and instances are `oops` (ordinary object pointers) that live in the Java heap.

### How it works

**Klass Hierarchy:**

```
#mermaid-1774232627275{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;fill:#ccc;}#mermaid-1774232627275 .error-icon{fill:#a44141;}#mermaid-1774232627275 .error-text{fill:#ddd;stroke:#ddd;}#mermaid-1774232627275 .edge-thickness-normal{stroke-width:2px;}#mermaid-1774232627275 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-1774232627275 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-1774232627275 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-1774232627275 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-1774232627275 .marker{fill:#6366f1;stroke:#6366f1;}#mermaid-1774232627275 .marker.cross{stroke:#6366f1;}#mermaid-1774232627275 svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;}#mermaid-1774232627275 g.classGroup text{fill:#6366f1;stroke:none;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:10px;}#mermaid-1774232627275 g.classGroup text .title{font-weight:bolder;}#mermaid-1774232627275 .nodeLabel,#mermaid-1774232627275 .edgeLabel{color:#f8fafc;}#mermaid-1774232627275 .edgeLabel .label rect{fill:#1e293b;}#mermaid-1774232627275 .label text{fill:#f8fafc;}#mermaid-1774232627275 .edgeLabel .label span{background:#1e293b;}#mermaid-1774232627275 .classTitle{font-weight:bolder;}#mermaid-1774232627275 .node rect,#mermaid-1774232627275 .node circle,#mermaid-1774232627275 .node ellipse,#mermaid-1774232627275 .node polygon,#mermaid-1774232627275 .node path{fill:#1e293b;stroke:#6366f1;stroke-width:1px;}#mermaid-1774232627275 .divider{stroke:#6366f1;stroke-width:1;}#mermaid-1774232627275 g.clickable{cursor:pointer;}#mermaid-1774232627275 g.classGroup rect{fill:#1e293b;stroke:#6366f1;}#mermaid-1774232627275 g.classGroup line{stroke:#6366f1;stroke-width:1;}#mermaid-1774232627275 .classLabel .box{stroke:none;stroke-width:0;fill:#1e293b;opacity:0.5;}#mermaid-1774232627275 .classLabel .label{fill:#6366f1;font-size:10px;}#mermaid-1774232627275 .relation{stroke:#6366f1;stroke-width:1;fill:none;}#mermaid-1774232627275 .dashed-line{stroke-dasharray:3;}#mermaid-1774232627275 .dotted-line{stroke-dasharray:1 2;}#mermaid-1774232627275 #compositionStart,#mermaid-1774232627275 .composition{fill:#6366f1!important;stroke:#6366f1!important;stroke-width:1;}#mermaid-1774232627275 #compositionEnd,#mermaid-1774232627275 .composition{fill:#6366f1!important;stroke:#6366f1!important;stroke-width:1;}#mermaid-1774232627275 #dependencyStart,#mermaid-1774232627275 .dependency{fill:#6366f1!important;stroke:#6366f1!important;stroke-width:1;}#mermaid-1774232627275 #dependencyStart,#mermaid-1774232627275 .dependency{fill:#6366f1!important;stroke:#6366f1!important;stroke-width:1;}#mermaid-1774232627275 #extensionStart,#mermaid-1774232627275 .extension{fill:transparent!important;stroke:#6366f1!important;stroke-width:1;}#mermaid-1774232627275 #extensionEnd,#mermaid-1774232627275 .extension{fill:transparent!important;stroke:#6366f1!important;stroke-width:1;}#mermaid-1774232627275 #aggregationStart,#mermaid-1774232627275 .aggregation{fill:transparent!important;stroke:#6366f1!important;stroke-width:1;}#mermaid-1774232627275 #aggregationEnd,#mermaid-1774232627275 .aggregation{fill:transparent!important;stroke:#6366f1!important;stroke-width:1;}#mermaid-1774232627275 #lollipopStart,#mermaid-1774232627275 .lollipop{fill:#1e293b!important;stroke:#6366f1!important;stroke-width:1;}#mermaid-1774232627275 #lollipopEnd,#mermaid-1774232627275 .lollipop{fill:#1e293b!important;stroke:#6366f1!important;stroke-width:1;}#mermaid-1774232627275 .edgeTerminals{font-size:11px;line-height:initial;}#mermaid-1774232627275 .classTitleText{text-anchor:middle;font-size:18px;fill:#ccc;}#mermaid-1774232627275 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}Klass_name : Symbol_super : Klass_layout_helper : jint_java_mirror : OopHandleInstanceKlass_constants : ConstantPool_methods : Array of Method_fields : Array of FieldInfo_vtable inline_itable inline_init_stateArrayKlass_dimension : int_component_mirrorInstanceRefKlassInstanceMirrorKlassInstanceClassLoaderKlassInstanceStackChunkKlassTypeArrayKlassObjArrayKlass
```

`InstanceKlass` contains everything about a class: constant pool, methods, fields, vtable (for virtual dispatch), itable (for interface dispatch), and initialization state.

**Object layout in the heap (oop):**

| Offset | Component | Size | Description |
| --- | --- | --- | --- |
| 0 | **Mark Word** | 64 bits | Tag bits (lock state), GC age (4 bits), identity hash code (31 bits), lock/GC metadata |
| 8 | **Klass Pointer** | 32 bits (compressed) | Points to the InstanceKlass in Metaspace |
| 12 | **Instance data** | Variable | Fields: int, long, Object references, etc. |
|  | **Padding** | 0-7 bytes | Alignment to 8-byte boundary |

**Project Lilliput:** This layout is being reworked by Project Lilliput ([JEP 450](https://openjdk.org/jeps/450) / [519](https://openjdk.org/jeps/519)), which merges the Klass Pointer into the Mark Word, reducing the base header from 12 bytes to 8 bytes.

For arrays, a 32-bit **length** field is inserted after the Klass pointer.

The **mark word** encodes multiple pieces of information. The tag bits indicate lock state: `01` = unlocked, `00` = lightweight-locked, `10` = inflated monitor, `11` = marked by GC. The 31-bit identity hash code is computed lazily upon first call to `hashCode()`. The 4-bit GC age tracks how many young GC cycles the object has survived (max 15, used for promotion decisions).

**Compressed oops:** object references are represented as 32 bits with a shift, addressing up to ~32 GB of heap with 32-bit pointers. Decoding: `address = heap_base + (narrow_oop << 3)`.

### Where it lives in the code

The mark word, all encoding/decoding logic lives in this class:

```
// src/hotspot/share/oops/markWord.hpp

class markWord {
 private:
 uintptr_t _value;          // the entire word

 public:
 // Bit layout (64-bit):
 static const int lock_bits       = 2;
 static const int age_bits       = 4;
 static const int hash_bits       = 31;    // max 31 bits for hash
 static const int unused_gap_bits    = 4;    // reserved for Valhalla

 // Lock bit state constants:
 //  00 -> lightweight locked
 //  01 -> unlocked (normal)
 //  10 -> monitor (inflated)
 //  11 -> marked by GC

 // Operations
 uint age() const { return mask_bits(value() >> age_shift, age_mask); }
 markWord incr_age() const {
   return age() == max_age ? markWord(_value) : set_age(age() + 1);
 }
 intptr_t hash() const { return mask_bits(value() >> hash_shift, hash_mask); }
};
```

[`src/hotspot/share/oops/markWord.hpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/oops/markWord.hpp#L77-L153)

The oop base (every object in the heap):

```
// src/hotspot/share/oops/oop.hpp

class oopDesc {
 private:
 volatile markWord _mark;      // mark word (64 bits)
 union _metadata {
  Klass*   _klass;       // direct pointer to Klass
  narrowKlass _compressed_klass;  // compressed pointer (32 bits)
 } _metadata;
 // .. instance fields follow after the header
};
```

[`src/hotspot/share/oops/oop.hpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/oops/oop.hpp#L47-L55)

[`src/hotspot/share/oops/klass.hpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/oops/klass.hpp#L63-L200), full Klass hierarchy

[`src/hotspot/share/oops/instanceKlass.hpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/oops/instanceKlass.hpp#L134-L350), InstanceKlass with vtable, itable, and more

### Why this matters in practice

Every Java object carries a 12-byte header (mark word + klass pointer) before a single field is stored. If your application has 10 million `Boolean` wrapper objects in the heap, that is 120 MB of headers alone. The actual data (`boolean` value) is 1 byte per object.

You can observe this directly using [JOL (Java Object Layout)](https://github.com/openjdk/jol):

```
// Run with: java -jar jol-cli.jar internals java.lang.Boolean
// Output (64-bit, compressed oops):
//
//  OFFSET SIZE   TYPE DESCRIPTION
//    0  12      (object header: mark word + klass)
//    12   1  boolean Boolean.value
//    13   3      (padding to 8-byte alignment)
//
//  Instance size: 16 bytes
//  Space losses: 3 bytes (padding) + 12 bytes (header) = 15 bytes overhead for 1 byte of data
```

This is why replacing `HashMap<Integer, Boolean>` with a `BitSet` or a primitive-specialized collection can cut memory consumption by 10x or more. Understanding object layout also explains why `record` types and value types ([Project Valhalla](https://openjdk.org/projects/valhalla)) are so anticipated. They target header overhead directly.

## 4\. Execution Engine: Interpretation

### What and why

When the JVM starts executing a method, it does not invoke the JIT compiler immediately. That would be too slow at startup. The interpreter executes bytecode directly, delivering immediate results while collecting profiling data that the JIT will use later.

### How it works

HotSpot does not interpret bytecode with a `switch/case` loop in C++. Instead, it uses a **template interpreter**: during JVM boot, it generates codelets (small blocks of native code) for each of the ~200 bytecodes. These codelets are stored in memory and executed via indirect jumps.

```
#mermaid-1774232627385{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;fill:#ccc;}#mermaid-1774232627385 .error-icon{fill:#a44141;}#mermaid-1774232627385 .error-text{fill:#ddd;stroke:#ddd;}#mermaid-1774232627385 .edge-thickness-normal{stroke-width:2px;}#mermaid-1774232627385 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-1774232627385 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-1774232627385 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-1774232627385 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-1774232627385 .marker{fill:#6366f1;stroke:#6366f1;}#mermaid-1774232627385 .marker.cross{stroke:#6366f1;}#mermaid-1774232627385 svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;}#mermaid-1774232627385 .label{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;color:#ccc;}#mermaid-1774232627385 .cluster-label text{fill:#F9FFFE;}#mermaid-1774232627385 .cluster-label span,#mermaid-1774232627385 p{color:#F9FFFE;}#mermaid-1774232627385 .label text,#mermaid-1774232627385 span,#mermaid-1774232627385 p{fill:#ccc;color:#ccc;}#mermaid-1774232627385 .node rect,#mermaid-1774232627385 .node circle,#mermaid-1774232627385 .node ellipse,#mermaid-1774232627385 .node polygon,#mermaid-1774232627385 .node path{fill:#1e293b;stroke:#6366f1;stroke-width:1px;}#mermaid-1774232627385 .flowchart-label text{text-anchor:middle;}#mermaid-1774232627385 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-1774232627385 .node .label{text-align:center;}#mermaid-1774232627385 .node.clickable{cursor:pointer;}#mermaid-1774232627385 .arrowheadPath{fill:lightgrey;}#mermaid-1774232627385 .edgePath .path{stroke:#6366f1;stroke-width:2.0px;}#mermaid-1774232627385 .flowchart-link{stroke:#6366f1;fill:none;}#mermaid-1774232627385 .edgeLabel{background-color:hsl(0, 0%, 34.4117647059%);text-align:center;}#mermaid-1774232627385 .edgeLabel rect{opacity:0.5;background-color:hsl(0, 0%, 34.4117647059%);fill:hsl(0, 0%, 34.4117647059%);}#mermaid-1774232627385 .labelBkg{background-color:rgba(87.75, 87.75, 87.75, 0.5);}#mermaid-1774232627385 .cluster rect{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#8b5cf6;stroke-width:1px;}#mermaid-1774232627385 .cluster text{fill:#F9FFFE;}#mermaid-1774232627385 .cluster span,#mermaid-1774232627385 p{color:#F9FFFE;}#mermaid-1774232627385 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:12px;background:#1e293b;border:1px solid #8b5cf6;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-1774232627385 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#ccc;}#mermaid-1774232627385 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}TemplateTableGeneratorStubQueueDispatch TableBytecode streamcodelet: iaddcodelet: iloadcodelet: invokevirtual
```

During JVM boot (left side), the TemplateTable drives the Generator to produce ~270 codelets stored in a StubQueue. At runtime (right side), the bytecode stream indexes into the Dispatch Table (256 entries per TOS state), which jumps to the corresponding codelet.

The execution cycle for each bytecode:

1. Load the next opcode from the bytecode stream
2. Advance the bytecode pointer
3. Jump indirectly to the corresponding codelet via the dispatch table: `jmp *(table + opcode * 8)`

That is only 2-3 machine instructions for dispatch. **TOS caching** (Top-of-Stack caching) keeps the top value of the operand stack in a dedicated CPU register (`rax` on x86-64), avoiding unnecessary push/pop between consecutive bytecodes.

**Dispatch table swap for safepoints:** when the VM needs to pause threads, it replaces the normal dispatch table with a variant that includes safepoint checks. No thread needs to be interrupted. Each one naturally checks on the next dispatch.

### Where it lives in the code

Interpreter initialization, note the comment in the code itself confirming the ~270 codelets:

```
// src/hotspot/share/interpreter/templateInterpreter.cpp

void TemplateInterpreter::initialize_stub() {
 assert(_code == nullptr, "must only initialize once");
 assert((int)Bytecodes::number_of_codes <= (int)DispatchTable::length,
     "dispatch table too small");

 int code_size = InterpreterCodeSize;
 NOT_PRODUCT(code_size *= 4;) // debug uses extra interpreter code space

 // 270+ interpreter codelets are generated and each of them is aligned
 // to HeapWordSize, plus their code section is aligned to CodeEntryAlignment.
 // ..
}
```

[`src/hotspot/share/interpreter/templateInterpreter.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/interpreter/templateInterpreter.cpp#L41-L56)

The dispatch table and the safepoint swap:

```
// src/hotspot/share/interpreter/templateInterpreter.hpp

class TemplateInterpreter: public AbstractInterpreter {
 // Three dispatch tables:
 static DispatchTable _active_table;  // currently active table (pointer that alternates)
 static DispatchTable _normal_table;  // normal dispatch
 static DispatchTable _safept_table;  // dispatch with safepoint checks

 // The dispatch table: one entry per byte value x each TOS state
 //  _table[number_of_states][256]
 // number_of_states includes: itos, ltos, ftos, dtos, atos, vtos, ..

 static address* dispatch_table(TosState state) { return _active_table.table_for(state); }
 static address* safept_table(TosState state)  { return _safept_table.table_for(state); }
};
```

[`src/hotspot/share/interpreter/templateInterpreter.hpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/interpreter/templateInterpreter.hpp#L86-L134)

A concrete example, how the template for the `_return` instruction generates native code on x86-64:

```
// src/hotspot/cpu/x86/templateTable_x86.cpp

void TemplateTable::_return(TosState state) {
 transition(state, state);

 if (_desc->bytecode() == Bytecodes::_return_register_finalizer) {
   Register robj = c_rarg1;
   __ movptr(robj, aaddress(0));       // load 'this'
   __ load_klass(rdi, robj, rscratch1);    // load Klass*
   __ testb(Address(rdi, Klass::misc_flags_offset()),
        KlassFlags::_misc_has_finalizer); // has finalizer?
   Label skip_register_finalizer;
   __ jcc(Assembler::zero, skip_register_finalizer);
   // If so, call runtime to register it
   __ call_VM(noreg, CAST_FROM_FN_PTR(address,
         InterpreterRuntime::register_finalizer), robj);
   __ bind(skip_register_finalizer);
 }
 // .. remove_activation and return
}
```

[`src/hotspot/cpu/x86/templateTable_x86.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/cpu/x86/templateTable_x86.cpp#L2114-L2157)

Note the pattern: the `__` macro is a shortcut for `_masm->` (the macro assembler), and each call generates native x86 instructions. This is the template interpreter: C++ that *generates* machine code.

### Why this matters in practice

**Startup performance is interpreter performance.**

The interpreter is what runs your code during startup and warmup. If your application has strict startup time requirements (serverless functions, CLI tools, microservices with frequent restarts), you are measuring interpreter performance, not JIT performance. This is why frameworks like Spring invest in reducing the amount of code executed before the application is ready. It also explains why `-XX:TieredStopAtLevel=1` (compile with C1 only, skip C2) can improve startup time at the cost of peak throughput — you get native code faster, just not the most optimized native code.

## 5\. Execution Engine: JIT Compilation

### What and why

The interpreter is fast enough for startup, but for peak performance, the JVM compiles "hot" methods into optimized native machine code. HotSpot has two JIT compilers that work together.

### How it works: Tiered Compilation

The JVM uses five tiers of execution, balancing startup speed with peak performance:

| Tier | Executor | Behavior |
| --- | --- | --- |
| **0** | Interpreter | Initial execution of all code. Collects basic invocation and backedge counters. |
| **1** | C1 without profiling | For trivial methods. Fast native code, no data collection. |
| **2** | C1 with limited profiling | Counters only. Fallback when the C2 queue is full. |
| **3** | C1 with full profiling | Collects rich data: receiver type profiles, branch frequencies, detailed counters. Default path before C2. |
| **4** | C2 full optimization | Highly optimized compilation using all data collected in Tier 3. |

```
#mermaid-1774232627421{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;fill:#ccc;}#mermaid-1774232627421 .error-icon{fill:#a44141;}#mermaid-1774232627421 .error-text{fill:#ddd;stroke:#ddd;}#mermaid-1774232627421 .edge-thickness-normal{stroke-width:2px;}#mermaid-1774232627421 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-1774232627421 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-1774232627421 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-1774232627421 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-1774232627421 .marker{fill:#6366f1;stroke:#6366f1;}#mermaid-1774232627421 .marker.cross{stroke:#6366f1;}#mermaid-1774232627421 svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;}#mermaid-1774232627421 .label{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;color:#ccc;}#mermaid-1774232627421 .cluster-label text{fill:#F9FFFE;}#mermaid-1774232627421 .cluster-label span,#mermaid-1774232627421 p{color:#F9FFFE;}#mermaid-1774232627421 .label text,#mermaid-1774232627421 span,#mermaid-1774232627421 p{fill:#ccc;color:#ccc;}#mermaid-1774232627421 .node rect,#mermaid-1774232627421 .node circle,#mermaid-1774232627421 .node ellipse,#mermaid-1774232627421 .node polygon,#mermaid-1774232627421 .node path{fill:#1e293b;stroke:#6366f1;stroke-width:1px;}#mermaid-1774232627421 .flowchart-label text{text-anchor:middle;}#mermaid-1774232627421 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-1774232627421 .node .label{text-align:center;}#mermaid-1774232627421 .node.clickable{cursor:pointer;}#mermaid-1774232627421 .arrowheadPath{fill:lightgrey;}#mermaid-1774232627421 .edgePath .path{stroke:#6366f1;stroke-width:2.0px;}#mermaid-1774232627421 .flowchart-link{stroke:#6366f1;fill:none;}#mermaid-1774232627421 .edgeLabel{background-color:hsl(0, 0%, 34.4117647059%);text-align:center;}#mermaid-1774232627421 .edgeLabel rect{opacity:0.5;background-color:hsl(0, 0%, 34.4117647059%);fill:hsl(0, 0%, 34.4117647059%);}#mermaid-1774232627421 .labelBkg{background-color:rgba(87.75, 87.75, 87.75, 0.5);}#mermaid-1774232627421 .cluster rect{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#8b5cf6;stroke-width:1px;}#mermaid-1774232627421 .cluster text{fill:#F9FFFE;}#mermaid-1774232627421 .cluster span,#mermaid-1774232627421 p{color:#F9FFFE;}#mermaid-1774232627421 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:12px;background:#1e293b;border:1px solid #8b5cf6;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-1774232627421 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#ccc;}#mermaid-1774232627421 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}trivial methoddefault pathhot method + rich datadeoptimizationTier 0: InterpreterTier 1: C1, no profilingTier 3: C1, full profilingTier 4: C2, full optimization
```

**The C1 Compiler** prioritizes compilation speed (~9-16x faster than C2). Three phases:

1. **HIR (High-Level IR):** abstract interpretation of bytecode generates an SSA (Static Single Assignment) representation, a form where every variable is assigned exactly once, making data flow analysis and optimization straightforward. Includes inlining of small methods and constant folding.
2. **LIR (Low-Level IR):** translation to platform-specific instructions.
3. **Register Allocation + Emission:** linear scan allocation (faster than graph coloring) + final machine code.

**The C2 Compiler** prioritizes code quality. Its IR is the **Sea of Nodes**, a graph where nodes represent operations and edges represent data and control dependencies. Nodes "float freely" without belonging to basic blocks, enabling aggressive reordering.

Before reading the table, a few terms: the **Ideal Graph** is C2's internal representation of the program as a Sea of Nodes graph. **GVN (Global Value Numbering)** is an optimization that eliminates redundant computations by identifying expressions that always produce the same result. **Escape analysis** determines whether an object is accessible outside the method that created it. If not, the JVM can allocate it on the stack or decompose it into individual fields, avoiding heap allocation entirely. **MachNodes** are platform-specific machine instruction representations that replace Ideal nodes during instruction selection.

| Phase | What it does |
| --- | --- |
| **Parsing** | Bytecode to Ideal Graph with GVN and inlining |
| **Optimization** | Iterative GVN, escape analysis, loop optimizations, vectorization |
| **Instruction Selection** | Ideal nodes to MachNodes via pattern matching |
| **Global Code Motion** | Places floating nodes into basic blocks |
| **Register Allocation** | Briggs-Chaitin graph coloring |
| **Code Emission** | Final machine code |

**Profiling, the bridge between interpretation and compilation.** Each method has a **MethodData** (MDO) that accumulates, per bytecode point: invocation counters, receiver type profiles (the 2 most frequent types, for bimorphic inlining), branch frequencies, and deoptimization history. This data fuels C2's speculative optimizations.

**Inline Caches and call site specialization.** The JVM classifies each virtual call site based on observed receiver types. A **monomorphic** call site has seen only one type. The JIT can inline the target method directly. A **bimorphic** site has seen exactly two types. The JIT generates a conditional branch checking both. A **megamorphic** site has seen three or more types. The JIT gives up on direct inlining and falls back to a virtual dispatch lookup via the vtable or itable. This transition from monomorphic to megamorphic is one of the most common causes of performance cliffs in Java applications, and understanding it helps explain many `-XX:+PrintCompilation` patterns.

**On-Stack Replacement (OSR):** allows compiling a method that is *inside a long-running loop* and replacing the interpreted frame with a compiled one without waiting for the method to return.

**Deoptimization:** when speculative optimizations fail (unexpected type, new subclass, null check), the compiled frame is reverted to interpreted. The method can be recompiled with updated profiling. Common reasons: `class_check`, `null_check`, `unstable_if`, `unreached`, `bimorphic`.

**Code Cache:** stores all compiled code in native memory, segmented into three areas:

| Segment | Content | Lifetime |
| --- | --- | --- |
| Non-method | Interpreter codelets, compiler buffers, VM internal code | Permanent (~5 MB) |
| Profiled nmethods | C1-compiled code (tiers 2/3) with profiling instrumentation | Short (replaced when C2 compiles) |
| Non-profiled nmethods | C2-compiled code (tier 4) and C1 tier 1 | Long (production code) |

### Where it lives in the code

The CompileBroker, the orchestrator that decides what to compile and when:

[`src/hotspot/share/compiler/compileBroker.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/compiler/compileBroker.cpp#L1177-L1250)

The C2 pipeline entry point, the `Compile` class:

[`src/hotspot/share/opto/compile.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/opto/compile.cpp#L629-L900)

Escape analysis, where the JVM decides if it can eliminate an allocation:

[`src/hotspot/share/opto/escape.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/opto/escape.cpp#L104-L160)

Deoptimization, the mechanism for "back to interpreter":

[`src/hotspot/share/runtime/deoptimization.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/runtime/deoptimization.cpp#L1869-L1900)

The MethodData, the profiling structure that connects interpreter and JIT:

[`src/hotspot/share/oops/methodData.hpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/oops/methodData.hpp#L1991-L2100)

### Why this matters in practice

**Benchmarking without warmup produces misleading numbers.**

Java benchmarks that do not warm up adequately are measuring the interpreter or C1, not the code that will run in production. That is why [JMH (Java Microbenchmark Harness)](https://github.com/openjdk/jmh) exists: it manages warmup iterations, fork isolation, and deoptimization detection. If you benchmark without JMH, you are likely producing misleading numbers.

**Megamorphic call sites** are one of the most common silent performance killers:

```
// Monomorphic: the JIT sees only one type at this call site.
// It inlines process() directly, eliminating the virtual dispatch entirely.
List<Order> orders = new ArrayList<>();
for (Order order : orders) {
  order.process(); // always StandardOrder.process() -> inlined
}

// Megamorphic: the JIT sees 4+ types at the same call site.
// It cannot inline and falls back to vtable lookup on every call.
List<Order> orders = loadMixedOrders(); // StandardOrder, ExpressOrder, BulkOrder, ReturnOrder...
for (Order order : orders) {
  order.process(); // which implementation? vtable lookup every time
}
```

The megamorphic version can be 2-5x slower at that call site compared to monomorphic dispatch because the JIT cannot inline across multiple implementations. This does not mean you should avoid polymorphism. It means you should be aware of the cost when polymorphism occurs in hot paths. `-XX:+PrintCompilation` and `-XX:+TraceDeoptimization` reveal when this happens.

**Deoptimization storms.**

A single class loading event (plugin loaded, serialization of a new type, dynamic proxy created) can invalidate dozens of compiled methods at once, causing a burst of recompilation. In latency-sensitive systems, this manifests as an unexplained latency spike that self-resolves after a few seconds (recompilation). `-XX:+TraceDeoptimization` is the diagnostic tool.

**How this compares to other runtime models.**

AOT-compiled runtimes (Go, Rust,.NET Native AOT) produce final machine code at build time. That code runs at full speed from the first instruction, but it cannot adapt. If a virtual call site turns out to be monomorphic in production, an AOT compiler has no way to know and no way to inline it. The JVM observes this at runtime and eliminates the dispatch entirely.

Interpreted runtimes (CPython, Ruby/CRuby) execute without compilation at all. V8 (Node.js) and LuaJIT sit between these extremes, with lightweight JIT compilation but without the deep speculative pipeline of C2. The closest comparable system to HotSpot is.NET's RyuJIT with dynamic PGO, which also uses tiered compilation and profile-guided recompilation. The JVM's advantage is the maturity and depth of its speculative optimization pipeline, built over two decades of production feedback. The trade-off is warmup time: AOT runtimes deliver peak performance immediately, the JVM takes seconds to minutes.

## 6\. Memory Management: Heap and Allocation

### What and why

The JVM manages all Java object memory automatically. This includes allocation (creating objects) and deallocation (garbage collection). The heap is divided into managed areas, and allocation is optimized to be extremely fast.

### How it works: TLABs

Object allocation is one of the most frequent operations. HotSpot optimizes it with **TLABs (Thread-Local Allocation Buffers)**: each Java thread receives a private buffer inside Eden (the young part of the heap). Allocation is **bump pointer**: the thread simply advances a cursor forward through a contiguous block of memory. The pointer moves by the object size and the space behind it becomes the new object. No synchronization, no locks, no atomic CAS. It takes ~6 machine instructions.

```
#mermaid-1774232627436{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;fill:#ccc;}#mermaid-1774232627436 .error-icon{fill:#a44141;}#mermaid-1774232627436 .error-text{fill:#ddd;stroke:#ddd;}#mermaid-1774232627436 .edge-thickness-normal{stroke-width:2px;}#mermaid-1774232627436 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-1774232627436 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-1774232627436 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-1774232627436 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-1774232627436 .marker{fill:#6366f1;stroke:#6366f1;}#mermaid-1774232627436 .marker.cross{stroke:#6366f1;}#mermaid-1774232627436 svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;}#mermaid-1774232627436 .label{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;color:#ccc;}#mermaid-1774232627436 .cluster-label text{fill:#F9FFFE;}#mermaid-1774232627436 .cluster-label span,#mermaid-1774232627436 p{color:#F9FFFE;}#mermaid-1774232627436 .label text,#mermaid-1774232627436 span,#mermaid-1774232627436 p{fill:#ccc;color:#ccc;}#mermaid-1774232627436 .node rect,#mermaid-1774232627436 .node circle,#mermaid-1774232627436 .node ellipse,#mermaid-1774232627436 .node polygon,#mermaid-1774232627436 .node path{fill:#1e293b;stroke:#6366f1;stroke-width:1px;}#mermaid-1774232627436 .flowchart-label text{text-anchor:middle;}#mermaid-1774232627436 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-1774232627436 .node .label{text-align:center;}#mermaid-1774232627436 .node.clickable{cursor:pointer;}#mermaid-1774232627436 .arrowheadPath{fill:lightgrey;}#mermaid-1774232627436 .edgePath .path{stroke:#6366f1;stroke-width:2.0px;}#mermaid-1774232627436 .flowchart-link{stroke:#6366f1;fill:none;}#mermaid-1774232627436 .edgeLabel{background-color:hsl(0, 0%, 34.4117647059%);text-align:center;}#mermaid-1774232627436 .edgeLabel rect{opacity:0.5;background-color:hsl(0, 0%, 34.4117647059%);fill:hsl(0, 0%, 34.4117647059%);}#mermaid-1774232627436 .labelBkg{background-color:rgba(87.75, 87.75, 87.75, 0.5);}#mermaid-1774232627436 .cluster rect{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#8b5cf6;stroke-width:1px;}#mermaid-1774232627436 .cluster text{fill:#F9FFFE;}#mermaid-1774232627436 .cluster span,#mermaid-1774232627436 p{color:#F9FFFE;}#mermaid-1774232627436 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:12px;background:#1e293b;border:1px solid #8b5cf6;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-1774232627436 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#ccc;}#mermaid-1774232627436 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}YesNoYesNonew Object()TLAB has space?Bump pointer: advance cursorRetire current TLAB, request new oneEden has space?Allocate new TLAB from EdenTrigger minor GCRetry allocation
```

CAS (Compare-And-Swap) is a CPU instruction that updates a memory location only if it still holds an expected value. It is the building block of lock-free data structures, but even a single CAS is far more expensive than the bump pointer fast path.

Each thread owns its TLAB exclusively, bump pointer allocation takes ~6 machine instructions with zero synchronization. When a TLAB is exhausted, the remaining space is filled with a filler object (so the GC can walk the heap linearly) and a new TLAB is carved out of Eden.

When the TLAB is exhausted:

1. Fill remaining space with a filler object
2. Allocate a new TLAB from Eden
3. If Eden is full, trigger a minor GC
4. If allocation still fails, OOM

Objects too large for a TLAB follow a different path. In G1 (the default collector), objects that are 50% or more of a region size are allocated directly as humongous regions in the old generation, bypassing Eden entirely. In other collectors, oversized objects are allocated in the shared Eden area using atomic CAS operations.

### Where it lives in the code

The heap allocation path, see how `obj_allocate` delegates to `MemAllocator`:

```
// src/hotspot/share/gc/shared/collectedHeap.inline.hpp

inline oop CollectedHeap::obj_allocate(Klass* klass, size_t size, TRAPS) {
 ObjAllocator allocator(klass, size, THREAD);
 return allocator.allocate();
}
```

[`src/hotspot/share/gc/shared/collectedHeap.inline.hpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/gc/shared/collectedHeap.inline.hpp#L34-L37)

The TLAB fast path, in `memAllocator.cpp`, `allocate()` tries the current thread's TLAB first. If exhausted, the slow path allocates a new TLAB or goes directly to Eden:

[`src/hotspot/share/gc/shared/memAllocator.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/gc/shared/memAllocator.cpp#L354-L400)

TLAB configuration:

[`src/hotspot/share/gc/shared/tlab_globals.hpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/gc/shared/tlab_globals.hpp#L1-L60)

### Why this matters in practice

Knowing that allocation is bump-pointer fast (~6 instructions) but GC cost is proportional to live objects changes a fundamental design instinct:

```
// This is FAST in Java. Each new StringBuilder() is a bump-pointer
// allocation in the thread's TLAB. The object dies young in Eden.
// GC cost is near zero for short-lived objects.
public String formatMessage(String user, String action) {
  return new StringBuilder()
    .append(user).append(": ").append(action)
    .toString();
}

// This is SLOWER despite looking "optimized." The pool adds synchronization
// overhead on borrow/return, the pooled objects survive to old gen (increasing
// GC scanning cost), and the CAS contention on the pool defeats the whole
// purpose of lock-free TLAB allocation.
public String formatMessage(String user, String action) {
  StringBuilder sb = pool.borrow();  // lock or CAS
  try {
    return sb.append(user).append(": ").append(action).toString();
  } finally {
    sb.setLength(0);
    pool.release(sb);        // lock or CAS again
  }
}
```

**Short-lived objects are cheap. Object pooling is usually counterproductive.**

In Java, creating short-lived objects and letting them die in Eden is often the correct and cheapest approach. Object pooling is counterproductive unless the objects are genuinely expensive to create (database connections, SSL contexts) or very large (direct byte buffers). When troubleshooting allocation pressure, `-XX:+PrintTLAB` reveals per-thread allocation rates and slow-path frequency.

**How this compares to other runtime models.**

Most runtimes with managed memory use similar thread-local allocation strategies. Go uses per-P mcache allocators with bump-pointer semantics..NET uses per-thread allocation contexts in its managed heap. V8 allocates in a generational heap with semi-space copying. The fast path is comparable across all of them. Where the JVM pulls ahead is downstream: C2's escape analysis can determine at runtime that an object never escapes the method, and eliminate the allocation entirely by decomposing the object into scalar values that live in CPU registers. Go performs escape analysis at compile time (AOT), but with less information: it cannot observe runtime behavior, so its decisions are more conservative. Runtimes without GC (Rust, C/C++) place allocation responsibility entirely on the developer, avoiding pause-time costs but requiring manual or ownership-based memory management.

## 7\. Garbage Collection

### What and why

The GC identifies unreachable objects in the heap and reclaims their space for new allocations. The JVM offers multiple collectors, each with different trade-offs between throughput, pause latency, and footprint.

### How it works

**The generational principle:** most objects die young (weak generational hypothesis). Generational collectors divide the heap into young generation (newly created objects) and old generation (objects that survived multiple collections). Young GCs are frequent and fast. Old GCs are rarer and more expensive.

| Collector | Strategy | Pauses | Best for |
| --- | --- | --- | --- |
| **Serial GC** | Single-threaded, generational | STW, proportional to heap | ≤1 core, small heaps |
| **Parallel GC** | Multi-threaded, same architecture | STW, optimized for throughput | Batch processing |
| **G1 GC** (default) | Region-based, incremental, concurrent marking | STW with configurable pause targets | General-purpose |
| **ZGC** | Region-based, colored pointers, concurrent compaction | Sub-millisecond regardless of heap size | Latency-sensitive, up to 16 TB |
| **Shenandoah** | Region-based, forwarding pointers, concurrent compaction | Sub-millisecond, supports compressed oops | Latency-sensitive |

### G1 GC in depth

The heap is divided into **equal-sized regions** (1-32 MB). Each region is dynamically assigned as Eden, Survivor, Old, Humongous, or Free. There is no fixed physical separation between generations.

| Region type | Role | Generation |
| --- | --- | --- |
| **Eden (E)** | Newly allocated objects, TLABs live here | Young |
| **Survivor (S)** | Objects that survived at least one young GC | Young |
| **Old (O)** | Objects promoted after surviving multiple GCs | Old |
| **Humongous (H)** | Objects ≥50% of a region size, allocated directly in old gen | Old |
| **Free (F)** | Available for assignment to any role | Unassigned |

G1 adjusts the number of young-generation regions dynamically to meet the configured pause target (`-XX:MaxGCPauseMillis`).

**Key G1 mechanisms:**
- **Remembered Sets and Card Table:** When compiled code writes a reference (`putfield`), a **write barrier** marks the corresponding card as "dirty." **Concurrent refinement threads** process these dirty cards in the background, updating remembered sets (per-region structures that track incoming references).
- **Concurrent Marking (SATB):** G1 uses Snapshot-At-The-Beginning. A pre-write barrier captures references being overwritten to avoid losing live objects.
- **Collection types:** Young GC (evacuates Eden+Survivor), Mixed GC (evacuates young + old regions with the most garbage, *garbage-first*), Full GC (last resort, compacts entire heap).

**ZGC:** sub-millisecond pauses regardless of heap size (8 MB to 16 TB). The core mechanism is **colored pointers**: metadata bits in 64-bit pointers. On every heap reference load, a **load barrier** checks the pointer "color" — if correct, fast path; if incorrect, the barrier "heals" the pointer (updates the address if the object was relocated). Generational ZGC adds store barriers for intergenerational tracking.

**Shenandoah:** also sub-millisecond, but via **forwarding pointers** instead of colored pointers. In early versions, a forwarding pointer was an extra word prepended to each object header. In modern Shenandoah (JDK 17+), the forwarding information is stored **inside the mark word** when the object is evacuated, eliminating the extra per-object overhead. During concurrent evacuation, application threads check the mark word and follow the redirect if the object has been relocated. Load barriers ensure this happens transparently. Advantage: supports compressed oops.

### Where it lives in the code

Each GC has its own subdirectory under `gc/`:

[`src/hotspot/share/gc/g1/`](https://github.com/openjdk/jdk/tree/jdk-25+33/src/hotspot/share/gc/g1), G1 complete

[`src/hotspot/share/gc/z/`](https://github.com/openjdk/jdk/tree/jdk-25+33/src/hotspot/share/gc/z), ZGC

[`src/hotspot/share/gc/shenandoah/`](https://github.com/openjdk/jdk/tree/jdk-25+33/src/hotspot/share/gc/shenandoah), Shenandoah

The BarrierSet framework, how each GC injects its barriers into the compilers:

[`src/hotspot/share/gc/shared/barrierSet.hpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/gc/shared/barrierSet.hpp#L46-L130)

G1 provides separate implementations for C1 and C2:

[`src/hotspot/share/gc/g1/c1/g1BarrierSetC1.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/gc/g1/c1/g1BarrierSetC1.cpp#L50-L100)

[`src/hotspot/share/gc/g1/c2/g1BarrierSetC2.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/gc/g1/c2/g1BarrierSetC2.cpp#L323-L370)

### Why this matters in practice

**Architectural impact of cross-generational references:** in G1, every reference write from an old-generation object to a young-generation object triggers a write barrier and eventually updates a remembered set. Consider two cache designs:

```
// Problematic: unbounded static cache lives in old gen forever.
// Every put() writes a reference from old gen to a young-gen value,
// triggering a write barrier and remembered set update.
// As the cache grows, GC refinement threads consume more CPU.
private static final Map<Long, UserSession> sessionCache = new ConcurrentHashMap<>();

public void onRequest(long userId) {
  sessionCache.put(userId, new UserSession(userId)); // old-to-young ref every time
}

// Better: bounded cache with eviction. Size is controlled,
// old entries are removed (reducing cross-gen references),
// and the GC has fewer remembered set entries to maintain.
private static final Cache<Long, UserSession> sessionCache = Caffeine.newBuilder()
  .maximumSize(10_000)
  .expireAfterAccess(Duration.ofMinutes(30))
  .build();
```

The symptom of excessive cross-generational references: the `-XX:MaxGCPauseMillis` target is met, but throughput drops because concurrent refinement threads are consuming CPU processing dirty cards. JFR events `G1MMU` and `GCPhasePause` break down where time is spent.

**Choosing a collector:** Serial for containers with < 256 MB heap and 1 vCPU. Parallel for batch jobs that tolerate pauses but need maximum throughput. G1 (default) for general-purpose workloads. ZGC or Shenandoah when tail latency requirements are strict regardless of heap size. The choice should be based on measured behavior, not assumptions. JFR recordings are the primary data source for this decision.

**How this compares to other runtime models.**

Most runtimes offer a single garbage collector. Go ships one concurrent, non-compacting, non-generational collector optimized for low latency..NET offers Workstation and Server GC modes with a generational architecture, but a narrower range of trade-offs. Runtimes without GC (Rust, C/C++) eliminate pause-time variability entirely. CPython uses reference counting with a cycle detector. The JVM is unique in offering five production collectors that cover the full spectrum from minimal-footprint (Serial) to sub-millisecond latency on terabyte heaps (ZGC, Shenandoah), selectable at startup without changing application code.

## 8\. Runtime: Threads and Synchronization

### What and why

The runtime subsystem manages the lifecycle of threads, synchronization between them, and the bridge to native code (JNI). It is the connective tissue that orchestrates the other subsystems.

### How it works: thread model

HotSpot uses a **1:1** model for platform threads: each Java `Thread` corresponds to exactly one OS native thread. **Virtual Threads** implement an **M:N** model: millions of virtual threads multiplexed over a pool of carrier threads (ForkJoinPool with work-stealing). The core mechanism is **continuations**, native stackful coroutines:

```
Virtual ThreadCarrier ThreadSchedulerVirtual ThreadCarrier ThreadScheduler#mermaid-1774232627453{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;fill:#ccc;}#mermaid-1774232627453 .error-icon{fill:#a44141;}#mermaid-1774232627453 .error-text{fill:#ddd;stroke:#ddd;}#mermaid-1774232627453 .edge-thickness-normal{stroke-width:2px;}#mermaid-1774232627453 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-1774232627453 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-1774232627453 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-1774232627453 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-1774232627453 .marker{fill:#6366f1;stroke:#6366f1;}#mermaid-1774232627453 .marker.cross{stroke:#6366f1;}#mermaid-1774232627453 svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;}#mermaid-1774232627453 .actor{stroke:#6366f1;fill:#1e293b;}#mermaid-1774232627453 text.actor>tspan{fill:lightgrey;stroke:none;}#mermaid-1774232627453 .actor-line{stroke:lightgrey;}#mermaid-1774232627453 .messageLine0{stroke-width:1.5;stroke-dasharray:none;stroke:lightgrey;}#mermaid-1774232627453 .messageLine1{stroke-width:1.5;stroke-dasharray:2,2;stroke:lightgrey;}#mermaid-1774232627453 #arrowhead path{fill:lightgrey;stroke:lightgrey;}#mermaid-1774232627453 .sequenceNumber{fill:black;}#mermaid-1774232627453 #sequencenumber{fill:lightgrey;}#mermaid-1774232627453 #crosshead path{fill:lightgrey;stroke:lightgrey;}#mermaid-1774232627453 .messageText{fill:lightgrey;stroke:none;}#mermaid-1774232627453 .labelBox{stroke:#6366f1;fill:#1e293b;}#mermaid-1774232627453 .labelText,#mermaid-1774232627453 .labelText>tspan{fill:lightgrey;stroke:none;}#mermaid-1774232627453 .loopText,#mermaid-1774232627453 .loopText>tspan{fill:lightgrey;stroke:none;}#mermaid-1774232627453 .loopLine{stroke-width:2px;stroke-dasharray:2,2;stroke:#6366f1;fill:#6366f1;}#mermaid-1774232627453 .note{stroke:hsl(180, 0%, 18.3529411765%);fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);}#mermaid-1774232627453 .noteText,#mermaid-1774232627453 .noteText>tspan{fill:rgb(183.8476190475, 181.5523809523, 181.5523809523);stroke:none;}#mermaid-1774232627453 .activation0{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#6366f1;}#mermaid-1774232627453 .activation1{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#6366f1;}#mermaid-1774232627453 .activation2{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#6366f1;}#mermaid-1774232627453 .actorPopupMenu{position:absolute;}#mermaid-1774232627453 .actorPopupMenuPanel{position:absolute;fill:#1e293b;box-shadow:0px 8px 16px 0px rgba(0,0,0,0.2);filter:drop-shadow(3px 5px 2px rgb(0 0 0 / 0.4));}#mermaid-1774232627453 .actor-man line{stroke:#6366f1;fill:#1e293b;}#mermaid-1774232627453 .actor-man circle,#mermaid-1774232627453 line{stroke:#6366f1;fill:#1e293b;stroke-width:2px;}#mermaid-1774232627453 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}Stack saved to heapReused for other VTsmount VTresume continuationexecute codehit blocking I/Ofreeze continuationVT unmountedmount another VT
```

Virtual thread stacks start at a few hundred bytes and grow dynamically on the heap (subject to GC), versus ~1 MB per platform thread.

### Synchronization evolution

| State | Tag Bits | Mechanism |
| --- | --- | --- |
| **Unlocked** | `01` | Normal state, no thread holds the lock |
| **Lightweight locked** | `00` | CAS flips tag bits. Header preserved in-place. Lock stack per-thread. |
| **Inflated (ObjectMonitor)** | `10` | Full runtime structure with wait queue, adaptive spinning, `Object.wait()/notify()` support |
| **Marked by GC** | `11` | Used during garbage collection |

```
#mermaid-1774232627556{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;fill:#ccc;}#mermaid-1774232627556 .error-icon{fill:#a44141;}#mermaid-1774232627556 .error-text{fill:#ddd;stroke:#ddd;}#mermaid-1774232627556 .edge-thickness-normal{stroke-width:2px;}#mermaid-1774232627556 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-1774232627556 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-1774232627556 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-1774232627556 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-1774232627556 .marker{fill:#6366f1;stroke:#6366f1;}#mermaid-1774232627556 .marker.cross{stroke:#6366f1;}#mermaid-1774232627556 svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;}#mermaid-1774232627556 .label{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;color:#ccc;}#mermaid-1774232627556 .cluster-label text{fill:#F9FFFE;}#mermaid-1774232627556 .cluster-label span,#mermaid-1774232627556 p{color:#F9FFFE;}#mermaid-1774232627556 .label text,#mermaid-1774232627556 span,#mermaid-1774232627556 p{fill:#ccc;color:#ccc;}#mermaid-1774232627556 .node rect,#mermaid-1774232627556 .node circle,#mermaid-1774232627556 .node ellipse,#mermaid-1774232627556 .node polygon,#mermaid-1774232627556 .node path{fill:#1e293b;stroke:#6366f1;stroke-width:1px;}#mermaid-1774232627556 .flowchart-label text{text-anchor:middle;}#mermaid-1774232627556 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-1774232627556 .node .label{text-align:center;}#mermaid-1774232627556 .node.clickable{cursor:pointer;}#mermaid-1774232627556 .arrowheadPath{fill:lightgrey;}#mermaid-1774232627556 .edgePath .path{stroke:#6366f1;stroke-width:2.0px;}#mermaid-1774232627556 .flowchart-link{stroke:#6366f1;fill:none;}#mermaid-1774232627556 .edgeLabel{background-color:hsl(0, 0%, 34.4117647059%);text-align:center;}#mermaid-1774232627556 .edgeLabel rect{opacity:0.5;background-color:hsl(0, 0%, 34.4117647059%);fill:hsl(0, 0%, 34.4117647059%);}#mermaid-1774232627556 .labelBkg{background-color:rgba(87.75, 87.75, 87.75, 0.5);}#mermaid-1774232627556 .cluster rect{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#8b5cf6;stroke-width:1px;}#mermaid-1774232627556 .cluster text{fill:#F9FFFE;}#mermaid-1774232627556 .cluster span,#mermaid-1774232627556 p{color:#F9FFFE;}#mermaid-1774232627556 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:12px;background:#1e293b;border:1px solid #8b5cf6;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-1774232627556 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#ccc;}#mermaid-1774232627556 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}CAS flip bitscontention detectedasync deflationUnlocked: 01Lightweight: 00Inflated: 10
```

When there is contention (multiple threads competing for the same lock), the lock is **inflated** to an `ObjectMonitor`, a full runtime structure that manages: the owning thread, recursion level, entry queue (with adaptive spinning before OS-level blocking), and wait set (threads in `Object.wait()`). Deflation occurs asynchronously when no thread references the monitor.

### Where it lives in the code

Threading:

[`src/hotspot/share/runtime/javaThread.hpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/runtime/javaThread.hpp#L84-L200), JavaThread

[`src/java.base/share/classes/java/lang/VirtualThread.java`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/java.base/share/classes/java/lang/VirtualThread.java#L63-L150), Virtual Threads (Java side)

[`src/hotspot/share/runtime/continuationFreezeThaw.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/runtime/continuationFreezeThaw.cpp#L207-L270), freeze (capture stack) and thaw (resume) of continuations

Synchronization:

[`src/hotspot/share/runtime/synchronizer.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/runtime/synchronizer.cpp#L511-L560), monitorenter/monitorexit dispatch

[`src/hotspot/share/runtime/objectMonitor.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/runtime/objectMonitor.cpp#L486-L530), ObjectMonitor (fat lock)

[`src/hotspot/share/runtime/lightweightSynchronizer.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/runtime/lightweightSynchronizer.cpp#L659-L700), lightweight locking

### Why this matters in practice

**Virtual threads change the architecture of I/O-bound services.** The one-thread-per-request model that was impractical with platform threads (10,000 threads = 10 GB of stack memory) is now the recommended approach. But the benefit only materializes if blocking operations allow the virtual thread to unmount from the carrier. Consider:

```
// Historically PINNED the carrier thread. Before JEP 491, the synchronized
// block prevented the virtual thread from unmounting when the I/O call blocked.
// JEP 491 addressed this by reworking monitor ownership tracking, but older
// JDK versions and some edge cases (native frames on stack) can still pin.
public synchronized String fetchData(String url) {
  return httpClient.send(request, BodyHandlers.ofString()).body();
}

// Continuation-aware alternative. ReentrantLock has always supported
// unmounting: when the virtual thread blocks on I/O, it unmounts from
// the carrier, freeing it for other virtual threads.
private final ReentrantLock lock = new ReentrantLock();

public String fetchData(String url) {
  lock.lock();
  try {
    return httpClient.send(request, BodyHandlers.ofString()).body();
  } finally {
    lock.unlock();
  }
}
```

On JDK versions before [JEP 491](https://openjdk.org/jeps/491), `synchronized` with blocking I/O is a significant scalability bottleneck for virtual threads. On newer versions the problem is largely resolved, but `ReentrantLock` remains the safer choice in libraries that need to support multiple JDK versions. The diagnostic: JFR event `jdk.VirtualThreadPinned` identifies pinning occurrences.

**Lock contention is an architecture problem, not a tuning problem.**

If your application spends significant time in inflated monitors, the answer is rarely to tune lock parameters. The answer is to redesign the data access pattern: reduce critical section duration, use lock striping, switch to `java.util.concurrent` structures, or eliminate shared mutable state entirely. JFR events `jdk.JavaMonitorWait` and `jdk.JavaMonitorEnter` quantify the cost.

**How this compares to other runtime models.**

Go pioneered M:N scheduling for mainstream use with goroutines (2012). Erlang/BEAM has run lightweight processes with preemptive scheduling since the 1980s. The JVM arrived later with virtual threads in JDK 21 (2023), but with a critical advantage: ecosystem integration. Virtual threads work transparently with the entire existing Java library surface (JDBC drivers, HTTP clients, logging frameworks, serialization) without requiring new APIs or concurrency patterns. Goroutines require channel-based communication and a different programming model. Erlang requires the OTP actor model. Virtual threads bring M:N scheduling to the imperative, thread-per-request style that most enterprise Java code already uses.

On the synchronization side, Rust eliminates data races at compile time through ownership and borrowing rules, a fundamentally different approach that trades runtime flexibility for compile-time safety. Go uses a simpler mutex model without the lightweight/inflated escalation that the JVM performs.

## 9\. Safepoints: The Universal Coordination Mechanism

### What and why

Several JVM operations require all Java threads to be in a safe and predictable state: STW GC phases, deoptimization, class redefinition. The mechanism that coordinates this is **safepoints**.

### How it works

The mechanism is cooperative via **page-trap polling**:

```
Polling PageThread 2Thread 1VMThreadPolling PageThread 2Thread 1VMThread#mermaid-1774232627630{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;fill:#ccc;}#mermaid-1774232627630 .error-icon{fill:#a44141;}#mermaid-1774232627630 .error-text{fill:#ddd;stroke:#ddd;}#mermaid-1774232627630 .edge-thickness-normal{stroke-width:2px;}#mermaid-1774232627630 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-1774232627630 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-1774232627630 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-1774232627630 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-1774232627630 .marker{fill:#6366f1;stroke:#6366f1;}#mermaid-1774232627630 .marker.cross{stroke:#6366f1;}#mermaid-1774232627630 svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;}#mermaid-1774232627630 .actor{stroke:#6366f1;fill:#1e293b;}#mermaid-1774232627630 text.actor>tspan{fill:lightgrey;stroke:none;}#mermaid-1774232627630 .actor-line{stroke:lightgrey;}#mermaid-1774232627630 .messageLine0{stroke-width:1.5;stroke-dasharray:none;stroke:lightgrey;}#mermaid-1774232627630 .messageLine1{stroke-width:1.5;stroke-dasharray:2,2;stroke:lightgrey;}#mermaid-1774232627630 #arrowhead path{fill:lightgrey;stroke:lightgrey;}#mermaid-1774232627630 .sequenceNumber{fill:black;}#mermaid-1774232627630 #sequencenumber{fill:lightgrey;}#mermaid-1774232627630 #crosshead path{fill:lightgrey;stroke:lightgrey;}#mermaid-1774232627630 .messageText{fill:lightgrey;stroke:none;}#mermaid-1774232627630 .labelBox{stroke:#6366f1;fill:#1e293b;}#mermaid-1774232627630 .labelText,#mermaid-1774232627630 .labelText>tspan{fill:lightgrey;stroke:none;}#mermaid-1774232627630 .loopText,#mermaid-1774232627630 .loopText>tspan{fill:lightgrey;stroke:none;}#mermaid-1774232627630 .loopLine{stroke-width:2px;stroke-dasharray:2,2;stroke:#6366f1;fill:#6366f1;}#mermaid-1774232627630 .note{stroke:hsl(180, 0%, 18.3529411765%);fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);}#mermaid-1774232627630 .noteText,#mermaid-1774232627630 .noteText>tspan{fill:rgb(183.8476190475, 181.5523809523, 181.5523809523);stroke:none;}#mermaid-1774232627630 .activation0{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#6366f1;}#mermaid-1774232627630 .activation1{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#6366f1;}#mermaid-1774232627630 .activation2{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#6366f1;}#mermaid-1774232627630 .actorPopupMenu{position:absolute;}#mermaid-1774232627630 .actorPopupMenuPanel{position:absolute;fill:#1e293b;box-shadow:0px 8px 16px 0px rgba(0,0,0,0.2);filter:drop-shadow(3px 5px 2px rgb(0 0 0 / 0.4));}#mermaid-1774232627630 .actor-man line{stroke:#6366f1;fill:#1e293b;}#mermaid-1774232627630 .actor-man circle,#mermaid-1774232627630 line{stroke:#6366f1;fill:#1e293b;stroke-width:2px;}#mermaid-1774232627630 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}Page marked unreadablemprotect PROT_NONEload pollSIGSEGVsignal handler enters safepointload pollSIGSEGVsignal handler enters safepointall threads safeexecute operationmprotect PROT_READresumeresume
```

Compiled and interpreted code contain periodic polls: a load from the polling page. During normal execution, this load hits the L1 cache (~1 cycle, negligible cost). When the VM needs a safepoint, it marks the page as unreadable. The next poll triggers a page fault caught by the signal handler. For the interpreter, the JVM swaps the dispatch table for a variant with safepoint checks.

**Thread-Local Handshakes** allow per-thread operations without a global safepoint. Instead of marking a shared polling page, the VM targets individual threads through a per-thread polling mechanism (a poll word in the `JavaThread` structure). This enables operations like stack trace sampling or lock revocation on a single thread without pausing the entire application.

### Where it lives in the code

[`src/hotspot/share/runtime/safepoint.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/runtime/safepoint.cpp#L329-L450)

[`src/hotspot/share/runtime/safepointMechanism.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/runtime/safepointMechanism.cpp#L135-L180)

[`src/hotspot/share/runtime/handshake.cpp`](https://github.com/openjdk/jdk/blob/jdk-25+33/src/hotspot/share/runtime/handshake.cpp#L49-L100), thread-local handshakes

### Why this matters in practice

**Safepoint pauses and GC pauses are different things.**

Confusing them is one of the most common troubleshooting mistakes. A GC pause is one *reason* for a safepoint, but deoptimization, class redefinition, thread dumps, and biased lock revocation are others. The **time-to-safepoint (TTSP)** can be significant: a thread inside a counted loop that the JIT optimized to remove safepoint polls can delay the entire safepoint by hundreds of milliseconds. The symptom: GC logs show short GC pauses, but application latency shows long pauses. The diagnostic: `-Xlog:safepoint` shows TTSP separately from operation time. `-XX:+SafepointTimeout -XX:SafepointTimeoutDelay=2000` identifies threads that take too long to reach safepoint.

## 10\. How the Subsystems Connect

The most important insight about HotSpot is that performance emerges not from individual components, but from their coordinated interactions.

### Subsystem interaction map

| Source | Target | Interaction |
| --- | --- | --- |
| **Interpreter / C1** | **C2 JIT** | Profiling data in MethodData feeds speculative optimizations |
| **C2 JIT** | **GC** | Write/load barriers injected via BarrierSet. OOP maps tell GC where references are in compiled code |
| **Class Loading** | **C2 JIT** | New subclass loaded invalidates class hierarchy dependency, triggers deoptimization |
| **C2 JIT** | **Interpreter** | Deoptimization reverts compiled frames to interpreted frames |
| **Safepoints** | **GC** | Coordinates STW phases. Ensures all roots are mapped |
| **Safepoints** | **JIT** | Coordinates bulk deoptimization when dependencies are invalidated |
| **Runtime (JVMTI)** | **Class Loading** | Class redefinition is a Runtime operation (via JVMTI agent) that uses a safepoint and modifies class metadata in the Class Loading subsystem |
| **Runtime** | **All** | VMThread executes safepoint operations. CompileBroker manages compilation. FJP schedules virtual threads |
| **JFR / JVMTI** | **All** | Observes events from every subsystem with minimal overhead |

The interactions form two distinct cycles: the **compilation cycle** (how code gets faster) and the **runtime coordination cycle** (how subsystems stay in sync).

### The compilation cycle

```
#mermaid-1774232627688{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;fill:#ccc;}#mermaid-1774232627688 .error-icon{fill:#a44141;}#mermaid-1774232627688 .error-text{fill:#ddd;stroke:#ddd;}#mermaid-1774232627688 .edge-thickness-normal{stroke-width:2px;}#mermaid-1774232627688 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-1774232627688 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-1774232627688 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-1774232627688 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-1774232627688 .marker{fill:#6366f1;stroke:#6366f1;}#mermaid-1774232627688 .marker.cross{stroke:#6366f1;}#mermaid-1774232627688 svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;}#mermaid-1774232627688 .label{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;color:#ccc;}#mermaid-1774232627688 .cluster-label text{fill:#F9FFFE;}#mermaid-1774232627688 .cluster-label span,#mermaid-1774232627688 p{color:#F9FFFE;}#mermaid-1774232627688 .label text,#mermaid-1774232627688 span,#mermaid-1774232627688 p{fill:#ccc;color:#ccc;}#mermaid-1774232627688 .node rect,#mermaid-1774232627688 .node circle,#mermaid-1774232627688 .node ellipse,#mermaid-1774232627688 .node polygon,#mermaid-1774232627688 .node path{fill:#1e293b;stroke:#6366f1;stroke-width:1px;}#mermaid-1774232627688 .flowchart-label text{text-anchor:middle;}#mermaid-1774232627688 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-1774232627688 .node .label{text-align:center;}#mermaid-1774232627688 .node.clickable{cursor:pointer;}#mermaid-1774232627688 .arrowheadPath{fill:lightgrey;}#mermaid-1774232627688 .edgePath .path{stroke:#6366f1;stroke-width:2.0px;}#mermaid-1774232627688 .flowchart-link{stroke:#6366f1;fill:none;}#mermaid-1774232627688 .edgeLabel{background-color:hsl(0, 0%, 34.4117647059%);text-align:center;}#mermaid-1774232627688 .edgeLabel rect{opacity:0.5;background-color:hsl(0, 0%, 34.4117647059%);fill:hsl(0, 0%, 34.4117647059%);}#mermaid-1774232627688 .labelBkg{background-color:rgba(87.75, 87.75, 87.75, 0.5);}#mermaid-1774232627688 .cluster rect{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#8b5cf6;stroke-width:1px;}#mermaid-1774232627688 .cluster text{fill:#F9FFFE;}#mermaid-1774232627688 .cluster span,#mermaid-1774232627688 p{color:#F9FFFE;}#mermaid-1774232627688 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:12px;background:#1e293b;border:1px solid #8b5cf6;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-1774232627688 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#ccc;}#mermaid-1774232627688 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}profiling databarriers + OOP mapsInterpreter / C1C2 JITGarbage Collector
```

The Interpreter and C1 collect profiling data (MethodData) that feeds C2's speculative optimizations. C2 generates write/load barriers for the active GC and OOP maps that tell the GC where references live in compiled frames.

### The invalidation cycle

```
#mermaid-1774232627751{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;fill:#ccc;}#mermaid-1774232627751 .error-icon{fill:#a44141;}#mermaid-1774232627751 .error-text{fill:#ddd;stroke:#ddd;}#mermaid-1774232627751 .edge-thickness-normal{stroke-width:2px;}#mermaid-1774232627751 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-1774232627751 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-1774232627751 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-1774232627751 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-1774232627751 .marker{fill:#6366f1;stroke:#6366f1;}#mermaid-1774232627751 .marker.cross{stroke:#6366f1;}#mermaid-1774232627751 svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:16px;}#mermaid-1774232627751 .label{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;color:#ccc;}#mermaid-1774232627751 .cluster-label text{fill:#F9FFFE;}#mermaid-1774232627751 .cluster-label span,#mermaid-1774232627751 p{color:#F9FFFE;}#mermaid-1774232627751 .label text,#mermaid-1774232627751 span,#mermaid-1774232627751 p{fill:#ccc;color:#ccc;}#mermaid-1774232627751 .node rect,#mermaid-1774232627751 .node circle,#mermaid-1774232627751 .node ellipse,#mermaid-1774232627751 .node polygon,#mermaid-1774232627751 .node path{fill:#1e293b;stroke:#6366f1;stroke-width:1px;}#mermaid-1774232627751 .flowchart-label text{text-anchor:middle;}#mermaid-1774232627751 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-1774232627751 .node .label{text-align:center;}#mermaid-1774232627751 .node.clickable{cursor:pointer;}#mermaid-1774232627751 .arrowheadPath{fill:lightgrey;}#mermaid-1774232627751 .edgePath .path{stroke:#6366f1;stroke-width:2.0px;}#mermaid-1774232627751 .flowchart-link{stroke:#6366f1;fill:none;}#mermaid-1774232627751 .edgeLabel{background-color:hsl(0, 0%, 34.4117647059%);text-align:center;}#mermaid-1774232627751 .edgeLabel rect{opacity:0.5;background-color:hsl(0, 0%, 34.4117647059%);fill:hsl(0, 0%, 34.4117647059%);}#mermaid-1774232627751 .labelBkg{background-color:rgba(87.75, 87.75, 87.75, 0.5);}#mermaid-1774232627751 .cluster rect{fill:hsl(217.2413793103, 32.5842696629%, 33.4509803922%);stroke:#8b5cf6;stroke-width:1px;}#mermaid-1774232627751 .cluster text{fill:#F9FFFE;}#mermaid-1774232627751 .cluster span,#mermaid-1774232627751 p{color:#F9FFFE;}#mermaid-1774232627751 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;font-size:12px;background:#1e293b;border:1px solid #8b5cf6;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-1774232627751 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#ccc;}#mermaid-1774232627751 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}invalidates dependenciesdeoptimizationnew profiling dataClass LoadingC2 JITInterpreter
```

When a new class is loaded that breaks a C2 assumption (e.g., a new subclass appears), the dependency system marks affected compiled methods as invalid. Deoptimization reverts them to the interpreter, which collects fresh profiling data, and the cycle restarts.

### The orchestration layer

The Runtime subsystem (VMThread, CompileBroker, ForkJoinPool scheduler) sits above all of this and orchestrates through **safepoints**, the cooperative mechanism that pauses threads when a stop-the-world operation is needed (GC STW phases, bulk deoptimization, class redefinition).

### The complete lifecycle of a hot method

1. **Class Loading** loads the class and resolves dependencies in the SystemDictionary.
2. **Interpreter** executes the method, collecting data in the MethodData.
3. **C1** compiles with full profiling (Tier 3), inserting GC barriers and OOP maps. Code goes to the code cache (profiled segment).
4. While executing, C1 code continues collecting rich data in the MethodData.
5. **C2** compiles with aggressive optimizations (Tier 4) using MethodData: devirtualization, inlining, escape analysis, vectorization. Registers dependencies. Inserts GC barriers and generates OOP maps.
6. C2 code goes to the code cache (non-profiled segment). Previous C1 code becomes zombie.
7. If a new class invalidates a dependency, **deoptimization** via safepoint brings execution back to step 2.
8. The cycle repeats with updated profiling.

## 11\. Where the JVM Pays the Price

The JVM's adaptive architecture delivers significant advantages in sustained workloads. But it comes with trade-offs that other runtime models do not pay. Understanding these trade-offs, and the work the OpenJDK community is doing to address them, is essential for making informed technology decisions.

### Startup time

**The cost.** AOT-compiled runtimes deliver running processes in single-digit milliseconds. The JVM needs to load classes, verify bytecode, interpret, and then JIT-compile. In serverless environments, container orchestration with aggressive scale-out, or CLI tools, this startup cost compounds with every cold start.

**The community response.** CDS and AppCDS (Class Data Sharing) allow multiple JVM instances to share pre-processed class metadata, cutting startup time significantly. [Project CRaC](https://openjdk.org/projects/crac/) (Coordinated Restore at Checkpoint) takes a snapshot of a fully warmed JVM process and restores it in milliseconds, preserving JIT-compiled code. [Project Leyden](https://openjdk.org/projects/leyden/) aims to "condense" the JVM's startup phases by shifting work ahead of time. GraalVM Native Image compiles Java to a native binary (AOT), trading the JIT for instant startup.

### Memory footprint

**The cost.** The JVM loads a full runtime before any application code runs. A minimal Java process consumes tens of megabytes. Comparable programs in Go, Rust, or.NET trimmed/AOT start with single-digit megabytes. In containerized environments where thousands of instances run simultaneously, this per-instance overhead multiplies.

**The community response.** Project Lilliput ([JEP 450](https://openjdk.org/jeps/450) / [519](https://openjdk.org/jeps/519)) reduces object headers from 12 to 8 bytes, saving meaningful heap space in object-heavy workloads. Compact Strings (since JDK 9) store Latin-1 strings in one byte per character instead of two. `jlink` builds custom runtime images containing only the modules the application needs. Project Leyden will reduce the amount of metadata loaded at startup.

### Warmup latency

**The cost.** Until the JIT reaches Tier 4 (C2), the application runs with suboptimal code. The first seconds of a process execute interpreted bytecode or C1-compiled code that is correct but not peak-optimized. In environments with frequent deployments or aggressive horizontal scaling, applications may spend a meaningful fraction of their lifetime below peak performance.

**The community response.** Tiered compilation delivers reasonable C1-compiled code within the first seconds. CRaC restores a fully warmed process from a checkpoint, bypassing the warmup phase entirely. Profile-guided AOT compilation is under development via Project Leyden, which would allow the JVM to use profiling data from previous runs to produce better initial code.

### Operational complexity

**The cost.** GC selection, heap sizing, code cache tuning, classpath vs modulepath, JIT flags. The JVM has a large operational surface. Runtimes like Go made a deliberate choice of simplicity: one garbage collector, no tuning flags, a single static binary.

**The community response.** JVM ergonomics have improved steadily since JDK 8+. The JVM auto-configures heap size, GC selection (G1 by default), and compilation thresholds based on the detected environment. JFR (Java Flight Recorder) is built into the runtime with negligible overhead, providing a diagnostic system that eliminates guesswork. The trend in modern JDK releases is fewer flags needed, not more. The default configuration is increasingly sufficient for most workloads.

## 12\. Conclusion

This continuous feedback loop between interpretation, profiling, compilation, and deoptimization is what defines the JVM's adaptive model. No single subsystem is responsible for peak performance. It emerges from the interaction between all of them: the interpreter collects data, the JIT uses it to speculate, the GC cooperates through barriers and OOP maps, and safepoints keep everything synchronized.

This is why the JVM remains such a strong choice in enterprise environments. In applications that run for hours, days, or months under sustained load, the adaptive model delivers performance that improves over time, shaped by the actual production workload rather than assumptions made at build time. Five garbage collectors, virtual threads, speculative devirtualization, and escape analysis are not features in isolation. They are parts of a system designed to extract maximum performance from long-running, high-concurrency workloads.

The JVM is not the right tool for every scenario. Its startup cost, memory footprint, and warmup latency are real trade-offs that matter in serverless functions, CLI tools, and resource-constrained environments. But the OpenJDK community is actively closing those gaps, and the engineering momentum behind projects like CRaC, Leyden, and Lilliput shows that the platform is not standing still.

Understanding how these subsystems work together does not just satisfy curiosity. It changes the way you design applications, diagnose production issues, and make technology decisions. That is the goal of this study: not to prove that the JVM is the best runtime, but to give you the depth of understanding to know when it is, and why.

## 13\. References

**Code reference:** All source code references and line anchors in this study point to tag [jdk-25+33](https://github.com/openjdk/jdk/tree/jdk-25+33) of the [openjdk/jdk](https://github.com/openjdk/jdk) repository on GitHub.

### Official Documentation

- [The Java Virtual Machine Specification, Java SE 21 Edition](https://docs.oracle.com/javase/specs/jvms/se21/html/)
- [HotSpot Runtime Overview](https://openjdk.org/groups/hotspot/docs/RuntimeOverview.html)
- [HotSpot Glossary of Terms](https://openjdk.org/groups/hotspot/docs/HotSpotGlossary.html)
- [Inside.java](https://inside.java/), Official Java team blog

### Repository

- [github.com/openjdk/jdk](https://github.com/openjdk/jdk), Full source code
- [DeepWiki, OpenJDK/JDK](https://deepwiki.com/openjdk/jdk), Documented repository navigation

### OpenJDK Projects

- [Project CRaC](https://openjdk.org/projects/crac/), Coordinated Restore at Checkpoint
- [Project Leyden](https://openjdk.org/projects/leyden/), Condensing the JVM startup
