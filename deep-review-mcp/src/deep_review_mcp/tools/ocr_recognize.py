# src/deep_review_mcp/tools/ocr_recognize.py
"""OCR识别+AI结构化解析Tool

使用PaddleOCR对题目图片进行文字识别，返回原始文本及结构化解析提示。
支持懒加载OCR引擎，避免模块导入时加载模型导致启动缓慢。
"""

from pathlib import Path
from deep_review_mcp.prompts.structure_parse import STRUCTURE_PARSE_PROMPT

# 全局OCR引擎实例，懒加载避免启动时加载模型
_ocr_engine = None


def _get_ocr_engine():
    """获取PaddleOCR引擎实例（懒加载单例模式）

    首次调用时初始化PaddleOCR引擎，后续调用直接复用。
    使用use_angle_cls=True支持旋转文字识别，lang="ch"支持中文。
    """
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR
        _ocr_engine = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
    return _ocr_engine


def _run_paddle_ocr(image_path: str) -> str:
    """执行PaddleOCR识别，返回识别出的文本

    Args:
        image_path: 图片文件路径

    Returns:
        识别出的文本，每行一个识别结果，用换行符连接
    """
    engine = _get_ocr_engine()
    result = engine.ocr(image_path, cls=True)
    lines = []
    if result and result[0]:
        for line in result[0]:
            # PaddleOCR返回格式: [坐标列表, (文本, 置信度)]
            if line and len(line) >= 2:
                lines.append(line[1][0])
    return "\n".join(lines)


def ocr_recognize(image_path: str) -> dict:
    """OCR识别题目图片

    对图片进行OCR文字识别，返回原始文本及结构化解析提示。
    识别失败时提供降级处理，提示用户手动输入。

    Args:
        image_path: 题目图片的文件路径

    Returns:
        包含以下字段的字典:
        - raw_text: OCR识别的原始文本
        - structured_question: 结构化题目数据（需AI二次解析，此处为None）
        - subject: 学科（需AI二次解析，此处为空）
        - grade_level: 年级段（需AI二次解析，此处为空）
        - parse_prompt: 结构化解析提示（包含原始文本，供AI解析使用）
        - error: 错误信息（仅在出错时存在）
    """
    # 检查文件是否存在
    if not Path(image_path).exists():
        return {
            "raw_text": "",
            "structured_question": None,
            "subject": "",
            "grade_level": "",
            "error": f"图片文件不存在: {image_path}",
        }

    # 执行OCR识别
    try:
        raw_text = _run_paddle_ocr(image_path)
    except Exception as e:
        return {
            "raw_text": "",
            "structured_question": None,
            "subject": "",
            "grade_level": "",
            "error": f"OCR识别失败: {str(e)}，请尝试手动输入题目文本",
        }

    # 检查识别结果是否为空
    if not raw_text.strip():
        return {
            "raw_text": "",
            "structured_question": None,
            "subject": "",
            "grade_level": "",
            "error": "OCR未识别到任何文字，请尝试手动输入",
        }

    # 返回识别结果及结构化解析提示
    return {
        "raw_text": raw_text,
        "structured_question": None,
        "subject": "",
        "grade_level": "",
        "parse_prompt": STRUCTURE_PARSE_PROMPT.format(raw_text=raw_text),
    }
