#!/usr/bin/env python3
"""
分析违规类型并创建概念页和分析页
"""
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import date

def extract_violation_types(results):
    """从解析结果中提取违规类型"""
    violation_keywords = defaultdict(list)

    for module, entities in results.items():
        for name, records in entities.items():
            for rec in records:
                violations = rec.get('violations', [])
                for v in violations:
                    # 提取关键违规类型
                    v = v.strip()
                    if not v:
                        continue

                    # 分类
                    if '未尽' in v or '勤勉' in v or '谨慎' in v:
                        violation_keywords['未尽谨慎勤勉义务'].append((name, v))
                    elif '挪用' in v or '侵占' in v or '侵占' in v:
                        violation_keywords['挪用基金财产'].append((name, v))
                    elif '违规募集' in v or '非法募集' in v or '公开募集' in v:
                        violation_keywords['违规募集'].append((name, v))
                    elif '承诺' in v and ('保本' in v or '收益' in v or '最低收益' in v):
                        violation_keywords['承诺保本收益'].append((name, v))
                    elif '挪用' in v:
                        violation_keywords['挪用基金财产'].append((name, v))
                    elif '信息披露' in v or '未披露' in v or '披露' in v:
                        violation_keywords['信息披露违规'].append((name, v))
                    elif '利益输送' in v or '老鼠仓' in v:
                        violation_keywords['利益输送'].append((name, v))
                    elif '内幕交易' in v:
                        violation_keywords['内幕交易'].append((name, v))
                    elif '超范围' in v or '超出' in v:
                        violation_keywords['超范围经营'].append((name, v))
                    elif '登记' in v or '备案' in v:
                        violation_keywords['未按规定登记备案'].append((name, v))
                    elif '委托' in v and ('不规范' in v or '无资质' in v):
                        violation_keywords['委托无资质机构提供服务'].append((name, v))
                    elif '让渡' in v and '管理' in v:
                        violation_keywords['让渡管理权限'].append((name, v))
                    else:
                        # 其他 - 取前20字作为标签
                        key = v[:20] if len(v) > 20 else v
                        violation_keywords[key].append((name, v))

    return violation_keywords

def create_concept_pages(violation_keywords, entities_dir):
    """创建概念页"""
    concepts_dir = Path(entities_dir).parent / 'concepts'
    concepts_dir.mkdir(parents=True, exist_ok=True)

    created = 0

    # 取最常见的违规类型
    sorted_violations = sorted(violation_keywords.items(), key=lambda x: len(x[1]), reverse=True)

    for violation_type, cases in sorted_violations[:20]:  # 最多20个
        if len(cases) < 2:  # 至少2个案例才创建概念页
            continue

        content = f"""---
type: concept
name: {violation_type}
description: {violation_type}相关违规行为汇总
case_count: {len(cases)}
tags: [违规类型, 纪律处分]
---

# {violation_type}

## 定义

{violation_type}是基金行业常见的违规行为类型。

## 典型案例

"""

        for name, detail in cases[:30]:  # 最多30个案例
            content += f"### {name}\n\n"
            content += f"- {detail[:150]}\n\n"

        content += f"""## 相关法规

- 《中华人民共和国证券投资基金法》
- 《私募投资基金监督管理暂行办法》
- 《中国证券投资基金业协会自律管理规则》

## 处罚措施

常见处罚措施包括：警告、罚款、取消资格、撤销登记、公开谴责等。
"""

        # 安全文件名
        safe_name = re.sub(r'[\\/:*?"<>|]', '', violation_type)
        filepath = concepts_dir / f"{safe_name}.md"
        filepath.write_text(content, encoding='utf-8')
        created += 1

    return created

def create_analysis_pages(results, output_dir):
    """创建分析页"""
    analysis_dir = Path(output_dir) / 'analysis'
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # 统计年度数据
    yearly_stats = defaultdict(lambda: {'机构': 0, '人员': 0})

    for module, entities in results.items():
        for name, records in entities.items():
            for rec in records:
                year = rec.get('date', '')[:4]
                if year and year.isdigit():
                    if '人员' in module:
                        yearly_stats[year]['人员'] += 1
                    else:
                        yearly_stats[year]['机构'] += 1

    # 创建年度趋势分析
    years = sorted(yearly_stats.keys())
    current_year = years[-1] if years else '2024'

    content = f"""---
type: analysis
name: 纪律处分年度趋势分析
description: 纪律处分数量年度统计
date: {date.today().isoformat()}
tags: [分析, 趋势]
---

# 纪律处分年度趋势分析

## 整体趋势

"""

    if years:
        content += "| 年份 | 机构处分 | 人员处分 | 合计 |\n"
        content += "|-------|---------|---------|-------|\n"

        for year in years:
            stats = yearly_stats[year]
            total = stats['机构'] + stats['人员']
            content += f"| {year} | {stats['机构']} | {stats['人员']} | {total} |\n"

    content += """

## 分析

"""

    if len(years) >= 2:
        last_year = years[-1]
        prev_year = years[-2] if len(years) >= 2 else None
        if prev_year:
            last_total = yearly_stats[last_year]['机构'] + yearly_stats[last_year]['人员']
            prev_total = yearly_stats[prev_year]['机构'] + yearly_stats[prev_year]['人员']
            change = last_total - prev_total
            change_str = f"+{change}" if change > 0 else str(change)
            content += f"- {last_year}年共处分 {last_total} 个主体，同比{'增加' if change > 0 else '减少'} {change_str}\n"

    content += """

## 高频违规类型

"""

    # 添加高频违规类型统计
    violation_keywords = extract_violation_types(results)
    sorted_violations = sorted(violation_keywords.items(), key=lambda x: len(x[1]), reverse=True)

    content += "| 违规类型 | 案例数 |\n"
    content += "|---------|-------|\n"
    for vtype, cases in sorted_violations[:10]:
        content += f"| {vtype[:30]} | {len(cases)} |\n"

    content += """

## 数据说明

- 数据来源：中国证券投资基金业协会（AMAC）官网
- 统计口径：纪律处分决定书涉及的当事人和机构
- 更新日期：""" + date.today().isoformat() + """
"""

    (analysis_dir / "分析_年度趋势.md").write_text(content, encoding='utf-8')

    # 创建最新处罚页面
    latest_content = """---
type: analysis
name: 最新处罚记录
description: 最近发布的纪律处分信息
date: """ + date.today().isoformat() + """
tags: [分析, 最新]
---

# 最新处罚记录

"""

    for module, entities in results.items():
        if '机构' in module:
            subtype = '机构'
        elif '人员' in module:
            subtype = '人员'
        else:
            subtype = module

        # 取每个模块最新的3条
        all_records = []
        for name, records in entities.items():
            for rec in records:
                all_records.append((rec.get('date', ''), name, rec))

        all_records.sort(key=lambda x: x[0], reverse=True)

        content += f"## {subtype}\n\n"
        for i, (dt, name, rec) in enumerate(all_records[:5]):
            content += f"### {i+1}. {name}\n\n"
            content += f"- **日期**: {dt}\n"
            if rec.get('case_num'):
                content += f"- **字号**: {rec['case_num']}\n"
            if rec.get('violations'):
                content += f"- **违规**: {rec['violations'][0][:60]}\n"
            content += "\n"

    (analysis_dir / "分析_最新处罚.md").write_text(content, encoding='utf-8')

    return len(years)

def main():
    base_dir = Path('/Users/sharon/ai-project/llm-wiki-regulation')
    raw_dir = base_dir / 'raw'
    wiki_dir = base_dir / 'wiki'

    # 加载解析结果
    with open(raw_dir / 'parsed_txt_results.json', 'r', encoding='utf-8') as f:
        txt_results = json.load(f)

    # 提取违规类型
    print("分析违规类型...")
    violation_keywords = extract_violation_types(txt_results)
    print(f"找到 {len(violation_keywords)} 种违规类型")

    # 创建概念页
    print("创建概念页...")
    entities_dir = wiki_dir / 'entities'
    created_concepts = create_concept_pages(violation_keywords, entities_dir)
    print(f"创建了 {created_concepts} 个概念页")

    # 创建分析页
    print("创建分析页...")
    years_count = create_analysis_pages(txt_results, wiki_dir)
    print(f"创建了 2 个分析页，覆盖 {years_count} 年数据")

    print("\n完成!")

if __name__ == '__main__':
    main()