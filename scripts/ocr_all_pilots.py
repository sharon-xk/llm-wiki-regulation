import subprocess
import os

pilots = [
    {"name": "上海极溉", "pdf": "raw/纪律处分/机构/202504_P020250430571512616428.pdf"},
    {"name": "杭州锦元", "pdf": "raw/纪律处分/机构/202409_P020240920542124169220.pdf"},
    {"name": "曹辉", "pdf": "raw/纪律处分/人员/202512_P020251231660906002817.pdf"},
    {"name": "河北建邦", "pdf": "raw/纪律处分/机构/202403_P020240301591809631988.pdf"},
]

base_dir = "/Users/sharon/ai-project/llm-wiki-regulation"
tmp_dir = os.path.join(base_dir, "scripts/tmp")

for p in pilots:
    name = p["name"]
    pdf_path = os.path.join(base_dir, p["pdf"])
    ocr_dir = os.path.join(tmp_dir, f"ocr_{name}")
    os.makedirs(ocr_dir, exist_ok=True)

    # Get page count
    result = subprocess.run(
        ["pdfinfo", pdf_path], capture_output=True, text=True
    )
    pages = 1
    for line in result.stdout.split("\n"):
        if line.startswith("Pages:"):
            pages = int(line.strip().split(":")[1].strip())
            break

    print(f"{name}: {pages} pages, converting to images...")

    # Convert PDF to images
    subprocess.run(
        ["pdftoppm", "-png", "-r", "300", pdf_path,
         os.path.join(ocr_dir, "page")],
        capture_output=True
    )

    # OCR each page
    full_text = []
    for i in range(1, pages + 1):
        img_file = os.path.join(ocr_dir, f"page-{i}.png")
        txt_file = os.path.join(ocr_dir, f"page-{i}_ocr")
        if os.path.exists(img_file):
            subprocess.run(
                ["tesseract", img_file, txt_file, "-l", "chi_sim"],
                capture_output=True
            )
            with open(txt_file + ".txt", "r") as f:
                full_text.append(f.read())

    # Write combined text
    output_path = os.path.join(tmp_dir, f"{name}_full.txt")
    with open(output_path, "w") as f:
        f.write("\n".join(full_text))

    line_count = sum(len(t.split("\n")) for t in full_text)
    print(f"  Done: {line_count} lines -> {output_path}")
    print()

print("All pilots OCR complete.")
