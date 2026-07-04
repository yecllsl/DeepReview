# DeepReview MCP Server 安装脚本
# 适用于 Windows PowerShell

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DeepReview MCP Server 安装向导" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录（项目根目录）
$projectRoot = $PSScriptRoot

# 检查 uv 是否安装
Write-Host "[1/5] 检查 uv 包管理器..." -ForegroundColor Yellow
try {
    uv --version | Out-Null
    Write-Host "  ✓ uv 已安装" -ForegroundColor Green
} catch {
    Write-Host "  ✗ uv 未安装" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请先安装 uv：" -ForegroundColor Yellow
    Write-Host '  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"' -ForegroundColor White
    exit 1
}

# 检查 Python 版本
Write-Host "[2/5] 检查 Python 版本..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Python 未安装" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请先安装 Python 3.12+：" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor White
    exit 1
}
Write-Host "  ✓ $pythonVersion" -ForegroundColor Green

# 安装依赖
Write-Host "[3/5] 安装 MCP Server 依赖..." -ForegroundColor Yellow
Set-Location "$projectRoot\deep-review-mcp"

# 检查是否已有虚拟环境
if (Test-Path ".venv") {
    Write-Host "  发现已有虚拟环境，使用现有环境..." -ForegroundColor Cyan
} else {
    Write-Host "  创建虚拟环境..." -ForegroundColor Cyan
    uv venv
}

Write-Host "  安装依赖包..." -ForegroundColor Cyan
uv pip install -e .

Write-Host "  ✓ 依赖安装完成" -ForegroundColor Green

# 生成 Trae 配置
Write-Host "[4/5] 生成 Trae MCP 配置..." -ForegroundColor Yellow

$escapedRoot = $projectRoot -replace '\\', '\\'
$configContent = @"
{
  "server_name": "deep-review-mcp",
  "command": "uv",
  "args": ["run", "deep-review-mcp"],
  "cwd": "$escapedRoot\\deep-review-mcp",
  "transport": "stdio"
}
"@

$mcpConfigDir = "$projectRoot\.trae\mcp-servers\deep-review-mcp
if (!(Test-Path $mcpConfigDir)) {
    New-Item -ItemType Directory -Path $mcpConfigDir -Force | Out-Null
    New-Item -ItemType Directory -Path "$mcpConfigDir\tools" -Force | Out-Null
}
Set-Content -Path "$mcpConfigDir\SERVER_METADATA.json -Value $configContent -Encoding UTF8
Write-Host "  ✓ MCP Server 配置已生成" -ForegroundColor Green

# 同步 Skills 和 Rules
Write-Host "[5/5] 同步 Skills 和 Rules..." -ForegroundColor Yellow

# 从项目根目录的 skills/ 和 rules/ 同步到 .trae/
$traeSkillsDir = "$projectRoot\.trae\skills"
$traeRulesDir = "$projectRoot\.trae\rules"
$sourceSkillsDir = "$projectRoot\skills"
$sourceRulesDir = "$projectRoot\rules"

if (Test-Path $sourceSkillsDir) {
    if (!(Test-Path $traeSkillsDir)) {
        New-Item -ItemType Directory -Path $traeSkillsDir -Force | Out-Null
    }
    Copy-Item -Path "$sourceSkillsDir\*" -Destination $traeSkillsDir -Recurse -Force
    Write-Host "  ✓ Skills 已同步" -ForegroundColor Green
} else {
    Write-Host "  ⚠  未找到 skills/ 目录，请检查项目结构" -ForegroundColor Yellow
}

if (Test-Path $sourceRulesDir) {
    if (!(Test-Path $traeRulesDir)) {
        New-Item -ItemType Directory -Path $traeRulesDir -Force | Out-Null
    }
    Copy-Item -Path "$sourceRulesDir\*" -Destination $traeRulesDir -Recurse -Force
    Write-Host "  ✓ Rules 已同步" -ForegroundColor Green
} else {
    Write-Host "  ⚠  未找到 rules/ 目录，请检查项目结构" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  安装完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor White
Write-Host "1. 打开 Trae Work IDE" -ForegroundColor White
Write-Host "2. 进入 设置 → MCP配置" -ForegroundColor White
Write-Host "3. 点击 添加MCP服务器" -ForegroundColor White
Write-Host "4. 选择从文件导入，导入以下文件：" -ForegroundColor White
Write-Host "   $mcpConfigDir\SERVER_METADATA.json" -ForegroundColor Cyan
Write-Host ""
Write-Host "或者复制以下配置信息手动填写：" -ForegroundColor Yellow
Write-Host "   - 服务器名称: deep-review-mcp" -ForegroundColor White
Write-Host "   - 命令: uv" -ForegroundColor White
Write-Host "   - 参数: run deep-review-mcp" -ForegroundColor White
Write-Host "   - 工作目录: $projectRoot\deep-review-mcp" -ForegroundColor White
Write-Host ""
Write-Host "5. Skills 和 Rules 已自动同步到 .trae/ 目录" -ForegroundColor White
Write-Host ""
Write-Host "使用示例：" -ForegroundColor Yellow
Write-Host '   /capture  - 采集新错题' -ForegroundColor White
Write-Host '   /analyze - 分析错题原因' -ForegroundColor White
Write-Host '   /review  - 生成复习计划' -ForegroundColor White
Write-Host '   /stats   - 查看错题统计' -ForegroundColor White
Write-Host ""
Write-Host ""
Write-Host "项目结构说明：" -ForegroundColor Yellow
Write-Host "  skills/           - Skills 源文件（编辑这里）" -ForegroundColor White
Write-Host "  rules/            - Rules 源文件（编辑这里）" -ForegroundColor White
Write-Host "  .trae/skills/   - Trae 运行时配置（自动同步）" -ForegroundColor White
Write-Host "  .trae/rules/    - Trae 运行时配置（自动同步）" -ForegroundColor White
Write-Host ""
