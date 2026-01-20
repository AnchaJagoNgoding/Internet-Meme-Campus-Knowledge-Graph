import json
from collections import Counter

# ================= PATH =================
INPUT_PATH = r"C:\TA KG Baru\data work\data\memes_dataset_with_named_entities2.json"

def find_most_frequent_named_entities(top_k=20):
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    entity_counter = Counter()

    for post in data:
        for ent in post.get("named_entities", []):
            text = ent.get("text", "").strip().lower()
            if text:
                entity_counter[text] += 1

    print("NAMED ENTITIES TERBANYAK")
    print("=" * 40)

    for entity, count in entity_counter.most_common(top_k):
        print(f"{entity:<30} : {count}")

    print("=" * 40)
    print(f"Total entitas unik: {len(entity_counter)}")


if __name__ == "__main__":
    find_most_frequent_named_entities(top_k=20)
