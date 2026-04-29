from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .api_ocr import ApiOcrClient, ApiOcrMode
from .models import OcrResult, SubtitleSegment
from .ocr import OcrEngine, save_debug_frame
from .segmenter import build_segments
from .srt import format_timestamp, render_srt
from .txt import render_txt
from .video import find_videos, get_video_duration, iter_video_samples


@dataclass(slots=True)
class ExtractConfig:
    input_dir: Path = Path("videos")
    output_dir: Path = Path("outputs")
    frame_interval: float = 0.5
    roi_bottom_ratio: float = 0.30
    min_confidence: float = 0.55
    similarity_threshold: float = 0.82
    min_duration: float = 0.35
    max_gap: float = 1.0
    debug_frames: Path | None = None
    api_batch_size: int = 4
    api_ocr_mode: ApiOcrMode = "off"
    api_ocr_confidence_threshold: float = 0.70


def extract_video(
    video_path: Path,
    config: ExtractConfig,
    *,
    output_path: Path | None = None,
    ocr_engine: OcrEngine | None = None,
    api_ocr_client: ApiOcrClient | None = None,
) -> list[SubtitleSegment]:
    engine = ocr_engine or ApiOcrClient()
    if ocr_engine is None and not engine.available():
        raise RuntimeError("API_OCR_API_KEY is required for API image OCR")
    duration = get_video_duration(video_path)
    total_samples = int(duration // config.frame_interval) + 1 if duration else 0
    samples: list[tuple[float, OcrResult]] = []
    batch_timestamps: list[float] = []
    batch_images: list[np.ndarray] = []
    processed_samples = 0

    def build_current_segments() -> list[SubtitleSegment]:
        return build_segments(
            samples,
            frame_interval=config.frame_interval,
            min_confidence=config.min_confidence,
            similarity_threshold=config.similarity_threshold,
            min_duration=config.min_duration,
            max_gap=config.max_gap,
            max_end=duration,
        )

    def save_current_segments(segments: list[SubtitleSegment]) -> None:
        if output_path is None:
            return
        write_outputs_atomic(output_path, segments)

    def flush_batch() -> None:
        nonlocal batch_timestamps, batch_images, processed_samples
        if not batch_images:
            return
        batch_start = processed_samples + 1
        results = engine.recognize_many(batch_images)
        if len(results) != len(batch_timestamps):
            raise RuntimeError("OCR result count does not match sampled frame count")
        samples.extend(zip(batch_timestamps, results, strict=True))
        processed_samples += len(results)
        batch_end = processed_samples
        total_label = str(total_samples) if total_samples else "?"
        print(f"OCR progress: {batch_end}/{total_label} frames", flush=True)
        for offset, (timestamp, result) in enumerate(
            zip(batch_timestamps, results, strict=True),
            start=batch_start,
        ):
            text = result.text or "<empty>"
            print(f"  [{offset}] {format_timestamp(timestamp)} {text}", flush=True)
        save_current_segments(build_current_segments())
        batch_timestamps = []
        batch_images = []

    for index, (timestamp, image) in enumerate(
        iter_video_samples(
            video_path,
            frame_interval=config.frame_interval,
            roi_bottom_ratio=config.roi_bottom_ratio,
        )
    ):
        if config.debug_frames is not None:
            save_debug_frame(image, config.debug_frames, video_path.stem, index)
        batch_timestamps.append(timestamp)
        batch_images.append(image)
        if len(batch_images) >= max(1, config.api_batch_size):
            flush_batch()

    flush_batch()

    segments = build_current_segments()
    client = api_ocr_client or ApiOcrClient()
    segments = client.refine(
        segments,
        mode=config.api_ocr_mode,
        confidence_threshold=config.api_ocr_confidence_threshold,
    )
    save_current_segments(segments)
    return segments


def write_srt_atomic(output_path: Path, segments: list[SubtitleSegment]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temp_path.write_text(render_srt(segments), encoding="utf-8")
    temp_path.replace(output_path)


def write_txt_atomic(output_path: Path, segments: list[SubtitleSegment]) -> None:
    txt_path = output_path.with_suffix(".txt")
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = txt_path.with_suffix(f"{txt_path.suffix}.tmp")
    temp_path.write_text(render_txt(segments), encoding="utf-8")
    temp_path.replace(txt_path)


def write_outputs_atomic(output_path: Path, segments: list[SubtitleSegment]) -> None:
    write_srt_atomic(output_path, segments)
    write_txt_atomic(output_path, segments)


def process_directory(config: ExtractConfig) -> list[Path]:
    if not config.input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {config.input_dir}")
    if not ApiOcrClient().available():
        raise RuntimeError("API_OCR_API_KEY is required for API image OCR")
    config.output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    videos = find_videos(config.input_dir)
    if not videos:
        print(f"No videos found in {config.input_dir}")
        return written

    for video_path in videos:
        output_path = config.output_dir / f"{video_path.stem}.srt"
        print(f"Processing {video_path}")
        print(f"Realtime SRT: {output_path}")
        segments = extract_video(video_path, config, output_path=output_path)
        write_outputs_atomic(output_path, segments)
        print(f"Wrote {output_path} ({len(segments)} segments)")
        written.append(output_path)
    return written
