#!/usr/bin/env python3
"""
增量 ingest 调度器.
用法: python3 scripts/incremental_runner.py [--since YYYYMMDD]

流程:
1. 读取 ingest_state.json → 获取各模块上次爬取日期
2. 取各模块中最小的日期作为 --since 传给爬虫
3. 增量爬取 (仅下载新文件)
4. 无新数据则退出, 有新数据则继续
5. 全量重解析 + 重建 wiki + 质检
6. 按模块分别更新最新文件日期
"""
import re
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
STATE_FILE = SCRIPTS_DIR / "tmp" / "ingest_state.json"
RAW_DIR = BASE_DIR / "raw"

# 模块 key → raw 子目录映射（与 scrape_amac.py 保持一致，不含 scfry）
MODULE_SUBDIRS = {
    "scfjg": "纪律处分/机构",
    "ycjy": "异常经营",
    "sljg": "失联机构",
    # "zlcs": "自律措施",  # 数据停更于2020年
}

ACTIVE_MODULES = list(MODULE_SUBDIRS.keys())


def run_py(script_rel, desc):
    path = SCRIPTS_DIR / script_rel
    if not path.exists():
        print(f"  [SKIP] {path} 不存在")
        return True
    print(f"\n{'=' * 50}\n  {desc}\n{'=' * 50}")
    start = time.time()
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(BASE_DIR), capture_output=True, text=True
    )
    elapsed = time.time() - start
    print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
    if result.stderr:
        print("[STDERR]", result.stderr[:500])
    ok = result.returncode == 0
    print(f"  {'OK' if ok else 'FAIL'} ({elapsed:.0f}s)")
    return ok


def extract_date_from_path(filepath):
    """从文件路径提取日期 YYYYMMDD"""
    name = str(filepath)
    m = re.search(r'P0(\d{8})', name)
    if m: return m.group(1)
    m = re.search(r't(\d{8})', name)
    if m: return m.group(1)
    m = re.search(r'/(\d{6})/', name)
    if m: return m.group(1) + '01'
    return '00000000'


def get_module_dates():
    """扫描各模块 raw 子目录，返回 {module_key: latest_date}"""
    dates = {}
    for key, subdir in MODULE_SUBDIRS.items():
        latest = '00000000'
        dir_path = RAW_DIR / subdir
        if dir_path.exists():
            for f in dir_path.iterdir():
                if f.is_file() and f.suffix not in ('.json', '.DS_Store'):
                    d = extract_date_from_path(f)
                    if d > latest:
                        latest = d
        dates[key] = latest
    return dates


def count_raw_files():
    total = 0
    for key, subdir in MODULE_SUBDIRS.items():
        dir_path = RAW_DIR / subdir
        if dir_path.exists():
            total += len([f for f in dir_path.iterdir()
                         if f.is_file() and f.suffix not in ('.json', '.DS_Store')])
    return total


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)
        # 兼容旧格式：如果还是 last_raw_date，迁移为新格式
        if "module_last_dates" not in state and "last_raw_date" in state:
            old_date = state["last_raw_date"]
            state["module_last_dates"] = {k: old_date for k in ACTIVE_MODULES}
            del state["last_raw_date"]
        return state
    return {"last_ingest_time": "", "module_last_dates": {k: "00000000" for k in ACTIVE_MODULES}}


def save_state(module_dates):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "last_ingest_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "module_last_dates": module_dates,
    }
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f"\n状态已更新:")
    for k, v in module_dates.items():
        print(f"  {k}: {v}")


def main():
    # ── 确定起始日期 ──
    since = ''
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == '--since' and i + 1 < len(args):
            since = args[i + 1]
    if not since:
        state = load_state()
        module_dates = state.get("module_last_dates", {})
        # 取各模块中最小的日期，确保不遗漏任一模块的补发数据
        dates = [v for v in module_dates.values() if v != '00000000']
        since = min(dates) if dates else '00000000'
        print(f"读取状态, 各模块日期:")
        for k, v in module_dates.items():
            print(f"  {k}: {v}")
        print(f"  → --since 取最小值: {since}")
    else:
        print(f"手动指定起始日期: {since}")

    # ── 1. 增量爬取 ──
    files_before = count_raw_files()
    if not run_py("scrape/scrape_amac.py", f"Step 1: 增量爬取 (--since {since})"):
        print("爬取失败, 终止")
        sys.exit(1)
    files_after = count_raw_files()
    new_files = files_after - files_before
    print(f"\nraw/ 文件数: {files_before} → {files_after} (+{new_files})")

    # ── 扫描各模块最新文件日期 ──
    new_module_dates = get_module_dates()
    print(f"\n各模块最新文件日期:")
    for k, v in new_module_dates.items():
        print(f"  {k}: {v}")

    if new_files == 0:
        # 没有新文件，但仍更新状态中日期落后的模块（补发场景）
        state = load_state()
        old_dates = state.get("module_last_dates", {})
        updated = False
        for key in ACTIVE_MODULES:
            if new_module_dates.get(key, '00000000') > old_dates.get(key, '00000000'):
                updated = True
        if updated:
            save_state(new_module_dates)
        print("无新增数据, 跳过后续步骤")
        return

    # ── 2. 全量重解析 ──
    run_py("parse/parse_txt.py", "Step 2: 解析纪律处分 TXT")
    run_py("parse/parse_html.py", "Step 2: 解析 HTML 公告")
    run_py("parse/extract_structured.py", "Step 2: 提取结构化数据")

    # ── 3. 重建 wiki ──
    run_py("wiki/concept_map.py", "Step 3: 违规 → 概念映射")
    run_py("wiki/update_entities.py", "Step 3: 更新 entity 内容")
    run_py("wiki/create_entities.py", "Step 3: 创建 entity 页面")
    run_py("wiki/create_modules.py", "Step 3: 创建 module 页面")
    run_py("wiki/create_concepts.py", "Step 3: 创建 concept 页面")
    run_py("wiki/create_analysis.py", "Step 3: 创建 analysis 页面")
    run_py("wiki/create_regulations.py", "Step 3: 创建法规页面")

    # ── 4. 更新索引 + 日志 ──
    log_msg = f"增量更新 | +{new_files} 个新文件 | since={since}"
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "wiki" / "update_index.py"), "--log", log_msg],
        cwd=str(BASE_DIR), capture_output=True, text=True
    )
    print(result.stdout)

    # ── 5. 质检 ──
    run_py("qualify/validate.py", "Step 5: 数据质量验证")

    # ── 6. 更新状态 ──
    save_state(new_module_dates)

    print(f"\n{'=' * 50}")
    print(f"增量 ingest 完成! +{new_files} 个新文件")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
