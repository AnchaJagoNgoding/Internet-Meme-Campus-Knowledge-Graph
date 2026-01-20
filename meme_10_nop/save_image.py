import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import os


excel_path = r"C:\TA KG Baru\data modelling\meme_10_nop\data\cleaned_data_meme10nopember.xlsx"
df =pd.read_excel(excel_path)

output_folder = r"C:\TA KG Baru\data modelling\meme_10_nop\data\images"
os.makedirs(output_folder, exist_ok=True) 


start_image_number = 2920

for i, url in enumerate(df['displayUrl'], start=start_image_number):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content)).convert("RGB")
        filename = f"img_{i:04d}.jpg" 
        filepath = os.path.join(output_folder, filename)

        img.save(filepath)
        print(f"Gambar {filename} berhasil disimpan.")
    except Exception as e:
        print(f"Gambar {i+1} tidak bisa disimpan: {e}")

    
