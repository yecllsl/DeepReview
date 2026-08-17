#!/usr/bin/env python3
"""一次性回填脚本：为结构化字段缺失的存量错题补齐默认值（业务规则 #6）。

v0.1.x 的旧记录可能缺少 structured/classification，或残留已废弃的
raw_text 字段，导致新搜索（基于 question_content）搜不到。本脚本扫描
data/wrong_questions/*.json，对缺失的 structured/classification 复用
crud._fill_required_defaults 填充规则默认值，并在存在 raw_text 时回填到
structured.question_content（UTF-8 安全，仅本地运行，不做任何外部写入）。

运行方式（与其它生成脚本同款 import 约定）：

    uv run --no-sync --directory deep-review-mcp python scripts/backfill-structured.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from deep_review_mcp.tools.crud import _fill_required_defaults

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "deep-review-mcp" / "data" / "wrong_questions"


def main() -> int:
    parser = argparse.ArgumentParser(description="回填存量错题的缺失结构化字段")
    parser.add_argument("--dry-run", action="store_true", help="只统计不写入")
    args = parser.parse_args()

    if not DATA_DIR.is_dir():
        print(f"数据目录不存在: {DATA_DIR}")
        return 1

    updated = 0
    untouched = 0
    for fp in sorted(DATA_DIR.glob("*.json")):
        data = json.loads(fp.read_text(encoding="utf-8"))

        # 迁移废弃的 raw_text -> structured.question_content（仅当题目内容为空时）
        raw_text = data.pop("raw_text", None)
        if raw_text and data.get("structured", {}) is not None \
                and not data["structured"].get("question_content"):
            data["structured"]["question_content"] = raw_text

        filled = _fill_required_defaults(data)
        if filled == data:
            untouched += 1
            continue

        updated += 1
        if args.dry_run:
            print(f"[dry-run] 需要回填: {fp.name}")
            continue
        # 原子写入，避免中途崩溃损坏数据
        tmp = fp.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(filled, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        tmp.replace(fp)
        print(f"[backfilled] {fp.name}")

    print(f"完成: 更新 {updated} 条, 无需处理 {untouched} 条"
          + ("（dry-run）" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())