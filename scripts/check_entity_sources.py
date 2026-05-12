import os
import re

entity_dir = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities"
files = [f for f in os.listdir(entity_dir) if f.endswith('.md')]

# Check for any references to other categories in content
other_cats = ['异常经营', '失联机构', '自律措施']
found_other = False

for fname in files:
    fpath = os.path.join(entity_dir, fname)
    with open(fpath, 'r') as f:
        content = f.read()
    for cat in other_cats:
        if cat in content:
            print(f"  {fname}: contains '{cat}'")
            found_other = True

if not found_other:
    print("所有 entity 文件中未发现引用 '异常经营'、'失联机构'、'自律措施'")

# Also check tags more thoroughly
all_tags = set()
for fname in files:
    fpath = os.path.join(entity_dir, fname)
    with open(fpath, 'r') as f:
        content = f.read()
    match = re.search(r'tags:\s*\[(.*?)\]', content)
    if match:
        tags_str = match.group(1)
        tags = [t.strip().strip('"').strip("'") for t in tags_str.split(',')]
        for t in tags:
            all_tags.add(t)

print(f"\n所有 tag 值: {all_tags}")
print(f"entity 总数: {len(files)}")
