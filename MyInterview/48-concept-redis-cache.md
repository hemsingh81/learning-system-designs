# 48 · Concept: Redis Cache (30 questions)

[← System Design](47-concept-system-design.md) · [Home](README.md) · [Next → Kafka](49-concept-kafka.md)

This file explains **Redis** and **caching** — how I make systems fast and scalable with an in-memory store — in simple English and real depth. I answer from projects A–E, where I used Redis for caching, sessions and rate limiting on TCW's platforms.

> Simple one-liner: *"Redis is a super-fast in-memory data store I use as a cache, session store, rate limiter and more. It cuts latency and database load — the main challenge is invalidation, keeping cached data fresh."*

**Jump to:** [RC1 What is caching](#rc1--what-is-caching) · [RC2 What is Redis](#rc2--what-is-redis) · [RC3 Why so fast](#rc3--why-redis-is-fast) · [RC4 Data types](#rc4--data-types) · [RC5 Cache-aside](#rc5--cache-aside-pattern) · [RC6 Write strategies](#rc6--write-strategies) · [RC7 TTL](#rc7--ttl-and-expiry) · [RC8 Invalidation](#rc8--cache-invalidation) · [RC9 Eviction](#rc9--eviction-policies) · [RC10 Sessions](#rc10--session-store)
> [RC11 Rate limiting](#rc11--rate-limiting) · [RC12 Distributed locks](#rc12--distributed-locks) · [RC13 Pub/Sub](#rc13--pubsub) · [RC14 Persistence](#rc14--persistence-rdb-aof) · [RC15 Is it durable](#rc15--is-redis-a-database) · [RC16 HA](#rc16--high-availability) · [RC17 Cluster](#rc17--clustering-and-sharding) · [RC18 Atomicity](#rc18--atomic-operations) · [RC19 Pipelining](#rc19--pipelining) · [RC20 Big keys](#rc20--big-keys-and-hot-keys)
> [RC21 Stampede](#rc21--cache-stampede) · [RC22 Consistency](#rc22--cache-consistency) · [RC23 What to cache](#rc23--what-to-cache) · [RC24 Key design](#rc24--key-design) · [RC25 Memory](#rc25--memory-management) · [RC26 Monitoring](#rc26--monitoring) · [RC27 Security](#rc27--security) · [RC28 Azure](#rc28--azure-cache-for-redis) · [RC29 Pitfalls](#rc29--common-pitfalls) · [RC30 My approach](#rc30--my-approach) · [Section index](#section-index)

---

## RC1 · What is caching?

**Simple explanation.** **Caching** stores a copy of data somewhere fast (memory) so I don't recompute it or hit a slow source (database, API) every time. It trades a little **freshness** for a lot of **speed** and reduced load — one of the highest-impact performance tools.

**Architect's view:** Caching is about serving hot data cheaply; the whole discipline is deciding *what* to cache and *when to invalidate* it.

**Follow-ups**
- *"One-line?"* — Keep hot data in fast storage to avoid slow/expensive fetches.
- *"Main trade-off?"* — Speed vs freshness — managed by TTL/invalidation.

---

## RC2 · What is Redis?

**Simple explanation.** **Redis** (REmote DIctionary Server) is an **in-memory key-value store**. Because it keeps data in RAM, reads/writes are sub-millisecond. It supports rich data types and is used as a **cache, session store, rate limiter, queue and pub/sub broker**.

**Follow-ups**
- *"Just a cache?"* — No — also sessions, locks, rate limiting, pub/sub, leaderboards.
- *"Key-value only?"* — Values can be strings, hashes, lists, sets, sorted sets, etc.

---

## RC3 · Why Redis is fast

**Simple explanation.** It's fast because data lives **in memory** (no disk seek), it's **single-threaded** for commands (no lock contention), uses efficient data structures, and speaks a lightweight protocol. Result: microsecond operations and huge throughput.

**Follow-ups**
- *"Single-threaded slow?"* — No — avoids locking overhead; it's extremely fast per core and scales via clustering.
- *"In-memory risk?"* — RAM is limited and volatile — manage memory and persistence.

---

## RC4 · Data types

**Simple explanation.** Redis offers **strings** (values/counters), **hashes** (objects), **lists** (queues), **sets** (unique items), **sorted sets** (leaderboards/ranking), plus streams, bitmaps and HyperLogLog. Choosing the right type makes operations simple and atomic.

**Follow-ups**
- *"Sorted set use?"* — Leaderboards, rate windows, priority — ordered by score.
- *"Hash use?"* — Store an object's fields without serialising the whole thing.

---

## RC5 · Cache-aside pattern

**Simple explanation.** **Cache-aside (lazy loading)** is my default: app checks Redis first; on a **miss** it reads the DB, stores the result in Redis with a TTL, then returns it. Only requested data gets cached, and the app controls it.

**Follow-ups**
- *"Miss behaviour?"* — Fetch from DB, populate cache, return — next read is a hit.
- *"Why default?"* — Simple, resilient (cache down → still read DB), caches only what's used.

---

## RC6 · Write strategies

**Simple explanation.** **Write-through** (write cache + DB together — fresh, slower writes), **write-behind** (write cache now, DB later — fast but risk of loss), **write-around** (write DB, skip cache). I mostly use cache-aside + write-through where freshness matters.

**Follow-ups**
- *"Write-behind risk?"* — Data loss if Redis fails before flush — use only when acceptable.
- *"Freshness need?"* — Write-through keeps cache and DB in step.

---

## RC7 · TTL and expiry

**Simple explanation.** **TTL** (time to live) auto-expires a key after N seconds so cached data can't stay stale forever. It's the simplest, most reliable freshness control — I set TTLs based on how often the underlying data changes.

**Follow-ups**
- *"Short vs long TTL?"* — Short = fresher but more DB hits; long = faster but staler — tune per data.
- *"No TTL?"* — Risk of stale data forever — always set one unless truly static.

---

## RC8 · Cache invalidation

**Simple explanation.** **Invalidation** removes/updates cached data when the source changes. Options: **TTL** (time-based), **event-based** (delete key on write), or **versioned keys**. It's famously the hard part — stale cache causes subtle bugs.

**Follow-ups**
- *"Best strategy?"* — TTL as a safety net + event-based delete on updates for freshness.
- *"Why hard?"* — Knowing *exactly* when and what to invalidate across the system.

---

## RC9 · Eviction policies

**Simple explanation.** When memory is full, Redis **evicts** keys by policy: **LRU** (least recently used), **LFU** (least frequently used), **TTL-based**, or **no-eviction** (reject writes). For a cache I use an LRU/LFU policy so hot data stays.

**Follow-ups**
- *"Cache default?"* — `allkeys-lru` (or LFU) — keep frequently used data.
- *"no-eviction?"* — For a data store where losing keys is unacceptable — not a pure cache.

---

## RC10 · Session store

**Simple explanation.** I keep **user sessions** in Redis so my app stays **stateless** ([file 47 SD7](47-concept-system-design.md#sd7--stateless-services)) — any instance can serve any user, and sessions survive restarts and scale horizontally. Fast, shared, with TTL for expiry.

**Follow-ups**
- *"Why not in-app memory?"* — It breaks scaling/failover — shared Redis fixes that.
- *"Session expiry?"* — TTL matches the session timeout.

---

## RC11 · Rate limiting

**Simple explanation.** I implement **rate limiting** with Redis counters (INCR + EXPIRE) or sorted sets — count requests per user per window and reject over the limit ([file 47 SD18](47-concept-system-design.md#sd18--rate-limiting)). Central, fast, and shared across all instances.

**Follow-ups**
- *"Why Redis for this?"* — Shared atomic counters across all app instances — accurate limits.
- *"Algorithm?"* — Fixed/sliding window or token bucket via atomic ops.

---

## RC12 · Distributed locks

**Simple explanation.** Redis provides **distributed locks** (SET NX with TTL, or Redlock) so only one instance runs a critical section (e.g. a scheduled job) at a time. The TTL prevents a crashed holder from locking forever.

**Follow-ups**
- *"Why TTL on a lock?"* — Auto-release if the holder dies — avoids deadlock.
- *"Caution?"* — Distributed locking is tricky — use proven libraries and short critical sections.

---

## RC13 · Pub/Sub

**Simple explanation.** Redis **Pub/Sub** lets services publish messages to channels and subscribers receive them in real time — handy for cache-invalidation broadcasts or live notifications. It's fire-and-forget (no persistence); for durable events I use Kafka ([file 49](49-concept-kafka.md)).

**Follow-ups**
- *"Pub/Sub vs Kafka?"* — Redis is lightweight/ephemeral; Kafka is durable/replayable.
- *"Use case?"* — Broadcast "invalidate key X" to all app nodes.

---

## RC14 · Persistence (RDB, AOF)

**Simple explanation.** Redis can persist to disk: **RDB** (periodic snapshots — compact, some data-loss window) and **AOF** (append every write — more durable, larger). I choose based on how much data loss is acceptable if Redis restarts.

**Follow-ups**
- *"RDB vs AOF?"* — RDB = fast/compact, small loss window; AOF = durable, bigger/slower.
- *"Both?"* — Yes — AOF for durability + RDB for fast restarts.

---

## RC15 · Is Redis a database?

**Simple explanation.** It *can* be a primary store (with persistence), but I mostly treat it as a **cache/accelerator** — the source of truth stays in a durable DB. As a cache, I design so the system still works if Redis is empty or down.

**Follow-ups**
- *"Rely on it as source of truth?"* — Only for suitable data with persistence + HA; usually not for critical finance data.
- *"Cache-down behaviour?"* — Fall back to the DB (cache-aside) — slower but correct.

---

## RC16 · High availability

**Simple explanation.** For HA I run **primary-replica** with **Sentinel** (automatic failover) or clustered/managed Redis. If the primary fails, a replica is promoted — no single point of failure ([file 47 SD19](47-concept-system-design.md#sd19--high-availability)).

**Follow-ups**
- *"Sentinel role?"* — Monitors and promotes a replica on failure automatically.
- *"Managed HA?"* — Azure Cache for Redis handles replication/failover for me.

---

## RC17 · Clustering and sharding

**Simple explanation.** **Redis Cluster** shards data across nodes by hash slots, so I scale beyond one machine's memory and throughput ([file 47 SD12](47-concept-system-design.md#sd12--sharding)). Each node holds part of the keyspace; the client routes to the right shard.

**Follow-ups**
- *"When cluster?"* — Dataset/throughput exceeds a single node.
- *"Multi-key ops?"* — Limited across shards — use hash tags to co-locate related keys.

---

## RC18 · Atomic operations

**Simple explanation.** Redis commands are **atomic** (single-threaded execution), and **MULTI/EXEC** or **Lua scripts** group operations atomically. This makes counters, locks and rate limits correct under concurrency without external locking.

**Follow-ups**
- *"Why atomicity matters?"* — Concurrent INCR/limit checks stay correct — no race conditions.
- *"Complex atomic logic?"* — Lua script runs atomically on the server.

---

## RC19 · Pipelining

**Simple explanation.** **Pipelining** sends many commands in one round trip instead of one-at-a-time, slashing network latency for bulk operations. It's a simple, big win when I issue lots of small commands.

**Follow-ups**
- *"Vs transactions?"* — Pipelining batches for speed; MULTI/EXEC adds atomicity — different goals.
- *"When use?"* — Bulk reads/writes where round-trip time dominates.

---

## RC20 · Big keys and hot keys

**Simple explanation.** **Big keys** (huge values) and **hot keys** (one key hit constantly) hurt performance — they block the single thread or overload one shard. I split big values, spread hot keys, and add local caching for extreme hotspots.

**Follow-ups**
- *"Hot key fix?"* — Local (in-process) cache in front, or replicate/spread the key.
- *"Big key fix?"* — Break into smaller structures; avoid giant lists/hashes.

---

## RC21 · Cache stampede

**Simple explanation.** A **stampede** happens when a popular key expires and many requests hit the DB at once to rebuild it. I prevent it with **locks** (one rebuilder), **early/jittered expiry**, or **stale-while-revalidate** so the DB isn't hammered.

**Follow-ups**
- *"Simplest fix?"* — A short lock so only one request rebuilds; others wait/serve stale.
- *"Jitter?"* — Randomise TTLs so keys don't all expire together.

---

## RC22 · Cache consistency

**Simple explanation.** Cache and DB can drift. I accept **eventual consistency** for most cached data, use **TTL + event-based invalidation** to bound staleness, and I **don't cache** data that must always be exact (like a live balance) unless I invalidate on every change.

**Follow-ups**
- *"Always-fresh data?"* — Don't cache it, or invalidate synchronously on write.
- *"Accept staleness?"* — Yes for most reads — bounded by TTL.

---

## RC23 · What to cache

**Simple explanation.** I cache data that's **read-often, changes-rarely, and expensive to fetch** — reference data, computed results, API responses, sessions. I avoid caching rarely-read or highly-volatile data where invalidation cost outweighs the gain.

**Follow-ups**
- *"Best candidates?"* — Hot, expensive, stable reads.
- *"Poor candidates?"* — Constantly-changing or rarely-accessed data.

---

## RC24 · Key design

**Simple explanation.** I use **consistent, namespaced keys** (e.g. `user:123:profile`), include a **version** when needed, and keep them predictable so I can find, group and invalidate them. Good key design makes invalidation and debugging far easier.

**Follow-ups**
- *"Why namespaces?"* — Group related keys, avoid collisions, target invalidation.
- *"Versioned keys?"* — Bump a version to invalidate a whole set instantly.

---

## RC25 · Memory management

**Simple explanation.** Redis lives in RAM, so I set **maxmemory** + an **eviction policy**, monitor usage, use efficient types, and set TTLs. Running out of memory triggers eviction or write failures — I size and watch it deliberately.

**Follow-ups**
- *"Out of memory?"* — Evicts per policy or rejects writes — configure intentionally.
- *"Reduce memory?"* — TTLs, compact structures, avoid big keys.

---

## RC26 · Monitoring

**Simple explanation.** I monitor **hit ratio**, memory, evictions, latency, connections and slow commands. A low hit ratio means my caching isn't helping; high evictions mean too little memory or bad TTLs. Metrics guide tuning ([file 47 SD21](47-concept-system-design.md#sd21--observability)).

**Follow-ups**
- *"Key metric?"* — Cache hit ratio — the measure of caching value.
- *"High evictions mean?"* — Undersized memory or too-long TTLs.

---

## RC27 · Security

**Simple explanation.** I secure Redis with **auth**, **TLS in transit**, **private networking** (no public exposure), and **ACLs** limiting commands/keys per client. In finance, Redis is never open to the internet and secrets stay in Key Vault ([file 37 Z12](37-concept-azure-services.md#z12--key-vault)).

**Follow-ups**
- *"Biggest risk?"* — An exposed, unauthenticated Redis — lock it in the private network.
- *"ACLs?"* — Restrict which commands/keys a client can use.

---

## RC28 · Azure Cache for Redis

**Simple explanation.** On Azure I use **Azure Cache for Redis** — managed Redis with replication, failover, scaling, TLS and VNet integration ([file 37](37-concept-azure-services.md)). I get Redis's speed without running the servers myself, which fits a regulated, ops-light setup.

**Follow-ups**
- *"Why managed?"* — HA, patching, scaling and security handled for me.
- *"Integration?"* — VNet + private endpoint + managed identity/Key Vault for secrets.

---

## RC29 · Common pitfalls

**Simple explanation.** Pitfalls: no TTL (stale forever), caching volatile data, no invalidation plan, treating Redis as a guaranteed source of truth, ignoring stampedes, big/hot keys, and exposing it publicly. I design against each from the start.

**Follow-ups**
- *"Most common?"* — No/weak invalidation → stale-data bugs.
- *"Reliability mistake?"* — Assuming the cache is always there — always have a DB fallback.

---

## RC30 · My approach

**How I answer (the whole picture).** *"I use Redis to make systems fast and scalable. My default is **cache-aside** with sensible **TTLs** plus **event-based invalidation**, caching hot, expensive, stable reads and never volatile data that must be exact. Beyond caching I use Redis for **stateless sessions**, **rate limiting** (atomic counters), **distributed locks**, and pub/sub for cache-invalidation broadcasts. I design so the system still works if Redis is down — falling back to the database — and I prevent **stampedes** with locks/jittered TTLs, avoid big/hot keys, and set **maxmemory + LRU eviction**. For production I use **Azure Cache for Redis** (managed HA, TLS, VNet), secured privately with secrets in Key Vault, and I monitor **hit ratio, memory and evictions** to keep it effective. That's how Redis kept TCW's platforms fast under load while the database stayed the source of truth."*

**Follow-ups**
- *"One sentence?"* — Cache-aside + TTL + invalidation, Redis for cache/sessions/limits, always with a DB fallback.
- *"Golden rule?"* — Never assume the cache is fresh or always up — bound staleness and design a fallback.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| RC1 | Caching | Hot data in fast storage |
| RC2 | Redis | In-memory key-value multi-tool |
| RC3 | Why fast | RAM + single-thread + good structures |
| RC4 | Data types | Strings/hashes/lists/sets/sorted sets |
| RC5 | Cache-aside | Default: check cache, load on miss |
| RC6 | Write strategies | Through/behind/around |
| RC7 | TTL | Auto-expiry bounds staleness |
| RC8 | Invalidation | The hard part; TTL + events |
| RC9 | Eviction | LRU/LFU keeps hot data |
| RC10 | Sessions | Stateless apps via shared store |
| RC11 | Rate limiting | Atomic counters per window |
| RC12 | Locks | SET NX + TTL for single-runner |
| RC13 | Pub/Sub | Ephemeral broadcasts; Kafka for durable |
| RC14 | Persistence | RDB snapshots vs AOF log |
| RC15 | Is it a DB | Mostly a cache; DB is source of truth |
| RC16 | HA | Primary-replica + Sentinel/managed |
| RC17 | Cluster | Shard by hash slots to scale |
| RC18 | Atomicity | Atomic commands + Lua/MULTI |
| RC19 | Pipelining | Batch commands, cut round trips |
| RC20 | Big/hot keys | Split/spread to avoid hotspots |
| RC21 | Stampede | Lock/jitter on expiry rebuilds |
| RC22 | Consistency | Eventual; bound by TTL/invalidation |
| RC23 | What to cache | Hot, expensive, stable reads |
| RC24 | Key design | Namespaced, predictable, versioned |
| RC25 | Memory | maxmemory + eviction + TTLs |
| RC26 | Monitoring | Hit ratio, memory, evictions |
| RC27 | Security | Auth, TLS, private network, ACLs |
| RC28 | Azure | Managed Azure Cache for Redis |
| RC29 | Pitfalls | No TTL, no invalidation, public exposure |
| RC30 | My approach | Cache-aside + TTL + fallback + managed |

---

[← System Design](47-concept-system-design.md) · [Home](README.md) · [Next → Kafka](49-concept-kafka.md)
