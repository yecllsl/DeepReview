# DeepReview 部署指南

## 快速开始

### Windows 用户

```powershell
# 1. 从 GitHub Releases 下载 DeepReview-vX.Y.Z.zip，解压到任意目录（如 D:\DeepReview\）
#    或用 7-Zip 解压 .tar.zst / .tar.gz

# 2. 运行安装脚本（-AgentRuntime 指定要配置的运行时）
.\install.ps1 -AgentRuntime all
#    或只配置单个：.\install.ps1 -AgentRuntime trae / codebuddy / opencode / goose

# 3. 用你的运行时打开文件夹
#    Trae:       设置 → MCP → 启用项目级 MCP
#    CodeBuddy:  打开项目后信任 deep-review-mcp
#    opencode:   项目目录运行 opencode
#    Goose:      打开项目自动读取 .goose/config.yaml
# 4. 重启运行时
```

### Linux / macOS 用户

```bash
# 1. 从 GitHub Releases 下载并解压
#    tar.zst (推荐):  tar --zstd -xf DeepReview-vX.Y.Z.tar.zst
#    tar.gz:          tar -xzf DeepReview-vX.Y.Z.tar.gz

# 2. 运行安装脚本（--agent-runtime 指定要配置的运行时）
chmod +x install.sh
./install.sh --agent-runtime all
#    或只配置单个：./install.sh --agent-runtime trae / codebuddy / opencode / goose

# 3. 用你的运行时打开文件夹
#    Trae:       设置 → MCP → 启用项目级 MCP
#    CodeBuddy:  打开项目后信任 deep-review-mcp
#    opencode:   项目目录运行 opencode
#    Goose:      打开项目自动读取 .goose/config.yaml
# 4. 重启运行时
```

## 环境要求

| 依赖 | 最低版本 | 安装方式 |
|------|---------|---------|
| Python | 3.12+ | https://www.python.org/downloads/ |
| uv | 最新版 | Windows: `irm https://astral.sh/uv/install.ps1 \| iex` |
| | | Linux/macOS: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Trae / CodeBuddy / opencode / Goose | 最新版 | 任一 Agent 运行时 |

## Agent 运行时配置详解

v0.3.0 起支持 4 个 Agent 运行时（harness）：Trae / CodeBuddy / opencode / Goose；v0.5.0 起符合 Agent Plugins 1.0（Vercel 等厂商中立打包规范，与 AAIF 无隶属关系）规范。配置统一由 `scripts/sync-agent-configs` 从 `deep-review.plugin/`（AAIF 唯一真相源 + 自包含插件包）单向生成，**禁止直接编辑生成目录**。修改配置的正确流程：改 `deep-review.plugin/` → 运行同步脚本 → 各生成目录与 `deep-review.plugin/` 一起提交（`scripts/pre-commit` 钩子会拦截违规提交；CI 另由 `scripts/check-config-drift.sh` 兜底）。

### Trae（项目级 MCP）

项目级 MCP 配置已内置于 `.trae/mcp.json`，使用 `${workspaceFolder}` 变量自动适配路径，无需手动填写。

**启用步骤：**

1. 打开 Trae
2. 进入 **设置** (齿轮图标) → **MCP**
3. 打开 **"启用项目级 MCP"** 开关
4. 在弹窗中确认信任
5. 重启 Trae

**mcp.json 配置内容：**

```json
{
  "mcpServers": {
    "deep-review-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--no-sync",
        "--directory",
        "${workspaceFolder}/deep-review.plugin/deep-review-mcp",
        "deep-review-mcp"
      ]
    }
  }
}
```

`${workspaceFolder}` 会在 MCP Server 启动时自动替换为项目根目录路径，因此解压到任意位置都能正常工作；`--no-sync` 复用安装时 `uv sync` 的环境，避免每次启动解析依赖。

### CodeBuddy（项目级）

- 配置目录 `.codebuddy/`（mcp.json + skills + AGENTS.md）
- 用 CodeBuddy 打开项目文件夹，在 MCP 配置中信任 `deep-review-mcp`

### opencode（项目级）

- 配置目录 `.opencode/`（opencode.json + skills + AGENTS.md）
- 在项目目录运行 `opencode`，自动加载 `deep-review.plugin/AGENTS.md` 规则

### Goose（项目级）

- 配置目录 `.goose/`（config.yaml + skills + AGENTS.md）
- 用 Goose 打开项目文件夹，自动读取 `.goose/config.yaml` 加载 MCP 扩展

### 手动配置（回退方案）

如果你的 Trae 版本不支持 `${workspaceFolder}` 变量，可以运行安装脚本的路径修复功能：

```powershell
# Windows
.\install.ps1 -FixPath

# Linux/macOS
./install.sh --fix-path
```

这会自动将 mcp.json 中的变量替换为实际路径。

也可以手动在 Trae 中添加 MCP 服务器：

| 字段 | 值 |
|------|-----|
| 服务器名称 | `deep-review-mcp` |
| 命令 | `uv` |
| 参数 | `run --directory 你的项目路径/deep-review.plugin/deep-review-mcp deep-review-mcp` |

### 验证配置

配置完成后，可以测试 MCP Server 是否正常工作：

```powershell
cd deep-review.plugin/deep-review-mcp
uv run deep-review-mcp
```

如果 MCP Server 正常启动，说明配置成功。

## Skills 和 Rules 配置

Skills 和 Rules 的**唯一真相源**在 `deep-review.plugin/`（AAIF 规范 + Agent Plugins 1.0 插件包）：

- **Skills**：`deep-review.plugin/skills/`（frontmatter 含 `command:` 字段映射命令）
- **Rules**：`deep-review.plugin/AGENTS.md`（统一规则，含采集/分类/分析/复习/交互/数据安全规则）
- **插件契约**：`deep-review.plugin/plugin.json`（manifest）+ `deep-review.plugin/mcp.json`（`${PLUGIN_ROOT}` 内联 MCP 启动）

四个项目级 harness 目录（`.trae/` `.opencode/` `.codebuddy/` `.goose/`）由 `scripts/sync-agent-configs` 单向生成，**禁止直接编辑**。修改后需重跑同步脚本，并提交 `deep-review.plugin/` 与各生成目录的改动（`scripts/pre-commit` 钩子与 CI `scripts/check-config-drift.sh` 双防线自动拦截违规）。

### Skills 说明

| Skill 名称 | 触发命令 | 功能描述 |
|-----------|---------|---------|
| deep-review-capture | `/capture` | 错题采集流程编排 |
| deep-review-batch-capture | `/batch-capture` | 多道错题连续采集 |
| deep-review-analyze | `/analyze` | 错题分析流程编排 |
| deep-review-review | `/review` | 复习计划生成 |
| deep-review-stats | `/stats` | 错题统计查询 |

## Web 可视化界面

### 启动

```powershell
cd deep-review.plugin/deep-review-mcp
uv run deep-review-web
```

浏览器访问 http://127.0.0.1:8001

### 四大页面

1. **概览 Dashboard**：错题总数、今日待复习、本周新增、学科分布、错误类型分布、30天趋势
2. **错题列表与详情**：筛选查看、编辑保存（HTMX OOB swap 局部刷新，**保存后左侧列表自动更新无需手动刷新**）
3. **统计图表**：知识点热力图、难度分布、错误类型雷达、时间趋势
4. **复习追踪**：待复习清单、复习日历、遗忘曲线、学科复习进度

### 技术栈

- **后端**：FastAPI（异步）+ Jinja2 模板
- **前端**：HTMX（局部更新 / OOB swap）+ Alpine.js（轻量交互）+ ECharts（图表）
- **数据访问**：通过 `web/services.py` 编排层访问 `storage.py`，保证与 MCP 工具一致

### 安全特性

- 仅绑定 `127.0.0.1`（不暴露到局域网）
- 所有 JS 库（HTMX / Alpine.js / ECharts）本地化在 `web/static/`，**无 CDN**
- 所有数据仅本地存储，无任何外部请求

## 常见问题

### Q1: 安装脚本报错 "uv 未安装"

**解决方案：**
```powershell
# 安装 uv (Windows PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 安装 uv (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Q2: MCP Server 启动失败

**检查项：**
1. Python 版本是否 >= 3.12
2. 依赖是否安装成功（运行 `cd deep-review.plugin/deep-review-mcp && uv sync`）
3. mcp.json 中的路径是否正确

**解决方案：**
```powershell
cd deep-review.plugin/deep-review-mcp
uv sync
```

### Q3: 运行时无法识别 MCP Server

**检查项：**
1. 是否已启用项目级 MCP（Trae/CodeBuddy）或已打开项目（opencode/Goose）
2. 对应配置目录是否存在（`.trae/mcp.json` / `.codebuddy/mcp.json` / `.opencode/opencode.json` / `.goose/config.yaml`）
3. 是否已重启运行时

**解决方案：**
- 运行 `.\install.ps1 -FixPath`（或 `./install.sh --fix-path`）修复路径
- 或手动在运行时中添加 MCP 服务器

### Q4: Skills/Commands 不生效

**检查项：**
1. `deep-review.plugin/skills/` 是否存在（唯一真相源）
2. 各 harness 目录的 skills/ 是否已同步（重跑 `scripts/sync-agent-configs.ps1` 或 `.sh`）
3. 运行时是否重启

**解决方案：**
- 重启运行时
- 重跑同步脚本：`pwsh scripts/sync-agent-configs.ps1`（或 `bash scripts/sync-agent-configs.sh`）
- 若提交被 `scripts/pre-commit` 拦截，说明直接改了生成目录，需从 `deep-review.plugin/` 重做

### Q5: Web 可视化界面无法访问

**检查项：**
1. 端口 8001 是否被占用：`netstat -ano | findstr 8001`（Windows）/ `lsof -i :8001`（macOS/Linux）
2. 浏览器是否访问 `http://127.0.0.1:8001`（不是 `localhost` 或局域网 IP）
3. Trae 是否占用了 8001 端口（Trae 内部服务）

**解决方案：**
- 修改端口：在 `deep-review.plugin/deep-review-mcp/src/deep_review_mcp/web/app.py` 中调整 `port` 参数
- 关闭占用进程后重试

### Q7: 如何升级到新版本

1. 备份你的 `data/` 目录（包含所有错题）
2. 从 GitHub Releases 下载新版并解压到新目录
3. 把旧版的 `data/wrong_questions/` 等数据目录复制到新版对应位置
4. 在新目录运行 `install.ps1` / `install.sh`（会自动 `uv sync`），并用 `-AgentRuntime` 重新配置运行时
5. 在运行时中重新启用项目级 MCP

## 项目结构说明

```
DeepReview/
├── deep-review.plugin/                     # Agent Plugins 1.0 插件根（AAIF 唯一真相源，自包含可分发）
│   ├── plugin.json                         # Agent Plugins 1.0 manifest（$schema/name/version/...）
│   ├── mcp.json                            # MCP 启动配置（${PLUGIN_ROOT} 内联 deep-review-mcp）
│   ├── AGENTS.md                           # 统一规则层（架构/安全/开发规范/流程规则 + 业务规则）
│   ├── skills/                             # 5 个技能源文件（frontmatter 含 command:）
│   ├── runtime/                            # 4 平台运行时配置（generate-platform-configs.py 生成）
│   ├── tools.json / triggers.json / workflows.json   # AAIF 声明（生成产物，勿手改）
│   └── deep-review-mcp/                    # 纯 MCP Server (通用服务层，内联)
│       ├── src/deep_review_mcp/
│       │   ├── server.py                  # 服务入口 (FastMCP)
│       │   ├── models.py                  # Pydantic 数据模型
│       │   ├── storage.py                 # JSON 文件存储（原子写）
│       │   ├── knowledge_map.py           # K12 知识点映射
│       │   ├── tools/                     # MCP Tools 实现 (10 个)
│       │   ├── prompts/                   # AI Prompt 模板
│       │   └── web/                       # Web 可视化模块（app/services/schemas/routes/templates/static）
│       ├── tests/                         # 测试套件
│       ├── data/                          # 数据存储目录 (运行时)
│       │   ├── wrong_questions/           # 错题 JSON
│       │   ├── analysis_reports/          # 分析报告
│       │   ├── review_plans/              # 复习计划
│       │   └── exports/                   # 导出文件
│       ├── pyproject.toml                 # Python 项目配置（version 0.5.0）
│       └── uv.lock                        # 依赖锁定
├── package.json                           # AAIF 声明入口（main）+ publish 脚本（agents publish）
├── .trae/                                  # [生成] Trae 配置（sync 单向覆盖；规则已合并入 deep-review.plugin/AGENTS.md）
├── .opencode/                              # [生成] opencode 配置（opencode.json + skills + AGENTS.md）
├── .codebuddy/                             # [生成] CodeBuddy 配置（memory/ 由运行时写入）
├── .goose/                                 # [生成] Goose 配置（config.yaml + skills + AGENTS.md）
├── scripts/                                # 开发者工具
│   ├── generate-aaif-declarations.py       # FastMCP 自省生成 AAIF 声明（规范格式）
│   ├── generate-platform-configs.py        # 生成 deep-review.plugin/runtime/ 4 平台 JSON
│   ├── generate-goose-config.py            # goose.json → .goose/config.yaml
│   ├── sync-agent-configs.ps1/.sh          # deep-review.plugin/ 单向同步到 4 平台目录
│   ├── pre-commit                          # git 钩子：内容一致性检查（拦截配置同步违规）
│   ├── check-config-drift.sh               # CI 工作区漂移检查（双防线）
│   └── build-release.ps1/.sh               # 发布包构建
├── AGENTS.md                               # [生成] 根规则文件（Trae 读取约定，由 sync 复制）
├── install.ps1 / install.sh                # 安装脚本（-AgentRuntime/-FixPath）
├── QUICKSTART.md / DEPLOY.md / README.md   # 文档
└── LICENSE                                 # MIT
```

## 开发者工具

### 本地构建发布包

```powershell
# Windows (PowerShell 7+)
pwsh .\scripts\build-release.ps1 -Version 0.5.0
```

```bash
# Linux / macOS
bash scripts/build-release.sh 0.5.0
```

产物：`dist/DeepReview-v0.5.0.{zip,tar.zst,tar.gz}`，结构与 GitHub Release 资产一致。

构建脚本采用**白名单复制策略**，打包 `deep-review.plugin/`（AAIF 真相源 + Agent Plugins 1.0 插件包，含内联 `deep-review-mcp/`）、`.trae/` `.opencode/` `.codebuddy/` `.goose/`（harness 配置）、`scripts/`（同步工具链）、`package.json`（发布入口），自动排除：

- `__pycache__/`、`.pytest_cache/`、`*.pyc`
- `.venv/`、`.git/`、`.vscode/`
- `data/*.json`（用户数据不打包，只放 `.gitkeep` 占位）
- `dist/`（构建产物本身）

> 发布包内的 `.goose/config.yaml` 使用相对路径版（`generate-goose-config.py --no-resolve-dir`），用户本地运行安装脚本后自动重新生成绝对路径版。

### 本地运行测试

```bash
cd deep-review.plugin/deep-review-mcp

# 单元 + 集成测试
uv sync --extra dev
uv run pytest tests/ -m "not e2e"

# E2E 测试
uv run playwright install chromium
uv run pytest tests/test_e2e_visualization.py -m e2e
```

### GitHub Actions

- **`.github/workflows/test.yml`**：PR / push 时跑单元 + E2E + config-drift（矩阵 Python 3.12 / 3.13）
- **`.github/workflows/release.yml`**：push tag `v*.*.*` 时构建 + 上传 release，附 `generate_release_notes` 自动生成 changelog
