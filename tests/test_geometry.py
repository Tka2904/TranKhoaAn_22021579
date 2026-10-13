import cv2
import numpy as np

from src.measurement import marker_homography, measure_contour


def test_axis_aligned_measurement():
    marker = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], np.float32)
    homography = marker_homography(marker, 50.0)
    contour = np.array(
        [[150, 100], [350, 100], [350, 200], [150, 200]], np.float32
    ).reshape(-1, 1, 2)
    result = measure_contour(contour, homography)
    assert result is not None
    assert abs(result.length_mm - 100.0) < 0.01
    assert abs(result.width_mm - 50.0) < 0.01


def test_perspective_measurement():
    metric_marker = np.array([[0, 0], [50, 0], [50, 50], [0, 50]], np.float32)
    image_marker = np.array([[90, 70], [230, 85], [210, 220], [70, 190]], np.float32)
    image_from_metric = cv2.getPerspectiveTransform(metric_marker, image_marker)
    metric_object = np.array([[70, 10], [190, 10], [190, 50], [70, 50]], np.float32)
    image_object = cv2.perspectiveTransform(
        metric_object.reshape(-1, 1, 2), image_from_metric
    )
    result = measure_contour(image_object, marker_homography(image_marker, 50.0))
    assert result is not None
    assert abs(result.length_mm - 120.0) < 0.05
    assert abs(result.width_mm - 40.0) < 0.05

