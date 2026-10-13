from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class Measurement:
    length_mm: float
    width_mm: float
    center_px: tuple[int, int]
    box_px: np.ndarray


@dataclass
class CameraCalibration:
    camera_matrix: np.ndarray
    distortion: np.ndarray
    image_size: tuple[int, int]
    approximate: bool = False


@dataclass
class MarkerPose:
    rvec: np.ndarray
    tvec: np.ndarray
    corners: np.ndarray
    reprojection_error_px: float


@dataclass
class Segment3D:
    start_mm: np.ndarray
    end_mm: np.ndarray
    kind: str

    @property
    def distance_mm(self) -> float:
        return float(np.linalg.norm(self.end_mm - self.start_mm))


def marker_homography(marker_corners: np.ndarray, marker_size_mm: float) -> np.ndarray:
    """Map image points on the marker plane to coordinates measured in mm."""
    src = np.asarray(marker_corners, dtype=np.float32).reshape(4, 2)
    size = float(marker_size_mm)
    dst = np.array([[0, 0], [size, 0], [size, size], [0, size]], dtype=np.float32)
    return cv2.getPerspectiveTransform(src, dst)


def transform_points(points: np.ndarray, homography: np.ndarray) -> np.ndarray:
    pts = np.asarray(points, dtype=np.float32).reshape(-1, 1, 2)
    return cv2.perspectiveTransform(pts, homography).reshape(-1, 2)


def measure_contour(contour: np.ndarray, homography: np.ndarray) -> Measurement | None:
    """Measure a contour after rectifying it into the marker's metric plane."""
    if contour is None or len(contour) < 3:
        return None
    metric_points = transform_points(contour, homography)
    rect_mm = cv2.minAreaRect(metric_points.astype(np.float32))
    (_, _), (side_a, side_b), _ = rect_mm
    if side_a <= 0 or side_b <= 0:
        return None
    length_mm, width_mm = sorted((float(side_a), float(side_b)), reverse=True)
    box_mm = cv2.boxPoints(rect_mm)
    box_px = transform_points(box_mm, np.linalg.inv(homography))
    center = tuple(np.mean(box_px, axis=0).round().astype(int))
    return Measurement(length_mm, width_mm, (int(center[0]), int(center[1])), np.round(box_px).astype(np.int32))


def default_camera_calibration(width: int, height: int, horizontal_fov_deg: float = 68.0) -> CameraCalibration:
    """Create a pinhole approximation until a real calibration is supplied."""
    focal = width / (2.0 * np.tan(np.deg2rad(horizontal_fov_deg) / 2.0))
    matrix = np.array([[focal, 0, width / 2.0], [0, focal, height / 2.0], [0, 0, 1]], dtype=np.float64)
    return CameraCalibration(matrix, np.zeros((1, 5), dtype=np.float64), (width, height), approximate=True)


def load_camera_calibration(path: str | Path, width: int, height: int, horizontal_fov_deg: float = 68.0) -> CameraCalibration:
    calibration_path = Path(path)
    if not calibration_path.exists():
        return default_camera_calibration(width, height, horizontal_fov_deg)
    data = np.load(calibration_path)
    matrix = np.asarray(data["camera_matrix"], dtype=np.float64).copy()
    distortion = np.asarray(data["distortion"], dtype=np.float64)
    saved_size = tuple(int(v) for v in np.asarray(data.get("image_size", (width, height))).reshape(-1)[:2])
    if saved_size != (width, height):
        sx, sy = width / saved_size[0], height / saved_size[1]
        matrix[0, :] *= sx
        matrix[1, :] *= sy
        matrix[2, 2] = 1.0
    return CameraCalibration(matrix, distortion, (width, height), approximate=False)


class MarkerTracker:
    """Reusable ArUco detector and pose estimator."""

    def __init__(self):
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()
        parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self.detector = cv2.aruco.ArucoDetector(dictionary, parameters)

    def detect(self, frame: np.ndarray, marker_id: int) -> tuple[np.ndarray | None, np.ndarray | None]:
        corners, ids, _ = self.detector.detectMarkers(frame)
        if ids is None:
            return None, None
        flat_ids = ids.flatten()
        matches = np.where(flat_ids == int(marker_id))[0]
        if not len(matches):
            return None, flat_ids
        selected = np.asarray(corners[int(matches[0])], dtype=np.float32).reshape(4, 2)
        return selected, flat_ids

    def estimate_pose(self, frame: np.ndarray, marker_id: int, marker_size_mm: float, calibration: CameraCalibration) -> MarkerPose | None:
        corners, _ = self.detect(frame, marker_id)
        if corners is None:
            return None
        half = float(marker_size_mm) / 2.0
        object_points = np.array(
            [[-half, half, 0], [half, half, 0], [half, -half, 0], [-half, -half, 0]], dtype=np.float64
        )
        ok, rvec, tvec = cv2.solvePnP(
            object_points, corners.astype(np.float64), calibration.camera_matrix, calibration.distortion,
            flags=cv2.SOLVEPNP_IPPE_SQUARE,
        )
        if not ok:
            return None
        projected, _ = cv2.projectPoints(object_points, rvec, tvec, calibration.camera_matrix, calibration.distortion)
        error = float(np.sqrt(np.mean(np.sum((projected.reshape(-1, 2) - corners) ** 2, axis=1))))
        return MarkerPose(rvec.reshape(3, 1), tvec.reshape(3, 1), corners, error)


_DEFAULT_TRACKER = MarkerTracker()


def find_reference_marker(frame: np.ndarray, marker_id: int, marker_size_mm: float) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
    """Backward-compatible 2D marker lookup."""
    corners, ids = _DEFAULT_TRACKER.detect(frame, marker_id)
    if corners is None:
        return None, None, ids
    return marker_homography(corners, marker_size_mm), corners, ids


def camera_center_world(pose: MarkerPose) -> np.ndarray:
    rotation, _ = cv2.Rodrigues(pose.rvec)
    return (-rotation.T @ pose.tvec).reshape(3)


def pixel_ray_world(pixel: tuple[float, float], pose: MarkerPose, calibration: CameraCalibration) -> tuple[np.ndarray, np.ndarray]:
    point = np.asarray(pixel, dtype=np.float64).reshape(1, 1, 2)
    normalized = cv2.undistortPoints(point, calibration.camera_matrix, calibration.distortion).reshape(2)
    ray_camera = np.array([normalized[0], normalized[1], 1.0], dtype=np.float64)
    rotation, _ = cv2.Rodrigues(pose.rvec)
    direction = rotation.T @ ray_camera
    direction /= np.linalg.norm(direction)
    return camera_center_world(pose), direction


def pixel_to_marker_plane(pixel: tuple[float, float], pose: MarkerPose, calibration: CameraCalibration) -> np.ndarray | None:
    origin, direction = pixel_ray_world(pixel, pose, calibration)
    if abs(direction[2]) < 1e-8:
        return None
    scale = -origin[2] / direction[2]
    if scale <= 0:
        return None
    point = origin + scale * direction
    point[2] = 0.0
    return point


def pixel_to_vertical_point(pixel: tuple[float, float], base_world: np.ndarray, pose: MarkerPose, calibration: CameraCalibration) -> np.ndarray | None:
    """Infer a point on the line normal to the marker plane through base_world."""
    origin, ray = pixel_ray_world(pixel, pose, calibration)
    camera = camera_center_world(pose)
    normal = np.array([0.0, 0.0, 1.0 if camera[2] >= 0 else -1.0])
    system = np.column_stack((ray, -normal))
    if np.linalg.cond(system.T @ system) > 1e8:
        return None
    ray_scale, height = np.linalg.lstsq(system, np.asarray(base_world) - origin, rcond=None)[0]
    if ray_scale <= 0:
        return None
    return np.asarray(base_world, dtype=np.float64) + normal * height


def project_world_points(points: np.ndarray, pose: MarkerPose, calibration: CameraCalibration) -> np.ndarray | None:
    points = np.asarray(points, dtype=np.float64).reshape(-1, 3)
    projected, _ = cv2.projectPoints(points, pose.rvec, pose.tvec, calibration.camera_matrix, calibration.distortion)
    result = projected.reshape(-1, 2)
    return result if np.all(np.isfinite(result)) else None


def point_inside_polygon(point: tuple[int, int], polygon: np.ndarray) -> bool:
    return cv2.pointPolygonTest(np.asarray(polygon, dtype=np.float32), point, False) >= 0
