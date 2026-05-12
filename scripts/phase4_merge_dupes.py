"""
修复因文件名碰撞导致丢失数据的 2 个 entity：
北京天星资本股份有限公司 (2 cases)
浙江厚道资产管理有限公司 (2 cases)
将多案合并到单个 entity 文件中
"""
import json
import os
import re

ENTITY_DIR = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities"
PARSED = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/parsed_data_with_concepts.json"


def truncate_text(text, max_len=300):
    if len(text) <= max_len:
        return text
    cutoff = text[:max_len].rfind('。')
    if cutoff > max_len * 0.6:
        return text[:cutoff + 1]
    return text[:max_len] + '...'


def build_merged_entity(entity_name, records):
    """合并同一 entity 的多条处罚记录"""
    # 从第一个 record 获取 entity 基础名
    entity_base = entity_name.replace('.md', '')
    all_concepts = set()
    for r in records:
        for vc in r.get('violation_concepts', []):
            all_concepts.update(vc['concepts'])

    # 确定日期范围
    dates = sorted([r['date'] for r in records if r.get('date')])
    first_date = dates[0][:7] if dates else ''
    latest_date = dates[-1][:7] if dates else ''

    lines = []
    lines.append('## 基本信息')
    lines.append('')
    lines.append(f'- **名称**: {entity_base}')
    lines.append(f'- **类型**: 基金管理人')
    lines.append(f'- **首次处罚**: {first_date}')
    lines.append(f'- **最近处罚**: {latest_date}')
    lines.append(f'- **案件数**: {len(records)}')
    lines.append('')

    lines.append('## 处罚记录')
    lines.append('')

    for case_idx, r in enumerate(records, 1):
        lines.append(f'### 案件 {case_idx}')
        lines.append('')
        if r.get('case_num'):
            lines.append(f'- **字号**: {r["case_num"]}')
        if r.get('date'):
            lines.append(f'- **日期**: {r["date"]}')
        lines.append(f'- **来源**: {r["source"]}')

        violations = r.get('violations', [])
        vconcepts = r.get('violation_concepts', [])
        if violations:
            lines.append('')
            lines.append('**违规行为**:')
            lines.append('')
            for i, v_text in enumerate(violations):
                clean = re.sub(r'\s+', ' ', v_text).strip()
                display = truncate_text(clean, 300)
                lines.append(f'{i + 1}. {display}')
                lines.append('')

            lines.append('**违规行为对应的概念页**:')
            lines.append('')
            for i, vc in enumerate(vconcepts):
                clean = re.sub(r'\s+', ' ', vc['text']).strip()
                summary = truncate_text(clean, 100)
                if vc['concepts']:
                    links = '、'.join([f'[{c}](/wiki/concepts/{c}.md)' for c in vc['concepts']])
                    lines.append(f'{i + 1}. {summary} → {links}')
                else:
                    lines.append(f'{i + 1}. {summary} → *待创建概念页*')
                lines.append('')

        penalty = r.get('penalty', '')
        if penalty:
            lines.append(f'- **处罚措施**: {penalty}')
            lines.append('')

        legal = r.get('legal_basis', '')
        if legal:
            lines.append(f'- **法规依据**: {legal}')
            lines.append('')

    # 违规类型汇总
    lines.append('## 违规类型汇总')
    lines.append('')
    if all_concepts:
        for c in sorted(all_concepts):
            lines.append(f'- [{c}](/wiki/concepts/{c}.md)')
    else:
        lines.append('- *暂无归类*')
    lines.append('')

    # frontmatter
    fm = f"""---
type: entity
name: {entity_base}
subtype: 基金管理人
source_count: {len(records)}
first_incident: {first_date}
latest_incident: {latest_date}
tags: [纪律处分]
---

"""
    return fm + '\n'.join(lines)


def main():
    with open(PARSED) as f:
        data = json.load(f)

    # 找出重复的 entity
    from collections import Counter
    entity_counts = Counter(r['entity'] for r in data)
    dupes = [e for e, c in entity_counts.items() if c > 1]

    print(f"需合并的 entity: {len(dupes)}")
    for entity_name in dupes:
        records = [r for r in data if r['entity'] == entity_name]
        records.sort(key=lambda r: r.get('date', ''))
        print(f"\n  {entity_name}: {len(records)} cases")
        for r in records:
            print(f"    - {r['date']} | {r['source']} | {r['case_num']}")

        # 构建合并后的内容
        merged_content = build_merged_entity(entity_name, records)

        # 写入
        fpath = os.path.join(ENTITY_DIR, entity_name)
        with open(fpath, 'w') as f:
            f.write(merged_content)
        print(f"    → 已合并写入 {fpath}")


if __name__ == "__main__":
    main()
