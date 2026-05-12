# 基金业协会处罚知识库

本知识库用于收集、整理和查询中国证券投资基金业协会（AMAC）自律管理处罚信息。

## 数据收集汇总

| 模块 | 原始文件 | 实体数 | 记录数 |
|------|---------|-------|-------|
| 纪律处分-机构 | 448 PDFs (391 TXTs) | 356 | 358 |
| 纪律处分-人员 | 950 PDFs (817 TXTs) | 732 | 732 |
| 异常经营 | 107 HTMLs | 324 | - |
| 失联机构 | 111 HTMLs | 342 | - |
| 自律措施 | 18 HTMLs | 1 | - |

**总计：** 1629 个原始文件，1098 个实体页

## Wiki 页面

### 目录结构

```
wiki/
├── entities/       # 市场主体（机构/个人）- 1098个
├── modules/        # 按模块分类的处罚记录 - 4个
├── concepts/       # 违规类型、概念定义 - 7个
└── analysis/       # 分析、对比、趋势页面 - 2个
```

### 模块页

- **纪律处分** - 纪律处分决定书，含机构和个人

### 概念页（违规类型）

- 未尽谨慎勤勉义务
- 违规募集
- 承诺保本收益
- 信息披露违规
- 挪用基金财产
- 未按规定登记备案
- 投资者适当性违规

### 分析页

- **分析_年度趋势** - 年度统计及违规类型分布
- **分析_最新处罚** - 最近发布的处罚记录

### 实体页

每个实体页包含：
- 基本信息（名称、类型、首次/最近处罚时间）
- 处罚记录列表
- 违规类型汇总

## Scripts 脚本说明

位于 `scripts/` 目录下：

| 脚本 | 说明 |
|------|------|
| `scrape_amac_v4.py` | 主爬虫脚本，使用 puppeteer 获取动态列表页数据，自动下载 PDF/HTML 并执行 OCR |
| `ocr_pdfs.py` | 单独运行 PDF OCR 处理，支持 pdftotext 和 tesseract 两种方式 |
| `redownload_html.py` | 重新下载 HTML 文件，修复下载失败的文件 |
| `parse_txt.py` | 解析纪律处分 TXT 文件，提取当事人、日期、违规类型等信息 |
| `parse_html.py` | 解析异常经营/失联机构/自律措施 HTML 页面，提取公司名称和公告信息 |
| `create_wiki.py` | 基于解析结果创建 Wiki 实体页和模块页 |
| `create_concepts_analysis_v2.py` | 分析违规类型，创建概念页和分析页 |

### 依赖安装

```bash
# Python 依赖
pip install beautifulsoup4 pyppeteer

# Node.js 依赖（用于 puppeteer）
npm install puppeteer-core

# 系统工具
# - pdftotext (poppler-utils)
# - tesseract (并安装 chi_sim 语言包)
# - pdftoppm (poppler-utils)
```

### 使用方法

```bash
# 1. 运行爬虫获取最新数据
python3 scripts/scrape_amac_v4.py

# 2. 如需单独处理 OCR
python3 scripts/ocr_pdfs.py

# 3. 解析数据并创建 Wiki 页面
python3 scripts/create_wiki.py
```

## 注意事项

1. **实体名称质量**：部分实体名称因 OCR 质量问题可能包含特殊字符（如 `;` 开头），建议定期检查并修正

2. **自律措施数据**：当前解析的实体较少（仅 1 个），可能需要检查 HTML 解析逻辑或数据源

3. **扫描件处理**：部分早期 PDF 为纯扫描件，OCR 识别效果有限，可能需要人工核实

4. **定期更新**：建议定期执行爬虫脚本获取最新数据，并重新运行 `create_wiki.py` 更新 Wiki

5. **数据源**：原始文件存储于 `raw/` 目录，不可直接修改，应通过解析脚本处理后写入 Wiki

## 数据来源

- **网站**：https://www.amac.org.cn/zlgl/
- **子模块**：
  - 纪律处分-机构：https://www.amac.org.cn/zlgl/jlcf/scfjg/
  - 异常经营：https://www.amac.org.cn/zlgl/ycjy/ycjyjgclgg/
  - 失联机构：https://www.amac.org.cn/zlgl/sljg/sljgclgg/
  - 自律措施：https://www.amac.org.cn/zlgl/zlcs/
