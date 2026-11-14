# Các mã nguồn mở tham khảo — AETHERION

**Mục đích:** giữ **toàn bộ các tệp mã nguồn được Git theo dõi** từ các dự án mã nguồn mở từng được đánh giá trong tài liệu ASTRA ngày 14/11/2026, làm tài liệu **tham khảo** cho thiết kế AETHERION.

- Không phải submodule. Khi nhập hoàn chỉnh, thư mục riêng của mỗi dự án chứa mã nguồn gốc, các tệp ẩn, kiểm thử, tài liệu, ảnh nhị phân và bản LICENSE của chính dự án.
- Không sao chép mã nguồn ASTRA cũ sang AETHERION và không tạo ứng dụng con cạnh tranh.
- Không tự động biên dịch hoặc chạy code từ thư mục này. **Chỉ nghiên cứu, chọn lọc và tích hợp có kiểm thử**, bảo đảm giấy phép.
- Mỗi bản sao khóa ở SHA cụ thể trong [SOURCES.lock.json](SOURCES.lock.json); `MANIFEST_<tên>.json` lưu SHA của **từng tệp**. `.git/` của repo nguồn không được nhét vào (Git metadata không phải tệp mã nguồn được theo dõi).
- Tất cả dữ liệu khoa học, mô hình giải phẫu, tài liệu y khoa được tải riêng phải kiểm tra giấy phép tài nguyên, không chỉ giấy phép của mã phần mềm.

## Danh sách gốc từ ASTRA

| Dự án | Nguồn | Giấy phép | Số tệp Git gốc | Vai trò |
|---|---|---|---:|---|
| PyVistaQt | https://github.com/pyvista/pyvistaqt | MIT | 51 | Qt + VTK 3D, mesh picking |
| VisPy | https://github.com/vispy/vispy | BSD-3-Clause | 841 | OpenGL 3D native |
| PyQtGraph | https://github.com/pyqtgraph/pyqtgraph | MIT | 804 | Đồ thị theo thời gian |
| NASA Open MCT | https://github.com/nasa/openmct | Apache-2.0 | 1279 | Thiết kế theo dõi telemetry; **không thay UI Windows** |
| napari | https://github.com/napari/napari | BSD-3-Clause | 1237 | Layers và viewer khoa học |
| 3D Slicer | https://github.com/Slicer/Slicer | BSD-style, có điều kiện bổ sung | 5014 | Nghiên cứu cấu trúc giải phẫu |

**Tiến độ kiểm chứng tại lúc tạo danh mục:** PyVistaQt đã được nhập trực tiếp đủ **51/51** tệp, SHA khớp nguồn. Năm dự án khác **chưa được coi là đã tải** cho đến khi các thư mục gốc và các tệp MANIFEST có mặt và lệnh verify thành công.

## Nhập tất cả tệp còn thiếu

Github Actions: [vendor_reference_sources.yml](../.github/workflows/vendor_reference_sources.yml). Workflow được thiết kế chạy khi tạo/cập nhật tệp workflow và có thể chạy thủ công trong Actions nếu cần. Nó clone chính xác commit đã khóa, chép toàn bộ Git blobs (không bỏ tệp nhị phân), kiểm tra SHA rồi commit mã nguồn thực vào AETHERION.

Cách tự chạy trên máy có kết nối GitHub (Python 3.11+, Git):

```bash
python scripts/vendor_reference_sources.py import
python scripts/vendor_reference_sources.py verify
git add -f "Các mã nguồn mở tham khảo/"
git commit -m "Import complete reference upstream source trees"
git push origin main
```

Nếu GitHub Actions không chạy được vì quyền hoặc giới hạn GitHub, **chưa có bằng chứng các dự án còn lại đã được tải**. Kiểm tra [IMPORT_REPORT.json](IMPORT_REPORT.json) sau khi chạy thành công; đừng nhầm một script import với bản nguồn đã nhập.

Không được tự động triển khai các repo này vào môi trường sản xuất hoặc sử dụng tài nguyên bên thứ ba ngoài quyền cấp phép.
