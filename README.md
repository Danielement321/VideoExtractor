# Video Subtitle Extractor

Extract Chinese hard subtitles from screen-recorded videos into `.srt` files.

The tool is designed for videos under `videos/` where subtitles are burned into
the bottom of the image and there is no separate subtitle track. It avoids
speech-to-text by default, which is useful when videos have speed changes.

## Install

```bash
python3 -m pip install -e ".[dev]"
```

For real OCR extraction, install an OCR backend as well:

```bash
python3 -m pip install -e ".[ocr]"
```

PaddleOCR may also require a matching CPU `paddlepaddle` package. If PaddleOCR
or PaddlePaddle is not available for your Python version, create a Python
3.10-3.12 environment and reinstall there.

## Usage

```bash
video-subtitle-extractor
```

Defaults:

- input directory: `videos/`
- output directory: `outputs/`
- OCR area: bottom 30% of the frame
- frame interval: every 0.5 seconds
- DeepSeek fallback: off

Useful options:

```bash
video-subtitle-extractor --frame-interval 0.4 --roi-bottom-ratio 0.25
video-subtitle-extractor --debug-frames debug_frames
video-subtitle-extractor --deepseek-mode cleanup
video-subtitle-extractor --deepseek-mode low-confidence
```

DeepSeek fallback reads `DEEPSEEK_API_KEY`. Optional environment variables:

- `DEEPSEEK_BASE_URL`, default `https://api.deepseek.com`
- `DEEPSEEK_MODEL`, default `deepseek-v4-flash`

`cleanup` asks DeepSeek to correct subtitle text while preserving timing.
`low-confidence` only asks DeepSeek to repair low-confidence OCR segments.
If the API key is missing or the request fails, the local OCR result is kept.

## Output

For `videos/example.mp4`, the generated subtitle file is:

```text
outputs/example.srt
```

Each entry contains a time range and the extracted Chinese text.
