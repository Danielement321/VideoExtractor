from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .api_ocr import ApiOcrMode
from .pipeline import ExtractConfig, process_directory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract Chinese hard subtitles from videos into SRT files."
    )
    parser.add_argument("--input-dir", type=Path, default=Path("videos"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--frame-interval", type=float, default=0.5)
    parser.add_argument("--roi-bottom-ratio", type=float, default=0.30)
    parser.add_argument("--min-confidence", type=float, default=0.1)
    parser.add_argument("--similarity-threshold", type=float, default=0.82)
    parser.add_argument("--min-duration", type=float, default=0.35)
    parser.add_argument("--max-gap", type=float, default=1.0)
    parser.add_argument("--debug-frames", type=Path)
    parser.add_argument(
        "--api-batch-size",
        type=int,
        default=4,
        help="Number of sampled subtitle crops sent in each API OCR request.",
    )
    parser.add_argument(
        "--api-ocr-mode",
        choices=["off", "cleanup", "low-confidence"],
        default="off",
        help="Optional second-pass API text cleanup after image OCR.",
    )
    parser.add_argument("--api-ocr-confidence-threshold", type=float, default=0.70)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = ExtractConfig(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        frame_interval=args.frame_interval,
        roi_bottom_ratio=args.roi_bottom_ratio,
        min_confidence=args.min_confidence,
        similarity_threshold=args.similarity_threshold,
        min_duration=args.min_duration,
        max_gap=args.max_gap,
        debug_frames=args.debug_frames,
        api_batch_size=args.api_batch_size,
        api_ocr_mode=args.api_ocr_mode,  # type: ignore[arg-type]
        api_ocr_confidence_threshold=args.api_ocr_confidence_threshold,
    )
    try:
        process_directory(config)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
