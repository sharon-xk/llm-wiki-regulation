import os
log_dir = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/ocr_logs"
total_ok = 0
total_skip = 0
total_err = 0
for fname in sorted(os.listdir(log_dir)):
    if fname.endswith('.log'):
        fpath = os.path.join(log_dir, fname)
        with open(fpath) as f:
            for line in f:
                if line.startswith("OK "):
                    total_ok += 1
                elif line.startswith("SKIP "):
                    total_skip += 1
                elif line.startswith("ERR "):
                    total_err += 1
total = total_ok + total_skip + total_err
pct = total * 100 / 1062
print(f"进度: {total}/1062 ({pct:.1f}%) | OK:{total_ok} SKIP:{total_skip} ERR:{total_err}")
