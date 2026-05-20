# 操作日志

> 记录所有 ingest、query、lint 操作。每条以 `## [日期]` 开头，可用 `grep "^## \[" log.md | tail -N` 快速查看最近 N 条。

---

---

## [2026-05-13] ingest | 补充异常经营/失联机构法规

- 从 parsed_html_results.json 提取法规引用，创建 3 个法规页
- 更新 233 个异常经营/失联机构 entity 页，补充"依据法规"链接
- 更新 reg_name_map.json（新增 5 条映射）
- 更新 index.md

### 创建/更新的页面

- wiki/regulations/关于私募基金管理人在异常经营情形下提交专项法律意见书的公告.md (296 引用)
- wiki/regulations/关于进一步规范私募基金管理人登记若干事项的公告.md (86 引用)
- wiki/regulations/私募基金管理人失联处理指引.md (48 引用)
- wiki/entities/ (233 个 entity 页补充法规链接)
- scripts/reg_name_map.json
- scripts/supplement_regulations.py
- index.md

## [2026-05-13] ingest | 法规索引建立

- 创建 `wiki/regulations/` 目录，12 个法规页面
- 创建 `scripts/reg_name_map.json` 法规名称映射表（OCR变体/简称 → 标准全称）
- 数据源: parsed_data_with_concepts.json
- 法规页面包含：概述、关联违规类型、高频引用条款（含条款描述和关联违规）、典型案例
- 更新 index.md 添加法规分类

### 创建/更新的页面

- wiki/regulations/ (12 个法规页)
- scripts/reg_name_map.json
- scripts/create_regulation_pages.py（法规页面生成脚本，可复用）
- scripts/extract_reg_names.py（法规名变体提取脚本）
- scripts/analyze_regulations.py（法规关联分析脚本）
- index.md

---


### 数据抓取完成

使用 puppeteer 抓取5个模块数据：
- 纪律处分-机构: 451 PDFs (已下载 448)
- 纪律处分-人员: 942 PDFs (已下载 950)
- 异常经营: 107 HTML页面 (已下载 107)
- 失联机构: 111 HTML页面 (已下载 111)
- 自律措施: 18 HTML页面 (已下载 18)

### OCR进度

- 纪律处分/机构: 448 PDFs, 366 TXTs (还需 OCR 约 82 个)
- 纪律处分/人员: 950 PDFs, 1 TXT (全部需要 OCR，约 949 个)

### 待完成

1. 完成纪律处分/机构剩余 PDF 的 OCR
2. 完成纪律处分/人员全部 PDF 的 OCR
3. 解析 HTML 页面的内容
4. 创建实体页和模块页

### 脚本更新

- scripts/scrape_amac.py (v4) - 使用 puppeteer 获取动态列表
- scripts/generate_download.py - 生成下载命令
- scripts/continue_ocr.sh - 继续 OCR 处理


## [2026-05-08] ingest | 纪律处分_机构

- 从 raw/纪律处分/机构/ 目录读取 21 个 PDF 文件
- 执行 OCR 提取文本（pdftotext + tesseract）
- 解析 16 个当事人实体
- 创建 wiki/entities/ 下的 16 个实体页
- 创建 wiki/modules/纪律处分.md 模块页
- 更新 index.md 索引

### 创建/更新的页面

- wiki/entities/ (16 个实体页)
- wiki/modules/纪律处分.md
- index.md

## [2026-05-08] ingest | 全量数据

- 纪律处分-机构: 356 实体, 358 条记录
- 纪律处分-人员: 732 实体, 732 条记录
- 异常经营: 324 实体
- 失联机构: 342 实体
- 自律措施: 1 实体

创建了 1088 个实体页和 4 个模块页

## [2026-05-11] ingest | 全量数据

- 纪律处分-机构: 356 实体, 358 条记录
- 纪律处分-人员: 732 实体, 732 条记录
- 异常经营: 324 实体
- 失联机构: 342 实体
- 自律措施: 1 实体

创建了 1088 个实体页和 4 个模块页

## [2026-05-11] ingest | 全量数据

- 纪律处分-机构: 356 实体, 358 条记录
- 纪律处分-人员: 732 实体, 732 条记录
- 异常经营: 324 实体
- 失联机构: 342 实体
- 自律措施: 1 实体

创建了 1088 个实体页和 4 个模块页

## [2026-05-11] ingest | 全量数据

- 纪律处分-机构: 356 实体, 358 条记录
- 纪律处分-人员: 732 实体, 732 条记录
- 异常经营: 324 实体
- 失联机构: 342 实体
- 自律措施: 1 实体

创建了 1088 个实体页和 4 个模块页

## [2026-05-11] ingest | 全量数据

- 纪律处分-机构: 356 实体, 358 条记录
- 纪律处分-人员: 732 实体, 732 条记录
- 异常经营: 324 实体
- 失联机构: 342 实体
- 自律措施: 1 实体

创建了 1088 个实体页和 4 个模块页

## [2026-05-11] ingest | 全量数据

- 纪律处分-机构: 356 实体, 358 条记录
- 纪律处分-人员: 732 实体, 732 条记录
- 异常经营: 324 实体
- 失联机构: 342 实体
- 自律措施: 1 实体

创建了 1088 个实体页和 4 个模块页

## [2026-05-11] ingest | 全量数据

- 纪律处分-机构: 356 实体, 358 条记录
- 纪律处分-人员: 732 实体, 732 条记录
- 异常经营: 324 实体
- 失联机构: 342 实体
- 自律措施: 1 实体

创建了 1077 个实体页和 4 个模块页

## [2026-05-11] ingest | 全量数据

- 纪律处分-机构: 356 实体, 358 条记录
- 纪律处分-人员: 732 实体, 732 条记录
- 异常经营: 324 实体
- 失联机构: 342 实体
- 自律措施: 1 实体

创建了 1077 个实体页和 4 个模块页

## [2026-05-11] ingest | 全量数据

- 纪律处分-机构: 356 实体, 358 条记录
- 纪律处分-人员: 732 实体, 732 条记录
- 异常经营: 324 实体
- 失联机构: 342 实体
- 自律措施: 1 实体

创建了 1077 个实体页和 4 个模块页

## [2026-05-11] ingest | 全量数据

- 纪律处分-机构: 356 实体, 358 条记录
- 纪律处分-人员: 732 实体, 732 条记录
- 异常经营: 324 实体
- 失联机构: 342 实体
- 自律措施: 1 实体

创建了 1077 个实体页和 4 个模块页

## [2026-05-11] ingest | 全量数据

- 纪律处分-机构: 356 实体, 358 条记录
- 纪律处分-人员: 732 实体, 732 条记录
- 异常经营: 324 实体
- 失联机构: 342 实体
- 自律措施: 1 实体

创建了 1077 个实体页和 4 个模块页
## [2026-05-12] ingest | 异常经营 + 失联机构 entity 创建

- 异常经营: 201 entities, 323 条记录（新建 525 个 entity 页）
- 失联机构: 330 entities, 453 条记录
- 合并到已有纪律处分 entity: 6 个
- 数据源: parsed_html_results.json
- 脚本: scripts/create_html_entities.py
## [2026-05-12] ingest | 异常经营 + 失联机构 entity 创建

- 异常经营: 201 entities, 323 条记录（新建 11 个 entity 页）
- 失联机构: 320 entities, 453 条记录
- 合并到已有纪律处分 entity: 510 个
- 数据源: parsed_html_results.json
- 脚本: scripts/create_html_entities.py
## [2026-05-12] ingest | 异常经营 + 失联机构 entity 创建

- 异常经营: 201 entities, 323 条记录（新建 0 个 entity 页）
- 失联机构: 320 entities, 453 条记录
- 合并到已有纪律处分 entity: 521 个
- 数据源: parsed_html_results.json
- 脚本: scripts/create_html_entities.py
## [2026-05-12] update | concepts + analysis 重建

- 数据源: scripts/tmp/parsed_data_with_concepts.json
- 重建 10 个 concept 页面 (完整文本, entity 链接)
- 重建 2 个 analysis 页面 (年度趋势 + 最新处罚, 覆盖全模块)
- 脚本: scripts/update_concepts_analysis.py
## [2026-05-12] update | concepts + analysis 重建

- 数据源: scripts/tmp/parsed_data_with_concepts.json
- 重建 10 个 concept 页面 (完整文本, entity 链接)
- 重建 2 个 analysis 页面 (年度趋势 + 最新处罚, 覆盖全模块)
- 脚本: scripts/update_concepts_analysis.py


## [2026-05-19] 增量更新 | +0 个新文件 | since=20260430
