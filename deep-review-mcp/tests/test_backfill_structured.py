"""backfill-structured.py 的最小单元测试。

脚本文件名含连字符无法常规 import，通过 importlib 按路径加载。
直接测试核心纯函数 _backfill(data)，验证 v0.1.x 旧记录
（structured 缺失 / 为 None / 残留 raw_text）不再崩溃、题目原文不再被
静默丢弃，且结构完整的记录不被改动。
"""
import importlib.util
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
SCRIPT_FILE = SCRIPTS_DIR / "backfill-structured.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "backfill_structured", SCRIPT_FILE
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


backfill = _load_module()


def test_backfill_structured_missing_with_raw_text():
    """structured 键缺失 + 残留 raw_text：不崩溃，且原文回填进 question_content。"""
    data = {
        "question_id": "wq_20240101_001",
        "created_at": "2024-01-01T00:00:00",
        "raw_text": "求解二次方程 x^2=4",
    }
    filled = backfill._backfill(data)
    assert filled["structured"]["question_content"] == "求解二次方程 x^2=4"
    assert filled["structured"]["subject"] == "数学"
    assert filled["classification"]["error_type"] == "知识漏洞"
    # 原任务内容保留，raw_text 已迁移不再残留
    assert "raw_text" not in filled
    assert filled["question_id"] == "wq_20240101_001"


def test_backfill_structured_none_with_raw_text():
    """structured 为 None + 残留 raw_text：不崩溃，原文回填，默认结构补齐。"""
    data = {
        "question_id": "wq_20240101_002",
        "created_at": "2024-01-01T00:00:00",
        "structured": None,
        "raw_text": "英语完形填空原文",
    }
    filled = backfill._backfill(data)
    assert filled["structured"]["question_content"] == "英语完形填空原文"
    assert filled["classification"]["error_type"] == "知识漏洞"


def test_backfill_does_not_overwrite_existing_content():
    """已有 question_content 时，raw_text 不应覆盖它（只迁移空内容记录）。"""
    data = {
        "question_id": "wq_20240101_005",
        "created_at": "2024-01-01T00:00:00",
        "structured": {
            "subject": "数学", "grade_level": "初中", "knowledge_points": [],
            "difficulty": "基础", "question_type": "解答题",
            "question_content": "已有内容",
        },
        "classification": {"error_type": "审题失误", "error_category": "细分类别"},
        "raw_text": "备用原文",
    }
    filled = backfill._backfill(data)
    assert filled["structured"]["question_content"] == "已有内容"


def test_backfill_complete_record_unchanged():
    """结构完整且无 raw_text：结果与输入逐字段等价（untouched）。"""
    data = {
        "question_id": "wq_20240101_003",
        "created_at": "2024-01-01T00:00:00",
        "structured": {
            "subject": "数学", "grade_level": "初中", "knowledge_points": [],
            "difficulty": "基础", "question_type": "解答题",
            "question_content": "已有内容",
        },
        "classification": {"error_type": "审题失误", "error_category": "细分类别"},
    }
    filled = backfill._backfill(data)
    assert filled == data