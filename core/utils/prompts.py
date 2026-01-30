"""AI Prompt 模板模块（core 版本）。

从 temp/tools/prompts.py 迁移，提供各种 AI 任务所需的 prompt 模板。
注意：更完整的版本在 tools/prompts.py 中。
"""

import json


def get_split_prompt(
    sentence: str,
    num_parts: int = 2,
    word_limit: int = 20,
    language: str = "zh",
) -> str:
    """生成语义分割 prompt。

    Args:
        sentence: 待分割的句子
        num_parts: 分割成几部分
        word_limit: 每部分的词/字数限制
        language: 语言代码 (如 "zh", "en")

    Returns:
        分割 prompt 字符串
    """
    # 根据语言设置不同的字数/词数限制说明
    if language == "zh":
        length_unit = "字（characters）"
        min_length = "8"
        max_allowed = word_limit
        split_instruction = f"""
**CRITICAL FOR CHINESE**: Split into meaningful phrases (NOT single characters)!
- Each part MUST be {max_allowed} characters or LESS - this is a HARD LIMIT
- Ideal length: 10-18 characters per part
- Minimum: 8 characters per part
- Split at natural boundaries: after punctuation, after complete phrases, or at semantic breaks
"""
    else:
        length_unit = "words"
        min_length = "3"
        max_allowed = word_limit
        split_instruction = f"""
- Each part MUST be {max_allowed} words or LESS - this is a HARD LIMIT
- Minimum: 3 words per part
- Split at natural boundaries: punctuation marks, conjunctions, or complete phrases
"""

    split_prompt = f"""## Role
You are a professional Netflix subtitle splitter in **{language}**.

## Task
Split the given subtitle text into **{num_parts}** parts, each less than **{word_limit}** {length_unit}.

1. Maintain sentence meaning coherence according to Netflix subtitle standards
2. MOST IMPORTANT: Keep parts roughly equal in length (minimum {min_length} {length_unit} each)
3. Split at natural points like punctuation marks or conjunctions
{split_instruction}
4. If provided text is repeated words, simply split at the middle of the repeated words

## Given Text
<split_this_sentence>
{sentence}
</split_this_sentence>

## Output in only JSON format and no other text
```json
{{
    "analysis": "Brief analysis of sentence structure and split strategy",
    "split1": "First splitting approach with [br] tags at split positions",
    "split2": "Alternative splitting approach with [br] tags at split positions",
    "assess": "Comparison of both approaches",
    "choice": "1 or 2"
}}
```

Note: Start you answer with ```json and end with ```, do not add any other text."""
    return split_prompt


def get_summary_prompt(
    source_content: str,
    src_lang: str = "zh",
    tgt_lang: str = "en",
    custom_terms_json: dict | None = None,
) -> str:
    """生成摘要和术语提取 prompt。

    Args:
        source_content: 源文本内容
        src_lang: 源语言代码
        tgt_lang: 目标语言代码
        custom_terms_json: 自定义术语（可选）

    Returns:
        摘要 prompt 字符串
    """
    terms_note = ""
    if custom_terms_json:
        terms_list = []
        for term in custom_terms_json.get("terms", []):
            terms_list.append(f"- {term['src']}: {term['tgt']} ({term['note']})")
        terms_note = "\n### Existing Terms\nPlease exclude these terms in your extraction:\n" + "\n".join(terms_list)

    summary_prompt = f"""
## Role
You are a video translation expert and terminology consultant, specializing in {src_lang}
comprehension and {tgt_lang} expression optimization.

## Task
For the provided {src_lang} video text:
1. Summarize main topic in two sentences
2. Extract professional terms/names with {tgt_lang} translations (excluding existing terms)
3. Provide brief explanation for each term

{terms_note}

## INPUT
<text>
{source_content}
</text>

## Output in only JSON format and no other text
{{
  "theme": "Two-sentence video summary",
  "terms": [
    {{
      "src": "{src_lang} term",
      "tgt": "{tgt_lang} translation or original",
      "note": "Brief explanation"
    }},
    ...
  ]
}}

Note: Start you answer with ```json and end with ```, do not add any other text.
""".strip()
    return summary_prompt


__all__ = ["get_split_prompt", "get_summary_prompt"]
