# Q-0489 — OnePad AI architecture to AETHERION real chat

**Source reviewed:** https://github.com/huyng0699-arch/OnePad-School-AI (default branch master, source inspected on 2026-11-15). **Destination:** https://github.com/huyng0699-arch/AETHERION (main).

## What was actually learned from OnePad

| OnePad source | Observed behavior | Adaptation in AETHERION |
| --- | --- | --- |
| `OnePadSchoolAI/src/services/ai/aiClient.ts` | Select Gemini/cloud, local_server or native Cactus; requests have AbortController and superseding request IDs; no blind success | Keep one authenticated ChatPage with request sequence guard, one existing FastAPI router choosing Ollama or server-selected Cloud; never silently fall back from local to cloud |
| `OnePadSchoolAI/src/services/ai/providers/geminiCloudProvider.ts` | Real HTTP POST to Google's `models/{model}:generateContent` with `x-goog-api-key`; reads candidates' returned text, distinguishes provider failures | Server-side Gemini HTTP POST, source-only context, multi-turn `user/model` role mapping, fixed Google domain, bounded output/errors |
| `OnePadSchoolAI/src/services/ai/providers/cactusLocalProvider.ts` | Native mobile Cactus runtime requires model download, initialization and actual device support; no automatic success without these | Do **not** import React Native/Cactus into native Windows; retain real local Ollama server model readiness test and Chat `/api/chat` |
| `OnePadSchoolAI/src/services/ai/providers/localAiProvider.ts` | Stub returns an error for requests; **not** a working server path | Do not copy a false-positive local_server provider |
| `OnePadSchoolAI/src/services/ai/aiPromptBuilder.ts` | Role/context prompts and limited conversation history, explicit no-diagnosis and provenance constraints | Preserve AETHERION's existing VI/EN safety instructions and bounded `FreeChatRequest`, not student-specific educational prompts |
| `backend/src/modules/ai-authoring/ai-authoring-provider.service.ts` | Backend Gemini call supports choosing model/API key; its Base64 key encoding is explicitly development-only and reversible | Use **admin-authorized transient Server memory only**; never import Base64 as encryption and never expose key on the Desktop |

OnePad's README itself states that backend nightly AI may fall back to `template_fallback` and local runtime may be absent. This source review **does not** claim every OnePad AI mode ran successfully on a physical device.

## AETHERION implementation — one Server, native Qt clients

Existing endpoints preserved:
- `POST /api/v1/auth/login` — authenticate actual account.
- `GET /api/v1/assistant/status` — authenticated read of local Ollama model availability and the configured Cloud provider/model (never an API key).
- `POST /api/v1/assistant/chat` — authenticated chat with `provider=local|cloud`, `messages` (16 entries max, max 12,000 characters total), VI/EN and explicit per-request `cloud_consent`. Returns **real model text or an explicit error**, never canned successful text.

Administrator-only Cloud endpoints added under the same FastAPI Server:
- `GET /api/v1/admin/ai/cloud/settings` — nonsecret status (provider, model, key configured, test status, memory/environment source).
- `PUT /api/v1/admin/ai/cloud/settings` — `{"provider":"gemini","model":"gemini-2.5-flash","api_key":"<enter on Server Admin>","enabled":true}`; the raw secret stays only in that server process's RAM. Model name is validated; no arbitrary endpoint.
- `POST /api/v1/admin/ai/cloud/test` — **actual outbound model inference** using a fixed, nonpatient test prompt; reports `status=READY` only if a real nonempty reply arrives. Test validity tied to the exact provider/model/key; admin key changes reset the test state.
- `DELETE /api/v1/admin/ai/cloud/settings` — remove in-process secret. An opt-in environment credential may still be configured separately by the Server operator.

Local Ollama endpoints remain `GET /api/v1/admin/ai/local/models`, `POST /api/v1/admin/ai/local/test` and `PUT /api/v1/admin/ai/settings` (mode `local_only`, selected model, timeout and loopback URL). No new AI server or health store was created.

### Configure from Server Control (Windows)

1. Open the existing native AETHERION Server Control window, authenticate as an actual `admin` Server user, and enter the existing local HTTP URL (usually `http://127.0.0.1:8765`).
2. In **Local / Cloud AI**, choose Cloud provider **Gemini** or **OpenAI**, type the model ID supported by that account, and paste the provider's real API key into the masked **API key (memory only)** field.
3. Click **Configure API** and then **Run real AI request**. A configured-key indicator alone is not a successful provider test. Only an actual inference round trip can report READY. The GUI never reads the key back.
4. Open the separate native AETHERION Desktop, sign in with a legitimate Server user, navigate Browse → AI Chat, choose **Cloud**, explicitly consent to sending **that chat text** to the provider, type and send the question. The Desktop has no API-key field and gets only the model reply/provenance from the Server.

To use Ollama, start the real local runtime with an actually installed model, then configure the already existing Local AI Settings within Server Control, use `Discover installed models` and `Test actual AI inference`, and select **Local** in Chat. If model service or model file is missing, the Server reports unavailable.

### Alternative environment variables (Server-owned, explicit opt-in)

```text
AETHERION_ALLOW_CLOUD_AI=true
AETHERION_ENABLE_CLOUD_CHAT=true
AETHERION_CHAT_CLOUD_PROVIDER=gemini    # or openai (default for legacy configuration)
AETHERION_CHAT_CLOUD_MODEL=<exact provider-supported ID>
AETHERION_GEMINI_API_KEY=<secret>        # Gemini only
AETHERION_OPENAI_API_KEY=<secret>       # OpenAI only
```

The existing `AETHERION_CHAT_CLOUD_MODEL` and OpenAI secret environment configuration remains compatible. When using the Server Admin UI, neither env variable nor persisting a key to SQLite is required: **admin click is the explicit cloud authorization**, and chat still requires consent.

## Safety and evidence boundary

- No automatic cloud fallback; no cloud transmission for local chat. The existing symptoms, deterministic emergency rules, triage and source-linked library are **not** replaced by LLM output. No synthetic patient measurements promoted to medical data or NASA provenance.
- Only loopback local Ollama URLs; external cloud calls use fixed provider HTTPS domains. Reject HTTP redirects/proxies, limit timeouts and response payload sizes. Text and credentials are not logged, and the Server does not persist chat histories.
- Server Administrator API credentials are **not encrypted/persisted**; deliberate security trade-off: runtime memory only. After a Server restart enter the cloud key again or configure secure environment credentials. Do **not** copy OnePad's Base64 mechanism.
- A Chat session belongs to the authenticated account even before that account has an authorized patient subject; a separate `subject_id` is required for Health/Monitoring and the existing account/subject ACLs. Signing out clears ChatPage identity.
- **No live provider key, Ollama runtime or Windows Desktop is available to this implementation runtime.** Source commits and focused GitHub contracts are not proof of live Cloud inference, a local model running, Windows UI rendering or clinical validity. A real Admin provider test and actual authenticated chat are required before Q-0489 can be DONE.
