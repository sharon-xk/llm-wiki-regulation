#!/usr/bin/env python3
"""运行修复后的脚本，重新生成全部wiki页面"""
import subprocess
import sys
from pathlib import Path

base_dir = Path('/Users/sharon/ai-project/llm-wiki-regulation')

print("=" * 50)
print("Step 1: 重新解析TXT文件")
print("=" * 50)
result = subprocess.run([sys.executable, 'parse_txt.py'], cwd=base_dir / 'scripts', capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)

print("\n" + "=" * 50)
print("Step 2: 重新生成实体页和模块页")
print("=" * 50)
result = subprocess.run([sys.executable, 'create_wiki.py'], cwd=base_dir / 'scripts', capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)

print("\n" + "=" * 50)
print("Step 3: 重新生成概念页和分析页")
print("=" * 50)
result = subprocess.run([sys.executable, 'create_concepts_analysis_v2.py'], cwd=base_dir / 'scripts', capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)

print("\n" + "=" * 50)
print("完成! 请检查生成的wiki页面")
print("=" * 50)