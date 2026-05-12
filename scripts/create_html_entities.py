#!/usr/bin/env python3
"""
为异常经营和失联机构创建 entity 页面。

数据源: raw/parsed_html_results.json
复用: create_wiki.py 的 safe_filename() 和 entity/module/index/log 更新模式

处理流程:
1. 读取 parsed_html_results.json
2. 清洗公司名（移除 "关于注销"、"关于请" 等前缀）
3. 过滤掉索引页记录
4. 按公司名合并、去重
5. 创建 entity 页面（处理与纪律处分 entity 的合并）
6. 更新 module 页、index.md、log.md
"""

import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import date


def safe_filename(name):
    """生成安全的文件名 — 与 create_wiki.py 相同逻辑"""
    safe = re.sub(r'[\\/:*?"<>|;,\'"()（）【】〈〈〉、、\s\-—]', '', name)
    return safe[:40]


def clean_company_name(name):
    """清洗 HTML 解析出的公司名，移除前缀和后缀杂物"""
    # 先统一引号字符（中文引号 → ASCII），避免匹配遗漏
    normalized = name.replace('“', '"').replace('”', '"')

    prefixes = [
        # 协会公告类（含引号变体："协会" 或 协会）
        '中国证券投资基金业协会（以下简称"协会"）已公告',
        '中国证券投资基金业协会（以下简称"协会"）已将',
        '中国证券投资基金业协会（以下简称"协会"）在自律核查工作中发现',
        '中国证券投资基金业协会（以下简称协会）已公告',
        '中国证券投资基金业协会（以下简称协会）已将',
        # 关于类
        '关于注销',
        '关于请',
        # 协会核查类
        '协会在日常工作中发现',
        '协会在处理投诉案件中发现',
        '协会的自律核查工作涉及到',
        # 其他
        '无法与',
        '现有',
        '协会已公告',
    ]
    for p in sorted(prefixes, key=len, reverse=True):
        if normalized.startswith(p):
            name = name[len(p):]
            break

    # 移除 "等N家..." 后缀
    name = re.sub(r'等\d+家.*', '', name)
    return name.strip()


def is_index_record(rec):
    """判断是否为索引页记录（title 为模块名本身，非具体公告）"""
    title = rec.get('title', '')
    return title in ('异常经营', '失联机构', '自律措施')


def dedup_records(records):
    """按 (date, title[:60]) 去重，保留第一次出现"""
    seen = set()
    unique = []
    for rec in sorted(records, key=lambda r: r['date'], reverse=True):
        key = (rec['date'], rec.get('title', '')[:60])
        if key not in seen:
            seen.add(key)
            unique.append(rec)
    return unique


def create_entity_content(name, records, module_type):
    """为异常经营/失联机构创建 entity 页面内容"""
    records = dedup_records(records)

    first_incident = records[-1]['date'][:7] if records else ''
    latest_incident = records[0]['date'][:7] if records else ''

    fm_lines = [
        "type: entity",
        f"name: {name}",
        "subtype: 基金管理人",
        f"source_count: {len(records)}",
        f"first_incident: {first_incident}",
        f"latest_incident: {latest_incident}",
        f"tags: [{module_type}]",
    ]
    fm = "---\n" + "\n".join(fm_lines) + "\n---\n"

    body = f"""## 基本信息

- **名称**: {name}
- **类型**: 基金管理人
- **首次记录**: {first_incident}
- **最近记录**: {latest_incident}
- **记录数**: {len(records)}

## 记录列表

"""
    for i, rec in enumerate(records):
        body += f"### 记录 {i+1}\n\n"
        body += f"- **日期**: {rec['date']}\n"
        body += f"- **标题**: {rec.get('title', '')}\n"
        body += f"- **来源**: {rec.get('source', '')}\n\n"

    return fm + body


def merge_with_existing(filepath, new_content, new_module_type):
    """处理 entity 文件已存在的情况。

    - 若已有文件只含 new_module_type 一种 tag → 重复运行，直接覆盖（修复重复数据）
    - 若已有文件含其他模块 tag（如纪律处分）→ 合并 tags，追加新模块记录
    """
    existing = filepath.read_text(encoding='utf-8')

    fm_match = re.match(r'^---\n(.*?)\n---', existing, re.DOTALL)
    if not fm_match:
        return new_content

    fm_text = fm_match.group(1)
    existing_body = existing[fm_match.end():]

    tags_match = re.search(r'^tags:\s*\[(.+)\]', fm_text, re.MULTILINE)
    existing_tags = []
    if tags_match:
        tag_str = tags_match.group(1)
        existing_tags = [t.strip() for t in tag_str.split(',') if t.strip()]

    if new_module_type in existing_tags:
        if len(existing_tags) == 1:
            # Only this module type — safe to overwrite (fixes duplicates from re-run)
            return new_content
        else:
            # Has other module types too — merge: replace only this module's section
            # Remove old 记录列表 section belonging to this module, then append new
            # Simple approach: keep the body before first "## 记录列表", append new
            body_parts = existing_body.split('## 记录列表\n\n', 1)
            base_body = body_parts[0].rstrip() if body_parts else existing_body
            new_records_match = re.search(r'## 记录列表\n\n', new_content)
            if new_records_match:
                new_section = new_content[new_records_match.start():]
                # Also update tags
                all_tags = sorted(set(existing_tags), key=lambda t: ('纪律处分', '异常经营', '失联机构').index(t) if t in ('纪律处分', '异常经营', '失联机构') else 99)
                new_fm = re.sub(
                    r'^tags:\s*\[.+\]',
                    f'tags: [{", ".join(all_tags)}]',
                    fm_text,
                    flags=re.MULTILINE
                )
                return f"---\n{new_fm}\n---{base_body}\n\n{new_section}"
            return existing

    # Different module — merge
    existing_tags.append(new_module_type)
    all_tags = sorted(set(existing_tags), key=lambda t: ('纪律处分', '异常经营', '失联机构').index(t) if t in ('纪律处分', '异常经营', '失联机构') else 99)
    new_fm = re.sub(
        r'^tags:\s*\[.+\]',
        f'tags: [{", ".join(all_tags)}]',
        fm_text,
        flags=re.MULTILINE
    )

    new_records_match = re.search(r'## 记录列表\n\n', new_content)
    if new_records_match:
        new_section = new_content[new_records_match.start():]
        combined = f"---\n{new_fm}\n---{existing_body.rstrip()}\n\n"
        combined += new_section
        return combined

    return f"---\n{new_fm}\n---{existing_body}"


def build_entities_from_html(html_data, module_type):
    """从 HTML 解析数据构建 entity 字典"""
    entities = defaultdict(list)

    for rec in html_data.get(module_type, []):
        if is_index_record(rec):
            continue

        for company in rec.get('companies', []):
            raw_name = company['name']
            clean = clean_company_name(raw_name)
            if not clean or len(clean) < 4:
                continue
            entities[clean].append({
                'date': rec['date'],
                'title': rec.get('title', ''),
                'source': rec.get('source', ''),
                'text': rec.get('text', ''),
            })

    return entities


def update_module_page(module_name, entities, module_key):
    """更新 module 页面 — 对齐 create_wiki.py 格式"""
    modules_dir = Path('/Users/sharon/ai-project/llm-wiki-regulation/wiki/modules')
    modules_dir.mkdir(parents=True, exist_ok=True)

    sorted_entities = sorted(entities.items(), key=lambda x: len(x[1]), reverse=True)
    total_records = sum(len(recs) for _, recs in sorted_entities)

    content = f"""---
type: module
name: {module_name}
description: 中国证券投资基金业协会{module_name}记录汇总
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
        latest = records[0]['date'][:7] if records else ''
        content += f"- **{latest}**: {name} ({len(records)} 条记录)\n"

    if len(sorted_entities) > 100:
        content += f"\n... 还有 {len(sorted_entities) - 100} 个实体\n"

    filepath = modules_dir / f"{module_name}.md"
    filepath.write_text(content, encoding='utf-8')
    return len(entities), total_records


def main():
    base_dir = Path('/Users/sharon/ai-project/llm-wiki-regulation')
    raw_dir = base_dir / 'raw'
    wiki_dir = base_dir / 'wiki'
    entities_dir = wiki_dir / 'entities'
    entities_dir.mkdir(parents=True, exist_ok=True)

    # 1. 加载数据
    with open(raw_dir / 'parsed_html_results.json', 'r', encoding='utf-8') as f:
        html_data = json.load(f)

    # 2. 构建 entity 字典
    ycjy_entities = build_entities_from_html(html_data, '异常经营')
    sljg_entities = build_entities_from_html(html_data, '失联机构')

    print(f"异常经营: {len(ycjy_entities)} entities")
    print(f"失联机构: {len(sljg_entities)} entities")

    # 3. 创建 entity 页面
    created = 0
    merged = 0

    for module_type, entities in [('异常经营', ycjy_entities), ('失联机构', sljg_entities)]:
        for name, records in entities.items():
            new_content = create_entity_content(name, records, module_type)
            filepath = entities_dir / f"{safe_filename(name)}.md"

            if filepath.exists():
                # 合并到已有 entity（来自纪律处分等）
                merged_content = merge_with_existing(filepath, new_content, module_type)
                filepath.write_text(merged_content, encoding='utf-8')
                merged += 1
            else:
                filepath.write_text(new_content, encoding='utf-8')
                created += 1

    print(f"\n新建 entity: {created}")
    print(f"合并到已有 entity: {merged}")

    # 4. 更新 module 页面
    ycjy_count, ycjy_records = update_module_page('异常经营', ycjy_entities, 'ycjy')
    sljg_count, sljg_records = update_module_page('失联机构', sljg_entities, 'sljg')
    print(f"\n模块页已更新: 异常经营({ycjy_count} entities), 失联机构({sljg_count} entities)")

    # 5. 更新 index.md
    entity_files = sorted(entities_dir.glob('*.md'))
    index_content = f"""# 基金业协会处罚知识库

> 本知识库收集整理中国证券投资基金业协会（AMAC）自律管理处罚信息，供查询和分析。

---

## 实体 (entities)

- 共 {len(entity_files)} 个实体

"""
    # 列出最近更新的实体
    for ef in entity_files[-20:]:
        name = ef.stem
        index_content += f"- [{name}](wiki/entities/{name}.md)\n"

    index_content += f"""
... 还有 {len(entity_files) - 20} 个实体

## 模块 (modules)

- [纪律处分](wiki/modules/纪律处分.md) — 纪律处分-机构 + 纪律处分-人员
- [异常经营](wiki/modules/异常经营.md) — {ycjy_count} 机构, {ycjy_records} 条记录
- [失联机构](wiki/modules/失联机构.md) — {sljg_count} 机构, {sljg_records} 条记录
- [自律措施](wiki/modules/自律措施.md) — 自律措施

## 概念 (concepts)

- [信息披露违规](wiki/concepts/信息披露违规.md)
- [关联交易违规](wiki/concepts/关联交易违规.md)
- [利益输送](wiki/concepts/利益输送.md)
- [承诺保本收益](wiki/concepts/承诺保本收益.md)
- [投资者适当性违规](wiki/concepts/投资者适当性违规.md)
- [挪用基金财产](wiki/concepts/挪用基金财产.md)
- [未尽谨慎勤勉义务](wiki/concepts/未尽谨慎勤勉义务.md)
- [未按规定登记备案](wiki/concepts/未按规定登记备案.md)
- [虚假登记备案](wiki/concepts/虚假登记备案.md)
- [违规募集](wiki/concepts/违规募集.md)

## 分析 (analysis)

- [分析_年度趋势](wiki/analysis/分析_年度趋势.md)
- [分析_最新处罚](wiki/analysis/分析_最新处罚.md)

---
*最后更新：{date.today().isoformat()}*
"""
    (base_dir / 'index.md').write_text(index_content, encoding='utf-8')
    print(f"index.md 已更新 (total: {len(entity_files)} entities)")

    # 6. 更新 log.md
    log_entry = f"""
## [{date.today().isoformat()}] ingest | 异常经营 + 失联机构 entity 创建

- 异常经营: {ycjy_count} entities, {ycjy_records} 条记录（新建 {created} 个 entity 页）
- 失联机构: {sljg_count} entities, {sljg_records} 条记录
- 合并到已有纪律处分 entity: {merged} 个
- 数据源: parsed_html_results.json
- 脚本: scripts/create_html_entities.py
"""
    log_file = base_dir / 'log.md'
    existing_log = log_file.read_text(encoding='utf-8') if log_file.exists() else "# 操作日志\n"
    log_file.write_text(existing_log.rstrip() + log_entry + "\n", encoding='utf-8')
    print(f"log.md 已更新")

    print("\n===== 完成 =====")
    print(f"合计 entity 文件: {len(entity_files)}")


if __name__ == '__main__':
    main()
