# services.py

import os
import shutil
from queue import Queue
import streamlit as st
from midi_processor import MidiProcessor
from utils import get_session_dirs, make_blank_midi


def safe_audio(path: str):
    """Safely play or offer download of audio files based on size."""
    if not os.path.isfile(path):
        st.error("File missing: " + path)
        return
    if os.path.getsize(path) > 50_000_000:
        st.warning("Audio too large to preview – download below.")
        with open(path, "rb") as f:
            st.download_button("Download WAV", f, file_name=os.path.basename(path))
    else:
        st.audio(path, format="audio/wav")


class MidiProcessingService:
    def __init__(self, model, processor, dirs):
        self.model = model
        self.processor = processor
        self.dirs = dirs
        self._lock = Queue()  # Dummy lock for serial access if needed

    def process_item(self, item, temperature=1.0):
        mid_id = item["id"]
        orig_mid = self.processor.blob_to_midifile(item["blob"], self.dirs["orig_midi"])
        orig_wav = self.processor.midi_to_audio(orig_mid, str(self.dirs["orig_wav"] / f"{mid_id}.wav"))
        gen_mid_path = str(self.dirs["gen_midi"] / f"{mid_id}.mid")
        self.processor.infer_continuation(orig_mid, gen_mid_path, temperature=temperature)
        gen_wav = self.processor.midi_to_audio(gen_mid_path, str(self.dirs["gen_wav"] / f"{mid_id}.wav"))
        return {"id": mid_id, "orig": orig_wav, "gen": gen_wav, "orig_mid": orig_mid, "gen_mid": gen_mid_path}


class SessionStateService:
    def __init__(self, session_state):
        self.session_state = session_state

    def initialize(self, server, queue):
        self.session_state.setdefault("midi_queue", queue)
        self.session_state.setdefault("server", server)
        self.session_state.setdefault("history", [])
        self.session_state.setdefault("busy", False)

    def clear_all(self, processor):
        with self.session_state.midi_queue.mutex:
            self.session_state.midi_queue.queue.clear()
        processor._ids_buf = []
        self.session_state.history.clear()
        if "dirs" in self.session_state:
            root = self.session_state.dirs["root"]
            shutil.rmtree(root, ignore_errors=True)
            self.session_state.dirs = get_session_dirs()

    def add_to_history(self, item):
        self.session_state.history.append(item)

    def get_history(self):
        return self.session_state.history

    def set_busy(self, value):
        self.session_state.busy = value

    def is_busy(self):
        return self.session_state.busy

    def has_pending_items(self):
        return not self.session_state.midi_queue.empty()


def handle_midi_queue(state_service, processing_service, temperature):
    if state_service.is_busy() or not state_service.has_pending_items():
        return
    state_service.set_busy(True)
    try:
        itm = state_service.session_state.midi_queue.get_nowait()
        res = processing_service.process_item(itm, temperature)
        state_service.add_to_history(res)
    except Exception as exc:
        st.error(f"Processing error: {exc}")
    finally:
        state_service.set_busy(False)
