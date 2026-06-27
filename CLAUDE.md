# CLAUDE.md — 金融监管处罚知识库

> **项目概况和数据统计**见 [README.md](README.md)。
> **脚本目录结构和使用说明**见 [scripts/README.md](scripts/README.md)。
> **知识库结构**（目录组织、页面类型规范、字段 schema、链接约定）见 [docs/schema/schema_design.md](docs/schema/schema_design.md)，机器可读的结构契约见 [docs/schema/profile.json](docs/schema/profile.json)。

## 【最高优先级】Python 代码执行强制规则

1. 绝对禁止使用：python -c、python3 -c 任何形式的命令行内联执行代码！
2. 所有Python代码，必须先写入完整的.py脚本文件，不允许任何临时单行执行。
3. 项目脚本放在/scripts路径下并及时更新。如果是临时一次性执行的检查语句，脚本放在/scripts/tmp下再执行，执行完之后可删除。
4. 唯一合法执行命令：python 文件名.py 或 python3 文件名.py
5. 标准执行流程：创建/编辑py文件 → 写入完整代码 → 执行文件脚本
6. 禁止任何交互式、内联式、临时式Python代码执行，无任何例外

## 概述

这是一个用于收集、整理和查询中国证券投资基金业协会（AMAC）自律管理处罚信息的知识库。
团队成员通过自然语言提问，LLM 负责维护 wiki 并生成答案。

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
4. 更新或创建 `wiki/institutions/` 中的机构页
5. 更新 `wiki/institutions/` 中相关机构的 source/tags 字段
6. 识别违规类型，更新或创建 `wiki/violations/` 中的违规类型页
7. 更新 `index.md` 中的目录索引
8. 在 `log.md` 中记录本次 ingest 操作
9. 执行数据质量校验（见下方"数据质量校验"），FAIL 项记入 `log.md`

### 数据质量校验

每次 ingest 完成后必须执行以下检查，不得跳过。

**1. 名称规范**
- 文件名和 frontmatter `name` 不得包含"以下简称XXX"等 OCR 残留
- 文件名与 `name` 字段必须一致

**2. Frontmatter 完整性**
- 必填字段以 [docs/schema/profile.json](docs/schema/profile.json) 中各类型的 schema 为准
- `source_count` = 正文实际案件数
- `tags` 覆盖该 institution 涉及的全部模块
- `first_incident` ≤ `latest_incident`，且不能是未来日期

**3. 内容结构**
- 三个 section 缺一不可：`## 基本信息`、`## 处罚记录`、`## 违规类型汇总`
- 违规类型必须链接到 `wiki/violations/` 页面
- 正文中的字号、日期不得有遗漏

**4. 抽样验证**
随机抽 10-15 个 institution，比对原始文件与机构页的日期、字号、处罚措施。通过率 < 90% 视为不合格。

**5. 校验输出**
上述检查整合到 `scripts/qualify/validate.py`。校验结果、解析失败的 institution 清单（原始文本 < 40 行、OCR 无有效输出、有字号无违规行为）一并写入 `log.md`。

### Query（查询）流程

1. 理解用户问题，判断需要查询哪些页面
2. 搜索 `index.md` 定位相关页面
3. 读取相关机构页/人员页/违规类型页
4. 综合信息生成答案，附上引用来源
5. 若答案有价值（如对比分析、案例汇总），询问用户是否写入 wiki

### Lint（健康检查）流程

定期执行：
- 检查机构页是否有缺失的处罚记录
- 检查违规类型页是否有遗漏的典型案例
- 识别同一违规行为的跨来源矛盾记录
- 标记超过 6 个月未更新的机构页（可能遗漏新数据）
- 生成待补充列表供团队核查

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
