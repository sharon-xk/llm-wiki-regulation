import os

base = "/Users/sharon/ai-project/llm-wiki-regulation/raw"
categories = ["纪律处分", "异常经营", "失联机构", "自律措施"]

for cat in categories:
    cat_path = os.path.join(base, cat)
    if not os.path.isdir(cat_path):
        print(f"=== {cat}: 目录不存在 ===")
        continue

    print(f"=== {cat} ===")
    subdirs = [d for d in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, d))]
    print(f"子目录: {subdirs}")

    total_txt = 0
    total_pdf = 0
    for sub in subdirs:
        sub_path = os.path.join(cat_path, sub)
        txt_count = len([f for f in os.listdir(sub_path) if f.endswith('.txt')])
        pdf_count = len([f for f in os.listdir(sub_path) if f.endswith('.pdf')])
        total_txt += txt_count
        total_pdf += pdf_count
        print(f"  {sub}: {txt_count} TXT, {pdf_count} PDF")

    # sample a few txt files to check completeness
    if subdirs:
        sample_sub = subdirs[0]
        sample_path = os.path.join(cat_path, sample_sub)
        txt_files = [f for f in os.listdir(sample_path) if f.endswith('.txt')]
        if txt_files:
            # read first 3 txt files, check last line
            for fname in txt_files[:3]:
                fpath = os.path.join(sample_path, fname)
                with open(fpath, 'r') as fp:
                    lines = fp.readlines()
                last = lines[-1].strip() if lines else "(empty)"
                print(f"    {fname}: {len(lines)} lines, last: {last[:80]}")
    print()
