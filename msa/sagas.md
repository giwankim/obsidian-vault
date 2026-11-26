---
title: "Sagas"
source: "https://vasters.com/archive/Sagas.html"
author:
  - "[[Clemens Vasters]]"
published: 2012-08-31
created: 2026-06-27
description:
tags:
  - "clippings"
---

> [!summary]
> Clemens Vasters' 2012 post arguing that a Saga is a failure-management pattern, not a workflow or state-machine engine. It splits a long-lived distributed transaction into local steps each paired with a compensating (undo) action, coordinated by a serializable "routing slip" passed between independent activity hosts with no central coordinator — moving forward on success and unwinding backward through compensations on failure. Illustrated with a C# travel-booking (car/hotel/flight) example.

Today has been a lively day in some parts of the Twitterverse debating the Saga pattern. As it stands, there are a few frameworks for.NET out there that use the term "Saga" for some framework implementation of a state machine or workflow. Trouble is, that's not what a Saga is. A Saga is a failure management pattern.

Sagas come out of the realization that particularly long-lived transactions (originally even just inside databases), but also far distributed transactions across location and/or trust boundaries can't eaily be handled using the classic ACID model with 2-Phase commit and holding locks for the duration of the work. Instead, a Saga splits work into individual transactions whose effects can be, somehow, reversed after work has been performed and commited.

[![image](http://vasters.com/binary/Windows-Live-Writer/Sagas_1273E/image_thumb_1.png "image")](http://vasters.com/binary/Windows-Live-Writer/Sagas_1273E/image_4.png)

The picture shows a simple Saga. If you book a travel itinerary, you want a car and a hotel and a flight. If you can't get all of them, it's probably not worth going. It's also very certain that you can't enlist all of these providers into a distributed ACID transaction. Instead, you'll have an activity for booking rental cars that knows both how to perform a reservation and also how to cancel it - and one for a hotel and one for flights.

The activities are grouped in a composite job (routing slip) that's handed along the activity chain. If you want, you can sign/encrypt the routing slip items so that they can only be understood and manipulated by the intended receiver. When an activity completes, it adds a record of the completion to the routing slip along with information on where its compensating operation can be reached (e.g. via a Queue). When an activity fails, it cleans up locally and then sends the routing slip backwards to the last completed activity's compensation address to unwind the transaction outcome.

If you're a bit familiar with travel, you'll also notice that I've organized the steps by risk. Reserving a rental car almost always succeeds if you book in advance, because the rental car company can move more cars on-site of there is high demand. Reserving a hotel is slightly more risky, but you can commonly back out of a reservation without penalty until 24h before the stay. Airfare often comes with a refund restriction, so you'll want to do that last.

I created a [Gist on Github that you can run as a console application](https://gist.github.com/3562597). It illustrates this model in code. Mind that it is a mockup and not a framework. I wrote this in less than 90 minutes, so don't expect to reuse this.

The main program sets up an examplary routing slip (all the classes are in the one file) and creates three completely independent "processes" (activity hosts) that are each responsible for handling a particular kind of work. The "processes" are linked by a "network" and each kind of activity has an address for forward progress work and one of compensation work. The network resolution is simulated by 'Send".

```js
1:  static ActivityHost[] processes;
```
```js
2:
```
```js
3:  static void Main(string[] args)
```
```js
4:  \{
```
```js
5:      var routingSlip = new RoutingSlip(new WorkItem[]
```
```js
6:          \{
```
```js
7:              new WorkItem<ReserveCarActivity>(new WorkItemArguments\{\{"vehicleType", "Compact"\}\}),
```
```js
8:              new WorkItem<ReserveHotelActivity>(new WorkItemArguments\{\{"roomType", "Suite"\}\}),
```
```js
9:              new WorkItem<ReserveFlightActivity>(new WorkItemArguments\{\{"destination", "DUS"\}\})
```
```js
10:          \});
```
```js
11:
```
```js
12:
```
```js
13:      // imagine these being completely separate processes with queues between them
```
```js
14:      processes = new ActivityHost[]
```
```js
15:                          \{
```
```js
16:                              new ActivityHost<ReserveCarActivity>(Send),
```
```js
17:                              new ActivityHost<ReserveHotelActivity>(Send),
```
```js
18:                              new ActivityHost<ReserveFlightActivity>(Send)
```
```js
19:                          \};
```
```js
20:
```
```js
21:      // hand off to the first address
```
```js
22:      Send(routingSlip.ProgressUri, routingSlip);
```
```js
23:  \}
```
```js
24:
```
```js
25:  static void Send(Uri uri, RoutingSlip routingSlip)
```
```js
26:  \{
```
```js
27:      // this is effectively the network dispatch
```
```js
28:      foreach (var process in processes)
```
```js
29:      \{
```
```js
30:          if (process.AcceptMessage(uri, routingSlip))
```
```js
31:          \{
```
```js
32:              break;
```
```js
33:          \}
```
```js
34:      \}
```
```js
35:  \}
```

The activities each implement a reservation step and an undo step. Here's the one for cars:

```js
1:  class ReserveCarActivity : Activity
```
```js
2:  {
```
```js
3:      static Random rnd = new Random(2);
```
```js
4:
```
```js
5:      public override WorkLog DoWork(WorkItem workItem)
```
```js
6:      {
```
```js
7:          Console.WriteLine("Reserving car");
```
```js
8:          var car = workItem.Arguments["vehicleType"];
```
```js
9:          var reservationId = rnd.Next(100000);
```
```js
10:          Console.WriteLine("Reserved car {0}", reservationId);
```
```js
11:          return new WorkLog(this, new WorkResult { { "reservationId", reservationId } });
```
```js
12:      }
```
```js
13:
```
```js
14:      public override bool Compensate(WorkLog item, RoutingSlip routingSlip)
```
```js
15:      {
```
```js
16:          var reservationId = item.Result["reservationId"];
```
```js
17:          Console.WriteLine("Cancelled car {0}", reservationId);
```
```js
18:          return true;
```
```js
19:      }
```
```js
20:
```
```js
21:      public override Uri WorkItemQueueAddress
```
```js
22:      {
```
```js
23:          get { return new Uri("sb://./carReservations"); }
```
```js
24:      }
```
```js
25:
```
```js
26:      public override Uri CompensationQueueAddress
```
```js
27:      {
```
```js
28:          get { return new Uri("sb://./carCancellactions"); }
```
```js
29:      }
```
```js
30:  }
```

The chaining happens solely through the routing slip. The routing slip is "serializable" (it's not, pretend that it is) and it's the only piece of information that flows between the collaborating activities. There is no central coordination. All work is local on the nodes and once a node is done, it either hands the routing slip forward (on success) or backward (on failure). For forward progress data, the routing slip has a queue and for backwards items it maintains a stack. The routing slip also handles resolving and invoking whatever the "next" thing to call is on the way forward and backward.

```js
1:  class RoutingSlip
```
```js
2:  {
```
```js
3:      readonly Stack<WorkLog> completedWorkLogs = new Stack<WorkLog>();
```
```js
4:      readonly Queue<WorkItem> nextWorkItem = new Queue<WorkItem>();
```
```js
5:
```
```js
6:      public RoutingSlip()
```
```js
7:      {
```
```js
8:      }
```
```js
9:
```
```js
10:      public RoutingSlip(IEnumerable<WorkItem> workItems)
```
```js
11:      {
```
```js
12:          foreach (var workItem in workItems)
```
```js
13:          {
```
```js
14:              this.nextWorkItem.Enqueue(workItem);
```
```js
15:          }
```
```js
16:      }
```
```js
17:
```
```js
18:      public bool IsCompleted
```
```js
19:      {
```
```js
20:          get { return this.nextWorkItem.Count == 0; }
```
```js
21:      }
```
```js
22:
```
```js
23:      public bool IsInProgress
```
```js
24:      {
```
```js
25:          get { return this.completedWorkLogs.Count > 0; }
```
```js
26:      }
```
```js
27:
```
```js
28:      public bool ProcessNext()
```
```js
29:      {
```
```js
30:          if (this.IsCompleted)
```
```js
31:          {
```
```js
32:              throw new InvalidOperationException();
```
```js
33:          }
```
```js
34:
```
```js
35:          var currentItem = this.nextWorkItem.Dequeue();
```
```js
36:          var activity = (Activity)Activator.CreateInstance(currentItem.ActivityType);
```
```js
37:          try
```
```js
38:          {
```
```js
39:              var result = activity.DoWork(currentItem);
```
```js
40:              if (result != null)
```
```js
41:              {
```
```js
42:                  this.completedWorkLogs.Push(result);
```
```js
43:                  return true;
```
```js
44:              }
```
```js
45:          }
```
```js
46:          catch (Exception e)
```
```js
47:          {
```
```js
48:              Console.WriteLine("Exception {0}", e.Message);
```
```js
49:          }
```
```js
50:          return false;
```
```js
51:      }
```
```js
52:
```
```js
53:      public Uri ProgressUri
```
```js
54:      {
```
```js
55:          get
```
```js
56:          {
```
```js
57:              if (IsCompleted)
```
```js
58:              {
```
```js
59:                  return null;
```
```js
60:              }
```
```js
61:              else
```
```js
62:              {
```
```js
63:                  return
```
```js
64:                      ((Activity)Activator.CreateInstance(this.nextWorkItem.Peek().ActivityType)).
```
```js
65:                          WorkItemQueueAddress;
```
```js
66:              }
```
```js
67:          }
```
```js
68:      }
```
```js
69:
```
```js
70:      public Uri CompensationUri
```
```js
71:      {
```
```js
72:          get
```
```js
73:          {
```
```js
74:              if (!IsInProgress)
```
```js
75:              {
```
```js
76:                  return null;
```
```js
77:              }
```
```js
78:              else
```
```js
79:              {
```
```js
80:                  return
```
```js
81:                      ((Activity)Activator.CreateInstance(this.completedWorkLogs.Peek().ActivityType)).
```
```js
82:                          CompensationQueueAddress;
```
```js
83:              }
```
```js
84:          }
```
```js
85:      }
```
```js
86:
```
```js
87:      public bool UndoLast()
```
```js
88:      {
```
```js
89:          if (!this.IsInProgress)
```
```js
90:          {
```
```js
91:              throw new InvalidOperationException();
```
```js
92:          }
```
```js
93:
```
```js
94:          var currentItem = this.completedWorkLogs.Pop();
```
```js
95:          var activity = (Activity)Activator.CreateInstance(currentItem.ActivityType);
```
```js
96:          try
```
```js
97:          {
```
```js
98:              return activity.Compensate(currentItem, this);
```
```js
99:          }
```
```js
100:          catch (Exception e)
```
```js
101:          {
```
```js
102:              Console.WriteLine("Exception {0}", e.Message);
```
```js
103:              throw;
```
```js
104:          }
```
```js
105:
```
```js
106:      }
```
```js
107:  }
```

The local work and making the decisions is encapsulated in the ActivityHost, which calls ProcessNext() on the routing slip to resolve the next activity and call its DoWork() function on the way forward or will resolve the last executed activity on the way back and invoke its Compensate() function. Again, there's nothing centralized here; all that work hinges on the routing slip and the three activities and their execution is completely disjoint.

```js
1:  abstract class ActivityHost
```
```js
2:  {
```
```js
3:      Action<Uri, RoutingSlip> send;
```
```js
4:
```
```js
5:      public ActivityHost(Action<Uri, RoutingSlip> send)
```
```js
6:      {
```
```js
7:          this.send = send;
```
```js
8:      }
```
```js
9:
```
```js
10:      public void ProcessForwardMessage(RoutingSlip routingSlip)
```
```js
11:      {
```
```js
12:          if (!routingSlip.IsCompleted)
```
```js
13:          {
```
```js
14:              // if the current step is successful, proceed
```
```js
15:              // otherwise go to the Unwind path
```
```js
16:              if (routingSlip.ProcessNext())
```
```js
17:              {
```
```js
18:                  // recursion stands for passing context via message
```
```js
19:                  // the routing slip can be fully serialized and passed
```
```js
20:                  // between systems.
```
```js
21:                  this.send(routingSlip.ProgressUri, routingSlip);
```
```js
22:              }
```
```js
23:              else
```
```js
24:              {
```
```js
25:                  // pass message to unwind message route
```
```js
26:                  this.send(routingSlip.CompensationUri, routingSlip);
```
```js
27:              }
```
```js
28:          }
```
```js
29:      }
```
```js
30:
```
```js
31:      public void ProcessBackwardMessage(RoutingSlip routingSlip)
```
```js
32:      {
```
```js
33:          if (routingSlip.IsInProgress)
```
```js
34:          {
```
```js
35:              // UndoLast can put new work on the routing slip
```
```js
36:              // and return false to go back on the forward
```
```js
37:              // path
```
```js
38:              if (routingSlip.UndoLast())
```
```js
39:              {
```
```js
40:                  // recursion stands for passing context via message
```
```js
41:                  // the routing slip can be fully serialized and passed
```
```js
42:                  // between systems
```
```js
43:                  this.send(routingSlip.CompensationUri, routingSlip);
```
```js
44:              }
```
```js
45:              else
```
```js
46:              {
```
```js
47:                  this.send(routingSlip.ProgressUri, routingSlip);
```
```js
48:              }
```
```js
49:          }
```
```js
50:      }
```
```js
51:
```
```js
52:      public abstract bool AcceptMessage(Uri uri, RoutingSlip routingSlip);
```
```js
53:  }
```

That's a Saga.
