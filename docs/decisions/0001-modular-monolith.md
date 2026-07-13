# ADR 0001: Start with a modular monolith

- Status: Accepted
- Date: 2026-07-13

## Context

The product needs authentication, practice content, resume retrieval, interview tracking,
provider synchronization, and AI workflows. The initial audience is one user, with a likely
near-term scale around 100 daily users. Independent services would increase operational cost
and make cross-feature transactions harder without providing a scale benefit.

## Decision

Use a FastAPI modular monolith with explicit internal boundaries and separate worker
processes. PostgreSQL is the system of record, `pgvector` handles similarity search, Redis
handles ephemeral state and the task broker, and S3-compatible storage holds source files.

The API, worker, and scheduler share one versioned codebase but deploy as separate process
types. External provider and AI APIs are accessed through adapters.

## Consequences

- Local development and deployment remain simple.
- Strong database transactions are available across tracker workflows.
- Modules can be extracted later at their service boundaries if load or team ownership
  requires it.
- Worker tasks must be idempotent because delivery is at least once.
- Database scaling is handled first through indexing, pooling, read replicas, and partitioning
  before service decomposition.

