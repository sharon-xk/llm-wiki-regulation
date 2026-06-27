# 基金业协会处罚知识库

本知识库用于收集、整理和查询中国证券投资基金业协会（AMAC）自律管理处罚信息。

> **AI 协作说明**：本项目的 wiki 由 LLM 辅助维护，操作规范见 [CLAUDE.md](CLAUDE.md)。
> **脚本管线**：数据处理脚本的使用说明见 [scripts/README.md](scripts/README.md)。
> **知识库结构**：目录组织、页面类型规范、字段 schema 见 [docs/schema/schema_design.md](docs/schema/schema_design.md)。


## 数据来源

- **网站**：[中国证券投资基金业协会 - 自律管理](https://www.amac.org.cn/zlgl/)
- **子模块**：
  - 纪律处分（机构）：https://www.amac.org.cn/zlgl/jlcf/scfjg/
  - 异常经营：https://www.amac.org.cn/zlgl/ycjy/ycjyjgclgg/
  - 失联机构：https://www.amac.org.cn/zlgl/sljg/sljgclgg/
  - 自律措施：https://www.amac.org.cn/zlgl/zlcs/

## 数据收集汇总

| 模块 | 原始文件 | 实体数 |
|------|---------|--------|
| 纪律处分-机构 | 448 PDFs (391 TXTs) | 339 |
| 异常经营 | 107 HTMLs | 200 |
| 失联机构 | 111 HTMLs | 320 |

**总计：** 854 个实体页

> **未建实体的数据**：
> - 纪律处分-人员：950 PDFs (817 TXTs)，732 条记录，暂未创建独立实体页
> - 自律措施：27 HTMLs，1 条记录，暂未创建独立实体页


## 注意事项

1. **实体名称质量**：部分实体名称因 OCR 质量问题可能包含特殊字符，建议定期检查并修正

2. **纪律处分-人员**：原始数据已有 732 条人员处罚记录，暂未创建独立实体页，后续可补充

3. **自律措施数据**：当前仅 1 条记录，数据量较少，可能需要检查解析逻辑或数据源

4. **扫描件处理**：部分早期 PDF 为纯扫描件，OCR 识别效果有限，可能需要人工核实

5. **定期更新**：建议定期执行增量脚本获取最新数据，详见 [scripts/README.md](scripts/README.md)
