import json
import pandas as pd

# =========================
# PATH KONFIGURASI
# =========================
INPUT_PATH = r"C:\TA KG Baru\data work\data\NER data\memes_dataset_with_entities_normalized3.json"
OUTPUT_PATH = r"C:\TA KG Baru\data work\data\named_entities_normalized.csv"


# =========================
# LOAD JSON
# =========================
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)


# =========================
# EXTRACT NAMED ENTITIES
# =========================
rows = []

for post in data:
    post_id = post.get("id")

    for ent in post.get("normalized_entities", []): #ganti ke named_entities untuk yang sebelum normalisasi
        rows.append({
            "post_id": post_id,
            #"text": ent.get("text"), #untuk sebelum normalisasi
            "canonical": ent.get("canonical"), #untuk yang normalisasi
            "entity_type": ent.get("type")
        })


# =========================
# SAVE TO CSV
# =========================
df_entities = pd.DataFrame(rows)
df_entities.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

print("Ekstraksi named_entities selesai")
print(f"Total entitas  : {len(df_entities)}")
print(f"Output CSV     : {OUTPUT_PATH}")
