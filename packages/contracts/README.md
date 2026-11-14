# Shared contracts

The server is the single source of truth. Machine-checkable OpenAPI 3.1 schema exported from `aetherion_server.main:app` is published at [openapi.json](openapi.json).

## Current routes

- `GET /health` — returns `{"service": "aetherion-server", "status": "ok"}`
- `GET /api/v1/observations?subject_id=...&limit=100` — returns persisted observations for `subject_id`
- `POST /api/v1/observations` — ingests one observation with timezone-aware `observed_at`

## Sample requests

### Health check
```bash
curl -s http://127.0.0.1:8765/health
```

### Create observation (valid)
```bash
curl -s -X POST http://127.0.0.1:8765/api/v1/observations \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "crew-01",
    "metric": "heart_rate",
    "value": 68.0,
    "unit": "bpm",
    "source": "manual-engineering-test",
    "observed_at": "2026-11-14T04:00:00Z"
  }'
```

### List observations
```bash
curl -s "http://127.0.0.1:8765/api/v1/observations?subject_id=crew-01&limit=10"
```

### Expected validation error (naive timestamp without timezone)
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "observed_at"],
      "msg": "Value error, observed_at must include a time-zone offset"
    }
  ]
}
```

## Contract & safety notes

- A new observation requires `subject_id`, `metric`, `value`, `unit`, `source`, `observed_at` (with explicit timezone offset).
- Do not infer verification from the `source` string; current starter responses explicitly mark entries `stored_unverified`.
- Before introducing phone/watch apps or multi-user deployments, expand this contract with identity/authorization, `scope`, `quality`, `verification_state`, error envelopes, and event acknowledgements (`Q-0031` and follow-on contract quests). See `docs/ARCHITECTURE.md`.
