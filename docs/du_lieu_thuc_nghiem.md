# Dữ liệu thực nghiệm

| Thành phần | Nội dung |
|---|---|
| [Ảnh bàn cờ](../calibration_images/) | 157 ảnh phục vụ hiệu chuẩn nội tại |
| [Cấu hình tham khảo](../data/calibration/) | Tệp nội tại, phép biến đổi mặt phẳng và ảnh nền của một bố trí |
| [Ảnh đo](../measurement_images/) | 371 ảnh kết quả có chú thích đường bao và số đo |
| [Bảng tổng hợp](../measurements.csv) | 372 bản ghi, gồm mẫu thử và mẫu thực nghiệm |
| [V01](../data/V01_curated.csv) | 140 mẫu, kích thước đối chiếu 70 × 30 mm |
| [V02](../data/V02_100_mau.csv) | 100 mẫu chính, kích thước đối chiếu 80 × 60 mm |
| [V02 – bảng đối chiếu](../data/doi_chieu_V02_119_anh.csv) | 119 bản ghi gồm mẫu chính và mẫu bổ sung |
| [V03](../data/V03_100_mau.csv) | 100 mẫu của bốn nhóm chiếu sáng A0–A3, kích thước đối chiếu 160 × 65 mm |
| [V04](../data/V04_chi_muc_anh.csv) | Chỉ mục 5 ảnh minh họa lỗi chọn vùng trên bao bì |
| [Danh mục tệp](../data/file_manifest.csv) | Kích thước và SHA-256 của từng tệp dữ liệu |

## Cách đối chiếu

Các tệp CSV dùng mã hóa UTF-8 và có thể mở bằng Excel. Bản chia sẻ lược bỏ ngày giờ thu mẫu và dùng mã trung tính `sample_id`. Mã này giống nhau giữa bảng tổng hợp, bảng phân nhóm và tên ảnh. Trường `image_file` trỏ từ thư mục gốc của kho đến ảnh có chú thích. Với V01, có thể tra `sample_id` trong bảng tổng hợp để lấy đường dẫn ảnh. Chỉ mục V02 dùng `image_path` để mở ảnh và `grouped_path` để mô tả nhóm.

Có 371 ảnh đo tương ứng với 372 bản ghi. Bản ghi thiếu ảnh được giữ để đối chiếu dữ liệu nguồn và nằm ngoài tập chính V01. Tập chính V01, V02 và V03 có đủ ảnh theo mã mẫu. Số đo và nội dung ảnh được giữ nguyên trong bản chia sẻ. V04 lưu riêng theo mã ảnh V04-M01 đến V04-M05.

## Phạm vi sử dụng

Ảnh đo chứa đường bao và số đo trên ảnh. Khi đối chiếu các thuật toán nhận dạng, cần ảnh RGB gốc và nền trống tương ứng nếu dùng phương pháp sai khác nền. Dữ liệu lưu mẫu hiện dùng để phân tích sai số trên các phép đo đã lưu. Tỷ lệ từ chối và thời gian xử lý cần nhật ký riêng.

Các tệp trong `data/calibration` phục vụ tham khảo. Khi đổi webcam hoặc bố trí đo cần hiệu chuẩn lại theo thiết bị và mặt phẳng sử dụng. Số ảnh bàn cờ trong thư mục là số ảnh hiện có. Số ảnh được chấp nhận trong một lần chạy hiệu chuẩn cần đối chiếu với nhật ký lần chạy đó.
