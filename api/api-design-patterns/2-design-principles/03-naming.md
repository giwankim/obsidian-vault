## 3.1 Why do names matter?

## 3.2 What makes a name "good?"

### 3.2.1 Expressive
A name clearly convey the thing that it's naming.

### 3.2.2 Simple
Names should be expressive but only to the extent that each additional part of a name adds value to justify its presence.

### 3.2.3 Predictable
Allow users of an API to learn one name and continue building on that knowledge to be able to predict what future names would look like.

## 3.3 Language, grammar, and syntax
### 3.3.1 Language
American English

### 3.3.2 Grammar
This section will touch on a few of the most common issues when attempting to apply American English grammar as it applies to naming things in an API.

#### Imperative Actions
#### Prepositions
When preposition are used in the context of a web API, particularly in resource names, they can be indicative of more complicated underlying problems with the API.

`Book` vs `BookWithAuthor`

In this case, the preposition ("with") is a *code smell.*
#### Pluralization
Most often, we'll choose the names for things in our APIs to be the singular form. If an API uses RESTful URLs, the collection name of a bunch of resources is almost always plural.

However, things can sometimes get messy when we need to talk about multiples of these resources. If an API uses RESTful URLs, the collection name of a bunch of resources is almost always plural.

### 3.3.3 Syntax
#### Case
Depending on the language used to represent an API specification, different components are rendered in different cases.

#### Reserved Keywords
Avoid the use of restricted keywords as names in your API whenever possible.

## 3.4 Context
While there are no strict rules about how to name things in a given context, all names we choose are inextricably linked to the context provided by that API.

*book* may refer to a resource in a Library API vs an action to be taken in a Flight Reservation API.

## 3.5 Data types and units
Some field names can be confusing without units.

## 3.6 Case study: What happens when you choose bad names?

### Subtle Meaning
Google API that follows pagination pattern except one important difference: instead of specifying a `maxPageSize` to say "give me a maximum of N items," requests specify a `pageSize.`

The most common scenario is when someone asks for 10 items, gets back 8, and thinks that there must be no more items. This results in API users to miss out on lots of items because they stop paging through the results before the actual end of the list.
### Units
In 1999, NASA planned to maneuver the Mars Climate Orbiter into an orbit about 140 miles above the surface. They did a bunch of calculations to figure out exactly what impulse forces to apply in order to get the orbiter into the right position then executed the maneuver. Instead of being at 140 miles above the surface, the orbiter was within 35 miles of the surface. The orbiter was destroyed in Mar's atmosphere.

In the investigation that followed, it was discovered that the Lockheed Martin team produced output in US standard units whereas NASA teams worked in SI units.

## 3.7 Exercises

## Summary
- Good names, like good APIs, are simple, expressive, and predictable.
- When it comes to language, grammar, and syntax, often the right answer is to pick something and stick to it.
- Prepositions in names are often API smells that hint at some larger underlying design problem worth fixing.
- Remember that the context in which a name is used both imparts information and can be potentially misleading. Be aware of the context in place when choosing a name.
- Include the units for primitives and rely on richer data types to help convey information not present in a name.
