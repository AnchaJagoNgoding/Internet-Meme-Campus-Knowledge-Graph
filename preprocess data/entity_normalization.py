import json
import re
from fuzzywuzzy import fuzz

INPUT_PATH = r"C:\TA KG Baru\data work\data\NER data\memes_dataset_with_named_entities_FINAL.json"
OUTPUT_PATH = r"C:\TA KG Baru\data work\data\NER data\memes_dataset_with_entities_normalized_FINAL.json"

CANONICAL_ENTITIES = [
    "telkom_university",
    "telyu",
    "telyutizen",
    "telyumenfess",
    "drama_telyu",
    "dratel",
    "bandung",
    "bojongsoang",
    "sukapura",
    "smbtelkom",
    "indonesia",
    "chatgpt",
    "admin",
    "tiktok",
    "instagram",
    "itb",
    "receh",
    "freya",
    "prabowo",
    "aniesbaswedan",
    "ganjarpranowo",
    "windahbasudara",
    "gibranraka",
    "tult",
    "guyonan",
    "mahasiswa"
    
]

ENTITY_ALIAS_MAP = {
    
    "telkom": "telkom_university",
    "telkom university": "telkom_university",
    "telkomuniversity": "telkom_university",
    "tel u": "telkom_university",
    "tel-u": "telkom_university",
    "telu": "telkom_university",
    "telyu": "telyu",
    "telyutizen": "telyu",
    "telyufess": "telyumenfess",
    "telyu fess": "telyumenfess",
    "telyumenfess": "telyumenfess",
    "dratel": "drama_telyu",
    "drama tel": "drama_telyu",
    "drama tel u": "drama_telyu",
    "drama telyu": "drama_telyu",
    "mbtel": "smbtelkom",
    "smbtel": "smbtelkom",
    "mbtelkom": "smbtelkom",
    "bojongsoang": "bojongsoang",
    "dayeuhkolot": "dayeuhkolot",
    "bandung": "bandung",
    "itb receh": "itb",
    "life receh": "receh",
    "fre": "freya",
    "prabow": "prabowo",
    "bumingraka": "gibranraka",
    "institutteknologibandung": "itb",
    "pag": "guyonan"
}

def clean_entity(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def is_noise_entity(text):
    return (
        len(text) < 3 or
        text in {"u", "yu", "tel", "a", "an", "ne"} or
        text.isdigit()
    )

def normalize_entity(entity_text):
    clean_text = clean_entity(entity_text)

    if is_noise_entity(clean_text):
        return None

    # Alias map
    if clean_text in ENTITY_ALIAS_MAP:
        return ENTITY_ALIAS_MAP[clean_text]

    # Fuzzy match
    best_match = None
    best_score = 0

    for canonical in CANONICAL_ENTITIES:
        score = fuzz.token_set_ratio(clean_text, canonical)
        if score > best_score:
            best_score = score
            best_match = canonical

    if best_score >= 60:
        return best_match

    
    return clean_text.replace(" ", "_")

def run_normalization():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for post in data:
        normalized_entities = []

        for ent in post.get("named_entities", []):
            canonical = normalize_entity(ent["text"])

            if canonical is None:
                continue

            normalized_entities.append({
                "original_text": ent["text"],
                "type": ent["type"],
                "canonical": canonical,
                "reference_id": f"local::{canonical}"
            })

        post["normalized_entities"] = normalized_entities

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Entity normalization selesai")
    print("Output:", OUTPUT_PATH)

if __name__ == "__main__":
    run_normalization()
