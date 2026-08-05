# ADR-0004: Use kafka for events only

- **Status**: Accepted
- **Date**: 2026-07-05

## Context

Given that this project is meant to be a show of skills, and all the other purposes people use Kafka for could be instead provided by other tools I'm already using in this project; I think it's better to limit Kafka only as an event broker.

## Decision

Keep Kafka as an event log for transport and replay, nothing much beyond that.

## Consequences

- It would allow me more resiliency allowing me to store, replay and broadcast responses without recalling external APIs
- It would allow me to decouple the architecture better and connect a separate service in the future if I need it by just attaching it to the queue.
- Also in case of failures, Kafka could temporarily store data that didn't get sent properly.

## Alternatives considered
