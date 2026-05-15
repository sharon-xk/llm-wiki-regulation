"""生成 OCR 任务列表，输出格式: pdf路径|txt路径|entity名称"""
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
ENTITY_DIR = BASE_DIR / "wiki" / "entities"
RAW_BASE = BASE_DIR / "raw" / "纪律处分"
OUTPUT = Path(__file__).parent.parent / "tmp" / "ocr_tasks.txt"

tasks = []
for fname in sorted([f for f in os.listdir(ENTITY_DIR) if f.endswith('.md')]):
    fpath = os.path.join(ENTITY_DIR, fname)
    with open(fpath, 'r') as f:
        content = f.read()

    m = re.search(r'\*\*来源\*\*:\s*(\S+)', content)
    if not m:
        continue

    source = m.group(1)
    pdf_name = source.replace('.txt', '.pdf')
    subdir = '人员' if 'subtype: 个人' in content else '机构'

    pdf_path = os.path.join(RAW_BASE, subdir, pdf_name)
    txt_path = os.path.join(RAW_BASE, subdir, source)

    if os.path.exists(pdf_path):
        tasks.append(f"{pdf_path}|{txt_path}|{fname}")

os.makedirs(OUTPUT.parent, exist_ok=True)
with open(OUTPUT, 'w') as f:
    f.write('\n'.join(tasks))

print(f"生成 {len(tasks)} 个 OCR 任务 → {OUTPUT}")
# 统计已完成的（TXT > 50行）
done = 0
for pdf_path, txt_path, _ in [t.split('|') for t in tasks]:
    if os.path.exists(txt_path):
        with open(txt_path) as f:
            if len(f.readlines()) > 50:
                done += 1
print(f"其中已完成 (>50行): {done}, 待处理: {len(tasks) - done}")
