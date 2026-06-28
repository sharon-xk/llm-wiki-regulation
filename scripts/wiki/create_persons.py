#!/usr/bin/env python3
"""
创建人员页 (persons/)
从 parsed_txt_results.json 的「纪律处分_人员」生成人员知识页。

与 create_institutions.py 的关系：
    - create_institutions 处理「纪律处分_机构」→ institutions/
    - 本脚本处理「纪律处分_人员」→ persons/
    - 复用 _parse_subject_info 解析人员信息（姓名/性别/职务/机构）

输入：raw/parsed/parsed_txt_results.json
输出：wiki/persons/*.md
"""
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
RAW_DIR = BASE_DIR / "raw"
PERSONS_DIR = BASE_DIR / "wiki" / "persons"
INSTITUTIONS_DIR = BASE_DIR / "wiki" / "institutions"

# 复用 create_institutions 的解析函数
import importlib.util
_ci_path = BASE_DIR / "scripts" / "wiki" / "create_institutions.py"
_spec = importlib.util.spec_from_file_location("ci", _ci_path)
ci = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ci)
_parse_subject_info = ci._parse_subject_info
safe_filename = ci.safe_filename


def build_person_page(name, records, info):
    """构建人员页面"""
    records.sort(key=lambda x: x['date'], reverse=True)
    first_incident = records[-1]['date'][:7] if records else ''
    latest_incident = records[0]['date'][:7] if records else ''

    # ── frontmatter ──
    fm_parts = [
        "type: person",
        f"name: {name}",
    ]
    if info.get('gender'): fm_parts.append(f"gender: {info['gender']}")
    if info.get('position'): fm_parts.append(f"position: {info['position']}")
    if info.get('org'): fm_parts.append(f"org: {info['org']}")
    fm_parts += [
        "source: AMAC",
        f"source_count: {len(records)}",
        f"first_incident: {first_incident}",
        f"latest_incident: {latest_incident}",
        "tags: [纪律处分]",
    ]
    fm = "---\n" + "\n".join(fm_parts) + "\n---\n"

    # ── 基本信息 ──
    body = f"## 基本信息\n\n- **姓名**: {name}\n"
    if info.get('gender'): body += f"- **性别**: {info['gender']}\n"
    if info.get('birth_date'): body += f"- **出生**: {info['birth_date']}\n"
    if info.get('position'):
        body += f"- **职务**: {info['position']}"
        if info.get('org'):
            # 尝试链接到机构页
            org_file = INSTITUTIONS_DIR / f"{safe_filename(info['org'])}.md"
            if org_file.exists():
                body += f" @ [{info['org']}](../institutions/{safe_filename(info['org'])}.md)"
            else:
                body += f" @ {info['org']}"
        body += "\n"
    body += f"- **首次处罚**: {first_incident}\n"
    body += f"- **最近处罚**: {latest_incident}\n"

    # ── 处罚记录 ──
    body += "\n## 处罚记录\n"
    for i, rec in enumerate(records):
        body += f"\n### 案件 {i+1}\n\n"
        if rec.get('case_num'): body += f"- **字号**: {rec['case_num']}\n"
        body += f"- **日期**: {rec['date']}\n"
        body += f"- **来源**: {rec['source']}\n"

        violations = rec.get('violations', [])
        if violations:
            body += "\n**违规行为**:\n\n"
            for j, v_text in enumerate(violations):
                clean = re.sub(r'\s+', ' ', v_text).strip()
                body += f"{j+1}. {clean}\n"
            body += "\n"

        body += "**违规行为对应的违规类型**:\n\n*待映射*\n\n"

        measures = rec.get('measures', [])
        if measures:
            body += f"- **处罚措施**: {'; '.join(measures)}\n"

        if rec.get('legal_basis'):
            body += f"- **法规依据**: {rec['legal_basis']}\n"

    # ── 违规类型汇总 ──
    body += "\n## 违规类型汇总\n\n"
    all_violations = []
    for rec in records:
        all_violations.extend(rec.get('violations', []))
    if all_violations:
        body += "*待映射*\n"
    else:
        body += "- *暂无*\n"

    return fm + "\n" + body


def main():
    PERSONS_DIR.mkdir(parents=True, exist_ok=True)

    txt_path = RAW_DIR / 'parsed' / 'parsed_txt_results.json'
    if not txt_path.exists():
        print(f"数据文件不存在: {txt_path}")
        return

    with open(txt_path, 'r', encoding='utf-8') as f:
        txt_data = json.load(f)

    persons = txt_data.get('纪律处分_人员', {})
    if not persons:
        print("纪律处分_人员: 无数据（人员数据尚未解析）")
        return

    created = 0
    for name, records in persons.items():
        info = _parse_subject_info(name)
        clean_name = info['name'] or ci.clean_subject(name)
        if not clean_name:
            continue
        filepath = PERSONS_DIR / f"{safe_filename(clean_name)}.md"
        filepath.write_text(build_person_page(clean_name, records, info), encoding='utf-8')
        created += 1

    print(f"纪律处分_人员: 创建 {created} 个人员页")
    print(f"总计 persons 文件: {len(list(PERSONS_DIR.glob('*.md'))) - (1 if (PERSONS_DIR / '_规范.md').exists() else 0)}")


if __name__ == "__main__":
    main()
