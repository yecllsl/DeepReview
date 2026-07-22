# DeepReview 部署指南

## 快速开始

### Windows 用户

```powershell
# 1. 克隆项目
git clone https://github.com/yecllsl/deep-review.git
cd deep-review

# 2. 运行安装脚本
.\install.ps1

# 3. 在 Trae Work 中配置 MCP
# 设置 → MCP配置 → 添加MCP服务器 → 从文件导入
# 选择: .trae/mcp-servers/deep-review-mcp/SERVER_METADATA.json
```

### Linux / macOS 用户

```bash
# 1. 克隆项目
git clone https://github.com/yecllsl/deep-review.git
cd deep-review

# 2. 添加执行权限并运行安装脚本
chmod +x install.sh
./install.sh

# 3. 在 Trae Work 中配置 MCP
# 设置 → MCP配置 → 添加MCP服务器 → 从文件导入
# 选择: .trae/mcp-servers/deep-review-mcp/SERVER_METADATA.json
```

## Trae Work 配置详解

### 方法一：从文件导入 (推荐)

1. 打开 Trae Work IDE
2. 进入 **设置** (齿轮图标)
3. 找到 **MCP配置** 选项
4. 点击 **添加MCP服务器**
5. 选择 **从文件导入**
6. 选择 `SERVER_METADATA.json` 文件

### 方法二：手动配置

如果导入失败，可以手动填写：

| 字段 | 值 |
|------|-----|
| 服务器名称 | `deep-review-mcp` |
| 命令 | `uv` |
| 参数 | `run deep-review-mcp` |
| 工作目录 | `项目路径\deep-review-mcp` |
| 传输方式 | `stdio` |

### 验证配置

配置完成后，可以测试 MCP Server 是否正常工作：

```powershell
cd deep-review-mcp
uv run deep-review-mcp
```

如果看到类似输出，说明配置成功：
```
Starting DeepReview MCP Server...
Tools registered: 11
Server ready.
```

## Skills 和 Rules 配置

Skills 和 Rules 配置位于 `.trae/` 目录下，是 Trae Work 实际读取的配置源，修改后重启 Trae Work 即可生效。

### 配置目录结构

```
.trae/skills/     → 5 个 Skill 流程定义
.trae/rules/      → 4 个 Rules 约束定义
```

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
2. 依赖是否安装成功
3. 工作目录是否正确

**解决方案：**
```powershell
cd deep-review-mcp
uv pip install -e .
```

### Q3: Trae 无法识别 MCP Server

**检查项：**
1. SERVER_METADATA.json 是否在正确位置
2. 工作目录路径是否包含中文字符（可能导致问题）
3. uv 命令是否在系统 PATH 中

**解决方案：**
- 尝试方法二：手动配置
- 确保工作目录使用英文路径

### Q4: Skills/Commands 不生效

**检查项：**
1. `.trae/skills/` 和 `.trae/rules/` 目录是否存在
2. 文件名和格式是否正确
3. Trae 是否重启

**解决方案：**
- 重启 Trae Work IDE
- 检查 .trae 目录结构是否完整

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
│   │   │   ├── ocr_recognize.py
│   │   │   ├── classify.py
│   │   │   ├── analyze.py
│   │   │   ├── improvement.py
│   │   │   ├── review.py
│   │   │   ├── statistics.py
│   │   │   ├── export.py
│   │   │   └── crud.py
│   │   └── prompts/           # AI Prompt 模板
│   │       ├── structure_parse.py
│   │       ├── classify_prompt.py
│   │       ├── analyze_prompt.py
│   │       └── improvement_prompt.py
│   ├── data/                   # 数据存储目录 (运行时)
│   │   ├── wrong_questions/   # 错题 JSON 文件
│   │   ├── analysis_reports/  # 分析报告
│   │   └── review_plans/      # 复习计划
│   ├── tests/                  # 单元测试
│   ├── pyproject.toml          # Python 项目配置
│   └── uv.lock                 # 依赖锁定文件
│
├── docs/                        # 设计文档与实施计划
│   └── superpowers/
│       ├── specs/               # 设计文档
│       └── plans/               # 实施计划
│
├── .trae/                       # Trae 配置与 Skills/Rules 源文件
│   ├── mcp-servers/
│   │   └── deep-review-mcp/
│   │       ├── SERVER_METADATA.json
│   │       └── tools/          # 工具元数据
│   ├── skills/                 # Skills 源文件（单一真相源）
│   │   ├── wrong-question-capture/
│   │   ├── wrong-question-analyze/
│   │   ├── review-plan-generate/
│   │   ├── wrong-question-stats/
│   │   └── wrong-question-batch-capture/
│   └── rules/                  # Rules 源文件（单一真相源）
│       ├── classification-rules.md
│       ├── analysis-rules.md
│       ├── data-safety-rules.md
│       └── interaction-rules.md
│
├── README.md                    # 项目说明
├── DEPLOY.md                    # 本部署指南
├── install.ps1                  # Windows 安装脚本
└── install.sh                   # Linux/macOS 安装脚本
```

## 架构设计原则

### 为什么 Skills/Rules 配置放在 `.trae/` 下？

| 设计决策 | 原因 |
|---------|------|
| **服务层独立** | `deep-review-mcp/` 是纯 Python MCP Server，通用，可独立发布到 PyPI |
| **配置单一真相源** | Skills/Rules 配置直接在 `.trae/` 下编辑，Trae Work 直接读取，无需同步步骤 |
| **结构清晰** | 项目根目录只保留核心代码和文档，Trae 专有配置集中在 `.trae/` 下 |

### 编辑哪个文件？

| 要修改的内容 | 编辑位置 | 说明 |
|------------|---------|------|
| Skills 流程 | `.trae/skills/` | 修改后重启 Trae Work 生效 |
| Rules 约束 | `.trae/rules/` | 修改后重启 Trae Work 生效 |
| MCP Tools 功能 | `deep-review-mcp/src/` | 修改后重新运行 `uv pip install -e .` |
| MCP 配置 | `.trae/mcp-servers/` | 安装脚本自动生成，一般无需手动编辑 |

## 更新项目

```powershell
# 拉取最新代码
git pull origin main

# 重新安装依赖
cd deep-review-mcp
uv pip install -e .

# 重启 Trae Work
```

## 卸载

```powershell
# 删除项目目录
rm -rf deep-review

# 从 Trae 中移除 MCP Server
# 设置 → MCP配置 → 删除 deep-review-mcp

# 删除 Skills 和 Rules (如果不再需要)
rm -rf 您的项目/.trae/skills/*
rm -rf 您的项目/.trae/rules/*
```

## 技术支持

- 提交 Issue: https://github.com/yecllsl/deep-review/issues
- 查看文档: https://github.com/yecllsl/deep-review#readme
