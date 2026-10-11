---
title: "Character Counts: Why “30 Characters Max” Is Usually Wrong"
source: "https://americanexpress.io/character-counts-why-30-characters-max-is-usually-wrong/"
author:
published: 2026-08-18
created: 2026-10-05
description: "How to define, count, and validate text-field limits with grapheme clusters."
tags:
  - "clippings"
---

> [!summary]
> A requirement like "30 characters max" is ambiguous because Unicode distinguishes code units, code points, glyphs, and grapheme clusters, and a plain `length` call usually counts code units, so emoji and combining marks inflate the count. The article argues user-facing counters should count grapheme clusters (UAX #29) the same way in the UI and the backend, and gives reference implementations in Kotlin/Java (ICU4J), Go, Swift, Python, and TypeScript (`Intl.Segmenter`) along with a shared QA case list. It also stresses that a grapheme limit needs a separate UTF-8 byte limit, since a single grapheme like `กัััััััััั` can keep growing in bytes without its count changing.

Every engineer has implemented a text field with a character limit. Most of us have also written something like text length <= 30 without thinking twice. Then someone pastes in an emoji. Suddenly the UI says there’s still room left, another client rejects the same input, or the backend refuses text that appeared to be valid.

When a requirement says “30 characters max,” the real problem is deciding what “character” means. Unicode distinguishes between code points, code units, glyphs, and grapheme clusters, and those units are not interchangeable.[^1] [^2]

For most user-facing counters, what is meant by “character” is much closer to a grapheme cluster: the default Unicode unit for user-perceived characters.[^2:1]

This article explains the differences between those text units, why they matter when writing product requirements, and how to implement and test character limits that behave consistently across clients and backends.

## The bug hiding in a simple requirement

Imagine this requirement:

> Add a **List name** field with a maximum length of **30 characters** and show a live counter below the field.

A first implementation in Compose might look like this:

```kotlin
Column {
    var listName by remember { mutableStateOf("") }
    val listNameLength = listName.length
    val maxLength = 30
    val isTooLong = listNameLength > maxLength

    OutlinedTextField(
        modifier = Modifier.width(400.dp),
        value = listName,
        onValueChange = { listName = it },
        label = { Text("List Name") },
        isError = isTooLong,
    )

    Text(
        text = "Count: $listNameLength/$maxLength",
        color = if (isTooLong) Color.Red else Color.Unspecified,
    )
}
```

At first, the implementation appears correct:

![Compose text field before emoji input](https://americanexpress.io/_post_assets/character-counts-why-30-characters-max-is-usually-wrong/img/compose-list-name-1.gif)

Then someone pastes in emoji:

![Compose text field with emoji input and inflated count](https://americanexpress.io/_post_assets/character-counts-why-30-characters-max-is-usually-wrong/img/compose-list-name-2.gif)

The resulting behavior is usually traced back to the requirement rather than the rendering code. The UI is counting one text unit while the product requirement is written as if there were only one obvious way to count characters.

At the product level, this creates an inconsistent user experience. One client may show room left while another rejects the same input, or the backend may reject text that the UI appeared to accept. Rather than reflecting incorrect Unicode handling, the discrepancy comes from different parts of the system enforcing different interpretations of the same requirement.

## Choosing the right text unit

| Unit | What it means | Good for | Bad for |
| --- | --- | --- | --- |
| **Code point** | A Unicode value such as `U+1F44D` | Unicode properties, parsing, low-level text logic | UI counters |
| **Code unit** | A storage unit in an encoding such as UTF-8 or UTF-16 | API internals, storage details | UI counters |
| **Glyph** | A shape drawn by the font | Rendering and typography | Validation rules |
| **Grapheme cluster** | The Unicode default for a user-perceived character | Text counters, caret movement, deletion | Byte limits |

Examples make the difference obvious:

| Text | Why it is tricky | Code points | Graphemes |
| --- | --- | --- | --- |
| `e + U+0301` | Base letter plus combining acute accent | 2 | 1 |
| `👍` | Single emoji outside the Basic Multilingual Plane (BMP) | 1 | 1 |
| `✌️` | Symbol plus variation selector | 2 | 1 |
| `🇺🇸` | Two regional indicators make one flag | 2 | 1 |
| `👩🏽‍💻` | Emoji plus skin-tone modifier plus zero-width joiner (ZWJ) plus emoji | 4 | 1 |
| `👨‍👩‍👧‍👦` | Multiple emoji joined into one family | 7 | 1 |

Switching from code units to code points does not solve the underlying product problem. If the requirement is intended to match what users perceive as characters, the counter still needs to follow grapheme-cluster boundaries.[^2:2]

That does not make code-unit or byte limits “wrong.” Some systems use them intentionally for compatibility with storage, transport, or downstream APIs. The real problem is ambiguity in the requirement. Teams need to say explicitly which unit each limit is using.

## Why glyph count is not the answer

Glyphs are for rendering, not product limits. The same text can render as a different number of glyphs depending on the font. Ligatures are the classic example. For example, ffi may render as three glyphs or as a single ligature glyph, but for most product requirements it is still three user-perceived letters.[^1:1]

## What the requirement should say instead

Here is a version that removes the ambiguity:

> The **List name** field accepts up to **30 grapheme clusters**. The visible counter and validation use the same grapheme-counting rule. Truncation, cursor movement, selection, and deletion must not split a grapheme cluster. The backend enforces the same rule.

That requirement is longer, but it is much easier to implement consistently.

## Normalization is a separate decision

Unicode normalization answers a different question: whether two different code point sequences should be treated as equivalent for comparison, search, storage, or validation.[^3] It is worth deciding explicitly, but it should not be folded into “character count” as if they were the same problem.

For example, `e + U+0301` and `é` are different code-point sequences, but they still count as one grapheme cluster. Normalization matters for equivalence policy; it does not change the basic unit a user-facing counter should use.[^3:1]

This matters any time you store and compare input over time. If you hash a password, compare stored values later, or build search behavior on top of user input, decide whether canonically equivalent forms should be treated as the same value before you ship.[^3:2]

## Practical guidance for teams

Use the following as a working checklist before you ship any user-facing character limit.

### Product checklist

- Do not stop at “30 characters.” Ask what unit is being counted.
- Make sure the UI and backend use the same counting rule.
- Require shared test cases with expected counts.

### Engineering checklist

- Do not use `length` for a user-facing counter unless the requirement explicitly means code units or code points.
- Count grapheme clusters with a Unicode-aware API or library.
- Make backspace, cursor movement, truncation, and validation follow the same grapheme boundaries.
- Keep the exact same test cases across web, iOS, Android, API, and backend.

Those engineering checks only work if the implementation is using a Unicode-aware segmentation rule instead of a raw string-length function.[^2:3]

## Reference implementations

The examples below all count grapheme clusters. They are intentionally minimal and should still be validated against shared test cases before being used in production.

### Kotlin

Use ICU4J `BreakIterator` to segment text on grapheme boundaries.[^4]

```kotlin
// Gradle:
// implementation("com.ibm.icu:icu4j:78.3")

import com.ibm.icu.text.BreakIterator
import java.util.Locale

fun graphemeCount(text: String): Int {
    val iterator = BreakIterator.getCharacterInstance(Locale.ROOT)
    iterator.setText(text)

    var count = 0
    while (iterator.next() != BreakIterator.DONE) {
        count += 1
    }
    return count
}
```

This example uses ICU4J explicitly so the same approach works across JVM environments. If your platform already exposes ICU-backed grapheme APIs, you may be able to use the platform implementation instead.[^4:1]

### Java

The same ICU4J approach works in Java.[^4:2]

```java
// Gradle:
// implementation("com.ibm.icu:icu4j:78.3")

import com.ibm.icu.text.BreakIterator;
import java.util.Locale;

public final class Graphemes {
    public static int graphemeCount(String text) {
        BreakIterator iterator = BreakIterator.getCharacterInstance(Locale.ROOT);
        iterator.setText(text);

        int count = 0;
        while (iterator.next() != BreakIterator.DONE) {
            count++;
        }
        return count;
    }
}
```

### Go

The `clipperhouse/uax29` package exposes grapheme iteration based on Unicode text-segmentation rules.[^5]

```go
// go get github.com/clipperhouse/uax29/v2/graphemes

package main

import "github.com/clipperhouse/uax29/v2/graphemes"

func graphemeCount(text string) int {
    count := 0
    tokens := graphemes.FromString(text)
    for tokens.Next() {
        count++
    }
    return count
}
```

### Swift

Swift `String` is a collection of extended grapheme clusters, so `count` is the right default for this use case.[^6]

```swift
func graphemeCount(_ text: String) -> Int {
    text.count
}
```

### Python

The third-party `regex` module supports `\X`, which matches an extended grapheme cluster.[^7]

```python
# pip install regex

import regex

def grapheme_count(text: str) -> int:
    return len(regex.findall(r"\X", text))
```

### TypeScript

`Intl.Segmenter` provides grapheme segmentation in JavaScript runtimes that implement it. Check your browser and Node support matrix before you rely on it without a fallback.[^8]

```typescript
function graphemeCount(text: string): number {
  const segmenter = new Intl.Segmenter(undefined, { granularity: "grapheme" });
  return [...segmenter.segment(text)].length;
}
```

## Shared QA cases are worth the effort

If different clients and services all enforce the same limit, they should share the same test cases.

| Example | Why it belongs in the QA cases |
| --- | --- |
| `e + U+0301` and `é` | Same visible result, different underlying representation |
| `✌` and `✌️` | Variation selector changes presentation |
| `🇺🇸` | Two code points, one flag |
| `👩🏽‍💻` | Modifier plus ZWJ sequence |
| `👨‍👩‍👧‍👦` | One visible family, many internal units |
| `ffi` and `ﬃ` | Ligatures are rendering concerns, not UI character-count rules |
| `क्‍ष` | Script-specific conjunct and joiner behavior |
| `กัััััััััั` | One grapheme cluster that grows to 33 UTF-8 bytes |
| `À̖᪰` | Multiple combining marks on one base |
| `grocery​list` | Contains `U+200B ZERO WIDTH SPACE`, so a grapheme-aware counter will count one more invisible unit |

Writing down the expected counts before implementation is useful because it forces the product rule to become explicit.

It is also worth recording the Unicode or ICU version behind each implementation. Grapheme-boundary behavior can change as Unicode evolves, so shared test cases should be re-checked when those dependencies move forward.[^2:4]

## Why encoded-size limits still matter

A grapheme limit is usually the right **UI** rule, but it is not enough by itself. [OWASP](https://owasp.org/) still recommends validating input and defining minimum and maximum lengths for strings.[^9] For text fields like this, teams often end up needing:

1. a grapheme-cluster limit for user experience, and
2. a separate encoded-size byte limit for API, storage, and processing safety.

That is why a grapheme limit is not a substitute for a byte limit.

As a practical starting heuristic, a byte limit of about **10x** the grapheme limit is often reasonable for fields that need to support emoji-rich text. That is not a Unicode rule; it is a product and security tradeoff. For stricter allow-lists, such as some password fields, a smaller multiplier may be the better choice.

## One grapheme can keep growing in bytes

UAX #29’s extended grapheme-cluster rules keep a base character and its following combining marks in the same cluster.[^2:5] That means a single grapheme can keep absorbing more marks without the grapheme count changing.

A useful stress case is `กัััััััััั`. It is:

1. 1 grapheme cluster,[^2:6]
2. 11 code points, and
3. 33 bytes in UTF-8.[^10]

Why 33 bytes? The string starts with `ก` and then repeats the Thai mark `ั` ten times. All 11 code points are in the `U+0800` to `U+FFFF` range, so UTF-8 encodes each one using 3 bytes.[^10:1] Add one more `ั`, and the grapheme count still stays at 1 while the encoded size grows to 36 bytes. In principle, you can keep doing that: the grapheme count stays fixed at 1 while the byte count keeps growing by 3 bytes each time.

This is not normal Thai prose. It is a deliberately adversarial test case. But that is exactly the point: a product rule such as “30 grapheme clusters max” does not, by itself, protect request size, storage, or downstream systems.

## One QA case that checks both limits

If a field allows up to **30 grapheme clusters** and up to **32 UTF-8 bytes**, copy and paste this exact string into your QA cases:

```
กัััััััััั
```

Expected result:

1. The visible counter should show `1/30`.
2. Any grapheme-based validation should pass.
3. Any 32-byte encoded-size validation should fail, because the string is 33 bytes in UTF-8.
4. UI, API, and storage-layer validation should all agree on that outcome.

If your system uses a different byte threshold, choose a limit below the encoded size of the string and follow the same process.

## Conclusion

There is no single universal way to count “characters.” There are code points, code units, glyphs, grapheme clusters, and bytes, and each answers a different question.

For most text-field counters, grapheme clusters are the best fit because they track what users usually perceive as characters.[^2:7] Once that rule is explicit, the counter, validation, deletion behavior, backend checks, and QA cases can all line up around the same definition.

[^1]: Unicode Glossary definitions for code point, grapheme cluster, glyph, and ligature: [https://unicode.org/glossary/](https://unicode.org/glossary/)

[^2]: Unicode Standard Annex #29, *Unicode Text Segmentation*: [https://www.unicode.org/reports/tr29/](https://www.unicode.org/reports/tr29/)

[^3]: Unicode Standard Annex #15, *Unicode Normalization Forms*: [https://www.unicode.org/reports/tr15/](https://www.unicode.org/reports/tr15/)

[^4]: ICU4J `BreakIterator` documentation: [https://unicode-org.github.io/icu-docs/apidoc/released/icu4j/com/ibm/icu/text/BreakIterator.html](https://unicode-org.github.io/icu-docs/apidoc/released/icu4j/com/ibm/icu/text/BreakIterator.html)

[^5]: `clipperhouse/uax29/v2/graphemes` package documentation: [https://pkg.go.dev/github.com/clipperhouse/uax29/v2/graphemes](https://pkg.go.dev/github.com/clipperhouse/uax29/v2/graphemes)

[^6]: Apple Swift `String` documentation: [https://developer.apple.com/documentation/swift/string](https://developer.apple.com/documentation/swift/string)

[^7]: Python `regex` package documentation: [https://pypi.org/project/regex/](https://pypi.org/project/regex/)

[^8]: ECMA-402 `Intl.Segmenter` specification: [https://tc39.es/ecma402/#segmenter-objects](https://tc39.es/ecma402/#segmenter-objects)

[^9]: OWASP Input Validation Cheat Sheet: [https://cheatsheetseries.owasp.org/cheatsheets/Input\_Validation\_Cheat\_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)

[^10]: RFC 3629, *UTF-8, a transformation format of ISO 10646*, specifies that code points from `U+0800` to `U+FFFF` are encoded using three octets in UTF-8: [https://www.rfc-editor.org/rfc/rfc3629](https://www.rfc-editor.org/rfc/rfc3629)
