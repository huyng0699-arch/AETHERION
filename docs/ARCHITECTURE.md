# Architecture decision — AETHERION monorepo

## Deliberate separation

```text
  Native Windows Desktop       Future Android        Future Wear OS
          |                         |                       |
          +-------------------------+-----------------------+
                                    |
                           Versioned HTTP API
                                    |
                     AETHERION SERVER (local first)
                   observation store / provenance
                       rules and care journeys *
                      optional AI gateway *
                                    |
                     Curated evidence and datasets
```

`*` = intended extension, **not implemented** in the starter.

The server runs as a distinct process, not inside a browser, while the Windows GUI runs as a native Qt process. The only shared mutable health observation store belongs to the server. Clients may cache authorized data in later versions but may not create diverging clinical truths.

## Source layout

- `apps/server`: FastAPI HTTP service, typed endpoints, SQLite implementation. Default bind address is `127.0.0.1`.
- `apps/desktop`: PySide6 Qt Widgets process. Main menu is a **top navigation row above the application content**. No separate landing page before the app.
- `apps/mobile` and `apps/watch`: roadmap placeholders only; not working applications.
- `packages/contracts`: API contract and evolution policy. A versioned schema will become the source of truth.
- `knowledge`: scientific data with licensing, provenance and verification status. Not a fabricated dataset.
- `tests`: executable store-level tests; API, UI and Windows packaging tests must be added.

## Engineering invariants

1. Record subject, measurement name, value, unit, source and observation time; missing data is not normal data.
2. Keep a clear distinction between measured, self-reported, derived and unknown values.
3. A source name alone is not evidence that a device measurement is verified.
4. Clinical suggestions require documented evidence, validation and a clear scope of use; AI must not silently override safety logic.
5. Disconnected use must fail safely. No reply from a device does not mean the person is unconscious.
6. Real PHI is prohibited in the unauthenticated prototype. Before any community release: access control, consent, threat model, encryption, audit and regulatory review.
7. Windows packaging must include dependency licenses and pass real executable cold-start and offline tests.

## First functional endpoints

| Endpoint | Purpose | Status |
| --- | --- | --- |
| `GET /health` | Process health | Initial implementation |
| `GET /api/v1/observations?subject_id=...` | Read observations for one subject | Initial implementation, no auth |
| `POST /api/v1/observations` | Engineering-only manual observation input | Initial implementation, no medical verification |

**Not implemented:** EVALUATE clinical rules, ACT care guidance, RECHECK journal, AI selection, sensor adapter, authenticated crew access, mobile/watch apps, verified NASA data ingestion.

## Integration direction

The local server may later expose an authenticated HTTP service over a trusted shipboard network. A cloud AI provider is **optional** and must never be a safety-critical dependency. Local inference should have a signed/model-versioned package, with no implicit data sharing.

## Versioning

Retain `/api/v1` for backward-compatible endpoints. Breaking changes require a new version and migration tests. Keep explicit responsibility for data storage, API, UI and knowledge ingestion.
