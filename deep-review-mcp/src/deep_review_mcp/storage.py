# src/deep_review_mcp/storage.py
"""本地JSON文件存储引擎

提供错题和复习计划的CRUD操作、查询过滤、统计支持。
数据以JSON文件形式存储在本地文件系统中，按类型分目录管理。
"""
import json
import os
from pathlib import Path
from typing import Optional

from deep_review_mcp.models import WrongQuestion

# DEPRECATED: 复习调度已改用 FSRS v6（见 tools/fsrs_scheduler.py）。
# 此列表仅保留用于 review.html 遗忘曲线 UI 展示，不再参与实际调度计算。
# 定义在此处避免 storage ↔ review 循环导入
REVIEW_INTERVALS = [1, 3, 7, 14, 30]


class Storage:
    """本地JSON文件存储引擎

    目录结构:
        base_dir/
        ├── wrong_questions/    # 错题JSON文件
        ├── analysis_reports/  # 分析报告
        ├── review_logs.jsonl  # FSRS ReviewLog 日志（按 question_id 索引，每条一行）
        └── fsrs_params.json   # FSRS 个性化参数持久化（UI 触发优化后保存）
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.questions_dir = base_dir / "wrong_questions"
        self.reports_dir = base_dir / "analysis_reports"
        # FSRS ReviewLog 日志文件：所有错题的复习记录都追加到同一文件
        # jsonl 格式（每行一个 JSON），按 question_id 索引查询
        # 数据源用于未来 Optimizer 计算个性化 21 参数（积累 1000+ 记录后启用）
        self.review_logs_file = base_dir / "review_logs.jsonl"
        # FSRS 个性化参数持久化文件：UI 触发优化并应用后保存
        # 启动时 fsrs_scheduler.load_persisted_parameters 自动加载
        self.fsrs_params_file = base_dir / "fsrs_params.json"
        # 确保所有子目录存在（review_logs.jsonl 和 fsrs_params.json 是文件，无需 mkdir）
        for d in [self.questions_dir, self.reports_dir]:
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

    def mark_reviewed(self, question_id: str, rating: int = 3) -> Optional[WrongQuestion]:
        """标记错题为已复习，基于 FSRS 更新调度状态

        使用 FSRS v6 DSR 记忆模型替代固定艾宾浩斯查表：
        根据用户评分（Again/Hard/Good/Easy）动态计算下次复习间隔，
        并更新 Card 的 stability/difficulty/state。

        同时将本次复习的 ReviewLog 追加到 review_logs.jsonl，
        作为未来 Optimizer 计算个性化参数的数据源（积累 1000+ 后启用）。

        Args:
            question_id: 错题ID
            rating: 1=Again 2=Hard 3=Good 4=Easy（默认 Good，向后兼容）

        Returns:
            更新后的 WrongQuestion，若 ID 不存在或无 improvement 返回 None
        """
        existing = self.load_wrong_question(question_id)
        if existing is None:
            return None

        # 若没有 improvement 字段，无法标记复习
        if existing.improvement is None:
            return None

        # 局部导入避免 storage ↔ tools 循环依赖
        from deep_review_mcp.tools.fsrs_scheduler import schedule_review

        # 调用 FSRS 调度：老数据无 fsrs_state 时自动初始化新卡
        result = schedule_review(existing.improvement.fsrs_state, rating)

        updated = self.patch_wrong_question(question_id, {
            "improvement": {
                "review_count": existing.improvement.review_count + 1,  # 兼容字段
                "next_review_date": result["next_review_date"],         # 由 FSRS due 回填
                "fsrs_state": result["fsrs_state"],                     # FSRS Card 真实状态
            }
        })

        # 错题状态更新成功后，追加 ReviewLog 到日志文件
        # 失败不回滚错题状态（错题调度已正确，日志缺失仅影响未来优化器精度）
        if updated is not None:
            try:
                self.append_review_log(
                    question_id=question_id,
                    review_log_json=result["review_log"],
                    rating=rating,
                    reviewed_at=result["reviewed_at"],
                )
            except OSError as e:
                # 文件写入失败：打印警告但不抛出，保证主流程可用
                print(f"[storage] 追加 review_log 失败（不影响调度）: {e}")

        return updated

    # ──────────────────────────────────────────
    # FSRS ReviewLog 日志（jsonl 追加写入）
    # ──────────────────────────────────────────

    def append_review_log(
        self,
        question_id: str,
        review_log_json: str,
        rating: int,
        reviewed_at: str,
    ) -> None:
        """追加一条复习记录到 review_logs.jsonl

        jsonl 格式：每行一个 JSON 对象，包含 question_id/rating/reviewed_at/review_log。
        追加模式写入，单条 write 在单进程下原子，本地单用户场景足够安全。

        Args:
            question_id: 错题ID（主索引）
            review_log_json: FSRS ReviewLog 的 JSON 字符串（来自 schedule_review）
            rating: 1-4 评分（冗余字段，便于直接查询统计）
            reviewed_at: ISO 时间戳（冗余字段，便于按时间排序）
        """
        # 组装一条日志记录：review_log 作为嵌套字符串保留原始 FSRS 数据
        record = {
            "question_id": question_id,
            "rating": rating,
            "reviewed_at": reviewed_at,
            "review_log": review_log_json,
        }
        # ensure_ascii=False 保留中文（若有），separators 紧凑输出
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))

        # 追加模式：文件不存在时自动创建，存在时在末尾追加
        # 单条 write + 换行，单进程下原子性足够
        with open(self.review_logs_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def list_review_logs(self, question_id: str) -> list[dict]:
        """查询某错题的所有复习记录（按时间升序）

        Args:
            question_id: 错题ID

        Returns:
            复习记录列表，每条含 question_id/rating/reviewed_at/review_log；
            文件不存在时返回空列表。
        """
        if not self.review_logs_file.exists():
            return []

        records = []
        for line in self.review_logs_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if rec.get("question_id") == question_id:
                    records.append(rec)
            except json.JSONDecodeError:
                # 跳过损坏行（部分写入等异常情况），不中断查询
                continue
        # 按时间升序排列
        records.sort(key=lambda x: x.get("reviewed_at", ""))
        return records

    def list_all_review_logs(self) -> list[dict]:
        """查询全部复习记录（供 Optimizer 计算个性化参数用）

        Returns:
            全部复习记录列表，每条含 question_id/rating/reviewed_at/review_log；
            文件不存在时返回空列表。
        """
        if not self.review_logs_file.exists():
            return []

        records = []
        for line in self.review_logs_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                # 跳过损坏行，保证 Optimizer 数据获取不被中断
                continue
        return records

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
