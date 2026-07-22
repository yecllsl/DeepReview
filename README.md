# DeepReview - K12错题收集与智能分析Agent

基于 Trae Work 平台的 K12 错题收集与智能分析解决方案，帮助学生通过拍照快速录入错题，AI 自动完成分类、原因分析、改进方案生成和复习推荐。提供本地 Web 可视化界面，直观展示错题分布、趋势和薄弱点。

## 核心功能

- 📷 **错题采集**: 拍照识别 + OCR文字提取 + AI结构化解析
- 🏷️ **智能分类**: 学科分类、知识点标签、错误类型标注
- 🔍 **原因分析**: 错误根因诊断 (知识漏洞/粗心/方法错误/审题失误)
- 📝 **改进方案**: 针对性学习建议、同类题推荐方向
- 📅 **复习推荐**: 基于遗忘曲线的复习计划
- 📊 **统计分析**: 多维度错题分布和趋势分析
- 🌐 **Web 可视化**: 本地 Web 界面，含概览 Dashboard、错题列表与详情、统计图表、复习追踪四大页面

## 系统架构

```
用户交互层
├── 对话式交互 (命令/自然语言)
└── Web 可视化界面 (本地浏览器 http://127.0.0.1:8001)
    ↓
Skills 编排层 (流程编排: capture / analyze / review / stats)
    ↓
MCP Tools 层 (deep-review-mcp, 11 个 Tools)
├── Web 可视化子模块 (FastAPI + HTMX + Alpine.js + ECharts)
    ↓
Rules 约束层 (分类/分析/安全/交互规则)
    ↓
数据存储层 (本地JSON文件, 原子写入)
```

## 技术栈

- **MCP Server**: Python 3.12+ / FastMCP
- **Web 可视化**: FastAPI + HTMX + Alpine.js + ECharts
- **OCR 引擎**: PaddleOCR (本地部署，无需API Key)
- **数据存储**: JSON 文件 (本地存储，数据安全)
- **包管理**: uv (现代高速Python包管理器)

## 安装

### 前置要求

- Python 3.12+
- uv 包管理器
- Trae Work IDE

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/yecllsl/deep-review.git
cd deep-review
```

#### 2. 安装依赖

```powershell
cd deep-review-mcp
uv venv
uv pip install -e .
```

#### 3. 配置 Trae Work

1. 打开 Trae Work
2. 进入 **设置 → MCP配置**
3. 点击 **添加MCP服务器**
4. 填写配置：

| 字段 | 值 |
|------|-----|
| 服务器名称 | `deep-review-mcp` |
| 命令 | `uv` |
| 参数 | `run deep-review-mcp` |
| 工作目录 | `你的项目路径\deep-review-mcp` |

#### 4. 启动 Web 可视化界面（可选）

```powershell
cd deep-review-mcp
uv run deep-review-web
```

浏览器访问 http://127.0.0.1:8001 即可使用可视化界面。

## 使用方法

### 命令模式

| 命令 | 功能 |
|------|------|
| `/capture` | 采集新错题 (拍照识别) |
| `/analyze` | 分析错题原因 |
| `/review` | 生成复习计划 |
| `/stats` | 查看错题统计 |
| `/export` | 导出错题数据 |

### 自然语言模式

- "帮我录入这道错题" → 触发 `/capture`
- "分析这道错题为什么做错" → 触发 `/analyze`
- "我该复习什么" → 触发 `/review`
- "看看我的错题分布" → 触发 `/stats`

### Web 可视化界面

启动 Web 服务后，访问 http://127.0.0.1:8001 可使用四大功能页面：

1. **概览 Dashboard**：错题总数、今日待复习、本周新增、学科分布、错误类型分布、30天趋势
2. **错题列表与详情**：筛选查看、编辑保存（学科/难度/错误类型等字段可在线修改）
3. **统计图表**：多维度可视化分析（知识点热力图、难度分布、错误类型雷达、时间趋势）
4. **复习追踪**：待复习清单、复习日历、遗忘曲线、学科复习进度

所有数据仅存储在本地，JS 库本地化，无外部请求。

## 项目结构

```
deep-review/
├── deep-review-mcp/           # 纯 MCP Server (通用服务层)
│   ├── src/deep_review_mcp/
│   │   ├── server.py          # FastMCP 服务入口
│   │   ├── models.py          # Pydantic 数据模型
│   │   ├── storage.py         # JSON 存储引擎（支持原子写、部分更新）
│   │   ├── knowledge_map.py   # K12 知识点映射
│   │   ├── tools/             # 11 个 MCP Tools
│   │   │   ├── ocr_recognize.py
│   │   │   ├── classify.py
│   │   │   ├── analyze.py
│   │   │   ├── improvement.py
│   │   │   ├── review.py
│   │   │   ├── statistics.py
│   │   │   ├── export.py
│   │   │   └── crud.py
│   │   ├── prompts/           # AI Prompt 模板
│   │   │   ├── structure_parse.py
│   │   │   ├── classify_prompt.py
│   │   │   ├── analyze_prompt.py
│   │   │   └── improvement_prompt.py
│   │   └── web/               # Web 可视化模块
│   │       ├── app.py         # FastAPI 应用工厂 + 入口
│   │       ├── services.py    # Web 服务层（编排 storage/statistics/review）
│   │       ├── schemas.py     # Web 请求/响应模型
│   │       ├── routes/        # 路由模块（dashboard/questions/stats/review）
│   │       ├── templates/     # Jinja2 模板（base.html + partials）
│   │       └── static/        # 静态资源（HTMX/Alpine/ECharts 本地化）
│   ├── data/                   # 运行时数据
│   │   └── wrong_questions/    # 错题 JSON 文件
│   ├── tests/                  # 测试套件（单元/集成/E2E）
│   └── pyproject.toml          # Python 项目配置
│
├── docs/                        # 设计文档与实施计划
│   └── superpowers/
│       ├── specs/               # 设计文档
│       └── plans/               # 实施计划
│
├── .trae/                       # Trae 配置与 Skills/Rules 源文件
│   ├── mcp-servers/
│   │   └── deep-review-mcp/
│   ├── skills/                  # Skills 源文件
│   │   ├── wrong-question-capture/
│   │   ├── wrong-question-analyze/
│   │   ├── review-plan-generate/
│   │   ├── wrong-question-stats/
│   │   └── wrong-question-batch-capture/
│   └── rules/                   # Rules 源文件
│       ├── classification-rules.md
│       ├── analysis-rules.md
│       ├── data-safety-rules.md
│       └── interaction-rules.md
│
├── install.ps1                  # Windows 安装脚本
├── install.sh                   # Linux/macOS 安装脚本
└── README.md
```

## 架构设计说明

### 分层分离原则

本项目采用 **"服务层 + 配置层"** 分离架构：

| 层级 | 位置 | 用途 |
|------|------|------|
| **服务层** | `deep-review-mcp/` | 纯 Python MCP Server，通用，不绑定任何客户端，可独立发布 |
| **Web 可视化层** | `deep-review-mcp/src/deep_review_mcp/web/` | 本地 Web 界面，FastAPI + HTMX + Alpine.js + ECharts |
| **配置层** | `.trae/skills/`, `.trae/rules/` | Trae Work 专用配置，定义流程与约束（单一真相源） |

### 为什么要分离？

1. **职责清晰**: 代码归代码，配置归配置
2. **可复用**: `deep-review-mcp/` 可单独在其他 MCP 客户端（如 Cursor）中使用
3. **单一真相源**: Skills/Rules 配置直接在 `.trae/` 下编辑，无需同步步骤
4. **Git 友好**: 项目结构一目了然，`.trae/` 即 Trae 配置根目录
5. **可视化独立**: Web 模块作为薄编排层，复用现有 storage/statistics/review 逻辑

### Web 可视化模块

Web 可视化模块位于 `deep-review-mcp/src/deep_review_mcp/web/`，提供本地 Web 界面：

- **技术栈**: FastAPI（后端）+ HTMX（局部更新）+ Alpine.js（表单状态）+ ECharts（图表渲染）
- **启动方式**: `uv run deep-review-web`，访问 http://127.0.0.1:8001
- **四大页面**:
  - 概览 Dashboard：KPI 指标、学科分布、错误类型分布、30天趋势
  - 错题列表与详情：筛选查看、编辑保存（支持 HTMX 局部更新）
  - 统计图表：多维度可视化分析（知识点热力图、难度分布、错误类型雷达、时间趋势）
  - 复习追踪：待复习清单、复习日历、遗忘曲线、学科复习进度
- **安全特性**: 仅绑定 127.0.0.1，JS 库本地化（无 CDN），无外部请求
- **数据访问**: 通过 `web/services.py` 编排层访问 storage，保证与 MCP 工具一致

## 数据安全

- ✅ 所有数据仅存储在本地
- ✅ OCR 本地部署，不调用外部 API
- ✅ 不收集任何个人身份信息
- ✅ 图片文件存储在项目目录下
- ✅ Web 可视化仅绑定 127.0.0.1，JS 库本地化，无外部请求

## License

MIT License

## Contributing

欢迎提交 Issue 和 Pull Request！
