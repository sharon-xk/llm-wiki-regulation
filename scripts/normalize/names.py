#!/usr/bin/env python3
"""
规范化entity文件命名和内容

规则：
1. 个人主体：文件名只保留姓名，提取性别/出生日期/任职信息到frontmatter
2. 公司主体：去掉文件名中的"（以下简称XXX）"后缀，提取简称到short_name属性
3. 合并重复实体（同一公司/个人只保留一条记录）

用法：
    python3 normalize_entities.py          # 干跑模式
    python3 normalize_entities.py --execute # 实际执行
"""
import re
import os
import yaml
import shutil
from pathlib import Path

def strip_bom(text):
    """去除UTF-8 BOM"""
    if text.startswith('﻿'):
        return text[1:]
    return text

def parse_frontmatter(content):
    """解析frontmatter"""
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
    """生成frontmatter字符串"""
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

def extract_person_info(name):
    """从个人主体name中提取信息"""
    info = {}

    # 提取性别
    gender_match = re.search(r'[,，]([男女])[,，\s]', name)
    if gender_match:
        info['gender'] = gender_match.group(1)

    # 提取出生年份
    birth_match = re.search(r'(\d{4})\s*年', name)
    if birth_match:
        info['birth_date'] = f"{birth_match.group(1)}年"

    # 提取职位信息
    position_keywords = ['时任', '现任', '登记为', '经查为']
    for kw in position_keywords:
        if kw in name:
            idx = name.find(kw)
            rest = name[idx+len(kw):].split('，')[0].split('。')[0].strip()
            if rest:
                info['position'] = kw + rest
                # 提取机构名
                info['org'] = rest.rstrip('。！？')
            break

    # 提取纯净人名
    parts = re.split(r'[,，]', name, 1)
    clean_name = parts[0].strip()
    clean_name = re.sub(r'等$', '', clean_name)

    return clean_name, info

def extract_company_short_name(name):
    """从公司主体name中提取简称"""
    # 匹配各种变体
    patterns = [
        r'[（〈]以下简称([^）〉]+)[）〉]',
        r'[（〈]以下简称(.+?)[）〉]',
        r'[（〈]以下简称(.+)',
    ]

    short_name = None
    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            short_name = match.group(1).strip()
            break

    # 清理主名称
    clean_name = re.sub(r'[（〈]以下简称[^）〉]+[）〉]?', '', name)
    clean_name = clean_name.strip()

    return clean_name, short_name

def sanitize_filename(name):
    """生成合法的文件名"""
    # 替换非法字符
    name = name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
    # 去除前后空格
    name = name.strip()
    # 限制长度
    return name[:100]

def process_file(filepath):
    """处理单个文件"""
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"读取失败 {filepath}: {e}")
        return None, None, None

    fm, body = parse_frontmatter(content)

    if not fm or 'name' not in fm:
        print(f"无法解析frontmatter: {filepath}")
        return None, None, None

    name = fm.get('name', '')
    subtype = fm.get('subtype', '')

    # 判断是否是个人主体
    is_person = False
    if subtype == '个人':
        is_person = True
    elif re.search(r'[,，][男女][,，\s]', name):
        is_person = True

    new_fm = dict(fm)

    if is_person:
        clean_name, person_info = extract_person_info(name)
        new_fm['name'] = clean_name
        new_fm['subtype'] = '个人'

        for k, v in person_info.items():
            key_map = {'gender': 'gender', 'birth_date': 'birth_date', 'position': 'position', 'org': 'org'}
            if k in key_map and key_map[k] not in new_fm:
                new_fm[key_map[k]] = v
    else:
        clean_name, short_name = extract_company_short_name(name)
        new_fm['name'] = clean_name

        if subtype not in new_fm:
            new_fm['subtype'] = '基金管理人'
        else:
            new_fm['subtype'] = subtype

        if short_name:
            new_fm['short_name'] = short_name

    new_filename = sanitize_filename(new_fm['name']) + '.md'

    return new_fm, new_filename, body

def main():
    entities_dir = Path(__file__).parent.parent.parent / "wiki" / "entities"
    dry_run = '--execute' not in sys.argv

    print(f"处理目录: {entities_dir}")
    print(f"模式: {'干跑' if dry_run else '执行'}")

    # 读取所有文件
    all_files = list(entities_dir.glob('*.md'))
    print(f"共发现 {len(all_files)} 个文件")

    # 统计
    stats = {'person': 0, 'company': 0, 'duplicates': 0, 'renamed': 0, 'errors': 0}
    name_to_info = {}  # key -> (filepath, new_fm, body)

    changes = []

    for filepath in sorted(all_files):
        result = process_file(filepath)
        if result[0] is None:
            stats['errors'] += 1
            continue

        new_fm, new_filename, body = result

        # 构建唯一key
        subtype = new_fm.get('subtype', '')
        name = new_fm.get('name', '')
        key = (subtype, name)

        is_duplicate = key in name_to_info

        if is_duplicate:
            stats['duplicates'] += 1
        else:
            name_to_info[key] = (filepath, new_fm, body)

        if subtype == '个人':
            stats['person'] += 1
        else:
            stats['company'] += 1

        if filepath.name != new_filename:
            stats['renamed'] += 1

        changes.append({
            'filepath': filepath,
            'old_name': filepath.name,
            'new_filename': new_filename,
            'fm': new_fm,
            'body': body,
            'is_duplicate': is_duplicate,
            'key': key
        })

    print(f"\n统计:")
    print(f"  个人主体: {stats['person']}")
    print(f"  公司主体: {stats['company']}")
    print(f"  重复实体: {stats['duplicates']}")
    print(f"  需重命名: {stats['renamed']}")
    print(f"  错误: {stats['errors']}")

    if dry_run:
        print(f"\n=== 变化预览 ===")
        shown = 0
        for c in changes[:50]:
            if c['is_duplicate']:
                print(f"[合并] {c['old_name']} -> {c['new_filename']}")
                shown += 1
            elif c['old_name'] != c['new_filename']:
                print(f"[重命名] {c['old_name']} -> {c['new_filename']}")
                shown += 1

        print(f"\n...共 {len(changes)} 条记录，显示前50条")

        dup_files = [c['old_name'] for c in changes if c['is_duplicate']]
        if dup_files:
            print(f"\n=== 重复实体 ({len(dup_files)} 个) ===")
            for f in dup_files[:20]:
                print(f"  {f}")
            if len(dup_files) > 20:
                print(f"  ...还有 {len(dup_files) - 20} 个")

        return

    # 执行模式
    print("\n开始执行...")

    # 删除重复文件
    for c in changes:
        if c['is_duplicate']:
            c['filepath'].unlink()
            print(f"删除重复: {c['old_name']}")

    # 处理重命名和内容更新
    for c in changes:
        if c['is_duplicate']:
            continue

        new_path = c['filepath'].parent / c['new_filename']

        # 处理文件名冲突
        if new_path.exists() and new_path != c['filepath']:
            base, ext = c['new_filename'].rsplit('.', 1)
            counter = 1
            while new_path.exists():
                new_path = c['filepath'].parent / f"{base}_{counter}.{ext}"
                counter += 1

        # 重命名
        if str(new_path) != str(c['filepath']):
            c['filepath'].rename(new_path)
            print(f"重命名: {c['old_name']} -> {new_path.name}")

        # 写入内容
        new_content = format_frontmatter(c['fm']) + c['body']
        new_path.write_text(new_content, encoding='utf-8')

    print(f"\n完成！处理了 {len(changes)} 个文件")

if __name__ == '__main__':
    import sys
    main()