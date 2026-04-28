from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Literal

from .models import SubtitleSegment
from .text import clean_text


DeepSeekMode = Literal["off", "cleanup", "low-confidence"]


class DeepSeekClient:
    def __init__(self) -> None:
        self.api_key = os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")

    def available(self) -> bool:
        return bool(self.api_key)

    def refine(
        self,
        segments: list[SubtitleSegment],
        *,
        mode: DeepSeekMode,
        confidence_threshold: float,
    ) -> list[SubtitleSegment]:
        if mode == "off" or not segments or not self.available():
            return segments

        if mode == "low-confidence":
            targets = [
                index
                for index, segment in enumerate(segments)
                if segment.confidence < confidence_threshold
            ]
            if not targets:
                return segments
        else:
            targets = list(range(len(segments)))

        try:
            replacements = self._request_replacements(segments, targets)
        except Exception as exc:
            print(f"DeepSeek fallback skipped: {exc}")
            return segments

        refined = [SubtitleSegment(**asdict(segment)) for segment in segments]
        for index_text in replacements:
            try:
                index = int(index_text["index"])
                text = clean_text(str(index_text["text"]))
            except (KeyError, TypeError, ValueError):
                continue
            if 0 <= index < len(refined) and text:
                refined[index].text = text
        return refined

    def _request_replacements(
        self,
        segments: list[SubtitleSegment],
        target_indices: list[int],
    ) -> list[dict[str, object]]:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        payload = [
            {
                "index": index,
                "start": round(segments[index].start, 3),
                "end": round(segments[index].end, 3),
                "text": segments[index].text,
                "confidence": round(segments[index].confidence, 4),
                "prev": segments[index - 1].text if index > 0 else "",
                "next": segments[index + 1].text if index + 1 < len(segments) else "",
            }
            for index in target_indices
        ]
        prompt = (
            "你是中文录屏硬字幕OCR纠错器。请只修正OCR文本中的错别字、断行、重复和明显噪声，"
            "不要翻译，不要扩写，不要改变含义，不要改变时间。"
            "返回严格JSON数组，每项格式为 {\"index\": 数字, \"text\": \"修正后的字幕\"}。\n"
            f"字幕片段：{json.dumps(payload, ensure_ascii=False)}"
        )
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "只输出可解析JSON，不要输出Markdown。"},
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )
        content = response.choices[0].message.content or "[]"
        parsed = json.loads(content)
        if not isinstance(parsed, list):
            raise ValueError("DeepSeek response is not a JSON array")
        return parsed
