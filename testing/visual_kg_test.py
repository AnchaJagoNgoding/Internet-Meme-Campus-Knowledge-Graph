# visual_kg_from_fuseki.py
from SPARQLWrapper import SPARQLWrapper, JSON
from pyvis.network import Network
import json
import hashlib
from urllib.parse import quote
import io
import os

# ----------------- CONFIG -----------------
fuseki_url = "http://localhost:3030/LAST_FINAL_UPD_Campus_Meme_Knowledge_Graph/query"  # ganti jika perlu
sparql = SPARQLWrapper(fuseki_url)
sparql.setReturnFormat(JSON)

# Output HTML
output_file = r"C:\TA KG Baru\data work\data\visual_popularity_10.html"

# Maximum number of memes to fetch (untuk mencegah visualisasi terlalu besar)


# ----------------- SPARQL QUERY (disesuaikan dengan ontology kamu) -----------------
query = f"""
PREFIX my: <http://example.org/memeontology#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT
  ?memePost
  ?caption
  ?concept ?conceptName
  ?likes ?comments ?timestamp ?origin ?url
WHERE {{
  ?memePost rdf:type my:MemePost .

  # tahun
  ?memePost my:hasTimestamp ?ts .
  BIND(YEAR(xsd:dateTime(?ts)) AS ?year)
  FILTER(?year IN (2023, 2024, 2025))

  # origin
  OPTIONAL {{ ?memePost my:hasOrigin ?origin . }}
  FILTER(BOUND(?origin))
  FILTER(LCASE(STR(?origin)) IN ("itb", "its", "telkomuniversity"))

  # semantic label
  ?memePost my:hasSemanticLabel ?concept .
  ?concept my:hasName ?conceptName .

  # popularity
  OPTIONAL {{ ?memePost my:hasLikes ?likes . }}
  OPTIONAL {{ ?memePost my:hasComments ?comments . }}

  BIND(IF(BOUND(?likes), xsd:integer(?likes), 0) AS ?likesInt)
  BIND(IF(BOUND(?comments), xsd:integer(?comments), 0) AS ?commentsInt)
  BIND((2*?likesInt + ?commentsInt) AS ?popularityScore)

  FILTER(
    (LCASE(STR(?origin)) = "itb" && ?popularityScore >= 5000) ||
    (LCASE(STR(?origin)) IN ("its","telkomuniversity") && ?popularityScore >= 10000)
  )

  OPTIONAL {{ ?memePost my:hasCaption ?caption . }}
  OPTIONAL {{ ?memePost my:hasURL ?url . }}
  OPTIONAL {{ ?memePost my:hasTimestamp ?timestamp . }}
}}
LIMIT 10 
"""
sparql.setQuery(query)

# ----------------- RUN QUERY -----------------
try:
    print("[INFO] Running SPARQL query...")
    results = sparql.query().convert()
    bindings = results.get("results", {}).get("bindings", [])
    print(f"[INFO] Rows returned: {len(bindings)}")
except Exception as e:
    print("Error running SPARQL query:", e)
    raise

# ----------------- INIT PYVIS -----------------
net = Network(height="800px", width="100%", bgcolor="#222222", font_color="white", notebook=False)
# set some options (optional)
net.set_options("""
var options = {
  "nodes": { "font": {"multi": "true", "size": 14}, "shapeProperties": {"useBorderWithImage": false} },
  "interaction": { "hover": true, "navigationButtons": true, "keyboard": true },
  "physics": { "enabled": true, "solver": "forceAtlas2Based" }
}
""")

# Track added node ids
added_nodes = set()

# Helper: create deterministic node id for literal text (so same literal maps to same node)
def literal_node_id(prefix: str, text: str):
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    return f"{prefix}_{h}"

# Helper: short label from full URI (after # or last /)
def short_label_from_uri(uri: str):
    if "#" in uri:
        return uri.split("#")[-1]
    return uri.rstrip("/").split("/")[-1]

# ----------------- PROCESS QUERY RESULTS -----------------
# Each SPARQL binding row may contain repeated memePost; we ensure unique node creation.
for row in bindings:
    meme_uri = row.get("memePost", {}).get("value")
    if not meme_uri:
        continue

    # short id for readability in label (fallback to full uri if underscore split not possible)
    try:
        post_id_short = meme_uri.split("_")[-1]
    except Exception:
        post_id_short = short_label_from_uri(meme_uri)

    # caption (may be absent)
    caption = row.get("caption", {}).get("value", "")

    # Meme node id (use full URI as unique id)
    meme_id = meme_uri
    meme_label = f"Post: {post_id_short}"

    if meme_id not in added_nodes:
        # Add MemePost node (box, blue)
        net.add_node(
            meme_id,
            label=meme_label,
            title=f"URI: {meme_uri}\nCaption: {caption}",
            color={"background": "#3498DB", "border": "#21618C"},
            shape="box",
            size=22,
            font={"color": "white", "size": 13, "face": "Arial", "multi": "true", "align": "center"},
            widthConstraint={"minimum": 140, "maximum": 300}
        )
        added_nodes.add(meme_id)

    # Concept (semantic label)
    concept_uri = row.get("concept", {}).get("value")
    concept_name = row.get("conceptName", {}).get("value")
    if concept_uri and concept_name:
        if concept_uri not in added_nodes:
            net.add_node(
                concept_uri,
                label=concept_name,
                title=f"Concept URI: {concept_uri}\nName: {concept_name}",
                color={"background": "#E74C3C", "border": "#C0392B"},
                shape="ellipse",
                size=18,
                font={"color": "white", "size": 12, "face": "Arial", "multi": "true"}
            )
            added_nodes.add(concept_uri)
        net.add_edge(meme_id, concept_uri, label="hasSemanticLabel", color={"color": "grey"}, width=0.6)

    # DetectedObject
    detected_obj_uri = row.get("detectedObject", {}).get("value")
    object_name = row.get("objectName", {}).get("value")
    if detected_obj_uri and object_name:
        if detected_obj_uri not in added_nodes:
            net.add_node(
                detected_obj_uri,
                label=object_name,
                title=f"Detected Object URI: {detected_obj_uri}\nName: {object_name}",
                color={"background": "#F39C12", "border": "#D35400"},
                shape="circle",
                size=14,
                font={"color": "white", "size": 11, "face": "Arial", "multi": "true"}
            )
            added_nodes.add(detected_obj_uri)
        net.add_edge(meme_id, detected_obj_uri, label="detectsObject", color={"color": "darkgrey"}, width=0.5)

    # Extracted Word (literal token) -- map token -> deterministic node via hash
    extracted_word = row.get("extractedWord", {}).get("value")
    if extracted_word:
        w_id = literal_node_id("word", extracted_word)
        if w_id not in added_nodes:
            net.add_node(
                w_id,
                label=extracted_word,
                title=f"Extracted word: {extracted_word}",
                color={"background": "#9B59B6", "border": "#8E44AD"},
                shape="dot",
                size=10,
                font={"color": "white", "size": 10, "face": "Arial"}
            )
            added_nodes.add(w_id)
        net.add_edge(meme_id, w_id, label="hasExtractedWord", color={"color": "lightgrey"}, width=0.3)

    # Likes / Comments / Timestamp / URL / Origin (add as small literal nodes)
    # We'll create literal nodes with deterministic ids so duplicates reuse nodes
    likes = row.get("likes", {}).get("value")
    if likes:
        nid = literal_node_id("likes", likes)
        if nid not in added_nodes:
            net.add_node(nid, label=f"likes: {likes}", title=f"Likes: {likes}", shape="box",
                         color={"background": "#34495E", "border": "#2C3E50"}, size=10,
                         font={"color": "white", "size": 10})
            added_nodes.add(nid)
        net.add_edge(meme_id, nid, label="hasLikes", color={"color": "silver"}, width=0.2)

    comments = row.get("comments", {}).get("value")
    if comments:
        nid = literal_node_id("comments", comments)
        if nid not in added_nodes:
            net.add_node(nid, label=f"comments: {comments}", title=f"Comments: {comments}", shape="box",
                         color={"background": "#34495E", "border": "#2C3E50"}, size=10,
                         font={"color": "white", "size": 10})
            added_nodes.add(nid)
        net.add_edge(meme_id, nid, label="hasComments", color={"color": "silver"}, width=0.2)

    timestamp = row.get("timestamp", {}).get("value")
    if timestamp:
        nid = literal_node_id("ts", timestamp)
        if nid not in added_nodes:
            net.add_node(nid, label=timestamp, title=f"Timestamp: {timestamp}", shape="box",
                         color={"background": "#2C3E50", "border": "#222222"}, size=10,
                         font={"color": "white", "size": 10})
            added_nodes.add(nid)
        net.add_edge(meme_id, nid, label="hasTimestamp", color={"color": "silver"}, width=0.2)

    url = row.get("url", {}).get("value")
    if url:
        nid = literal_node_id("url", url)
        if nid not in added_nodes:
            # shorten label for URL display
            short_url = url if len(url) < 50 else (url[:40] + "...")
            net.add_node(nid, label=short_url, title=f"URL: {url}", shape="box",
                         color={"background": "#2C3E50", "border": "#222222"}, size=10,
                         font={"color": "white", "size": 10})
            added_nodes.add(nid)
        net.add_edge(meme_id, nid, label="hasURL", color={"color": "silver"}, width=0.2)

    origin = row.get("origin", {}).get("value")
    if origin:
        nid = literal_node_id("origin", origin)
        if nid not in added_nodes:
            net.add_node(nid, label=origin, title=f"Origin: {origin}", shape="box",
                         color={"background": "#2C3E50", "border": "#222222"}, size=10,
                         font={"color": "white", "size": 10})
            added_nodes.add(nid)
        net.add_edge(meme_id, nid, label="hasOrigin", color={"color": "silver"}, width=0.2)

# ----------------- FINISH: generate HTML and write robustly -----------------
print("[INFO] Generating interactive HTML...")
html_str = net.generate_html()

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with io.open(output_file, "w", encoding="utf-8") as f:
    f.write(html_str)

print("[DONE] Visualization written to:", output_file)
print("[INFO] Total unique nodes added:", len(added_nodes))
