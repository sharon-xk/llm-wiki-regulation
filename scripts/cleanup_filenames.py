#!/usr/bin/env python3
"""
彻底清理entity文件名的非法字符
"""
import re
from pathlib import Path

def sanitize_filename(name):
    """清理文件名，只允许中文、字母、数字、括号、括号、空格"""
    # 只保留合法字符
    result = ''
    for c in name:
        if c.isalnum() or c in '()-（）() 《》「」''""' or c.isspace() or c in '的的和与及或':
            result += c
    # 去除多余空格
    result = re.sub(r'\s+', ' ', result).strip()
    # 去除末尾的标点
    result = re.sub(r'[。！？，、；：]+$', '', result)
    return result

def main():
    entities_dir = Path('/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities')

    files = list(entities_dir.glob('*.md'))
    print(f"共 {len(files)} 个文件")

    fixed = 0

    for filepath in files:
        filename = filepath.name

        # 检查是否以非法字符开头
        if filename.startswith('，') or filename.startswith('，') or filename.startswith(';') or filename.startswith(';'):
            # 从frontmatter读取正确的name
            try:
                content = filepath.read_text(encoding='utf-8')
            except:
                continue

            # 提取name
            match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
            if match:
                correct_name = match.group(1).strip()
                safe_name = sanitize_filename(correct_name)

                if safe_name and safe_name != filename.rsplit('.md', 1)[0]:
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

    print(f"\n完成: 修复了 {fixed} 个文件")

if __name__ == '__main__':
    main()