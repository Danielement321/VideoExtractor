from __future__ import annotations

import base64
import json
import os
from dataclasses import asdict
from typing import Literal

import numpy as np

from .models import OcrResult, SubtitleSegment
from .text import clean_text


ApiOcrMode = Literal["off", "cleanup", "low-confidence"]


class ApiOcrClient:
    def __init__(self) -> None:
        _load_env_file()
        self.api_key = os.environ.get("API_OCR_API_KEY")
        self.base_url = _normalize_base_url(
            os.environ.get("API_OCR_BASE_URL", "https://api.openai.com/v1")
        )
        self.model = os.environ.get("API_OCR_MODEL", "gpt-4o-mini")

    def available(self) -> bool:
        return bool(self.api_key)

    def recognize(self, image: np.ndarray) -> OcrResult:
        return self.recognize_many([image])[0]

    def recognize_many(self, images: list[np.ndarray]) -> list[OcrResult]:
        if not self.available():
            raise RuntimeError("API_OCR_API_KEY is required for API OCR")
        if not images:
            return []

        replacements = self._request_image_ocr(images)
        results = [OcrResult("", 0.0) for _ in images]
        for item in replacements:
            try:
                index = int(item["index"])
                text = clean_text(str(item["text"]))
            except (KeyError, TypeError, ValueError):
                continue
            if 0 <= index < len(results) and text:
                results[index] = OcrResult(text, 1.0)
        return results

    def refine(
        self,
        segments: list[SubtitleSegment],
        *,
        mode: ApiOcrMode,
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
            print(f"API OCR cleanup skipped: {exc}")
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
        return _parse_json_array(content)

    def _request_image_ocr(self, images: list[np.ndarray]) -> list[dict[str, object]]:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        content: list[dict[str, object]] = [
            {
                "type": "text",
                "text": (
                    "请识别这些中文录屏字幕截图中的字幕文字。每张图片只返回画面里作为字幕出现的中文，"
                    "忽略播放器控件、水印、图标、背景文字和非字幕内容。没有字幕则返回空字符串。"
                    "返回严格JSON数组，每项格式为 {\"index\": 图片序号, \"text\": \"字幕文字\"}。"
                    "不要输出Markdown，不要解释。图片序号从0开始。"
                ),
            }
        ]
        for index, image in enumerate(images):
            content.append({"type": "text", "text": f"图片序号：{index}"})
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": _image_to_data_url(image)},
                }
            )
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是高精度中文硬字幕OCR引擎。只输出可解析JSON。"},
                {"role": "user", "content": content},
            ],
            stream=False,
        )
        return _parse_json_array(response.choices[0].message.content or "[]")


def _image_to_data_url(image: np.ndarray) -> str:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV is not installed. Install with: python3 -m pip install -e ."
        ) from exc

    ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    if not ok:
        raise RuntimeError("Failed to encode frame as JPEG")
    data = base64.b64encode(encoded.tobytes()).decode("ascii")
    return f"data:image/jpeg;base64,{data}"


def _normalize_base_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    if base_url == "https://www.autodl.art":
        return f"{base_url}/api/v1"
    return base_url


def _load_env_file() -> None:
    env_path = os.getcwd()
    path = os.path.join(env_path, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value.strip().strip('"').strip("'")


def _parse_json_array(content: str) -> list[dict[str, object]]:
    content = content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()
    parsed = json.loads(content)
    if not isinstance(parsed, list):
        raise ValueError("API OCR response is not a JSON array")
    return parsed
