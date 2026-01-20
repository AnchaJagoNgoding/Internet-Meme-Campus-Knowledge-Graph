import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import os


excel_path = r"C:\TA KG Baru\data modelling\drama_telyu\data\cleaned_data_dratel.xlsx"
df = pd.read_excel(excel_path)


output_folder = r"C:\TA KG Baru\data modelling\drama_telyu\data\images"
os.makedirs(output_folder, exist_ok=True)


for idx, url in enumerate(df['displayUrl']):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content)).convert("RGB")
        filename = f"img_{idx+1:03d}.jpg"
        filepath = os.path.join(output_folder, filename)

        img.save(filepath)
        print(f"Gambar {filename} berhasil disimpan.")
    except Exception as e:
        print(f"Gambar {idx+1} tidak bisa disimpan: {e}")
