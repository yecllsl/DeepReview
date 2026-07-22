# 错题数据 Web 可视化方案 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 DeepReview 项目实现错题数据本地 Web 可视化应用，含概览、错题列表与详情（可编辑保存）、统计图表、复习追踪四页。

**Architecture:** 独立 web 模块 `deep_review_mcp.web`，FastAPI 提供 API 和 Jinja2 片段，HTMX 做局部交换，Alpine.js 管表单状态，ECharts 渲染图表。复用现有 storage/statistics/review 代码，Web 层是薄编排。

**Tech Stack:** Python 3.12+ / FastAPI / Uvicorn / Jinja2 / HTMX / Alpine.js / ECharts / pytest / Playwright

## Global Constraints

- Python 3.12+，包管理用 uv
- 数据仅本地存储，JS 库本地化不走 CDN，FastAPI 绑定 127.0.0.1
- 复用现有 storage.py / statistics.py / review.py / models.py，不复制数据访问逻辑
- 错题 JSON 路径：`deep-review-mcp/data/wrong_questions/wq_*.json`
- 学科列表：语文/数学/英语/物理/化学/生物/政治/历史/地理
- 错误类型：知识漏洞/粗心失误/方法错误/审题失误
- 难度：基础/中等/困难
- 复习间隔（天）：[1, 3, 7, 14, 30]
- 所有代码注释用中文

## 文件结构

```
deep-review-mcp/src/deep_review_mcp/
├── storage.py                 [修改] 原子写 + patch_wrong_question + mark_reviewed
├── web/                       [新建]
│   ├── __init__.py            [新建]
│   ├── app.py                 [新建] FastAPI 工厂 + main 入口
│   ├── services.py            [新建] 编排 storage/statistics/review
│   ├── schemas.py             [新建] Web 请求模型
│   ├── routes/
│   │   ├── __init__.py       [新建]
│   │   ├── dashboard.py      [新建] 概览页
│   │   ├── questions.py      [新建] 列表/详情/编辑
│   │   ├── stats.py          [新建] 统计图表
│   │   └── review.py         [新建] 复习追踪
│   ├── templates/
│   │   ├── base.html         [新建] 单页外壳
│   │   ├── partials/
│   │   │   ├── dashboard.html
│   │   │   ├── question_list.html
│   │   │   ├── question_detail.html
│   │   │   ├── question_edit.html
│   │   │   ├── stats.html
│   │   │   └── review.html
│   │   └── errors.html
│   └── static/
│       ├── htmx.min.js       [下载]
│       ├── alpine.min.js     [下载]
│       ├── echarts.min.js    [下载]
│       └── app.css           [新建]

deep-review-mcp/pyproject.toml  [修改] 依赖 + deep-review-web 入口
deep-review-mcp/tests/
├── test_storage_patch.py       [新建]
├── test_web_services.py        [新建]
├── test_web_routes.py          [新建]
└── test_e2e_visualization.py   [新建] Playwright E2E
```

---

### Task 1: storage.py 增强

**Files:**
- Modify: `deep-review-mcp/src/deep_review_mcp/storage.py`
- Test: `deep-review-mcp/tests/test_storage_patch.py`

**Interfaces:**
- Produces: `Storage.patch_wrong_question(id, patch: dict) -> WrongQuestion` — 加载现有，合并 patch，原子写入
- Produces: `Storage.mark_reviewed(id) -> WrongQuestion` — review_count+=1，重算 next_review_date
- Produces: 原子写入（临时文件+rename）应用于 `save_wrong_question`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_storage_patch.py
import json
from pathlib import Path
from datetime import datetime
from deep_review_mcp.storage import Storage
from deep_review_mcp.models import WrongQuestion

def _make_storage(tmp_path):
    return Storage(base_dir=tmp_path)

def _make_question(qid="wq_test_001"):
    return WrongQuestion(
        question_id=qid, created_at=datetime.now(),
        raw_text="测试题目", structured=None, classification=None,
        analysis=None, improvement=None,
    )

def test_patch_wrong_question_updates_field(tmp_path):
    storage = _make_storage(tmp_path)
    wq = _make_question()
    storage.save_wrong_question(wq)
    updated = storage.patch_wrong_question("wq_test_001", {"raw_text": "修改后题目"})
    assert updated.raw_text == "修改后题目"
    loaded = storage.load_wrong_question("wq_test_001")
    assert loaded.raw_text == "修改后题目"

def test_patch_wrong_question_not_found(tmp_path):
    storage = _make_storage(tmp_path)
    result = storage.patch_wrong_question("nonexistent", {"raw_text": "x"})
    assert result is None

def test_mark_reviewed_increments_count(tmp_path):
    storage = _make_storage(tmp_path)
    wq = _make_question()
    # 需要 improvement 字段才能 mark_reviewed
    from deep_review_mcp.models import Improvement
    wq.improvement = Improvement(plan="测试", similar_topics=[], review_count=0, next_review_date="2026-07-22")
    storage.save_wrong_question(wq)
    updated = storage.mark_reviewed("wq_test_001")
    assert updated.improvement.review_count == 1
    assert updated.improvement.next_review_date > "2026-07-22"

def test_atomic_write_no_corruption(tmp_path):
    storage = _make_storage(tmp_path)
    wq = _make_question()
    storage.save_wrong_question(wq)
    # 确认文件写入后可正常读取
    loaded = storage.load_wrong_question("wq_test_001")
    assert loaded is not None
    assert loaded.question_id == "wq_test_001"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd deep-review-mcp && uv run pytest tests/test_storage_patch.py -v`
Expected: FAIL（方法不存在）

- [ ] **Step 3: 实现**

在 `storage.py` 中添加：
- `save_wrong_question` 改为原子写（写 `.tmp` 文件 → `os.replace` 重命名）
- `patch_wrong_question(id, patch)` — 加载、用 `model_copy(update=...)` 合并、原子写入
- `mark_reviewed(id)` — 调 `patch_wrong_question` 更新 `review_count` 和 `next_review_date`，复用 `review._calculate_next_review_date`

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git add src/deep_review_mcp/storage.py tests/test_storage_patch.py
git commit -m "feat: add atomic write, patch and mark_reviewed to storage"
```

---

### Task 2: pyproject.toml 依赖与 web 包骨架

**Files:**
- Modify: `deep-review-mcp/pyproject.toml`
- Create: `web/__init__.py`, `web/app.py`（最小骨架）

**Interfaces:**
- Produces: `deep_review_mcp.web.app:create_app() -> FastAPI` — FastAPI 应用工厂
- Produces: `deep_review_mcp.web.app:main()` — CLI 入口，启动 uvicorn

- [ ] **Step 1: 更新 pyproject.toml**

dependencies 新增：`fastapi`, `uvicorn`, `jinja2`, `python-multipart`
dev 新增：`httpx`, `playwright`
scripts 新增：`deep-review-web = "deep_review_mcp.web.app:main"`

- [ ] **Step 2: 创建 web 包骨架**

`web/__init__.py` 空。`web/app.py` — `create_app()` 返回 FastAPI 实例，`main()` 启动 uvicorn 绑定 127.0.0.1:8001。

- [ ] **Step 3: 安装新依赖**

Run: `cd deep-review-mcp && uv pip install -e ".[dev]"`

- [ ] **Step 4: 提交**

---

### Task 3: 下载静态 JS 库 + app.css

**Files:**
- Create: `web/static/htmx.min.js`, `web/static/alpine.min.js`, `web/static/echarts.min.js`, `web/static/app.css`

- [ ] **Step 1: 下载 JS 库到 static/**

用 `Invoke-WebRequest` 下载 htmx 2.0.x、alpine 3.x、echarts 5.x 的压缩版到 `web/static/`

- [ ] **Step 2: 编写 app.css**

简洁的 CSS 样式：顶栏导航、卡片网格、左右分栏布局、表单样式、配色（学科色标）

- [ ] **Step 3: 提交**

---

### Task 4: Web 服务层 + schemas

**Files:**
- Create: `web/services.py`, `web/schemas.py`
- Test: `tests/test_web_services.py`

**Interfaces:**
- Produces: `services.get_dashboard_summary() -> dict` — KPI + 分布 + 趋势
- Produces: `services.get_multi_dim_stats() -> dict` — 多维度统计（热力图、雷达、难度分布）
- Produces: `services.get_upcoming_reviews() -> list[dict]` — 待复习列表
- Produces: `services.mark_question_reviewed(id) -> dict` — 标记已复习
- Produces: `services.update_question(id, data: dict) -> WrongQuestion` — 编辑保存

- [ ] **Step 1: 写失败测试**（测试 services 各方法返回结构）
- [ ] **Step 2: 运行确认失败**
- [ ] **Step 3: 实现 services.py + schemas.py**
- [ ] **Step 4: 运行确认通过**
- [ ] **Step 5: 提交**

---

### Task 5: FastAPI app 完整搭建 + base.html

**Files:**
- Modify: `web/app.py` — 挂载静态文件、注册路由、Jinja2 配置
- Create: `web/templates/base.html` — 单页外壳
- Create: `web/routes/__init__.py`

- [ ] **Step 1: 完善 app.py**

`create_app()` 配置 Jinja2 模板目录、挂载 `/static`、注册 4 个路由模块的 router

- [ ] **Step 2: 编写 base.html**

含 `<head>` 引入本地 JS/CSS、顶栏导航 4 Tab（Dashboard/错题/统计/复习）、`#content` 容器、HTMX 首屏加载逻辑

- [ ] **Step 3: 提交**

---

### Task 6: Dashboard 路由 + 模板

**Files:**
- Create: `web/routes/dashboard.py`, `web/templates/partials/dashboard.html`
- Test: `tests/test_web_routes.py`（Dashboard 部分）

- [ ] **Step 1: 写失败测试** — GET `/partials/dashboard` 返回 200 含 HTML；GET `/api/dashboard/summary` 返回 JSON 含 total/kpis/distributions/trends
- [ ] **Step 2: 运行确认失败**
- [ ] **Step 3: 实现 dashboard.py 路由 + dashboard.html 模板**

模板含 4 KPI 卡片 + ECharts 容器（学科环形/错误类型横条/趋势折线）+ 待复习清单。JS 用 `htmx:afterSwap` 触发 ECharts init，数据从 `/api/dashboard/summary` fetch

- [ ] **Step 4: 运行确认通过**
- [ ] **Step 5: 提交**

---

### Task 7: 错题列表 + 详情（只读）

**Files:**
- Create: `web/routes/questions.py`, `web/templates/partials/question_list.html`, `web/templates/partials/question_detail.html`
- Test: `tests/test_web_routes.py`（Questions 部分）

- [ ] **Step 1: 写失败测试** — GET `/partials/questions?subject=数学` 返回筛选后列表；GET `/partials/questions/{id}` 返回详情 HTML
- [ ] **Step 2: 运行确认失败**
- [ ] **Step 3: 实现 questions.py 路由 + 模板**

列表模板：筛选栏（学科/错误类型/知识点下拉 + 搜索框）+ 错题卡片列表 + 分页。详情模板：左右分栏右侧，展示所有字段只读 + 「编辑」按钮

- [ ] **Step 4: 运行确认通过**
- [ ] **Step 5: 提交**

---

### Task 8: 错题编辑保存

**Files:**
- Modify: `web/routes/questions.py` — 增加编辑表单路由 + PUT API
- Create: `web/templates/partials/question_edit.html`
- Test: `tests/test_web_routes.py`（编辑部分）

- [ ] **Step 1: 写失败测试** — GET `/partials/questions/{id}/edit` 返回表单；PUT `/api/questions/{id}` 保存后返回 200 且数据更新
- [ ] **Step 2: 运行确认失败**
- [ ] **Step 3: 实现编辑表单 + PUT 路由**

编辑表单：raw_text 文本域、structured 各字段下拉、classification 下拉、analysis 文本域、improvement 文本域 + 同类题 + 复习日期。Alpine 管表单状态，`hx-put` 提交后返回只读详情片段

- [ ] **Step 4: 运行确认通过**
- [ ] **Step 5: 提交**

---

### Task 9: 统计图表页

**Files:**
- Create: `web/routes/stats.py`, `web/templates/partials/stats.html`
- Test: `tests/test_web_routes.py`（Stats 部分）

- [ ] **Step 1: 写失败测试** — GET `/partials/stats` 返回 200；GET `/api/stats?group_by=subject` 返回分组数据
- [ ] **Step 2: 运行确认失败**
- [ ] **Step 3: 实现 stats.py + stats.html**

模板含维度切换器 + 5 个 ECharts 图表容器（主图、热力图、难度堆叠、雷达、趋势）。JS 在 `afterSwap` 时从 `/api/stats` 拉数据渲染

- [ ] **Step 4: 运行确认通过**
- [ ] **Step 5: 提交**

---

### Task 10: 复习追踪页

**Files:**
- Create: `web/routes/review.py`, `web/templates/partials/review.html`
- Test: `tests/test_web_routes.py`（Review 部分）

- [ ] **Step 1: 写失败测试** — GET `/partials/review` 返回 200；POST `/api/review/{id}/done` 返回 200 且 review_count 递增
- [ ] **Step 2: 运行确认失败**
- [ ] **Step 3: 实现 review.py + review.html**

模板含今日待复习卡片 + 标记按钮、复习日历、遗忘曲线、学科完成率进度条、逾期清单

- [ ] **Step 4: 运行确认通过**
- [ ] **Step 5: 提交**

---

### Task 11: 后端测试完善

**Files:**
- Test: `tests/test_web_routes.py`（完善所有路由的边界测试）

- [ ] **Step 1: 补全边界测试** — 不存在的 ID 返回 404、空数据空状态、筛选组合、PUT 校验失败 422
- [ ] **Step 2: 运行全部后端测试**

Run: `cd deep-review-mcp && uv run pytest tests/ -v --tb=short`

- [ ] **Step 3: 提交**

---

### Task 12: Playwright E2E 测试

**Files:**
- Create: `tests/test_e2e_visualization.py`

- [ ] **Step 1: 安装 Playwright**

Run: `cd deep-review-mcp && uv run playwright install chromium`

- [ ] **Step 2: 编写 E2E 测试**

测试场景：
1. 启动 web app → 访问 localhost:8001 → Dashboard 加载 → 图表渲染
2. 点击「错题」Tab → 列表加载 → 筛选学科 → 列表刷新
3. 点击错题卡片 → 详情展示 → 点击编辑 → 修改字段 → 保存 → 确认局部刷新
4. 点击「统计」Tab → 图表渲染 → 切换维度
5. 点击「复习」Tab → 待复习列表 → 标记已复习 → 确认更新

- [ ] **Step 3: 运行 E2E 测试**

Run: `cd deep-review-mcp && uv run pytest tests/test_e2e_visualization.py -v`

- [ ] **Step 4: 提交**
