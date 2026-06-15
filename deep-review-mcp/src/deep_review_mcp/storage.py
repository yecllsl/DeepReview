# src/deep_review_mcp/storage.py
"""本地JSON文件存储引擎

提供错题和复习计划的CRUD操作、查询过滤、统计支持。
数据以JSON文件形式存储在本地文件系统中，按类型分目录管理。
"""
import json
from pathlib import Path
from typing import Optional

from deep_review_mcp.models import WrongQuestion, ReviewPlan


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
        """保存错题到JSON文件，返回包含question_id和文件路径的字典"""
        fp = self.questions_dir / f"{question.question_id}.json"
        fp.write_text(
            question.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
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
