# src/deep_review_mcp/tools/fsrs_scheduler.py
"""FSRS v6 间隔重复调度封装层

替代 storage.py 中固定的艾宾浩斯查表（REVIEW_INTERVALS=[1,3,7,14,30]），
引入 FSRS（Free Spaced Repetition Scheduler）的 DSR 记忆模型：
  - Difficulty（难度 1-10）：该错题对用户的掌握难度
  - Stability（稳定性）：记忆稳固程度，决定下次复习间隔
  - Retrievability（可提取性）：当前能回忆起的概率，目标保持率 0.9

核心优势（相对固定查表）：
  1. 间隔随用户评分动态调整，而非固定 [1,3,7,14,30]
  2. 4 档评分（Again/Hard/Good/Easy）驱动调度，区分"真会"与"蒙对"
  3. 答错（Again）触发 lapse，稳定性回退而非简单递增计数

序列化策略：
  py-fsrs 的 Card 对象自带 to_json()/from_json()，直接存入 Improvement.fsrs_state
  字段（JSON 字符串），无需手写字段映射。复习时反序列化回 Card 对象。

参考：https://github.com/open-spaced-repetition/py-fsrs
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from fsrs import Card, Rating, Scheduler

# ──────────────────────────────────────────
# 全局调度器（单例）
# ──────────────────────────────────────────
# 目标保持率 0.9（FSRS 默认）：卡片被调度到"预测回忆概率降至 90%"时复习
# maximum_interval 36500 天（约 100 年）：FSRS 默认上限，避免极端长间隔
# enable_fuzzing=True：对长间隔加微小随机扰动，避免同日复习堆积
_scheduler = Scheduler(desired_retention=0.9, maximum_interval=36500, enable_fuzzing=True)
# 标识当前调度器是否使用默认 21 参数（apply_optimized_parameters 后置 False）
# 用于 UI 展示「当前是默认参数还是个性化参数」
_is_default_scheduler = True

# 评分档位映射（供 UI 与 API 层引用）
# 1=Again 完全忘记 / 2=Hard 吃力想起 / 3=Good 顺利想起 / 4=Easy 秒懂
RATING_AGAIN = 1
RATING_HARD = 2
RATING_GOOD = 3
RATING_EASY = 4

# 评分档位中文标签（UI 展示用）
RATING_LABELS: dict[int, str] = {
    RATING_AGAIN: "忘记",
    RATING_HARD: "吃力",
    RATING_GOOD: "顺利",
    RATING_EASY: "秒懂",
}


def init_card() -> str:
    """新建错题时初始化 FSRS Card，返回 JSON 序列化字符串

    新 Card 状态为 Learning、立即到期（due=now），
    首次调用 schedule_review 时才真正开始调度。

    Returns:
        Card 的 JSON 字符串，存入 Improvement.fsrs_state
    """
    return Card().to_json()


def schedule_review(fsrs_state: str | None, rating: int) -> dict:
    """根据用户评分更新 Card 调度状态

    流程：反序列化 Card → 调用 FSRS review_card → 序列化新 Card → 回填兼容字段
    同时返回 ReviewLog 的 JSON，供 storage 层持久化到 review_logs.jsonl，
    未来积累 1000+ 记录后用 Optimizer 计算个性化 21 参数。

    Args:
        fsrs_state: 已有的 FSRS Card JSON 字符串；为 None 时初始化新卡（向后兼容老数据）
        rating: 1=Again 2=Hard 3=Good 4=Easy

    Returns:
        {
            "fsrs_state": 新 Card 的 JSON 字符串,
            "next_review_date": "YYYY-MM-DD" 下次复习日期（兼容字段）,
            "retrievability": 当前可提取性概率（0-1，用于 UI 展示记忆强度）,
            "review_log": 本次复习的 ReviewLog JSON 字符串（供持久化）,
            "reviewed_at": 本次复习的 ISO 时间戳（UTC，供日志索引）,
        }

    Raises:
        ValueError: rating 不在 1-4 范围
    """
    if rating not in (RATING_AGAIN, RATING_HARD, RATING_GOOD, RATING_EASY):
        raise ValueError(f"rating 必须为 1-4，收到: {rating}")

    # 反序列化 Card；老数据无 fsrs_state 时初始化新卡
    card = Card.from_json(fsrs_state) if fsrs_state else Card()

    # FSRS 核心调度：返回 (新 Card, ReviewLog)
    new_card, review_log = _scheduler.review_card(card, Rating(rating))

    # 计算当前可提取性（记忆强度指标，供 UI 展示）
    retrievability = _scheduler.get_card_retrievability(new_card)

    return {
        "fsrs_state": new_card.to_json(),
        # due 是带时区的 datetime，取日期部分回填兼容字段
        "next_review_date": new_card.due.strftime("%Y-%m-%d"),
        "retrievability": round(retrievability, 4),
        # ReviewLog 序列化：供 storage.append_review_log 持久化
        # 未来 Optimizer 通过 ReviewLog.from_json 反序列化计算个性化参数
        "review_log": review_log.to_json(),
        # review_log.review_datetime 是 UTC datetime，转 ISO 字符串供日志索引
        "reviewed_at": review_log.review_datetime.isoformat(),
    }


def optimize_parameters(review_log_jsons: list[str]) -> dict:
    """基于历史 ReviewLog 列表计算 FSRS 个性化 21 参数

    UI 主动触发：用户在复习页点击「分析参数」按钮时调用。
    不硬性阻止数据量不足，但返回警告标识，让 UI 提示用户结果可能不稳定。

    Args:
        review_log_jsons: ReviewLog JSON 字符串列表（来自 review_logs.jsonl）

    Returns:
        {
            "success": bool,                 # 是否成功计算
            "parameters": list[float]|None,  # 21 个优化参数（成功时）
            "desired_retention": float|None, # 优化后的目标保持率（成功时）
            "review_log_count": int,         # 参与计算的 ReviewLog 数量
            "warning": str|None,             # 数据量不足等警告（成功但有警告时）
            "error": str|None,               # 异常错误信息（失败时）
        }
    """
    result: dict[str, object] = {
        "success": False,
        "parameters": None,
        "desired_retention": None,
        "review_log_count": len(review_log_jsons) if review_log_jsons else 0,
        "warning": None,
        "error": None,
    }

    if not review_log_jsons:
        result["error"] = "暂无复习记录，无法分析参数"
        return result

    try:
        from fsrs import Optimizer
        from fsrs import ReviewLog as _RL
    except ImportError:
        result["error"] = "Optimizer 未安装，请运行: pip install \"fsrs[optimizer]\""
        return result

    # 反序列化所有 ReviewLog
    try:
        review_logs = [_RL.from_json(rl) for rl in review_log_jsons]
    except (ValueError, KeyError, TypeError) as e:
        result["error"] = f"ReviewLog 反序列化失败: {e}"
        return result

    warning: str | None = None
    # 数据量警告（不阻止计算，让用户自己决定是否应用）
    if len(review_logs) < 1000:
        warning = f"数据量不足（{len(review_logs)}/1000），结果可能不稳定，建议积累更多复习记录后再应用"

    # 调用 Optimizer 计算
    try:
        optimizer = Optimizer(review_logs)
        optimal_parameters = optimizer.compute_optimal_parameters()
        try:
            # fsrs 类型标注误标为 list[float]（见 fsrs/optimizer.py:628），
            # 实为单个 float（line 663 return optimal_retention），cast 校正外部类型
            optimal_retention = cast(
                float, optimizer.compute_optimal_retention(optimal_parameters)
            )
        except (ValueError, TypeError):
            # 计算 optimal_retention 可能失败，降级用默认 0.9
            optimal_retention = 0.9
            warning = (warning or "") + "；目标保持率计算失败，降级为 0.9"
        result["success"] = True
        result["parameters"] = list(optimal_parameters)
        result["desired_retention"] = optimal_retention
    except (ValueError, TypeError, RuntimeError) as e:
        result["error"] = f"Optimizer 计算失败: {e}"

    if warning is not None:
        result["warning"] = warning

    return result


def get_current_scheduler_info() -> dict:
    """返回当前全局调度器的参数信息（供 UI 展示「当前参数」）"""
    return {
        "desired_retention": _scheduler.desired_retention,
        "maximum_interval": _scheduler.maximum_interval,
        "enable_fuzzing": _scheduler.enable_fuzzing,
        "parameters_count": len(_scheduler.parameters),
        "is_default": _is_default_scheduler,
    }


def apply_optimized_parameters(parameters, desired_retention: float) -> bool:
    """应用优化后的参数到全局调度器（替换 _scheduler 单例）

    UI 用户点击「应用参数」确认后调用。应用后仅影响未来的复习调度，
    已存在的 Card 状态不会自动重算（py-fsrs 提供 reschedule_card 可批量重算，
    但开销大，第一期不实现）。

    Args:
        parameters: 21 个参数的元组或列表
        desired_retention: 目标保持率（0-1）

    Returns:
        True 表示应用成功
    """
    global _scheduler, _is_default_scheduler
    _scheduler = Scheduler(
        parameters=tuple(parameters),
        desired_retention=desired_retention,
        maximum_interval=36500,
        enable_fuzzing=True,
    )
    _is_default_scheduler = False
    return True


def load_persisted_parameters(params_file: Path) -> dict | None:
    """从持久化文件加载已保存的优化参数

    启动时调用：若文件存在，自动应用保存的参数到全局 _scheduler。

    Args:
        params_file: fsrs_params.json 路径

    Returns:
        {"parameters": list, "desired_retention": float} 或 None（文件不存在时）
    """
    if not params_file.exists():
        return None
    try:
        data = json.loads(params_file.read_text(encoding="utf-8"))
        if "parameters" in data and "desired_retention" in data:
            apply_optimized_parameters(data["parameters"], data["desired_retention"])
            return data
    except (json.JSONDecodeError, OSError, ValueError, TypeError, KeyError) as e:
        print(f"[fsrs_scheduler] 加载持久化参数失败，使用默认参数: {e}")
    return None


def save_persisted_parameters(params_file: Path, parameters, desired_retention: float) -> None:
    """持久化优化参数到文件（原子写入）

    应用参数后调用，确保下次启动时自动加载。

    Args:
        params_file: fsrs_params.json 路径
        parameters: 21 个参数
        desired_retention: 目标保持率
    """
    # 局部导入避免顶层依赖（与 storage.py 的原子写入策略一致）
    import os as _os
    import tempfile as _tempfile

    data = {
        "parameters": list(parameters),
        "desired_retention": float(desired_retention),
        "saved_at": datetime.now(UTC).isoformat(),
    }
    # 原子写入：临时文件 → os.replace（与 storage.save_wrong_question 一致）
    params_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = _tempfile.mkstemp(
        dir=str(params_file.parent), suffix=".tmp", prefix="fsrs_params_"
    )
    try:
        with _os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        _os.replace(tmp_path, params_file)
    except Exception:
        # 失败时清理临时文件
        if _os.path.exists(tmp_path):
            _os.unlink(tmp_path)
        raise


def get_retrievability(fsrs_state: str | None) -> float:
    """查询某错题当前的记忆可提取性（0-1）

    用于复习列表展示"这道题你现在还能记住多少"，不修改 Card 状态。

    Args:
        fsrs_state: FSRS Card JSON 字符串；None 返回 0

    Returns:
        可提取性概率（0-1），如 0.92 表示 92% 概率能回忆起
    """
    if not fsrs_state:
        return 0.0
    card = Card.from_json(fsrs_state)
    return round(_scheduler.get_card_retrievability(card), 4)
