import os
import glob
import numpy as np
import mido


def transpose_mido(input_path, output_path, semis):
    mid = mido.MidiFile(input_path)
    for track in mid.tracks:
        for msg in track:
            if msg.type in ('note_on', 'note_off'):
                msg.note = max(0, min(127, msg.note + semis))
    mid.save(output_path)


def random_semitone_shift(max_range: int = 5) -> int:
    return np.random.randint(-max_range, max_range + 1)


def sample_unique_shifts(max_range, n_variants):
    possible = [i for i in range(-max_range, max_range + 1) if i != 0]
    if len(possible) < n_variants:
        return list(np.random.choice(possible, size=n_variants, replace=True))
    return list(np.random.choice(possible, size=n_variants, replace=False))


def tempo_scale_mido(mid, rate):
    for track in mid.tracks:
        for msg in track:
            msg.time = int(msg.time / rate)
            if msg.type == 'set_tempo':
                msg.tempo = int(msg.tempo /rate)
    return mid
    

input_dir = r"C:\Users\User\Desktop\DATASET_CLEANED\DATASET\midi"
output_dir = r"C:\Users\User\Desktop\DATASET_CLEANED\DATASET_AUGMENTED"
os.makedirs(output_dir, exist_ok=True)

n_variants = 3       # number of unique transpositions per file
max_transpose = 7    # maximum semitone shift (±)
tempo_slow, tempo_fast = 0.5, 1.25

min_key, max_key_val = 0, 127
encountered_pitches = set()

midi_paths = glob.glob(os.path.join(input_dir, "**", "*.mid"), recursive=True)

# generate augmented files
for path in midi_paths:
    base_name = os.path.splitext(os.path.basename(path))[0]
    shifts = sample_unique_shifts(max_transpose, n_variants)
    
    for variant_idx, semis in enumerate(shifts, start=1):
        for tempo_label, rate in [('slow', tempo_slow), ('fast', tempo_fast)]:
            mid = mido.MidiFile(path)
            
            for track in mid.tracks:
                for msg in track:
                    if hasattr(msg, 'note') and msg.type in ('note_on', 'note_off'):
                        msg.note = max(0, min(127, msg.note + semis))
                        if min_key <= msg.note <= max_key_val:
                            encountered_pitches.add(msg.note)
                            
            mid = tempo_scale_mido(mid, rate)
            
            out_name = f"{base_name}_aug{variant_idx}_shift{semis:+d}.mid"
            out_path = os.path.join(output_dir, out_name)
            mid.save(out_path)
            print(f"Wrote augmented MIDI: {out_path}")


# After all files, report coverage
all_piano_keys = set(range(min_key, max_key_val + 1))
missing = sorted(all_piano_keys - encountered_pitches)
if not missing:
    print("All piano keys covered in augmented dataset.")
else:
    print(f"Missing piano keys: {missing}")
print("ALL DONE")