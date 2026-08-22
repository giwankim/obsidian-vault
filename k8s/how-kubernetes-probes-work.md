---
title: "How Kubernetes probes work"
source: "https://ngrok.com/blog/probes"
author:
  - "[[Sam Rose]]"
published: 2026-08-19
created: 2026-08-21
description: "Learn how probes work interactively on simulated Kubernetes clusters running in your browser."
tags:
  - "clippings"
---

> [!summary]
> An interactive walkthrough of Kubernetes' three probe types, using simulated clusters that run in the browser so you can watch pods fail, restart, and drop traffic in real time.
> It covers what startup, readiness, and liveness probes are each for, how to combine them, how common misconfigurations produce restart loops and dropped requests, and how probes affect Deployment rollout speed.
> The closing guidance: keep readiness cheap and conservative, avoid failing readiness or liveness on shared dependencies or high CPU/memory, and fail liveness only when a restart is very likely to help.

I’m going to show you, *really show you*, how probes work in Kubernetes. How they can make your application more resilient, and how they can help you prevent avoidable mistakes. Like restart loops that take hours to recover from, and dropping requests during rollouts.

Every interactive demo in this post uses [webernetes](https://github.com/ngrok/webernetes), my partial port of Kubernetes to TypeScript. It contains more than 100,000 lines of ported Kubernetes Go code to run a simulated cluster *right here in your browser*. I verified the behaviour of these demos against k3s and managed to find a bug in Kubernetes! More on that later.

### What you will learn

1. The 3 types of probe and what they’re for.
2. How to configure and combine them.
3. How common misconfigurations fail.
4. How probes affect Deployment speed.

## A pod without probes

I want to run a pod with a single container. Here’s its manifest, `pod-a.yaml`:

### pod-a.yaml

```yaml
apiVersion: "v1"
kind: "Pod"
⋯
  name: "pod-a"
⋯
⋯
⋯
      image: "my-app:latest"
```

This image, `my-app:latest`, spends a few seconds initialising before listening on port 8080. You will see this below when you click restart to send the container a signal, causing it to crash and get started back up by Kubernetes. You can pause or reset any demo at any time.

node-1

- 0/2Restart container

After the first crash, the container restarts straight away. After the second, Kubernetes imposes a CrashLoopBackOff on it before starting it again. By default this delay is 10 seconds, doubling with each crash up to a maximum wait of 5 minutes. I shortened it to 3 seconds for this demo.

In both cases, Kubernetes considers the container Ready as soon as it starts, even though we know it’s not. It’s still doing startup work and not listening on port 8080.

Next I’ll add pod-b, which sends a request to pod-a every 2 seconds. Throughout the post, you can think of pod-b as any source of client traffic: an ingress controller, a load balancer, inter-service requests, etc.

If you restart pod-a in the demo below while a request is on its way, that request will fail.

node-1

- Cause a request to fail

From the moment you restart the container until its startup work finishes, requests will fail, even though the container is considered Ready! This is not what I want. I need Kubernetes to know when pod-a is ready to receive traffic.

For this, Kubernetes gives us **probes**. Probes are periodic checks sent to containers to determine their health. They come in three flavours:

- Startup probes determine whether my application inside the container has started.
- Readiness probes determine whether my application is ready to receive traffic.
- Liveness probes determine whether my application needs to be restarted.

It sounds like startup probes are best suited to the problem I showed you in the demos above, so let’s start there.

## Startup probes

Below, I’ve added a startup probe to `pod-a.yaml`:

### pod-a.yaml

```yaml
apiVersion: "v1"
kind: "Pod"
⋯
  name: "pod-a"
⋯
⋯
⋯
      image: "my-app:latest"
⋯
⋯
          path: "/startup"
          port: 8080
        periodSeconds: 1
        failureThreshold: 5
```

It’s an `httpGet` probe that sends a `GET /startup` request to the pod on port 8080. Status codes 200-399 count as a success. This happens every `periodSeconds` seconds, and is allowed to fail `failureThreshold` consecutive times before Kubernetes kills the container. This gives my container ~5 seconds to complete its startup work.

Kubernetes also supports `tcpSocket`, `exec`, and `grpc` probes. These establish a TCP connection, run a command inside the container, or call the gRPC health-checking protocol to establish container health. You can [read about them in the Kubernetes documentation](https://kubernetes.io/docs/concepts/workloads/pods/probes/). I’ll be using `httpGet` throughout this post.

Probes are sent by a process called the kubelet. Each node in the cluster has its own kubelet, and it’s the kubelet’s job to make sure the right pods are running and being probed for each node.

When you restart pod-a below, it now shows as NotReady. Kubernetes is now *aware* that pod-a hasn’t initialised yet. It only becomes Ready after the first startup probe succeeds.

node-1

- 0/2Restart container

NotReady is the default for pods with containers that have a startup probe. However, even when not ready, pod-b still sends requests to pod-a and those requests still fail during the container’s startup period. This is because I’ve configured pod-b to send requests directly to pod-a’s IP address, which bypasses the readiness mechanism.

### I'm lying a bit about NotReady

*Technically* Kubernetes doesn’t have a `NotReady` condition, it has a `Ready` condition that can be `True`, `False`, or `Unknown`. I’m referring to it as `NotReady` because it was shorter than having `Ready=True` or `Ready=False` in the demos.

To fix these failed requests I need to graduate to a more production-grade setup: multiple copies of pod-a with requests load-balanced between them. I’m going to create a ReplicaSet configured to run 2 replicas of pod-a and a Service to load balance between them.

### replica-set-a.yaml

```yaml
apiVersion: "apps/v1"
kind: "ReplicaSet"
⋯
  name: "replica-set-a"
⋯
  # Run 2 copies of the pod defined under \`template\`.
  replicas: 2
⋯
⋯
      # Consider pods with this label to be part of this replica set.
      app: "pod-a"
⋯
⋯
⋯
        app: "pod-a"
⋯
      # The same pod spec from before.
⋯
⋯
          image: "my-app:latest"
⋯
⋯
              path: "/startup"
              port: 8080
            periodSeconds: 1
            failureThreshold: 5
```

### service-a.yaml

```yaml
apiVersion: "v1"
kind: "Service"
⋯
  name: "service-a"
⋯
⋯
    # Load-balance between pods that have this label.
    app: "pod-a"
⋯
    # Send requests to this port on the pods.
⋯
      targetPort: 8080
```

pod-b will from now on send requests to the DNS name Kubernetes creates for the Service, in this case `service-a.default.svc.cluster.local`, instead of directly to an individual pod. Kubernetes uses a pod’s `Ready` condition to include or exclude it from Service load balancing.

Below you can click the restart button to crash only the top container. Notice that when the top container is starting up, requests are always sent to the bottom container. When a container is NotReady, it marks the whole pod not ready and it won’t get traffic from any Services it is part of.

node-1

- 0/2Restart top container

service-a

Despite this, requests *can* still fail if they’re in-flight when you restart the top container. This happens because the restart button crashes the container abruptly. It doesn’t get a chance to finish in-flight requests.

The better thing to do here is *delete* the pod and rely on the ReplicaSet to bring up a new one. This is better for 2 reasons:

1. Kubernetes gives pods a 30-second termination grace period by default, which I’ve configured to 2 seconds in this post so you don’t have to wait. When deleted, pods are considered terminating and Kubernetes removes them from any Services they’re part of. They won’t receive any new requests.
2. ReplicaSets don’t count terminating pods as active replicas, so they create replacements as soon as the deleted pod is terminating.

Together, graceful termination and the startup probe keep requests away from containers that are starting or stopping. In this next demo, clicking delete won’t cause any requests from pod-b to fail.

node-1

- 0/2Wait for containers to be ready

service-a

There’s always a pod ready to service a new request, making it safe to delete pods without interrupting user traffic.

### How does this grace period actually work?

When you delete a pod, the kubelet first sends a `SIGTERM` signal to the container, then `terminationGracePeriodSeconds` later it sends a `SIGKILL` if the container is still running. The Kubernetes docs on [pod lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/) contain all of the gory details.

In this post, my containers are configured to exit 1 second after receiving the `SIGTERM`. I chose this because I know it’s long enough for them to finish any in-flight requests. When configuring this on your own pods, make sure you leave enough time for your longest-running requests to finish.

### How to misconfigure a startup probe

Earlier I mentioned that I’m giving my pod ~5 seconds to complete its startup work by setting `failureThreshold` to 5 with a `periodSeconds` of 1. Choose these values on your own containers carefully. Too little time can cause a container to crash-loop.

Setting the `failureThreshold` below will restart the container with the new value. Set it to 1 or 2 and see what happens.

node-1

- Make **pod-a** crash loop

failureThreshold

5

After a few restarts, pod-a is put in CrashLoopBackOff. The startup probe never gives the container enough time to start, so this demo crash-loops until you set `failureThreshold` back to 3 or above. When configuring this for your own containers, choose values that allow for your worst-case startup time.

## Readiness probes

After any startup probe succeeds, readiness probes monitor the container for the rest of its life. Failing a readiness probe marks the container NotReady and removes it from receiving requests for any Service it is part of.

I’ve modified `pod-a.yaml` to have just a readiness probe for now:

### pod-a.yaml

```yaml
apiVersion: "v1"
kind: "Pod"
⋯
  name: "pod-a"
⋯
⋯
⋯
      image: "my-app:latest"
⋯
⋯
          path: "/ready"
          port: 8080
        periodSeconds: 3
        failureThreshold: 1
        successThreshold: 1
```

I’m sending it to the `/ready` endpoint every 3 seconds. After a single failure, the container gets the NotReady condition. Switch `/ready` in the demo below from 200 to 503 and watch the container become not ready.

node-1

- Wait for **pod-a** to become ready

/ready

200

503

### Out-of-band probing

Reset the demo above and watch the first few seconds again. Readiness probes are sent *way* more often than every 3 seconds. What gives? The [Kubernetes docs](https://kubernetes.io/docs/concepts/workloads/pods/probes/#configure-probes) say this:

> While a container is not Ready, the readiness probe may be executed at times other than the configured `periodSeconds` interval. This is to make the Pod ready faster.

Wonderfully vague. In the work I did on [webernetes](https://github.com/ngrok/webernetes) I found that there are many things that can trigger these out-of-band probes. Without going too into the weeds, *most* updates to the pod while the container is NotReady can trigger an out-of-band probe. Things like updating annotations or status, for example. Many things can be updating pods that you may not be aware of.

Fun to know, but ultimately not something you should rely on in practice.

The demo above sets `failureThreshold` and `successThreshold` to 1, but I don’t want a single transient failure to remove my pods from their Services. Below I’ve set the thresholds to 2. Set `/ready` to 503 again and notice it now takes 2 failures before the container becomes NotReady.

node-1

- Wait for **pod-a** to become ready

/ready

200

503

You may notice here that when flipping from ready to not ready, an out-of-band probe can be fired. This is for the same reasons as before. The pod is NotReady and its status just got updated.

By default `successThreshold` is 1 and `failureThreshold` is 3. Generally good defaults that I don’t recommend changing unless you have a great reason.

### Why do we need startup probes if we have readiness probes?

The demos above only use a readiness probe. Probing starts straight away and doesn’t succeed until my container has finished its startup work. This is exactly the job my startup probe was doing, so why do we need both probe types?

A few good reasons:

1. Startup probes delay readiness and liveness starting until initialisation is complete.
2. They allow startup to have a separate `periodSeconds` and `failureThreshold`, so slow initialisation can be probed more frequently than steady-state readiness and liveness.
3. Repeated startup failures kill the container and apply its restart policy. Readiness failures don’t. A restart *could* help a stuck container become ready.

You can use multiple probes at the same time. For example, I might send a startup probe every second to detect initialisation quickly, then slow down to every 5 seconds for my readiness probe to reduce steady-state probe load on the container and kubelet.

### pod-a.yaml

```yaml
apiVersion: "v1"
kind: "Pod"
⋯
  name: "pod-a"
⋯
⋯
⋯
      image: "my-app:latest"
⋯
⋯
          path: "/startup"
          port: 8080
        periodSeconds: 1
        failureThreshold: 5
⋯
⋯
          path: "/ready"
          port: 8080
        periodSeconds: 5
```

Readiness probes don’t start until the startup probe succeeds. I’ve started the demo below paused so you can see it from the start. Hit the play button when you’re ready, and press reset if you want to start again from the beginning.

node-1

/startup

200

503

/ready

200

503

This guarantee, that readiness probes don’t start until startup succeeds, allows me to check startup-specific things in the `/startup` endpoint. I could make sure initial configs have been loaded, caches have been pre-warmed and so on. In practice, startup probes are less commonly used than readiness probes. It’s nice to know they’re there as an option if I need them, though.

If you do find yourself wishing readiness probes could restart containers, though, I have just the thing for you.

## Liveness probes

The final probe type is the liveness probe. This probe works just like the readiness probe, but instead of marking a container NotReady when it reaches its `failureThreshold`, the liveness probe kills the container. Kubernetes then applies the Pod’s `restartPolicy`, which defaults to `"Always"` and means a killed container will be restarted.

### pod-a.yaml

```yaml
apiVersion: "v1"
kind: "Pod"
⋯
  name: "pod-a"
⋯
⋯
⋯
      image: "my-app:latest"
⋯
⋯
          path: "/startup"
          port: 8080
        periodSeconds: 1
        failureThreshold: 5
⋯
⋯
          path: "/live"
          port: 8080
        periodSeconds: 2
        failureThreshold: 1
```

This helps when the container can’t recover on its own, such as when its main thread has deadlocked or a critical background thread has died. If I can reliably detect these conditions, I can fail the liveness probe and rely on Kubernetes to restart the container.

The demo below shows pod-a getting sent startup probes until it finishes its startup, after which the liveness probes begin. Set the `/live` endpoint to return 503 to see the container get restarted.

node-1

- Cause a liveness restart

/startup

200

503

/live

200

503

### There's something wrong with the demo above...

You might notice that when you set the /live endpoint to 503, an odd sequence of events happens.

1. The liveness probe fails.
2. The kubelet restarts pod-a’s container.
3. Before the startup probe has a chance to fire, a liveness probe fires and fails because the container is still in startup.
4. The kubelet *restarts the container again*, before it has a chance to pass its startup probe!

This is a real Kubernetes bug that I found during the making of this post. Liveness probes shouldn’t be firing before the startup probe has succeeded. I reproduced this in `k3s`, `minikube`, and `kind` against the latest Kubernetes at time of writing `v1.36.2`. The bug appears to have been introduced in `v1.35.0`. I’ve [filed an issue about it](https://github.com/kubernetes/kubernetes/issues/141155) and SIG Node have accepted it and marked it `priority/important-soon`.

Until it’s fixed, please imagine the premature liveness probe never fires. Thank you.

### How to misconfigure a liveness probe

It would be a bad idea for my liveness probe to check if my database is healthy. A blip in the database could cause all of my containers to crash-loop if it lasts long enough.

When you take the database down in the demo below, the pod-a liveness probes will fail. After a few failures, each container will go into CrashLoopBackOff. To stress how bad this can be, I’ve made the backoff delay scale like it does in real Kubernetes: 10 seconds at first, doubling for each crash. Go and cause some havoc!

node-1

- Take the database down

database

service-a

database

Up

Down

This problem gets worse if clients retry. It hasn’t come up in any other demos so far, but my pod-a containers can only handle 3 requests per second. If they get more than that, they get overloaded and crash! I’ve configured pod-b in the demo below to retry failed requests in a loop, and set the maximum CrashLoopBackOff delay to 5 seconds again. Cause another outage, and see if you can recover from it.

node-1

- Take the database down

database

service-a

database

Up

Down

The retries create what’s called a **thundering herd**, which causes a **cascading failure**. It doesn’t matter that the database is up, any container that dares to recover gets a laser beam of traffic that kills it again.

Probes, sadly, can’t help me get out of this. I would need to create some way to only let a small percentage of traffic through, allowing the containers time to recover, then ramp back up to full traffic over time. Or if I have control over the clients, for example they’re a mobile app I’ve also created, I could add a backoff delay to the retries. This would slow the traffic growth, making it easier to recover.

The best thing I can do, though, is **avoid this mistake in the first place**. Fail a liveness probe only when the failure is local to one container and a restart is likely to restore it. Don’t fail on conditions that will be true for all of your containers at the same time.

## Probes and Deployments

The last thing I want to touch on is how probes affect Deployments. In Kubernetes, most of a Pod’s `spec` is immutable. The way to update an immutable field is to create a new Pod and delete the old one. Deployments manage this replacement as a “rollout.”

Let’s take `deployment-a.yaml` here as an example:

### deployment-a.yaml

```yaml
apiVersion: "apps/v1"
kind: "Deployment"
⋯
  name: "deployment-a"
⋯
  replicas: 3
⋯
    type: "RollingUpdate"
⋯
      maxUnavailable: "25%"
      maxSurge: "25%"
⋯
⋯
      app: "pod-a"
⋯
⋯
⋯
        app: "pod-a"
⋯
⋯
⋯
          image: "my-app:latest"
⋯
⋯
              containerPort: 8080
⋯
⋯
              path: "/startup"
              port: "http"
            periodSeconds: 1
            successThreshold: 1
            failureThreshold: 5
```

I’ve highlighted the `strategy` because it’s the part that controls how new Pods get rolled out. Deployments start off by creating a ReplicaSet to bring up the `replicas` I’ve configured. Changing a Deployment’s `template` after it has been created makes a new, second ReplicaSet configured with this new `template`. The Deployment then scales up the new ReplicaSet while scaling down the old one, based on the `strategy` parameters.

Here’s what each `strategy` parameter means:

1. `type: "RollingUpdate"` updates the Pods gradually rather than all at once. If you did want all at once, you would use `type: "Recreate"`. This first scales the old ReplicaSet to 0, then the new one to the configured `replicas`. This causes downtime, so it’s not the default.
2. `maxUnavailable: "25%"` allows `floor(3 * 0.25) = 0` unavailable replicas, so all 3 must remain available during the rollout.
3. `maxSurge: "25%"` allows `ceil(3 * 0.25) = 1` extra pod above `replicas` during the rollout, so in our case 4 replicas are allowed to exist.

It’s a lot, so clicking deploy below may help you better understand. Remember that the rollout has to keep 3 pods Ready at all times, and is allowed to go up to 4 replicas thanks to `maxSurge`. Pods that are terminating don’t count as available, so you will see more than 4 replicas at times.

node-1

- 0/3Wait for deployment ready

deployment-a

0.0s

The rollout can only create 1 extra pod, and has to wait for that pod to become Ready before it can kill an old pod. This means that probes play a direct role in how fast a rollout can go. You should see that with the above configuration, it takes about 11 seconds to finish. Also notice that no requests from pod-b fail.

Below, I’ve changed `periodSeconds` from 1 to 5. See how long it takes to deploy with this longer period.

node-1

- 0/3Wait for deployment ready

deployment-a

0.0s

It now takes about 19-20 seconds for this rollout to complete. Longer startup probe periods delay rollouts because each replacement pod has to wait until it passes the probe. Keep this in mind when tuning your own probes.

Lastly, what happens if I update a Deployment and have *no probes at all*? In the demo below, you will notice that a rollout will cause a small number of requests to fail because the new containers haven’t finished their startup.

node-1

- 0/3Wait for deployment ready

deployment-a

0.0s

A rollout without probes happens very quickly because each container is considered ready as soon as it starts. This causes a small number of requests to fail because the containers haven’t finished startup yet.

## Tips for designing good probe endpoints

### Startup

1. Use them when startup is slow or variable, or you have initialisation work that can get stuck and needs to be restarted.
2. Probe frequently to detect initialisation quickly. If you do lower `periodSeconds`, make sure to increase `failureThreshold` to maintain the total time you wait for startup. Target your worst-case startup time, plus a little headroom.
3. Take advantage of a separate `/startup` endpoint if there are checks you can do to be certain initialisation has finished. If not, using the same endpoint as your liveness check is reasonable.

### Readiness

1. Keep this probe cheap and conservative. Fail it only when removing a pod from serving is likely to improve overall service health.
2. **Prefer not** to fail readiness based on the status of shared dependencies like database servers and third-party APIs. Include a dependency only when a container truly can’t serve useful traffic without it.
3. **Prefer not** to fail readiness in response to high CPU or memory. If your service is near total capacity, removing a replica may cause a cascading failure.

### Liveness

1. Fail this probe **only** when it’s *very* likely a container is stuck and a restart will help. If you aren’t sure, return success.
2. **Don’t** fail liveness based on the status of shared dependencies like database servers and third-party APIs.
3. **Don’t** fail liveness in response to high CPU or memory.

### General advice

1. Keep probes bounded and cheap. Startup probes have a bit more wiggle room than the other two, but they still consume cluster resources that could be spent serving user traffic.
2. The default `failureThreshold` is 3. Lower it only when immediate intervention is worth the risk of reacting to a transient failure.

## Probe playground

Below is a demo that lets you set whatever probe parameters you want. Changes won’t be applied until you press deploy. It’s surprisingly easy to get yourself into unrecoverable situations, so don’t feel bad about using the reset button.

node-1

deployment-a

0.0s

## Conclusion

Probes are tricky to get right. By *showing* you how they work, and letting you cause some chaos, you’re now better equipped to make informed decisions about your own probes. If you have feedback about this post, or you’re curious about [webernetes](https://github.com/ngrok/webernetes), I would love to talk to you! Email me at [s.rose@ngrok.com](mailto:s.rose@ngrok.com).

### The shameless plug

ngrok have a [first-party Kubernetes Operator](https://github.com/ngrok/ngrok-operator)! It supports both the Ingress and Gateway APIs, as well as letting you declaratively create agent endpoints in your cluster. You can learn more at our [docs](https://ngrok.com/docs/k8s).
