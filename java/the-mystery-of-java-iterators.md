---
title: "The mystery of Java iterators"
source: "https://ericnormand.substack.com/p/the-mystery-of-java-iterators?utm_source=post-email-title&publication_id=2076847&post_id=148229069&utm_campaign=email-post-title&isFreemail=true&r=8x3s&triedRedirect=true"
author:
  - "[[Eric Normand]]"
published: 2024-09-24
created: 2026-02-25
description: "Why weren't they made more powerful?"
tags:
  - "clippings"
  - "java"
  - "data-structures"
  - "api-design"
---

> [!summary]
> Explores why Java's iterator abstraction—similar to Clojure's seq—was never extended with map/filter/reduce operations despite being technically capable. The author proposes ideas including lack of closures, fear of higher-order programming, mutability issues, and cultural resistance to composition.

### Why weren't they made more powerful?

I published some major updates to the [Composition Lens Part 1](https://ericnormand.me/domain-modeling/Composition-Lens/index.html) chapter. Some of the content has moved to Composition Lens Part 2 (upcoming).

Last week, I put in the wrong link to buy Clojure/conj tickets. Here’s the right link to [buy tickets](https://ti.to/nubank/clojureconj-2024).

[Heart of Clojure](https://2024.heartofclojure.eu/) was amazing. Thanks to Leuven for the great location and hospitality, the venues, the organizers, the volunteers, the speakers, and the attendees for making it the best conference I’ve been to.

---

I remember when I first learned about Clojure, the seq construct was amazing. It seemed to unify the CAR/CDR interface of Lisp’s linked lists with Java iterators. It freed our programs from the concrete CONS representation, but allowed the same powerful abstract interface over all collections.

Recently, I was learning about Java streams because Clojure now provides [functions for consuming Java streams](https://clojure.org/reference/java_interop#streams). Streams seem pretty cool. They were introduced in 2014 with the suite of functional features called Java 8. Streams support parallelizing of operations and a “declarative” API.

But Java has had iterators since Java 2, 16 years before streams. They’re useful for iterating over collections, but not much else. Why did Java not do more with iterators before the introduction of Streams? It is a mystery to me, but I have some ideas.

As background, Java iterators were introduced in Java 1.2 (1998). They’re essentially the same as Clojure’s seq. They have two primary operations, `next()` and `hasNext()`. You first call `hasNext()` to see if there are any more. If it returns true, you call `next()` to get the next thing and advance the iterator. Repeat until `hasNext()` returns false.

Here’s an example:

```markup
List list = ...;
for (Iterator it = list.iterator(); it.hasNext(); ) {
    String element = (String)it.next();
    ...
}
```

The main difference with Clojure’s seq is that iterators are stateful. The same object “advances” over the elements, while a seq is itself an immutable object that points to the `first` and the `rest`.

In Java 1.5 (2004), for loop syntax was extended to work on iterators (and generics made casting unnecessary).

```markup
List<String> list = ...;
for (String element : list) {
    ...
}
```

As far as I can tell, this was the only innovation regarding iterators since their release. (I don’t count the bi-directional iterators of Java 6 because only sorted collections implemented them).

Iterators even had an equivalent to the Clojure idea of “seqable.” There is a related interface in Java called `Iterable` which means you could get an iterator from an object by calling the `.iterator()` method. It meant your custom collections could join the iterator party!

There was nothing technically preventing Java from adding map, filter, and reduce methods to iterators—or using static methods. [Google’s Guava library](https://github.com/google/guava) had them and many other “lispy” constructs. With constructs so similar to Clojure’s beloved seq, why weren’t they used more than as a way to loop over collections?

## Idea 1: Lack of closures

A lot of what we use seqs for in Clojure are using `map` / `filter` / `reduce` chains. These are examples of higher-order functions—they’re functions that take other functions as arguments. Until Java 8, the most concise way of passing it bits of behavior was with anonymous classes—and that had its own problems. For instance, primitive values stored in the stack cannot be accessed from a long-lived object because the stack will be popped. Here’s some code for counting up every second:

```markup
final AtomicInteger i = new AtomicInteger(0);

executor.submit(new Runnable() {
  public void run() {
    while(true) {
      Thread.sleep(1000);
      i.incrementAndGet();
    }
  }
});
```

Got to use an `AtomicInteger` so it’s thread safe.

So there was a syntactic speed bump for doing higher-order programming. BTW, here’s what it looks like now with closures:

```markup
AtomicInteger i = new AtomicInteger(0);

executor.submit(() -> {
  while(true) {
    Thread.sleep(1000);
    i.incrementAndGet();
  }
});
```

Now that Java has closures, programmers seem to be picking them up—albeit for processing streams, not iterators.

## Idea 2: Fear of higher-order programming

Now is where I have to start giving opinions, because the facts don’t tell enough of a story. It could be said that the fear of higher-order programming in the Java world was so great that the community had to rename it to *Dependency Injection* to make it sound important enough to even talk about it. This might be unfair, but in other communities (including JavaScript), dependency injection is just higher-order functions.

Still, many functions on sequences do not require higher-order programming. For instance, concatenating two iterators, or making a cycle out of an iterator, or making an iterator that represents a range of integers. These are very common and easy-to-write functions that would be very useful. Without them, you have to jump through hoops using for loops to replicate the same thing a concat could do.

## Idea 3: Mutability

Perhaps I am spoiled by Clojure’s immutability by default. Sure, iterators and seqs look similar and serve similar purposes. But it could be that since the iterator is stateful and it’s pointing at a mutable collection underneath, it’s really very different. Could it be that once things are mutable, the usefulness of composing them plummets?

## Idea 4: Fear of composition

So, there’s a saying in the OOP world that we should favor composition over inheritance. The fact that they have to remind each other of that is a big sign that it’s not a common practice. But it’s not the kind of composition we might think of in the functional world. The kind of composition they’re talking about is writing a new class that composes the functionality of two (or more) other classes.

What they’re not talking about is writing code that takes two objects and makes a third object that is their composition. This is not seen very much in the OOP world. Could it be that this style of composition was a conceptual bridge too far?

## Idea 5: Not Java native

Something tells me that if Java had packaged some routines for composing iterators, like found in Guava, people would have adopted it. It’s a bit like how we have this rich set of collection functions in Clojure that are widely used, but it’s rare to bring in one of the “missing utility” libraries that third-parties have made. This does not explain why the JDK folks did not make more functions like this. Perhaps it’s as simple as being easy to do in user land, so why bake it into the JVM?

## Conclusions

Those are my best ideas, but I have very little evidence to back up any as a causal explanation. I’m glad that Rich Hickey learned the lesson and included a lot of sequence functions in `clojure.core`. Otherwise, we might not use them as much as we should. Still, I see this as a blindspot for the Java ecosystem. A powerful abstraction was right under their noses, and it was even part of the inspiration for the seq interface. It makes me wonder what blind spots we have in the Clojure wold. What can we learn from other languages?
