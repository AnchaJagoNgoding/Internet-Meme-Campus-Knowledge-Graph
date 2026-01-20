import os
import ast
import re
from urllib.parse import quote
import pandas as pd
from rdflib import Graph, Literal, URIRef, Namespace
from rdflib.namespace import RDF, XSD

# ----------------- konfigurasi paths -----------------
excel_path = r"C:\TA KG Baru\data work\data\memes_dataset_semantic_cleaned.xlsx"
output_ttl = r"C:\TA KG Baru\data work\data\imkg_output_UPD2.ttl"
# ----------------------------------------------------

# Namespace / ontology
MY = Namespace("http://example.org/memeontology#")

g = Graph()
g.bind("my", MY)
g.bind("rdf", RDF)
g.bind("xsd", XSD)


# ---------------- helper: parse list-like cell ----------------
def parse_list_cell(cell):
    """Mengembalikan list of strings dari cell: list, repr list, atau CSV-like."""
    if cell is None:
        return []
    if isinstance(cell, (list, tuple)):
        return [str(x).strip() for x in cell if str(x).strip()]
    s = str(cell).strip()
    if s == "":
        return []
    try:
        parsed = ast.literal_eval(s)
        if isinstance(parsed, (list, tuple)):
            return [str(x).strip() for x in parsed if str(x).strip()]
        return [p.strip() for p in str(parsed).split(",") if p.strip()]
    except Exception:
        cleaned = s
        if cleaned.startswith("[") and cleaned.endswith("]"):
            cleaned = cleaned[1:-1]
        parts = [p.strip().strip("'\"") for p in cleaned.split(",") if p.strip()]
        return parts


# ---------------- helper: URI creation ----------------
def make_uri(base_ns, prefix, name):
    safe = quote(str(name), safe="")
    return URIRef(f"{base_ns}{prefix}_{safe}")


# ---------------- helper: tokenisasi & normalisasi ----------------
_token_re = re.compile(r"[A-Za-z0-9\u00C0-\u017F]+")  # huruf + angka + latin-ext

def normalize_and_tokenize(text: str):
    """
    Normalisasi dan tokenisasi text:
      - lower-case
      - ganti underscore -> spasi
      - ambil substring token alfanumerik (latin-ext)
      - kembalikan list token (already lowercase)
    """
    if not text:
        return []
    s = str(text)
    s = s.replace("_", " ")
    s = s.lower()
    tokens = _token_re.findall(s)
    return tokens


# ---------------- Main: baca Excel dan bangun RDF ----------------
df = pd.read_excel(excel_path, engine="openpyxl", dtype=object)

expected_cols = [
    "id", "likesCount", "commentsCount", "timestamp",
    "detected_objects", "url", "origin",
    "extracted_caption_ocr_cleaned", "semantic_label_cleaned", "caption"
]
missing_cols = [c for c in expected_cols if c not in df.columns]
if missing_cols:
    print("Peringatan: kolom berikut tidak ditemukan di Excel:", missing_cols)

for idx, row in df.iterrows():
    # ID
    raw_id = row.get("id")
    if raw_id is None or (isinstance(raw_id, float) and pd.isna(raw_id)) or str(raw_id).strip() == "":
        post_id = f"row{idx+1}"
    else:
        try:
            post_id = str(int(raw_id))
        except Exception:
            post_id = str(raw_id).strip()

    meme_uri = URIRef(f"{MY}MemePost_{quote(post_id, safe='')}")
    g.add((meme_uri, RDF.type, MY.MemePost))

    # likes
    likes_raw = row.get("likesCount")
    try:
        likes_val = int(likes_raw) if likes_raw not in [None, ""] and not (isinstance(likes_raw, float) and pd.isna(likes_raw)) else 0
    except:
        likes_val = 0
    g.add((meme_uri, MY.hasLikes, Literal(likes_val, datatype=XSD.integer)))

    # comments
    comments_raw = row.get("commentsCount")
    try:
        comments_val = int(comments_raw) if comments_raw not in [None, ""] and not (isinstance(comments_raw, float) and pd.isna(comments_raw)) else 0
    except:
        comments_val = 0
    g.add((meme_uri, MY.hasComments, Literal(comments_val, datatype=XSD.integer)))

    # timestamp
    ts_raw = row.get("timestamp")
    if ts_raw not in [None, ""] and not pd.isna(ts_raw):
        try:
            ts_parsed = pd.to_datetime(ts_raw, errors="coerce")
            if pd.isna(ts_parsed):
                ts_literal = Literal(str(ts_raw))
            else:
                ts_literal = Literal(ts_parsed.isoformat(), datatype=XSD.dateTime)
        except:
            ts_literal = Literal(str(ts_raw))
        g.add((meme_uri, MY.hasTimestamp, ts_literal))

    # detected objects
    det_list = parse_list_cell(row.get("detected_objects"))
    for obj in det_list:
        if not obj:
            continue
        obj_uri = make_uri(MY, "DetectedObject", obj)
        g.add((meme_uri, MY.detectsObject, obj_uri))
        g.add((obj_uri, RDF.type, MY.DetectedObject))
        g.add((obj_uri, MY.hasName, Literal(obj)))

    # url
    url_raw = row.get("url")
    if isinstance(url_raw, str) and url_raw.strip():
        g.add((meme_uri, MY.hasURL, Literal(url_raw.strip())))

    # origin
    origin_raw = row.get("origin")
    if isinstance(origin_raw, str) and origin_raw.strip():
        g.add((meme_uri, MY.hasOrigin, Literal(origin_raw.strip())))

    # caption -> store original caption literal (if present)
    caption_raw = row.get("caption")
    if caption_raw not in [None, ""] and not pd.isna(caption_raw):
        g.add((meme_uri, MY.hasCaption, Literal(str(caption_raw).strip())))

    # extracted_caption_ocr_cleaned -> parse list or string
    ecc_raw = row.get("extracted_caption_ocr_cleaned")
    ecc_list = parse_list_cell(ecc_raw)

    # --- combine caption + ecc_text for tokenization ---
    combined_pieces = []
    # caption first (if present)
    if caption_raw not in [None, ""] and not pd.isna(caption_raw):
        combined_pieces.append(str(caption_raw))
    # then ECC pieces (if list)
    if ecc_list:
        combined_pieces.extend(ecc_list)
    # if ECC column is a single string but parse_list_cell returned empty, fallback to raw ecc_raw
    if not combined_pieces and ecc_raw not in [None, ""] and not pd.isna(ecc_raw):
        combined_pieces.append(str(ecc_raw))

    joined_text = " ".join(p for p in combined_pieces if str(p).strip())

    # tokenize merged text and add my:hasExtractedWord (dedup per post)
    tokens = normalize_and_tokenize(joined_text)
    seen = set()
    for t in tokens:
        if t in seen:
            continue
        seen.add(t)
        # optionally skip trivial tokens (single char) or pure numbers — keep as is for now
        g.add((meme_uri, MY.hasExtractedWord, Literal(t)))

    # semantic_label_cleaned -> Concept nodes
    semc_list = parse_list_cell(row.get("semantic_label_cleaned"))
    for clabel in semc_list:
        if not clabel:
            continue
        concept_uri = make_uri(MY, "Concept", clabel)
        g.add((meme_uri, MY.hasSemanticLabel, concept_uri))
        g.add((concept_uri, RDF.type, MY.Concept))
        g.add((concept_uri, MY.hasName, Literal(clabel)))


# ---------------- save graph ----------------
os.makedirs(os.path.dirname(output_ttl), exist_ok=True)
g.serialize(destination=output_ttl, format="turtle")
print("RDF Turtle disimpan di:", output_ttl)
print("Jumlah triple:", len(g))
