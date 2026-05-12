#!/usr/bin/env python3
"""
修复entity的frontmatter中的name字段和文件名，使其与文件名一致
清理name中的"（以下简称XXX）"部分，并提取简称到short_name字段
"""
import re
import yaml
from pathlib import Path

def parse_frontmatter(content):
    lines = content.split('\n')
    if not lines or lines[0].strip() != '---':
        return {}, content

    end_idx = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == '---':
            end_idx = i
            break

    if end_idx is None:
        return {}, content

    fm_text = '\n'.join(lines[1:end_idx])
    body = '\n'.join(lines[end_idx+1:])

    try:
        fm = yaml.safe_load(fm_text) or {}
    except:
        fm = {}

    return fm, body

def format_frontmatter(data):
    ordered_keys = ['type', 'name', 'short_name', 'gender', 'birth_date', 'position', 'org', 'subtype', 'source_count', 'first_incident', 'latest_incident', 'tags']

    lines = ['---']
    for key in ordered_keys:
        if key in data and data[key] is not None:
            if isinstance(data[key], list):
                lines.append(f'{key}: [{", ".join(data[key])}]')
            elif isinstance(data[key], bool):
                lines.append(f'{key}: {"true" if data[key] else "false"}')
            else:
                lines.append(f'{key}: {data[key]}')
    lines.append('---')
    return '\n'.join(lines) + '\n'

def extract_clean_name(name):
    """从name中提取干净的公司名，去掉简称部分"""
    # 去掉各种形式的"（以下简称XXX）"
    clean = re.sub(r'[（〈(][^）〉)]*以下简称[^）〉)]+[）〉)]?', '', name)
    clean = re.sub(r'[（〈(]以下简称[^）〉)]*[）〉)]', '', clean)
    clean = clean.strip()
    clean = re.sub(r'\s+', ' ', clean)
    clean = re.sub(r'^[，、；:]+', '', clean)
    return clean if clean else None

def main():
    entities_dir = Path('/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities')

    files = list(entities_dir.glob('*.md'))
    print(f"共 {len(files)} 个文件")

    fixed = 0

    for filepath in files:
        filename = filepath.name
        current_stem = filepath.stem

        try:
            content = filepath.read_text(encoding='utf-8')
        except:
            continue

        fm, body = parse_frontmatter(content)

        if not fm or 'name' not in fm:
            continue

        current_name = fm.get('name', '')

        # 检查是否需要清理
        needs_clean = '以下简称' in current_name

        if not needs_clean and current_name == current_stem:
            continue

        new_fm = dict(fm)

        if needs_clean:
            clean_name = extract_clean_name(current_name)
            if clean_name:
                new_fm['name'] = clean_name

                # 提取简称
                match = re.search(r'以下简称([^）〉)]+)', current_name)
                if match:
                    new_fm['short_name'] = match.group(1).strip()

                # 重命名文件
                new_filename = clean_name + '.md'
                new_path = filepath.parent / new_filename

                if new_path.exists() and new_path != filepath:
                    base, ext = new_filename.rsplit('.', 1)
                    counter = 1
                    while new_path.exists():
                        new_path = filepath.parent / f"{base}_{counter}.{ext}"
                        counter += 1

                print(f"修复: {filename} -> {new_path.name}")
                filepath.rename(new_path)

                new_content = format_frontmatter(new_fm) + body
                new_path.write_text(new_content, encoding='utf-8')
                fixed += 1
        else:
            # 只是frontmatter与文件名不一致
            new_fm['name'] = current_stem
            new_content = format_frontmatter(new_fm) + body
            filepath.write_text(new_content, encoding='utf-8')
            print(f"修复frontmatter: {filename}")
            fixed += 1

    print(f"\n完成: 修复了 {fixed} 个文件")

if __name__ == '__main__':
    main()