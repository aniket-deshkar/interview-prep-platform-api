# Contributing

## Development workflow

1. Create a focused branch from `main`.
2. Copy `.env.example` to `.env` and generate real local secrets.
3. Start infrastructure with `docker compose up -d postgres redis minio minio-init`.
4. Install the package with `make install`.
5. Run migrations with `make migrate`.
6. Before opening a pull request, run `make lint test`.

## Engineering conventions

- Keep HTTP concerns in `api/`, business workflows in `services/`, persistence in
  `repositories/`, and storage models in `models/`.
- Every schema change requires an Alembic migration.
- External APIs must sit behind a service adapter with explicit timeouts and retries.
- Never log access tokens, resume text, email bodies, or interview notes.
- New endpoints require response models and authorization tests.

Commit messages should describe one logical change in the imperative mood.

