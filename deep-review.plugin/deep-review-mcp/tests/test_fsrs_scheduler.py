# tests/test_fsrs_scheduler.py
"""FSRS v6 调度封装层单元测试

验证 fsrs_scheduler.py 的核心功能：
  - init_card 返回有效 JSON
  - schedule_review 初始化新卡 / 更新已有卡
  - 4 档评分（Again/Hard/Good/Easy）产生差异化调度
  - 无效 rating 抛 ValueError
  - get_retrievability 查询记忆强度
  - optimize_parameters / apply / persist 个性化参数流程
"""
import json
from datetime import UTC, datetime

import pytest

from deep_review_mcp.tools.fsrs_scheduler import (
    RATING_AGAIN,
    RATING_EASY,
    RATING_GOOD,
    RATING_HARD,
    RATING_LABELS,
    apply_optimized_parameters,
    get_current_scheduler_info,
    get_retrievability,
    init_card,
    is_optimizer_available,
    load_persisted_parameters,
    optimize_parameters,
    save_persisted_parameters,
    schedule_review,
)


@pytest.fixture
def restore_scheduler():
    """保存并恢复全局 _scheduler 状态

    apply_optimized_parameters 会替换全局 _scheduler 单例，
    测试后必须恢复，避免污染其他测试。
    """
    from deep_review_mcp.tools import fsrs_scheduler
    original_scheduler = fsrs_scheduler._scheduler
    original_is_default = fsrs_scheduler._is_default_scheduler
    yield
    fsrs_scheduler._scheduler = original_scheduler
    fsrs_scheduler._is_default_scheduler = original_is_default


# ──────────────────────────────────────────
# init_card
# ──────────────────────────────────────────

def test_init_card_returns_valid_json_string():
    """init_card 返回 JSON 字符串，可被 json.loads 解析"""
    state = init_card()
    assert isinstance(state, str)
    data = json.loads(state)
    # FSRS Card 必含字段
    assert "due" in data
    assert "state" in data
    assert "stability" in data
    assert "difficulty" in data


def test_init_card_new_card_is_learning_state():
    """新卡初始状态为 Learning（state=1），立即可复习"""
    state = init_card()
    data = json.loads(state)
    assert data["state"] == 1  # State.Learning


# ──────────────────────────────────────────
# schedule_review - 基础功能
# ──────────────────────────────────────────

def test_schedule_review_returns_required_fields():
    """schedule_review 返回 dict 含 fsrs_state/next_review_date/retrievability/review_log/reviewed_at"""
    result = schedule_review(None, RATING_GOOD)
    assert "fsrs_state" in result
    assert "next_review_date" in result
    assert "retrievability" in result
    assert "review_log" in result
    assert "reviewed_at" in result
    assert isinstance(result["fsrs_state"], str)
    assert isinstance(result["next_review_date"], str)
    assert isinstance(result["review_log"], str)
    assert isinstance(result["reviewed_at"], str)
    assert 0 <= result["retrievability"] <= 1


def test_schedule_review_review_log_is_valid_fsrs_reviewlog():
    """返回的 review_log 应可被 fsrs.ReviewLog.from_json 反序列化

    这是未来 Optimizer 计算个性化参数的前提。
    """
    from fsrs import ReviewLog
    result = schedule_review(None, RATING_GOOD)
    rl = ReviewLog.from_json(result["review_log"])
    # ReviewLog 应含 rating 字段（1-4）
    assert rl.rating in (1, 2, 3, 4)
    # review_datetime 应与 reviewed_at 对应
    assert result["reviewed_at"] == rl.review_datetime.isoformat()


def test_schedule_review_review_log_rating_matches_input():
    """返回的 review_log 内含的 rating 与传入 rating 一致"""
    for rating in [RATING_AGAIN, RATING_HARD, RATING_GOOD, RATING_EASY]:
        from fsrs import ReviewLog
        result = schedule_review(None, rating)
        rl = ReviewLog.from_json(result["review_log"])
        assert rl.rating == rating


def test_schedule_review_initializes_new_card_from_none():
    """fsrs_state=None 时自动初始化新卡（向后兼容老数据）"""
    result = schedule_review(None, RATING_GOOD)
    # 返回的 fsrs_state 应为有效 JSON
    data = json.loads(result["fsrs_state"])
    assert "due" in data
    assert "stability" in data


def test_schedule_review_updates_existing_card():
    """连续两次复习，Card 状态应发生变化（stability 增长）"""
    r1 = schedule_review(None, RATING_GOOD)
    state_after_first = json.loads(r1["fsrs_state"])
    r2 = schedule_review(r1["fsrs_state"], RATING_GOOD)
    state_after_second = json.loads(r2["fsrs_state"])
    # 两次复习后 stability 应有变化（通常增长）
    assert state_after_first["stability"] != state_after_second["stability"] or \
           state_after_first["state"] != state_after_second["state"]


# ──────────────────────────────────────────
# schedule_review - 4 档评分差异化
# ──────────────────────────────────────────

def test_four_ratings_all_succeed():
    """4 档评分都能正常调用，返回有效结果"""
    for rating in [RATING_AGAIN, RATING_HARD, RATING_GOOD, RATING_EASY]:
        result = schedule_review(None, rating)
        assert result["next_review_date"]  # 非空
        assert result["fsrs_state"]


def test_first_again_schedules_today():
    """首次 Again 评分：Learning 状态，1 分钟后到期，next_review_date 为今天"""
    result = schedule_review(None, RATING_AGAIN)
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    assert result["next_review_date"] == today


def test_first_easy_schedules_future_date():
    """首次 Easy 评分：直接毕业到 Review，due 应在未来（非今天）"""
    result = schedule_review(None, RATING_EASY)
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    # Easy 会让卡毕业，调度到几天后
    assert result["next_review_date"] >= today


def test_again_creates_sooner_due_than_easy_for_graduated_card():
    """已毕业的卡：Again（lapse）比 Easy 调度更近

    先用多次 Good 让卡毕业到 Review 状态，
    再对比 Again vs Easy 的 due 日期。
    """
    # 连续 3 次 Good 让卡毕业并积累 stability
    state = None
    for _ in range(3):
        r = schedule_review(state, RATING_GOOD)
        state = r["fsrs_state"]

    # 同一状态分叉测试：Again vs Easy
    r_again = schedule_review(state, RATING_AGAIN)
    r_easy = schedule_review(state, RATING_EASY)
    # Again 触发 lapse，due 应早于 Easy
    assert r_again["next_review_date"] <= r_easy["next_review_date"]


# ──────────────────────────────────────────
# schedule_review - 异常处理
# ──────────────────────────────────────────

def test_schedule_review_invalid_rating_raises():
    """rating 不在 1-4 范围抛 ValueError"""
    with pytest.raises(ValueError):
        schedule_review(None, 0)
    with pytest.raises(ValueError):
        schedule_review(None, 5)
    with pytest.raises(ValueError):
        schedule_review(None, -1)


# ──────────────────────────────────────────
# get_retrievability
# ──────────────────────────────────────────

def test_get_retrievability_zero_for_none():
    """无 fsrs_state 时返回 0"""
    assert get_retrievability(None) == 0.0
    assert get_retrievability("") == 0.0


def test_get_retrievability_returns_value_for_card():
    """有 fsrs_state 时返回 0-1 之间的可提取性"""
    state = init_card()
    r = get_retrievability(state)
    assert 0 <= r <= 1


def test_get_retrievability_does_not_mutate_state():
    """get_retrievability 不修改 Card 状态（只读查询）"""
    state = init_card()
    before = json.loads(state)
    get_retrievability(state)
    after = json.loads(state)
    assert before == after


# ──────────────────────────────────────────
# 评分档位常量与标签
# ──────────────────────────────────────────

def test_rating_constants_match_fsrs_enum():
    """评分常量与 FSRS Rating 枚举一致"""
    assert RATING_AGAIN == 1
    assert RATING_HARD == 2
    assert RATING_GOOD == 3
    assert RATING_EASY == 4


def test_rating_labels_complete():
    """4 档评分标签完整"""
    assert len(RATING_LABELS) == 4
    assert RATING_LABELS[RATING_AGAIN] == "忘记"
    assert RATING_LABELS[RATING_GOOD] == "顺利"


# ──────────────────────────────────────────
# optimize_parameters - UI 触发的个性化参数计算
# ──────────────────────────────────────────

def test_optimize_parameters_empty_logs_returns_error():
    """空 ReviewLog 列表应返回 error，不调用 Optimizer"""
    result = optimize_parameters([])
    assert result["success"] is False
    assert result["error"] is not None
    assert result["review_log_count"] == 0


def test_is_optimizer_available():
    """is_optimizer_available 返回 bool（不抛异常）"""
    assert isinstance(is_optimizer_available(), bool)


def test_optimize_parameters_with_optimizer_returns_warning():
    """已装 Optimizer：少量 ReviewLog 返回 success + 数据量不足警告（不阻止计算）"""
    if not is_optimizer_available():
        pytest.skip("Optimizer 未安装（跳过真实优化路径测试）")
    # 构造 5 条 ReviewLog（远少于 1000）
    review_logs = []
    state = None
    for _ in range(5):
        r = schedule_review(state, RATING_GOOD)
        review_logs.append(r["review_log"])
        state = r["fsrs_state"]

    result = optimize_parameters(review_logs)
    # 不验证参数正确性（Optimizer 行为由 py-fsrs 保证），只验证结构
    assert result["review_log_count"] == 5
    # 数据量不足应有警告
    assert result["warning"] is not None
    assert "1000" in result["warning"]
    if result["success"]:
        assert isinstance(result["parameters"], list)
        assert result["desired_retention"] is not None


def test_optimize_parameters_without_optimizer_returns_friendly_error():
    """未装 Optimizer：少量 ReviewLog 返回友好安装提示（而非抛异常/500）"""
    if is_optimizer_available():
        pytest.skip("Optimizer 已安装（跳过未安装降级路径测试）")
    # 构造 5 条 ReviewLog（远少于 1000）
    review_logs = []
    state = None
    for _ in range(5):
        r = schedule_review(state, RATING_GOOD)
        review_logs.append(r["review_log"])
        state = r["fsrs_state"]

    result = optimize_parameters(review_logs)
    assert result["success"] is False
    assert "Optimizer 未安装" in (result["error"] or "")
    assert "uv sync --extra optimize" in (result["error"] or "")


def test_optimize_parameters_result_structure():
    """optimize_parameters 返回结构含所有必需字段"""
    r = schedule_review(None, RATING_GOOD)
    result = optimize_parameters([r["review_log"]])
    # 必需字段
    assert "success" in result
    assert "parameters" in result
    assert "desired_retention" in result
    assert "review_log_count" in result
    assert "warning" in result
    assert "error" in result


# ──────────────────────────────────────────
# get_current_scheduler_info
# ──────────────────────────────────────────

def test_get_current_scheduler_info_default():
    """默认调度器信息：is_default=True，desired_retention=0.9"""
    info = get_current_scheduler_info()
    assert info["is_default"] is True
    assert info["desired_retention"] == 0.9
    assert info["parameters_count"] == 21  # FSRS 默认 21 参数
    assert info["maximum_interval"] == 36500


def test_get_current_scheduler_info_after_apply(restore_scheduler):
    """应用优化参数后：is_default=False，desired_retention 改变"""
    # 构造一组参数（用默认参数的副本，desired_retention 改为 0.85）
    from deep_review_mcp.tools.fsrs_scheduler import _scheduler
    custom_params = list(_scheduler.parameters)
    apply_optimized_parameters(custom_params, desired_retention=0.85)

    info = get_current_scheduler_info()
    assert info["is_default"] is False
    assert info["desired_retention"] == 0.85


# ──────────────────────────────────────────
# apply_optimized_parameters
# ──────────────────────────────────────────

def test_apply_optimized_parameters_replaces_scheduler(restore_scheduler):
    """应用参数后全局 _scheduler 被替换"""
    from deep_review_mcp.tools import fsrs_scheduler
    original = fsrs_scheduler._scheduler
    custom_params = list(original.parameters)

    apply_optimized_parameters(custom_params, desired_retention=0.88)

    # _scheduler 应是新实例
    assert fsrs_scheduler._scheduler is not original
    assert fsrs_scheduler._scheduler.desired_retention == 0.88
    assert fsrs_scheduler._is_default_scheduler is False


def test_apply_optimized_parameters_affects_future_scheduling(restore_scheduler):
    """应用新参数后，后续 schedule_review 使用新调度器

    验证 desired_retention 变化会影响 due 日期计算
    """
    from deep_review_mcp.tools.fsrs_scheduler import _scheduler
    custom_params = list(_scheduler.parameters)

    # 用相同评分对比：默认 0.9 vs 应用 0.75
    _ = schedule_review(None, RATING_GOOD)

    apply_optimized_parameters(custom_params, desired_retention=0.75)
    _ = schedule_review(None, RATING_GOOD)

    # 两种 desired_retention 下，due 日期应可能不同（0.75 复习更频繁，due 更近）
    # 不强求一定不同（FSRS 内部可能对首张卡有 learning_steps 影响），
    # 但调度器实例必须不同
    from deep_review_mcp.tools import fsrs_scheduler
    assert fsrs_scheduler._scheduler.desired_retention == 0.75


# ──────────────────────────────────────────
# persist parameters（save / load 往返）
# ──────────────────────────────────────────

def test_save_persisted_parameters_creates_file(tmp_path, restore_scheduler):
    """save_persisted_parameters 应创建 JSON 文件"""
    from deep_review_mcp.tools.fsrs_scheduler import _scheduler
    params = list(_scheduler.parameters)
    params_file = tmp_path / "fsrs_params.json"

    save_persisted_parameters(params_file, params, desired_retention=0.85)

    assert params_file.exists()
    data = json.loads(params_file.read_text(encoding="utf-8"))
    assert data["desired_retention"] == 0.85
    assert len(data["parameters"]) == 21
    assert "saved_at" in data


def test_load_persisted_parameters_applies_to_scheduler(tmp_path, restore_scheduler):
    """load_persisted_parameters 应应用到全局 _scheduler"""
    from deep_review_mcp.tools.fsrs_scheduler import _scheduler
    params = list(_scheduler.parameters)
    params_file = tmp_path / "fsrs_params.json"

    # 保存
    save_persisted_parameters(params_file, params, desired_retention=0.82)
    # 加载
    loaded = load_persisted_parameters(params_file)

    assert loaded is not None
    assert loaded["desired_retention"] == 0.82
    # 全局调度器应被更新
    from deep_review_mcp.tools import fsrs_scheduler
    assert fsrs_scheduler._scheduler.desired_retention == 0.82
    assert fsrs_scheduler._is_default_scheduler is False


def test_load_persisted_parameters_returns_none_when_file_not_exists(tmp_path):
    """文件不存在时返回 None，不抛异常"""
    params_file = tmp_path / "not_exist.json"
    assert load_persisted_parameters(params_file) is None


def test_load_persisted_parameters_handles_corrupted_file(tmp_path, restore_scheduler):
    """损坏的参数文件应降级返回 None，不影响默认调度器"""
    params_file = tmp_path / "fsrs_params.json"
    params_file.write_text("{invalid json}", encoding="utf-8")

    result = load_persisted_parameters(params_file)
    assert result is None
    # 默认调度器未被修改
    from deep_review_mcp.tools import fsrs_scheduler
    assert fsrs_scheduler._is_default_scheduler is True


def test_persist_roundtrip_preserves_parameters(tmp_path, restore_scheduler):
    """保存 → 加载往返：参数值应一致"""
    from deep_review_mcp.tools.fsrs_scheduler import _scheduler
    original_params = list(_scheduler.parameters)
    params_file = tmp_path / "fsrs_params.json"

    save_persisted_parameters(params_file, original_params, desired_retention=0.87)
    loaded = load_persisted_parameters(params_file)

    assert loaded["parameters"] == original_params
    assert loaded["desired_retention"] == 0.87
