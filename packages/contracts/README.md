# Shared contracts

The server is the single source of truth. Current experimental routes:

- `GET /health`
- `GET /api/v1/observations?subject_id=...`
- `POST /api/v1/observations`

A new observation has `subject_id`, `metric`, `value`, `unit`, `source`, `observed_at`. Do not infer verification from the `source` string. Entries are engineering records only.

Before introducing phone/watch apps, publish and freeze versioned JSON schemas, identity/authorization model, error envelopes, event acknowledgements, offline reconciliation and time-zone rules. See `docs/ARCHITECTURE.md`.
