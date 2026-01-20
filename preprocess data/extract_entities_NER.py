import re
import pandas as pd
from transformers import pipeline
from nltk.corpus import stopwords
import nltk

nltk.download("stopwords")
stop_words = set(stopwords.words("indonesian") + stopwords.words("english"))

def load_full_dataset():
    path = r"C:\TA KG Baru\data work\data\memes_dataset_cleaned.xlsx"
    df = pd.read_excel(path)

    required_cols = ["id", "caption"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Kolom '{col}' tidak ditemukan")

    return df

def light_clean(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

ner_pipeline = pipeline(
    task="ner",
    model="cahya/xlm-roberta-large-indonesian-NER",
    aggregation_strategy="simple"
)

def extract_named_entities(df):
    all_entities = []                      

    MAIN_LABELS = {"PER", "LOC", "ORG"}

    for _, row in df.iterrows():
        caption = light_clean(row["caption"])

        if not caption:
            all_entities.append([])
            continue

        try:
            entities = ner_pipeline(caption)
        except Exception as e:
            print("NER error:", e)
            all_entities.append([])
            continue

        filtered_entities = []

        for ent in entities:
            ent_text = ent["word"].strip()
            raw_label = ent["entity_group"]

            
            if raw_label in MAIN_LABELS:
                final_label = raw_label
            else:
                final_label = "MISC"

            
            if len(ent_text) < 3:
                continue
            if ent_text.lower() in stop_words:
                continue
            if ent_text.isdigit():
                continue
            if re.fullmatch(r"[a-z]{1,2}", ent_text.lower()):
                continue

            filtered_entities.append({
                "text": ent_text,
                "type": final_label
            })

        all_entities.append(filtered_entities)

    df["named_entities"] = all_entities
    return df

if __name__ == "__main__":
    df = load_full_dataset()
    df = extract_named_entities(df)

    output_path = r"C:\TA KG Baru\data work\data\NER data\memes_dataset_with_named_entities_FINAL.json"
    df.to_json(
        output_path,
        orient="records",
        indent=2,
        force_ascii=False
    )

    print("NER dengan XLM-RoBERTa bahasa Indonesia selesai")
    print("Output:", output_path)
