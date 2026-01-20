import ast
import re
from pathlib import Path

import pandas as pd


INPUT_PATH = Path(r"C:\TA KG Baru\data work\evaluasi\data\gt_flickr80.xlsx")
OUTPUT_PATH = INPUT_PATH.with_name(INPUT_PATH.stem + "_cleaned" + INPUT_PATH.suffix)

COLUMN = "semantic_label"


def parse_label_value(val):
    
    if pd.isna(val):
        return []
    if isinstance(val, list):
        return [str(x) for x in val]
    if isinstance(val, str):
        s = val.strip()
        # coba literal_eval bila format list Python
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = ast.literal_eval(s)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except Exception:
                pass
        
        if "," in s:
            parts = [p.strip() for p in re.split(r",\s*", s)]
            parts = [re.sub(r"^['\"]|['\"]$", "", p) for p in parts]
            parts = [p for p in parts if p != ""]
            return parts
        
        return [re.sub(r"^['\"]|['\"]$", "", s)]
    return [str(val)]

def clean_and_split_label_token(token: str):
    
    if not isinstance(token, str):
        token = str(token)
    parts = token.split("_")
    clean_parts = []
    for p in parts:
        found = re.findall(r"[A-Za-z0-9]+", p)  
        for f in found:
            w = f.lower()
            if w:
                clean_parts.append(w)
    return clean_parts

def clean_label_list(raw_list):
    
    out = []
    seen = set()
    for token in raw_list:
        pieces = clean_and_split_label_token(token)
        for p in pieces:
            if p not in seen:
                seen.add(p)
                out.append(p)
    return out


def main():
    print("Membaca file:", INPUT_PATH)
    df = pd.read_excel(INPUT_PATH, dtype={COLUMN: object})

    if COLUMN not in df.columns:
        raise KeyError(f"Kolom '{COLUMN}' tidak ditemukan di {INPUT_PATH}")

    
    df[f"{COLUMN}_cleaned"] = df[COLUMN].apply(lambda v: clean_label_list(parse_label_value(v)))
    df[f"{COLUMN}_cleaned_str"] = df[f"{COLUMN}_cleaned"].apply(lambda lst: ", ".join(lst) if lst else "")

    
    df.to_excel(OUTPUT_PATH, index=False)
    print("Selesai. File disimpan ke:", OUTPUT_PATH)

if __name__ == "__main__":
    main()
