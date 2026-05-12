#!/usr/bin/env python3
"""
PDF OCR处理脚本
处理纪律处分/机构和纪律处分/人员目录下的PDF文件
"""
import os
import subprocess
from pathlib import Path

def process_pdf(pdf_path, txt_path):
    """处理单个PDF，返回是否成功"""
    # 先尝试pdftotext
    try:
        result = subprocess.run(
            ['pdftotext', '-layout', str(pdf_path), '-'],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and len(result.stdout.strip()) > 100:
            txt_path.write_text(result.stdout, encoding='utf-8')
            return True, 'pdftotext'
    except Exception:
        pass

    # 尝试OCR
    try:
        img_path = pdf_path.with_suffix('.png')
        subprocess.run(
            ['pdftoppm', '-png', '-singlefile', '-r', '200', str(pdf_path), str(pdf_path.with_suffix(''))],
            capture_output=True, timeout=60
        )
        if img_path.exists():
            ocr_txt_path = pdf_path.with_suffix('.ocr.txt')
            r = subprocess.run(
                ['tesseract', str(img_path), str(ocr_txt_path.with_suffix('')), '-l', 'chi_sim'],
                capture_output=True, text=True, timeout=120
            )
            if ocr_txt_path.exists():
                txt_path.write_text(ocr_txt_path.read_text(encoding='utf-8'), encoding='utf-8')
                img_path.unlink(missing_ok=True)
                return True, 'ocr'
    except Exception:
        pass

    return False, None

def process_directory(dir_path, ext='.pdf'):
    """处理目录下的所有PDF"""
    dir_path = Path(dir_path)
    pdf_files = list(dir_path.glob(f'*{ext}'))

    print(f'目录: {dir_path}')
    print(f'共 {len(pdf_files)} 个文件')

    success = 0
    fail = 0

    for i, pdf_file in enumerate(pdf_files):
        txt_file = pdf_file.with_suffix('.txt')

        # 跳过已存在的非空txt
        if txt_file.exists() and txt_file.stat().st_size > 100:
            continue

        ok, method = process_pdf(pdf_file, txt_file)
        if ok:
            success += 1
            print(f'  [{i+1}/{len(pdf_files)}] OK ({method}): {pdf_file.name[:50]}')
        else:
            fail += 1
            print(f'  [{i+1}/{len(pdf_files)}] FAIL: {pdf_file.name[:50]}')

        # 每50个报告一次进度
        if (i + 1) % 50 == 0:
            print(f'进度: {i+1}/{len(pdf_files)} (成功:{success}, 失败:{fail})')

    print(f'\n完成: 成功 {success}, 失败 {fail}')
    return success, fail

def main():
    base_dir = Path('/Users/sharon/ai-project/llm-wiki-regulation/raw')

    # 处理纪律处分/机构
    print('='*60)
    print('处理纪律处分/机构')
    process_directory(base_dir / '纪律处分/机构')

    # 处理纪律处分/人员
    print('='*60)
    print('处理纪律处分/人员')
    process_directory(base_dir / '纪律处分/人员')

if __name__ == '__main__':
    main()