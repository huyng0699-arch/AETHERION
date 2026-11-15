# Shared contracts

The server is the single source of truth. Machine-checkable OpenAPI 3.1 schema exported from `aetherion_server.main:app` is published at [openapi.json](openapi.json).

## Current routes (48 paths exported from `aetherion_server.main:app`)

- **Core / Health / Sync:** `GET /health`, `GET /ready`, `GET /api/v1/sync/status`
- **Public Demo Archive (`Q-0478` / `Q-0197`):** `GET /api/v1/demo/nasa-ma7`
- **Auth & Subjects (`Q-0032` / `Q-0033` / `2787a6d`):** `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`, `GET / POST /api/v1/subjects`, `GET /api/v1/subjects/{subject_id}`, `GET /api/v1/subjects/{subject_id}/summary`
- **Observations / Sources / Devices / ECG:** `GET / POST /api/v1/observations`, `GET /api/v1/observations/series`, `GET /api/v1/sources`, `GET /api/v1/sources/{source_id}`, `POST /api/v1/devices/heartbeat`, `GET /api/v1/devices/{source_id}/status`, `GET / POST /api/v1/ecg/recordings`, `GET /api/v1/ecg/recordings/{recording_id}`
- **Care Journey & AI Assistant:** `GET / POST /api/v1/care/episodes`, `GET /api/v1/care/episodes/{episode_id}`, `POST /api/v1/care/episodes/{episode_id}/advance`, `GET /api/v1/assistant/status`, `POST /api/v1/assistant/chat`
- **Knowledge, Symptoms & 3D Anatomy:** `GET /api/v1/knowledge/status`, `GET /api/v1/knowledge/articles`, `GET /api/v1/knowledge/articles/{article_id}`, `GET /api/v1/knowledge/symptoms`, `GET /api/v1/knowledge/interview/ai-status`, `POST /api/v1/knowledge/interview/next`, `GET /api/v1/knowledge/anatomy/models`, `GET /api/v1/knowledge/anatomy/models/{anatomical_id}/file`
- **Safety / Emergencies / Offline Fallback:** `POST /api/v1/safety/incidents`, `GET /api/v1/safety/incidents/{incident_id}`, `POST /api/v1/safety/incidents/{incident_id}/ack`, `GET /api/v1/safety/incidents/{incident_id}/audit`, `POST /api/v1/safety/incidents/{incident_id}/evaluate-timeout`, `GET / POST /api/v1/safety/incidents/{incident_id}/receipts`, `GET /api/v1/safety/offline-fallback`
- **Admin Runtime & AI Control:** `GET /api/v1/admin/overview`, `GET /api/v1/admin/users`, `GET /api/v1/admin/sources`, `GET /api/v1/admin/events`, `GET / PUT /api/v1/admin/ai/settings`, `GET / PUT / DELETE /api/v1/admin/ai/cloud/settings`, `POST /api/v1/admin/ai/cloud/test`, `GET /api/v1/admin/ai/local/models`, `POST /api/v1/admin/ai/local/test`, `POST /api/v1/admin/storage/backup`

## Sample requests

### Health check
```bash
curl -s http://127.0.0.1:8765/health
```

### Create observation (valid)
```bash
curl -s -X POST http://127.0.0.1:8765/api/v1/observations \
  -H "Authorization: Bearer <TOKEN>" \
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
curl -s -H "Authorization: Bearer <TOKEN>" "http://127.0.0.1:8765/api/v1/observations?subject_id=crew-01&limit=10"
```

### Expected validation error (naive timestamp without timezone)

Illustrative HTTP 422 envelope from the FastAPI validation handler. The `detail` array varies with the invalid input; this is not a byte-for-byte captured HTTP response.
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "status": 422,
    "message": "Request validation failed",
    "action": "Fix the invalid request fields shown in detail and retry."
  },
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

- A new observation requires `subject_id`, `metric`, `value`, `unit`, `observed_at` (with explicit timezone offset), and **at least one of** `source_id` or `source` (non-blank). Neither source field is individually required by the OpenAPI schema; the `ObservationIn` model validator enforces the alternative at runtime.
- Do not infer verification from the `source` string; unverified client submissions carry `UNVERIFIED` / explicit quality states rather than silent verification.
- See [openapi.json](openapi.json) for full request/response schemas and `HTTPBearer` security requirements.
