---
title: "A Single Subscriber Doesn’t Turn Pub/Sub Into a Queue"
source: "https://newsletter.systemdesignclassroom.com/p/a-single-subscriber-doesnt-turn-pubsub-into-a-queue?utm_source=post-email-title&publication_id=2391457&post_id=188817135&utm_campaign=email-post-title&isFreemail=true&r=8x3s&triedRedirect=true&utm_medium=email"
author:
  - "[[Raul Junco]]"
published: 2026-02-28
created: 2026-03-07
description: "Learn why pub/sub and work queues are not interchangeable, how delivery guarantees affect retries, and why idempotency ensures reliable async systems."
tags:
  - "clippings"
  - "event-driven"
  - "distributed-systems"
  - "microservices"
---

> [!summary]
> Explains why pub/sub and work queues are fundamentally different async patterns. Delivery semantics—not tooling—define the pattern; idempotency is essential for reliable at-least-once message processing.

### Why execution semantics -not tooling- define async patterns.

A few weeks ago, an engineer reached out with a question that looked simple on the surface:

> **User requests a report → API queues a job → worker generates the PDF.
> Is this pub/sub or a work queue?**

The team was split.
Some argued it was pub/sub because the producer is decoupled from the consumer.
Others said it was a queue because only one worker processes the job.

It looked like a terminology debate.

It wasn’t.

The answer changes how the system behaves under load, failure, and scale, which means we need to step back and look beyond the tools.

---

### The best way to build any app

![](https://substackcdn.com/image/fetch/$s_!zOKL!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fceef8368-d4ab-4de6-b178-3974fbd77de7_2048x1152.png)

Most “AI app builders” aren’t actually app builders. They are infrastructure middlemen. You live inside their box, choose from their secret stack, and force you to start over the moment you want to use a different database, payment processor, or tool. With Orchids:

- You’re not locked-in to Supabase or Stripe.
- Not forced to spend credits, bring your own AI subscriptions with you.
- One-click deployment straight to Vercel

Build anything. From Web, mobile, internal tools, browser extensions, scripts, and bots. Orchids.app is capable of building anything that you can put your mind to.

Use code **MARCH15** for **15% off** (one-time discount).

---

### Start with intent, not tooling

When engineers discuss async systems, the conversation often jumps straight to Kafka, SQS, RabbitMQ, or Redis.

That’s like choosing a truck before deciding whether you’re moving furniture or delivering packages.

Transport moves messages.
Patterns define meaning.

The real question is: **what is the system trying to accomplish?**

Understanding the intent becomes easier when we look at the actual flow that triggered the debate.

### The report generator scenario

1. User requests a report
2. API enqueues a job
3. Worker generates the PDF
4. Result is stored, and the client is notified the report is ready

![](https://substackcdn.com/image/fetch/$s_!tc5O!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F03357557-c96c-4b09-8ab7-c62c6db365f5_3290x1028.png)

The system expects the job to run once. If the worker crashes, the job must retry. If demand increases, more workers can be added.

Nothing here suggests broadcasting information.

The system is executing work.

This is a **work queue**.

To see why, we need to look at the pattern designed specifically for executing tasks.

### Work queue: built to execute work

A work queue says:

> “Do this task.”

Each job is handled by a single worker. If you add more workers, the workload spreads across them. If no worker successfully processes the job, the task remains incomplete, and the system retries it or moves it to a dead-letter queue, but this is a story for another day.

Think about generating a PDF, sending an email receipt, or resizing images. You don’t want five services doing the same work. You want the work done once, reliably.

This model optimizes for throughput, retries, and completion guarantees.

![](https://substackcdn.com/image/fetch/$s_!43JX!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F5d735b00-3762-4028-b2e9-8dd05f4d8eb6_3436x1641.png)

To understand the contrast, let’s look at the pattern built for distributing information instead of executing work.

### Pub/sub: built to distribute facts

Pub/sub says:

> “This happened.”

When an event occurs, multiple systems may react independently. Each subscriber receives its own copy. One subscriber failing does not block the others.

Imagine a user signs up. That single event might trigger analytics tracking, a welcome email, CRM updates, and fraud checks.

No single service owns the event. They react to it.

![](https://substackcdn.com/image/fetch/$s_!oyL9!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fd6fd7f9c-2716-453f-87cd-b4808fe2affd_3365x1567.png)

This model optimizes for independence and extensibility.

At this point, the confusion usually appears: both patterns decouple components, so why aren’t they the same?

### Why decoupling alone isn’t the definition

Decoupling is a side effect, not the defining trait.

If decoupling were the definition, every async system would be pub/sub, and the term would stop being useful.

What matters is consumption behavior.

If another consumer joins:

- should the work split?
- or should the work duplicate?

That answer reveals the pattern.

Your PDF generation should not run twice.

Another way to clarify the difference is to look at what the message represents.

### Commands vs events: a useful shortcut

A **command** tells the system to do something.
An **event** tells the system something already happened.

“GenerateReport” is a command.
“ReportGenerated” is an event.

Commands belong in work queues.
Events belong in pub/sub systems.

By the way, most of the time, mature architectures use both.

This distinction may sound subtle, but it becomes very real once systems reach production scale.

### Why the distinction becomes painful in production

The difference may sound subtle during design discussions, but it becomes very real once systems are under load and failures begin to surface.

Teams that blur the boundary often discover problems the hard way.

Duplicate billing because the same job ran twice.
Customers receiving the same email multiple times.
Retries triggering unexpected side effects.
Work completed but reported as failed due to acknowledgment timing.

These issues don’t come from bad intentions. They come from how messaging systems behave in real environments.

Most queues and streaming platforms provide **at-least-once delivery**. If a worker crashes, times out, or fails to acknowledge completion, the job becomes visible again and is retried. This improves reliability, but it also means the same job can execute more than once.

Because of this, consumers must be **idempotent**; the job may run multiple times, but the outcome must remain correct.

Event systems face a related challenge. Pub/sub consumers may replay historical events, reprocess messages after failures, or start from earlier offsets. Idempotency ensures these replays do not create duplicate side effects.

Exactly-once delivery is often discussed but rarely absolute. Some platforms provide transactional guarantees within the messaging system, yet external side effects (sending emails, charging payments, calling APIs) still require safeguards.

Understanding delivery guarantees explains why duplicates happen:

- Retries improve reliability
- Reliability introduces duplicates
- Idempotency preserves correctness

> Queues prioritize reliable execution of work.
> Pub/sub prioritizes reliable distribution of events.

Getting the pattern right and designing for its guarantees is what keeps systems predictable when real failures occur.

### The clean evolution path

Start by enqueueing a command to generate the report.

After completion, emit a `ReportGenerated` event.

![](https://substackcdn.com/image/fetch/$s_!HCqc!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F79865689-290d-4528-9e9f-99977c1bf290_4899x2123.png)

Now other systems can react, notifications, analytics, auditing, and caching, without coupling themselves to the report service.

The work remains controlled.
The ecosystem stays extensible.

If the distinction still feels abstract, a real-world analogy makes the difference obvious.

### A simple analogy

Think of an airport baggage system.

![](https://substackcdn.com/image/fetch/$s_!CL6S!,w_424,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F5438b565-f345-4a3a-8319-75ff8b419ee6_4879x2459.png)

When you check a suitcase, it is routed to one handler who loads it onto your flight. That’s a work queue. The task must be completed once, and if it fails, your bag doesn’t arrive.

When the plane lands, an arrival event is triggered. Baggage claim displays update, ground crew prepare the gate, and notifications are sent to connecting flights. That’s pub/sub. Multiple systems react independently to the same event.

Different intent. Different behavior.

Understanding the difference is what allows systems to scale without surprises.

### If you remember one thing

Most async flows are not pub/sub.
They are work queues that may emit events after completion.

Understanding that difference prevents duplicate work, simplifies retries, and keeps system responsibilities clear.

> And clarity is what allows systems to scale without surprises.

Until next time,
— Raul

---

System Design Classroom is a reader-supported publication. To receive new posts and support my work, consider becoming a paid subscriber.
