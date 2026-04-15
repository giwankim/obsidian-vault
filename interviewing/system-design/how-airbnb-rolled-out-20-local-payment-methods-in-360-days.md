---
title: "How Airbnb Rolled Out 20+ Local Payment Methods in 360 Days"
source: "https://blog.bytebytego.com/p/how-airbnb-rolled-out-20-local-payment?utm_source=post-email-title&publication_id=817132&post_id=190157419&utm_campaign=email-post-title&isFreemail=true&r=8x3s&triedRedirect=true&utm_medium=email"
author:
  - "[[ByteByteGo]]"
published: 2026-03-11
created: 2026-03-20
description: "In this article, we will look at the technical architecture and engineering decisions that made this expansion possible."
tags:
  - "clippings"
  - "payments"
  - "system-design"
  - "distributed-systems"
---

> [!summary]
> Details how Airbnb’s engineering team integrated 20+ local payment methods across global markets in 14 months through the "Pay as a Local" initiative. Covers their domain-driven platform rearchitecture, multi-step transaction framework, config-driven integration approach, dynamic payment widgets, and centralized observability system.

## It’s not just about getting the prompt right. (Sponsored)

![](https://substackcdn.com/image/fetch/$s_!-OVs!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F1136fc1a-4e7d-4dc2-9088-1affbf4a947c_1600x900.jpeg)

When trying to spin up AI agents, companies often get stuck in the prompting weeds and end up with agents that don’t deliver dependable results. This ebook from You.com goes beyond the prompt, revealing five stages for building a successful AI agent and why most organizations haven’t gotten there yet.

In this guide, you’ll learn:

- Why prompts alone aren’t enough and how context and metadata unlock reliable agent automation
- Four essential ways to calculate ROI, plus when and how to use each metric

If you’re ready to go beyond the prompt, this is the ebook for you.

---

For years, Airbnb supported credit and debit cards as the primary way guests could pay for accommodations.

However, today Airbnb operates in over 220 countries worldwide, and while cards work well in many regions, just relying on this payment approach excludes millions of potential users. In countries where credit card penetration is low or where people strongly prefer local payment methods, Airbnb was losing bookings and limiting its growth potential.

To solve this problem, the Airbnb Engineering Team launched the “Pay as a Local” initiative. The goal was to integrate 20+ locally preferred payment methods across multiple markets in just 14 months.

In this article, we will look at the technical architecture and engineering decisions that made this expansion possible.

*Disclaimer: This post is based on publicly shared details from the Airbnb Engineering Team. Please comment if you notice any inaccuracies.*

## Understanding Local Payment Methods

Local Payment Methods, or LPMs, extend beyond traditional payment cards. They include digital wallets like Naver Pay in South Korea and M-Pesa in Kenya, online bank transfers used across Europe, instant payment systems like PIX in Brazil and UPI in India, and regional payment schemes like EFTPOS and Cartes Bancaires.

Supporting LPMs provides several advantages.

- First, offering familiar payment options increases conversion rates at checkout.
- Second, it unlocks markets where credit card usage is minimal or nonexistent.
- Third, it improves accessibility for guests who lack credit cards or traditional banking access.

The Airbnb team identified over 300 unique payment methods worldwide through initial research. For the first phase, they used a qualification framework to narrow this list. They evaluated the top 75 travel markets, selected the top one or two payment methods per market, excluded methods without clear travel use cases, and arrived at a shortlist of just over 20 LPMs suited for integration.

## Modernizing the Payment Platform

Before building support for LPMs, Airbnb needed to modernize its payment infrastructure.

The original system was monolithic, meaning all payment logic existed in one large codebase. This architecture created several problems:

- Adding new features took considerable time, and time to market for new capabilities was measured in months.
- Different teams couldn’t work independently.
- The system was difficult to scale.

Airbnb implemented a multi-year replatforming initiative called Payments LTA, where LTA stands for Long-Term Architecture. The team shifted from a monolithic system to a capability-oriented services system structured by domains. This approach uses domain-driven decomposition, where the system is broken into smaller services based on business capabilities.

See the diagram below that shows a sample domain-driven approach:

![](https://substackcdn.com/image/fetch/$s_!7_Js!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fa316a67f-f231-4983-a857-fb828034db98_1938x1246.png)

After the entire exercise, the core payment domain at Airbnb consisted of multiple subdomains:

- The Pay-in subdomain handles guest payments.
- The Payout subdomain manages host payments.
- Transaction Fulfillment oversees the complete transaction lifecycle.
- The Processing subdomain integrates with third-party payment service providers.
- Wallet and Instruments for stored payment methods.
- Ledger for recording transactions.
- Incentives and Stored Value for credits and coupons.
- Issuing for creating payment instruments.
- Settlement and Reconciliation for ensuring accurate money flows.

This modernization approach reduced time to market for new features, increased code reusability and extensibility, and empowered greater team autonomy by allowing teams to work on specific domains independently.

---

## Using AI agents to debug production incidents from AI-generated code (Sponsored)

![](https://substackcdn.com/image/fetch/$s_!QANu!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F4c912ebd-5844-465e-834b-12bce3deccf2_3852x1868.png)

With AI generating ~80% of code, production systems are getting harder to debug with every deployment. Investigating issues requires following a trail of breadcrumbs across code, infrastructure, telemetry, and documents.

Teams are keeping up with production at scale using AI agents that investigate like senior engineers, forming hypotheses, running queries across systems, and converging on root cause with evidence.

Engineering teams at Coinbase and DoorDash are using Resolve AI to cut incident investigation time by 70%+.

Explore how AI agents help investigate issues in this interactive demo.

---

## Building the Multi-Step Transaction Framework

The Processing subdomain became particularly important for LPM integration.

Airbnb adopted a connector and plugin-based architecture for onboarding new payment service providers, or PSPs.

During replatforming, the team introduced Multi-Step Transactions, abbreviated as MST. This processor-agnostic framework supports payment flows completed across multiple stages.

For example, traditional card payments happen in a single step where you enter your card details and receive an immediate response. However, many local payment methods require multiple steps, such as redirecting to another website, authenticating with a separate app, or scanning a QR code.

MST defines a PSP-agnostic transaction language to describe the intermediate steps required in a payment. These steps are called Actions. Common action types include redirects to external websites or apps, strong customer authentication frictions like security challenges and fingerprinting, and payment method-specific flows unique to each LPM.

When a PSP indicates that an additional user action is required, its vendor plugin normalizes the request into an ActionPayload and returns it with a transaction intent status of ACTION\_REQUIRED. This architecture ensures consistent handling of complex, multi-step payment experiences across diverse PSPs and markets.

Here is an example of what an ActionPayload looks like in JSON format:

```markup
{
  “actionPayload”: {
    “actionType”: “redirect”,
    “actionParameters”: {
      “redirectUrl”: “https://pspvendor1...”,
      “method”: “GET”
    }
  }
}
```

**Source:** [Airbnb Engineering Blog](https://medium.com/airbnb-engineering/pay-as-a-local-bef469b72f32)

## Three Foundational Payment Flows

While the modernized payment platform laid the foundation for enabling LPMs, these payment methods introduced unique challenges.

For example, many local methods require users to complete transactions in third-party wallet apps, introducing complexity in app switching, session handoff, and synchronization between Airbnb and external digital wallets. Each local payment vendor also exposes different APIs and behaviors across charge, refund, and settlement flows.

The Airbnb team analyzed the end-to-end behavior of their 20+ LPMs and identified three foundational payment flows that capture the full spectrum of user and system interactions.

### The Redirect Flow

The first is the redirect flow. In this pattern, guests are redirected to a third-party site or app to complete the payment, then return to Airbnb to finalize their booking. Examples include Naver Pay, GoPay, and FPX. The process works as follows:

- Airbnb’s payments platform sends a charge request to the local payment vendor
- The vendor’s response includes a redirectUrl
- The platform redirects the user to the external app or website
- The user completes the payment
- The user is redirected back to Airbnb with a result token
- Airbnb’s payments platform uses this token to confirm and finalize the payment securely

### The Async Flow

The second is the async flow, where “async” stands for asynchronous. Guests complete payment externally after receiving a prompt, such as a QR code or push notification. Airbnb receives payment confirmation asynchronously via webhooks. Examples include PIX, MB Way, and Blik. The process works as follows:

- Airbnb’s payments platform sends a charge request to the local payment vendor.
- The vendor’s response includes QR code data.
- The checkout page displays the QR code for the user to scan.
- The user completes the payment in their wallet app.
- After payment succeeds, the vendor sends a webhook notification to Airbnb.
- The platform updates the payment status and confirms the order.

See the diagram below:

![](https://substackcdn.com/image/fetch/$s_!8Ykq!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fe5c9f1f5-c38e-4713-b3ad-24d1b3519872_4136x3022.png)

### The Direct Flow

The third is the direct flow.

Guests enter their payment credentials directly within Airbnb’s interface, allowing real-time processing similar to traditional card payments. Examples include Carte Bancaires and Apple Pay.

## Config-Driven Integration

Airbnb embraced a config-driven approach powered by a central YAML-based Payment Method Config.

This file acts as a single source of truth for flows, eligibility rules, input fields, refund rules, and other critical details. Instead of scattering payment method logic across frontend code, backend services, and various other systems, the team consolidated all relevant details in this config.

Both core payment services and frontend experiences reference this single source of truth. This ensures consistency for eligibility checks, UI rendering, and business rules. The unified approach dramatically reduces duplication, manual updates, and errors across the technology stack.

See the diagram below:

![](https://substackcdn.com/image/fetch/$s_!R7c_!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F96f98632-e32e-4f21-98cc-67b4d2cce220_2184x1562.png)

These configs also drive automated code generation for backend services. Using code generation tools, the system produces Java classes, DTOs (Data Transfer Objects), enums, database schemas, and integration scaffolding. As a result, integrating or updating a payment method becomes largely declarative. You simply make a config change rather than writing extensive new code. This streamlines launches from months to weeks and makes ongoing maintenance far simpler.

## Dynamic Payment Widget

The payment widget is the payment method UI embedded into the checkout page. It includes the list of available payment methods and handles user inputs. Local payment methods often require specialized input forms and have unique country and currency eligibility requirements.

For example, PIX in Brazil requires the guest’s first name, last name, and CPF, which is the Brazilian tax identification number. Rather than hardcoding forms and rules into the client applications, Airbnb centralizes both form field specification and eligibility checks in the backend.

![](https://substackcdn.com/image/fetch/$s_!352B!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fbba6dd4e-aabf-4518-ad17-4b3aca893a61_1962x1562.png)

Source: Airbnb Engineering Blog

Servers send configuration payloads to clients, defining exactly which fields to collect, which validation rules to apply, and which payment options to render. This empowers the frontend to dynamically adapt UI and validation for each payment method. Teams can accelerate launches and keep user experiences current without requiring frequent client releases.

See the diagram below:

![](https://substackcdn.com/image/fetch/$s_!dGGU!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fe11bb9f8-12ff-4060-a0f9-a611458497ce_4458x3022.png)

Source: Airbnb Engineering Blog

## Testing Infrastructure

Testing local payment methods presents unique challenges.

Developers often don’t have access to local wallets. For example, a developer in the United States cannot easily test PIX, which requires a Brazilian bank account. Yet with such a broad range of payment methods and complex flows, comprehensive testing is essential to prevent regressions and ensure seamless functionality.

To address this challenge, Airbnb enhanced its in-house Payment Service Provider Emulator. See the diagram below:

![](https://substackcdn.com/image/fetch/$s_!rgRe!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Faedee334-efe5-4aea-992f-873cdb69df8f_4136x3022.png)

This tool enables realistic simulation of PSP interactions for both redirect and asynchronous payment methods. The Emulator allows developers to test end-to-end payment scenarios without relying on unstable or nonexistent PSP sandboxes.

For redirect payments, the Emulator provides a simple UI mirroring PSP acquirer pages. Testers can explicitly approve or decline transactions for precise scenario control. For async methods, it returns QR code details and automatically schedules webhook emission tasks upon receiving a payment request. This delivers a complete, reliable testing environment across diverse LPMs.

## Centralized Observability

Maintaining high reliability and availability is critical for Airbnb’s global payment system.

As the team expanded to support many new local payment methods, they faced increasing complexity. There were greater dependencies on external PSPs and wide variations in payment behaviors. A real-time card payment and a redirect flow like Naver Pay follow completely different technical paths.

Without proper visibility, regressions can go unnoticed until they affect real users. As dozens of new LPMs went live, observability became the foundation of reliability. Airbnb built a centralized monitoring framework that unifies metrics across all layers, from client to PSP.

When launching a new LPM, onboarding requires a single config change. Add the method name, and metrics begin streaming automatically. The system tracks four layers:

- Client metrics showing user-level flow health from client applications
- Payment backend metrics providing API-level metrics for payment flows
- PSP metrics offering API-level visibility between Airbnb and the PSP
- Webhook metrics tracking async completion status for redirect methods or refunds

Airbnb also standardized alerting rules across platform layers using composite alerts and anomaly detection. Each alert follows a consistent pattern with failure count, failure rate, and time window thresholds. An example alert might state: “Naver Pay resume failures greater than 5 and failure rate greater than 20% in 30 minutes.” This design minimizes false positives during low-traffic periods.

## Conclusion

Two examples demonstrate the impact of this work.

- Naver Pay is one of the fastest-growing digital payment methods in South Korea. As of early 2025, it reached over 30.6 million active users, representing approximately 60% of the South Korean population. Enabling Naver Pay delivered a more seamless and familiar payment experience for local guests while expanding Airbnb’s reach to new users who prefer Naver Pay as their primary payment method.
- PIX is an instant payment system developed by the Central Bank of Brazil. By late 2024, more than 76% of Brazil’s population was using PIX, making it the country’s most popular payment method, surpassing cash, credit cards, and debit cards. In 2024 alone, PIX processed over 26.4 trillion Brazilian reals, approximately 4.6 trillion US dollars, in transaction volume. This underscores its pivotal role in Brazil’s digital payment ecosystem.

The Pay as a Local initiative delivered significant business and technical impact. Airbnb observed booking uplift and new user acquisition in markets where they launched local payment methods. Integration time was reduced through reusable flows and config-driven automation. Reliability improved through enhanced observability for early outage detection, standardized testing to prevent regressions, and streamlined vendor escalation and on-call processes for global resilience.

In other words, supporting local payment methods helps Airbnb remain competitive and relevant in the global travel industry. These payment options improve checkout conversion, drive adoption, and unlock new growth opportunities.

**References:**

- [How Airbnb rolled out 20+ locally relevant payment methods worldwide in just 14 months](https://medium.com/airbnb-engineering/pay-as-a-local-bef469b72f32)
