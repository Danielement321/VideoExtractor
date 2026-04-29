from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np

from .models import OcrResult


class OcrEngine(Protocol):
    def recognize(self, image: np.ndarray) -> OcrResult:
        ...

    def recognize_many(self, images: list[np.ndarray]) -> list[OcrResult]:
        ...


def save_debug_frame(image: np.ndarray, directory: Path, stem: str, index: int) -> None:
    import cv2

    directory.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(directory / f"{stem}_{index:05d}.png"), image)
