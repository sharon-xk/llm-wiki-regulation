#!/usr/bin/env python3
"""
重新下载HTML文件
用于修复下载失败的HTML页面
"""
import json
import urllib.parse
import subprocess
import os
import sys

def redownload_html():
    data = json.load(open('/tmp/all_amac_links.json'))
    base_dir = '/Users/sharon/ai-project/llm-wiki-regulation/raw'

    modules = [
        ('异常经营', data['ycjy'], f'{base_dir}/异常经营'),
        ('失联机构', data['sljg'], f'{base_dir}/失联机构'),
        ('自律措施', data['zlcs'], f'{base_dir}/自律措施'),
    ]

    for key, urls, dir_path in modules:
        print(f'\n=== {key} ===')
        count = 0
        for url in urls:
            parsed = urllib.parse.urlparse(url)
            path = parsed.path
            filename = path.split('/')[-1]
            dir_prefix = path.split('/')[-2]
            dest = f'{dir_path}/{dir_prefix}_{filename}'

            if os.path.exists(dest) and os.path.getsize(dest) > 100:
                continue

            subprocess.run(
                ['curl', '-s', '-L', '--max-time', '30', '-o', dest, url],
                capture_output=True
            )
            count += 1

        print(f'新增下载: {count} 个文件')

    print('\n完成')

if __name__ == '__main__':
    redownload_html()