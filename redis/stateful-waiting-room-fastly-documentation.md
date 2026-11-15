---
title: "Stateful waiting room | Fastly Documentation"
source: "https://www.fastly.com/documentation/solutions/tutorials/compute/stateful-waiting-room/"
author:
published:
created: 2026-11-13
description: "You have regular large volumes of traffic and need to limit the rate at which users can start new sessions. Once a user has been allowed in, they should retain access."
tags:
  - "clippings"
---

> [!summary]
> Fastly tutorial for building a fair, ordered waiting room at the edge with Compute and the JavaScript SDK, which limits the rate of new sessions while letting admitted users keep access. It works like a shop ticket counter: Redis, reached over an HTTP interface, atomically holds now-serving and back-of-queue counters, and each visitor gets a signed cookie recording their position. The steps cover config, the holding page, token validation, fetching the queue cursor, and adjusting the flow rate.

## Stateful waiting room

- Copy as Markdown
- [View as Markdown](https://www.fastly.com/documentation/solutions/tutorials/compute/stateful-waiting-room.md)
- [Set up AI](https://www.fastly.com/documentation/reference/agent-setup)

You have regular large volumes of traffic and need to limit the rate at which users can start new sessions. Once a user has been allowed in, they should retain access.

The guidance on this page was tested with an older version (3.28.0) of the [JavaScript SDK](https://js-compute-reference-docs.edgecompute.app/). It may still work with the latest version (4.2.0), but the [change log](https://www.fastly.com/documentation/reference/changes/javascript-sdk) may help if you encounter any issues.

The concept of a waiting room is similar to other kinds of rate limiting, but differs in that it is applied at a session level, and users must earn access to the site by waiting some amount of time. Waiting rooms can get complicated - especially if you want people to have a numbered position in the queue, or if you want to allow people access based on availability of a resource, such as allowing only a fixed number of baskets to enter the checkout stage at a time. Fastly also offers the more common form of [rate limiting](https://www.fastly.com/documentation/guides/concepts/rate-limiting) in CDN services if you want to prevent individual users issuing large volumes of requests in a short period.

For this solution we'll show how you can create a stateful, ordered queue as a waiting room at the edge of the network, holding back eager users and ensuring that you don't overwhelm your infrastructure, and allowing them to be granted access in the order in which they arrived at the website.

## Instructions

The waiting room principle we're demonstrating here is like a ticket system at a shop counter. The system needs to know two numbers: the number of the user who has just reached the front of the queue (think of this as the "now serving" digital sign), and the number of the user at the back of the queue (which is like the number of the next ticket to come out of the ticket machine). The people in the waiting room need to know what number they are, but the system doesn't need to remember that information, as long as we make sure people can't cheat.

To implement such a mechanism, you need a state store that can atomically increment a counter. One of the most popular choices for this is [Redis](https://redis.io/), which is a powerful in-memory data store. As the Redis network protocol is not HTTP-based, in order to be able to speak to Redis from a Compute service you need a HTTP interface on top of it. [Upstash](https://upstash.com/) is a Redis-as-a-service provider that offers such an interface along with a generous free tier, so we'll use that for this example.

Redis will store two entries representing the two numbers we want to track - position markers for the beginning and end of the queue. When a new user that we've never seen before makes a request, we increment the back-of-queue counter, and serve them a 'holding' page (from the edge) along with a tamper-proof cookie that stores their position in the queue. When that user makes subsequent requests (with their queue token in the cookie), we can check whether the front-of-queue counter has yet reached their number. If it has, we forward their request to the backend.

Some things we want from such a solution are:

- Support changing the secret used for signing visitor positions, so the queue can be reset
- Make it hard for users to get multiple spots in the queue
- Allow requests and responses to stream through Fastly without buffering
- Ensure visitors end up accessing the site in the same order they joined the queue (i.e. it is fair)
- Allow the flow rate of the queue to be adjusted quickly

Let's dive in.

### Create a Compute project

This solution is also available as a [starter kit](https://www.fastly.com/documentation/solutions/starters/compute-starter-kit-javascript-queue) but for the purposes of this tutorial we will assume you want to start from scratch. Create an empty JavaScript project:

```
$ mkdir waiting-room && cd waiting-room
$ fastly compute init --from=starter-kit/javascript/empty

Creating a new Compute project (using --from to locate package template).

Press ^C at any time to quit.

Name: [waiting-room]
Description: A waiting room powered by JavaScript at the edge
Author: My Name <me@example.com>

✓ Initializing...
✓ Fetching package template...
✓ Updating package manifest...
✓ Initializing package...

SUCCESS: Initialized package waiting-room
```

Open `src/index.js` in your code editor of choice and you should see a small Compute program with an empty request handler.

```js
/// <reference types="@fastly/js-compute" />

addEventListener("fetch", (event) => event.respondWith(handleRequest(event)));

async function handleRequest(event) {
  return new Response("OK", { status: 200 });
}
```

### Define some configuration

There are a bunch of things about the way your queue behaves that you may need to change easily, so it's a nice idea to create a configuration file to hold these properties. Copy this configuration code into a file named `config.js` in your `src` directory:

```
1

3
4
5
6
7
8
9
10
11
12
13
14
15
16

34
35

53
54
55
```
```js
import { Dictionary } from "fastly:dictionary";
  function fetchConfig() {
    let dict = new Dictionary("config");
    return {
        queue: {
            // how often to refresh the queue page
            //
            // default 5 seconds
            refreshInterval: 5,
            // how long to remember a given visitor
            //
            // after this time, a visitor may lose their position in the queue and have to start queuing again.
            //
            // default 24 hours
            cookieExpiry: 24 * 60 * 60,
          },
    jwtSecret: dict.get("jwt_secret"),
      };
}
export default fetchConfig;
```

Since this code fetches some parameters from a [dictionary](https://www.fastly.com/documentation/guides/full-site-delivery/dictionaries/about-dictionaries), you need to configure a dictionary for the local testing server to use. Create a file named `devconfig.json` with the following fields:

```json
{
    "jwt_secret": "abc123"
}
```

**IMPORTANT:** Make sure to add this file to `.gitignore` so you don't accidentally commit secrets to your repository.

And make sure to refer to it in your `fastly.toml` so the local testing server can fetch the configuration:

```
6
7
8
9
10
```
```toml
[local_server]
[local_server.dictionaries]
  [local_server.dictionaries.config]
    format = "json"
    file = "src/devconfig.json"
```

**HINT:** A benefit to storing the JWT signing key in a dictionary is that if you have granted access to too many users, and you want a mechanism to apply an 'emergency reset', changing the secret would terminate the access of all users whose sessions have been signed with that key.

### Create a queue page

If you block a visitor's request, it would be confusing for them to see a browser error. Instead, you should serve a webpage to indicate that they should wait.

![A branded waiting room, showing the header "Sometimes we have to restrict the number of people who can access our website at the same time, so that everything works properly." with a subtitle "There are 3288 people ahead of you in the queue."](https://www.fastly.com/documentation/static/9cd4419b7afb014ad57a6eaf38fee6c2/queue.png)

Since the page needs to include some dynamic content (visitor's current queue position), we'll whip up a rudimentary page templating function (you could also use an off-the-shelf dependency here like Mustache or Handlebars).

You can add this to your `index.js` or even split it out into a separate file. Here's an example:

```
1
2
3
4
5
6
7
8
9
10
```
```js
// Injects props into the given template (handlebars syntax)
export default function processView(template, props) {
    for (let key in props) {
      template = template.replace(
        new RegExp(\`{{\\s?${key}\\s?}}\`, "g"),
        props[key]
      );
    }
    return template;
  }
```

Now build a template that uses this interpolation syntax:

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
```
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Virtual Queue</title>
  </head>
  <body>
    <div class="info">
      <h1>Sometimes we have to restrict the number of people who can access our website at the same time, so that everything works properly.</h1>

      <p>There {{ visitorsVerb }} <em>{{ visitorsAhead }}</em> {{ visitorsPlural }} ahead of you in the queue.</p>
    </div>
  </body>
</html>
```

You could serve this page from your origin server but we find that customers prefer to host the waiting room content purely at the edge. You're going to be serving these responses a lot, and they are the first line of defense against surges of traffic.

**HINT:** Remember that for the same reason you want to serve the waiting room HTML page from the edge, you'll want to serve any images, stylesheets and scripts from the edge too. Don't accidentally overload your origin by having your waiting room page load an uncached stylesheet from your origin server!

### Handle permitted and blocked requests

Before writing the logic to decide if a visitor should be given access, make sure the service can pass traffic to the origin as well as serve the queue page.

Back in the main file, write a function that passes a permitted request to the origin, making sure to update the backend name to match your service:

```
5
6

127
128
129
130
131
132
133
```
```js
// The name of the backend serving the content that is being protected by the queue.
const CONTENT_BACKEND = "protected_content";
  // Handle an incoming request that has been authorized to access protected content.
async function handleAuthorizedRequest(req) {
    return await fetch(req, {
        backend: CONTENT_BACKEND,
        ttl: 21600,
    });
}
```

And another function that returns a queue page when the request is unauthorized:

```
135
136
137
138
139
140
141
142
143
144
145
146
147
148
149
150
```
```js
// Handle an incoming request that is not yet authorized to access protected content.
async function handleUnauthorizedRequest(req, config, visitorsAhead) {
    return new Response(
        processView(queueView, {
            visitorsAhead: visitorsAhead.toLocaleString(),
            visitorsVerb: visitorsAhead == 1 ? "is" : "are",
            visitorsPlural: visitorsAhead == 1 ? "person" : "people"
        }),
        {
            status: 401,
            headers: {
                "Content-Type": "text/html",
                "Refresh": config.queue.refreshInterval,
            },
        });
}
```

Note that here we're using the `processView` method written earlier to interpolate dynamic data into the queue page template. This code also sends a `Refresh` header in the response which will cause the browser to reload the page after the given interval.

### Deal with decisions that don't require a token

Sometimes you'll want to allow requests regardless of whether the requestor has waited in the queue. For example, on the queue page, you might want to allow requests to a static asset from the backend such as a CSS file (as discussed earlier, make sure these assets are highly cacheable!).

For this purpose, build an allowlist of paths that you want to permit:

```
8
9
10
11
12
13
14
```
```js
// An array of paths that will be served from the origin regardless of the visitor's queue state.
const ALLOWED_PATHS = [
    "/robots.txt",
    "/favicon.ico",
    "/assets/background.jpg",
    "/assets/logo.svg",
];
```

At the top of the `handleRequest` function, parse the request URL and check if the request path is in the allowlist:

```
19
20
21
22
23
24
25
26
27
28
```
```js
// Handle an incoming request.
async function handleRequest(event) {
    // Get the client request and parse the URL.
    const { request, client } = event;
    const url = new URL(request.url);

    // Allow requests to assets that are not protected by the queue.
    if (ALLOWED_PATHS.includes(url.pathname)) {
      return await handleAuthorizedRequest(request);
    }
```

### Extract data from cookie

To determine if a request should be permitted, you need to be able to determine the visitor's position in the queue.

Write a function to extract the cookie from the request headers:

```
152
153
154
155
156
157
158
159
160
161
162
```
```js
export function getQueueCookie(req) {
    let rawCookie = req.headers.get("Cookie");
    if (!rawCookie) return null;
    let res = rawCookie
      .split(";")
      .map((c) => c.split("="))
      .filter(([k, _]) => k === "queue");

    if (res.length < 1) return null;
    return res[0][1];
}
```

Install the `jws` package to decode the cookie:

```
$ npm install jws
```

And make sure to import it at the top of `index.js`

```
2
```
```js
import * as jws from "jws";
```

Then use the `getQueueCookie` function to extract the cookie from the request headers. Place this code after the allowlist check:

```
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
```
```js
// Get the user's queue cookie.
let cookie = getQueueCookie(request);

let payload = null;
let isValid = false;

try {
    // Decode the JWT signature to get the visitor's position in the queue.
    payload =
        cookie &&
        JSON.parse(jws.decode(cookie, "HS256", config.jwtSecret).payload);
    // If the queue cookie is set, verify that it is valid.
    isValid =
        payload &&
        jws.verify(cookie, "HS256", config.jwtSecret) &&
        new Date(payload.expiry) > Date.now();
} catch (e) {
    console.error(\`Error while validating cookie: ${e}\`);
}
```

When parsing the JWT, this validates that the signature is valid and that the cookie has not expired.

### Connect to Redis

In order to determine if the visitor should be permitted to make requests to the origin, you need to know their position in the queue, which is the difference between their assigned number and the current queue cursor.

For the purposes of this tutorial, this state will be stored in Upstash, a Redis-as-a-service provider that offers a REST API, perfect for running commands from the Compute platform.

If you haven't already, [sign up](https://console.upstash.com/) for Upstash and create a Redis service.

Next, install the Upstash JavaScript client:

```
$ npm install @upstash/redis
```

You can now write some helper functions to fetch and set data within the store. It's recommended to put this in a separate file, such as `store.js`:

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
```
```js
import { Redis } from "@upstash/redis/fastly";

// The name of the backend providing the Upstash Redis service.
const UPSTASH_BACKEND = "upstash";

// The name of the keys to use in Redis.
const CURSOR_KEY = "queue:cursor";
const LENGTH_KEY = "queue:length";

// Helper function for configuring a Redis client.
export function getStore(config) {
    return new Redis({
        url: config.upstash.url,
        token: config.upstash.token,
        backend: UPSTASH_BACKEND,
    });
}

// Get the current queue cursor, i.e. how many visitors have been let in.
export async function getQueueCursor(store) {
    return parseInt((await store.get(CURSOR_KEY)) || 0);
}

// Increment the current queue cursor, letting in \`amt\` visitors.
//
// Returns the new cursor value.
export async function incrementQueueCursor(store, amt) {
    return await store.incrby(CURSOR_KEY, amt);
}

// Get the current length of the queue. Subtracting the cursor from this
// shows how many visitors are waiting.
export async function getQueueLength(store) {
    return parseInt(await store.get(LENGTH_KEY));
}

// Add a visitor to the queue.
//
// Returns the new queue length.
export async function incrementQueueLength(store) {
    return await store.incr(LENGTH_KEY);
}
```

After your existing logic in `index.js`, initialize the store:

```
29
30
31
32
33
```
```js
// Get the queue configuration.
let config = fetchConfig();

// Configure the Redis interface.
let redis = getStore(config);
```

### Deal with invalid tokens

If the cookie either does not exist, is not valid, or has expired, `isValid` will be set to false. In this case you need to create a new cookie for the visitor.

Create another function, this time to set a cookie:

```
163
164
165
166
167
168
169
```
```js
export function setQueueCookie(res, queueCookie, maxAge) {
    res.headers.set(
        "Set-Cookie",
        \`queue=${queueCookie}; path=/; Secure; HttpOnly; Max-Age=${maxAge}; SameSite=None\`
    );
    return res;
}
```

Then use the `setQueueCookie` function to set the cookie in the response, incrementing a counter within Redis to get the next queue position:

```
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
```
```js
// Initialise properties used to construct a response.
let newToken = null;
let visitorPosition = null;

if (payload && isValid) {
    visitorPosition = payload.position;
} else {
    // Add a new visitor to the end of the queue.
    visitorPosition = await incrementQueueLength(redis);

    // Sign a JWT with the visitor's position.
    newToken = jws.sign({
        header: { alg: "HS256" },
        payload: {
            position: visitorPosition,
            expiry: new Date(Date.now() + config.queue.cookieExpiry * 1000),
        },
        secret: config.jwtSecret,
    });
}
```

When sending a response later, you will check for the existence of `newToken` and if it is set, set the cookie in the response.

### Fetch the current queue cursor

Using the data from the store, the service can now make a decision about whether to permit the incoming request:

```
77
78
79
80
81

99
100
101
102
103
104
105
106
107
```
```js
// Fetch the current queue cursor.
let queueCursor = await getQueueCursor(redis);

// Check if the queue has reached the visitor's position yet.
let permitted = queueCursor >= visitorPosition;
  if (!permitted) {
    response = await handleUnauthorizedRequest(
        request,
        config,
        visitorPosition - queueCursor - 1
    );
} else {
    response = await handleAuthorizedRequest(request);
}
```

Make sure to set a new cookie, if required, before returning the response:

```
108
109
110
111

124
125
```
```js
// Set a cookie on the response if needed and return it to the client.
    if (newToken) {
        response = setQueueCookie(response, newToken, config.queue.cookieExpiry);
    }
      return response;
}
```

This is a great point to stop and try out what you've built.

```
$ fastly compute serve --watch
```

Go to [http://127.0.0.1:7676/](http://127.0.0.1:7676/) and you should be greeted by the queue page. However, you will find that you are queuing indefinitely and your requests will not pass to the origin.

### Controlling the queue

The next step is to build a mechanism to let visitors in. There are a few ways to do this:

- **Manual:** A human manually lets visitors in.
- **Scheduled:** Visitors are let in at a fixed interval.
- **Origin managed:** Your server calls an endpoint to let people in when its load is below a certain threshold.

For the purposes of this tutorial, we will implement capabilities that allow for all three of these methods:

#### Create an admin panel

The most obvious way to keep visitors flowing in to your site is to manually increment the queue cursor. However, you definitely don't want any random visitor to be able to do this.

[HTTP Basic Auth](https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication) is a really easy-to-implement authentication mechanism that should work just fine for this purpose. To support this, add a new section to the configuration:

```
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
```
```js
admin: {
    // the path for serving the admin interface and API
    //
    // set to null to disable the admin interface
    path: "/_queue",

    // the password for the admin interface, requested
    // when the admin path is accessed via HTTP Basic Auth
    // with the username \`admin\`.
    //
    // it is recommended that you change this in a production
    // deployment, or better, implement your own authentication
    // method, as this would allow anybody to skip the queue.
    //
    // set to null to disable HTTP Basic Auth (not recommended!)
    password: null,
},
```

Keep in mind that credentials are base64-encoded when using HTTP Basic Auth, so you will need a library to encode/decode them, unless you want to hardcode a base64 string:

```
$ npm install base-64
```

Make sure to import the library so it is available:

```
2
```
```js
import * as base64 from "base-64";
```

Back in the main function, check if the request path is within the admin section. You should do this in the same place that you check for allowlisted paths, as there is no point in making yourself queue for the admin endpoints.

```
34
35
36
37
```
```js
// Handle requests to admin endpoints.
if (config.admin.path && url.pathname.startsWith(config.admin.path)) {
    return await handleAdminRequest(request, url.pathname, config, redis);
}
```

Now you can write a function to handle requests made to the admin endpoints. First, validate that the password has been provided.

```
170
171
172
173
174
175
176
177
178
179
180
181
182

212
```
```js
// Handle an incoming request to an admin-related endpoint.
async function handleAdminRequest(req, path, config, redis) {
    if (
        config.admin.password &&
        req.headers.get("Authorization") != \`Basic ${base64.encode(\`admin:${config.admin.password}\`)}\`
    ){
        return new Response(null, {
            status: 401,
            headers: {
                "WWW-Authenticate": 'Basic realm="Queue Admin"',
            },
        });
    }
  }
```

Now implement an interface for letting a specified number of visitors in:

```
199
200
201
202
203
204
205
206
207
208
209
210
211
```
```js
if (path == \`${config.admin.path}/permit\`) {
    let amt = parseInt(
        new URL("http://127.0.0.1/?" + (await req.text())).searchParams.get("amt")
    );
    await incrementQueueCursor(redis, amt || 1);

    return new Response(null, {
        status: 302,
        headers: {
            Location: config.admin.path,
        },
    });
}
```

Finally, serve a web page with a form that allows the above endpoint to be `POST` ed to.

Create a new HTML template:

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
```
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Virtual Queue</title>
  </head>
  <body>
    <div class="controls">
      <form method="POST" action="{{ adminBase }}/permit">
        <input type="number" name="amt" value="1" />
        <input type="submit" value="Let visitors in" />
      </form>

      <br />

      <p>There are <em>{{ visitorsWaiting }}</em> visitors waiting to enter.</p>
    </div>
  </body>
</html>
```

Import it into your JavaScript:

```
4
```
```js
import adminView from "./views/admin.html";
```

Then serve it in the `handleAdminRequest` function:

```
183
184
185
186
187
188
189
190
191
192
193
194
195
196
197
198
```
```js
if (path == config.admin.path) {
    let visitorsWaiting = (await getQueueLength(redis)) - (await getQueueCursor(redis));

    return new Response(
        processView(adminView, {
            adminBase: config.admin.path,
            visitorsWaiting,
        }),

        {
            status: 200,
            headers: {
                "Content-Type": "text/html",
            },
        });
}
```

This works really well if you have a backend that can constantly ensure that the queue cursor is kept up to date, but if you are trying to protect a backend that you don't have much control over, this can be unfeasible. Instead, the waiting room should automatically let visitors in every few seconds.

#### Enable automatic mode

The Compute platform does not allow you to schedule a task to run at a specific time. However, a website in need of a waiting room can assume that there will be requests coming in regularly. You can take advantage of this by rounding the current time, and checking it against a counter of requests within that given time period. If a given request is the first one within a period, you can run some extra code to let extra visitors in.

The first step is to write some configuration for this functionality. Add the `automatic` and `automaticQuantity` fields to the configuration:

```
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
```
```js
// how often to let visitors in automatically.
// set to 0 to disable automatic queue advancement.
//
// only disable this if you have logic on the backend to call
// the API to let in visitors. if you don't let enough visitors
// in, they may queue forever.
//
// you may still call the admin API (if enabled) to let in more
// visitors than configured here.
//
// default 15 seconds
automatic: 15,

// how many visitors should be let in at a time?
//
// default 5
automaticQuantity: 5,
```

You also need some extra logic in the `store.js` file to handle tracking the requests for each time period:

```
43
44
45
46
47
48
49
50
51
52
```
```js
const AUTO_KEY_PREFIX = "queue:auto";

// Increment the request counter for the current period.
//
// Returns the new counter value.
export async function incrementAutoPeriod(store, config) {
    let period = Math.ceil(new Date().getTime() / (config.queue.automatic * 1000));

    return await store.incr(\`${AUTO_KEY_PREFIX}:${period}\`);
}
```

Now, when a request is received but not permitted, you can check if there have been any requests in the current period and if not, allow the visitor in.

```
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
```
```js
if (!permitted && config.queue.automatic > 0) {
    let reqsThisPeriod = await incrementAutoPeriod(redis, config);
    if (reqsThisPeriod == 1) {
        let queueLength = await getQueueLength(redis);

        if (queueCursor < queueLength + config.queue.automaticQuantity) {
            queueCursor = await incrementQueueCursor(
                redis,
                config.queue.automaticQuantity
            );

            if (visitorPosition < queueCursor) {
                permitted = true;
            }
        }
    }
}
```

If you refresh, the queue should now automatically progress and eventually let you access the origin.

### Log the request and response

Waiting rooms are complex and you're probably going to want to do some logging.

Not only does this help with debugging during the development process, but you can feed this data to a monitoring tool such as Grafana or New Relic to monitor your queue in real-time once you deploy to Fastly.

![A dashboard on New Relic showing the current amount of visitors waiting, a graph of visitors waiting plotted against visitors permitted, and request logs](https://www.fastly.com/documentation/static/108051b2a2baf86da1383c5601682aec/monitoring.png)

Add a `logging.js` file to allow for the output of structured log messages for each request:

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
```
```js
import { Logger } from "fastly:logger";
import { env } from "fastly:env";

export default function log(
  endpointName,
  req,
  client,
  permitted,
  responseStatus,
  queueData
) {
  const endpoint = new Logger(endpointName);
  endpoint.log(
    JSON.stringify({
      timestamp: new Date().toISOString(),
      clientAddress: client.address,
      requestUrl: req.url.toString(),
      requestMethod: req.method,
      requestReferer: req.headers.get("Referer"),
      requestUserAgent: req.headers.get("User-Agent"),
      fastlyRegion: env.get("FASTLY_REGION"),
      fastlyServiceId: env.get("FASTLY_SERVICE_ID"),
      fastlyServiceVersion: env.get("FASTLY_SERVICE_VERSION"),
      fastlyHostname: env.get("FASTLY_HOSTNAME"),
      fastlyTraceId: env.get("FASTLY_TRACE_ID"),
      ...tryGeo(client),
      responseStatus,
      permitted,
      ...queueData,
    })
  );
}

// Geolocation is not supported by the local testing server,
// so we just return an empty object if it fails.
function tryGeo(client) {
  try {
    return {
      clientGeoCountry: client.geo.country_code,
      clientGeoCity: client.geo.city,
    };
  } catch (e) {
    return {};
  }
}
```

This function is collecting as much relevant information about the request and response as possible, including information about the Fastly cache node that the service is running on, and the visitor's geolocation data.

Define a [log endpoint](https://www.fastly.com/documentation/guides/integrations/non-fastly-services/developer-guide-logging) to send the logs to:

```
15
16
```
```js
// The name of the log endpoint receiving request logs.
const LOG_ENDPOINT = "queue_logs";
```

Make sure to call the `log` function before returning the response:

```
112
113
114
115
116
117
118
119
120
121
122
123
124
125
```
```js
// Log the request and response.
    log(
        LOG_ENDPOINT,
        request,
        client,
        permitted,
        response.status,
        {
            queueCursor,
            visitorPosition,
        }
    );
    return response;
}
```

## Next steps

- Consider how you could harden this queue by limiting entries per IP address or requiring a CAPTCHA or other challenge on the queue page.
- If you have globally distributed backends, you could split the queue up into smaller regional queues.
- If using automatic mode, calculate the estimated time that a visitor will remain waiting.
- Provide a way for VIP visitors to jump the queue with a one-time-use code or URL.

This page is part of a series in the [Rate limiting](https://www.fastly.com/documentation/solutions/use-cases/rate-limiting/) [use case](https://www.fastly.com/documentation/solutions/use-cases/).
