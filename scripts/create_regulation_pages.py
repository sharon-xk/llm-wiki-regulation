"""
创建全部法规索引页面 wiki/regulations/
"""
import json
import re
import os
from collections import Counter, defaultdict

PARSED_DATA = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/parsed_data_with_concepts.json"
MAP_FILE = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/reg_name_map.json"
REG_DIR = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/regulations"

with open(MAP_FILE) as f:
    name_map = json.load(f)

with open(PARSED_DATA) as f:
    data = json.load(f)

def normalize(name):
    return name_map.get(name.strip(), name.strip())

# 法规元信息
reg_meta = {
    "私募投资基金监督管理暂行办法": {
        "short_name": "私募基金监管办法",
        "issuing_body": "中国证监会",
        "effective_date": "2014-08-21",
        "overview": "中国证监会颁布的私募基金行业核心监管规章，对私募基金管理人登记、基金备案、合格投资者、资金募集、投资运作等作出全面规定。是协会自律管理最重要的上位依据之一。"
    },
    "中华人民共和国证券投资基金法": {
        "short_name": "基金法",
        "issuing_body": "全国人大常委会",
        "effective_date": "2013-06-01",
        "overview": "基金行业的基本法律，规定了基金管理人职责、基金托管、基金募集、信息披露等基本制度框架。2015年修订后明确将私募基金纳入监管范围。"
    },
    "纪律处分实施办法（试行）": {
        "short_name": "实施办法",
        "issuing_body": "中国证券投资基金业协会",
        "effective_date": "2014-09-01",
        "overview": "协会对会员及从业人员实施纪律处分的基本规则，规定了处分的种类、程序、适用情形和执行机制。是协会自律管理权的直接依据。"
    },
    "中国证券投资基金业协会会员管理办法": {
        "short_name": "会员管理办法",
        "issuing_body": "中国证券投资基金业协会",
        "effective_date": "2013-06-01",
        "overview": "规定协会会员的入会条件、会员权利与义务、会籍管理等事项。违反会员义务是常见的纪律处分触发原因。"
    },
    "中国证券投资基金业协会章程": {
        "short_name": "协会章程",
        "issuing_body": "中国证券投资基金业协会",
        "effective_date": "2012-06-06",
        "overview": "协会的组织章程，规定了协会的宗旨、职责、会员、组织机构等基本事项，是协会实施自律管理的根本性文件。"
    },
    "私募投资基金管理人内部控制指引": {
        "short_name": "内控指引",
        "issuing_body": "中国证券投资基金业协会",
        "effective_date": "2016-02-01",
        "overview": "规范私募基金管理人内部控制体系的建立与运行，涵盖组织架构、业务流程、风险控制、合规管理等方面。"
    },
    "私募投资基金信息披露管理办法": {
        "short_name": "信披办法",
        "issuing_body": "中国证券投资基金业协会",
        "effective_date": "2016-02-04",
        "overview": "规定私募基金管理人向投资者和协会进行信息披露的内容、方式和时限要求。信息披露违规是处罚案例中最常见的违规类型之一。"
    },
    "私募投资基金募集行为管理办法": {
        "short_name": "募集办法",
        "issuing_body": "中国证券投资基金业协会",
        "effective_date": "2016-07-15",
        "overview": "规范私募基金的推介、销售和资金募集行为，包括合格投资者确认、适当性匹配、冷静期回访等制度。"
    },
    "私募投资基金登记备案办法": {
        "short_name": "登记备案办法",
        "issuing_body": "中国证券投资基金业协会",
        "effective_date": "2014-02-07",
        "overview": "规定私募基金管理人登记和基金产品备案的程序与要求。未按规定登记备案是处罚案例中的高频违规类型。"
    },
    "关于加强私募投资基金监管的若干规定": {
        "short_name": "加强私募监管规定",
        "issuing_body": "中国证监会",
        "effective_date": "2020-12-30",
        "overview": "中国证监会关于加强私募基金监管的规范性文件，重申和细化了管理人登记、基金备案、资金募集、投资运作等方面的监管要求。"
    },
    "中国证券投资基金业协会自律检查规则": {
        "short_name": "自律检查规则",
        "issuing_body": "中国证券投资基金业协会",
        "effective_date": "2020-09-01",
        "overview": "规定协会对会员进行自律检查的程序和要求，包括检查方式、检查内容、配合义务和违规处理。"
    },
    "私募投资基金备案须知": {
        "short_name": "备案须知",
        "issuing_body": "中国证券投资基金业协会",
        "effective_date": "2019-12-23",
        "overview": "协会对私募基金备案的细化要求和注意事项说明，补充了登记备案办法的具体操作规范。"
    },
}

# 收集每个法规的统计信息
reg_stats = defaultdict(lambda: {
    'cited_count': 0,
    'concepts': Counter(),
    'entities': [],
    'articles': defaultdict(lambda: {'count': 0, 'concepts': Counter()})
})

for item in data:
    basis = item.get('legal_basis', '')
    if not basis:
        continue

    found = re.findall(r'《([^》]+)》', basis)
    entity_name = item.get('entity', '').replace('.md', '')

    for name in found:
        std_name = normalize(name)
        if std_name not in reg_meta:
            continue
        stats = reg_stats[std_name]
        stats['cited_count'] += 1
        if entity_name and entity_name not in stats['entities']:
            stats['entities'].append(entity_name)

        for vc in item.get('violation_concepts', []):
            for c in vc.get('concepts', []):
                stats['concepts'][c] += 1

        # 从违规文本中提取条款号
        for v in item.get('violations', []):
            # 提取 "第X条" 模式
            articles = re.findall(r'第([一二三四五六七八九十百千]+)条', v)
            for art in articles:
                stats['articles'][art]['count'] += 1
                for vc in item.get('violation_concepts', []):
                    for c in vc.get('concepts', []):
                        stats['articles'][art]['concepts'][c] += 1

# 文章编号映射
ARTICLE_NUM_MAP = {
    '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
    '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
    '十一': '11', '十二': '12', '十三': '13', '十四': '14', '十五': '15',
    '十六': '16', '十七': '17', '十八': '18', '十九': '19', '二十': '20',
    '二十一': '21', '二十二': '22', '二十三': '23', '二十四': '24', '二十五': '25',
    '二十六': '26', '二十七': '27', '二十八': '28', '二十九': '29', '三十': '30',
    '三十一': '31', '三十二': '32', '三十三': '33', '三十四': '34', '三十五': '35',
    '三十六': '36', '三十七': '37', '三十八': '38', '三十九': '39', '四十': '40',
}

# 常见条款的简要描述
COMMON_ARTICLES = {
    "私募投资基金监督管理暂行办法": {
        "4": "管理人应当恪尽职守，履行诚实信用、谨慎勤勉义务",
        "8": "私募基金募集完毕后，管理人应当办理基金备案手续",
        "11": "私募基金募集完毕后应向协会备案",
        "12": "私募基金的合格投资者标准",
        "14": "管理人不得向合格投资者之外的单位和个人募集资金",
        "15": "禁止向投资者承诺本金不受损失或承诺最低收益",
        "16": "私募基金销售机构应履行投资者适当性审查义务",
        "23": "管理人及其从业人员不得将基金财产混同、挪用或侵占",
        "24": "管理人应按规定向投资者披露信息",
        "25": "管理人应按规定向协会报送信息",
        "26": "协会对管理人实施自律管理",
    },
    "中华人民共和国证券投资基金法": {
        "4": "基金管理人应恪尽职守，履行诚实信用、谨慎勤勉义务",
        "46": "基金份额持有人权利",
        "60": "基金管理人应按规定披露基金信息",
        "95": "私募基金管理人应按规定办理登记备案",
        "103": "禁止挪用基金财产",
        "120": "基金管理人违反规定的法律责任",
    },
    "纪律处分实施办法（试行）": {
        "2": "协会对会员及从业人员的纪律处分适用本办法",
        "4": "纪律处分种类（警告、罚款、暂停资格、取消资格等）",
        "10": "纪律处分的程序规定",
    },
    "私募投资基金募集行为管理办法": {
        "15": "私募基金推介禁止行为",
        "17": "委托募集应委托具有基金销售资格的机构",
        "18": "合格投资者确认程序",
        "24": "禁止向投资者承诺保本保收益",
        "29": "投资冷静期不少于24小时",
        "30": "冷静期后应进行回访确认",
    },
    "私募投资基金信息披露管理办法": {
        "9": "基金募集期间的信息披露义务",
        "11": "基金运作期间的信息披露义务",
        "17": "重大事项信息披露",
        "21": "信息披露违规的处理",
    },
    "私募投资基金管理人内部控制指引": {
        "17": "管理人不得委托不具有基金销售资格的机构募集资金",
        "20": "管理人应建立合格投资者适当性制度",
        "31": "管理人应建立信息披露制度",
    },
    "私募投资基金登记备案办法": {
        "11": "私募基金募集完毕后的备案要求",
        "22": "重大事项变更报告义务",
        "29": "冷静期规定",
        "30": "回访确认规定",
    },
    "关于加强私募投资基金监管的若干规定": {
        "4": "管理人应履行诚实信用、谨慎勤勉义务",
        "6": "管理人不得有损害基金财产和投资者利益的行为",
        "9": "管理人信息报送义务",
    },
    "中国证券投资基金业协会自律检查规则": {
        "2": "自律检查的范围和配合义务",
    },
}

def format_article_num(cn_num):
    return ARTICLE_NUM_MAP.get(cn_num, cn_num)

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

def create_regulation_page(std_name):
    meta = reg_meta.get(std_name)
    if not meta:
        return

    stats = reg_stats[std_name]

    # Build frontmatter
    # Use top 3 concepts as tags
    top_concepts = [c for c, _ in stats['concepts'].most_common(3)]

    fm = format_frontmatter({
        'type': 'regulation',
        'name': std_name,
        'short_name': meta['short_name'],
        'issuing_body': meta['issuing_body'],
        'effective_date': meta['effective_date'],
        'cited_count': stats['cited_count'],
        'tags': top_concepts,
    })

    # Build content
    lines = [fm]
    lines.append(f"## 概述")
    lines.append(f"")
    lines.append(meta['overview'])
    lines.append(f"")

    # 关联违规类型
    if stats['concepts']:
        lines.append(f"## 关联违规类型")
        lines.append(f"")
        for concept, count in stats['concepts'].most_common():
            lines.append(f"- [{concept}](concepts/{concept}.md) — {count} 次引用")
        lines.append(f"")

    # 高频条款 (top 10 by citation count)
    top_articles = sorted(stats['articles'].items(), key=lambda x: -x[1]['count'])[:10]

    if top_articles:
        lines.append(f"## 高频条款")
        lines.append(f"")

        for art_num_cn, art_info in top_articles:
            art_num = format_article_num(art_num_cn)
            art_desc = COMMON_ARTICLES.get(std_name, {}).get(art_num, "")

            lines.append(f"### 第{art_num_cn}条{'（' + art_desc + '）' if art_desc else ''}")
            lines.append(f"")
            lines.append(f"- 引用次数：{art_info['count']}")
            if art_info['concepts']:
                top_art_concepts = ', '.join(
                    f"[{c}](concepts/{c}.md)" for c, _ in art_info['concepts'].most_common(3)
                )
                lines.append(f"- 关联违规：{top_art_concepts}")
            lines.append(f"")

    # 典型案例 (top 10 entities)
    if stats['entities']:
        lines.append(f"## 典型案例")
        lines.append(f"")
        for entity in stats['entities'][:10]:
            # Clean entity filename
            entity_clean = entity.replace('.md', '')
            lines.append(f"- [{entity_clean}](entities/{entity})")

    content = '\n'.join(lines)

    # Write file
    fname = std_name + '.md'
    fpath = os.path.join(REG_DIR, fname)
    with open(fpath, 'w') as f:
        f.write(content)

    print(f"Created: {fname}")
    print(f"  cited_count: {stats['cited_count']}")
    print(f"  concepts: {len(stats['concepts'])}")
    print(f"  articles: {len(stats['articles'])} (top: {len(top_articles)})")
    print(f"  entities: {len(stats['entities'])}")

def main():
    os.makedirs(REG_DIR, exist_ok=True)

    # 按引用次数降序创建页面
    sorted_regs = sorted(reg_meta.keys(), key=lambda n: -reg_stats[n]['cited_count'])

    created = 0
    for std_name in sorted_regs:
        if reg_stats[std_name]['cited_count'] > 0:
            create_regulation_page(std_name)
            created += 1

    print(f"\n共创建 {created} 个法规页面")

if __name__ == '__main__':
    main()
