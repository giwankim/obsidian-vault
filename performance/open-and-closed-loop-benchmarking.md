---
title: "Open and closed loop benchmarking"
source: "https://theconsensus.dev/p/2026/10/25/open-and-closed-loop-benchmarking.html"
author:
  - "[[Phil Eaton]]"
published: 2026-10-25
created: 2026-11-01
description: "In a closed loop benchmark, mean latency is just the number of clients divided by throughput. Latency is better measured with an open loop benchmark, but there you have to consider request distribution policy, desired throughput, and retries. We take a look at both types of benchmarks running against nginx and PostgreSQL."
tags:
  - "clippings"
---

> [!summary]
> Phil Eaton builds a small Go load generator and runs it against nginx and PostgreSQL to show what each benchmark model hides. Closed loops suffer coordinated omission and make mean latency simply clients divided by throughput (Little's law), so a half-second lock stall barely moves p99; open loops expose it, but their results depend on request spacing, run length, and whether retries are modeled, and retries at 70% load halved throughput in the nginx test. The advice: use a closed loop with enough clients to find peak throughput, then an open loop just below that peak to measure latency.

You are getting early access to this article as a subscriber. Your support makes articles like this possible. Thank you.

The [2019 Lancet](https://www.usenix.org/system/files/atc19-kogias-lancet.pdf?utm_source=theconsensus.dev&utm_medium=referral) paper describes two main ways benchmarks send requests from a client to a server.

> An open-loop system models n = ∞ clients that send requests to the target according to a rate λ and an inter-arrival distribution, e.g., Poisson. A closed-loop system bounds the maximum number of possible outstanding requests at any given time. The distinction between an open and a closed loop system is a property of a specific deployment and the same system can be deployed under different scenarios, e.g., a key-value store may serve only a few blocking clients (i.e., closed-loop) or thousands of application servers, which is best modelled as open-loop.

These definitions are a little more general than the breakdown in the otherwise excellent and oft-cited [2006 Open Versus Closed](https://www.usenix.org/legacy/event/nsdi06/tech/full_papers/schroeder/schroeder.pdf?utm_source=theconsensus.dev&utm_medium=referral) paper.

Beyond these two papers, the topic has been [written](https://danluu.com/latency-pitfalls/?utm_source=theconsensus.dev&utm_medium=referral) [about](https://groups.google.com/g/mechanical-sympathy/c/icNZJejUHfE/m/BfDekfBEs_sJ?pli=1&utm_source=theconsensus.dev&utm_medium=referral) [by](https://www.scylladb.com/2021/04/22/on-coordinated-omission/?utm_source=theconsensus.dev&utm_medium=referral) [many](https://buttondown.com/jaffray/archive/measuring-throughput/?utm_source=theconsensus.dev&utm_medium=referral) [experienced](https://brooker.co.za/blog/2023/05/10/open-closed.html?utm_source=theconsensus.dev&utm_medium=referral) [developers](https://emptysqua.re/blog/ycsb-is-obsolete/?utm_source=theconsensus.dev&utm_medium=referral). This article surveys such work to discuss the inherent assumptions in both open and closed loop benchmarks, as well as common mistakes made in each model. We'll demonstrate each issue in either [nginx](https://theconsensus.dev/project/nginx.html) or [PostgreSQL](https://theconsensus.dev/project/postgresql.html).

## Setup

Grab a machine with at least 4 vCPUs, ideally a bare metal machine to avoid noisy neighbors. We'll restrict nginx and PostgreSQL to each use 1 vCPU. And we'll give our benchmark tool 2 vCPUs to make sure it has enough space to saturate nginx and PostgreSQL.

Then install nginx, PostgreSQL, and Golang.

```
sudo apt-get update -y
sudo apt-get install -y nginx postgresql golang-go
```

Grant the PostgreSQL daemon access to 1 CPU, and create an accounts table with some data.

```
sudo systemctl set-property --runtime postgresql@16-main.service AllowedCPUs=1
sudo systemctl restart postgresql
sudo -u postgres createuser -s $USER && createdb
echo '
  DROP TABLE IF EXISTS accounts;
  CREATE TABLE accounts AS
    SELECT id, 0 AS balance
    FROM generate_series(0, 1049999) id;
  ALTER TABLE accounts ADD PRIMARY KEY (id);' | psql
```

Then set up nginx with some files on disk to serve. To make sure it actually does a bit of work (since serving files alone would be too cheap), have it compress every file it serves. And limit nginx to 1 CPU.

```
sudo systemctl disable --now nginx
mkdir -p /tmp/www && cat /usr/share/common-licenses/GPL-3{,,} | head -c 80000 > /tmp/www/page.txt
echo '
events {}
http {
  access_log off;
  gzip on;
  gzip_comp_level 9;
  gzip_types text/plain;

  server {
    listen 9100 reuseport;
    root /tmp/www;
  }
}' > /tmp/nginx.conf
sudo nginx -c /tmp/nginx.conf -g 'worker_processes 1; worker_cpu_affinity 0010;'
```

Finally, we'll give our bash prompt itself 2 CPUs, since this is where we'll run the benchmarking tool.

```
taskset -cp 2,3 $$
```

Now let's build a little benchmarking tool.

## A benchmarking tool

Our benchmark tool will run in an open mode (requests from the same client do not wait on each other) and closed mode (requests from the same client do wait on each other).

```
mkdir /tmp/bench
```

You pass `-closed` or `-open` to toggle the modes. Pass `-seconds` to set the length of the run. For a closed loop run, you need to say how many `-clients` to limit to.

For an open loop run, you must set the `-rate` of requests per second. By default the gap before each request is random with a mean of one over `-rate` (a Poisson process). `-even` makes every gap exactly one over `-rate`. You can pass `-retry DURATION` to send a slow request again, up to 3 times in total.

You pick the driver to use with `-driver` (e.g. nginx or PostgreSQL). (There'll be some other flags we'll add to driver-specific code later on.)

```
package main

import (
        "flag"
        "fmt"
        "log"
        "math/rand/v2"
        "slices"
        "sync"
        "time"
)

var (
        driver  = flag.String("driver", "http", "how to send each request: http or postgres")
        closed  = flag.Bool("closed", false, "run a closed loop")
        open    = flag.Bool("open", false, "run an open loop")
        clients = flag.Int("clients", 0, "with -closed, how many clients")
        rate    = flag.Float64("rate", 0, "with -open, requests per second")
        seconds = flag.Float64("seconds", 30, "how long to run")
        even    = flag.Bool("even", false, "with -open, space requests evenly instead of at random (Poisson) gaps")
        retry   = flag.Duration("retry", 0, "with -open, send a request again if it is unanswered this long, up to 3 times")
)

type sender func(key int) error

var drivers = map[string]func() sender{}

type result struct {
        scheduled, answered time.Duration
        ok                  bool
}

var (
        start   time.Time
        mu      sync.Mutex
        results []result
)
```

/tmp/bench/main.go

We'll model the closed loop benchmark as a degenerate form of the open loop benchmark: instead of just sending more requests at a chosen rate, we wait for the last request to complete.

```
func main() {
        flag.Parse()
        if *closed == *open || (*closed && *clients == 0) || (*open && *rate == 0) {
                log.Fatal("use -closed -clients N or -open -rate R")
        }
        connect, ok := drivers[*driver]
        if !ok {
                log.Fatalf("no driver %q", *driver)
        }
        request := connect()
        // -open gets 1 loop with indefinite new clients making a single request (aside from retries)
        loops := 1
        if *closed {
                // -closed gets 1 loop per client
                loops = *clients
        }
        start = time.Now()
        var wg sync.WaitGroup
        for range loops {
                wg.Add(1)
                go func() {
                        defer wg.Done()
                        for scheduled := time.Duration(0); scheduled.Seconds() < *seconds; {
                                if *open {
                                        time.Sleep(time.Until(start.Add(scheduled)))
                                }
                                answered := make(chan struct{})
                                wg.Add(1)
                                go func(scheduled time.Duration) {
                                        defer wg.Done()
                                        send(request, scheduled)
                                        close(answered)
                                }(scheduled)
                                if *closed {
                                        <-answered
                                        scheduled = time.Since(start) // the next request goes out now
                                } else {
                                        scheduled += gap() // the next request goes out on schedule, answered or not
                                }
                        }
                }()
        }
        wg.Wait()
        summarize()
}
```

/tmp/bench/main.go

The `gap` function is dependent on the rate and distribution of requests.

```
func gap() time.Duration {
        if *even {
                return time.Duration(float64(time.Second) / *rate)
        }
        return time.Duration(rand.ExpFloat64() / *rate * float64(time.Second))
}
```

/tmp/bench/main.go

The `send` function wraps requests to retry ones that take too long if `-retry` is set.

```
func send(request sender, scheduled time.Duration) {
        answered := make(chan error, 3)
        key := rand.IntN(1_000_000) // a random id for the driver's query
        attempt := func() { answered <- request(key) }
        go attempt()
        var first error
        for copies, got := 1, false; !got; copies++ {
                var again <-chan time.Time
                if *retry > 0 && copies < 3 {
                        again = time.After(*retry)
                }
                select {
                case first = <-answered:
                        got = true
                case <-again:
                        go attempt()
                }
        }
        finished := time.Since(start)
        mu.Lock()
        defer mu.Unlock()
        results = append(results, result{scheduled, finished, first == nil})
}
```

/tmp/bench/main.go

Lastly, a helper to summarize latencies and throughput.

```
func summarize() {
        var latencies []time.Duration
        var total, elapsed time.Duration
        failed := 0
        for _, r := range results {
                if !r.ok {
                        failed++
                        continue
                }
                total += r.answered - r.scheduled
                elapsed = max(elapsed, r.answered)
                latencies = append(latencies, r.answered-r.scheduled)
        }
        mean := time.Duration(0)
        if len(latencies) > 0 {
                mean = total / time.Duration(len(latencies))
        }
        fmt.Printf("%.0f answered/s over %.1f s, mean %.2f ms, p50 %s, p99 %s, max %s; %d failed\n",
                float64(len(latencies))/elapsed.Seconds(), elapsed.Seconds(),
                mean.Seconds()*1000, at(latencies, 0.5), at(latencies, 0.99), at(latencies, 1), failed)
}

func at(latencies []time.Duration, fraction float64) string {
        if len(latencies) == 0 {
                return "none"
        }
        slices.Sort(latencies)
        return fmt.Sprintf("%.2f ms", latencies[min(len(latencies)-1, int(fraction*float64(len(latencies))))].Seconds()*1000)
}
```

/tmp/bench/main.go

Importantly, latency counts from when a request was *scheduled*, not from when it was sent. If you time from the send you can reintroduce coordinated omission into an open loop.

Now let's build the drivers.

First nginx, which fetches the page we set up without decompressing it (we don't want the generator to be doing unnecessary work).

```
package main

import (
        "flag"
        "fmt"
        "io"
        "net/http"
)

var timeout = flag.Duration("timeout", 0, "give up on an HTTP request after this long")

func init() { drivers["http"] = connectHTTP }

func connectHTTP() sender {
        client := &http.Client{Timeout: *timeout, Transport: &http.Transport{MaxIdleConnsPerHost: 100_000}}
        return func(int) error {
                request, _ := http.NewRequest("GET", "http://127.0.0.1:9100/page.txt", nil)
                request.Header.Set("Accept-Encoding", "gzip")
                response, err := client.Do(request)
                if err != nil {
                        return err
                }
                _, err = io.Copy(io.Discard, response.Body)
                response.Body.Close()
                if err == nil && response.StatusCode != http.StatusOK {
                        return fmt.Errorf("%s", response.Status)
                }
                return err
        }
}
```

/tmp/bench/nginx.go

And then Postgres.

```
package main

import (
        "context"
        "flag"
        "log"

        "github.com/jackc/pgx/v5/pgxpool"
)

var query = flag.String("sql", "", "the query to run, with $1 as a random id")

func init() { drivers["postgres"] = connectPostgres }

func connectPostgres() sender {
        ctx := context.Background()
        config, err := pgxpool.ParseConfig("")
        if err != nil {
                log.Fatal(err)
        }
        size := 1 // -open queues on one connection; -closed gets one per client
        if *closed {
                size = *clients
        }
        config.MaxConns = int32(size)
        pool, err := pgxpool.NewWithConfig(ctx, config)
        if err != nil {
                log.Fatal(err)
        }
        var conns []*pgxpool.Conn // open every connection before the run
        for range size {
                conn, err := pool.Acquire(ctx)
                if err != nil {
                        log.Fatal(err)
                }
                conns = append(conns, conn)
        }
        for _, conn := range conns {
                conn.Release()
        }
        return func(key int) error {
                conn, err := pool.Acquire(ctx)
                if err != nil {
                        return err
                }
                defer conn.Release()
                _, err = conn.Exec(ctx, *query, key)
                return err
        }
}
```

/tmp/bench/postgres.go

Build it all.

```
cd /tmp/bench
go mod init bench
go mod tidy
go build -o bench
```

Now let's figure out the peak sustained requests per second for nginx and PostgreSQL on our machine for the workload we'll use for both. We'll do this by growing the number of clients in a closed loop benchmark and finding the peak.

```
sweep() {
  for c in 1 2 4 8 16 32; do
    ./bench -closed -clients $c -seconds 5 "$@" | tee /dev/stderr;
  done | sort -n | tail -1 | cut -d' ' -f1;
}
```

First nginx, which on my machine peaks at 250 requests per second.

```
$ NGINX_CAPACITY=$(sweep -driver http)
245 answered/s over 5.0 s, mean 4.08 ms, p50 4.08 ms, p99 4.16 ms, max 4.93 ms; 0 failed
250 answered/s over 5.0 s, mean 7.99 ms, p50 7.98 ms, p99 8.10 ms, max 12.39 ms; 0 failed
250 answered/s over 5.0 s, mean 15.97 ms, p50 15.97 ms, p99 16.24 ms, max 16.50 ms; 0 failed
247 answered/s over 5.0 s, mean 32.33 ms, p50 32.28 ms, p99 35.01 ms, max 36.31 ms; 0 failed
246 answered/s over 5.1 s, mean 64.55 ms, p50 64.90 ms, p99 65.94 ms, max 66.17 ms; 0 failed
247 answered/s over 5.1 s, mean 128.05 ms, p50 129.28 ms, p99 134.23 ms, max 135.40 ms; 0 failed
```

And then PostgreSQL, which on my machine peaks at 226 requests per second.

```
$ POSTGRES_QUERY='SELECT sum(balance) FROM accounts WHERE id BETWEEN $1 AND $1 + 49999'
$ POSTGRES_CAPACITY=$(sweep -driver postgres -sql "$POSTGRES_QUERY")
219 answered/s over 5.0 s, mean 4.55 ms, p50 4.55 ms, p99 6.82 ms, max 7.23 ms; 0 failed
209 answered/s over 5.0 s, mean 9.58 ms, p50 9.70 ms, p99 14.42 ms, max 16.27 ms; 0 failed
226 answered/s over 5.0 s, mean 17.71 ms, p50 17.95 ms, p99 26.33 ms, max 34.11 ms; 0 failed
209 answered/s over 5.0 s, mean 38.21 ms, p50 36.73 ms, p99 65.19 ms, max 71.68 ms; 0 failed
222 answered/s over 5.0 s, mean 71.79 ms, p50 72.79 ms, p99 110.88 ms, max 128.87 ms; 0 failed
218 answered/s over 5.1 s, mean 145.71 ms, p50 147.42 ms, p99 228.83 ms, max 265.13 ms; 0 failed
```

We'll use these rates to drive benchmarks at fractions of peak capacity as we go.

Let's take a closer look at closed loop benchmarks.

## Closed loop

In a closed loop benchmark we have a fixed number of clients make requests, each waiting for their last request to succeed before making the next. This makes it a fine approach for finding maximum throughput, so long as you increase the number of clients until your throughput peaks. But there are a number of well-known properties that make closed loops bad for uncovering real-world latency.

## Property 1: Stalls and slow requests are hidden

In this example, we'll kick off a PostgreSQL background job that locks the `accounts` table we created for half a second every 5 seconds.

```
while sleep 5; do
  psql -qc 'BEGIN; LOCK accounts; SELECT pg_sleep(0.5); COMMIT' > /dev/null;
done &
```

We'd expect p99 latency to go up since the table is not available every 5 seconds for half a second. But when we run the closed loop benchmark now we'll see a p99 response time well below the actual max times.

```
$ ./bench -closed -driver postgres -clients 8 -sql "$POSTGRES_QUERY"
206 answered/s over 30.0 s, mean 38.79 ms, p50 35.88 ms, p99 59.09 ms, max 582.70 ms; 0 failed
```

Gil Tene called this [coordinated omission](https://groups.google.com/g/mechanical-sympathy/c/icNZJejUHfE/m/BfDekfBEs_sJ?utm_source=theconsensus.dev&utm_medium=referral), where the generator coordinates with the server, sending nothing while it stalls.

If we run the same benchmark open looped, we see a more expected p99 latency, near half a second.

```
$ ./bench -open -driver postgres -rate $((POSTGRES_CAPACITY/2)) -sql "$POSTGRES_QUERY"
111 answered/s over 30.0 s, mean 60.37 ms, p50 7.48 ms, p99 482.80 ms, max 520.46 ms; 0 failed
```

It wasn't that the closed loop benchmark was not fair. Since only 8 requests can be waiting when the lock is taken, each stall catches at most 8 of the roughly 6,200 requests in the run, which is well under 1%. It just isn't reflective of how users will actually use your software. And when they use your software the open loop way (the more likely way), they'll experience much higher p99 latency.

Kill the background job we started.

```
kill %1
```

As Marc Brooker [said](https://brooker.co.za/blog/2025/05/20/icpe.html?utm_source=theconsensus.dev&utm_medium=referral), closed loop benchmarks are "too kind to realistically reflect how performance changes with load, for the simple reason that they slow their load down when latency goes up."

## Property 2: Latency is a function of the number of clients

We saw this already as we looked for maximum throughput. You can get whatever latency you want because in a closed loop benchmark mean latency is *defined* as the number of clients divided by throughput. It is a restatement of [Little's law](https://en.wikipedia.org/wiki/Little%27s_law?utm_source=theconsensus.dev&utm_medium=referral): requests in flight equal throughput times mean latency. In a closed loop the requests in flight are the clients.

```
$ for c in 1 4 16 64; do
  ./bench -closed -driver postgres -clients $c -seconds 10 -sql "$POSTGRES_QUERY"
done
243 answered/s over 10.0 s, mean 4.11 ms, p50 4.07 ms, p99 5.76 ms, max 11.73 ms; 0 failed
245 answered/s over 10.0 s, mean 16.33 ms, p50 16.11 ms, p99 24.15 ms, max 31.20 ms; 0 failed
242 answered/s over 10.0 s, mean 66.01 ms, p50 65.32 ms, p99 86.05 ms, max 126.33 ms; 0 failed
234 answered/s over 10.1 s, mean 271.82 ms, p50 270.44 ms, p99 356.01 ms, max 500.50 ms; 0 failed
```

Whereas latency in an open loop benchmark at peak throughput is a function of the length of the benchmark itself. (To ensure we actually get peak throughput we'll increase the `POSTGRES_CAPACITY` slightly.)

```
$ for s in 10 20 40; do
  ./bench -open -driver postgres -rate $((POSTGRES_CAPACITY*11/10)) -seconds $s -sql "$POSTGRES_QUERY"
done
246 answered/s over 10.1 s, mean 146.42 ms, p50 166.94 ms, p99 252.30 ms, max 261.09 ms; 0 failed
242 answered/s over 20.3 s, mean 162.60 ms, p50 168.56 ms, p99 382.80 ms, max 405.64 ms; 0 failed
244 answered/s over 41.0 s, mean 643.91 ms, p50 807.49 ms, p99 1103.70 ms, max 1149.02 ms; 0 failed
```

Or if we slightly reduce the throughput so the queue can handle bursts, we can observe latency differing by the spacing of requests (evenly spaced within a second, or randomly spaced within a second).

```
$ ./bench -open -driver postgres -rate $((POSTGRES_CAPACITY*3/4)) -sql "$POSTGRES_QUERY"
171 answered/s over 30.0 s, mean 8.71 ms, p50 7.05 ms, p99 29.64 ms, max 54.57 ms; 0 failed
$ ./bench -open -driver postgres -rate $((POSTGRES_CAPACITY*3/4)) -sql "$POSTGRES_QUERY" -even
169 answered/s over 30.0 s, mean 4.74 ms, p50 4.69 ms, p99 6.99 ms, max 10.71 ms; 0 failed
```

All of this is to say, if latency has a direct relationship to throughput, you're probably doing closed loop benchmarks that do not discover true latency in real world scenarios.

Now let's focus on open loop benchmarks.

## Open loop

Open loop benchmarks do not depend on the server to decide when to send their requests. But there are also some ways that open loop benchmarks might not fairly represent real-world workloads.

## Property 1: There is no neutral distribution of requests

Popular workload generation tools prefer to [distribute](https://github.com/giltene/wrk2/blob/44a94c17d8e6a0bac8559b53da76848e430cb7a7/src/wrk.c?utm_source=theconsensus.dev&utm_medium=referral#L433-L436) [requests](https://github.com/tsenart/vegeta/blob/v12.12.0/lib/pacer.go?utm_source=theconsensus.dev&utm_medium=referral#L51-L72) [evenly](https://theconsensus.dev/project/k6/source/v2.3.0/lib/executor/helpers.go#L-207). For example, delivering a rate of 1000 requests per second with all requests evenly spaced. This models no bursty behavior at all. Some tools, like [pgbench](https://www.postgresql.org/docs/current/pgbench.html?utm_source=theconsensus.dev&utm_medium=referral#:~:text=The%20rate%20is%20targeted,to%20catch%20up%20again.), offer random distribution of requests within the desired rate, along a Poisson distribution. While [some](https://cs-web.bu.edu/fac/crovella/paper-archive/sigm98-surge.pdf?utm_source=theconsensus.dev&utm_medium=referral) [studies](https://arxiv.org/pdf/2003.03423?utm_source=theconsensus.dev&utm_medium=referral) [have](https://web.stanford.edu/class/cs244/papers/paxson1995.pdf?utm_source=theconsensus.dev&utm_medium=referral) [shown](https://doi.org/10.1145/2254756.2254766?utm_source=theconsensus.dev&utm_medium=referral) that even Poisson distributions are not bursty enough to reflect observed real-world workloads.

Distributing requests evenly is the gentlest on latency, we already saw this above.

```
$ ./bench -open -driver postgres -rate $((POSTGRES_CAPACITY*3/4)) -sql "$POSTGRES_QUERY" -even
169 answered/s over 30.0 s, mean 4.74 ms, p50 4.69 ms, p99 6.99 ms, max 10.71 ms; 0 failed
```

While random distribution had 4x worse p99 latency.

```
$ ./bench -open -driver postgres -rate $((POSTGRES_CAPACITY*3/4)) -sql "$POSTGRES_QUERY"
171 answered/s over 30.0 s, mean 8.71 ms, p50 7.05 ms, p99 29.64 ms, max 54.57 ms; 0 failed
```

## Property 2: Clients do not react to the server

The usual definition of open loop benchmarks is that clients do not react to the server. So open loop benchmarks would not *classically* model retries. This allows you to measure how fast the server can respond, but it won't tell you if the server is able to recover after, say, an outage.

The [2022 Metastable Failures in the Wild](https://www.usenix.org/system/files/osdi22-huang-lexiang.pdf?utm_source=theconsensus.dev&utm_medium=referral) paper showed that *retries* after an initial trigger subsided were the main sustaining factor in over half of large historic outages surveyed.

I hesitate to call this a "property" of open loop benchmarks because you can just… support retries… as we've already done. We can see this in action by stopping and continuing the nginx server we set up in the background.

```
while sleep 10; do
  sudo pkill -STOP -f 'nginx: worker';
  sleep 2;
  sudo pkill -CONT -f 'nginx: worker';
done &
```

And running the open loop benchmark with retries. If a request takes longer than `-retry DURATION` then the client will send the same request again, up to 3 times in total.

```
$ ./bench -open -driver http -rate $((NGINX_CAPACITY*7/10)) -seconds 40 -timeout 5s -retry 200ms
87 answered/s over 44.6 s, mean 2551.45 ms, p50 3102.18 ms, p99 4934.64 ms, max 4999.98 ms; 3067 failed
```

And without retries.

```
$ ./bench -open -driver http -rate $((NGINX_CAPACITY*7/10)) -seconds 40 -timeout 5s
166 answered/s over 41.8 s, mean 615.12 ms, p50 30.22 ms, p99 4260.34 ms, max 4979.07 ms; 0 failed
```

Both show a similar p99 latency. But with retries, 3,067 requests failed and throughput halved because three copies at 70% load is 210% load and nginx never caught up.

## In parting

Use a closed loop with enough clients to find your throughput. Use an open loop at slightly less than peak throughput to find your latency. And be suspicious of a closed loop benchmark if someone talks about throughput increasing and latency decreasing.
