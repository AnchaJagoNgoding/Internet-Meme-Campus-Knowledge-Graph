import ast
import re
import unicodedata
from pathlib import Path

import pandas as pd

# ------------------------- CONFIG -------------------------
INPUT_PATH = Path(r"C:\TA KG Baru\data work\data\memes_dataset.xlsx")
OUTPUT_PATH = INPUT_PATH.with_name(INPUT_PATH.stem + "_caption_ocr_tokenized" + INPUT_PATH.suffix)

COL_CAPTION = "caption"
COL_OCR = "extracted_text_ocr"
# ----------------------------------------------------------

# helper: parse cell that may be list, string repr of list, or plain string
def parse_maybe_list(val):
    if pd.isna(val):
        return []
    # already a list
    if isinstance(val, list):
        return [str(x) for x in val]
    # if it's a string that looks like a python list repr
    if isinstance(val, str):
        s = val.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = ast.literal_eval(s)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except Exception:
                # fallback to splitting below
                pass
        # if there are explicit separators (newline or '||' or comma) split conservatively by newline first
        # but typical OCR column is list-like so return as single-item list
        return [s]
    # fallback
    return [str(val)]

# helper: normalize text unicode, remove URLs and mentions, replace underscores with spaces
URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"@\w+")
HASHTAG_RE = re.compile(r"#(\w+)")
NON_ALNUM_RE = re.compile(r"[^0-9A-Za-z\u00C0-\u017F]+")  # keep basic latin & latin-ext letters and numbers

def normalize_text(text: str) -> str:
    # normalize unicode (NFKC) and make lowercase
    text = unicodedata.normalize("NFKC", text)
    # remove URLs and mentions
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    # convert hashtags like #telyutizen -> telyutizen (we keep the word)
    text = HASHTAG_RE.sub(r"\1", text)
    # replace underscores with spaces (so they split)
    text = text.replace("_", " ")
    # now collapse repeated whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()

def tokenize_text(text: str):
    """
    Return list of tokens (lowercase), keeping only alphanumeric substrings.
    Preserves token order as they appear in text.
    """
    if not text:
        return []
    text = normalize_text(text)
    # find alphanumeric word substrings (including latin-ext)
    # NON_ALNUM_RE matches characters to remove; we replace them with space then split
    cleaned = NON_ALNUM_RE.sub(" ", text)
    tokens = [t for t in cleaned.split() if t]
    return tokens

def tokens_from_caption_cell(val):
    # caption expected to be plain string; handle list fallback defensively
    if pd.isna(val):
        return []
    if isinstance(val, list):
        # join elements with space
        joined = " ".join(str(x) for x in val)
        return tokenize_text(joined)
    return tokenize_text(str(val))

def tokens_from_ocr_cell(val):
    # OCR column often is list of strings (each text block). Flatten then tokenize.
    items = parse_maybe_list(val)
    if not items:
        return []
    joined = " ".join(str(x) for x in items)
    return tokenize_text(joined)

def main():
    print("Membaca file:", INPUT_PATH)
    df = pd.read_excel(INPUT_PATH, dtype={COL_CAPTION: object, COL_OCR: object})

    # Pastikan kolom ada
    if COL_CAPTION not in df.columns:
        raise KeyError(f"Kolom '{COL_CAPTION}' tidak ditemukan di {INPUT_PATH}")
    if COL_OCR not in df.columns:
        raise KeyError(f"Kolom '{COL_OCR}' tidak ditemukan di {INPUT_PATH}")

    # Proses caption
    df["caption_tokens"] = df[COL_CAPTION].apply(tokens_from_caption_cell)
    df["caption_tokens_str"] = df["caption_tokens"].apply(lambda lst: ", ".join(lst) if lst else "")

    # Proses extracted_text_ocr
    df["ocr_tokens"] = df[COL_OCR].apply(tokens_from_ocr_cell)
    df["ocr_tokens_str"] = df["ocr_tokens"].apply(lambda lst: ", ".join(lst) if lst else "")

    # Gabungkan tokens (caption first then ocr), pertahankan urutan, deduplicate sambil menjaga urutan
    def merge_preserve_order(a, b):
        out = []
        seen = set()
        for t in (a or []) + (b or []):
            if t not in seen:
                seen.add(t)
                out.append(t)
        return out

    df["combined_tokens"] = df.apply(lambda r: merge_preserve_order(r["caption_tokens"], r["ocr_tokens"]), axis=1)
    df["combined_tokens_str"] = df["combined_tokens"].apply(lambda lst: ", ".join(lst) if lst else "")

    # Tulis ke Excel
    df.to_excel(OUTPUT_PATH, index=False)
    print("Selesai. File tokenized disimpan ke:", OUTPUT_PATH)

if __name__ == "__main__":
    main()
