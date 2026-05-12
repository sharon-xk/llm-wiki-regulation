import os
import re

entity_dir = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities"
raw_base = "/Users/sharon/ai-project/llm-wiki-regulation/raw/纪律处分"

files = [f for f in os.listdir(entity_dir) if f.endswith('.md')]

pdf_refs = {}  # pdf_path -> list of entity names

for fname in files:
    fpath = os.path.join(entity_dir, fname)
    with open(fpath, 'r') as f:
        content = f.read()

    source_match = re.search(r'\*\*来源\*\*:\s*(\S+)', content)
    if not source_match:
        continue

    source = source_match.group(1)
    pdf_name = source.replace('.txt', '.pdf')

    if 'subtype: 个人' in content:
        subdir = '人员'
    else:
        subdir = '机构'

    pdf_path = os.path.join(raw_base, subdir, pdf_name)
    if pdf_path not in pdf_refs:
        pdf_refs[pdf_path] = []
    pdf_refs[pdf_path].append(fname)

unique_pdfs = len(pdf_refs)
multi_entity_pdfs = {k: v for k, v in pdf_refs.items() if len(v) > 1}

print(f"Total entity files: {len(files)}")
print(f"Unique PDFs to process: {unique_pdfs}")
print(f"Duplication ratio: {len(files)} entities / {unique_pdfs} PDFs = {len(files)/unique_pdfs:.1f}x")
print(f"PDFs shared by multiple entities: {len(multi_entity_pdfs)}")
print(f"Max entities per PDF: {max(len(v) for v in pdf_refs.values())}")

# Distribution
dist = {}
for v in pdf_refs.values():
    n = len(v)
    dist[n] = dist.get(n, 0) + 1
print(f"\nEntity count per PDF distribution:")
for n in sorted(dist.keys()):
    print(f"  {n} entities: {dist[n]} PDFs")

# Estimate OCR time
pages_per_pdf = 3  # conservative estimate
seconds_per_page = 15
seconds_per_pdf = pages_per_pdf * seconds_per_page
total_seconds = unique_pdfs * seconds_per_pdf
total_hours = total_seconds / 3600
print(f"\nEstimated OCR time (sequential):")
print(f"  {unique_pdfs} PDFs x ~{pages_per_pdf} pages x {seconds_per_page}s/page = {total_seconds/3600:.1f} hours")
print(f"  With 4 parallel workers: ~{total_hours/4:.1f} hours")
print(f"  With 8 parallel workers: ~{total_hours/8:.1f} hours")
