from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class OcrResult:
    text: str
    confidence: float


@dataclass(slots=True)
class SubtitleSegment:
    start: float
    end: float
    text: str
    confidence: float = 1.0

    def duration(self) -> float:
        return max(0.0, self.end - self.start)
