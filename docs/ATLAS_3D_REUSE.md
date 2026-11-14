# AETHERION Body Atlas — lựa chọn thư viện 3D đã có

**Body Atlas không bắt buộc để giải quyết đề bài theo dõi sức khỏe NASA 2026.** Đây là thành phần trực quan P1 có thể bổ sung sau khi Server, giao diện và thư viện bệnh học chạy ổn định.

## Chọn công nghệ

- **PyVistaQt + VTK / PySide6 QtInteractor:** tích hợp trực tiếp vào cửa sổ Windows native, có viewport 3D thật, camera, mesh và picking. Mã nguồn PyVistaQt đã được lưu đầy đủ trong `Các mã nguồn mở tham khảo/pyvistaqt/`. MIT cho thư viện, nhưng phải kiểm giấy phép Qt/VTK riêng.
- **3D Slicer + SlicerOpenAnatomy:** công cụ tác giả và xuất mô hình có sẵn sang OBJ/glTF; không chạy nguyên Slicer như app thứ hai. https://github.com/PerkLab/SlicerOpenAnatomy
- **Z-Anatomy:** kho mô hình thật, https://github.com/Z-Anatomy/Models-of-human-anatomy . Đặc biệt có dữ liệu CC BY-SA và một số thành phần được ghi CC BY-NC hoặc CC BY-NC-SA. **Không chép toàn bộ vô điều kiện vào sản phẩm có mục tiêu thương mại**.

## Phân công đúng giữa Server và Desktop

Server kiểm nguồn tài liệu, mô hình và quyền; lưu manifests; trong tương lai chuyển đổi/giảm đa giác/cache/phân phối asset qua API. Desktop mới là nơi GPU dựng 3D để tương tác trực tiếp. Muốn Server dựng hoàn toàn khung hình 3D thì cần GPU server và giao thức streaming bổ sung, không phù hợp bản Windows offline.

## Đã thêm mã

`apps/desktop/src/aetherion_desktop/atlas3d.py`: adapter PyVistaQt thật, chỉ load mesh được kiểm SHA và quyền. Không bao giờ vẽ hình khối giả thành cơ thể người.

`knowledge/anatomy/approved_models.json` hiện chưa có mô hình được duyệt. Phải nhập mesh với nguồn, SHA, giấy phép từng asset trước khi chứng nhận 3D hoạt động. Bộ code này chưa được gắn vào menu đang có agent khác nhận.

## Cài tùy chọn

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".\apps\desktop[atlas]"
```

## Tiêu chí hoàn thiện

1. Có bộ mesh giải phẫu thật đã kiểm license và SHA, không chứa NC khi phát hành thương mại.
2. Chọn được cơ quan; có tên và đối chiếu nguồn đúng cấu trúc.
3. Zoom, orbit, pan, reset và pick thực trên Windows.
4. Server API cấp danh mục mesh và liên kết khoa học; client hiển thị được kể cả khi offline với assets cache đã duyệt.
5. Không đánh dấu DONE khi chỉ có source PyVistaQt hoặc mã viewport chưa chạy.
