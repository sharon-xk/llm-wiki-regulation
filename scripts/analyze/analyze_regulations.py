"""
从 parsed data 和 entity 页面提取每个法规的关联违规类型和典型案例
"""
import json
import re
import os
from pathlib import Path
from collections import Counter, defaultdict

PARSED_DATA = str(Path(__file__).parent.parent / "tmp" / "parsed_data_with_concepts.json")
MAP_FILE = str(Path(__file__).parent.parent / "config" / "reg_name_map.json")
ENTITY_DIR = str(Path(__file__).parent.parent.parent / "wiki" / "entities")

with open(MAP_FILE) as f:
    name_map = json.load(f)

with open(PARSED_DATA) as f:
    data = json.load(f)

def normalize(name):
    return name_map.get(name.strip(), name.strip())

# 统计每个标准法规的引用次数、关联违规类型、典型案例
reg_stats = defaultdict(lambda: {
    'cited_count': 0,
    'concepts': Counter(),
    'entities': set(),
    'violations_samples': []
})

for item in data:
    basis = item.get('legal_basis', '')
    if not basis:
        continue

    found = re.findall(r'《([^》]+)》', basis)
    entity_name = item.get('entity', '')

    for name in found:
        std_name = normalize(name)
        reg_stats[std_name]['cited_count'] += 1
        if entity_name:
            reg_stats[std_name]['entities'].add(entity_name)

        # 收集关联的违规概念
        for vc in item.get('violation_concepts', []):
            for c in vc.get('concepts', []):
                reg_stats[std_name]['concepts'][c] += 1

        # 收集违规文本样本（含条款信息）
        for v in item.get('violations', [])[:2]:
            reg_stats[std_name]['violations_samples'].append(v[:300])

# 打印结果
for std_name in sorted(reg_stats.keys(), key=lambda n: -reg_stats[n]['cited_count']):
    stats = reg_stats[std_name]
    print(f"\n{'='*60}")
    print(f"【{std_name}】")
    print(f"  引用次数: {stats['cited_count']}")
    print(f"  关联实体数: {len(stats['entities'])}")
    print(f"  关联违规类型:")
    for c, cnt in stats['concepts'].most_common(10):
        print(f"    - {c} ({cnt})")
    print(f"  典型案例 (前5):")
    for e in list(stats['entities'])[:5]:
        print(f"    - {e}")
    print(f"  违规文本样本 (前3):")
    for v in stats['violations_samples'][:3]:
        # 提取条款引用
        articles = re.findall(r'第[一二三四五六七八九十百千]+条', v)
        if articles:
            print(f"    条款: {', '.join(articles)}")
            print(f"    原文: {v[:200]}...")
