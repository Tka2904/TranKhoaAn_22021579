from __future__ import annotations

import csv
import json
import threading
import time
import tkinter as tk
from collections import deque
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from src.detectors import BackgroundDifferenceDetector, ClassicalContourDetector, Detection, YoloSegmenter
from src.measurement import MarkerTracker, load_camera_calibration, marker_homography, measure_contour, transform_points


ROOT = Path(__file__).resolve().parent
PLANE_FILE = ROOT / "plane_calibration.json"
RESULTS_FILE = ROOT / "measurements.csv"
BACKGROUND_FILE = ROOT / "background_reference.png"
SNAPSHOTS_DIR = ROOT / "measurement_images"
RESULT_FIELDS = [
    "sample_id", "image_file", "timestamp", "frame_id", "label", "confidence",
    "length_mm", "width_mm", "true_length_mm", "true_width_mm",
    "abs_error_length_mm", "abs_error_width_mm", "ape_length_pct", "ape_width_pct",
    "distance_cm", "rectangularity", "stability_cv", "plane_source", "intrinsic_calibrated",
]


class MeasurementApp:
    """Measure planar length/width with a calibrated monocular webcam."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Đo chiều dài và chiều rộng trên mặt phẳng bằng webcam")
        self.root.geometry("1440x900")
        self.config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
        self.capture: cv2.VideoCapture | None = None
        self.running = False
        self.frame_id = 0
        self.last_frame: np.ndarray | None = None
        self.last_annotated: np.ndarray | None = None
        self.last_result: dict | None = None
        self.calibration = None

        self.marker_tracker = MarkerTracker()
        self.plane_h: np.ndarray | None = None
        self.plane_source = "chưa hiệu chuẩn"
        self.plane_image_size: tuple[int, int] | None = None
        self.marker_corners: np.ndarray | None = None
        self.manual_points: list[tuple[float, float]] = []
        self.manual_mode = False

        self.contour_detector = ClassicalContourDetector(self.config["min_object_area_px"])
        self.background_detector = BackgroundDifferenceDetector(
            self.config["min_object_area_px"],
            self.config.get("background_difference_threshold", 24.0),
            self.config.get("background_open_kernel", 5),
            self.config.get("background_close_kernel", 19),
        )
        if BACKGROUND_FILE.exists():
            self.background_detector.set_background(cv2.imread(str(BACKGROUND_FILE)))
        self.yolo: YoloSegmenter | None = None
        self.yolo_error: str | None = None
        self.inference_lock = threading.Lock()
        self.inference_event = threading.Event()
        self.inference_stop = threading.Event()
        self.inference_job = None
        self.inference_busy = False
        self.yolo_detections: list[Detection] = []
        self.yolo_frame_id = -1000
        self.inference_ms = 0.0
        self.inference_thread = threading.Thread(target=self._inference_loop, daemon=True)
        self.inference_thread.start()

        self.history: deque[np.ndarray] = deque(maxlen=int(self.config.get("smoothing_window", 9)))
        self.recent_frames: deque[np.ndarray] = deque(maxlen=12)
        self.target_bbox: tuple[int, int, int, int] | None = None
        self.display_scale = 1.0
        self.display_offset = (0, 0)
        self.notice_until = 0.0

        self.camera_var = tk.IntVar(value=self.config["camera_index"])
        self.detector_var = tk.StringVar(value="Nền trống (khuyên dùng)")
        self.conf_var = tk.DoubleVar(value=self.config["confidence"])
        self.marker_size_var = tk.DoubleVar(value=self.config["marker_size_mm"])
        self.reference_width_var = tk.DoubleVar(value=210.0)
        self.reference_height_var = tk.DoubleVar(value=297.0)
        self.distance_cm_var = tk.DoubleVar(value=50.0)
        self.true_length_var = tk.DoubleVar(value=0.0)
        self.true_width_var = tk.DoubleVar(value=0.0)
        self.result_var = tk.StringVar(value="Chưa có kết quả")
        self.status_var = tk.StringVar(value="Bấm Bắt đầu, sau đó hiệu chuẩn mặt phẳng đo")
        self.calibration_var = tk.StringVar(value="Mặt phẳng: chưa hiệu chuẩn")
        self._load_saved_plane()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self):
        controls = ttk.Frame(self.root, padding=8)
        controls.pack(fill=tk.X)
        ttk.Label(controls, text="Camera:").grid(row=0, column=0, padx=4)
        ttk.Spinbox(controls, from_=0, to=10, width=4, textvariable=self.camera_var).grid(row=0, column=1)
        ttk.Label(controls, text="Nhận dạng:").grid(row=0, column=2, padx=(14, 4))
        ttk.Combobox(controls, width=23, state="readonly", textvariable=self.detector_var,
                     values=("Nền trống (khuyên dùng)", "Contour (nhanh)", "YOLO11-seg", "Kết hợp")).grid(row=0, column=3)
        ttk.Label(controls, text="Độ tin cậy:").grid(row=0, column=4, padx=(14, 4))
        ttk.Entry(controls, width=6, textvariable=self.conf_var).grid(row=0, column=5)
        ttk.Button(controls, text="Bắt đầu", command=self.start).grid(row=0, column=6, padx=(18, 4))
        ttk.Button(controls, text="Dừng", command=self.stop).grid(row=0, column=7, padx=4)
        ttk.Button(controls, text="Lưu mẫu (ảnh + CSV)", command=self.save_sample).grid(row=0, column=8, padx=4)
        ttk.Button(controls, text="Ghi nền trống", command=self.capture_empty_background).grid(row=0, column=9, padx=4)

        ttk.Label(controls, text="ArUco cạnh (mm):").grid(row=1, column=0, padx=4, pady=(8, 0), sticky=tk.W)
        ttk.Entry(controls, width=8, textvariable=self.marker_size_var).grid(row=1, column=1, pady=(8, 0))
        ttk.Button(controls, text="Khóa theo ArUco", command=self.lock_aruco_plane).grid(row=1, column=2, padx=4, pady=(8, 0))
        ttk.Label(controls, text="hoặc mẫu chữ nhật R × C (mm):").grid(row=1, column=3, padx=(14, 4), pady=(8, 0), sticky=tk.E)
        ref_box = ttk.Frame(controls)
        ref_box.grid(row=1, column=4, columnspan=2, pady=(8, 0), sticky=tk.W)
        ttk.Entry(ref_box, width=7, textvariable=self.reference_width_var).pack(side=tk.LEFT)
        ttk.Label(ref_box, text=" × ").pack(side=tk.LEFT)
        ttk.Entry(ref_box, width=7, textvariable=self.reference_height_var).pack(side=tk.LEFT)
        ttk.Button(controls, text="Chọn 4 góc", command=self.begin_manual_calibration).grid(row=1, column=6, padx=4, pady=(8, 0))
        ttk.Button(controls, text="Xóa hiệu chuẩn", command=self.clear_plane).grid(row=1, column=7, padx=4, pady=(8, 0))
        ttk.Label(controls, textvariable=self.calibration_var, foreground="#075985").grid(
            row=1, column=8, columnspan=3, padx=(8, 0), pady=(8, 0), sticky=tk.W)

        ttk.Label(controls, text="Khoảng cách camera-mặt phẳng (cm):").grid(
            row=2, column=0, columnspan=2, padx=4, pady=(8, 0), sticky=tk.W)
        ttk.Entry(controls, width=8, textvariable=self.distance_cm_var).grid(row=2, column=2, pady=(8, 0))
        ttk.Label(controls, text="Kích thước chuẩn D × R (mm):").grid(row=2, column=3, padx=(14, 4), pady=(8, 0), sticky=tk.E)
        truth_box = ttk.Frame(controls)
        truth_box.grid(row=2, column=4, columnspan=2, pady=(8, 0), sticky=tk.W)
        ttk.Entry(truth_box, width=7, textvariable=self.true_length_var).pack(side=tk.LEFT)
        ttk.Label(truth_box, text=" × ").pack(side=tk.LEFT)
        ttk.Entry(truth_box, width=7, textvariable=self.true_width_var).pack(side=tk.LEFT)
        ttk.Label(controls, text="Một lần bấm sẽ lưu đồng thời ảnh và số liệu CSV.",
                  foreground="#075985").grid(row=2, column=6, padx=4, pady=(8, 0), sticky=tk.W)
        ttk.Label(controls, text="Đặt mặt cần đo đồng phẳng với mẫu chuẩn; sau hiệu chuẩn không cần chọn điểm trên vật.",
                  foreground="#92400e").grid(row=2, column=7, columnspan=4, padx=(8, 0), pady=(8, 0), sticky=tk.W)

        result_bar = ttk.Frame(self.root, padding=(12, 4, 12, 4))
        result_bar.pack(fill=tk.X)
        ttk.Label(result_bar, text="Kết quả:", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        ttk.Label(result_bar, textvariable=self.result_var, foreground="#b91c1c",
                  font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT, padx=10)
        self.video_label = ttk.Label(self.root, anchor=tk.CENTER)
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.video_label.bind("<Button-1>", self._on_video_click)
        ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W, padding=8).pack(fill=tk.X)

    def _load_saved_plane(self):
        if not PLANE_FILE.exists():
            return
        try:
            payload = json.loads(PLANE_FILE.read_text(encoding="utf-8"))
            h = np.asarray(payload["homography"], dtype=np.float64)
            if h.shape != (3, 3) or not np.all(np.isfinite(h)):
                return
            self.plane_h = h
            size = payload.get("image_size")
            self.plane_image_size = tuple(int(v) for v in size) if size else None
            self.plane_source = str(payload.get("source", "đã lưu"))
            self.calibration_var.set(f"Mặt phẳng: {self.plane_source} (đã lưu)")
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            self.plane_h = None

    def _save_plane(self):
        if self.plane_h is None or self.last_frame is None:
            return
        height, width = self.last_frame.shape[:2]
        payload = {"version": 1, "source": self.plane_source, "image_size": [width, height],
                   "homography": self.plane_h.tolist(), "created_at": datetime.now().isoformat(timespec="seconds")}
        PLANE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.plane_image_size = (width, height)

    def start(self):
        if self.running:
            return
        index = int(self.camera_var.get())
        capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not capture.isOpened():
            capture.release()
            capture = cv2.VideoCapture(index)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, int(self.config["camera_width"]))
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, int(self.config["camera_height"]))
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not capture.isOpened():
            capture.release()
            messagebox.showerror("Không mở được camera", f"Không tìm thấy camera số {index}.")
            return
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or int(self.config["camera_width"])
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or int(self.config["camera_height"])
        self.calibration = load_camera_calibration(ROOT / self.config.get("calibration_file", "calibration.npz"),
                                                   width, height, float(self.config.get("camera_horizontal_fov_deg", 68.0)))
        if self.plane_image_size and self.plane_image_size != (width, height):
            self.plane_h = None
            self.calibration_var.set("Mặt phẳng: phải hiệu chuẩn lại do đổi độ phân giải")
        self.capture = capture
        self.running = True
        intrinsic = "nội tại thật" if not self.calibration.approximate else "chưa có nội tại thật"
        self.status_var.set(f"Camera {width}×{height} đã mở ({intrinsic})")
        self._update_frame()

    def stop(self):
        self.running = False
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        self.status_var.set("Đã dừng camera")

    def _undistort(self, frame: np.ndarray) -> np.ndarray:
        if self.calibration is None or self.calibration.approximate:
            return frame
        return cv2.undistort(frame, self.calibration.camera_matrix, self.calibration.distortion)

    def _inference_loop(self):
        while not self.inference_stop.is_set():
            self.inference_event.wait(0.2)
            if self.inference_stop.is_set():
                break
            with self.inference_lock:
                job = self.inference_job
                self.inference_job = None
                self.inference_event.clear()
                self.inference_busy = job is not None
            if job is None:
                continue
            frame_id, frame, confidence = job
            started = time.perf_counter()
            try:
                if self.yolo is None:
                    self.yolo = YoloSegmenter(str(ROOT / self.config["model"]), int(self.config.get("yolo_image_size", 512)))
                detections = self.yolo.detect(frame, confidence, int(self.config.get("max_objects", 8)))
                with self.inference_lock:
                    self.yolo_detections = detections
                    self.yolo_frame_id = frame_id
                    self.inference_ms = (time.perf_counter() - started) * 1000.0
                self.yolo_error = None
            except Exception as exc:
                self.yolo_error = str(exc)
            finally:
                with self.inference_lock:
                    self.inference_busy = False

    def _submit_yolo(self, frame: np.ndarray):
        if self.detector_var.get() in {"Contour (nhanh)", "Nền trống (khuyên dùng)"}:
            return
        if self.frame_id % max(1, int(self.config.get("inference_every_n_frames", 3))):
            return
        with self.inference_lock:
            if self.inference_busy or self.inference_job is not None:
                return
            self.inference_job = (self.frame_id, frame.copy(), float(self.conf_var.get()))
            self.inference_event.set()

    @staticmethod
    def _bbox(contour: np.ndarray) -> tuple[int, int, int, int]:
        return tuple(int(v) for v in cv2.boundingRect(contour))

    @staticmethod
    def _iou(a, b) -> float:
        if b is None:
            return 0.0
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        x1, y1, x2, y2 = max(ax, bx), max(ay, by), min(ax + aw, bx + bw), min(ay + ah, by + bh)
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        union = aw * ah + bw * bh - inter
        return inter / union if union else 0.0

    def _detections(self, frame: np.ndarray) -> list[Detection]:
        mode = self.detector_var.get()
        background = (self.background_detector.detect(frame, int(self.config.get("max_objects", 8)))
                      if self.background_detector.ready else [])
        if mode == "Nền trống (khuyên dùng)":
            return background
        contours = self.contour_detector.detect(frame, int(self.config.get("max_objects", 8)))
        if mode == "Contour (nhanh)":
            return contours
        with self.inference_lock:
            age = self.frame_id - self.yolo_frame_id
            yolo = list(self.yolo_detections) if age <= int(self.config.get("max_detection_age_frames", 12)) else []
        if mode == "YOLO11-seg":
            return yolo
        # In combined mode, the captured background is the most reliable cue
        # for a fixed camera. YOLO and Canny only add objects not already
        # represented by that foreground mask.
        merged = list(background)
        for item in [*yolo, *contours]:
            if not any(self._iou(self._bbox(item.contour), self._bbox(other.contour)) > 0.45 for other in merged):
                merged.append(item)
        return merged

    def capture_empty_background(self):
        if not self.running or self.last_frame is None:
            messagebox.showwarning("Chưa có hình", "Bấm Bắt đầu và để camera ổn định trước khi ghi nền.")
            return
        if len(self.recent_frames) < 5:
            messagebox.showwarning("Chưa đủ khung hình", "Để mặt bàn trống và chờ camera ổn định thêm một chút.")
            return
        background = np.median(np.stack(tuple(self.recent_frames), axis=0), axis=0).astype(np.uint8)
        self.background_detector.set_background(background)
        cv2.imwrite(str(BACKGROUND_FILE), background)
        self.detector_var.set("Nền trống (khuyên dùng)")
        self.history.clear()
        self.target_bbox = None
        self.status_var.set("Đã ghi nền trống; bây giờ đặt một vật vào dấu ngắm")

    def _select_target(self, detections: list[Detection], shape) -> Detection | None:
        height, width = shape[:2]
        center = np.array([width / 2.0, height / 2.0])
        margin = int(self.config.get("object_border_margin_px", 8))
        candidates = []
        for detection in detections:
            x, y, w, h = self._bbox(detection.contour)
            if x <= margin or y <= margin or x + w >= width - margin or y + h >= height - margin:
                continue
            if self.marker_corners is not None and self._iou((x, y, w, h), self._bbox(self.marker_corners)) > 0.20:
                continue
            area = cv2.contourArea(detection.contour)
            if area <= 0:
                continue
            object_center = np.array([x + w / 2.0, y + h / 2.0])
            distance = np.linalg.norm(object_center - center) / max(width, height)
            continuity = self._iou((x, y, w, h), self.target_bbox)
            candidates.append((distance - 0.35 * continuity - 0.03 * np.log1p(area), detection))
        if not candidates:
            self.target_bbox = None
            return None
        selected = min(candidates, key=lambda item: item[0])[1]
        self.target_bbox = self._bbox(selected.contour)
        return selected

    def _automatic_marker(self, frame: np.ndarray):
        corners, _ = self.marker_tracker.detect(frame, int(self.config.get("marker_id", 0)))
        self.marker_corners = corners
        if corners is None:
            return
        side_px = np.linalg.norm(corners - np.roll(corners, -1, axis=0), axis=1)
        if float(np.min(side_px)) < float(self.config.get("marker_min_side_px", 55)):
            return
        self.plane_h = marker_homography(corners, float(self.marker_size_var.get()))
        self.plane_source = "ArUco theo từng khung"
        self.calibration_var.set("Mặt phẳng: ArUco đang được nhận dạng")

    def lock_aruco_plane(self):
        if self.marker_corners is None or self.last_frame is None:
            messagebox.showwarning("Chưa thấy ArUco", "Đưa đầy đủ marker ArUco ID 0 vào ảnh rồi thử lại.")
            return
        self.plane_h = marker_homography(self.marker_corners, float(self.marker_size_var.get()))
        self.plane_source = "ArUco khóa cố định"
        self._save_plane()
        self.calibration_var.set("Mặt phẳng: đã khóa theo ArUco; không di chuyển camera")
        self.history.clear()

    def begin_manual_calibration(self):
        if self.last_frame is None:
            messagebox.showwarning("Chưa có hình", "Hãy mở camera trước khi hiệu chuẩn.")
            return
        if self.reference_width_var.get() <= 0 or self.reference_height_var.get() <= 0:
            messagebox.showerror("Kích thước không hợp lệ", "Chiều rộng và chiều cao mẫu phải lớn hơn 0 mm.")
            return
        self.manual_points = []
        self.manual_mode = True
        self.status_var.set("Nhấp 4 góc mẫu theo thứ tự: trên-trái, trên-phải, dưới-phải, dưới-trái")

    def _on_video_click(self, event):
        if not self.manual_mode or self.last_frame is None:
            return
        ox, oy = self.display_offset
        x, y = (event.x - ox) / self.display_scale, (event.y - oy) / self.display_scale
        height, width = self.last_frame.shape[:2]
        if not (0 <= x < width and 0 <= y < height):
            return
        self.manual_points.append((float(x), float(y)))
        self.status_var.set(f"Đã chọn {len(self.manual_points)}/4 góc")
        if len(self.manual_points) < 4:
            return
        src = np.asarray(self.manual_points, dtype=np.float32)
        w_mm, h_mm = float(self.reference_width_var.get()), float(self.reference_height_var.get())
        dst = np.array([[0, 0], [w_mm, 0], [w_mm, h_mm], [0, h_mm]], dtype=np.float32)
        if abs(cv2.contourArea(src.reshape(-1, 1, 2))) < 500:
            self.manual_points = []
            messagebox.showerror("Bốn góc không hợp lệ", "Vùng hiệu chuẩn quá nhỏ hoặc thứ tự góc bị sai.")
            return
        self.plane_h = cv2.getPerspectiveTransform(src, dst)
        self.plane_source = f"mẫu {w_mm:g}×{h_mm:g} mm"
        self.manual_mode = False
        self._save_plane()
        self.calibration_var.set(f"Mặt phẳng: {self.plane_source}; không di chuyển camera")
        self.status_var.set("Hiệu chuẩn xong; đưa vật vào dấu ngắm giữa ảnh")
        self.history.clear()

    def clear_plane(self):
        self.plane_h = None
        self.plane_image_size = None
        self.marker_corners = None
        self.manual_points = []
        self.manual_mode = False
        self.history.clear()
        if PLANE_FILE.exists():
            PLANE_FILE.unlink()
        self.calibration_var.set("Mặt phẳng: chưa hiệu chuẩn")
        self.result_var.set("CHƯA HIỆU CHUẨN")

    @staticmethod
    def _rectangularity(contour: np.ndarray, homography: np.ndarray) -> float:
        metric = transform_points(contour, homography).astype(np.float32)
        area = abs(float(cv2.contourArea(metric)))
        rect = cv2.minAreaRect(metric)
        rect_area = float(rect[1][0] * rect[1][1])
        return area / rect_area if rect_area > 0 else 0.0

    def _annotate(self, frame: np.ndarray) -> np.ndarray:
        canvas = frame.copy()
        self._automatic_marker(frame)
        self._submit_yolo(frame)
        if self.marker_corners is not None:
            cv2.polylines(canvas, [np.round(self.marker_corners).astype(np.int32)], True, (0, 180, 255), 2)
            cv2.putText(canvas, "Mau chuan", tuple(np.round(self.marker_corners[0]).astype(int)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 180, 255), 2, cv2.LINE_AA)
        for point in self.manual_points:
            cv2.circle(canvas, tuple(np.round(point).astype(int)), 7, (255, 0, 255), -1)
        height, width = frame.shape[:2]
        cv2.drawMarker(canvas, (width // 2, height // 2), (255, 255, 255), cv2.MARKER_CROSS, 42, 2)
        if self.plane_h is None:
            self.last_result = None
            self.result_var.set("CHƯA HIỆU CHUẨN MẶT PHẲNG")
            cv2.putText(canvas, "Can ArUco hoac chon 4 goc mau chuan", (25, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
            return canvas

        if self.detector_var.get() == "Nền trống (khuyên dùng)" and not self.background_detector.ready:
            self.last_result = None
            self.result_var.set("HÃY DỌN HẾT VẬT RỒI BẤM GHI NỀN TRỐNG")
            return canvas

        detection = self._select_target(self._detections(frame), frame.shape)
        if detection is None:
            self.last_result = None
            self.result_var.set("Đưa vật dạng hộp vào dấu ngắm")
            return canvas
        measurement = measure_contour(detection.contour, self.plane_h)
        if measurement is None:
            self.last_result = None
            self.result_var.set("Không xác định được hình chữ nhật bao")
            return canvas
        rectangularity = self._rectangularity(detection.contour, self.plane_h)
        dimensions = np.array([measurement.length_mm, measurement.width_mm], dtype=np.float64)
        accepted_geometry = bool(np.all(np.isfinite(dimensions)) and np.all(dimensions > 3.0)
                                 and np.all(dimensions < float(self.config.get("max_planar_measurement_mm", 1500.0)))
                                 and rectangularity >= float(self.config.get("minimum_rectangularity", 0.62)))
        if accepted_geometry:
            self.history.append(dimensions)
        else:
            self.history.clear()
        stable_count = int(self.config.get("minimum_stable_frames", 5))
        median = np.median(np.asarray(self.history), axis=0) if self.history else dimensions
        cv = (float(np.max(np.std(np.asarray(self.history), axis=0) / np.maximum(median, 1.0)))
              if len(self.history) >= 2 else 1.0)
        stable = len(self.history) >= stable_count and cv <= float(self.config.get("max_stability_cv", 0.025))
        color = (0, 180, 0) if stable and accepted_geometry else (0, 165, 255)
        cv2.drawContours(canvas, [np.round(detection.contour).astype(np.int32)], -1, color, 2)
        cv2.polylines(canvas, [measurement.box_px], True, (255, 90, 0), 2)
        label = detection.label if detection.label != "Vật thể" else "vat the dang hop"
        conf_text = f" {detection.confidence:.2f}" if detection.confidence is not None else ""
        cv2.putText(canvas, f"{label}{conf_text}: {median[0]:.1f} x {median[1]:.1f} mm",
                    (max(10, measurement.center_px[0] - 190), max(30, measurement.center_px[1] - 30)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.72, color, 2, cv2.LINE_AA)
        if not accepted_geometry:
            self.last_result = None
            self.result_var.set(f"TỪ CHỐI: hình dạng chưa đủ chữ nhật ({rectangularity:.0%})")
        elif not stable:
            self.last_result = None
            self.result_var.set(f"Đang ổn định {len(self.history)}/{stable_count}: {median[0]:.1f} × {median[1]:.1f} mm")
        else:
            self.last_result = {
                "timestamp": datetime.now().isoformat(timespec="milliseconds"), "frame_id": self.frame_id,
                "label": label, "confidence": detection.confidence, "length_mm": float(median[0]),
                "width_mm": float(median[1]), "rectangularity": rectangularity, "stability_cv": cv,
                "distance_cm": float(self.distance_cm_var.get()), "plane_source": self.plane_source,
                "intrinsic_calibrated": bool(self.calibration and not self.calibration.approximate),
            }
            self.result_var.set(f"{median[0]:.1f} × {median[1]:.1f} mm | ổn định {max(0.0, 1.0-cv):.1%} | hình học {rectangularity:.0%}")
        intrinsic = "đã hiệu chuẩn nội tại" if self.calibration and not self.calibration.approximate else "chưa hiệu chuẩn nội tại"
        yolo = f" | YOLO {self.inference_ms:.0f} ms" if self.detector_var.get() != "Contour (nhanh)" else ""
        if self.yolo_error:
            yolo = " | YOLO lỗi, đang dùng contour"
        if time.monotonic() >= self.notice_until:
            self.status_var.set(f"{intrinsic} | {self.plane_source}{yolo}")
        return canvas

    def _update_frame(self):
        if not self.running or self.capture is None:
            return
        ok, frame = self.capture.read()
        if not ok:
            self.stop()
            self.result_var.set("Mất tín hiệu camera")
            return
        self.frame_id += 1
        frame = self._undistort(frame)
        self.last_frame = frame.copy()
        self.recent_frames.append(frame.copy())
        annotated = self._annotate(frame)
        self.last_annotated = annotated.copy()
        self._show_frame(annotated)
        self.root.after(15, self._update_frame)

    def _show_frame(self, frame: np.ndarray):
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        area_w, area_h = max(900, self.video_label.winfo_width()), max(560, self.video_label.winfo_height())
        scale = min(area_w / image.width, area_h / image.height)
        shown_w, shown_h = max(1, int(image.width * scale)), max(1, int(image.height * scale))
        self.display_scale = scale
        self.display_offset = ((area_w - shown_w) // 2, (area_h - shown_h) // 2)
        photo = ImageTk.PhotoImage(image.resize((shown_w, shown_h), Image.Resampling.LANCZOS))
        self.video_label.configure(image=photo)
        self.video_label.image = photo

    @staticmethod
    def _write_png(output: Path, image: np.ndarray):
        ok, encoded = cv2.imencode(".png", image)
        if not ok:
            raise OSError("OpenCV không mã hóa được ảnh PNG")
        encoded.tofile(str(output))
        if not output.exists() or output.stat().st_size == 0:
            raise OSError("Tệp ảnh không được tạo")

    @staticmethod
    def _append_csv_row(result: dict):
        existing_rows: list[dict] = []
        rewrite = False
        if RESULTS_FILE.exists() and RESULTS_FILE.stat().st_size > 0:
            with RESULTS_FILE.open("r", newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                existing_rows = list(reader)
                rewrite = list(reader.fieldnames or []) != RESULT_FIELDS
        mode = "w" if rewrite or not RESULTS_FILE.exists() else "a"
        with RESULTS_FILE.open(mode, newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
            if mode == "w":
                writer.writeheader()
                for row in existing_rows:
                    writer.writerow({key: row.get(key, "") for key in RESULT_FIELDS})
            writer.writerow({key: result.get(key, "") for key in RESULT_FIELDS})

    def save_sample(self):
        if self.last_annotated is None or self.last_result is None:
            messagebox.showwarning("Chưa có phép đo hợp lệ",
                                   "Giữ vật ổn định đến khi kết quả được chấp nhận rồi mới lưu mẫu.")
            return
        try:
            true_l = float(self.true_length_var.get())
            true_w = float(self.true_width_var.get())
        except (ValueError, tk.TclError):
            messagebox.showwarning("Kích thước chuẩn không hợp lệ", "Hãy nhập D và R bằng đơn vị mm.")
            return
        if true_l <= 0 or true_w <= 0:
            messagebox.showwarning("Thiếu kích thước chuẩn",
                                   "Hãy nhập kích thước thật D × R trước khi lưu mẫu.")
            return

        # Tkinter xử lý nút bấm và cập nhật khung hình trên cùng một luồng; hai bản sao
        # này vì vậy thuộc chính xác cùng một khung hình và không thể lệch nhau.
        annotated = self.last_annotated.copy()
        result = dict(self.last_result)
        true_l, true_w = sorted((true_l, true_w), reverse=True)
        result.update({
            "true_length_mm": true_l,
            "true_width_mm": true_w,
            "abs_error_length_mm": abs(result["length_mm"] - true_l),
            "abs_error_width_mm": abs(result["width_mm"] - true_w),
            "ape_length_pct": abs(result["length_mm"] - true_l) / true_l * 100.0,
            "ape_width_pct": abs(result["width_mm"] - true_w) / true_w * 100.0,
        })

        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        captured_at = datetime.now()
        sample_id = f"measurement_{captured_at:%Y%m%d_%H%M%S_%f}"
        output = SNAPSHOTS_DIR / f"{sample_id}.png"
        result.update({
            "sample_id": sample_id,
            "image_file": str(output.relative_to(ROOT)),
            "timestamp": captured_at.isoformat(timespec="milliseconds"),
        })
        try:
            self._write_png(output, annotated)
            self._append_csv_row(result)
        except (OSError, PermissionError, cv2.error) as exc:
            if output.exists():
                output.unlink()
            messagebox.showerror("Không lưu được mẫu",
                                 f"Không thể lưu đồng thời ảnh và số liệu.\n\n{exc}\n\n"
                                 "Nếu measurements.csv đang mở trong Excel, hãy đóng file rồi thử lại.")
            return
        self.notice_until = time.monotonic() + 4.0
        self.status_var.set(f"ĐÃ LƯU CÙNG MỘT MẪU: {output.name} + measurements.csv")

    def close(self):
        self.stop()
        self.inference_stop.set()
        self.inference_event.set()
        if self.inference_thread.is_alive():
            self.inference_thread.join(timeout=1.0)
        self.root.destroy()


def main():
    root = tk.Tk()
    MeasurementApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
