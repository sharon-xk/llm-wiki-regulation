import json

with open("/Users/sharon/ai-project/llm-wiki-regulation/raw/parsed_txt_results.json", "r") as f:
    d = json.load(f)

print("Keys:", list(d.keys()))
print()

# Show structure of each key
for key in d:
    items = d[key]
    print(f"=== {key}: type={type(items).__name__} ===")
    if isinstance(items, dict):
        sample_keys = list(items.keys())[:3]
        print(f"Sample keys: {sample_keys}")
        if sample_keys:
            k0 = sample_keys[0]
            print(f"First key: {k0}")
            print(f"First value: {json.dumps(items[k0], ensure_ascii=False, indent=2)[:2000]}")
    elif isinstance(items, list):
        print(f"Length: {len(items)}")
        if items:
            print(json.dumps(items[0], ensure_ascii=False, indent=2)[:2000])
    print()
