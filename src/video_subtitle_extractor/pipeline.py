from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .deepseek import DeepSeekClient, DeepSeekMode
from .models import OcrResult, SubtitleSegment
from .ocr import OcrEngine, PaddleOcrEngine, save_debug_frame
from .segmenter import build_segments
from .srt import render_srt
from .video import find_videos, iter_video_samples


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
    deepseek_mode: DeepSeekMode = "off"
    deepseek_confidence_threshold: float = 0.70


def extract_video(
    video_path: Path,
    config: ExtractConfig,
    *,
    ocr_engine: OcrEngine | None = None,
    deepseek_client: DeepSeekClient | None = None,
) -> list[SubtitleSegment]:
    engine = ocr_engine or PaddleOcrEngine()
    samples: list[tuple[float, OcrResult]] = []

    for index, (timestamp, image) in enumerate(
        iter_video_samples(
            video_path,
            frame_interval=config.frame_interval,
            roi_bottom_ratio=config.roi_bottom_ratio,
        )
    ):
        if config.debug_frames is not None:
            save_debug_frame(image, config.debug_frames, video_path.stem, index)
        samples.append((timestamp, engine.recognize(image)))

    segments = build_segments(
        samples,
        frame_interval=config.frame_interval,
        min_confidence=config.min_confidence,
        similarity_threshold=config.similarity_threshold,
        min_duration=config.min_duration,
        max_gap=config.max_gap,
    )
    client = deepseek_client or DeepSeekClient()
    return client.refine(
        segments,
        mode=config.deepseek_mode,
        confidence_threshold=config.deepseek_confidence_threshold,
    )


def process_directory(config: ExtractConfig) -> list[Path]:
    if not config.input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {config.input_dir}")
    config.output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    videos = find_videos(config.input_dir)
    if not videos:
        print(f"No videos found in {config.input_dir}")
        return written

    for video_path in videos:
        print(f"Processing {video_path}")
        segments = extract_video(video_path, config)
        output_path = config.output_dir / f"{video_path.stem}.srt"
        output_path.write_text(render_srt(segments), encoding="utf-8")
        print(f"Wrote {output_path} ({len(segments)} segments)")
        written.append(output_path)
    return written
