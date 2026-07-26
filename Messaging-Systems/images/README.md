# Images

Every image in this folder lives here and nowhere else. Markdown files link to it with relative paths.

## Two kinds of image, on purpose

| Kind | Where | How it is made | Edit by |
|---|---|---|---|
| **Hand-authored** | `svg/` | Written directly as SVG. Dense, annotated, poster-quality. | Editing the `.svg` file |
| **Machine-rendered** | `svg/` + `png/` | Generated from `../diagrams/*.mmd` by `../scripts/render-diagrams.sh` | Editing the `.mmd` file, then re-running the script |

The render script **skips** hand-authored names so it never overwrites them. The skip list lives in the `HAND_AUTHORED` array at the top of the script — keep the two in sync.

## The four hand-authored diagrams

| File | Shows | Companion Mermaid |
|---|---|---|
| [`svg/kafka-architecture.svg`](svg/kafka-architecture.svg) | Brokers, partitions, leaders and followers, consumer groups, tiered storage | [`../diagrams/kafka-architecture.mmd`](../diagrams/kafka-architecture.mmd) |
| [`svg/azure-service-bus-architecture.svg`](svg/azure-service-bus-architecture.svg) | Topic, subscriptions with filters, sessions, dead-letter queue, Geo-DR | [`../diagrams/azure-service-bus-architecture.mmd`](../diagrams/azure-service-bus-architecture.mmd) |
| [`svg/rabbitmq-architecture.svg`](svg/rabbitmq-architecture.svg) | Exchange types, binding keys, quorum queues, dead-letter exchange, the TTL retry trick | [`../diagrams/rabbitmq-architecture.mmd`](../diagrams/rabbitmq-architecture.mmd) |
| [`svg/broker-decision.svg`](svg/broker-decision.svg) | The five questions that pick a broker | [`../diagrams/broker-decision.mmd`](../diagrams/broker-decision.mmd) |

The Mermaid companions carry the same structure in a form GitHub renders inline and diffs cleanly. The SVGs carry the annotations that make the structure mean something. Both are checked in.

## Colour semantics

The palette is shared with [`../../MicroServices/diagrams/README.md`](../../MicroServices/diagrams/README.md) so the two folders read as one body of work. Here the product colours carry the meaning:

| Colour | Meaning |
|---|---|
| 🟠 Amber `#FF7A45` | **Apache Kafka** — partitions, offsets, the log |
| 🔵 Blue `#6C8EF5` | **Azure Service Bus** — queues, topics, subscriptions |
| 🟢 Green `#3DDC97` | **RabbitMQ** — exchanges, bindings, quorum queues |
| 🟣 Purple `#B980F0` | **Hybrid / abstraction** — Event Hubs, MassTransit, anything spanning two transports |
| 🔴 Red `#F45B69` | **Failure path** — dead-letter, poison message, parked |
| 🟡 Gold `#E0B341` | **Legacy / being replaced** — the old queue in a migration |
| ⚪ Slate `#8FA3B5` | Infrastructure, storage, neutral |

Backgrounds are always `#0F1620`. Monospace is reserved for identifiers — topic names, queue names, config keys. Sans-serif for anything a human wrote.

This differs from the MicroServices set, where amber meant *synchronous* and green meant *asynchronous*. Everything on these pages is asynchronous, so that split would carry no information. The [`broker-decision.svg`](svg/broker-decision.svg) diagram says so on its own face.

## Regenerating

```bash
# from the Messaging-Systems folder
./scripts/render-diagrams.sh            # everything
./scripts/render-diagrams.sh case-study # only files matching "case-study"
./scripts/render-diagrams.sh --check    # CI gate: fail if a .mmd has no image
```

PNGs are gitignored — they are 1600×900 exports for LinkedIn and slide decks, which do not accept SVG uploads. Regenerate them when you need them:

```bash
pip install cairosvg     # only needed for the hand-authored SVGs
./scripts/render-diagrams.sh
```
