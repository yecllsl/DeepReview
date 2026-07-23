# DeepReview 部署指南

## 快速开始

### Windows 用户

```powershell
# 1. 从 GitHub Releases 下载 DeepReview-vX.Y.Z.zip，解压到任意目录（如 D:\DeepReview\）
#    或用 7-Zip 解压 .tar.zst / .tar.gz

# 2. 运行安装脚本
.\install.ps1

# 3. 用 Trae IDE 打开文件夹
# 4. 设置 → MCP → 启用项目级 MCP
# 5. 重启 Trae
```

### Linux / macOS 用户

```bash
# 1. 从 GitHub Releases 下载并解压
#    tar.zst (推荐):  tar --zstd -xf DeepReview-vX.Y.Z.tar.zst
#    tar.gz:          tar -xzf DeepReview-vX.Y.Z.tar.gz

# 2. 运行安装脚本
chmod +x install.sh
./install.sh

# 3. 用 Trae IDE 打开文件夹
# 4. 设置 → MCP → 启用项目级 MCP
# 5. 重启 Trae
```

### 安装时的可选步骤

`install.ps1` / `install.sh` 会在基础依赖装完后询问：

> **是否安装 OCR 可选依赖？**
> OCR 用于图片错题识别，paddleocr + paddlepaddle 约 1.5GB，安装较慢。
> 仅当需要 `/capture` 拍照录入错题时才需要。

- 选 `N`（默认）：跳过 OCR，文本录入、统计、复习等功能完全可用
- 选 `Y`：安装 PaddleOCR，后续可调用 `uv sync --extra ocr` 重新装

> 💡 跳过后若需要补装：`cd deep-review-mcp && uv sync --extra ocr`

## 环境要求

| 依赖 | 最低版本 | 安装方式 |
|------|---------|---------|
| Python | 3.12+ | https://www.python.org/downloads/ |
| uv | 最新版 | Windows: `irm https://astral.sh/uv/install.ps1 \| iex` |
| | | Linux/macOS: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Trae IDE CN | 最新版 | https://trae.com.cn |

## Trae IDE 配置详解

### 项目级 MCP（推荐）

项目级 MCP 配置已内置于 `.trae/mcp.json`，使用 `${workspaceFolder}` 变量自动适配路径，无需手动填写。

**启用步骤：**

1. 打开 Trae IDE
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
        "--directory",
        "${workspaceFolder}/deep-review-mcp",
        "deep-review-mcp"
      ]
    }
  }
}
```

`${workspaceFolder}` 会在 MCP Server 启动时自动替换为项目根目录路径，因此解压到任意位置都能正常工作。

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
| 参数 | `run --directory 你的项目路径/deep-review-mcp deep-review-mcp` |

### 验证配置

配置完成后，可以测试 MCP Server 是否正常工作：

```powershell
cd deep-review-mcp
uv run deep-review-mcp
```

如果 MCP Server 正常启动，说明配置成功。

## Skills 和 Rules 配置

Skills 和 Rules 配置位于 `.trae/` 目录下，Trae 会自动读取，修改后重启 Trae 即可生效。

### Skills 说明

| Skill 名称 | 触发命令 | 功能描述 |
|-----------|---------|---------|
| wrong-question-capture | `/capture` | 错题采集流程编排 |
| wrong-question-analyze | `/analyze` | 错题分析流程编排 |
| review-plan-generate | `/review` | 复习计划生成 |
| wrong-question-stats | `/stats` | 错题统计查询 |
| wrong-question-batch-capture | 批量采集 | 多道错题连续采集 |

### Rules 说明

| Rule 名称 | 作用范围 | 功能描述 |
|-----------|---------|---------|
| classification-rules | 分类相关 | 学科、知识点、错误类型约束 |
| analysis-rules | 分析相关 | 分析深度、改进方案约束 |
| data-safety-rules | 全局 | 数据安全与隐私保护 |
| interaction-rules | 全局 | 交互行为规范 |

## Web 可视化界面

### 启动

```powershell
cd deep-review-mcp
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
2. 依赖是否安装成功（运行 `cd deep-review-mcp && uv sync`）
3. mcp.json 中的路径是否正确

**解决方案：**
```powershell
cd deep-review-mcp
uv sync
```

### Q3: Trae 无法识别 MCP Server

**检查项：**
1. 是否已启用项目级 MCP
2. `.trae/mcp.json` 文件是否存在
3. 是否已重启 Trae

**解决方案：**
- 运行 `.\install.ps1 -FixPath` 修复路径
- 或手动在 Trae 中添加 MCP 服务器

### Q4: Skills/Commands 不生效

**检查项：**
1. `.trae/skills/` 和 `.trae/rules/` 目录是否存在
2. 文件名和格式是否正确
3. Trae 是否重启

**解决方案：**
- 重启 Trae IDE
- 检查 .trae 目录结构是否完整

### Q5: PaddleOCR / OCR 安装失败

**检查项：**
1. Python 版本是否 >= 3.12
2. 网络是否畅通（需下载 paddleocr + paddlepaddle 约 1.5GB）
3. 是否在 `uv sync` 时选择了 `N` 跳过 OCR

**解决方案：**
- OCR 为**可选依赖**，默认 `uv sync` 不会安装
- 如需使用 `/capture` 拍照录入：`cd deep-review-mcp && uv sync --extra ocr`
- 如不使用 OCR（手动输入/纯文本录入），**无需任何额外操作**

### Q6: Web 可视化界面无法访问

**检查项：**
1. 端口 8001 是否被占用：`netstat -ano | findstr 8001`（Windows）/ `lsof -i :8001`（macOS/Linux）
2. 浏览器是否访问 `http://127.0.0.1:8001`（不是 `localhost` 或局域网 IP）
3. Trae 是否占用了 8001 端口（Trae 内部服务）

**解决方案：**
- 修改端口：在 `deep-review-mcp/src/deep_review_mcp/web/app.py` 中调整 `port` 参数
- 关闭占用进程后重试

### Q7: 如何升级到新版本

1. 备份你的 `data/` 目录（包含所有错题）
2. 从 GitHub Releases 下载新版并解压到新目录
3. 把旧版的 `data/wrong_questions/` 等数据目录复制到新版对应位置
4. 在新目录运行 `install.ps1` / `install.sh`（会自动 `uv sync`）
5. 在 Trae 中重新启用项目级 MCP

## 项目结构说明

```
deep-review/
├── deep-review-mcp/                       # 纯 MCP Server (通用服务层)
│   ├── src/deep_review_mcp/
│   │   ├── server.py                      # 服务入口 (FastMCP)
│   │   ├── models.py                      # Pydantic 数据模型
│   │   ├── storage.py                     # JSON 文件存储（原子写）
│   │   ├── knowledge_map.py               # K12 知识点映射
│   │   ├── tools/                         # MCP Tools 实现 (11 个)
│   │   ├── prompts/                       # AI Prompt 模板
│   │   └── web/                           # Web 可视化模块
│   │       ├── app.py                     # FastAPI 应用工厂
│   │       ├── services.py                # Web 编排层
│   │       ├── schemas.py                 # 请求/响应模型
│   │       ├── routes/                    # 路由（dashboard/questions/stats/review）
│   │       ├── templates/                 # Jinja2 模板（base + partials）
│   │       └── static/                    # 本地化 JS 库
│   ├── tests/                             # 测试套件
│   │   ├── test_models.py
│   │   ├── test_storage.py / test_storage_patch.py
│   │   ├── test_tools_*.py                # 11 个 Tools 单元测试
│   │   ├── test_web_routes.py
│   │   ├── test_web_services.py
│   │   └── test_e2e_visualization.py      # Playwright E2E（8 用例）
│   ├── data/                              # 数据存储目录 (运行时)
│   │   ├── wrong_questions/               # 错题 JSON
│   │   ├── analysis_reports/              # 分析报告
│   │   ├── review_plans/                  # 复习计划
│   │   └── exports/                       # 导出文件
│   ├── pyproject.toml                     # Python 项目配置
│   └── uv.lock                            # 依赖锁定
│
├── .trae/                                  # Trae 配置与 Skills/Rules 源文件
│   ├── mcp.json                            # 项目级 MCP 配置
│   ├── hooks.json
│   ├── skills/                             # 5 个 Skills 源文件
│   │   ├── wrong-question-capture/         # /capture
│   │   ├── wrong-question-analyze/         # /analyze
│   │   ├── review-plan-generate/           # /review
│   │   ├── wrong-question-stats/           # /stats
│   │   └── wrong-question-batch-capture/   # 批量采集
│   └── rules/                              # 4 个 Rules
│       ├── classification-rules.md
│       ├── analysis-rules.md
│       ├── data-safety-rules.md
│       └── interaction-rules.md
│
├── .github/
│   └── workflows/
│       ├── test.yml                        # CI：单元 + E2E（3.12/3.13）
│       └── release.yml                     # Release：push tag → 自动打包 + 上传
│
├── scripts/                                # 开发者工具
│   ├── build-release.ps1                   # Windows 发布包构建
│   └── build-release.sh                    # Linux/macOS 发布包构建（与 .ps1 对齐）
├── install.ps1                             # Windows 安装脚本（可选装 OCR）
├── install.sh                              # Linux/macOS 安装脚本（可选装 OCR）
├── QUICKSTART.md                           # 5 分钟快速上手
├── DEPLOY.md                               # 本文件
├── README.md                               # 项目总览
└── LICENSE                                 # MIT
```

## 开发者工具

### 本地构建发布包

```powershell
# Windows (PowerShell 7+)
pwsh .\scripts\build-release.ps1 -Version 0.2.0
```

```bash
# Linux / macOS
bash scripts/build-release.sh 0.2.0
```

产物：`dist/DeepReview-v0.2.0.{zip,tar.zst,tar.gz}`，结构与 GitHub Release 资产一致。

构建脚本采用**白名单复制策略**，只打包必要文件，自动排除：

- `__pycache__/`、`.pytest_cache/`、`*.pyc`
- `.venv/`、`.git/`、`.vscode/`
- `data/*.json`（用户数据不打包，只放 `.gitkeep` 占位）
- `dist/`（构建产物本身）

### 本地运行测试

```bash
cd deep-review-mcp

# 单元 + 集成测试（72 用例，~2 秒）
uv sync --extra dev
uv run pytest tests/ -m "not e2e"

# E2E 测试（8 用例，~15 秒）
uv run playwright install chromium
uv run pytest tests/test_e2e_visualization.py -m e2e
```

### GitHub Actions

- **`.github/workflows/test.yml`**：PR / push 时跑单元 + E2E（矩阵 Python 3.12 / 3.13）
- **`.github/workflows/release.yml`**：push tag `v*.*.*` 时构建 + 上传 release，附 `generate_release_notes` 自动生成 changelog
