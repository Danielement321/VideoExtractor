from __future__ import annotations

from .models import OcrResult, SubtitleSegment
from .text import choose_better_text, clean_text, is_noise, text_similarity


def build_segments(
    samples: list[tuple[float, OcrResult]],
    *,
    frame_interval: float,
    min_confidence: float,
    similarity_threshold: float,
    min_duration: float,
    max_gap: float,
) -> list[SubtitleSegment]:
    segments: list[SubtitleSegment] = []
    current: SubtitleSegment | None = None

    for timestamp, result in samples:
        text = clean_text(result.text)
        if result.confidence < min_confidence or is_noise(text):
            if current is not None and timestamp - current.end > max_gap:
                segments.append(current)
                current = None
            continue

        sample_start = timestamp
        sample_end = timestamp + frame_interval

        if current is None:
            current = SubtitleSegment(sample_start, sample_end, text, result.confidence)
            continue

        similar = text_similarity(current.text, text) >= similarity_threshold
        close_enough = sample_start - current.end <= max_gap
        if similar and close_enough:
            current.end = sample_end
            current.text = choose_better_text(current.text, text)
            current.confidence = max(current.confidence, result.confidence)
        else:
            segments.append(current)
            current = SubtitleSegment(sample_start, sample_end, text, result.confidence)

    if current is not None:
        segments.append(current)

    return [segment for segment in segments if segment.duration() >= min_duration]
