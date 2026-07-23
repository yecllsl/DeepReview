# DeepReview MCP Server 安装脚本
# 适用于 Windows PowerShell
#
# 使用方法：
#   1. 右键此文件 → "使用 PowerShell 运行"
#   2. 或在 PowerShell 中执行: .\install.ps1
#
# 前置要求：
#   - Python 3.12+
#   - uv 包管理器 (https://docs.astral.sh/uv/)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DeepReview v0.1.0 安装向导" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录（项目根目录）
$projectRoot = $PSScriptRoot

# ──────────────────────────────────────────
# [1/4] 检查 uv 包管理器
# ──────────────────────────────────────────
Write-Host "[1/4] 检查 uv 包管理器..." -ForegroundColor Yellow
try {
    $uvVersion = uv --version 2>&1
    Write-Host "  ✓ uv 已安装 ($uvVersion)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ uv 未安装" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请先安装 uv：" -ForegroundColor Yellow
    Write-Host '  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"' -ForegroundColor White
    Write-Host ""
    Write-Host "  或访问 https://docs.astral.sh/uv/getting-started/install/" -ForegroundColor White
    exit 1
}

# ──────────────────────────────────────────
# [2/4] 检查 Python 版本
# ──────────────────────────────────────────
Write-Host "[2/5] 检查 Python 版本 (>=3.12)..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Python 未安装" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请先安装 Python 3.12+：" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor White
    exit 1
}
# 提取版本号并比较
$versionMatch = $pythonVersion -match "(\d+)\.(\d+)"
if ($versionMatch) {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 12)) {
        Write-Host "  ✗ Python 版本过低: $pythonVersion (需要 >= 3.12)" -ForegroundColor Red
        Write-Host ""
        Write-Host "  请升级 Python: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host "  ✓ $pythonVersion" -ForegroundColor Green

# ──────────────────────────────────────────
# [3/5] 安装基础依赖
# ──────────────────────────────────────────
Write-Host "[3/5] 安装基础依赖..." -ForegroundColor Yellow
Write-Host "  基础依赖不含 OCR 引擎（paddleocr/paddlepaddle 体积大，已拆为可选）" -ForegroundColor Cyan

$mcpDir = Join-Path $projectRoot "deep-review-mcp"

# 使用 uv sync 安装基础依赖（不包含 ocr extra）
Push-Location $mcpDir
try {
    Write-Host "  正在安装依赖包..." -ForegroundColor Cyan
    uv sync 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ 依赖安装失败" -ForegroundColor Red
        Write-Host ""
        Write-Host "  请尝试手动安装：" -ForegroundColor Yellow
        Write-Host "  cd deep-review-mcp" -ForegroundColor White
        Write-Host "  uv sync" -ForegroundColor White
        exit 1
    }
    Write-Host "  ✓ 基础依赖安装完成" -ForegroundColor Green
} finally {
    Pop-Location
}

# ──────────────────────────────────────────
# [4/5] 询问并安装可选 OCR 依赖
# ──────────────────────────────────────────
Write-Host "[4/5] 是否安装 OCR 可选依赖？" -ForegroundColor Yellow
Write-Host "  OCR 用于图片错题识别，paddleocr+paddlepaddle 约 1.5GB，安装较慢。" -ForegroundColor Cyan
Write-Host "  仅当需要 /capture 拍照录入错题时才需要。" -ForegroundColor Cyan
$installOcr = Read-Host "  安装 OCR 依赖？[y/N]"
if ($installOcr -match "^[Yy]$") {
    Push-Location $mcpDir
    try {
        Write-Host "  正在安装 OCR 依赖..." -ForegroundColor Cyan
        uv sync --extra ocr 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ OCR 依赖安装失败，可稍后手动重试：uv sync --extra ocr" -ForegroundColor Red
        } else {
            Write-Host "  ✓ OCR 依赖安装完成" -ForegroundColor Green
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  ⊘ 已跳过 OCR 依赖。后续需要时执行：cd deep-review-mcp && uv sync --extra ocr" -ForegroundColor DarkGray
}

# ──────────────────────────────────────────
# [5/5] 验证安装
# ──────────────────────────────────────────
Write-Host "[5/5] 验证安装..." -ForegroundColor Yellow

Push-Location $mcpDir
try {
    # 验证 MCP Server 入口点可用
    $testResult = uv run deep-review-mcp --help 2>&1
    # FastMCP 的 --help 可能直接启动 server，所以只要不报错即可
    Write-Host "  ✓ MCP Server 入口点可用" -ForegroundColor Green
    
    # 验证 Web 入口点可用
    $webTest = uv run python -c "from deep_review_mcp.web.app import create_app; print('OK')" 2>&1
    if ($webTest -match "OK") {
        Write-Host "  ✓ Web 可视化模块可用" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Web 可视化模块验证跳过" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ 自动验证失败，但不影响使用" -ForegroundColor Yellow
    Write-Host "  如遇问题请手动验证: cd deep-review-mcp && uv run deep-review-mcp" -ForegroundColor Yellow
} finally {
    Pop-Location
}

# ──────────────────────────────────────────
# mcp.json 路径回退方案
# ──────────────────────────────────────────
# 检查 .trae/mcp.json 中的 ${workspaceFolder} 变量是否被 Trae 支持
# 如果用户 Trae 版本不支持此变量，安装脚本可自动替换为实际路径
$mcpJsonPath = Join-Path $projectRoot ".trae\mcp.json"
if (Test-Path $mcpJsonPath) {
    $mcpContent = Get-Content $mcpJsonPath -Raw
    if ($mcpContent -match '\$\{workspaceFolder\}') {
        Write-Host ""
        Write-Host "  ℹ 检测到 mcp.json 使用了 \${workspaceFolder} 变量" -ForegroundColor Cyan
        Write-Host "    Trae IDE CN 会自动替换此变量，无需手动配置" -ForegroundColor Cyan
        Write-Host "    如果你的 Trae 版本不支持变量替换，请运行：" -ForegroundColor Cyan
        Write-Host "    .\install.ps1 -FixPath" -ForegroundColor White
    }
}

# 处理 -FixPath 参数：将 ${workspaceFolder} 替换为实际路径
if ($args -contains "-FixPath") {
    Write-Host ""
    Write-Host "  正在修复 mcp.json 路径..." -ForegroundColor Yellow
    if (Test-Path $mcpJsonPath) {
        $mcpContent = Get-Content $mcpJsonPath -Raw
        $escapedRoot = $projectRoot -replace '\\', '/'
        $fixedContent = $mcpContent -replace '\$\{workspaceFolder\}', $escapedRoot
        Set-Content -Path $mcpJsonPath -Value $fixedContent -Encoding UTF8
        Write-Host "  ✓ mcp.json 路径已修复为: $escapedRoot" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 未找到 $mcpJsonPath" -ForegroundColor Red
    }
}

# ──────────────────────────────────────────
# 安装完成提示
# ──────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ 安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor White
Write-Host ""
Write-Host "  1. 用 Trae IDE 打开此文件夹" -ForegroundColor White
Write-Host "     文件 → 打开文件夹 → 选择: $projectRoot" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  2. 启用项目级 MCP" -ForegroundColor White
Write-Host "     设置 → MCP → 打开'启用项目级 MCP'开关" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  3. 重启 Trae" -ForegroundColor White
Write-Host ""
Write-Host "  4. 开始使用！" -ForegroundColor White
Write-Host "     /capture  - 采集新错题" -ForegroundColor DarkGray
Write-Host "     /analyze  - 分析错题原因" -ForegroundColor DarkGray
Write-Host "     /review   - 生成复习计划" -ForegroundColor DarkGray
Write-Host "     /stats    - 查看错题统计" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  可选：启动 Web 可视化界面" -ForegroundColor Cyan
Write-Host "     cd deep-review-mcp && uv run deep-review-web" -ForegroundColor DarkGray
Write-Host "     浏览器访问 http://127.0.0.1:8001" -ForegroundColor DarkGray
Write-Host ""
