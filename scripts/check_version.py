#!/usr/bin/env python3
"""版本一致性校验 —— AGENTS.md「质量与合规规则 > 文档」的机械防线

真相源：`deep-review.plugin/deep-review-mcp/pyproject.toml` 的 `[project].version`。

校验项：
    1. CHANGELOG.md 最新条目版本
    2. README.md / DEPLOY.md / QUICKSTART.md 中的发行包名 `DeepReview-vX.Y.Z.*`
    3. README.md / DEPLOY.md 中的 `build-release.{ps1,sh}` 示例版本参数
    4. 清单类文件：根 package.json / plugin.json（主 + CodeBuddy 副本）/ marketplace.json / tools.json
    5. `src/deep_review_mcp/__init__.py` 的硬编码 `__version__`
    6. （可选 --tag）发布 tag 与真相源一致，防止打错 tag

背景：vocabcraft 引入本脚本的原因是 `__init__.py` 硬编码版本漂移 5 个版本无人察觉；
DeepReview 是同样的硬编码模式，故移植时一并纳入校验；tools.json（AAIF 声明）
携带版本但常规清单校验不覆盖，同样纳入。

用法：
    python scripts/check_version.py              # 校验文档与清单
    python scripts/check_version.py --tag v0.6.0 # 额外校验发布 tag
退出码：0 全部一致；1 存在不一致。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "deep-review.plugin" / "deep-review-mcp" / "pyproject.toml"

# 只匹配确定指向本项目版本的位置，避免把依赖约束（如 fastmcp>=3.0.0）当成误报
PATTERNS: list[tuple[str, str]] = [
    # dist/DeepReview-v0.6.0.zip / DeepReview-v0.6.0.tar.zst
    (r"DeepReview-v(\d+\.\d+\.\d+)", "发行包名"),
    # build-release.ps1 -Version 0.6.0 / build-release.sh 0.6.0
    (r"build-release\.(?:ps1|sh)(?:\s+-Version)?\s+(\d+\.\d+\.\d+)", "构建命令示例"),
]

DOCS = ["README.md", "DEPLOY.md", "QUICKSTART.md"]

# 清单类文件的版本路径（键为相对路径，值为从 JSON 根到版本的键序列；int 表示数组下标）
MANIFEST_VERSIONS: list[tuple[str, tuple[str | int, ...]]] = [
    ("package.json", ("version",)),
    ("deep-review.plugin/plugin.json", ("version",)),
    ("deep-review.plugin/.codebuddy-plugin/plugin.json", ("version",)),
    (".codebuddy-plugin/marketplace.json", ("plugins", 0, "version")),
    ("marketplace.json", ("plugins", 0, "version")),
    ("deep-review.plugin/tools.json", ("version",)),
]

INIT_PY = (
    ROOT / "deep-review.plugin" / "deep-review-mcp"
    / "src" / "deep_review_mcp" / "__init__.py"
)
INIT_VERSION = re.compile(r'^__version__\s*=\s*"(\d+\.\d+\.\d+)"', re.MULTILINE)


def scan_manifests(expected: str) -> list[str]:
    """校验插件/市场/声明清单的版本号，返回不一致项描述"""
    problems: list[str] = []
    for rel, keys in MANIFEST_VERSIONS:
        path = ROOT / rel
        if not path.exists():
            problems.append(f"{rel}: 文件不存在")
            continue
        try:
            node: object = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{rel}: JSON 解析失败（{exc}）")
            continue
        found: object = None
        for key in keys:
            if (isinstance(node, dict) and isinstance(key, str) and key in node) or (
                isinstance(node, list) and isinstance(key, int) and key < len(node)
            ):
                node = node[key]
            else:
                node = None
                break
            found = node
        if not isinstance(found, str):
            problems.append(f"{rel}: 未找到版本字段 {'/'.join(map(str, keys))}")
        elif found != expected:
            problems.append(f"{rel}: 版本为 {found}，应为 {expected}")
    return problems


def scan_init_py(expected: str) -> list[str]:
    """校验包 __init__.py 的硬编码 __version__（历史漂移盲区）"""
    m = INIT_VERSION.search(INIT_PY.read_text(encoding="utf-8"))
    if not m:
        return [f"{INIT_PY.relative_to(ROOT)}: 未找到 __version__ 定义"]
    if m.group(1) != expected:
        return [f"__init__.py: __version__ 为 {m.group(1)}，应为 {expected}"]
    return []


def source_version() -> str:
    """从 pyproject.toml 读取真相源版本"""
    with PYPROJECT.open("rb") as f:
        return tomllib.load(f)["project"]["version"]


def changelog_version() -> str | None:
    """取 CHANGELOG.md 中最新的 `## [X.Y.Z]` 条目"""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^##\s*\[(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    return m.group(1) if m else None


def scan_docs(expected: str) -> list[str]:
    """扫描文档中的版本引用，返回不一致项描述"""
    problems: list[str] = []
    for name in DOCS:
        path = ROOT / name
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for pattern, label in PATTERNS:
                for found in re.findall(pattern, line):
                    if found != expected:
                        problems.append(
                            f"{name}:{lineno} {label}为 {found}，应为 {expected}"
                        )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="校验版本号在各处保持一致")
    parser.add_argument("--tag", help="发布 tag（形如 v0.6.0 或 0.6.0）")
    args = parser.parse_args()

    expected = source_version()
    problems = scan_docs(expected)
    problems += scan_manifests(expected)
    problems += scan_init_py(expected)

    changelog = changelog_version()
    if changelog is None:
        problems.append("CHANGELOG.md 未找到形如 `## [X.Y.Z]` 的版本条目")
    elif changelog != expected:
        problems.append(f"CHANGELOG.md 最新条目为 {changelog}，应为 {expected}")

    if args.tag:
        tag = args.tag.lstrip("v")
        if tag != expected:
            problems.append(f"发布 tag 为 v{tag}，但 pyproject.toml 为 {expected}")

    if problems:
        print(f"版本不一致（真相源 pyproject.toml = {expected}）：", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("\n修正后重试；真相源本身需变更时，请先改 pyproject.toml。", file=sys.stderr)
        return 1

    print(f"版本一致性校验通过：{expected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())