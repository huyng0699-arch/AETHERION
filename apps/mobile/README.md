# AETHERION Mobile

Expo React Native and TypeScript app for Android and web. English is the default; Vietnamese is selectable.

## Run

```powershell
npm install
npm run web
```

For Android Emulator, use `http://10.0.2.2:8765`. For a USB-connected phone, run `adb reverse tcp:8765 tcp:8765` and use `http://127.0.0.1:8765`. Production connections require HTTPS. The server remains the source of truth for accounts, health records, care journeys, science articles, and AI availability.

## Screens

- Portal, sign-in, Health, Monitor, AI, Science, Care Journey, Crew, Settings, More, Notifications, Help, Privacy, and Server Connection.
- The NASA demo works offline using the bundled Mercury-Atlas 7 postflight report extraction. It shows source anchors and missing metrics; it is historical data, not a current patient record.
- Health, Monitor, AI, Care, and Crew require a server session. Science and the historical NASA demo are public.

## Server API

- Auth: `/api/v1/auth/login`, `/api/v1/auth/me`, `/api/v1/auth/logout`
- Health: `/api/v1/subjects/{subject_id}/summary`, `/api/v1/observations`
- AI: `/api/v1/assistant/status`, `/api/v1/assistant/chat`
- Science: `/api/v1/knowledge/status`, `/api/v1/knowledge/articles`, `/api/v1/sources`
- Care: `/api/v1/care/episodes`
- Readiness: `/health`

Native sessions use `expo-secure-store`; Expo Web keeps the session in `sessionStorage`. The app does not save passwords, fabricate sensor readings, or create AI replies locally.
