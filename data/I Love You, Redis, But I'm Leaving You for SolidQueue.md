---
title: "I Love You, Redis, But I'm Leaving You for SolidQueue"
source: "https://www.simplethread.com/redis-solidqueue/"
author:
  - "[[Matt Kelly]]"
published: 2025-11-19
created: 2026-02-09
description: "Rails 8 eliminates Redis from the default stack. Learn how SolidQueue, SolidCache, and SolidCable replace Redis for job processing, caching, and real-time updates—powered entirely by PostgreSQL. Explore the true cost of Redis, how SolidQueue works, when it scales, and how to migrate from Sidekiq to a simpler, Redis-free Rails architecture."
tags:
  - "clippings"
---
![I Love You, Redis, But I’m Leaving You for SolidQueue](https://www.simplethread.com/wp-content/uploads/2025/11/redis-tattoo-mattK.jpg)

[Rails 8](https://rubyonrails.org/), the latest release of the popular web application framework based on Ruby, excised [Redis](https://redis.io/)  from its standard technology stack. Redis is no longer required to queue jobs, cache partials and data, and send real-time messages. Instead, Rails’s new features— [SolidQueue](https://github.com/rails/solid_queue)  for job queuing, [SolidCache](https://github.com/rails/solid_cache)  for caching, and [SolidCable](https://github.com/rails/solid_cable) for transiting ActionCable messages—run entirely on your application’s existing relational database service. For most Rails applications, Redis can be discarded.

I know how that sounds. The Redis key-value store is fast, adept, and robust, and its reliability made it the preferred infrastructure for Rails job queueing and caching for more than a decade. Countless applications depend on Redis every day.

However, Redis does add complexity. SolidQueue, SolidCache, and SolidCable sparked something of an epiphany for me: [boring technology](https://boringtechnology.club/) such as relational database tables can be just as capable as a specialized solution.

Here, let’s examine the true cost of running Redis, discover how SolidQueue works and supplants a key-value store, and learn how to use SolidQueue to migrate an application’s job queues to vanilla PostgreSQL (or SQLite or MySQL). Web development is already too complicated—let’s *simplify*.

## The True Cost of Redis

What does Redis cost beyond its monthly hosting bill? Setup and ongoing maintenance are not free. To use Redis you must:

- Deploy, version, patch, and monitor the server software
- [Configure a persistence strategy](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence). Do you choose RDB snapshots, AOF logs, or both?
- Set and watch [memory limits](https://redis.io/docs/latest/operate/rs/databases/memory-performance/memory-limit/\))  and establish [eviction policies](https://redis.io/docs/latest/operate/rs/databases/memory-performance/eviction-policy)

In addition to those taxes, there are other ongoing burdens to infrastructure and interoperability. You must also:

- Sustain network connectivity, including firewall rules, between Rails and Redis
- Authenticate your Redis clients
- Build and care for a high availability (HA) Redis cluster
- Orchestrate the lifecycles of Sidekiq processes across deployments

Further, when something goes wrong with a job, you’re faced with debugging Redis and your RDBMS, two data stores with very different semantics, switching context between different query languages and tools. And then there’s the issue of two separate backup strategies. (You tested them both, right?)

In a “Redis-less” Rails stack, things are simpler. If Rails or PostgreSQL fails, everything stops.

## How SolidQueue Works

Redis is a very different data store than PostgreSQL. In many ways, Redis is treated as if it’s memory: atomic, volatile, and very fast. So how does SolidQueue manage to replace it with PostgreSQL?

[PostgreSQL 9.5](https://www.postgresql.org/docs/9.5/sql-select.html#sql-for-update-share)  enhanced its SQL `FOR UPDATE`  clause to add   `SKIP LOCKED`. The `FOR UPDATE`  clause creates an exclusive row lock. `SKIP LOCKED` further skips any rows currently locked. This mechanism makes running database-backed job queues viable, even at scale.

Here’s what happens when a worker needs a job:

```sql
SELECT * FROM solid_queue_ready_executions
WHERE queue_name = 'default'
ORDER BY priority DESC, job_id ASC
LIMIT 1
FOR UPDATE SKIP LOCKED
```

A free worker always picks up the next available job.

This database optimization solves the fundamental problem that plagued earlier database queue implementations: *lock contention*. A worker never waits for another and a worker never blocks. Multiple workers can query simultaneously and PostgreSQL guarantees each claims a unique job. When a worker finishes processing, it releases the lock and deletes the execution record.

The SolidQueue architecture centers on three tables:

1. All jobs are stored in `solid_queue_jobs`. The table persists job metadata, such as the name of the job, its Ruby class, and timestamps to record when the job started and finished. By default, every queueing request is recorded in this table and retained permanently, even after the job completes.
2. A scheduled job waits in `solid_queue_scheduled_executions` until its scheduled time arrives.
3. A job ready to run immediately is queued to solid\_queue\_ready\_executions, where a worker claims it.

Job tables can churn rapidly and steadily (there are hordes of inserts and deletes), but PostgreSQL’s MVCC design handles this fine with its built-in autovacuum process. No special tuning required.

A handful of processes coordinate this flow.

- Workers poll `solid_queue_ready_executions` at configurable intervals (as fast as 0.1 seconds for high-priority queue/se
- Jobs are claimed and subsequently executed with `FOR UPDATE SKIP LOCKED` to control concurrency.
- Dispatchers poll `solid_queue_scheduled_executions` once per second, moving due jobs into the ready table.
- Schedulers manage recurring tasks by enqueueing jobs per defined timetables.
- A supervisor process monitors all these, tracking heartbeats and restarting crashed processes.

These separate concerns may be SolidQueue’s most elegant feature. Each process type operates on different tables with different polling intervals optimized for its workload. The processes never interfere with each other, and the database handles all coordination through vanilla transactional database semantics.

## Scheduling Recurring Jobs with SolidQueue

Recurring jobs add to the costs inherent with Redis, as you often must integrate yet another library to schedule regular jobs. For example, assuming an application uses [Sidekiq](https://sidekiq.org/)  for its [ActiveJob](https://guides.rubyonrails.org/active_job_basics.html)  adapter, [sidekiq-cron](https://github.com/sidekiq-cron/sidekiq-cron)  and [whenever](https://github.com/javan/whenever) are two popular solutions to schedule repetitive jobs.

Nothing supplemental is required; however, if you use SolidQueue. It includes *cron* -style recurring jobs out of the box. Simply edit *config/recurring.yml*. The configuration file should look hauntingly familiar:

```yml
# config/recurring.yml
production:

  cleanup_old_sessions:
    class: CleanupSessionsJob
    schedule: every day at 2am
    queue: maintenance

  send_daily_digest:
    class: DailyDigestJob
    schedule: every day at 9am
    queue: mailers

  refresh_cache:
    class: CacheWarmupJob
    schedule: every hour
    queue: default
```

Here’s how SolidQueue’s recurring jobs work in practice.

- When the scheduler runs it finds the jobs due and enqueues each job to run. In the list above, for example, the task **refresh\_cache** causes CacheWarmupJob to run at the top of each hour.
- Concurrently, the scheduler also queues a new job to run at the time of the next occurrence in the series. Continuing the example, an hourly task that runs at 8:00 AM schedules itself to run again at 9:00 AM.
- The 9:00 AM task schedules itself for 10:00 AM, ad infinitum.

This pattern is borrowed from [GoodJob](https://github.com/bensheldon/good_job), another database-backed queue system. It’s crash-resistant because schedules are deterministic. “Every hour” always resolves to the top of the hour, regardless of when the scheduler process starts.

If you want more detail on everything SolidQueue is doing under the hood, over at AppSignal gives a really [thorough treatment](https://blog.appsignal.com/2025/06/18/a-deep-dive-into-solid-queue-for-ruby-on-rails.html) of all its pulleys and belts.

## Job Concurrency: The Feature You Didn’t Know You Needed

If you’ve historically used Rails at mere mortal scale, you may be unaware that Sidekiq also offers [concurrency limits as a paid feature](https://github.com/sidekiq/sidekiq/wiki/Ent-Rate-Limiting) in Sidekiq Enterprise. If you’re considering using Sidekiq, concurrency limiting alone is worth the additional expense for the Enterprise edition.

But SolidQueue gives you this, and more, for free! Simply add `limits_concurrency` to any job.

```sql
class ProcessUserOnboardingJob < ApplicationJob
  limits_concurrency to: 1,
    key: ->(user) { user.id },
    duration: 15.minutes

def perform(user)<
    # Complex onboarding workflow
  end
end
```

`limits_concurrency to: 1` ensures only one `ProcessUserOnboardingJob` job runs per user at any one time.

The `duration` parameter is also essential, as it defines how long SolidQueue guarantees the concurrency limit. If a job crashes, say, the semaphore eventually expires, preventing deadlocks caused by crashed workers that never release their locks.

The implementation uses two tables: `solid_queue_semaphores`  to track concurrency limits and `solid_queue_blocked_executions` to hold jobs waiting for semaphore release. When a job finishes, it releases its semaphore and triggers a dispatcher to unblock the next waiting job. It’s elegant, database-native, and requires zero external coordination.

## Monitor SolidQueue with Mission Control

The no-fee version of Sidekiq’s web user interface is okay. [Sidekiq Pro](https://sidekiq.org/) ($949/year) and Sidekiq Enterprise (starting at $1,699/year) offer enhanced dashboards.

[Mission Control Jobs](https://github.com/rails/mission_control-jobs) is free, open source, and designed specifically for Rails 8’s SolidQueue ecosystem:

```sql
# config/routes.rb
mount MissionControl::Jobs::Engine, at: "/jobs"
```

With this single line in your routes, you now have:

- “Real-time” job status across all queues
- Failed job inspection with full stack traces
- Retry and discard controls with batch operations
- Scheduled job timeline visualization
- Recurring job management
- Queue-specific metrics and throughput graphs

Even better, Mission Control can inspect your database schema. When you inspect a failed job, you can see its job arguments (just like Sidekiq), but you can also query the job data with everyone’s favorite query language, SQL:

```sql
SELECT j.queue_name, COUNT(*) as failed_count
FROM solid_queue_failed_executions fe
JOIN solid_queue_jobs j ON j.id = fe.job_id
WHERE fe.created_at > NOW() - INTERVAL '1 hour'
GROUP BY j.queue_name;
```

SQL is a language you already know running in tools you already use. No external parsing. No timestamp arithmetic. Just SQL.

## The Migration Path: From Sidekiq to SolidQueue

It’s almost trivial to migrate from Sidekiq to SolidQueue.

#### Step 1: Change the Rails queue adapter

Rails’s queue adapter setting specifies which queuing backend is used for processing background jobs asynchronously. Set it to `:solid_queue`.

```ruby
# config/environments/production.rb
config.active_job.queue_adapter = :solid_queue
```

#### Step 2: Install SolidQueue

The SolidQueue gem must be installed separately from Rails. The gem includes two tasks to add SolidQueue’s tables to the application’s database.

```sql
$ bundle add solid_queue
$ rails solid_queue:install
$ rails db:migrate
```

#### Step 3: Replace sidekiq-cron schedules

Assuming you are using Sidekiq, convert your *config/sidekiq.yml*  cron schedules to *config/recurring.yml*. The config is similarly shaped, but you’ll need to update key names and convert classic cron strings to Fugit’s preferred natural language:

```sql
# OLD: config/sidekiq.yml
:schedule:
  cleanup_job:
    cron: '0 2 * * *'
    class: CleanupJob
# NEW: config/recurring.yml
production:
  cleanup_job:
    class: CleanupJob
    schedule: every day at 2am
```

#### Step 4: Update your Procfile

A *Procfile*  enumerates the processes to launch on application start. To kick off SolidQueue, add the task `solid_queue:start` (replacing Sidekiq, say).

```sql
web: bundle exec puma -C config/puma.rb
jobs: bundle exec rake solid_queue:start
```

#### Step 5: Blast the old stack

Redis and Sidekiq are now obsolete. You can remove any corresponding gems from the *Gemfile*. Run Bundler to remove the dependencies from *Gemfile.lock*.

```sql
# Gemfile - DELETE
# gem "redis"<
# gem "sidekiq"
# gem "sidekiq-cron"

$ bash
$ bundle install
$ bundle clean --force
```

Your existing ActiveJob jobs work without modification. All retry strategies, error handling, and job options transfer directly.

## When NOT To Use SolidQueue

Some applications *need* Redis. Here are some candidates:

- You’re processing thousands of jobs per second sustained (not spikes, but consistent, sustained load).
- [Job latency under 1ms](https://redis.io/docs/latest/develop/use/patterns/twitter-clone) is critical to your business. This is a real and pressing concern for real-time bidding, high frequency trading (HFT), and other applications in the same ilk.
- You have complex [pub/sub](https://redis.io/docs/latest/develop/interact/pubsub) patterns across multiple services
- You require intensive [rate limiting or counters](https://redis.io/commands/incr) that benefit from Redis’s atomic operations.

As a benchmark, Shopify engineer John Duff presented some numbers at [Big Ruby 2013](https://www.youtube.com/watch?v=lsKXPnB6SvQ): 833 requests/second, 72ms average response time, 53 servers with 1,172 worker processes. At that scale—twelve years ago—Shopify needed Redis-level infrastructure. Are you there yet?

You definitely do not need Redis if processing is less than 100 jobs/second or job latency tolerance is greater than 100ms. You may need Redis if processing 100-1000 jobs/second (test both, measure), traffic is spiky, (Black Friday sales, ticket releases), or sub-100ms job queue latency is required.

## Practical Implementation Guide

Let’s walk through a real-world setup.

#### Step 1: Generate a New Rails 8 App

```ruby
$ rails new myapp --database=postgresql
$ cd myapp
```

Rails 8 auto-configures SolidQueue, SolidCache, and SolidCable. You’re halfway done already.

#### Step 2: Set Up Queue Database

SolidQueue needs to know where to store its tables. The recommended approach is a separate database connection (even if it’s the same physical database server).

Update your *config/database.yml*:

```sql
development:
  primary: &primary_development
    <<: *default
    database: myapp_development
  queue:
    <<: *primary_development
   database: myapp_queue_development
    migrations_paths: db/queue_migrate
```

If you’re using SQLite or MySQL, the [official SolidQueue documentation](https://github.com/rails/solid_queue#usage-in-development-and-other-non-production-environments) has examples for those setups.

Now tell SolidQueue to use its own connection in *config/environments/development.rb*:

```sql
Rails.application.configure do
  config.active_job.queue_adapter = :solid_queue
  config.solid_queue.connects_to = { database: { writing: :queue } }
end
```

Run db:prepare and Rails handles everything automatically:

```ruby
$ rails db:prepare
```

Rails creates the queue database and loads the schema. No custom rake tasks needed.

#### Step 3: Configure Mission Control Authentication

```ruby
# config/environments/development.rb (add to existing config block)
config.mission_control.jobs.http_basic_auth_user = "dev"
config.mission_control.jobs.http_basic_auth_password = "dev"
```

#### Step 4: Mount Mission Control

```ruby
# config/routes.rb
mount MissionControl::Jobs::Engine, at: "/jobs"
```

#### Step 5: Create Procfile.dev

```ruby
web: bin/rails server
jobs: bundle exec rake solid_queue:start
```

#### Step 6: Start Everything

```shell
# Start all the servers for Rails from the shell
$ bin/dev
```

## How to Test SolidQueue

Create a test job, enqueue it, and watch it in Mission Control:

```shell
# Generate a new job class from the shell
$ rails generate job EmailReport
```

Open the new Ruby file and add this code.

```ruby
# Job definition
class EmailReportJob < ApplicationJob
  queue_as :default
  retry_on StandardError, wait: :exponentially_longer, attempts: 5
  def perform(user_id)
    user = User.find(user_id)
    ReportMailer.weekly_summary(user).deliver_now
  end
end
```

Next, run the Rails console and queue an immediate job.

```ruby
console> EmailReportJob.perform_later(User.first.id)
```

While in the console, queue a scheduled job, too.

```shell
console> EmailReportJob
.set(wait:  1.week)
.perform_later(User.first.id)
```

Make it recurring in *config/recurring.yml*:

```shell
production:
  weekly_reports:<
    class: EmailReportJob
    schedule: every monday at 8am
    queue: mailers
```

Finally, you might want to kick over your server and visit *http://localhost:3000/jobs* to admire your handiwork in Mission Control Jobs.

## Common Gotchas

#### Single Database Setup (Alternative)

SolidQueue recommends the use of a separate database connection, but you can run everything in one database, if you prefer.

1. Copy the contents of *db/queue\_schema.rb* into a regular migration
2. Delete *db/queue\_schema.rb*
3. Remove **config.solid\_queue.connects\_to** from your environment configs
4. Run rails db:migrate

This works fine for smaller apps, but at the cost of operational flexibility. The Rails team recommends the separate connection approach. See the [official docs](https://github.com/rails/solid_queue#single-database-configuration) for details.

#### Mission Control in Production

Don’t forget to add authentication to limit access to Mission Control in production environments! The development example uses Basic Auth, but you’ll want something more robust for production:

```ruby
# config/initializers/mission_control.rb
Rails.application.configure do
  config.mission_control.jobs.base_controller_class =
    "AdminController"
end
```

#### Polling Intervals

The default polling interval is 1 second for scheduled jobs and 0.2 seconds for ready jobs. If you’re migrating from Sidekiq and notice jobs feel “slower,” check your expectations. In my experience, SolidQueue’s defaults work well for most applications. Sub-second latency usually doesn’t matter for background jobs.

#### ActionCable and Turbo Streams

If you’re using ActionCable (or anything that depends on it like Turbo Streams), you’ll need to configure SolidCable with its own database connection too. Add a cable database to your database.yml:

```yml
# config/database.yml
production:
  primary:
    <<: *default
    database: myapp_production
  cable:
    <<: *default
    database: myapp_cable_production
    migrations_paths: db/cable_migrate
```

Then in *config/cable.yml*:

```
production:
  adapter: solid_cable
  connects_to:
    database:
      writing: cable
  polling_interval: 0.1.seconds
  message_retention: 1.day
```

#### Polling Interval

The polling\_interval of 0.1 seconds means your ActionCable server polls the database 10 times per second—light enough for PostgreSQL to handle without breaking a sweat. This gives you 100ms latency for real-time updates, which feels plenty snappy for Turbo Streams, live notifications, or even chat.

## Does it Scale

You may be asking the [timeless question](https://www.youtube.com/watch?v=VBwWbFpkl):

**bUT doES iT ScALe?**

The answer is yes, it scales. A better question, though, is “Does it scale enough for me?” To answer, you can start with this lovely formula from Nate Berkopec’s 2015 article [“Scaling Ruby Apps to 1000 RPM”](https://www.speedshop.co/2015/07/29/scaling-ruby-apps-to-1000-rpm.html).

**Required app instances = request rate (req/sec) × average response time (sec)**

Let’s do the math for a typical app. Say your app is getting 100 requests per minute, with a 200ms average response time. That’s ~1.67 requests per second. Multiply by 0.2 seconds and you get 0.083 application instances required. You need 8% of one application instance to handle your load.

As an anecdote, 37signals [processes 20 million jobs per day](https://blog.appsignal.com/2025/06/18/a-deep-dive-into-solid-queue-for-ruby-on-rails.html). That’s roughly 230 jobs per second running all on MySQL sans Redis. Unless you’re processing millions of jobs per day, PostgreSQL can handle your load.

Here’s a side by side comparison of Redis and Sidekiq versus SolidQueue.

| Aspect | Redis + Sidekiq | SolidQueue |
| --- | --- | --- |
| Setup complexity | Separate service + config | Already there |
| Query language | Redis commands | SQL |
| Monitoring | Separate dashboard | Same as your app |
| Failure modes | 6+ distinct scenarios | 2 scenarios |
| Job throughput | ~1000s/sec | ~200-300/sec |
| Good enough for | 99.9% of apps | 95% of apps |

## The Bottom Line

Redis and Sidekiq are masterfully engineered and Rails applications have benefited immeasurably from the combination for over a decade. But for most Rails apps, Redis and Sidekiq solve a problem you don’t have at a cost you can’t afford.

Give SolidQueue a spin. Your infrastructure simplifies, your operational burden lightens, and you can focus on building a product instead of maintaining a stack.

*A lot of these practices are still emerging in our community. If you have corrections, criticisms, or feedback, please reach out and let me know. I would love to hear from you.*

,

,

,

,
