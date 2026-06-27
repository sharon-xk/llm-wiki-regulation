# 知识库结构说明

LLM Wiki 的知识库结构权威定义。包含目录组织、页面类型规范、链接约定。

> **机器可读的结构契约**（字段 schema、create/merge 规则、模板）见同目录的 [profile.json](profile.json)。本文档是其人读版说明，两者内容保持一致。

---

## 一、整体目录结构

```
llm-wiki-regulation/
├── CLAUDE.md           # AI 操作规范
├── README.md           # 项目首页，数据概况
├── index.md            # 知识库总索引（LLM 维护）
├── log.md              # 操作日志
├── docs/
│   └── schema/         # 知识库结构定义
│       ├── schema_design.md # 本文件（人读版）
│       └── profile.json # 结构契约（机器读版）
├── scripts/            # 处理脚本（详见 scripts/README.md）
├── raw/                # 原始来源（不可修改）
│   ├── 纪律处分/
│   ├── 异常经营/
│   ├── 失联机构/
│   └── 自律措施/
└── wiki/               # LLM 生成的知识页面
    ├── institutions/   # 机构（基金管理人等）
    ├── persons/        # 人员（基金经理/高管等）
    ├── products/       # 产品类型（规划中）
    ├── violations/     # 违规类型
    ├── regulations/    # 涉及法规
    └── analysis/       # 分析、对比、趋势页面
```

## 二、分层架构

| 层 | 含义 | 包含类型 |
|----|------|---------|
| **fact** | 客观事实层：来源于监管文书的结构化数据，可追溯、可校验 | institution · violation · regulation |
| **experience** | 分析洞察层：基于 fact 层的统计、趋势、风险研判 | analysis |
| **planned** | 规划中类型：已定义 schema 与模板，待数据接入后启用 | person · product |

## 三、页面类型规范

### 机构页 (institutions/)

- **层**：fact
- **命名**：`机构名.md`，仅保留完整公司名，去掉「以下简称xxx」、公文前缀及 OCR 噪声。同名加后缀区分。
- **内容**：机构基本信息、被处罚记录汇总（每案含字号/日期/来源/违规行为/对应 violation 链接/处罚措施/法规依据）、违规类型汇总
- **Frontmatter**：
  ```yaml
  ---
  type: institution
  name: XXX基金管理有限公司
  subtype: 私募基金管理人       # enum: 私募基金管理人/证券公司/公募基金公司/期货公司/...
  source: AMAC                 # enum: AMAC/证监会/交易所（监管主体）
  source_count: 5
  first_incident: 2023-03
  latest_incident: 2024-11
  tags: [纪律处分, 异常经营]     # 来源栏目，支持多个
  ---
  ```
- **合并规则**：合并同名机构主体及处罚案件。若主体名称因 OCR 产生错别字（如「稻满/稻暮」「常青藤/常青苹」），应合并为同一主体。

### 人员页 (persons/)

- **层**：planned（待接入纪律处分-人员数据）
- **命名**：`姓名.md`，同名人员加机构后缀区分（如 `姓名_机构.md`）
- **内容**：自然人基本信息（职务/从业资格号）、处罚记录、关联机构
- **Frontmatter**：`type: person`，含 `org`（链接到 institutions/）、`position`、`qualification_no`、`source` 等字段
- **双向链接**：人员页 `org` → 机构页；机构页"相关人员"→ 人员页

### 产品页 (products/)

- **层**：planned（待建，按管理人类型分类）
- **命名**：`产品类型名.md`，如 `证券公司集合资管计划.md`
- **内容**：产品定义、运作模式、监管框架、易发违规类型、典型案例
- **Frontmatter**：`type: product`，含 `manager_type`（桥接 institution）、`product_form`（集合/定向/契约型）、`typical_concepts`（链接 violations）等字段
- **合并规则**：历史承接关系的产品需合并并标注沿革（如「直投基金」并入「证券公司私募投资基金」）

### 违规类型页 (violations/)

- **层**：fact
- **命名**：`违规类型.md`（如 `违规募集.md`）
- **内容**：该违规类型的概述、时间分布、典型案例汇总、违规构成要件、处罚依据、处罚措施
- **Frontmatter**：
  ```yaml
  ---
  type: violation
  name: 违规募集
  description: 违规募集相关违规行为及处罚案例
  case_count: 86
  tags: [违规类型, 纪律处分]
  last_updated: 2026-05-19
  ---
  ```
- **合并规则**：合并语义相同的违规类型（如「委托无资格机构募集」归入「违规募集」）

### 法规页 (regulations/)

- **层**：fact
- **命名**：`法规全称.md`（如 `私募投资基金监督管理暂行办法.md`）
- **内容**：法规概述、关联违规类型（含引用次数）、高频引用条款、典型案例
- **Frontmatter**：
  ```yaml
  ---
  type: regulation
  name: 私募投资基金监督管理暂行办法
  short_name: 私募基金监管办法
  issuing_body: 中国证监会
  effective_date: 2014-08-21
  cited_count: 456
  tags: [信息披露违规, 未按规定登记备案]   # violation 链接数组
  ---
  ```
- **法规名映射表**：`scripts/config/reg_name_map.json`，格式 `{"OCR变体/简称": "标准全称"}`，供程序归一化读取，人工维护

### 分析页 (analysis/)

- **层**：experience
- **命名**：`分析_主题.md`（如 `分析_2024年处罚趋势.md`）
- **内容**：分析说明（口径/数据范围/统计方法）、数据表格、分析结论、数据更新日期。所有结论须可回溯到 fact 层数据，不得编造。
- **Frontmatter**：`type: analysis`，含 `description`、`date`、`tags`、`data_source`（覆盖的数据来源栏目）

### 原始页 (raw/)

- **命名**：`日期_标题.md`
- **内容**：保留 AMAC 原文内容，供溯源核实

## 四、数据来源栏目

机构页通过 `source` 字段（监管主体）和 `tags` 字段（来源栏目）标记数据来源：

| 栏目 | 说明 |
|------|------|
| 纪律处分 | 纪律处分决定书，含机构和个人 |
| 异常经营 | 异常经营机构处理公告 |
| 失联机构 | 失联机构处理公告 |
| 自律措施 | 自律管理措施决定（数据停更于2020年） |

## 五、链接约定

各类节点间的双向链接规范：

| 方向 | 说明 |
|------|------|
| institution → violation | 机构页「违规行为对应的违规类型」段落 |
| violation → institution | 违规类型页「典型案例」段落 |
| regulation → violation | 法规页「关联违规类型」「高频条款」段落 |
| regulation → institution | 法规页「典型案例」段落 |
| person → institution | 人员页 org 字段 + 正文「职务 @ 机构」 |
| product → institution | 产品页 manager_type 字段（按 subtype 桥接） |
| product → violation | 产品页 typical_concepts 字段 |
| product → regulation | 产品页 legal_basis 字段 |

## 六、索引格式

`index.md` 按以下分类组织，每条目包含链接 + 一句话摘要：

```markdown
## 机构 (institutions)
- [机构名](wiki/institutions/机构名.md) — 摘要

## 人员 (persons)
- [姓名](wiki/persons/姓名.md) — 职务 @ 机构

## 违规类型 (violations)
- [违规类型名](wiki/violations/违规类型名.md) — X 个案例

## 分析 (analysis)
- [分析标题](wiki/analysis/分析_标题.md) — 日期
```
