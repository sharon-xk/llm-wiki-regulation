#!/usr/bin/env python3
"""
更新 index.md 和 log.md.
用法: python3 scripts/wiki/update_index.py [--log "操作描述"]
"""
import sys
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).parent.parent.parent
WIKI_DIR = BASE_DIR / "wiki"


def update_index():
    entities = sorted((WIKI_DIR / "entities").glob("*.md"))
    concepts = sorted((WIKI_DIR / "concepts").glob("*.md"))
    analysis = sorted((WIKI_DIR / "analysis").glob("*.md"))

    content = f"""# 基金业协会处罚知识库

> 本知识库收集整理中国证券投资基金业协会（AMAC）自律管理处罚信息，供查询和分析。

---

## 实体 (entities)

- 共 {len(entities)} 个实体

## 模块 (modules)

- [纪律处分](wiki/modules/纪律处分.md) — 纪律处分决定书
- [异常经营](wiki/modules/异常经营.md) — 异常经营私募基金管理人
- [失联机构](wiki/modules/失联机构.md) — 失联私募基金管理人
<!-- - [自律措施](wiki/modules/自律措施.md) — 自律措施（数据停更于2020年）-->

## 概念 (concepts)

"""
    for f in concepts[:20]:
        content += f"- [{f.stem}](wiki/concepts/{f.stem}.md)\n"
    if len(concepts) > 20:
        content += f"\n... 还有 {len(concepts) - 20} 个概念页\n"

    content += "\n## 分析 (analysis)\n\n"
    for f in analysis:
        content += f"- [{f.stem}](wiki/analysis/{f.stem}.md)\n"

    content += f"\n---\n*最后更新：{date.today().isoformat()}*\n"
    (BASE_DIR / "index.md").write_text(content, encoding="utf-8")
    print(f"index.md 已更新 ({len(entities)} entities, {len(concepts)} concepts, {len(analysis)} analyses)")


def update_log(description="全量更新"):
    log_file = BASE_DIR / "log.md"
    existing = log_file.read_text(encoding="utf-8") if log_file.exists() else "# 操作日志\n"
    entry = f"\n## [{date.today().isoformat()}] {description}\n"
    existing += entry
    log_file.write_text(existing, encoding="utf-8")
    print(f"log.md 已更新")


def main():
    log_msg = None
    args = sys.argv[1:]
    if "--log" in args and args.index("--log") + 1 < len(args):
        log_msg = args[args.index("--log") + 1]

    update_index()
    update_log(log_msg or "更新 index / log")


if __name__ == "__main__":
    main()
