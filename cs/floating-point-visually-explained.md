---
title: "Floating Point Visually Explained"
source: "https://fabiensanglard.net/floating_point_visually_explained/"
author:
published:
created: 2026-09-09
description:
tags:
  - "clippings"
---

> [!summary]
> Fabien Sanglard reframes IEEE 754 floats without the sign/exponent/mantissa formula: the exponent picks a "window" between two consecutive powers of two, and the 23-bit mantissa is an "offset" that splits that window into 8,388,608 buckets. Precision halves each time the window doubles, which is why large floats get coarser. A worked example encodes 3.14 as S=0, E=128, M=4781507.

---

While I was writing the Wolfenstein 3D book [<sup>[1]</sup>](#footnote_1), I wanted to demonstrate how much of a handicap it was to work without floating points. My attempts at understanding floating points using canonical [<sup>[2]</sup>](#footnote_2) articles [<sup>[3]</sup>](#footnote_3) were met with resistance from my brain.

I tried to find a different way. Something far from $(-1)^S * 1.M * 2^{(E-127)}$ and its mysterious exponent/mantissa. Possibly a drawing since they seem to flow through my brain better.

I ended up with what follows and I decided to include it in the book. I am not claiming this is my invention but I have never seen floating points explained this way so far. I hope it will helps a few people like me who are a bit allergic to mathematic notations.

How Floating Point are usually explained

---

In the C language, floats are 32-bit container following the IEEE 754 standard. Their purpose is to store and allow operations on approximation of real numbers. The way I have seen them explained so far is as follow. The 32 bits are divided in three sections:

- 1 bit S for the sign
- 8 bits E for the exponent
- 23 bits for the mantissa

![](https://fabiensanglard.net/floating_point_visually_explained/floating_point_layout.svg)

*Floating Point internals.*

*The three sections of a floating point number.*

So far, so good. Now, how numbers are interpreted is usually explained with the formula:

$$
(-1)^S * 1.M * 2^{(E-127)}
$$

*How everybody hates floating point to be explained to them.*

This is usually where I flip the table. Maybe I am allergic to mathematic notation but something just doesn't click when I read it. It feels like learning to [draw a owl](https://fabiensanglard.net/floating_point_visually_explained/01.jpg).

> Floating-point arithmetic is considered an esoteric subject by many people.
>
>
> \- David Goldberg

A different way to explain...

---

Although correct, this way of explaining floating point will leaves some of us completely clueless. Fortunately, there is a different way to explain it. Instead of Exponent, think of a Window between two consecutive power of two integers. Instead of a Mantissa, think of an Offset within that window.

*The three sections of a floating Point number.*

The window tells within which two consecutive power-of-two the number will be: \[0.5,1\], \[1,2\], \[2,4\], \[4,8\] and so on (up to \[$2^{127}$,$2^{128}$\]). The offset divides the window in $2^{23} = 8388608$ buckets. With the window and the offset you can approximate a number. The window is an excellent mechanism to protect from overflowing. Once you have reached the maximum in a window (e.g \[2,4\]), you can "float" it right and represent the number within the next window (e.g \[4,8\]). It only costs a little bit of precision since the window becomes twice as large.

The next figure illustrates how the number 6.1 would be encoded. The window must start at 4 and span to next power of two, 8. The offset is about half way down the window.

![](https://fabiensanglard.net/floating_point_visually_explained/floating_point_window.svg)

*Value 6.1 approximated with floating point.*

Precision

---

How much precision is lost when the window covers a wider range? Let's take an example with window \[1,2\] where the 8388608 offsets cover a range of 1 which gives a precision of $\frac{(2-1)}{8388608}=0.00000011920929$. In the window \[2048,4096\] the 8388608 offsets cover a range of $4096 - 2048 = 2048$ which gives a precision of $\frac{4096 - 2048}{8388608} = 0.0002$.

An other example

---

Let's take an other example with the detailed calculations of the floating point representation of a number we all know well: 3.14.

- The number 3.14 is positive $\rightarrow S=0$.
- The number 3.14 is between the power of two 2 and 4 so the floating window must start at $2^1$ $\rightarrow E = 128$ (see formula where window is $2^{\left(E - 127\right)}$).
- Finally there are $2^{23}$ offsets available to express where 3.14 falls within the interval \[2-4\]. It is at $\frac{3.14 - 2}{4 - 2} = 0.57$ within the interval which makes the offset $M = 2^{23} * 0.57 = 4781507$

Which in binary translates to:

- S = 0 = 0b
- E = 128 = 10000000b
- M = 4781507 = 10010001111010111000011b

![](https://fabiensanglard.net/floating_point_visually_explained/floating_point_layout_pi.svg)

*3.14 floating point binary representation.*

The value 3.14 is therefore approximated to 3.1400001049041748046875. The corresponding value with the ugly formula:

$$
3.14 = (-1)^0 * 1.57 * 2^{(128-127)}
$$

And finally the graphic representation with window and offset:

![](https://fabiensanglard.net/floating_point_visually_explained/floating_point_window_pi.svg)

*3.14 window and offset.*

I hope that helped:)!

References

---

| [^](#back_1) | \[1\] | [Game Engine Black Book: Wolfenstein 3D](https://fabiensanglard.net/gebb/index.html) |
| --- | --- | --- |
| [^](#back_2) | \[2\] | [Wikipedia, Floating-point arithmetic](https://en.wikipedia.org/wiki/Floating-point_arithmetic) |
| [^](#back_3) | \[3\] | [What Every Computer Scientist Should Know About Floating-Point Arithmetic](http://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html) |

---

\*
