import os
import re

# Pilot entities to test
pilots = [
    "尹伟霖.md",                          # 个人, 有字号, 明显截断
    "上海极溉私幕基金管理有限公司.md",      # 机构, 明显截断
    "杭州锦元资产管理有限公司.md",          # 机构, 明显截断
    "曹辉.md",                             # 个人, 处罚措施截断
    "河北建邦股权投资基金管理有限公司.md",  # 机构, 违规+处罚都截断
]

entity_dir = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities"
raw_base = "/Users/sharon/ai-project/llm-wiki-regulation/raw/纪律处分"

for fname in pilots:
    fpath = os.path.join(entity_dir, fname)
    with open(fpath, 'r') as f:
        content = f.read()

    # Extract source reference
    source_match = re.search(r'\*\*来源\*\*:\s*(\S+)', content)
    source = source_match.group(1) if source_match else "N/A"

    # Determine which subdir (人员 or 机构)
    if 'subtype: 个人' in content:
        subdir = '人员'
    else:
        subdir = '机构'

    # Build PDF path
    pdf_name = source.replace('.txt', '.pdf') if source != 'N/A' else None
    pdf_path = os.path.join(raw_base, subdir, pdf_name) if pdf_name else None

    pdf_exists = os.path.exists(pdf_path) if pdf_path else False

    print(f"Entity: {fname}")
    print(f"  Subdir: {subdir}")
    print(f"  Source TXT: {source}")
    print(f"  PDF: {pdf_name}")
    print(f"  PDF exists: {pdf_exists}")
    if pdf_exists:
        size_kb = os.path.getsize(pdf_path) / 1024
        print(f"  PDF size: {size_kb:.0f} KB")
    print()
