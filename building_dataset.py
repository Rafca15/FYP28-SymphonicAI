import mido
import os

def split_midi_tracks(input_midi_file, output_folder):
    """Splits each track in a MIDI file into separate files while preserving global metadata, but skips track_0."""
    mid = mido.MidiFile(input_midi_file)
    midi_file_name = os.path.splitext(os.path.basename(input_midi_file))[0]

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Extract global metadata (tempo, time signature, key signature) from track_0
    global_metadata = []
    if mid.tracks:
        for msg in mid.tracks[0]:  # Always extract metadata from track_0
            if msg.type in ["set_tempo", "time_signature", "key_signature"]:
                global_metadata.append(msg)

    # Iterate through each track, but **skip track_0**
    track_files = []
    track_count = 0
    for i, track in enumerate(mid.tracks[1:], start=1):  # Start from track_1, skipping track_0
        new_midi = mido.MidiFile(ticks_per_beat=mid.ticks_per_beat)
        new_track = mido.MidiTrack()
        new_midi.tracks.append(new_track)

        # Add global metadata (tempo & time signature) to each track
        for msg in global_metadata:
            new_track.append(msg)

        # Copy track-specific events
        for msg in track:
            if msg.type not in ["set_tempo", "time_signature"]:  # Avoid duplicate tempo changes
                new_track.append(msg)

        # Save the track
        track_count += 1
        track_filename = os.path.join(output_folder, f"{midi_file_name}_track_{track_count}.mid")
        new_midi.save(track_filename)
        track_files.append((track_filename, len(new_track)))

    return track_files

def process_midi_directory(input_dir, output_dir):
    """
    Reads all MIDI files in the input directory, applies the split_midi_tracks function,
    and stores all track outputs in a single output directory.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Iterate over all MIDI files in the input directory
    for midi_file in os.listdir(input_dir):
        if midi_file.lower().endswith(".mid"):
            input_midi_path = os.path.join(input_dir, midi_file)
            split_midi_tracks(input_midi_path, output_dir)

if __name__ == "__main__":
    input_dir = "midi_files"  # Change this to your input folder
    output_dir = "all_midi_tracks"  # Output folder for all MIDI tracks
    
    process_midi_directory(input_dir, output_dir)
