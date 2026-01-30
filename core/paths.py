"""Path management for VideoVerse pipeline."""
from pathlib import Path

from core.config import get_settings

settings = get_settings()


class PathManager:
    """Manages all file paths for the pipeline."""

    def __init__(self, base_dir: Path | None = None):
        self._base_dir = base_dir or Path.cwd()
        self._output_dir = None

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    @property
    def output_dir(self) -> Path:
        if self._output_dir is None:
            custom_path = settings.output_dir
            # If custom_path is absolute, use it; otherwise make it relative to base_dir
            if custom_path and Path(custom_path).is_absolute():
                self._output_dir = Path(custom_path)
            else:
                self._output_dir = self._base_dir / (custom_path or "output")
        return self._output_dir

    @property
    def models_dir(self) -> Path:
        return Path(settings.model_cache_dir)

    @property
    def temp_dir(self) -> Path:
        return Path(settings.temp_dir)

    @property
    def audio_dir(self) -> Path:
        return self.output_dir / "audio"

    @property
    def log_dir(self) -> Path:
        return self.output_dir / "log"

    @property
    def audio_refers_dir(self) -> Path:
        return self.audio_dir / "refers"

    @property
    def audio_segs_dir(self) -> Path:
        return self.audio_dir / "segs"

    @property
    def audio_tmp_dir(self) -> Path:
        return self.audio_dir / "tmp"

    # Output files
    @property
    def cleaned_chunks(self) -> Path:
        return self.log_dir / "cleaned_chunks.xlsx"

    @property
    def split_by_nlp(self) -> Path:
        return self.log_dir / "split_by_nlp.txt"

    @property
    def split_by_meaning(self) -> Path:
        return self.log_dir / "split_by_meaning.txt"

    @property
    def terminology(self) -> Path:
        return self.log_dir / "terminology.json"

    @property
    def translation_results(self) -> Path:
        return self.log_dir / "translation_results.xlsx"

    @property
    def translation_for_subtitles(self) -> Path:
        return self.log_dir / "translation_for_subtitles.xlsx"

    @property
    def raw_audio_file(self) -> Path:
        return self.audio_dir / "raw.mp3"

    @property
    def vocal_audio_file(self) -> Path:
        return self.audio_dir / "vocal.mp3"

    @property
    def output_video_with_sub(self) -> Path:
        return self.output_dir / "output_with_subtitles.mp4"

    @property
    def output_video_dubbed(self) -> Path:
        return self.output_dir / "output_dubbed.mp4"

    def ensure_directories(self) -> None:
        """Create all necessary directories."""
        dirs = [
            self.output_dir,
            self.audio_dir,
            self.log_dir,
            self.audio_refers_dir,
            self.audio_segs_dir,
            self.audio_tmp_dir,
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)


# Global instance
paths = PathManager()
