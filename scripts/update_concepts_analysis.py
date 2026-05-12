#!/usr/bin/env python3
"""
更新 concepts 和 analysis 页面。

数据源:
- scripts/tmp/parsed_data_with_concepts.json (纪律处分, 341 records, 预计算 concept 映射)
- raw/parsed_html_results.json (异常经营/失联机构, for analysis pages)

处理流程:
1. 读取 parsed_data_with_concepts.json, 按 concept 聚合案例
2. 为每个 concept 重建页面 (完整文本, entity 链接, 准确计数)
3. 更新分析页 (年度趋势 + 最新处罚, 覆盖全部模块)
4. 更新 index.md, log.md
"""

import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import date


BASE_DIR = Path('/Users/sharon/ai-project/llm-wiki-regulation')
CONCEPTS_DIR = BASE_DIR / 'wiki' / 'concepts'
ANALYSIS_DIR = BASE_DIR / 'wiki' / 'analysis'
ENTITIES_DIR = BASE_DIR / 'wiki' / 'entities'


def clean_html_name(name):
    """清洗 HTML 解析出的公司名 — 与 create_html_entities.py 相同逻辑"""
    normalized = name.replace('“', '"').replace('”', '"')
    prefixes = [
        '中国证券投资基金业协会（以下简称"协会"）已公告',
        '中国证券投资基金业协会（以下简称"协会"）已将',
        '中国证券投资基金业协会（以下简称"协会"）在自律核查工作中发现',
        '中国证券投资基金业协会（以下简称协会）已公告',
        '中国证券投资基金业协会（以下简称协会）已将',
        '关于注销', '关于请',
        '协会在日常工作中发现',
        '协会在处理投诉案件中发现',
        '协会的自律核查工作涉及到',
        '无法与', '现有', '协会已公告',
    ]
    for p in sorted(prefixes, key=len, reverse=True):
        if normalized.startswith(p):
            name = name[len(p):]
            break
    name = re.sub(r'等\d+家.*', '', name)
    return name.strip()

# Concept name → display name mapping (for filename)
CONCEPT_MAP = {
    '信息披露违规': '信息披露违规',
    '未按规定登记备案': '未按规定登记备案',
    '未尽谨慎勤勉义务': '未尽谨慎勤勉义务',
    '投资者适当性违规': '投资者适当性违规',
    '违规募集': '违规募集',
    '承诺保本收益': '承诺保本收益',
    '虚假登记备案': '虚假登记备案',
    '挪用基金财产': '挪用基金财产',
    '关联交易违规': '关联交易违规',
    '利益输送': '利益输送',
}


def clean_violation_text(text):
    """清理违规文本中的 OCR artifact"""
    # 移除孤立的 "1" artifact (空格包围的单个 1)
    text = re.sub(r'\s+1\s+', '', text)
    # 移除行首/行尾孤立的 1
    text = re.sub(r'^\s*1\s+', '', text)
    text = re.sub(r'\s+1\s*$', '', text)
    # 压缩多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def entity_link(entity_name):
    """生成 entity 页面的 markdown 链接"""
    safe = re.sub(r'[\\/:*?"<>|;,\'"()（）【】〈〈〉、、\s\-—]', '', entity_name)[:40]
    return f'[{entity_name}](/wiki/entities/{safe}.md)'


def build_concept_content(concept_name, cases):
    """为一个 concept 构建页面内容"""
    cases.sort(key=lambda x: x['date'], reverse=True)

    # 统计时间分布
    years = Counter()
    for c in cases:
        year = c['date'][:4] if c['date'] else ''
        if year and year.isdigit() and 1950 <= int(year) <= 2030:
            years[year] += 1
        else:
            years['未知'] += 1

    # Dedup by entity (keep earliest per entity for count, but show all)
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

    # 按日期排序，取最多 30 条
    for i, c in enumerate(cases[:30]):
        elink = entity_link(c['entity_name'])
        content += f"### {i+1}. {elink}\n\n"
        content += f"- **日期**：{c['date']}\n"
        if c.get('case_num'):
            content += f"- **字号**：{c['case_num']}\n"
        content += f"- **违规行为**：{c['detail']}\n\n"

    # 如果案例超过 30，添加省略提示
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


def create_concept_pages(concept_cases):
    """创建所有 concept 页面"""
    CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)
    created = 0

    for concept_name, cases in sorted(concept_cases.items()):
        if len(cases) < 2:
            continue

        content = build_concept_content(concept_name, cases)
        filepath = CONCEPTS_DIR / f"{concept_name}.md"
        filepath.write_text(content, encoding='utf-8')
        created += 1
        print(f"  {concept_name}: {len(set(c['entity_name'] for c in cases))} entities, {len(cases)} cases")

    return created


def create_annual_trend_analysis(concept_cases, txt_results, html_data):
    """创建年度趋势分析页 — 覆盖全部 4 个模块，仅机构数据"""
    # === 纪律处分年度统计 (from parsed_txt_results.json 纪律处分_机构 only) ===
    yearly_jlcf = defaultdict(int)

    for name, records in txt_results.get('纪律处分_机构', {}).items():
        for rec in records:
            year = rec.get('date', '')[:4]
            if year and year.isdigit():
                yearly_jlcf[year] += 1

    # === 异常经营/失联机构年度统计 (from parsed_html_results.json) ===
    yearly_ycjy = Counter()
    yearly_sljg = Counter()

    for module_type in ['异常经营', '失联机构']:
        for rec in html_data.get(module_type, []):
            if rec.get('title') in ('异常经营', '失联机构', '自律措施'):
                continue
            date_str = rec.get('date', '')
            year = date_str[:4]
            if year and year.isdigit():
                if module_type == '异常经营':
                    yearly_ycjy[year] += len(rec.get('companies', []))
                else:
                    yearly_sljg[year] += len(rec.get('companies', []))

    # === Violation type distribution ===
    violation_counter = Counter()
    for concept_name, cases in concept_cases.items():
        violation_counter[concept_name] = len(cases)

    # === Build page ===
    all_years = sorted(set(list(yearly_jlcf.keys()) + list(yearly_ycjy.keys()) + list(yearly_sljg.keys())))
    all_years = [y for y in all_years if y.isdigit() and 1950 <= int(y) <= 2030]

    content = f"""---
type: analysis
name: 处罚年度趋势分析
description: 全模块处罚数量年度统计及趋势（仅机构）
date: {date.today().isoformat()}
tags: [分析, 趋势, 年度统计]
---

# 处罚年度趋势分析

> 注：本统计仅包含机构，不包含个人。

## 纪律处分年度统计

"""
    if all_years:
        content += "| 年份 | 机构数 |\n"
        content += "|------|--------|\n"
        for year in all_years:
            inst = yearly_jlcf.get(year, 0)
            if inst > 0:
                content += f"| {year} | {inst} |\n"

    content += f"""

## 异常经营 & 失联机构年度统计

| 年份 | 异常经营 | 失联机构 |
|------|----------|----------|
"""
    for year in all_years:
        yc = yearly_ycjy.get(year, 0)
        sl = yearly_sljg.get(year, 0)
        if yc + sl > 0:
            content += f"| {year} | {yc} | {sl} |\n"

    content += "\n## 违规类型分布 (纪律处分)\n\n"
    content += "| 违规类型 | 案例数 |\n"
    content += "|----------|--------|\n"
    for vtype, count in violation_counter.most_common(15):
        content += f"| {vtype} | {count} |\n"

    content += f"""

## 分析说明

- 纪律处分数据覆盖 {len(all_years)} 年（仅机构）
- 最常见的违规类型：{violation_counter.most_common(1)[0][0]}（{violation_counter.most_common(1)[0][1]}个案例）
- 异常经营和失联机构数据来自 AMAC 公告

---
*数据更新日期：{date.today().isoformat()}*
"""
    (ANALYSIS_DIR / '分析_年度趋势.md').write_text(content, encoding='utf-8')
    print(f"  分析_年度趋势: {len(all_years)} years covered")


def create_latest_analysis(concept_cases, html_data):
    """创建最新处罚页面 — 覆盖全部模块"""
    all_records = []

    # 纪律处分
    for concept_name, cases in concept_cases.items():
        for c in cases:
            all_records.append({
                'date': c['date'],
                'name': c['entity_name'],
                'module': '纪律处分',
                'case_num': c.get('case_num', ''),
                'violation': c['detail'][:150],
                'concept': concept_name,
            })

    # 异常经营/失联机构 — 清洗公司名
    for module_type in ['异常经营', '失联机构']:
        for rec in html_data.get(module_type, []):
            if rec.get('title') in ('异常经营', '失联机构', '自律措施'):
                continue
            for company in rec.get('companies', []):
                cleaned = clean_html_name(company['name'])
                if not cleaned or len(cleaned) < 4:
                    continue
                all_records.append({
                    'date': rec['date'],
                    'name': cleaned,
                    'module': module_type,
                    'case_num': '',
                    'violation': rec.get('title', ''),
                    'concept': module_type,
                })

    # Dedup and sort
    seen = set()
    unique_records = []
    for r in sorted(all_records, key=lambda x: x['date'], reverse=True):
        key = (r['date'], r['name'][:40], r['module'])
        if key not in seen:
            seen.add(key)
            unique_records.append(r)

    content = f"""---
type: analysis
name: 最新处罚记录
description: 最近发布的处罚信息 (全模块)
date: {date.today().isoformat()}
tags: [分析, 最新]
---

# 最新处罚记录

以下是按最新日期排列的处罚记录，覆盖纪律处分、异常经营、失联机构：

"""
    for i, rec in enumerate(unique_records[:50]):
        elink = entity_link(rec['name'])
        content += f"### {i+1}. {elink}\n\n"
        content += f"- **日期**: {rec['date']}\n"
        content += f"- **模块**: {rec['module']}\n"
        if rec['case_num']:
            content += f"- **字号**: {rec['case_num']}\n"
        content += f"- **摘要**: {rec['violation'][:200]}\n\n"

    content += f"""
---
*数据更新日期：{date.today().isoformat()}*
"""
    (ANALYSIS_DIR / '分析_最新处罚.md').write_text(content, encoding='utf-8')
    print(f"  分析_最新处罚: {len(unique_records)} records (top 50 shown)")


def update_index(concept_count, entity_count):
    """更新 index.md"""
    concept_files = sorted(CONCEPTS_DIR.glob('*.md'))
    analysis_files = sorted(ANALYSIS_DIR.glob('*.md'))

    content = f"""# 基金业协会处罚知识库

> 本知识库收集整理中国证券投资基金业协会（AMAC）自律管理处罚信息，供查询和分析。

---

## 实体 (entities)

- 共 {entity_count} 个实体

## 模块 (modules)

- [纪律处分](wiki/modules/纪律处分.md) — 纪律处分-机构 + 纪律处分-人员
- [异常经营](wiki/modules/异常经营.md) — 异常经营私募基金管理人
- [失联机构](wiki/modules/失联机构.md) — 失联私募基金管理人
- [自律措施](wiki/modules/自律措施.md) — 自律措施

## 概念 (concepts)

"""
    for cf in sorted(concept_files):
        content += f"- [{cf.stem}](wiki/concepts/{cf.stem}.md)\n"

    content += """
## 分析 (analysis)

"""
    for af in sorted(analysis_files):
        content += f"- [{af.stem}](wiki/analysis/{af.stem}.md)\n"

    content += f"""
---
*最后更新：{date.today().isoformat()}*
"""
    (BASE_DIR / 'index.md').write_text(content, encoding='utf-8')
    print(f"  index.md updated")


def update_log(concept_count):
    """更新 log.md"""
    log_entry = f"""
## [{date.today().isoformat()}] update | concepts + analysis 重建

- 数据源: scripts/tmp/parsed_data_with_concepts.json
- 重建 {concept_count} 个 concept 页面 (完整文本, entity 链接)
- 重建 2 个 analysis 页面 (年度趋势 + 最新处罚, 覆盖全模块)
- 脚本: scripts/update_concepts_analysis.py
"""
    log_file = BASE_DIR / 'log.md'
    existing = log_file.read_text(encoding='utf-8') if log_file.exists() else "# 操作日志\n"
    log_file.write_text(existing.rstrip() + log_entry + "\n", encoding='utf-8')
    print(f"  log.md updated")


def main():
    print("=" * 60)
    print("更新 Concepts & Analysis 页面")
    print("=" * 60)

    # 1. Load data
    print("\n[1/4] 加载数据...")
    with open(BASE_DIR / 'scripts' / 'tmp' / 'parsed_data_with_concepts.json', 'r', encoding='utf-8') as f:
        concept_data = json.load(f)

    with open(BASE_DIR / 'raw' / 'parsed_html_results.json', 'r', encoding='utf-8') as f:
        html_data = json.load(f)

    with open(BASE_DIR / 'raw' / 'parsed_txt_results.json', 'r', encoding='utf-8') as f:
        txt_results = json.load(f)

    print(f"  parsed_data_with_concepts: {len(concept_data)} records")
    print(f"  parsed_html: 异常经营({len(html_data.get('异常经营', []))}), 失联机构({len(html_data.get('失联机构', []))})")
    print(f"  parsed_txt: 纪律处分_机构({len(txt_results.get('纪律处分_机构', {}))})")

    # 2. Aggregate cases by concept
    print("\n[2/4] 聚合概念案例...")
    concept_cases = defaultdict(list)

    for rec in concept_data:
        entity_name = rec['entity'].replace('.md', '')
        for vc in rec.get('violation_concepts', []):
            for concept in vc['concepts']:
                if concept in CONCEPT_MAP:
                    concept_cases[concept].append({
                        'entity_name': entity_name,
                        'date': rec.get('date', ''),
                        'case_num': rec.get('case_num', ''),
                        'detail': clean_violation_text(vc['text']),
                        'subtype': '机构',
                    })

    print(f"  {len(concept_cases)} concept types found")
    for cname, cases in sorted(concept_cases.items(), key=lambda x: -len(x[1])):
        print(f"    {cname}: {len(cases)} cases")

    # 3. Create concept pages
    print("\n[3/4] 创建 concept 页面...")
    created = create_concept_pages(concept_cases)
    print(f"  Created {created} concept pages")

    # 4. Create analysis pages
    print("\n[4/4] 创建 analysis 页面...")
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    create_annual_trend_analysis(concept_cases, txt_results, html_data)
    create_latest_analysis(concept_cases, html_data)

    # 5. Update index and log
    entity_count = len(list(ENTITIES_DIR.glob('*.md')))
    update_index(created, entity_count)
    update_log(created)

    print(f"\n===== 完成 =====")
    print(f"Concepts: {created} pages")
    print(f"Analysis: 2 pages")
    print(f"Entities: {entity_count} total")


if __name__ == '__main__':
    main()
