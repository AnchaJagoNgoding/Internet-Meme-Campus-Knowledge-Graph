import os
import re

folder_path = r"C:\TA KG Baru\data modelling\itb_receh\data\images"

# Ambil hanya file .jpg
image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]

# Ekstrak angka dari nama file agar bisa diurutkan
def extract_number(filename):
    match = re.search(r"(\d+)", filename)
    return int(match.group(1)) if match else float("inf")

# Urutkan file berdasarkan angka
image_files.sort(key=extract_number)

# Mulai rename dari nomor 1596
start_number = 1596

for idx, old_name in enumerate(image_files, start=start_number):
    new_name = f"{idx}.jpg"
    old_path = os.path.join(folder_path, old_name)
    new_path = os.path.join(folder_path, new_name)

    os.rename(old_path, new_path)
    print(f"Renamed: {old_name} -> {new_name}")
