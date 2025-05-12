# utils.py
import tempfile, shutil
from pathlib import Path
import streamlit as st
import uuid, os, mido

def get_session_dirs():
    if "dirs" not in st.session_state:
        root = Path(tempfile.mkdtemp(prefix="session_"))
        dirs = {
            "orig_midi": root / "orig" / "midis",
            "orig_wav":  root / "orig" / "wavs",
            "gen_midi":  root / "gen" / "midis",
            "gen_wav":   root / "gen" / "wavs",
            "root":      root
        }
        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)
        st.session_state.dirs = dirs
    return st.session_state.dirs

def clear_session():
    dirs = st.session_state.get("dirs")
    if dirs:
        shutil.rmtree(dirs["root"], ignore_errors=True)
    # clear all Streamlit state
    for key in list(st.session_state.keys()):
        del st.session_state[key]



def make_blank_midi(out_dir: str, tempo_bpm: int = 120) -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{uuid.uuid4()}.mid")

    mid   = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("set_tempo",
                                  tempo=mido.bpm2tempo(tempo_bpm),
                                  time=0))
    mid.tracks.append(track)
    mid.save(path)
    return path
 