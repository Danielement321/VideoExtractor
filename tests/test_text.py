from video_subtitle_extractor.text import clean_text, is_noise, text_similarity


def test_clean_text_removes_whitespace() -> None:
    assert clean_text(" 你 好\n世 界 ") == "你好世界"


def test_is_noise() -> None:
    assert is_noise("")
    assert is_noise("----")
    assert not is_noise("中文")


def test_text_similarity() -> None:
    assert text_similarity("你好世界", "你好 世界") == 1.0
    assert text_similarity("你好", "再见") < 0.5
