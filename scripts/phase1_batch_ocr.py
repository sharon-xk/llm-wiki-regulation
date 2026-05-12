"""
阶段1: 批量 PDF OCR，覆盖原始 TXT 文件
用法: python3 phase1_batch_ocr.py [--workers N] [--limit N]
"""
import os
import re
import subprocess
import shutil
import sys
import time
import uuid
from multiprocessing import Pool

ENTITY_DIR = "/Users/sharon/ai-project/llm-wiki-regulation/wiki/entities"
RAW_BASE = "/Users/sharon/ai-project/llm-wiki-regulation/raw/纪律处分"
TMP_BASE = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/ocr_batch"


def get_pdf_txt_pairs():
    """从 entity 文件中提取 (pdf_path, txt_path) 配对"""
    pairs = []
    entity_files = sorted([f for f in os.listdir(ENTITY_DIR) if f.endswith('.md')])
    for fname in entity_files:
        fpath = os.path.join(ENTITY_DIR, fname)
        with open(fpath, 'r') as f:
            content = f.read()

        source_match = re.search(r'\*\*来源\*\*:\s*(\S+)', content)
        if not source_match:
            continue

        source = source_match.group(1)
        txt_name = source  # e.g., "202504_P020250411568047688933.txt"
        pdf_name = source.replace('.txt', '.pdf')

        if 'subtype: 个人' in content:
            subdir = '人员'
        else:
            subdir = '机构'

        pdf_path = os.path.join(RAW_BASE, subdir, pdf_name)
        txt_path = os.path.join(RAW_BASE, subdir, txt_name)

        if os.path.exists(pdf_path):
            pairs.append((pdf_path, txt_path, fname))

    return pairs


def ocr_one_pdf(args):
    """处理单个 PDF，OCR 结果写入目标 TXT 文件"""
    pdf_path, txt_path, entity_name = args

    # 如果 TXT 已有完整内容（>50行），跳过
    if os.path.exists(txt_path):
        with open(txt_path, 'r') as f:
            existing_lines = len(f.readlines())
        if existing_lines > 50:
            return (entity_name, "skip", f"已有 {existing_lines} 行，跳过")

    tmp_dir = os.path.join(TMP_BASE, uuid.uuid4().hex[:8])
    os.makedirs(tmp_dir, exist_ok=True)

    try:
        # 获取 PDF 页数
        result = subprocess.run(
            ["pdfinfo", pdf_path], capture_output=True, text=True, timeout=10
        )
        pages = 1
        for line in result.stdout.split("\n"):
            if line.startswith("Pages:"):
                try:
                    pages = int(line.strip().split(":")[1].strip())
                except ValueError:
                    pass
                break

        # 转换 PDF 为图片 (忽略输出避免管道阻塞)
        subprocess.run(
            ["pdftoppm", "-png", "-r", "300", pdf_path,
             os.path.join(tmp_dir, "page")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180
        )

        # OCR 每页
        full_text = []
        for i in range(1, pages + 1):
            img_file = os.path.join(tmp_dir, f"page-{i}.png")
            txt_file = os.path.join(tmp_dir, f"page-{i}_ocr")
            if os.path.exists(img_file):
                subprocess.run(
                    ["tesseract", img_file, txt_file, "-l", "chi_sim"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=90
                )
                ocr_txt = txt_file + ".txt"
                if os.path.exists(ocr_txt):
                    with open(ocr_txt, 'r') as f:
                        full_text.append(f.read())

        # 写入目标 TXT
        combined = "\n".join(full_text)
        with open(txt_path, 'w') as f:
            f.write(combined)

        line_count = len(combined.split("\n"))
        return (entity_name, "ok", f"{pages} 页, {line_count} 行")

    except Exception as e:
        return (entity_name, "error", str(e))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main():
    workers = 4
    limit = 0  # 0 means all

    # parse args
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--workers" and i + 1 < len(args):
            workers = int(args[i + 1])
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        else:
            i += 1

    os.makedirs(TMP_BASE, exist_ok=True)

    pairs = get_pdf_txt_pairs()
    total = len(pairs)
    print(f"共 {total} 个 PDF 待处理")

    if limit > 0:
        pairs = pairs[:limit]
        print(f"限制处理前 {limit} 个")

    print(f"使用 {workers} 个并行 worker\n")

    ok_count = 0
    skip_count = 0
    error_count = 0
    processed = 0
    start_time = time.time()

    with Pool(workers) as pool:
        for (name, status, info) in pool.imap_unordered(ocr_one_pdf, pairs):
            processed += 1
            if status == "ok":
                ok_count += 1
            elif status == "skip":
                skip_count += 1
            else:
                error_count += 1

            if processed % 50 == 0 or processed == len(pairs):
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = (len(pairs) - processed) / rate if rate > 0 else 0
                print(f"[{processed}/{len(pairs)}] "
                      f"OK:{ok_count} Skip:{skip_count} Err:{error_count} "
                      f"速率:{rate:.1f}/min 剩余:{remaining/60:.0f}min")

    elapsed = time.time() - start_time
    print(f"\n完成! 耗时 {elapsed/60:.1f} 分钟")
    print(f"成功: {ok_count}, 跳过: {skip_count}, 错误: {error_count}")

    if error_count > 0:
        print("注意: 有处理错误，请检查上述输出")


if __name__ == "__main__":
    main()
