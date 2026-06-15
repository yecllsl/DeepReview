# DeepReview - 错题收集与智能分析Agent 设计文档

> 日期：2026-06-15
> 状态：已确认
> 架构方案：单体MCP Server + 轻量Skills

---

## 1. 项目概述

### 1.1 产品定位

基于Trae Work平台开发的K12错题收集与智能分析Agent，帮助学生通过拍照快速录入错题，AI自动完成分类、原因分析、改进方案生成和复习推荐，形成错题管理的完整闭环。

### 1.2 目标用户

K12学生（小学至高中），错题以标准学科为主（语文/数学/英语/物理/化学/生物/政治/历史/地理）。

### 1.3 核心约束

- 仅通过MCP Tools、Skills、Rules进行扩展，不开发独立UI
- AI能力优先使用Trae内置模型
- OCR+大模型组合方案，优先免费方案
- 数据仅存储在本地文件系统（JSON格式）

---

## 2. 功能模块划分

| 模块 | 核心职责 | 实现载体 |
|------|---------|---------|
| 错题采集 | 拍照/上传图片 → OCR文字提取 → AI结构化解析 | MCP Tool + Skill |
| 智能分类 | 学科分类、知识点标签、错误类型标注 | MCP Tool + Rule |
| 原因分析 | 错误根因诊断（知识漏洞/粗心/方法错误/审题失误） | MCP Tool + Skill |
| 改进方案 | 针对性学习建议、同类题推荐方向 | MCP Tool + Skill |
| 复习推荐 | 基于遗忘曲线的复习计划、薄弱知识点优先级排序 | MCP Tool + Skill |
| 数据管理 | 错题CRUD、统计查询、导出 | MCP Tools |

---

## 3. 整体架构

```
用户交互层
├── 对话式交互（自然语言触发）
└── 命令式交互（/capture, /analyze, /review, /stats, /export）
        │
Skills编排层
├── wrong-question-capture    → 错题采集流程编排
├── wrong-question-analyze    → 分析+分类+原因诊断流程
├── review-plan-generate      → 复习计划生成流程
└── wrong-question-stats      → 统计与导出流程
        │
MCP Tools层（单体Server: deep-review-mcp）
├── ocr_recognize             → OCR识别+AI结构化
├── classify_question         → 智能分类
├── analyze_error             → 错误原因分析
├── generate_improvement      → 改进方案生成
├── recommend_review          → 复习推荐
├── save_wrong_question       → 错题数据保存
├── query_wrong_questions     → 错题数据查询
├── get_statistics            → 统计查询
└── export_data               → 数据导出
        │
Rules约束层
├── classification-rules      → 分类标准与标签体系规则
├── analysis-rules            → 分析深度与输出格式规则
├── data-safety-rules         → 数据安全与隐私保护规则
└── interaction-rules         → 交互行为约束规则
        │
数据存储层
└── 本地文件系统（JSON格式）
    ├── wrong_questions/       → 错题记录
    ├── analysis_reports/      → 分析报告
    └── review_plans/          → 复习计划
```

---

## 4. MCP Tools开发规范

### 4.1 Server基本信息

- 名称：`deep-review-mcp`
- 传输协议：stdio（Trae本地调用标准方式）
- 开发语言：TypeScript + Node.js
- 包管理：npm

### 4.2 Tools接口定义

#### ocr_recognize

- 输入：`{image_path: string}`
- 输出：`{raw_text: string, structured_question: object, subject: string, grade_level: string}`
- 说明：调用PaddleOCR提取文字，再由AI结构化解析为题目、选项、答案

#### classify_question

- 输入：`{question_text: string, subject?: string}`
- 输出：`{subject: string, knowledge_points: string[], error_type: string, difficulty: string}`
- 说明：AI驱动分类，输出学科、知识点标签、错误类型、难度

#### analyze_error

- 输入：`{question_id: string, user_answer?: string, correct_answer?: string}`
- 输出：`{root_cause: string, cause_category: string, diagnosis_detail: string}`
- 说明：错误根因分析，输出原因类别和诊断详情

#### generate_improvement

- 输入：`{question_id: string, analysis_result: object}`
- 输出：`{improvement_plan: string, similar_topics: string[], study_resources: string[]}`
- 说明：生成改进方案、同类题方向、学习资源推荐

#### recommend_review

- 输入：`{student_id: string, time_range?: string}`
- 输出：`{review_plan: object, priority_topics: string[], schedule: object[]}`
- 说明：基于遗忘曲线和薄弱点生成复习计划

#### save_wrong_question

- 输入：`{question_data: object}`
- 输出：`{question_id: string, saved_path: string}`
- 说明：保存错题记录到本地JSON

#### query_wrong_questions

- 输入：`{filters: {subject?: string, knowledge_point?: string, error_type?: string, date_range?: object}}`
- 输出：`{questions: object[], total_count: number}`
- 说明：按条件查询错题

#### get_statistics

- 输入：`{group_by: "subject"|"error_type"|"knowledge_point"|"date"}`
- 输出：`{statistics: object[], trends: object}`
- 说明：统计分析错题分布和趋势

#### export_data

- 输入：`{format: "json"|"markdown", filters?: object}`
- 输出：`{file_path: string}`
- 说明：导出错题数据

### 4.3 OCR选型

- 主选：PaddleOCR（开源本地部署，无需API Key，中文识别优秀）
- 备选：Tesseract.js（纯JS方案，安装简单但中文识别率较低）
- AI结构化：OCR原始文本交Trae内置大模型，通过Prompt模板解析为结构化数据

### 4.4 数据存储格式

```json
{
  "question_id": "wq_20260615_001",
  "created_at": "2026-06-15T10:30:00Z",
  "image_path": "images/math_001.jpg",
  "raw_text": "若x²-5x+6=0，则x=",
  "structured": {
    "subject": "数学",
    "grade_level": "初二",
    "knowledge_points": ["一元二次方程", "因式分解"],
    "difficulty": "中等",
    "question_type": "计算题"
  },
  "classification": {
    "error_type": "方法错误",
    "error_category": "因式分解方法选择错误"
  },
  "analysis": {
    "root_cause": "未掌握十字相乘法的适用条件和解题步骤",
    "cause_category": "知识漏洞",
    "diagnosis_detail": "学生尝试使用公式法但计算过程中出现符号错误，说明对因式分解方法的选择判断不足"
  },
  "improvement": {
    "plan": "复习十字相乘法的适用条件和解题步骤",
    "similar_topics": ["因式分解类方程", "配方法对比"],
    "review_count": 0,
    "next_review_date": "2026-06-17"
  }
}
```

---

## 5. Skills技能设计

### 5.1 Skills清单

| Skill名称 | 触发方式 | 核心流程 | 依赖Tools |
|-----------|---------|---------|----------|
| wrong-question-capture | `/capture` 或 "帮我录入这道错题" | 图片→OCR识别→AI结构化→分类→保存 | ocr_recognize, classify_question, save_wrong_question |
| wrong-question-analyze | `/analyze` 或 "分析这道错题" | 查询错题→原因分析→改进方案生成→更新记录 | query_wrong_questions, analyze_error, generate_improvement |
| review-plan-generate | `/review` 或 "生成复习计划" | 统计薄弱点→遗忘曲线计算→生成复习计划 | get_statistics, recommend_review |
| wrong-question-stats | `/stats` 或 "查看错题统计" | 按条件查询→统计分析→格式化输出 | query_wrong_questions, get_statistics |

### 5.2 各Skill设计要点

#### wrong-question-capture（错题采集）

- 支持用户粘贴图片路径或拖拽上传
- OCR失败时提供重试机制，允许用户手动输入题目文本作为降级方案
- 结构化解析后展示给用户确认，支持修改后再保存
- 自动触发初步分类，用户可覆盖AI分类结果

#### wrong-question-analyze（错题分析）

- 支持单题深度分析和批量分析两种模式
- 分析结果以结构化报告呈现：错误类型→根因→改进建议
- 改进方案必须包含可执行的学习动作（非泛泛而谈）
- 分析完成后自动更新错题记录的analysis和improvement字段

#### review-plan-generate（复习计划）

- 基于艾宾浩斯遗忘曲线设定复习间隔：1天→3天→7天→14天→30天
- 优先推荐错误频率高、知识漏洞类的错题
- 输出包含每日复习清单，标注预计复习时长
- 支持按学科筛选生成复习计划

#### wrong-question-stats（统计查询）

- 支持多维度统计：学科分布、错误类型分布、知识点薄弱度排名
- 支持时间趋势分析（周/月错题量变化）
- 输出为Markdown格式，可直接在对话中展示

---

## 6. Rules规则体系

### 6.1 classification-rules（分类规则）

1. 学科必须从K12标准学科列表中选择：语文/数学/英语/物理/化学/生物/政治/历史/地理
2. 错误类型限定4类：知识漏洞/粗心失误/方法错误/审题失误
3. 知识点标签必须来自学科知识图谱，不可自由生成
4. 难度分3级：基础/中等/困难

### 6.2 analysis-rules（分析规则）

1. 原因分析必须具体到知识点层面，禁止笼统结论
2. 改进方案必须包含：具体学习动作+建议时长+验证方式
3. 同类题推荐至少3个方向
4. 分析结果必须用户确认后才写入记录

### 6.3 data-safety-rules（数据安全规则）

1. 所有数据仅存储在本地，禁止上传到任何外部服务
2. 图片文件存储在项目目录下，不外传
3. 导出数据前需用户确认
4. 不记录用户姓名等个人身份信息

### 6.4 interaction-rules（交互规则）

1. 命令格式：`/capture`、`/analyze`、`/review`、`/stats`、`/export`
2. 自然语言识别关键词：录入/分析/复习/统计/导出
3. 每次操作结果必须给出明确反馈
4. 错误发生时提供降级方案而非直接报错

---

## 7. 数据流程设计

### 7.1 核心数据流

**采集流**：图片 → `ocr_recognize` → `classify_question` → 用户确认 → `save_wrong_question`

**分析流**：`query_wrong_questions` → `analyze_error` → `generate_improvement` → 用户确认 → 更新记录

**复习流**：`get_statistics` → `recommend_review` → 生成复习计划 → 保存

**统计流**：`query_wrong_questions` → `get_statistics` → 格式化输出

### 7.2 数据流图

```
┌─────────────────────────────────────────────────────┐
│                    用户交互入口                        │
│         对话式（自然语言）/ 命令式（/xxx）              │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  Skills编排层    │ ← Rules约束行为
              │  识别意图&编排   │
              └────────┬────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────▼────┐  ┌─────▼─────┐ ┌────▼────┐
    │采集流程  │  │分析流程    │ │复习流程  │
    │capture  │  │analyze    │ │review   │
    └────┬────┘  └─────┬─────┘ └────┬────┘
         │             │             │
    ┌────▼─────────────▼─────────────▼────┐
    │         MCP Tools 层                 │
    │  ocr → classify → analyze → improve │
    │  → recommend → crud → stats → export│
    └────────────────┬───────────────────┘
                     │
              ┌──────▼──────┐
              │  本地存储层   │
              │  JSON文件    │
              │  wrong_questions/ │
              │  analysis_reports/│
              │  review_plans/    │
              └─────────────┘
```

---

## 8. 关键技术难点及解决方案

| 难点 | 影响 | 解决方案 |
|------|------|---------|
| OCR识别准确率 | 手写体、公式、图表识别困难 | 1. PaddleOCR对中文手写体优化较好 2. AI后处理纠错：将OCR原文交大模型修正 3. 降级方案：允许用户手动输入/修正 |
| 数学公式识别 | 数学符号、上下标、分数等特殊格式 | 1. OCR提取后由AI模型识别公式结构 2. 输出时用LaTeX格式表示公式 3. 复杂公式建议用户手动补充 |
| 知识点标签一致性 | AI每次可能生成不同表述的知识点 | 1. Rules约束：知识点必须从预定义图谱选择 2. MCP Tool内置K12知识点映射表 3. 模糊匹配已有标签，避免重复 |
| 遗忘曲线复习调度 | 需要跟踪每道题的复习状态 | 1. 每道错题记录review_count和next_review_date 2. recommend_review Tool按日期筛选到期题目 3. 复习完成后自动更新下次复习日期 |
| 分析质量稳定性 | 大模型输出可能不稳定 | 1. Rules约束输出格式和深度 2. Skill中固化分析Prompt模板 3. 关键字段结构化输出，减少自由文本 |

---

## 9. 开发里程碑

| 阶段 | 交付物 | 验收标准 |
|------|-------|---------|
| M1：基础框架 | MCP Server骨架 + 数据存储 + CRUD Tools | save_wrong_question/query_wrong_questions可正常调用，数据持久化到本地JSON |
| M2：采集能力 | ocr_recognize + classify_question + capture Skill | 上传图片→OCR识别→结构化解析→分类→保存，全流程跑通 |
| M3：分析能力 | analyze_error + generate_improvement + analyze Skill | 单题分析输出完整的根因诊断+改进方案，用户确认后写入记录 |
| M4：复习推荐 | recommend_review + get_statistics + review/stats Skill | 基于错题数据生成复习计划，统计查询多维度可用 |
| M5：Rules+集成 | 全部Rules + 交互优化 + 端到端测试 | 命令/对话双模式触发正常，Rules约束生效，全流程闭环 |

---

## 10. 测试验收标准

| 维度 | 验收标准 |
|------|---------|
| 功能完整性 | 4个核心功能（采集/分类/分析/复习）全部可用，5个命令全部响应 |
| OCR准确率 | 印刷体识别率≥90%，手写体识别率≥70%（AI纠错后） |
| 分类准确率 | 学科分类准确率≥95%，错误类型分类准确率≥80% |
| 分析质量 | 原因分析具体到知识点层面（非笼统结论），改进方案包含可执行动作 |
| 数据安全 | 所有数据仅存本地，无任何外部数据传输（OCR本地部署） |
| 交互体验 | 命令式响应<3秒，对话式意图识别准确率≥90% |
| 降级能力 | OCR失败时可手动输入，AI分析异常时有友好提示和重试机制 |
