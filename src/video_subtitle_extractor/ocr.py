from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np

from .models import OcrResult
from .text import clean_text


class OcrEngine(Protocol):
    def recognize(self, image: np.ndarray) -> OcrResult:
        ...


class PaddleOcrEngine:
    def __init__(self) -> None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                "PaddleOCR is not installed. Install with: "
                'python3 -m pip install -e ".[ocr]"'
            ) from exc

        try:
            self._ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        except TypeError:
            self._ocr = PaddleOCR(use_angle_cls=True, lang="ch")

    def recognize(self, image: np.ndarray) -> OcrResult:
        result = self._ocr.ocr(image, cls=True)
        texts: list[str] = []
        confidences: list[float] = []

        for page in result or []:
            for item in page or []:
                if len(item) < 2:
                    continue
                text_info = item[1]
                if not text_info:
                    continue
                text = clean_text(str(text_info[0]))
                confidence = float(text_info[1])
                if text:
                    texts.append(text)
                    confidences.append(confidence)

        if not texts:
            return OcrResult("", 0.0)
        return OcrResult("".join(texts), sum(confidences) / len(confidences))


def save_debug_frame(image: np.ndarray, directory: Path, stem: str, index: int) -> None:
    import cv2

    directory.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(directory / f"{stem}_{index:05d}.png"), image)
