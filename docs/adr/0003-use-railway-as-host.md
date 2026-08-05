# ADR-0003: Use railway as host

- **Status**: Accepted
- **Date**: 2026-07-05

## Context

This decision is mostly shaped by cost, given that this project is designed to be minimal, though with lots of moving parts, I believe that railway and their flexible resource management would allow me to keep costs to a minimal while keeping flexibility of a managed space.

## Decision

Use railway as principal host of the entire project.

## Consequences

- Host would be initially cheaper.
- It would be easier to manage short term.
- If the project grows, moving it to another CSP could be reconsidered. Depending on the money I have available.

## Alternatives considered

- AWS
- GCP
- Hetzner (problem with hetzner is the locations tend to be Europe-based)
