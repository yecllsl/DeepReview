---
name: wrong-question-stats
command: /stats
description: Use when 用户想查看错题统计、查看错题分布、了解薄弱点、导出错题数据
---

# 错题统计查询流程

## Overview

错题统计分析助手，负责按不同维度统计错题分布和趋势。核心流程：确定统计维度 → 查询统计 → 格式化输出。

## When to Use

- 用户说"错题统计"、"查看统计"、"错题分布"、"薄弱点"
- 用户想了解错题在各维度的分布情况
- 用户想导出错题数据

## Workflow

### 1. 确定维度
询问用户想按哪个维度统计：
- `subject`：按学科分组
- `error_type`：按错误类型分组
- `knowledge_point`：按知识点分组
- `date`：按日期分组

### 2. 查询统计
调用 `get_statistics`，传入 `group_by` 参数。

### 3. 格式化输出
将统计结果以Markdown表格形式展示：
- 维度名称
- 错题数量
- 占比（可选）

### 4. 导出（可选）
如果用户要求导出，调用 `export_data`，支持：
- JSON格式
- Markdown格式

## Quick Reference

| 维度 | group_by 参数 | 说明 |
|------|---------------|------|
| 学科 | `subject` | 按语文/数学/英语等分组 |
| 错误类型 | `error_type` | 按知识漏洞/粗心失误等分组 |
| 知识点 | `knowledge_point` | 按具体知识点分组 |
| 日期 | `date` | 按录入日期分组 |

## Common Mistakes

- **未解释统计维度**：应说明各维度的含义，帮助用户选择
- **表格格式混乱**：使用标准Markdown表格语法
- **导出前未确认**：导出数据前需用户确认

## 约束规则

- 导出数据前需用户确认
- 输出为Markdown格式，可直接在对话中展示
- 支持导出为JSON或Markdown文件
