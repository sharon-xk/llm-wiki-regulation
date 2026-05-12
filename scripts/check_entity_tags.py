import os
import re

entity_dir = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities"
files = [f for f in os.listdir(entity_dir) if f.endswith('.md')]

tag_counts = {}
for fname in files:
    fpath = os.path.join(entity_dir, fname)
    with open(fpath, 'r') as f:
        content = f.read()
    # extract tags from frontmatter
    match = re.search(r'tags:\s*\[(.*?)\]', content)
    if match:
        tags_str = match.group(1)
        tags = [t.strip().strip('"').strip("'") for t in tags_str.split(',')]
        for t in tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    else:
        tag_counts['(no tags)'] = tag_counts.get('(no tags)', 0) + 1

print(f"Total entity files: {len(files)}")
print()
for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
    print(f"  [{tag}]: {count}")
