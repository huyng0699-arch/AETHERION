# Thư mục kiểm chứng phần việc chưa đồng bộ & đối soát trước đồng bộ / Unsynchronized Work & Pre-Sync Verification Ledger (2026-11-14)

**Mục đích / Purpose:** Theo yêu cầu của chủ dự án (`image.png`), thư mục này lưu toàn bộ danh mục phần việc chưa đồng bộ giữa nhánh `main`, các PR mở (`#9`, `#10`, `#11`) và gói kiểm chứng Windows (`up.zip`, SHA-256 `3fb9e6c37672424dfb1d64caa55a1225fe26d4b7eedc57ac3f28de67497432be`), **kèm đầy đủ kết quả kiểm chứng đo trực tiếp TRƯỚC KHI thực hiện hợp nhất phiên bản**.

---

## 1. Ảnh chụp & bằng chứng kiểm chứng TRƯỚC KHI đồng bộ phiên bản (Baseline `origin/main` `5873f95` / `9bf4158`)

### 1.1 Ảnh chụp màn hình hiện trạng trước đồng bộ (`5873f95`)
- [presync_5873f95_login.png](presync_5873f95_login.png): Chụp trực tiếp `AetherionWindow` trên `origin/main` (`5873f95`, Linux `QT_QPA_PLATFORM=offscreen`, PySide6 `6.12.0`, `1360×850`) trước khi ghép bất kỳ bản vá nào từ `up.zip`, PR `#9` hoặc PR `#11`. Xác nhận màn hình khởi đầu là `LoginPage` song ngữ (`Q-0487`).
- [q0486_smoke_preview.png](q0486_smoke_preview.png): Kết quả render component `TelemetryPlot` nhập từ PR #9 (`Q-0486_SMOKE_OK records=15 plotted=14 table=15 gap_pairs=10 colors=73`).
- Danh mục SHA-256 đầy đủ 83 tệp trong `up.zip` + 7 tệp PR #9/PR #11 so với `5873f95`: [UP_ZIP_INVENTORY.json](UP_ZIP_INVENTORY.json).

### 1.2 Bảng kết quả kiểm thử đo trực tiếp TRƯỚC KHI đồng bộ (`5873f95` / `9bf4158`)

| Hạng mục / Check | Lệnh chạy thực tế (Pre-sync) | Kết quả đo được / Observed Pre-Sync Result | Ghi chú / Root Cause |
| --- | --- | --- | --- |
| Quest Ledger Integrity | `python scripts/quest_board.py check` | **FAIL (`exit 1`)** | `Expected contiguous Q-0001..Q-0486; missing=['Q-0486'], extra=['Q-0487']` (do `Q-0486` kẹt ở PR #9 trong khi `Q-0487` đã lên `main`). |
| Python Syntax & Indentation | `python scripts/lint_python.py` | **PASS** (`495` files, `0` errors) | Sạch lỗi cú pháp Python trên `main`. |
| Song ngữ VI/EN Catalog | `python scripts/audit_bilingual.py` | **PASS** (`761 VI / 761 EN`) | Khóa `personal.metricSource` vẫn bị tráo chuỗi hiển thị ở `HEAD` (chưa đồng bộ bản sửa từ `up.zip`). |
| NASA Registry & Truthfulness | `python scripts/validate_nasa_registry.py` & `audit_nasa_truthfulness.py` | **PASS** (`118` records, `0` violations) | Trung thực `118/119 PARTIAL`; thiếu `CLIFF-119` ở thượng nguồn. |
| Toàn bộ pytest (`301` file, subprocess cô lập) | `QT_QPA_PLATFORM=offscreen pytest -q tests/test_*.py` | **287 PASS / 14 FAIL** | Danh sách 14 lỗi xem chi tiết Mục 1.3. |
| Mobile TypeScript & Web Bundle (`apps/mobile`) | `npm --prefix apps/mobile ci` → `run typecheck` → `run export:web` | **PASS** (`659` pkg, `0` TS errors, `434` Web modules) | Đồng bộ `2787a6d` đã chạy ổn định trên Expo Web/TS; thiết bị Android/LAN vật lý chưa thử. |
| Wearable Watch (`apps/watch/`) | Kiểm tra thư mục | **`PLANNED ONLY`** | Chỉ có `apps/watch/README.md`, chưa có mã nguồn. |

### 1.3 Chi tiết 14 bài test bị FAIL trước khi đồng bộ (trên `9bf4158`/`5873f95`)
1. `tests/test_quest_board.py` — Thiếu `Q-0486`, dư `Q-0487`.
2. `tests/test_contracts.py` — `packages/contracts/openapi.json` chỉ có 10 path cũ trong khi FastAPI `create_app().openapi()` có 45 path.
3. `tests/test_cliff_044_sepsis.py` — `scripts/medical_image_rights.py:114` từ chối JPEG hợp lệ có khối metadata Samsung `SEFT` sau EOI `\xff\xd9`.
4. `tests/test_cliff_021_source_audit.py` — Kỳ vọng slot cũ bị chặn trước `Q-0457`.
5. `tests/test_nasa_cliff_119_status.py` — `audit_status.{json,md}` vẫn ghi `116/119 NO_DATA` thay vì `118/119 PARTIAL_STRUCTURED_JSON_NO_PDF_ARCHIVE`.
6. `tests/test_cliff_sqlite_library_build.py` — File SQLite cục bộ `*.sqlite` bị `.gitignore` bỏ qua nên chưa build sẵn tại môi trường sạch.
7. `tests/test_anatomy_catalog_api.py` — `test_empty_repo_catalog_returns_no_data` đọc `knowledge/anatomy/approved_models.json` thật trên repo.
8. `tests/test_desktop_portal.py` — Kiểm tra chuỗi tĩnh trước khi chuyển vào `i18n/vi.json` và trước `LoginPage`.
9–14. 6 bộ E2E Desktop (`test_desktop_qt_startup_e2e.py`, `test_offline_cold_start_e2e.py`, `test_care_back_resume_episode_e2e.py`, `test_main_menu_controls_audit.py`, `test_mission_to_personal_identity_e2e.py`, `test_personal_responsive_layout_e2e.py`): Lỗi `DeprecationWarning` từ `setTimeSpec(Qt.TimeSpec.UTC)` trong `mission_ops_home.py`, tham chiếu giao diện `portal_page` cũ, và chưa tương thích luồng `LoginPage` + `StartupRuntime` (`Q-0487`).

---

## 2. Danh mục phần việc chưa đồng bộ & xung đột đã phát hiện (Pre-Merge Triage)

| Nguồn chưa đồng bộ / Unsynced Source | Số file / Nội dung | Điểm xung đột & lỗi phát hiện trước khi đồng bộ / Conflicts & Defects Found | Chiến lược hợp nhất an toàn / Safe Reconciliation Plan |
| --- | --- | --- | --- |
| **PR #9 (`codex/q0486-native-telemetry-plot`)** | 4 file độc lập (`Q-0486.md`, `telemetry_plot.py`, `scripts/smoke_telemetry_plot.py`, workflow) | Lease `13:08Z` đã hết hạn; chưa nhập vào `main` gây đứt chuỗi `Q-0486`. | Nhập 4 file sạch, giải phóng lease -> `BLOCKED / PENDING`, giữ nguyên `owner` & `depends_on: [Q-0477]`. |
| **`up.zip` (gói Windows 2026-11-14)** | 83 file (`11` NEW gồm 7 ảnh `windows-visual-qa` + 2 bằng chứng `Q-0430` + báo cáo Windows + `sqlite_compat.py`; `71` DIFF; `1` SAME) | Gói được tạo **trước** các commit `2787a6d`, `Q-0261`, `Q-0096`, `Q-0487`. Chép đè mù quáng sẽ làm **mất** `LoginPage`, `StartupRuntime`, `GET /api/v1/subjects`, bản sửa `architecture_diagram` mới (`Q-0261`), và `README.md` của `up.zip` ghi nhầm 2 tên route (`/assistant/ask`, `/auth/session`). | Gộp 70+ file an toàn (`sqlite_compat`, `medical_image_rights`, `audit_status`, `anatomy_handoff`, `personal_visual`, `atlas3d`, `ecg_page`, `medical_library`, `native_workspaces`, `i18n`, PowerShell, QA Windows); **giữ `HEAD`** cho `Q-0261` (`submission/ARCHITECTURE_DIAGRAM.md`, `tests/test_submission_architecture_diagram.py`, `Q-0261.md`); **tạo lại** `openapi.json` trực tiếp từ `create_app().openapi()` (45 path gồm `/api/v1/subjects`) + sửa đúng 45 route trong `packages/contracts/README.md`. |
| **PR #10 (`import/windows-tested-fixes-20261114`)** | 33 file nháp Windows sớm | Là tập con cũ hơn `up.zip` (chưa có 7 ảnh PNG và các bản sửa cuối ngày 14/11). | Không merge trùng; dùng `up.zip` đầy đủ và giữ lại `Q-0096` fail-closed trên `HEAD`. |
| **PR #11 (`agent/q0485-openmct-visual-20261115`)** | `mission_ops_home.py`, `scripts/render_q0485_ui.py`, workflow | **Phát hiện lỗi crash trên PR #11 trước khi gộp:** dòng 1418 trong `set_visuals()` vẫn gọi `self.utc_chart.set_series(...)` (đã xóa khi đổi `ReportedBars` → `UtcSamplePlot`), gây `AttributeError` khi đổi theme/mode! Ngoài ra PR #11 làm mất `QTimeZone.utc()`, route `care_guide`, và sửa tràn cột Inspector của `up.zip`. | Hợp nhất 3 chiều `mission_ops_home.py` = `up.zip` (`QTimeZone.utc()`, `care_guide`, Inspector layout, `_browse_selected`) + `PR #11` (`UtcSamplePlot` với `index_offset`, clamp nhãn UTC, `demo` trên cây Browse, ẩn Time Conductor ở Monitor) + **sửa `set_visuals()` sang `set_points(..., index_offset=...)`**; cập nhật `scripts/render_q0485_ui.py` chạy được qua `LoginPage` (`Q-0487`). |
| **Commit `Q-0487` trên `main` (`09982de..b1e4a33`)** | `main.py`, `startup_runtime.py`, `login_page.py`, `start_desktop.ps1` | `main.py` trên `HEAD` thiếu `closeEvent` gọi `first_run_runtime.stop()` (dễ rò `QThread`/`QProcess` khi đóng cửa sổ), thiếu `shiboken6.isValid`, timeout `2500ms`/`Connection: close`, `time_range_changed` -> `sync_utc_window`, và route `care_guide`. | Giữ nguyên 100% luồng `LoginPage` + `StartupRuntime` (`Q-0487`), ghép bổ sung các sửa lỗi vòng đời từ `up.zip`, và giữ `care_guide` truy cập được ngoại tuyến trong khi các route hồ sơ vẫn yêu cầu đăng nhập. |

| **Commit `98e92f5` trên `origin/main` (`huyng0699-arch`)** | 22 tệp (`login_page.py`, `main.py`, `apps/server/*`, `apps/mobile/*`, 5 script `verify_*`) | Đổi `login_page.demo_requested` sang `show_hackathon_demo` (NASA briefing); thêm `LoginPage.set_visuals`; chặn wildcard `*` ở `SubjectIn`/`/api/v1/subjects`; thêm `export:android`/`export:android:js` và phân trang `MonitorScreen`. **Phát hiện lỗi compile TS2554 thực tế khi chạy `tsc --noEmit`:** `MonitorScreen.tsx:34` gọi `getObservations(subjectId, token, cursor)` trong khi `apps/mobile/src/api/health.ts` chỉ nhận 2 tham số. | Rebase toàn bộ phần đồng bộ lên trên `98e92f5`, giữ nguyên luồng Login Demo → NASA briefing & Operations Demo → `SIMULATED`, **vá `apps/mobile/src/api/health.ts` hỗ trợ `cursor?: string \| null`**, đồng bộ `test_offline_cold_start_e2e.py`, `test_startup_runtime_q0487.py`, `scripts/render_q0485_ui.py` theo cả 2 luồng Demo. |

---

## 3. Nhật ký kiểm chứng sau đồng bộ (Post-Sync Verification — đo trực tiếp trên bản hợp nhất sau `98e92f5`)

### 3.1 Kết quả đo trực tiếp sau hợp nhất (Linux VM + Offscreen Qt `6.12.0` + Python `3.11` + Node `24`)

| Bề mặt / Kiểm tra | Lệnh thực tế | Kết quả đo được (Observed Post-Sync) | Ghi chú trung thực |
| --- | --- | --- | --- |
| Quest Ledger Integrity | `python scripts/quest_board.py check` | **PASS (`488` files, contiguous `Q-0001..Q-0488`, acyclic)** | Đã nối mạch `Q-0486` (PR #9) và `Q-0488`; giữ nguyên lease `Q-0261`, `Q-0487`; không tự duyệt `DONE`/`APPROVED`. |
| Python Syntax & Indentation | `python scripts/lint_python.py` | **PASS (`502` Python files, `0` errors)** | Sạch lỗi cú pháp trên toàn bộ mã nguồn Python. |
| Song ngữ VI/EN UI Catalog | `python scripts/audit_bilingual.py` | **PASS (`761 VI / 761 EN` UI keys)** | Đã sửa tráo chuỗi `personal.metricSource` và giữ nguyên bản gốc NASA + từ vựng triệu chứng tiếng Việt. |
| NASA Registry & Truthfulness | `validate_nasa_registry.py` & `audit_nasa_truthfulness.py` | **PASS (`118` CliFF records, `5` registry items, `0` violations)** | Trung thực `118/119 PARTIAL` (thiếu `CLIFF-119`), `clinical_rules_validated=false`. |
| Offline CliFF SQLite Pack | `library_schema.py` build & verify (`393,748,480` B, gitignored) | **PASS (`118/119` complete articles, `366` assets, `321` approved, `0` hash mismatches)** | `integrity="ok"`, `foreign_key_errors=0`, `missing_originals=["CLIFF-119"]`, `library_complete=false`. |
| Toàn bộ Python `pytest` Suite | `QT_QPA_PLATFORM=offscreen python -m pytest -q tests/test_*.py` (302 subprocess cô lập) | **PASS (`total=302`, `passed=302`, `failed=0`)** | Xử lý sạch 14/14 lỗi trước đồng bộ + bổ sung `tests/test_startup_runtime_q0487.py` (3 test PASS). |
| Server FastAPI + Loopback Auth Smoke | `python scripts/smoke_server.py` | **PASS** | SQLite replay idempotent, tách biệt live/test (`verification.sqlite3` riêng biệt). |
| Native Telemetry Plot (`Q-0486`) | `QT_QPA_PLATFORM=offscreen python scripts/smoke_telemetry_plot.py --output /tmp/q0486_recheck.png` | **PASS (`Q-0486_SMOKE_OK records=15 plotted=14 table=15 gap_pairs=10 colors=73`)** | Xem preview tại [q0486_smoke_preview.png](q0486_smoke_preview.png). |
| Native Desktop Flow & Offscreen UI | `scripts/verify_native_login.py` + `scripts/render_q0485_ui.py --output-dir docs/qa/unsynced_20261114/postsync_preview` | **PASS (`verify_native_login`: `8/8` 100%; `9` PNG rendered & visually inspected)** | Đã xác nhận `LoginPage` (`Q-0487`), Login Demo → NASA briefing (`98e92f5`), Operations Demo → `SIMULATED` 5×540 (`31,610` rows), đổi Light/Dark theme `UtcSamplePlot.set_points`, single conductor ở Monitoring, `1040×650`/`1360×850`/`1600×900`. |
| Mobile TypeScript, Expo Bundles & OpenAPI | `npm --prefix apps/mobile run typecheck` + `export:web` + `export:android:js` + contract parity | **PASS (`0` TS errors sau khi vá `health.ts`; `434` Web modules; `707` Android JS modules; `16/16` endpoint khớp OpenAPI `45` paths)** | Không cần sửa lockfile mới trên npm registry offline; `apps/mobile/dist*` giữ gitignored. |
| Mobile State / Live Client / ACL Verifiers (`98e92f5`) | `verify_mobile_state.mjs` + `verify_mobile_web.mjs --api-only` + `verify_mobile_clients.mjs` + `verify_mobile_acl.py` | **PASS (`14/14` + `18/18` + `9/9` + `6/6` = `47/47` 100%)** | Xác thực wildcard `*` chặn đúng, cursor pagination không lặp bản ghi, cross-user ACL trả `403`/`401`, Expo font & `/api/v1/*` phục vụ sạch. |
| Wearable Watch (`apps/watch/`) | Kiểm tra thư mục & tài liệu | **`PLANNED ONLY`** | Chỉ có [apps/watch/README.md](../../../apps/watch/README.md); chưa có mã nguồn Wear OS hay cảm biến thật. |
| Submission Team & Release Readiness | `verify_submission_team.py` & `release_readiness.py` | **HONEST BLOCK (`exit 1` / `BLOCKED_UNVERIFIED`)** | Chờ URL trang đội thi Space Apps chính thức và phê duyệt của reviewer độc lập. |

### 3.2 Bằng chứng giao diện sau đồng bộ (`docs/qa/unsynced_20261114/postsync_preview/`) & Windows QA Archive
- **Ảnh chụp Qt offscreen sau hợp nhất `98e92f5` (`postsync_preview/` — đã kiểm tra trực quan cả 9 PNG):** `login-vi-1360x850.png`, `nasa-ma7-archive-entry-vi-1360x850.png`, `nasa-ma7-source-table-vi-1360x850.png`, `simulated-briefing-vi-1360x850.png`, `simulated-patient-experience-vi-1360x850.png`, `mission-home-vi-1600x900.png`, `mission-home-vi-minimum-1040x650.png`, `monitoring-openmct-shell-1040x650.png`, `mission-home-en-1360x850.png`.
- **Ảnh & kết quả Windows trước `98e92f5` (từ `up.zip`, đã kiểm tra trực quan & bảo toàn):** 7 ảnh `QWidget.grab()` Windows `1040×650` Light VI & `1360×850` Dark EN trong [`docs/qa/windows-visual-qa/`](../windows-visual-qa/), bằng chứng UIA EXE đóng gói [`docs/qa/windows-cliff-evidence/q0430-20261114T174601Z.json`](../windows-cliff-evidence/q0430-20261114T174601Z.json) và [`docs/qa/WINDOWS_COMPLETION_REPORT_20261114.md`](../WINDOWS_COMPLETION_REPORT_20261114.md).

### 3.3 Cổng nghiệm thu ngoài VM chưa thể tự hoàn tất (Remaining Physical / External Gates)
1. **Reviewer độc lập (`review: PENDING`):** Tuân thủ `AGENTS.md` (không tự phê duyệt), toàn bộ Quest đã đồng bộ và `Q-0488` chuyển/giữ `review: PENDING` để agent/người kiểm duyệt độc lập đối soát trực tiếp.
2. **Kiểm chứng Windows 10/11 vật lý tại commit hợp nhất:** Re-run `scripts/build_windows.ps1`, `scripts/smoke_cliff_windows_offline.ps1`, tương tác **150% DPI** và ký số EXE trên bản đã gộp `98e92f5`.
3. **Thiết bị Android thật qua LAN / APK:** Chạy Expo Go hoặc bản build Android trên điện thoại thật kết nối Server LAN/HTTPS (bài test ở đây mới phủ Expo Web, Android JS bundle, Node VM adapters và API trực tiếp).
4. **Dữ liệu `CLIFF-119` & Trang nộp bài NASA:** Bổ sung URL/PDF thượng nguồn cho slot thứ 119 và gắn URL đội TRUY TINH trên Space Apps 2026.
5. **Ứng dụng đồng hồ (`apps/watch/`):** Hiện ở trạng thái `PLANNED ONLY`, chưa triển khai code Wear OS.

Xem tổng hợp điều phối tại [Super Quest Q-0488](../../quests/v1/Q-0488.md) và [SCREEN_STATUS.md](../../docs/SCREEN_STATUS.md).
