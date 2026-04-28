---
title: "Exposing Floating Point"
source: "https://ciechanow.ski/exposing-floating-point/"
author:
  - "[[Bartosz Ciechanowski]]"
published:
created: 2026-04-28
description: "In depth explanation of floating point format."
tags:
  - "clippings"
---

> [!summary]
> Bartosz Ciechanowski explains the IEEE 754 binary floating-point format from first principles, building intuition for why the format behaves the way it does rather than treating it as a black box. The post is a companion to his interactive site float.exposed, which lets readers inspect bit patterns of `half`, `float`, and `double` values alongside the explanation.

Despite everyday use, floating point numbers are often understood in a hand-wavy manner and their behavior [raises many eyebrows](https://stackoverflow.com/q/588004/558816). Over the course of this article I’d like to show that things aren’t actually that complicated.

This blog post is a companion to my recently launched website – [float.exposed](https://float.exposed/). Other than exploiting the absurdity of present day [list of top level domains](https://en.wikipedia.org/wiki/List_of_Internet_top-level_domains#ICANN-era_generic_top-level_domains), it’s intended to be a handy tool for inspecting floating point numbers. While I encourage you to play with it, the purpose of many of its elements may be exotic at first. By the time we’ve finished, however, all of them will hopefully become familiar.

On a technical note, by floating point I’m referring to the ubiquitous [IEEE 754](https://en.m.wikipedia.org/wiki/IEEE_754) binary floating point format. Types `half`, `float`, and `double` are understood to be binary16, binary32, and binary64 respectively. There were [other formats](https://en.wikipedia.org/wiki/Floating-point_arithmetic#History) back in the day, but whatever device you’re reading this on is [pretty much guaranteed](https://stackoverflow.com/q/2234468/558816) to use IEEE 754.

With the formalities out of the way, let’s start at the shallow end of the pool.

## Writing Numbers

We’ll begin with the very basics of writing numeric values. The initial steps may seem trivial, but starting from the first principles will help us build a working model of floating point numbers.

## Decimal Numbers

Consider the number 327.849. Digits to the left of the decimal point represent increasing powers of ten, while digits to the right of the decimal point represent decreasing powers of ten:

3

10 <sup>2</sup>

2

10 <sup>1</sup>

7

10 <sup>0</sup>

.

8

10 <sup>−1</sup>

4

10 <sup>−2</sup>

9

10 <sup>−3</sup>

Even though this notation is very natural, it has a few disadvantages:

- small numbers like 0.000000000653 require skimming over many zeros before they start “showing” actually useful digits
- it’s hard to estimate the magnitude of large numbers like 7298345251 at a glance
- at some point the distant digits of a number become increasingly less significant and could often be dropped, yet for big numbers we don’t save any space by replacing them with zeros, e.g. 7298000000

By “small” and “big” numbers I’m referring to their *magnitude* so −4205 is understood to be bigger than 0.03 even though it’s to the left of it on the real number line.

[Scientific notation](https://en.wikipedia.org/wiki/Scientific_notation) solves all these problems. It shifts the decimal point to right after the first non-zero digit and sets the exponent accordingly:

+3.27849×10 <sup>2</sup>

Scientific notation has three major components: the sign (+), the significand (3.27849), and the exponent (2). For positive values the “+” sign is often omitted, but we’ll keep it around for the sake of verbosity. Note that the “10” simply shows that we’re dealing with base-10 system. The aforementioned disadvantages disappear:

- the 0-heavy small number is presented as 6.53×10 <sup>−10</sup> with all the pesky zeros removed
- just by looking at the first digit and the exponent of 7.298345251×10 <sup>9</sup> we know that number is roughly 7 billion
- we can drop the unwanted distant digits from the tail to get 7.298×10 <sup>9</sup>

Continuing with the protagonist of this section, if we’re only interested in 4 most significant digits we can round the number using one of the [many rounding rules](https://en.wikipedia.org/wiki/Rounding):

+3.278×10 <sup>2</sup>

The number of digits shown describes the precision we’re dealing with. A number with 8 digits of precision could be printed as:

+3.2784900×10 <sup>2</sup>

## Binary Numbers

With the familiar base-10 out of the way, let’s look at the binary numbers. The rules of the game are exactly the same, it’s just that the base is 2 and not 10. Digits to the left of the binary point represent increasing powers of two, while digits to the right of the binary point represent decreasing powers of two:

1

2 <sup>3</sup>

0

2 <sup>2</sup>

0

2 <sup>1</sup>

1

2 <sup>0</sup>

.

0

2 <sup>−1</sup>

1

2 <sup>−2</sup>

0

2 <sup>−3</sup>

1

2 <sup>−4</sup>

When ambiguous I’ll use <sub>2</sub> to mean the number is in base-2. As such, 1000 <sub>2</sub> is not a thousand, but 2 <sup>3</sup> i.e. eight. To get the decimal value of the discussed 1001.0101 <sub>2</sub> we simply sum up the powers of two that have the bit set: 8 + 1 + 0.25 + 0.0625, ending up with the value of 9.3125.

Binary numbers can use scientific notation as well. Since we’re shifting the binary point by three places, the exponent ends up having the value of 3:

+1.0010101×2 <sup>3</sup>

Similarly to scientific notation in base-10, we also moved the binary point to right after the first non-zero digit of the original representation. However, since the only non-zero digit in base-2 system is 1, *every* non-zero binary number in scientific notation starts with a 1.

We can round the number to a shorter form:

+1.0011×2 <sup>3</sup>

Or show that we’re more accurate by storing 11 binary digits:

+1.0010101000×2 <sup>3</sup>

If you’ve grasped everything that we’ve discussed so far then congratulations – you understand how floating point numbers work.

## Floating Point Numbers

Floating points numbers are just numbers in base-2 scientific notation with the following two restrictions:

- limited number of digits in the significand
- limited range of the exponent – it can’t be greater than some maximum limit and also can’t be less than some minimum limit

That’s (almost) all there is to them.

Different floating point types have different number of significand digits and allowed exponent range. For example, a `float` has 24 binary digits (i.e. bits) of significand and the exponent range of \[−126, +127\], where “\[” and “\]” denote inclusivity of the range (e.g. +127 is valid, but +128 is not). Here’s a number with a decimal value of −616134.5625 that can fit in a `float`:

−1.00101100110110001101001×2 <sup>19</sup>

Unfortunately, the number of bits of significand in a `float` is limited, so some real values may not be perfectly representable in the floating point form. A decimal number 0.2 has the following base-2 representation:

+1.1001...×2 <sup>−3</sup>

The overline (technically known as [vinculum](https://en.wikipedia.org/wiki/Vinculum_\(symbol\))) indicates a forever repeating value. The 25 <sup>th</sup> and later significant digits of the perfect base-2 scientific representation of that number won’t fit in a `float` and have to be accounted for by rounding the remaining bits. The full significand:

1.100110011001100110011001100

Will be rounded to:

1.10011001100110011001101

After multiplication by the exponent the resulting number has a *different* decimal value than the perfect 0.2:

0.20000000298023223876953125

If we tried rounding the full significand down:

1.10011001100110011001100

The resulting number would be equal to:

0.199999988079071044921875

No matter what we do, the limited number of bits in the significand prevents us from getting the correct result. This explains why some decimal numbers don’t have their exact floating point representation.

Similarly, since the value of the exponent is limited, many huge and many tiny numbers won’t fit in a `float`: neither 2 <sup>200</sup> nor 2 <sup>−300</sup> can be represented since they don’t fall into the allowed exponent range of \[−126, +127\].

## Encoding

Knowing the number of bits in the significand and the allowed range of the exponent we can start encoding floating point numbers into their binary representation. We’ll use the number −2343.53125 which has the following representation in base-2 scientific notation:

−1.0010010011110001×2 <sup>11</sup>

## The Sign

The sign is easy – we just need 1 bit to express whether the number is positive or negative. IEEE 754 uses the value of `0` for the former and `1` for the latter. Since the discussed number is negative we’ll use one:

1

## The Significand

For the significand of a `float` we need 24 bits. However, per what [we’ve already discussed](#implicit_bit_not_needed), the first digit of the significand in base-2 is always 1, so the format cleverly skips it to save a bit. We just have to remember it’s there when doing calculations. We copy the remaining 23 digits verbatim while filling in the missing bits at the end with 0s:

00100100111100010000000

The leading “1” we skipped is often referred to as an “implicit bit”.

## The Exponent

Since the exponent range of \[−126, +127\] allows 254 possible values, we’ll need 8 bits to store it. To avoid special handling of negative exponent values we’ll add a fixed *bias* to make sure no encoded exponent is negative.

To obtain a *biased* exponent we’ll use the bias value of 127. While 126 would work for regular range of exponents, using 127 will let us reserve a biased value of 0 for [special purposes](#special-values). Biasing is just a matter of shifting all values to the right:

![The bias in a float](https://ciechanow.ski/images/float_bias.svg)

The bias in a `float`

For the discussed number we have to shift its exponent of 11 by 127 to get 138, or 10001010 <sub>2</sub> and that’s what we will encode as the exponent:

10001010

## Putting it All Together

To conform with the standard we’ll put the sign bit first, then the exponent bits, and finally, the significand bits. While seemingly arbitrary, the order is part of the standard’s [ingenuity](#raw-integer-value). By sticking all the pieces together a `float` is born:

11000101000100100111100010000000

The entire encoding occupies 32 bits. To verify we did things correctly we can fire up LLDB and let the hacky [type punning](https://en.wikipedia.org/wiki/Type_punning) do its work:

```plain
(lldb) p -2343.53125f
(float) $0 = -2343.53125

(lldb) p/t *(uint32_t *)&$0
(uint32_t) $1 = 0b11000101000100100111100010000000
```

While neither C nor C++ standards *technically* require a `float` or a `double` to be represented using IEEE 754 format, the rest of this article will sensibly assume so.

The same procedure of encoding a number in base-2 scientific notation can be repeated for almost any number, however, some of them require special handling.

## Special Values

The `float` exponent range allows 254 different values and with a bias of 127 we’re left with two yet unused biased exponent values: 0 and 255. Both are employed for very useful purposes.

## A Map of Floats

A dry description doesn’t really paint a picture, so let’s present all the special values visually. In the following plot every dot represents a unique positive `float`:

![All the special values](https://ciechanow.ski/images/float_special_values.svg)

All the special values

If you have trouble seeing color you can [switch to the alternative version](#). Notice the necessary truncation of a large part of exponents and of a gigantic part of significand values. At your current viewing size you’d have to scroll through roughly 27981 window widths to see all the values of the significand.

We’ve already discussed all the unmarked dots — the normal floats. It’s time to dive into the remaining values.

## Zero

A `float` number with biased exponent value of 0 *and* all zeros in significand is interpreted as positive or negative 0. The arbitrary value of sign (shown as `_`) decides which 0 we’re dealing with:

\_0000000000000000000000000000000

Yes, the floating point standard specifies both +0.0 and −0.0. This concept is actually useful because it tells us from which “direction” the 0 was approached as a result of storing value too small to be represented in a `float`. For instance `-10e-30f / 10e30f` won’t fit in a `float`, however, it will produce the value of `-0.0`.

When working with zeros note that `0.0 == -0.0` is true even though the two zeros have different encoding. Additionally, `-0.0 + 0.0` is equal to `0.0`, so by default the compiler can’t optimize `a + 0.0` into just `a`, however, you can [set flags](https://stackoverflow.com/a/22135559/558816) to relax the strict conformance.

## Infinity

A `float` number with maximum biased exponent value *and* all zeros in significand is interpreted as positive or negative infinity depending on the value of the sign bit:

\_1111111100000000000000000000000

Infinity arises as a result of rounding a value that’s too large to fit in the type (assuming default rounding mode). In case of a `float`, any number in base-2 scientific notation with exponent greater than 127 will become infinity. You can also use macro `INFINITY` directly.

The positive and negative zeros become useful again since dividing a positive value by +0.0 will produce a positive infinity, while dividing it by −0.0 will produce a negative infinity.

Operations involving *finite* numbers and infinities are actually well defined and follow common sense property of keeping infinities infinite:

- any finite value added to or subtracted from ±infinity ends up as ±infinity
- any finite positive value multiplied by ±infinity ends up as ±infinity, while any finite negative value multiplied by ±infinity flips its sign to ∓infinity
- division by a finite non-zero value works similarly to multiplication (think of division as multiplication by an inverse)
- square root of a +infinity is +infinity
- any finite value divided by ±infinity will become ±0.0 depending on the signs of the operands

In other words, infinities are so big that any shifting or scaling won’t affect their infinite magnitude, only their sign may flip. However, some operations throw a wrench into that simple rule.

## NaNs

A `float` number with maximum biased exponent value *and* non-zero significand is interpreted as NaN – Not a Number:

\_11111111 at least one 1

The easiest way to obtain NaN directly is by using `NAN` macro. In practice though, NaN arises in the following set of operations:

- ±0.0 multiplied by ±infinity
- −infinity added to +infinity
- ±0.0 divided by ±0.0
- ±infinity divided by ±infinity
- square root of a negative number (−0.0 is fine though!)

If the floating point variable is uninitialized, it’s also somewhat likely to contain NaNs. By default the result of any operation involving NaNs will result in a NaN as well. That’s *one* of the reasons why compiler can’t optimize seemingly simple cases like `a + (b - b)` into just `a`. If `b` is NaN the result of the entire operation *has to* be NaN too.

NaNs are not equal to anything, even to themselves. If you were to look at your compiler’s implementation of `isnan` function you’d see something like `return x != x;`.

It’s worth pointing out how many different NaN values there are – a `float` can store 2 <sup>23</sup> −1 (over 8 million) different NaNs, while a `double` fits 2 <sup>52</sup> −1 (over 4.5 quadrillion) different NaNs. It may seem wasteful, but the standard specifically made the pool large for, quote, “uninitialized variables and arithmetic-like enhancements”. You can read about one of those uses in [Annie Cherkaev](https://anniecherkaev.com/about/) ’s very interesting [“the secret life of NaN”](https://anniecherkaev.com/the-secret-life-of-nan). Her article also discusses the concepts of quiet and signaling NaNs.

## Maximum & Minimum

The exponent range limit puts some constraints on the minimum and the maximum value that can be represented with a `float`. The maximum value of that type is 2 <sup>128</sup> − 2 <sup>104</sup> (3.40282347×10 <sup>38</sup>). The biased exponent is one short of maximum value and the significand is all lit up:

01111111011111111111111111111111

The smallest *normal* `float` is 2 <sup>−126</sup> (roughly 1.17549435×10 <sup>−38</sup>). Its biased exponent is set to 1 and the significand is cleared out:

00000000100000000000000000000000

In C the minimum and maximum values can be accessed with `FLT_MIN` and `FLT_MAX` macros respectively. While `FLT_MIN` is the smallest normal value, it’s not *the* smallest value a `float` can store. We can squeeze things down even more.

## Subnormals

When discussing base-2 scientific notation we assumed the numbers were normalized, i.e. the first digit of the significand was 1:

+1.00101100110110001101001×2 <sup>19</sup>

The range of subnormals (also known as denormals) relaxes that requirement. When the biased exponent is set to 0, the exponent is interpreted as −126 (*not* −127 despite the bias), and the leading digit is assumed to be 0:

+0.00000000000110001101001×2 <sup>−126</sup>

The encoding doesn’t change, when performing calculations we just have to remember that this time the implicit bit is 0 and not 1:

00000000000000000000110001101001

While subnormals let us store smaller values than the minimum normal value, it comes at the cost of precision. As the significand decreases we effectively have fewer bits to work with, which is more apparent after normalization:

+1.10001101001×2 <sup>−138</sup>

The classic example for the need for subnormals is based on simple arithmetic. If two floating point values are equal to each other:

x == y

Then by simply rearranging the terms it follows that their difference should be equal to 0:

x − y == 0

Without subnormal values that simple assumption would not be true! Consider `x` set to a valid normal `float` number:

+1.01100001111101010000101×2 <sup>−124</sup>

And `y` as:

+1.01100000011001011100001×2 <sup>−124</sup>

The numbers are distinct (observe the last few bits of significand). Their difference is:

+1.1000111101001×2 <sup>−132</sup>

Which is outside of the normal range of a `float` (notice the exponent value smaller than −126). If it wasn’t for subnormals the difference after rounding would be equal to 0, thus implying the equality of not equal numbers.

On a historical note, subnormals were very controversial part of the IEEE 754 standardization process, you can read about it more in [“An Interview with the Old Man of Floating-Point”](https://people.eecs.berkeley.edu/~wkahan/ieee754status/754story.html).

## Discrete Space

Due to the fixed number of bits in the significand floating point numbers can’t store arbitrarily precise values. Moreover, the exponential part causes the distribution of values in a `float` to be uneven. In the picture below each tick on the horizontal axis represents a unique float value:

![Chunky float values](https://ciechanow.ski/images/float_space.svg)

Chunky `float` values

Notice how the powers of 2 are special – they define the transition points for the change of “chunkiness”. The distance between representable `float` values in between neighboring powers of two (i.e. between 2 <sup>n</sup> and 2 <sup>n + 1</sup>) are constant and we can jump between them by changing the significand by 1 bit.

The larger the exponent the “larger” the 1 bit of significand is. For example, the number 0.5 has the exponent value of −1 (since 2 <sup>−1</sup> is 0.5) and 1 bit of its significand jumps by 2 <sup>−24</sup>. For the number 1.0 the step is equal to 2 <sup>−23</sup>. The width of the jump at 1.0 has a dedicated name – [machine epsilon](https://en.wikipedia.org/wiki/Machine_epsilon). For a `float` it can be accessed via `FLT_EPSILON` macro.

Starting at 2 <sup>23</sup> (decimal value of 8388608) increasing significand by 1 increases the decimal value of float by 1.0. As such, 2 <sup>24</sup> (16777216 in base-10) is the limit of the range of integers that can be stored in a `float` without omitting *any* of them. The next float has the value of 16777218, the value of 16777217 can’t be represented in a `float`:

![The end of the gapless region](https://ciechanow.ski/images/float_space_integers.svg)

The end of the gapless region

Note that the type can handle *some* larger integers as well, however, 2 <sup>24</sup> defines the end of the gapless region.

## Raw Integer Value

With a fixed exponent increasing the significand by 1 bit jumps between equidistant float values, however, the format has more tricks up its sleeve. Consider 2097151.875 stored in a `float`:

01001001111111111111111111111111

Ignoring the division into three parts for a second, we can think of the number as a string of 32 bits. Let’s try interpreting them as a 32-bit unsigned integer:

01001001111111111111111111111111

As a quick experiment, let’s add one to the value…

01001010000000000000000000000000

…and put the bits verbatim back into the `float` format:

01001010000000000000000000000000

We’ve just obtained the value of 2097152.0, which is the next representable `float` – the type can’t store *any* other values between this and the previous one.

Notice how adding one overflowed the significand and added one to the exponent value. This is the beauty of putting the exponent part *before* the significand. It lets us easily obtain the next/previous representable float (away/towards zero) by simply increasing/decreasing its raw integer value.

Incrementing the integer representation of the maximum `float` value by one? You get infinity. Decrementing the integer form of the minimum `float`? You enter the world of subnormals. Decrease it for the smallest subnormal? You get zero. Things fall into place just perfectly. The two caveats with this trick is that it won’t jump from +0.0 to −0.0 and vice versa, moreover, infinities will “increment” to NaNs, and the last NaN will increment to zero.

## Other Types

So far we’ve focused our discussion on a `float`, but its popular bigger cousin `double` and the less common `half` are also worth looking at.

## Double

In base-2 scientific notation a `double` has 53 digits of significand and exponent range of \[−1022, +1023\] resulting in an encoding with 11 bits dedicated to exponent and 52 bits to significand to form a 64-bit encoding:

1011111101001011000101101101100100111101101110100010001101101000

## Half

Half-float is used relatively often in computer graphics. In base-2 scientific notation a `half` has 11 digits of significand and exponent range of \[−14, +15\] resulting in an encoding with 5 bits dedicated to exponent and 10 bits to significand creating a 16-bit type:

0101101101010001

`half` is really compact, but also has very small range of representable values. Additionally, given only 5 bits of the exponent, almost 1/32 of the possible `half` values are dedicated to NaNs.

## Larger Types

IEEE 754 specifies [128-bit floating point format](https://en.wikipedia.org/wiki/Quadruple-precision_floating-point_format), however, native hardware support is [very limited](https://en.wikipedia.org/wiki/Quadruple-precision_floating-point_format#Hardware_support). Some compilers will [let you use it](https://godbolt.org/z/ATAFss) when `__float128` type is used, but the operations are usually done in software.

The standard also suggests equations for obtaining the number of exponent and significand bits in higher precision formats (e.g. [256-bit](https://en.wikipedia.org/wiki/Octuple-precision_floating-point_format)), but I think it’s fair to say those are rather impractical.

## Same Behavior

While all IEEE 754 types have different lengths, they all behave the same way:

- ±0.0 always has all the bits of the exponent and the significand set to zero
- ±infinity has all ones in the exponent and all zeros in the significand
- NaNs have all ones in the exponent and a non-zero significand
- the encoded exponent of subnormals is 0

The only difference between the types is in how many bits they dedicate to the exponent and to the significand.

## Conversions

While in practice many floating point calculations are performed using the same type throughout, a type change is often unavoidable. For example, JavaScript’s `Number` is just a `double`, however, WebGL deals with `float` values. Conversions to a larger and a smaller type behave differently.

## Conversion to a Larger Type

Since a `double` has more bits of the significand and of the exponent than a `float` and so does a `float` compared to a `half` we can be sure that converting a floating-point value to a higher precision type will maintain the exact stored value.

Let’s see how this pans out for a `half` value of 234.125. Its binary representation is:

0 101101101010001

The same number stored in a `float` has the following representation:

0 1000011011010100010000000000000

And in a `double`:

0100000001101101010001000000000000000000000000000000000000000000

Note that the new significand bits in a larger format are filled with zeros, which simply follows from scientific notation. The new exponent bits are filled with 0s when the highest bit is 1, and with 1s when the highest bit is 0 (you can see it by changing type e.g. for [0.11328125](https://float.exposed/0x2f40)) – a result of unbiasing the value with original bias then biasing again with the new bias.

## Conversion to a Smaller Type

The following should be fairly unsurprising, but it’s worth going through an example. Consider a `double` value of [−282960.039306640625](https://float.exposed/0xc111454028400000):

1100000100010001010001010100000000101000010000000000000000000000

When converting to a `float` we have to account for the significand bits that don’t fit, which is by default done using [rounding-to-nearest-even](https://en.wikipedia.org/wiki/Rounding#Round_half_to_even) method. As such, the same number stored in a `float` has the following representation:

1 1001000100010100010101000000001

The decimal value of this float is [−282960.03125](https://float.exposed/0xc88a2a01), i.e. a different number than the one stored in a `double`. Converting to a `half` produces:

1 111110000000000

What happened here? The exponent value of 18 that fits perfectly fine in a `float` is too large for the maximum exponent of 15 that a `half` can handle and the resulting value is −infinity.

Converting from a higher to a lower precision floating point type will maintain the exact value if the significand bits that don’t fit in the smaller type are 0s *and* the exponent value can be represented in the smaller type. If we were to convert the previously examined `234.125` from a `double` to a `float` or to a `half` it would keep its exact value in all three types.

### A Sidenote on Rounding

While [round-half-up](https://en.wikipedia.org/wiki/Rounding#Round_half_up) (“If the fraction is.5 – round up”) is the common rounding rule used in everyday life, it’s actually quite flawed. Consider the results of the following made up survey:

- 725 responders said their favorite color is red
- 275 responders said their favorite color is green

The distribution of votes is 72.5% and 27.5% respectively. If we wanted to round the percentages to integer values and were to use round-half-up we’d end up with the following outcome: 73% and 28%. To everyone’s dissatisfaction we just made the survey results add up to 101%.

Round-to-nearest-even solves this problem by, unsurprisingly, rounding to nearest even value. 72.5% becomes 72%, 27.5% becomes 28%. The expected sum of 100% is restored.

## Conversion of Special Values

Neither NaNs nor infinities follow the usual conventions. Their special rule is very straightforward: NaNs remain NaNs and infinities remain infinities in all the type conversions.

## Printing

Working with floating point numbers often requires printing their value so that it can be restored accurately — every bit should maintain its exact value. When it comes to `printf` -style formatting characters, `%f` and `%e` are commonly used. Sadly, they often fail to maintain enough precision:

```objc
float f0 = 3.0080111026763916015f;
float f1 = 3.0080118179321289062f;

printf("%f\n", f0);
printf("%f\n", f1);
printf("%e\n", f0);
printf("%e\n", f1);
```

Produces:

```plain
3.008011
3.008011
3.008011e+00
3.008011e+00
```

However, those two floating point numbers are *not* the same and store different values. `f0` is:

01000000010000001000001101000001

And `f1` differs from `f0` by 3:

01000000010000001000001101000100

The usual solution to this problem is to specify the precision manually to the maximum number of digits. We can use `FLT_DECIMAL_DIG` macro (value of 9) for this purpose:

```objc
float f0 = 3.0080111026763916015f;
float f1 = 3.0080118179321289062f;

printf("%.*e\n", FLT_DECIMAL_DIG, f0);
printf("%.*e\n", FLT_DECIMAL_DIG, f1);
```

Yields:

```plain
3.008011102e+00
3.008011817e+00
```

Unfortunately, it will print the long form even for simple values, e.g. `3.0f` will be printed as `3.000000000e+00`. It seems that [there is no way](https://stackoverflow.com/a/19897395/558816) to configure the printing of floating point values to automatically maintain exact number of *decimal* digits needed to accurately represent the value.

## Hexadecimal Form

Luckily, hexadecimal form comes to the rescue. It uses `%a` specifier and prints the shortest, exact representation of floating point number in a hexadecimal form:

```objc
float f0 = 3.0080111026763916015f;
float f1 = 3.0080118179321289062f;

printf("%a\n", f0);
printf("%a\n", f1);
```

Produces:

```plain
0x1.810682p+1
0x1.810688p+1
```

The hexadecimal constant can be used verbatim in code or as an input to `scanf` \\ `strtof` on any reasonable compiler and platform. To verify the results we can fire up LLDB one more time:

```plain
(lldb) p 0x1.810682p+1f
(float) $0 = 3.0080111

(lldb) p 0x1.810688p+1f
(float) $1 = 3.00801182

(lldb) p/t *(uint32_t *)&$0
(uint32_t) $2 = 0b01000000010000001000001101000001

(lldb) p/t *(uint32_t *)&$1
(uint32_t) $3 = 0b01000000010000001000001101000100
```

The hexadecimal form is exact and concise – each set of four bits of the significand is converted to the corresponding hex digit. Using our example values: `1000` becomes `8`, `0001` becomes `1` and so on. An unbiased exponent just follows the letter `p`. You can find more details about the `%a` specifier in [“Hexadecimal Floating-Point Constants”](https://www.exploringbinary.com/hexadecimal-floating-point-constants/).

Nine digits may be enough to *maintain* the exact value, but it’s nowhere near the number of digits required to show the floating point number in its *full* decimal glory.

## Exact Decimal Representation

While not every decimal number can be represented using floating point numbers (the infamous 0.1), *every* floating point number has its own exact decimal representation. The following example is done on a `half` since it’s much more compact, but the method is equivalent for a `float` and a `double`.

Let’s consider the value of 3.142578125 stored in a `half`:

0100001001001001

The equivalent value in scientific base-2 notation is:

+1.1001001001×2 <sup>1</sup>

Firstly, we can convert the significand part to an integer by multiplying it by 1:

1.1001001001×1

Which we can cleverly expand:

1.1001001001×2 <sup>10</sup> ×2 <sup>−10</sup>

To obtain an integer times a power of two:

11001001001 <sub>2</sub> ×2 <sup>−10</sup>

Then we can combine the fractional part with the exponent part:

11001001001 <sub>2</sub> ×2 <sup>−10</sup> ×2 <sup>1</sup>

And in decimal form:

1609×2 <sup>−9</sup>

We can get rid of the power of two by multiplying it by a cleverly written value of 1 yet another time:

2 <sup>−9</sup> ×5 <sup>−9</sup> × 5 <sup>9</sup>

We can pair every 2 with every 5 to obtain:

10 <sup>−9</sup> ×5 <sup>9</sup>

Putting back all the pieces together we end up with a product of two integers and a shift of a decimal place encoded in the power of 10:

10 <sup>−9</sup> ×5 <sup>9</sup> ×1609 = 3.142578125

Coincidentally, the trick of multiplying by 5 <sup>−n</sup> ×5 <sup>n</sup> also explains why negative powers of 2 are just powers of 5 with a shifted decimal place (e.g. 1/4 is 25/100, and 1/16 is 625/10000).

Even though the exact decimal representation always exists, it’s often cumbersome to use – some small numbers that can be stored in a `double` have [over 760 significant digits](https://float.exposed/0x000fffffffffffff) of decimal representation!

## Further Reading

My article is just a drop in the sea of resources about floating point numbers. Perhaps the most thorough technical write-ups on floating point numbers is [“What Every Computer Scientist Should Know About Floating-Point Arithmetic”](https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html). While very comprehensive, I find it difficult to get through. Almost five years have passed since I first [mentioned it](https://ciechanow.ski/exploring-gpgpu-on-ios/#reasons) on this blog and, frankly, I’ve still limited my engagement to mostly skimming through it.

One of the most fascinating resources out there is [Bruce Dawson](https://twitter.com/BruceDawson0xB) ’s amazing [series of posts](https://randomascii.wordpress.com/category/floating-point/). Bruce dives into a ton of details about the format and its behavior. I consider many of his articles a must-read for any programmer who deals with floating point numbers on a regular basis, but if you only have time for one I’d go with [“Comparing Floating Point Numbers, 2012 Edition”](https://randomascii.wordpress.com/2012/02/25/comparing-floating-point-numbers-2012-edition/).

[Exploring Binary](https://www.exploringbinary.com/) contains many detailed [articles on floating point format](https://www.exploringbinary.com/tag/floating-point/). As a delightful example, it [demonstrates](https://www.exploringbinary.com/maximum-number-of-decimal-digits-in-binary-floating-point-numbers/) that the maximum number of significant digits in the decimal representation of a `float` is 112, while a `double` requires up to 767 digits.

For a different look on floating point numbers I recommend [Fabien Sanglard](https://twitter.com/fabynou) ’s [“Floating Point Visually Explained”](http://fabiensanglard.net/floating_point_visually_explained/) – it shows an interesting concept of the exponent interpreted as a sliding window and the significand as an offset into that window.

## Final Words

Even though we’re done, I encourage you to go on. Any of the mentioned resources should let you discover something more in the vast space of floating point numbers.

The more I learn about IEEE 754 the more enchanted I feel. [William Kahan](https://en.wikipedia.org/wiki/William_Kahan) with the aid of Jerome Coonen and Harold Stone created something truly beautiful and ever-lasting.

I genuinely hope this trip through the details of floating point numbers made them a bit less mysterious and showed you some of that beauty.
