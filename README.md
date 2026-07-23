# DeepReview - K12错题收集与智能分析Agent

基于 Trae IDE CN 平台的 K12 错题收集与智能分析解决方案，帮助学生通过拍照快速录入错题，AI 自动完成分类、原因分析、改进方案生成和复习推荐。提供本地 Web 可视化界面，直观展示错题分布、趋势和薄弱点。

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
- **Web 可视化**: FastAPI + HTMX（OOB 局部刷新）+ Alpine.js（轻量交互）+ ECharts（图表）
- **OCR 引擎（可选）**: PaddleOCR（本地部署，无需 API Key；不安装也能用基础功能）
- **数据存储**: JSON 文件（本地存储，原子写入）
- **包管理**: uv（现代高速 Python 包管理器）
- **测试**: pytest + pytest-asyncio + pytest-cov + Playwright（E2E）
- **CI/CD**: GitHub Actions（Tests + Release）

## 快速安装

### 前置要求

- Python 3.12+
- [uv 包管理器](https://docs.astral.sh/uv/)（Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`）
- Trae IDE CN

### 安装步骤

#### 1. 下载并解压

下载 `DeepReview-v0.1.0.zip`，解压到任意目录（如 `D:\DeepReview\`）。

#### 2. 运行安装脚本

**Windows:**
```powershell
# 右键 install.ps1 → "使用 PowerShell 运行"
# 或在 PowerShell 中：
.\install.ps1
```

**Linux / macOS:**
```bash
chmod +x install.sh
./install.sh
```

安装脚本会自动检查环境、创建虚拟环境并安装所有依赖。

> ⏱️ 首次安装需要下载 PaddleOCR 模型，可能需要 2-5 分钟。

#### 3. 在 Trae IDE 中配置

1. 用 Trae IDE 打开解压后的文件夹
2. 进入 **设置 → MCP**
3. 打开 **"启用项目级 MCP"** 开关
4. 重启 Trae

> 💡 项目级 MCP 配置已内置于 `.trae/mcp.json`，使用 `${workspaceFolder}` 变量自动适配路径，无需手动填写。

#### 4. 开始使用

```
/capture  - 采集新错题
/analyze  - 分析错题原因
/review   - 生成复习计划
/stats    - 查看错题统计
```

### 可选：启动 Web 可视化界面

```powershell
cd deep-review-mcp
uv run deep-review-web
```

浏览器访问 http://127.0.0.1:8001 即可使用可视化界面。

### 可选：安装 OCR 引擎

OCR 引擎（PaddleOCR + PaddlePaddle，约 1.5 GB）用于图片错题识别，**非必需**。仅当使用 `/capture` 拍照录入时才需要安装：

```bash
cd deep-review-mcp
uv sync --extra ocr
```

未安装时调用 OCR 会得到友好提示，不影响其他功能。

## 下载与发布

每次发版会在 GitHub Release 页面提供三种压缩包，按需选择：

| 格式 | 适用平台 | 特点 |
|------|---------|------|
| `DeepReview-vX.Y.Z.zip` | Windows | 与 PowerShell `Compress-Archive` 兼容，最通用 |
| `DeepReview-vX.Y.Z.tar.zst` | 现代 Linux/macOS | 体积最小、速度最快（**推荐**） |
| `DeepReview-vX.Y.Z.tar.gz` | 所有 Unix | 兼容性最好，老旧系统 fallback |

访问 https://github.com/yecllsl/DeepReview/releases 下载最新版本。

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
├── deep-review-mcp/                       # 纯 MCP Server (通用服务层)
│   ├── src/deep_review_mcp/
│   │   ├── server.py                      # FastMCP 服务入口
│   │   ├── models.py                      # Pydantic 数据模型
│   │   ├── storage.py                     # JSON 存储引擎（支持原子写、部分更新）
│   │   ├── knowledge_map.py               # K12 知识点映射
│   │   ├── tools/                         # 11 个 MCP Tools
│   │   │   ├── ocr_recognize.py
│   │   │   ├── classify.py
│   │   │   ├── analyze.py
│   │   │   ├── improvement.py
│   │   │   ├── review.py
│   │   │   ├── statistics.py
│   │   │   ├── export.py
│   │   │   └── crud.py
│   │   ├── prompts/                       # AI Prompt 模板
│   │   │   ├── structure_parse.py
│   │   │   ├── classify_prompt.py
│   │   │   ├── analyze_prompt.py
│   │   │   └── improvement_prompt.py
│   │   └── web/                           # Web 可视化模块（薄编排层）
│   │       ├── app.py                     # FastAPI 应用工厂 + 入口
│   │       ├── services.py                # Web 服务层（编排 storage/statistics/review）
│   │       ├── schemas.py                 # Web 请求/响应模型
│   │       ├── routes/                    # 路由模块（dashboard/questions/stats/review）
│   │       ├── templates/                 # Jinja2 模板（base.html + partials）
│   │       │   ├── base.html
│   │       │   ├── errors.html
│   │       │   └── partials/              # HTMX 片段模板（含 OOB swap）
│   │       └── static/                    # 静态资源（HTMX/Alpine/ECharts 本地化）
│   ├── tests/                             # 测试套件
│   │   ├── test_models.py                 # Pydantic 模型
│   │   ├── test_storage.py                # 存储层（含 patch 工具）
│   │   ├── test_storage_patch.py          # 部分更新逻辑
│   │   ├── test_tools_*.py                # 11 个 Tools 的单元测试
│   │   ├── test_web_routes.py             # Web 路由测试
│   │   ├── test_web_services.py           # Web 服务层测试
│   │   └── test_e2e_visualization.py      # Playwright E2E（8 用例）
│   ├── data/                              # 运行时数据（被 .gitignore）
│   ├── pyproject.toml                     # Python 项目配置
│   └── uv.lock                            # 依赖锁定文件
│
├── .trae/                                  # Trae 配置与 Skills/Rules 源文件
│   ├── mcp.json                            # 项目级 MCP 配置（自动路径适配）
│   ├── hooks.json
│   ├── skills/                             # Skills 源文件
│   │   ├── wrong-question-capture/         # /capture
│   │   ├── wrong-question-analyze/         # /analyze
│   │   ├── review-plan-generate/           # /review
│   │   ├── wrong-question-stats/           # /stats
│   │   └── wrong-question-batch-capture/   # 批量采集
│   └── rules/                              # Rules 源文件
│       ├── classification-rules.md
│       ├── analysis-rules.md
│       ├── data-safety-rules.md
│       └── interaction-rules.md
│
├── .github/
│   └── workflows/
│       ├── test.yml                        # CI：单元测试 + E2E（3.12/3.13）
│       └── release.yml                     # Release：push tag → 自动打包 + 上传
│
├── scripts/                                # 开发者工具
│   ├── build-release.ps1                   # Windows 发布包构建（PowerShell）
│   └── build-release.sh                    # Linux/macOS 发布包构建（bash，与 .ps1 逻辑对齐）
├── install.ps1                             # Windows 安装脚本（可选装 OCR）
├── install.sh                              # Linux/macOS 安装脚本（可选装 OCR）
├── QUICKSTART.md                           # 5 分钟快速上手
├── DEPLOY.md                               # 详细部署指南
├── README.md                               # 本文件
└── LICENSE                                 # MIT
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

## 常见问题

### Q: 安装脚本报错 "uv 未安装"

```powershell
# 安装 uv (Windows)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 安装 uv (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Q: MCP Server 不生效

1. 确认已在 Trae 中打开 **"启用项目级 MCP"** 开关
2. 确认已重启 Trae
3. 如果 `${workspaceFolder}` 变量不被支持，运行 `.\install.ps1 -FixPath` 自动修复路径

### Q: OCR / PaddleOCR 安装失败

- 确认 Python 版本 >= 3.12
- 确认网络畅通（需下载模型文件）
- OCR 为**可选依赖**，默认 `uv sync` 不会安装。需要时执行：`cd deep-review-mcp && uv sync --extra ocr`
- 若仅使用文本录入、统计、复习等基础功能，**无需安装 OCR**

## License

MIT License

## Contributing

欢迎提交 Issue 和 Pull Request！

## 测试与开发

### 本地运行测试

```bash
cd deep-review-mcp

# 仅单元/集成测试（默认不装 paddleocr/浏览器，最快）
uv sync --extra dev
uv run pytest tests/ -m "not e2e"

# E2E 测试（需先装 Playwright 浏览器）
uv run playwright install chromium
uv run pytest tests/test_e2e_visualization.py -m e2e
```

测试覆盖：72 个单元/集成用例 + 8 个 E2E 用例，矩阵 Python 3.12 / 3.13。

### 本地构建发布包

```powershell
# Windows
pwsh .\scripts\build-release.ps1 -Version 0.2.0
```

```bash
# Linux / macOS
bash scripts/build-release.sh 0.2.0
```

产物：`dist/DeepReview-v0.2.0.{zip,tar.zst,tar.gz}`。

### CI/CD

- **PR / push** → [`.github/workflows/test.yml`](.github/workflows/test.yml) 跑单元 + E2E
- **push tag `v*.*.*`** → [`.github/workflows/release.yml`](.github/workflows/release.yml) 自动构建并发布 GitHub Release（附 `generate_release_notes` 自动 changelog）
