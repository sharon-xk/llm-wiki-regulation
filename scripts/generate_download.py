#!/usr/bin/env python3
import json
import urllib.parse
import os

data = json.load(open('/tmp/all_amac_links.json'))
base_dir = '/Users/sharon/ai-project/llm-wiki-regulation/raw'

commands = []

# scfjg - PDFs
for url in data['scfjg']:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    filename = path.split('/')[-1]
    dir_prefix = path.split('/')[-2]
    dest = f'{base_dir}/纪律处分/机构/{dir_prefix}_{filename}'
    if not os.path.exists(dest):
        commands.append(f'curl -s -L --max-time 60 -o "{dest}" "{url}"')

# scfry - PDFs
for url in data['scfry']:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    filename = path.split('/')[-1]
    dir_prefix = path.split('/')[-2]
    dest = f'{base_dir}/纪律处分/人员/{dir_prefix}_{filename}'
    if not os.path.exists(dest):
        commands.append(f'curl -s -L --max-time 60 -o "{dest}" "{url}"')

# ycjy - HTML
for url in data['ycjy']:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    filename = path.split('/')[-1]
    dir_prefix = path.split('/')[-2]
    dest = f'{base_dir}/异常经营/{dir_prefix}_{filename}'
    if not os.path.exists(dest):
        commands.append(f'curl -s -L --max-time 60 -o "{dest}" "{url}"')

# sljg - HTML
for url in data['sljg']:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    filename = path.split('/')[-1]
    dir_prefix = path.split('/')[-2]
    dest = f'{base_dir}/失联机构/{dir_prefix}_{filename}'
    if not os.path.exists(dest):
        commands.append(f'curl -s -L --max-time 60 -o "{dest}" "{url}"')

# zlcs - HTML
for url in data['zlcs']:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    filename = path.split('/')[-1]
    dir_prefix = path.split('/')[-2]
    dest = f'{base_dir}/自律措施/{dir_prefix}_{filename}'
    if not os.path.exists(dest):
        commands.append(f'curl -s -L --max-time 60 -o "{dest}" "{url}"')

print(f'Total commands: {len(commands)}')

with open('/tmp/download_commands.sh', 'w') as f:
    f.write('#!/bin/bash\n')
    f.write('\n'.join(commands))

print('Commands saved to /tmp/download_commands.sh')