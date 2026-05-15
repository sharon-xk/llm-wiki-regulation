#!/bin/bash
# 用法: bash scripts/ocr/ocr_worker.sh "pdf_path|txt_path|entity_name"
set -e

IFS='|' read -r PDF_PATH TXT_PATH ENTITY_NAME <<< "$1"

# 跳过已完成的 (>50行)
if [ -f "$TXT_PATH" ]; then
    LINES=$(wc -l < "$TXT_PATH")
    if [ "$LINES" -gt 50 ]; then
        echo "SKIP $ENTITY_NAME (已有 ${LINES} 行)"
        exit 0
    fi
fi

# 项目内临时目录（避免 macOS 沙箱限制 /tmp）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TMP_BASE="${SCRIPT_DIR}/../tmp/ocr_batch"
WORK_DIR="${TMP_BASE}/ocr_$$_${RANDOM}"
mkdir -p "$WORK_DIR"

# 获取页数
PAGES=$(pdfinfo "$PDF_PATH" 2>/dev/null | grep "Pages:" | awk '{print $2}')
PAGES=${PAGES:-1}

# PDF 转图片
pdftoppm -png -r 300 "$PDF_PATH" "${WORK_DIR}/p" 2>/dev/null

# OCR 每页
FULL_TEXT=""
for i in $(seq 1 $PAGES); do
    IMG="${WORK_DIR}/p-${i}.png"
    OUT="${WORK_DIR}/p-${i}"
    if [ -f "$IMG" ]; then
        tesseract "$IMG" "$OUT" -l chi_sim 2>/dev/null
        if [ -f "${OUT}.txt" ]; then
            FULL_TEXT="${FULL_TEXT}$(cat "${OUT}.txt")"$'\n'
        fi
    fi
done

# 写入目标文件
echo "$FULL_TEXT" > "$TXT_PATH"

LINE_COUNT=$(wc -l < "$TXT_PATH")
echo "OK $ENTITY_NAME (${PAGES}页 → ${LINE_COUNT}行)"

# 清理
rm -rf "$WORK_DIR"
