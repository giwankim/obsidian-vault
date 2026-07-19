---
title: "Spring Boot RestClient - No suitable HttpMessageConverter found for custom JSON MIME types"
source: "https://www.youtube.com/post/UgkxNedhX_e7TlqCXTe4p0rXug6UW3pC_CSx"
author:
  - "[[Linh Vu]]"
created: 2026-07-19
description: "A RestClient lesson from upgrading Spring Boot 3 to 4: an API responding with application/vnd.company.api.v2.json (dot instead of +json) breaks the default Jackson converter, fixed by registering a custom JacksonJsonHttpMessageConverter with the extra MIME type."
tags:
  - "clippings"
---

> [!summary]
> A RestClient lesson from upgrading Spring Boot 3 to 4: Jackson's default converter only handles `application/json` and `application/*+json`, so an API responding with the non-standard `application/vnd.company.api.v2.json` (dot instead of `+json`) triggers a "No suitable HttpMessageConverter found" exception. The fix is to register your own converter bean that adds the custom MIME type to the supported list — `JacksonJsonHttpMessageConverter` in Spring Boot 4, `MappingJackson2HttpMessageConverter` in Spring Boot 3.

Here's a lesson I learned a while back with RestClient, and I recently had to adapt it while upgrading from Spring Boot 3 to Spring Boot 4. 🚀🧠

You might already know that:

- 🎯 The **serialization** of requests sent by the **RestClient**
- 🎯 The **deserialization** of responses received

...are handled by a list of `HttpMessageConverter`s configured inside the **RestClient** instance.

Spring Boot, by default, auto-configures a `RestClient.Builder` with several pre-defined `HttpMessageConverter`s. Whenever we create a RestClient using this builder, we benefit from these defaults. And the most widely used converter these days is `JacksonJsonHttpMessageConverter` in Spring Boot 4 (it will be `MappingJackson2HttpMessageConverter` if you're using Spring Boot 3), which handles serializing and deserializing our Java objects to and from the payload. 📦✨

The strategy is, whenever the **Content-Type** (MIME type) of the request/response is:

- 👉 `application/json`
- 👉 `application/*+json` (e.g., `application/vnd.company.api.v2+json`) (RFC-6838, RFC-6839)

`JacksonJsonHttpMessageConverter` will be responsible for handling the serialization/deserialization, respectively.

**Here is the problem I encountered:**
An API provider responded with `Content-Type: application/vnd.company.api.v2.json` (using a dot) instead of `+json` (the RFC standard). Since this Content-Type didn't match the default supported options, it resulted in a "No suitable HttpMessageConverter found" exception. 🚫🐞

I simulated this situation with the PostmanEcho API: `GET https://postman-echo.com/response-headers?Content-Type=application/vnd.company.api.v2.json` (see picture 1). This API will respond to us a response with the headers that we sent in the request's query params (see picture 2). 🔍💻

**The Solution:**
To fix this, we need to explicitly add `application/vnd.company.api.v2.json` to the list of MIME types supported by the `JacksonJsonHttpMessageConverter`. We want it to support:

- ✅ `application/json`
- ✅ `application/*+json`
- ✅ `application/vnd.company.api.v2.json`

We can easily achieve this by defining our own `JacksonJsonHttpMessageConverter` bean in our configuration class (Spring Boot 4), effectively overriding the default configuration in the `JacksonHttpMessageConvertersConfiguration` class (see picture 3). 🛠️💡
For Spring Boot 3, use `MappingJackson2HttpMessageConverter` instead (see picture 4). ✅🛠️

Happy coding! 👨‍💻🎉

#RestClient #HttpMessageConverter #Converter #Jackson #JsonMapper #SpringBoot #SpringFramework #Java

![Picture 1 - Postman Echo request](https://yt3.ggpht.com/mwvsuwRIbQ45YbY1uS4aTd0c6CsSD4y8lOYREhlNoXOFUgKZ47FgVbQZ-4uVaJ1H3ULrUTwPmhCzgTA=s640-c-fcrop64=1,12fb0000ed04ffff-rw-nd-v1)

![Picture 2 - Response headers](https://yt3.ggpht.com/0L2dtUurOrEF-2rCE2vrAdW8I_zNbN9EfuQbdMNdfBTauZO6MLg5MQZptWRxml055uY4IbdRKVXeUg=s640-c-fcrop64=1,38190000c7e6ffff-rw-nd-v1)

![Picture 3 - Spring Boot 4 JacksonJsonHttpMessageConverter bean](https://yt3.ggpht.com/LyWlP2C496vmXO6hh7Mu5soCkKZA1EcFRv7v1L2OQ8_0qB0GkttKiju7QmPKQ-VIIxZy_qaKqCVs=s640-c-fcrop64=1,0be70000f418ffff-rw-nd-v1)

![Picture 4 - Spring Boot 3 MappingJackson2HttpMessageConverter bean](https://yt3.ggpht.com/S9sgu4Kj3noSC6gOo_hXxD6CpIvg-SiHQ8oH7VkEHQ-n6S64apMQ0vh3ekSSjRX9c_AQCsM79hdV=s640-c-fcrop64=1,11800000ee7fffff-rw-nd-v1)
