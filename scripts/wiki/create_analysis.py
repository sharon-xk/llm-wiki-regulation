#!/usr/bin/env python3
"""
创建/更新 analysis 页面 (年度趋势 + 最新处罚).
用法: python3 scripts/wiki/create_analysis.py
"""
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import date

BASE_DIR = Path(__file__).parent.parent.parent
ANALYSIS_DIR = BASE_DIR / "wiki" / "analysis"
ENTITIES_DIR = BASE_DIR / "wiki" / "institutions"


def clean_html_name(name):
    normalized = name.replace('"', '"').replace('"', '"')
    prefixes = [
        '中国证券投资基金业协会（以下简称"协会"）已公告',
        '中国证券投资基金业协会（以下简称"协会"）已将',
        '中国证券投资基金业协会（以下简称协会）已公告',
        '中国证券投资基金业协会（以下简称协会）已将',
        '关于注销', '关于请', '协会在日常工作中发现',
        '协会在处理投诉案件中发现', '协会的自律核查工作涉及到',
        '无法与', '现有', '协会已公告',
    ]
    for p in sorted(prefixes, key=len, reverse=True):
        if normalized.startswith(p):
            name = name[len(p):]
            break
    name = re.sub(r'等\d+家.*', '', name)
    return name.strip()


def entity_link(name):
    safe = re.sub(r'[\\/:*?"<>|;,\'"()（）【】〈〈〉、、\s\-—]', '', name)[:40]
    return f'[{name}](/wiki/institutions/{safe}.md)'


def build_annual_trend(concept_cases, txt_data, html_data):
    """年度趋势分析 (仅机构)"""
    yearly_jlcf = defaultdict(int)
    for name, records in txt_data.get('纪律处分_机构', {}).items():
        for rec in records:
            year = rec.get('date', '')[:4]
            if year and year.isdigit():
                yearly_jlcf[year] += 1

    yearly_ycjy = Counter()
    yearly_sljg = Counter()
    for module_type in ['异常经营', '失联机构']:
        for rec in html_data.get(module_type, []):
            if rec.get('title') in ('异常经营', '失联机构', '自律措施'): continue
            year = rec.get('date', '')[:4]
            if year and year.isdigit():
                if module_type == '异常经营':
                    yearly_ycjy[year] += len(rec.get('companies', []))
                else:
                    yearly_sljg[year] += len(rec.get('companies', []))

    violation_counter = Counter()
    for concept_name, cases in concept_cases.items():
        violation_counter[concept_name] = len(cases)

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
        content += "| 年份 | 机构数 |\n|------|--------|\n"
        for year in all_years:
            inst = yearly_jlcf.get(year, 0)
            if inst > 0: content += f"| {year} | {inst} |\n"

    content += "\n## 异常经营 & 失联机构年度统计\n\n| 年份 | 异常经营 | 失联机构 |\n|------|----------|----------|\n"
    for year in all_years:
        yc, sl = yearly_ycjy.get(year, 0), yearly_sljg.get(year, 0)
        if yc + sl > 0: content += f"| {year} | {yc} | {sl} |\n"

    content += "\n## 违规类型分布 (纪律处分)\n\n| 违规类型 | 案例数 |\n|----------|--------|\n"
    for vtype, count in violation_counter.most_common(15):
        content += f"| {vtype} | {count} |\n"

    if violation_counter:
        mc = violation_counter.most_common(1)[0]
        content += f"\n## 分析说明\n\n- 纪律处分数据覆盖 {len(all_years)} 年\n- 最常见违规类型：{mc[0]}（{mc[1]}个案例）\n"
    content += f"\n---\n*数据更新日期：{date.today().isoformat()}*\n"
    (ANALYSIS_DIR / '分析_年度趋势.md').write_text(content, encoding='utf-8')
    print(f"  分析_年度趋势: {len(all_years)} years")


def build_latest_records(concept_cases, html_data):
    """最新处罚记录 (全模块)"""
    all_records = []
    for concept_name, cases in concept_cases.items():
        for c in cases:
            all_records.append({'date': c['date'], 'name': c['entity_name'],
                'module': '纪律处分', 'case_num': c.get('case_num', ''),
                'violation': c['detail'][:150], 'concept': concept_name})

    for module_type in ['异常经营', '失联机构']:
        for rec in html_data.get(module_type, []):
            if rec.get('title') in ('异常经营', '失联机构', '自律措施'): continue
            for company in rec.get('companies', []):
                cleaned = clean_html_name(company['name'])
                if not cleaned or len(cleaned) < 4: continue
                all_records.append({'date': rec['date'], 'name': cleaned,
                    'module': module_type, 'case_num': '',
                    'violation': rec.get('title', ''), 'concept': module_type})

    seen = set()
    unique = []
    for r in sorted(all_records, key=lambda x: x['date'], reverse=True):
        key = (r['date'], r['name'][:40], r['module'])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    content = f"""---
type: analysis
name: 最新处罚记录
description: 最近发布的处罚信息 (全模块)
date: {date.today().isoformat()}
tags: [分析, 最新]
---

# 最新处罚记录

"""
    for i, rec in enumerate(unique[:50]):
        elink = entity_link(rec['name'])
        content += f"### {i+1}. {elink}\n\n- **日期**: {rec['date']}\n- **模块**: {rec['module']}\n"
        if rec['case_num']: content += f"- **字号**: {rec['case_num']}\n"
        content += f"- **摘要**: {rec['violation'][:200]}\n\n"

    content += f"\n---\n*数据更新日期：{date.today().isoformat()}*\n"
    (ANALYSIS_DIR / '分析_最新处罚.md').write_text(content, encoding='utf-8')
    print(f"  分析_最新处罚: {len(unique)} records (top 50 shown)")


def main():
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    parsed_path = BASE_DIR / "scripts" / "tmp" / "parsed_data_with_concepts.json"
    html_path = BASE_DIR / "raw" / "parsed" / "parsed_html_results.json"
    txt_path = BASE_DIR / "raw" / "parsed" / "parsed_txt_results.json"

    if not parsed_path.exists():
        print(f"数据文件不存在: {parsed_path}")
        return

    with open(parsed_path, 'r', encoding='utf-8') as f:
        concept_data = json.load(f)

    concept_cases = defaultdict(list)
    for rec in concept_data:
        entity_name = rec['entity'].replace('.md', '')
        for vc in rec.get('violation_concepts', []):
            for concept in vc['concepts']:
                concept_cases[concept].append({'entity_name': entity_name,
                    'date': rec.get('date', ''), 'case_num': rec.get('case_num', ''),
                    'detail': vc['text'], 'subtype': '机构'})

    with open(html_path, 'r', encoding='utf-8') as f:
        html_data = json.load(f)
    with open(txt_path, 'r', encoding='utf-8') as f:
        txt_data = json.load(f)

    build_annual_trend(concept_cases, txt_data, html_data)
    build_latest_records(concept_cases, html_data)
    print("Analysis 页面已更新")


if __name__ == '__main__':
    main()
