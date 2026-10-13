from __future__ import annotations

import argparse
from pathlib import Path

import cv2


def parse_args():
    parser = argparse.ArgumentParser(description="Chụp ảnh bàn cờ để hiệu chuẩn nội tại webcam.")
    parser.add_argument("--camera", type=int, default=0, help="Chỉ số webcam")
    parser.add_argument("--output", type=Path, default=Path("calibration_images"))
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    return parser.parse_args()


def main():
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    existing = sorted(args.output.glob("calibration_*.png"))
    next_index = len(existing) + 1

    camera = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    if not camera.isOpened():
        raise SystemExit(f"Không mở được camera {args.camera}.")

    print("SPACE: lưu ảnh | Q hoặc ESC: thoát")
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                break
            view = frame.copy()
            cv2.putText(
                view,
                f"Da luu: {next_index - 1} | SPACE: chup | Q: thoat",
                (24, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow("Chup anh hieu chuan camera", view)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == 32:
                path = args.output / f"calibration_{next_index:03d}.png"
                if cv2.imwrite(str(path), frame):
                    print(f"Đã lưu: {path}")
                    next_index += 1
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
