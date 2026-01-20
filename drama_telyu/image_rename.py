import os
import re


folder_path = r"C:\TA KG Baru\data modelling\drama_telyu\data\images"


image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]


def extract_number(filename):
    match = re.search(r"(\d+)", filename)
    return int(match.group(1)) if match else float("inf")

image_files.sort(key=extract_number)


for i, old_name in enumerate(image_files, start=1):
    new_name = f"{i}.jpg"
    old_path = os.path.join(folder_path, old_name)
    new_path = os.path.join(folder_path, new_name)
    
    os.rename(old_path, new_path)
    print(f"Renamed: {old_name} -> {new_name}")
