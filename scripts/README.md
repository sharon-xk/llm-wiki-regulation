# Scripts 说明

本文档记录 `/scripts` 目录下各脚本的用途和使用方法。

## Entity 规范化脚本

### normalize_entities.py

规范化entity文件命名和内容。

**规则：**
1. 个人主体：文件名只保留姓名，提取性别/出生日期/任职信息到frontmatter
2. 公司主体：去掉文件名中的"（以下简称XXX）"后缀，提取简称到short_name属性
3. 合并重复实体（同一公司/个人只保留一条记录）

**用法：**
```bash
python3 scripts/normalize_entities.py          # 干跑模式
python3 scripts/normalize_entities.py --execute # 实际执行
```

---

### fix_entity_filenames.py

修复entity文件命名问题。

**功能：**
1. 清理文件名中的非法字符（`,;` 等开头）
2. 处理空文件名（如 `.md`）
3. 确保文件名与frontmatter中的name一致

---

### fix_frontmatter_names.py

修复entity的frontmatter中的name字段和文件名，使其与文件名一致。清理name中的"（以下简称XXX）"部分，并提取简称到short_name字段。

---

### cleanup_abbreviation.py

清理文件名中的"（以下简称XXX）"部分。

---

### cleanup_abbreviation_v2.py

彻底清理文件名中的各种"简称"变体。

**清理的模式：**
- （以下简称XXX）
- 〈以下简称XXX）
- (以下简称XXX)
- 以下简称XXX
- 〈以下简XXX）
- 等等

---

### fix_truncated_filenames.py

修复截断的entity文件名（括号不闭合）。从文件内容中提取正确的name并重命名。

---

### cleanup_filenames.py

彻底清理entity文件名的非法字符。

**功能：**
- 清理文件名中的非法字符开头
- 从frontmatter提取正确名称重命名文件

---

## 其他脚本

### create_wiki.py

创建wiki页面。根据 `parsed_txt_results.json` 和 `parsed_html_results.json` 生成 entities、modules 等页面。

### parse_txt.py

解析 txt 格式的原始文件。

### parse_html.py

解析 HTML 格式的原始文件。

### scrape_amac.py / scrape_amac_v4.py

爬取 AMAC 网站内容。

### ocr_pdfs.py

对 PDF 文件进行 OCR 识别。

---

## 使用流程

1. 使用 `scrape_amac*.py` 爬取数据到 `raw/`
2. 使用 `parse_txt.py` / `parse_html.py` 解析原始文件
3. 使用 `create_wiki.py` 生成 wiki 页面
4. 如需规范化entity命名，执行：
   - `normalize_entities.py --execute`
   - `fix_entity_filenames.py`
   - `fix_frontmatter_names.py`
   - `cleanup_abbreviation_v2.py`
   - `fix_truncated_filenames.py`