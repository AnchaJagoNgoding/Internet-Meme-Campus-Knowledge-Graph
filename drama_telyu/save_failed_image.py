import pandas as pd
import os


excel_path = r"C:\TA KG Baru\data modelling\drama_telyu\data\cleaned_data_dratel.xlsx"
output_folder = r"C:\TA KG Baru\data modelling\drama_telyu\data\images"


df = pd.read_excel(excel_path)


expected_total = len(df)
expected_files = {f"img_{i+1:03d}.jpg" for i in range(expected_total)}


existing_files = set(os.listdir(output_folder))


missing_files = sorted(expected_files - existing_files)


print("Daftar gambar yang gagal disimpan:")
for fname in missing_files:
    print(fname)