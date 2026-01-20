from SPARQLWrapper import SPARQLWrapper, JSON
from pyvis.network import Network
import hashlib
import io
import os


fuseki_url = "http://localhost:3030/Campus_Meme_Knowledge_Graph_FINAL/query"
output_file = r"C:\TA KG Baru\data work\data\visual graf\visual_kg_baru_lim50000.html"
LIMIT = 50000

sparql = SPARQLWrapper(fuseki_url)
sparql.setReturnFormat(JSON)

query = f"""
PREFIX my: <http://example.org/memeontology#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT
  ?memePost ?caption
  ?concept ?conceptName
  ?detectedObject ?objectName
  ?entity ?entityName ?entityType
  ?origin
WHERE {{
  ?memePost rdf:type my:MemePost .

  OPTIONAL {{ ?memePost my:hasCaption ?caption . }}

  OPTIONAL {{
    ?memePost my:hasSemanticLabel ?concept .
    ?concept my:hasName ?conceptName .
  }}

  OPTIONAL {{
    ?memePost my:detectsObject ?detectedObject .
    ?detectedObject my:hasName ?objectName .
  }}

  OPTIONAL {{
    ?memePost my:mentionsEntity ?entity .
    ?entity my:hasName ?entityName .
    OPTIONAL {{ ?entity my:hasEntityType ?entityType . }}
  }}

  OPTIONAL {{ ?memePost my:hasOrigin ?origin . }}
}}
LIMIT {LIMIT}
"""

sparql.setQuery(query)

print("[INFO] Running SPARQL query...")
rows = sparql.query().convert()["results"]["bindings"]
print("[INFO] Rows returned:", len(rows))


net = Network(
    height="850px",
    width="100%",
    bgcolor="#1e1e1e",
    font_color="white"
)

net.set_options("""
var options = {
  "interaction": { "hover": true, "navigationButtons": true },
  "physics": { "solver": "forceAtlas2Based" }
}
""")

added = set()

def literal_node_id(prefix, text):
    return f"{prefix}_{hashlib.md5(text.encode()).hexdigest()}"


for r in rows:
    meme = r["memePost"]["value"]
    post_id = meme.split("_")[-1]

    #Memepost
    if meme not in added:
        net.add_node(
            meme,
            label=f"Meme {post_id}",
            title=r.get("caption", {}).get("value", ""),
            shape="box",
            color="#3498db",
            size=24
        )
        added.add(meme)

    #Concept (Label Semantik)
    if "concept" in r:
        c = r["concept"]["value"]
        name = r["conceptName"]["value"]
        if c not in added:
            net.add_node(c, label=name, color="#e74c3c", shape="ellipse", size=18)
            added.add(c)
        net.add_edge(meme, c, label="hasSemanticLabel")

    #Detected Objects
    if "detectedObject" in r:
        o = r["detectedObject"]["value"]
        name = r["objectName"]["value"]
        if o not in added:
            net.add_node(o, label=name, color="#f39c12", shape="circle", size=16)
            added.add(o)
        net.add_edge(meme, o, label="detectsObject")

    #Entity NER
    if "entity" in r:
        e = r["entity"]["value"]
        name = r["entityName"]["value"]
        etype = r.get("entityType", {}).get("value", "")
        label = f"{name}\n({etype})" if etype else name

        if e not in added:
            net.add_node(e, label=label, color="#2ecc71", shape="ellipse", size=18)
            added.add(e)
        net.add_edge(meme, e, label="mentionsEntity")

    #ORigin
    if "origin" in r:
        origin = r["origin"]["value"]
        oid = literal_node_id("origin", origin)

        if oid not in added:
            net.add_node(
                oid,
                label=origin,
                title="Origin platform",
                shape="box",
                color="#9b59b6",
                size=14
            )
            added.add(oid)

        net.add_edge(meme, oid, label="hasOrigin")

#Load
os.makedirs(os.path.dirname(output_file), exist_ok=True)
html = net.generate_html()

with io.open(output_file, "w", encoding="utf-8") as f:
    f.write(html)

print("[DONE] Visualization saved:", output_file)
print("[INFO] Total nodes:", len(added))
