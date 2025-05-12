import os
import processor as midi_tokenizer

DEVICE = "cpu"
SF2_PATH = r".\assets\FluidR3_GM.sf2"
MODEL_PATH = r".\assets\model.pt"

HTTP_HOST = "localhost"
HTTP_PORT = 9000
BROWSER_APP_URL = "http://localhost:8000/"


event_range = midi_tokenizer.RANGE_NOTE_ON
event_range += midi_tokenizer.RANGE_NOTE_OFF
event_range += midi_tokenizer.RANGE_TIME_SHIFT
event_range += midi_tokenizer.RANGE_VEL

CONFIG = {
    "device" : "cpu",
    "max_sequence_len": 1024,
    "block_size": 512,
    "embedding_dim": 256,
    "num_heads": 8,
    "num_layers": 6, #num_blocks
    "batch_size": 16,
    "token_pad": event_range,
    "token_sos": event_range + 1,
    "token_eos": event_range + 2,
    "vocab_size": event_range + 3,
    "seed": 42,
    "model_out": "midi_transformer_model.pt"
}


