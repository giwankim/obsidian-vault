---
title: "What happens when a GPU reads memory"
source: "https://blog.doubleword.ai/what-happens-when-a-gpu-reads-memory"
author:
  - "[[Fergus Finn]]"
published: 2026-08-13
created: 2026-08-22
description: "Following an LDG.E SASS instruction through the hardware units in an RTX 4090."
tags:
  - "clippings"
---

> [!summary]
> Follows a single `LDG.E` global-load SASS instruction through the hardware of an RTX 4090: warp scheduler, address coalescer, L1, TLB, crossbar, one of thirty-six L2 slices, memory controller, and finally a DRAM row activate plus four column reads. Because NVIDIA documents almost none of this path, the author recovers it empirically — L1 and L2 set functions, the L2 slice hash, and DRAM row geometry — via timing experiments and eviction sets, with the probe methodology in an appendix. A follow-up to the same author's post on running a GPU kernel.

Fergus Finn

Founder & Member of Technical Staff, Doubleword

Our [previous post](https://fergusfinn.com/blog/what-happens-when-you-run-a-gpu-kernel/) followed a vector-add kernel — `c[i] = a[i] + b[i]`, one thread per float — from `nvcc` down to the warps. We went into a lot of detail on how the kernel was launched, but we also left a lot out.

This time, we’re going to address our omissions, and follow the path the critical SASS instruction (a global load) takes through the hardware — in this case, since it’s under my desk, an [RTX 4090](https://www.nvidia.com/en-gb/geforce/graphics-cards/40-series/rtx-4090/). Little of the detail of this path is documented by NVIDIA, at least not to the level that we’d like, so we’ll determine it by running timing experiments on the hardware itself.

The CUDA kernel we are investigating has two lines in its function body:

```
__global__ void vadd(const float* a, const float* b, float* c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) c[i] = a[i] + b[i];
}
```

If you inspect the compiled SASS, you’ll see the instructions that power those lines:

```
/*0080*/  IMAD.WIDE R4, R6, R7, c[0x0][0x168] ;   // &b[i]
/*00a0*/  LDG.E R4, [R4.64] ;                     // b[i]
```

They serve to load the elements of the vector `b` from global memory into a register, where they can be added to the elements of `a` to perform the kernel. One `LDG.E` asks for four bytes in each of 32 lanes. Serving it takes four 32-byte sectors, one cache line, one address translation, a crossbar crossing, one of thirty-six L2 slices, and, when it misses everywhere, an activate and four column reads at a DRAM chip. It’s this journey of the instruction through the hardware, and back, that we’ll try to follow.

To set the scene: our warp lives on one of the SM’s four **sub-partitions**, alongside eleven other resident warps. Each cycle the sub-partition’s scheduler picks one warp that is eligible, and issues its next instruction across the 32 lanes at once. Our warp wins twice: once for the `IMAD.WIDE`, and a few cycles later (the addresses now sitting in `R4` and `R5`) for the `LDG`.

Our story starts with the `LDG`.

warp

coalescer

L1

15 ns

TLB

crossbar

L2

127 ns

controller

DRAM

255 ns

SM

die

board

## From the warp to the L1 cache

Let’s start with the instruction. `LDG.E R4, [R4.64]` is a global load of 32 bits from the 64-bit *address* stored in registers `R4` and `R5`, storing the result in register `R4`. To load the data itself, we first must go get that address from those registers.

One row of the register file holds `R4` for all 32 lanes at once. Another holds `R5`. The warp reads both entries, yielding 256 bytes read as 32 distinct 64-bit addresses, one address per lane.

**What the register retrieve costs**

The address read adds at most one cycle. A shared-memory load taking its address from a register takes 24 cycles from issue to first use, and the same load with the address as an immediate takes 23. (`LDG` can’t take an immediate).

With all of its addresses resolved, the instruction issues to the **load/store** unit (LSU). The LSU takes the instruction and its operand addresses, does some address arithmetic (if necessary), and sends on the **opcode** (‘load these addresses’, in binary), a 32-bit mask of active lanes, its computed addresses, and the number of the register the result belongs in. The next destination is the **coalescer**.

Each `LDG.E` instruction in each lane asks for 4 bytes, but our next destination, the **L1 cache**, is addressed in 32 byte **sectors**. The coalescer’s job is to figure out the minimal number of L1 sectors it needs to retrieve to service our 4-byte requests.

The coalescer figures out that it ought to emit 4 contiguous sector requests, for the 128 bytes the warp has asked for [^1].

### Entering the L1 cache

warp

coalescer

L1

15 ns

TLB

crossbar

L2

127 ns

controller

DRAM

255 ns

SM

die

board

The request for four contiguous 32-byte sectors is sent onto the **L1 cache**.

The L1 cache’s unit of organization is still less granular: 128 byte **lines**. Our 4 contiguous sectors represent the 4 parts of a single line, so a request gets made to L1 for that cache line.

First, we have to determine whether that line is already in the cache. The cache is divided into groups of slots called **sets**, and a line’s address determines which set it belongs to. A set on this card holds four slots [^2], and each carries a **tag** identifying the line in it. The lookup compares all four against the tag of the line it wants. The address it uses is the **virtual** address used in the program [^3]. The set in which a line lands is generated from the line’s virtual address by a hashing scheme, which you can reverse engineer [^4].

If one of the four tags matches and the sectors we want are in that slot, the data is read out and the load is done [^5]. Because we’re loading all of our data for the first time, our request misses, and must descend further into the memory system.

**How much does an L1 hit cost**

An L1 hit returns in about 15.4 ns — 40 cycles. The number comes from one thread chasing a dependent chain through a random permutation of L1-resident lines, with [the latency chase](#setup).

## Looking for L2: translation

warp

coalescer

L1

15 ns

TLB

crossbar

L2

127 ns

controller

DRAM

255 ns

SM

die

board

**Virtual memory** puts one level of indirection between the addresses a program names and the addresses at which the hardware stores data. The program gets a contiguous space of its own, and the hardware lays that space out across physical pages however it likes. **Translation** is the map between them.

The L1 we just spoke to was **virtually addressed**, so we didn’t need to concern ourselves with translation. Past this point, we have to start speaking the hardware’s language — an L1 miss has to be translated before it leaves the SM [^6].

The actual mapping between physical and virtual addresses is established at allocation in the driver: when `b` was allocated, the driver picked physical (2MiB) pages for it and wrote page tables into VRAM recording the assignment [^7].

The translation unit takes in a virtual address and returns a physical address, according to those tables. The SM keeps its sixteen most recent translations in a TLB, shared across warps [^8]. The very first load will miss in this TLB.

**What translation costs**

We can’t see any cost to hitting the TLB in any of the probes we have. Misses cost about 4.4 ns — eleven cycles. The same refill cost holds within 0.1 ns across all the pages this chip can map, and from any SM, so the next level of the translation cache is universal, and very cheap.

Once translation has been performed, what leaves is one request per 128-byte line: now with the line’s **physical** address, along with a mask of the sectors we want from it. Ours is a single request with all four sectors marked [^9].

The request proceeds out of the SM, across the **crossbar** to the **L2 cache**.

## Lost in L2

warp

coalescer

L1

15 ns

TLB

crossbar

L2

127 ns

controller

DRAM

255 ns

SM

die

board

The request runs across the crossbar to one of 36 2 MiB L2 slices, picked by a somewhat complex function of its physical address [^10]. Any SM can hit any slice. All slices can serve in parallel, so the aggregate bandwidth is 36x that of a single slice.

Inside a slice, the structure is of the same kind as the L1. Each slice holds 1024 **sets**. The set to which a line belongs is picked by a hash of the line’s physical address. Each set now contains 16 slots: the slices are individually **16 way set-associative** [^11]. The lines are 128 bytes in size, the same as in L1.

The line is not present in L2, since we’ve not fetched it before. Each slice falls through to one of 12 memory controllers — 3 slices per controller. Each memory controller’s job is to speak to a single [**GDDR6X**](https://en.wikipedia.org/wiki/GDDR_SDRAM) DRAM chip [^12]. Our request gets handed over to that controller.

**What does this cost**

An L2 hit costs about 127 ns — some 330 cycles. Each SM can hand the crossbar up to two line-requests per cycle, and the 36 slices serve independently. The exit-port counter is `l1tex__m_l1tex2xbar_req_cycles_active`.

## Found in DRAM

warp

coalescer

L1

15 ns

TLB

crossbar

L2

127 ns

controller

DRAM

255 ns

SM

die

board

The memory controller’s job is to load the data from its 2 GiB DRAM chip. It does so by issuing commands to DRAM over a bus.

The DRAM is divided into two separate buses the controller drives independently, called **channels**. On each channel sit 16 **banks**: two-dimensional arrays of memory cells. A bank consists of 65,536 **rows**. The hardware can open one row at a time (an **activate**, expensive), and then return any 32-byte **columns** from that row (a **read**, cheap while the row is open).

GDDR6X

<svg viewBox="0 -26 680 384" xmlns="http://www.w3.org/2000/svg"><g><line x1="111.5" y1="16" x2="111.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="116.5" y1="16" x2="116.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="121.5" y1="16" x2="121.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="126.5" y1="16" x2="126.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="131.5" y1="16" x2="131.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="136.5" y1="16" x2="136.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="141.5" y1="16" x2="141.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="146.5" y1="16" x2="146.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="151.5" y1="16" x2="151.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="156.5" y1="16" x2="156.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="161.5" y1="16" x2="161.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="166.5" y1="16" x2="166.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="171.5" y1="16" x2="171.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="176.5" y1="16" x2="176.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="181.5" y1="16" x2="181.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="186.5" y1="16" x2="186.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="200.5" y1="16" x2="200.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="204.5" y1="16" x2="204.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="208.5" y1="16" x2="208.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="212.5" y1="16" x2="212.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="216.5" y1="16" x2="216.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="220.5" y1="16" x2="220.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="224.5" y1="16" x2="224.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="228.5" y1="16" x2="228.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="232.5" y1="16" x2="232.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="236.5" y1="16" x2="236.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line></g><g><line x1="443.5" y1="16" x2="443.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="448.5" y1="16" x2="448.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="453.5" y1="16" x2="453.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="458.5" y1="16" x2="458.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="463.5" y1="16" x2="463.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="468.5" y1="16" x2="468.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="473.5" y1="16" x2="473.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="478.5" y1="16" x2="478.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="483.5" y1="16" x2="483.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="488.5" y1="16" x2="488.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="493.5" y1="16" x2="493.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="498.5" y1="16" x2="498.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="503.5" y1="16" x2="503.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="508.5" y1="16" x2="508.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="513.5" y1="16" x2="513.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="518.5" y1="16" x2="518.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="532.5" y1="16" x2="532.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="536.5" y1="16" x2="536.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="540.5" y1="16" x2="540.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="544.5" y1="16" x2="544.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="548.5" y1="16" x2="548.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="552.5" y1="16" x2="552.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="556.5" y1="16" x2="556.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="560.5" y1="16" x2="560.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="564.5" y1="16" x2="564.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line><line x1="568.5" y1="16" x2="568.5" y2="-20" stroke="currentColor" stroke-opacity="0.2"></line></g><polygon points="99,72 133,72 676,124 4,124" fill="none" stroke="currentColor"></polygon><line x1="99" y1="72" x2="4" y2="124" stroke="currentColor" stroke-opacity="0.2"></line><line x1="133" y1="72" x2="676" y2="124" stroke="currentColor" stroke-opacity="0.2"></line><rect x="4" y="6" width="672" height="84" rx="10" fill="none" stroke="currentColor"></rect><g><rect x="14" y="16" width="320" height="64" rx="6" fill="none" stroke="currentColor"></rect><text x="22" y="32" fill="currentColor">channel 0 · 1 GiB</text> <rect x="22" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="60.5" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="99" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="137.5" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="176" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="214.5" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="253" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="291.5" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="22" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="60.5" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="99" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="137.5" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="176" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="214.5" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="253" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="291.5" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect></g><g><rect x="346" y="16" width="320" height="64" rx="6" fill="none" stroke="currentColor"></rect><text x="354" y="32" fill="currentColor">channel 1 · 1 GiB</text> <rect x="354" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="392.5" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="431" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="469.5" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="508" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="546.5" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="585" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="623.5" y="40" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="354" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="392.5" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="431" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="469.5" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="508" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="546.5" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="585" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect><rect x="623.5" y="58" width="34" height="14" rx="2" fill="none" stroke="currentColor"></rect></g><rect x="4" y="124" width="672" height="126" rx="8" fill="none" stroke="currentColor"></rect><text x="14" y="142" fill="currentColor">one bank · 65,536 rows of 1 KiB</text> <rect x="90" y="150" width="500" height="9" rx="1.5" fill="none" stroke="currentColor"></rect><rect x="90" y="163" width="500" height="9" rx="1.5" fill="none" stroke="currentColor"></rect><rect x="90" y="176" width="500" height="9" rx="1.5" fill="none" stroke="currentColor"></rect><text x="340" y="197" text-anchor="middle" fill="currentColor">⋯</text> <rect x="90" y="204" width="500" height="9" rx="1.5" fill="none" stroke="currentColor"></rect><rect x="90" y="216" width="500" height="10" rx="1.5" fill="none" stroke="currentColor"></rect><rect x="90" y="230" width="500" height="9" rx="1.5" fill="none" stroke="currentColor"></rect><polygon points="90,226 590,226 676,280 4,280" fill="none" stroke="currentColor"></polygon><line x1="90" y1="226" x2="4" y2="280" stroke="currentColor" stroke-opacity="0.2"></line><line x1="590" y1="226" x2="676" y2="280" stroke="currentColor" stroke-opacity="0.2"></line><rect x="4" y="280" width="672" height="72" rx="8" fill="none" stroke="currentColor"></rect><text x="14" y="298" fill="currentColor">one row · 1 KiB · 32 columns of 32 B</text><rect x="14" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="34.4" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="54.8" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="75.19999999999999" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="95.6" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="116" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="136.39999999999998" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="156.79999999999998" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="177.2" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="197.6" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="218" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="238.39999999999998" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="258.79999999999995" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="279.2" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="299.59999999999997" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="320" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="340.4" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="360.79999999999995" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="381.2" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="401.59999999999997" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="422" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="442.4" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="462.79999999999995" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="483.2" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="503.59999999999997" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="524" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="544.4" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="564.8" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="585.1999999999999" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="605.5999999999999" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="626" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect><rect x="646.4" y="306" width="18.4" height="26" rx="2" fill="none" stroke="currentColor"></rect></svg>

The address is taken apart one last time, to match this memory structure. It picks out a channel, a bank, a row, and a column. Our four sectors are four columns of one row [^13].

So, to serve our load, the memory controller must first send one **activate**, and then four **read** s [^14].

## How the DRAM replies

warp

coalescer

L1

15 ns

TLB

crossbar

L2

127 ns

controller

DRAM

255 ns

SM

die

board

What does a DRAM chip do in response to those commands?

Each DRAM cell is one capacitor behind one transistor. The transistors of a row share a **wordline**, attached to their gates. Each transistor sits between its capacitor and a **bitline**, which runs along a column, providing a path from each cell (shared with the cells of other rows) to the **sense amplifiers**. Bits are stored in the charge state of the capacitor. The capacitors constantly leak charge, so the chip has to pause each bank now and then to top them up.

The structure of DRAM. Click a row to act as the row decoder, releasing charge from the capacitors onto the bitline and into the row buffer.

<svg viewBox="0 0 680 330" role="img" aria-label="Inside one bank, drawn as a schematic four-by-six cell array: wordlines run across, bitlines run down to a row of sense amplifiers at the foot, and each crossing holds a one-transistor-one-capacitor cell. Activating a row lights its wordline and opens its gates; the charge falls down the bitlines and the amplifiers latch it as the row buffer. One row is open at a time."><line x1="110" y1="30" x2="110" y2="290" stroke="currentColor" stroke-opacity="0.2"></line><line x1="200" y1="30" x2="200" y2="290" stroke="currentColor" stroke-opacity="0.2"></line><line x1="290" y1="30" x2="290" y2="290" stroke="currentColor" stroke-opacity="0.2"></line><line x1="380" y1="30" x2="380" y2="290" stroke="currentColor" stroke-opacity="0.2"></line><line x1="470" y1="30" x2="470" y2="290" stroke="currentColor" stroke-opacity="0.2"></line><line x1="560" y1="30" x2="560" y2="290" stroke="currentColor" stroke-opacity="0.2"></line><text x="118" y="28" fill="currentColor">bitline</text> <rect x="14" y="40" width="30" height="216" rx="4" fill="none" stroke="currentColor"></rect><text transform="rotate(-90 29 148)" x="29" y="152" text-anchor="middle" fill="currentColor">row decoder</text> <g><line x1="44" y1="60" x2="640" y2="60" stroke="currentColor" stroke-opacity="0.2"></line><g><line x1="110" y1="76" x2="130" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="140" y1="76" x2="148" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="135" y1="60" x2="135" y2="69" stroke="currentColor" stroke-opacity="0.2"></line><line x1="129" y1="69" x2="141" y2="69" stroke="currentColor" stroke-opacity="0.2"></line><line x1="148" y1="68" x2="148" y2="84" stroke="currentColor" stroke-opacity="0.2"></line><line x1="154" y1="68" x2="154" y2="84" stroke="currentColor" stroke-opacity="0.2"></line><line x1="154" y1="76" x2="162" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="162" y1="70" x2="162" y2="82" stroke="currentColor" stroke-opacity="0.2"></line><line x1="165" y1="72" x2="165" y2="80" stroke="currentColor" stroke-opacity="0.2"></line><line x1="168" y1="74" x2="168" y2="78" stroke="currentColor" stroke-opacity="0.2"></line><rect x="149.5" y="70" width="3.5" height="12" fill="none" stroke="currentColor"></rect></g><g><line x1="200" y1="76" x2="220" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="230" y1="76" x2="238" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="225" y1="60" x2="225" y2="69" stroke="currentColor" stroke-opacity="0.2"></line><line x1="219" y1="69" x2="231" y2="69" stroke="currentColor" stroke-opacity="0.2"></line><line x1="238" y1="68" x2="238" y2="84" stroke="currentColor" stroke-opacity="0.2"></line><line x1="244" y1="68" x2="244" y2="84" stroke="currentColor" stroke-opacity="0.2"></line><line x1="244" y1="76" x2="252" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="252" y1="70" x2="252" y2="82" stroke="currentColor" stroke-opacity="0.2"></line><line x1="255" y1="72" x2="255" y2="80" stroke="currentColor" stroke-opacity="0.2"></line><line x1="258" y1="74" x2="258" y2="78" stroke="currentColor" stroke-opacity="0.2"></line></g><g><line x1="290" y1="76" x2="310" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="320" y1="76" x2="328" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="315" y1="60" x2="315" y2="69" stroke="currentColor" stroke-opacity="0.2"></line><line x1="309" y1="69" x2="321" y2="69" stroke="currentColor" stroke-opacity="0.2"></line><line x1="328" y1="68" x2="328" y2="84" stroke="currentColor" stroke-opacity="0.2"></line><line x1="334" y1="68" x2="334" y2="84" stroke="currentColor" stroke-opacity="0.2"></line><line x1="334" y1="76" x2="342" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="342" y1="70" x2="342" y2="82" stroke="currentColor" stroke-opacity="0.2"></line><line x1="345" y1="72" x2="345" y2="80" stroke="currentColor" stroke-opacity="0.2"></line><line x1="348" y1="74" x2="348" y2="78" stroke="currentColor" stroke-opacity="0.2"></line><rect x="329.5" y="70" width="3.5" height="12" fill="none" stroke="currentColor"></rect></g><g><line x1="380" y1="76" x2="400" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="410" y1="76" x2="418" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="405" y1="60" x2="405" y2="69" stroke="currentColor" stroke-opacity="0.2"></line><line x1="399" y1="69" x2="411" y2="69" stroke="currentColor" stroke-opacity="0.2"></line><line x1="418" y1="68" x2="418" y2="84" stroke="currentColor" stroke-opacity="0.2"></line><line x1="424" y1="68" x2="424" y2="84" stroke="currentColor" stroke-opacity="0.2"></line><line x1="424" y1="76" x2="432" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="432" y1="70" x2="432" y2="82" stroke="currentColor" stroke-opacity="0.2"></line><line x1="435" y1="72" x2="435" y2="80" stroke="currentColor" stroke-opacity="0.2"></line><line x1="438" y1="74" x2="438" y2="78" stroke="currentColor" stroke-opacity="0.2"></line><rect x="419.5" y="70" width="3.5" height="12" fill="none" stroke="currentColor"></rect></g><g><line x1="470" y1="76" x2="490" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="500" y1="76" x2="508" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="495" y1="60" x2="495" y2="69" stroke="currentColor" stroke-opacity="0.2"></line><line x1="489" y1="69" x2="501" y2="69" stroke="currentColor" stroke-opacity="0.2"></line><line x1="508" y1="68" x2="508" y2="84" stroke="currentColor" stroke-opacity="0.2"></line><line x1="514" y1="68" x2="514" y2="84" stroke="currentColor" stroke-opacity="0.2"></line><line x1="514" y1="76" x2="522" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="522" y1="70" x2="522" y2="82" stroke="currentColor" stroke-opacity="0.2"></line><line x1="525" y1="72" x2="525" y2="80" stroke="currentColor" stroke-opacity="0.2"></line><line x1="528" y1="74" x2="528" y2="78" stroke="currentColor" stroke-opacity="0.2"></line></g><g><line x1="560" y1="76" x2="580" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="590" y1="76" x2="598" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="585" y1="60" x2="585" y2="69" stroke="currentColor" stroke-opacity="0.2"></line><line x1="579" y1="69" x2="591" y2="69" stroke="currentColor" stroke-opacity="0.2"></line><line x1="598" y1="68" x2="598" y2="84" stroke="currentColor" stroke-opacity="0.2"></line><line x1="604" y1="68" x2="604" y2="84" stroke="currentColor" stroke-opacity="0.2"></line><line x1="604" y1="76" x2="612" y2="76" stroke="currentColor" stroke-opacity="0.2"></line><line x1="612" y1="70" x2="612" y2="82" stroke="currentColor" stroke-opacity="0.2"></line><line x1="615" y1="72" x2="615" y2="80" stroke="currentColor" stroke-opacity="0.2"></line><line x1="618" y1="74" x2="618" y2="78" stroke="currentColor" stroke-opacity="0.2"></line></g><rect x="44" y="40" width="596" height="46" role="button" tabindex="0" aria-label="activate row 0" fill="none" stroke="currentColor"></rect></g><g><line x1="44" y1="116" x2="640" y2="116" stroke="currentColor" stroke-opacity="0.2"></line><g><line x1="110" y1="132" x2="130" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="140" y1="132" x2="148" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="135" y1="116" x2="135" y2="125" stroke="currentColor" stroke-opacity="0.2"></line><line x1="129" y1="125" x2="141" y2="125" stroke="currentColor" stroke-opacity="0.2"></line><line x1="148" y1="124" x2="148" y2="140" stroke="currentColor" stroke-opacity="0.2"></line><line x1="154" y1="124" x2="154" y2="140" stroke="currentColor" stroke-opacity="0.2"></line><line x1="154" y1="132" x2="162" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="162" y1="126" x2="162" y2="138" stroke="currentColor" stroke-opacity="0.2"></line><line x1="165" y1="128" x2="165" y2="136" stroke="currentColor" stroke-opacity="0.2"></line><line x1="168" y1="130" x2="168" y2="134" stroke="currentColor" stroke-opacity="0.2"></line></g><g><line x1="200" y1="132" x2="220" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="230" y1="132" x2="238" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="225" y1="116" x2="225" y2="125" stroke="currentColor" stroke-opacity="0.2"></line><line x1="219" y1="125" x2="231" y2="125" stroke="currentColor" stroke-opacity="0.2"></line><line x1="238" y1="124" x2="238" y2="140" stroke="currentColor" stroke-opacity="0.2"></line><line x1="244" y1="124" x2="244" y2="140" stroke="currentColor" stroke-opacity="0.2"></line><line x1="244" y1="132" x2="252" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="252" y1="126" x2="252" y2="138" stroke="currentColor" stroke-opacity="0.2"></line><line x1="255" y1="128" x2="255" y2="136" stroke="currentColor" stroke-opacity="0.2"></line><line x1="258" y1="130" x2="258" y2="134" stroke="currentColor" stroke-opacity="0.2"></line><rect x="239.5" y="126" width="3.5" height="12" fill="none" stroke="currentColor"></rect></g><g><line x1="290" y1="132" x2="310" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="320" y1="132" x2="328" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="315" y1="116" x2="315" y2="125" stroke="currentColor" stroke-opacity="0.2"></line><line x1="309" y1="125" x2="321" y2="125" stroke="currentColor" stroke-opacity="0.2"></line><line x1="328" y1="124" x2="328" y2="140" stroke="currentColor" stroke-opacity="0.2"></line><line x1="334" y1="124" x2="334" y2="140" stroke="currentColor" stroke-opacity="0.2"></line><line x1="334" y1="132" x2="342" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="342" y1="126" x2="342" y2="138" stroke="currentColor" stroke-opacity="0.2"></line><line x1="345" y1="128" x2="345" y2="136" stroke="currentColor" stroke-opacity="0.2"></line><line x1="348" y1="130" x2="348" y2="134" stroke="currentColor" stroke-opacity="0.2"></line><rect x="329.5" y="126" width="3.5" height="12" fill="none" stroke="currentColor"></rect></g><g><line x1="380" y1="132" x2="400" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="410" y1="132" x2="418" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="405" y1="116" x2="405" y2="125" stroke="currentColor" stroke-opacity="0.2"></line><line x1="399" y1="125" x2="411" y2="125" stroke="currentColor" stroke-opacity="0.2"></line><line x1="418" y1="124" x2="418" y2="140" stroke="currentColor" stroke-opacity="0.2"></line><line x1="424" y1="124" x2="424" y2="140" stroke="currentColor" stroke-opacity="0.2"></line><line x1="424" y1="132" x2="432" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="432" y1="126" x2="432" y2="138" stroke="currentColor" stroke-opacity="0.2"></line><line x1="435" y1="128" x2="435" y2="136" stroke="currentColor" stroke-opacity="0.2"></line><line x1="438" y1="130" x2="438" y2="134" stroke="currentColor" stroke-opacity="0.2"></line></g><g><line x1="470" y1="132" x2="490" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="500" y1="132" x2="508" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="495" y1="116" x2="495" y2="125" stroke="currentColor" stroke-opacity="0.2"></line><line x1="489" y1="125" x2="501" y2="125" stroke="currentColor" stroke-opacity="0.2"></line><line x1="508" y1="124" x2="508" y2="140" stroke="currentColor" stroke-opacity="0.2"></line><line x1="514" y1="124" x2="514" y2="140" stroke="currentColor" stroke-opacity="0.2"></line><line x1="514" y1="132" x2="522" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="522" y1="126" x2="522" y2="138" stroke="currentColor" stroke-opacity="0.2"></line><line x1="525" y1="128" x2="525" y2="136" stroke="currentColor" stroke-opacity="0.2"></line><line x1="528" y1="130" x2="528" y2="134" stroke="currentColor" stroke-opacity="0.2"></line><rect x="509.5" y="126" width="3.5" height="12" fill="none" stroke="currentColor"></rect></g><g><line x1="560" y1="132" x2="580" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="590" y1="132" x2="598" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="585" y1="116" x2="585" y2="125" stroke="currentColor" stroke-opacity="0.2"></line><line x1="579" y1="125" x2="591" y2="125" stroke="currentColor" stroke-opacity="0.2"></line><line x1="598" y1="124" x2="598" y2="140" stroke="currentColor" stroke-opacity="0.2"></line><line x1="604" y1="124" x2="604" y2="140" stroke="currentColor" stroke-opacity="0.2"></line><line x1="604" y1="132" x2="612" y2="132" stroke="currentColor" stroke-opacity="0.2"></line><line x1="612" y1="126" x2="612" y2="138" stroke="currentColor" stroke-opacity="0.2"></line><line x1="615" y1="128" x2="615" y2="136" stroke="currentColor" stroke-opacity="0.2"></line><line x1="618" y1="130" x2="618" y2="134" stroke="currentColor" stroke-opacity="0.2"></line></g><rect x="44" y="96" width="596" height="46" role="button" tabindex="0" aria-label="activate row 1" fill="none" stroke="currentColor"></rect></g><g><line x1="44" y1="172" x2="640" y2="172" stroke="currentColor" stroke-opacity="0.2"></line><g><line x1="110" y1="188" x2="130" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="140" y1="188" x2="148" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="135" y1="172" x2="135" y2="181" stroke="currentColor" stroke-opacity="0.2"></line><line x1="129" y1="181" x2="141" y2="181" stroke="currentColor" stroke-opacity="0.2"></line><line x1="148" y1="180" x2="148" y2="196" stroke="currentColor" stroke-opacity="0.2"></line><line x1="154" y1="180" x2="154" y2="196" stroke="currentColor" stroke-opacity="0.2"></line><line x1="154" y1="188" x2="162" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="162" y1="182" x2="162" y2="194" stroke="currentColor" stroke-opacity="0.2"></line><line x1="165" y1="184" x2="165" y2="192" stroke="currentColor" stroke-opacity="0.2"></line><line x1="168" y1="186" x2="168" y2="190" stroke="currentColor" stroke-opacity="0.2"></line><rect x="149.5" y="182" width="3.5" height="12" fill="none" stroke="currentColor"></rect></g><g><line x1="200" y1="188" x2="220" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="230" y1="188" x2="238" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="225" y1="172" x2="225" y2="181" stroke="currentColor" stroke-opacity="0.2"></line><line x1="219" y1="181" x2="231" y2="181" stroke="currentColor" stroke-opacity="0.2"></line><line x1="238" y1="180" x2="238" y2="196" stroke="currentColor" stroke-opacity="0.2"></line><line x1="244" y1="180" x2="244" y2="196" stroke="currentColor" stroke-opacity="0.2"></line><line x1="244" y1="188" x2="252" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="252" y1="182" x2="252" y2="194" stroke="currentColor" stroke-opacity="0.2"></line><line x1="255" y1="184" x2="255" y2="192" stroke="currentColor" stroke-opacity="0.2"></line><line x1="258" y1="186" x2="258" y2="190" stroke="currentColor" stroke-opacity="0.2"></line><rect x="239.5" y="182" width="3.5" height="12" fill="none" stroke="currentColor"></rect></g><g><line x1="290" y1="188" x2="310" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="320" y1="188" x2="328" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="315" y1="172" x2="315" y2="181" stroke="currentColor" stroke-opacity="0.2"></line><line x1="309" y1="181" x2="321" y2="181" stroke="currentColor" stroke-opacity="0.2"></line><line x1="328" y1="180" x2="328" y2="196" stroke="currentColor" stroke-opacity="0.2"></line><line x1="334" y1="180" x2="334" y2="196" stroke="currentColor" stroke-opacity="0.2"></line><line x1="334" y1="188" x2="342" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="342" y1="182" x2="342" y2="194" stroke="currentColor" stroke-opacity="0.2"></line><line x1="345" y1="184" x2="345" y2="192" stroke="currentColor" stroke-opacity="0.2"></line><line x1="348" y1="186" x2="348" y2="190" stroke="currentColor" stroke-opacity="0.2"></line></g><g><line x1="380" y1="188" x2="400" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="410" y1="188" x2="418" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="405" y1="172" x2="405" y2="181" stroke="currentColor" stroke-opacity="0.2"></line><line x1="399" y1="181" x2="411" y2="181" stroke="currentColor" stroke-opacity="0.2"></line><line x1="418" y1="180" x2="418" y2="196" stroke="currentColor" stroke-opacity="0.2"></line><line x1="424" y1="180" x2="424" y2="196" stroke="currentColor" stroke-opacity="0.2"></line><line x1="424" y1="188" x2="432" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="432" y1="182" x2="432" y2="194" stroke="currentColor" stroke-opacity="0.2"></line><line x1="435" y1="184" x2="435" y2="192" stroke="currentColor" stroke-opacity="0.2"></line><line x1="438" y1="186" x2="438" y2="190" stroke="currentColor" stroke-opacity="0.2"></line></g><g><line x1="470" y1="188" x2="490" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="500" y1="188" x2="508" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="495" y1="172" x2="495" y2="181" stroke="currentColor" stroke-opacity="0.2"></line><line x1="489" y1="181" x2="501" y2="181" stroke="currentColor" stroke-opacity="0.2"></line><line x1="508" y1="180" x2="508" y2="196" stroke="currentColor" stroke-opacity="0.2"></line><line x1="514" y1="180" x2="514" y2="196" stroke="currentColor" stroke-opacity="0.2"></line><line x1="514" y1="188" x2="522" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="522" y1="182" x2="522" y2="194" stroke="currentColor" stroke-opacity="0.2"></line><line x1="525" y1="184" x2="525" y2="192" stroke="currentColor" stroke-opacity="0.2"></line><line x1="528" y1="186" x2="528" y2="190" stroke="currentColor" stroke-opacity="0.2"></line></g><g><line x1="560" y1="188" x2="580" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="590" y1="188" x2="598" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="585" y1="172" x2="585" y2="181" stroke="currentColor" stroke-opacity="0.2"></line><line x1="579" y1="181" x2="591" y2="181" stroke="currentColor" stroke-opacity="0.2"></line><line x1="598" y1="180" x2="598" y2="196" stroke="currentColor" stroke-opacity="0.2"></line><line x1="604" y1="180" x2="604" y2="196" stroke="currentColor" stroke-opacity="0.2"></line><line x1="604" y1="188" x2="612" y2="188" stroke="currentColor" stroke-opacity="0.2"></line><line x1="612" y1="182" x2="612" y2="194" stroke="currentColor" stroke-opacity="0.2"></line><line x1="615" y1="184" x2="615" y2="192" stroke="currentColor" stroke-opacity="0.2"></line><line x1="618" y1="186" x2="618" y2="190" stroke="currentColor" stroke-opacity="0.2"></line><rect x="599.5" y="182" width="3.5" height="12" fill="none" stroke="currentColor"></rect></g><rect x="44" y="152" width="596" height="46" role="button" tabindex="0" aria-label="activate row 2" fill="none" stroke="currentColor"></rect></g><g><line x1="44" y1="228" x2="640" y2="228" stroke="currentColor" stroke-opacity="0.2"></line><g><line x1="110" y1="244" x2="130" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="140" y1="244" x2="148" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="135" y1="228" x2="135" y2="237" stroke="currentColor" stroke-opacity="0.2"></line><line x1="129" y1="237" x2="141" y2="237" stroke="currentColor" stroke-opacity="0.2"></line><line x1="148" y1="236" x2="148" y2="252" stroke="currentColor" stroke-opacity="0.2"></line><line x1="154" y1="236" x2="154" y2="252" stroke="currentColor" stroke-opacity="0.2"></line><line x1="154" y1="244" x2="162" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="162" y1="238" x2="162" y2="250" stroke="currentColor" stroke-opacity="0.2"></line><line x1="165" y1="240" x2="165" y2="248" stroke="currentColor" stroke-opacity="0.2"></line><line x1="168" y1="242" x2="168" y2="246" stroke="currentColor" stroke-opacity="0.2"></line></g><g><line x1="200" y1="244" x2="220" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="230" y1="244" x2="238" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="225" y1="228" x2="225" y2="237" stroke="currentColor" stroke-opacity="0.2"></line><line x1="219" y1="237" x2="231" y2="237" stroke="currentColor" stroke-opacity="0.2"></line><line x1="238" y1="236" x2="238" y2="252" stroke="currentColor" stroke-opacity="0.2"></line><line x1="244" y1="236" x2="244" y2="252" stroke="currentColor" stroke-opacity="0.2"></line><line x1="244" y1="244" x2="252" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="252" y1="238" x2="252" y2="250" stroke="currentColor" stroke-opacity="0.2"></line><line x1="255" y1="240" x2="255" y2="248" stroke="currentColor" stroke-opacity="0.2"></line><line x1="258" y1="242" x2="258" y2="246" stroke="currentColor" stroke-opacity="0.2"></line></g><g><line x1="290" y1="244" x2="310" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="320" y1="244" x2="328" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="315" y1="228" x2="315" y2="237" stroke="currentColor" stroke-opacity="0.2"></line><line x1="309" y1="237" x2="321" y2="237" stroke="currentColor" stroke-opacity="0.2"></line><line x1="328" y1="236" x2="328" y2="252" stroke="currentColor" stroke-opacity="0.2"></line><line x1="334" y1="236" x2="334" y2="252" stroke="currentColor" stroke-opacity="0.2"></line><line x1="334" y1="244" x2="342" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="342" y1="238" x2="342" y2="250" stroke="currentColor" stroke-opacity="0.2"></line><line x1="345" y1="240" x2="345" y2="248" stroke="currentColor" stroke-opacity="0.2"></line><line x1="348" y1="242" x2="348" y2="246" stroke="currentColor" stroke-opacity="0.2"></line><rect x="329.5" y="238" width="3.5" height="12" fill="none" stroke="currentColor"></rect></g><g><line x1="380" y1="244" x2="400" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="410" y1="244" x2="418" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="405" y1="228" x2="405" y2="237" stroke="currentColor" stroke-opacity="0.2"></line><line x1="399" y1="237" x2="411" y2="237" stroke="currentColor" stroke-opacity="0.2"></line><line x1="418" y1="236" x2="418" y2="252" stroke="currentColor" stroke-opacity="0.2"></line><line x1="424" y1="236" x2="424" y2="252" stroke="currentColor" stroke-opacity="0.2"></line><line x1="424" y1="244" x2="432" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="432" y1="238" x2="432" y2="250" stroke="currentColor" stroke-opacity="0.2"></line><line x1="435" y1="240" x2="435" y2="248" stroke="currentColor" stroke-opacity="0.2"></line><line x1="438" y1="242" x2="438" y2="246" stroke="currentColor" stroke-opacity="0.2"></line></g><g><line x1="470" y1="244" x2="490" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="500" y1="244" x2="508" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="495" y1="228" x2="495" y2="237" stroke="currentColor" stroke-opacity="0.2"></line><line x1="489" y1="237" x2="501" y2="237" stroke="currentColor" stroke-opacity="0.2"></line><line x1="508" y1="236" x2="508" y2="252" stroke="currentColor" stroke-opacity="0.2"></line><line x1="514" y1="236" x2="514" y2="252" stroke="currentColor" stroke-opacity="0.2"></line><line x1="514" y1="244" x2="522" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="522" y1="238" x2="522" y2="250" stroke="currentColor" stroke-opacity="0.2"></line><line x1="525" y1="240" x2="525" y2="248" stroke="currentColor" stroke-opacity="0.2"></line><line x1="528" y1="242" x2="528" y2="246" stroke="currentColor" stroke-opacity="0.2"></line><rect x="509.5" y="238" width="3.5" height="12" fill="none" stroke="currentColor"></rect></g><g><line x1="560" y1="244" x2="580" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="590" y1="244" x2="598" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="585" y1="228" x2="585" y2="237" stroke="currentColor" stroke-opacity="0.2"></line><line x1="579" y1="237" x2="591" y2="237" stroke="currentColor" stroke-opacity="0.2"></line><line x1="598" y1="236" x2="598" y2="252" stroke="currentColor" stroke-opacity="0.2"></line><line x1="604" y1="236" x2="604" y2="252" stroke="currentColor" stroke-opacity="0.2"></line><line x1="604" y1="244" x2="612" y2="244" stroke="currentColor" stroke-opacity="0.2"></line><line x1="612" y1="238" x2="612" y2="250" stroke="currentColor" stroke-opacity="0.2"></line><line x1="615" y1="240" x2="615" y2="248" stroke="currentColor" stroke-opacity="0.2"></line><line x1="618" y1="242" x2="618" y2="246" stroke="currentColor" stroke-opacity="0.2"></line><rect x="599.5" y="238" width="3.5" height="12" fill="none" stroke="currentColor"></rect></g><rect x="44" y="208" width="596" height="46" role="button" tabindex="0" aria-label="activate row 3" fill="none" stroke="currentColor"></rect></g><text x="640" y="50" text-anchor="end" fill="currentColor">wordline</text><g><rect x="94" y="290" width="32" height="24" rx="4" fill="none" stroke="currentColor"></rect></g><g><rect x="184" y="290" width="32" height="24" rx="4" fill="none" stroke="currentColor"></rect></g><g><rect x="274" y="290" width="32" height="24" rx="4" fill="none" stroke="currentColor"></rect></g><g><rect x="364" y="290" width="32" height="24" rx="4" fill="none" stroke="currentColor"></rect></g><g><rect x="454" y="290" width="32" height="24" rx="4" fill="none" stroke="currentColor"></rect></g><g><rect x="544" y="290" width="32" height="24" rx="4" fill="none" stroke="currentColor"></rect></g></svg>

The activate command triggers the **row decoder** to drive that row’s wordline, opening the row’s transistors and driving the charge from the capacitors in that row (and only that row) through the bitline into the sense amplifiers, which amplify that charge into full-rail bits and hold them for the controller to read.

When the read is issued, its column address picks out 256 of these row bits. Reading from the sense amplifiers gives us very many bits at once, but we need to serialize them onto the pins that drive data back across the bus. There are 16 data pins per channel. The 256 bits of our read leave on these pins as [PAM4](https://fergusfinn.com/blog/nvlink-scale-up/#fast-or-far) symbols: each symbol is one of four voltage levels, carrying two bits, so 256 bits over 16 pins is 16 bits per pin — eight symbols. The clock is sent along a shared wire so that the controller can sample at the right edges.

## The way back

warp

coalescer

L1

15 ns

TLB

crossbar

L2

127 ns

controller

DRAM

255 ns

SM

die

board

These PAM4 bursts are deserialized in the memory controller, and written into the L2 slice’s line. The results run back through the crossbar, back to their SM, and fill their L1 slot. They rendezvous with the record left by their leaving, and their bytes are written into register `R4` across all the lanes.

When the load was issued, a dependency barrier was set, which this register write clears. The warp becomes eligible again, and on the scheduler’s next cycle it wins the arbitration. The instruction it issues is the add that was waiting on `b[i]`.

The round trip — L1, TLB, crossbar, L2, controller, and back — costs about 255 ns, some 660 cycles. All the while our warp was parked on its barrier. The rest of the chip wasn’t idle though. The sub-partition issued the same loads for another 11 warps, the rest of the SM for another 36, the other SMs for the other 6096. The result is a cacophony of loads, the per-load latency of any one of them lost in the noise. Here’s what that looks like:

A timing-proportional simulation of the execution of only the instructions in the `vadd` kernel that correspond to the load of `b`. Each SM loads only those addresses it loads in the real kernel: those addresses light up (and miss) in the correct L1 set, then are routed through the crossbar to the correct L2 slice, where they miss, falling through a correctly contended memory controller to a simulated DRAM bank, before returning back through L2, back through L1, and returning their results into the correct register.

Loading b

SMs (128), one pixel per L1 set

crossbar

L2 (36 slices, 3 per controller), one pixel per set

memory controllers (level is instantaneous throughput)

MC

MC

MC

MC

MC

MC

MC

MC

MC

MC

MC

MC

GDDR6X, 12 chips, 32 banks

activate row open precharge refresh

in flight 0 retired 0 activates 0 refreshes 0 GB/s 0

## Appendix: the probes

### Setup

All measurements are on one RTX 4090 (`sm_89`), with the core clock locked at 2.6 GHz. Cycles come from measured nanoseconds at that frequency. Two main instruments:

**A latency chase.** To get a latency measurement (especially when that latency changing tells you something about the chip), we run a pointer cycle through a chosen set of lines, hopped 20,000 times, and then measure the mean ns per hop. If the lines we point to fit in a cache level, then they stay resident, and the mean is that level’s hit latency. Because of the steepness of the hierarchy, any loads that overflow to the next level down tend to show up strongly in the average. `ld.global.ca` (`LDG.E…STRONG.SM`) for chases at the L1, `ld.global.cg` (`LDG.E…STRONG.GPU`) goes past L1. Hit latencies are 15.4 ns at the L1, 127.4 ns at the L2, and 255.4 ns at DRAM.

**Hardware counters.** To read `ncu` ’s counters reliably you have to take them as slopes over iteration count so fixed overhead cancels. Sector and request counters at the L1 exit port and the L2 side are used to figure out more about the shape of the requests, and a per-slice sector counter helps to give us the L2 slice measurements.

### The L1 set function

The 8 bits of the L1 index are the XOR of a fixed subset of the address bits. Written as a bitmask over the address, one basis for those subsets is:

| bit | mask |  | bit | mask |
| --- | --- | --- | --- | --- |
| 0 | `0xc3901e00` |  | 4 | `0x47810400` |
| 1 | `0x119a80a00` |  | 5 | `0x1b4e09180` |
| 2 | `0x167041b00` |  | 6 | `0xb6405400` |
| 3 | `0xdbc21d80` |  | 7 | `0xdc202c80` |

The masks themselves aren’t unique — any invertible combination of these eight describes the same partition.

### Page tables and the TLB

The 16-entry TLB is only the first level, but what happens when you miss? A miss refills in about 4.4 ns, and an L2 hit is 127 ns and a VRAM access is 255 ns, so we can’t be going from those. The inference is that it comes from some larger on-chip translation cache.

The cost is flat within 0.1 ns for all the pages the chip can map, and from any SM. More evidence: walking the page tables with [nvdebug](http://rtsrv.cs.unc.edu/cgit/cgit.cgi/nvdebug.git/) shows the volatile bit set on every directory entry, so they’re not cached in the normal hierarchy.

### The L2 slice function

Measuring which slice owns a line is pretty hard. The L2 is physically indexed, so the probe has to work in device-physical addresses from the page-table walk. Nsight Compute does have a per-slice sector counter, but reports only the min, max, average, and sum across the 36 instances, never the actual slice index.

Even so, the aggregate is enough to tell whether two addresses share a slice. If the two addresses live on the same slice, after loading both, the max counter reports 2, if they’re on different slices the max is 1. You can use this probe to get a representative address that lands on each of the 36 slices.

With the 36 representatives in hand, you can get any new candidate’s slice. If you read the candidate many times alongside all 36, with each of the different addresses read a distinct number of times (say 20001, 20002, … times), the sum of the candidate’s read count and only one of the representatives will match the max counter, and you can figure the slice by inference.

From that, you can produce a table of many physical address-slice pairs. The hard part is going from such a table to a physically plausible function. One tool that helped us a bit was running the same kinds of experiments on two different chips built on the same die: the 4090, and the L40S, which has an extra slice per memory controller.

Here’s one Claude made earlier:

```
SHIFT, OFFSET = (5, 0, 1), (1, 0, 0)

def parity(x):
    return bin(x).count("1") & 1

def _state(a, N):
    wide = (N == 48)                             # L40S: 4 slices/controller, and it reaches bit 35
    b35 = (1 << 35) if wide else 0

    # stage 1 — which of the 12 controllers: two parities and a mod-3 digit
    P1c = parity(a & 0x76A990400)                # controller parity 1 (narrow; used on both chips)
    P1  = parity(a & (0x76A990400 ^ b35))        # wide form, only needed for the L40S read-out
    P2  = parity(a & 0x2CCF7B000)                # controller parity 2
    A   = ((a >> 15) + 2*parity(a & 0x3C9041000) + parity(a & (0x2882B0800 ^ b35)) + 2) % 3  # mod-3 digit: (a>>15) + 2 corrections

    # stage 2 — which slice inside the controller: a 9-position cyclic counter
    g   = ((a + (1 << 16)) >> 17) % 9            # the counter value, round(a / 2^17) mod 9
    q0  = parity(a & 0x8000)                     # four correction parities
    q1  = parity(a & 0x5985E0500)
    q2  = parity(a & (0x2354E4400 ^ b35))
    q3  = parity(a & 0x3C9041000)
    carry = 1 if q0 + q1 + q2 >= 2 else 0        # q0,q1,q2 as a full adder: the carry (majority)...
    start = (5 + 7*q0 + 5*q1 + 2*q2 + q3 - carry) % 9   # ...sets where the counter starts
    o     = (g - SHIFT[A] - start) % 9           # position within the 9-cycle
    Lf    = 2 if (q0 ^ q1 ^ q2) == 0 else 1      # ...and their XOR sets where it splits
    return P1c, P1, P2, A, q2, o // 3, (1 if (o % 3) >= Lf else 0)   # d = o // 3, u = the split bit

def slice_of(a, N=36):
    P1c, P1, P2, A, q2, d, u = _state(a, N)
    controller = (2*P1c + P2) * 3 + A            # 0..11
    if N == 36:                                  # 4090: 3 slices live, read (d, u) as three arcs of Z/9
        base = 2 if d == 0 else (1 if (d == 1 and u == 0) else 0)
        B = ((1 - base) % 3 if q2 else base) % 3 # q2 flips the arc order
        B = (B + OFFSET[A]) % 3                   # per-controller offset
        return controller * 3 + B
    if N == 48:                                  # L40S: 4 slices live, read u as two index bits
        i0, i1 = P1 ^ q2 ^ u, P1 ^ P2 ^ u
        return controller * 4 + 2*i0 + i1
    raise ValueError("N must be 36 or 48")
```

Whilst it is very hard to find such a function, it’s very easy to tell if you’ve found one that works. Drawing 8,192 L2-resident lines from exactly *k* predicted slices:

| lines drawn from | Mload/s | vs *k* =1 |
| --- | --- | --- |
| 1 predicted slice | 1,957 | 1.00× |
| 2 | 3,917 | 2.00× |
| 4 | 7,826 | 4.00× |
| 9 | 17,582 | 8.98× |
| 18 | 34,446 | 17.60× |
| all 36 | 68,085 | 34.78× |

### The L2 set index and geometry

Once the slice function pins addresses to a single slice, you can do the same eviction-set archaeology on that slice, to figure out the structure, which tells you that it’s 16 way set-associative (a chase with 17 elements thrashes, but one with 16 doesn’t).

The set index within a slice is the same kind of parity function as the L1’s — ten bits, with the same `(a >> 15) mod 9` nonlinearity in the top bit. Unfortunately, the masks involved differ depending on the slice. For one slice:

```
def parity(x):
    return bin(x).count("1") & 1

def set_index(a):                                # within one slice
    q = a // 1152
    b0 = parity(a & 0x0bd654c80) ^ parity(q & 0x00e500)
    b1 = parity(a & 0x0bd654c80) ^ parity(q & 0x010000)
    b2 = parity(a & 0x07aed8b80) ^ parity(q & 0x027c00)
    b3 = parity(a & 0x03e313180) ^ parity(q & 0x045500)
    b4 = parity(a & 0x03e313300) ^ parity(q & 0x080300)
    b5 = parity(a & 0x0bd654e80) ^ parity(q & 0x104200)
    b6 = parity(a & 0x0bd654c00) ^ parity(q & 0x200b00)
    b7 = parity(a & 0x044dcb880) ^ parity(q & 0x401600)
    b8 = parity(a & 0x000000200) ^ parity(q & 0x804600)
    b9 = parity(a & 0x13bc21180) ^ parity(q & 0x006400) ^ int((a >> 15) % 9 in (2, 6))
    return sum(b << i for i, b in enumerate([b0, b1, b2, b3, b4, b5, b6, b7, b8, b9]))
```

It has some properties that let you sense-check it. For example: a contiguous 72MiB fills each slot in each slice without thrashing anything, as you’d expect.

### DRAM refresh

DRAM cells leak charge and so have to be periodically refreshed, which makes some kinds of timing probes harder. You can see it by running a dependent chase that writes each hop’s timing into shared memory. Most DRAM accesses come back at the usual latency, but a small share take longer, spread evenly out to a hard ceiling about 210 ns higher than usual. An evenly spaced run like that is the signature of a fixed length stall. The stall is ~210 ns. About 2% of accesses hit one. It doesn’t hit the whole chip at once — it’s more local than that — but I couldn’t tell what the unit was.

```
@misc{doubleword-what-happens-when-a-gpu-reads-memory,
  title        = {What happens when a GPU reads memory},
  author       = {Fergus Finn},
  year         = {2026},
  howpublished = {Doubleword Blog},
  url          = {https://blog.doubleword.ai/what-happens-when-a-gpu-reads-memory},
}
```

[^1]: You can get some visibility here from the hardware counters. We set up a one-warp kernel that loads 4 bytes per lane with a fixed stride. If you run it under `ncu`, it reports ‘sectors per load’ as `l1tex__average_t_sectors_per_request_pipe_lsu_mem_global_op_ld.ratio`. At stride 1 the 32 lanes cover 128 contiguous bytes and the counter reads four sectors. At every wider stride the count equals the number of distinct 32-byte spans the lane addresses touch, with no extra sectors requested.

[^2]: To count the slots in a set, we take a pool of candidate lines much larger than the L1 cache and pointer-chase them in a cycle. By design, the pool doesn’t fit in L1, so each line thrashes, and the latency stays > L1 latency. Then you progressively drop members, and watch the latency. If the latency suddenly drops, you know that somewhere in your pool there is one full set (since it doesn’t thrash). The goal is to find the minimal set such that everything thrashes, where removing any address drops you to L1 access speeds. This is the standard process of finding [eviction sets](https://arxiv.org/pdf/1810.01497)

[^3]: Caches can be indexed & tagged either virtually or physically. This L1 uses the virtual address for both its index and its tag. You can see this by mapping one physical allocation at two virtual addresses, in the minimal conflict set we built to identify the number of ways. Swapping one member of a minimal conflict set for the same physical line seen through the other mapping breaks the conflict, so the index must be computed from virtual bits (if it was physically addressed, they’d deduplicate). Adding the alias back to a full set restores the conflict, so the alias occupies a slot of its own and the tag is virtual too.

[^4]: Each of the eight index bits is the exclusive-or of a fixed subset of the address bits. The masks defining these subsets are in [the appendix](#the-l1-set-function). Figuring out these masks takes two probes. Inside one 2 MiB page, the differences between members of minimal conflict sets fix the masks over address bits 7 to 20. Above the page, flipping one high address bit and reading which set the line lands in gives that bit’s contribution, for every bit from 21 to 32. You can check if you’ve got the right function by using it to construct eviction sets manually (since you know what addresses go in what sets).

[^5]: A slot can hold a line with only some of its sectors present. When a load misses, the request sent on to the L2 names only the sectors the warp wants. `ncu` ’s L2-side counters show the sector count per request tracking exactly what the lanes touch, with no rounding up to the full line. The counters are `lts__t_requests_srcunit_tex_op_read` and its `t_sectors` counterpart.

[^6]: To figure out that the L2 is physically tagged and indexed: we map one physical allocation at two virtual addresses, and a chase visits every line in the allocation through both virtual indexes. If the L2 tagged lines by virtual address, the aliased chase would occupy twice the footprint and exceed the L2’s 72 MiB capacity edge at half the size (this is a tradeoff for any virtually addressed cache: that you get no deduplication. Also vulnerable to timing attacks w/ multitenancy, not a factor here). Sweeping the physical footprint from 24 to 128 MiB, the control and the aliased chase cross the L2 threshold at the same size, so translation must happen before L2.

[^7]: You can read GPU page tables directly, using a tool like [nvdebug](http://rtsrv.cs.unc.edu/cgit/cgit.cgi/nvdebug.git/) that walks the GPU’s page tables from the host. Every device allocator terminates in a 2 MiB page-table entry, with the 4 KiB table beside it invalid. That covers `cudaMalloc`, `cuMemAlloc`, the virtual-memory API at either granularity, and managed memory. Pinned host memory is the exception, with 4 KiB entries in the system aperture. The walker is in [the appendix](#page-tables-and-the-tlb). In the open kernel modules, the mapping path is [`dmaAllocMapping`](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/590.48.01/src/nvidia/src/kernel/gpu/mem_mgr/arch/maxwell/virt_mem_allocator_gm107.c#L315), which calls `dmaUpdateVASpace` and then [`mmuWalkMap`](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/590.48.01/src/nvidia/src/libraries/mmu/mmu_walk_map.c#L41) to fill the entries. The walker allocates each page-table level the first time a mapping needs it.

[^8]: The TLB is fully associative, holds sixteen entries, is per-SM (shared by the warps), and replaces the least recently used entry. You can find this out with yet another pointer chase, this time, one line per 2 MiB page. Sixteen pages cost a 127 ns baseline — the L2 hit latency, since the chase bypasses L1 — but seventeen thrash. Splitting the pages among the warps of one block gives the same step, so the pool is per-SM and shared by its warps. Cyclic visits over seventeen pages miss on every hop, which is the LRU pattern. The tables are in [the appendix](#page-tables-and-the-tlb)

[^9]: Same logic for figuring out the L1 request from the counters, only using the L2 counters.

[^10]: In the function, two address parities and a mod-3 digit are used to pick out the memory controller, which is shared between 4 slices in the full AD102, but only 3 on the 4090, which fuses off one slice per controller. Within those three, a mod-9 digit picks the specific slice. The card has twelve controllers (a 384-bit bus, 12 × 32-bit). The function was recovered by measurement; details in [the appendix](#the-l2-slice-function). You can tell once you’ve got it right, because loading from a set of pointers that share a slice is ~36x (the number of slices) slower than a load from pointers that spread across all the slices.

[^11]: Once you figure out the function mapping specific addresses to specific slices, you can do the cache archaeology in the same way we did it for L1, using eviction sets, with the caveat that you can only use addresses that map to a single slice. More in [the appendix](#the-l2-set-index-and-geometry)

[^12]: The count of twelve controllers is public (it’s a 384-bit bus at 32 bits per chip). The association of slices to controllers is read out of the slice function. Three of its digits take twelve values, and the same three digits appear unchanged on the L40S, which ships the same silicon with all four slices per controller enabled. The factoring is in [the appendix](#the-l2-slice-function)

[^13]: You can measure the row size from timing. Because a DRAM chip is much faster at serving loads that sit in the same row (since a pair of addresses in different rows require closing the row buffer, + activating the new one), if you assume that rows are contiguous, you can find row size by sweeping. Offsets of 32, 64 and 96 bytes always stay within one row, so our four sectors are four columns of one row. With the same instrument, you can figure out the set of addresses that share a row: any difference in $2^5$, $2^6$, $2^7$, $2^9$ and $2^8 \oplus 2^{14}$ preserves a row, so the row is 1 KiB, or 32 columns of 32 bytes.

[^14]: You can measure the cost of activating a new row by keeping many reads in flight. When consecutive reads land in the same row, each extra read adds about 3.4 ns. When each read opens a fresh row, it costs about 15x as much. With one read in flight at a time the difference disappears, because the row is closed again before the next read arrives.
