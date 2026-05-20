#!/usr/bin/env python3
"""
创建 entity 页面, 合并纪律处分(parsed_txt) 和 异常经营/失联机构(parsed_html) 两个数据源.
用法: python3 scripts/wiki/create_entities.py
"""
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import date

BASE_DIR = Path(__file__).parent.parent.parent
RAW_DIR = BASE_DIR / "raw"
WIKI_DIR = BASE_DIR / "wiki"
ENTITIES_DIR = WIKI_DIR / "entities"
MODULES_DIR = WIKI_DIR / "modules"


# ── helpers ──────────────────────────────────────────────────────────

def safe_filename(name):
    safe = re.sub(r'[\\/:*?"<>|;,\'"()（）【】〈〈〉、、\s\-—]', '', name)
    return safe[:40]


def clean_subject(subject):
    """清理当事人名称, 提取核心标识"""
    info = _parse_subject_info(subject)
    return info['name']


def _parse_subject_info(subject):
    info = {'name': subject, 'gender': '', 'birth_date': '', 'position': '', 'org': '', 'abbreviation': ''}
    abbrev_match = re.search(r'《([^》]+)》', subject)
    if abbrev_match:
        info['abbreviation'] = abbrev_match.group(1)

    clean = re.sub(r'《[^》]*》', '', subject)
    person_match = re.match(r'^([^\s，,]+)[，,]\s*[男女]', clean)

    if person_match:
        info['name'] = person_match.group(1)
        info['gender'] = '男' if '男' in clean else '女'
        birth = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月?', clean)
        if birth:
            info['birth_date'] = f"{birth.group(1)}年{birth.group(2)}月"
        for kw in ['时任', '现任', '登记为', '曾任']:
            if kw in clean:
                idx = clean.find(kw)
                pos_str = clean[idx:]
                end_match = re.search(r'[，,]', pos_str)
                if end_match:
                    pos_str = pos_str[:end_match.start()]
                info['position'] = pos_str
                rest = clean[idx + len(kw):]
                rest = re.sub(r'[^公司管理投资]*((?:有限公司?|基金管理|投资中心|合伙企业).*)', r'\1', rest)
                end_match = re.search(r'[，,\s]', rest)
                if end_match:
                    org = rest[:end_match.start()].strip()
                    if org:
                        info['org'] = org
                break
    else:
        clean2 = subject
        clean2 = clean2.replace('〈', '《').replace('〉', '》')
        clean2 = clean2.replace('【', '《').replace('】', '》')
        clean2 = re.sub(r'《[^》]*》', '', clean2)
        clean2 = re.sub(r'（[^）]*）', '', clean2)
        clean2 = re.sub(r'《[^》]*', '', clean2)
        clean2 = re.sub(r'[^《]*》', '', clean2)
        clean2 = re.sub(r'\s+', '', clean2)
        parts = re.split(r'[，,]\s*', clean2)
        info['name'] = parts[0] if parts else clean2

    return info


def clean_company_name(name):
    """清洗 HTML 解析出的公司名"""
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


def dedup_records(records):
    seen = set()
    unique = []
    for rec in sorted(records, key=lambda r: r['date'], reverse=True):
        key = (rec['date'], rec.get('title', '')[:60])
        if key not in seen:
            seen.add(key)
            unique.append(rec)
    return unique


def is_index_record(rec):
    return rec.get('title', '') in ('异常经营', '失联机构', '自律措施')


# ── entity page builders ─────────────────────────────────────────────

def build_jlcf_entity(name, records, subtype, subject_info=None):
    """构建纪律处分 entity 页面（统一模版）"""
    records.sort(key=lambda x: x['date'], reverse=True)
    first_incident = records[-1]['date'][:7] if records else ''
    latest_incident = records[0]['date'][:7] if records else ''

    info = subject_info or {}
    fm_parts = [
        "type: entity", f"name: {name}", f"subtype: {subtype}",
        f"source_count: {len(records)}",
        f"first_incident: {first_incident}", f"latest_incident: {latest_incident}",
    ]
    if info.get('abbreviation'): fm_parts.append(f"short_name: {info['abbreviation']}")
    fm_parts.append("tags: [纪律处分]")
    fm = "---\n" + "\n".join(fm_parts) + "\n---\n"

    # ── 基本信息 ──
    body = f"## 基本信息\n\n- **名称**: {name}\n"
    if info.get('abbreviation'): body += f"- **简称**: {info['abbreviation']}\n"
    body += f"- **类型**: {subtype}\n"
    if first_incident:
        body += f"- **首次处罚**: {first_incident}\n"
        body += f"- **最近处罚**: {latest_incident}\n"

    # ── 处罚记录 ──
    body += "\n## 处罚记录\n"
    for i, rec in enumerate(records):
        body += f"\n### 案件 {i+1}\n\n"
        if rec.get('case_num'): body += f"- **字号**: {rec['case_num']}\n"
        body += f"- **日期**: {rec['date']}\n"
        body += f"- **来源**: {rec['source']}\n"

        # 违规行为：完整编号列表
        violations = rec.get('violations', [])
        if violations:
            body += "\n**违规行为**:\n\n"
            for j, v_text in enumerate(violations):
                clean = re.sub(r'\s+', ' ', v_text).strip()
                body += f"{j+1}. {clean}\n"
            body += "\n"

        # 违反行为对应的概念页：create 阶段留占位，update 阶段填充
        body += "**违规行为对应的概念页**:\n\n*待映射*\n\n"

        # 处罚措施
        measures = rec.get('measures', [])
        if measures:
            body += f"- **处罚措施**: {'; '.join(measures)}\n"

        # 法规依据
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


def build_html_entity(name, records, module_type):
    """构建异常经营/失联机构 entity 页面"""
    records = dedup_records(records)
    first = records[-1]['date'][:7] if records else ''
    latest = records[0]['date'][:7] if records else ''

    fm = f"""---
type: entity
name: {name}
subtype: 基金管理人
source_count: {len(records)}
first_incident: {first}
latest_incident: {latest}
tags: [{module_type}]
---"""

    body = f"""## 基本信息

- **名称**: {name}
- **类型**: 基金管理人
- **首次记录**: {first}
- **最近记录**: {latest}
- **记录数**: {len(records)}

## 记录列表

"""
    for i, rec in enumerate(records):
        body += f"### 记录 {i+1}\n\n- **日期**: {rec['date']}\n- **标题**: {rec.get('title', '')}\n- **来源**: {rec.get('source', '')}\n\n"
    return fm + "\n" + body


def merge_with_existing(filepath, new_content, new_module_type):
    existing = filepath.read_text(encoding='utf-8')
    fm_match = re.match(r'^---\n(.*?)\n---', existing, re.DOTALL)
    if not fm_match:
        return new_content

    fm_text = fm_match.group(1)
    existing_body = existing[fm_match.end():]
    tags_match = re.search(r'^tags:\s*\[(.+)\]', fm_text, re.MULTILINE)
    existing_tags = []
    if tags_match:
        existing_tags = [t.strip() for t in tags_match.group(1).split(',') if t.strip()]

    if new_module_type in existing_tags:
        if len(existing_tags) == 1:
            return new_content
        body_parts = existing_body.split('## 记录列表\n\n', 1)
        base_body = body_parts[0].rstrip() if body_parts else existing_body
        new_records_match = re.search(r'## 记录列表\n\n', new_content)
        if new_records_match:
            new_section = new_content[new_records_match.start():]
            all_tags = sorted(set(existing_tags), key=lambda t: ('纪律处分', '异常经营', '失联机构').index(t) if t in ('纪律处分', '异常经营', '失联机构') else 99)
            new_fm = re.sub(r'^tags:\s*\[.+\]', f'tags: [{", ".join(all_tags)}]', fm_text, flags=re.MULTILINE)
            return f"---\n{new_fm}\n---{base_body}\n\n{new_section}"
        return existing

    existing_tags.append(new_module_type)
    all_tags = sorted(set(existing_tags), key=lambda t: ('纪律处分', '异常经营', '失联机构').index(t) if t in ('纪律处分', '异常经营', '失联机构') else 99)
    new_fm = re.sub(r'^tags:\s*\[.+\]', f'tags: [{", ".join(all_tags)}]', fm_text, flags=re.MULTILINE)
    new_records_match = re.search(r'## 记录列表\n\n', new_content)
    if new_records_match:
        new_section = new_content[new_records_match.start():]
        return f"---\n{new_fm}\n---{existing_body.rstrip()}\n\n{new_section}"
    return f"---\n{new_fm}\n---{existing_body}"


# ── main ─────────────────────────────────────────────────────────────

def main():
    ENTITIES_DIR.mkdir(parents=True, exist_ok=True)

    # ─── 1. 纪律处分 (parsed_txt_results.json) ───
    txt_path = RAW_DIR / 'parsed_txt_results.json'
    if txt_path.exists():
        with open(txt_path, 'r', encoding='utf-8') as f:
            txt_data = json.load(f)

        created = 0
        for name, records in txt_data.get('纪律处分_机构', {}).items():
            clean_name = clean_subject(name)
            if not clean_name: continue
            info = _parse_subject_info(name)
            filepath = ENTITIES_DIR / f"{safe_filename(clean_name)}.md"
            filepath.write_text(build_jlcf_entity(clean_name, records, '基金管理人', info), encoding='utf-8')
            created += 1

        for name, records in txt_data.get('纪律处分_人员', {}).items():
            clean_name = clean_subject(name)
            if not clean_name: continue
            info = _parse_subject_info(name)
            filepath = ENTITIES_DIR / f"{safe_filename(clean_name)}.md"
            filepath.write_text(build_jlcf_entity(clean_name, records, '个人', info), encoding='utf-8')
            created += 1
        print(f"纪律处分 entity: {created}")

    # ─── 2. 异常经营 / 失联机构 (parsed_html_results.json) ───
    html_path = RAW_DIR / 'parsed_html_results.json'
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            html_data = json.load(f)

        html_entities = defaultdict(list)
        for module_type in ['异常经营', '失联机构']:
            for rec in html_data.get(module_type, []):
                if is_index_record(rec): continue
                for company in rec.get('companies', []):
                    name = clean_company_name(company['name'])
                    if not name or len(name) < 4: continue
                    html_entities[name].append({'date': rec['date'], 'title': rec.get('title', ''), 'source': rec.get('source', ''), 'text': rec.get('text', ''), 'module': module_type})

        created, merged = 0, 0
        for name, records in html_entities.items():
            module_type = records[0]['module']
            content = build_html_entity(name, records, module_type)
            filepath = ENTITIES_DIR / f"{safe_filename(name)}.md"
            if filepath.exists():
                merged_content = merge_with_existing(filepath, content, module_type)
                filepath.write_text(merged_content, encoding='utf-8')
                merged += 1
            else:
                filepath.write_text(content, encoding='utf-8')
                created += 1
        print(f"HTML entity: 新建 {created}, 合并 {merged}")

    print(f"总计 entity 文件: {len(list(ENTITIES_DIR.glob('*.md')))}")


if __name__ == '__main__':
    main()
