import random
from rdflib import Graph, URIRef
from rdflib.namespace import RDF
from collections import defaultdict


KG_FILE_PATH = r"C:\TA KG Baru\data work\data\output data rdf\UPD5_imkg_output_FINAL_LAST.ttl"


REAL_INSTAGRAM_POST_COUNTS = {
    "drama.telyu": 2295,
    "itb.receh": 1611,
    "meme10nopember": 394,
}


COLLECTED_INSTAGRAM_POST_COUNTS = {
    "drama.telyu": 1595,
    "itb.receh": 1324,
    "meme10nopember": 300,
}

def evaluate_coverage(kg_path, real_counts, collected_counts):
   
    print("--- Memulai Evaluasi Coverage (Cakupan Data) ---")

    
    kg = Graph()
    try:
        kg.parse(kg_path, format="turtle")
        print(f"Knowledge Graph berhasil dimuat dari {kg_path}.")
    except Exception as e:
        print(f"Error saat memuat Knowledge Graph: {e}. Tidak dapat melanjutkan evaluasi coverage.")
        return

    MYONTOLOGY = URIRef("http://example.org/memeontology#")

    
    query_total_meme_posts_in_kg = f"""
    PREFIX myontology: <http://example.org/memeontology#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT (COUNT(DISTINCT ?memePost) AS ?count)
    WHERE {{
      ?memePost rdf:type myontology:MemePost .
    }}
    """
    total_meme_posts_in_kg = 0
    
    for row in kg.query(query_total_meme_posts_in_kg):
        
        total_meme_posts_in_kg = int(str(row[0])) 
    
    print(f"\nJumlah Total MemePost Unik dalam Knowledge Graph: {total_meme_posts_in_kg}")

    
    total_real_posts = sum(real_counts.values())
    
    total_collected_posts = sum(collected_counts.values())

    print("\n--- Ringkasan Coverage ---")
    print(f"Total Post Riil di Instagram (dari akun target): {total_real_posts}")
    print(f"Total Post yang Berhasil Dikumpulkan (data input KG): {total_collected_posts}")
    
    
    collection_coverage = total_collected_posts / total_real_posts if total_real_posts > 0 else 0
    print(f"Cakupan Pengumpulan Data (Collected/Real): {collection_coverage:.2%}")

    
    kg_formation_coverage = total_meme_posts_in_kg / total_collected_posts if total_collected_posts > 0 else 0
    print(f"Cakupan Pembentukan KG (KG/Collected): {kg_formation_coverage:.2%}")
    
    
    overall_coverage = total_meme_posts_in_kg / total_real_posts if total_real_posts > 0 else 0
    print(f"Cakupan Keseluruhan (KG/Real): {overall_coverage:.2%}")

    print("\n--- Coverage Per Akun ---")
    for account, real_count in real_counts.items():
        collected_count = collected_counts.get(account, 0)
        
        print(f"- {account}:")
        print(f"  - Real Posts              : {real_count}")
        print(f"  - Collected Posts         : {collected_count}")
        
        account_collection_coverage = collected_count / real_count if real_count > 0 else 0
        print(f"  - Cakupan Pengumpulan     : {account_collection_coverage:.2%}")
        
       
    print("\n-------------------------------------------------\n")

evaluate_coverage(KG_FILE_PATH, REAL_INSTAGRAM_POST_COUNTS, COLLECTED_INSTAGRAM_POST_COUNTS)