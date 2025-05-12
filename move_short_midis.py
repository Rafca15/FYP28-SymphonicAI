import os
import shutil # shell utilities python library

SHORT_MIDIS_PATHS = r"C:\Users\User\Desktop\DATASET_CLEANED\short_midis_paths.txt"
SRC_DIR = r"C:\Users\User\Desktop\DATASET_CLEANED\DATASET\midi"
DST_DIR = r"C:\Users\User\Desktop\DATASET_CLEANED\short_midis"

os.makedirs(DST_DIR, exist_ok=True)

with open(SHORT_MIDIS_PATHS, 'r', encoding='utf-8') as f:
    filenames = [line.strip() for line in f if line.strip()]
    
for name in filenames:
    src_path = os.path.join(SRC_DIR, name)
    dst_path = os.path.join(DST_DIR, name)
    
    if os.path.isfile(src_path):
        shutil.move(src_path, dst_path)
        print(f"Moved: {name}")
    else:
        print(f"{name} not found")