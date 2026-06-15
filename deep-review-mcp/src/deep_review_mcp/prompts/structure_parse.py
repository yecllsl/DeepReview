STRUCTURE_PARSE_PROMPT = """你是一位K12教育领域的题目结构化专家。请将以下OCR识别出的题目文本解析为结构化数据。

OCR原始文本：
{raw_text}

请按以下JSON格式输出（不要输出其他内容）：
{{
    "subject": "学科（语文/数学/英语/物理/化学/生物/政治/历史/地理）",
    "grade_level": "年级段（小学/初一/初二/初三/高一/高二/高三）",
    "knowledge_points": ["知识点1", "知识点2"],
    "difficulty": "难度（基础/中等/困难）",
    "question_type": "题型（选择题/填空题/计算题/证明题/应用题/其他）",
    "question_content": "题目内容（修正OCR错误后的完整题目）",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "correct_answer": "正确答案（如果能推断出）"
}}

注意事项：
1. 修正OCR识别中的明显错误（如乱码、错别字）
2. 数学公式用LaTeX格式表示
3. 如果无法确定某个字段，填null
4. knowledge_points必须从该学科的标准知识点中选择
"""
