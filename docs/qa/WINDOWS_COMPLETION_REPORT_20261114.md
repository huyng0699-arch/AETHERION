# Báo cáo hoàn thiện & nghiệm thu AETHERION trên Windows — 2026-11-14

**Phạm vi thực hiện:** Windows 10 (`10.0.19045-SP0`), Python `3.13.14` (`.venv`), PySide6 `6.12.0`, PyVista, PyInstaller `6.22.3`, FastAPI/Uvicorn.  
**Nguyên tắc tuân thủ:** Tuân thủ nghiêm `AGENTS.md` (không tự phê duyệt `review: APPROVED`, giữ `CLIFF-119` trung thực là `118/119 PARTIAL`, tách biệt dữ liệu NASA lịch sử khỏi `SIMULATED` và telemetry có xác thực). Phạm vi Mobile (`apps/mobile/`) được loại trừ theo chỉ thị người dùng (*"ko cần quan tâm tới điện thoại nữa, có người khác làm"*).

---

## 1. Tổng hợp các lỗi đã phát hiện & sửa chữa

### 1.1. Backend, SQLite trên Windows (`WinError 32`) & Runtime Config
1. **Khóa file SQLite trên Windows (`PermissionError / WinError 32` khi xóa/di chuyển file tạm):**
   - **Nguyên nhân:** `sqlite3.connect(...)` trong nhiều module dùng `with sqlite3.connect(...) as conn:` (theo chuẩn Python, `sqlite3.Connection.__exit__` chỉ commit/rollback transaction chứ **không đóng handle file**), khiến Windows giữ khóa file khi `TemporaryDirectory` hoặc atomic refresh dọn dẹp.
   - **Khắc phục:** Tạo `apps/server/src/aetherion_server/sqlite_compat.py` (`closing_connection`) và chuẩn hóa đóng connection rõ ràng tại 14 module backend (`admin_control.py`, `audit_log.py`, `dev_reset.py`, `environment_store.py`, `replay_guard.py`, `self_report.py`, `store.py`, `care/episode.py`, `care/event_history.py`, `care/http_api.py`, `care/interview_persistence.py`, `ecg/http_api.py`, `safety/assistance.py`, `safety/witness_log.py`, `safety_api.py`), các module thư viện/desktop (`packages/medical_library/atomic_refresh.py`, `offline_search.py`, `knowledge/nasa/cliff_119_2023/library_schema.py`, `apps/desktop/src/aetherion_desktop/medical_article_reader.py`, `features/demo/synthetic_patients.py`) và test (`test_store.py`, `test_core_*.py`, `test_medical_library_atomic_refresh.py`, `test_cliff119_*.py`).
2. **Đường dẫn chéo POSIX/Windows (`apps/server/src/aetherion_server/runtime_config.py`):**
   - **Khắc phục:** Hỗ trợ chuẩn hóa cả `PurePosixPath` và `PureWindowsPath` khi kiểm tra đường dẫn cấu hình/DB không rò rỉ.

### 1.2. API Contracts, Tài liệu kiến trúc & Quyền/Định dạng ảnh NASA CliFF
3. **Lệch chuẩn OpenAPI (`Q-0016`):**
   - **Nguyên nhân:** `packages/contracts/openapi.json` chỉ ghi 10 path trong khi FastAPI `create_app().openapi()` phục vụ 45 paths.
   - **Khắc phục:** Đồng bộ đầy đủ **45 paths** vào `packages/contracts/openapi.json` và cập nhật bảng tóm tắt route trong `packages/contracts/README.md`.
4. **Kiến trúc Submission (`Q-0261`):**
   - **Khắc phục:** Cập nhật `submission/ARCHITECTURE_DIAGRAM.md` và `tests/test_submission_architecture_diagram.py` mô tả trung thực trạng thái `apps/mobile/` là `PREPARE` (chưa kiểm chứng thiết bị/lockfile) và `apps/watch/` là `PLANNED ONLY`.
5. **Kiểm tra JPEG trailer & trạng thái CLIFF (`Q-0458` / `CLIFF-119`):**
   - **Khắc phục:** Cập nhật `scripts/medical_image_rights.py` nhận diện marker kết thúc JPEG `\xff\xd9` hợp lệ đi kèm khối metadata Samsung `SEFT` phía sau (kết hợp decode PIL), giữ nguyên file ảnh gốc.
   - Cập nhật `knowledge/nasa/cliff_119_2023/audit_status.{json,md}` phản ánh trung thực `0/119` PDF thô, `118/119` bản ghi JSON có cấu trúc và thiếu thượng nguồn `CLIFF-119`, kèm test `test_nasa_cliff_119_status.py` và `test_cliff_021_source_audit.py`.

### 1.3. Desktop PySide6 Architecture, Bảo mật Handoff & Test Alignment
6. **Lỗi tương thích PySide6 6.12 (`setTimeSpec`) & QUrl (`Q-0478`, `Q-0485`):**
   - **Khắc phục:** Thay `setTimeSpec(Qt.TimeSpec.UTC)` đã deprecated bằng `setTimeZone(QTimeZone.utc())` trong `mission_ops_home.py` và chuẩn hóa `.toUTC()` trong `ecg_page.py`.
   - Bổ sung `from PySide6.QtCore import QUrl` trong `features/demo/nasa_ma7.py` để click mở link PDF/OSDR NASA gốc không bị `NameError`.
7. **Tích hợp Care Guide (`Q-0465`), UTC Time Conductor Sync (`Q-0477`) & An toàn Vòng Đời Mạng (`main.py`, `atlas3d.py`):**
   - **Khắc phục:** Khai báo route `"care_guide"` (`CareWorkspace`) trong `mission_ops_home.py` (`ROUTE_IDS`, `groups["clinical"]`, VI/EN) và nối vào `main.py` (`attach_feature("care_guide", self.care_page)`, `show_care_guide()`).
   - Thêm `MonitoringWorkspace.sync_utc_window(start_iso, end_iso)` trong `native_workspaces.py` nối từ `operations_home_page.time_range_changed` trong `main.py`, chỉ gọi API khi `self.subject_id` và `self._token` đã được cấp phép (bảo toàn ACL của `Q-0477`).
   - Bổ sung kiểm tra `shiboken6.isValid`, `setTransferTimeout(2500)`, header `Connection: close`, và `closeEvent` dọn reply/timer trong `main.py` và `atlas3d.py`; dùng `runtime_paths` trong `atlas3d.py` để hoạt động cả ở source tree lẫn Windows EXE đóng gói.
8. **Chống tiêm tham số URL trong Anatomy Handoff (`Q-0082`):**
   - **Khắc phục:** `apps/desktop/src/aetherion_desktop/features/personal/anatomy_handoff.py` từ chối ký tự điều khiển/định dạng Unicode (`Cc`/`Cf`) và encode route trả về (`READY` lẫn `NO_DATA`) bằng `urllib.parse.urlencode({"subject_id": checked_subject})`. Bổ sung regression test vào `tests/test_personal_anatomy_handoff.py`.
9. **Cập nhật 6 bộ test Desktop cho kiến trúc Persistent Shell (`Q-0485`) & `Q-0087`:**
   - Cập nhật `test_desktop_portal.py`, `test_desktop_qt_startup_e2e.py`, `test_main_menu_controls_audit.py`, `test_care_back_resume_episode_e2e.py`, `test_mission_to_personal_identity_e2e.py`, `test_offline_cold_start_e2e.py`, `test_anatomy_catalog_api.py`, và nâng cấp `test_personal_responsive_layout_e2e.py` kiểm tra cả `vi`/`en` ở 3 kích thước `1040×650`, `1280×720`, `1600×900` với 4 cạnh viewport qua `workspace_scroll.ensureWidgetVisible`.

### 1.4. Các lỗi giao diện thực tế phát hiện qua chụp ảnh Windows Qt (`QWidget.grab()`) & Đã Sửa
Khi chạy render thực tế trên Windows Qt (Light `vi` 1040×650 & Dark `en` 1360×850 kết nối uvicorn cục bộ), việc kiểm tra trực tiếp ảnh chụp đã phát hiện và sửa triệt để 6 lỗi UI sau:
10. **Ô ngày giờ `TIME CONDUCTOR` chữ trắng trên nền trắng ở Dark mode (`visual_theme.py`):**
    - **Khắc phục:** Bổ sung `QDateTimeEdit, QAbstractSpinBox` vào QSS stylesheet trong `visual_theme.py` (kèm `QPalette`, `QScrollArea` nền trong suốt, `QSplitter`).
11. **Tráo đổi bản dịch VI/EN của `"personal.metricSource"` (`i18n/en.json` & `i18n/vi.json`):**
    - **Khắc phục:** Sửa lại `"personal.metricSource"` thành `"Source: {source}  ·  {observed}"` trong `en.json` và `"Nguồn: {source}  ·  {observed}"` trong `vi.json`.
12. **Tiêu đề Thư viện y khoa bị cắt ngang ở `1040×650` (`medical_library.py`):**
    - **Khắc phục:** Bật `heading.setWordWrap(True)` và ưu tiên `selectedItems()[0]` trong `show_selection()` / `open_selected_article()`.
13. **ComboBox và nút công cụ đè nhau + banner VTK tràn chữ ở `Body Atlas 3D` (`atlas3d.py`):**
    - **Khắc phục:** Tách thanh công cụ thành 2 hàng sạch sẽ (`selector` dùng `AdjustToMinimumContentsLengthWithIcon`), ẩn thông báo phủ `enable_mesh_picking(..., show_message=False)` (có fallback tương thích test mock).
14. **Nút 4 bước của `Care Guide` gây thanh cuộn ngang ở `1040×650` (`native_workspaces.py`):**
    - **Khắc phục:** Chuyển `CareWorkspace.steps` thành lưới `QGridLayout` 2×2.
15. **Bảng thuộc tính Inspector bên phải bị tràn ngang (`mission_ops_home.py`):**
    - **Khắc phục:** Bật `ScrollBarAlwaysOff`, `QHeaderView.ResizeMode.Stretch`, `setTextElideMode(ElideRight)` và `resizeRowsToContents()`. Sửa `_browse_selected()` ưu tiên `selectedItems()[0]` để click UIA chính xác.

### 1.5. Packaging Windows EXE & Probe UIA (`Q-0430`)
16. **`scripts/build_windows.ps1`:** Bổ sung đóng gói dữ liệu `knowledge/anatomy`, xử lý an toàn khi thư mục dự án không có `.git` (`$gitSha = "UNKNOWN"`), tăng ngưỡng chờ cold-boot lên 45 bước (~29s) tránh timeout do antivirus quét lần đầu, và đảm bảo thu hồi tiến trình smoke trong `finally`.
17. **`scripts/smoke_cliff_windows_offline.ps1`:** Sửa lỗi quote câu lệnh SQLite trên PowerShell (dùng script `.py` tạm), nhận diện tiến trình con của Windows Store Python (`python3.13.exe`), thay `SelectionItemPattern.Select()` bằng Win32 point-click cho `QTreeWidget` trên Qt 6.12, và bổ sung fallback `PrintWindow` cho `CopyFromScreen`.

---

## 2. Kết quả kiểm thử đã quan sát trực tiếp (sau lần chỉnh sửa cuối)

| Hạng mục kiểm tra | Lệnh / Công cụ | Kết quả quan sát |
| --- | --- | --- |
| Toàn bộ test suite (`301` file) | `.venv\Scripts\python.exe -m pytest -q tests\test_*.py` (chạy từng file trong subprocess độc lập) | **PASS: `total=301`, `passed=301`, `failed=0`, `skipped_files=0`** |
| Lint cú pháp Python | `.venv\Scripts\python.exe scripts\lint_python.py` | **PASS:** `Checked 491 Python file(s), 0 errors.` |
| Toàn vẹn backlog Quest | `.venv\Scripts\python.exe scripts\quest_board.py check` | **PASS:** `485 unique Quest specs; IDs contiguous; dependencies valid and acyclic` |
| Đối khớp song ngữ VI/EN | `.venv\Scripts\python.exe scripts\audit_bilingual.py` | **PASS:** `BILINGUAL PASS: 761 VI / 761 EN UI keys` |
| Đăng ký nguồn NASA | `.venv\Scripts\python.exe scripts\validate_nasa_registry.py` | **PASS:** `CliFF records: 118; QA: 119; media: 108`, `5 NASA source registry items verified` |
| Kiểm tra trung thực NASA/branding | `.venv\Scripts\python.exe scripts\audit_nasa_truthfulness.py` | **PASS:** `0 violations` |
| Server FastAPI + SQLite smoke | `.venv\Scripts\python.exe scripts\smoke_server.py` | **PASS:** loopback server khởi động sẵn sàng, replay idempotent, tách biệt live/test |
| Cú pháp PowerShell scripts | `[System.Management.Automation.Language.Parser]::ParseFile` | **PASS:** `build_windows.ps1` & `smoke_cliff_windows_offline.ps1` |
| Build Windows EXE & boot handle | `powershell -File scripts\build_windows.ps1` | **PASS (`exit 0`):** `AETHERION-Desktop.exe` (`15,128,073` bytes), SHA-256 `1ac92d650d8154d2e591cd185df291d54859a166702c25d66b60f47bece8578b`, `native_gui_smoke: "WINDOW_HANDLE_OBSERVED"`, `medical_library_bundled: true` (`118/119 PARTIAL`) |
| Kiểm thử UIA trực tiếp trên EXE đóng gói | Khởi chạy `AETHERION-Desktop.exe` với `AETHERION_API_URL=http://127.0.0.1:1` | **PASS:** mở cửa sổ chính, bấm `Thư viện y khoa` -> 7+ bài nạp sẵn -> mở trình đọc `Trở về thư viện`; bấm `Cơ thể 3D` -> thấy nút `Đặt lại góc nhìn` |
| Probe UIA offline CliFF (`Q-0430`) | `powershell -File scripts\smoke_cliff_windows_offline.ps1` | **PASS probe (`exit 0`):** `WINDOWS_NATIVE_PROBE_PASSED_REVIEW_PENDING` (`docs/qa/windows-cliff-evidence/q0430-20261114T174601Z.json`) |
| Kiểm tra ảnh render Qt thực trên Windows | Script QA nội bộ dùng Qt platform `windows` (`QWidget.grab()`, `1040×650` Light VI & `1360×850` Dark EN kết nối Uvicorn thật) | **PASS:** 13 ảnh chụp hợp lệ, đã kiểm tra trực quan 7 ảnh đại diện lưu tại `docs/qa/windows-visual-qa/` |
| Cổng phát hành tài liệu (`release_readiness.py`) | `.venv\Scripts\python.exe scripts\release_readiness.py` | **Exit `1` (Đúng thực tế):** `documentary_gates_complete: false`, `release_authorized: false` do các gate review/chấp thuận độc lập vẫn ở trạng thái `PENDING` |

---

## 3. Những giới hạn & hạng mục tồn đọng cần lưu ý trung thực

1. **Dữ liệu `CLIFF-119` chưa đủ 119/119:** Kho gốc thiếu URL/PDF thượng nguồn cho `CLIFF-119`, nên thư viện offline đạt **`118/119` (`PARTIAL`)** và giữ nguyên cảnh báo theo `AGENTS.md`.
2. **Quyền phê duyệt độc lập (`review: PENDING`):** Tuân thủ quy tắc chống tự duyệt, toàn bộ Quest đã sửa chuyển về `PENDING` (hoặc giữ nguyên trạng thái `BLOCKED`/`STALE` tương ứng), **không tự đặt `review: APPROVED` hoặc `DONE`**.
3. **Hạn chế chụp màn hình DWM từ shell nền:** Trong phiên shell nền của môi trường chạy tự động, Win32 `CopyFromScreen` báo `"The handle is invalid"` (`build_windows.ps1` ghi warning hợp lệ) và `PrintWindow` trong `q0430-20261114T174601Z.png` chỉ thu được thanh tiêu đề cùng vùng client trắng; do đó bằng chứng pixel giao diện thực tế được cung cấp bổ sung qua `QWidget.grab()` dưới Qt platform `windows` tại `docs/qa/windows-visual-qa/`.
4. **Hạng mục chưa kiểm chứng tương tác / ngoài phạm vi:**
   - Windows Desktop chưa ký số code-signing.
   - Tỷ lệ hiển thị **150% DPI** thực tế trên màn hình vật lý và phân trang dữ liệu quan sát trực tiếp **>500 bản ghi** chưa được kiểm tra tương tác bằng tay bởi reviewer độc lập.
   - **`apps/mobile/`:** Nằm ngoài phạm vi phiên này theo chỉ thị của người dùng. Lưu ý trạng thái còn sót: `apps/mobile/package-lock.json` từng bị xóa trong lần thử chạy `npm install` bị treo do không truy cập được npm registry ở bước trước đó, và do không có file nén gốc để khôi phục, phần mobile được giữ nguyên để đội phụ trách mobile xử lý riêng.
