from SPARQLWrapper import SPARQLWrapper, JSON
from pyvis.network import Network
import hashlib
import os
import io

# ================= CONFIG =================
FUSEKI_URL = "http://localhost:3030/LAST_FINAL_UPD_Campus_Meme_Knowledge_Graph/query"
OUTPUT_HTML = r"C:\TA KG Baru\data work\data\visual graf\visual_politik_kg.html"

sparql = SPARQLWrapper(FUSEKI_URL)
sparql.setReturnFormat(JSON)

# ================= QUERY =================
query = """
PREFIX my: <http://example.org/memeontology#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT
  ?memePost
  ?caption
  ?origin
  ?concept
  ?conceptName
  ?entity
  ?entityName
  ?object
  ?objectName
WHERE {
  ?memePost rdf:type my:MemePost .

  ?memePost my:hasSemanticLabel ?concept .
  ?concept my:hasName ?conceptName .
  FILTER(LCASE(STR(?conceptName)) = "politik")

  OPTIONAL { ?memePost my:hasCaption ?caption . }
  OPTIONAL { ?memePost my:hasOrigin ?origin . }

  OPTIONAL {
    ?memePost my:mentionsEntity ?entity .
    ?entity my:hasName ?entityName .
  }

  OPTIONAL {
    ?memePost my:detectsObject ?object .
    ?object my:hasName ?objectName .
  }
}
LIMIT 200
"""
sparql.setQuery(query)

results = sparql.query().convert()["results"]["bindings"]

# ================= INIT GRAPH =================
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
    "solver": "forceAtlas2Based"
  }
}
""")

added = set()

def node_id(prefix, value):
    return f"{prefix}_{hashlib.md5(value.encode()).hexdigest()}"

# ================= BUILD GRAPH =================
for row in results:
    meme = row["memePost"]["value"]
    caption = row.get("caption", {}).get("value", "")
    origin = row.get("origin", {}).get("value")

    meme_id = meme
    meme_label = meme.split("_")[-1]

    if meme_id not in added:
        net.add_node(
            meme_id,
            label=f"MemePost {meme_label}",
            title=caption,
            shape="box",
            color="#3498db"
        )
        added.add(meme_id)

    # semantic label POLITIK
    concept = row["concept"]["value"]
    cname = row["conceptName"]["value"]

    if concept not in added:
        net.add_node(
            concept,
            label=cname,
            shape="ellipse",
            color="#e74c3c"
        )
        added.add(concept)

    net.add_edge(meme_id, concept, label="hasSemanticLabel")

    # origin
    if origin:
        oid = node_id("origin", origin)
        if oid not in added:
            net.add_node(
                oid,
                label=origin,
                shape="box",
                color="#2ecc71"
            )
            added.add(oid)
        net.add_edge(meme_id, oid, label="hasOrigin")

    # entity
    if "entity" in row and "entityName" in row:
        ent = row["entity"]["value"]
        ename = row["entityName"]["value"]

        if ent not in added:
            net.add_node(
                ent,
                label=ename,
                shape="ellipse",
                color="#9b59b6"
            )
            added.add(ent)

        net.add_edge(meme_id, ent, label="mentionsEntity")

    # detected object
    if "object" in row and "objectName" in row:
        obj = row["object"]["value"]
        oname = row["objectName"]["value"]

        if obj not in added:
            net.add_node(
                obj,
                label=oname,
                shape="circle",
                color="#f39c12"
            )
            added.add(obj)

        net.add_edge(meme_id, obj, label="detectsObject")

# ================= SAVE =================
os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
with io.open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(net.generate_html())

print("Visualisasi KG politik berhasil dibuat:")
print(OUTPUT_HTML)
