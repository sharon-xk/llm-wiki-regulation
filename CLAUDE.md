# 【最高优先级】Python代码执行强制规则
1. 绝对禁止使用：python -c、python3 -c 任何形式的命令行内联执行代码！
2. 所有Python代码，必须先写入完整的.py脚本文件，不允许任何临时单行执行。
3. 项目脚本放在/scripts路径下并及时更新。如果是临时一次性执行的检查语句，脚本放在/scripts/tmp下再执行，执行完之后可删除。
4. 唯一合法执行命令：python 文件名.py 或 python3 文件名.py
5. 标准执行流程：创建/编辑py文件 → 写入完整代码 → 执行文件脚本
6. 禁止任何交互式、内联式、临时式Python代码执行，无任何例外

# CLAUDE.md — 金融监管处罚知识库

## 概述

这是一个用于收集、整理和查询中国证券投资基金业协会（AMAC）自律管理处罚信息的知识库。
团队成员通过自然语言提问，LLM 负责维护 wiki 并生成答案。

## 数据来源

- **网站**：https://www.amac.org.cn/zlgl/
- **子模块**：
  - 纪律处分-机构：https://www.amac.org.cn/zlgl/jlcf/scfjg/
  - 异常经营：https://www.amac.org.cn/zlgl/ycjy/ycjyjgclgg/
  - 失联机构：https://www.amac.org.cn/zlgl/sljg/sljgclgg/
  - 自律措施：https://www.amac.org.cn/zlgl/zlcs/
- **原文存储**：`raw/` 目录下，按模块分类存放爬取的原始页面

## 目录结构

```
llm-wiki-regulation/
├── CLAUDE.md           # 本文件，schema 定义
├── index.md            # 知识库总索引（LLM 维护）
├── log.md              # 操作日志
├── scripts/            # 处理脚本
├── raw/                # 原始来源（不可修改）
│   ├── 纪律处分/
│   ├── 异常经营/
│   ├── 失联机构/
│   └── 自律措施/
└── wiki/               # LLM 生成的知识页面
    ├── entities/       # 市场主体（机构/个人）
    ├── modules/        # 按模块分类的处罚记录
    ├── concepts/       # 违规类型、概念定义
    └── analysis/       # 分析、对比、趋势页面
```

## 页面规范

### 实体页 (entities/)
- **命名**：`机构名.md`，仅保留完整公司名，去掉其他杂乱文字
- **内容**：机构基本信息、被处罚记录汇总、处罚类型分布
- **Frontmatter**：
  ```yaml
  ---
  type: entity
  name: XXX基金管理有限公司
  subtype: 基金管理人
  source_count: 5
  first_incident: 2023-03
  latest_incident: 2024-11
  tags: [纪律处分, 异常经营]
  ---
  ```

### 模块页 (modules/)
- **命名**：`模块名.md`（如 `纪律处分.md`）
- **内容**：该模块下的处罚记录列表、时间线摘要

### 概念页 (concepts/)
- **命名**：`违规类型.md`（如 `违规募集.md`）
- **内容**：该违规类型的定义、典型案例汇总、处罚依据

### 分析页 (analysis/)
- **命名**：`分析_主题.md`（如 `分析_2024年处罚趋势.md`）
- **内容**：跨页面综合分析、对比表格、趋势图表

### 原始页 (raw/)
- **命名**：`日期_标题.md`
- **内容**：保留 AMAC 原文内容，供溯源核实

## 工作流程

### Ingest（摄取）流程

1. 爬取 AMAC 网站指定模块的处罚列表页面
2. 逐一进入详情页，抓取全文存入 `raw/` 对应子目录
3. 读取 raw 文件，提炼关键信息：
   - 被处罚主体名称
   - 违规类型/事由
   - 处罚措施（警告、罚款、取消资格等）
   - 处罚日期
   - 依据法规
4. 更新或创建 `wiki/entities/` 中的实体页
5. 更新 `wiki/modules/` 中的模块页
6. 识别违规类型，更新或创建 `wiki/concepts/` 中的概念页
7. 更新 `index.md` 中的目录索引
8. 在 `log.md` 中记录本次 ingest 操作

### Query（查询）流程

1. 理解用户问题，判断需要查询哪些页面
2. 搜索 `index.md` 定位相关页面
3. 读取相关实体页/模块页/概念页
4. 综合信息生成答案，附上引用来源
5. 若答案有价值（如对比分析、案例汇总），询问用户是否写入 wiki

### Lint（健康检查）流程

定期执行：
- 检查实体页是否有缺失的处罚记录
- 检查概念页是否有遗漏的典型案例
- 识别同一违规行为的跨模块矛盾记录
- 标记超过 6 个月未更新的实体页（可能遗漏新数据）
- 生成待补充列表供团队核查

## 索引格式

`index.md` 按以下分类组织，每条目包含链接 + 一句话摘要：

```markdown
## 实体 (entities)
- [机构名](wiki/entities/机构名.md) — 摘要

## 模块 (modules)
- [纪律处分](wiki/modules/纪律处分.md) — X 条记录

## 概念 (concepts)
- [违规类型名](wiki/concepts/违规类型名.md) — X 个案例

## 分析 (analysis)
- [分析标题](wiki/analysis/分析_标题.md) — 日期
```

## 日志格式

`log.md` 每条记录格式：

```markdown
## [YYYY-MM-DD] ingest | 来源模块
- 操作描述
- 创建/更新的页面列表
```

## 工具偏好

- 搜索：`qmd`（本地 markdown 搜索工具，支持 BM25/向量混合搜索）
- 如无 `qmd`，依赖 `index.md` 线性搜索
- 图片下载到本地 `raw/assets/`，避免链接失效
- 定期用 `grep` 解析 `log.md` 回顾操作历史