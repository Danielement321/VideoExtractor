from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import numpy as np


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


def find_videos(input_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )


def crop_bottom_roi(frame: np.ndarray, ratio: float) -> np.ndarray:
    ratio = min(max(ratio, 0.05), 1.0)
    height = frame.shape[0]
    start_y = int(height * (1.0 - ratio))
    return frame[start_y:height, :]


def preprocess_for_ocr(frame: np.ndarray) -> np.ndarray:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV is not installed. Install with: python3 -m pip install -e ."
        ) from exc

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    scale = 2.0
    enlarged = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    normalized = cv2.equalizeHist(enlarged)
    return normalized


def iter_video_samples(
    video_path: Path,
    *,
    frame_interval: float,
    roi_bottom_ratio: float,
) -> Iterator[tuple[float, np.ndarray]]:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV is not installed. Install with: python3 -m pip install -e ."
        ) from exc

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if frame_count else 0.0
    timestamp = 0.0

    try:
        while True:
            if duration and timestamp > duration:
                break
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ok, frame = cap.read()
            if not ok:
                break
            roi = crop_bottom_roi(frame, roi_bottom_ratio)
            yield timestamp, preprocess_for_ocr(roi)
            timestamp += frame_interval
    finally:
        cap.release()
