@echo off
setlocal

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    set "%%A=%%B"
  )
)

if not defined API_OCR_API_KEY (
  echo Error: API_OCR_API_KEY is not configured 1>&2
  echo Create a .env file from .env.example and set API_OCR_API_KEY. 1>&2
  exit /b 1
)

if not defined INPUT_DIR set "INPUT_DIR=videos"
if not defined OUTPUT_DIR set "OUTPUT_DIR=outputs"
if not defined FRAME_INTERVAL set "FRAME_INTERVAL=1.0"
if not defined ROI_BOTTOM_RATIO set "ROI_BOTTOM_RATIO=0.90"
if not defined API_BATCH_SIZE set "API_BATCH_SIZE=8"
if not defined API_OCR_MODE set "API_OCR_MODE=cleanup"

python -m pip install -e . >nul
if errorlevel 1 exit /b %errorlevel%

echo Starting subtitle extraction
echo Input: %INPUT_DIR%
echo Output: %OUTPUT_DIR%
echo Frame interval: %FRAME_INTERVAL%s
echo API batch size: %API_BATCH_SIZE%
echo API OCR mode: %API_OCR_MODE%

python -m video_subtitle_extractor.cli ^
  --input-dir "%INPUT_DIR%" ^
  --output-dir "%OUTPUT_DIR%" ^
  --frame-interval "%FRAME_INTERVAL%" ^
  --roi-bottom-ratio "%ROI_BOTTOM_RATIO%" ^
  --api-batch-size "%API_BATCH_SIZE%" ^
  --api-ocr-mode "%API_OCR_MODE%"

exit /b %errorlevel%
