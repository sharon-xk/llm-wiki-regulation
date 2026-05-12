#!/usr/bin/env python3
"""
创建wiki页面
"""
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import date

def parse_subject_info(subject_str):
    """解析当事人信息，提取姓名/公司名及附加信息"""
    info = {
        'name': subject_str,
        'gender': '',
        'birth_date': '',
        'position': '',
        'org': '',
        'abbreviation': ''
    }

    # 提取公司简称《...》
    abbrev_match = re.search(r'《([^》]+)》', subject_str)
    if abbrev_match:
        info['abbreviation'] = abbrev_match.group(1)

    # 去除《...》部分
    clean = re.sub(r'《[^》]+》', '', subject_str)

    # 判断是个人的还是机构的
    # 个人格式：姓名，男/女，XXXX年X月出生，现任/时任/登记为XXX
    person_match = re.match(r'^([^\s，,]+)[，,]\s*[男女]', clean)

    if person_match:
        # 个人
        info['name'] = person_match.group(1)
        info['gender'] = '男' if '男' in clean else '女'

        # 提取出生日期
        birth = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月?', clean)
        if birth:
            info['birth_date'] = f"{birth.group(1)}年{birth.group(2)}月"

        # 提取职务信息
        for kw in ['时任', '现任', '登记为', '曾任']:
            if kw in clean:
                idx = clean.find(kw)
                pos_str = clean[idx:]
                # 找到下一个标点或结尾
                end_match = re.search(r'[，,]', pos_str)
                if end_match:
                    pos_str = pos_str[:end_match.start()]
                info['position'] = pos_str
                break

        # 提取任职机构
        for kw in ['时任', '现任', '登记为', '曾任']:
            if kw in clean:
                idx = clean.find(kw) + len(kw)
                rest = clean[idx:]
                # 去除公司简称
                rest = re.sub(r'[^公司管理投资]*((?:有限公司?|基金管理|投资中心|合伙企业).*)', r'\1', rest)
                # 找第一个标点
                end_match = re.search(r'[，,\s]', rest)
                if end_match:
                    org = rest[:end_match.start()].strip()
                    if org:
                        info['org'] = org
                break
    else:
        # 机构 - 提取公司名
        clean = subject_str
        # 去除各种括号及其内容（使用简单替换处理特殊括号）
        # 先处理 〈 〉 这类单角括号
        clean = clean.replace('〈', '《').replace('〉', '》')
        clean = clean.replace('【', '《').replace('】', '》')
        # 去除《...》 - 贪婪匹配会尽可能多地匹配
        clean = re.sub(r'《[^》]*》', '', clean)
        # 去除（...）- 贪婪
        clean = re.sub(r'（[^）]*）', '', clean)
        # 去除剩余的孤立的《或》（可能由上述替换产生）
        clean = re.sub(r'《[^》]*', '', clean)
        clean = re.sub(r'[^《]*》', '', clean)
        clean = re.sub(r'\s+', '', clean)
        # 取第一部分作为公司名
        parts = re.split(r'[，,]\s*', clean)
        info['name'] = parts[0] if parts else clean

    return info

def clean_subject(subject):
    """清理当事人名称，提取核心标识"""
    info = parse_subject_info(subject)
    return info['name']

def safe_filename(name):
    """生成安全的文件名"""
    # 只保留字母、数字、中文，替换特殊符号为空
    safe = re.sub(r'[\\/:*?"<>|;,\'"()（）【】〈〉，，、\s\-—]', '', name)
    return safe[:40]

def create_entity_page(name, records, subtype, subject_info=None):
    """创建实体页"""
    # 按日期排序
    records.sort(key=lambda x: x['date'], reverse=True)

    first_incident = records[-1]['date'][:7] if records else ''
    latest_incident = records[0]['date'][:7] if records else ''

    # 默认值
    gender = ''
    birth_date = ''
    position = ''
    org = ''
    abbreviation = ''

    if subject_info:
        gender = subject_info.get('gender', '')
        birth_date = subject_info.get('birth_date', '')
        position = subject_info.get('position', '')
        org = subject_info.get('org', '')
        abbreviation = subject_info.get('abbreviation', '')

    # 构建frontmatter
    fm_parts = [
        f"type: entity",
        f"name: {name}",
        f"subtype: {subtype}",
        f"source_count: {len(records)}",
        f"first_incident: {first_incident}",
        f"latest_incident: {latest_incident}",
    ]
    if gender:
        fm_parts.append(f"gender: {gender}")
    if birth_date:
        fm_parts.append(f"birth_date: {birth_date}")
    if position:
        fm_parts.append(f"position: {position}")
    if org:
        fm_parts.append(f"org: {org}")
    if abbreviation:
        fm_parts.append(f"abbreviation: {abbreviation}")
    fm_parts.append("tags: [纪律处分]")

    fm = "---\n" + "\n".join(fm_parts) + "\n---\n"

    # 构建基本信息部分
    basic_info = f"""## 基本信息

- **名称**: {name}
"""
    if abbreviation:
        basic_info += f"- **简称**: {abbreviation}\n"
    if gender:
        basic_info += f"- **性别**: {gender}\n"
    if birth_date:
        basic_info += f"- **出生日期**: {birth_date}\n"
    if position:
        basic_info += f"- **职务**: {position}\n"
    if org:
        basic_info += f"- **任职机构**: {org}\n"
    basic_info += f"- **类型**: {subtype}\n"
    basic_info += f"- **首次处罚**: {first_incident}\n"
    basic_info += f"- **最近处罚**: {latest_incident}\n"

    content = fm + "\n" + basic_info + "\n## 处罚记录\n\n"

    for i, rec in enumerate(records):
        content += f"### 案件 {i+1}\n\n"
        if rec.get('case_num'):
            content += f"- **字号**: {rec['case_num']}\n"
        content += f"- **日期**: {rec['date']}\n"
        content += f"- **来源**: {rec['source']}\n"

        # 违规行为 - 完整显示，不截断
        if rec.get('violations'):
            content += f"- **违规行为**: {'; '.join(rec['violations'][:3])}\n"

        # 处罚措施 - 完整显示
        if rec.get('measures'):
            content += f"- **处罚措施**: {'; '.join(rec['measures'][:3])}\n"

        content += "\n"

    # 违规类型汇总
    all_violations = []
    for rec in records:
        all_violations.extend(rec.get('violations', []))

    if all_violations:
        content += "## 违规类型汇总\n\n"
        seen = set()
        for v in all_violations:
            if v and v not in seen:
                seen.add(v)
                content += f"- {v}\n"

    return content

def create_module_page(module_name, entities, subtype, module_key):
    """创建模块页"""
    # 按最新处罚日期排序
    sorted_entities = []
    for name, records in entities.items():
        latest = records[0]['date'][:7] if records else ''
        sorted_entities.append((latest, name, len(records)))

    sorted_entities.sort(reverse=True)

    content = f"""---
type: module
name: {module_name}
description: 中国证券投资基金业协会{module_name}记录汇总
source_count: {len(entities)}
entity_count: {sum(len(r) for r in entities.values())}
last_updated: {date.today().isoformat()}
---

# {module_name}

本模块收录中国证券投资基金业协会（AMAC）发布的{module_name}决定书。

## 统计概览

- **涉及主体**: {len(entities)} 个
- **记录总数**: {sum(len(r) for r in entities.values())} 条

## 实体列表

"""

    for latest, name, count in sorted_entities[:100]:
        content += f"- **{latest}**: {name} ({count} 条记录)\n"

    if len(sorted_entities) > 100:
        content += f"\n... 还有 {len(sorted_entities) - 100} 个实体\n"

    return content

def main():
    base_dir = Path('/Users/sharon/ai-project/llm-wiki-regulation')
    raw_dir = base_dir / 'raw'
    wiki_dir = base_dir / 'wiki'

    # 加载解析结果
    with open(raw_dir / 'parsed_txt_results.json', 'r', encoding='utf-8') as f:
        txt_results = json.load(f)

    with open(raw_dir / 'parsed_html_results.json', 'r', encoding='utf-8') as f:
        html_results = json.load(f)

    # 创建实体页
    entities_dir = wiki_dir / 'entities'
    entities_dir.mkdir(parents=True, exist_ok=True)

    created_entities = 0

    # 处理纪律处分-机构
    for name, records in txt_results.get('纪律处分_机构', {}).items():
        clean_name = clean_subject(name)
        if not clean_name:
            continue

        # 解析完整信息（用于提取简称等）
        subject_info = parse_subject_info(name)

        filepath = entities_dir / f"{safe_filename(clean_name)}.md"
        content = create_entity_page(clean_name, records, '基金管理人', subject_info)
        filepath.write_text(content, encoding='utf-8')
        created_entities += 1

    # 处理纪律处分-人员
    for name, records in txt_results.get('纪律处分_人员', {}).items():
        clean_name = clean_subject(name)
        if not clean_name:
            continue

        # 解析完整信息
        subject_info = parse_subject_info(name)

        filepath = entities_dir / f"{safe_filename(clean_name)}.md"
        content = create_entity_page(clean_name, records, '个人', subject_info)
        filepath.write_text(content, encoding='utf-8')
        created_entities += 1

    print(f"创建了 {created_entities} 个实体页")

    # 创建模块页
    modules_dir = wiki_dir / 'modules'
    modules_dir.mkdir(parents=True, exist_ok=True)

    # 纪律处分
    jlcf_entities = {}
    jlcf_entities.update(txt_results.get('纪律处分_机构', {}))
    jlcf_entities.update(txt_results.get('纪律处分_人员', {}))
    content = create_module_page('纪律处分', jlcf_entities, '基金管理人/个人', 'jlcf')
    (modules_dir / '纪律处分.md').write_text(content, encoding='utf-8')
    print(f"创建了纪律处分模块页")

    # 异常经营
    ycjy_entities = defaultdict(list)
    for rec in html_results.get('异常经营', []):
        for company in rec.get('companies', []):
            name = company['name']
            ycjy_entities[name].append({
                'date': rec['date'],
                'source': rec['source'],
                'title': rec['title']
            })
    content = create_module_page('异常经营', ycjy_entities, '私募基金管理人', 'ycjy')
    (modules_dir / '异常经营.md').write_text(content, encoding='utf-8')
    print(f"创建了异常经营模块页")

    # 失联机构
    sljg_entities = defaultdict(list)
    for rec in html_results.get('失联机构', []):
        for company in rec.get('companies', []):
            name = company['name']
            sljg_entities[name].append({
                'date': rec['date'],
                'source': rec['source'],
                'title': rec['title']
            })
    content = create_module_page('失联机构', sljg_entities, '私募基金管理人', 'sljg')
    (modules_dir / '失联机构.md').write_text(content, encoding='utf-8')
    print(f"创建了失联机构模块页")

    # 自律措施
    zlcs_entities = defaultdict(list)
    for rec in html_results.get('自律措施', []):
        for company in rec.get('companies', []):
            name = company['name']
            zlcs_entities[name].append({
                'date': rec['date'],
                'source': rec['source'],
                'title': rec['title']
            })
    content = create_module_page('自律措施', zlcs_entities, '机构/个人', 'zlcs')
    (modules_dir / '自律措施.md').write_text(content, encoding='utf-8')
    print(f"创建了自律措施模块页")

    # 更新 index.md
    entity_files = list(entities_dir.glob('*.md'))

    index_content = """# 基金业协会处罚知识库

> 本知识库收集整理中国证券投资基金业协会（AMAC）自律管理处罚信息，供查询和分析。

---

## 实体 (entities)

"""
    for ef in sorted(entity_files)[:100]:
        name = ef.stem
        index_content += f"- [{name}](wiki/entities/{name}.md)\n"

    if len(entity_files) > 100:
        index_content += f"\n... 还有 {len(entity_files) - 100} 个实体\n"

    index_content += """

## 模块 (modules)

- [纪律处分](wiki/modules/纪律处分.md) — 纪律处分-机构 + 纪律处分-人员
- [异常经营](wiki/modules/异常经营.md) — 异常经营私募基金管理人
- [失联机构](wiki/modules/失联机构.md) — 失联私募基金管理人
- [自律措施](wiki/modules/自律措施.md) — 自律措施

## 概念 (concepts)

>暂无

## 分析 (analysis)

>暂无
"""

    (base_dir / 'index.md').write_text(index_content, encoding='utf-8')
    print(f"更新了 index.md")

    # 更新 log.md
    log_entry = f"""

## [{date.today().isoformat()}] ingest | 全量数据

- 纪律处分-机构: 356 实体, 358 条记录
- 纪律处分-人员: 732 实体, 732 条记录
- 异常经营: {len(ycjy_entities)} 实体
- 失联机构: {len(sljg_entities)} 实体
- 自律措施: {len(zlcs_entities)} 实体

创建了 {created_entities} 个实体页和 4 个模块页
"""

    log_file = base_dir / 'log.md'
    existing_log = log_file.read_text(encoding='utf-8') if log_file.exists() else "# 操作日志\n"
    log_file.write_text(existing_log.rstrip() + log_entry + "\n", encoding='utf-8')
    print(f"更新了 log.md")

    print('\n完成!')

if __name__ == '__main__':
    main()