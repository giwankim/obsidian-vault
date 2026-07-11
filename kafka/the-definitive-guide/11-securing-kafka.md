# 11. Securing Kafka

> _Kafka: The Definitive Guide_, 2nd Edition — Shapira, Palino, Sivaram & Petty

> [!tip]- How to use these Cornell notes
> 1. **While reading** — fill only the right **Notes** column.
> 2. **After reading** — refine the left **Cue** column into sharp questions (already seeded below).
> 3. **To study** — cover the Notes column; answer each cue **from memory**; uncover to check.
> 4. **Last** — write each section's **Summary** in your own words, without looking up.

## Locking Down Kafka

| Cue / Question | Notes |
| --- | --- |
| Which layers combine to secure a cluster (authentication, authorization, encryption, quotas, auditability), and what does each protect against? | |
| Walk the path of one message — where can it be attacked (client connection, broker disk, inter-broker replication, ZooKeeper metadata)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Security Protocols

| Cue / Question | Notes |
| --- | --- |
| What are the four security protocols (PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL), as combinations of transport encryption × authentication? | |
| How do listeners let one broker serve different protocols (multiple listeners, `inter.broker.listener.name` for replication traffic)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Authentication

| Cue / Question | Notes |
| --- | --- |
| How does mTLS authenticate clients (keystores/truststores, `ssl.client.auth=required`, principal from the certificate DN), and what are its costs (cert lifecycle, no zero-copy)? | |
| When do you choose each SASL mechanism — GSSAPI/Kerberos (existing AD/KDC), PLAIN (simple, must ride TLS, custom callback for password store), SCRAM (salted credentials stored in ZK), OAUTHBEARER (OIDC tokens; the default unsecured JWT is dev-only)? | |
| What problem do delegation tokens solve (lightweight, short-lived credentials so frameworks/workers don't need the real Kerberos/SSL secrets)? | |
| Why might you force reauthentication (`connections.max.reauth.ms` — bound the lifetime of a connection using expired/revoked credentials)? | |
| How do you roll out security changes without downtime (add a new listener with the new protocol, migrate clients, rolling restarts, then remove the old listener)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Encryption

| Cue / Question | Notes |
| --- | --- |
| What does TLS protect and what does it not (in transit only — brokers still see and store plaintext)? | |
| How does end-to-end message encryption work (encrypting serializer/decrypting deserializer with keys from a KMS), and what do you lose (broker-side compaction/compression usefulness, key-rotation complexity)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Authorization

| Cue / Question | Notes |
| --- | --- |
| How does AclAuthorizer model permissions (principal + host, operation, resource type, allow/deny), and how do literal / prefixed / wildcard resource patterns match? | |
| What are the precedence rules (deny beats allow; `super.users` bypass everything; `allow.everyone.if.no.acl.found` as a dangerous default)? | |
| Which subtle grants matter in practice (least privilege; topic-creation via cluster vs prefixed ACLs; consumer needs group *and* topic access; metadata leakage)? | |
| When would you plug in a custom authorizer (central policy service, group/role-based rules, extra audit hooks)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Auditing

| Cue / Question | Notes |
| --- | --- |
| How do you capture who did what (log4j authorizer and request loggers at the right levels, shipped to analysis — e.g., into Kafka itself)? | |
| What patterns should audit analysis look for (spikes in denials, unusual principals/hosts, access to sensitive topics)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Securing ZooKeeper

| Cue / Question | Notes |
| --- | --- |
| Why must ZooKeeper be secured too (it stores ACLs, SCRAM credentials, and cluster metadata), and how (SASL/Kerberos auth, `zookeeper.set.acl=true`, TLS in ZK 3.5+)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

## Securing the Platform

| Cue / Question | Notes |
| --- | --- |
| Where do secrets leak outside Kafka itself (keystore/truststore files, plaintext passwords in config files), and what mitigates it (file permissions, externalized/encrypted configs via config providers)? | |

**Summary:**
<!-- 1-2 sentences, your words -->

---

## Chapter Summary (cover everything above, write from memory)

<!-- 3-4 sentences synthesizing the whole chapter in your own words. -->

## Optional: sketch the model

```mermaid
%% Draw: client --> listener (protocol: SASL_SSL) --> authN (principal) --> authZ (ACL check) --> log/audit ; side boxes: inter-broker listener, ZooKeeper with its own auth+ACLs
flowchart LR
```
