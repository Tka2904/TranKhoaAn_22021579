from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Detection:
    contour: np.ndarray
    label: str
    confidence: float | None = None


class YoloSegmenter:
    def __init__(self, model_path: str, image_size: int = 640):
        from ultralytics import YOLO
        import torch

        self.model = YOLO(model_path)
        self.image_size = int(image_size)
        self.device = 0 if torch.cuda.is_available() else "cpu"

    def detect(self, frame: np.ndarray, confidence: float, max_objects: int) -> list[Detection]:
        results = self.model.predict(
            source=frame,
            conf=float(confidence),
            imgsz=self.image_size,
            device=self.device,
            retina_masks=False,
            verbose=False,
        )
        result = results[0]
        if result.masks is None or result.boxes is None:
            return []

        class_ids = result.boxes.cls.detach().cpu().numpy().astype(int)
        scores = result.boxes.conf.detach().cpu().numpy()
        names = result.names
        detections: list[Detection] = []
        for polygon, class_id, score in zip(result.masks.xy, class_ids, scores):
            contour = np.asarray(polygon, dtype=np.float32).reshape(-1, 1, 2)
            if len(contour) < 3:
                continue
            detections.append(Detection(contour, str(names[class_id]), float(score)))

        detections.sort(key=lambda item: cv2.contourArea(item.contour), reverse=True)
        return detections[:max_objects]


class ClassicalContourDetector:
    """Fallback detector for objects that are not among the pretrained YOLO classes."""

    def __init__(self, min_area_px: int = 2500):
        self.min_area_px = int(min_area_px)

    def detect(self, frame: np.ndarray, max_objects: int) -> list[Detection]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(gray, 40, 120)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        height, width = gray.shape
        frame_area = height * width
        selected: list[Detection] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area_px or area > frame_area * 0.75:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            if x <= 2 or y <= 2 or x + w >= width - 2 or y + h >= height - 2:
                continue
            selected.append(Detection(contour.astype(np.float32), "Vật thể"))

        selected.sort(key=lambda item: cv2.contourArea(item.contour), reverse=True)
        return selected[:max_objects]


class BackgroundDifferenceDetector:
    """Segment foreground objects against a fixed, previously captured background."""

    def __init__(
        self,
        min_area_px: int = 2500,
        difference_threshold: float = 24.0,
        open_kernel: int = 5,
        close_kernel: int = 19,
    ):
        self.min_area_px = int(min_area_px)
        self.difference_threshold = float(difference_threshold)
        self.open_kernel = self._odd_kernel(open_kernel)
        self.close_kernel = self._odd_kernel(close_kernel)
        self.background: np.ndarray | None = None

    @staticmethod
    def _odd_kernel(value: int) -> int:
        value = max(1, int(value))
        return value if value % 2 else value + 1

    @property
    def ready(self) -> bool:
        return self.background is not None

    def set_background(self, frame: np.ndarray | None):
        if frame is None:
            self.background = None
            return
        self.background = np.asarray(frame, dtype=np.uint8).copy()

    def _foreground_mask(self, frame: np.ndarray) -> np.ndarray | None:
        if self.background is None or self.background.shape != frame.shape:
            return None

        current_lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
        background_lab = cv2.cvtColor(self.background, cv2.COLOR_BGR2LAB).astype(np.float32)

        delta = np.abs(current_lab - background_lab)
        # Chroma receives a slightly larger weight so illumination-only changes
        # are less likely to become a false object or shadow.
        score = 0.45 * delta[:, :, 0] + 0.80 * np.maximum(delta[:, :, 1], delta[:, :, 2])
        mask = np.where(score >= self.difference_threshold, 255, 0).astype(np.uint8)

        open_element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.open_kernel, self.open_kernel))
        close_element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.close_kernel, self.close_kernel))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, open_element, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_element, iterations=1)
        return mask

    def detect(self, frame: np.ndarray, max_objects: int) -> list[Detection]:
        mask = self._foreground_mask(frame)
        if mask is None:
            return []

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        height, width = mask.shape
        frame_area = height * width
        selected: list[Detection] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area_px or area > frame_area * 0.75:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            if x <= 2 or y <= 2 or x + w >= width - 2 or y + h >= height - 2:
                continue

            # Fill small holes caused by labels and printed textures while
            # preserving the observed outer silhouette for metric measurement.
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            if hull_area <= 0 or area / hull_area < 0.70:
                continue
            selected.append(Detection(hull.astype(np.float32), "Vật thể"))

        selected.sort(key=lambda item: cv2.contourArea(item.contour), reverse=True)
        return selected[:max_objects]
