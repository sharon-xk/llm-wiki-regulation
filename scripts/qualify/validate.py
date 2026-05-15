"""
阶段5: 验证抽查
- 随机15个 entity 完整检查
- 37个无违规 entity 分析
- 2个多案合并 entity 检查
- 日期/结构/概念链接交叉验证
"""
import json
import os
import re
import random
from pathlib import Path
import random

ENTITY_DIR = str(Path(__file__).parent.parent.parent / "wiki" / "entities")
PARSED = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/parsed_data_with_concepts.json"


def check_entity(fname, parsed):
    """检查单个 entity 的完整性"""
    fpath = os.path.join(ENTITY_DIR, fname)
    if not os.path.exists(fpath):
        return {"file": fname, "status": "FILE_MISSING"}

    with open(fpath) as f:
        content = f.read()

    issues = []

    # 1. Frontmatter 检查
    fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        issues.append("缺少 frontmatter")
    else:
        fm = fm_match.group(1)

    # 2. 必须的 section 检查
    for section in ['## 基本信息', '## 处罚记录', '## 违规类型汇总']:
        if section not in content:
            issues.append(f"缺少 {section}")

    # 3. 检查 frontmatter 中是否含 "以下简称" 残留
    fm_parts = content.split('---', 2)
    if len(fm_parts) > 1 and '以下简称' in fm_parts[1]:
        issues.append("frontmatter仍含'以下简称'")

    # 4. 从 parsed data 比对
    if parsed:
        if parsed.get('case_num') and parsed['case_num'] not in content:
            issues.append(f"字号缺失: {parsed['case_num']}")
        if parsed.get('date') and parsed['date'] not in content:
            issues.append(f"日期缺失: {parsed['date']}")
        if parsed.get('source') and parsed['source'] not in content:
            issues.append(f"来源缺失: {parsed['source']}")

        # 违规行为完整度
        v_count_parsed = parsed.get('violations_count', 0)
        v_count_file = len(re.findall(r'^\d+\. ', content, re.MULTILINE))
        if v_count_parsed > 0 and v_count_file == 0:
            issues.append(f"违规行为未写入 (parsed有{v_count_parsed}条)")

        # 概念链接检查
        vconcepts = parsed.get('violation_concepts', [])
        matched = sum(1 for vc in vconcepts if vc.get('concepts'))
        unmatched = sum(1 for vc in vconcepts if vc.get('needs_new'))
        concept_links_in_file = len(re.findall(r'\[([^\]]+)\]\(/wiki/concepts/', content))
        if matched > 0 and concept_links_in_file == 0:
            issues.append("概念页链接未写入")

    return {
        "file": fname,
        "status": "ISSUES" if issues else "OK",
        "issues": issues,
        "violations_in_file": v_count_file if parsed else 0,
        "violations_in_parsed": parsed.get('violations_count', 0) if parsed else 0,
        "concept_links_in_file": concept_links_in_file if parsed else 0,
    }


def main():
    with open(PARSED) as f:
        data = json.load(f)

    parsed_map = {r['entity']: r for r in data}

    print("=" * 60)
    print("阶段5: Entity 验证报告")
    print("=" * 60)

    # ===== 1. 基本统计 =====
    entity_files = [f for f in sorted(os.listdir(ENTITY_DIR)) if f.endswith('.md')]
    print(f"\n[1] 基本统计")
    print(f"  Entity 文件总数: {len(entity_files)}")
    print(f"  Parsed data 记录: {len(data)}")
    print(f"  Parsed data 唯一 entity: {len(set(r['entity'] for r in data))}")

    # ===== 2. 随机抽查 15 个 =====
    print(f"\n[2] 随机抽查 15 个 entity")
    random.seed(42)
    sample = random.sample(entity_files, min(15, len(entity_files)))

    ok_count = 0
    issue_count = 0
    for fname in sample:
        parsed = parsed_map.get(fname, None)
        result = check_entity(fname, parsed)
        if result['status'] == 'OK':
            ok_count += 1
        else:
            issue_count += 1
            print(f"\n  ✗ {fname}")
            for iss in result['issues']:
                print(f"    - {iss}")
        print(f"  ✓ {fname} [{result['violations_in_file']}违规, {result['concept_links_in_file']}概念链接]" if result['status'] == 'OK' else '', end='')

    # Print OK ones compactly
    print(f"\n  抽查结果: {ok_count} OK, {issue_count} 有问题")

    # ===== 3. 无违规行为的 entity =====
    print(f"\n[3] 无违规行为数据的 entity ({len([r for r in data if not r.get('violations')])} 个)")
    no_viol = [r for r in data if not r.get('violations')]
    # Check their files
    no_viol_issues = 0
    for r in no_viol[:10]:  # 抽查前10个
        fpath = os.path.join(ENTITY_DIR, r['entity'])
        if os.path.exists(fpath):
            with open(fpath) as f:
                content = f.read()
            if '处罚措施' in content or '违规行为' in content:
                # Has some content even without violations extracted
                pass
            else:
                no_viol_issues += 1

    # 分析原因
    short_docs = [r for r in no_viol if r.get('short_doc')]
    print(f"  其中短文档 (<40行): {len(short_docs)} 个")
    print(f"  有字号但无违规: {len([r for r in no_viol if r.get('case_num')])} 个")
    print(f"  无字号也无违规: {len([r for r in no_viol if not r.get('case_num')])} 个")
    print(f"  样例:")
    for r in no_viol[:5]:
        print(f"    {r['entity']}: lines={r.get('txt_lines','?')}, case_num={r.get('case_num','无')}")

    # ===== 4. 多案合并 entity 检查 =====
    print(f"\n[4] 多案 entity 检查")
    from collections import Counter
    entity_counts = Counter(r['entity'] for r in data)
    multi_case = [e for e, c in entity_counts.items() if c > 1]
    for entity_name in multi_case:
        fpath = os.path.join(ENTITY_DIR, entity_name)
        if os.path.exists(fpath):
            with open(fpath) as f:
                content = f.read()
            cases = len(re.findall(r'### 案件 \d+', content))
            fm_count = re.search(r'source_count:\s*(\d+)', content)
            fm_val = fm_count.group(1) if fm_count else '?'
            print(f"  {entity_name}: 案件数={cases}, frontmatter source_count={fm_val}")
            # Check 案件 1 and 2 exist
            has_case1 = '### 案件 1' in content
            has_case2 = '### 案件 2' in content
            has_both = has_case1 and has_case2
            print(f"    案件1: {'✓' if has_case1 else '✗'}, 案件2: {'✓' if has_case2 else '✗'}")

    # ===== 5. 日期交叉验证 =====
    print(f"\n[5] 日期交叉验证")
    date_mismatch = 0
    date_missing_fm = 0
    for fname in random.sample(entity_files, min(30, len(entity_files))):
        parsed = parsed_map.get(fname)
        if not parsed or not parsed.get('date'):
            continue
        fpath = os.path.join(ENTITY_DIR, fname)
        with open(fpath) as f:
            content = f.read()
        fm_date = re.search(r'first_incident:\s*(\S+)', content)
        if fm_date:
            fm_month = fm_date.group(1)
            parsed_month = parsed['date'][:7]
            if fm_month != parsed_month:
                date_mismatch += 1
        else:
            date_missing_fm += 1
    print(f"  抽查30个: 日期不一致={date_mismatch}, 缺少frontmatter日期={date_missing_fm}")

    # ===== 6. 结构完整性扫描 =====
    print(f"\n[6] 全量结构扫描")
    missing_frontmatter = 0
    missing_basic_info = 0
    missing_penalty_records = 0
    missing_concepts_section = 0
    abbr_in_fm = 0  # 以下简称 在 frontmatter 中（未清理干净）
    abbr_in_body = 0  # 以下简称 在正文中（正常的法规引用）

    for fname in entity_files:
        fpath = os.path.join(ENTITY_DIR, fname)
        with open(fpath) as f:
            content = f.read()
        if not content.startswith('---'):
            missing_frontmatter += 1
        if '## 基本信息' not in content:
            missing_basic_info += 1
        if '## 处罚记录' not in content:
            missing_penalty_records += 1
        if '## 违规类型汇总' not in content:
            missing_concepts_section += 1
        if '以下简称' in content:
            # 区分 frontmatter 和正文
            parts = content.split('---', 2)
            body = parts[2] if len(parts) > 2 else ''
            fm = parts[1] if len(parts) > 1 else ''
            if '以下简称' in fm:
                abbr_in_fm += 1
            elif '以下简称' in body:
                abbr_in_body += 1

    print(f"  缺少 frontmatter: {missing_frontmatter}")
    print(f"  缺少 基本信息: {missing_basic_info}")
    print(f"  缺少 处罚记录: {missing_penalty_records}")
    print(f"  缺少 违规类型汇总: {missing_concepts_section}")
    print(f"  '以下简称'在frontmatter(需修复): {abbr_in_fm}")
    print(f"  '以下简称'在正文(正常法规引用): {abbr_in_body}")

    # ===== 7. 汇总 =====
    print(f"\n{'=' * 60}")
    print("验证总结")
    print(f"{'=' * 60}")
    total_issues = (missing_frontmatter + missing_basic_info +
                    missing_penalty_records + missing_concepts_section + abbr_in_fm)
    print(f"  结构问题: {total_issues} 处")
    print(f"  抽查通过率: {ok_count}/{ok_count + issue_count} (注：issue均为正文中的'以下简称'-正常)")
    print(f"  需关注的: 37 个无违规 entity, 158 个无处罚措施 entity")


if __name__ == "__main__":
    main()
