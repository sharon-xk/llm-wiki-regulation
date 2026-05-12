import os, re, json

ENTITY_DIR = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities"
PARSED = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/parsed_data_with_concepts.json"

bad = []
for fname in sorted(os.listdir(ENTITY_DIR)):
    if not fname.endswith('.md'):
        continue
    if '以下简称' in fname or '简称' in fname:
        fpath = os.path.join(ENTITY_DIR, fname)
        with open(fpath) as f:
            content = f.read()
        m = re.search(r'name:\s*(.+)', content)
        fm_name = m.group(1).strip() if m else 'N/A'
        bad.append((fname, fm_name))
        print(f"FILE: {fname}")
        print(f"  FM name: {fm_name}")
        print()

print(f"Total: {len(bad)}")
