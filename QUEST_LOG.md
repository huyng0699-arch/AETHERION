# AETHERION — Quest control board

**Scope (later GitHub directory scan, 2026-11-14):** 485 Quest specifications listed on `main`, **Q-0001 through Q-0485** (contiguous at the time of scan). **Dynamic backlog:** recheck `quests/v1/` for live counts; the attached Windows read-only audit examined only Q-0001–Q-0482. Individual Quest files remain the status source of truth. Q-0436–Q-0438 establish the owner design and native Portal/theme work; Q-0480–Q-0485 represent newer work, not automatically accepted releases.

## Q-0484 → Q-0485: Owner visual override / documented ACK (2026-11-14)

This is a redesign of the **native AETHERION application Home**, not a Server Admin HTML/Qt choice. The owner rejects the five oversized Portal cards and the Demo CTA below them. Target: compact mission-operations Home with **DEMO FOR HACKATHON** conspicuous at the top → short **SIMULATED** guide → fully navigable synthetic patient data (5 fictional patients × 540 days × 12 metrics). **NASA MA-7 remains a distinct source-labelled genuine 1962 archive (83 values)**; never merge it into synthetic records.

**Q-0484 ACK to Q-0485:** [Issue #8 comment 6876297980](https://github.com/huyng0699-arch/AETHERION/issues/8#issuecomment-6876297980). Constructor `build_synthetic_patient_demo(parent=None, *, locale="en", theme="daybreak", mode="light")`; Qt `back_requested`, `start()`, `set_locale()`, `set_visuals(theme_name, display_mode)`. `synthetic_patients.py::demo_path()` returns `Path.home()/".aetherion"/"demo"/"synthetic_patients_v1.sqlite3"`; writer `build_demo_database()` and read helpers `demo_stats/subjects/series/day_values/latest`. Q-0485 has **routing permission only**; source ownership and existing Q-0484 metadata remain unchanged. Other owners' shared `main.py`, `portal.py`, and `i18n/{en,vi}.json` claims still require ACK and SHA/CAS before writes. [Issue #8](https://github.com/huyng0699-arch/AETHERION/issues/8) and [Q-0485](quests/v1/Q-0485.md) are the integration coordination records.

**Proof boundary:** Issue comment successfully created and current component source read; **no** verified Windows post-fix Home, clickthrough, SQLite seeded-row count, fresh green CI, or independent review. The 31,610 synthetic rows are an **expected calculation**, not an observed SQLite seed. Q-0484 and Q-0485 remain `COMPONENT_READY / BLOCKED`, reviews `PENDING`. The older Windows five-card baseline remains rejected, not accepted.

---

## Latest owner read-only Windows audit — newer 482-Quest checkout (2026-11-14)

**Highest-priority coordination notice:** A subsequent **read-only** report from an actual Windows computer found serious regressions after the earlier 17:17 Windows retest. **Do not use the earlier 640 passed / 1 failed as the current quality gate.** The new report tested a downloaded checkout containing **482 Quests**, with Python **3.13.14**, FastAPI **0.162.7**, Pydantic **2.14.3**, Uvicorn **0.54.0**, PySide6 **6.12.0**, pytest **9.2.0**, httpx **0.28.1**. Its exact Git commit SHA, raw logs and native screenshot hashes were not supplied. The agent updating this file **read the report and inspected files on live GitHub; it did not rerun the Windows tests**. Findings below describe the tested checkout, while the rightmost columns describe later GitHub source **as separately inspected**.

**Scope:** Server, native Windows Desktop, Watch, CI/tests, data and Quest Board. **Mobile was explicitly excluded from this particular audit** and must not be assigned a result based on it. All earlier reports remain historical snapshots; individual Quest frontmatter remains authoritative for claim/review/status, and no item is newly certified PASS by this navigation document.

### Windows measurements — preserve the actual runner and denominator

| Exact scope / command | Owner-reported result | Interpretation |
| --- | --- | --- |
| `python scripts/lint_python.py` | **FAIL:** scanned 433 Python files; 1 SyntaxError in `tests/test_mission_last_known.py` line 107; 3 SyntaxWarnings in `scripts/quest_review_queue.py` | Syntax fix needed before reliable collection/CI; not equivalent to earlier 336-file PASS |
| `python scripts/quest_board.py check` | **FAIL:** 482 Quests in tested checkout; Q-0426/Q-0427 each refer to themselves | **Already repaired in later GitHub Quest files**; rerun on a pinned checkout before claiming the board is green |
| `pytest tests` without ignores | **5 collection errors:** 1 SyntaxError, 1 missing `PIL`, 3 relative-import failures | Collection was incomplete; no full-suite PASS |
| `pytest tests --ignore=...` (the five collection-failure files) | **666 passed, 79 failed**, including **62 Windows SQLite file-lock failures** and **17 other functional/contract/data failures** | Incomplete *subset* of tests; never report this as a 745-test clean run or claim all failures are SQLite |
| `python -m unittest discover -s tests -v` | **704 tests / 160.71 s: 9 failures + 75 errors**; **63 WinError 32** cases, **21 other errors/failures** | Distinct runner from pytest; do not sum its counts with pytest as if they were separate defects |
| Live Uvicorn / native PySide6 Windows | **PARTIAL:** health/ready/auth/subjects/observations/care/admin/knowledge endpoints responded; Portal five cards, 13 routes, AdminWindow and server health connected | **Severe Qt crash when painting MonitoringWorkspace**; ECG 404 and ancillary features blocked in tested checkout |
| `release_readiness.py` across demo/release/library | **NOT READY** (`release_authorized: false` all three scopes) | No approved release or NASA submission inferred |

### Critical defects and targeted remediation

| Severity / Quest owner | Observed in owner Windows audit | GitHub HEAD reconciliation and next action |
| --- | --- | --- |
| **P0 CRASH · [Q-0477](quests/v1/Q-0477.md)** | `MonitoringWorkspace` assigns `self.metric = QComboBox()`, shadowing virtual `QWidget.metric()`; `win.monitor_page.grab()` triggers Qt eventFilter/paint TypeError | **Still present in** `apps/desktop/src/aetherion_desktop/native_workspaces.py` on inspected main; rename to `metric_box` consistently, run an actual Windows paint/grab and inspect signal/filter controls. Q-0477 is BLOCKED/PENDING; do not self-approve |
| **P0 CI · [Q-0001](quests/v1/Q-0001.md), [Q-0241](quests/v1/Q-0241.md)** | `tests/test_mission_last_known.py:107` misses a closing `)`; `scripts/quest_review_queue.py` has three invalid-escape warnings; pytest collection fails also for three file-loaded desktop modules with package-relative `localization` imports (`test_medical_library_nav.py`, `test_mission_control.py`, `test_mission_event_list.py`) | **Syntax error and warning strings still visible in latest source inspection.** Fix syntax; run `lint_python.py` / pytest collect; update test imports to use real package context, not speculative source fixes. CI workflow installs pytest but does not **explicitly** install `httpx`, and its focused server-only command does not cover Desktop |
| **P0 Windows SQLite · [Q-0031](quests/v1/Q-0031.md) + core stores** | **62** pytest and **63** unittest teardown errors reported as `PermissionError [WinError 32]`; `with sqlite3.connect(...)` handles transactions but **does not close the connection** | Audit scoped connection lifetime in `store.py`, `knowledge_catalog.py`, `care/*`, `audit_log.py`, `replay_guard.py`, `self_report.py`, `environment_store.py`; use explicit `close()`/`contextlib.closing`, then prove Windows TemporaryDirectory cleanup. Earlier one-off Windows-close fix did not establish all modules safe |
| **P0 ECG · [Q-0481](quests/v1/Q-0481.md)** | Windows checkout returned **404** on `/api/v1/ecg/records?subject_id=CREW-1`; Desktop monitoring displayed `no_waveform` text instead of waveform | **Later GitHub server `main.py` now includes `include_router(build_ecg_router(...))`**; previous 404 must be **retested** with authorization on that revision. Real waveform upload/storage/render and Qt ECG link still unaccepted; Q-0481 currently BLOCKED/COMPONENT_READY |
| **P0 Source registry · [Q-0052](quests/v1/Q-0052.md)** | `/api/v1/knowledge/anatomy/models` had a real approved model but `/api/v1/sources?kind=anatomy_3d_model` returned zero; `source_registry.py` expects list/id/creator instead of object/models/anatomical_id/author; symptom source SHA has only 40 hex chars | **Mismatch and 40-character field still visible on main.** Parse actual approved-model schema, calculate actual SHA-256 from source bytes, cross-check registry vs anatomy endpoint and never claim a verified provenance digest from Git blob SHA-1 |
| **P0 release config · [Q-0005](quests/v1/Q-0005.md)** | Release path tests fail on Windows for POSIX-style `/var/lib/aetherion/store.sqlite3` test value | **Path code still lacks cross-platform normalization.** Clarify intended platform-specific release policy before accepting a POSIX path on Windows; adjust fixture or validation safely and verify Windows/Posix cases. No security relaxation merely to satisfy one test |
| **P0 interview/privacy · [Q-0444](quests/v1/Q-0444.md), [Q-0445](quests/v1/Q-0445.md), [Q-0460](quests/v1/Q-0460.md), [Q-0471](quests/v1/Q-0471.md)** | `symptom_interview.py` does not consistently return `cloud_used`, `persistence_requires_consent`, `session_history`, `unknown_answers_count`; tests also disagree on `model_status` for breathing red flags | Reconcile response contract and `admin_ai_bridge.py` while preserving **consent/cloud OFF by default** and deterministic safety-stop behavior; update tests only to match the explicitly approved safety policy, never suppress a real red flag |
| **P0 OpenAPI · [Q-0016](quests/v1/Q-0016.md) / [Q-0241](quests/v1/Q-0241.md)** | `packages/contracts/openapi.json` differs from `create_app().openapi()` by a reported **83,037 characters**; missing care/knowledge/admin/sources paths | **Main contract file still has only the older core API paths** at inspection. Regenerate reproducibly from the actual registered app, run exact schema comparison and review compatibility before release |
| **P1 native images · [Q-0427](quests/v1/Q-0427.md)** | `apps/desktop/medical_image_gallery.py` sits outside the installed `src/aetherion_desktop/` package and is not wired to the native reader | **Still root-level on GitHub.** Relocate/integrate under exclusive path claim; link gallery to rights-cleared local BLOBs; Qt keyboard/zoom/pan/Windows checks, captions/alt text/licensing required |
| **P1 Atlas/installer · Desktop / [Q-0003](quests/v1/Q-0003.md)** | Standard Windows setup lacks optional `aetherion-desktop[atlas]` (`pyvista`/`pyvistaqt`), so no real 3D rendered; media tests lack `Pillow` | **`[atlas]` extra exists but default installer only installs desktop without extras.** Decide opt-in install step and verified native VTK GPU/DPI capability; declare Pillow for relevant test/runtime path and test offline installation as needed. A 3D menu/placeholder is not validated 3D |
| **P1 localization/older tests** | `tests/test_desktop_portal.py` still checks a prior hard-coded Vietnamese phrase even though Portal now uses `tr(locale,...)`; other three direct-loader tests fail because modules use relative imports | Adjust tests to bilingual semantic IDs/actual VI+EN view instead of forcing implementation to old literal; run both languages, not a single-string assertion |
| **P0 medical library · [Q-0457](quests/v1/Q-0457.md), [Q-0458](quests/v1/Q-0458.md), [Q-0459](quests/v1/Q-0459.md)** | **116/119** structured JSON records; missing CLIFF-019, CLIFF-021, CLIFF-119; **0 archived original NASA PDFs**; offline `.sqlite` was absent on Windows checkout; CLIFF-044 JPEG lacks valid EOI | Repository `audit_status.json` also records 116/119 and zero archived PDFs. **Q-0458 and Q-0459 metadata on later main say DONE/APPROVED**, but this alone cannot certify the defective JPEG or a populated bundled SQLite: a final `.sqlite` is **not present as an accessible tracked repo file** at inspection. Verify actual binary/licensing and run build/import on Windows with authentic sources; require independent review; Q-0457 remains RUNNING |
| **P0 copyright/submission · [Q-0264](quests/v1/Q-0264.md)** | Owner-reported current SHA-256 of `THIRD_PARTY_NOTICES.md` is `ff0866bf46313f9831275cae83919c52b14dc500f01f034219e4bdf6a1a9e96a` but submission notice lists old `51340c...` | **Old SHA is still present in `submission/SOURCES_AND_LICENSES.md` on GitHub.** Recompute actual bytes SHA-256 on a pinned commit; fix citation, rerun source/license test and request independent review (Quest record says DONE/APPROVED, which is not proof of current hash correctness) |
| **P1 NASA status/tests** | `audit_status.json` uses `PARTIAL_STRUCTURED_JSON_NO_PDF_ARCHIVE` while older test accepts only NO_DATA/UNVERIFIED; anatomy test expects NO_DATA even though approved-model JSON now has real meshes | Reconcile schema of truthful NASA uncertainty and current verified model availability; do not rewrite real research status to satisfy obsolete fixture assumptions |
| **P2 Watch [Q-0181–0195](quests/INDEX_181_195.md)** | `apps/watch/` is README-only in owner audit; contract test alone does not provide native Wear OS code or sensor evidence | Keep PLANNED/P2; **Mobile was outside the scope of this audit** and is not reclassified here |

### Task metadata and concurrency — differences from the downloaded 482-Quest snapshot

- **Q-0426 and Q-0427 self-dependencies have ALREADY been corrected on later GitHub main:** Q-0426 now depends only on `[Q-0421, Q-0425]`, and Q-0427 on `[Q-0423]`; both are `BLOCKED`, `review: PENDING`, `implementation_state: COMPONENT_READY`. **Do not delete dependencies again or claim `quest_board.py check` PASS until executed against a known current checkout.** This supersedes the report recommendation and the older 17:17 log entry.
- **Latest Quest claims observed:** Q-0477 BLOCKED/PENDING (crash unresolved); Q-0480 Local/Cloud chat BLOCKED/COMPONENT_READY; Q-0481 ECG BLOCKED/COMPONENT_READY; Q-0482 authorized Mission roster BLOCKED/COMPONENT_READY. Newer **Q-0483** persistent Care episode, **Q-0484** fictional five-patient 540-day demo and **Q-0485** Mission Operations view have also appeared. A component-ready or code commit is **not** independent acceptance, and fictional demo values must never be called live astronaut data.
- **Repo count observed separately, later than the submitted report:** GitHub `quests/v1/` listed **485 contiguous files (Q-0001–Q-0485)** at the scan, versus **482** in the Windows downloaded checkout. Do not copy old task totals into a live dashboard; new Quests may arrive at any time. The historical log below keeps earlier snapshots for traceability.
- **Board validator:** latest `scripts/quest_board.py` uses a dynamic contiguous count and parses multiline frontmatter lists. No reason to restore obsolete `EXPECTED_COUNT=435`; after graph correction, still run the real checker and inspect new failures.
- **Review policy:** this is a coordination audit, **not** permission to change another agent owner/lease, self-approve, downgrade DONE, or enable unsafe clinical paths. Claim exact free paths with current blob-SHA CAS, fix high-impact defects first, gather actual focused Windows/API proof and let a different reviewer approve. Prior audit dates and 640-pass results remain historically true **only for their own tested checkouts**.

---

## Owner language directive — VI / EN, mandatory for every agent (14/11/2026)

**AETHERION là app song ngữ tiếng Việt + tiếng Anh.** Không agent nào được ép ứng dụng thành "thuần Việt" hay chỉ có tiếng Anh. Mọi Quest chỉnh giao diện phải bổ sung cả `vi` và `en`, theo [AGENTS.md](AGENTS.md) và [docs/LANGUAGE_POLICY.md](docs/LANGUAGE_POLICY.md). Bản thiết kế viết tiếng Việt là mô tả, **không phải lệnh chỉ hiển thị tiếng Việt**.

- Bộ chọn ngôn ngữ của Portal và khung Desktop chính được thêm dưới `apps/desktop/src/aetherion_desktop/...`; dùng `i18n/vi.json` và `i18n/en.json`, lưu `ui/language`. **Đã có mã chuyển ngữ** cho Mission, Personal, Medical Library, NASA Explore và trình đọc CliFF, bên cạnh Portal/shell; riêng giao diện Server Admin và các tính năng mới vẫn cần rà soát. **Chưa nghiệm thu Windows thực tế/độc lập**, không tự đánh dấu toàn ứng dụng là đã hoàn tất song ngữ. Agent sửa từng màn phải nối vào cùng cơ chế, không tạo bộ ngôn ngữ riêng.
- Kho CliFF JSON lưu **nội dung tiếng Anh nguyên bản** và phải giữ nguyên; `knowledge/symptoms/ASTRA_819_REFERENCE.json` có tên và nhận định tiếng Việt cần lớp dịch tiếng Anh có thẩm định. **Không dịch đè JSON nguồn, không đổi key/ID/tier/enum**, không tự nhận bản dịch là phác đồ y khoa đã duyệt.
- Tiêu chí nghiệm thu: nhãn/nút/trạng thái an toàn của phạm vi màn được sửa phải hoạt động khi chuyển sang cả hai ngôn ngữ, và không làm đổi dữ liệu nguồn. Không lấy sự có mặt của tệp JSON làm bằng chứng đã dịch xong.

## Chính sách triển khai mới nhất — ít test, làm trực tiếp (14/11/2026)

**Lệnh của chủ dự án:** Đa số Quest chỉ cần **làm trực tiếp → kiểm tra nhanh kết quả đã làm → commit → chuyển Quest tiếp**. **Không bắt buộc tạo unit test, chạy toàn bộ CI, chụp ảnh, hay E2E cho từng Quest thường.** Các mô tả Quest cũ yêu cầu test chung áp dụng theo chính sách mới trong [AGENTS.md](AGENTS.md), không thay đổi mục tiêu hay tiêu chí tính năng.

- Giao diện, sửa UX, cấu trúc file, nghiên cứu nguồn và tài liệu: không cần test formal. Agent nghiệm thu độc lập kiểm tra kết quả thực, không đòi file test.
- Server/API/SQLite, tích hợp app và nhập nguồn: một smoke check có ích là đủ khi không có dấu hiệu lỗi.
- Lõi an toàn y khoa, bảo mật/quyền, nguồn NASA, giấy phép, 3D thực, thiết bị thật và Windows release: vẫn cần bằng chứng phù hợp, không bỏ kiểm chứng quan trọng.
- Các Quest QA/acceptance chuyên trách thực hiện kiểm thử tổng hợp; không rải nhiều bài test trùng lặp khắp mọi Quest.
- Quest có thể **bắt đầu làm trước khi phụ thuộc PASS**, miễn giữ nguyên liên kết phụ thuộc, quyền ghi tệp và chỉ nghiệm thu tích hợp khi đã đủ đầu vào.
- Reviewer khác người làm có quyền chấp thuận dựa trên diff và sản phẩm thật cho các nhiệm vụ ít rủi ro, **không yêu cầu log unit test**.

Trạng thái DONE vẫn phải phản ánh sản phẩm thực sự; giảm test **không đồng nghĩa tự động PASS**.

## Current working contract — concurrent build, independent acceptance

**Owner directive (14 Nov 2026):** `QUEUED` Quest may start **before its dependencies PASS**. Keep original `depends_on` and claim via exact file SHA with `execution_mode: PREPARE`. Implement direct code first, then focused evidence. A different agent reviews acceptance; missing dependencies prevent only **integration / final PASS**, not independent work. Do not weaken the concrete acceptance criteria in any of the currently indexed Quest records.

**Standing review Quest:** [REVIEW-0001](quests/review/REVIEW-0001.md) is separate from the numbered implementation Quest files; the live total is determined from `quests/v1/`, not a fixed value. [GitHub Actions](.github/workflows/quest-review-15m.yml) is configured to refresh its pending-review audit **on a 15-minute cron** (GitHub scheduling is best-effort, not guaranteed exactly at the minute). The workflow checks structured evidence and publishes a report; it does not automatically perform a different AI agent's semantic code review. An independently invoked reviewer follows the standing Quest to verify changed code/deliverables and resolve PASS/REWORK. No automatic acceptance without evidence.

**Useful distinction:** `status: RUNNING, execution_mode: PREPARE` allows coding; `implementation_state: COMPONENT_READY, review: PENDING` records code awaiting independent evaluation; `review: COMPONENT_APPROVED` is not final PASS; `status: DONE, review: APPROVED` is final after integration requirements are satisfied.

## Current canonical product
- AETHERION is the new canonical product/repository, evolving the earlier product vision without copying the old repository or borrowing old PASS results. **Owner-corrected design:** [DESIGN V3](docs/DESIGN_2026_11_14.md).
- **Updated target:** Native Windows app starts at the **five-card Portal**, keeps its menu horizontally above the content; Mission Control opens only on selection by an authorized user. Server Admin GUI manages local/cloud AI, devices, knowledge, LAN and optional Earth Telegram relay. Mobile/Watch are distinct clients. The five-card Qt Portal, top grouped menu and selectable animated ambience are committed as component code (Q-0437); the complete app, real Windows visual QA and AI/ECG/Server Admin remain unverified.
- Every data point is source-backed or explicitly UNKNOWN/UNVERIFIED; historical NASA records are never passed off as live astronaut vital signs.
- The hackathon **ends on November 15, 2026 at 23:59 local time**; full P2/P3 development is not required for initial submission. Use the 2026 official Project tab to submit.

## Live status commands
```bash
python scripts/quest_board.py check
python scripts/quest_board.py stats
python scripts/quest_board.py ready
python scripts/quest_board.py running
python scripts/quest_parallel_candidates.py --limit 40  # READY + QUEUED tasks
```

The index pages below cover the **initial 438-Quest baseline**, not the entire evolving backlog: 300 original tasks, 119 individual NASA CliFF source-ingestion Quests, 16 App View medical-library Quests, plus Q-0436 (design), Q-0437 (Portal), Q-0438 (theme/Settings). Additional Quests Q-0439 onward are recorded by their live `quests/v1/` files (at this scan: through Q-0485).

| Stream | Quest range | Meaning |
| --- | --- | --- |
| Foundation | [0001–0015](quests/INDEX_001_015.md) | Build, native startup, CI, packaging |
| API contracts | [0016–0030](quests/INDEX_016_030.md) | Versioned schemas and client contracts |
| Core data | [0031–0045](quests/INDEX_031_045.md) | Source identity, scope, SQLite and provenance |
| HTTP server | [0046–0060](quests/INDEX_046_060.md) | API routes, persistence, typed events |
| Mission | [0061–0075](quests/INDEX_061_075.md) | Crew-wide native Qt mission dashboard |
| Personal | [0076–0090](quests/INDEX_076_090.md) | Personal health Today view |
| Care | [0091–0105](quests/INDEX_091_105.md) | GATHER → EVALUATE → ACT → RECHECK |
| NASA science | [0106–0120](quests/INDEX_106_120.md) | Real NASA datasets, five hazards and citations |
| Body Atlas 3D | [0121–0135](quests/INDEX_121_135.md) | True native 3D anatomy and renderer evaluation |
| Encyclopedia | [0136–0150](quests/INDEX_136_150.md) | Verified 119-condition/CliFF mapping and reader |
| Guide | [0151–0165](quests/INDEX_151_165.md) | Offline scientific guide, no mandatory AI |
| Safety | [0166–0180](quests/INDEX_166_180.md) | Assistance, human reports, ACK and privacy |
| Wearable | [0181–0195](quests/INDEX_181_195.md) | Future Wear OS and genuine device proof |
| Mobile | [0196–0210](quests/INDEX_196_210.md) | Future independent Android companion |
| AI gateway | [0211–0225](quests/INDEX_211_225.md) | Optional local/cloud AI with safety boundaries |
| Devices | [0226–0240](quests/INDEX_226_240.md) | Real source/device adapter contracts |
| QA | [0241–0255](quests/INDEX_241_255.md) | Unit/API/native Windows E2E proof |
| NASA submission | [0256–0270](quests/INDEX_256_270.md) | English submission, NASA data, 30s demo, citations |
| Earth health | [0271–0285](quests/INDEX_271_285.md) | Future public-health product |
| Mars 2050 | [0286–0300](quests/INDEX_286_300.md) | Long-term research and qualification gates |

## New NASA CliFF 119 + medical image-rich SQLite Library (2026-11-14)

**OWNER PRIORITY:** Exactly **119 source Quests Q-0301–Q-0419** and **16 native desktop library Quests Q-0420–Q-0435** have been added. [119-source catalog](quests/CLIFF_119_INDEX.md) · [Library infrastructure](quests/INDEX_420_435.md).

Each source Quest must resolve its *own actual NASA CliFF 119 original link*, ingest page-anchored source text/tables/figures and find additional medically relevant, rights-cleared image assets with full file-level provenance. Target at least three relevant licensed images per article when possible, without image padding. A single offline `.sqlite` knowledge library will be rendered by the native PySide6 desktop App View with search and offline images. **No old repository may be accessed as an input.**

**Important audit:** The current rendered NASA table yielded only 118 individually named entries; Q-0419 must investigate the unresolved 119th instead of inventing data. All 119 Quests are work to do, not completed source documents. Source IDs, direct URLs and image bytes are not verified at backlog creation.

Do not mark a source Quest DONE for a URL list, no data, fabricated copy, missing license, or missing offline render proof. Agent work only starts upon actual invocation and claim.

## Initial handoff and emergency priority

At backlog creation, no Quest has been tested or accepted by these new task files. **No DONE is implied.** `READY` tasks are independently claimable after checking ownership; `QUEUED` tasks require their dependencies; `PLANNED` tasks are intentionally non-hackathon.

For a short path to a credible NASA submission, prioritize:
**Q-0001** (CI), **Q-0002** (actual Windows native boot), **Q-0016** (schema), **Q-0031** (observation provenance after schema), **Q-0047** (real observations endpoint), **Q-0061/0062** (Mission UI), **Q-0076/0077** (Personal UI), **Q-0091–0095** (Care), **Q-0106–0109** (real NASA sources), **Q-0241–0246** (tests), and **Q-0256–0265** (submission).

These are **dependencies and priorities, not parallel agents already running**. Read the actual Quest links and claim according to `AGENTS.md`.

## Animated appearance and Settings Q-0438

[Q-0438](quests/v1/Q-0438.md) implements native Qt D62 Settings: 14 vivid theme palettes with Light/Dark/Fusion, adjustable colors/fonts/contrast/motion, animated owl/tree/sun/moon preview, VI/EN settings, connection/notifications/privacy/accessibility tabs and responsive top navigation. Current main.py preserves the existing NASA Explore and localized Portal. Source commits are recorded in the Quest. **Component-ready / Windows Qt visual acceptance and independent review PENDING.** Server Admin, true Mobile/Watch, full i18n and clinical capabilities are not claimed.

## Native Portal implementation Q-0437

[Q-0437](quests/v1/Q-0437.md) records real native Qt Portal/theme/menu commits. Five routes and persisted theme preferences are implemented at source level; its `BLOCKED` / `review: PENDING` reflects missing real Windows Qt visual check and independent acceptance. Existing Mission/Personal/Library integrations are preserved; unavailable AI/ECG/3D functions disclose their status. Any test counting scripts may require a separate compatibility adjustment for 437 Quest records.

## Owner design reconciliation Q-0436

[Q-0436](quests/v1/Q-0436.md) updates the canonical product blueprint, menu/screens and Server AI/network requirements. **This is a documentation correction only**, not Windows UI implementation or independent PASS. Existing code Quest writers must follow the new Portal-first contract when integrating. Review by a different agent is mandatory.

## Design and science references

- [Current design 2026-11-14](docs/DESIGN_2026_11_14.md)
- [Official NASA 2026 challenge](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/)
- [NASA 2026 event schedule](https://www.spaceappschallenge.org/2026/)

## Earlier Platform Test & Remediation Audit (historical snapshot, 2026-11-14)

Full test/runtime verification across **Server**, **Desktop**, **Mobile**, **Watch**, and **CI/Tooling** is recorded in [docs/PLATFORM_TEST_AUDIT_2026_11_14.md](docs/PLATFORM_TEST_AUDIT_2026_11_14.md):

- **Server (`apps/server`):** Boots and serves `/health` & `/api/v1/auth/login`, but **fails 6 validation test suites** (`TypeError: Object of type ValueError is not JSON serializable` in `apps/server/src/aetherion_server/main.py:187` under Pydantic v2) and **fails `scripts/smoke_server.py`** (`GET /api/v1/observations` missing `include_non_live=true` for `scope=engineering_test`). Server Control GUI (`Q-0436`) is not yet implemented.
- **Desktop (`apps/desktop`):** Headless `PySide6` `AetherionWindow` boots and switches 8 pages (`PortalPage`, `MissionControlPage`, `AuthorizedPersonalTodayPage`, `MedicalLibraryPage`, 4 placeholders). Body Atlas, Explore, Care Journey, and Medical Guide remain placeholder `QWidget`s; `medical_image_gallery.py` & `medical_source_audit.py` sit outside `src/aetherion_desktop/`; Windows EXE (`Q-0010`/`Q-0011`) and live Windows boot (`Q-0002`) remain unverified.
- **Mobile (`apps/mobile`):** `README.md` only — no Android/mobile client code yet (`Q-0196`–`Q-0210`, currently `PLANNED` / `P2`).
- **Watch (`apps/watch`):** `README.md` only — no Wear OS/watch client code yet (`Q-0181`–`Q-0195`, currently `PLANNED` / `P2`).
- **CI / Data / Quest Tooling:** `scripts/quest_board.py` crashes on `Q-0436.md` multi-line YAML (`EXPECTED_COUNT=435` vs 436); 9 `test_encyclopedia_*.py` / `test_guide_*.py` modules pass under `pytest` (64 passed) but fail `unittest` in `.github/workflows/server-tests.yml` because `pytest` is not installed; `tests/test_cliff_044_sepsis.py` fails with `ImageRightsError: JPEG missing end marker` (`Q-0344`); `submission/SOURCES_AND_LICENSES.md` has a stale SHA-256 for `THIRD_PARTY_NOTICES.md` (`Q-0264`).


## Windows 2026-11-14 15:54–16:00 ICT — owner-supplied test follow-up

**Evidence boundary:** Results below come from a Windows PowerShell test report supplied by the project owner for local checkout d:\hoc\khoahoc2\AETHERION-main (Python 3.13.14; FastAPI 0.143.0; Pydantic 2.12.4; Uvicorn 0.54.0; httpx 0.28.1). This Quest-log edit does **not** rerun those Windows commands or authenticate their console logs; exact tested Git SHA and raw tracebacks were not supplied. Other agents continue committing, so this is a **historical test snapshot**, not a claim about every later commit.

**Quest-count caveat:** The supplied report counted **436** Quests and recorded DONE 204 / QUEUED 107 / PLANNED 90 / BLOCKED 19 / RUNNING 13 / READY 2 / STALE 1 (sum 436). The current canonical backlog is **437** Quests (Q-0001–Q-0437). Do not copy the 436 snapshot into current Quest states; live statuses belong exclusively to individual files under quests/v1.

### Owner-reported Windows test outcomes

| Reported action | Outcome and evidence |
| --- | --- |
| python -m unittest discover -s tests -v | **FAIL: 606 tests in 72.069s; 3 failures and 63 errors** |
| python scripts/lint_python.py | **PASS:** 334 Python files, 0 errors; Python 3.13 invalid-escape SyntaxWarnings reported in scripts/quest_review_queue.py |
| python scripts/validate_nasa_registry.py | **PASS:** 5 source-registry entries |
| python scripts/audit_nasa_truthfulness.py | **PASS:** 0 violations reported |
| Server configuration and TestClient | **PASS (limited):** /health 200; /ready 200; unauthenticated /api/v1/observations 401 |
| python scripts/verify_submission_team.py | **BLOCKED:** no verified official public team page; exit 1 |
| python scripts/quest_board.py check and stats | **FAIL:** multiline frontmatter in Q-0436 cannot be parsed; script still expects 435 Quest records |
| python scripts/release_readiness.py --scope demo | **NOT READY:** release_authorized=false; exit 2 |
| python scripts/smoke_server.py | **FAIL:** reads engineering_test observation without include_non_live=true; default API query correctly hides fixture data |
| python scripts/audit_cliff_119.py | **FAIL:** NOT_IMPORTED, zero verified original PDFs, no manifest |
| python scripts/audit_cliff119_library.py | **FAIL:** zero imported articles, no manifest or final SQLite |
| scripts/setup_windows.ps1 | **FAIL on reported Windows host:** hard-coded py -3.11 launcher unavailable, preventing venv/PySide6 installation |

**Failure families reported (sum 66 = 3 failures + 63 errors):** 49 PermissionError [WinError 32] cases when cleanup meets open SQLite handles; 9 modules requiring pytest under unittest; 4 quest-board/Windows-runtime-path cases; 2 Pydantic-v2 request-validation HTTP-422 serialization crashes; 1 CliFF-044 JPEG end-marker error; 1 stale SHA-256 assertion for THIRD_PARTY_NOTICES.md. Root-cause categories should be confirmed against exact raw tracebacks before bulk fixes.

### Remediation queue — prioritized and mapped to Quest records

| Priority | Quest(s) / exact area | Proposed implementation and verification |
| --- | --- | --- |
| P0 | [Q-0001](quests/v1/Q-0001.md), [Q-0241](quests/v1/Q-0241.md), scripts/quest_board.py | Support multiline YAML list metadata; update EXPECTED_COUNT from 435 to the **current 437**; verify check/stats/ready on latest main; align CI dependency installation with nine pytest-only modules and add focused Windows SQLite-close checks |
| P0 | [Q-0047](quests/v1/Q-0047.md), apps/server/src/aetherion_server/main.py, scripts/smoke_server.py | Sanitize exc.errors() before JSON serialization of HTTP 422; include engineering_test fixtures only when explicitly queried with include_non_live=true; close all SQLite connections before Windows TemporaryDirectory removal. Request independent re-review of earlier DONE/APPROVED acceptance rather than silently changing its status |
| P0 | [Q-0002](quests/v1/Q-0002.md), [Q-0003](quests/v1/Q-0003.md), scripts/setup_windows.ps1 | Discover a valid supported Python executable without assuming py launcher; run actual Qt Windows start and document its observed result; do not assert EXE PASS from source alone |
| P0 | [Q-0264](quests/v1/Q-0264.md), submission/SOURCES_AND_LICENSES.md | Recompute digest of THIRD_PARTY_NOTICES.md from actual bytes, repair stale attribution SHA, rerun the focused attribution check, request independent re-review |
| P1 | [Q-0344](quests/v1/Q-0344.md), CliFF-044 Sepsis JPEG | Audit genuine bytes, JPEG EOI, license and media SHA; avoid weakening the image validator to admit truncated media, request independent clinical/rights re-review |
| P0 | [Q-0436](quests/v1/Q-0436.md), [Q-0437](quests/v1/Q-0437.md), Desktop | Reconcile existing five-card Portal with V3 menu, real content versus placeholder Body Atlas/Explore/Care/Guide, native animated theme, Server Control GUI and Windows EXE/real session acceptance |
| P2 / not implemented in reported snapshot | [Mobile](quests/INDEX_196_210.md) and [Watch](quests/INDEX_181_195.md) | README-only in test report; preserve planned phase and do not claim released APK/Wear OS client without real artifacts |

**Historical GitHub source spot-check during the earlier documentation update (superseded by later commits):** scripts/quest_board.py had EXPECTED_COUNT=435 and colon-only frontmatter parsing; .github/workflows/server-tests.yml installs server then runs unittest without explicitly installing pytest; scripts/setup_windows.ps1 still invokes py -3.11; the server HTTP-422 handler still sends raw exc.errors(); submission/SOURCES_AND_LICENSES.md still shows the earlier notices hash prefix 51340c. These are **source observations only**, not a reproduced Windows test run.

**Coordination:** These are remediation proposals and review requests, NOT automatic Quest state changes. In particular Q-0047, Q-0264 and Q-0344 retain their actual current metadata until a separate agent with exclusive file ownership reproduces/fixes/reviews the regression. CLAIM via current blob SHA and scoped lease; record actual smoke results and commit; leave review PENDING or REWORK_REQUIRED until an independent reviewer checks it. Source integrity, hardware evidence and final NASA submission requirements are not waived.



## Windows PowerShell retest — owner report 2026-11-14 17:17 ICT

**Provenance / time boundary:** Owner-supplied Windows PowerShell retest completed **2026-11-14 17:17 UTC+7** in a local `.venv` with **Python 3.13.14**, PySide6 6.12.0, FastAPI 0.162.7, Pydantic 2.14.3, Uvicorn 0.54.0, httpx 0.28.1 and pytest 9.2.0. These are **reported actual Windows results from the owner's checkout**, not a Windows run independently executed by the agent editing this document; the exact tested checkout SHA, console transcripts and GUI capture hashes were not attached. This retest **supersedes the earlier 15:54–16:00 Windows failure snapshot for that tested checkout**, not for all future main commits.

### Before / after — Windows retest

| Check | Earlier Windows run | Owner-reported retest at 17:17 ICT |
| --- | --- | --- |
| `.venv\\Scripts\\python.exe -m pytest tests -q` | 606 tests: 3 failures, 63 errors (via unittest) | **640 passed, 1 failed**, plus **71 subtests passed**; the remaining reported failure is `tests/test_quest_board.py::test_count_and_dependencies` due to **Q-0426 and Q-0427 self-dependencies**. Different runner/suite, so counts are not a like-for-like regression percentage |
| `scripts/lint_python.py` | PASS with five Python 3.13 SyntaxWarnings | **PASS: 336 files, 0 errors, 0 warnings** |
| `scripts/validate_nasa_registry.py` / `scripts/audit_nasa_truthfulness.py` | PASS | **PASS: 5 registry items** / **PASS: 0 violations** |
| `python -m aetherion_server.runtime_config --check` | PASS | **PASS:** development, loopback `127.0.0.1:8765` |
| `scripts/smoke_server.py` | FAIL: default query hides engineering-test fixtures | **PASS:** default live query excludes `engineering_test`; `include_non_live=true` retrieves one expected fixture |
| Actual Windows PySide6 + Uvicorn | PySide6 install blocked, Qt `NoError` check buggy | **PASS (shell-level):** setup script created `.venv`; native Portal with five cards opened; eight pages navigable; live `/health` showed connected |

**Server status (reported):** Independent API process supports health/readiness, auth/login, authorized observations POST/GET, idempotent replay (201 then 200), unauthorized/forbidden responses (401/403), and JSON 422 after validation serialization fix. Windows SQLite connections were explicitly closed, reportedly eliminating the earlier **49 WinError 32** temporary-file cleanup failures. **Server Control GUI S00–S15 remains absent**, including admin Local AI, cloud key management, LAN, Telegram Earth relay, users/devices/backup.

**Desktop status (reported):** Native **five-card Portal-first** and top horizontal menu work on Windows with PySide6 6.12.0; Mission Control, Personal Today, Medical Library and other page slots can be reached, and local server health reports connected. `medical_image_gallery.py` and `medical_source_audit.py` were moved into the native package. At that tested checkout, Body Atlas, Explore, Care and Guide remained placeholder `QWidget` views, the AI card displayed an unavailable notice, full V3 submenu/theme animation had not been demonstrated, and no Windows EXE had been built/accepted. **Do not confuse navigable placeholder slots with implemented user journeys.** Later main changes (including appearance/localization Quests) require new inspection; this report does not negate them.

**Mobile and Watch:** Shared backend event/idempotency/alert contract tests reported **7/7 PASS**. `apps/mobile/` and `apps/watch/` were README-only in the tested checkout: **no native mobile APK or Wear OS sensor client**; relevant Q-0196–Q-0210 and Q-0181–Q-0195 remain PLANNED/P2 unless separately authorized and implemented.

**CliFF / NASA / submission:** This retest does **not** verify 119 original PDFs or an accepted offline SQLite library; CliFF audit remains **NOT_IMPORTED / 0 of 119 verified** in the cited test report. `verify_submission_team.py` remains `BLOCKED_UNVERIFIED` until a real NASA team page URL is supplied. Do not report a completed medical library or a submitted official Project tab.

### Outstanding board defect and Quest handoff

- **P0 task-graph correction:** [Q-0426](quests/v1/Q-0426.md) still declares `depends_on: [Q-0421, Q-0425, Q-0426]`; [Q-0427](quests/v1/Q-0427.md) still declares `depends_on: [Q-0423, Q-0427]` on GitHub when this update was prepared. Correct the **self-referential entries only** under an exclusive, scoped ownership claim; retain `[Q-0421, Q-0425]` and `[Q-0423]` respectively. Preserve pending Qt integration/Windows evidence and distinct reviewer requirement — a passing Quest-board check is **not** medical-library acceptance. Related [issue #5](https://github.com/huyng0699-arch/AETHERION/issues/5).
- **Board implementation update already on GitHub:** `scripts/quest_board.py` has been revised from hard-coded `EXPECTED_COUNT=435` to a contiguous dynamic count and now parses block-style YAML lists. **Do not reapply the obsolete parser/count fix.** The new test report isolates the two still-cyclic Quest records.
- **Previously reported fixes needing independent review:** [Q-0047](quests/v1/Q-0047.md) (422 handler, SQLite close, smoke), [Q-0264](quests/v1/Q-0264.md) (third-party notices SHA), [Q-0344](quests/v1/Q-0344.md) (JPEG trailer and provenance), [Q-0001](quests/v1/Q-0001.md)/[Q-0241](quests/v1/Q-0241.md) (pytest CI), [Q-0002](quests/v1/Q-0002.md)/[Q-0003](quests/v1/Q-0003.md) (actual Windows setup/Portal/server connection). Existing individual Quest `DONE/APPROVED` status must be reviewed against **actual changed artifacts**, not silently overridden or reaffirmed by this navigational document.
- **Current source spot checks:** `main.py` contains a `jsonable_encoder(... custom_encoder={Exception: str})` in the HTTP 422 handler; `scripts/smoke_server.py` includes `include_non_live=true`; `scripts/setup_windows.ps1` probes supported installed Python versions; `.github/workflows/server-tests.yml` installs pytest and runs focused pytest suites; the Desktop main now contains Portal-first and the explicit `QNetworkReply.NetworkError.NoError` check. **One discrepancy:** the latest inspected `submission/SOURCES_AND_LICENSES.md` still lists the old `THIRD_PARTY_NOTICES.md` hash beginning `51340c...`, despite the owner's report that this was fixed in their Windows checkout. Reconcile by computing the actual current file hash from bytes and commit the corrected notice separately. Source inspection is **not** a rerun of the owner's Windows pytest suite.
- **Backlog concurrency:** The repository evolves during testing. At this edit's GitHub directory scan there were **479 contiguous Quest files (Q-0001–Q-0479)**, superseding the historical 436/437/438 counts. Counts can change again; per-Quest frontmatter and fresh directory scans are authoritative. Keep `PLANNED` P2 mobile/watch tasks untouched.

**Disposition:** Keep the 17:17 Windows retest as **owner-reported evidence of substantial improvement**, with **one reported failing test** at that checkout. Fix the two self-dependencies under scoped ownership, rerun `pytest tests -q` / `quest_board.py check` at a known Git commit, save actual PASS evidence and request independent review. Do not label the whole project PASS from this report.


Review owner and current state **on GitHub at HEAD** before each task claim. This file is not a daemon or automatic task runner.

