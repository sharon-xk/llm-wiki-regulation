#!/usr/bin/env python3
"""
创建/重建 concept 页面, 从 parsed_data_with_concepts.json 聚合案例.
用法: python3 scripts/wiki/create_concepts.py
"""
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import date

BASE_DIR = Path(__file__).parent.parent.parent
CONCEPTS_DIR = BASE_DIR / "wiki" / "concepts"

CONCEPT_MAP = {
    '信息披露违规': '信息披露违规', '未按规定登记备案': '未按规定登记备案',
    '未尽谨慎勤勉义务': '未尽谨慎勤勉义务', '投资者适当性违规': '投资者适当性违规',
    '违规募集': '违规募集', '承诺保本收益': '承诺保本收益',
    '虚假登记备案': '虚假登记备案', '挪用基金财产': '挪用基金财产',
    '关联交易违规': '关联交易违规', '利益输送': '利益输送',
}


def clean_violation_text(text):
    text = re.sub(r'\s+1\s+', '', text)
    text = re.sub(r'^\s*1\s+', '', text)
    text = re.sub(r'\s+1\s*$', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def entity_link(name):
    safe = re.sub(r'[\\/:*?"<>|;,\'"()（）【】〈〈〉、、\s\-—]', '', name)[:40]
    return f'[{name}](/wiki/entities/{safe}.md)'


def build_concept_page(concept_name, cases):
    cases.sort(key=lambda x: x['date'], reverse=True)
    years = Counter()
    for c in cases:
        year = c['date'][:4] if c['date'] else ''
        years[year if (year.isdigit() and 1950 <= int(year) <= 2030) else '未知'] += 1

    entity_set = set(c['entity_name'] for c in cases)
    case_count = len(entity_set)

    content = f"""---
type: concept
name: {concept_name}
description: {concept_name}相关违规行为及处罚案例
case_count: {case_count}
tags: [违规类型, 纪律处分]
last_updated: {date.today().isoformat()}
---

# {concept_name}

## 概述

本概念页收录 **{case_count}** 个涉及「{concept_name}」的主体案例。

## 时间分布

"""
    for year, count in sorted(years.items(), reverse=True):
        content += f"- {year}年：{count}个案例\n"

    content += "\n## 典型案例\n\n"
    for i, c in enumerate(cases[:30]):
        elink = entity_link(c['entity_name'])
        content += f"### {i+1}. {elink}\n\n"
        content += f"- **日期**：{c['date']}\n"
        if c.get('case_num'): content += f"- **字号**：{c['case_num']}\n"
        content += f"- **违规行为**：{c['detail']}\n\n"

    if len(cases) > 30:
        content += f"\n... 还有 {len(cases) - 30} 条案例\n\n"

    content += """## 违规构成要件

一般包括：
1. 违规主体（机构或个人）
2. 违规行为的具体表现
3. 主观过错（如故意或过失）
4. 损害后果

## 处罚依据

- 《中华人民共和国证券投资基金法》
- 《私募投资基金监督管理暂行办法》
- 《中国证券投资基金业协会自律管理规则》

## 处罚措施

常见的处罚措施包括：
- **机构**：警告、罚款、责令改正、公开谴责、取消会员资格、撤销登记等
- **个人**：警告、罚款、取消基金从业资格、加入黑名单等
"""
    return content


def main():
    CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)

    data_path = BASE_DIR / "scripts" / "tmp" / "parsed_data_with_concepts.json"
    if not data_path.exists():
        print(f"数据文件不存在: {data_path}")
        print("请先运行 wiki/concept_map.py 生成概念映射")
        return

    with open(data_path, 'r', encoding='utf-8') as f:
        concept_data = json.load(f)

    concept_cases = defaultdict(list)
    for rec in concept_data:
        entity_name = rec['entity'].replace('.md', '')
        for vc in rec.get('violation_concepts', []):
            for concept in vc['concepts']:
                if concept in CONCEPT_MAP:
                    concept_cases[concept].append({
                        'entity_name': entity_name, 'date': rec.get('date', ''),
                        'case_num': rec.get('case_num', ''),
                        'detail': clean_violation_text(vc['text']),
                        'subtype': '机构',
                    })

    print(f"{len(concept_cases)} 个概念类型")

    created = 0
    for concept_name, cases in sorted(concept_cases.items()):
        if len(cases) < 2: continue
        filepath = CONCEPTS_DIR / f"{concept_name}.md"
        filepath.write_text(build_concept_page(concept_name, cases), encoding='utf-8')
        created += 1
        entity_ct = len(set(c['entity_name'] for c in cases))
        print(f"  {concept_name}: {entity_ct} entities, {len(cases)} cases")

    print(f"创建了 {created} 个 concept 页面")
    return concept_cases


if __name__ == '__main__':
    main()
