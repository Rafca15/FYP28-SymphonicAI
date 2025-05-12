import os
import base64
import uuid
import subprocess
import threading
import traceback
import streamlit as st

from config import CONFIG                 
from processor import encode_midi, decode_midi


# ────────────────────────── helpers ──────────────────────────
def synchronized(fn):
    """Decorator: run method bodies under a per-instance lock."""
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return fn(self, *args, **kwargs)
    return wrapper


# ─────────────────────────── class ───────────────────────────
class MidiProcessor:
    """
    Thread-safe utilities to:
      • convert a MIDI browser upload → tokens
      • feed tokens to the language model
      • convert generated tokens → MIDI → WAV
    """

    def __init__(self, soundfont_path: str, model):
        self.sf2 = soundfont_path
        self.model = model
        self._lock = threading.Lock()
        self._ids_buf: list[int] = [CONFIG["token_sos"], CONFIG["token_eos"]]         

    # ---------- low-level I/O --------------------------------------------------

    @synchronized
    def blob_to_midifile(self, blob_b64: str, out_dir: str) -> str:
        os.makedirs(out_dir, exist_ok=True)
        data = base64.b64decode(blob_b64)
        path = os.path.join(out_dir, f"{uuid.uuid4()}.mid")
        with open(path, "wb") as f:
            f.write(data)
        return path

    @synchronized
    def midi_to_audio(self, midi_path: str, out_wav_path: str) -> str:
        """Render MIDI to WAV with Fluidsynth (blocking call)."""
        os.makedirs(os.path.dirname(out_wav_path), exist_ok=True)
        cmd = [
            "fluidsynth", "-n", "-i",
            "-a", "file", "-F", out_wav_path,
            "-r", "44100",
            self.sf2,
            midi_path,
        ]
        subprocess.run(cmd, check=True)
        return out_wav_path

    # --------------------------- generation -----------------------------------------------------

    @synchronized
    def infer_continuation(
        self,
        midi_path: str,
        out_mid_path: str,
        length: int = 20,
        temperature: float = 1.0,
    ) -> str:
        
        try:
            ids = encode_midi(midi_path)
            st.info(f"Prompt tokens: {len(ids)}")
        except Exception:
            st.error("Failed to encode MIDI - see console for details.")
            traceback.print_exc()
            raise

        
        ctx = CONFIG.get("block_size", 512)
        prompt_ids = (self._ids_buf[:-1] + ids[1:])[-ctx:]       

        
        try:
            gen_ids = (
                self.model.generate(
                    idx=prompt_ids,
                    max_new_tokens=length,
                    eos_token_id=CONFIG["token_eos"],
                    temperature=temperature,
                )
                .tolist()[0]
            )
            print(len(gen_ids))
        except Exception:
            st.error("Model generation failed – see console for details.")
            traceback.print_exc()
            raise

        
        try:
            self._ids_buf = (prompt_ids + gen_ids)[-ctx:]  
            os.makedirs(os.path.dirname(out_mid_path), exist_ok=True)
            decode_midi(prompt_ids + gen_ids, out_mid_path)
        except Exception:
            st.error("Failed to write generated MIDI – see console for details.")
            traceback.print_exc()
            raise

        if not os.path.isfile(out_mid_path):
            raise RuntimeError(f"Generated MIDI not found: {out_mid_path}")
        return out_mid_path
