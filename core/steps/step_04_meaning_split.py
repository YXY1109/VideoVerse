"""Step 04: Meaning Split.

使用 LLM 对长句进行语义分割。
从 temp/steps/step_04_meaning_split.py 迁移并转换为 PipelineStep。
"""

import asyncio
import math
from difflib import SequenceMatcher
from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext
from core.utils.llm import ask_llm
from core.utils.common import get_joiner
from tools.prompts import get_split_prompt
from tools import spacy_utils

settings = get_settings()

# 尝试导入 jieba
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False


class MeaningSplitStep(PipelineStep):
    """AI 语义分割步骤 - PipelineStep 实现。

    使用 LLM 对长句进行语义分割。
    """

    @property
    def name(self) -> str:
        return "step_04_meaning_split"

    @property
    def dependencies(self) -> list[str]:
        return ["step_03_nlp_split"]

    async def validate(self, context: PipelineContext) -> bool:
        """验证 NLP 分割结果是否存在。"""
        nlp_split_result = context.get("nlp_split_result")
        if not nlp_split_result:
            logger.error("No nlp_split_result in context")
            return False
        return True

    async def execute(self, context: PipelineContext) -> str:
        """执行 AI 语义分割。

        Args:
            context: 流水线上下文

        Returns:
            分割结果文件路径
        """
        logger.info("Starting meaning split with AI")

        nlp_split_file = context.get("nlp_split_result")
        source_language = context.source_language

        # 读取输入句子
        with open(nlp_split_file, 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f.readlines()]

        # 检测语言，中文使用 jieba 进行 tokenization
        use_jieba = (source_language == 'zh' and JIEBA_AVAILABLE)

        if use_jieba:
            logger.info('Using jieba for Chinese tokenization in meaning split')
            nlp = None
        else:
            nlp = await asyncio.to_thread(spacy_utils.init_nlp)

        # 处理句子多次以确保所有句子都被分割
        for retry_attempt in range(3):
            sentences = await self._parallel_split_sentences(
                sentences,
                nlp=nlp,
                use_jieba=use_jieba,
                retry_attempt=retry_attempt
            )

        # 保存结果
        paths.split_by_meaning.parent.mkdir(parents=True, exist_ok=True)
        with open(paths.split_by_meaning, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sentences))

        logger.info(f"All sentences have been successfully split: {paths.split_by_meaning}")
        context.set("meaning_split_result", str(paths.split_by_meaning))
        return str(paths.split_by_meaning)

    async def _parallel_split_sentences(
        self,
        sentences: list,
        nlp: object | None,
        use_jieba: bool,
        retry_attempt: int = 0
    ) -> list:
        """并行分割句子。"""
        new_sentences = [None] * len(sentences)
        futures = []
        language = settings.whisper_language
        max_length = settings.max_split_length

        # 创建任务
        for index, sentence in enumerate(sentences):
            if language == 'zh':
                sentence_length = len(sentence)
            else:
                if use_jieba:
                    tokens = list(jieba.cut(sentence))
                else:
                    doc = nlp(sentence)
                    tokens = [token.text for token in doc]
                sentence_length = len(tokens)

            num_parts = math.ceil(sentence_length / max_length)
            if sentence_length > max_length:
                future = asyncio.create_task(
                    self._split_sentence(sentence, num_parts, max_length, index=index, retry_attempt=retry_attempt)
                )
                futures.append((future, index))
            else:
                new_sentences[index] = [sentence]

        # 等待所有任务完成
        for future, index in futures:
            split_result = await future
            if split_result:
                split_lines = split_result.strip().split('\n')
                new_sentences[index] = [line.strip() for line in split_lines]
            else:
                new_sentences[index] = [sentences[index]]

        return [sentence for sublist in new_sentences for sentence in sublist]

    async def _split_sentence(
        self,
        sentence: str,
        num_parts: int,
        word_limit: int,
        index: int = -1,
        retry_attempt: int = 0
    ) -> str:
        """分割长句。"""
        split_prompt = get_split_prompt(sentence, num_parts, word_limit, settings.whisper_language)

        def valid_split(response_data):
            choice = response_data.get("choice", "1")
            if f'split{choice}' not in response_data:
                return {"status": "error", "message": "Missing required key: `split`"}

            split_result = response_data.get(f"split{choice}", "")
            if "[br]" not in split_result:
                return {"status": "error", "message": "Split failed, no [br] found"}

            return {"status": "success", "message": "Split completed"}

        response_data = await ask_llm(
            split_prompt + " " * retry_attempt,
            log_title='split_by_meaning'
        )

        choice = response_data.get("choice", "1")
        best_split = response_data.get(f"split{choice}", "")
        split_points = self._find_split_positions(sentence, best_split)

        if not split_points:
            logger.warning(f"No valid split points found for sentence {index}, returning original")
            return sentence

        # 分割句子
        parts = []
        start = 0
        for split_point in split_points:
            parts.append(sentence[start:split_point])
            start = split_point
        parts.append(sentence[start:])

        if index != -1:
            logger.info(f'Sentence {index} has been successfully split into {len(split_points) + 1} parts')

        return '\n'.join(parts)

    def _find_split_positions(self, original: str, modified: str) -> list:
        """找到分割位置。"""
        split_positions = []
        parts = modified.split('[br]')
        start = 0
        language = settings.whisper_language
        joiner = get_joiner(language)

        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) <= 1:
            return []

        for i in range(len(parts) - 1):
            current_part = parts[i]

            max_similarity = 0
            best_split = None

            for j in range(start + min(3, len(original) - start), len(original)):
                original_left = original[start:j]

                if language == 'zh':
                    modified_left = current_part
                else:
                    modified_left = joiner.join(current_part.split())

                left_similarity = SequenceMatcher(None, original_left, modified_left).ratio()

                if left_similarity > max_similarity:
                    max_similarity = left_similarity
                    best_split = j

                if left_similarity >= 0.95:
                    break

            if max_similarity >= 0.7 and best_split is not None:
                split_positions.append(best_split)
                start = best_split

        return split_positions


def create_step() -> MeaningSplitStep:
    """工厂函数：创建语义分割步骤。"""
    return MeaningSplitStep()


__all__ = ["MeaningSplitStep", "create_step"]
