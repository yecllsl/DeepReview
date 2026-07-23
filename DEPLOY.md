# DeepReview 部署指南

## 快速开始

### Windows 用户

```powershell
# 1. 解压 DeepReview-v0.1.0.zip 到任意目录（如 D:\DeepReview\）

# 2. 运行安装脚本
.\install.ps1

# 3. 用 Trae IDE 打开文件夹
# 4. 设置 → MCP → 启用项目级 MCP
# 5. 重启 Trae
```

### Linux / macOS 用户

```bash
# 1. 解压 DeepReview-v0.1.0.zip 到任意目录

# 2. 运行安装脚本
chmod +x install.sh
./install.sh

# 3. 用 Trae IDE 打开文件夹
# 4. 设置 → MCP → 启用项目级 MCP
# 5. 重启 Trae
```

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
2. **错题列表与详情**：筛选查看、编辑保存（支持 HTMX 局部更新）
3. **统计图表**：知识点热力图、难度分布、错误类型雷达、时间趋势
4. **复习追踪**：待复习清单、复习日历、遗忘曲线、学科复习进度

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

### Q5: PaddleOCR 安装失败

**检查项：**
1. Python 版本是否 >= 3.12
2. 网络是否畅通（需下载模型文件）

**解决方案：**
- 确保网络畅通后重新运行 `uv sync`
- OCR 有降级方案：可手动输入题目内容

## 项目结构说明

```
deep-review/
├── deep-review-mcp/           # 纯 MCP Server (通用服务层)
│   ├── src/deep_review_mcp/
│   │   ├── server.py          # 服务入口 (FastMCP)
│   │   ├── models.py          # Pydantic 数据模型
│   │   ├── storage.py         # JSON 文件存储
│   │   ├── knowledge_map.py   # K12 知识点映射
│   │   ├── tools/             # MCP Tools 实现 (11 个)
│   │   └── web/               # Web 可视化模块
│   ├── data/                   # 数据存储目录 (运行时)
│   ├── pyproject.toml          # Python 项目配置
│   └── uv.lock                 # 依赖锁定文件
│
├── .trae/                       # Trae 配置与 Skills/Rules 源文件
│   ├── mcp.json                 # 项目级 MCP 配置
│   ├── skills/                  # Skills 源文件
│   └── rules/                   # Rules 源文件
│
├── scripts/                     # 开发者工具
│   └── build-release.ps1        # 发布包构建脚本
├── install.ps1                  # Windows 安装脚本
├── install.sh                   # Linux/macOS 安装脚本
└── README.md
```
