from streamlit.testing.v1 import AppTest
from unittest.mock import MagicMock
import pytest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import *
from midi_processor import *



# Fixtures allow to setup and teardown resources needed for the tests
@pytest.fixture
def mock_processor():
    # This method mocks all functions called by the midi processor:
    # turning the blob into a path for a MIDI file, and converting the MIDI to an audio file (.wav)
    processor = MagicMock()
    processor.blob_to_midifile.return_value = "mocked_orig.mid" # mock blob_to_midifile to return a path for a midifile
    processor.midi_to_audio.side_effect = lambda midi_path, out_path: f"{out_path}_audio.wav"
    return processor


@pytest.fixture
def mock_dirs():
    return {
        "orig_midi": Path("mock/orig/midi"),
        "orig_wav": Path("mock/orig/wav"),
        "gen_midi": Path("mock/gen/midi"),
        "gen_wav": Path("mock/gen/wav")
    }


@pytest.fixture
def service(mock_processor, mock_dirs):
    mock_model = MagicMock()  # Replace with real or mock model if needed
    return MidiProcessingService(mock_model, mock_processor, mock_dirs)


def test_process_item_success(service, mock_processor):
    # Arrange
    item = {"id": "test123", "blob": b"fake midi blob"}

    # Act
    result = service.process_item(item, temperature=1.0)

    # Assert
    mock_processor.blob_to_midifile.assert_called_once_with(item["blob"], Path("mock/orig/midi"))
    assert mock_processor.midi_to_audio.call_count == 2
    mock_processor.infer_continuation.assert_called_once_with("mocked_orig.mid", "mock\\gen\\midi\\test123.mid", temperature=1.0)

    assert result["id"] == "test123"
    assert result["orig"].endswith("mock\\orig\\wav\\test123.wav_audio.wav")
    assert result["gen"].endswith("mock\\gen\\wav\\test123.wav_audio.wav")
    assert result["orig_mid"] == "mocked_orig.mid"
    assert result["gen_mid"] == "mock\\gen\\midi\\test123.mid"


def test_process_item_inference_failure(service, mock_processor):
    # Arrange
    item = {"id": "failcase", "blob": b"fake midi blob"}
    mock_processor.infer_continuation.side_effect = Exception("Model error")

    # Act & Assert
    with pytest.raises(RuntimeError, match="AI generation failed: Model error"):
        service.process_item(item, temperature=1.0)

    mock_processor.blob_to_midifile.assert_called_once_with(item["blob"], Path("mock/orig/midi"))
