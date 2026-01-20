
from SPARQLWrapper import SPARQLWrapper, JSON
from pyvis.network import Network
import hashlib
import io
import os


FUSEKI_URL = "http://localhost:3030/LAST_FINAL_UPD_Campus_Meme_Knowledge_Graph/query"
TARGET_MEME_ID = "MemePost_1"   
OUTPUT_FILE = r"C:\TA KG Baru\data work\data\visual_single_memepost.html"



sparql = SPARQLWrapper(FUSEKI_URL)
sparql.setReturnFormat(JSON)


query = f"""
PREFIX my: <http://example.org/memeontology#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT
  ?meme
  ?caption
  ?concept ?conceptName
  ?detectedObject ?objectName
  ?word
  ?likes
  ?comments
  ?timestamp
  ?origin
  ?url
WHERE {{
  ?meme rdf:type my:MemePost .
  FILTER(CONTAINS(STR(?meme), "{TARGET_MEME_ID}"))

  OPTIONAL {{ ?meme my:hasCaption ?caption . }}

  OPTIONAL {{
    ?meme my:hasSemanticLabel ?concept .
    ?concept my:hasName ?conceptName .
  }}

  OPTIONAL {{
    ?meme my:detectsObject ?detectedObject .
    ?detectedObject my:hasName ?objectName .
  }}

  OPTIONAL {{ ?meme my:hasExtractedWord ?word . }}
  OPTIONAL {{ ?meme my:hasLikes ?likes . }}
  OPTIONAL {{ ?meme my:hasComments ?comments . }}
  OPTIONAL {{ ?meme my:hasTimestamp ?timestamp . }}
  OPTIONAL {{ ?meme my:hasOrigin ?origin . }}
  OPTIONAL {{ ?meme my:hasURL ?url . }}
}}
"""
sparql.setQuery(query)

print("[INFO] Running SPARQL query...")
results = sparql.query().convert()
rows = results["results"]["bindings"]
print(f"[INFO] Rows returned: {len(rows)}")


net = Network(
    height="800px",
    width="100%",
    bgcolor="#222222",
    font_color="white",
    notebook=False
)

net.set_options("""
var options = {
  "nodes": { "font": { "size": 14 } },
  "interaction": {
    "hover": true,
    "navigationButtons": true,
    "keyboard": true
  },
  "physics": {
    "enabled": true,
    "solver": "forceAtlas2Based"
  }
}
""")

added_nodes = set()


def literal_id(prefix, value):
    h = hashlib.md5(value.encode("utf-8")).hexdigest()
    return f"{prefix}_{h}"


for r in rows:
    meme_uri = r["meme"]["value"]
    caption = r.get("caption", {}).get("value", "")


    if meme_uri not in added_nodes:
        net.add_node(
            meme_uri,
            label="MemePost",
            title=f"{meme_uri}\n\nCaption:\n{caption}",
            shape="box",
            size=30,
            color={"background": "#2980B9", "border": "#1F618D"},
            font={"color": "white", "size": 16}
        )
        added_nodes.add(meme_uri)


    if "concept" in r and "conceptName" in r:
        c_uri = r["concept"]["value"]
        c_name = r["conceptName"]["value"]

        if c_uri not in added_nodes:
            net.add_node(
                c_uri,
                label=c_name,
                shape="ellipse",
                size=22,
                color={"background": "#E74C3C", "border": "#C0392B"}
            )
            added_nodes.add(c_uri)

        net.add_edge(meme_uri, c_uri, label="hasSemanticLabel")


    if "detectedObject" in r and "objectName" in r:
        o_uri = r["detectedObject"]["value"]
        o_name = r["objectName"]["value"]

        if o_uri not in added_nodes:
            net.add_node(
                o_uri,
                label=o_name,
                shape="circle",
                size=18,
                color={"background": "#F39C12", "border": "#D35400"}
            )
            added_nodes.add(o_uri)

        net.add_edge(meme_uri, o_uri, label="detectsObject")


    if "word" in r:
        w = r["word"]["value"]
        w_id = literal_id("word", w)

        if w_id not in added_nodes:
            net.add_node(
                w_id,
                label=w,
                shape="dot",
                size=12,
                color={"background": "#9B59B6", "border": "#8E44AD"}
            )
            added_nodes.add(w_id)

        net.add_edge(meme_uri, w_id, label="hasExtractedWord")


    for key, rel in [
        ("likes", "hasLikes"),
        ("comments", "hasComments"),
        ("timestamp", "hasTimestamp"),
        ("origin", "hasOrigin"),
        ("url", "hasURL")
    ]:
        if key in r:
            val = r[key]["value"]
            lid = literal_id(key, val)

            if lid not in added_nodes:
                net.add_node(
                    lid,
                    label=f"{key}: {val}",
                    shape="box",
                    size=12,
                    color={"background": "#34495E", "border": "#2C3E50"}
                )
                added_nodes.add(lid)

            net.add_edge(meme_uri, lid, label=rel)


html = net.generate_html()
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with io.open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print("[DONE] Ego-network visualization saved at:")
print(OUTPUT_FILE)
print("[INFO] Total nodes:", len(added_nodes))
