# tests/test_tools_ocr.py
"""OCR识别Tool单元测试"""

import pytest
from unittest.mock import patch, MagicMock
from deep_review_mcp.tools.ocr_recognize import ocr_recognize, _run_paddle_ocr


def test_ocr_with_mock():
    """测试PaddleOCR正常识别流程"""
    with patch("deep_review_mcp.tools.ocr_recognize._get_ocr_engine") as mock_get:
        mock_engine = MagicMock()
        # 模拟PaddleOCR返回格式: [[None, [("识别文本", 置信度)]]]
        mock_engine.ocr.return_value = [[
            [["坐标"], ("若x²-5x+6=0", 0.95)],
            [["坐标"], ("则x的值为", 0.92)],
        ]]
        mock_get.return_value = mock_engine
        text = _run_paddle_ocr("fake.jpg")
        assert "若x²-5x+6=0" in text
        assert "则x的值为" in text


def test_ocr_fallback():
    """测试OCR识别失败时的降级处理"""
    with patch("deep_review_mcp.tools.ocr_recognize._run_paddle_ocr", side_effect=Exception("失败")):
        result = ocr_recognize("nonexistent.jpg")
        assert result["raw_text"] == ""
        assert "error" in result


def test_ocr_file_not_exist():
    """测试图片文件不存在时的错误处理"""
    result = ocr_recognize("nonexistent_file_12345.jpg")
    assert result["raw_text"] == ""
    assert "error" in result
    assert "不存在" in result["error"]


def test_ocr_empty_result():
    """测试OCR返回空结果时的处理"""
    with patch("deep_review_mcp.tools.ocr_recognize._get_ocr_engine") as mock_get:
        mock_engine = MagicMock()
        # 模拟PaddleOCR返回空结果
        mock_engine.ocr.return_value = [[None]]
        mock_get.return_value = mock_engine
        result = ocr_recognize("fake.jpg")
        assert result["raw_text"] == ""
        assert "error" in result


def test_ocr_success_returns_parse_prompt():
    """测试OCR成功时返回结构化解析提示"""
    with patch("deep_review_mcp.tools.ocr_recognize._run_paddle_ocr") as mock_run:
        mock_run.return_value = "若x²-5x+6=0，则x的值为"
        # 需要文件存在才能走到OCR逻辑，用patch绕过文件检查
        with patch("deep_review_mcp.tools.ocr_recognize.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            result = ocr_recognize("fake.jpg")
            assert result["raw_text"] == "若x²-5x+6=0，则x的值为"
            assert "parse_prompt" in result
            assert "结构化" in result["parse_prompt"]


def test_ocr_paddleocr_not_installed():
    """测试未安装 paddleocr 可选依赖时的降级行为

    paddleocr/paddlepaddle 已从核心依赖移到 optional[ocr]，
    懒加载时若未安装应抛 ImportError，上层 ocr_recognize 应转为友好降级响应。
    """
    import deep_review_mcp.tools.ocr_recognize as ocr_mod

    # 重置懒加载缓存，确保 patch 生效
    ocr_mod._ocr_engine = None

    # 模拟 import paddleocr 抛 ImportError
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "paddleocr" or name.startswith("paddleocr."):
            raise ImportError("No module named 'paddleocr'")
        return real_import(name, *args, **kwargs)

    with patch.object(builtins, "__import__", side_effect=fake_import):
        # 文件存在，绕过文件检查
        with patch.object(ocr_mod, "_run_paddle_ocr", side_effect=ImportError(
            "未安装 PaddleOCR。请运行 `uv sync --extra ocr`"
        )):
            with patch("deep_review_mcp.tools.ocr_recognize.Path") as mock_path:
                mock_path.return_value.exists.return_value = True
                result = ocr_recognize("fake.jpg")

    assert result["raw_text"] == ""
    assert "error" in result
    assert "OCR识别失败" in result["error"]
