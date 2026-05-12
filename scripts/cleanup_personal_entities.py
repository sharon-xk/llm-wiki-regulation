"""删除所有个人类型的 entity 文件"""
import os
import re

entity_dir = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities"

personal = []
institutional = []

for fname in os.listdir(entity_dir):
    if not fname.endswith('.md'):
        continue
    fpath = os.path.join(entity_dir, fname)
    with open(fpath, 'r') as f:
        content = f.read()
    if 'subtype: 个人' in content:
        personal.append(fpath)
    else:
        institutional.append(fname)

print(f"个人 entity: {len(personal)} 个 → 删除")
print(f"机构 entity: {len(institutional)} 个 → 保留")

for fpath in personal:
    os.remove(fpath)

print(f"\n已删除 {len(personal)} 个个人 entity 文件")
print(f"保留 {len(institutional)} 个机构 entity 文件")
