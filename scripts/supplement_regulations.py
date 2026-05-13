"""
补充异常经营/失联机构法规：更新映射表、创建法规页、更新entity页
"""
import json
import os
import re
from collections import Counter, defaultdict

PARSED_HTML = "/Users/sharon/ai-project/llm-wiki-regulation/raw/parsed_html_results.json"
MAP_FILE = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/reg_name_map.json"
ENTITY_DIR = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities"
REG_DIR = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/regulations"

# ===== 1. 更新映射表 =====
new_regs = {
    "关于私募基金管理人在异常经营情形下提交专项法律意见书的公告": "关于私募基金管理人在异常经营情形下提交专项法律意见书的公告",
    "关于进一步规范私募基金管理人登记若干事项的公告": "关于进一步规范私募基金管理人登记若干事项的公告",
    "私募基金管理人失联处理指引": "私募基金管理人失联处理指引",
    "公告": "关于私募基金管理人在异常经营情形下提交专项法律意见书的公告",
    "指引": "私募基金管理人失联处理指引",
}

with open(MAP_FILE) as f:
    name_map = json.load(f)

for k, v in new_regs.items():
    if k not in name_map:
        name_map[k] = v

with open(MAP_FILE, 'w') as f:
    json.dump(name_map, f, ensure_ascii=False, indent=2)

print("Updated reg_name_map.json")

# ===== 2. 从 parsed_html_results.json 提取法规引用 =====
with open(PARSED_HTML) as f:
    html_data = json.load(f)

# 统计每个法规在哪些entity中被引用
reg_entities = defaultdict(lambda: {'count': 0, 'entities': [], 'module': '', 'samples': []})

for module in ['异常经营', '失联机构']:
    for item in html_data.get(module, []):
        text = item.get('text', '')
        companies = item.get('companies', [])
        source = item.get('source', '')

        # 提取法规名
        found = re.findall(r'《([^》]+)》', text)
        for name in found:
            name = name.strip()
            std_name = name_map.get(name)
            if std_name and std_name in new_regs.values():
                reg_entities[std_name]['count'] += 1
                reg_entities[std_name]['module'] = module
                for company in companies:
                    if isinstance(company, dict):
                        cname = company.get('name', '')
                    else:
                        cname = str(company)
                    # 过滤明显不是公司名的条目（如公告标题）
                    if cname.startswith('关于') and ('注销' in cname or '请' in cname):
                        continue
                    fname = cname + '.md'
                    if fname not in reg_entities[std_name]['entities']:
                        reg_entities[std_name]['entities'].append(fname)
                # 保存样本
                if len(reg_entities[std_name]['samples']) < 3:
                    reg_entities[std_name]['samples'].append(text[:500])

print("\n法规统计:")
for reg_name, stats in reg_entities.items():
    print(f"  [{reg_name}]")
    print(f"    模块: {stats['module']}")
    print(f"    引用次数: {stats['count']}")
    print(f"    关联entity: {len(stats['entities'])}")
    print(f"    样本entity: {stats['entities'][:5]}")

# ===== 3. 创建法规页 =====
reg_meta = {
    "关于私募基金管理人在异常经营情形下提交专项法律意见书的公告": {
        "short_name": "异常经营法律意见书公告",
        "issuing_body": "中国证券投资基金业协会",
        "effective_date": "2018-03-27",
        "overview": "协会关于私募基金管理人在异常经营情形下提交专项法律意见书的程序性规定。明确了异常经营的认定标准、专项法律意见书提交时限（3个月）及逾期未提交的注销后果。是异常经营注销程序的核心依据。",
        "tags": ["异常经营"],
    },
    "关于进一步规范私募基金管理人登记若干事项的公告": {
        "short_name": "登记事项规范公告",
        "issuing_body": "中国证券投资基金业协会",
        "effective_date": "2016-02-05",
        "overview": "协会关于规范私募基金管理人登记事项的公告，明确了管理人登记信息更新、法律意见书提交等要求，是异常经营注销程序中援引的注销依据之一。",
        "tags": ["异常经营"],
    },
    "私募基金管理人失联处理指引": {
        "short_name": "失联处理指引",
        "issuing_body": "中国证券投资基金业协会",
        "effective_date": "2023-07-14",
        "overview": "协会关于私募基金管理人失联认定与处理的程序性规定。明确了失联的认定标准（无法通过电话、电子邮件等取得有效联系）、主动联系期限（5个工作日）、公示流程及公示期满一个月未完成情况报告的注销后果。",
        "tags": ["失联机构"],
    },
}

ARTICLE_NUM_MAP = {
    '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
    '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
    '十一': '11', '十二': '12', '十三': '13', '十四': '14', '十五': '15',
}

def format_frontmatter(data):
    ordered_keys = ['type', 'name', 'short_name', 'issuing_body', 'effective_date', 'cited_count', 'tags']
    lines = ['---']
    for key in ordered_keys:
        if key in data and data[key] is not None:
            if isinstance(data[key], list):
                lines.append(f'{key}: [{", ".join(data[key])}]')
            else:
                lines.append(f'{key}: {data[key]}')
    lines.append('---')
    return '\n'.join(lines) + '\n'

def format_article_num(cn_num):
    return ARTICLE_NUM_MAP.get(cn_num, cn_num)

os.makedirs(REG_DIR, exist_ok=True)

for reg_name, meta in reg_meta.items():
    stats = reg_entities.get(reg_name, {'count': 0, 'entities': [], 'samples': []})

    fm = format_frontmatter({
        'type': 'regulation',
        'name': reg_name,
        'short_name': meta['short_name'],
        'issuing_body': meta['issuing_body'],
        'effective_date': meta['effective_date'],
        'cited_count': stats['count'],
        'tags': meta['tags'],
    })

    # 从样本中提取条款引用
    articles = Counter()
    for sample in stats['samples']:
        arts = re.findall(r'第([一二三四五六七八九十]+)条', sample)
        for a in arts:
            articles[a] += 1

    lines = [fm]
    lines.append("## 概述")
    lines.append("")
    lines.append(meta['overview'])
    lines.append("")

    # 关联模块
    module = stats.get('module', '')
    if module:
        lines.append(f"## 关联模块")
        lines.append(f"")
        lines.append(f"- [{module}](modules/{module}.md)")
        lines.append(f"")

    # 高频条款（从样本提取，可能不完整）
    if articles:
        lines.append("## 主要条款")
        lines.append("")
        for art_cn, cnt in articles.most_common(10):
            lines.append(f"- 第{art_cn}条 — {cnt} 次引用")
        lines.append("")

    # 典型案例
    if stats['entities']:
        lines.append("## 典型案例")
        lines.append("")
        for entity_file in stats['entities'][:15]:
            entity_name = entity_file.replace('.md', '')
            lines.append(f"- [{entity_name}](entities/{entity_file})")

    content = '\n'.join(lines)
    fpath = os.path.join(REG_DIR, reg_name + '.md')
    with open(fpath, 'w') as f:
        f.write(content)
    print(f"Created: {reg_name}.md (cited: {stats['count']}, entities: {len(stats['entities'])})")

# ===== 4. 更新entity页面的法规链接 =====
# 为异常经营/失联机构 entity 补充法规跳转
print("\n更新 entity 页面...")

updated = 0
for module, reg_name in [('异常经营', '关于私募基金管理人在异常经营情形下提交专项法律意见书的公告'),
                          ('失联机构', '私募基金管理人失联处理指引')]:
    stats = reg_entities.get(reg_name, {})
    for entity_file in stats['entities']:
        fpath = os.path.join(ENTITY_DIR, entity_file)
        if not os.path.exists(fpath):
            continue
        with open(fpath) as f:
            content = f.read()

        # 检查是否已有法规链接
        if 'wiki/regulations/' in content:
            continue

        # 在"基本信息" section 末尾补充法规依据
        regulation_link = f"wiki/regulations/{reg_name}.md"
        insert_text = f"\n- **依据法规**: [{reg_name}]({regulation_link})"

        # 找到 ## 基本信息 section，在下一个 ## 之前插入
        if '## 基本信息' in content:
            # 在 ## 基本信息 后的第一个空行处或下一个 ## 之前插入
            pattern = r'(## 基本信息.*?)(\n## |\n---)'
            replacement = rf'\1{insert_text}\n\2'
            new_content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)
            if new_content != content:
                with open(fpath, 'w') as f:
                    f.write(new_content)
                updated += 1

print(f"  更新了 {updated} 个 entity 页面")

print("\nDone.")
