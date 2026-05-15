"""
修复 entity 文件名中的 "以下简称XXX" 问题
1. 文件名去除此类后缀
2. frontmatter name 同步修正
3. parsed_data_with_concepts.json entity 字段同步更新
"""
import os
import re
import json
from pathlib import Path

ENTITY_DIR = str(Path(__file__).parent.parent.parent / "wiki" / "entities")
PARSED = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/parsed_data_with_concepts.json"


def clean_name(raw_name):
    """移除 '以下简称XXX' 及后续内容，保留干净的公司名"""
    # 移除 [〔(（]?以下简称... 及之后所有内容
    cleaned = re.sub(r'[〔(（]?以下简称.*$', '', raw_name)
    # 清理尾部残留的无关字符
    cleaned = cleaned.rstrip()
    return cleaned


def main():
    renamed = []
    name_map = {}  # old_filename -> new_filename

    for fname in sorted(os.listdir(ENTITY_DIR)):
        if not fname.endswith('.md'):
            continue
        if '以下简称' not in fname:
            continue

        fpath = os.path.join(ENTITY_DIR, fname)
        with open(fpath, 'r') as f:
            content = f.read()

        # 提取旧 frontmatter name
        fm_match = re.search(r'name:\s*(.+)', content)
        old_fm_name = fm_match.group(1).strip() if fm_match else ''

        # 清理公司名
        clean = clean_name(fname.replace('.md', ''))
        new_fname = clean + '.md'

        # 更新 frontmatter
        new_content = re.sub(
            r'^name:\s*.+$',
            f'name: {clean}',
            content,
            flags=re.MULTILINE
        )

        # 写回文件
        new_fpath = os.path.join(ENTITY_DIR, new_fname)
        with open(new_fpath, 'w') as f:
            f.write(new_content)

        # 删除旧文件（如果新旧文件名不同）
        if new_fname != fname:
            os.remove(fpath)

        name_map[fname] = new_fname
        renamed.append((fname, clean))
        print(f"  {fname}")
        print(f"    → {new_fname}")

    print(f"\n文件名修复: {len(renamed)} 个")

    # 更新 parsed_data_with_concepts.json
    if name_map:
        with open(PARSED, 'r') as f:
            data = json.load(f)

        updates = 0
        for record in data:
            old_entity = record.get('entity', '')
            if old_entity in name_map:
                record['entity'] = name_map[old_entity]
                updates += 1

        with open(PARSED, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"parsed_data_with_concepts.json 同步更新: {updates} 条")

    # 验证：确保无重名冲突
    for fname in sorted(os.listdir(ENTITY_DIR)):
        if fname.endswith('.md') and '以下简称' in fname:
            print(f"WARNING: 仍有未修复文件: {fname}")


if __name__ == "__main__":
    main()
