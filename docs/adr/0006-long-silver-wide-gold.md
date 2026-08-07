# ADR-0006: Long silver, Wide gold

- **Status**: Accepted
- **Date**: 2026-08-07

## Context

Because the data obtained from the different ingestion services is asymmetrical at times, leaving Silver with a Wide shape would make a table with multiple blank columns at times, easier to understand, but I believe would make working with that data very convoluted, so I instead opted for making this __Silver__ model have a long shape which would then be converted afterwards into a Wide shape for the __Gold__ data warehouses.

## Decision

This means we will have one row per __station-variable-timestamp-source__ and then a __variable/key__ column + a __value__ column in Silver. While Gold would be structured more as regular DBs are built, creating a column per variable in each schema.

## Consequences

- It would be easier to perform a source-disagreement-analysis in the future in case some of my sources disagree.
- Also adding more variables or sources would require no migration.
- Humans and APIs would have a harder time reading Silver directly.

Would revisit if anything needs to serve from silver directly

## Alternatives considered

- **Wide silver**: rejected because given the variety of sources we have it would have made multiple shadow quality columns and it would require a migration per new variable added.
- **JSONB blobs**: rejected because loses typed values and the uniqueness constraint that enforces the invariant.
