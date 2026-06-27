"""
阶段2: 从 OCR TXT 文件中提取违规行为结构化数据

职责：读取已建的机构页（institutions/）及其引用的原始 TXT，深度提取每条处罚的
      违规行为、字号、处罚措施、法规依据等结构化字段，输出 parsed_data.json，
      供 map_violations.py 做违规类型映射。

输入：wiki/institutions/*.md + raw/纪律处分/机构/txt/*.txt
输出：scripts/tmp/parsed_data.json

依赖：须在 parse_txt.py + create_institutions.py 之后运行（需要已建的机构页）。
"""
import os
import re
import json
from pathlib import Path

RAW_BASE = str(Path(__file__).parent.parent.parent / "raw" / "纪律处分")
ENTITY_DIR = str(Path(__file__).parent.parent.parent / "wiki" / "institutions")
OUTPUT = str(Path(__file__).parent.parent / "tmp" / "parsed_data.json")


def extract_case_number(text):
    """提取字号，如 中基协处分(2025)30号"""
    m = re.search(r'中基协[处分复核]+[(\[（]\s*(\d{4})\s*[)\]}】]\s*(\d+)\s*号', text)
    if m:
        return f"中基协处分({m.group(1)}){m.group(2)}号"
    # alternative patterns
    m = re.search(r'中基协[处分复核]+.*?(\d{4}).*?(\d+)\s*号', text)
    if m:
        return f"中基协处分({m.group(1)}){m.group(2)}号"
    return ""


def extract_date_from_filename(txt_name):
    """从文件名提取日期 P020250411 -> 2025-04-11"""
    m = re.search(r'P0(\d{4})(\d{2})(\d{2})', txt_name)
    if m:
        y = m.group(1)
        mo = m.group(2)
        d = m.group(3)
        return f"{y}-{mo}-{d}"
    return ""


def split_violations(violation_text):
    """将违规行为文本拆分为独立条目"""
    items = []

    # 尝试按 (一)(二)(三) 拆分
    parts = re.split(r'(?:^|\n)\s*[(（]([一二三四五六七八九十]+)[)）]', violation_text)
    if len(parts) > 1:
        # parts = [before, '一', 'content1', '二', 'content2', ...]
        for i in range(1, len(parts), 2):
            num = parts[i]
            content = parts[i + 1] if i + 1 < len(parts) else ""
            content = re.sub(r'\s+', ' ', content).strip()
            if len(content) > 5:
                items.append(f"({num}) {content}")
        if items:
            return items

    # 尝试按 一是/二是/三是 拆分
    parts = re.split(r'(?:(?:^|\n)\s*|\s+)([一二三四五六七八九十]+是)\s*', violation_text)
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            num = parts[i]
            content = parts[i + 1] if i + 1 < len(parts) else ""
            content = re.sub(r'\s+', ' ', content).strip()
            if len(content) > 5:
                items.append(f"{num} {content}")
        if items:
            return items

    # 无法拆分，返回整体
    cleaned = re.sub(r'\s+', ' ', violation_text).strip()
    if len(cleaned) > 10:
        items.append(cleaned)
    return items


def extract_penalty(text):
    """提取处罚措施"""
    # 定位纪律处分决定后的内容
    patterns = [
        r'[二三][、.]\s*(?:纪律)?处分决定.*?协会决定[作做]出以下[纪律处分]*[：:]\s*(.*?)(?:根据《[实施办]|$)',
        r'协会决定[作做]出以下[纪律处分]*[：:]\s*(.*?)(?:根据《[实施办]|抄送|$)',
        r'[二三][、.]\s*审理意见.*?协会决定[作做]出以下[纪律处分]*[：:]\s*(.*?)(?:根据《[实施办]|$)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL)
        if m:
            penalty = m.group(1).strip()
            # Clean up
            penalty = re.sub(r'\s+', ' ', penalty)
            penalty = re.sub(r'\d+\s*$', '', penalty).strip()
            if len(penalty) > 2:
                return penalty
    return ""


def extract_legal_basis(text):
    """提取法规依据"""
    laws = []
    for law in ['《基金法》', '《私募基金监管办法》', '《私募投资基金监督管理暂行办法》',
                 '《实施办法》', '《协会章程》', '《会员管理办法》',
                 '《私募投资基金登记备案办法》', '《私募投资基金信息披露管理办法》',
                 '《私募投资基金募集行为管理办法》', '《私募投资基金管理人内部控制指引》',
                 '《关于加强私募投资基金监管的若干规定》',
                 '《私募投资基金备案须知》', '《中国证券投资基金业协会自律检查规则》']:
        if law in text:
            laws.append(law)
    return '、'.join(laws) if laws else '《基金法》《私募基金监管办法》《实施办法》'


def extract_violation_section(text):
    """提取违规行为段落"""
    # 找到"基本事实"段
    start_patterns = [
        r'一[、.]\s*基本事实\s*\n(.*?)(?=二[、.]|$)',  # 标准结构
        r'一[、.]\s*(?:事先告知情况|基本事实)\s*\n(.*?)(?=二[、.]|三[、.]|$)',  # 变体
        # 变体：经查，XXX存在以下违规[行为|事实|情况]：... 到 审理意见/协会决定/根据 结束
        r'经查[，,].*?(?:违规[行事实况情况]+|违法违规事实)[：:]\s*(.*?)(?=审理意见|协会决定|根据《|$)',
        # 变体：经查，XXX存在...违规[行为|事实]，具体如下：...（倒装结构）
        r'经查[，,].*?(?:违规[行事实况情况]+)[，,]\s*具体(?:如下)?[：:]\s*(.*?)(?=审理意见|协会决定|根据《|$)',
        # 变体：经查后直接是违规事实（无"存在以下违规行为"中转），到 审理意见/协会决定 结束
        r'经查[，,]\s*(.*?)(?=审理意见|协会决定|根据《|$)',
    ]
    for pat in start_patterns:
        m = re.search(pat, text, re.DOTALL)
        if m:
            section = m.group(1).strip()
            # Remove evidence line
            section = re.sub(r'以上[事实行为].*?[。\n]', '', section, flags=re.DOTALL)
            section = re.sub(r'\d+\s*$', '', section)  # trailing page numbers
            if len(section) > 10:  # 确保提取到实质内容
                return section
    return ""


def parse_one_entity(fname, entity_content):
    """解析单个 entity"""
    m = re.search(r'\*\*来源\*\*:\s*(\S+)', entity_content)
    if not m:
        return None
    txt_name = m.group(1)
    subdir = '人员' if 'subtype: 个人' in entity_content else '机构'
    txt_path = os.path.join(RAW_BASE, subdir, 'txt', txt_name)

    if not os.path.exists(txt_path):
        return None

    with open(txt_path, 'r') as f:
        text = f.read()

    # 提取各字段
    case_num = extract_case_number(text)
    violations_raw = extract_violation_section(text)
    violations = split_violations(violations_raw) if violations_raw else []
    penalty = extract_penalty(text)
    legal = extract_legal_basis(text)
    date = extract_date_from_filename(txt_name)

    # 补充：如果 case_num 为空但 entity 已有字号，保留已有的
    existing_case = re.search(r'\*\*字号\*\*:\s*(.+?)(?:\n|$)', entity_content)
    if not case_num and existing_case:
        case_num = existing_case.group(1).strip()

    # 文件行数（判断是否为短文档）
    line_count = len(text.split('\n'))

    return {
        "entity": fname,
        "source": txt_name,
        "case_num": case_num,
        "date": date,
        "violations": violations,
        "violations_count": len(violations),
        "penalty": penalty,
        "legal_basis": legal,
        "txt_lines": line_count,
        "short_doc": line_count < 40,
    }


def main():
    results = []
    stats = {
        "total": 0, "has_case_num": 0, "no_case_num": 0,
        "has_violations": 0, "no_violations": 0,
        "has_penalty": 0, "no_penalty": 0,
        "short_docs": 0, "violation_items_total": 0,
    }

    for fname in sorted(os.listdir(ENTITY_DIR)):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(ENTITY_DIR, fname)
        with open(fpath, 'r') as f:
            entity_content = f.read()

        parsed = parse_one_entity(fname, entity_content)
        if parsed is None:
            continue

        results.append(parsed)
        stats["total"] += 1

        if parsed["case_num"]:
            stats["has_case_num"] += 1
        else:
            stats["no_case_num"] += 1

        if parsed["violations"]:
            stats["has_violations"] += 1
            stats["violation_items_total"] += parsed["violations_count"]
        else:
            stats["no_violations"] += 1

        if parsed["penalty"]:
            stats["has_penalty"] += 1
        else:
            stats["no_penalty"] += 1

        if parsed["short_doc"]:
            stats["short_docs"] += 1

    with open(OUTPUT, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"=== 阶段2 完成 ===")
    print(f"解析 entity 总数: {stats['total']}")
    print(f"有字号: {stats['has_case_num']}, 缺字号: {stats['no_case_num']}")
    print(f"有违规行为: {stats['has_violations']} (共 {stats['violation_items_total']} 条)")
    print(f"缺违规行为: {stats['no_violations']}")
    print(f"有处罚措施: {stats['has_penalty']}, 缺处罚措施: {stats['no_penalty']}")
    print(f"短文档 (<40行): {stats['short_docs']}")
    print(f"\n输出文件: {OUTPUT}")

    # 展示几个样例
    print("\n--- 样例 ---")
    for r in results[:3]:
        print(f"\n[{r['entity']}]")
        print(f"  字号: {r['case_num']}")
        print(f"  日期: {r['date']}")
        print(f"  违规: {r['violations_count']} 条")
        for v in r['violations']:
            print(f"    {v[:100]}...")
        print(f"  处罚: {r['penalty'][:100]}")
        print(f"  法规: {r['legal_basis']}")


if __name__ == "__main__":
    main()
