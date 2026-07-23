# DeepReview v0.1.0 发布打包方案

## Context

项目 v0.1.0 功能完成，需要打包为 zip 发布。用户下载解压后用 Trae IDE CN 打开即可使用，尽量少手工调整。

**核心问题**：当前 `.trae/mcp.json` 中 `cwd` 字段为硬编码绝对路径，解压到不同位置后 MCP Server 无法启动。需彻底消除路径硬编码。

**已验证**：Trae IDE CN 官方文档确认 `.trae/mcp.json` 支持 `${workspaceFolder}` 变量（在 MCP Server 启动时自动替换为项目根目录绝对路径），项目级 MCP 在 IDE 模式下正常工作。

---

## 一、核心改造：mcp.json 使用 ${workspaceFolder}

**当前**（硬编码路径）：
```json
{
  "mcpServers": {
    "deep-review-mcp": {
      "command": "uv",
      "args": ["run", "deep-review-mcp"],
      "cwd": "d:\\yecll\\Documents\\LocalCode\\DeepReview\\deep-review-mcp"
    }
  }
}
```

**改造后**（变量路径，无需 `cwd`）：
```json
{
  "mcpServers": {
    "deep-review-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "${workspaceFolder}/deep-review-mcp",
        "deep-review-mcp"
      ]
    }
  }
}
```

**关键变更**：
1. 删除 `cwd` 字段（Trae 官方文档中 stdio 类型配置无此字段）
2. 使用 `uv run --directory <path>` 替代 `cwd`，等价于先 cd 再执行
3. `${workspaceFolder}` 在 MCP Server 启动时由 Trae 自动替换，例如 → `D:/Tools/DeepReview`
4. 正斜杠路径在 Windows + uv 下正常工作

---

## 二、安装脚本改造：install.ps1 / install.sh

**主要变更**：
1. 移除 `SERVER_METADATA.json` 生成逻辑（项目级 mcp.json 已替代）
2. 使用 `uv sync` 替代 `uv venv` + `uv pip install -e .`（精确复现 uv.lock 环境）
3. 增加安装验证步骤
4. 提示用户启用项目级 MCP（设置 → MCP → 启用项目级 MCP）
5. PaddleOCR 安装进度提示

**简化后的用户流程**：
```
[1/4] 检查 uv 包管理器
[2/4] 检查 Python 版本 (>=3.12)
[3/4] 安装依赖（PaddleOCR 模型较大，可能需要几分钟）
[4/4] 验证安装 → uv run deep-review-mcp 入口点可用
→ 提示：用 Trae 打开文件夹 → 设置 > MCP > 启用项目级 MCP → 重启
```

---

## 三、.python-version 统一

`3.13` → `3.12`，降低用户门槛（3.12 更广泛可用，且与 pyproject.toml 的 `requires-python = ">=3.12"` 一致）

---

## 四、打包清单

### 包含

```
DeepReview-v0.1.0/
├── .trae/
│   ├── mcp.json                      # ← 改造后，${workspaceFolder}
│   ├── hooks.json
│   ├── rules/                        # 4 个规则文件
│   └── skills/                       # 5 个 Skill
├── deep-review-mcp/
│   ├── src/deep_review_mcp/          # 全部源码
│   ├── data/
│   │   ├── wrong_questions/.gitkeep
│   │   ├── analysis_reports/.gitkeep
│   │   ├── review_plans/.gitkeep
│   │   └── exports/.gitkeep
│   ├── pyproject.toml
│   ├── uv.lock
│   └── .python-version               # ← 改为 3.12
├── install.ps1                       # ← 改造后
├── install.sh                        # ← 改造后
├── README.md
├── DEPLOY.md
├── QUICKSTART.md
└── LICENSE
```

### 排除

| 排除项 | 原因 |
|--------|------|
| `.git/` | 版本控制元数据 |
| `.github/` | CI 配置 |
| `deep-review-mcp/.venv/` | 虚拟环境，用户本机生成 |
| `deep-review-mcp/__pycache__/` | 编译缓存 |
| `deep-review-mcp/.pytest_cache/` | 测试缓存 |
| `deep-review-mcp/tests/` | 测试代码 |
| `deep-review-mcp/data/wrong_questions/*.json` | 用户数据 |
| `deep-review-mcp/data/exports/*`（除 .gitkeep） | 用户数据 |
| `deep-review-mcp/data/analysis_reports/*.json` | 用户数据 |
| `deep-review-mcp/data/review_plans/*.json` | 用户数据 |
| `.vscode/` | IDE 个人配置 |
| `docs/` | 开发文档 |

---

## 五、构建脚本：scripts/build-release.ps1

新增开发者用打包脚本，从源码生成发布 zip：

1. 创建临时目录，复制需要包含的文件
2. 清理用户数据（保留 .gitkeep）
3. 删除 tests/、.github/、docs/ 等
4. 打包为 `DeepReview-v0.1.0.zip`

预估包大小：~1.8 MB（压缩后 ~500 KB，不含 PaddleOCR 模型——模型在首次运行时由 PaddleOCR 自动下载到用户缓存目录）

---

## 六、文档更新

### README.md 更新
- 简化安装步骤（不再需要手动配置全局 MCP）
- 增加"启用项目级 MCP"说明
- 更新 mcp.json 配置示例（使用 ${workspaceFolder}）

### DEPLOY.md 更新
- 同步简化安装流程
- 增加故障排查：${workspaceFolder} 不替换时的回退方案

### QUICKSTART.md 更新
- 首步增加"运行 install.ps1 安装依赖"

---

## 七、风险评估与回退

| 风险 | 缓解措施 |
|------|----------|
| `${workspaceFolder}` 在某些 Trae 版本不替换 args 中的变量 | install.ps1 回退逻辑：检测到未替换时，自动将 `${workspaceFolder}` 替换为实际路径写入 mcp.json |
| PaddleOCR 安装失败 | install.ps1 给出详细错误提示 + 手动安装命令；OCR 有降级方案（手动输入） |
| 用户未启用项目级 MCP | install.ps1 末尾醒目提示；README 中标注 |

**回退方案**：在 install.ps1 中增加逻辑，如果 Trae 版本不支持变量替换，自动将 mcp.json 中的 `${workspaceFolder}` 替换为 `$PSScriptRoot` 实际路径。

---

## 八、实施步骤

1. **改造 `.trae/mcp.json`** — 使用 `${workspaceFolder}`，删除 `cwd`
2. **改造 `install.ps1` / `install.sh`** — 简化流程，增加验证和回退逻辑
3. **修改 `.python-version`** — 3.13 → 3.12
4. **新增 `scripts/build-release.ps1`** — 自动化打包
5. **更新 `README.md` / `DEPLOY.md` / `QUICKSTART.md`** — 同步新安装流程
6. **执行打包测试** — 运行 build-release.ps1，在全新目录验证安装流程

---

## 九、目标用户体验

```
3 步即可使用：
1. 下载 zip → 解压到 D:\DeepReview\
2. 双击 install.ps1（等 2-5 分钟安装依赖）
3. Trae 打开 D:\DeepReview\ → 启用项目级 MCP → 开始使用
```

对比当前流程（需手动配置全局 MCP、手动填写路径），大幅简化。
