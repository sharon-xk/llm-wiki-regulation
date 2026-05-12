#!/bin/bash
# 阶段1: 将任务文件拆成8个分片，每个分片后台串行执行
TASK_FILE="/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/ocr_tasks.txt"
WORKER="/Users/sharon/ai-project/llm-wiki-regulation/scripts/phase1_ocr_worker.sh"
LOG_DIR="/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/ocr_logs"
CHUNKS=8

mkdir -p "$LOG_DIR"

# 拆分任务文件
TOTAL=$(wc -l < "$TASK_FILE")
LINES_PER_CHUNK=$(( (TOTAL + CHUNKS - 1) / CHUNKS ))
split -l $LINES_PER_CHUNK "$TASK_FILE" "${LOG_DIR}/chunk_"

echo "共 $TOTAL 个任务，拆成 $CHUNKS 个分片，每片 ~$LINES_PER_CHUNK 个"
echo "启动 $CHUNKS 个后台进程..."

START_TIME=$(date +%s)

for chunk in "${LOG_DIR}"/chunk_*; do
    (
        CHUNK_NAME=$(basename "$chunk")
        LOG="${LOG_DIR}/${CHUNK_NAME}.log"
        while IFS= read -r task; do
            bash "$WORKER" "$task" >> "$LOG" 2>&1
        done < "$chunk"
    ) &
done

echo "所有 worker 已启动，等待完成..."
wait

ELAPSED=$(($(date +%s) - START_TIME))
echo "=========="
echo "全部完成! 耗时: $((ELAPSED / 60)) 分钟"

# 汇总统计
TOTAL_OK=0
TOTAL_SKIP=0
for log in "${LOG_DIR}"/chunk_*.log; do
    OK=$(grep -c "^OK " "$log" 2>/dev/null || echo 0)
    SKIP=$(grep -c "^SKIP " "$log" 2>/dev/null || echo 0)
    TOTAL_OK=$((TOTAL_OK + OK))
    TOTAL_SKIP=$((TOTAL_SKIP + SKIP))
done
echo "OK: $TOTAL_OK, SKIP: $TOTAL_SKIP, 总计: $((TOTAL_OK + TOTAL_SKIP))"
echo "各分片日志: ${LOG_DIR}/chunk_*.log"
