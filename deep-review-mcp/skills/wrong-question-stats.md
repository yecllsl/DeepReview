---
name: wrong-question-stats
description: 错题统计查询流程编排
triggers:
  - command: /stats
  - keywords: ["错题统计", "查看统计", "错题分布", "薄弱点"]
---

# 错题统计查询流程

1. **确定维度**：subject/error_type/knowledge_point/date
2. **查询统计**：调用 `get_statistics`
3. **格式化输出**：Markdown表格展示

支持导出：调用 `export_data` 导出为JSON或Markdown
