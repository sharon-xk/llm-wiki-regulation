#!/usr/bin/env python3
"""
阶段1: 解析纪律处分 TXT，提取主体信息

职责：从 OCR 后的纪律处分 TXT 文件中提取处罚主体信息（被处罚机构/人员名称、
      字号、日期等），输出 parsed_txt_results.json，供 create_institutions.py 建机构页。

输入：raw/纪律处分/机构/txt/*.txt
输出：raw/parsed/parsed_txt_results.json

与 extract_structured.py 的关系：
    本脚本提取"主体信息"（建机构页所需），extract_structured.py 在机构页建成后
    再提取"违规行为结构化数据"（字号/处罚措施/违规条款）。两者有先后依赖。
"""
import re
import json
from pathlib import Path
from collections import defaultdict

def extract_complete_violations(content):
    """提取完整的违规事由段落"""
    violations = []

    # 匹配"存在以下违规行为"或"违规事实"之后的完整段落
    # 常见的模式：
    # 1. "经查，XXX存在以下违规行为："之后到"二、"或句号
    # 2. "一、违规事实"之后的内容
    # 3. "违反了《..."之前的内容

    # 尝试匹配"经查，XXX存在以下违规行为"段落
    patterns = [
        r'经查[，。].*?存在以下违规[行为事实]*[：:]([^""]+)',
        r'一[、\s]*违规[行为事实][：:]([^""]+)',
        r'违规[行为事实][：:]\s*([^依据\n]+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        for m in matches:
            # 清理：去除多余空白，限制长度
            text = re.sub(r'\s+', ' ', m).strip()
            if len(text) > 10:
                violations.append(text)  # 保留完整内容

    # 如果没找到， fallback到行内匹配
    if not violations:
        for line in content.split('\n'):
            line = line.strip()
            if any(kw in line for kw in ['未尽', '违反', '违规', '存在以下']):
                if len(line) > 15:
                    violations.append(line)

    return violations[:5]  # 最多5条

def extract_complete_measures(content):
    """提取完整的处罚措施"""
    measures = []

    # 匹配处罚措施段落
    patterns = [
        r'决定[：:]?\s*([^依据\n]+)',
        r'采取\s*([^自律\n]+)\s*自律管理措施',
        r'作出\s*([^决定\n]+)\s*决定',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        for m in matches:
            text = re.sub(r'\s+', ' ', m).strip()
            if len(text) > 5:
                measures.append(text)

    # Fallback: 行内匹配
    if not measures:
        for line in content.split('\n'):
            line = line.strip()
            if any(kw in line for kw in ['警告', '罚款', '取消资格', '撤销登记', '责令改正', '公开谴责', '暂停', '停止']):
                if len(line) > 5:
                    measures.append(line)

    return measures[:5]

def parse_txt_file(txt_path):
    """解析单个TXT文件"""
    try:
        content = txt_path.read_text(encoding='utf-8')
    except:
        return None

    # 跳过非处罚决定书的文件（如年报）
    if '中国证券投资基金业年报' in content or '图书在版编目' in content:
        return None

    # 提取当事人
    subject = ''
    subject_info = ''  # 保存当事人完整信息用于后续分析
    for line in content.split('\n')[:20]:
        if '当事人' in line and ('：' in line or ':' in line):
            parts = re.split(r'[:：]', line, 1)
            if len(parts) > 1:
                subject = parts[1].strip()
                # 去除《》等标记
                subject = re.sub(r'《.+', '', subject)
                subject = subject.strip()
                # 保存当事人信息行
                subject_info = line
            break

    if not subject:
        return None

    # 提取处分字号（在当事人信息附近）
    case_num = ''
    for line in content.split('\n')[:30]:
        m = re.search(r'中基协处分\s*[\(（]?\s*(\d+)\s*[\)）]\s*(\d+)', line)
        if m:
            case_num = f"中基协处分({m.group(1)}){m.group(2)}号"
            break

    # 提取日期 - 优先找决定书日期
    # 决定书日期通常在文件开头，或者在"中基协处分"字样附近
    date = ''

    # 从文件名提取年月（备用）
    filename_match = re.search(r'(\d{4})(\d{2})_', txt_path.name)
    filename_year = filename_match.group(1) if filename_match else ''
    filename_month = filename_match.group(2) if filename_match else ''

    # 尝试从"中基协处分 (XXXX)"字样提取年份
    year_match = re.search(r'中基协处分\s*[\[（(]\s*(\d{4})\s*[\])）]', content)
    decision_year = year_match.group(1) if year_match else ''

    # 在文件前50行中查找完整的决定书日期
    lines = content.split('\n')[:50]

    # 找出当事人信息的结束位置（"当事人:"之后的几行）
    subject_end = 0
    for i, line in enumerate(lines):
        if '当事人' in line:
            subject_end = i + 3  # 包含当事人信息的后3行
            break

    date_patterns = [
        r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日',
        r'(\d{4})\s*年\s*(\d{1,2})\s*月',
    ]

    found_date = False

    # 如果有决定书年份（case号），优先使用
    if decision_year and 2015 <= int(decision_year) <= 2026:
        # 使用决定书年份 + 文件名中的月份
        if filename_month:
            date = f"{decision_year}-{filename_month}-01"
        else:
            date = f"{decision_year}-01-01"
        found_date = True
    else:
        # 在当事人信息之后的部分查找日期
        for i in range(subject_end, min(50, len(lines))):
            line = lines[i]
            for pattern in date_patterns:
                date_match = re.search(pattern, line)
                if date_match:
                    year = int(date_match.group(1))
                    # 出生日期的年份范围是1940-2005，决定书年份应该是2015-2026
                    if 2015 <= year <= 2026:
                        if len(date_match.groups()) == 3:
                            date = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
                        else:
                            date = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-01"
                        found_date = True
                        break
            if found_date:
                break

    # 如果仍然没有，用文件名年月
    if not date and filename_year:
        date = f"{filename_year}-{filename_month}-01" if filename_month else f"{filename_year}-01-01"

    # 提取违规类型 - 使用改进的完整提取
    violations = extract_complete_violations(content)

    # 提取处罚措施 - 使用改进的完整提取
    measures = extract_complete_measures(content)

    return {
        'subject': subject,
        'date': date,
        'case_num': case_num,
        'violations': violations,
        'measures': measures,
        'source': txt_path.name
    }

def process_directory(dir_path, module_name):
    """处理目录下的所有TXT文件"""
    dir_path = Path(dir_path)
    txt_files = list(dir_path.glob('*.txt'))

    print(f'\n=== {module_name} ===')
    print(f'共 {len(txt_files)} 个TXT文件')

    entities = defaultdict(list)
    no_subject = 0

    for i, txt_file in enumerate(txt_files):
        parsed = parse_txt_file(txt_file)
        if parsed and parsed['subject']:
            entities[parsed['subject']].append(parsed)
        else:
            no_subject += 1

        if (i + 1) % 100 == 0:
            print(f'进度: {i+1}/{len(txt_files)}')

    print(f'找到 {len(entities)} 个实体, {no_subject} 个无法解析')

    return entities

def main():
    base_dir = Path(__file__).parent.parent.parent / 'raw'

    # 处理纪律处分/机构
    jlcf_jg = process_directory(base_dir / '纪律处分' / '机构' / 'txt', '纪律处分-机构')
    jlcf_jg_count = sum(len(v) for v in jlcf_jg.values())

    # 处理纪律处分/人员 — 已禁用，人名不纳入知识库
    # jlcf_ry = process_directory(base_dir / '纪律处分/人员', '纪律处分-人员')
    # jlcf_ry_count = sum(len(v) for v in jlcf_ry.values())

    # 合并结果
    all_entities = {
        '纪律处分_机构': dict(jlcf_jg),
        # '纪律处分_人员': dict(jlcf_ry)
    }

    # 统计
    print('\n=== 统计 ===')
    print(f'纪律处分-机构: {len(jlcf_jg)} 个实体, {jlcf_jg_count} 条记录')
    # print(f'纪律处分-人员: {len(jlcf_ry)} 个实体, {jlcf_ry_count} 条记录')

    # 保存结果
    output_file = base_dir / 'parsed' / 'parsed_txt_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_entities, f, ensure_ascii=False, indent=2)

    print(f'\n结果已保存: {output_file}')

    # 输出示例
    print('\n=== 示例实体 ===')
    for module, entities in [('机构', jlcf_jg)]:
        if entities:
            name = list(entities.keys())[0]
        info = list(entities.values())[0][0]
        print(f"{module}: {name} - {info['date']} - {info['case_num']}")
        break

if __name__ == '__main__':
    main()