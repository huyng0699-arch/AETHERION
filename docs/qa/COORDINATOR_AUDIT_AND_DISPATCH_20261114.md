# AETHERION — Báo cáo Kiểm toán Điều phối & Phân công Cộng tác viên / Coordinator Audit & Dispatch (2026-11-14)

- **Audit Baseline Commits:** Verified test & contract baseline `de4afef0367ab161d280bceb4fcb1c9319f59536`; governance rebase baseline `c242a18980ddb93ba1be2fbe721d8ab72f7b0064` (includes `01c9e2b6`, `1e228106`, and `c242a189`)
- **Coordinator Update UTC:** `2026-11-14T15:02Z`
- **Execution Scope / Giới hạn xác minh:** Linux headless CI sandbox (Python 3.11.2, FastAPI/SQLite, `PySide6==6.12.0` + `QT_QPA_PLATFORM=offscreen`, Node 24 / `npm`). **No real Windows 10/11 desktop interactive session, physical Android phone, physical Wear OS watch, GPU VTK viewport, live Ollama server, or clinical medical review was run in this environment.** Those gates remain honestly `PENDING` / `BLOCKED` / `NOT_IMPLEMENTED`.

---

## 1. Bức tranh Tổng thể theo Nền tảng / Platform Status Matrix

| Nền tảng / Platform | Trạng thái hiện tại (Verified on `de4afef`..`c242a18`) | Kết quả kiểm tra trực tiếp / Direct Verification | Khối việc còn lại trước khi đạt chuẩn / Remaining Gates |
| :--- | :--- | :--- | :--- |
| **Server (`apps/server`)** | **Chạy ổn định cốt lõi / Core HTTP + SQLite READY**, còn 1 lỗi an toàn lâm sàng & trôi OpenAPI | `scripts/smoke_server.py` **PASS**; 7/7 `symptom_interview` suites (`9/9` tests) **PASS** (`COMPONENT_APPROVED` trong `01c9e2b6`); core Auth/Obs/Care/Admin suites **PASS**. **NHƯNG:** `guidance_citations.py:52` fail-open khi thiếu SQLite (`Q-0096`), OpenAPI `10` vs `45` routes (`Q-0016`) | Vá fail-open trong `guidance_citations.py`, xuất lại `packages/contracts/openapi.json`, kiểm định Windows `WinError 32` SQLite (`ClosingConnection` trong PR #10), kiểm duyệt độc lập `DONE` (`Q-0047` v.v.) |
| **Desktop (`apps/desktop`)** | **Mã nguồn `MissionOperationsHome` (`Q-0485`) đã thay giao diện khởi động**, chưa nghiệm thu Windows thực tế & gây gãy 6 test cũ | `Q-0485` chạy Persistent Browse/Workspace/Inspect + UTC conductor + `Q-0484` synthetic patient + `Q-0478` MA-7 + `Q-0134` Atlas provenance (`Q-0122/0124/0133/0134` vừa đạt `COMPONENT_APPROVED` trong `c242a189`). **Cảnh báo:** `QOpenGLWidget is not supported on this platform` khi `offscreen`; `mission_ops_home.py:423,431` gọi `setTimeSpec` deprecated; 6 E2E test cũ fail + Qt/VTK multi-window `pytest tests/` dính `SIGSEGV`/`SIGABRT` trên Linux | Hợp nhất/chọn lọc PR #10 (`QUrl` fix trong `nasa_ma7.py`, `QPalette`, `ClosingConnection`), dời 6 test E2E + `test_desktop_portal.py` sang `Q-0485` + `i18n`, nối route `CareWorkspace` Guide (`Q-0465`), chạy Windows 10/11 thật (`1040×650`, `150% DPI`, chụp ảnh thật sau sửa) & build EXE (`Q-0010`, `Q-0470`) |
| **Mobile (`apps/mobile`)** | **Đang phát triển Expo Web / Android (`PREPARE`), lỗi lockfile** | Expo React Native + TypeScript source tồn tại (`Q-0197`), **NHƯNG** `npm ci --dry-run --prefix apps/mobile` **FAIL (`EUSAGE`)** do `package.json` & `package-lock.json` lệch (`metro@0.83.3`, `lightningcss-*`, `hermes-parser`, `semver@7.8.6`). LAN pairing/TLS chưa làm | Đồng bộ lại `package-lock.json` (`npm install`), sửa `submission/ARCHITECTURE_DIAGRAM.md` (`Q-0261`), kiểm tra Android Emulator (`10.0.2.2:8765`), USB `adb reverse`, LAN pairing/HTTPS & máy Android thật |
| **Watch (`apps/watch`)** | **Chưa triển khai (`PLANNED ONLY`)** | Chỉ có `apps/watch/README.md` (`Q-0181`..`Q-0195` ở trạng thái `PLANNED`, `P2`) | Chưa có project Wear OS hoặc bridge điện thoại–đồng hồ; không được tuyên bố chạy trên đồng hồ |
| **NASA CliFF 119 & 3D Atlas** | **118/119 bài đã đóng gói SQLite offline; 7 mesh STL CC BY 4.0** | `importer.pack_offline_library()` **PASS**: `393,748,480` bytes, `118/119` complete (`CLIFF-119` trống), `366` media (`321` approved), `0` FK errors, `integrity='ok'`. `audit_bilingual.py` **PASS** (`761 VI / 761 EN`). **Lỗi:** `test_cliff_044_sepsis.py` fail ở `medical_image_rights.py:113` (Samsung `SEFT` trailer sau `\xff\xd9`); `audit_status.json` vẫn ghi `116/119` | Xử lý JPEG trailer trong `medical_image_rights.py` (`Q-0458`), cập nhật `audit_status.json` lên `118/119`, xác minh link/nguồn `CLIFF-119`, nghiệm thu Windows SQLite offline reader + VTK GPU 3D thật (`Q-0435`, `Q-0466`, `Q-0134`) |
| **CI & Governance (`scripts/`)** | **Board `quest_board.py check` đã PASS trở lại; GitHub Actions runner lỗi nền tảng** | `1e228106` đã thêm `depends_on: []` vào `Q-0483` -> `quest_board.py check` **PASS (485/485)**; `tests/test_quest_board.py` **7/7 PASS**; `scripts/lint_python.py` **490 files, 0 errors**. GitHub Actions vẫn fail 1–3s (`runner_name=""`, `steps=0`, log `404`) | Cộng tác viên **không** dựa vào GitHub Actions bị nghẽn runner để coi là kết quả Python; chạy kiểm tra cục bộ + Windows trực tiếp và báo trạng thái thật |

---

## 2. Kết quả Kiểm toán Toàn bộ 485 Quest & Sửa chữa đã Thực hiện (2026-11-14T15:02Z)

Trước khi điều phối, bảng Quest trên `main` bị 52 `RUNNING` (50 trong số đó đã hết hạn lease hoặc `lease_until_utc: null`), `Q-0483` vừa được `antigravity-reviewer` vá `depends_on: []` (`1e228106`) để sửa `quest_board.py check`, 19 Quest đã được duyệt độc lập bị thiếu `reviewer_id` hoặc mang short SHA tiền-rebase không còn trong lịch sử git, 4 lỗi code/an toàn thật vẫn mang nhãn `DONE` hoặc `PENDING`, và metadata `Q-0319`/`Q-0321` bị lỗi thời sau khi `Q-0457` nhập được `CLIFF-019`/`CLIFF-021`.

### Phân bố trạng thái sau cập nhật điều phối / Live Status Snapshot
- **Tổng số:** `485` Quest liên tục (`Q-0001`–`Q-0485`), `0` lỗi YAML/đồ thị phụ thuộc (`quest_board.py check` **EXIT 0**).
- **Trạng thái (`STATUS`):** `DONE: 217` · `BLOCKED: 104` · `PLANNED: 93` · `STALE: 50` · `QUEUED: 18` · `RUNNING: 2` (`Q-0180` đến `15:10:00Z`, `Q-0268` đến `15:23:00Z` — đều đang hoạt động nên được giữ nguyên) · `READY: 1` (`Q-0260`).
- **Ưu tiên (`PRIORITY`):** `P0: 111` · `P1: 247` · `P2: 95` · `P3: 32`.

### Các hành động điều phối đã ghi thẳng vào `quests/v1/Q-*.md`
1. **Giữ toàn vẹn sửa chữa Board & kiểm duyệt vừa hợp nhất (`1e228106`, `01c9e2b6`, `c242a189`):** Bảo toàn sửa chữa `Q-0483` (`depends_on: []`) và quyết định `COMPONENT_APPROVED` cho `Q-0122, Q-0124, Q-0133, Q-0134` cũng như `Q-0444, Q-0445, Q-0460, Q-0471` -> `tests/test_quest_board.py` **7/7 PASS**.
2. **Mở lại 4 lỗi thật (`STALE` / `review: REWORK_REQUIRED`):**
   - [`Q-0016`](../../quests/v1/Q-0016.md): Trôi OpenAPI schema (`10` paths trong `packages/contracts/openapi.json` so với `45` paths thực tế trên `create_app().openapi()`, thiếu `admin/*`, `assistant/*`, `care/*`, `devices/*`, `ecg/*`, `knowledge/*`, `safety/*`, `sources/*`, `sync/status`).
   - [`Q-0096`](../../quests/v1/Q-0096.md): **Lỗi an toàn lâm sàng fail-open** tại `apps/server/src/aetherion_server/care/guidance_citations.py:52` (khi chưa có `AETHERION_NASA_CLIFF_119.sqlite`, `verified_articles` rỗng khiến `if not article_id or (verified_articles and ...)` cho qua trích dẫn chưa kiểm chứng!) + fixture test còn kiểm `CLIFF-019` thay vì `CLIFF-119`.
   - [`Q-0261`](../../quests/v1/Q-0261.md): `submission/ARCHITECTURE_DIAGRAM.md` ghi sai rằng `apps/mobile/` chỉ có `README.md` (`PLANNED ONLY`), mâu thuẫn với Expo app của `Q-0197` và dữ liệu CliFF `118/119`.
   - [`Q-0458`](../../quests/v1/Q-0458.md): Giữ công sửa 5 ảnh phổi `CLIFF-077..081/095`, mở lại để giải quyết xung đột `scripts/medical_image_rights.py:113` (`endswith(b"\xff\xd9")`) làm fail `tests/test_cliff_044_sepsis.py` trên ảnh Samsung `SEFT` trailer hợp lệ (`CLIFF-044/397db8ff...jpg`).
3. **Đóng khóa & bổ sung kiểm chứng cho cụm `symptom_interview_rework` (`RUNNING` -> `BLOCKED`):**
   - [`Q-0444`](../../quests/v1/Q-0444.md), [`Q-0445`](../../quests/v1/Q-0445.md), [`Q-0460`](../../quests/v1/Q-0460.md), [`Q-0471`](../../quests/v1/Q-0471.md): giữ `COMPONENT_APPROVED` của `antigravity-reviewer` (`01c9e2b6`), chuyển `status: RUNNING` -> `BLOCKED` (giải phóng khóa `symptom_interview.py`, `runtime_config.py`, `knowledge_api.py`), và bổ sung kết quả kiểm chứng **9/9 PASS** trên cả 7 suite gồm Ollama & Cloud opt-in tại commit `7d978293ce7355d0e2fa087e21cd7b06bae8aefc`.
4. **Chuẩn hóa 19 hồ sơ `DONE` đã qua kiểm chứng (`MEDICAL_LIBRARY` + `BODY_IND`):**
   - `Q-0420, Q-0421, Q-0424, Q-0431` (xác minh 11/11 unit tests + đóng gói `118/119` SQLite trên `de4afef...`) và 15 Quest đã có independent review (`Q-0439, 0441, 0443, 0446, 0447, 0448, 0449, 0452, 0453, 0454, 0455, 0459, 0469, 0475, 0476`) được đồng bộ `reviewer`, `reviewer_id`, và SHA 40 ký tự tồn tại trên `main`, loại bỏ 19 cảnh báo giả trong `scripts/quest_review_queue.py`.
5. **Đối soát Nha khoa (`Q-0319`, `Q-0321`) & Giải phóng 45 lease `RUNNING` hết hạn/`null` -> `STALE`:**
   - Giữ `Q-0319`/`Q-0321` ở `BLOCKED` (chờ Windows offline reader & review) nhưng cập nhật đúng URL PDF gốc mà `Q-0457` đã nhập, đồng thời gắn cảnh báo test cũ `test_cliff_021_source_audit.py`.
   - 45 lease hết hạn hoặc `lease_until_utc: null` chuyển sang `STALE` (giữ nguyên `review: COMPONENT_APPROVED` / `REWORK_REQUIRED` và `implementation_state`) để cộng tác viên claim lại hợp lệ qua CAS.
6. **Tồn đọng `DONE` chưa có kiểm duyệt độc lập (`198` mục trong `quest_review_queue.py`):**
   - Gồm **65** Quest `DONE` tự duyệt ở frontmatter (`Q-0007`, `Q-0017..0023`, `Q-0032..0035`, `Q-0046..0050` — bao gồm gate `Q-0047`, `Q-0106..0107` — bao gồm gate `Q-0106`, `Q-0109..0120`, `Q-0136..0165`, `Q-0257`, `Q-0262..0265`) và **133** Quest `DONE` thiếu reviewer (`Q-0024..0030`, `Q-0036..0045`, và `116` bản ghi `NASA_CLIFF_119` `Q-0301..0418`). Để bảo toàn lịch sử theo `REVIEW-0001`, Coordinator không hủy hàng loạt trạng thái `DONE` của nhóm chưa có lỗi chứng minh; vai trò **`independent-reviewer`** xử lý theo hàng đợi `scripts/quest_review_queue.py` và các cổng `scripts/release_readiness.py`.

---

## 3. Phân loại Toàn bộ Test Đang Fail & Cảnh báo Kỹ thuật (Verified on `de4afef`)

Sau khi sửa `Q-0483`, bộ `test_quest_board.py` (**7/7**) đã PASS; đồng thời `scripts/lint_python.py` (**490/490**), `scripts/audit_bilingual.py` (**761 VI / 761 EN**), `scripts/smoke_server.py`, và nhóm 19 module core/library/interview/admin (**32/32 tests**) đều PASS. Các điểm còn fail trên clean checkout gồm **15 file test Python**, **1 lỗi lockfile Mobile**, và **2 lỗi sập process Qt/VTK `offscreen`**:

| Nhóm nguyên nhân | File / Lệnh bị lỗi | Quest liên quan | Chi tiết kỹ thuật & hướng xử lý |
| :--- | :--- | :--- | :--- |
| **1. Lỗi an toàn / Hợp đồng / Dữ liệu thật (4)** | `tests/test_care_guidance_citations.py` | `Q-0096` | `guidance_citations.py:52` fail-open khi thiếu SQLite + fixture kiểm `CLIFF-019` |
| | `tests/test_contracts.py` | `Q-0016` | `packages/contracts/openapi.json` có `10` paths vs `45` paths trên server sống |
| | `tests/test_cliff_044_sepsis.py` | `Q-0458` | `scripts/medical_image_rights.py:113` từ chối ảnh Samsung có `SEFT` trailer sau `\xff\xd9` |
| | `tests/test_submission_architecture_diagram.py` | `Q-0261` | `ARCHITECTURE_DIAGRAM.md` ghi `apps/mobile/` `PLANNED ONLY` trái với Expo app `Q-0197` |
| **2. Thiếu artifact clean-checkout (1)** | `tests/test_cliff_sqlite_library_build.py` | `Q-0459`, `Q-0457` | Đọc file gitignored `AETHERION_NASA_CLIFF_119.sqlite` (`118/119` — chạy `importer.pack_offline_library()` trước khi test; Coordinator đã xác nhận PASS sau khi build) |
| **3. Test cũ lệch trạng thái `Q-0457` / `Q-0466` / `Q-0437` (4)** | `tests/test_cliff_021_source_audit.py` (7 fails) | `Q-0321`, `Q-0457` | Khẳng định `qa/CLIFF-021.json` ở schema `UNRESOLVED` tiền-`Q-0457` |
| | `tests/test_nasa_cliff_119_status.py` | `Q-0108`, `Q-0476` | Kỳ vọng `NO_DATA`/`UNVERIFIED` trong khi `audit_status.json` ghi `PARTIAL_STRUCTURED_JSON_NO_PDF_ARCHIVE` (và `116/119` chưa cập nhật lên `118/119`) |
| | `tests/test_anatomy_catalog_api.py` (1/2) | `Q-0467`, `Q-0466` | `test_empty_repo_catalog_returns_no_data` đọc thẳng `approved_models.json` (đã có 7 model) thay vì mock thư mục rỗng |
| | `tests/test_desktop_portal.py` | `Q-0002`, `Q-0437` | Khẳng định chuỗi chữ cứng đã được tách ra `i18n/{vi,en}.json` |
| **4. 6 Test Desktop E2E lệch shell `Q-0485` + Qt crash (6)** | `tests/test_offline_cold_start_e2e.py` | `Q-0006`, `Q-0485` | Kỳ vọng `116` bài (giờ `118`) + giao diện Portal cũ |
| | `tests/test_desktop_qt_startup_e2e.py` | `Q-0243`, `Q-0485` | Kỳ vọng `portal_page` & `nav_home` cũ; đồng thời **gây `SIGSEGV` (`Exit 139`) ở dòng 77 (`app.processEvents()`)** khi chạy chung pytest process với VTK/PySide6 `offscreen` |
| | `tests/test_care_back_resume_episode_e2e.py` | `Q-0101`, `Q-0485` | Kỳ vọng `win.pages.currentWidget()` thay vì hosted container của `MissionOperationsHome` |
| | `tests/test_main_menu_controls_audit.py` | `Q-0244`, `Q-0485` | Kiểm tra thanh menu ngang cũ bị `Q-0485` ẩn để nhường `Browse` |
| | `tests/test_mission_to_personal_identity_e2e.py` | `Q-0245`, `Q-0485` | Kỳ vọng `pages.currentWidget() is personal_today_page` thay vì hosted Workspace |
| | `tests/test_personal_responsive_layout_e2e.py` | `Q-0087`, `Q-0485` | Fail trên cả kiểm tra biên dọc/bảng (`REWORK_REQUIRED`) và container mới; ngoài ra `test_personal_restart_persistence_e2e.py` PASS `1/1` khi chạy riêng nhưng **`SIGABRT` (`Exit 134`)** khi chạy chung nhiều cửa sổ Qt trong 1 process |
| **5. Mobile Lockfile Drift (1)** | `npm ci --dry-run --prefix apps/mobile` | `Q-0197` | `EUSAGE`: `apps/mobile/package.json` và `package-lock.json` không khớp |

---

## 4. Cảnh báo Xung đột Đang Mở (PR & Issues) — ĐỌC TRƯỚC KHI CLAIM

1. **Draft PR #9 (`codex/q0486-native-telemetry-plot`):** Đang giữ **`Q-0486`** (component biểu đồ UTC dùng lại được). Không tái sử dụng mã số `Q-0486` và không thay đổi cấu trúc biểu đồ thời gian khi chưa thống nhất với PR #9.
2. **Draft PR #10 (`import/windows-tested-fixes-20261114`):** Chứa 33 file chỉnh sửa đối chiếu từ bản Windows test của chủ dự án (`ClosingConnection`, `nasa_ma7.py` `QUrl` import fix, `QPalette`, `build_windows.ps1` UIA). **KHÔNG** viết chồng `nasa_ma7.py` / `build_windows.ps1` / `ClosingConnection` khi chưa đối chiếu PR #10 và không gắn ảnh ZIP chưa upload làm file trong repo.
3. **GitHub Issue #8 (P0 ACK):** Q-0485 cần hợp đồng public API hẹp từ chủ `Q-0477` (`monitoring_time.py` / `native_workspaces.py`) để đồng bộ bottom UTC Time Conductor với Monitoring, và cần chủ `Q-0478`/`Q-0484` chốt bản vá `QUrl` trong `nasa_ma7.py` (nếu không nhập từ PR #10).
4. **Lease đang chạy hợp lệ (tại `15:02Z`):** Không đụng **`Q-0180`** (`tests/test_assistance_e2e_restart.py`, hết hạn `15:10:00Z`) và **`Q-0268`** (`submission/CHALLENGE_EVIDENCE_MATRIX.md`, hết hạn `15:23:00Z`) trước khi lease hết hạn hoặc hoàn tất.

---

## 5. Bảng Phân công Theo Vai trò cho Cộng tác viên / Contributor Dispatch Playbook

> **Quy tắc bắt buộc (AGENTS.md):**
> 1. Chỉ lấy đúng **1–3 file không trùng lặp** vào `owned_paths` qua Compare-And-Swap trên `main`, ghi rõ `owner`, `run_id`, `lease_until_utc` (+60 phút).
> 2. Tự lấy `git pull --rebase origin main` trước khi sửa. Người code **không bao giờ** tự ghi `review: APPROVED` hay `DONE`.
> 3. Không đưa mã/dữ liệu từ repository cũ; giữ nguyên tiếng Anh gốc NASA và chỉ định danh bệnh/triệu chứng gốc ASTRA (`819` nhãn).

| Nhóm chuyên môn / Track | Việc ưu tiên làm ngay (theo thứ tự) | Quest nên claim | File trọng tâm (khai báo exact `owned_paths`) | Kiểm tra bắt buộc trước khi nộp |
| :--- | :--- | :--- | :--- | :--- |
| **`server-backend`** | 1) Xuất lại `packages/contracts/openapi.json` khớp 45 route sống & cập nhật `test_contracts.py`<br>2) Đưa `ClosingConnection` từ PR #10 hoặc sửa rò handle SQLite trên Windows<br>3) Cập nhật `Q-0031`, `Q-0479` (admin GUI Windows smoke) | `Q-0016` (`P0`, `STALE`), `Q-0031`, `Q-0479` | `packages/contracts/openapi.json`, `packages/contracts/README.md`, `tests/test_contracts.py` | `pytest tests/test_contracts.py tests/test_openapi_route_validation.py tests/test_server_admin_integration.py` + `scripts/smoke_server.py` |
| **`clinical-safety`** | 1) Vá lỗi **fail-open** tại `guidance_citations.py:52` khi không có SQLite<br>2) Sửa `test_care_guidance_citations.py` kiểm trường hợp thiếu DB + `CLIFF-119`<br>3) Đối chiếu kiểm chứng `Q-0096` / `Q-0180` | `Q-0096` (`P1`, `STALE`), sau đó `Q-0092`, `Q-0177` | `apps/server/src/aetherion_server/care/guidance_citations.py`, `tests/test_care_guidance_citations.py` | `pytest tests/test_care_guidance_citations.py` (có cả test negative thiếu SQLite) |
| **`desktop-qt`** | 1) Thay `setTimeSpec` deprecated tại `mission_ops_home.py:423,431` bằng `setTimeZone(QTimeZone.UTC)`<br>2) Sửa URL encoding chống query-injection trong `anatomy_handoff.py` (`Q-0082`) & khẳng định giá trị lưu thật trong `test_personal_restart_persistence_e2e.py` (`Q-0090`)<br>3) Cập nhật `test_desktop_portal.py` + 6 E2E tests theo `Q-0485` `MissionOperationsHome`, sửa vòng đời `close()` tránh `SIGSEGV`/`SIGABRT`<br>4) Phối hợp Issue #8: nối UTC conductor <-> `Q-0477` & gắn route `CareWorkspace` Guide (`Q-0465`) | `Q-0082`, `Q-0090`, `Q-0087`, `Q-0243`, `Q-0244`, `Q-0245`, `Q-0101`, `Q-0485`, `Q-0465` | Khai báo từng file cụ thể (`anatomy_handoff.py`, `mission_ops_home.py`, từng file `tests/test_*_e2e.py`, `main.py` theo lượt riêng) | Chạy **từng file** dưới `QT_QPA_PLATFORM=offscreen` + chạy thật trên Windows; không gộp 2 agent cùng khóa `main.py` |
| **`3d-atlas`** | 1) Cách ly test `test_empty_repo_catalog_returns_no_data` trong `test_anatomy_catalog_api.py` bằng `tempfile`<br>2) Chạy VTK `BodyAtlas3D` trên Windows có GPU thật cho 7 mesh CC BY 4.0 & chụp ảnh picking + hộp thoại `source_inspector.py` (`Q-0134` local-path security) | `Q-0467`, `Q-0466`, `Q-0134`, `Q-0123` (`QUEUED`) | `tests/test_anatomy_catalog_api.py`, và checklist Windows GPU trên `Q-0134` / `Q-0466` | `pytest tests/test_anatomy_catalog_api.py tests/test_q0466_anatomy_meshes.py` + screenshot Windows OpenGL/VTK thật |
| **`medical-data`** | 1) Thống nhất `scripts/medical_image_rights.py:113` với JPEG có Samsung `SEFT` trailer (`CLIFF-044`, `Q-0458`)<br>2) Cập nhật `audit_status.json` (`116` -> `118/119`), `test_nasa_cliff_119_status.py`, `test_cliff_021_source_audit.py`, `test_offline_cold_start_e2e.py` (`116` -> `118`)<br>3) Cập nhật `submission/ARCHITECTURE_DIAGRAM.md` (`Q-0261`) + rà `CLIFF-119` (`Q-0433`, `Q-0435`) | `Q-0458` (`P0`, `STALE`), `Q-0261` (`P0`, `STALE`), `Q-0108`, `Q-0433`, `Q-0434`, `Q-0435` | `scripts/medical_image_rights.py`, `knowledge/nasa/cliff_119_2023/audit_status.*`, `submission/ARCHITECTURE_DIAGRAM.md`, `tests/test_cliff_*` | `pytest tests/test_cliff_044_sepsis.py tests/test_cliff_media_integrity.py tests/test_nasa_cliff_119_status.py tests/test_cliff_021_source_audit.py tests/test_submission_architecture_diagram.py` + build SQLite test `test_cliff_sqlite_library_build.py` |
| **`mobile-expo`** | 1) Đồng bộ `apps/mobile/package-lock.json` (`npm install`) sao cho `npm ci` sạch<br>2) Kiểm thử Expo Web (`AETHERION_ENABLE_DEV_CORS=1`) & Android Emulator (`10.0.2.2:8765`, `AETHERION_ALLOW_DEV_HTTP=1`) + `adb reverse`<br>3) Thiết kế/triển khai ghép nối LAN & TLS cho máy Android thật | `Q-0197` (`P1`, `STALE`, `REWORK_REQUIRED`), rồi nhóm `Q-0196..0210` | `apps/mobile/package.json`, `apps/mobile/package-lock.json`, `apps/mobile/src/**` | `npm ci --dry-run --prefix apps/mobile`, `npx tsc --noEmit`, `npx expo export --platform web` + log chạy thực tế trên emulator/điện thoại |
| **`watch-wearos`** | Khởi tạo kiến trúc companion Wear OS / bridge qua điện thoại nếu team mở scope đồng hồ (giữ trung thực không bịa số đo cảm biến) | `Q-0181..0195` (`P2`, `PLANNED`) | `apps/watch/**` (chưa có build nào) | Chứng minh build Android Studio/Wear OS & truyền quan sát có `source/unit/observed_at` |
| **`windows-qa-exe`** | 1) Đối chiếu & test Draft PR #10 trên Windows 10/11 thật (`setup_windows.ps1`, `start_server.ps1`, `start_desktop.ps1`)<br>2) Chạy `build_windows.ps1`, kiểm chứng `AETHERION-Desktop.exe`, `Q-0485` (`1040×650`, `150% DPI`), `Q-0477` ECG/UTC, `Q-0484` 5×540 SQLite, `Q-0483` Care create, `admin_gui`<br>3) Upload ảnh `QWidget.grab()` thật vào repo (binary-capable) & hoàn thiện `Q-0256` / `Q-0260` | `Q-0002`, `Q-0003`, `Q-0004`, `Q-0010`, `Q-0253`, `Q-0254`, `Q-0470`, `Q-0260` (`READY`) | `docs/evidence/**`, `build-evidence.json` (tạm), cập nhật từng Quest tương ứng | Log PowerShell Windows 10/11 + SHA-256 EXE + ảnh chụp thực tế (không dùng screenshot Portal cũ đã bị reject) |
| **`independent-reviewer`** | Thực hiện chu trình `REVIEW-0001`: rà 8 cổng `release_readiness.py --scope demo/release/library` (đặc biệt `Q-0047`, `Q-0106`, `Q-0241`, `Q-0256`) và xác minh `65` `SELF_FM` + `133` `OTHER_NO_IND` `DONE` bằng công cụ thật tại `HEAD` | `REVIEW-0001`, hàng đợi `scripts/quest_review_queue.py` | Chỉ sửa YAML & mục review trong `quests/v1/Q-*.md` (không sửa code implementer) | `python scripts/quest_board.py check` + `python scripts/release_readiness.py --scope demo` |

---

## 6. Lệnh Tái kiểm tra Nhanh cho Cộng tác viên / Quick Verification Commands

```powershell
# 1. Integrity & Governance (Windows / Linux)
python scripts/quest_board.py check
python scripts/lint_python.py
python scripts/audit_bilingual.py
python scripts/release_readiness.py --scope demo
python scripts/release_readiness.py --scope release
python scripts/release_readiness.py --scope library

# 2. Core Server + Offline CliFF Library Build & Smoke
python scripts/smoke_server.py
python -c "from pathlib import Path; from knowledge.nasa.cliff_119_2023 import importer; print(importer.pack_offline_library(Path('knowledge/nasa/cliff_119_2023/AETHERION_NASA_CLIFF_119.sqlite')))"

# 3. Mobile Lockfile Check
npm ci --dry-run --prefix apps/mobile
```
