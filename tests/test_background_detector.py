import cv2
import numpy as np

from src.detectors import BackgroundDifferenceDetector


def synthetic_scene():
    background = np.full((480, 640, 3), (95, 135, 165), dtype=np.uint8)
    cv2.line(background, (0, 80), (639, 80), (100, 140, 170), 4)
    current = background.copy()
    rectangle = ((330, 250), (230, 130), 17)
    box = cv2.boxPoints(rectangle).round().astype(np.int32)
    cv2.fillConvexPoly(current, box, (230, 230, 225))
    inner_start = tuple(np.round(0.9 * box[0] + 0.1 * box[2]).astype(int))
    inner_end = tuple(np.round(0.1 * box[0] + 0.9 * box[2]).astype(int))
    cv2.line(current, inner_start, inner_end, (20, 20, 20), 8)
    cv2.putText(current, "TEXTURE", (245, 255), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    return background, current


def test_background_detector_ignores_internal_texture():
    background, current = synthetic_scene()
    detector = BackgroundDifferenceDetector(min_area_px=2000, difference_threshold=20)
    detector.set_background(background)
    detections = detector.detect(current, 4)
    assert len(detections) == 1
    (_, _), (a, b), _ = cv2.minAreaRect(detections[0].contour)
    measured = sorted((a, b), reverse=True)
    assert abs(measured[0] - 230) < 8
    assert abs(measured[1] - 130) < 8


def test_background_detector_requires_reference():
    _, current = synthetic_scene()
    detector = BackgroundDifferenceDetector()
    assert detector.detect(current, 4) == []
