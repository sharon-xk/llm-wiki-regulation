#!/usr/bin/env python3
"""分析 wiki 层数据，生成风险监测报告所需统计。"""
import os
import re
import json
from collections import defaultdict, Counter
from pathlib import Path

WIKI = Path("/Users/sharon/ai-project/llm-wiki-regulation/wiki")

def parse_frontmatter(text):
    """Extract YAML frontmatter as dict."""
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).strip().split('\n'):
        if ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            # Handle lists
            if val.startswith('[') and val.endswith(']'):
                val = [v.strip() for v in val[1:-1].split(',')]
            fm[key] = val
    return fm

def list_md_files(d):
    return sorted([f for f in os.listdir(d) if f.endswith('.md')])

# === 1. Entity analysis ===
entities_dir = WIKI / "entities"
entity_files = list_md_files(entities_dir)
print(f"=== 实体总数: {len(entity_files)} ===")

# Cross-module analysis
entity_modules = defaultdict(set)
multi_module = []
entity_violation_count = defaultdict(int)

for fname in entity_files:
    with open(entities_dir / fname, 'r', encoding='utf-8') as f:
        content = f.read()
    fm = parse_frontmatter(content)
    tags = fm.get('tags', [])
    if isinstance(tags, str):
        tags = [tags]
    for t in tags:
        entity_modules[t].add(fname)
    if len(tags) >= 2:
        multi_module.append((fname, tags))
    sc = fm.get('source_count', 0)
    if isinstance(sc, str):
        try: sc = int(sc)
        except: sc = 0
    entity_violation_count[fname] = sc

print(f"\n=== 跨模块实体 (出现在2个及以上模块) ===")
print(f"总数: {len(multi_module)}")
for name, tags in sorted(multi_module, key=lambda x: -len(x[1]))[:30]:
    print(f"  {name}: {tags}")

# === 2. Module analysis - monthly breakdown ===
print(f"\n=== 模块月度分布 ===")
modules_dir = WIKI / "modules"
for mf in sorted(list_md_files(modules_dir)):
    with open(modules_dir / mf, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract monthly counts from entity list
    monthly = defaultdict(int)
    for line in content.split('\n'):
        m = re.match(r'- \*\*(\d{4}-\d{2})\*\*:', line)
        if m:
            monthly[m.group(1)] += 1

    module_name = mf.replace('.md', '')
    print(f"\n  [{module_name}]")
    for month in sorted(monthly.keys(), reverse=True)[:12]:
        print(f"    {month}: {monthly[month]} entities")

# === 3. Violation type breakdown by time ===
print(f"\n=== 违规类型时间分布 ===")
concepts_dir = WIKI / "concepts"
for cf in sorted(list_md_files(concepts_dir)):
    with open(concepts_dir / cf, 'r', encoding='utf-8') as f:
        content = f.read()
    fm = parse_frontmatter(content)
    case_count = fm.get('case_count', 'N/A')
    cname = cf.replace('.md', '')

    # Extract yearly breakdown
    yearly = {}
    for line in content.split('\n'):
        m = re.match(r'- (\d{4})年[：:]?\s*(\d+)个案例', line)
        if m:
            yearly[m.group(1)] = int(m.group(2))
    print(f"  {cname} (total: {case_count}): {yearly}")

# === 4. Multi-violation entities (high source_count) ===
print(f"\n=== 高违规频次实体 (source_count >= 2) ===")
multi_violation = [(k, v) for k, v in entity_violation_count.items() if v >= 2]
multi_violation.sort(key=lambda x: -x[1])
print(f"总数: {len(multi_violation)}")
for name, count in multi_violation[:25]:
    print(f"  {name}: {count} 次")

# === 5. Recent (2026) violation patterns ===
print(f"\n=== 2026年纪律处分违规类型统计 ===")
# Count violation types mentioned in 2026 discipline cases
# by checking concept pages for 2026 cases
violation_2026 = Counter()
for cf in list_md_files(concepts_dir):
    with open(concepts_dir / cf, 'r', encoding='utf-8') as f:
        content = f.read()
    cname = cf.replace('.md', '')
    # Count 2026 cases in this concept
    for line in content.split('\n'):
        if '日期」2026' in line or '日期」2026' in line.replace('**', '') or '日期：2026' in line or '日期**: 2026' in line or '日期**：2026' in line:
            violation_2026[cname] += 1
    # Also check yearly summary
    for line in content.split('\n'):
        m = re.match(r'- 2026年[：:]?\s*(\d+)个案例', line)
        if m:
            violation_2026[cname] = int(m.group(1))

print("2026年违规类型分布:")
for vtype, count in violation_2026.most_common():
    print(f"  {vtype}: {count}")

# === 6. Cross-reference: entities in BOTH discipline AND other modules ===
print(f"\n=== 纪律处分 ∩ 其他模块 ===")
discipline_set = entity_modules.get('纪律处分', set())
for mod in ['异常经营', '失联机构', '自律措施']:
    other_set = entity_modules.get(mod, set())
    overlap = discipline_set & other_set
    print(f"  纪律处分 ∩ {mod}: {len(overlap)}")
    for name in sorted(overlap)[:10]:
        print(f"    - {name}")

print(f"\n=== 异常经营 ∩ 失联机构 ===")
abnormal = entity_modules.get('异常经营', set())
lost = entity_modules.get('失联机构', set())
overlap_al = abnormal & lost
print(f"  异常经营 ∩ 失联机构: {len(overlap_al)}")
for name in sorted(overlap_al)[:10]:
    print(f"    - {name}")

# === 7. Top cited regulations (from regulations directory) ===
print(f"\n=== 法规引用情况 ===")
regs_dir = WIKI / "regulations"
for rf in sorted(list_md_files(regs_dir)):
    with open(regs_dir / rf, 'r', encoding='utf-8') as f:
        content = f.read()
    fm = parse_frontmatter(content)
    cited = fm.get('cited_count', 'N/A')
    print(f"  {rf.replace('.md', '')}: cited_count={cited}")

print("\n=== 分析完成 ===")
