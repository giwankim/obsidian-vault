---
title: "Learn GameCube Decompilation (MWCC GC/2.0)"
source: "https://decomp-academy.dev/"
author:
published:
created: 2026-06-30
description: "Learn to decompile GameCube PowerPC assembly into byte-matching C, graded live by the real Metrowerks CodeWarrior GC/2.0 compiler. Free, interactive lessons."
tags:
  - "clippings"
---

> [!summary]
> Decomp Academy is a free, interactive course for learning GameCube decompilation: you read PowerPC assembly, write the C source, and the real Metrowerks CodeWarrior GC/2.0 compiler grades your answer byte-for-byte. The curriculum progresses from core C idioms (arithmetic, structs, floats) through the real ABI (frames, globals, optimizer, 64-bit) to a "proving ground" of complete Star Fox Adventures functions.

## The Curriculum

Read the asm · write the source · the compiler grades it byte-for-byte.

[Jump back in →](https://decomp-academy.dev/courses/gamecube-c/lesson/foundations-what-is-matching)

Solved Attempted Not started Concept (reading) Difficulty 1–5

II

Core idioms

Every shape C compiles into

0/159

[An Add Then a Subtract](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-add-sub) [Two Adds, Reassociated](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-two-adds) [A Subtract Then an Add](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-sub-add) [A Three-Instruction Chain](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-add-sub-add) [Multiplying Two Registers](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-mul) [Multiply by a Power of Two](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-mul-const-pow2) [Multiply by a Small Constant](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-mul-const) [An Affine Expression](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-affine) [Unsigned Divide by a Power of Two](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-div-pow2-unsigned) [Signed Divide by a Power of Two](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-div-pow2-signed) [Real Division](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-div-var) [Modulo Has No Instruction](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-mod) [Multiply Then Add](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-mul-add) [Precedence Changes the Order](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-add-mul) [Two Products, Subtracted](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-two-products) [A Three-Instruction Mixed Chain](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-mul-add-sub) [When a Multiply Is a Shift](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-scale-sum) [A Shift Inside a Mixed Chain](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-scale-chain) [Divide Then Add](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-div-add) [When a Divide Is a Shift](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-shrink-sum) [A Shift-Divide in a Chain](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-shrink-chain) [Divide and Multiply, Then Subtract](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-div-sub-mul) [Multiply and Divide Combined](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-mul-add-div) [All Four Arithmetic Operators](https://decomp-academy.dev/courses/gamecube-c/lesson/arithmetic-all-four-ops)

[Reading a Struct Field](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-read-field) [Writing a Struct Field](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-write-field) [Narrow Fields: Byte and Halfword Loads](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-narrow-read) [Storing a Byte Field](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-narrow-write) [Alignment Padding Shifts an Offset](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-padding) [Combining Two Fields](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-sum-fields) [Computing Across Three Fields](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-combine-fields) [Nested Structs Flatten to One Offset](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-nested) [Combining Fields Across Nested Structs](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-struct-of-structs) [Arrays of Structs: Scaling the Index](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-array-index) [An Array Inside a Struct](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-array-field) [Unions Overlay the Same Bytes](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-union) [A Single-Bit Flag: li; rlwimi](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-bitfield-set) [Multi-Bit Bitfield Writes](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-bitfield-multi) [Reading a Bitfield: rlwinm Extract](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-bitfield-read) [Walking a Linked List](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-linked-list) [Calling Through a Function Pointer](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-function-pointer) [Copying a Whole Struct](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-copy-whole) [Eight-Byte Alignment Copies Through Float Registers](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-copy-aligned) [Big Structs Copy in a Loop](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-copy-large) [Combining a Copy With a Field Update](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-copy-chain) [Capstone: Reading a Whole Struct](https://decomp-academy.dev/courses/gamecube-c/lesson/structs-capstone)

[Floats Live in a Different Register File](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-add) [Single-Precision Multiply](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-mul) [Subtraction Keeps Its Order](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-sub) [Floating-Point Division Is Real](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-div) [Dividing by a Constant Becomes a Multiply](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-div-const-reciprocal) [Doubles Drop the 's'](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-double-add) [★ The Spurious frsp: f32 vs double Helpers](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-frsp-highlight) [Loading a Float Constant from the SDA](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-literal) [★ Fused Multiply-Add](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-fmadds-highlight) [Integer to Float: The Magic-Number Trick](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-int-to-float) [Float to Int: fctiwz and the Store/Load Dance](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-float-to-int) [Comparing Floats: fcmpo Feeding a Branch](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-compare-branch) [Absolute Value and Negation](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-abs-neg) [Chaining Two Float Adds](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-two-adds) [Mixing Add and Subtract in One Chain](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-add-then-subtract) [A Weighted Sum Folds Into One fmadds](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-weighted-sum) [The Lerp Idiom — fsubs Feeding fmadds](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-lerp) [Two Products Summed — the 2D Dot Product](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-dot-product-2d) [Accumulating Three Products — the 3D Dot Product](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-dot-product-3d) [Picking the Larger: fcmpo + Conditional fmr](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-max-via-compare) [Clamping Between Two Constants](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-two-sided-clamp) [Mixing f32 and f64 — Double Math, then frsp](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-f32-f64-mixing) [★ Capstone: A Float Step With a Clamp](https://decomp-academy.dev/courses/gamecube-c/lesson/floats-capstone-approach)

III

The real ABI

Frames, globals, optimizer, 64-bit

0/75IV

Proving ground

Real Star Fox Adventures functions, start to finish

0/14
