# Security policy

## Reporting

Please report security issues privately to the repository owner. Do not open a public issue
for a suspected vulnerability.

## Data-handling baseline

- OAuth refresh tokens are encrypted at rest using a dedicated application key.
- Provider connections request read-only Gmail, Outlook, and calendar scopes.
- Resume objects are private and encrypted by the object store.
- Every user-owned query includes an ownership predicate; object keys are never trusted as
  authorization boundaries.
- Secrets belong in the deployment secret manager, never in Git or frontend bundles.
- Production deployments should add a managed WAF, rate limits, audit retention, dependency
  scanning, and secret rotation.

Before public launch, complete Google OAuth verification, Microsoft publisher verification,
a privacy policy, account deletion/export workflows, and a focused penetration test.

