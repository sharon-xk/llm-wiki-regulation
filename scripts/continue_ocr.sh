#!/bin/bash
# 继续OCR处理脚本
# 用法: bash scripts/continue_ocr.sh

cd /Users/sharon/ai-project/llm-wiki-regulation/raw/纪律处分/机构

echo "开始OCR..."
count=0

for pdf in *.pdf; do
  txt="${pdf%.pdf}.txt"
  if [ ! -f "$txt" ] || [ ! -s "$txt" ]; then
    # 先尝试pdftotext
    if pdftotext -layout "$pdf" - 2>/dev/null | grep -q "纪律处分\|处分决定书\|私募基金管理"; then
      pdftotext -layout "$pdf" "$txt" 2>/dev/null
      echo "pdftotext: $pdf"
    else
      # OCR
      pdftoppm -png -singlefile -r 200 "$pdf" ./ocr_tmp 2>/dev/null
      tesseract ./ocr_tmp.png ./ocr_tmp -l chi_sim 2>/dev/null
      if [ -s ./ocr_tmp.txt ]; then
        cp ./ocr_tmp.txt "$txt"
        echo "OCR: $pdf"
      fi
      rm -f ./ocr_tmp*
    fi
    count=$((count + 1))
  fi
done

echo "完成 $count 个文件的OCR"

# 处理人员目录
cd /Users/sharon/ai-project/llm-wiki-regulation/raw/纪律处分/人员
echo "开始OCR人员目录..."

for pdf in *.pdf; do
  txt="${pdf%.pdf}.txt"
  if [ ! -f "$txt" ] || [ ! -s "$txt" ]; then
    pdftotext -layout "$pdf" "$txt" 2>/dev/null || true
    if [ ! -s "$txt" ]; then
      pdftoppm -png -singlefile -r 200 "$pdf" ./ocr_tmp 2>/dev/null
      tesseract ./ocr_tmp.png ./ocr_tmp -l chi_sim 2>/dev/null
      if [ -s ./ocr_tmp.txt ]; then
        cp ./ocr_tmp.txt "$txt"
        echo "OCR: $pdf"
      fi
      rm -f ./ocr_tmp*
    else
      echo "pdftotext: $pdf"
    fi
  fi
done