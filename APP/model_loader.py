import torch
import streamlit as st
from config import MODEL_PATH, CONFIG, DEVICE
from model import TransformerMIDILanguageModel

@st.cache_resource
def load_model():
    try:
        model = TransformerMIDILanguageModel(CONFIG)
        model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device(DEVICE)))
        model.eval()
        
        print(model)
        
        return model

    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

