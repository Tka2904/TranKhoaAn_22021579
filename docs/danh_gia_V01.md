# Khảo sát vật V01

Vật V01 có kích thước đối chiếu 70 × 30 mm. Dữ liệu được ghi ngày 19–20/10/2026.

## Tập phân tích

Tập chính gồm 140 ảnh thực: 7 vùng × 4 nhóm góc × 5 lần ghi. Mỗi vùng có 20 ảnh:

[Bảng số liệu 140 mẫu](../data/V01_curated.csv) có thể mở bằng Excel. Mẫu được đánh mã S001–S140 trong `sample_code`; `source_sample_code` và `sample_id` giữ liên kết với dữ liệu nguồn. Các cột số đo giữ nguyên giá trị nguồn; sai số được tính lại theo chuẩn 70 × 30 mm. Cột `orientation_source` phân biệt nhóm góc được người thực hiện xác nhận với nhóm được ước lượng từ ảnh.

| Vùng ảnh | Nhóm 0° | Nhóm 30° | Nhóm 60° | Nhóm 90° | Tổng |
|---|---:|---:|---:|---:|---:|
| Giữa | 5 | 5 | 5 | 5 | 20 |
| Trái | 5 | 5 | 5 | 5 | 20 |
| Phải | 5 | 5 | 5 | 5 | 20 |
| Trên trái | 5 | 5 | 5 | 5 | 20 |
| Trên phải | 5 | 5 | 5 | 5 | 20 |
| Dưới trái | 5 | 5 | 5 | 5 | 20 |
| Dưới phải | 5 | 5 | 5 | 5 | 20 |

Các nhóm góc mô tả tư thế bố trí vật trong mặt phẳng. Hướng chiếu quan sát trên ảnh được lưu riêng, không đồng nhất với góc quay danh định. Nhóm 60° tại vùng giữa được xác nhận theo thông tin bố trí của người thực hiện.

Trong mỗi tổ hợp, lấy năm bản ghi có đủ ảnh và số liệu đầu tiên theo thời gian. Quy tắc chọn mẫu được áp dụng thống nhất, không lựa chọn theo độ lớn sai số. Dữ liệu nguồn được bảo toàn riêng với tập phân tích.

## Kết quả trên 140 mẫu

Các chỉ tiêu được tính từ giá trị chưa làm tròn. Chữ số thập phân của bảng không biểu thị độ chính xác của dụng cụ đối chiếu.

| Cạnh | Chuẩn (mm) | Trung bình (mm) | Bias (mm) | MAE (mm) | RMSE (mm) | MAPE (%) |
|---|---:|---:|---:|---:|---:|---:|
| Dài L | 70 | 71,490 | 1,490 | 5,165 | 5,911 | 7,379 |
| Rộng W | 30 | 30,826 | 0,826 | 2,387 | 2,889 | 7,958 |

Bias là trung bình của sai số có dấu; MAE là trung bình trị tuyệt đối của sai số; RMSE là căn trung bình bình phương sai số; MAPE là trung bình phần trăm trị tuyệt đối của sai số so với kích thước đối chiếu.

## Giới hạn diễn giải

- Kết quả giới hạn ở một vật và bố trí khảo sát hiện tại. Mẫu xác lập mặt phẳng có cùng kích thước V01; kết quả gần vùng chuẩn cần được diễn giải như kiểm tra tính nhất quán, không thay thế đánh giá trên vật kiểm tra độc lập.
- Cấu hình mặt phẳng giữa nhóm tâm và các nhóm rìa khác nhau; cần xét yếu tố này khi diễn giải sai số theo vị trí.
- Các chỉ tiêu hiện tại tập trung vào sai số kích thước. Độ lặp lại khi đặt lại, tỷ lệ phép đo hợp lệ, tỷ lệ từ chối và thời gian xử lý cần được đánh giá bằng quy trình ghi nhận riêng.
- V02 có đợt khảo sát riêng trong kho; V03–V05 chưa có số liệu. Cần phân tích riêng cấu hình từng đợt trước khi tổng hợp nhiều vật.

Ảnh thí nghiệm được lưu trong `measurement_images` và CSV nguồn nằm tại `measurements.csv`. Bảng CSV đã chọn mẫu ở trên chứa thông tin đối chiếu và số liệu của tập chính. Khi tái lập, cần tự hiệu chuẩn đúng webcam, độ phân giải và mặt phẳng làm việc, đồng thời dùng vật kiểm tra độc lập.
