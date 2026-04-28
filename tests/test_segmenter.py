from video_subtitle_extractor.models import OcrResult
from video_subtitle_extractor.segmenter import build_segments


def test_build_segments_merges_similar_adjacent_samples() -> None:
    segments = build_segments(
        [
            (0.0, OcrResult("你好 世界", 0.9)),
            (0.5, OcrResult("你好世界", 0.8)),
            (1.0, OcrResult("", 0.0)),
            (2.0, OcrResult("下一句", 0.9)),
        ],
        frame_interval=0.5,
        min_confidence=0.5,
        similarity_threshold=0.8,
        min_duration=0.1,
        max_gap=0.75,
    )

    assert len(segments) == 2
    assert segments[0].start == 0.0
    assert segments[0].end == 1.0
    assert segments[0].text == "你好世界"
    assert segments[1].text == "下一句"


def test_build_segments_filters_low_confidence() -> None:
    segments = build_segments(
        [(0.0, OcrResult("低置信度", 0.2))],
        frame_interval=0.5,
        min_confidence=0.5,
        similarity_threshold=0.8,
        min_duration=0.1,
        max_gap=0.75,
    )
    assert segments == []
