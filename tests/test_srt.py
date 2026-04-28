from video_subtitle_extractor.models import SubtitleSegment
from video_subtitle_extractor.srt import format_timestamp, render_srt


def test_format_timestamp_rounds_to_milliseconds() -> None:
    assert format_timestamp(3661.2344) == "01:01:01,234"
    assert format_timestamp(0) == "00:00:00,000"


def test_render_srt() -> None:
    text = render_srt([SubtitleSegment(0, 1.5, "你好")])
    assert text == "1\n00:00:00,000 --> 00:00:01,500\n你好\n"
