# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.1] - 2026-09-29

### Added

- **Git URL 远程安装（方式 B）**：QUICKSTART / README / DEPLOY 补充 VS Code 与 CodeBuddy 直接把 GitHub 仓库（`https://github.com/yecllsl/DeepReview.git`）作为插件市场来源的安装步骤、排障与验收说明，无需下载 Release 压缩包
- **`插件安装验证.md`**：记录 VS Code / CodeBuddy 两条通道在本机的实际安装落盘位置与验证结论（带日期的验证快照，不随版本回填）

### Changed

- **CodeBuddy 改走 Tier 1 插件通道**：CodeBuddy 不再生成 `.codebuddy/` 原生目录，改用根目录 `.codebuddy-plugin/marketplace.json` 本地市场安装；`scripts/sync-agent-configs` 不再生成 `.codebuddy/`，`generate-platform-configs.py` 不再生成 `runtime/codebuddy.json`，`build-release` 不再打包 `.codebuddy/` 原生目录；`pre-commit` / `check-config-drift.sh` 不再将 `.codebuddy/` 视为生成目录
- **安装脚本按通道分流**：`install.ps1` / `install.sh` 新增 `vscode` 运行时；`vscode` / `codebuddy` 走 Tier 1 插件安装指引，`trae` / `opencode` 走 Tier 2 原生同步
- **MCP 启动去掉 `--no-sync`**：`deep-review.plugin/mcp.json` 与 `.mcp.json` 恢复 `uv run` 默认同步行为，插件首启自动构建虚拟环境（Git URL 远程安装场景必需）
- **文档层级标注与基线对齐**：README 架构图/技术栈/「支持的 Harness」表、`deep-review.plugin/AGENTS.md` 架构图（及其生成的根 `AGENTS.md`、`.opencode/AGENTS.md`）、DEPLOY「手动 E2E 验收」小节与验收表、`build-release.{ps1,sh}` 与 `install.{ps1,sh}` 提示文案，统一将 CodeBuddy 表述为 Tier 1 市场通道，不再写作 Tier 2 / 单向同步目标；pre-commit 钩子提示移除 `.codebuddy/`

### Removed

- **`.codebuddy/` 原生配置目录**：`AGENTS.md`、`mcp.json`、5 个 Skill 与 `runtime/codebuddy.json` 全部删除，仅保留 `.codebuddy/settings.json` 与运行时自有数据（memory 等），不再参与同步与漂移校验

## [0.6.0] - 2026-09-28

### Added

- **CodeBuddy 本地插件市场通道**：新建根级 `.codebuddy-plugin/marketplace.json`（市场 `deep-review-local-market`，单插件）；`deep-review.plugin/.codebuddy-plugin/plugin.json` 补 `mcpServers` 指向可移植 `.mcp.json`（`${CODEBUDDY_PLUGIN_ROOT}` + `uv` 入口，替换原硬编码绝对路径版）；build-release 白名单增补市场通道三文件（mkdir + 显式复制 + 包内校验三件套）
- **`scripts/check_version.py` 版本一致性校验**：以 `pyproject.toml` 为真相源，覆盖文档发行包名/构建示例、插件/市场/AAIF 声明清单与 `__init__.py` 硬编码 `__version__`（vocabcraft 同源漂移教训），并接入 CI config-drift job
- **README「支持的 Harness」与各客户端安装方式对照表**；**DEPLOY 手动 E2E 验收方法**（Tier 1 Agents Window / Tier 2 CodeBuddy 本地市场；实测状态如实标「未实测」）

### Changed

- **两层 Harness 策略写入真相源与文档**：Tier 1 — Agent Plugins 1.0 插件标准（代表 VS Code / Copilot，插件形态分发，规范不携带 AGENTS.md）；Tier 2 — 免费额度 / 开箱即用（Trae、CodeBuddy、OpenCode 原生目录 + install 脚本）；明确不支持 WorkBuddy / Hermes / Goose
- **术语清理**：「AAIF 真相源 / AAIF 配置层 / AAIF 插件包」等混写统一为「配置唯一真相源」，打包标准统一表述为 Agent Plugins 1.0（AAIF 作为基金会/单项标准的表述保留）
- **`fsrs[optimizer]` 改为可选依赖**：默认安装只含 `fsrs`（纯 FSRS v6 调度，无重依赖）；个性化 21 参数优化（Optimizer，依赖 numpy/pandas/torch 约 570MB）改为 `uv sync --extra optimize` 按需安装。此前默认背上 torch 是过度设计——复习记录积累 512+ 条前 Optimizer 会空转返回默认参数，retention 优化子功能因 `review_duration` 未记录而必然降级
- **`/api/fsrs/status` 新增 `optimizer_installed` 字段**（`fsrs_scheduler.is_optimizer_available` 检测 torch），优化面板据此提示按需安装
- **优化面板增强**：未安装优化组件时显示黄色提示条（含安装命令）；点击「分析参数」返回友好错误（修复了 py-fsrs 占位 Optimizer 实例化抛 ImportError 未被捕获导致 500 的问题）
- **测试适配可选依赖**：优化路径测试在未装 torch 时验证降级提示、已装时验证真实警告，CI（`uv sync --extra dev`）与本地均可通过

### Removed

- **Goose 支持**：`.goose/` 目录、`runtime/goose.json`、`generate-goose-config.py`、sync/install/build-release 的 Goose 分支、pre-commit 与 check-config-drift 校验项、文档全部引用（历史条目保留）

## [0.5.0] - 2026-08-17

### Added

- **Agent Plugins 1.0（Vercel 等厂商中立打包规范，与 AAIF 无隶属关系）规范支持**：新建 `deep-review.plugin/` 自包含插件包——`plugin.json`（`agent-plugins.org/schemas/1.0.0/plugin.schema.json` manifest）+ `mcp.json`（`${PLUGIN_ROOT}` 内联 MCP 启动配置），可整体分发、向标准注册中心发布（`agents publish deep-review.plugin`）
- **根 `package.json`**：`main` 指向 `deep-review.plugin/tools.json`（AAIF 声明入口），`scripts` 内置 `generate-declarations` / `sync-configs` / `check-drift` / `publish`
- **`scripts/check-config-drift.sh`**：CI 工作区漂移检查，与 pre-commit 钩子构成配置同步双防线
- **CI config-drift job**：`.github/workflows/test.yml` 新增，校验四平台生成目录与 `deep-review.plugin/` 真相源一致

### Changed

- **配置层目录重构**：`.agents/` → `deep-review.plugin/`（AAIF 唯一真相源迁移），`deep-review-mcp/` 内联进插件包为 `deep-review.plugin/deep-review-mcp/`；同步脚本、平台生成脚本、pre-commit、build-release、install、CI、文档路径全部更新
- **AAIF 声明格式规范化**：重写 `generate-aaif-declarations.py`，`tools.json` 用顶层 `name/version/description/tools`（去 `package` 包装与 `generated_by` 元数据）、`triggers.json` 用 `type: command/conversation` + `pattern` + `handler`、`workflows.json` 用 `name/description/steps:[{action,description}]`，并重新生成三个声明文件
- **pre-commit 升级为内容一致性检查**：逐字节比对四平台生成目录（skills/、AGENTS.md，含 Trae 根 AGENTS.md）与 `deep-review.plugin/` 源，同时拦截「直改生成目录」与「改源忘同步」两类违规
- **版本号统一 0.5.0**：`pyproject.toml` / `__init__.py` / web 入口 / `plugin.json` / `package.json` / install 脚本 / build-release / 文档全部对齐

### Removed

- **删除 `.agents/` 目录**：内容（`AGENTS.md`、`skills/`、`runtime/`）全部迁入 `deep-review.plugin/`，AAIF 真相源单一化

### 说明

- 服务层业务逻辑、5 个 Skill 内容、业务规则不变，纯结构重构
- 数据目录同步更新为 `deep-review.plugin/deep-review-mcp/data/...`，`.gitignore` 路径已调整

## [0.4.0] - 2026-08-13

### Removed

- **删除本地 PaddleOCR 实现**：`ocr_recognize` MCP 工具、`tools/ocr_recognize.py`、`prompts/structure_parse.py`、`pyproject.toml` 的 `[ocr]` 可选依赖（paddleocr/paddlepaddle）、安装脚本中的 OCR 安装步骤
- **移除 `WrongQuestion.raw_text` 字段**：题目文本改由 `StructuredQuestion.question_content`（及 `options`）承载；web 展示、编辑、搜索、analyze/export 全链路迁移

### Changed

- **图片导入改为宿主 LLM 多模态解析**：`/capture`、`/batch-capture` 不再调用 OCR，由宿主 LLM 直接读取图片并按结构化提示解析，解析提示内联进采集 Skill
- **MCP 工具数量**：11 个 → 10 个（业务工具 7 → 6）
- **版本号统一**：`pyproject.toml` / `__init__.py` / web 入口 / install 脚本 / 文档全部对齐 0.4.0

### 说明

- 服务层 `StructuredQuestion.question_content` 带默认值，兼容旧数据加载；图片 `image_path` 字段保留
- 配置同步：AAIF 声明（`tools.json` / `workflows.json`）已重生成，四平台生成目录已同步

## [0.3.0] - 2026-08-13

### Added

- **AAIF 规范支持**：建立 `.agents/` 作为配置层唯一真相源（`AGENTS.md` 规则、`skills/` 技能、`runtime/` 平台运行时配置、`tools.json` / `triggers.json` / `workflows.json` 三个 AAIF 标准声明文件，由脚本自动生成）
- **多 Agent harness 支持**：Trae / CodeBuddy / opencode / Goose 四个项目级 harness（`scripts/sync-agent-configs` 单向同步生成各自配置目录），WorkBuddy / Hermes 两个个人级 harness（安装脚本写入 `~/.workbuddy`、`~/.hermes`）
- **脚本工具链**：`generate-aaif-declarations.py`（FastMCP 自省生成 AAIF 声明）、`generate-platform-configs.py`（生成 4 平台 runtime JSON）、`generate-goose-config.py`（goose.json → `.goose/config.yaml`，支持 `--no-resolve-dir` 发布版相对路径）、`sync-agent-configs.ps1/.sh`（单向同步）
- **pre-commit 钩子**：拦截「直接修改生成目录而未同步 .agents/」的违规提交（`.codebuddy/memory/**` 例外）
- **安装脚本增强**：`install.ps1` / `install.sh` 新增 `-AgentRuntime`（trae/codebuddy/opencode/goose/all/workbuddy/hermes）与 `-FixPath`（`${workspaceFolder}` → 绝对路径）参数；个人级 harness 采用符号链接、失败降级复制
- **发布包增强**：打包清单加入 `.agents/`、`.goose/`、`.opencode/`、`.codebuddy/`、`.workbuddy/`、`.hermes/`、`scripts/` 同步工具链与根 `AGENTS.md`（带点前缀目录名）

### Changed

- **配置同步机制**：`.trae/`、`.opencode/`、`.codebuddy/`、`.goose/` 改为 `scripts/sync-agent-configs` 的生成产物，**禁止直接编辑**；唯一真相源为 `.agents/`
- **4 个既有 rules 合并**进 `.agents/AGENTS.md`（classification / analysis / data-safety / interaction），避免多份规则漂移；`.trae/rules/` 已删除，规则唯一来源即 `.agents/AGENTS.md`
- **MCP 启动参数**：统一改用 `uv run --no-sync`（复用安装时 `uv sync` 的环境，避免每次启动解析依赖）
- **版本号统一**：`pyproject.toml` / `__init__.py` / web 入口 / install 脚本 / 文档全部对齐 0.3.0

### 说明

- 服务层（`deep-review-mcp/`）业务代码与 11 个 MCP 工具注册保持不变，向后兼容
- 配置同步约束由 `scripts/pre-commit` 机械防线保障（详见 `AGENTS.md`「流程规则 > 配置同步」）

## [0.2.1] - 2026-07-25

### Changed

- **死代码清理**（基于 ponytail-audit 全仓库扫描，13 项接受 / 1 项拒绝并修正原评审误判）
  - 删除未使用的 `ReviewPlan`、`ReviewScheduleItem`、`QueryFilters`、`StatisticsResult` 模型
  - 删除 `Storage.save_review_plan` / `load_review_plan` 方法（FSRS 已替代旧复习计划系统）
  - 删除 `_calculate_next_review_interval` / `_calculate_next_review_date` 兼容别名（仅测试覆盖，业务无调用）；保留 `REVIEW_INTERVALS` 常量供遗忘曲线 UI 展示
  - 删除 `_validate_classification`（仅测试覆盖，`classify_question` 业务函数不调用）
  - 删除 `find_closest_knowledge_point` / `validate_subject`（无任何引用）
  - 删除整个 `web/schemas.py`（`QuestionUpdateRequest` / `ReviewDoneResponse` 均无路由引用）
  - 删除 `web/templates/errors.html`（无路由引用）
- **简化重复代码**
  - `export.py` 复用 `storage.base_dir`，删除重复的 `_DEFAULT_DATA_DIR` 定义
  - `storage.py` 方法内 3 处 `import json as _json` 改用顶部已导入的 `json`
  - 删除 `storage.py` 未使用的 `datetime` / `timezone` / `timedelta` 导入
  - 删除 `web/routes/questions.py` 未使用的 `Jinja2Templates` 导入
- **修正版本号不一致**：`__init__.py` 的 `__version__` 从 0.1.0 更新为 0.2.1

### Fixed

- 补充 `_json_default` 的 docstring 说明：明确 `model_dump()` 返回的 dict 中 `created_at` 仍为 datetime 对象，`json.dumps` 需要此 handler 序列化（原 ponytail-audit 误判为死代码，复核后拒绝删除）

### Testing

- 143 项测试全部通过（0.2.0 基线 149 项 − 6 项被删死测试 = 143 项，完全吻合）
- MCP 工具注册验证：11 个 tool 全部可导入
- Web 路由响应验证：10 个关键路由 TestClient 实测全部 2xx
- FSRS 端到端工作流验证：4 档评分 + ReviewLog 持久化 + 查询
- 数据安全规则检查：127.0.0.1 绑定、本地 PaddleOCR、本地存储、无 PII 字段

## [0.2.0] - 2026-07-25

### Added

- **FSRS v6 间隔重复调度系统**：替代固定艾宾浩斯查表（[1,3,7,14,30]），引入基于 DSR 记忆模型的动态调度
  - 4 档评分交互（忘记/吃力/顺利/秒懂），复习时间随评分动态调整
  - 目标保持率默认 0.9（FSRS 标准）
  - 老数据（无 fsrs_state）首次复习自动初始化，向后兼容
- **ReviewLog 持久化**（`review_logs.jsonl`）：每次复习记录追加一行，作为 Optimizer 个性化参数的数据源
- **FSRS 参数优化 UI 面板**（复习页底部）：
  - 展示当前调度器状态（默认/个性化）+ ReviewLog 积累进度（X/1000）
  - 「分析参数」按钮触发 Optimizer 计算个性化 21 参数
  - 「应用参数」按钮确认后替换全局调度器并持久化到 `fsrs_params.json`
  - 数据量不足时显示警告（不阻止计算），让用户自主决定
  - 应用后自动刷新页面，下次启动自动加载持久化参数
- **3 个 FSRS API 路由**：
  - `GET /api/fsrs/status` — 获取优化状态
  - `POST /api/fsrs/optimize` — 触发优化计算
  - `POST /api/fsrs/apply` — 应用优化参数（Pydantic 校验 desired_retention 0.5-1.0）
- `fsrs[optimizer]` 依赖：拉入 numpy/torch/pandas，支持 UI 触发的参数优化计算
- Improvement 模型新增 `fsrs_state` 字段：存储 FSRS Card 序列化状态（JSON）
- `tools/fsrs_scheduler.py` 封装层：`init_card` / `schedule_review` / `get_retrievability` / `optimize_parameters` / `apply_optimized_parameters` / `load_persisted_parameters` / `save_persisted_parameters`

### Changed

- `storage.mark_reviewed` 新增 `rating` 参数（默认 3=Good），调用 FSRS 调度替代固定查表
- `routes/review.py mark_review_done` 新增 `rating: int = Form(3)` 表单参数
- 复习页「完成」按钮替换为 4 档评分按钮（忘记/吃力/顺利/秒懂），颜色由红→蓝递增
- `web/app.py create_app` 启动时自动加载持久化 FSRS 参数，加载失败降级默认参数

### Testing

- 新增 149 项测试（0.1.0 基线 80 项 → 0.2.0 共 149 项），覆盖：
  - FSRS 调度封装层单元测试（17 项）
  - FSRS 与 Storage 集成测试（13 项）
  - ReviewLog 持久化测试（13 项）
  - FSRS API 路由测试（14 项）
  - 参数优化/应用/持久化往返测试（11 项）
  - E2E 可视化测试（8 项，含 Playwright）
  - Web 路由/服务/存储基线测试（73 项，全部回归通过）

### Dependencies

- `fsrs[optimizer]>=6.0.0`（新增，含 numpy/torch/pandas 约 130MB）
- `fsrs>=6.0.0` → `fsrs[optimizer]>=6.0.0`（升级依赖声明）

## [0.1.0] - 2026-06-16

### Added

- K12 错题收集与智能分析 MCP Server 初始版本
- OCR 识别（PaddleOCR，可选依赖）
- 错题结构化、分类、分析、改进建议
- 本地 JSON 文件存储引擎（原子写入）
- Web 可视化界面（FastAPI + HTMX + Alpine.js + ECharts）
- 复习追踪（固定艾宾浩斯间隔 [1,3,7,14,30]）
- 统计分析（学科/知识点/错误类型多维统计）
- 数据导出（JSON/Markdown）
- GitHub CI/CD + Release 工作流
