---
title: "The Bedrock of Software Design"
source: "https://alex.draftist.io/blog/the-bedrock-of-software-design-ycqvcedsj"
author:
  - "[[Alex Fedoseev]]"
published:
created: 2026-09-16
description: "A simple concept that makes software easier to understand, harder to misuse, and safer to change."
tags:
  - "clippings"
---

> [!summary]
> Alex Fedoseev argues that algebraic data types — sum types above all — have shaped how he designs software more than anything else. Uses Rust and TypeScript examples to show making invalid states unrepresentable, putting expected failures in the signature via `Result`, giving absence a type via `Option`, and relying on exhaustive pattern matching so that a domain change turns into a compiler-generated list of every site that must be reviewed.

Nothing has influenced the way I design software more than **algebraic data types**.

It sounds overly academic—the kind of term that makes people roll their eyes or scares them away altogether. But honestly, it only sounds scary. The idea itself is quite simple, and learning it showed me a fundamentally better way to build software.

A few years ago, I even started recording a video series about ADTs. I finished one and a half episodes; then life happened. Consider this post the written and compressed version I should have finished years ago.

## Theory

I hate doing this part. Theory is boring most of the time, and I would rather jump straight to the good stuff. You can skip this section entirely, to be honest. But I need to lay down a couple of terms so they do not make you go “WTF?” later. I’ll keep it short and on-point.

There are two fundamental kinds of algebraic data types.

### Product types

Product types are roughly what objects look like in mainstream languages—roughly, because objects often come with extra baggage.

```
struct User {
    id: UserId,
    role: Role,
}
```

A `User` has an `id` **and** a `role`. Every `User` contains both—that is what makes it a product type.

### Sum types

The king!

A sum type says that a value is one of several possible variants:

```
enum Session {
    Anonymous,
    Authenticated { user: User },
}
```

A `Session` is either `Anonymous` **or** `Authenticated`. Better yet, every variant can carry its own data: a `User` exists only when the session is `Authenticated`.

Most of the benefits in this post come from this one deceptively simple idea.

Okay. Theory over. Let’s get to the good stuff: why these things are actually useful.

## Let types enforce the rules

Every non-trivial domain is full of rules. Some values must exist together. Others must never exist at the same time. Sometimes which fields are required depends on the value of another field.

Too often, these rules live only in code comments, documentation, validation functions, or developers’ heads. That is fragile as hell, because documentation gets outdated, validation gets skipped, and people forget.

A well-designed sum type encodes rules into the type itself. Anyone reading it can see which values can exist and how they fit together, while the compiler rejects everything else. Often, the type is all the documentation you need.

To make it clear what I mean, let’s take the color settings for a website. A site can either let visitors switch between light and dark modes or use one fixed mode.

A switchable site needs a default mode and color schemes for both modes. A fixed site needs one mode and one scheme.

We could model that with a boolean and a pile of nullable fields:

```
type SiteTheme = {
    switchable: boolean;
    defaultMode: ColorMode | null;
    lightScheme: ColorScheme | null;
    darkScheme: ColorScheme | null;
    fixedMode: ColorMode | null;
    fixedScheme: ColorScheme | null;
};
```

This type allows many nonsensical configurations. A switchable theme can be missing one of its schemes. A fixed theme can have no fixed scheme. Both configurations can be present at the same time, or every nullable field can be `null`. The type accepts all of it.

To know which combinations are actually valid, you need documentation, validation, or tribal knowledge. Every part of the program that receives this value must either trust that someone checked it earlier or defend itself against complete nonsense.

Now let’s model what the domain actually says:

```
enum SiteTheme {
    Switchable {
        default_mode: ColorMode,
        light_scheme: ColorScheme,
        dark_scheme: ColorScheme,
    },
    Fixed {
        mode: ColorMode,
        scheme: ColorScheme,
    },
}

enum ColorMode {
    Light,
    Dark,
}
```

The type describes exactly two possibilities.

A `Switchable` theme always has a default mode and both schemes. A `Fixed` theme always has one mode and one scheme. Required values can’t be omitted, and fields from one configuration can’t leak into the other. Every `SiteTheme` value satisfies these rules. Guaranteed.

This is what “make invalid states unrepresentable” means: instead of worrying about nonsense, design the type so it cannot exist in the first place.

## Make errors part of the contract

A function’s signature should describe not only what it returns when it succeeds, but also whether it can fail.

In languages built around exceptions, the return type usually describes only the happy path:

```
function parsePort(value: string): number {
    const port = Number(value);

    if (!Number.isInteger(port) || port < 1 || port > 65535) {
        throw new Error("Invalid port");
    }

    return port;
}
```

From the function signature alone, we see only that `parsePort` returns a number. To discover that it can fail, we have to read its documentation or, better yet, inspect its implementation. We may also need to inspect every function it calls, since any of them might throw an exception of its own.

Honestly, I go into paranoid mode whenever I work in an exception-based language. Literally any function call can throw a surprise punch, and nothing at the call site tells me whether I should brace for it.

Rust makes a useful distinction between two kinds of failure. An unrecoverable failure means the program cannot reasonably continue and causes a panic. An expected, recoverable failure is a normal possibility the caller may know how to handle, such as invalid input or a missing file.

For expected failures, a `Result` type makes both possible outcomes explicit:

```
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

`T` represents the successful value, while `E` represents the error. Because `E` can be any type, we can use another sum type to describe every expected failure precisely:

```
enum ParsePortError {
    NotANumber,
    OutOfRange {
        min: u16,
        max: u16,
    },
}

fn parse_port(value: &str) -> Result<u16, ParsePortError> {
    // ...
}
```

An error variant can also carry data relevant to that particular failure. `OutOfRange` includes the limits accepted by the parser, so the caller can explain the requirement without duplicating that knowledge. `NotANumber` has no additional context to provide. Each error brings exactly the information it can guarantee.

The signature now tells the whole story. The function can return a port, fail because the input is not a number, or fail because the number is outside the allowed range.

The caller cannot access the port without dealing with the `Result`. It must either handle the error or deliberately pass it to its own caller. Expected failures can no longer remain hidden in the implementation.

The important part is not merely that a `Result` type exists—we could define a similar type in TypeScript. In Rust, returning a `Result` is the idiomatic way to represent an expected failure. The standard library and the wider ecosystem follow the same convention.

This keeps the contract explicit across the entire call chain. The functions you call return their expected failures as values, and your function must handle or propagate them. In an exception-based ecosystem, that certainty disappears as soon as one dependency throws.

## Give absence a type

The absence of a value is a valid possibility and should be represented as explicitly as any other state.

JavaScript has both `null` and `undefined`, and APIs use them inconsistently, leaving callers to remember which form of absence to expect and check for. Tony Hoare, who introduced null references, famously called them his “billion-dollar mistake.”

Rust has neither `null` nor `undefined` in ordinary code. It represents absence with another sum type:

```
enum Option<T> {
    Some(T),
    None,
}
```

A signature such as this tells the whole story:

```
fn find_user(id: UserId) -> Option<User> {
    // ...
}
```

The function may return a user or no user. Absence has one representation, visible in the type, and the caller cannot access the `User` without handling both possibilities.

When absence is all the caller needs to know, `Option` is enough. When the reason matters, `Result` describes it.

The two can also be combined. If not finding a user is an expected outcome but the lookup itself can fail, the function can represent all three outcomes explicitly:

```
fn find_user(id: UserId) -> Result<Option<User>, FindUserError> {
    // ...
}
```

`Ok(Some(user))` means the user was found, `Ok(None)` means no matching user exists, and `Err(error)` means the lookup failed. Three different outcomes, with no ambiguity between them.

## Handle every possible case

Representing every valid state is only half the story. We also need to handle every state without accidentally forgetting one.

Pattern matching lets us consider each possibility separately. In Rust, a `match` must be exhaustive: the compiler rejects it unless every possible case is covered.

For example, we have three possible results from `parse_port`: a valid port, a value that is not a number, or a number outside the accepted range.

```
match parse_port(input) {
    Ok(port) => {
        println!("Using port {port}");
    }
    Err(ParsePortError::NotANumber) => {
        eprintln!("Port must be a number");
    }
    Err(ParsePortError::OutOfRange { min, max }) => {
        eprintln!("Port must be between {min} and {max}");
    }
}
```

Each branch has access to exactly the data available in that case. `port` exists only in the successful branch, while `min` and `max` exist only for `OutOfRange`. No null checks or type casts are needed.

If we remove any branch, the program stops compiling. The type defines every possible outcome, and pattern matching ensures that the code accounts for all of them.

## Let the compiler guide changes

Application models change all the time. Adding a new possibility is usually easy. The difficult part is finding every piece of code whose assumptions are now outdated.

Suppose an application initially has two user roles:

```
enum Role {
    User,
    Admin,
}
```

When banning a user, we handle the roles directly inside that operation:

```
fn ban_user(
    user_id: UserId,
    current_user: User,
) -> Result<(), BanUserError> {
    match current_user.role {
        Role::User => Err(BanUserError::NotAllowed),
        Role::Admin => // Ban the user...
    }
}
```

Later, we introduce a staff role:

```
enum Role {
    User,
    Staff,
    Admin,
}
```

The existing `match` no longer compiles. The compiler points to the banning operation and forces us to decide what `Staff` means in this particular context.

```
match current_user.role {
    Role::User => Err(BanUserError::NotAllowed),
    Role::Admin => // Ban the user...
}
```
```
error[E0004]: non-exhaustive patterns: \`Role::Staff\` not covered
```

Perhaps staff members can ban regular users but not administrators. Perhaps they can only ban users from the same organization. Because the match is located inside the actual operation, we have the surrounding context needed to make that decision.

The compiler does this for every exhaustive match on `Role` throughout the codebase. Its errors become a list of places that must be reviewed. We do not have to remember where roles affect behavior or hope that a text search finds every relevant condition.

With strings, booleans, and loosely related fields, adding a new state often leaves old code compiling with outdated assumptions. With a sum type and exhaustive matching, a change to the domain propagates through the program.

## Focus on one case at a time

This is probably less relevant now that we have LLMs, but it was huge for me when I was writing code by hand. Exhaustive matching removed a lot of mental overhead.

When several inputs affect a result, the difficult part is often not handling any individual case. It is keeping track of every possible combination.

Suppose delivery time depends on both the destination and shipping speed:

```
enum Destination {
    Domestic,
    International,
}

enum ShippingSpeed {
    Standard,
    Express,
}
```

We can match on both inputs at once:

```
fn delivery_days(
    destination: Destination,
    speed: ShippingSpeed,
) -> u8 {
    match (destination, speed) {
        (Destination::Domestic, ShippingSpeed::Standard) => 3,
        (Destination::Domestic, ShippingSpeed::Express) => 1,
        (Destination::International, ShippingSpeed::Standard) => 10,
        (Destination::International, ShippingSpeed::Express) => 3,
    }
}
```

Once the inputs are listed in the `match`, the compiler takes responsibility for tracking their combinations. I can focus entirely on one case, decide what it should do, and then move to the next. I do not have to keep asking myself whether I missed something—the code will not compile until every combination is covered.

This makes a surprisingly large difference to how it feels to solve complex logic. The real work is correctly identifying which inputs affect the output. Once that is done, handling their possible combinations is mostly mechanical. The compiler holds the checklist, leaving me to concentrate on the case directly in front of me.

Good domain modeling is important here. The match should contain only meaningful combinations. If a combination is impossible in the domain, the types should make it impossible in the code too.

With a loose collection of strings, booleans, and nullable values, many combinations may be nonsensical, and an `if` / `else` chain provides no general guarantee that every valid combination has been considered.

---

I really hope I managed to show how this elegant yet simple concept can improve the software we build. After working this way, I can’t see sum types and exhaustive matching as nice extras. They are the baseline I want from a programming language.

The video series is still stuck at one and a half episodes. At least this post finally has an ending.
