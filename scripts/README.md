# 脚本目录说明

数据处理管线脚本。按 7 阶段流水线组织：`scrape → ocr → parse → wiki → qualify`，
由 `runner.py`（全量）或 `incremental_runner.py`（增量）调度。

```
scripts/
├── runner.py              # 全量管线调度器
├── incremental_runner.py  # 增量管线调度器（按日期增量爬取）
│
├── scrape/                # ① 爬取
│   └── scrape_amac.py              # AMAC 自律管理爬虫，支持 --since 增量
│
├── ocr/                   # ② OCR
│   ├── gen_tasks.py                # 生成 OCR 任务列表（PDF↔TXT 配对）
│   ├── run_batch.py                # 批量 PDF OCR，写 txt/
│   └── fix_ocr.py                  # OCR 后处理：纠正高频错别字（被 run_batch/scrape 引用）
│
├── parse/                 # ③ 解析（双阶段）
│   ├── parse_txt.py                # 阶段1: 提取主体信息 → parsed_txt_results.json
│   ├── parse_html.py               # 解析 HTML 公告 → parsed_html_results.json
│   └── extract_structured.py       # 阶段2: 提取违规行为结构化数据 → parsed_data.json
│
├── wiki/                  # ④ 生成知识页面
│   ├── create_institutions.py      # 创建机构页
│   ├── map_violations.py           # 违规行为 → 违规类型映射
│   ├── update_institutions.py      # 更新机构页的违规类型链接
│   ├── create_violations.py        # 创建违规类型页
│   ├── create_regulations.py       # 创建法规页
│   ├── supplement_regulations.py   # 补充法规页（异常经营/失联机构的法规）
│   ├── create_analysis.py          # 创建分析页（趋势/统计）
│   └── update_index.py             # 更新 index.md
│
├── qualify/               # ⑤ 质量校验与治理
│   ├── validate.py                 # 数据质量校验（frontmatter/链接/抽样）
│   ├── survey.py                   # 全量统计
│   └── names.py                    # 规范化文件命名和内容（手动运行）
│
├── config/                # 配置文件
│   ├── reg_name_map.json           # 法规名映射表（OCR变体 → 标准全称）
│   └── ocr_fix_map.json            # OCR 错别字纠正规则
│
└── tmp/                   # 临时文件（中间产物缓存，不提交）
    ├── parsed_data.json            # extract_structured 输出
    ├── parsed_data_with_concepts.json  # map_violations 输出
    └── ingest_state.json           # 增量爬取状态
```

## 数据流

```
raw/ (PDF/HTML)
  │ scrape
  ▼
raw/纪律处分/机构/{pdf,txt}/ + raw/{异常经营,失联机构}/
  │ parse (阶段1)
  ▼
raw/parsed/parsed_{txt,html}_results.json
  │ wiki/create_institutions
  ▼
wiki/institutions/
  │ parse (阶段2) + wiki/map_violations
  ▼
scripts/tmp/parsed_data_with_concepts.json
  │ wiki/create_violations + create_regulations + create_analysis
  ▼
wiki/{violations,regulations,analysis}/
  │ qualify
  ▼
校验报告 → log.md
```

## 运行

```bash
# 全量重建
python scripts/runner.py --steps scrape,ocr,parse,wiki,qualify

# 增量更新（日常）
python scripts/incremental_runner.py

# 单独运行某阶段
python scripts/wiki/create_institutions.py
```
