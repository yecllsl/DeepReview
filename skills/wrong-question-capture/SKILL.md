---
name: wrong-question-capture
description: Use when 用户想录入错题、拍照识别题目、添加错题记录、上传错题图片
---

# 错题采集流程

## Overview

K12错题采集助手，负责将纸质/图片错题转化为结构化数据并保存。核心流程：OCR识别 → AI结构化解析 → 智能分类 → 用户确认 → 保存记录。

## When to Use

- 用户说"录入错题"、"拍照录题"、"添加错题"、"上传错题"
- 用户提供错题图片路径或要求直接输入题目文本
- 用户需要将错题保存到本地数据库

## Workflow

### 1. 获取图片
要求用户提供错题图片路径，或允许直接输入题目文本。

### 2. OCR识别
调用 `deep-review-mcp/ocr_recognize` Tool。
- 失败时提示用户手动输入题目文本

### 3. AI结构化解析
用返回的 `parse_prompt` 调用AI模型解析，提取：
- 学科、年级段
- 知识点标签
- 难度、题型
- 题目内容、选项、正确答案

### 4. 展示确认
将解析结果以结构化格式展示给用户，请用户确认或修改。

### 5. 智能分类
调用 `deep-review-mcp/classify_question` Tool，用 `classify_prompt` 调用AI分类，确定：
- 错误类型（知识漏洞/粗心失误/方法错误/审题失误）
- 错误细分类别
- 相关知识点

### 6. 展示分类
将分类结果展示给用户，请用户确认或修改。

### 7. 保存记录
调用 `deep-review-mcp/save_wrong_question`，生成 question_id（格式：wq_YYYYMMDD_NNN）。

## Quick Reference

| 步骤 | Tool | 降级方案 |
|------|------|----------|
| OCR识别 | `ocr_recognize` | 手动输入题目文本 |
| 结构化解析 | AI模型 + `parse_prompt` | 标记待确认 |
| 智能分类 | `classify_question` | 标记待确认 |
| 保存记录 | `save_wrong_question` | - |

## Common Mistakes

- **OCR失败直接报错**：应提示用户手动输入，而非终止流程
- **跳过用户确认**：分类和解析结果必须经用户确认后才保存
- **知识点自由生成**：知识点必须来自学科知识图谱，不可自由生成
- **question_id格式错误**：必须使用 wq_YYYYMMDD_NNN 格式

## 约束规则

- 学科必须从K12标准列表选择：语文/数学/英语/物理/化学/生物/政治/历史/地理
- 错误类型限定4类：知识漏洞/粗心失误/方法错误/审题失误
- 知识点标签必须来自学科知识图谱
- 分类结果必须经用户确认后才保存
