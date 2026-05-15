#!/usr/bin/env python3
"""
创建/更新 module 页面 (纪律处分、异常经营、失联机构、自律措施).
用法: python3 scripts/wiki/create_modules.py
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import date

BASE_DIR = Path(__file__).parent.parent.parent
RAW_DIR = BASE_DIR / "raw"
MODULES_DIR = BASE_DIR / "wiki" / "modules"


def build_module_page(module_name, entities, description=None):
    sorted_entities = sorted(entities.items(), key=lambda x: len(x[1]), reverse=True)
    total_records = sum(len(recs) for _, recs in sorted_entities)

    content = f"""---
type: module
name: {module_name}
description: {description or f'中国证券投资基金业协会{module_name}记录汇总'}
source_count: {len(entities)}
entity_count: {total_records}
last_updated: {date.today().isoformat()}
---

# {module_name}

本模块收录中国证券投资基金业协会（AMAC）发布的{module_name}决定书。

## 统计概览

- **涉及主体**: {len(entities)} 个
- **记录总数**: {total_records} 条

## 实体列表

"""
    for name, records in sorted_entities[:100]:
        latest = max((r['date'][:7] for r in records if r.get('date')), default='')
        content += f"- **{latest}**: {name} ({len(records)} 条记录)\n"

    if len(sorted_entities) > 100:
        content += f"\n... 还有 {len(sorted_entities) - 100} 个实体\n"

    filepath = MODULES_DIR / f"{module_name}.md"
    filepath.write_text(content, encoding='utf-8')
    return len(entities), total_records


def _clean_html_name(name):
    """与 create_entities.py 相同的清洗逻辑"""
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
    import re
    for p in sorted(prefixes, key=len, reverse=True):
        if normalized.startswith(p):
            name = name[len(p):]
            break
    name = re.sub(r'等\d+家.*', '', name)
    return name.strip()


def main():
    MODULES_DIR.mkdir(parents=True, exist_ok=True)

    # ── 纪律处分 ──
    txt_path = RAW_DIR / 'parsed_txt_results.json'
    if txt_path.exists():
        with open(txt_path, 'r', encoding='utf-8') as f:
            txt_data = json.load(f)
        jlcf = {}
        jlcf.update(txt_data.get('纪律处分_机构', {}))
        jlcf.update(txt_data.get('纪律处分_人员', {}))
        n, r = build_module_page('纪律处分', jlcf, '中国证券投资基金业协会纪律处分记录汇总')
        print(f"纪律处分: {n} entities, {r} records")

    # ── 异常经营 / 失联机构 ──
    html_path = RAW_DIR / 'parsed_html_results.json'
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            html_data = json.load(f)

        for module_type in ['异常经营', '失联机构']:
            entities = defaultdict(list)
            for rec in html_data.get(module_type, []):
                if rec.get('title') in ('异常经营', '失联机构', '自律措施'): continue
                for company in rec.get('companies', []):
                    name = _clean_html_name(company['name'])
                    if not name or len(name) < 4: continue
                    entities[name].append({'date': rec['date'], 'title': rec.get('title', ''), 'source': rec.get('source', '')})
            n, r = build_module_page(module_type, entities)
            print(f"{module_type}: {n} entities, {r} records")

    print("Module 页面已更新")


if __name__ == '__main__':
    main()
