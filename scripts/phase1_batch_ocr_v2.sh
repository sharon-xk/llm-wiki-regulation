#!/bin/bash
# 批量 OCR：8 并行，从任务文件逐行读取
set -e

TASK_FILE="/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/ocr_tasks.txt"
WORKER="/Users/sharon/ai-project/llm-wiki-regulation/scripts/phase1_ocr_worker.sh"
LOG_FILE="/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/ocr_progress_v2.log"
MAX_JOBS=8

TOTAL=$(wc -l < "$TASK_FILE")
echo "共 $TOTAL 个任务，$MAX_JOBS 并行" | tee "$LOG_FILE"

ACTIVE=0
DONE=0
OK=0
SKIP=0
ERR=0
START_TIME=$(date +%s)

while IFS= read -r TASK; do
    # 启动 worker (后台)
    bash "$WORKER" "$TASK" >> "$LOG_FILE" 2>&1 &
    ACTIVE=$((ACTIVE + 1))

    # 达到最大并行数时等待任意一个完成
    if [ $ACTIVE -ge $MAX_JOBS ]; then
        wait -n 2>/dev/null || true
        ACTIVE=$((ACTIVE - 1))
        DONE=$((DONE + 1))

        # 每 50 个报告一次进度
        if [ $((DONE % 50)) -eq 0 ]; then
            ELAPSED=$(($(date +%s) - START_TIME))
            RATE=$(echo "scale=1; $DONE / $ELAPSED" | bc 2>/dev/null || echo "0")
            REMAINING=$((TOTAL - DONE))
            ETA=$(echo "scale=0; $REMAINING / $RATE / 60" | bc 2>/dev/null || echo "?")
            echo "[$(date +%H:%M)] $DONE/$TOTAL 速率:${RATE}/s 剩余:${ETA}min" | tee -a "$LOG_FILE"
        fi
    fi
done < "$TASK_FILE"

# 等待所有后台任务完成
wait

# 统计
OK=$(grep -c "^OK " "$LOG_FILE" || echo 0)
SKIP=$(grep -c "^SKIP " "$LOG_FILE" || echo 0)
ELAPSED=$(($(date +%s) - START_TIME))
echo "==========" | tee -a "$LOG_FILE"
echo "阶段1完成! 耗时: ${ELAPSED}s (${ELAPSED}秒)" | tee -a "$LOG_FILE"
echo "OK: $OK, SKIP: $SKIP" | tee -a "$LOG_FILE"
