# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
