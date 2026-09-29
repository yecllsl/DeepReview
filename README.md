# DeepReview - K12错题收集与智能分析Agent

基于 Trae / CodeBuddy / opencode 多 Agent 运行时（harness）的 K12 错题收集与智能分析解决方案，帮助学生通过拍照快速录入错题，AI 自动完成分类、原因分析、改进方案生成和复习推荐。提供本地 Web 可视化界面，直观展示错题分布、趋势和薄弱点。

> v0.3.0 起支持 **AAIF 规范**；v0.5.0 起符合 **Agent Plugins 1.0**（Vercel 等厂商中立打包规范，与 AAIF 无隶属关系）：`deep-review.plugin/` 为配置层唯一真相源 + 自包含插件包（`plugin.json` / `mcp.json`），多 harness 配置由 `scripts/sync-agent-configs` 单向同步生成。Harness 支持只分两层（见下方「支持的 Harness」）。

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
├── Tier 1 (Agent Plugins 1.0 插件标准): VS Code / Copilot + CodeBuddy — 插件形态分发
├── Tier 2 (免费额度/开箱即用): Trae + opencode — 原生目录 + install 脚本
└── Web 可视化界面 (本地浏览器 http://127.0.0.1:8001)
    ↓
Skills 编排层 (配置定义，由 deep-review.plugin/skills/ 同步到多平台)
├── 5 个 Skill: capture / batch-capture / analyze / review / stats
    ↓
服务层 (deep-review.plugin/deep-review-mcp — Agent Plugins 1.0 内联 MCP)
├── MCP Tools: 10 个 Tools
└── Web 可视化子模块 (FastAPI + HTMX + Alpine.js + ECharts)
    ↓
规则层 (deep-review.plugin/AGENTS.md — 统一规则源)
    ↓
数据存储层 (本地JSON文件, 原子写入)
```

## 技术栈

- **插件层**: Agent Plugins 1.0（Vercel 等厂商中立打包规范，与 AAIF 无隶属关系）——`deep-review.plugin/plugin.json` + `mcp.json`（`${PLUGIN_ROOT}` 内联 MCP 启动），根 `package.json` 提供 `agents publish deep-review.plugin` 标准发布
- **配置层**: 配置唯一真相源（`deep-review.plugin/`）+ Tier 2 原生 harness（Trae/opencode，单向同步；另含 tools/triggers/workflows.json 三个 AAIF 声明）
- **MCP Server**: Python 3.12+ / FastMCP
- **Web 可视化**: FastAPI + HTMX（OOB 局部刷新）+ Alpine.js（轻量交互）+ ECharts（图表）
- **图片解析**: 宿主 LLM 多模态直接看图解析（无需额外图像识别依赖）
- **数据存储**: JSON 文件（本地存储，原子写入）
- **包管理**: uv（现代高速 Python 包管理器）
- **测试**: pytest + pytest-asyncio + pytest-cov + Playwright（E2E）
- **CI/CD**: GitHub Actions（Tests + Release）

## 支持的 Harness

Harness 支持只分两层，判定标准是「是否采纳 Agent Plugins 1.0 插件标准」与「是否免费额度可开箱即用」：

| 层 | 代表 | 交付形态 | 说明 |
|----|------|---------|------|
| **Tier 1 — Agent Plugins 1.0 插件标准** | VS Code / Copilot、CodeBuddy | `deep-review.plugin/` 插件目录（`plugin.json` + `mcp.json` + `skills/`） | 任何采纳 Agent Plugins 1.0 的客户端可直接指向该目录，不为单个客户端新增同步目标。CodeBuddy 另经本地/Git URL 插件市场通道安装（`.codebuddy-plugin/marketplace.json`，自有格式）。**VS Code / Copilot 经 Agent Plugins 1.0 远程市场安装：仓库根 `marketplace.json`（Claude Code / Copilot CLI 同源市场格式，其 `source` 指向 `./deep-review.plugin`）加入 `chat.plugins.marketplaces` 后 Browse Marketplace 安装**——这是 VS Code 走 GitHub 的正确路径（Install from Source 要求 `plugin.json` 在仓库根，本仓库插件在子目录，故不能用仓库根/子目录 URL 直装）。该规范不携带 AGENTS.md，规则文件走 Tier 2 与仓库根 |
| **Tier 2 — 免费额度 / 开箱即用** | Trae、OpenCode | `.trae/` / `.opencode/` 原生目录 + `install.*` | 有免费额度，用户解压即用，零额外付费门槛 |

> 交付状态如实记录：CodeBuddy（本地 / Git URL 远程市场）已实测；**VS Code / Copilot 经 `chat.plugins.marketplaces` 远程市场安装 `deep-review` 已实测 ✅**（2026-09-29，经仓库根 `marketplace.json` 解析 `./deep-review.plugin`）。验收方法见 DEPLOY「手动 E2E 验收方法」。

### 各客户端安装方式对照

| 客户端 | 安装 MCP + skills 的方式 | 用 Agent Plugins 1.0 插件包？ | 层 | 实测 |
|--------|--------------------------|------------------------------|----|------|
| VS Code / Copilot | 本地：Agents Window → **Install from Source** 指向 `deep-review.plugin/`<br>远程：settings.json `chat.plugins.marketplaces` 加 `yecllsl/DeepReview` → Browse Marketplace 安装 `deep-review` | ✅ 是 | Tier 1 | ✅ 是（远程市场） |
| CodeBuddy | **插件管理 → 插件市场 → 添加本地市场**（`.codebuddy-plugin/marketplace.json`，市场 `deep-review-local-market`） | ❌ 自有市场格式 | Tier 1 | 未实测 |
| OpenCode | `opencode.json` 的 `mcp` 字段 + `.opencode/skills/`（`install.ps1 -AgentRuntime opencode`） | ❌ | Tier 2 | 未实测 |
| Trae | 内置 MCP 市场 / `.trae/mcp.json` + `.trae/skills/`（`install.ps1 -AgentRuntime trae`） | ❌ | Tier 2 | 未实测 |

> **VS Code / CodeBuddy 还支持「方式 B」Git URL 远程安装**：CodeBuddy 用 `/plugin marketplace add https://github.com/yecllsl/DeepReview.git`（或 `yecll/DeepReview`）；VS Code 在 settings.json 的 `chat.plugins.marketplaces` 加入 `yecllsl/DeepReview`，二者均经仓库根 `marketplace.json` 解析到 `./deep-review.plugin`，无需下载 Release 压缩包（详见 [QUICKSTART.md](QUICKSTART.md)）。

> OpenCode / Trae 的「插件」（IDE 扩展或 hook 插件）与 Agent Plugins 1.0 打包标准不是一回事；两者均**未采纳**该标准，故 MCP+skills 只能走原生目录/市场。若将来采纳，按「先归层再加」升入 Tier 1。

**明确不支持**：**WorkBuddy、Hermes**（用户级 harness，配置只能写 `~/`，无法项目级统一）与 **Goose**（未采纳 Agent Plugins 1.0，支持已移除）；其余 harness 一律不尝试。新增 harness 前必须先归入上表两层之一。

## 快速安装

### 前置要求

- Python 3.12+
- [uv 包管理器](https://docs.astral.sh/uv/)（Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`）
- 任一 Agent 运行时：Trae / CodeBuddy / opencode

### 安装步骤

> **获取插件包有两种方式，结果一致**：
> - **方式 A — 下载并解压**：从 GitHub Release 取压缩包（全部运行时通用，见下「1. 下载并解压」）。
> - **方式 B — Git URL / 仓库安装**：VS Code / CodeBuddy 直接把 GitHub 仓库（`https://github.com/yecllsl/DeepReview.git`）作为插件市场来源远程加载，**无需下载压缩包**；插件包（mcp.json + skills/ + AGENTS.md + deep-review-mcp/）由客户端克隆加载。详见 [QUICKSTART.md](QUICKSTART.md)。

#### 1. 下载并解压（方式 A）

下载 `DeepReview-v0.6.2.zip`，解压到任意目录（如 `D:\DeepReview\`）。

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

安装脚本会自动检查环境，并在 `deep-review.plugin/deep-review-mcp/` 下执行 `uv sync` 创建虚拟环境、安装依赖（MCP server 依赖此虚拟环境启动）。

#### 3. 配置 Agent 运行时（按通道分流）

安装脚本通过 `-AgentRuntime` 指定运行时：`vscode` / `codebuddy` 走 **Tier 1 插件通道**，`trae` / `opencode` 走 **Tier 2 原生目录**同步。（VS Code / CodeBuddy 也可走「方式 B」Git URL 远程安装，跳过本步与安装脚本，详见 [QUICKSTART.md](QUICKSTART.md)）

```powershell
# Windows：Tier 2 一次配置全部（Trae + opencode）
.\install.ps1 -AgentRuntime all

# 或只配置单个运行时
.\install.ps1 -AgentRuntime vscode
.\install.ps1 -AgentRuntime codebuddy
.\install.ps1 -AgentRuntime trae
.\install.ps1 -AgentRuntime opencode
```

```bash
# Linux/macOS
./install.sh --agent-runtime all
```

> 四种运行时的**完整首次使用步骤**（各客户端具体操作、验证与排障）见 [QUICKSTART.md](QUICKSTART.md)。

Tier 2 两个项目级运行时的配置目录（`.trae/` `.opencode/`）由 `scripts/sync-agent-configs` 从 `deep-review.plugin/`（配置唯一真相源）单向生成（CodeBuddy / VS Code 走 Tier 1 插件通道，不产生原生目录）：

| 运行时 | 通道 | 配置目录 | 说明 |
|--------|------|---------|------|
| Trae | Tier 2 原生 | `.trae/` | 设置 → MCP → 启用项目级 MCP |
| opencode | Tier 2 原生 | `.opencode/` | 项目目录运行 `opencode` 自动加载 |

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
npm run sync-configs   # 同步 Tier 2 配置目录
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
│   │   ├── deep-review-capture/         # /capture
│   │   ├── deep-review-batch-capture/   # /batch-capture
│   │   ├── deep-review-analyze/         # /analyze
│   │   ├── deep-review-review/          # /review
│   │   └── deep-review-stats/           # /stats
│   ├── runtime/                            # 2 平台（Tier 2）运行时配置（generate-platform-configs.py 生成）
│   │   ├── trae.json / opencode.json
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
│       ├── pyproject.toml                 # Python 项目配置（version 0.6.2）
│       └── uv.lock                        # 依赖锁定文件
├── package.json                           # AAIF 声明入口（main）+ publish 脚本（agents publish）
├── .trae/                                  # [生成] Trae 配置（sync 单向覆盖；规则已合并入 deep-review.plugin/AGENTS.md）
├── .opencode/                              # [生成] opencode 配置（opencode.json + skills + AGENTS.md）
├── scripts/                                # 开发者工具
│   ├── generate-aaif-declarations.py       # FastMCP 自省生成 AAIF 声明（规范格式）
│   ├── generate-platform-configs.py        # 生成 deep-review.plugin/runtime/ 2 平台（Tier 2）JSON
│   ├── sync-agent-configs.ps1/.sh          # deep-review.plugin/ 单向同步到 Tier 2 平台目录
│   ├── pre-commit                          # git 钩子：内容一致性检查（拦截配置同步违规）
│   ├── check-config-drift.sh               # CI 工作区漂移检查（与 pre-commit 双防线）
│   ├── check_version.py                    # 版本一致性校验（CI config-drift job 调用）
│   └── build-release.ps1/.sh               # 发布包构建
├── AGENTS.md                               # [生成] 根规则文件（Trae 读取约定，由 sync 复制）
├── install.ps1 / install.sh                # 安装脚本（-AgentRuntime/-FixPath）
├── QUICKSTART.md / DEPLOY.md / README.md   # 文档
├── CHANGELOG.md                            # 变更记录
└── LICENSE                                 # MIT
```

## 架构设计说明

### 分层分离原则

本项目采用 **"服务层 + 配置层 + 规则层 + 插件层"** 分离架构（Agent Plugins 1.0 插件打包规范 + AAIF 单项标准声明）：

| 层级 | 位置 | 用途 |
|------|------|------|
| **插件层** | `deep-review.plugin/`（自包含插件包） | Agent Plugins 1.0：`plugin.json`（manifest）+ `mcp.json`（`${PLUGIN_ROOT}` 内联 MCP 启动），可整体分发 |
| **服务层** | `deep-review.plugin/deep-review-mcp/` | 纯 Python MCP Server，通用，不绑定任何客户端，内联在插件包内 |
| **Web 可视化层** | `deep-review.plugin/deep-review-mcp/src/deep_review_mcp/web/` | 本地 Web 界面，FastAPI + HTMX + Alpine.js + ECharts |
| **配置层** | `deep-review.plugin/`（唯一真相源） | AGENTS.md + skills/ + runtime/ + tools/triggers/workflows.json（AAIF 声明）+ plugin.json/mcp.json |
| **生成产物** | `.trae/` `.opencode/` | 由 `scripts/sync-agent-configs` 从 `deep-review.plugin/` 单向同步生成（禁止直接编辑） |
| **规则层** | `deep-review.plugin/AGENTS.md` | 业务规则（采集/分类/分析/复习/交互/数据安全）统一约束 |

### 为什么要分离？

1. **职责清晰**: 代码归代码，配置归配置，规则归规则
2. **可复用**: `deep-review.plugin/deep-review-mcp/` 可单独在其他 MCP 客户端中使用，也可随插件整体发布
3. **配置单一真相源**: 配置只在 `deep-review.plugin/` 下编辑，3 个 harness 目录由同步脚本生成，杜绝配置漂移
4. **机械防线（双防线）**: `scripts/pre-commit` 钩子拦截「直接改生成目录而未同步」的违规提交；CI 另由 `scripts/check-config-drift.sh` 校验工作区一致性
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

1. 确认已在你的运行时中启用项目级 MCP（Trae：设置 → MCP → 启用项目级 MCP；CodeBuddy：打开项目后信任 deep-review-mcp；opencode：直接打开项目即可）
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

### 按需安装 FSRS 参数优化组件（可选）

复习页「FSRS 参数优化」面板默认可用默认 21 参数（对个人已足够好）。个性化参数拟合（Optimizer，依赖 numpy/pandas/torch 约 570MB）**默认不安装**，复习记录积累 512+ 条后按需启用：

```bash
uv sync --extra optimize
```

未安装时优化面板会提示安装命令，点击「分析参数」返回友好提示而非报错。

测试覆盖：72 个单元/集成用例 + 8 个 E2E 用例，矩阵 Python 3.12 / 3.13。

### 本地构建发布包

```powershell
# Windows
pwsh .\scripts\build-release.ps1 -Version 0.6.2
```

```bash
# Linux / macOS
bash scripts/build-release.sh 0.6.2
```

产物：`dist/DeepReview-v0.6.2.{zip,tar.zst,tar.gz}`。

### CI/CD

- **PR / push** → [`.github/workflows/test.yml`](.github/workflows/test.yml) 跑单元 + E2E + config-drift
- **push tag `v*.*.*`** → [`.github/workflows/release.yml`](.github/workflows/release.yml) 自动构建并发布 GitHub Release（附 `generate_release_notes` 自动 changelog）
