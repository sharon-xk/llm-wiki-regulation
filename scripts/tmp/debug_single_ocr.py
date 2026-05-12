"""Debug single PDF OCR to understand why batch fails"""
import os
import subprocess
import uuid
import shutil

pdf_path = "/Users/sharon/ai-project/llm-wiki-regulation/raw/纪律处分/人员/202402_P020240208581729425611.pdf"
tmp_base = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/ocr_batch"

tmp_dir = os.path.join(tmp_base, "debug_" + uuid.uuid4().hex[:8])
os.makedirs(tmp_dir, exist_ok=True)

print(f"Tmp dir: {tmp_dir}")

# Get page count
result = subprocess.run(["pdfinfo", pdf_path], capture_output=True, text=True, timeout=10)
pages = 1
for line in result.stdout.split("\n"):
    if line.startswith("Pages:"):
        pages = int(line.strip().split(":")[1].strip())
        break
print(f"PDF pages: {pages}")

# Convert PDF to images
print("Running pdftoppm...")
r = subprocess.run(
    ["pdftoppm", "-png", "-r", "300", pdf_path, os.path.join(tmp_dir, "page")],
    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=180
)
print(f"pdftoppm returncode: {r.returncode}")
if r.stderr:
    print(f"pdftoppm stderr: {r.stderr[:200]}")

# Check images
png_files = sorted([f for f in os.listdir(tmp_dir) if f.endswith('.png')])
print(f"PNG files created: {len(png_files)}")
for pf in png_files:
    png_path = os.path.join(tmp_dir, pf)
    size_kb = os.path.getsize(png_path) / 1024
    print(f"  {pf}: {size_kb:.0f} KB")

# OCR each page
full_text = []
for i in range(1, pages + 1):
    img_file = os.path.join(tmp_dir, f"page-{i}.png")
    txt_file = os.path.join(tmp_dir, f"page-{i}_ocr")
    if os.path.exists(img_file):
        r = subprocess.run(
            ["tesseract", img_file, txt_file, "-l", "chi_sim"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=90
        )
        ocr_txt = txt_file + ".txt"
        if os.path.exists(ocr_txt):
            with open(ocr_txt, 'r') as f:
                text = f.read()
            full_text.append(text)
            print(f"Page {i}: {len(text.split(chr(10)))} lines, returncode={r.returncode}")
        else:
            print(f"Page {i}: NO OUTPUT FILE, returncode={r.returncode}")
            if r.stderr:
                print(f"  stderr: {r.stderr[:200]}")
    else:
        print(f"Page {i}: IMAGE NOT FOUND: {img_file}")

combined = "\n".join(full_text)
print(f"\nTotal lines: {len(combined.split(chr(10)))}")
print(f"Last 3 lines: {combined.split(chr(10))[-3:]}")

shutil.rmtree(tmp_dir, ignore_errors=True)
