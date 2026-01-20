import pandas as pd

excel_path = r"C:\TA KG Baru\data work\data\memes_dataset.xlsx"
output_txt = r"C:\TA KG Baru\data work\data\memes_dataset_filtered.txt"


df = pd.read_excel(excel_path, engine="openpyxl")


df_filtered = df[["id", "caption", "extracted_text_ocr"]]

lines = []
for _, row in df_filtered.iterrows():
    id_val = str(row["id"])
    caption_val = str(row["caption"]).replace("\n", " ").strip()
    ocr_val = str(row["extracted_text_ocr"]).strip()
    
    
    line = f"{id_val} {caption_val} {ocr_val}"
    lines.append(line)
    lines.append("---")  


with open(output_txt, "w", encoding="utf-8-sig") as f:
    f.write("\n".join(lines))

print("TXT berhasil dibuat dengan format --- antar record!")
print("Disimpan di:", output_txt)
