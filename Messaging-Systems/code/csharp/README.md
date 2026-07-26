# C# samples

Six files, one per producer/consumer pair. Every file opens with the **algorithm in plain English** as a comment block — read that first, then the code. The point is that the algorithm is the transferable part; the C# is just one way to type it.

| File | What it teaches |
|---|---|
| [`kafka-producer.cs`](kafka-producer.cs) | Idempotent producer, `acks=all`, keys and partitioning, transactional read-process-write |
| [`kafka-consumer.cs`](kafka-consumer.cs) | Manual offset commits, cooperative rebalancing, bounded retry, hand-built DLQ topic |
| [`azure-producer.cs`](azure-producer.cs) | PeekLock-friendly sends, sessions, batching, scheduled messages, topology as code |
| [`azure-consumer.cs`](azure-consumer.cs) | Lock renewal, Complete/Abandon/DeadLetter/Defer, session sagas, DLQ drain job |
| [`rabbitmq-producer.cs`](rabbitmq-producer.cs) | Publisher confirms, `mandatory` + returns, quorum queues, the outbox pattern |
| [`rabbitmq-consumer.cs`](rabbitmq-consumer.cs) | Prefetch, manual ack, the TTL retry queue, `x-death` triage |
| [`dapr-publisher.cs`](dapr-publisher.cs) | Broker-agnostic publish, partition keys, bulk publish, raw payload, the Dapr outbox |
| [`dapr-subscriber.cs`](dapr-subscriber.cs) | SUCCESS/RETRY/DROP response semantics, CloudEvents, dead letter topics |

## Running them

These are teaching files, not a solution. To run them, drop them into a console project:

```bash
mkdir messaging-samples && cd messaging-samples
dotnet new console
dotnet add package Confluent.Kafka                  # Kafka
dotnet add package Azure.Messaging.ServiceBus       # Service Bus
dotnet add package Azure.Identity                   # Service Bus auth
dotnet add package RabbitMQ.Client                  # RabbitMQ (v7+ — the async API)
dotnet add package Dapr.Client                      # Dapr publisher
dotnet add package Dapr.AspNetCore                  # Dapr subscriber
dotnet add package Microsoft.Extensions.Hosting
cp ../*.cs .
dotnet build
```

The Dapr samples are a **web app**, not a console app — the sidecar calls your HTTP endpoint rather than you polling a broker. Use `dotnet new web` if you want to run those.

Package versions the samples target:

| Package | Version | Note |
|---|---|---|
| `Confluent.Kafka` | 2.6.x | Wraps librdkafka; the config names map 1:1 to the Java client |
| `Azure.Messaging.ServiceBus` | 7.18.x | `ServiceBusProcessor` is the high-level API used here |
| `Azure.Identity` | 1.13.x | `DefaultAzureCredential` — managed identity, no connection strings |
| `RabbitMQ.Client` | **7.x** | v7 made the whole API async. On v6 the calls are `BasicPublish`, not `BasicPublishAsync` |
| `Dapr.Client` / `Dapr.AspNetCore` | 1.15.x | Component metadata options move between Dapr releases — verify against your version |

`RabbitMQ.Client` 7 is a breaking change from 6. If your codebase is on 6.x, the shapes are the same but drop the `Async` suffix and the `CancellationToken`.

## Local brokers

```bash
# Kafka — single broker, KRaft mode, no ZooKeeper
docker run -d --name kafka -p 9092:9092 apache/kafka:3.9.0

# RabbitMQ — with the management UI on :15672 (guest/guest)
docker run -d --name rabbit -p 5672:5672 -p 15672:15672 rabbitmq:4-management

# Dapr — self-hosted mode gives you a sidecar plus a local Redis component
dapr init
dapr run --app-id order-api --app-port 8080 --resources-path ./components -- dotnet run
```

Azure Service Bus has **no local emulator with full fidelity**. The Service Bus emulator container covers queues, topics and subscriptions but not sessions, transactions, or Geo-DR. For anything past the basics, use a real Standard-tier namespace — it costs about $10/month and behaves like production.

```bash
# what the emulator does cover
docker run -d -p 5672:5672 mcr.microsoft.com/azure-messaging/servicebus-emulator:latest
```

## Wiring for the samples

The samples read credentials from environment variables so nothing lands in source control:

```bash
export KAFKA_USER=... KAFKA_PASSWORD=...
export RABBIT_USER=... RABBIT_PASSWORD=...
# Service Bus uses DefaultAzureCredential — az login, or a managed identity
```

For a local broker with no auth, delete the four security lines in the Kafka config block and use `guest/guest` for RabbitMQ.

## What is deliberately missing

- **Serialization beyond JSON.** Production systems should use Avro or Protobuf with a schema registry. JSON keeps the samples readable; see the schema evolution section in [`../../docs/tutorial.md`](../../docs/tutorial.md#20-schema-evolution-and-versioning) for what to do instead.
- **A real `IIdempotencyStore`.** Every consumer depends on this interface and none of them implement it. That is on purpose — the implementation is one table with a unique index on `MessageId` and a TTL cleanup job, and it belongs in your data layer, not in a broker sample.
- **Dependency injection wiring.** Each class is DI-shaped (constructor injection, `BackgroundService`) but there is no `Program.cs`. Register the producers as singletons and the consumers as hosted services.
- **MassTransit / NServiceBus.** Both are excellent and both hide exactly the mechanics these files exist to show. Use them in production; read these first so you know what they are doing for you. The Dapr samples *are* included, because the abstraction's trade-offs are themselves a decision this repo has to cover — see [`../../docs/dapr.md`](../../docs/dapr.md). For a .NET-only shop, MassTransit is usually the better choice than Dapr; the comparison is in that document.
