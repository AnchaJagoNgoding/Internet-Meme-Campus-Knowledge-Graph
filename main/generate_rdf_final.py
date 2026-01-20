import os
import ast
import re
import json
from urllib.parse import quote
import pandas as pd
from rdflib import Graph, Literal, URIRef, Namespace
from rdflib.namespace import RDF, XSD

excel_path = r"C:\TA KG Baru\data work\data\memes_dataset_cleaned.xlsx"
entities_json_path = r"C:\TA KG Baru\data work\data\NER data\memes_dataset_with_entities_normalized_FINAL.json"
output_ttl = r"C:\TA KG Baru\data work\data\output data rdf\UPD5_imkg_output_FINAL_LAST.ttl"


MY = Namespace("http://example.org/memeontology#")

g = Graph()
g.bind("my", MY)
g.bind("rdf", RDF)
g.bind("xsd", XSD)


with open(entities_json_path, "r", encoding="utf-8") as f:
    entity_data = {
        str(item["id"]): item
        for item in json.load(f)
        if "id" in item
    }


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
        cleaned = s.strip("[]")
        return [p.strip().strip("'\"") for p in cleaned.split(",") if p.strip()]


def make_uri(prefix, value):
    safe = quote(str(value), safe="")
    return URIRef(f"{MY}{prefix}_{safe}")


df = pd.read_excel(excel_path, engine="openpyxl", dtype=object)


for idx, row in df.iterrows():

    
    raw_id = row.get("id")
    if raw_id is None or str(raw_id).strip() == "":
        post_id = f"row{idx+1}"
    else:
        try:
            post_id = str(int(raw_id))
        except Exception:
            post_id = str(raw_id).strip()

    meme_uri = URIRef(f"{MY}MemePost_{quote(post_id, safe='')}")
    g.add((meme_uri, RDF.type, MY.MemePost))

    
    def safe_int(val):
        try:
            return int(val)
        except:
            return 0

    g.add((meme_uri, MY.hasLikes,
           Literal(safe_int(row.get("likesCount")), datatype=XSD.integer)))
    g.add((meme_uri, MY.hasComments,
           Literal(safe_int(row.get("commentsCount")), datatype=XSD.integer)))

    
    ts_raw = row.get("timestamp")
    if ts_raw not in [None, ""] and not pd.isna(ts_raw):
        ts = pd.to_datetime(ts_raw, errors="coerce")
        if not pd.isna(ts):
            g.add((meme_uri, MY.hasTimestamp,
                   Literal(ts.isoformat(), datatype=XSD.dateTime)))

    
    url_raw = row.get("url")
    if isinstance(url_raw, str) and url_raw.strip():
        g.add((meme_uri, MY.hasURL, Literal(url_raw.strip())))

    
    origin_raw = row.get("origin")
    if isinstance(origin_raw, str) and origin_raw.strip():
        g.add((meme_uri, MY.hasOrigin, Literal(origin_raw.strip())))

    
    caption_raw = row.get("caption")
    if isinstance(caption_raw, str) and caption_raw.strip():
        g.add((meme_uri, MY.hasCaption, Literal(caption_raw.strip())))

    
    detected_objects = parse_list_cell(row.get("detected_objects"))
    for obj in detected_objects:
        obj_uri = make_uri("DetectedObject", obj)
        g.add((obj_uri, RDF.type, MY.DetectedObject))
        g.add((obj_uri, MY.hasName, Literal(obj)))
        g.add((meme_uri, MY.detectsObject, obj_uri))

    
    semantic_labels = parse_list_cell(row.get("semantic_label_cleaned"))
    for label in semantic_labels:
        concept_uri = make_uri("Concept", label)
        g.add((concept_uri, RDF.type, MY.Concept))
        g.add((concept_uri, MY.hasName, Literal(label)))
        g.add((meme_uri, MY.hasSemanticLabel, concept_uri))

    
    post_entities = entity_data.get(post_id, {}).get("normalized_entities", [])

    for ent in post_entities:
        canonical = ent.get("canonical")
        ent_type = ent.get("type")

        if not canonical:
            continue

        
        ent_type_safe = ent_type if ent_type else "UNK"
        ent_uri = make_uri("Entity", f"{canonical}_{ent_type_safe}")

        g.add((ent_uri, RDF.type, MY.Entity))
        g.add((ent_uri, MY.hasName, Literal(canonical)))
        g.add((ent_uri, MY.hasEntityType, Literal(ent_type_safe)))

        g.add((meme_uri, MY.mentionsEntity, ent_uri))

os.makedirs(os.path.dirname(output_ttl), exist_ok=True)
g.serialize(destination=output_ttl, format="turtle")

print("RDF Knowledge Graph BERHASIL dibuat")
print("Output:", output_ttl)
print("Jumlah triple:", len(g))
