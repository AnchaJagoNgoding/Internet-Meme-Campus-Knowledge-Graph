import os
import ast
import pandas as pd
import torch
from PIL import Image
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


DATASET_PATH = r"C:\TA KG Baru\data work\evaluasi\data\gt_flickr80_cleaned.xlsx"
IMAGE_FOLDER = r"C:\TA KG Baru\data work\evaluasi\data\images"
OUTPUT_PATH = r"C:\TA KG Baru\data work\evaluasi\data\multimodal_alignment_results_for_gt.xlsx"


# =========================
# LOAD MODEL CLIP
# =========================
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer("clip-ViT-B-32", device=device)


# =========================
# HELPER FUNCTIONS
# =========================
def safe_parse_list(cell):
    """
    Mengamankan parsing kolom list (semantic label)
    """
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


def load_image_by_id(meme_id):
    """
    Load image berdasarkan ID meme
    """
    image_path = os.path.join(IMAGE_FOLDER, f"{meme_id}.jpg")
    if not os.path.exists(image_path):
        return None
    return Image.open(image_path).convert("RGB")


# =========================
# LOAD DATASET
# =========================
df = pd.read_excel(DATASET_PATH)

print("Jumlah data:", len(df))
print("Kolom tersedia:", df.columns.tolist())


# =========================
# MULTIMODAL ALIGNMENT
# =========================
results = []

for idx, row in df.iterrows():
    meme_id = int(row["id"])

    caption = row.get("caption", "")
    semantic_labels = safe_parse_list(
        row.get("semantic_label_cleaned", "")
    )

    # =========================
    # TEXT INPUT (HANYA CAPTION)
    # =========================
    combined_text = caption if isinstance(caption, str) else ""

    text_emb = None
    if combined_text.strip():
        text_emb = model.encode(combined_text)

    # =========================
    # LABEL EMBEDDING
    # =========================
    label_emb = None
    label_text = " ".join(semantic_labels)
    if label_text.strip():
        label_emb = model.encode(label_text)

    # =========================
    # IMAGE EMBEDDING
    # =========================
    image_emb = None
    img = load_image_by_id(meme_id)
    if img is not None:
        image_emb = model.encode(img)

    # =========================
    # SIMILARITY CALCULATION
    # =========================
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

    # =========================
    # ALIGNMENT SCORE
    # =========================
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


# =========================
# SAVE OUTPUT
# =========================
df_result = pd.DataFrame(results)
df_result.to_excel(OUTPUT_PATH, index=False)

print("Multimodal alignment selesai")
print("Output tersimpan di:", OUTPUT_PATH)
