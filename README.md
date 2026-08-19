# DeepReview - K12错题收集与智能分析Agent

基于 Trae IDE CN / CodeBuddy / opencode / Goose / WorkBuddy / Hermes 多 Agent 运行时（harness）的 K12 错题收集与智能分析解决方案，帮助学生通过拍照快速录入错题，AI 自动完成分类、原因分析、改进方案生成和复习推荐。提供本地 Web 可视化界面，直观展示错题分布、趋势和薄弱点。

> v0.3.0 起支持 **AAIF 规范**；v0.5.0 起符合 **Agent Plugins 1.0**（Vercel 等厂商中立打包规范，与 AAIF 无隶属关系）：`deep-review.plugin/` 为配置层唯一真相源 + 自包含插件包（`plugin.json` / `mcp.json`），多 harness 配置由 `scripts/sync-agent-configs` 单向同步生成。

## 核心功能

- 📷 **错题采集**: 拍照识别（宿主LLM多模态看图解析）+ AI结构化解析
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
├── 多运行时: Trae IDE CN + CodeBuddy + opencode + Goose + WorkBuddy + Hermes
└── Web 可视化界面 (本地浏览器 http://127.0.0.1:8001)
    ↓
Skills 编排层 (配置定义，由 deep-review.plugin/skills/ 同步到多平台)
├── 5 个 Skill: capture / batch-capture / analyze / review / stats
    ↓
服务层 (deep-review.plugin/deep-review-mcp — Agent Plugins 1.0 内联 MCP)
├── MCP Tools: 10 个 Tools
└── Web 可视化子模块 (FastAPI + HTMX + Alpine.js + ECharts)
    ↓
规则层 (deep-review.plugin/AGENTS.md — AAIF 统一规则源)
    ↓
数据存储层 (本地JSON文件, 原子写入)
```

## 技术栈

- **插件层**: Agent Plugins 1.0（Vercel 等厂商中立打包规范，与 AAIF 无隶属关系）——`deep-review.plugin/plugin.json` + `mcp.json`（`${PLUGIN_ROOT}` 内联 MCP 启动），根 `package.json` 提供 `agents publish deep-review.plugin` 标准发布
- **配置层**: AAIF 规范（`deep-review.plugin/` 唯一真相源）+ 多 Agent harness（Trae/CodeBuddy/opencode/Goose + WorkBuddy/Hermes，单向同步）
- **MCP Server**: Python 3.12+ / FastMCP
- **Web 可视化**: FastAPI + HTMX（OOB 局部刷新）+ Alpine.js（轻量交互）+ ECharts（图表）
- **图片解析**: 宿主 LLM 多模态直接看图解析（无需额外图像识别依赖）
- **数据存储**: JSON 文件（本地存储，原子写入）
- **包管理**: uv（现代高速 Python 包管理器）
- **测试**: pytest + pytest-asyncio + pytest-cov + Playwright（E2E）
- **CI/CD**: GitHub Actions（Tests + Release）

## 快速安装

### 前置要求

- Python 3.12+
- [uv 包管理器](https://docs.astral.sh/uv/)（Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`）
- 任一 Agent 运行时：Trae IDE CN / CodeBuddy / opencode / Goose（WorkBuddy / Hermes 为个人级 harness，无需桌面 IDE）

### 安装步骤

#### 1. 下载并解压

下载 `DeepReview-v0.5.0.zip`，解压到任意目录（如 `D:\DeepReview\`）。

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

#### 3. 配置 Agent 运行时（多 harness）

安装脚本支持通过 `-AgentRuntime` 指定要配置的运行时：

```powershell
# Windows：一次性配置全部（Trae/CodeBuddy/opencode/Goose + 个人级 WorkBuddy/Hermes）
.\install.ps1 -AgentRuntime all

# 或只配置单个运行时
.\install.ps1 -AgentRuntime codebuddy
.\install.ps1 -AgentRuntime goose
.\install.ps1 -AgentRuntime workbuddy   # 个人级，写入 ~/.workbuddy
```

```bash
# Linux/macOS
./install.sh --agent-runtime all
```

四个项目级运行时的配置目录由 `scripts/sync-agent-configs` 从 `deep-review.plugin/`（AAIF 唯一真相源）单向生成：

| 运行时 | 配置目录 | 说明 |
|--------|---------|------|
| Trae IDE CN | `.trae/` | 设置 → MCP → 启用项目级 MCP |
| CodeBuddy | `.codebuddy/` | 打开项目后信任 deep-review-mcp |
| opencode | `.opencode/` | 项目目录运行 `opencode` 自动加载 |
| Goose | `.goose/` | 打开项目自动读取 `config.yaml` |

#### 4. 开始使用

```
/capture        - 采集新错题
/batch-capture  - 批量采集错题
/analyze        - 分析错题原因
/review         - 生成复习计划
/stats          - 查看错题统计
/export         - 导出错题数据
```

### 可选：启动 Web 可视化界面

```powershell
cd deep-review.plugin/deep-review-mcp
uv run deep-review-web
```

浏览器访问 http://127.0.0.1:8001 即可使用可视化界面。

## 下载与发布

每次发版会在 GitHub Release 页面提供三种压缩包，按需选择：

| 格式 | 适用平台 | 特点 |
|------|---------|------|
| `DeepReview-vX.Y.Z.zip` | Windows | 与 PowerShell `Compress-Archive` 兼容，最通用 |
| `DeepReview-vX.Y.Z.tar.zst` | 现代 Linux/macOS | 体积最小、速度最快（**推荐**） |
| `DeepReview-vX.Y.Z.tar.gz` | 所有 Unix | 兼容性最好，老旧系统 fallback |

访问 https://github.com/yecllsl/DeepReview/releases 下载最新版本。

### Agent Plugins 1.0 标准发布

`deep-review.plugin/` 是符合 Agent Plugins 1.0（Vercel 等厂商中立打包规范，与 AAIF 无隶属关系）规范的自包含插件包，可向标准插件注册中心发布：

```bash
# 校验插件包清单（plugin.json / mcp.json schema）
npx agents validate deep-review.plugin

# 发布到插件注册中心
npx agents publish deep-review.plugin
```

根 `package.json` 已内置脚本别名：

```bash
npm run publish        # 等价于 agents publish deep-review.plugin
npm run generate-declarations   # 重新生成 AAIF 声明（tools/triggers/workflows.json）
npm run sync-configs   # 同步四平台配置目录
npm run check-drift    # 校验配置漂移
```

## 使用方法

### 命令模式

| 命令 | 功能 |
|------|------|
| `/capture` | 采集新错题 (拍照识别) |
| `/batch-capture` | 批量采集错题（一次录入多道） |
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
DeepReview/
├── deep-review.plugin/                     # Agent Plugins 1.0 插件根（单一配置与打包真相源，自包含可分发）
│   ├── plugin.json                         # Agent Plugins 1.0 manifest（$schema/name/version/...）
│   ├── mcp.json                            # MCP 启动配置（${PLUGIN_ROOT} 内联 deep-review-mcp）
│   ├── AGENTS.md                           # 统一规则层（架构/安全/开发规范/流程规则 + 业务规则）
│   ├── skills/                             # 5 个技能源文件（frontmatter 含 command:）
│   │   ├── wrong-question-capture/         # /capture
│   │   ├── wrong-question-batch-capture/   # /batch-capture
│   │   ├── wrong-question-analyze/         # /analyze
│   │   ├── review-plan-generate/           # /review
│   │   └── wrong-question-stats/           # /stats
│   ├── runtime/                            # 4 平台运行时配置（generate-platform-configs.py 生成）
│   │   ├── trae.json / codebuddy.json / opencode.json / goose.json
│   ├── tools.json                          # AAIF 声明：MCP 工具自省（生成产物，勿手改）
│   ├── triggers.json                       # AAIF 声明：命令+对话触发器（生成产物）
│   ├── workflows.json                      # AAIF 声明：技能工作流（生成产物）
│   └── deep-review-mcp/                    # 纯 MCP Server（内联在插件包内，通用服务层）
│       ├── src/deep_review_mcp/
│       │   ├── server.py                  # FastMCP 服务入口
│       │   ├── models.py                  # Pydantic 数据模型
│       │   ├── storage.py                 # JSON 存储引擎（支持原子写、部分更新）
│       │   ├── knowledge_map.py           # K12 知识点映射
│       │   ├── tools/                     # 10 个 MCP Tools
│       │   ├── prompts/                   # AI Prompt 模板
│       │   └── web/                       # Web 可视化模块（薄编排层）
│       ├── tests/                         # 测试套件
│       ├── data/                          # 运行时数据（被 .gitignore）
│       ├── pyproject.toml                 # Python 项目配置（version 0.5.0）
│       └── uv.lock                        # 依赖锁定文件
├── package.json                           # AAIF 声明入口（main）+ publish 脚本（agents publish）
├── .trae/                                  # [生成] Trae 配置（sync 单向覆盖；规则已合并入 deep-review.plugin/AGENTS.md）
├── .opencode/                              # [生成] opencode 配置（opencode.json + skills + AGENTS.md）
├── .codebuddy/                             # [生成] CodeBuddy 配置（memory/ 由运行时写入）
├── .goose/                                 # [生成] Goose 配置（config.yaml + skills + AGENTS.md）
├── .workbuddy/                             # 个人级 harness 说明（安装脚本写入 ~/.workbuddy）
├── .hermes/                                # 个人级 harness 说明（安装脚本写入 ~/.hermes）
├── scripts/                                # 开发者工具
│   ├── generate-aaif-declarations.py       # FastMCP 自省生成 AAIF 声明（规范格式）
│   ├── generate-platform-configs.py        # 生成 deep-review.plugin/runtime/ 4 平台 JSON
│   ├── generate-goose-config.py            # goose.json → .goose/config.yaml
│   ├── sync-agent-configs.ps1/.sh          # deep-review.plugin/ 单向同步到 4 平台目录
│   ├── pre-commit                          # git 钩子：内容一致性检查（拦截配置同步违规）
│   ├── check-config-drift.sh               # CI 工作区漂移检查（与 pre-commit 双防线）
│   └── build-release.ps1/.sh               # 发布包构建
├── AGENTS.md                               # [生成] 根规则文件（Trae 读取约定，由 sync 复制）
├── install.ps1 / install.sh                # 安装脚本（-AgentRuntime/-FixPath）
├── QUICKSTART.md / DEPLOY.md / README.md   # 文档
├── CHANGELOG.md                            # 变更记录
└── LICENSE                                 # MIT
```

## 架构设计说明

### 分层分离原则

本项目采用 **"服务层 + 配置层 + 规则层 + 插件层"** 分离架构（对标 AAIF 规范 + Agent Plugins 1.0）：

| 层级 | 位置 | 用途 |
|------|------|------|
| **插件层** | `deep-review.plugin/`（自包含插件包） | Agent Plugins 1.0：`plugin.json`（manifest）+ `mcp.json`（`${PLUGIN_ROOT}` 内联 MCP 启动），可整体分发 |
| **服务层** | `deep-review.plugin/deep-review-mcp/` | 纯 Python MCP Server，通用，不绑定任何客户端，内联在插件包内 |
| **Web 可视化层** | `deep-review.plugin/deep-review-mcp/src/deep_review_mcp/web/` | 本地 Web 界面，FastAPI + HTMX + Alpine.js + ECharts |
| **配置层** | `deep-review.plugin/`（唯一真相源） | AAIF 标准：AGENTS.md + skills/ + runtime/ + tools/triggers/workflows.json + plugin.json/mcp.json |
| **生成产物** | `.trae/` `.opencode/` `.codebuddy/` `.goose/` | 由 `scripts/sync-agent-configs` 从 `deep-review.plugin/` 单向同步生成（禁止直接编辑） |
| **规则层** | `deep-review.plugin/AGENTS.md` | 业务规则（采集/分类/分析/复习/交互/数据安全）统一约束 |

### 为什么要分离？

1. **职责清晰**: 代码归代码，配置归配置，规则归规则
2. **可复用**: `deep-review.plugin/deep-review-mcp/` 可单独在其他 MCP 客户端中使用，也可随插件整体发布
3. **AAIF 单一真相源**: 配置只在 `deep-review.plugin/` 下编辑，4 个 harness 目录由同步脚本生成，杜绝配置漂移
4. **机械防线（双防线）**: `scripts/pre-commit` 钩子拦截「直接改生成目录而未同步」的违规提交（`.codebuddy/memory/**` 例外）；CI 另由 `scripts/check-config-drift.sh` 校验工作区一致性
5. **可视化独立**: Web 模块作为薄编排层，复用现有 storage/statistics/review 逻辑

### Web 可视化模块

Web 可视化模块位于 `deep-review.plugin/deep-review-mcp/src/deep_review_mcp/web/`，提供本地 Web 界面：

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
- ✅ 图片解析由宿主 LLM 多模态完成，图片仅存本地不外传
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

1. 确认已在你的运行时中启用项目级 MCP（Trae：设置 → MCP → 启用项目级 MCP；CodeBuddy：打开项目后信任 deep-review-mcp；opencode/Goose：直接打开项目即可）
2. 确认已重启运行时
3. 如果 `${workspaceFolder}` 变量不被支持，运行 `.\install.ps1 -FixPath`（或 `./install.sh --fix-path`）自动修复路径

## License

MIT License

## Contributing

欢迎提交 Issue 和 Pull Request！

## 测试与开发

### 本地运行测试

```bash
cd deep-review.plugin/deep-review-mcp

# 仅单元/集成测试（默认不装浏览器，最快）
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
pwsh .\scripts\build-release.ps1 -Version 0.5.0
```

```bash
# Linux / macOS
bash scripts/build-release.sh 0.5.0
```

产物：`dist/DeepReview-v0.5.0.{zip,tar.zst,tar.gz}`。

### CI/CD

- **PR / push** → [`.github/workflows/test.yml`](.github/workflows/test.yml) 跑单元 + E2E + config-drift
- **push tag `v*.*.*`** → [`.github/workflows/release.yml`](.github/workflows/release.yml) 自动构建并发布 GitHub Release（附 `generate_release_notes` 自动 changelog）
