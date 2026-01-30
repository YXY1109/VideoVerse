"""Step 06: Translate.

使用 LLM 进行多步翻译（直译 → 反思 → 意译）。
从 temp/steps/step_06_translate.py 迁移并转换为 PipelineStep（简化版）。
"""

import json
from difflib import SequenceMatcher
from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext
from tools.translate_lines import translate_lines

settings = get_settings()


def similar(a: str, b: str) -> float:
    """计算两个字符串的相似度。"""
    return SequenceMatcher(None, a, b).ratio()


def split_chunks_by_chars(chunk_size: int, max_i: int, split_file: str) -> list:
    """根据字符数分割文本块。"""
    with open(split_file, "r", encoding="utf-8") as file:
        sentences = file.read().strip().split('\n')

    chunks = []
    chunk = ''
    sentence_count = 0
    for sentence in sentences:
        if len(chunk) + len(sentence + '\n') > chunk_size or sentence_count == max_i:
            if chunk.strip():
                chunks.append(chunk.strip())
            chunk = sentence + '\n'
            sentence_count = 1
        else:
            chunk += sentence + '\n'
            sentence_count += 1
    if chunk.strip():
        chunks.append(chunk.strip())
    return chunks


class TranslateStep(PipelineStep):
    """翻译步骤 - PipelineStep 实现。

    使用 LLM 进行多步翻译（直译 → 可选的意译）。
    """

    @property
    def name(self) -> str:
        return "step_06_translate"

    @property
    def dependencies(self) -> list[str]:
        return ["step_05_summarize"]

    async def validate(self, context: PipelineContext) -> bool:
        """验证语义分割结果是否存在。"""
        meaning_split_result = context.get("meaning_split_result")
        if not meaning_split_result:
            logger.error("No meaning_split_result in context")
            return False
        return True

    async def execute(self, context: PipelineContext) -> str:
        """执行翻译。

        Args:
            context: 流水线上下文

        Returns:
            翻译结果文件路径
        """
        logger.info("Starting translation")

        # 获取文件路径
        split_file = context.get("meaning_split_result")
        terminology_file = context.get("terminology")
        target_language = context.target_language

        # 分割文本块
        chunks = split_chunks_by_chars(chunk_size=600, max_i=10, split_file=split_file)

        # 读取术语表
        with open(terminology_file, 'r', encoding='utf-8') as f:
            terminology_data = json.load(f)
        theme_prompt = terminology_data.get('theme', '')
        terminology_terms = terminology_data.get('terms', [])

        # 翻译每个文本块
        logger.info(f"Translating {len(chunks)} chunks...")
        src_text, trans_text = [], []

        for i, chunk in enumerate(chunks):
            # 获取上下文
            previous_content = self._get_previous_content(chunks, i)
            after_content = self._get_after_content(chunks, i)
            things_to_note = self._search_things_to_note_in_prompt(chunk, terminology_terms)

            # 翻译
            translation, original = translate_lines(
                chunk,
                previous_content,
                after_content,
                things_to_note,
                theme_prompt,
                src_language=context.source_language,
                target_language=target_language,
                index=i,
            )

            chunk_lines = chunk.split('\n')
            src_text.extend(chunk_lines)
            trans_text.extend(translation.split('\n'))

        # 保存翻译结果
        import pandas as pd
        df_final = pd.DataFrame({'Source': src_text, 'Translation': trans_text})
        df_final.to_excel(paths.translation_results, index=False)

        logger.info(f"Translation results saved to: {paths.translation_results}")
        context.set("translation_result", str(paths.translation_results))
        return str(paths.translation_results)

    def _get_previous_content(self, chunks: list, chunk_index: int) -> str | None:
        """获取前文内容。"""
        if chunk_index == 0:
            return None
        return '\n'.join(chunks[chunk_index - 1].split('\n')[-3:])

    def _get_after_content(self, chunks: list, chunk_index: int) -> str | None:
        """获取后文内容。"""
        if chunk_index == len(chunks) - 1:
            return None
        return '\n'.join(chunks[chunk_index + 1].split('\n')[:2])

    def _search_things_to_note_in_prompt(self, chunk: str, terms: list) -> str | None:
        """搜索需要注意的术语。"""
        chunk_lower = chunk.lower()
        matching_terms = [t for t in terms if t['src'].lower() in chunk_lower]
        if matching_terms:
            lines = [
                f'{i + 1}. "{term["src"]}": "{term["tgt"]}", meaning: {term["note"]}'
                for i, term in enumerate(matching_terms)
            ]
            return '\n'.join(lines)
        return None


def create_step() -> TranslateStep:
    """工厂函数：创建翻译步骤。"""
    return TranslateStep()


__all__ = ["TranslateStep", "create_step"]
