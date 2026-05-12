#!/usr/bin/env python3
"""
彻底清理文件名中的各种"简称"变体
"""
import re
from pathlib import Path

def extract_clean_name(name):
    """从name中提取干净的公司名，去掉各种简称标记"""
    # 去掉以下各种模式：
    # （以下简称XXX）
    # 〈以下简称XXX）
    # (以下简称XXX)
    # 以下简称XXX
    # 〈以下简XXX）
    # (以下简XXX)
    # 等等

    patterns = [
        r'[（〈(][^）〉)]*以下[^）〉)]*简[^）〉)]*[）〉]?',
        r'[（〈(]以下简称[^）〉)]*[）〉]?',
        r'以下简[^）〉]+',
    ]

    clean = name
    for pattern in patterns:
        clean = re.sub(pattern, '', clean)

    # 清理
    clean = clean.strip()
    clean = re.sub(r'\s+', ' ', clean)
    clean = re.sub(r'^[，、；:]+', '', clean)
    clean = re.sub(r'^[（〈)]+', '', clean)

    # 去除尾部不完整的括号
    clean = re.sub(r'[（〈]$', '', clean)
    clean = re.sub(r'\)udes$', '', clean)

    return clean if clean else None

def main():
    entities_dir = Path('/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities')

    files = list(entities_dir.glob('*.md'))
    print(f"共 {len(files)} 个文件")

    fixed = 0

    for filepath in files:
        filename = filepath.name
        current_stem = filepath.stem

        # 只处理包含"以下"的文件
        if '以下' not in current_stem:
            continue

        clean_name = extract_clean_name(current_stem)

        if not clean_name or clean_name == current_stem:
            continue

        new_filename = clean_name + '.md'
        new_path = filepath.parent / new_filename

        # 处理冲突
        if new_path.exists():
            base, ext = new_filename.rsplit('.', 1)
            counter = 1
            while new_path.exists():
                new_path = filepath.parent / f"{base}_{counter}.{ext}"
                counter += 1

        print(f"重命名: {filename} -> {new_path.name}")

        # 读取内容并更新frontmatter
        try:
            content = filepath.read_text(encoding='utf-8')
        except:
            continue

        # 更新name和short_name
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if line.startswith('name:'):
                new_lines.append(f'name: {clean_name}')
            elif line.startswith('short_name:'):
                # 提取简称
                match = re.search(r'以下简([^）〉]+)', current_stem)
                if match:
                    short = match.group(1).strip()
                    if short:
                        new_lines.append(f'short_name: {short}')
                continue
            else:
                new_lines.append(line)

        # 如果没有short_name但能提取出来，添加它
        if 'short_name:' not in content:
            match = re.search(r'以下简([^）〉]+)', current_stem)
            if match:
                short = match.group(1).strip()
                if short:
                    # 在name行后面插入
                    final_lines = []
                    for line in new_lines:
                        final_lines.append(line)
                        if line.startswith('name:'):
                            final_lines.append(f'short_name: {short}')
                    new_lines = final_lines

        filepath.rename(new_path)
        new_path.write_text('\n'.join(new_lines), encoding='utf-8')
        fixed += 1

    print(f"\n完成: 重命名了 {fixed} 个文件")

if __name__ == '__main__':
    main()