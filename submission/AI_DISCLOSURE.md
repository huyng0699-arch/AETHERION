# AETHERION — AI Tools & Generation Limits Disclosure (Q-0265)

This disclosure states truthfully how AI tools were used during development of AETHERION by **Team TRUY TINH** for the 2026 NASA Space Apps Challenge, and defines strict limits on AI in both development and runtime behavior.

## 1. Development AI Tools Used

- **Agentic Coding Assistants (Codex & Antigravity/Gemini):** Used under `AGENTS.md` rules for repository scaffolding, Quest coordination, schema/provenance documentation, and automated unit test authoring.
- **Verification Principle:** No AI-generated code, scientific summary, or Quest status is accepted on AI assertion alone; every change requires deterministic test execution, SHA-256/source verification, and recorded commit SHAs.

## 2. Runtime AI Boundaries & Safety Limits

- **No Mandatory AI Dependency:** AETHERION's core health-indicator gathering, provenance tracking (`READY`, `NO_DATA`, `STALE`, `OFFLINE`, `DENIED`, `ERROR`, `UNVERIFIED`), and **GATHER → EVALUATE → ACT → RECHECK** workflow operate deterministically when optional AI is disabled or offline.
- **Not a Safety-Critical or Clinical Authority:** Optional local/cloud AI gateways cannot override deterministic alert/identity logic, invent missing sensor measurements, or issue medical diagnoses or treatment orders.
- **No Unverified Medical Performance Claims:** AETHERION does **not** claim clinical sensitivity/specificity, FDA/NASA flight certification, or autonomous medical triage accuracy.

## 3. Data & Content Generation Limits

- **No Fabricated NASA Records:** Historical NASA OSDR/NLSP/HRP metadata and CliFF 119 audit counts are verified directly against official NASA sources; unimported CliFF 119 PDFs (`0/119`) are never synthesized by an LLM.
- **No Synthetic Patient Telemetry:** Test fixtures are explicitly separated from real human health telemetry.
