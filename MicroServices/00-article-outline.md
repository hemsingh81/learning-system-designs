# Origin Notes

← [Back to the map](README.md)

## What this file is

Before there was a [tutorial](tutorial/README.md) or any [case studies](case-studies/README.md), there was a section-by-section outline for a single long article. This file is what's left of that outline — kept only because it shows *why* the material is shaped the way it is.

**You do not need to read this.** Everything in it was written and expanded into the tutorial and case studies below, in far more depth than the outline planned for.

## Two ideas from the outline that shaped everything downstream

**The three-layer rule.** Every section had to work at three depths: *one line* (the idea, no jargon), *how it works* (mechanics and an example), *sharp edges* (what breaks, what bites at scale). That's still the backbone of every tutorial chapter today.

**The 2 a.m. incident.** The original hook: an order service calls payment synchronously, payment slows under load, orders time out, retries amplify the load, checkout collapses. The thesis it was making the case for — *the hard part of microservices isn't splitting the code, it's choosing how the pieces talk* — is still the closing thought of [chapter 11](tutorial/11-decision-framework.md#the-closing-thought).

## Where each planned section ended up

| Planned section | Now lives at |
|---|---|
| The three axes | [Chapter 1](tutorial/01-three-axes.md) |
| Synchronous communication | [Chapter 2](tutorial/02-synchronous.md) |
| Asynchronous communication | [Chapter 3](tutorial/03-asynchronous.md) |
| Choosing a broker | [Chapter 4](tutorial/04-choosing-a-broker.md) |
| North-south / gateway & BFF | [Chapter 5](tutorial/05-gateway-and-bff.md) |
| Boundaries | [Chapter 6](tutorial/06-boundaries-and-data.md) |
| Sagas | [Chapter 7](tutorial/07-saga.md) |
| Outbox and idempotency | [Chapter 8](tutorial/08-outbox-and-idempotency.md) |
| Resilience | [Chapter 9](tutorial/09-resilience.md) |
| Observability | [Chapter 10](tutorial/10-observability.md) |
| Decision framework | [Chapter 11](tutorial/11-decision-framework.md) |
| Industry case studies | [case-studies/](case-studies/README.md) — grew from a five-row sketch into five full systems with runnable code |
| The 10 diagrams (D1–D10) | [diagrams/](diagrams/README.md) |

Two things exist now that were never in the plan at all: the [reading guide for the sample code](case-studies/HOW-TO-READ-THE-CODE.md), and the [137-question interview prep](interview-prep/README.md).

---

← [Back to the map](README.md)
