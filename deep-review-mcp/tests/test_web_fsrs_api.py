# tests/test_web_fsrs_api.py
"""FSRS 参数优化 UI 路由测试

验证 review.py 中新增的 3 个 FSRS 路由：
  - GET  /api/fsrs/status   获取优化状态
  - POST /api/fsrs/optimize 触发优化计算
  - POST /api/fsrs/apply    应用优化参数

以及 /partials/review 页面包含 FSRS 优化面板。
"""
from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from deep_review_mcp.models import (
    Classification,
    Improvement,
    StructuredQuestion,
    WrongQuestion,
)
from deep_review_mcp.storage import Storage
from deep_review_mcp.web.app import create_app
from deep_review_mcp.web import services


@pytest.fixture
def restore_scheduler():
    """保存并恢复全局 _scheduler 状态（apply 测试会修改全局调度器）"""
    from deep_review_mcp.tools import fsrs_scheduler
    original_scheduler = fsrs_scheduler._scheduler
    original_is_default = fsrs_scheduler._is_default_scheduler
    yield
    fsrs_scheduler._scheduler = original_scheduler
    fsrs_scheduler._is_default_scheduler = original_is_default


@pytest.fixture
def temp_data_with_logs(tmp_path, monkeypatch):
    """创建临时 storage，含若干已复习错题（产生 ReviewLog）"""
    storage = Storage(base_dir=tmp_path)
    monkeypatch.setattr(services, "_get_storage", lambda: storage)

    # 创建 3 道错题并标记复习，生成 ReviewLog
    for i in range(3):
        wq = WrongQuestion(
            question_id=f"wq_fsrs_api_{i:03d}",
            created_at=datetime.now(timezone.utc) - timedelta(days=i),
            structured=StructuredQuestion(
                subject="数学", grade_level="高中",
                knowledge_points=["函数"], difficulty="中等", question_type="计算题",
                question_content=f"FSRS API 测试题 {i}",
            ),
            classification=Classification(error_type="知识漏洞", error_category="概念不清"),
            improvement=Improvement(
                plan=f"复习 {i}", similar_topics=["相似题"],
                review_count=0, next_review_date=None, fsrs_state=None,
            ),
        )
        storage.save_wrong_question(wq)
        # 标记复习，触发 ReviewLog 写入
        storage.mark_reviewed(f"wq_fsrs_api_{i:03d}", rating=3)
    return storage


@pytest_asyncio.fixture
async def client(temp_data_with_logs):
    """创建测试客户端"""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ──────────────────────────────────────────
# GET /api/fsrs/status
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_fsrs_status_returns_scheduler_info(client):
    """status 接口应返回当前调度器信息"""
    resp = await client.get("/api/fsrs/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "current_scheduler" in data
    assert "review_log_count" in data
    assert "progress" in data
    assert "has_persisted_params" in data


@pytest.mark.asyncio
async def test_fsrs_status_scheduler_info_fields(client):
    """调度器信息含 is_default/desired_retention/parameters_count"""
    resp = await client.get("/api/fsrs/status")
    scheduler = resp.json()["current_scheduler"]
    assert "is_default" in scheduler
    assert "desired_retention" in scheduler
    assert "parameters_count" in scheduler
    assert "maximum_interval" in scheduler
    assert "enable_fuzzing" in scheduler


@pytest.mark.asyncio
async def test_fsrs_status_reflects_review_log_count(client, temp_data_with_logs):
    """review_log_count 应反映已积累的 ReviewLog 数量"""
    resp = await client.get("/api/fsrs/status")
    data = resp.json()
    # temp_data_with_logs 中标记了 3 次复习，应有 3 条 ReviewLog
    assert data["review_log_count"] == 3
    # 进度 = 3/1000
    assert data["progress"] == round(3 / 1000, 4)


@pytest.mark.asyncio
async def test_fsrs_status_no_persisted_params_by_default(client):
    """默认情况下 has_persisted_params 为 False（未应用过参数）"""
    resp = await client.get("/api/fsrs/status")
    assert resp.json()["has_persisted_params"] is False


# ──────────────────────────────────────────
# POST /api/fsrs/optimize
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_fsrs_optimize_returns_result_structure(client):
    """optimize 接口应返回完整结果结构"""
    resp = await client.post("/api/fsrs/optimize")
    assert resp.status_code == 200
    data = resp.json()
    # 必需字段
    assert "success" in data
    assert "parameters" in data
    assert "desired_retention" in data
    assert "review_log_count" in data
    assert "warning" in data
    assert "error" in data


@pytest.mark.asyncio
async def test_fsrs_optimize_with_logs_returns_warning(client):
    """有少量 ReviewLog 时应返回警告（数据量不足 1000）"""
    resp = await client.post("/api/fsrs/optimize")
    data = resp.json()
    # 3 条 ReviewLog，应触发数据量不足警告
    assert data["review_log_count"] == 3
    assert data["warning"] is not None
    assert "1000" in data["warning"]


@pytest.mark.asyncio
async def test_fsrs_optimize_no_logs_returns_error(tmp_path, monkeypatch):
    """无 ReviewLog 时 optimize 应返回 error"""
    # 用空 storage
    empty_storage = Storage(base_dir=tmp_path)
    monkeypatch.setattr(services, "_get_storage", lambda: empty_storage)

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/fsrs/optimize")

    data = resp.json()
    assert data["success"] is False
    assert data["error"] is not None
    assert data["review_log_count"] == 0


# ──────────────────────────────────────────
# POST /api/fsrs/apply
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_fsrs_apply_validates_parameters_count(client, restore_scheduler):
    """apply 接口应接受 21 个参数"""
    # 构造 21 个参数（用默认参数的副本）
    from deep_review_mcp.tools.fsrs_scheduler import _scheduler
    params = list(_scheduler.parameters)
    assert len(params) == 21

    resp = await client.post(
        "/api/fsrs/apply",
        json={"parameters": params, "desired_retention": 0.85},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_fsrs_apply_persists_to_file(client, temp_data_with_logs, restore_scheduler):
    """apply 后应持久化参数到 fsrs_params.json"""
    from deep_review_mcp.tools.fsrs_scheduler import _scheduler
    params = list(_scheduler.parameters)

    resp = await client.post(
        "/api/fsrs/apply",
        json={"parameters": params, "desired_retention": 0.88},
    )
    assert resp.status_code == 200

    # 验证文件已创建
    assert temp_data_with_logs.fsrs_params_file.exists()
    import json
    data = json.loads(temp_data_with_logs.fsrs_params_file.read_text(encoding="utf-8"))
    assert data["desired_retention"] == 0.88
    assert len(data["parameters"]) == 21


@pytest.mark.asyncio
async def test_fsrs_apply_rejects_invalid_retention(client):
    """desired_retention 超出范围应被 Pydantic 拒绝（422）"""
    resp = await client.post(
        "/api/fsrs/apply",
        json={"parameters": [0.1] * 21, "desired_retention": 1.5},  # > 1.0
    )
    assert resp.status_code == 422  # Pydantic 校验失败


@pytest.mark.asyncio
async def test_fsrs_apply_rejects_missing_parameters(client):
    """缺少 parameters 字段应被 Pydantic 拒绝（422）"""
    resp = await client.post(
        "/api/fsrs/apply",
        json={"desired_retention": 0.85},
    )
    assert resp.status_code == 422


# ──────────────────────────────────────────
# /partials/review 页面包含 FSRS 优化面板
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_review_partial_contains_fsrs_panel(client):
    """复习页应包含「FSRS 参数优化」面板"""
    resp = await client.get("/partials/review")
    assert resp.status_code == 200
    assert "FSRS 参数优化" in resp.text
    # 应有「分析参数」按钮
    assert "分析参数" in resp.text
    # 应有进度条展示 ReviewLog 积累
    assert "1000" in resp.text


@pytest.mark.asyncio
async def test_review_partial_shows_review_log_progress(client):
    """复习页应展示 ReviewLog 积累进度（3/1000）"""
    resp = await client.get("/partials/review")
    # 应包含 "3/1000" 进度展示
    assert "3/1000" in resp.text


@pytest.mark.asyncio
async def test_review_partial_contains_optimize_js(client):
    """复习页应包含 FSRS 优化交互 JS 函数"""
    resp = await client.get("/partials/review")
    assert "runFsrsOptimization" in resp.text
    assert "applyFsrsParameters" in resp.text
    assert "renderOptimizationResult" in resp.text
