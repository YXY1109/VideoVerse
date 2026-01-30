"""Step 03: NLP Split.

使用 Spacy/jieba 对文本进行语言学分割。
从 temp/steps/step_03_nlp_split.py 迁移并转换为 PipelineStep。
"""

import asyncio
import pandas as pd
from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext
from tools import spacy_utils

settings = get_settings()


class NLPSplitStep(PipelineStep):
    """NLP 句子分割步骤 - PipelineStep 实现。

    使用 Spacy（或中文使用 jieba）对文本进行语言学分割。
    """

    @property
    def name(self) -> str:
        return "step_03_nlp_split"

    @property
    def dependencies(self) -> list[str]:
        return ["step_02_asr"]

    async def validate(self, context: PipelineContext) -> bool:
        """验证 ASR 结果是否存在。"""
        asr_result = context.get("asr_result")
        if not asr_result:
            logger.error("No asr_result in context")
            return False
        return True

    async def execute(self, context: PipelineContext) -> str:
        """执行 NLP 分割。

        Args:
            context: 流水线上下文

        Returns:
            分割结果文件路径
        """
        logger.info("Starting NLP split")

        # 读取转录文件
        asr_result = context.get("asr_result")
        df = pd.read_excel(asr_result)
        sentences = df['text'].str.strip('"').str.strip().tolist()

        # 写入到 split_by_meaning.txt（中间文件）
        paths.split_by_meaning.parent.mkdir(parents=True, exist_ok=True)
        with open(paths.split_by_meaning, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sentences))

        # 使用 asyncio.to_thread 执行同步的 NLP 分割
        source_language = context.source_language
        await asyncio.to_thread(self._split_by_nlp_sync, asr_result, source_language)

        logger.info(f"NLP split complete: {paths.split_by_nlp}")
        context.set("nlp_split_result", str(paths.split_by_nlp))
        return str(paths.split_by_nlp)

    def _split_by_nlp_sync(self, transcript_file: str, source_language: str) -> None:
        """同步 NLP 分割。"""
        # 根据语言自动选择 Spacy 或 jieba 进行 NLP 分割
        if source_language == 'zh' and spacy_utils.JIEBA_AVAILABLE:
            self._split_by_jieba_sync()
        else:
            self._split_by_spacy_sync()

    def _split_by_spacy_sync(self) -> None:
        """使用 Spacy 进行 NLP 分割。"""
        nlp = spacy_utils.init_nlp()
        spacy_utils.split_by_mark(nlp)
        spacy_utils.split_by_comma_main(nlp)
        spacy_utils.split_sentences_main(nlp)
        spacy_utils.split_long_by_root_main(nlp)

    def _split_by_jieba_sync(self) -> None:
        """使用 jieba 进行中文 NLP 分割。"""
        logger.info("Using jieba for Chinese text splitting")
        spacy_utils.split_by_mark_jieba()
        spacy_utils.split_by_comma_jieba_main()
        spacy_utils.split_sentences_jieba_main()
        spacy_utils.split_long_by_root_jieba_main()


def create_step() -> NLPSplitStep:
    """工厂函数：创建 NLP 分割步骤。"""
    return NLPSplitStep()


__all__ = ["NLPSplitStep", "create_step"]
