---
title: "Database Connection Pool Sizing - Demystified! by Jasmin Fluri"
source: "https://www.youtube.com/watch?v=Cp-aFYHLiCw"
author:
  - "[[Devoxx]]"
published: 2026-04-01
created: 2026-04-03
description: "This talk addresses a common misconception in Oracle application development: that larger connection pools in the backend automatically lead to better performance.While this belief is widespread, exp"
tags:
  - "clippings"
---

> [!summary]
> A Devoxx talk explaining why larger database connection pools often hurt performance rather than help. Uses Little's Law to calculate minimum required connections and Kingman's formula to show how utilization above 80% causes exponential wait time increases. Provides the practical formula: max pool size = (CPU cores × 2) + spindle count, illustrated with a real-world banking system example.

![](https://www.youtube.com/watch?v=Cp-aFYHLiCw)

This talk addresses a common misconception in Oracle application development: that larger connection pools in the backend automatically lead to better performance.
While this belief is widespread, experienced DBAs understand that oversized connection pools can actually harm performance.
The presentation provides an introduction to connection pool sizing for backend developers of all seniority levels, explaining the reasons why excessively large pools negatively impact system throughput and resource efficiency.

A key part of the discussion focuses on mathematical principles behind connection pool behavior, including Kingman's law, which models queueing delays,
to illustrate how adding more connections can increase waiting times rather than reduce them.
The talk also covers the mathematical foundations for sizing connection pools optimally based on workload and resource constraints.

By the end of the session, attendees will be equipped with practical formulas and guidelines to calculate the appropriate size for their connection pools.
This knowledge will enable them to guide application teams towards resizing their pools in a way that maximizes performance, stability, and efficient resource use,
rather than simply increasing pool size in hopes of improving it.

## Transcript

**0:15** · So, welcome everyone. I'm so happy to be here. Today we are diving together into the topic of connection pool sizing. By the end of this session, I hope you will have a good understanding of why connection pool is necessary and what is going on inside a connection pool.

**0:34** · Uh my name is Jasmine. I'm a database engineer and in my consulting work I usually work between the infrastructure teams and the application teams. Um, I'm building database systems, automating services and that makes me also the per uh person that application teams asks why their queries are slow. So, this is me. Um, let's get started. Uh, connection pooling is a very common source of performance problems. Um but it is easily overlooked because implementing new functionality is easily more interesting than caring about one's query performance.

**1:14** · So which makes the right configuration that one um disappear in the background a little. So this is why we want to have a look into connection pool sizing and also find out how we can configure it properly.

**1:30** · Let's start with looking at what a connection is. what's going on there. A connection is a session uh between your application and the database. And over this session uh SQL statements are sent and in return queries come back in the context of this connection. Now if we want to execute a new SQL statement from our application against the database, first we need to open this connection to the database and then execute our SQL statement and then also close the connection again. So this sounds easy, right?

**2:08** · But opening and closing connections are very time consuming tasks that are happening and this makes it a bit of a problem.

**2:20** · Let's have a look at what happens if we open and close a connection. Again, this is the database. So, this might be a little technical. Now, this is a diagram of um closing a database applica uh database connection between a Hikari connection pool in blue and the Oracle database on the right. This is a bit simplified. I ignored all SSL TLS encryption here. So the first thing what happens is a TCP handshake you know the sins in act and act and then Oracle net tns negotiation happens. So the JDBC sends a connect in a TNS package and the service name and Oracle returns an accept with the protocol version and the used options.

**3:08** · After that authentication happens that's user user authentication in all phase one um the client sends the username um Oracle sends a challenge um with a salt and the encrypted session key and in all phase two the client sends the calculated verifier and the encryption password. This makes sure that the password is never transferred un unencrypted over the network.

**3:38** · and then everything is fine. So session in initialization can happen. So Hikari does an alter session um with its NLS uh settings and the time zone.

**3:53** · This is an optional round trip if you have it configured. It is your initialization SQL that you have. You don't have to have it. Um and then a pool validation happens at the end.

**4:06** · So you do a select one from dual and if this works the connection is ready.

**4:13** · So that's just all the round trips for opening one connection and it's seven to eight round trip depending on if you have your in it SQL. If you now encrypt it with SSL and TLS it adds additional two round trips. So a lot is going on a lot of network round trips.

**4:35** · Now if we do that or if we would do that for every query that we execute, what is happening?

**4:43** · Um let's have a look at how long it takes to open a connection. Um RT is our network roundrip time and is a multiplier and with Hikari and SSLTLS we have a rough roundtrip time of around 10. So if you are in the same data center in a different rack a full connection would lead to 5 to 20 milliseconds of time consumed across data center it's between 50 and 200 milliseconds and if you're cross region even this can add up to 800 milliseconds to 1.5 seconds.

**5:24** · So that's a lot of time spent in just connection in initialization.

**5:32** · So if we open a new connection for every database request that we're doing from our application, we wait and we wait a lot.

**5:41** · So connection pools make our life weight less and make our life faster.

**5:48** · Let's have a look at the job of a connection pool, what it's actually doing and why are we using it.

**5:55** · Um the connection pool is as I said between your application and the database and it maintains a pool of connections that you configured previously.

**6:06** · So every time a new query comes in you don't need to open another connections.

**6:10** · They're already there and the pool reuses those connections.

**6:16** · So when a query comes in it gets assigned to an open connection gets executed and sends the query back to the application.

**6:25** · Now we differentiate between active and idle connections. Active connections are those that actually are use um are executing queries currently and idle connections wait for incoming queries from your application.

**6:40** · If you have open connections, if you have idle connections, they're not free.

**6:45** · There's no free launch here. They still block a few megabytes of memory in your database.

**6:53** · So for every connection that you have opened 10 to 30 megabytes of memory are allocated to just leaving this connection open and this may add up as you open more and more connections.

**7:09** · Now third the connection pool manages also the connection life cycle.

**7:14** · It adds new connections if you have a lower and an upper bound configured. So as uh usage of the connection pool is rising, the connection pool might increase the amount of connections that are open. So this is a bit dynamic, but opening new connections can add overhead again because if you open too many connections at once, um the connection pools might lock out for a little until you can use it again.

**7:45** · So this can be another problem of using the connection pool. Um it also improves our performance because it reuses the connections. It handles the limits. It doesn't overuse the connections to the database and it balances our load that is coming from the application side.

**8:07** · Now when we configure application side database um if we configure connection pools we always can choose between the application side and the database side connection pools. So there are multiple ways of how we can approach connection pool sizing.

**8:26** · We also can have a combination of the two and let's have a look at what's the difference between them. So application side connection pools is what you probably all know and also have in your job applications. Um they are configured in for example Hikari and they can be very specific to your application and every application should have one because if they don't what we need to have from a database side is database site connection pools.

**8:59** · We usually use database side connection pools when we have applications without connection pools that just open connections randomly and don't close them again. So we need to handle pool size management and the connection management on the database side. So this is really something that you can use to treat symptoms of bad connection pooling.

**9:24** · Next, we want to look what happens when there are more requests to the database than actual connections.

**9:33** · So, we talked about o overloading the database with connections and now we want to see what happens. And if the application is hammering requests against the database, requests are cued.

**9:47** · For example, if you only have one connection to your database, but a very high number of requests that are sent, the requests cue.

**9:56** · So, they line up and wait to be assigned to an open connection.

**10:02** · Now, what's a queue? Let's quickly dive into the maths of queuing.

**10:07** · We have here a queuing model. Um when customers arrive in our system as the model is showing here um and all the server in our systems are occupied as well they start to create this queue that you see in the middle. Um the service time in a queueing system generally is our bottleneck. So that's where everything is locking up. So if the servers are busy all the time very long cues will happen. So service usually have a call principle which in computer science is almost always um first in first out. So the connections that arrive first also get served first.

**10:49** · Now with a queueing model we can calculate our maximal throughput of our uh connection pool. If we multiply the amount of servers that we're having with the service time, we get our maximum throughput that we can handle.

**11:05** · What we want to avoid, and this is important, um, is to have an arrival rate of queries or requests that is bigger than our maximal throughput because then our Q size would grow infinitely.

**11:23** · Let's have another look at our uh queuing model. Our connection pool is a queue as well.

**11:31** · Um where there are servers that um are open connections and the service times equals the execution times of our queries. So we have those incoming requests here. This is our connection pool with the waiting requests.

**11:46** · And ideally you don't have a queue.

**11:49** · That's what you want to avoid.

**11:51** · And the amount of connections that we have opened against our database are the servers that we're having with the service time being the execution time or the mean execution time of your queries.

**12:07** · Um with knowing that our connection pool is a queue, we can apply Little's law um defined by 1954 by John Little. Um and that was a good time before connection pool sizing was even a thing where little came up with this theorem. Um little's law was initially used um and still is to calculate the capacity of all sorts of cues. So also in manufacturing or in project management or in retails um little's law is applied to um calculate the size of cues and queuing.

**12:47** · So little's law is pretty simple. Um we calculate L which is equal to lambda \* W. Um L is the average numbers of customers that our maximum work in progress is.

**13:01** · So work in process times um divided by capacity.

**13:07** · Um lambda is our average arrival rate.

**13:11** · Um this is our throughput that we're having and w is the time spent in the system.

**13:17** · This is also called our lead time or service time. And as you can see immediately here the service time or also called lead time is the bottleneck in every queuing system.

**13:30** · And that's important. So if we can reduce our service time, the system will be faster. This means the faster your query performance is, the less problems you will have.

**13:47** · Um let's have a look at a practical application of Little's law. Um imagining we have a bookstore with 10 visitors arriving every hour.

**13:58** · It takes those visitors um 30 minutes or half an hour to find a book they want and after they have found their book they go and pay. It means that you have five customers at your shop at every given time.

**14:16** · Lambda is our throughput. W is the time spent or service time um that it takes uh to find a book which makes L the work in progress.

**14:30** · This is equals to the five customers that are in the shop at every given time.

**14:37** · But how does this help us with connection pool sizing? Let's have a look at the same example with a connection pool example.

**14:46** · Imagining that you have an application that executes 50 transactions per second.

**14:53** · That's our throughput.

**14:55** · What needs to be done? It takes those 50 transactions 100 milliseconds to get a response and leave. So that's our average query performance, the time spent, our service time, which means that you have five transaction open at every given time.

**15:15** · that is L.

**15:17** · So L is five.

**15:20** · This is the minimal amount of connections that you need to manage this throughput minimally.

**15:29** · And since we're working with averages, this can also be lower. Um but if we since we're using means here, um this is the minimal mean amount under the assumption the workload is stable. But almost no workload is stable. So, okay, cool. We set the pool size to five, right? Is that a good idea? No. No, it's not that easy. Um, but why is the minimal number not enough? Or why shouldn't you use your resources up to 100%. Because if we would have five, our resources that we're having would be used up to 100%.

**16:10** · And that's where the second law comes in.

**16:13** · um Kingman's law or Kingman's formula.

**16:16** · Um it was developed by the British mathematician uh Sir John Kingman in 1962 a little later than little and and it's approximation rather than an exact formula. Um Kingman's law says that even a small increase of utilization can cause a disproportionately large increase in waiting time.

**16:43** · So if your utilization or if your queries go up or your throughput goes up just a little um it can break a system that is close to capa close to capacity.

**16:57** · And if we have a look at this visually this is probably a bit too theoretical.

**17:03** · If we have a look at it visually um by keeping your utilization also of your connection pool or of any queuing system below 80% you maintain a buffer that helps you handle sudden spikes spikes in demand spikes in query performance um and it ensures a smoother performance of your system overall.

**17:28** · If you don't do this the systems system might tip over.

**17:34** · So it gets it gets unsustainable. All the pink area is the unsustainable area or danger zone. So as utilization increase also waiting time will increase exponentially and this tipping point is um important to know. it can be around 75 to 80% of your maximum capacity that you're having.

**18:03** · Um but let's look at what happens in this unstable zone.

**18:09** · So this is on the left side. You're overprovisioned. You have way more um capacity that you than you use that you need to.

**18:22** · But let's look at this unsustainable zone.

**18:25** · when we're unsustainable, when we are using our system up to capacity, um additional requests must wait for a free connection. So our queue starts to get bigger. This is where queuing happens and this is after this 80% um zone. So when a queue when the pool is highly utilized, additional requests must wait for a free connection.

**18:54** · So you have this dramatic increase.

**18:58** · It can also cause resource contention.

**19:01** · So high utilization means more threats or processes that are competing for the same connections in your connection pool and this leads to delays and potential deadlocks which is again unsustainable.

**19:16** · The third effect that we're having is um exponential back off. When the utilization is too high, um the time taken to to acquire a connection increases exponentially as well. So every additional request against database has to wait longer and that can lead to timeouts.

**19:38** · Um, in the Hikari CP docs, um, there's a very well phrase that says you want a small pool saturated with threats waiting for connections.

**19:50** · So, another problem when our connection pools are too big, time sharing. So we're no longer in the we don't don't have a enough um um we don't have enough resources but we have enough but our connection tool pools are too big um but the database isn't so the database doesn't have the resources but the connection pool is allocating them nonetheless. So time sharing sharing happens on the database.

**20:23** · Time sharing is also known as context switching or multitasking and this happens on the database side. So in multitasking the CPU especially keeps switching between processes because it wants to treat them equally.

**20:41** · So you see here in the picture um process PC0 comes in um but the context switch then happens after it's executed for a bit and it saves the state reloads another state from another process executes P1 a bit saves the state again and switches between those processes and this takes a lot of time saving state loading states again executing stuff a little because it wants to treat all incoming processes equally.

**21:16** · So we now know we don't set the pool to five.

**21:19** · But how do we find out the exact maximum size of our connection pool and this is with the process to core ratio that we can calculate. Uh the process to core ratio tells you how many processes you can have per CPU core. um that you have available and this is the amount of possible active connections that you can have and that will run smoothly. Um and one way you can calculate those is based on the amount of CPUs that you that you're having available and this is called the process to core ratio.

**22:00** · Um in general modern CPUs can handle multiple threats per core. In this example, we will calculate with the factor two. But this is something that you need to know about your hardware.

**22:16** · This means a quad core CPU with hyper threading can manage up to eight threads at once. Um, keep in mind on a server not only your connections are handled but other processes are being run in the background as well. So it's not only about executing qu queries also other stuff is running as well and need CPU time as well.

**22:43** · And when it comes to connection pooling the optimal process to core ratio can varying can vary depending on your workload that you're having. So a general guideline is to have the maximum number of connections to be two times the number of CPU. This might vary based on your hardware and this range helps to balance the load and ensures efficient use of your resources without overwhelming the CPU.

**23:13** · It's also important to monitor this um configuration because you might need to fine-tune it and as I said there might be other thing needing CPU as well. So keep that in mind and don't overdo it. Now how do we calculate the max pool size? We'll have a real life example after this. Um also Hikari CP documentation says that the pool size is the core count that you have available times two plus the effective spindle count of your disk.

**23:47** · Um so that makes a pretty easy uh calculation here. A four core server times 2 + 1 is nine connections that you can have maximally.

**24:04** · In a real life example, um this was a finance system handling uh customer transactions.

**24:11** · Um it was set up with eight JVMs that you're having on the left in pink. The connection pool was configured with an initial amount of 80 connections um and a maximum amount of 80 connections as well which opened 640 connections initially to the database server which had 104 cores with 208 threads.

**24:37** · So on eight JVMs times 80 init connections it's 640 connections. Um only the initialization for those connections took time because opening a connections as we learned takes some time. Um and we can open about 10 to 15 connections uh per second for initialization. So only initialization of this connection pool already took a minute.

**25:05** · With that with those numbers we can now calculate the maximum pool size that we're having. It's again the core count of 104\* 2 plus a spindle count of eight is 216 connections maximally whereas we're having here 640 connections.

**25:26** · Let's challenge this with our real workloads that we're having just to calculate what is a uh a decent amount of connections that we're uh configuring for this kind of applications.

**25:42** · This banking system during a normal day um has an average transaction time or a mean transaction time of 100 milliseconds.

**25:52** · The mean load is uh 50 transactions per second and the mean required connections we can now calculate with a load of 50 and a transaction time of 100 is five connections open and divided on those eight JVMs um it's eight containers with eight JVMs it's 625 connections per JVM that we really need on a normal day. That's not much.

**26:23** · So, even if we have two, that's a lot more than we're actually needing.

**26:29** · Now, banking systems, they're not stable systems. We have high workload days and we have low workload days. So, on a Black Friday, um we have an SLA of a max transaction time of 2 seconds or 2,000 milliseconds. That's the amount of time that when you pay with your card, um the card comes back out because the transaction wasn't successful. So that's the time out set with a peak load of uh 100 transactions per second that we're having. Now we can calculate our max connection on peak load.

**27:06** · Um it's 100 transactions per second with a transaction time of maximally what we can have um 2,000 milliseconds.

**27:15** · makes two f 200 connections that we would need to open against the database.

**27:23** · And remember previously we calculated if we go two slides back we can have on this server 216 connections on peak load 25 \* 8 is 200 connections that are divided on those eight JVMs.

**27:40** · So the server is on a proper size, but the connection pool is way too big for the hardware that we're having.

**27:49** · Now we can install one pool and handle all the connections that are coming in over one pool, right? So we can have one pool to rule them all. Well, if you have stable workloads of the same kinds, you might as well do that. But if you have different types of workloads, different types of connection and different types of chops that you're running on your uh applications, different workloads might need different connection pools in the back end. So you can have short and long running chops and you might separate those into different connection pools that you for example have one connection pools for longer running batch jobs and one connection pools for shorter running transactions which is then more efficient because longer running batch jobs aren't blocking open connections for shorter running transactions. So both get their fair share of the database.

**28:52** · Now the key takeaways that I want you to take with you after today, you absolutely need a connection pool and you need to configure it well.

**29:04** · Um, if you have very small pools, they can be very harmful, but large pools can be even more harmful because they overload the database on the back end.

**29:19** · Um, your maximum pool size depends on the amount of cores and spindles that you're having. So also know what hardware you're running on and calculate what your max pool size should be and don't overdo it on on that level.

**29:36** · Um remember the process to core ratio.

**29:39** · So the maximum connections is two times the number of CPU cores plus your spindle count. Whereas the spindle count really isn't a big deal here. Usually you have a number between one and eight.

**29:51** · When you have many cores, this doesn't affect your calculation much.

**29:57** · Remember Little's law that helps us determine the minimum amount of connections that you really need and go don't go under this calculated number.

**30:07** · Um, and use Kingman's law to help determine the maximum number of connections that you're having.

**30:16** · So, we are way ahead of time. So we have time for questions if you have any.

**30:26** · Yes.

**30:43** · report that.

**30:49** · So the question is um if there are in AWR report or in the listener log um hints for troubles with connection pooling. I don't know the AWR report that well so I wouldn't know that. Um usually um how you detect that you're having problems with connection pool is pooling is that you have when you use tracing that you lose a lot of time in the connection pool section of your trace.

**31:21** · That's one way to find out that you're having problems with it. If you don't have tracing, um, then it's just slow query performance, which can be a hint, but doesn't necessarily mean that it's a problem with the connection pool because it could also be a problem with your query.

**31:38** · Um, but AWR report, I don't think it's the way to to look for problems with the connection pool. I would rather have a look at tracing.

**31:55** · I'm not sure if that's connected. No.

**32:00** · Yes.

**32:03** · Yes.

**32:49** · Yeah, you you were talking about the database side connection pools, right?

**32:54** · So, if an application doesn't have their own connection pool, we use database side connection pools. Um no the data the database side connection pool comes in when the application usually doesn't have one. So for example with Ruby applications they usually don't come with connection pools or I have seen many that don't come with connection pool. What happens is um connections are opened against the database um and then left um untouched uh because they are exactly used once and that then forgotten but not closed. So if bad connection handling happens on an application side this is really something that can prevent a symptom of um unlimited open connections against the database that they grow and grow. So for example, PG bouncer is something that you can deploy between the application and your database as um an additional application. It's really an additional application. The database side connection pools, they don't live in the database. they live before the database and the application then connects first to PG bouncer does the authentication with the database and um the connection gets back over this piece of software

**34:39** · No, once you have it, um the connection pool also will have open connections against the database. So what the connection pool then does is knowing that the application comes with queries all the time um having open connections and reusing those.

**34:56** · So there's a reusage of connections but it also prevents uh the database from having too many open connections which happens if you don't terminate them on the application side.

**35:14** · Other questions? Yeah.

**35:20** · Yeah. That's for hard drives. Yeah. But in SSDs it's usually one.

**35:26** · Yeah.

**35:28** · All SSDs have a spin count of one.

**35:33** · Yeah.

**35:40** · It depends. It depends on your CPU.

**35:44** · Not I I I would not rely on them when I calculate the connection pool size. I would always go for the amount of CPU threats that you're having without the virtual threat.

**36:01** · Yes.

**36:52** · Okay. Yeah.

**37:00** · Yeah. You would also see that in tracing that if an application um uses a connections and then doesn't end the the the transaction for example so it's still in use but not um given free um as an idle idle connection so it cannot be reused again um you would see that in tracing because you can then have your query time that you see query executing time and the time reserved for um using the connections that they are very different. You would also see that in a trace that you're running.

**37:44** · Yes.

**37:54** · I always see Kari used by Java um applications. is the most common one. Um I don't see a good alternative currently for using it, but it's a very good one. And if you don't want to um go all through the maths and do your numbering, the defaults of Hikari CP are very good. So if you just use the defaults, that's also a message to just take away.

**38:21** · They're very good.

**38:28** · Okay, I guess we're done. Thank you so much for coming.
