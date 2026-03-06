## 7.1 Motivation
One of the most valuable aspects of a well-designed API is the ability for users to apply what they already know in order to more quickly understand how an API works. Once users built up their understanding of resources, they're familiar with a set of standard methods that can be performed on those resources.

## 7.2 Overview
Guidelines in this chapter provide some standard answers that ensure consistency (and prevent security leaks or other issues) across standard methods in a way that will grow gracefully as an API expands over time.

## 7.3 Implementation

### 7.3.1 Which methods should be supported?
Not every standard method is required for each resource type.

In general, each standard method should exist on each resource unless there is a good reason for it not to (and the reason should be documented and explained).

Certain methods might not make sense for a specific instance of a resource but still make conceptual sense for the resource type. This scenario also covers resource types that might be considered permanent or immutable. Just because they are permanent and immutable now does not mean they will never be in the future.

### 7.3.2 Idempotence and side effects
Standard methods should not have any side effects or unexpected behavior.

### 7.3.3 Get

### 7.3.4  List

### 7.3.5 Create

### 7.3.6 Update

### 7.3.7 Delete

### 7.3.8 Replace

### 7.3.9 Final API definition

## 7.4 Trade-offs

## Summary
