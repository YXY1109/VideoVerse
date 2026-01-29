"""Test PathManager functionality."""
import pytest
import tempfile
from pathlib import Path
from core.paths import PathManager, paths


def test_path_manager_output_dir():
    """Test output directory property."""
    manager = PathManager()
    output_dir = manager.output_dir
    assert isinstance(output_dir, Path)
    assert str(output_dir).endswith("output")


def test_path_manager_models_dir():
    """Test models directory uses configuration."""
    manager = PathManager()
    models_dir = manager.models_dir
    assert isinstance(models_dir, Path)


@pytest.mark.unit
def test_ensure_directories():
    """Test directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_base = Path(tmpdir) / "test_base"
        test_base.mkdir()

        manager = PathManager(base_dir=test_base)
        manager.ensure_directories()
        assert (test_base / "output").exists()
        assert (test_base / "output" / "audio").exists()
        assert (test_base / "output" / "log").exists()


def test_global_paths_instance():
    """Test global paths instance is available."""
    from core.paths import paths
    assert paths is not None
    assert hasattr(paths, 'output_dir')


def test_audio_properties():
    """Test audio-related path properties."""
    manager = PathManager()
    assert manager.audio_dir.name == "audio"
    assert manager.audio_refers_dir.name == "refers"
    assert manager.audio_segs_dir.name == "segs"


def test_log_properties():
    """Test log-related path properties."""
    manager = PathManager()
    assert manager.log_dir.name == "log"


def test_output_file_paths():
    """Test output file path properties."""
    manager = PathManager()
    assert manager.cleaned_chunks.name == "cleaned_chunks.xlsx"
    assert manager.split_by_nlp.name == "split_by_nlp.txt"
    assert manager.split_by_meaning.name == "split_by_meaning.txt"
    assert manager.terminology.name == "terminology.json"
