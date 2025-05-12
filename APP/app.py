# app.py

import streamlit as st
from queue import Queue
import uuid, base64
from io import BytesIO
import zipfile

from server import start_server
from model_loader import load_model
from utils import get_session_dirs, make_blank_midi
from config import HTTP_HOST, HTTP_PORT, SF2_PATH, BROWSER_APP_URL
from streamlit_autorefresh import st_autorefresh
from midi_processor import MidiProcessor
from services import (
    MidiProcessingService,
    SessionStateService,
    handle_midi_queue,
    safe_audio
)


# ──────────────────── Setup ────────────────────
st.set_page_config("Symphonic AI - MIDI Chatbot", layout="wide", page_icon="🎹")
st.title("🎹 Symphonic AI - MIDI Chatbot")

@st.cache_resource(show_spinner="Creating MIDI processor …")
def get_processor():
    return MidiProcessor(SF2_PATH, model)


# ─────────────── Initialization ────────────────
model = load_model()
dirs = get_session_dirs()
processor = get_processor()

if "midi_queue" not in st.session_state:
    st.session_state.midi_queue = Queue()

queue = st.session_state.midi_queue
server = start_server(queue, HTTP_HOST, HTTP_PORT)

state_service = SessionStateService(st.session_state)
state_service.initialize(server, queue)
processing_service = MidiProcessingService(model, processor, dirs)





































# ─────────────── Sidebar Controls ────────────────
st.sidebar.header("🗂️ Conversation History")
history = state_service.get_history()

if not history:
    st.sidebar.info("No melodies processed yet.")
else:
    for item in reversed(history):
        st.sidebar.markdown(f"**ID:** `{item['id'][:8]}`")

if st.sidebar.button("Clear All"):
    state_service.clear_all(processor)

if st.sidebar.button("Download latest AI MIDI"):
    if not history:
        st.sidebar.warning("Nothing to download yet - play a melody first!")
    else:
        last = history[-1]
        with open(last["gen_mid"], "rb") as f:
            st.sidebar.download_button("Download .mid", f, file_name=f"{last['id'][:8]}_gen.mid", mime="audio/midi")

# ─────────────── Main Interaction Area ────────────────
if not state_service.session_state.server:
    st.error("🚨 Could not start MIDI server.")
elif not history:
    st.info("▶ Play a melody on your keyboard to get started.")
else:
    for idx, itm in enumerate(history, 1):
        col1, col2 = st.columns(2)

        if "error" in itm:
            st.error(itm["error"])
            continue

        with col1:
            
            st.write("😒 You")
            safe_audio(itm["orig"])
            st.write("")
            st.write("")
            st.write("")
        with col2:
            st.write("")
            st.write("")
            st.write("")
            st.write("💀 AI Generated")
            safe_audio(itm["gen"])

        st.divider()

# ─────────────── Temperature Control ────────────────
st.subheader("🌡️ Temperature Controls")
st.markdown(
    "<style>.streamlit-slider > div[data-baseweb=\"slider\"] > div {height: 20px;}</style>",
    unsafe_allow_html=True,
)
temperature = st.slider(" ", 0.1, 2.0, 1.0, step=None)

# ─────────────── Processing Queue ────────────────
if state_service.is_busy():
    st.info("⚙️ Still processing…")
elif state_service.has_pending_items():
    with st.spinner("🎵 Generating continuation… Please wait."):
        handle_midi_queue(state_service, processing_service, temperature)

if st.button("Generate"):
    blank_mid = make_blank_midi(dirs["orig_midi"])
    with open(blank_mid, "rb") as f:
        blob_b64 = base64.b64encode(f.read()).decode()
    queue.put({"id": str(uuid.uuid4()), "blob": blob_b64})

# ─────────────── MIDI Keyboard Iframe ────────────────
st.subheader("🎹 MIDI Keyboard")
st.components.v1.html(
    f'<iframe src="{BROWSER_APP_URL}" width="100%" height="500" style="border:1px solid #ccc;"></iframe>',
    height=520,
)

# ─────────────── Auto-Refresh ────────────────
st_autorefresh(interval=2000, key="auto")
