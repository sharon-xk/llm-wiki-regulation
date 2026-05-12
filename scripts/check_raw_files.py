import os

# Check line counts of raw txt files
for subdir in ['机构', '人员']:
    path = f'/Users/sharon/ai-project/llm-wiki-regulation/raw/纪律处分/{subdir}'
    files = [f for f in os.listdir(path) if f.endswith('.txt')]

    # Line count distribution
    line_counts = {}
    for f in files[:200]:  # sample first 200
        fpath = os.path.join(path, f)
        with open(fpath, 'r') as fp:
            n_lines = len(fp.readlines())
        line_counts[n_lines] = line_counts.get(n_lines, 0) + 1

    print(f"=== {subdir}: {len(files)} total txt files, sampling first 200 ===")
    for n, count in sorted(line_counts.items()):
        print(f"  {n} lines: {count} files")
    print()
