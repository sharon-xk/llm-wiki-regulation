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
    institutions = sorted((WIKI_DIR / "institutions").glob("*.md"))
    persons = sorted((WIKI_DIR / "persons").glob("*.md"))
    violations = sorted((WIKI_DIR / "violations").glob("*.md"))
    analysis = sorted((WIKI_DIR / "analysis").glob("*.md"))

    content = f"""# 基金业协会处罚知识库

> 本知识库收集整理中国证券投资基金业协会（AMAC）自律管理处罚信息，供查询和分析。

---

## 机构 (institutions)

- 共 {len(institutions)} 个机构（来源：AMAC）

## 人员 (persons)

- 共 {len(persons)} 个人员

## 违规类型 (violations)

"""
    for f in violations[:20]:
        content += f"- [{f.stem}](wiki/violations/{f.stem}.md)\n"
    if len(violations) > 20:
        content += f"\n... 还有 {len(violations) - 20} 个违规类型页\n"

    content += "\n## 分析 (analysis)\n\n"
    for f in analysis:
        content += f"- [{f.stem}](wiki/analysis/{f.stem}.md)\n"

    content += f"\n---\n*最后更新：{date.today().isoformat()}*\n"
    (BASE_DIR / "index.md").write_text(content, encoding="utf-8")
    print(f"index.md 已更新 ({len(institutions)} institutions, {len(persons)} persons, {len(violations)} violations, {len(analysis)} analyses)")


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
