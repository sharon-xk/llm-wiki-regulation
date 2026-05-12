#!/usr/bin/env python3
"""
分析违规类型并创建概念页和分析页 - 改进版
"""
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import date

def classify_violation(violation_text):
    """将违规文本分类到标准类型"""
    v = violation_text.strip()

    if not v:
        return None

    # 标准化分类
    patterns = [
        (r'未尽.*勤勉.*义务|谨慎.*义务', '未尽谨慎勤勉义务'),
        (r'挪用.*基金|侵占.*基金财产', '挪用基金财产'),
        (r'违规.*募集|非法.*募集|擅自.*募集', '违规募集'),
        (r'承诺.*保本|承诺.*收益|保本.*承诺', '承诺保本收益'),
        (r'信息披露.*违规|未.*披露|未按规定披露', '信息披露违规'),
        (r'利益输送|老鼠仓', '利益输送'),
        (r'内幕交易', '内幕交易'),
        (r'超范围.*经营|超出.*范围', '超范围经营'),
        (r'未按规定.*登记|未.*登记备案|未.*备案', '未按规定登记备案'),
        (r'委托.*无资质|委托.*不规范', '委托无资质机构'),
        (r'让渡.*管理权限|让渡.*职责', '让渡管理权限'),
        (r'投资者.*适当性|适当性.*违规|合格投资者', '投资者适当性违规'),
        (r'基金.*安全|安全.*保管', '基金财产安全违规'),
        (r'关联交易|关联.*交易.*违规', '关联交易违规'),
        (r'估值.*违规|净值.*违规|估值.*不当', '估值违规'),
        (r'备案.*信息.*虚假|登记.*虚假|虚假.*登记', '虚假登记备案'),
    ]

    for pattern, category in patterns:
        if re.search(pattern, v):
            return category

    return None

def create_concept_pages(entities_data, entities_dir):
    """创建概念页"""
    concepts_dir = Path(entities_dir).parent / 'concepts'
    concepts_dir.mkdir(parents=True, exist_ok=True)

    # 统计每种违规类型
    violation_stats = defaultdict(list)

    for module, entities in entities_data.items():
        for name, records in entities.items():
            for rec in records:
                violations = rec.get('violations', [])
                for v in violations:
                    category = classify_violation(v)
                    if category:
                        violation_stats[category].append({
                            'name': name,
                            'detail': v,
                            'date': rec.get('date', ''),
                            'source': rec.get('source', '')
                        })

    # 按数量排序
    sorted_violations = sorted(violation_stats.items(), key=lambda x: len(x[1]), reverse=True)

    created = 0
    for violation_type, cases in sorted_violations[:15]:  # 最多15个
        if len(cases) < 2:
            continue

        # 统计时间分布
        years = Counter()
        current_year = 2026
        for c in cases:
            year = c['date'][:4] if c['date'] else ''
            # 过滤不合理年份：1950年之前或当前年份之后
            if year and year.isdigit() and 1950 <= int(year) <= current_year:
                years[year] += 1
            else:
                years['未知'] += 1

        content = f"""---
type: concept
name: {violation_type}
description: {violation_type}相关违规行为及处罚案例
case_count: {len(cases)}
tags: [违规类型, 纪律处分]
---

# {violation_type}

## 概述

本概念页收录 **{len(cases)}** 个涉及「{violation_type}」的违规案例。

## 时间分布

"""

        for year, count in sorted(years.items(), reverse=True)[:5]:
            content += f"- {year}年：{count}个案例\n"

        content += "\n## 典型案例\n\n"

        # 按日期排序，取最新案例
        cases.sort(key=lambda x: x['date'], reverse=True)
        for i, c in enumerate(cases[:20]):
            content += f"### {i+1}. {c['name']}\n\n"
            content += f"- **时间**：{c['date']}\n"
            # 完整显示违规行为，不截断
            detail = c['detail'] if c['detail'] else '暂无详细信息'
            content += f"- **违规行为**：{detail}\n\n"

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

        # 干净的文件名
        safe_name = re.sub(r'[\\/:*?"<>|]', '', violation_type)
        filepath = concepts_dir / f"{safe_name}.md"
        filepath.write_text(content, encoding='utf-8')
        created += 1

    return created

def create_analysis_pages(entities_data, output_dir):
    """创建分析页"""
    analysis_dir = Path(output_dir) / 'analysis'
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # 统计年度数据
    yearly = defaultdict(lambda: {'机构': 0, '人员': 0})
    violation_counter = Counter()

    for module, entities in entities_data.items():
        subtype = '机构' if '机构' in module else '人员'

        for name, records in entities.items():
            for rec in records:
                year = rec.get('date', '')[:4]
                if year and year.isdigit():
                    yearly[year][subtype] += 1

                # 统计违规类型
                for v in rec.get('violations', []):
                    cat = classify_violation(v)
                    if cat:
                        violation_counter[cat] += 1

    years = sorted(yearly.keys())

    # 创建年度趋势分析
    content = f"""---
type: analysis
name: 纪律处分年度趋势分析
description: 纪律处分数量年度统计及趋势
date: {date.today().isoformat()}
tags: [分析, 趋势, 年度统计]
---

# 纪律处分年度趋势分析

## 年度统计

"""

    if years:
        content += "| 年份 | 机构 | 人员 | 合计 |\n"
        content += "|------|------|------|------|\n"

        for year in years:
            inst = yearly[year]['机构']
            pers = yearly[year]['人员']
            content += f"| {year} | {inst} | {pers} | {inst+pers} |\n"

    content += "\n## 违规类型分布\n\n"

    content += "| 违规类型 | 案例数 |\n"
    content += "|----------|--------|\n"
    for vtype, count in violation_counter.most_common(15):
        content += f"| {vtype} | {count} |\n"

    content += "\n## 分析说明\n\n"
    if len(years) >= 2:
        last_year = years[-1]
        prev_year = years[-2]
        last_total = yearly[last_year]['机构'] + yearly[last_year]['人员']
        prev_total = yearly[prev_year]['机构'] + yearly[prev_year]['人员']
        change = last_total - prev_total
        content += f"- {last_year}年共处分 {last_total} 个主体（机构{yearly[last_year]['机构']}个，个人{yearly[last_year]['人员']}个）\n"
        if change != 0:
            content += f"- 同比{'增加' if change > 0 else '减少'} {abs(change)} 个\n"
        content += f"- 最常见的违规类型：{violation_counter.most_common(1)[0][0]}（{violation_counter.most_common(1)[0][1]}个案例）\n"

    content += f"\n---\n*数据更新日期：{date.today().isoformat()}*\n"

    (analysis_dir / "分析_年度趋势.md").write_text(content, encoding='utf-8')

    # 创建最新处罚页面
    content = f"""---
type: analysis
name: 最新处罚记录
description: 最近发布的纪律处分信息
date: {date.today().isoformat()}
tags: [分析, 最新]
---

# 最新处罚记录

以下是按最新日期排列的处罚记录：

"""

    for module, entities in entities_data.items():
        subtype = '机构' if '机构' in module else '人员'

        all_records = []
        for name, records in entities.items():
            for rec in records:
                all_records.append({
                    'date': rec.get('date', ''),
                    'name': name,
                    'case_num': rec.get('case_num', ''),
                    'violations': rec.get('violations', []),
                    'type': subtype
                })

        all_records.sort(key=lambda x: x['date'], reverse=True)

        if all_records:
            content += f"## {subtype}\n\n"
            for i, rec in enumerate(all_records[:10]):
                content += f"### {i+1}. {rec['name']}\n\n"
                content += f"- **日期**: {rec['date']}\n"
                if rec['case_num']:
                    content += f"- **字号**: {rec['case_num']}\n"
                if rec['violations']:
                    content += f"- **主要违规**: {rec['violations'][0][:80]}\n"
                content += "\n"

    (analysis_dir / "分析_最新处罚.md").write_text(content, encoding='utf-8')

    return years

def main():
    base_dir = Path('/Users/sharon/ai-project/llm-wiki-regulation')
    raw_dir = base_dir / 'raw'
    wiki_dir = base_dir / 'wiki'

    # 加载解析结果
    with open(raw_dir / 'parsed_txt_results.json', 'r', encoding='utf-8') as f:
        txt_results = json.load(f)

    # 创建概念页
    print("创建概念页...")
    entities_dir = wiki_dir / 'entities'
    created_concepts = create_concept_pages(txt_results, entities_dir)
    print(f"创建了 {created_concepts} 个概念页")

    # 创建分析页
    print("创建分析页...")
    years = create_analysis_pages(txt_results, wiki_dir)
    print(f"创建了 2 个分析页 (覆盖 {len(years)} 年数据)")

    # 更新 index.md
    concept_files = list((wiki_dir / 'concepts').glob('*.md'))
    analysis_files = list((wiki_dir / 'analysis').glob('*.md'))

    index_content = f"""# 基金业协会处罚知识库

> 本知识库收集整理中国证券投资基金业协会（AMAC）自律管理处罚信息，供查询和分析。

---

## 实体 (entities)

- [纪律处分实体索引](wiki/entities/) — {len(list(entities_dir.glob('*.md')))} 个实体

## 模块 (modules)

- [纪律处分](wiki/modules/纪律处分.md) — 纪律处分决定书

## 概念 (concepts)

"""
    for cf in sorted(concept_files)[:15]:
        name = cf.stem
        index_content += f"- [{name}](wiki/concepts/{name}.md)\n"

    if len(concept_files) > 15:
        index_content += f"- ... 还有 {len(concept_files) - 15} 个概念页\n"

    index_content += """

## 分析 (analysis)

"""
    for af in sorted(analysis_files):
        name = af.stem
        index_content += f"- [{name}](wiki/analysis/{name}.md)\n"

    index_content += f"""

---
*最后更新：{date.today().isoformat()}*
"""

    (base_dir / 'index.md').write_text(index_content, encoding='utf-8')
    print("更新了 index.md")

    print("\n完成!")

if __name__ == '__main__':
    main()