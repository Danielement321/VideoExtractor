# 视频硬字幕提取工具

从录屏视频中识别画面底部的中文字幕，并导出为 `.srt` 字幕文件和纯文本 `.txt` 文件。

这个工具适合处理字幕已经压进视频画面的场景，也就是没有单独字幕轨的“硬字幕”视频。它默认通过兼容 OpenAI Vision Chat API 格式的多模态接口做图片 OCR，不依赖语音转文字，因此对倍速播放、变速剪辑一类视频更稳定。

## 功能特点

- 批量处理 `videos/` 目录中的视频文件。
- 识别画面底部字幕区域，生成 SRT 时间轴字幕。
- 同时输出 `.srt` 和 `.txt`。
- 支持实时写入结果，长视频处理中途也能看到已生成内容。
- 支持通过 API 做 OCR，以及可选的二次文本纠错。
- 可保存调试帧，方便检查截取的字幕区域是否正确。

## 环境要求

- Python 3.10 或更高版本
- 可用的视觉 OCR 接口，接口格式需要兼容 OpenAI Chat Completions 的多模态 `image_url` 消息格式

项目依赖会通过 `pip install -e .` 安装，主要包括：

- `opencv-python`
- `numpy`
- `openai`

## 安装

在项目根目录执行：

```bash
python3 -m pip install -e .
```

Windows 可以使用：

```bat
python -m pip install -e .
```

## 配置 OCR 接口

先复制环境变量示例文件：

```bash
cp .env.example .env
```

Windows 可以手动复制 `.env.example` 为 `.env`。

然后编辑 `.env`：

```text
API_OCR_API_KEY=your_api_key_here
API_OCR_BASE_URL=https://www.autodl.art
API_OCR_MODEL=qwen3-vl-plus
```

配置说明：

- `API_OCR_API_KEY`：必填，OCR 接口密钥。
- `API_OCR_BASE_URL`：可选，API 地址。默认是 `https://api.openai.com/v1`。如果填写 `https://www.autodl.art`，程序会自动转换为 `https://www.autodl.art/api/v1`。
- `API_OCR_MODEL`：可选，视觉模型名称。默认是 `gpt-4o-mini`。

`.env` 已被 Git 忽略，不会提交到仓库。

## 使用方法

把视频文件放到 `videos/` 目录，然后运行：

```bash
video-subtitle-extractor
```

也可以使用项目自带启动脚本：

```bash
./run_extractor.sh
```

Windows：

```bat
run_extractor.bat
```

启动脚本会自动加载 `.env`，检查 `API_OCR_API_KEY`，安装本地包，并使用一组适合直接处理录屏字幕的默认参数。

## 输入与输出

默认输入目录：

```text
videos/
```

默认输出目录：

```text
outputs/
```

支持的视频格式：

```text
.mp4, .mov, .mkv, .avi, .webm, .m4v
```

例如输入文件是：

```text
videos/example.mp4
```

处理后会生成：

```text
outputs/example.srt
outputs/example.txt
```

`.srt` 文件包含字幕时间轴，`.txt` 文件只包含识别出的文本内容。

## 常用参数

```bash
video-subtitle-extractor \
  --input-dir videos \
  --output-dir outputs \
  --frame-interval 0.5 \
  --roi-bottom-ratio 0.30 \
  --api-batch-size 4 \
  --api-ocr-mode cleanup
```

参数说明：

- `--input-dir`：输入视频目录，默认 `videos`。
- `--output-dir`：输出目录，默认 `outputs`。
- `--frame-interval`：抽帧间隔，单位秒。数值越小识别越密集，速度越慢，默认 `0.5`。
- `--roi-bottom-ratio`：截取画面底部的比例。`0.30` 表示只截取底部 30%，默认 `0.30`。
- `--min-confidence`：保留字幕片段的最低置信度，默认 `0.1`。
- `--similarity-threshold`：相邻 OCR 文本合并为同一字幕的相似度阈值，默认 `0.82`。
- `--min-duration`：保留字幕片段的最短时长，单位秒，默认 `0.35`。
- `--max-gap`：相邻相似字幕允许合并的最大时间间隔，单位秒，默认 `1.0`。
- `--api-batch-size`：每次 API OCR 请求发送的字幕截图数量，默认 `4`。
- `--api-ocr-mode`：二次文本处理模式，可选 `off`、`cleanup`、`low-confidence`，默认 `off`。
- `--api-ocr-confidence-threshold`：`low-confidence` 模式下需要二次纠错的置信度阈值，默认 `0.70`。
- `--debug-frames`：保存抽取出的字幕区域截图，用于排查 ROI 是否正确。

## 启动脚本默认值

直接运行 `run_extractor.sh` 或 `run_extractor.bat` 时，脚本会读取以下环境变量；如果没有设置，会使用脚本默认值：

```text
INPUT_DIR=videos
OUTPUT_DIR=outputs
FRAME_INTERVAL=1.0
ROI_BOTTOM_RATIO=0.90
API_BATCH_SIZE=8
API_OCR_MODE=cleanup
```

这和直接运行 `video-subtitle-extractor` 的 CLI 默认值不完全相同。脚本默认截取底部 90% 画面，并启用 `cleanup`，更偏向“开箱即用”；CLI 默认值更适合手动精调。

## 调试字幕区域

如果识别结果不理想，先检查截取区域是否覆盖了字幕：

```bash
video-subtitle-extractor --debug-frames debug_frames
```

程序会把抽取出的字幕区域截图保存到 `debug_frames/`。如果发现字幕没有被截进去，可以调大 `--roi-bottom-ratio`：

```bash
video-subtitle-extractor --roi-bottom-ratio 0.50
```

如果截取区域里包含太多无关内容，可以调小：

```bash
video-subtitle-extractor --roi-bottom-ratio 0.25
```

## 提高识别质量

可以尝试以下方向：

- 字幕变化很快：减小 `--frame-interval`，例如 `0.3` 或 `0.4`。
- OCR 请求太慢或接口限流：减小 `--api-batch-size`。
- 画面底部还有播放器控件、水印或其他文字：调小 `--roi-bottom-ratio`，只截字幕区域。
- OCR 有错别字或重复：使用 `--api-ocr-mode cleanup`。
- 只想修正低置信度片段：使用 `--api-ocr-mode low-confidence`。

示例：

```bash
video-subtitle-extractor \
  --frame-interval 0.4 \
  --roi-bottom-ratio 0.25 \
  --api-batch-size 2 \
  --api-ocr-mode cleanup
```

## 工作流程

程序处理每个视频时会：

1. 按固定时间间隔抽帧。
2. 截取画面底部字幕区域。
3. 将截图批量发送给视觉 OCR 接口。
4. 合并相邻相似文本，生成字幕时间段。
5. 可选执行文本纠错。
6. 输出 `.srt` 和 `.txt`。

处理过程中会在终端打印 OCR 进度和每一帧的识别文本。

## 注意事项

- 本工具识别的是画面中的硬字幕，不会读取视频内嵌字幕轨。
- 视觉 OCR 接口必须支持 OpenAI 兼容的多模态消息格式。
- 视频越长、抽帧越密集，API 调用次数和处理时间越多。
- 如果输入目录不存在，程序会报错。
- 如果输入目录没有支持的视频文件，程序会提示未找到视频。
