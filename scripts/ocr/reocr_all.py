"""
一次性全量修复存量 PDF 的 OCR 输出（300 DPI，全页，纠正错别字）
运行后会覆盖所有 .txt 和 .ocr.txt 文件
用法: python3 scripts/ocr/reocr_all.py [--workers N]
"""
import os
import json
import sys
import time
import uuid
import shutil
import subprocess
from multiprocessing import Pool
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
RAW_DIR = BASE_DIR / "raw" / "纪律处分" / "机构"
TMP_BASE = Path(__file__).parent.parent / "tmp" / "ocr_batch"
FIX_MAP_PATH = Path(__file__).parent.parent / "config" / "ocr_fix_map.json"

# 在模块级别加载纠正规则（避免子进程 import 问题）
with open(FIX_MAP_PATH, 'r', encoding='utf-8') as _f:
    _FIX_RULES = sorted(
        json.load(_f)["rules"],
        key=lambda r: len(r["from"]), reverse=True
    )


def _fix_text(text):
    """应用 OCR 纠正规则"""
    for rule in _FIX_RULES:
        text = text.replace(rule["from"], rule["to"])
    return text


def ocr_one_pdf(pdf_path):
    """对单个 PDF 做 300 DPI 全页 OCR，返回 (文件名, 状态, 详情)"""
    txt_path = pdf_path.with_suffix(".txt")
    ocr_txt_path = Path(str(pdf_path.with_suffix("")) + ".ocr.txt")

    tmp_dir = os.path.join(TMP_BASE, uuid.uuid4().hex[:8])
    os.makedirs(tmp_dir, exist_ok=True)

    try:
        # 获取 PDF 页数
        pages = 1
        try:
            result = subprocess.run(
                ["pdfinfo", str(pdf_path)], capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.split("\n"):
                if line.startswith("Pages:"):
                    pages = int(line.strip().split(":")[1].strip())
                    break
        except Exception:
            pass

        # pdftoppm 全页 300 DPI
        subprocess.run(
            ["pdftoppm", "-png", "-r", "300", str(pdf_path),
             f"{tmp_dir}/page"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180
        )

        # OCR 每页
        full_text = []
        for p in range(1, pages + 1):
            img_file = f"{tmp_dir}/page-{p}.png"
            out_prefix = f"{tmp_dir}/page-{p}"
            if os.path.exists(img_file):
                subprocess.run(
                    ["tesseract", img_file, out_prefix, "-l", "chi_sim"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120
                )
                ocr_out = out_prefix + ".txt"
                if os.path.exists(ocr_out):
                    with open(ocr_out, 'r') as f:
                        full_text.append(f.read())

        if not full_text:
            return (pdf_path.name, "error", "无 OCR 输出")

        combined = "\n".join(full_text)

        # OCR 后处理纠正
        combined = _fix_text(combined)

        # 写入 .txt 和 .ocr.txt
        txt_path.write_text(combined, encoding="utf-8")
        ocr_txt_path.write_text(combined, encoding="utf-8")

        line_count = len(combined.split("\n"))
        return (pdf_path.name, "ok", f"{pages} 页, {line_count} 行")

    except Exception as e:
        return (pdf_path.name, "error", str(e))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main():
    workers = 4
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--workers" and i + 1 < len(args):
            workers = int(args[i + 1])
            i += 2
        else:
            i += 1

    os.makedirs(TMP_BASE, exist_ok=True)

    # 扫描所有 PDF 文件
    pdf_files = sorted(RAW_DIR.glob("*.pdf"))
    print(f"共 {len(pdf_files)} 个 PDF 文件")
    print(f"使用 {workers} 个并行 worker\n")

    ok_count = 0
    error_count = 0
    start_time = time.time()

    with Pool(workers) as pool:
        for i, (name, status, info) in enumerate(pool.imap_unordered(ocr_one_pdf, pdf_files)):
            if status == "ok":
                ok_count += 1
            else:
                error_count += 1
                if error_count <= 5:
                    print(f"  ✗ {name}: {info}", flush=True)

            processed = i + 1
            if processed % 20 == 0 or processed == len(pdf_files):
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = (len(pdf_files) - processed) / rate if rate > 0 else 0
                print(f"[{processed}/{len(pdf_files)}] OK:{ok_count} Err:{error_count} "
                      f"速率:{rate:.1f}/min 剩余:{remaining/60:.0f}min")

            # 打印多页文件的详情
            if status == "ok" and "页" in str(info):
                pages = int(str(info).split("页")[0])
                if pages > 1:
                    print(f"  ✓ {name}: {info}")

    elapsed = time.time() - start_time
    print(f"\n完成! 耗时 {elapsed/60:.1f} 分钟")
    print(f"成功: {ok_count}, 错误: {error_count}")


if __name__ == "__main__":
    main()
