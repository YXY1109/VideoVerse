"""Step 02: ASR - Automatic Speech Recognition."""
from pathlib import Path

from loguru import logger

from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext


class ASRStep(PipelineStep):
    """ASR processing step - transcribes audio to text."""

    def __init__(self, use_demucs: bool = True):
        self._use_demucs = use_demucs

    @property
    def name(self) -> str:
        return "step_02_asr"

    @property
    def dependencies(self) -> list[str]:
        return ["step_01_download"]

    async def validate(self, context: PipelineContext) -> bool:
        """Validate video file exists."""
        video_path = context.get("video_path")
        if not video_path:
            logger.error("No video_path in context")
            return False
        return Path(video_path).exists()

    async def execute(self, context: PipelineContext) -> str:
        """
        Execute ASR processing.

        Returns:
            Path to output Excel file with transcription results
        """
        video_path = context.get("video_path")

        logger.info(f"Starting ASR processing: {video_path}")

        # Import ASR functions here to avoid circular imports
        from core.asr.common import save_results
        from core.asr.demucs_local import demucs_audio
        from core.asr.ffmpeg_local import ffmpeg_video_to_audio
        from core.asr.pydub_local import normalize_audio_volume, split_audio
        from core.asr.whisperx_local import transcribe_audio
        from core.paths import paths

        # 2.1: Extract audio
        mp3_path = ffmpeg_video_to_audio(video_path)
        logger.info(f"Audio extracted: {mp3_path}")

        # 2.2: Separate vocals (optional)
        if self._use_demucs:
            vocal_audio = demucs_audio(mp3_path)
        else:
            vocal_audio = mp3_path

        # 2.3: Normalize audio
        vocal_normalized = normalize_audio_volume(vocal_audio)

        # 2.4: Split audio into segments
        segments = split_audio(vocal_normalized)
        logger.info(f"Audio split into {len(segments)} segments")

        # 2.5: Transcribe each segment
        all_results = []
        for start, end in segments:
            result = transcribe_audio(vocal_normalized, vocal_audio, start, end)
            all_results.append(result)

        # 2.6: Merge results
        combined_result = {"segments": []}
        for result in all_results:
            combined_result["segments"].extend(result["segments"])

        # 2.7: Process and save
        from core.asr.common import process_transcription
        df = process_transcription(combined_result)

        output_path = paths.cleaned_chunks
        df = save_results(df, str(output_path))

        # Store results in context
        context.set("asr_result", str(output_path))
        context.set("asr_dataframe", df)

        logger.success(f"ASR processing complete: {output_path}")
        return str(output_path)


def create_step(use_demucs: bool = True) -> ASRStep:
    """Factory function for ASR step."""
    return ASRStep(use_demucs=use_demucs)
