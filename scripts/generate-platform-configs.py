#!/usr/bin/env python3
"""Generate AAIF platform runtime configs into deep-review.plugin/runtime/.

The generated files are consumed by scripts/sync-agent-configs(.ps1/.sh),
which distributes them to the .trae / .opencode platform directories.

Note: CodeBuddy and VS Code use the Tier 1 plugin channel (the
deep-review.plugin/ Agent Plugins 1.0 package, installed via the
.codebuddy-plugin/marketplace.json local market for CodeBuddy), so no
.codebuddy runtime config is generated here.

Usage:
    python scripts/generate-platform-configs.py
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = PROJECT_ROOT / "deep-review.plugin" / "runtime"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def generate_trae() -> dict:
    return {
        "mcpServers": {
            "deep-review-mcp": {
                "command": "uv",
                "args": [
                    "run",
                    "--no-sync",
                    "--directory",
                    "${workspaceFolder}/deep-review.plugin/deep-review-mcp",
                    "deep-review-mcp",
                ],
            }
        }
    }


def generate_opencode() -> dict:
    return {
        "$schema": "https://opencode.ai/config.json",
        "mcp": {
            "deep-review-mcp": {
                "type": "local",
                "command": ["uv", "run", "--no-sync", "deep-review-mcp"],
                "cwd": "deep-review.plugin/deep-review-mcp",
            }
        },
        "instructions": ["deep-review.plugin/AGENTS.md"],
    }


def main() -> None:
    (RUNTIME_DIR / "trae.json").write_text(
        json.dumps(generate_trae(), indent=2) + "\n", encoding="utf-8"
    )
    (RUNTIME_DIR / "opencode.json").write_text(
        json.dumps(generate_opencode(), indent=2) + "\n", encoding="utf-8"
    )
    print("已生成 Tier 2 平台配置 (deep-review.plugin/runtime/): trae.json, opencode.json")


if __name__ == "__main__":
    main()
