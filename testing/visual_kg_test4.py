from SPARQLWrapper import SPARQLWrapper, JSON
from pyvis.network import Network
import hashlib
import io
import os

# ======================================================
# CONFIG
# ======================================================
FUSEKI_URL = "http://localhost:3030/LAST_FINAL_UPD_Campus_Meme_Knowledge_Graph/query"
OUTPUT_FILE = r"C:\TA KG Baru\data work\data\visual graf\visual_instance_core_with_id.html"
LIMIT = 150   # jumlah MemePost yang divisualisasikan

sparql = SPARQLWrapper(FUSEKI_URL)
sparql.setReturnFormat(JSON)

# ======================================================
# HELPER FUNCTION
# ======================================================
def get_memepost_id(uri: str):
    """
    Ambil ID MemePost dari URI
    contoh:
    http://example.org/memeontology#MemePost_123
    -> MemePost_123
    """
    if "#" in uri:
        return uri.split("#")[-1]
    return uri.split("/")[-1]

def safe_node_id(prefix, value: str):
    """ID deterministik untuk node non-URI (misal origin)"""
    return prefix + "_" + hashlib.md5(value.encode("utf-8")).hexdigest()

# ======================================================
# SPARQL QUERY (INSTANCE-LEVEL)
# ======================================================
sparql.setQuery(f"""
PREFIX my: <http://example.org/memeontology#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT
  ?memePost
  ?origin
  ?caption
  ?concept ?conceptName
  ?object ?objectName
  ?entity ?entityName
WHERE {{
  ?memePost rdf:type my:MemePost .

  # ---------- Filter tahun ----------
  ?memePost my:hasTimestamp ?ts .
  BIND(YEAR(xsd:dateTime(?ts)) AS ?year)
  FILTER(?year IN (2023, 2024, 2025))

  # ---------- Origin ----------
  ?memePost my:hasOrigin ?origin .
  FILTER(LCASE(STR(?origin)) IN ("itb", "its", "telkomuniversity"))

  # ---------- Popularity (filter only) ----------
  OPTIONAL {{ ?memePost my:hasLikes ?likes . }}
  OPTIONAL {{ ?memePost my:hasComments ?comments . }}

  BIND(IF(BOUND(?likes), xsd:integer(?likes), 0) AS ?likesInt)
  BIND(IF(BOUND(?comments), xsd:integer(?comments), 0) AS ?commentsInt)
  BIND((2 * ?likesInt + ?commentsInt) AS ?score)

  FILTER(
    (LCASE(STR(?origin)) = "itb" && ?score >= 5000) ||
    (LCASE(STR(?origin)) IN ("its","telkomuniversity") && ?score >= 10000)
  )

  # ---------- Semantic Label ----------
  OPTIONAL {{
    ?memePost my:hasSemanticLabel ?concept .
    ?concept my:hasName ?conceptName .
  }}

  # ---------- Detected Object ----------
  OPTIONAL {{
    ?memePost my:detectsObject ?object .
    ?object my:hasName ?objectName .
  }}

  # ---------- Entity ----------
  OPTIONAL {{
    ?memePost my:mentionsEntity ?entity .
    ?entity my:hasName ?entityName .
  }}

  # ---------- Caption (tooltip only) ----------
  OPTIONAL {{ ?memePost my:hasCaption ?caption . }}
}}
LIMIT {LIMIT}
""")

# ======================================================
# RUN QUERY
# ======================================================
print("[INFO] Running SPARQL query...")
results = sparql.query().convert()
rows = results["results"]["bindings"]
print(f"[INFO] Rows returned: {len(rows)}")

# ======================================================
# INIT PYVIS NETWORK
# ======================================================
net = Network(
    height="800px",
    width="100%",
    bgcolor="#1e1e1e",
    font_color="white",
    notebook=False
)

# JSON murni (AMAN)
net.set_options("""
{
  "physics": {
    "enabled": true,
    "solver": "forceAtlas2Based"
  },
  "interaction": {
    "hover": true,
    "navigationButtons": true,
    "keyboard": true
  }
}
""")

added_nodes = set()

# ======================================================
# BUILD GRAPH
# ======================================================
for r in rows:
    meme_uri = r["memePost"]["value"]
    meme_label = get_memepost_id(meme_uri)  # <-- INI KUNCINYA
    caption = r.get("caption", {}).get("value", "")
    origin = r.get("origin", {}).get("value")

    # ---------------- MemePost ----------------
    if meme_uri not in added_nodes:
        net.add_node(
            meme_uri,
            label=meme_label,
            title=caption,
            shape="box",
            size=32,
            color="#3498DB"
        )
        added_nodes.add(meme_uri)

    # ---------------- Origin ----------------
    if origin and origin.strip():
        origin_id = safe_node_id("origin", origin)
        if origin_id not in added_nodes:
            net.add_node(
                origin_id,
                label=origin,
                shape="ellipse",
                size=26,
                color="#2ECC71"
            )
            added_nodes.add(origin_id)
        net.add_edge(meme_uri, origin_id, label="hasOrigin")

    # ---------------- Semantic Label ----------------
    if "concept" in r and "conceptName" in r:
        cname = r["conceptName"]["value"]
        curi = r["concept"]["value"]
        if cname.strip() and curi not in added_nodes:
            net.add_node(
                curi,
                label=cname,
                shape="ellipse",
                size=22,
                color="#E74C3C"
            )
            added_nodes.add(curi)
        if cname.strip():
            net.add_edge(meme_uri, curi, label="hasSemanticLabel")

    # ---------------- Detected Object ----------------
    if "object" in r and "objectName" in r:
        oname = r["objectName"]["value"]
        ouri = r["object"]["value"]
        if oname.strip() and ouri not in added_nodes:
            net.add_node(
                ouri,
                label=oname,
                shape="circle",
                size=20,
                color="#F39C12"
            )
            added_nodes.add(ouri)
        if oname.strip():
            net.add_edge(meme_uri, ouri, label="detectsObject")

    # ---------------- Entity ----------------
    if "entity" in r and "entityName" in r:
        ename = r["entityName"]["value"]
        euri = r["entity"]["value"]
        if ename.strip() and euri not in added_nodes:
            net.add_node(
                euri,
                label=ename,
                shape="diamond",
                size=22,
                color="#9B59B6"
            )
            added_nodes.add(euri)
        if ename.strip():
            net.add_edge(meme_uri, euri, label="mentionsEntity")

# ======================================================
# SAVE HTML
# ======================================================
html = net.generate_html()
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with io.open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print("[DONE] Visualization saved to:")
print(OUTPUT_FILE)
print("[INFO] Total nodes created:", len(added_nodes))
