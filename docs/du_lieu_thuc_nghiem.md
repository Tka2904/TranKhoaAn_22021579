# Dữ liệu thực nghiệm

## Thành phần

| Đường dẫn | Nội dung |
|---|---|
| `calibration_images/` | 157 ảnh bàn cờ hiện có, giữ nguyên tên và nội dung |
| `measurement_images/` | 270 ảnh kết quả đo đã có chú thích |
| `measurements.csv` | 271 bản ghi nguồn, giữ nguyên giá trị lịch sử |
| `data/V01_curated.csv` | 140 mẫu V01, 7 vùng × 4 nhóm góc × 5 mẫu |
| `data/V02_100_mau.csv` | 100 mẫu V02, 5 vị trí × 4 nhóm góc × 5 mẫu |
| `data/doi_chieu_V02_119_anh.csv` | Toàn bộ 119 mẫu V02, gồm mẫu chính và bổ sung |
| `data/V02_image_index.csv` | Liên kết ảnh gốc và nhãn nhóm V02, không nhân đôi ảnh |
| `data/calibration/` | Nội tại camera, homography mặt phẳng và nền tham khảo hiện có |
| `data/file_manifest.csv` | Kích thước tệp và mã SHA-256 |

## Đối chiếu ảnh và số liệu

Mở CSV bằng Excel với mã hóa UTF-8. Cột `sample_id` là khóa đối chiếu; `image_file` trong CSV nguồn là đường dẫn tính từ thư mục gốc của kho. Các dấu gạch chéo ngược trong dữ liệu nguồn được giữ để bảo toàn bản ghi Windows.

CSV nguồn có 10 mẫu thử ban đầu, 142 bản ghi V01 và 119 bản ghi V02. Thư mục ảnh có 10 ảnh thử, 141 ảnh V01 và 119 ảnh V02. Không tạo ảnh thay thế cho bản ghi không có ảnh; tập V01 đã chọn gồm 140 mẫu có ảnh.

V01 có bảy vùng; V02 có năm vị trí. Trong mỗi tổ hợp vị trí và nhóm góc, tập chính chọn năm mẫu đầu theo thời gian, không dựa vào sai số. Nhóm góc danh định và hướng ước lượng trên ảnh là hai đại lượng khác nhau. V02 ghi nhận khoảng cách 35 cm trong bảng đã phân loại; CSV nguồn được giữ nguyên để truy vết. Các mẫu ngoài tập chính vẫn có trong CSV nguồn và thư mục ảnh.

Cột `grouped_path` trong chỉ mục V02 là nhãn tổ chức của thư mục đã phân loại, không phải một bản sao ảnh trong kho. Dùng `image_path` để mở ảnh gốc; mọi ảnh chỉ lưu một lần.

## Hiệu chuẩn

Các tệp trong `data/calibration` là bản chụp cấu hình hiện có, không chứng minh rằng cùng cấu hình được dùng cho toàn bộ các đợt đo. Không tự động áp dụng homography hoặc nền của bộ dữ liệu cho bố trí mới. Khi chạy trên máy khác, cần thu ảnh bàn cờ và hiệu chuẩn riêng, sau đó xác lập lại mặt phẳng và nền trống.

157 ảnh là số tệp bàn cờ hiện có; không mặc định đây cũng là số ảnh đã tham gia lần tạo `calibration.npz` đang lưu. Cần dựa vào nhật ký hiệu chuẩn tương ứng để xác nhận số ảnh được chấp nhận của từng lần chạy.

Ảnh đo đã chứa đường bao và số đo, không phải ảnh RGB thô. Không dùng trực tiếp các ảnh có chú thích này làm ảnh đầu vào để so sánh công bằng các thuật toán nhận dạng. Dữ liệu đã lưu cũng không bao gồm toàn bộ lần từ chối hoặc thời gian xử lý từng khung.

## Bảo toàn dữ liệu

Ảnh và các CSV nguồn được sao chép nguyên byte. Danh mục SHA-256 cho phép kiểm tra lại sau khi tải xuống. Không đưa môi trường Python, bộ nhớ đệm, tài khoản, tệp soạn thảo nội bộ hoặc mô hình tải ngoài vào bộ dữ liệu này.
