from video_subtitle_extractor.deepseek import DeepSeekClient
from video_subtitle_extractor.models import SubtitleSegment


class UnavailableClient(DeepSeekClient):
    def available(self) -> bool:
        return False


class FakeClient(DeepSeekClient):
    def available(self) -> bool:
        return True

    def _request_replacements(self, segments, target_indices):  # type: ignore[no-untyped-def]
        return [{"index": target_indices[0], "text": "修正文本"}]


def test_deepseek_skips_without_key() -> None:
    segments = [SubtitleSegment(0, 1, "原文", 0.4)]
    assert UnavailableClient().refine(
        segments, mode="cleanup", confidence_threshold=0.7
    ) == segments


def test_low_confidence_refines_only_low_confidence_segments() -> None:
    segments = [
        SubtitleSegment(0, 1, "错文", 0.4),
        SubtitleSegment(1, 2, "正确", 0.9),
    ]
    refined = FakeClient().refine(
        segments, mode="low-confidence", confidence_threshold=0.7
    )
    assert refined[0].text == "修正文本"
    assert refined[1].text == "正确"
