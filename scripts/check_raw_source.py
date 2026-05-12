import json

with open("/Users/sharon/ai-project/llm-wiki-regulation/raw/parsed_txt_results.json", "r") as f:
    d = json.load(f)

# Find 尹伟霖 entry
for key in ['纪律处分_人员', '纪律处分_机构']:
    for item in d.get(key, []):
        if '尹伟霖' in str(item):
            print(json.dumps(item, ensure_ascii=False, indent=2)[:3000])
            print('---')
            break
