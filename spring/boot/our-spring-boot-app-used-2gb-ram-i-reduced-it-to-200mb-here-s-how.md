---
title: "Our Spring Boot App Used 2GB RAM. I Reduced It to 200MB. Here’s How"
source: "https://medium.com/engineering-playbook/our-spring-boot-app-used-2gb-ram-i-reduced-it-to-200mb-heres-how-49314435aaac"
author:
  - "[[Devrim Ozcay | Scaling Systems & Surviving Outages]]"
published: 2025-12-28
created: 2026-09-09
description: "The memory optimization journey that saved us $3,000/month in AWS costs"
tags:
  - "clippings"
---

> [!summary]
> War story of shrinking a Spring Boot user-service from 2GB to 200MB through eight fixes: pruning unused starters and swapping Tomcat for Undertow, disabling Hibernate's second-level cache and adding explicit entity graphs, right-sizing HikariCP and thread pools, removing double Jackson deserialization, trimming Actuator retention and DEBUG logging, and finally setting explicit JVM heap and metaspace flags. Reports pods dropping from 8 to 4 and OOMKills stopping. Interspersed with many links to the author's paid Gumroad products.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*khz35VaBChdgbfAot_kvcA.png)

## The memory optimization journey that saved us $3,000/month in AWS costs

Look, I’m gonna be real with you.

Three months ago, our Spring Boot microservice was eating RAM like it was going out of style. 2GB baseline. Sometimes spiking to 3GB under load. Our AWS bill was hurting. Our ops team was sending passive-aggressive Slack messages about “maybe optimizing things.”

And the worst part? I thought this was just… normal. “Java uses memory, that’s how it works,” I told myself. Everyone knows Java is a memory hog, right?

Wrong.

Dead wrong.

Firstly you can look here:

## [Subscribe to Devrim Ozcay on Gumroad](https://devrimozcay.gumroad.com/?source=post_page-----49314435aaac-----------------------------------------)

### I help backend teams find and fix production performance issues. Start with the free checklist, then get the full…

devrimozcay.gumroad.com

**Before we ever deploy to production, we run through a brutal checklist — and when things break, we follow a structured incident process.**
I made both public:

– Pre-Production Checklist + Incident Response Template (free):
👉

## [Pre-Production Checklist + Incident Response Template](https://devrimozcay.gumroad.com/l/kfccl?source=post_page-----49314435aaac-----------------------------------------)

### These are the exact operational tools we built after multiple real production failures.Not a tutorial.Not a blog…

devrimozcay.gumroad.com

– Production Failures Playbook — 30 real incidents with timelines, root causes, and fixes:
👉

## [Production Failures Playbook 30 Real Incidents That Broke Production (And How to Never Repeat Them)](https://devrimozcay.gumroad.com/l/xbihfx?source=post_page-----49314435aaac-----------------------------------------)

### Production Failures Playbook30 Real Incidents That Broke Production (And How to Never Repeat Them)This is not a…

devrimozcay.gumroad.com

Use them if you want to avoid learning these lessons the expensive way.

After two weeks of profiling, experimenting, and occasionally wanting to throw my laptop out the window, I got that service down to 200MB. Not by switching languages. Not by rewriting everything. Just by understanding what the hell was actually happening.

This isn’t a theory post. This is what I actually did, with real numbers, real mistakes, and real results.

You can look:

I’ve seen too many backend systems fail for the same reasons — and too many teams learn the hard way.

So I turned those incidents into a practical field manual:
real failures, root causes, fixes, and prevention systems.

No theory. No fluff. Just production.

👉 **The Backend Failure Playbook** — *How real systems break and how to fix them:*

## [The Backend Failure Playbook How Real Systems Break and How to Fix Them (Java, Spring, SQL, Cloud)](https://devrimozcay.gumroad.com/l/menhx?source=post_page-----49314435aaac-----------------------------------------)

### This is not a tutorial.This is a field manual.The Backend Failure Playbook is a practical guide built from real…

devrimozcay.gumroad.com

## The “Oh Shit” Moment That Started Everything

Monday morning. 9:47 AM. Coffee still hot.

Our DevOps lead drops this in the backend channel:

“Hey team, our user-service pods keep getting OOMKilled in production. Third time this week. Can someone look into this?”

Attached: A Kubernetes dashboard showing our service restarting every few hours. Memory usage climbing steadily until… crash.

I checked the resource limits. We’d set them to 2.5GB because “Java needs space.” The service was hitting that limit and getting murdered by the OOM killer.

My first thought? “Let’s just increase the limit to 4GB.”

My second thought? “Wait, that’s stupid. Why does a simple user CRUD service need 2GB of RAM?”

So I started digging.

**🧩 If you enjoy these deep-dive stories, you might like some of the notes I keep around while working on Spring systems:
**• Grokking the Spring Boot Interview →

## [Grokking the Spring Boot Interview](https://gumroad.com/a/134347923/hrUXKY?source=post_page-----49314435aaac-----------------------------------------)

### SPECIAL OFFER 20% OFF - USE DISCOUNT CODE FRIENDS20Crack your Java and Spring Developer interview by preparing…

gumroad.com

• Spring Boot Troubleshooting Cheatsheet →

## [Spring Boot Troubleshooting Cheatsheet](https://gumroad.com/a/416513171/ggwlgd?source=post_page-----49314435aaac-----------------------------------------)

### Stop wasting hours on common Spring Boot errors.Get unstuck fast with this developer-tested troubleshooting…

gumroad.com

• 250+ Spring Certification Practice Questions →

## [250+ Spring Professional Certification Practice Questions](https://gumroad.com/a/134347923/sygyq?source=post_page-----49314435aaac-----------------------------------------)

### SPECIAL OFFER 20% OFF (CODE - FREINDS20)If you are preparing for Spring Professional certification, a Java interview…

gumroad.com

☕ I’ve been keeping these handy while mentoring junior devs and preparing for interviews myself:
• Grokking the Java Interview →

## [Grokking the Java Interview](https://gumroad.com/a/134347923/QqjGH?source=post_page-----49314435aaac-----------------------------------------)

### Cracking the Java Interview: Special Offer - 20% OFF with Code FRIENDS20 Preparing for a Java interview can feel…

gumroad.com

• Grokking the SQL Interview (Free Copy) →

## [Grokking the SQL Interview \[Free Sample Copy\]](https://gumroad.com/a/416513171/brruh?source=post_page-----49314435aaac-----------------------------------------)

### SPECIAL OFFER 20% OFF (CODE - FREINDS20) This is the sample copy of my classic SQL interview book, Grokking the SQL…

gumroad.com

• Grokking the Java Interview Vol 2 →

## [Grokking the Java Interview Vol 2 \[Free Sample Copy\]](https://gumroad.com/a/416513171/mtghj?source=post_page-----49314435aaac-----------------------------------------)

### SPECIAL OFFER 20% OFF (CODE - FREINDS20) This is the sample copy of my classic Java interview book, Grokking the Java…

gumroad.com

They’re short, practical, and cover exactly what interviewers actually ask.
These have saved me countless hours chasing weird bean issues and context reload bugs.

## [Why We Removed Lombok After Two Years (And Slept Better)](https://levelup.gitconnected.com/why-we-removed-lombok-after-two-years-and-slept-better-b53dea46f9b2?source=post_page-----49314435aaac-----------------------------------------)

### We thought annotations would make our lives easier — until our build pipeline begged for mercy.

levelup.gitconnected.com

## [Python is Dying And Nobody Admit It](https://medium.com/lets-code-future/python-is-dying-and-nobody-wants-to-admit-it-4260f774117a?source=post_page-----49314435aaac-----------------------------------------)

### The hard truth about Python’s slowdown — and why even loyal developers are jumping ship.

medium.com

## [Why Senior Java Developers Never Use if-else Anymore (And Why Your Code Screams “Junior”)](https://medium.com/javarevisited/why-senior-java-developers-never-use-if-else-anymore-and-why-your-code-screams-junior-ac199ea95002?source=post_page-----49314435aaac-----------------------------------------)

medium.com

## What I Found (Spoiler: It Wasn’t Pretty)

First, I spun up the service locally with JVisualVM attached. If you’ve never profiled a Java app, JVisualVM is your best friend. It comes with the JDK. It’s free. Use it.

What I saw made me feel like an idiot:

**Heap memory:** 1.2GB used, 1.8GB allocated
**Non-heap memory:** 400MB (mostly metaspace and code cache)
**Classes loaded:** 18,000+
**Threads:** 200 active threads

For context, this service does:

- User CRUD operations
- JWT authentication
- Some caching with Redis
- Publishing events to RabbitMQ

That’s it. No ML. No image processing. No crazy algorithms.

18,000 classes? 200 threads? For THAT?

Something was very wrong.

## Problem 1: We Were Loading the Entire Universe

Spring Boot makes it stupidly easy to add dependencies. Too easy.

Our `pom.xml` looked like this:

```hs
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
<!-- ... 23 more starters -->
```

Each Spring Boot “starter” pulls in a bunch of transitive dependencies. Many of which we weren’t using.

I ran `mvn dependency:tree` and found:

- Jackson modules we never used
- Hibernate validators we didn’t need
- Tomcat embedded features we weren’t leveraging
- Micrometer metrics libraries (all of them, for every monitoring system)

**The Fix:**

I went through each dependency and asked: “Do we actually use this?”

Removed unnecessary starters. Excluded transitive dependencies we didn’t need. Used `spring-boot-starter-web` exclusions to drop unused components.

```hs
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <exclusions>
        <exclusion>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-tomcat</artifactId>
        </exclusion>
    </exclusions>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-undertow</artifactId>
</dependency>
```

Switched from Tomcat to Undertow as the embedded server. Undertow has a smaller memory footprint.

**Result:** Memory usage dropped to 1.6GB. Not great, but progress.

## Problem 2: Hibernate Was Caching… Everything

Our JPA entities had `@OneToMany` relationships everywhere. And we weren't being careful about fetch strategies.

Classic N+1 problem, but worse. Hibernate’s second-level cache was holding onto entities we’d queried once and never needed again.

I found entities in memory from queries we ran hours ago.

**The Fix:**

First, I disabled Hibernate’s second-level cache entirely. We were using Redis for caching anyway. No need for duplicate cache layers.

```hs
spring:
  jpa:
    properties:
      hibernate:
        cache:
          use_second_level_cache: false
```

Then I went through our JPA repositories and added explicit fetch strategies:

```hs
// Bad (loads everything)
@Query("SELECT u FROM User u")
List<User> findAll();

// Good (loads only what we need)
@Query("SELECT u FROM User u")
@EntityGraph(attributePaths = {"roles"})
List<User> findAllWithRoles();
```

Added `@Transactional(readOnly = true)` to all read operations. This tells Hibernate not to track entities for changes, saving memory.

**Result:** Memory dropped to 1.2GB. Getting somewhere.

## Problem 3: Connection Pools Were Oversized

Our HikariCP configuration (Spring Boot’s default connection pool) was set to auto-configuration defaults.

Defaults are:

- Maximum pool size: 10 connections
- Minimum idle: 10 connections

We were running 8 pods in Kubernetes. That’s 80 database connections for a service that typically handles 50 requests per second.

Our database only needed maybe 20 connections total.

**The Fix:**

```hs
spring:
  datasource:
    hikari:
      maximum-pool-size: 5
      minimum-idle: 2
      connection-timeout: 20000
      idle-timeout: 300000
```

Each connection takes memory. By reducing the pool size, we saved ~100MB across all instances.

**Result:** Memory down to 1.1GB.

## Problem 4: Jackson Was Deserializing Everything Twice

We had a weird bug in our code where we were deserializing request bodies manually AND letting Spring do it automatically.

```hs
// Bad (double deserialization)
@PostMapping("/users")
public ResponseEntity<User> createUser(@RequestBody String json) {
    ObjectMapper mapper = new ObjectMapper();
    User user = mapper.readValue(json, User.class); // Why???
    return ResponseEntity.ok(userService.create(user));
}
```

This was a leftover from some legacy code. Someone copy-pasted it. It spread.

**The Fix:**

```hs
// Good (let Spring handle it)
@PostMapping("/users")
public ResponseEntity<User> createUser(@RequestBody User user) {
    return ResponseEntity.ok(userService.create(user));
}
```

Also configured Jackson to not store type information unless absolutely necessary:

```hs
spring:
  jackson:
    default-property-inclusion: non_null
    serialization:
      write-dates-as-timestamps: false
```

**Result:** Memory down to 950MB. We’re cooking now.

## Problem 5: Thread Pools Were Out of Control

Remember those 200 active threads I mentioned? Most were idle.

Spring Boot creates thread pools for:

- Tomcat/Undertow request handling
- Async task execution
- Scheduled tasks
- Database connection pool threads

Default thread pool sizes are generous. Too generous for our use case.

**The Fix:**

```hs
server:
  undertow:
    threads:
      io: 4
      worker: 20

spring:
  task:
    execution:
      pool:
        core-size: 2
        max-size: 4
        queue-capacity: 100
```

Each thread consumes memory (default stack size is 1MB per thread). Reducing threads from 200 to ~30 saved another 170MB.

**Result:** Memory down to 780MB.

## Problem 6: Actuator Endpoints Were Hoarding Data

Spring Boot Actuator is amazing for monitoring. But it also stores a lot of data in memory.

HTTP trace, metrics history, thread dumps — all kept in memory by default.

We had Actuator configured to store the last 1000 HTTP requests in memory. Why? Nobody knows.

**The Fix:**

```hs
management:
  endpoint:
    health:
      show-details: when-authorized
  endpoints:
    web:
      exposure:
        include: health,info,metrics
  metrics:
    export:
      simple:
        enabled: false
  trace:
    http:
      enabled: false
```

Only expose the endpoints you actually use. Don’t store HTTP traces in memory when you have proper logging.

**Result:** Memory down to 650MB.

## Problem 7: Logging Was More Verbose Than Needed

Our logging configuration was set to DEBUG in production.

Yes, I know. Don’t judge. Someone did it during a late-night bug hunt and forgot to revert it.

Debug logging creates tons of String objects. Those objects need memory. Especially when you’re logging every single database query (thanks, Hibernate).

**The Fix:**

```hs
logging:
  level:
    root: INFO
    com.yourcompany: INFO
    org.hibernate.SQL: WARN
    org.hibernate.type.descriptor.sql: WARN
```

Changed to INFO level. Reduced Hibernate’s SQL logging. Kept critical logs for debugging.

Also configured Logback to use async appenders with a reasonable buffer:

```hs
<appender name="ASYNC" class="ch.qos.logback.classic.AsyncAppender">
    <queueSize>512</queueSize>
    <discardingThreshold>0</discardingThreshold>
    <appender-ref ref="CONSOLE" />
</appender>
```

**Result:** Memory down to 500MB.

## Problem 8: JVM Itself Was Overallocating

Finally, the JVM settings. We weren’t tuning them at all. Just letting Java decide.

Default JVM behavior: allocate 25% of system RAM as max heap, or 1GB, whichever is higher.

Our Kubernetes pods had 2.5GB limits. JVM was allocating 1.8GB for heap, leaving only 700MB for everything else (non-heap, OS, buffers).

**The Fix:**

Added explicit JVM flags:

```hs
java -Xms256m -Xmx384m \
     -XX:MaxMetaspaceSize=128m \
     -XX:+UseG1GC \
     -XX:MaxGCPauseMillis=200 \
     -XX:+UseStringDeduplication \
     -jar app.jar
```

Let me break this down:

`-Xms256m`: Initial heap size. Start small, grow if needed.
`-Xmx384m`: Maximum heap size. Force efficiency.
`-XX:MaxMetaspaceSize=128m`: Limit class metadata space.
`-XX:+UseG1GC`: Use G1 garbage collector (better for low-latency).
`-XX:MaxGCPauseMillis=200`: Target GC pause time.
`-XX:+UseStringDeduplication`: Reduce duplicate String overhead.

**Result:** Memory stabilized at 200MB. Holy shit.

## [The Java Interview Question That 90% of Seniors Get Wrong](https://medium.com/javarevisited/the-java-interview-question-that-90-of-seniors-get-wrong-ec86aa3e7db8?source=post_page-----49314435aaac-----------------------------------------)

### I watched a 15-year Java “expert” fail this question in 47 seconds flat. He had Spring on his resume. He had…

medium.com

## [I Automate Everything With Python. My Boss Thinks I’m Productive](https://levelup.gitconnected.com/i-automate-everything-with-python-my-boss-thinks-im-productive-3c1a7bf69ac1?source=post_page-----49314435aaac-----------------------------------------)

### The scripts that save me 20 hours a week (and the ethical questions I pretend don’t exist)

levelup.gitconnected.com

## [Data Scientist vs ML Engineer: I Tried Both. They’re Not the Same Job](https://medium.com/lets-code-future/data-scientist-vs-ml-engineer-i-tried-both-theyre-not-the-same-job-a6dad00cfdb2?source=post_page-----49314435aaac-----------------------------------------)

### One writes notebooks. One writes production systems. Guess which one makes more money.

medium.com

## [Docker Made Our Java Apps 10x Slower (Until We Fixed This One Thing)](https://medium.com/javarevisited/docker-made-our-java-apps-10x-slower-until-we-fixed-this-one-thing-d2cc8fcbea07?source=post_page-----49314435aaac-----------------------------------------)

### It wasn’t Docker’s fault — it was ours. The JVM was quietly burning our CPUs for months.

medium.com

## [Virtual Threads vs Traditional Threads: I Tested Both With 1M Requests](https://medium.com/javarevisited/virtual-threads-vs-traditional-threads-i-tested-both-with-1m-requests-4824b0d26bef?source=post_page-----49314435aaac-----------------------------------------)

medium.com

## [Why I Stopped Trusting ChatGPT After It Nearly Got Me Fired](https://medium.com/lets-code-future/why-i-stopped-trusting-chatgpt-after-it-nearly-got-me-fired-bf8700ffe1e6?source=post_page-----49314435aaac-----------------------------------------)

### How one confident-but-wrong ChatGPT answer triggered a production meltdown — and nearly cost me my job.

medium.com

## The Actual Results

Before optimization:

- Memory usage: 2GB baseline, 3GB under load
- Monthly AWS cost (8 pods): ~$450
- OOMKilled events: 3–5 per week
- Startup time: 12 seconds

After optimization:

- Memory usage: 200MB baseline, 350MB under load
- Monthly AWS cost (8 pods): ~$180
- OOMKilled events: 0 in the last 8 weeks
- Startup time: 6 seconds

We also scaled down from 8 pods to 4 pods because we didn’t need the capacity anymore.

Total savings: ~$3,000/year for one microservice.

We have 12 microservices.

You do the math.

## What I Learned (The Hard Way)

**Lesson 1:** Default configurations are defaults for a reason — they’re safe, not optimal.

Spring Boot can’t know your specific use case. It gives you reasonable defaults that work for most scenarios but waste resources.

**Lesson 2:** Dependencies have a cost.

Every library you add increases memory usage. Be deliberate. Read the docs. Understand what you’re pulling in.

**Lesson 3:** Profile early, profile often.

I should’ve profiled this service six months ago. Would’ve saved us thousands of dollars and countless hours of incident response.

**Lesson 4:** Thread pools are not free.

More threads ≠ better performance. Tune them based on actual workload.

**Lesson 5:** The JVM is smart, but it’s not psychic.

Give it guidance with proper flags. Don’t just let it YOLO your memory allocation.

## Tools That Actually Helped

**JVisualVM** — Free, comes with JDK, perfect for heap dumps and profiling. If you’re not using this, start today.

**Maven Dependency Plugin** — `mvn dependency:tree` shows you exactly what you're importing. Run it. Be horrified. Clean up.

**Spring Boot Actuator** — `/metrics` and `/health` endpoints helped identify bottlenecks. Just don't let it hoard data in memory.

If you’re serious about Spring Boot optimization, the [Spring Boot Troubleshooting Cheatsheet](https://gumroad.com/a/416513171/ggwlgd) has saved me more times than I can count. It covers common memory issues, configuration gotchas, and debugging strategies.

For interview prep (because this stuff comes up), [Grokking the Spring Boot Interview](https://gumroad.com/a/134347923/hrUXKY) and [250+ Spring Certification Practice Questions](https://gumroad.com/a/134347923/sygyq) cover the concepts interviewers actually ask about.

And if you’re building production Spring services, the [Spring Boot Production Checklist](https://devrimozcay.gumroad.com/l/fmcerf) (free) has the things I double-check before shipping. Memory configuration, connection pools, logging — all the stuff that bites you later if you skip it.

## The Uncomfortable Truth

Most Spring Boot apps are running with 2–3x more memory than they need.

Not because Spring Boot is bad. Because developers (including past me) don’t question defaults, don’t profile, and don’t optimize until something breaks.

Your service probably doesn’t need 2GB of RAM. Mine didn’t.

But you won’t know until you actually look.

## What You Should Do Next

If you’re running Spring Boot in production:

**Step 1:** Profile it. Right now. Use JVisualVM or YourKit or whatever. Just look at what’s actually happening.

**Step 2:** Run `mvn dependency:tree` and question every dependency. Remove the ones you don't need.

**Step 3:** Review your application.yml. Are you using default values? Tune them for your use case.

**Step 4:** Set explicit JVM flags. Don’t let Java guess.

**Step 5:** Monitor it for a week. Check for memory leaks or weird patterns.

This isn’t premature optimization. This is responsible engineering.

## Some Tools I Actually Use

Over the years, I realized I kept solving the same problems over and over — optimizing services, setting up boilerplates, debugging production issues.

So I built some tools that I actually use when building real products (not demos):

If you’re working with Spring Boot in production, the [Spring Boot Microservices Boilerplate](https://devrimozcay.gumroad.com/l/ozkziq) is a solid starter that includes proper memory configuration out of the box.

For Python ETL work (because not everything is Java), [Python for Production Cheatsheet](https://devrimozcay.gumroad.com/l/python-for-production-cheatsheet) covers the stuff that actually matters in real systems.

And if you’re building mobile habit-tracking apps, the [Expo Habit App Boilerplate](https://devrimozcay.gumroad.com/l/mliech) has offline support and proper architecture built in.

I’m not selling dreams — just things I got tired of rebuilding from scratch.

## Final Thoughts

Reducing memory usage from 2GB to 200MB wasn’t one big fix. It was ten small fixes, each chipping away at waste.

Most developers won’t do this work until forced to. Until AWS bills get scary. Until services crash in production.

Don’t be most developers.

Profile your services. Question your defaults. Optimize before it hurts.

Your wallet (and your ops team) will thank you.

**Your turn:** What’s the biggest memory optimization you’ve done? Or the most embarrassing default config you left in production?

Drop it in the comments. Let’s share war stories.

And if you found this useful, maybe it’ll save someone else $3K/year too. Share it around.

Now go profile something. You’ll probably hate what you find.

## [Why We Removed Lombok After Two Years (And Slept Better)](https://levelup.gitconnected.com/why-we-removed-lombok-after-two-years-and-slept-better-b53dea46f9b2?source=post_page-----49314435aaac-----------------------------------------)

### We thought annotations would make our lives easier — until our build pipeline begged for mercy.

levelup.gitconnected.com

## [The Java Interview Question That 90% of Seniors Get Wrong](https://medium.com/javarevisited/the-java-interview-question-that-90-of-seniors-get-wrong-ec86aa3e7db8?source=post_page-----49314435aaac-----------------------------------------)

### I watched a 15-year Java “expert” fail this question in 47 seconds flat. He had Spring on his resume. He had…

medium.com

## [Docker Made Our Java Apps 10x Slower (Until We Fixed This One Thing)](https://medium.com/javarevisited/docker-made-our-java-apps-10x-slower-until-we-fixed-this-one-thing-d2cc8fcbea07?source=post_page-----49314435aaac-----------------------------------------)

### It wasn’t Docker’s fault — it was ours. The JVM was quietly burning our CPUs for months.

medium.com

## [Why Senior Java Developers Never Use if-else Anymore (And Why Your Code Screams “Junior”)](https://medium.com/javarevisited/why-senior-java-developers-never-use-if-else-anymore-and-why-your-code-screams-junior-ac199ea95002?source=post_page-----49314435aaac-----------------------------------------)

medium.com

## About me and what I’m working on

**One last thing.**

I’m actively talking to teams who are dealing with problems like:

• services slowly eating memory until they crash
• rising cloud costs nobody understands anymore
• incidents that feel “random” but keep repeating
• systems that only one or two people truly understand

If any of this sounds like your team, I’d genuinely love to hear what you’re dealing with.

I’m not selling anything here — I’m trying to understand where teams are struggling most so I can build better tools and practices around it.

You can reach me here:

🔗 LinkedIn: [https://www.linkedin.com/in/devrimozcay/](https://www.linkedin.com/in/devrimozcay/)

✍️ Medium: [https://medium.com/@devrimozcay](https://medium.com/@devrimozcay)

Follow along:
X: [https://x.com/devrimozcy](https://x.com/devrimozcy)
Instagram: [https://www.instagram.com/devrim.software/](https://www.instagram.com/devrim.software/)

## [Python is Dying And Nobody Admit It](https://medium.com/lets-code-future/python-is-dying-and-nobody-wants-to-admit-it-4260f774117a?source=post_page-----49314435aaac-----------------------------------------)

### The hard truth about Python’s slowdown — and why even loyal developers are jumping ship.

medium.com

## [Response Time From 3s to 80ms: The 20 Bottlenecks I Fixed](https://medium.com/lets-code-future/response-time-from-3s-to-80ms-the-20-bottlenecks-i-fixed-b794e5d22b69?source=post_page-----49314435aaac-----------------------------------------)

### Why your API is slow and exactly where to look first

medium.com

## [Our Microservices Were Slow. The Problem Wasn’t the Code](https://medium.com/lets-code-future/our-microservices-were-slow-the-problem-wasnt-the-code-d8a23164c880?source=post_page-----49314435aaac-----------------------------------------)

### Network latency, database queries, and architecture mistakes everyone blames on frameworks

medium.com

## [We Replaced Our ML Model With a Simple If-Else. Performance Improved](https://blog.gopenai.com/we-replaced-our-ml-model-with-a-simple-if-else-performance-improved-5e1e6095b0ba?source=post_page-----49314435aaac-----------------------------------------)

### Sometimes the smartest solution is admitting you were overthinking it

blog.gopenai.com

## [PostgreSQL vs MySQL for Spring Boot: Same App, Different Results](https://medium.com/@devcommando/postgresql-vs-mysql-for-spring-boot-same-app-different-results-2439223b4fbc?source=post_page-----49314435aaac-----------------------------------------)

### We built the same e-commerce API twice. One database choice cost us 3 days of debugging and $400 in AWS bills.

medium.com

## [We Switched From Pandas to Polars. Data Processing Got 20x Faster](https://python.plainenglish.io/we-switched-from-pandas-to-polars-data-processing-got-20x-faster-fd1db1bb0004?source=post_page-----49314435aaac-----------------------------------------)

### The Python library everyone should know about but somehow doesn’t

python.plainenglish.io

## [I Optimized a Java Service From 3s to 80ms Response Time](https://medium.com/@devcommando/i-optimized-a-java-service-from-3s-to-80ms-response-time-1d75366949e0?source=post_page-----49314435aaac-----------------------------------------)

### The database query, caching strategy, and JVM flags that saved our SLA (and my job)

medium.com

## [Python Pandas Killed Our Performance. Polars Saved Us](https://medium.com/lets-code-future/python-pandas-killed-our-performance-polars-saved-us-2bfc6479dec0?source=post_page-----49314435aaac-----------------------------------------)

### From 45-minute data processing to 2 minutes with one library swap (and the painful lessons in between)

medium.com

## [My First Data Science Project Failed Spectacularly](https://blog.stackademic.com/my-first-data-science-project-failed-spectacularly-a5599e42a1d0?source=post_page-----49314435aaac-----------------------------------------)

### $50,000 mistake, 3 months wasted, and the lessons that actually made me a better ML engineer

blog.stackademic.com

## [Kaggle Made Me Worse at Real Data Science](https://medium.com/engineering-playbook/kaggle-made-me-worse-at-real-data-science-0945f7c61b27?source=post_page-----49314435aaac-----------------------------------------)

### Clean datasets, perfect labels, and leaderboard addiction: how competition platforms teach you everything except the…

medium.com

## [I Know Both Java and Python. You Should Pick One](https://medium.com/activated-thinker/i-know-both-java-and-python-you-should-pick-one-e7c06845e58d?source=post_page-----49314435aaac-----------------------------------------)

### The polyglot trap that’s keeping you mediocre at everything

medium.com

## [Scikit-Learn Is Not Enough: The ML Libraries You’re Missing](https://blog.stackademic.com/scikit-learn-is-not-enough-the-ml-libraries-youre-missing-dd2ec13f5d36?source=post_page-----49314435aaac-----------------------------------------)

### Why your Kaggle silver medal won’t save you in production ML

blog.stackademic.com

## [C# Developer Learns Java: 7 Things That Made No Sense](https://medium.com/lets-code-future/c-developer-learns-java-7-things-that-made-no-sense-07ebfefb0456?source=post_page-----49314435aaac-----------------------------------------)

### When your favorite language betrays you and makes you question everything you thought you knew about programming

medium.com

## [I Built a Rate Limiter in Java (Redis, Bucket Algorithm, Real Production)](https://medium.com/lets-code-future/i-built-a-rate-limiter-in-java-redis-bucket-algorithm-real-production-fa31080239d9?source=post_page-----49314435aaac-----------------------------------------)

### The interview question everyone fails, turned into production code that handles 50K requests/second

medium.com

## [Stop Using Lombok. It’s Making You a Worse Developer](https://blog.stackademic.com/stop-using-lombok-its-making-you-a-worse-developer-5cc715706ab8?source=post_page-----49314435aaac-----------------------------------------)

### That magic @Data annotation is teaching you nothing about Java. And your interviews are about to expose it.

blog.stackademic.com

## [Spring Boot Is Overengineered. I Said It.](https://blog.stackademic.com/spring-boot-is-overengineered-i-said-it-9bfd176c8bce?source=post_page-----49314435aaac-----------------------------------------)

### When simple CRUD apps don’t need enterprise frameworks (and when they do)

blog.stackademic.com

## [I Tried Becoming a Backend Engineer in 14 Days — I Wasn’t Ready](https://medium.com/lets-code-future/i-tried-becoming-a-backend-engineer-in-14-days-i-wasnt-ready-ad6e16879481?source=post_page-----49314435aaac-----------------------------------------)

### Automation promised freedom. What it delivered was noise, context switching, and more work pretending to be progress.

medium.com

You can follow

## [Engineering Playbook](https://medium.com/engineering-playbook?source=post_page-----49314435aaac-----------------------------------------)

### We write about software engineering, backend architecture, DevOps, cloud systems, AI engineering, system design…

medium.com
