#!/usr/bin/env python3
"""
AMAC 自律管理处罚信息爬虫 v4
使用 puppeteer 动态获取列表页数据

依赖安装:
    npm install puppeteer-core
    pip install pyppeteer

用法:
    python3 scripts/scrape/scrape_amac.py                  # 全量爬取
    python3 scripts/scrape/scrape_amac.py --since 20260501 # 增量：只下载此日期之后
"""
import os
import re
import sys
import time
import json
import subprocess
import urllib.parse
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent.parent / "raw"


def extract_date_from_url(url):
    """从 URL 提取日期 YYYYMMDD"""
    m = re.search(r'P0(\d{8})', url)
    if m: return m.group(1)
    m = re.search(r't(\d{8})', url)
    if m: return m.group(1)
    m = re.search(r'/(\d{6})/', url)
    if m: return m.group(1) + '01'
    return '00000000'

def extract_text_from_pdf(pdf_path):
    """从 PDF 提取文本"""
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and len(result.stdout.strip()) > 50:
            return result.stdout
    except Exception:
        pass
    return None

def ocr_pdf(pdf_path):
    """OCR 扫描版 PDF（全页 300 DPI）"""
    import tempfile
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

        # 转图片（所有页，300 DPI）
        with tempfile.TemporaryDirectory() as tmp_dir:
            subprocess.run(
                ["pdftoppm", "-png", "-r", "300", str(pdf_path),
                 f"{tmp_dir}/page"],
                capture_output=True, timeout=180
            )

            # OCR 每页
            full_text = []
            for p in range(1, pages + 1):
                img_file = f"{tmp_dir}/page-{p}.png"
                txt_file = f"{tmp_dir}/page-{p}"
                if os.path.exists(img_file):
                    subprocess.run(
                        ["tesseract", img_file, txt_file, "-l", "chi_sim"],
                        capture_output=True, text=True, timeout=120
                    )
                    ocr_out = txt_file + ".txt"
                    if os.path.exists(ocr_out):
                        with open(ocr_out, 'r') as f:
                            full_text.append(f.read())

            if not full_text:
                return None

            text = "\n".join(full_text)

            # OCR 后处理纠正
            from scripts.ocr.fix_ocr import fix_ocr_text
            text = fix_ocr_text(text)

            # 写入 .ocr.txt
            ocr_txt_path = pdf_path.with_suffix(".ocr.txt")
            ocr_txt_path.write_text(text, encoding="utf-8")
            return text
    except Exception as e:
        print(f"    OCR 失败: {e}")
    return None

def download_file(url, save_path):
    """下载文件"""
    if save_path.exists() and save_path.stat().st_size > 100:
        return True

    cmd = [
        "curl", "-s", "-L", "--max-time", "60",
        "-o", str(save_path),
        url
    ]
    result = subprocess.run(cmd, capture_output=True)
    return save_path.exists() and save_path.stat().st_size > 100

def get_all_links():
    """使用 puppeteer 获取所有模块的链接"""
    try:
        from pyppeteer import launch
    except ImportError:
        print("请安装 pyppeteer: pip install pyppeteer")
        return None

    modules = [
        ("scfjg", "https://www.amac.org.cn/zlgl/jlcf/scfjg/", "zlgl/jlcf/scfjg/", ".pdf"),
        # ("scfry", "https://www.amac.org.cn/zlgl/jlcf/scfry/", "zlgl/jlcf/scfry/", ".pdf"),
        ("ycjy", "https://www.amac.org.cn/zlgl/ycjy/ycjyjgclgg/", "zlgl/ycjy/ycjyjgclgg/", ".html"),
        ("sljg", "https://www.amac.org.cn/zlgl/sljg/sljgclgg/", "zlgl/sljg/sljgclgg/", ".html"),
        # ("zlcs", "https://www.amac.org.cn/zlgl/zlcs/", "zlgl/zlcs/", ".html"),  # 自律措施数据停更于2020年
    ]

    all_links = {}

    async def run():
        browser = await launch(
            headless=True,
            executablePath='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        for key, base_url, pattern, ext in modules:
            print(f"\n=== {key} ===")

            page = await browser.newPage()
            await page.goto(base_url, {'waitUntil': 'networkidle2', 'timeout': 30000})

            # 获取总页数
            page_count = await page.evaluate('''() => {
                const links = document.querySelectorAll('a[href*="index_"]');
                let max = 0;
                links.forEach(l => {
                    const m = l.href.match(/index_(\d+)\.html/);
                    if (m) max = Math.max(max, parseInt(m[1]));
                });
                return max;
            }''')
            print(f"Pages: 0-{page_count}")

            links = []

            # 抓取每一页
            for p in range(page_count + 1):
                page_url = base_url if p == 0 else f"{base_url}index_{p}.html"
                p_obj = await browser.newPage()
                await p_obj.goto(page_url, {'waitUntil': 'networkidle2', 'timeout': 15000})

                page_links = await p_obj.evaluate(f'''(filterStr, ext) => {{
                    const as = document.querySelectorAll('a[href]');
                    return Array.from(as)
                        .map(a => a.href)
                        .filter(href => href.includes(filterStr) && href.endsWith(ext));
                }}''', pattern, ext)

                links.extend(page_links)
                await p_obj.close()

                if len(page_links) == 0 and p > 0:
                    break

            all_links[key] = list(set(links))
            print(f"Found {len(all_links[key])} links")

            await page.close()

        await browser.close()

    import asyncio
    asyncio.get_event_loop().run_until_complete(run())

    return all_links

def process_module(module_key, links, subdir, ext):
    """处理单个模块的下载和OCR"""
    print(f"\n{'='*60}")
    print(f"模块: {module_key}, 文件数: {len(links)}")

    save_dir = OUTPUT_DIR / subdir
    os.makedirs(save_dir, exist_ok=True)
    # PDF 模块：原始文件存入 pdf/，OCR 产物存入 txt/，分离原始数据与处理产物
    pdf_dir = save_dir / "pdf"
    txt_dir = save_dir / "txt"
    if ext == '.pdf':
        os.makedirs(pdf_dir, exist_ok=True)
        os.makedirs(txt_dir, exist_ok=True)

    results = []
    for i, url in enumerate(links):
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        filename = path.split('/')[-1]
        dir_prefix = path.split('/')[-2]
        # PDF 存入 pdf/ 子目录，HTML 仍存栏目目录
        file_dir = pdf_dir if ext == '.pdf' else save_dir
        dest = file_dir / f"{dir_prefix}_{filename}"

        print(f"\n  [{i+1}/{len(links)}] {filename[:50]}")

        # 下载文件
        if download_file(url, dest):
            if ext == '.pdf':
                # 尝试提取文本
                text = extract_text_from_pdf(dest)
                if text and len(text.strip()) > 50:
                    txt_path = txt_dir / (dest.stem + '.txt')
                    txt_path.write_text(text, encoding='utf-8')
                    print(f"    [OK] pdftotext ({len(text)} 字)")
                    results.append({"status": "success", "file": str(dest)})
                else:
                    # 尝试 OCR
                    print(f"    [无文字层，OCR...]")
                    text = ocr_pdf(dest)
                    if text and len(text.strip()) > 50:
                        txt_path = txt_dir / (dest.stem + '.txt')
                        txt_path.write_text(text, encoding='utf-8')
                        print(f"    [OK] OCR ({len(text)} 字)")
                        results.append({"status": "success", "file": str(dest), "is_ocr": True})
                    else:
                        print(f"    [扫描件]")
                        results.append({"status": "scan_only", "file": str(dest)})
            elif ext == '.html':
                print(f"    [OK] HTML 已保存")
                results.append({"status": "success", "file": str(dest)})
        else:
            print(f"    [下载失败]")
            results.append({"status": "download_failed"})

        time.sleep(0.2)

    return results

def main():
    print("=" * 60)
    print("AMAC 自律管理处罚信息爬虫 v4")
    print("=" * 60)

    # 解析 --since 参数
    since = ''
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == '--since' and i + 1 < len(args):
            since = args[i + 1]
    if since:
        print(f"\n增量模式: 仅下载日期 > {since} 的文件")

    # 获取所有链接
    print("\n获取列表页链接...")
    all_links = get_all_links()

    if not all_links:
        print("获取链接失败")
        sys.exit(1)

    # 按日期过滤（增量模式）
    if since:
        total_before = sum(len(v) for v in all_links.values())
        for key in all_links:
            before = len(all_links[key])
            all_links[key] = [url for url in all_links[key] if extract_date_from_url(url) >= since]
            after = len(all_links[key])
            if before != after:
                print(f"  {key}: {before} -> {after} (过滤 {before - after} 条)")
        total_after = sum(len(v) for v in all_links.values())
        print(f"  合计: {total_before} -> {total_after}")

    # 保存链接
    links_file = OUTPUT_DIR / "all_amac_links.json"
    with open(links_file, 'w', encoding='utf-8') as f:
        json.dump(all_links, f, ensure_ascii=False, indent=2)
    print(f"链接已保存: {links_file}")

    # 处理每个模块
    modules = [
        ("纪律处分_机构", all_links.get("scfjg", []), "纪律处分/机构", ".pdf"),
        # ("纪律处分_人员", all_links.get("scfry", []), "纪律处分/人员", ".pdf"),
        ("异常经营", all_links.get("ycjy", []), "异常经营", ".html"),
        ("失联机构", all_links.get("sljg", []), "失联机构", ".html"),
        # ("自律措施", all_links.get("zlcs", []), "自律措施", ".html"),  # 自律措施数据停更于2020年
    ]

    all_results = {}
    for module_key, links, subdir, ext in modules:
        results = process_module(module_key, links, subdir, ext)
        all_results[module_key] = results
        time.sleep(1)

    # 打印汇总
    print("\n" + "=" * 60)
    print("汇总报告：")
    total = 0
    for mk, rs in all_results.items():
        ok = sum(1 for r in rs if r.get("status") == "success")
        scan = sum(1 for r in rs if r.get("status") == "scan_only")
        print(f"  {mk}: {len(rs)} 条 (成功:{ok} 扫描件:{scan})")
        total += len(rs)
    print(f"\n总计: {total} 条")

    # 保存摘要
    summary_path = OUTPUT_DIR / "scrape_summary_v4.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"摘要已保存: {summary_path}")

if __name__ == "__main__":
    main()