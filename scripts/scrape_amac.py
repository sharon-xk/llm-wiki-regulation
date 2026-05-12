#!/usr/bin/env python3
"""
AMAC 自律管理处罚信息爬虫 v4
使用 puppeteer 动态获取列表页数据
"""

import os
import re
import time
import json
import subprocess
import urllib.parse
from pathlib import Path

# 需要先安装: npm install puppeteer-core
try:
    from pyppeteer import launch
except ImportError:
    print("请安装 pyppeteer: pip install pyppeteer")
    import sys
    sys.exit(1)

OUTPUT_DIR = Path(__file__).parent.parent / "raw"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


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
    """OCR 扫描版 PDF"""
    try:
        img_path = pdf_path.with_suffix(".png")
        subprocess.run(
            ["pdftoppm", "-png", "-singlefile", "-r", "200", str(pdf_path), str(pdf_path.with_suffix(""))],
            capture_output=True, timeout=60
        )
        if not img_path.exists():
            return None

        txt_path = pdf_path.with_suffix(".ocr.txt")
        r = subprocess.run(
            ["tesseract", str(img_path), str(txt_path.with_suffix("")), "-l", "chi_sim"],
            capture_output=True, text=True, timeout=120
        )
        if txt_path.exists():
            text = txt_path.read_text(encoding="utf-8")
            img_path.unlink(missing_ok=True)
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
        "-A", HEADERS["User-Agent"],
        "-o", str(save_path),
        url
    ]
    result = subprocess.run(cmd, capture_output=True)
    return save_path.exists() and save_path.stat().st_size > 100


def get_page_links(browser, url, pattern, ext):
    """获取分页的所有链接"""
    from pyppeteer import launch

    all_links = []

    # 获取总页数
    page = await browser.newPage()
    await page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 30000})

    page_count = await page.evaluate('''() => {
        const links = document.querySelectorAll('a[href*="index_"]');
        let max = 0;
        links.forEach(l => {
            const m = l.href.match(/index_(\d+)\.html/);
            if (m) max = Math.max(max, parseInt(m[1]));
        });
        return max;
    }''')

    await page.close()

    # 抓取每一页
    for p in range(page_count + 1):
        page_url = url if p == 0 else f"{url}index_{p}.html"
        page_obj = await browser.newPage()
        await page_obj.goto(page_url, {'waitUntil': 'networkidle2', 'timeout': 15000})

        links = await page.evaluate(f'''(filterStr, ext) => {{
            const as = document.querySelectorAll('a[href]');
            return Array.from(as)
                .map(a => a.href)
                .filter(href => href.includes(filterStr) && href.endsWith(ext));
        }}''', pattern, ext)

        all_links.extend(links)
        await page_obj.close()

        if len(links) == 0 and p > 0:
            break

    return list(set(all_links))


async def process_module(module_key, base_url, pattern, subdir, ext):
    """处理单个模块"""
    print(f"\n{'='*60}")
    print(f"模块: {module_key}")
    print(f"URL: {base_url}")

    save_dir = OUTPUT_DIR / subdir
    os.makedirs(save_dir, exist_ok=True)

    # 获取所有链接
    browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
    links = await get_page_links(browser, base_url, pattern, ext)
    await browser.close()

    print(f"  发现 {len(links)} 条链接")

    results = []
    for i, url in enumerate(links):
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        filename = path.split('/')[-1]
        dir_prefix = path.split('/')[-2]
        dest = save_dir / f"{dir_prefix}_{filename}"

        print(f"\n  [{i+1}/{len(links)}] {filename[:50]}")

        # 下载文件
        if ext == '.pdf':
            if download_file(url, dest):
                # 尝试提取文本
                text = extract_text_from_pdf(dest)
                if text and len(text.strip()) > 50:
                    txt_path = dest.with_suffix('.txt')
                    txt_path.write_text(text, encoding='utf-8')
                    print(f"    [OK] pdftotext ({len(text)} 字)")
                    results.append({"status": "success", "file": str(dest)})
                else:
                    # 尝试 OCR
                    print(f"    [无文字层，OCR...]")
                    text = ocr_pdf(dest)
                    if text and len(text.strip()) > 50:
                        txt_path = dest.with_suffix('.txt')
                        txt_path.write_text(text, encoding='utf-8')
                        print(f"    [OK] OCR ({len(text)} 字)")
                        results.append({"status": "success", "file": str(dest), "is_ocr": True})
                    else:
                        print(f"    [扫描件]")
                        results.append({"status": "scan_only", "file": str(dest)})
            else:
                print(f"    [下载失败]")
                results.append({"status": "download_failed"})

        elif ext == '.html':
            if download_file(url, dest):
                print(f"    [OK] HTML 已保存")
                results.append({"status": "success", "file": str(dest)})
            else:
                print(f"    [下载失败]")
                results.append({"status": "download_failed"})

        time.sleep(0.3)

    return results


async def main():
    print("=" * 60)
    print("AMAC 自律管理处罚信息爬虫 v4")
    print("=" * 60)

    modules = [
        ("纪律处分_机构", "https://www.amac.org.cn/zlgl/jlcf/scfjg/", "zlgl/jlcf/scfjg/", "纪律处分/机构", ".pdf"),
        ("纪律处分_人员", "https://www.amac.org.cn/zlgl/jlcf/scfry/", "zlgl/jlcf/scfry/", "纪律处分/人员", ".pdf"),
        ("异常经营", "https://www.amac.org.cn/zlgl/ycjy/ycjyjgclgg/", "zlgl/ycjy/ycjyjgclgg/", "异常经营", ".html"),
        ("失联机构", "https://www.amac.org.cn/zlgl/sljg/sljgclgg/", "zlgl/sljg/sljgclgg/", "失联机构", ".html"),
        ("自律措施", "https://www.amac.org.cn/zlgl/zlcs/", "zlgl/zlcs/", "自律措施", ".html"),
    ]

    all_results = {}

    for module_key, base_url, pattern, subdir, ext in modules:
        results = await process_module(module_key, base_url, pattern, subdir, ext)
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
    import asyncio
    asyncio.get_event_loop().run_until_complete(main())