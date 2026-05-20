"""
OCR 后处理：根据 ocr_fix_map.json 纠正高频错别字
用于 scrape_amac.py 和 run_batch.py 的 OCR 输出后处理
"""
import json
from pathlib import Path

_MAP_PATH = Path(__file__).parent.parent / "config" / "ocr_fix_map.json"
_RULES = None


def _load_rules():
    global _RULES
    if _RULES is None:
        with open(_MAP_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 按 from 长度降序排列，长词优先替换，避免短词误伤长词子串
        _RULES = sorted(data["rules"], key=lambda r: len(r["from"]), reverse=True)


def fix_ocr_text(text):
    """对 OCR 输出文本执行错别字纠正"""
    if not text:
        return text
    _load_rules()
    for rule in _RULES:
        text = text.replace(rule["from"], rule["to"])
    return text
