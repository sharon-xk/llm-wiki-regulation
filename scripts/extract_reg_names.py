"""
从 parsed_data 和 entity 页面提取所有法规名称及其变体
"""
import json
import re
import os
from collections import Counter

PARSED_DATA = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/parsed_data_with_concepts.json"
ENTITY_DIR = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities"

def extract_from_parsed():
    """从 parsed data 的 legal_basis 字段提取"""
    with open(PARSED_DATA) as f:
        data = json.load(f)

    names = Counter()
    for item in data:
        basis = item.get('legal_basis', '')
        if not basis:
            continue
        # legal_basis 格式: "《基金法》、《私募基金监管办法》、《协会章程》"
        found = re.findall(r'《([^》]+)》', basis)
        for name in found:
            names[name.strip()] += 1

    return names

def extract_from_entities():
    """从 entity 页面提取法规名"""
    names = Counter()
    for fname in os.listdir(ENTITY_DIR):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(ENTITY_DIR, fname)
        with open(fpath) as f:
            content = f.read()
        found = re.findall(r'《([^》]+)》', content)
        for name in found:
            # 过滤掉非法规名（机构名、地名等）
            name = name.strip()
            # 法规名通常包含"法"、"办法"、"条例"、"指引"等
            if any(kw in name for kw in ['法', '办法', '条例', '指引', '规定', '规则', '章程', '办法', '通知', '规范', '细则']):
                names[name] += 1

    return names

def main():
    parsed_names = extract_from_parsed()
    entity_names = extract_from_entities()

    all_names = parsed_names + entity_names

    print(f"=== 来自 parsed data ({len(parsed_names)} 个唯一名) ===")
    for name, count in parsed_names.most_common(50):
        print(f"  [{count:4d}] {name}")

    print(f"\n=== 仅在 entity 页面出现 ({len(entity_names)} 个唯一名) ===")
    only_entity = entity_names - parsed_names
    for name, count in only_entity.most_common(30):
        print(f"  [{count:4d}] {name}")

    print(f"\n=== 总计唯一法规名: {len(all_names)} ===")

if __name__ == '__main__':
    main()
