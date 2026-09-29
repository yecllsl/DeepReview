# DeepReview 快速入门

## 前置要求（四种运行时都需要）

- **Python 3.12+**，且 `python` 命令在 PATH（安装脚本会以 `python --version` 校验）
- **uv** 包管理器：`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`（或见 https://docs.astral.sh/uv/getting-started/installation/）

> ⚠️ **前置**：MCP server 由 `uv run` 启动。VS Code / CodeBuddy（Tier 1，含 Git URL 远程安装）会在首次启动时自动 `uv sync` 构建虚拟环境；Trae / opencode（Tier 2）需先跑一次安装脚本（`uv sync` 建环境 + 同步原生目录）。只要本机已装 `uv` 与 Python 3.12+ 即可。

## 开始使用（两种方式）

DeepReview 提供**两种获取方式，结果完全一致**——都拿到插件包 `deep-review.plugin/`（`mcp.json` + `skills/` + `AGENTS.md` + `deep-review-mcp/`）：

- **方式 A — 下载并解压**：从 GitHub Release 取压缩包，全部运行时通用。
- **方式 B — Git URL / 仓库安装**：仅 VS Code / CodeBuddy 支持，把 GitHub 仓库直接作为插件市场来源加载，**无需下载压缩包**。

### 方式 A：下载并解压

从 [GitHub Releases](https://github.com/yecllsl/DeepReview/releases) 下载最新版本，按需选择格式：

- **Windows**：`DeepReview-vX.Y.Z.zip`（用资源管理器/7-Zip 解压）
- **现代 Linux/macOS**：`DeepReview-vX.Y.Z.tar.zst`（`tar --zstd -xf` 或 `zstd -d` + `tar -xf`）
- **兼容老旧系统**：`DeepReview-vX.Y.Z.tar.gz`（`tar -xzf`）

解压到任意目录（如 `D:\DeepReview\` 或 `~/DeepReview/`）。

### 方式 B：Git URL / 仓库安装（VS Code / CodeBuddy，无需下载）

VS Code 与 CodeBuddy 支持把 **GitHub 仓库 / Git URL 直接作为插件市场来源**，客户端自动克隆插件包到其市场缓存目录，**无需手动下载 Release 压缩包**。插件包（`mcp.json` + `skills/` + `AGENTS.md` + `deep-review-mcp/`）随之一并加载：

- **CodeBuddy**：对话中执行 `/plugin marketplace add https://github.com/yecllsl/DeepReview.git`（或简写 `yecll/DeepReview`）添加远程市场 → `/plugin marketplace list` 确认市场名（GitHub 仓库通常形如 `yecllsl-deep-review`）→ `/plugin install deep-review@<市场名>` → 必要时 `/reload-plugins`。
- **VS Code（Agent Plugins 1.0）**：在 VS Code `settings.json` 的 `chat.plugins.marketplaces` 加入 `"yecllsl/DeepReview"`（仓库根含 `marketplace.json`，其 `source` 指向 `./deep-review.plugin`）→ 打开 Agents 面板 → **Browse Marketplace / 浏览插件市场** → 安装 `deep-review`，客户端克隆插件包到市场缓存目录。

> 方式 B 下 MCP server 首次启动时 `uv run` 会自动 `uv sync` 构建虚拟环境，无需手动执行；`skills/` 与 `AGENTS.md` 随插件包一并加载。Trae / opencode 不支持此方式，请走方式 A。

### 安装依赖（仅方式 A 需要）

```powershell
# Windows: 右键 install.ps1 → "使用 PowerShell 运行"
.\install.ps1
```

```bash
# Linux/macOS:
chmod +x install.sh && ./install.sh
```

> 方式 B（VS Code / CodeBuddy 远程安装）由客户端托管插件包，`uv run` 自动同步依赖，**无需运行安装脚本**。

### 配置 Agent 运行时（方式 A 按通道分流）

安装脚本通过 `-AgentRuntime` 指定要配置的运行时（缺省只装依赖，不配置运行时）：

```powershell
# Windows
.\install.ps1 -AgentRuntime vscode     # 或 trae / codebuddy / opencode / all
```

```bash
# Linux/macOS
./install.sh --agent-runtime vscode    # 或 trae / codebuddy / opencode / all
```

| 运行时 | 通道 | 获取方式 | 使用方式 |
|--------|------|---------|---------|
| VS Code | Tier 1 插件 | 方式 A 或 **方式 B** | A：打开项目 → Agent 面板添加本地 Agent Plugin → 指向 `deep-review.plugin/`<br>B：settings.json `chat.plugins.marketplaces` 加 `yecllsl/DeepReview` → 浏览市场安装 `deep-review` |
| CodeBuddy | Tier 1 插件 | 方式 A 或 **方式 B** | A：打开项目 → `/plugin marketplace add <根目录>` → install<br>B：`/plugin marketplace add <仓库URL>` → install |
| Trae | Tier 2 原生 | 仅方式 A | 打开项目 → 设置 → MCP → 启用项目级 MCP（`.trae/` 由 install 同步生成） |
| opencode | Tier 2 原生 | 仅方式 A | 在项目根目录运行 `opencode`（`.opencode/` 由 install 同步生成） |

#### VS Code（Tier 1 · Agent Plugins 1.0）

- **方式 B（推荐，无需下载 · GitHub 远程市场）**：在 VS Code `settings.json` 加入 `"chat.plugins.marketplaces": ["yecllsl/DeepReview"]`（仓库根含 `marketplace.json`，其 `source` 指向 `./deep-review.plugin`）→ 打开 Agents 面板 → **Browse Marketplace / 浏览插件市场** → 安装 `deep-review`（含 `plugin.json` + `mcp.json` + `skills/` + `AGENTS.md`）。
  - 注：VS Code 的 **Install from Source** 要求在仓库**根**存在 `plugin.json`，本仓库插件在 `deep-review.plugin/` 子目录，故不能用「子目录 URL」直装；远程市场方式借助根 `marketplace.json` 的 `source` 间接层解析子目录，是本仓库走 GitHub 的正确路径。
- **方式 A（下载解压）**：`.\install.ps1 -AgentRuntime vscode`（或 `./install.sh --agent-runtime vscode`）→ 用 VS Code 打开项目文件夹 → 在 Agent 面板**添加本地 Agent Plugin**，目录指向 `deep-review.plugin/`。
- 调用 `/capture` 等 Skill 即可使用。

#### CodeBuddy（Tier 1 · 插件市场）

- **方式 B（推荐，无需下载）**：对话中执行 `/plugin marketplace add https://github.com/yecllsl/DeepReview.git`（或 `yecll/DeepReview`）添加远程市场 → `/plugin marketplace list` 确认市场名 → `/plugin install deep-review@<市场名>` → 必要时 `/reload-plugins`。
- **方式 A（下载解压）**：`.\install.ps1 -AgentRuntime codebuddy` → 用 CodeBuddy 打开项目文件夹 → 对话中执行 `/plugin marketplace add <项目根目录绝对路径>`（根目录含 `.codebuddy-plugin/marketplace.json`，其 `source` 指向 `./deep-review.plugin`）→ `/plugin install deep-review@deep-review-local-market` → `/reload-plugins`。

> CodeBuddy **不再生成 `.codebuddy/` 原生目录**，插件内容全部来自 `deep-review.plugin/`，不会与旧配置重复加载。

#### Trae（Tier 2 · 原生目录）

1. `.\install.ps1 -AgentRuntime trae`（会 `uv sync` 并同步生成 `.trae/`：`mcp.json` + `skills/` + 根 `AGENTS.md`）
2. 用 Trae 打开项目文件夹
3. 设置 → **MCP** → 启用「项目级 MCP」
4. 设置 → **规则** → 开启「将 AGENTS.md 包含在上下文中」（Trae 读项目根 `AGENTS.md`）

> 若 Trae 不识别 `${workspaceFolder}` 变量，改用 `.\install.ps1 -AgentRuntime trae -FixPath` 替换为绝对路径。

#### opencode（Tier 2 · 原生目录）

1. `./install.sh --agent-runtime opencode`（会 `uv sync` 并同步生成 `.opencode/`：`opencode.json` + `skills/` + `AGENTS.md`）
2. 在**项目根目录**运行 `opencode`
3. 它会自动加载 `.opencode/opencode.json`（MCP）与 `AGENTS.md`

### 开始使用

输入 `/capture`、`/batch-capture`、`/analyze`、`/review` 或 `/stats` 即可！

### 验证安装

让 LLM 执行 `/capture`（或直接问「查询我的错题」）——若能调用到 `deep-review-mcp` 工具即正常；也可在各运行时的 MCP 面板确认 `deep-review-mcp` 已连接。

### 排障

- **MCP 起不来**：确认本机 `uv` 与 `python`(3.12+) 在 PATH；方式 B（VS Code / CodeBuddy 远程安装）首启会自动 `uv sync`，方式 A 请先跑安装脚本或手动 `cd deep-review.plugin/deep-review-mcp && uv sync`
- **Trae 读不到规则**：确认已开启「将 AGENTS.md 包含在上下文中」，必要时用 `-FixPath`
- **CodeBuddy 插件未生效**：执行 `/plugin marketplace list` 确认市场已添加，再 `/reload-plugins`

### 数据位置

全部数据存于本地 `deep-review.plugin/deep-review-mcp/data/`。

---

## 可选：Web 可视化界面

如果喜欢图形化界面，可启动本地 Web 服务：

```powershell
cd deep-review.plugin/deep-review-mcp
uv run deep-review-web
```

浏览器访问 http://127.0.0.1:8001 即可使用四大页面：

| 页面 | 功能 |
|------|------|
| 概览 Dashboard | 错题总数、待复习、本周新增、学科/错误类型分布、30天趋势 |
| 错题列表 | 筛选查看、编辑保存（HTMX 局部刷新，OOB 自动更新） |
| 统计图表 | 知识点热力图、难度分布、错误类型雷达、时间趋势 |
| 复习追踪 | 待复习清单、复习日历、遗忘曲线、学科复习进度 |

> 💡 Web 服务仅绑定 `127.0.0.1`，所有数据本地存储，JS 库本地化（HTMX / Alpine.js / ECharts），**无任何外部请求**。

---

## 5 分钟快速体验

### 1. 采集第一道错题

**命令方式:**
```
/capture
```

**自然语言方式:**
```
帮我录入这道错题（附上图片路径）
```

**操作流程:**
1. 执行 `/capture` 命令
2. 输入或粘贴错题图片路径
3. AI 自动识别题目内容
4. 确认或修改识别结果
5. AI 自动分类（学科、知识点、错误类型）
6. 确认分类并保存

### 2. 分析错题原因

**命令方式:**
```
/analyze
```

**自然语言方式:**
```
分析这道错题为什么做错了
```

**操作流程:**
1. 执行 `/analyze` 命令
2. 选择要分析的错题
3. 提供你的答案和正确答案
4. AI 生成深度原因分析
5. AI 生成个性化改进方案
6. 确认方案并更新记录

### 3. 生成复习计划

**命令方式:**
```
/review
```

**自然语言方式:**
```
我该复习什么？
```

**操作流程:**
1. 执行 `/review` 命令
2. AI 自动筛选到期复习的错题
3. 按遗忘曲线智能排序
4. 生成每日复习清单
5. 展示薄弱知识点排名
6. 确认计划

### 4. 查看错题统计

**命令方式:**
```
/stats
```

**自然语言方式:**
```
看看我的错题分布情况
```

**操作流程:**
1. 执行 `/stats` 命令
2. AI 展示多维度统计：
   - 学科分布
   - 错误类型分布
   - 知识点薄弱度排名
   - 时间趋势
3. 可以导出为 JSON 或 Markdown

## 常用示例

### 示例 1: 采集数学错题

```
/capture
> 请提供错题图片路径: C:\Users\...\math_question.jpg

[AI] 多模态看图解析完成
题目内容: 若 x² - 5x + 6 = 0，则 x = ?

[AI] 结构化解析:
- 学科: 数学
- 年级: 初二
- 知识点: [一元二次方程, 因式分解]
- 难度: 中等
- 题型: 计算题

> 确认解析结果? (y/n): y

[AI] 智能分类:
- 错误类型: 方法错误
- 错误细分类别: 因式分解方法选择错误

> 确认分类? (y/n): y

[AI] ✅ 错题已保存
question_id: wq_20260615_001
保存路径: deep-review.plugin/deep-review-mcp/data/wrong_questions/wq_20260615_001.json
```

### 示例 2: 分析英语错题

```
/analyze
> 请选择要分析的错题ID: wq_20260615_001

[AI] 请提供分析信息:
- 你的答案: B
- 正确答案: D

[AI] 原因分析:
┌─────────────────────────────────────┐
│ 错误类型: 知识漏洞                     │
├─────────────────────────────────────┤
│ 根本原因:                            │
│ 未掌握定语从句的关系代词选择规则        │
│ (who vs. whom 的使用场景)            │
├─────────────────────────────────────┤
│ 详细诊断:                            │
│ 学生混淆了 who 和 whom 的使用条件，    │
│ 对介词+关系代词结构理解不准确...       │
└─────────────────────────────────────┘

> 确认分析结果? (y/n): y

[AI] 改进方案:
┌─────────────────────────────────────┐
│ 学习动作:                            │
│ 1. 复习 who/whom 的3个使用规则(30分钟)│
│ 2. 完成5道定语从句专项练习(30分钟)    │
│ 3. 整理错题本，记录介词+关系代词结构   │
├─────────────────────────────────────┤
│ 同类题方向:                          │
│ 1. 介词+关系代词结构练习              │
│ 2. whose vs. who's 区分练习          │
│ 3. 非限制性定语从句练习               │
├─────────────────────────────────────┤
│ 复习计划:                            │
│ 首次复习: 1天后                       │
│ 二次复习: 3天后                       │
└─────────────────────────────────────┘

> 确认改进方案? (y/n): y

[AI] ✅ 分析完成，已更新记录
下次复习日期: 2026-06-17
```

### 示例 3: 生成复习计划

```
/review
> 请选择学科过滤（直接回车跳过）: 数学

[AI] 复习概览:
┌─────────────────────────────────────┐
│ 📊 统计信息                          │
│ - 待复习错题: 8 道                   │
│ - 预计复习时长: 2 小时                │
│ - 预计完成天数: 2 天                 │
├─────────────────────────────────────┤
│ 🔴 薄弱知识点 (Top 5)                │
│ 1. 一元二次方程 (3次)                │
│ 2. 因式分解 (2次)                    │
│ 3. 三角形全等 (2次)                  │
│ 4. 二次函数 (1次)                    │
│ 5. 圆的性质 (1次)                    │
└─────────────────────────────────────┘

[AI] 每日复习计划:
📅 Day 1 (今天)
  - wq_20260610_001 (一元二次方程)
  - wq_20260611_002 (因式分解)
  - wq_20260612_003 (三角形全等)
  - wq_20260613_004 (二次函数)
  - wq_20260614_005 (圆的性质)
  预计时长: 75 分钟

📅 Day 2 (明天)
  - wq_20260615_006 (一元二次方程)
  - wq_20260615_007 (因式分解)
  - wq_20260615_008 (三角形全等)
  预计时长: 45 分钟

> 确认复习计划? (y/n): y

[AI] ✅ 复习计划已保存
计划ID: rp_20260615_001
保存路径: deep-review.plugin/deep-review-mcp/data/review_plans/rp_20260615_001.json
```

## 小技巧

### 1. 批量采集

使用 `/batch-capture` 命令一次录入多道错题（同学科批量只确认一次学科，混合学科每题确认；每题确认后才保存，已保存题目不受后续影响）：

```
/batch-capture
> 请提供错题图片路径（多张图片或图片文件夹）: C:\Users\...\math_questions/
```

### 2. 按学科筛选复习

```
/review
> 请选择学科过滤: 英语
```
只复习英语相关的错题

### 3. 多维度统计

```
/stats
> 请选择统计维度: subject
```
可以按 学科/错误类型/知识点/日期 统计

### 4. 数据导出

```
/export
> 请选择导出格式: markdown
> 请选择过滤条件（直接回车跳过）:
```
导出全部错题为 Markdown 格式

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| 安装脚本报错 "uv 未安装" | 安装 uv：`irm https://astral.sh/uv/install.ps1 \| iex` |
| MCP Server 不生效 | 确认启用项目级 MCP → 重启对应运行时（Trae/CodeBuddy/opencode） |
| 路径变量不替换 | 运行 `.\install.ps1 -FixPath`（或 `./install.sh --fix-path`）修复路径 |
| Skills 不生效 | 重启运行时 → 检查 `deep-review.plugin/skills/`（真相源；各平台 skills/ 由 `scripts/sync-agent-configs` 同步） |

## 下一步

- 📖 查看 [完整部署指南](DEPLOY.md)
- 📚 查看 [项目 README](README.md)
