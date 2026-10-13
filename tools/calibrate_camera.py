from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(description="Hiệu chuẩn camera bằng ảnh bàn cờ.")
    parser.add_argument("--images", type=Path, default=Path("calibration_images"), help="Thư mục chứa ảnh JPG/PNG")
    parser.add_argument("--cols", type=int, default=9, help="Số góc trong theo chiều ngang")
    parser.add_argument("--rows", type=int, default=6, help="Số góc trong theo chiều dọc")
    parser.add_argument("--square-mm", type=float, default=25.0, help="Cạnh một ô bàn cờ, đơn vị mm")
    parser.add_argument("--output", type=Path, default=Path("calibration.npz"))
    return parser.parse_args()


def main():
    args = parse_args()
    paths = sorted(p for p in args.images.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"})
    if not paths:
        raise SystemExit(f"Không tìm thấy ảnh hiệu chuẩn trong: {args.images.resolve()}")

    pattern = (args.cols, args.rows)
    object_template = np.zeros((args.cols * args.rows, 3), np.float32)
    object_template[:, :2] = np.mgrid[0 : args.cols, 0 : args.rows].T.reshape(-1, 2) * args.square_mm
    object_points, image_points = [], []
    image_size = None
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.001)

    for path in paths:
        image = cv2.imread(str(path))
        if image is None:
            continue
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image_size = (gray.shape[1], gray.shape[0])
        found, corners = cv2.findChessboardCorners(gray, pattern)
        if not found:
            continue
        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        object_points.append(object_template.copy())
        image_points.append(corners)

    if len(object_points) < 10:
        raise SystemExit(f"Chỉ nhận được {len(object_points)} ảnh hợp lệ; cần ít nhất 10 ảnh ở nhiều góc khác nhau.")

    rms, camera_matrix, distortion, rvecs, tvecs = cv2.calibrateCamera(
        object_points, image_points, image_size, None, None
    )
    errors = []
    for objects, observed, rvec, tvec in zip(object_points, image_points, rvecs, tvecs):
        projected, _ = cv2.projectPoints(objects, rvec, tvec, camera_matrix, distortion)
        errors.append(float(cv2.norm(observed, projected, cv2.NORM_L2) / len(projected)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        args.output,
        camera_matrix=camera_matrix,
        distortion=distortion,
        image_size=np.asarray(image_size, dtype=np.int32),
        rms=np.asarray(rms),
        mean_reprojection_error=np.asarray(np.mean(errors)),
    )
    print(f"Đã dùng {len(object_points)}/{len(paths)} ảnh")
    print(f"RMS: {rms:.4f} | reprojection trung bình: {np.mean(errors):.4f} px")
    print(f"Đã lưu: {args.output.resolve()}")


if __name__ == "__main__":
    main()
