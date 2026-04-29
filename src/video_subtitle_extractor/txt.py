from __future__ import annotations

from .models import SubtitleSegment
from .srt import format_timestamp


def render_txt(segments: list[SubtitleSegment]) -> str:
    lines = [
        f"{format_timestamp(segment.start)} --> {format_timestamp(segment.end)} {segment.text}"
        for segment in segments
    ]
    return "\n".join(lines) + ("\n" if lines else "")
