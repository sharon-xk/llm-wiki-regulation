# Scripts 说明

按 ingest 工作流分阶段组织，可跨项目复用。

## 目录结构

```
scripts/
├── config/                         # 配置文件
│   └── reg_name_map.json           # 法规名映射表
├── scrape/                         # ① 爬取（网站专用适配层，换站需重写）
│   └── scrape_amac.py              # AMAC 全模块爬虫，支持 --since 增量
├── ocr/                            # ② OCR
│   ├── gen_tasks.py                # 生成 OCR 任务列表
│   ├── run_batch.py                # 批量 PDF OCR
│   └── ocr_worker.sh               # 单文件 OCR worker
├── parse/                          # ③ 解析（可复用）
│   ├── parse_txt.py                # 解析纪律处分 TXT
│   ├── parse_html.py               # 解析 HTML 公告
│   └── extract_structured.py       # 从 OCR TXT 提取结构化数据
├── wiki/                           # ④ 生成 wiki（可复用）
│   ├── create_entities.py          # 创建 entity 页面
│   ├── create_modules.py           # 创建 module 页面
│   ├── create_concepts.py          # 创建 concept 页面
│   ├── create_analysis.py          # 创建 analysis 页面
│   ├── create_regulations.py       # 创建法规页面
│   ├── concept_map.py              # 违规行为 → 概念映射
│   ├── update_entities.py          # 更新 entity 内容
│   └── update_index.py             # 更新 index.md + log.md
├── qualify/                        # ⑤ 质检（可复用）
│   ├── validate.py                 # 数据质量验证
│   └── survey.py                   # 全量统计汇总
├── normalize/                      # ⑥ 数据清洗
│   ├── names.py                    # 规范化 entity 命名
│   ├── fix_names.py                # 修复命名问题
│   └── merge_dupes.py              # 合并重复实体
├── analyze/                        # ⑦ 补充分析
│   ├── extract_reg_names.py        # 提取法规名称
│   ├── analyze_regulations.py      # 分析法规关联
│   └── supplement_regulations.py   # 补充法规信息
├── runner.py                       # 全量 ingest（初次建库用）
├── incremental_runner.py           # 增量 ingest（日常更新用）
├── pilot.py                        # 试点选择
└── tmp/                            # 临时文件
    ├── ingest_state.json           # 增量状态追踪
    ├── parsed_data.json            # 结构化解析缓存
    └── parsed_data_with_concepts.json  # 概念映射缓存
```

## 使用流程

**初次建库（全量）：**

```bash
python3 scripts/runner.py                    # 完整五阶段
python3 scripts/runner.py --from parse       # 从解析步骤开始（已有 raw 文件时）
```

**日常更新（增量）：**

```bash
# 自动读取上次爬取状态，只下载新文件，然后全量重建 wiki
python3 scripts/incremental_runner.py

# 手动指定起跑线
python3 scripts/incremental_runner.py --since 20260501
```

增量 runner 内部流程：

```
1. 读取 tmp/ingest_state.json → 获取 last_raw_date
2. scrape_amac.py --since {last_raw_date}   # 只下载新文件
3. 检查 raw/ 文件数变化 → 无新增则退出，有则继续
4. 全量重解析（parse/）
5. 全量重建 wiki（wiki/）
6. 更新 index.md + log.md
7. 质检（qualify/validate.py）
8. 更新 tmp/ingest_state.json
```

**定时调度（cron）：**

```bash
# 每周一上午 9 点自动检查更新
0 9 * * 1 cd /path/to/project && python3 scripts/incremental_runner.py
```

**爬虫单跑：**

```bash
python3 scripts/scrape/scrape_amac.py                     # 全量
python3 scripts/scrape/scrape_amac.py --since 20260501    # 只下载此日期之后
```

## 跨项目复用

复制 `scripts/` 到新项目后：

1. `scrape/` 整个目录重写（页面结构不同，爬虫不可复用）
2. 修改 `config/reg_name_map.json` 为新领域的名称映射
3. `ocr/` `parse/` `wiki/` `qualify/` 为核心管线，通常只需调整 wiki 模板
4. `tmp/` 清空，清除旧项目的解析缓存和状态文件
