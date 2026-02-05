---
title: "Spring AI 1.0 Delivers Easy AI Systems and Services"
source: "https://www.infoq.com/articles/spring-ai-1-0/?utm_source=linkedin&utm_medium=link&utm_campaign=calendar"
author:
  - "[[Josh Long]]"
published: 2025-07-23
created: 2026-02-05
description: "Jakarta EE 11 introduces support for Java 21, records, virtual threads, and Jakarta Data, laying the groundwork for Jakarta EE 12 and its emphasis on unified data access across persistence APIs."
tags:
  - "clippings"
---
[BT](https://www.infoq.com/int/bt/ "bt")

[InfoQ Homepage](https://www.infoq.com/ "InfoQ Homepage") [Articles](https://www.infoq.com/articles "Articles") Spring AI 1.0 Delivers Easy AI Systems and Services

[Java](https://www.infoq.com/java/ "Java")

[Observability-First Development: Staying in Flow While Shipping AI-Assisted Software (Webinar Feb 10th)](https://www.infoq.com/url/t/8009784d-6844-44a0-9150-705c9a19d8f4/?label=Dynatrace-EventPromoBox)

Listen to this article - 30:47

### Key Takeaways

- Spring AI 1.0 introduces first-class support for LLMs and multimodal AI within the Spring ecosystem, providing abstractions for chat, embedding, image, and transcription models that integrate seamlessly with Spring Boot.
- The framework supports advanced AI engineering patterns, such as RAG, tool calling, and memory management via advisors, enabling developers to build agentic applications with minimal boilerplate.
- Model Context Protocol (MCP) support allows developers to create composable AI services that interoperate across languages and runtimes, reinforcing Spring AI’s utility in modern, polyglot architectures.
- The article demonstrates how to build a full-stack, production-aware AI application, incorporating vector stores, PostgreSQL, OpenAI, Spring Security, observability via Micrometer, and native image builds with GraalVM.
- Java developers can now create scalable, privacy-conscious AI-powered systems using familiar Spring idioms, lowering the barrier to enterprise-grade AI adoption.

Spring AI 1.0, a comprehensive solution for AI engineering in Java, is now available after a significant development period influenced by rapid advancements in the AI field. The release includes many essential new features for AI engineers. Here’s a quick rundown of some of the most prominent features. We’ll introduce these concepts throughout this article.

- Portable service abstractions that allow easy, familiar, consistent, and idiomatic access to various chat models, transcription models, embedding models, image models, etc.
- Rich integration with the wider Spring portfolio, including projects such as Micrometer.io, Spring Boot, Spring MVC and GraalVM.
- Support for the day-to-day patterns of AI engineering, including Retrieval Augmented Generation (RAG) and tool calling that informs an AI model about tools in its environment.
- Support for the MCP that allows Spring AI to be used to build and integrate MCP services.

As usual, you can get the bits when generating an application on [Spring Initializr](https://start.spring.io/).

## Spring AI is your one-stop-shop for AI engineering

Java and Spring are in a prime spot to jump on this AI wave. Many companies are running their applications on Spring Boot, which makes it easy to plug AI into what they’re already doing. You can basically link up your business logic and data right to those AI models without too much effort.

Spring AI provides support for various AI models and technologies. Image models can generate images given text prompts. Transcription models can take audio and convert them to text. Embedding models can convert arbitrary data into vectors, which are data types optimized for semantic similarity search. Chat models should be familiar! You’ve no doubt even had a brief conversation with one somewhere. Chat models are where most of the fanfare seems to be in the AI space. You can get them to help you correct a document or write a poem (just don’t ask them to tell a joke). They are very useful, but they have some issues.

Let’s go through some of these problems and their solutions in Spring AI. Chat models are open-minded and given to distraction. You need to give them a system prompt to govern their overall shape and structure. AI models don’t have memory. It’s up to you to help them correlate one message from a given user to another by giving them memory. AI models live in isolated little sandboxes, but they can do really amazing things if you give them access to tools, functions that they can invoke when they deem it necessary. Spring AI supports tool calling, letting you tell the AI model about tools in its environment, which it can then ask you to invoke. This multi-turn interaction is all handled transparently.

AI models are smart but they’re not omniscient! They neither know what’s in your proprietary databases, nor would want them to! Therefore, you need to inform their responses by stuffing the prompts, basically using the string concatenation operator to put text in the request that the model considers before it looks at the question being asked (background information, if you like).

You can stuff it with a lot of data, but not infinite amounts. How do you decide what should be sent and what should not? Use a vector store to select only the relevant data and send it in onward. This technique is called [Retrieval Augmented Generation](https://www.promptingguide.ai/techniques/rag) (RAG).

AI chat models like to, well, chat! And sometimes they do so so confidently that they can make stuff up, so you need to use evaluation, using one model to validate the output of another, to confirm reasonable results.

And, of course, no AI application is an island. Today, modern AI systems and services work best when integrated with other systems and services. MCP can connect your AI applications with other MCP-based services, regardless of what language they’re written in. You can assemble and compose MCP services in agentic workflows to drive towards a larger goal.

And you can do all this while building on the familiar idioms and abstractions that any Spring Boot developer has come to expect: convenient starter dependencies for basically everything available on the Spring Initializr. Spring AI provides convenient Spring Boot autoconfiguration that gives you the convention-over-configuration setup you’ve come to know and expect. And Spring AI supports observability with Spring Boot’s Actuator and the Micrometer project. It plays well with GraalVM and virtual threads, too, allowing you to build fast and efficient AI applications that scale.

## Meet the Dogs

To demonstrate some of the cool possibilities in action, we’re going to build a sample application. I always struggle with deciding upon a proper domain for these things. Let’s use one that’s relatable: we’re going to build a fictitious dog adoption agency called *Pooch Palace*. It’s like a shelter where you can find and adopt dogs online! Just like most shelters, people will want to talk to somebody and interview them about the dogs. We will build an assistant service to facilitate that.

We’ve got a bunch of dogs in the SQL database that will install when the application starts. We aim to build an assistant to help us find the dog of somebody’s dream, Prancer, described rather hilariously as "Demonic, neurotic, man-hating, animal-hating, children-hating dogs that look like gremlins". This dog is awesome. You might’ve heard about him. He went viral a few years ago when his owner was looking to find a new home for him. The ad was hysterical, and it went viral! Here’s the [original ad](https://www.facebook.com/tyfanee.fortuna/posts/10219752628710467) post, in [Buzzfeed News](https://www.buzzfeednews.com/article/amberjamieson/prancer-chihuahua), in [USA Today](https://www.usatoday.com/story/news/nation/2021/04/12/chihuahua-hates-men-and-children-goes-viral-facebook-meet-prancer/7186543002/), and in [The New York Times](https://www.nytimes.com/2021/04/28/us/prancer-chihuahua-adopted-connecticut.html).

We’re going to build a simple HTTP endpoint that will use the Spring AI integration with a Large Language Model (LLM). In this case, we’ll use Open AI though you can use anything you’d like, including Ollama, Amazon Bedrock, Google Gemini, HuggingFace, and scores of others – all supported through Spring AI – to ask the AI model to help us find the dog of our dreams by analyzing our question and deciding after looking at the dogs in the shelter (and in our database), which might be the best match for us.

## The Build

Using [Spring Initializr](https://start.spring.io/), let’s generate a new project. I’m going to be using the latest version of Spring Boot. Choose Open AI (the 1.0 or later release). I’ll be using a vector store. In this case, it is the PostgreSQL-powered vector store called [PgVector](https://github.com/pgvector/pgvector/blob/master/README.md). Let’s also add the Spring Boot `Actuator` module for observability. Add the Web support. Add support for SQL-based ORM-like data mapping using Spring Data JDBC. You should also choose `Docker Compose`. I’m using Apache Maven, too. I’ll use Java 24 in this article, but you should use the latest reasonable version. If Java 25 is out when you read this, then use that! I’m also using GraalVM native images. So, make sure to add `GraalVM` and the dependencies.

Many different options exist here, including Weaviate, Qdrant, ChromaDB, Elastic, Oracle, SQLServer, MySQL, Redis, MongoDB, etc. Indeed, Spring AI even ships with a [`SimpleVectorStore`](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-vector-store/src/main/java/org/springframework/ai/vectorstore/SimpleVectorStore.java) class, a vector store implementation that you can use. However, I wouldn’t use this implementation in production since it’s just in-memory and not very good at retaining data. But it’s a start.

We’ll need to support the aforementioned RAG pattern, so add the following dependency to the `pom.xml`:

```java
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-advisors-vector-store</artifactId>
</dependency>
```

Are you using GraalVM? No? Well, you should be! If you’re on macOS or Linux or Windows Subsystem for Linux, you should manage your JVM-based infrastructure using the amazing [SDKMAN.io](https://sdkman.io/) project. Once installed, installing GraalVM is as simple as:

```java
$ sdk install java 24-graalce
```

Mind you, I’m using the latest version of Java as of this writing. But, you do you! Always remember to use the newest version of the runtime and technology. As my late father used to say, "It’s a cinch by the inch, hard by the yard". If you’re not using freedom units, somebody might translate it as "It’s easy by the centimeter, difficult by the meter". If you do things as they come, they don’t accrue into an insurmountable technical debt.

Click `Generate`, unzip the resulting `.zip`, and then open `pom.xml` in your favorite IDE.

We added Docker Compose support, so you’ll have a `compose.yml` file in the folder. Open it up and make sure to change the port export line, where it says the following:

```java
ports:
    - '5432'
```

Change it to be:

```java
ports:
    - '5432:5432'
```

This way, when you start the PostgreSQL Docker image, you can connect to it from your external clients. This is handy for development, as you can see what’s being done.

## The Configuration

First, Spring AI is a multimodal AI system that allows you to work with many different models. In this case, we’ll be interacting principally with a [`ChatModel`](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-model/src/main/java/org/springframework/ai/chat/model/ChatModel.java), OpenAI. It’s perfectly possible and reasonable to use any number of dozens of different supported models like Amazon Bedrock, Google Gemini, Azure OpenAI, and even local models such as those enabled via Docker’s Model Runner and Ollama. Running your model is non-negotiable if you’re in a privacy-sensitive domain, like a bank or much of Europe. There are options for you, too! If no explicit support works for you, use the OpenAI API and swap out the base URL gains you purchase with new models, many of which implement the OpenAI API.

To connect to the model, we’ll need to specify an OpenAI key. Add the following to `application.properties`:

```java
spring.ai.openai.api-key=<YOUR_API_KEY_HERE>
```

If you don’t have an OpenAI API key, you can get one from the [OpenAI developer console](https://platform.openai.com/docs/overview).

Spring Boot has support for running Docker images on startup. It will automatically run the `compose.yml` file in the root of the folder. Unfortunately, PostgreSQL isn’t serverless, so we only want Spring Boot to start the image if it’s not running. Add this to `application.properties`:

```java
spring.docker.compose.lifecycle-management=start_only
```

Spring Boot will automatically connect to the Docker image on startup. But this is only for development. Later, we’re going to build a GraalVM native image which is a production build of the code. Now let’s specify some `spring.datasource.*` properties so that the application can connect to our local SQL database running in the Docker daemon.

```java
spring.datasource.password=secret
spring.datasource.username=myuser
spring.datasource.url=jdbc:postgresql://localhost/mydatabase
```

Again, you won’t need this for now, but you will eventually want to connect your application to a SQL database. Now you know how. Also note, that in a production environment, you wouldn’t hard code your configuration. Set up environment variables, e.g., `SPRING_DATASOURCE_USERNAME`.

When Spring Boot starts up, it launches the SQL database. We also want it to install some data into this database, so we have two files: `data.sql` and `schema.sql`. Spring Boot will automatically run `schema.sql` and then `data.sql` if we ask.

```java
spring.sql.init.mode=always
```

Now we’re ready to go!

## Show Me the Code!

The code is the easy part. We’ll build a simple HTTP controller that will field inquiries – to interview, in effect – the shelter about the dogs in the shelter.

```java
package com.example.assistant;

import io.modelcontextprotocol.client.McpClient;
import io.modelcontextprotocol.client.McpSyncClient;
import io.modelcontextprotocol.client.transport.HttpClientSseClientTransport;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.PromptChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.vectorstore.QuestionAnswerAdvisor;
import org.springframework.ai.chat.memory.InMemoryChatMemoryRepository;
import org.springframework.ai.chat.memory.MessageWindowChatMemory;
import org.springframework.ai.document.Document;
import org.springframework.ai.mcp.SyncMcpToolCallbackProvider;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.data.annotation.Id;
import org.springframework.data.repository.ListCrudRepository;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@SpringBootApplication
public class AssistantApplication {

    public static void main(String[] args) {
        SpringApplication.run(AssistantApplication.class, args);
    }
}
```

Any new Spring Boot project will already have something that looks like that class automatically generated for you. In this application, the generated class is called `AssistantApplication.java`.

We need data access functionality to connect our application to the underlying SQL database, so let’s dispense with that right now. Add the following underneath the main class:

```java
interface DogRepository extends ListCrudRepository<Dog, Integer> { }

record Dog(@Id int id, String name, String owner, String description) { }
```

That’s our data access layer. Now, let’s move on to the actual controller. Add the following controller underneath everything else.

```java
@Controller
@ResponseBody
class AssistantController {

    private final ChatClient ai;

    AssistantController(ChatClient.Builder ai,
                        McpSyncClient mcpSyncClient,
                        DogRepository repository, VectorStore vectorStore
    ) {
        var system = """
                You are an AI powered assistant to help people adopt a dog from the adoption
                agency named Pooch Palace with locations in Antwerp, Seoul, Tokyo, Singapore, Paris,
                Mumbai, New Delhi, Barcelona, San Francisco, and London. Information about the dogs
                available will be presented below. If there is no information, then return a polite response
                suggesting we don't have any dogs available.
                """;
        this.ai = ai
                .defaultSystem(system)
                .build();
    }

    @GetMapping("/{user}/assistant")
    String inquire (@PathVariable String user, @RequestParam String question) {
        return this.ai
                .prompt()
                .user(question)
                .call()
                .content();
    }
}
```

We’ve already got a few critical pieces here. In the constructor, we inject the `ChatClient.Builder` and use that builder to configure a default system prompt. In the `inquire()` method, we accept inbound requests and then forward those requests from clients as a `String` to the underlying model.

Try it out. I’m using the handy `HTTPie` command line tool.

```java
$ http :8080/jlong/assistant question=="my name is Josh"
```

It should respond with something confirming it understands what you’ve just said. But did it?

```java
$ http :8080/jlong/assistant question=="what's my name?"
```

This time, it should respond by basically saying that it has already forgotten you. (Or maybe it’s just me. I seem to have that effect on people!)

Anyway, the way to fix that is to configure an *advisor*, a Spring AI concept that allows you to pre- and post-process requests bound for the model. Let’s configure an instance of the [`PromptChatMemoryAdvisor`](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/advisor/PromptChatMemoryAdvisor.java) class, which will keep track of everything sent to the model and then re-transmit it to subsequent requests. We’ll use the user path variable passed in the URL as the key by which we distinguish each transcript. After all, we wouldn’t like some random person to get your chat transcript! We’re going to use an in-memory implementation, but you could just as easily use a JDBC-backed implementation.

Let’s create a concurrent map to store the multi-tenant requests. So, add this to the class.

```java
//...
    private final Map<String, PromptChatMemoryAdvisor> memory = new ConcurrentHashMap<>();
    //...
```

Let’s configure the advisor and then pass it into the `ChatClient` at the call site. Here’s the updated method.

```java
@GetMapping("/{user}/assistant")
String assistant(@PathVariable String user, @RequestParam String question) {

    var inMemoryChatMemoryRepository = new InMemoryChatMemoryRepository();
    var chatMemory = MessageWindowChatMemory
            .builder()
            .chatMemoryRepository(inMemoryChatMemoryRepository)
            .build();
    var advisor = PromptChatMemoryAdvisor
            .builder(chatMemory)
            .build();
    var advisorForUser = this.memory.computeIfAbsent(user, k -> advisor);

    return this.ai
            .prompt()
            .user(question)
            .advisors(advisorForUser)
            .call()
            .content();
}
```

Relaunch the program and try the two requests above again. It should remember you!

But, it still doesn’t know about the dogs! Prove it by issuing a more specific request.

```java
$ http :8080/jlong/assistant question==" do you have any neurotic dogs?"
```

Remember, we want to find *Prancer*, the "demonic, neurotic, man-hating, animal-hating, children-hating dog that looks like a gremlin".

We will need to integrate the data from the SQL database and send that along with the request, but not all of the data. There is no need. Instead, let’s use a vector store to find only the most germane data for our query. Recall that we were using Spring AI’s implementation of the vector type in a table designed by Spring AI. Let’s set up a table in PostgreSQL first.

```java
spring.ai.vectorstore.pgvector.initialize-schema=true
```

Now modify the constructor to look like this:

```java
AssistantController(ChatClient.Builder ai,
                        DogRepository repository, VectorStore vectorStore
    ) {
        // be prepared to comment out from here...
        repository.findAll().forEach(dog -> {
            var dogument = new Document("id: %s, name: %s, description: %s".formatted(dog.id(), dog.name(), dog.description()));
            vectorStore.add(List.of(dogument));
        });
        // to here

        // ..as before...
        this.ai = ai
            // as before
            .defaultAdvisors(new QuestionAnswerAdvisor(vectorStore))
            // as before ...
            .build();
    }
```

Now, when the application starts up, we’ll read all the data from the SQL database and write it to a `VectorStore`. Then, we configure a new advisor that will know to query the `VectorStore` for relevant results before embedding the results in the request to the model for final analysis.

Relaunch the program and try the last `http` call again.

It works!

Now, comment out the code above that initializes the `VectorStore` as it does us no good to initialize the vector store twice!

We’re making good progress, but we’re not nearly done! We may have found Prancer, but now what? Any red-blooded human being would leap at the chance to adopt this doggo! I know I would. Let’s modify the program to give our model access to tools to help schedule a time when we might pick up or adopt Prancer. Add the following class to the bottom of the code page.

```java
@Component
class DogAdoptionScheduler {

    @Tool(description = "schedule an appointment to pickup or "+
                        "adopt a dog from a Pooch Palace location")
    String scheduleAdoption(
            @ToolParam(description = "the id of the dog") int dogId,
            @ToolParam(description = "the name of the dog") String dogName) {
        System.out.println("scheduleAdoption: " + dogId + " " + dogName + "".);
        return Instant
                .now()
                .plus(3, ChronoUnit.DAYS)
                .toString();
    }
}
```

The implementation returns a date three days later and prints out a message. Modify the constructor to be aware of this new tool: inject the `DogAdoptionScheduler` and then pass it into the `defaultTools()` method defined in `ChatClient.Builder`. Restart the program.

```java
$ http :8080/jlong/assistant question==" do you have any neurotic dogs?"
```

It should return that there’s a neurotic dog named Prancer. Now, let’s get it to help us adopt the dog.

```java
$ http :8080/jlong/assistant question== "fantastic. When can I schedule an  appointment to pick up or adopt Prancer from the San Francisco Pooch Palace location?"
```

You should see that it’s worked. (Neat, right?)

Now we’ve integrated our model and business logic with the AI models. We *could* stop here! After all, what else is there? Well, quite a bit. I’d like to take the tool calling support here just a few more steps forward by introducing the [Model Context Protocol](https://modelcontextprotocol.io/) (MCP).

Anthropic introduced MCP in November 2024. It’s a protocol for models (in that case, Claude via the Claude Desktop application) to interoperate with tools worldwide. The Spring AI team jumped on the opportunity and built a Java implementation that eventually became the official Java SDK on the MCP website. The Spring AI team then rebased their integration on that. Let’s see it in action. We will first extract the scheduler into a separate MCP service (called scheduler), then connect our assistant.

Using [Spring Initializr](https://start.spring.io/), name it `scheduler`, select `Web` and `MCP Server`, and hit `Generate`. Open the project in your IDE.

Cut and paste the `DogAdoptionScheduler` class from above and paste it at the bottom of the code page of the newly minted `scheduler` codebase. Ensure the service doesn’t start on the same port as the `assistant`; add the following to `application.properties`:

```java
server.port=8081
```

We will also need to register a [`ToolCallbackProvider`](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-model/src/main/java/org/springframework/ai/tool/ToolCallbackProvider.java), which tells Spring AI which beans to export as MCP services. Here’s the entirety of the code for our new `scheduler` application:

```java
package com.example.scheduler;

import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.ai.tool.method.MethodToolCallbackProvider;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.temporal.ChronoUnit;

@SpringBootApplication
public class SchedulerApplication {

    public static void main(String[] args) {
        SpringApplication.run(SchedulerApplication.class, args);
    }

    @Bean
    MethodToolCallbackProvider methodToolCallbackProvider(DogAdoptionScheduler scheduler) {
        return MethodToolCallbackProvider
                .builder()
                .toolObjects(scheduler)
                .build();
    }
}

@Component
class DogAdoptionScheduler {

    @Tool(description = "schedule an appointment to pickup or"+
                        " adopt a dog from a Pooch Palace location")
    String scheduleAdoption(@ToolParam(description = "the id of the dog") int dogId,
                            @ToolParam(description = "the name of the dog") String dogName) {
        System.out.println("scheduleAdoption: " + dogId + " " + dogName + "".);
        return Instant
                .now()
                .plus(3, ChronoUnit.DAYS)
                .toString();
    }
}
```

Launch this service. Then return to the `assistant`. Delete references to `DogAdoptionScheduler` in the code – the constructor, its definition, the configuration on `defaultTools`, etc. Define a new bean of type `McpSyncClient` in the main class:

```java
@Bean
    McpSyncClient mcpSyncClient() {
        var mcp = McpClient
                    .sync(HttpClientSseClientTransport
                            .builder("http://localhost:8081")
                            .build())
                    .build();
        mcp.initialize();
        return mcp;
    }
```

Inject that reference into the constructor and then change it to this:

```java
AssistantController(ChatClient.Builder ai,
                        McpSyncClient mcpSyncClient,
                        DogRepository repository,
                        VectorStore vectorStore
    ) {
        // like before...
        this.ai = ai
                // ...
                .defaultToolCallbacks(new SyncMcpToolCallbackProvider(mcpSyncClient))
                .build();
    }
```

Launch the program and inquire about neurotic dogs and at what time you might pick the dog up for adoption. You should see that this time, the tool is invoked in the `scheduler` module.

## Production Worthy AI

The code is complete; now, it’s time to turn our focus toward production.

### Security

It’s trivial to use Spring Security to lock down this web application. You could use the authenticated [`Principal.getName()`](https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/security/Principal.html#getName\(\)) as the conversation ID, too. But, what about the data stored in the SQL database, like the conversations? Well, you have a few options here. Most SQL databases have transparent data encryption. As you read or write values, it’s stored securely on disk. No changes are required to the code for this.

### Scalability

We want this code to be scalable. Remember, each time you make an HTTP request to an LLM (or many SQL databases), you block IO, which seems to be a waste of a perfectly good thread! Threads should not simply sit idle and waiting. Java 21 gives us virtual threads, which can dramatically improve scalability for sufficiently IO-bound services. That’s why we set up `spring.threads.virtual.enabled=true` in the `application.properties` file.

### GraalVM Native Images

GraalVM CE is an Ahead-of-Time (AOT) compiler that produces architecture- and operating system-specific native binaries. If you’ve got that setup as your SDK, you can turn this Spring AI application into a native image with ease:

```java
$ ./mvnw -DskipTests -Pnative native:compile
```

This takes a minute or so on most machines, but once it’s done, you can easily run the binary.

```java
$ ./target/assistant
```

This program will start up in a fraction of the time it did on the JVM. It starts up in less than a tenth of a second on my machine. The application takes a fraction of the RAM it would otherwise have taken on the JVM. That’s all very well and good, you might say, but I need to get this running on my cloud platform (CloudFoundry or Kubernetes, of course), and that means making it into a Docker image. Easy!

```java
$ ./mvnw -DskipTests -Pnative spring-boot:build-image
```

Stand back. This might take another minute. When it finishes, you’ll see the name of the generated Docker image printed out. You can run it, remembering to override the hosts and ports of things it would’ve referenced on your host.

```java
$ docker run -e SPRING_DATASOURCE_URL=jdbc:postgresql://docker.host.internal/mydatabase \
  docker.io/library/assistant:0.0.1-SNAPSHOT
```

*Vroom!*

We’re on macOS, and amazingly, when run in a virtual machine emulating Linux, this application runs even faster than – and right from the jump, too! – it would’ve if it were run on macOS directly! Amazing.

### Observability

This application is so darn good that I bet it’ll make headlines, just like Prancer, in no time. And when that happens, you’d be well advised to keep an eye on your system resources and – importantly – the token count. All requests to an LLM have a cost, at least one of complexity if not dollars and cents. Thankfully, Spring AI has your back. Launch a few requests to the model, and then up the Spring Boot Actuator metrics endpoint powered by [Micrometer](https://micrometer.io/): `http://localhost:8080/actuator/metrics`, and you’ll see some metrics related to token consumption. Nice! You can use Micrometer to forward those metrics to your time-series database to get a single pane of glass, a dashboard.

## Conclusion/Wrapping up

AI has dramatically reshaped how we build software, unlocking new opportunities to make our applications more interactive, more usable, more powerful, and increasingly agentic. But take heart, Java and Spring developers: you don’t need to switch to Python to be part of this revolution.

At its core, AI integration often comes down to talking to HTTP endpoints, something at which Java and Spring have always excelled. Integration is our wheelhouse. Beyond that, Java and Spring are proven platforms for building production-grade software. With Spring, you get robust support for observability, security, lightning-fast performance with GraalVM, and scalability with virtual threads, everything you need to run real-world systems under real-world load.

Most enterprises already run their mission-critical business logic on the JVM. The software that powers the world is already written in Java and Spring. And with Spring AI, it’s not just about adding AI, it’s about adding production-ready AI to systems built to last.

## Resources

- [Link to the Spring AI 1.0 blog](https://spring.io/blog/2025/05/20/spring-ai-1-0-GA-released)
- [Josh’s Youtube channel](https://youtube.com/@coffeesoftware)
- Check out the [Spring Initializr](https://start.spring.io/). You can build projects on Spring Boot 3.5 today and, later in 2025, build projects on Spring Boot 4 and Spring Framework 7, too!

## About the Author

### Related Sponsors

- Sponsored by
	[![Icon image](https://imgopt.infoq.com//fit-in/275x500/filters:quality(100)/filters:no_upscale()/sponsorship/topic/2ce2aab1-50d3-4793-9186-cfe7dbe88f8a/DynatraceWebinarFeb10-RSB-1767889359504.png)](https://www.infoq.com/url/f/6eec73cb-79f9-4198-a932-d63e6582fff3/?ha=bW91c2Vtb3Zl&ha=bW91c2Vtb3Zl&ha=bW91c2Vtb3Zl&ha=bW91c2Vtb3Zl&ha=c2Nyb2xs&ha=c2Nyb2xs&ha=c2Nyb2xs&ha=c2Nyb2xs&ha=c2Nyb2xs)

### Related Sponsors

### The InfoQ Newsletter

A round-up of last week’s content on InfoQ sent out every Tuesday. Join a community of over 250,000 senior developers. [View an example](https://assets.infoq.com/newsletter/regular/en/newsletter_sample/newsletter_sample.html)

[BT](https://www.infoq.com/int/bt/ "bt")
