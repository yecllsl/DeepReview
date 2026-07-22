# src/deep_review_mcp/storage.py
"""本地JSON文件存储引擎

提供错题和复习计划的CRUD操作、查询过滤、统计支持。
数据以JSON文件形式存储在本地文件系统中，按类型分目录管理。
"""
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from deep_review_mcp.models import WrongQuestion, ReviewPlan

# 艾宾浩斯遗忘曲线复习间隔（天）：第1次复习后1天，第2次3天，第3次7天，第4次14天，第5次30天
# 定义在此处避免 storage ↔ review 循环导入
REVIEW_INTERVALS = [1, 3, 7, 14, 30]


def _calculate_next_review_interval(review_count: int) -> int:
    """根据复习次数返回下次复习间隔天数（艾宾浩斯遗忘曲线）

    Args:
        review_count: 已复习次数

    Returns:
        下次复习的间隔天数
    """
    return REVIEW_INTERVALS[review_count] if review_count < len(REVIEW_INTERVALS) else 30


class Storage:
    """本地JSON文件存储引擎

    目录结构:
        base_dir/
        ├── wrong_questions/    # 错题JSON文件
        ├── analysis_reports/  # 分析报告
        └── review_plans/      # 复习计划JSON文件
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.questions_dir = base_dir / "wrong_questions"
        self.reports_dir = base_dir / "analysis_reports"
        self.plans_dir = base_dir / "review_plans"
        # 确保所有子目录存在
        for d in [self.questions_dir, self.reports_dir, self.plans_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────
    # 错题 CRUD
    # ──────────────────────────────────────────

    def save_wrong_question(self, question: WrongQuestion) -> dict:
        """保存错题到JSON文件（原子写入），返回包含question_id和文件路径的字典

        原子写入策略：先写临时文件 .tmp，再用 os.replace 原子替换，
        防止写入中途崩溃导致数据文件损坏。
        """
        fp = self.questions_dir / f"{question.question_id}.json"
        tmp_fp = fp.with_suffix(".json.tmp")
        tmp_fp.write_text(
            question.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(tmp_fp, fp)
        return {"question_id": question.question_id, "saved_path": str(fp)}

    def load_wrong_question(self, question_id: str) -> Optional[WrongQuestion]:
        """根据ID加载错题，不存在则返回None"""
        fp = self.questions_dir / f"{question_id}.json"
        if not fp.exists():
            return None
        return WrongQuestion.model_validate(json.loads(fp.read_text(encoding="utf-8")))

    def update_wrong_question(self, question: WrongQuestion) -> dict:
        """更新错题（覆盖写入），语义上等同于save"""
        return self.save_wrong_question(question)

    def patch_wrong_question(self, question_id: str, patch: dict) -> Optional[WrongQuestion]:
        """部分更新错题，只修改 patch 中包含的字段

        加载现有错题 → 合并 patch → 原子写回。
        支持嵌套字段合并（如 improvement.review_count）。

        Args:
            question_id: 错题ID
            patch: 要更新的字段字典，支持嵌套 dict 合并

        Returns:
            更新后的 WrongQuestion，若 ID 不存在返回 None
        """
        existing = self.load_wrong_question(question_id)
        if existing is None:
            return None

        # 递归合并 patch 到现有数据
        existing_data = existing.model_dump()
        merged = _deep_merge(existing_data, patch)

        updated = WrongQuestion.model_validate(merged)
        self.save_wrong_question(updated)
        return updated

    def mark_reviewed(self, question_id: str) -> Optional[WrongQuestion]:
        """标记错题为已复习

        递增 review_count，并根据艾宾浩斯遗忘曲线重算 next_review_date。

        Args:
            question_id: 错题ID

        Returns:
            更新后的 WrongQuestion，若 ID 不存在返回 None
        """
        existing = self.load_wrong_question(question_id)
        if existing is None:
            return None

        # 若没有 improvement 字段，无法标记复习
        if existing.improvement is None:
            return None

        new_count = existing.improvement.review_count + 1
        interval_days = _calculate_next_review_interval(new_count - 1)
        next_date = (datetime.now(timezone.utc) + timedelta(days=interval_days)).strftime("%Y-%m-%d")

        return self.patch_wrong_question(question_id, {
            "improvement": {
                "review_count": new_count,
                "next_review_date": next_date,
            }
        })

    def delete_wrong_question(self, question_id: str) -> bool:
        """删除错题文件，返回是否删除成功"""
        fp = self.questions_dir / f"{question_id}.json"
        if fp.exists():
            fp.unlink()
            return True
        return False

    def list_all_question_ids(self) -> list[str]:
        """列出所有错题ID（文件名不含扩展名）"""
        return [f.stem for f in self.questions_dir.glob("wq_*.json")]

    def query_wrong_questions(self, filters: dict) -> dict:
        """根据过滤条件查询错题，返回匹配列表和总数

        支持的过滤条件:
            - subject: 学科
            - knowledge_point: 知识点（模糊匹配）
            - error_type: 错误类型
            - date_range: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
        """
        questions = []
        for qid in self.list_all_question_ids():
            wq = self.load_wrong_question(qid)
            if wq and self._matches(wq, filters):
                questions.append(wq.model_dump())
        # 按创建时间倒序排列
        questions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return {"questions": questions, "total_count": len(questions)}

    def _matches(self, wq: WrongQuestion, f: dict) -> bool:
        """判断错题是否匹配过滤条件"""
        if not f:
            return True
        # 学科过滤
        if f.get("subject") and (not wq.structured or wq.structured.subject != f["subject"]):
            return False
        # 知识点过滤（模糊匹配：错题知识点列表包含指定知识点）
        if f.get("knowledge_point") and (
            not wq.structured or f["knowledge_point"] not in wq.structured.knowledge_points
        ):
            return False
        # 错误类型过滤
        if f.get("error_type") and (
            not wq.classification or wq.classification.error_type != f["error_type"]
        ):
            return False
        # 日期范围过滤
        dr = f.get("date_range")
        if dr:
            created = wq.created_at.isoformat()[:10]
            if dr.get("start") and created < dr["start"]:
                return False
            if dr.get("end") and created > dr["end"]:
                return False
        return True

    # ──────────────────────────────────────────
    # 复习计划 CRUD
    # ──────────────────────────────────────────

    def save_review_plan(self, plan: ReviewPlan) -> dict:
        """保存复习计划到JSON文件"""
        fp = self.plans_dir / f"{plan.plan_id}.json"
        fp.write_text(
            plan.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return {"plan_id": plan.plan_id, "saved_path": str(fp)}

    def load_review_plan(self, plan_id: str) -> Optional[ReviewPlan]:
        """根据ID加载复习计划，不存在则返回None"""
        fp = self.plans_dir / f"{plan_id}.json"
        if not fp.exists():
            return None
        return ReviewPlan.model_validate(json.loads(fp.read_text(encoding="utf-8")))

    # ──────────────────────────────────────────
    # 统计辅助
    # ──────────────────────────────────────────

    def get_all_questions_for_statistics(self) -> list[WrongQuestion]:
        """获取全部错题用于统计计算"""
        return [wq for qid in self.list_all_question_ids() if (wq := self.load_wrong_question(qid))]


def _deep_merge(base: dict, patch: dict) -> dict:
    """递归合并 patch 到 base 字典

    对于嵌套 dict，递归合并而非覆盖。
    对于非 dict 值，用 patch 的值覆盖 base。
    用于 patch_wrong_question 的部分更新。
    """
    result = dict(base)
    for key, value in patch.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
