---
title: "Spring AI: Mapping LLM Responses to Java Objects"
source: "https://thorben-janssen.com/spring-ai-mapping-llm-responses/"
author:
  - "[[Thorben Janssen]]"
published: 2025-11-19
created: 2026-07-08
description: "Learn how Spring AI generates JSON Schema, guides the LLM to return JSON, and maps the response straight into your Java objects."
tags:
  - "clippings"
---

> [!summary]
> Spring AI's structured output lets you map an LLM's response straight into typed Java objects: you pass a class or record to `.entity()`, and Spring AI uses Jackson to generate a JSON Schema, injects it into the prompt with formatting instructions, and maps the returned JSON back to your type. You can refine the schema with Jackson's `@JsonProperty` and `@JsonPropertyDescription` annotations, and retrieve collections by nesting a record or using a `ParameterizedTypeReference`. Since valid JSON isn't guaranteed, the `StructuredOutputValidationAdvisor` adds automatic schema validation and retry (default 3 attempts).

**Take your skills to the next level!**

The Persistence Hub is the place to be for every Java developer. It gives you access to all my premium video courses, monthly Java Persistence News, monthly coding problems, and regular expert sessions.

[Join the Persistence Hub!](https://thorben-janssen.com/join-persistence-hub?utm_source=blog&utm_medium=tutorial&utm_campaign=top)

---

Working with large language models often starts simple. You send a question and get a text response. That works fine if you show the answer to a user, but it becomes a problem when you want to process it in your business logic. Plain text is unstructured. Parsing it is an error-prone task, especially when working with a non-deterministic system, like an LLM.

Spring AI solves this problem with structured output. Instead of returning text, it can ask the model to produce a JSON document. When doing that, Spring AI automatically generates a JSON Schema from a Java class or record, adds it to the prompt, and then maps the model’s response into a Java object, which you can use easily in your application.

And to make it even better, you get all of this by only calling 1 method with a reference to the Java type you want to receive.

## Defining a Record for the Response

Let’s start with a simple example. You want to ask the model for information about the current chess world champion. But instead of a text response, you want to receive the following `ChessChampion` record with first and last name and the year in which they were world champion.

```java
public record ChessChampion(
        String first,
        String last,
        List<Integer> years) {
}
```

You do that by providing a prompt to a `ChatClient` instance and calling the `entity` method with a reference to the `ChessChampion` record.

```java
ChessChampion champ = chatClient.prompt("Name the current chess world champion.")
                .call()
                .entity(ChessChampion.class);
```

When you run this code, Spring AI does several things behind the scenes. It uses Jackson to generate a JSON Schema for your record, tells the model to return a valid JSON document that matches the schema, and includes additional formatting instructions.
Here’s what that full prompt looks like when sent to the LLM:

```json
Name the current chess world champion.
Your response should be in JSON format.
Do not include any explanations, only provide a RFC8259 compliant JSON response following this format without deviation.
Do not include markdown code blocks in your response.
Remove the \`\`\`json markdown from the output.
Here is the JSON Schema instance your output must adhere to:
\`\`\`{
  "$schema" : "https://json-schema.org/draft/2020-12/schema",
  "type" : "object",
  "properties" : {
    "first" : {
      "type" : "string"
    },
    "last" : {
      "type" : "string"
    },
    "years" : {
      "type" : "array",
      "items" : {
        "type" : "integer"
      }
    }
  },
  "additionalProperties" : false
}\`\`\`
```

The model receives this prompt and responds with a JSON object matching the provided schema. The following snippet shows the formatted response. As you can see, the LLM provided a good response, even though the field names don’t clearly define which information they represent.

```json
{
    "first": "Magnus",
    "last": "Carlsen",
    "years": [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
}
```

And in the final step, Spring AI uses Jackson to map the JSON document to a `ChessChampion` instance.

By default, Spring AI and Jackson don’t perform any validation before mapping the response to the requested type. So, if the model returned an invalid JSON document, the mapping fails, Jackson throws an exception, and your request fails. I will show you [later in this article](#structure-validation-and-retry) how to add an automatic validation and retry mechanism.

## Customizing the JSON Mapping

Sometimes, you need more control over the generated JSON schema. You may want to change or shorten a field name or give the model more context about a field’s meaning. You can do this by using Jackson’s `@JsonProperty` and `@JsonPropertyDescription` annotations.

Let’s use them to map `first` and `last` to the more expressive field names `firstName` and `lastName`, and to add a description to the `years` field. In general, expressive field names and descriptions explaining the semantics of a field to the LLM improve the quality of the response. So, you should always make sure the JSON schema clearly defines which information you want to retrieve.

```java
public record ChessChampion(
        @JsonProperty(value = "firstName")
        String first,

        @JsonProperty(value = "lastName")
        String last,

        @JsonPropertyDescription("The years when they were world champions.")
        List<Integer> years) {
}
```

Jackson uses these annotations to create the JSON schema definition, and Spring AI includes it in the prompt. Here’s how the updated prompt looks:

```json
Name the current chess world champion.
Your response should be in JSON format.
Do not include any explanations, only provide a RFC8259 compliant JSON response following this format without deviation.
Do not include markdown code blocks in your response.
Remove the \`\`\`json markdown from the output.
Here is the JSON Schema instance your output must adhere to:
\`\`\`{
  "$schema" : "https://json-schema.org/draft/2020-12/schema",
  "type" : "object",
  "properties" : {
    "firstName" : {
      "type" : "string"
    },
    "lastName" : {
      "type" : "string"
    },
    "years" : {
      "description" : "The years when they were world champions.",
      "type" : "array",
      "items" : {
        "type" : "integer"
      }
    }
  },
  "additionalProperties" : false
}\`\`\`
```

Everything else works as in the previous example. The LLM responds with a JSON document, and Spring AI uses JSON to map it to a `ChessChampion` instance.

## Getting Collections of Objects

If you want to retrieve a `Collection` of objects, you have 2 options. You can either model a nested data structure or specify a parameterized type.

Let’s first model a nested data structure as a record.

```java
public record ChessChampions(List<ChessChampion> champions) {}
```

The `ChessChampions` record wraps a list of `ChessChampion` objects. Spring AI will generate a JSON Schema for this composite structure, telling the model to respond with a JSON object containing an array of champions.

As you can see in the following code snippet, you can use the `ChessChampions` record in the same way as the simpler `ChessChampion` record in the previous examples.

```java
ChessChampions champions = chatClient.prompt("Name the world champions in classical chess of the last 10 years.")
                .call()
                .entity(ChessChampions.class);
```

And Spring AI handles this is the same way. It uses Jackson to create the schema, extends the prompt, and maps the response.

```json
Name the world champions in classical chess of the last 10 years.
Your response should be in JSON format.
Do not include any explanations, only provide a RFC8259 compliant JSON response following this format without deviation.
Do not include markdown code blocks in your response.
Remove the \`\`\`json markdown from the output.
Here is the JSON Schema instance your output must adhere to:
\`\`\`{
  "$schema" : "https://json-schema.org/draft/2020-12/schema",
  "type" : "object",
  "properties" : {
    "champions" : {
      "type" : "array",
      "items" : {
        "type" : "object",
        "properties" : {
          "firstName" : {
            "type" : "string"
          },
          "lastName" : {
            "type" : "string"
          },
          "years" : {
            "description" : "The years when they were world champions.",
            "type" : "array",
            "items" : {
              "type" : "integer"
            }
          }
        },
        "additionalProperties" : false
      }
    }
  },
  "additionalProperties" : false
}\`\`\`
```

If you don’t want to wrap your list in another record, you can directly request a `List` of objects using a `ParameterizedTypeReference`.

```java
List<ChessChampion> champions = chatClient.prompt("Name the world champions in classical chess of the last 10 years.")
                .call()
                .entity(new ParameterizedTypeReference<List<ChessChampion>>() {});
```

Both methods work the same way. The only difference is that the first one wraps the list inside a record, while the second one works directly with a Java `List`.

## Structure Validation and Retry

As you saw in the previous examples, Spring AI adds the JSON schema definition to the prompt and expects the LLM to return a valid JSON document. This works most of the time, but there is no guarantee. In those cases, Jackson throws an exception and your request fails.

You can add the `StructuredOutputValidationAdvisor` to add an automatic validation and retry to reduce that risk.

```sql
return chatClient.prompt(message)
        .advisors(StructuredOutputValidationAdvisor.builder().outputType(ChessChampion.class).build())
        .call()
        .entity(ChessChampion.class);
```

Spring AI automatically calls all configured advisors before and after executing the prompt. I will discuss the details of Spring AI’s `Advisor` s and the `AdvisorChain` in a future article.

In the context of this article, you only have to know that you have to initialize the `StructuredOutputValidationAdvisor` with the type you requested from the LLM. In the example above, that’s the ChessChampion record.

The advisor uses the JSON schema for that type to validate the structure of the LLM’s response. If the LLM didn’t return a JSON document or the response didn’t match the schema definition, the `StructuredOutputValidationAdvisor` extends the prompt with the result of the failed validation and executes it again. It does that until the LLM returns a valid JSON document or the `maxRepeatAttempts` limit is reached. By default, the limit is set to 3, and you can adjust it when instantiating the advisor.

## Practical Notes

Structured output is extremely useful because it bridges the gap between language models and business logic. Instead of parsing plain text, you can work directly with typed Java objects. That makes your code safer and easier to maintain.

You should still treat model responses with some caution. The LLM’s response usually matches the requested schema definition, but that’s not guaranteed. The `StructuredOutputValidationAdvisor` can be a good way to handle those situations, but you should be aware that the LLM must process every retry, and you will be charged for them.

And we haven’t even talked about the facts. A model can return valid JSON that contains incorrect or incomplete information. It’s therefore a good idea to validate the returned data. I will talk about that in more detail in a future post.

During development, it’s also helpful to log the raw JSON responses. Seeing the exact output helps you adjust your records, simplify and comment your schemas, or refine your prompts.

## Summary

Structured output in Spring AI makes model responses predictable and type-safe. You define a class or record, and Spring AI generates a JSON Schema and instructs the model to return a matching JSON document. Spring AI then maps the JSON to your Java type.

Jackson provides a reliable default mapping for Java records and classes. If you want to, you can customize field names using Jackson’s `@JsonProperty` annotation and provide additional information to the LLM by providing a field description via a `@JsonPropertyDescription` annotation.

And if you want to retrieve a `Collection` of objects, you can either wrap it in another data structure or use a `ParameterizedTypeDescription` to specify the requested type.
