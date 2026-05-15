"""
阶段4: 更新 entity 文件内容
- 保留现有 frontmatter
- 更新 基本信息 / 处罚记录 / 违规类型汇总
输入: scripts/tmp/parsed_data_with_concepts.json
"""
import json
import os
import re
import textwrap
from pathlib import Path

BASE_DIR = str(Path(__file__).parent.parent.parent)
ENTITY_DIR = os.path.join(BASE_DIR, "wiki", "entities")
PARSED_DATA = os.path.join(Path(__file__).parent.parent, "tmp", "parsed_data_with_concepts.json")


def parse_frontmatter(content):
    """解析 yaml frontmatter，返回 (frontmatter_dict, body_text)"""
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if not m:
        return {}, content
    fm_text = m.group(1)
    body = m.group(2)
    fm = {}
    for line in fm_text.strip().split('\n'):
        line = line.strip()
        if ':' in line and not line.startswith('#'):
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip()
            if val.startswith('[') and val.endswith(']'):
                val = [v.strip().strip("'\"") for v in val[1:-1].split(',') if v.strip()]
            fm[key] = val
    return fm, body


def format_frontmatter(fm):
    """格式化 frontmatter 为字符串"""
    lines = ['---']
    for key in ['type', 'name', 'subtype', 'source_count', 'first_incident', 'latest_incident', 'tags']:
        if key in fm:
            val = fm[key]
            if isinstance(val, list):
                lines.append(f"{key}: [{', '.join(val)}]")
            else:
                lines.append(f"{key}: {val}")
    lines.append('---')
    return '\n'.join(lines) + '\n'


def truncate_text(text, max_len=250):
    """截断过长的违规文本"""
    if len(text) <= max_len:
        return text
    # 在句号处截断
    cutoff = text[:max_len].rfind('。')
    if cutoff > max_len * 0.6:
        return text[:cutoff + 1]
    return text[:max_len] + '...'


def build_body(parsed, existing_fm):
    """根据 parsed data 构建新的 entity body"""
    entity_name = parsed['entity'].replace('.md', '')
    concepts_all = set()
    for vc in parsed.get('violation_concepts', []):
        concepts_all.update(vc['concepts'])

    # Determine date from parsed data for incidents
    date_str = parsed.get('date', '')
    if date_str:
        incident_month = date_str[:7]  # YYYY-MM
    else:
        incident_month = existing_fm.get('first_incident', '')

    date_display = date_str if date_str else existing_fm.get('first_incident', '')

    lines = []

    # 基本信息
    lines.append('## 基本信息')
    lines.append('')
    lines.append(f'- **名称**: {entity_name}')
    lines.append(f'- **类型**: 基金管理人')
    if incident_month:
        lines.append(f'- **首次处罚**: {incident_month}')
        lines.append(f'- **最近处罚**: {incident_month}')
    if parsed.get('case_num'):
        lines.append(f'- **字号**: {parsed["case_num"]}')
    lines.append('')

    # 处罚记录
    lines.append('## 处罚记录')
    lines.append('')
    lines.append('### 案件 1')
    lines.append('')
    if parsed.get('case_num'):
        lines.append(f'- **字号**: {parsed["case_num"]}')
    if date_display:
        lines.append(f'- **日期**: {date_display}')
    lines.append(f'- **来源**: {parsed["source"]}')

    # 违规行为
    violations = parsed.get('violations', [])
    violation_concepts = parsed.get('violation_concepts', [])
    if violations:
        lines.append('')
        lines.append('**违规行为**:')
        lines.append('')
        for i, v_text in enumerate(violations):
            clean = re.sub(r'\s+', ' ', v_text).strip()
            # Truncate for readability
            display = truncate_text(clean, 300)
            lines.append(f'{i + 1}. {display}')
            lines.append('')

        # 违规行为对应的概念页
        lines.append('**违规行为对应的概念页**:')
        lines.append('')
        for i, vc in enumerate(violation_concepts):
            clean = re.sub(r'\s+', ' ', vc['text']).strip()
            summary = truncate_text(clean, 100)
            if vc['concepts']:
                links = '、'.join([f'[{c}](/wiki/concepts/{c}.md)' for c in vc['concepts']])
                lines.append(f'{i + 1}. {summary} → {links}')
            else:
                lines.append(f'{i + 1}. {summary} → *待创建概念页*')
            lines.append('')

    # 处罚措施
    penalty = parsed.get('penalty', '')
    if penalty:
        lines.append(f'- **处罚措施**: {penalty}')
        lines.append('')

    # 法规依据
    legal = parsed.get('legal_basis', '')
    if legal:
        lines.append(f'- **法规依据**: {legal}')
        lines.append('')

    # 违规类型汇总
    lines.append('## 违规类型汇总')
    lines.append('')
    if concepts_all:
        for c in sorted(concepts_all):
            lines.append(f'- [{c}](/wiki/concepts/{c}.md)')
    else:
        # 检查是否有 needs_new 的违规
        has_unmatched = any(vc.get('needs_new') for vc in violation_concepts)
        if has_unmatched:
            lines.append('- *待创建概念页*')
        else:
            lines.append('- *暂无归类*')
    lines.append('')

    return '\n'.join(lines)


def main():
    with open(PARSED_DATA) as f:
        data = json.load(f)

    stats = {"updated": 0, "skipped": 0, "no_violations": 0, "no_penalty": 0}
    date_fixes = 0

    for record in data:
        entity_file = record['entity']
        filepath = os.path.join(ENTITY_DIR, entity_file)

        if not os.path.exists(filepath):
            stats["skipped"] += 1
            continue

        with open(filepath, 'r') as f:
            content = f.read()

        existing_fm, _ = parse_frontmatter(content)

        # Update dates in frontmatter
        old_first = existing_fm.get('first_incident', '')
        date_str = record.get('date', '')
        if date_str:
            incident_month = date_str[:7]
            if str(old_first) != str(incident_month):
                date_fixes += 1
            existing_fm['first_incident'] = incident_month
            existing_fm['latest_incident'] = incident_month

        new_body = build_body(record, existing_fm)
        new_content = format_frontmatter(existing_fm) + '\n' + new_body

        with open(filepath, 'w') as f:
            f.write(new_content)

        stats["updated"] += 1
        if not record.get("violations"):
            stats["no_violations"] += 1
        if not record.get("penalty"):
            stats["no_penalty"] += 1

    print("=== 阶段4: Entity 文件更新完成 ===")
    print(f"更新 entity: {stats['updated']} 个")
    print(f"跳过 (文件不存在): {stats['skipped']} 个")
    print(f"日期更正: {date_fixes} 个")
    print(f"无违规行为数据: {stats['no_violations']} 个")
    print(f"无处罚措施数据: {stats['no_penalty']} 个")


if __name__ == "__main__":
    main()
