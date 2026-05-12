import os

log_dir = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/ocr_logs"
total_ok = 0; total_skip = 0; total_err = 0
ok_entities = []
err_entities = []

for fname in sorted(os.listdir(log_dir)):
    if fname.endswith('.log'):
        fpath = os.path.join(log_dir, fname)
        with open(fpath) as f:
            for line in f:
                if line.startswith("OK "):
                    total_ok += 1
                    ok_entities.append(line.strip())
                elif line.startswith("SKIP "):
                    total_skip += 1
                elif line.startswith("ERR "):
                    total_err += 1
                    err_entities.append(line.strip())

total = total_ok + total_skip + total_err
print(f"=== 阶段1 完成 ===")
print(f"总计: {total}/1062")
print(f"OK (新OCR): {total_ok}")
print(f"SKIP (已有>50行): {total_skip}")
print(f"ERR: {total_err}")

# 检查产出质量
raw_base = "/Users/sharon/ai-project/llm-wiki-regulation/raw/纪律处分"
short_txt = []
for subdir in ['人员', '机构']:
    dir_path = os.path.join(raw_base, subdir)
    for fname in os.listdir(dir_path):
        if fname.endswith('.txt'):
            fpath = os.path.join(dir_path, fname)
            lines = len(open(fpath).readlines())
            if lines < 40:
                short_txt.append((fname, lines))

print(f"\n行数仍 <40 的 TXT: {len(short_txt)} 个")
if short_txt:
    for name, lines in short_txt[:10]:
        print(f"  {name}: {lines} lines")
    if len(short_txt) > 10:
        print(f"  ... 等 {len(short_txt)-10} 个")

# 检查 ERR 的
if err_entities:
    print(f"\nERR 详情:")
    for e in err_entities[:10]:
        print(f"  {e}")
