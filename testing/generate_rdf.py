import os
import ast
from urllib.parse import quote
import pandas as pd
from rdflib import Graph, Literal, URIRef, Namespace
from rdflib.namespace import RDF, XSD

excel_path = r"C:\TA KG Baru\data work\data\memes_dataset_semantic_cleaned.xlsx"
output_ttl = r"C:\TA KG Baru\data work\data\imkg_output_UPD.ttl"


# Namespace / ontology
MY = Namespace("http://example.org/memeontology#")

g = Graph()
g.bind("my", MY)
g.bind("rdf", RDF)
g.bind("xsd", XSD)



# helper: parse a cell that might be a python-list string like "['a','b']"
def parse_list_cell(cell):
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



# helper: create URI-safe node id
def make_uri(base_ns, prefix, name):
    safe = quote(str(name), safe="")
    return URIRef(f"{base_ns}{prefix}_{safe}")



# Read Excel
df = pd.read_excel(excel_path, engine="openpyxl", dtype=object)

expected_cols = [
    "id", "likesCount", "commentsCount", "timestamp",
    "detected_objects", "url", "origin",
    "extracted_caption_ocr_cleaned", "semantic_label_cleaned"
]
missing_cols = [c for c in expected_cols if c not in df.columns]

if missing_cols:
    print("Peringatan: kolom berikut tidak ditemukan:", missing_cols)



# iterate rows → build RDF graph
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


    
    # likesCount
    likes_raw = row.get("likesCount")
    try:
        likes_val = int(likes_raw) if likes_raw not in [None, ""] else 0
    except:
        likes_val = 0
    g.add((meme_uri, MY.hasLikes, Literal(likes_val, datatype=XSD.integer)))


    
    # commentsCount
    comments_raw = row.get("commentsCount")
    try:
        comments_val = int(comments_raw) if comments_raw not in [None, ""] else 0
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


    
    # detected_objects → node per objek
    det_list = parse_list_cell(row.get("detected_objects"))
    for obj in det_list:
        obj_uri = make_uri(MY, "DetectedObject", obj)
        g.add((meme_uri, MY.detectsObject, obj_uri))
        g.add((obj_uri, RDF.type, MY.DetectedObject))
        g.add((obj_uri, MY.hasName, Literal(obj)))


    
    # url
    url_raw = row.get("url")
    if isinstance(url_raw, str) and url_raw.strip() != "":
        g.add((meme_uri, MY.hasURL, Literal(url_raw.strip())))


    
    # origin
    origin_raw = row.get("origin")
    if isinstance(origin_raw, str) and origin_raw.strip() != "":
        g.add((meme_uri, MY.hasOrigin, Literal(origin_raw.strip())))


    
    # extracted_caption_ocr_cleaned (string/list cleaned)
    ecc_raw = row.get("extracted_caption_ocr_cleaned")
    if ecc_raw not in [None, ""] and not pd.isna(ecc_raw):
        if isinstance(ecc_raw, (list, tuple)):
            joined = " | ".join([str(x).strip() for x in ecc_raw if str(x).strip()])
            if joined:
                g.add((meme_uri, MY.hasExtractedCaptionCleaned, Literal(joined)))
        else:
            g.add((meme_uri, MY.hasExtractedCaptionCleaned, Literal(str(ecc_raw).strip())))


    
    # semantic_label_cleaned → Concept nodes
    semc_list = parse_list_cell(row.get("semantic_label_cleaned"))
    for clabel in semc_list:
        if not clabel:
            continue
        concept_uri = make_uri(MY, "Concept", clabel)
        g.add((meme_uri, MY.hasSemanticLabel, concept_uri))
        g.add((concept_uri, RDF.type, MY.Concept))
        g.add((concept_uri, MY.hasName, Literal(clabel)))




# Save graph
os.makedirs(os.path.dirname(output_ttl), exist_ok=True)
g.serialize(destination=output_ttl, format="turtle")

print("RDF Turtle disimpan di:", output_ttl)
print("Jumlah triple:", len(g))
