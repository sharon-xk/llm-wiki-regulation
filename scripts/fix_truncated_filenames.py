#!/usr/bin/env python3
"""
修复截断的entity文件名（括号不闭合）
从文件内容中提取正确的name并重命名
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

def sanitize_filename(name):
    """生成合法的文件名"""
    name = name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_').strip()
    return name[:100]

def main():
    entities_dir = Path('/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities')

    files = list(entities_dir.glob('*.md'))
    print(f"共 {len(files)} 个文件")

    fixed = 0

    for filepath in files:
        filename = filepath.name
        name = filepath.stem

        # 检查是否是截断的文件
        # 1. 以〈.md 或 《.md 结尾
        # 2. 含"以下"但没有闭括号
        is_truncated = False

        if name.endswith('〈') or name.endswith('《'):
            is_truncated = True
        elif ('以下' in name or '以下简称' in name) and not ('）' in name or ')' in name or '》' in name):
            is_truncated = True

        if not is_truncated:
            continue

        # 从frontmatter获取正确的name
        try:
            content = filepath.read_text(encoding='utf-8')
        except:
            continue

        fm, body = parse_frontmatter(content)

        if not fm or 'name' not in fm:
            print(f"无法获取name: {filename}")
            continue

        correct_name = fm['name']

        # 如果name也包含截断信息，从frontmatter提取
        if '〈' in correct_name or '《' in correct_name or '以下' in correct_name:
            # 清理name
            clean = re.sub(r'[〈《][^》〉]*$', '', correct_name)
            clean = re.sub(r'以下.*$', '', clean)
            clean = clean.strip()
            if clean:
                correct_name = clean

        correct_name = sanitize_filename(correct_name)
        new_filename = correct_name + '.md'
        new_path = filepath.parent / new_filename

        # 处理冲突
        if new_path.exists() and new_path != filepath:
            base, ext = new_filename.rsplit('.', 1)
            counter = 1
            while new_path.exists():
                new_path = filepath.parent / f"{base}_{counter}.{ext}"
                counter += 1

        print(f"修复: {filename} -> {new_path.name}")
        filepath.rename(new_path)
        fixed += 1

    print(f"\n完成: 修复了 {fixed} 个文件")

if __name__ == '__main__':
    main()