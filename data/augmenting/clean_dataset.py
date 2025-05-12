import midi_neural_processor.processor as midi_tokenizer
import os
from mido import MidiFile

DATASET_DIR = r"C:\Users\User\Desktop\DATASET_CLEANED\DATASET\midi"
SHORT_MIDIS_PATHS = r"C:\Users\User\Desktop\DATASET_CLEANED\short_midis_paths.txt"
CORRUPTED_MIDIS_PATHS = r"C:\Users\User\Desktop\DATASET_CLEANED\corrupted_midis_paths.txt"

short_midis_paths = []
corrupted_midis_paths = []

all_midis = [f for f in os.listdir(DATASET_DIR) if f.lower().endswith((".mid",".midi"))]

for midi_path in all_midis:

    full_path = os.path.join(DATASET_DIR, midi_path)
    
    try:
        MidiFile(full_path)
    except Exception as e:
        corrupted_midis_paths.append(midi_path)
        print("Skipping corrupted file ", midi_path)
    
    print("Encoding ", midi_path, "...")
    tokens = midi_tokenizer.encode_midi(full_path)
    if(len(tokens) < 128):
        print(midi_path, " contains ", len(tokens), " tokens")
        short_midis_paths.append(midi_path)
        
        
with open(SHORT_MIDIS_PATHS, 'w', encoding='utf-8') as out:
    for midi_name in short_midis_paths:
        out.write(midi_name + '\n')
        
with open(CORRUPTED_MIDIS_PATHS, 'w', encoding='utf-8') as out:
    for midi_name in corrupted_midis_paths:
        out.write(midi_name + '\n')

print(f"\nSaved {len(short_midis_paths)} entries to {SHORT_MIDIS_PATHS}")