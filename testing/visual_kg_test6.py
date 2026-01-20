# visual_politik_cooccurrence_kg.py

from SPARQLWrapper import SPARQLWrapper, JSON
from pyvis.network import Network
import hashlib
import os
import io

# ===================== CONFIG =====================
FUSEKI_URL = "http://localhost:3030/LAST_FINAL_UPD_Campus_Meme_Knowledge_Graph/query"
OUTPUT_HTML = r"C:\TA KG Baru\data work\data\visual_politik_cooccurrence.html"

sparql = SPARQLWrapper(FUSEKI_URL)
sparql.setReturnFormat(JSON)

# ===================== SPARQL QUERY =====================
query = """
PREFIX my: <http://example.org/memeontology#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT
  ?memePost
  ?caption
  ?origin
  ?labelName
WHERE {
  ?memePost rdf:type my:MemePost .

  # Meme harus punya label politik
  ?memePost my:hasSemanticLabel ?c1 .
  ?c1 my:hasName ?politicLabel .
  FILTER(LCASE(STR(?politicLabel)) = "politik")

  # Ambil semua label dalam meme yang sama
  ?memePost my:hasSemanticLabel ?c2 .
  ?c2 my:hasName ?labelName .

  OPTIONAL { ?memePost my:hasCaption ?caption . }
  OPTIONAL { ?memePost my:hasOrigin ?origin . }
}
LIMIT 300
"""

sparql.setQuery(query)
results = sparql.query().convert()
bindings = results["results"]["bindings"]

# ===================== INIT NETWORK =====================
net = Network(
    height="800px",
    width="100%",
    bgcolor="#1e1e1e",
    font_color="white"
)

net.set_options("""
{
  "physics": {
    "enabled": true,
    "solver": "forceAtlas2Based",
    "forceAtlas2Based": {
      "gravitationalConstant": -50,
      "centralGravity": 0.01,
      "springLength": 120
    }
  }
}
""")

added_nodes = set()

def hash_id(prefix, value):
    return f"{prefix}_{hashlib.md5(value.encode()).hexdigest()}"

# ===================== BUILD GRAPH =====================
for row in bindings:
    meme_uri = row["memePost"]["value"]
    caption = row.get("caption", {}).get("value", "")
    origin = row.get("origin", {}).get("value", "")
    label = row["labelName"]["value"]

    meme_id = meme_uri
    meme_short = meme_uri.split("_")[-1]

    # === MemePost node ===
    if meme_id not in added_nodes:
        net.add_node(
            meme_id,
            label=f"MemePost {meme_short}",
            title=caption,
            shape="box",
            color="#3498db"
        )
        added_nodes.add(meme_id)

    # === Origin node ===
    if origin:
        origin_id = hash_id("origin", origin)
        if origin_id not in added_nodes:
            net.add_node(
                origin_id,
                label=origin,
                shape="box",
                color="#2ecc71"
            )
            added_nodes.add(origin_id)
        net.add_edge(meme_id, origin_id, label="hasOrigin")

    # === Semantic label node ===
    label_id = hash_id("label", label)

    if label_id not in added_nodes:
        if label.lower() == "politik":
            color = "#e74c3c"   # merah (pusat)
            size = 30
        else:
            color = "#f1c40f"   # kuning (label lain)
            size = 20

        net.add_node(
            label_id,
            label=label,
            shape="ellipse",
            color=color,
            size=size
        )
        added_nodes.add(label_id)

    # === Edge MemePost -> Label ===
    net.add_edge(meme_id, label_id, label="hasSemanticLabel")

# ===================== CO-OCCURRENCE EDGE =====================
# Hubungkan label "politik" dengan label lain
politic_id = hash_id("label", "politik")

for node in list(added_nodes):
    if node.startswith("label_") and node != politic_id:
        net.add_edge(
            politic_id,
            node,
            label="co_occurs",
            color="orange",
            width=2
        )

# ===================== SAVE =====================
os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
html = net.generate_html()

with io.open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("Visualisasi Knowledge Graph POLITIK + CO-OCCURRENCE berhasil dibuat")
print("Output:", OUTPUT_HTML)
print("Total node:", len(added_nodes))
