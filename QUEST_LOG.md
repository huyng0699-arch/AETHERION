# AETHERION — Quest control board

**Scope:** 438 Quest specifications on `main`, **Q-0001 through Q-0438**. Q-0436 updates the owner design; Q-0437 implements the native Portal shell; Q-0438 adds light/dark/fusion visual themes and the animated D62 Settings page. All retain their independent-review requirements. Each task's live metadata is stored **only in its own `quests/v1/Q-XXXX.md`**. This root file is navigational and does not claim task completion.

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
- Các Quest QA/acceptance chuyên trách thực hiện kiểm thử tổng hợp; không rải nhiều bài test trùng lặp khắp 435 Quest.
- Quest có thể **bắt đầu làm trước khi phụ thuộc PASS**, miễn giữ nguyên liên kết phụ thuộc, quyền ghi tệp và chỉ nghiệm thu tích hợp khi đã đủ đầu vào.
- Reviewer khác người làm có quyền chấp thuận dựa trên diff và sản phẩm thật cho các nhiệm vụ ít rủi ro, **không yêu cầu log unit test**.

Trạng thái DONE vẫn phải phản ánh sản phẩm thực sự; giảm test **không đồng nghĩa tự động PASS**.

## Current working contract — concurrent build, independent acceptance

**Owner directive (14 Nov 2026):** `QUEUED` Quest may start **before its dependencies PASS**. Keep original `depends_on` and claim via exact file SHA with `execution_mode: PREPARE`. Implement direct code first, then focused evidence. A different agent reviews acceptance; missing dependencies prevent only **integration / final PASS**, not independent work. Do not weaken the concrete acceptance criteria in any of the 438 Quest records.

**Standing review Quest:** [REVIEW-0001](quests/review/REVIEW-0001.md) is separate from the 437 numbered implementation tasks. [GitHub Actions](.github/workflows/quest-review-15m.yml) is configured to refresh its pending-review audit **on a 15-minute cron** (GitHub scheduling is best-effort, not guaranteed exactly at the minute). The workflow checks structured evidence and publishes a report; it does not automatically perform a different AI agent's semantic code review. An independently invoked reviewer follows the standing Quest to verify changed code/deliverables and resolve PASS/REWORK. No automatic acceptance without evidence.

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

The index pages below are initial listings; individual Quest status is authoritative. There are **438** tasks: 300 original tasks, 119 individual NASA CliFF source-ingestion Quests, 16 App View medical-library Quests, **Q-0436** (design), **Q-0437** (Portal), **Q-0438** (immersive theme and Settings).

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

## Platform Test & Remediation Audit (2026-11-14)

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

**Current GitHub source spot-check during documentation update:** scripts/quest_board.py still has EXPECTED_COUNT=435 and colon-only frontmatter parsing; .github/workflows/server-tests.yml installs server then runs unittest without explicitly installing pytest; scripts/setup_windows.ps1 still invokes py -3.11; the server HTTP-422 handler still sends raw exc.errors(); submission/SOURCES_AND_LICENSES.md still shows the earlier notices hash prefix 51340c. These are **source observations only**, not a reproduced Windows test run.

**Coordination:** These are remediation proposals and review requests, NOT automatic Quest state changes. In particular Q-0047, Q-0264 and Q-0344 retain their actual current metadata until a separate agent with exclusive file ownership reproduces/fixes/reviews the regression. CLAIM via current blob SHA and scoped lease; record actual smoke results and commit; leave review PENDING or REWORK_REQUIRED until an independent reviewer checks it. Source integrity, hardware evidence and final NASA submission requirements are not waived.


Review owner and current state **on GitHub at HEAD** before each task claim. This file is not a daemon or automatic task runner.

