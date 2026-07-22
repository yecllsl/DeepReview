#!/bin/bash
# DeepReview MCP Server 安装脚本
# 适用于 Linux / macOS

set -e

echo "========================================"
echo "  DeepReview MCP Server 安装向导"
echo "========================================"
echo ""

# 获取脚本所在目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检查 uv 是否安装
echo "[1/5] 检查 uv 包管理器..."
if ! command -v uv &> /dev/null; then
    echo "  ✗ uv 未安装"
    echo ""
    echo "  请先安装 uv："
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo "  ✓ uv 已安装 ($(uv --version))"

# 检查 Python 版本
echo "[2/5] 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "  ✗ Python 未安装"
    echo ""
    echo "  请先安装 Python 3.12+："
    echo "  https://www.python.org/downloads/"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "  ✓ $PYTHON_VERSION"

# 安装依赖
echo "[3/5] 安装 MCP Server 依赖..."

cd "$PROJECT_ROOT/deep-review-mcp"

if [ -d ".venv" ]; then
    echo "  发现已有虚拟环境，使用现有环境..."
else
    echo "  创建虚拟环境..."
    uv venv
fi

echo "  安装依赖包..."
uv pip install -e .

echo "  ✓ 依赖安装完成"

# 生成 Trae MCP 配置
echo "[4/5] 生成 Trae MCP 配置..."

MCP_CONFIG_DIR="$PROJECT_ROOT/.trae/mcp-servers/deep-review-mcp"

mkdir -p "$MCP_CONFIG_DIR/tools"

cat > "$MCP_CONFIG_DIR/SERVER_METADATA.json" << EOF
{
  "server_name": "deep-review-mcp",
  "command": "uv",
  "args": ["run", "deep-review-mcp"],
  "cwd": "$PROJECT_ROOT/deep-review-mcp",
  "transport": "stdio"
}
EOF

echo "  ✓ MCP Server 配置已生成"

# 检查 Skills 和 Rules 配置
echo "[5/5] 检查 Skills 和 Rules 配置..."

TRAE_SKILLS_DIR="$PROJECT_ROOT/.trae/skills"
TRAE_RULES_DIR="$PROJECT_ROOT/.trae/rules"

if [ -d "$TRAE_SKILLS_DIR" ]; then
    echo "  ✓ Skills 配置已就绪 ($TRAE_SKILLS_DIR)"
else
    echo "  ⚠  未找到 .trae/skills/ 目录，请检查项目结构"
fi

if [ -d "$TRAE_RULES_DIR" ]; then
    echo "  ✓ Rules 配置已就绪 ($TRAE_RULES_DIR)"
else
    echo "  ⚠  未找到 .trae/rules/ 目录，请检查项目结构"
fi

echo ""
echo "========================================"
echo "  安装完成！"
echo "========================================"
echo ""
echo "下一步操作："
echo "1. 打开 Trae Work IDE"
echo "2. 进入 设置 → MCP配置"
echo "3. 点击 添加MCP服务器"
echo "4. 选择从文件导入，导入以下文件："
echo "   $MCP_CONFIG_DIR/SERVER_METADATA.json"
echo ""
echo "或者复制以下配置信息手动填写："
echo "   - 服务器名称: deep-review-mcp"
echo "   - 命令: uv"
echo "   - 参数: run deep-review-mcp"
echo "   - 工作目录: $PROJECT_ROOT/deep-review-mcp"
echo ""
echo "5. Skills 和 Rules 配置已就绪"
echo ""
echo "使用示例："
echo "   /capture  - 采集新错题"
echo "   /analyze - 分析错题原因"
echo "   /review  - 生成复习计划"
echo "   /stats   - 查看错题统计"
echo ""
echo ""
echo "项目结构说明："
echo "  .trae/skills/   - Skills 源文件（编辑这里）"
echo "  .trae/rules/    - Rules 源文件（编辑这里）"
echo "  deep-review-mcp/ - MCP Server 代码"
echo ""
