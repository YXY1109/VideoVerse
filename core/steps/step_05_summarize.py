"""Step 05: Summarize.

提取视频内容的摘要和术语表。
从 temp/steps/step_05_summarize.py 迁移并转换为 PipelineStep。
"""

import asyncio
import json
from pathlib import Path

import pandas as pd
from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext
from core.utils.llm import ask_llm
from tools.prompts import get_summary_prompt

settings = get_settings()

CUSTOM_TERMS_PATH = 'custom_terms.xlsx'


class SummarizeStep(PipelineStep):
    """内容摘要和术语提取步骤 - PipelineStep 实现。

    提取视频内容的摘要和术语表。
    """

    @property
    def name(self) -> str:
        return "step_05_summarize"

    @property
    def dependencies(self) -> list[str]:
        return ["step_04_meaning_split"]

    async def validate(self, context: PipelineContext) -> bool:
        """验证语义分割结果是否存在。"""
        meaning_split_result = context.get("meaning_split_result")
        if not meaning_split_result:
            logger.error("No meaning_split_result in context")
            return False
        return True

    async def execute(self, context: PipelineContext) -> str:
        """执行摘要和术语提取。

        Args:
            context: 流水线上下文

        Returns:
            术语表文件路径
        """
        logger.info("Starting summarization")

        # 合并文本块
        src_content = await asyncio.to_thread(self._combine_chunks_sync)

        # 加载自定义术语
        custom_terms_json = await asyncio.to_thread(self._load_custom_terms_sync)

        # 生成摘要 prompt
        src_language = context.source_language
        target_language = context.target_language
        summary_prompt = get_summary_prompt(src_content, src_language, target_language, custom_terms_json)
        logger.info("Summarizing and extracting terminology ...")

        def valid_summary(response_data):
            required_keys = {'src', 'tgt', 'note'}
            if 'terms' not in response_data:
                return {"status": "error", "message": "Invalid response format"}
            for term in response_data['terms']:
                if not all(key in term for key in required_keys):
                    return {"status": "error", "message": "Invalid response format"}
            return {"status": "success", "message": "Summary completed"}

        summary = await ask_llm(summary_prompt, log_title='summary')

        # 合并自定义术语
        if 'terms' not in summary:
            summary['terms'] = []
        summary['terms'].extend(custom_terms_json['terms'])

        # 保存术语表
        paths.terminology.parent.mkdir(parents=True, exist_ok=True)
        with open(paths.terminology, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)

        logger.info(f"Summary log saved to: {paths.terminology}")
        context.set("terminology", str(paths.terminology))
        context.set("summary", summary)
        return str(paths.terminology)

    def _combine_chunks_sync(self) -> str:
        """合并文本块为单一长文本。"""
        with open(paths.split_by_meaning, 'r', encoding='utf-8') as file:
            sentences = file.readlines()
        cleaned_sentences = [line.strip() for line in sentences]
        combined_text = ' '.join(cleaned_sentences)
        summary_length = settings.summary_length
        return combined_text[:summary_length]

    def _load_custom_terms_sync(self) -> dict:
        """加载自定义术语表。"""
        custom_terms_json = {"terms": []}
        if Path(CUSTOM_TERMS_PATH).exists():
            try:
                custom_terms = pd.read_excel(CUSTOM_TERMS_PATH)
                if len(custom_terms) > 0:
                    custom_terms_json = {
                        "terms": [
                            {
                                "src": str(row.iloc[0]),
                                "tgt": str(row.iloc[1]),
                                "note": str(row.iloc[2])
                            }
                            for _, row in custom_terms.iterrows()
                        ]
                    }
                    logger.info(f"Custom Terms Loaded: {len(custom_terms)} terms")
            except Exception as e:
                logger.warning(f"Failed to load custom terms: {e}")
        return custom_terms_json


def create_step() -> SummarizeStep:
    """工厂函数：创建摘要步骤。"""
    return SummarizeStep()


__all__ = ["SummarizeStep", "create_step"]
