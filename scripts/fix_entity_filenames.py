#!/usr/bin/env python3
"""
修复entity文件命名问题

1. 清理文件名中的非法字符（,; 等开头）
2. 处理空文件名（如.md, .md 等）
3. 确保文件名与frontmatter中的name一致
"""
import re
import os
import yaml
from pathlib import Path

def strip_bom(text):
    if text.startswith('﻿'):
        return text[1:]
    return text

def parse_frontmatter(content):
    content = strip_bom(content)
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
            else:
                lines.append(f'{key}: {data[key]}')
    lines.append('---')
    return '\n'.join(lines) + '\n'

def is_problematic_filename(filename):
    """检查文件名是否有问题"""
    name = filename.rsplit('.md', 1)[0]
    if not name:  # 空的base name，如 ".md"
        return True
    # 以,;开头
    if name.startswith(',') or name.startswith(';') or name.startswith('，') or name.startswith('；'):
        return True
    if name.startswith('.') or name.startswith(' '):
        return True
    return False

def generate_name_from_fm(fm):
    """从frontmatter生成名称"""
    if fm.get('name'):
        return fm['name']

    # 尝试从gender/birth_date/position/org推断
    parts = []
    if fm.get('gender') and fm.get('birth_date'):
        parts.append(fm['gender'])
        parts.append(fm['birth_date'])

    position = fm.get('position', '')
    org = fm.get('org', '')

    if position:
        parts.append(position)
    elif org:
        parts.append(f"登记为{org}")

    if parts:
        return ''.join(parts)

    return None

def main():
    entities_dir = Path('/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities')

    files = list(entities_dir.glob('*.md'))
    print(f"共 {len(files)} 个文件")

    fixed = 0
    errors = 0
    deleted = 0

    for filepath in files:
        filename = filepath.name

        # 检查是否需要修复
        needs_fix = is_problematic_filename(filename)

        if not needs_fix:
            continue

        # 读取内容获取正确的name
        try:
            content = filepath.read_text(encoding='utf-8')
        except Exception as e:
            print(f"读取失败: {filename} - {e}")
            errors += 1
            continue

        fm, body = parse_frontmatter(content)

        correct_name = generate_name_from_fm(fm)

        if not correct_name:
            print(f"无法确定正确名称，删除无效文件: {filename}")
            filepath.unlink()
            deleted += 1
            continue

        new_fm = fm if fm.get('name') else {
            'type': 'entity',
            'name': correct_name,
            'subtype': fm.get('subtype', '基金管理人'),
            'source_count': fm.get('source_count', 0),
            'gender': fm.get('gender', ''),
            'birth_date': fm.get('birth_date', ''),
            'position': fm.get('position', ''),
            'org': fm.get('org', ''),
            'tags': fm.get('tags', [])
        }

        # 生成安全的新文件名
        safe_name = (correct_name or '').replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_').strip()[:80]
        if not safe_name:
            print(f"安全名称为空，跳过: {filename}")
            errors += 1
            continue

        new_filename = safe_name + '.md'
        new_path = filepath.parent / new_filename

        # 处理冲突
        if new_path.exists():
            base, ext = new_filename.rsplit('.', 1)
            counter = 1
            while new_path.exists():
                new_path = filepath.parent / f"{base}_{counter}.{ext}"
                counter += 1

        print(f"修复: {filename} -> {new_path.name}")
        filepath.rename(new_path)
        fixed += 1

        # 更新内容（确保frontmatter正确）
        new_content = format_frontmatter(new_fm) + body
        new_path.write_text(new_content, encoding='utf-8')

    print(f"\n完成: 修复了 {fixed} 个文件, 删除了 {deleted} 个无效文件, {errors} 个错误")

if __name__ == '__main__':
    main()