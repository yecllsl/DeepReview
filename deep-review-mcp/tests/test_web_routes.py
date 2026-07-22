# tests/test_web_routes.py
"""测试 Web 路由 — API 响应状态码和内容"""
from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from deep_review_mcp.models import (
    Analysis,
    Classification,
    Improvement,
    StructuredQuestion,
    WrongQuestion,
)
from deep_review_mcp.storage import Storage
from deep_review_mcp.web.app import create_app
from deep_review_mcp.web import services


@pytest.fixture
def temp_data(tmp_path, monkeypatch):
    """创建临时 storage 和测试数据，注入 services"""
    storage = Storage(base_dir=tmp_path)
    monkeypatch.setattr(services, "_get_storage", lambda: storage)

    # 创建测试错题
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for i in range(5):
        wq = WrongQuestion(
            question_id=f"wq_test_{i:03d}",
            created_at=datetime.now(timezone.utc) - timedelta(days=i),
            raw_text=f"测试题目 {i} - 数学函数题",
            structured=StructuredQuestion(
                subject="数学" if i % 2 == 0 else "物理",
                grade_level="高中",
                knowledge_points=["函数基础", "二次函数"],
                difficulty="中等" if i < 3 else "困难",
                question_type="选择题",
            ),
            classification=Classification(
                error_type="知识漏洞" if i % 2 == 0 else "粗心失误",
                error_category="概念不清",
            ),
            analysis=Analysis(
                root_cause=f"测试根因 {i}",
                cause_category="知识漏洞",
                diagnosis_detail=f"详细诊断 {i}",
            ),
            improvement=Improvement(
                plan=f"改进方案 {i}",
                similar_topics=["相似题1"],
                review_count=i,
                next_review_date=today,
            ),
        )
        storage.save_wrong_question(wq)
    return storage


@pytest_asyncio.fixture
async def client(temp_data):
    """创建测试客户端"""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ──────────────────────────────────────────
# 根路由
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_root_returns_html(client):
    """根路由应返回 base.html"""
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "DeepReview" in resp.text


# ──────────────────────────────────────────
# Dashboard 路由
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_dashboard_partial(client):
    """Dashboard 片段应返回 HTML"""
    resp = await client.get("/partials/dashboard")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")

@pytest.mark.asyncio
async def test_dashboard_summary_api(client):
    """Dashboard summary API 应返回 JSON"""
    resp = await client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert data["total"] == 5
    assert "subject_distribution" in data
    assert "trends" in data


# ──────────────────────────────────────────
# Questions 路由
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_question_list_partial(client):
    """错题列表应返回 HTML"""
    resp = await client.get("/partials/questions")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")

@pytest.mark.asyncio
async def test_question_list_with_filter(client):
    """学科筛选应生效"""
    resp = await client.get("/partials/questions", params={"subject": "数学"})
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_question_detail_partial(client):
    """单题详情应返回 HTML"""
    resp = await client.get("/partials/questions/wq_test_000")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")

@pytest.mark.asyncio
async def test_question_detail_not_found(client):
    """不存在的错题应返回 404"""
    resp = await client.get("/partials/questions/nonexistent")
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_question_edit_partial(client):
    """编辑表单应返回 HTML"""
    resp = await client.get("/partials/questions/wq_test_000/edit")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")

@pytest.mark.asyncio
async def test_update_question_api(client):
    """PUT 保存应更新数据，并返回详情 + OOB 左侧列表片段"""
    resp = await client.put(
        "/api/questions/wq_test_000",
        data={"raw_text": "修改后的题目", "subject": "物理", "error_type": "方法错误"},
        headers={"HX-Current-URL": "http://test/partials/questions"},
    )
    assert resp.status_code == 200
    text = resp.text
    # 主响应应包含更新后的详情
    assert "修改后的题目" in text
    # OOB 片段应刷新左侧列表容器
    assert 'id="question-list-container" hx-swap-oob="true"' in text
    assert "question-card" in text

@pytest.mark.asyncio
async def test_update_question_not_found(client):
    """更新不存在的错题应返回 404"""
    resp = await client.put(
        "/api/questions/nonexistent",
        data={"raw_text": "x"},
    )
    assert resp.status_code == 404


# ──────────────────────────────────────────
# Stats 路由
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_stats_partial(client):
    """统计页应返回 HTML"""
    resp = await client.get("/partials/stats")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_stats_api(client):
    """统计 API 应返回 JSON"""
    resp = await client.get("/api/stats", params={"group_by": "subject"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data

@pytest.mark.asyncio
async def test_multi_dim_stats_api(client):
    """多维统计 API 应返回 JSON"""
    resp = await client.get("/api/stats/multi-dim")
    assert resp.status_code == 200
    data = resp.json()
    assert "knowledge_heatmap" in data
    assert "difficulty_distribution" in data
    assert "error_type_radar" in data
    assert "trend_data" in data


# ──────────────────────────────────────────
# Review 路由
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_review_partial(client):
    """复习页应返回 HTML"""
    resp = await client.get("/partials/review")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_upcoming_reviews_api(client):
    """待复习 API 应返回 JSON"""
    resp = await client.get("/api/review/upcoming")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data

@pytest.mark.asyncio
async def test_mark_review_done(client):
    """标记复习应返回 200"""
    resp = await client.post("/api/review/wq_test_000/done")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_mark_review_not_found(client):
    """标记不存在的错题应返回 404"""
    resp = await client.post("/api/review/nonexistent/done")
    assert resp.status_code == 404


# ──────────────────────────────────────────
# 空数据测试
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_empty_dashboard(tmp_path, monkeypatch):
    """无数据时 Dashboard 应正常返回"""
    storage = Storage(base_dir=tmp_path)
    monkeypatch.setattr(services, "_get_storage", lambda: storage)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/partials/dashboard")
        assert resp.status_code == 200
        assert "还没有错题记录" in resp.text

@pytest.mark.asyncio
async def test_empty_question_list(tmp_path, monkeypatch):
    """无数据时列表应显示空状态"""
    storage = Storage(base_dir=tmp_path)
    monkeypatch.setattr(services, "_get_storage", lambda: storage)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/partials/questions")
        assert resp.status_code == 200
        assert "没有匹配的错题" in resp.text
