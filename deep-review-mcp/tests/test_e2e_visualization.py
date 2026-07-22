# tests/test_e2e_visualization.py
"""Playwright E2E 测试 — 错题可视化 Web 应用

测试关键用户流程：页面加载、Tab 切换、图表渲染、列表筛选、编辑保存、复习追踪。
"""
import asyncio
import socket
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from playwright.async_api import Page, async_playwright

# 尝试导入 uvicorn，如不可用则跳过 E2E 测试
try:
    import uvicorn
    HAS_UVICORN = True
except ImportError:
    HAS_UVICORN = False

from deep_review_mcp.models import (
    Analysis,
    Classification,
    Improvement,
    StructuredQuestion,
    WrongQuestion,
)
from deep_review_mcp.storage import Storage
from deep_review_mcp.web import services


def _find_free_port() -> int:
    """查找可用端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _seed_test_data(storage: Storage):
    """填充测试错题数据"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subjects = ["数学", "物理", "化学", "英语", "语文"]
    error_types = ["知识漏洞", "粗心失误", "方法错误", "审题失误"]

    for i in range(10):
        wq = WrongQuestion(
            question_id=f"wq_e2e_{i:03d}",
            created_at=datetime.now(timezone.utc) - timedelta(days=i),
            raw_text=f"E2E测试题目 {i} - {subjects[i % 5]}相关内容",
            structured=StructuredQuestion(
                subject=subjects[i % 5],
                grade_level="高中",
                knowledge_points=["函数基础", "二次函数"] if i % 2 == 0 else ["力学", "电学"],
                difficulty="中等" if i % 3 != 0 else "困难",
                question_type="选择题" if i % 2 == 0 else "填空题",
            ),
            classification=Classification(
                error_type=error_types[i % 4],
                error_category="概念不清",
            ),
            analysis=Analysis(
                root_cause=f"测试根因 {i}",
                cause_category=error_types[i % 4],
                diagnosis_detail=f"详细诊断说明 {i}",
            ),
            improvement=Improvement(
                plan=f"改进方案 {i}",
                similar_topics=["相似题A", "相似题B"],
                review_count=i % 3,
                next_review_date=today,
            ),
        )
        storage.save_wrong_question(wq)


@pytest.fixture(scope="module")
def server_url(tmp_path_factory):
    """启动 FastAPI 服务器并返回 URL"""
    if not HAS_UVICORN:
        pytest.skip("uvicorn 不可用")

    # 创建临时数据目录
    data_dir = tmp_path_factory.mktemp("e2e_data")
    storage = Storage(base_dir=data_dir)
    _seed_test_data(storage)

    # monkeypatch services 的 storage
    original_get = services._get_storage
    services._get_storage = lambda: storage

    # 创建 FastAPI app
    from deep_review_mcp.web.app import create_app
    app = create_app()

    port = _find_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)

    # 在后台线程启动服务器
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # 等待服务器就绪
    url = f"http://127.0.0.1:{port}"
    for _ in range(30):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                break
        except (ConnectionRefusedError, socket.timeout):
            time.sleep(0.2)

    yield url

    # 清理
    server.should_exit = True
    thread.join(timeout=5)
    services._get_storage = original_get


@pytest_asyncio.fixture
async def page(server_url):
    """创建 Playwright 页面"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        pg = await context.new_page()
        yield pg
        await context.close()
        await browser.close()


# ──────────────────────────────────────────
# E2E 测试用例
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_page_loads(page: Page, server_url: str):
    """页面应正确加载"""
    await page.goto(server_url)
    await page.wait_for_selector(".navbar-brand")
    assert "DeepReview" in await page.text_content(".navbar-brand")


@pytest.mark.asyncio
async def test_dashboard_loads(page: Page, server_url: str):
    """Dashboard 应加载并显示 KPI 卡片"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)
    # 应有 4 个 KPI 卡片
    cards = await page.query_selector_all(".kpi-card")
    assert len(cards) == 4
    # 第一个卡片应显示"错题总数"
    assert "错题总数" in await cards[0].text_content()


@pytest.mark.asyncio
async def test_tab_switching(page: Page, server_url: str):
    """Tab 切换应加载对应内容"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    # 切换到"错题"Tab
    await page.click('button[data-tab="questions"]')
    await page.wait_for_selector(".split-layout", timeout=10000)

    # 切换到"统计"Tab
    await page.click('button[data-tab="stats"]')
    await page.wait_for_selector(".dimension-switcher", timeout=10000)

    # 切换到"复习"Tab
    await page.click('button[data-tab="review"]')
    await page.wait_for_selector(".review-calendar", timeout=10000)

    # 切回 Dashboard
    await page.click('button[data-tab="dashboard"]')
    await page.wait_for_selector(".kpi-grid", timeout=10000)


@pytest.mark.asyncio
async def test_question_list_and_detail(page: Page, server_url: str):
    """错题列表应展示，点击应显示详情"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    # 切换到错题 Tab
    await page.click('button[data-tab="questions"]')
    await page.wait_for_selector(".question-list", timeout=10000)

    # 应有错题卡片
    cards = await page.query_selector_all(".question-card")
    assert len(cards) > 0

    # 点击第一张卡片
    await cards[0].click()
    # 详情区应加载
    await page.wait_for_selector("#detail-panel .detail-section", timeout=10000)
    detail_text = await page.text_content("#detail-panel")
    assert "原题内容" in detail_text or "题目编号" in detail_text


@pytest.mark.asyncio
async def test_question_edit_and_save(page: Page, server_url: str):
    """编辑错题并保存"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    # 切换到错题 Tab
    await page.click('button[data-tab="questions"]')
    await page.wait_for_selector(".question-list", timeout=10000)

    # 点击第一张卡片，并记录保存前列表中的学科标签
    cards = await page.query_selector_all(".question-card")
    first_card_subject_before = await cards[0].text_content()
    await cards[0].click()
    await page.wait_for_selector("#detail-panel .detail-section", timeout=10000)

    # 点击编辑按钮
    edit_btn = await page.query_selector('button:has-text("编辑")')
    if edit_btn:
        await edit_btn.click()
        # 应显示编辑表单
        await page.wait_for_selector("#edit-form", timeout=10000)
        # 修改原题内容
        textarea = await page.query_selector('textarea[name="raw_text"]')
        if textarea:
            await textarea.fill("E2E修改后的题目内容")

        # 修改分类字段
        await page.locator('#edit-form select[name="subject"]').select_option('物理')
        await page.locator('#edit-form select[name="difficulty"]').select_option('困难')
        await page.locator('#edit-form select[name="error_type"]').select_option('方法错误')

        # 点击保存
        save_btn = await page.query_selector('button:has-text("保存")')
        if save_btn:
            await save_btn.click()
            # 等待返回详情
            await page.wait_for_selector(".detail-section", timeout=10000)

            # 验证分类字段已保存
            detail_text = await page.text_content("#detail-panel")
            assert "物理" in detail_text
            assert "困难" in detail_text
            assert "方法错误" in detail_text

            # 验证左侧列表也自动刷新（第一张卡片的学科标签应变为物理）
            first_card_after = await page.query_selector(".question-card")
            first_card_subject_after = await first_card_after.text_content()
            assert "物理" in first_card_subject_after
            assert first_card_subject_before != first_card_subject_after


@pytest.mark.asyncio
async def test_stats_page_charts(page: Page, server_url: str):
    """统计页应显示图表容器"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    # 切换到统计 Tab
    await page.click('button[data-tab="stats"]')
    await page.wait_for_selector(".chart-grid", timeout=10000)

    # 应有多个图表容器
    charts = await page.query_selector_all(".chart-container")
    assert len(charts) >= 3


@pytest.mark.asyncio
async def test_review_page(page: Page, server_url: str):
    """复习页应显示待复习列表和日历"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    # 切换到复习 Tab
    await page.click('button[data-tab="review"]')
    await page.wait_for_selector(".review-calendar", timeout=10000)

    # 应有复习日历
    calendar_days = await page.query_selector_all(".calendar-day")
    assert len(calendar_days) > 0

    # 应有待复习项或空状态
    review_items = await page.query_selector_all(".review-item")
    empty_state = await page.query_selector(".review-list .empty-state")
    assert len(review_items) > 0 or empty_state is not None


@pytest.mark.asyncio
async def test_mark_review_done(page: Page, server_url: str):
    """标记复习完成"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    # 切换到复习 Tab
    await page.click('button[data-tab="review"]')
    await page.wait_for_selector(".review-calendar", timeout=10000)

    # 查找"完成"按钮
    done_btn = await page.query_selector('button:has-text("完成")')
    if done_btn:
        await done_btn.click()
        # 等待页面刷新
        await page.wait_for_selector(".review-calendar", timeout=10000)
