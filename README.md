# DeepReview - K12错题收集与智能分析Agent

基于 Trae Work 平台的 K12 错题收集与智能分析解决方案，帮助学生通过拍照快速录入错题，AI 自动完成分类、原因分析、改进方案生成和复习推荐。

## 核心功能

- 📷 **错题采集**: 拍照识别 + OCR文字提取 + AI结构化解析
- 🏷️ **智能分类**: 学科分类、知识点标签、错误类型标注
- 🔍 **原因分析**: 错误根因诊断 (知识漏洞/粗心/方法错误/审题失误)
- 📝 **改进方案**: 针对性学习建议、同类题推荐方向
- 📅 **复习推荐**: 基于遗忘曲线的复习计划
- 📊 **统计分析**: 多维度错题分布和趋势分析

## 系统架构

```
用户交互层 (命令/对话)
    ↓
Skills 编排层 (流程编排)
    ↓
MCP Tools 层 (deep-review-mcp)
    ↓
Rules 约束层 (分类/分析/安全/交互规则)
    ↓
数据存储层 (本地JSON文件)
```

## 技术栈

- **MCP Server**: Python 3.12+ / FastMCP
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
git clone https://github.com/your-username/deep-review.git
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

#### 4. 复制 Skills 和 Rules

将 `.trae/` 目录下的 `skills/` 和 `rules/` 复制到您的项目目录。

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

## 项目结构

```
deep-review/
├── deep-review-mcp/           # 纯 MCP Server (通用服务层)
│   ├── src/deep_review_mcp/
│   │   ├── server.py          # FastMCP 服务入口
│   │   ├── models.py          # Pydantic 数据模型
│   │   ├── storage.py         # JSON 存储引擎
│   │   ├── knowledge_map.py   # K12 知识点映射
│   │   └── tools/             # 11 个 MCP Tools
│   │       ├── ocr_recognize.py
│   │       ├── classify.py
│   │       ├── analyze.py
│   │       ├── improvement.py
│   │       ├── review.py
│   │       ├── statistics.py
│   │       └── crud.py
│   ├── data/                   # 运行时数据
│   └── pyproject.toml          # Python 项目配置
│
├── skills/                      # Skills 源文件 (Trae Work 专用配置)
│   ├── wrong-question-capture/
│   ├── wrong-question-analyze/
│   ├── review-plan-generate/
│   └── wrong-question-stats/
│
├── rules/                       # Rules 源文件 (Trae Work 专用配置)
│   ├── classification-rules.md
│   ├── analysis-rules.md
│   ├── data-safety-rules.md
│   └── interaction-rules.md
│
├── .trae/                       # Trae 运行时配置 (由 install 脚本自动生成)
│   ├── mcp-servers/
│   │   └── deep-review-mcp/
│   ├── skills/                  # ← 从根目录 skills/ 同步
│   └── rules/                   # ← 从根目录 rules/ 同步
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
| **配置层** | `skills/`, `rules/` | Trae Work 专用 Markdown 配置，定义流程与约束 |
| **运行时** | `.trae/` | Trae Work IDE 实际读取的配置目录，由安装脚本从配置层同步 |

### 为什么要分离？

1. **职责清晰**: 代码归代码，配置归配置
2. **可复用**: `deep-review-mcp/` 可单独在其他 MCP 客户端（如 Cursor）中使用
3. **便于维护**: 修改 Skills/Rules 只在根目录操作，无需深入 Python 源码
4. **Git 友好**: 项目结构一目了然，根目录的配置文件就是真相源

## 数据安全

- ✅ 所有数据仅存储在本地
- ✅ OCR 本地部署，不调用外部 API
- ✅ 不收集任何个人身份信息
- ✅ 图片文件存储在项目目录下

## License

MIT License

## Contributing

欢迎提交 Issue 和 Pull Request！
