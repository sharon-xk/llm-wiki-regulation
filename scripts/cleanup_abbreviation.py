#!/usr/bin/env python3
"""
清理文件名中的"（以下简称XXX）"部分
"""
import re
from pathlib import Path

def extract_clean_name(name):
    """提取干净的公司名，去掉简称部分"""
    # 去掉各种形式的"（以下简称XXX）"
    patterns = [
        r'[（〈(][^）〉)]*以下简称[^）〉)]+[）〉)]?',
        r'[（〈(]以下简称[^）〉)]*[）〉)]',
    ]

    clean = name
    for pattern in patterns:
        clean = re.sub(pattern, '', clean)

    # 清理多余的标点和空格
    clean = clean.strip()
    clean = re.sub(r'\s+', ' ', clean)
    clean = re.sub(r'[。！？，、；：]+$', '', clean)
    clean = re.sub(r'^[，、；:]+', '', clean)

    return clean if clean else None

def main():
    entities_dir = Path('/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities')

    files = list(entities_dir.glob('*.md'))
    print(f"共 {len(files)} 个文件")

    fixed = 0

    for filepath in files:
        filename = filepath.name

        if '以下简称' not in filename:
            continue

        # 提取干净名称
        clean_name = extract_clean_name(filepath.stem)

        if not clean_name:
            print(f"无法提取干净名称: {filename}")
            continue

        new_filename = clean_name + '.md'

        if new_filename == filename:
            continue

        new_path = filepath.parent / new_filename

        # 处理冲突
        if new_path.exists():
            base, ext = new_filename.rsplit('.', 1)
            counter = 1
            while new_path.exists():
                new_path = filepath.parent / f"{base}_{counter}.{ext}"
                counter += 1

        print(f"重命名: {filename} -> {new_path.name}")
        filepath.rename(new_path)

        # 同时更新frontmatter中的name
        try:
            content = new_path.read_text(encoding='utf-8')
        except:
            continue

        # 更新name
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if line.startswith('name:'):
                new_lines.append(f'name: {clean_name}')
            elif line.startswith('short_name:'):
                # 跳过short_name行，将在后面添加
                continue
            else:
                new_lines.append(line)

        # 在name后面插入short_name（如果存在）
        if 'short_name' not in content and new_path.stem != clean_name:
            # 在name行后面插入short_name
            final_lines = []
            for line in new_lines:
                final_lines.append(line)
                if line.startswith('name:'):
                    # 从原filename提取简称
                    match = re.search(r'以下简称([^）)]+)', filename)
                    if match:
                        final_lines.append(f'short_name: {match.group(1)}')

            new_path.write_text('\n'.join(final_lines), encoding='utf-8')
        else:
            new_path.write_text('\n'.join(new_lines), encoding='utf-8')

        fixed += 1

    print(f"\n完成: 重命名了 {fixed} 个文件")

if __name__ == '__main__':
    main()