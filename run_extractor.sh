#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

if [[ -z "${API_OCR_API_KEY:-}" ]]; then
  echo "Error: API_OCR_API_KEY is not configured" >&2
  echo "Create a .env file from .env.example and set API_OCR_API_KEY." >&2
  exit 1
fi

INPUT_DIR="${INPUT_DIR:-videos}"
OUTPUT_DIR="${OUTPUT_DIR:-outputs}"
FRAME_INTERVAL="${FRAME_INTERVAL:-1.0}"
ROI_BOTTOM_RATIO="${ROI_BOTTOM_RATIO:-0.90}"
API_BATCH_SIZE="${API_BATCH_SIZE:-8}"
API_OCR_MODE="${API_OCR_MODE:-cleanup}"

python3 -m pip install -e . >/dev/null

echo "Starting subtitle extraction"
echo "Input: $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo "Frame interval: ${FRAME_INTERVAL}s"
echo "API batch size: $API_BATCH_SIZE"
echo "API OCR mode: $API_OCR_MODE"

video-subtitle-extractor \
  --input-dir "$INPUT_DIR" \
  --output-dir "$OUTPUT_DIR" \
  --frame-interval "$FRAME_INTERVAL" \
  --roi-bottom-ratio "$ROI_BOTTOM_RATIO" \
  --api-batch-size "$API_BATCH_SIZE" \
  --api-ocr-mode "$API_OCR_MODE"
