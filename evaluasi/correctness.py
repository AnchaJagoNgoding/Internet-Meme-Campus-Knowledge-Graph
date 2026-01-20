import os
import ast
import pandas as pd
import torch
from PIL import Image
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


DATASET_PATH = r"C:\TA KG Baru\data work\data\memes_dataset_cleaned.xlsx"
IMAGE_FOLDER = r"C:\TA KG Baru\data work\data\images"
OUTPUT_PATH = r"C:\TA KG Baru\data work\evaluasi\multimodal_alignment_results.xlsx"


# Load Label Multimodal
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer("clip-ViT-B-32", device=device)


def safe_parse_list(cell):
    
    if cell is None:
        return []
    if isinstance(cell, list):
        return cell
    try:
        parsed = ast.literal_eval(cell)
        if isinstance(parsed, list):
            return parsed
    except:
        pass
    return [str(cell)]

def combine_text(caption, ocr):
    
    caption = caption if isinstance(caption, str) else ""
    ocr_list = safe_parse_list(ocr)
    ocr_text = " ".join(ocr_list)
    return f"{caption} {ocr_text}".strip()

def load_image_by_id(meme_id):
    
    image_path = os.path.join(IMAGE_FOLDER, f"{meme_id}.jpg")
    if not os.path.exists(image_path):
        return None
    return Image.open(image_path).convert("RGB")


df = pd.read_excel(DATASET_PATH)

print("Jumlah data:", len(df))
print("Kolom tersedia:", df.columns.tolist())


# Multimodal Alignment
results = []

for idx, row in df.iterrows():
    meme_id = int(row["id"])

    caption = row.get("caption", "")
    ocr = row.get("extracted_text_ocr", "")
    semantic_labels = safe_parse_list(row.get("semantic_label_cleaned", ""))

   
    combined_text = combine_text(caption, ocr)

   
    text_emb = None
    if combined_text:
        text_emb = model.encode(combined_text)

   
    label_emb = None
    label_text = " ".join(semantic_labels)
    if label_text:
        label_emb = model.encode(label_text)

    
    image_emb = None
    img = load_image_by_id(meme_id)
    if img is not None:
        image_emb = model.encode(img)

   
    similarities = {}

    if text_emb is not None and image_emb is not None:
        similarities["text_image"] = cosine_similarity(
            [text_emb], [image_emb]
        )[0][0]

    if text_emb is not None and label_emb is not None:
        similarities["text_label"] = cosine_similarity(
            [text_emb], [label_emb]
        )[0][0]

    if image_emb is not None and label_emb is not None:
        similarities["image_label"] = cosine_similarity(
            [image_emb], [label_emb]
        )[0][0]

    
    if similarities:
        alignment_score = sum(similarities.values()) / len(similarities)
    else:
        alignment_score = 0.0

    results.append({
        "id": meme_id,
        "alignment_score": round(float(alignment_score), 4),
        "text_image_similarity": round(similarities.get("text_image", 0.0), 4),
        "text_label_similarity": round(similarities.get("text_label", 0.0), 4),
        "image_label_similarity": round(similarities.get("image_label", 0.0), 4)
    })

    if idx % 100 == 0:
        print(f"Processed {idx}/{len(df)}")


df_result = pd.DataFrame(results)
df_result.to_excel(OUTPUT_PATH, index=False)

print("Multimodal alignment selesai")
print("Output tersimpan di:", OUTPUT_PATH)
