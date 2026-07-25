# Chapter 1 — The Three Axes

← [Tutorial index](README.md) · Next: [Chapter 2 — Synchronous](02-synchronous.md)

---

## In one line

Your services talk in three different directions, and most teams only think about one of them.

---

## The words you need

| Word | Plain meaning |
|---|---|
| **Service** | One program you can deploy on its own. It owns some data and does some job. |
| **Boundary** | The line around a service. Inside the line is yours. Outside the line you must ask. |
| **Coupling** | How much two services need each other. High coupling means changing one forces you to change the other. |
| **Latency** | How long a call takes. Measured end to end, including the network. |
| **Blast radius** | How much breaks when one thing breaks. |
| **Trust boundary** | The edge of your own network. Inside, you can assume callers are your own services. Outside, you assume nothing. |

---

## The three axes

### Axis 1 — East-west: service to service

This is one of your services calling another of your services. Both are inside your network. Both are yours.

Example: `Ordering` needs to know if 3 units of item `SKU-88` are in stock, so it asks `Inventory`.

Almost every microservices article is about this axis. It is important, but it is one third of the problem.

### Axis 2 — North-south: the outside world to your system

This is traffic crossing your trust boundary. A phone app, a browser, a partner company's server, a payment provider calling you back.

Example: a mobile app sends `POST /orders`. A shipping partner sends you a webhook when a parcel is scanned.

North-south is different from east-west in every way that matters:

- You cannot trust the caller. You must authenticate and authorise every request.
- You cannot change the caller. An old version of your mobile app will be in someone's pocket for two years.
- The network is slow and unreliable — mobile data, not a data-centre switch.
- You must publish a stable contract and version it.

### Axis 3 — The boundary itself: who owns what

This axis is not about a network call at all. It is about where you drew the lines in the first place, and which service owns which piece of data.

Example: does `Ordering` own the customer's shipping address, or does `Customers`? If both write to it, you have a problem that no amount of good messaging will fix.

---

> **Diagram: D1 — The communication landscape**
> [`images/svg/d1-landscape.svg`](../images/svg/d1-landscape.svg) · [Mermaid source](../diagrams/README.md#d1--the-communication-landscape)

![The communication landscape](../images/svg/d1-landscape.svg)

---

## Why axis 3 matters most

Here is the claim, stated plainly:

> Most teams obsess over axis 1, under-invest in axis 2, and skip axis 3 entirely. Skipping axis 3 is what produces a **distributed monolith** — the worst of both worlds.

A distributed monolith is a system that has all the operational cost of microservices (many deploys, network calls, distributed debugging) and none of the benefit (independent deployment, independent failure, independent teams).

You get it by splitting the code without splitting the ownership.

### A concrete example of getting axis 3 wrong

Say you split a monolith into `Ordering` and `Inventory`. It looks like two services. But:

- Both connect to the same database.
- Both read and write the `Products` table.
- `Ordering` reads `Inventory`'s `StockLevels` table directly, because "it is faster than an API call".

What have you actually built? One service with extra network hops. Proof:

- You cannot deploy `Inventory` alone, because a schema change breaks `Ordering`.
- You cannot scale them separately in any useful way — they share the same database bottleneck.
- A bad query in `Ordering` slows down `Inventory`.

The network calls made things slower and harder to debug. You got nothing back.

---

## How the three axes map to the rest of this tutorial

| Axis | Chapters |
|---|---|
| **East-west** | [2 — Synchronous](02-synchronous.md), [3 — Asynchronous](03-asynchronous.md), [4 — Choosing a broker](04-choosing-a-broker.md) |
| **North-south** | [5 — Gateway and BFF](05-gateway-and-bff.md) |
| **The boundary** | [6 — Boundaries and data ownership](06-boundaries-and-data.md) |
| Everything cracks along these lines | [7 — Sagas](07-saga.md), [8 — Outbox](08-outbox-and-idempotency.md), [9 — Resilience](09-resilience.md), [10 — Observability](10-observability.md) |

---

## Sharp edges

**Edge 1 — East-west security is not optional any more.** "Inside the trust boundary" used to mean "no auth needed". With shared clusters and supply-chain attacks, that assumption is dead. Modern practice is service-to-service identity (mTLS via a service mesh, or signed tokens). Treat the trust boundary as thin, not absent.

**Edge 2 — A north-south contract is forever.** You can refactor an internal API on a Tuesday afternoon. You cannot refactor the API your mobile app uses without a migration plan measured in months.

**Edge 3 — Boundaries are expensive to move later.** Changing which service owns a table is a data migration plus a code change plus a coordinated deploy. This is why axis 3 deserves the most thought up front, even though it feels like the least urgent.

---

## When to use what — the short version

You will get the full framework in [chapter 11](11-decision-framework.md). The one-line version:

- Caller **cannot continue** without the answer, and the answer is fast → **synchronous** (chapter 2)
- Caller **can continue** → **asynchronous** (chapter 3)
- Traffic **crosses your boundary** → put a **gateway** in front of it (chapter 5)
- Two services want the **same table** → you drew the boundary wrong (chapter 6)

---

## Try it yourself

Take a system you work on now. On one page, draw:

1. Every service as a box.
2. Every synchronous call as a **solid arrow**.
3. Every message or event as a **dashed arrow**.
4. Every database as a cylinder, connected to the services that write to it.

Then answer three questions honestly:

- **Q1.** Is there a cylinder with more than one solid arrow into it? That is a shared database. That is axis 3 broken.
- **Q2.** What is the longest chain of solid arrows for one user request? Multiply the hops by your average call time. That number is your latency floor, before any real work happens.
- **Q3.** Which single box, if it went down, would take the most other boxes with it? That is your blast radius. Chapter 9 is about shrinking it.

Keep this drawing. You will use it again in chapters 6, 9, and 11.

---

← [Tutorial index](README.md) · Next: [Chapter 2 — Synchronous communication](02-synchronous.md)
