import os
import re

entity_dir = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities"
raw_base = "/Users/sharon/ai-project/llm-wiki-regulation/raw/纪律处分"

files = [f for f in os.listdir(entity_dir) if f.endswith('.md')]

# Stats
stats = {
    "total": len(files),
    "has_source": 0,
    "no_source": 0,
    "pdf_found": 0,
    "pdf_not_found": 0,
    "has_case_num": 0,
    "no_case_num": 0,
    "subtype_个人": 0,
    "subtype_基金管理人": 0,
    "subtype_other": 0,
    "truncated": 0,  # likely truncated (ends with non-sentence-ending chars)
    "pdf_page_counts": {},  # count distribution
}

missing_pdfs = []
no_source_entities = []

for fname in files:
    fpath = os.path.join(entity_dir, fname)
    with open(fpath, 'r') as f:
        content = f.read()

    # subtype
    if 'subtype: 个人' in content:
        subdir = '人员'
        stats["subtype_个人"] += 1
    elif 'subtype: 基金管理人' in content:
        subdir = '机构'
        stats["subtype_基金管理人"] += 1
    else:
        subdir = '机构'
        stats["subtype_other"] += 1

    # source
    source_match = re.search(r'\*\*来源\*\*:\s*(\S+)', content)
    if source_match:
        stats["has_source"] += 1
        source = source_match.group(1)
        pdf_name = source.replace('.txt', '.pdf')
        pdf_path = os.path.join(raw_base, subdir, pdf_name)
        if os.path.exists(pdf_path):
            stats["pdf_found"] += 1
        else:
            stats["pdf_not_found"] += 1
            missing_pdfs.append((fname, pdf_path))
    else:
        stats["no_source"] += 1
        no_source_entities.append(fname)

    # case number
    if re.search(r'\*\*字号\*\*:', content):
        stats["has_case_num"] += 1
    else:
        stats["no_case_num"] += 1

    # truncation check - does last line of 违规行为 end with complete sentence?
    # Look for content that ends mid-character or with single residual char
    violation_match = re.search(r'\*\*违规行为\*\*:(.*?)(?:\n|$)', content, re.DOTALL)
    if violation_match:
        v_text = violation_match.group(1).strip()
        # Check if ends abruptly (not with period, question mark, etc.)
        if v_text and not v_text[-1] in '。！？）)】]」》\n':
            # check if it looks truncated (ends with number or partial word)
            last_chars = v_text[-20:]
            if len(v_text) < 200 or re.search(r'[\d\s]{3,}$', last_chars) or re.search(r'[一-龥]\s*$', last_chars):
                stats["truncated"] += 1

print("=== Entity 全量统计 ===")
for k, v in stats.items():
    if k == "pdf_page_counts":
        continue
    print(f"  {k}: {v}")

print(f"\n  PDF 缺失 ({len(missing_pdfs)}个):")
for name, path in missing_pdfs[:10]:
    print(f"    {name} -> {path}")
if len(missing_pdfs) > 10:
    print(f"    ... 以及另外 {len(missing_pdfs)-10} 个")

print(f"\n  无来源引用 ({len(no_source_entities)}个):")
for name in no_source_entities[:10]:
    print(f"    {name}")
if len(no_source_entities) > 10:
    print(f"    ... 以及另外 {len(no_source_entities)-10} 个")
