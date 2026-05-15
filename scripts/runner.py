#!/usr/bin/env python3
"""
一键执行全流程: scrape → ocr → parse → wiki → qualify
用法: python3 scripts/runner.py [--from STEP]
  STEP: scrape | ocr | parse | wiki | qualify
"""
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
STEPS = ["scrape", "ocr", "parse", "wiki", "qualify"]


def run(script, desc):
    path = SCRIPTS_DIR / script
    if not path.exists():
        print(f"  [SKIP] {script} 不存在")
        return
    print(f"\n{'='*50}\n  {desc}\n{'='*50}")
    result = subprocess.run([sys.executable, str(path)], cwd=str(BASE_DIR),
                            capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("[STDERR]", result.stderr[:500])
    if result.returncode != 0:
        print(f"[WARN] {desc} 退出码: {result.returncode}")


def main():
    start_from = None
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "--from":
        start_from = args[1]

    steps_to_run = STEPS
    if start_from:
        if start_from not in STEPS:
            print(f"未知步骤: {start_from}, 可选: {', '.join(STEPS)}")
            sys.exit(1)
        steps_to_run = STEPS[STEPS.index(start_from):]

    for step in steps_to_run:
        if step == "scrape":
            run("scrape/scrape_amac.py", "Step 1: 爬取 AMAC 网站")
        elif step == "ocr":
            run("ocr/gen_tasks.py", "Step 2: 生成 OCR 任务列表")
            run("ocr/run_batch.py", "Step 2: 批量 OCR")
        elif step == "parse":
            run("parse/parse_txt.py", "Step 3: 解析纪律处分 TXT")
            run("parse/parse_html.py", "Step 3: 解析 HTML 公告")
            run("parse/extract_structured.py", "Step 3: 提取结构化数据")
        elif step == "wiki":
            run("wiki/concept_map.py", "Step 4: 违规→概念映射")
            run("wiki/update_entities.py", "Step 4: 更新 entity 内容")
            run("wiki/create_entities.py", "Step 4: 创建 entity 页面")
            run("wiki/create_modules.py", "Step 4: 创建 module 页面")
            run("wiki/create_concepts.py", "Step 4: 创建 concept 页面")
            run("wiki/create_analysis.py", "Step 4: 创建 analysis 页面")
            run("wiki/create_regulations.py", "Step 4: 创建法规页面")
            run("wiki/update_index.py", "Step 4: 更新 index 和 log")
        elif step == "qualify":
            run("qualify/validate.py", "Step 5: 数据质量验证")
            run("qualify/survey.py", "Step 5: 全量统计")

    print("\n" + "=" * 50)
    print("全流程完成!")


if __name__ == "__main__":
    main()
