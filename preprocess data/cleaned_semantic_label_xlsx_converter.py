import ast
import pandas as pd
import os

input_csv = r"C:\TA KG Baru\data work\data\semantic_label2.csv"
output_xlsx = r"C:\TA KG Baru\data work\data\new_semantic_label2.xlsx"
encoding = "utf-8"

def parse_label_list(s):
    if s is None:
        return []

    s = str(s).strip()

    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s_content = s[1:-1]
    else:
        s_content = s

    try:
        parsed = ast.literal_eval(s_content)
        if isinstance(parsed, (list, tuple)):
            return [str(x).strip() for x in parsed]
        return [str(parsed).strip()]
    except:
        if s_content.startswith("[") and s_content.endswith("]"):
            s_content = s_content[1:-1]
        return [p.strip().strip("'\" ") for p in s_content.split(",") if p.strip()]

rows = []
with open(input_csv, "r", encoding=encoding, errors="replace") as f:
    header = f.readline()
    for raw in f:
        line = raw.strip()
        if not line or ";" not in line:
            continue

        id_part, rest = line.split(";", 1)
        labels = parse_label_list(rest)

        atomic_labels = []
        seen = set()
        for label in labels:
            for p in label.split("_"):
                p = p.strip().lower()
                if p and p not in seen:
                    seen.add(p)
                    atomic_labels.append(p)

        rows.append((id_part.strip(), atomic_labels))

clean_rows = []
for id_val, labels in rows:
    try:
        id_val = int(id_val)
    except:
        pass

    
    label_str = "[" + ", ".join(f"'{l}'" for l in labels) + "]"

    clean_rows.append({
        "id": id_val,
        "label_semantik": label_str
    })

df_out = pd.DataFrame(clean_rows, columns=["id", "label_semantik"])

os.makedirs(os.path.dirname(output_xlsx), exist_ok=True)
df_out.to_excel(output_xlsx, index=False, engine="openpyxl")

print("SUKSES! File Excel tersimpan di:", output_xlsx)
