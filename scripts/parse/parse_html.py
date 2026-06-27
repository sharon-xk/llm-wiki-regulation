#!/usr/bin/env python3
"""
解析HTML公告页面，提取关键信息
"""
import re
from pathlib import Path
from bs4 import BeautifulSoup

def parse_html_file(html_path):
    """解析单个HTML文件"""
    try:
        content = html_path.read_text(encoding='utf-8')
    except:
        return None

    soup = BeautifulSoup(content, 'html.parser')

    # 提取标题
    title = soup.find('title')
    title = title.text.strip() if title else ''

    # 提取正文内容 - 查找 job-infos 或 content 区域
    content_div = soup.find('div', class_='job-infos')
    if not content_div:
        content_div = soup.find('div', class_='content')

    if content_div:
        # 移除脚本和样式
        for tag in content_div.find_all(['script', 'style']):
            tag.decompose()

        # 获取文本
        text = content_div.get_text(separator='\n', strip=True)
        text = '\n'.join([l for l in text.split('\n') if l.strip()])
    else:
        text = ''

    # 提取日期
    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', content)
    if date_match:
        date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
    else:
        date = ''

    # 提取机构名称
    companies = []
    # 常见模式：关于注销XXX等N家...
    for m in re.finditer(r'关于注销([^等]+?)等(\d+)家', title):
        companies.append({'name': m.group(1), 'count': m.group(2)})

    # 从正文中提取公司名称
    for line in text.split('\n'):
        if '私募基金管理人' in line or '投资管理' in line:
            # 提取公司名
            m = re.search(r'([^\s，。、]+(?:投资|资产|基金|资本|管理|私募)有限公司)', line)
            if m and m.group(1) not in [c['name'] for c in companies]:
                companies.append({'name': m.group(1), 'count': '1'})

    return {
        'title': title,
        'date': date,
        'text': text[:5000],  # 限制长度
        'companies': companies,
        'source': html_path.name
    }

def process_directory(dir_path, module_name):
    """处理目录下的所有HTML文件"""
    dir_path = Path(dir_path)
    html_files = list(dir_path.glob('*.html'))

    print(f'\n=== {module_name} ===')
    print(f'共 {len(html_files)} 个HTML文件')

    results = []
    for i, html_file in enumerate(html_files):
        parsed = parse_html_file(html_file)
        if parsed:
            results.append(parsed)
            if (i + 1) % 20 == 0:
                print(f'进度: {i+1}/{len(html_files)}')

    print(f'解析完成: {len(results)} 个文件')

    # 按日期排序
    results.sort(key=lambda x: x['date'], reverse=True)

    return results

def main():
    base_dir = Path(__file__).parent.parent.parent / 'raw'

    # 处理异常经营
    ycjy_results = process_directory(base_dir / '异常经营', '异常经营')

    # 处理失联机构
    sljg_results = process_directory(base_dir / '失联机构', '失联机构')

    # 自律措施数据停更于2020年，暂不处理
    # zlcs_results = process_directory(base_dir / '自律措施', '自律措施')

    # 保存结果
    import json
    output = {
        '异常经营': ycjy_results,
        '失联机构': sljg_results,
        # '自律措施': zlcs_results,  # 数据停更于2020年
    }

    output_file = base_dir / 'parsed' / 'parsed_html_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n结果已保存: {output_file}')

    # 输出示例
    print('\n=== 示例数据 ===')
    if ycjy_results:
        r = ycjy_results[0]
        print(f"标题: {r['title'][:60]}")
        print(f"日期: {r['date']}")
        print(f"公司: {[c['name'] for c in r['companies'][:3]]}")

if __name__ == '__main__':
    main()