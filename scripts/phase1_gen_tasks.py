"""生成 OCR 任务列表，输出格式: pdf路径|txt路径|entity名称"""
import os
import re

entity_dir = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities"
raw_base = "/Users/sharon/ai-project/llm-wiki-regulation/raw/纪律处分"
output = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/ocr_tasks.txt"

tasks = []
for fname in sorted([f for f in os.listdir(entity_dir) if f.endswith('.md')]):
    fpath = os.path.join(entity_dir, fname)
    with open(fpath, 'r') as f:
        content = f.read()

    m = re.search(r'\*\*来源\*\*:\s*(\S+)', content)
    if not m:
        continue

    source = m.group(1)
    pdf_name = source.replace('.txt', '.pdf')
    subdir = '人员' if 'subtype: 个人' in content else '机构'

    pdf_path = os.path.join(raw_base, subdir, pdf_name)
    txt_path = os.path.join(raw_base, subdir, source)

    if os.path.exists(pdf_path):
        tasks.append(f"{pdf_path}|{txt_path}|{fname}")

with open(output, 'w') as f:
    f.write('\n'.join(tasks))

print(f"生成 {len(tasks)} 个 OCR 任务 → {output}")
# 统计已完成的（TXT > 50行）
done = 0
for pdf_path, txt_path, _ in [t.split('|') for t in tasks]:
    if os.path.exists(txt_path):
        with open(txt_path) as f:
            if len(f.readlines()) > 50:
                done += 1
print(f"其中已完成 (>50行): {done}, 待处理: {len(tasks) - done}")
