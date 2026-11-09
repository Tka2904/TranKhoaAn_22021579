# Ước lượng kích thước vật thể bằng thị giác máy

## Phạm vi hiện tại

Hệ thống thực hiện phép đo hai chiều trên một mặt phẳng đã hiệu chuẩn. Phương pháp chính gồm:

1. Hiệu chuẩn nội tại webcam để khử méo ống kính.
2. Xác lập quan hệ từ tọa độ ảnh sang milimét bằng homography.
3. Tách vật thể bằng ảnh nền trống hoặc contour; YOLO11-seg là lựa chọn bổ trợ.
4. Biến đổi đường bao sang mặt phẳng metric và khớp hình chữ nhật bao định hướng.
5. Lọc kết quả theo thời gian và lưu đồng thời ảnh cùng số liệu CSV.

Phần mềm không suy ra chiều cao hoặc mô hình ba chiều từ một ảnh webcam đơn. Mặt cần đo phải đồng phẳng với mặt phẳng đã hiệu chuẩn.

## Cài đặt nhanh trên Windows

Yêu cầu Python 3.10 đến 3.12 và webcam hoạt động bình thường.

1. Tải mã nguồn về máy.
2. Chạy `setup_and_run.bat` ở lần đầu tiên.
3. Các lần sau chạy `run.bat`.

Tệp cài đặt sẽ tạo môi trường `.venv` và cài các thư viện trong `requirements.txt`. Chế độ **Nền trống** và **Contour** không cần tệp trọng số học sâu. Khi dùng YOLO11-seg, Ultralytics có thể tải trọng số `yolo11n-seg.pt`; tệp trọng số không được lưu trong kho mã nguồn.

## Hiệu chuẩn nội tại

Mẫu bàn cờ hiện dùng có 7 × 7 ô, tương ứng 6 × 6 góc trong; cạnh mỗi ô phải được đo lại chính xác trước khi hiệu chuẩn.

1. Cố định webcam ở độ phân giải 1280 × 720.
2. Chạy `capture_calibration.bat`.
3. Nhấn phím Space để chụp tối thiểu 15 đến 20 ảnh rõ nét tại nhiều vị trí, khoảng cách và góc nghiêng.
4. Nhấn Esc để kết thúc.
5. Chạy `calibrate_camera.bat` để tạo `calibration.npz`.

Nếu cạnh ô không phải 25 mm, sửa tham số `--square-mm` trong `calibrate_camera.bat` trước khi chạy. Tệp `calibration.npz` chỉ có giá trị với đúng webcam, độ phân giải và trạng thái lấy nét đã hiệu chuẩn.

## Hiệu chuẩn mặt phẳng đo

Có hai lựa chọn:

- **Mẫu chữ nhật:** nhập chiều rộng và chiều cao thật của mẫu, chọn **Chọn 4 góc**, sau đó bấm lần lượt trên-trái, trên-phải, dưới-phải và dưới-trái. Sau bước này phải giữ nguyên camera.
- **ArUco:** in `marker/aruco_id0_50mm.pdf` ở tỷ lệ 100%, kiểm tra cạnh marker bằng thước, nhập đúng kích thước và chọn **Khóa theo ArUco**.

Mẫu chuẩn nên lớn, phẳng, rõ biên và nằm gần vùng đặt vật. Mặt trên cần đo phải đồng phẳng với mẫu chuẩn.

## Quy trình đo

1. Chọn số camera và độ phân giải, sau đó bấm **Bắt đầu**. Trạng thái trên khung ảnh hiển thị độ phân giải thực mà camera cấp.
2. Chọn **Nền trống (khuyên dùng)**.
3. Dọn sạch vùng đo và bấm **Ghi nền trống**.
4. Hiệu chuẩn mặt phẳng bằng một trong hai cách ở trên.
5. Đưa một vật dạng hộp vào vùng quan sát, không che khuất và không chạm biên ảnh.
6. Chờ kết quả ổn định rồi đọc chiều dài và chiều rộng trên màn hình.
7. Khi thu thập thí nghiệm, nhập kích thước chuẩn rồi bấm **Lưu mẫu (ảnh + CSV)**. Một lần bấm lưu đúng khung ảnh đang đo và một dòng tương ứng trong `measurements.csv`.

## Dữ liệu đầu ra

- Ảnh có chú thích được lưu trong `measurement_images`.
- Số liệu được nối vào `measurements.csv`.
- Ảnh nền được lưu thành `background_reference.png`.
- Homography mặt phẳng được lưu trong `plane_calibration.json`.

Ảnh và CSV thực nghiệm được lưu trong kho này. Các cấu hình mặt phẳng và ảnh nền phụ thuộc phiên đo; bản chụp tham khảo nằm trong `data/calibration`. Người dùng cần tự hiệu chuẩn khi đổi webcam hoặc bố trí đo.

## Kiểm thử

Sau khi cài đặt, chạy:

```bat
.venv\Scripts\python.exe -m pytest tests -q
```

Kiểm thử tự động xác nhận phép đo hình học trên mặt phẳng và khả năng tách vật thể khỏi nền tổng hợp. Độ chính xác thực tế vẫn phải được đánh giá bằng vật chuẩn và tập dữ liệu độc lập.

## Dữ liệu thực nghiệm

Kho chứa 157 ảnh bàn cờ, 371 ảnh kết quả đo, 372 bản ghi số liệu và 5 ảnh minh họa lỗi nhận dạng. Bản chia sẻ dùng mã mẫu trung tính và lược bỏ ngày giờ thu mẫu. Một bản ghi đo có trong bảng tổng hợp nhưng thiếu ảnh nguồn tương ứng.

- [Danh mục và cách đối chiếu dữ liệu](docs/du_lieu_thuc_nghiem.md).
- [Bảng tổng hợp các đợt đo](measurements.csv).
- [V01 – 140 mẫu](data/V01_curated.csv) và [phân tích V01](docs/danh_gia_V01.md).
- [V02 – 100 mẫu chính](data/V02_100_mau.csv), [119 mẫu đối chiếu](data/doi_chieu_V02_119_anh.csv) và [chỉ mục ảnh](data/V02_image_index.csv).
- [V03 – 100 mẫu khảo sát chiếu sáng](data/V03_100_mau.csv).
- [V04 – chỉ mục ảnh lỗi](data/V04_chi_muc_anh.csv) và [ảnh chụp giao diện](data/V04_anh_minh_hoa/).
- [Danh mục tệp và SHA-256](data/file_manifest.csv).

## Cấu trúc thư mục

- `app.py`: giao diện và luồng xử lý thời gian thực.
- `src/detectors.py`: các phương pháp tách vật thể.
- `src/measurement.py`: hiệu chuẩn, homography và phép đo metric.
- `tools`: công cụ chụp ảnh hiệu chuẩn, hiệu chuẩn camera và tạo marker.
- `tests`: kiểm thử hình học và tách nền.
- `marker`: marker ArUco mẫu.
- `HDSD_phan_mem.docx`: hướng dẫn sử dụng chi tiết.
