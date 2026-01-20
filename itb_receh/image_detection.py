import os
import re
import json
import cv2
import easyocr
from ultralytics import YOLO
import pandas as pd

IMAGE_DIR = r"C:\TA KG Baru\data modelling\itb_receh\data\images"
INPUT_PATH = r"C:\TA KG Baru\data modelling\itb_receh\data\cleaned_data_itbreceh.xlsx"
OUTPUT_JSON_PATH = r"C:\TA KG Baru\data modelling\itb_receh\data\data_with_image_and_text.json"
OUTPUT_XLSX_PATH = r"C:\TA KG Baru\data modelling\itb_receh\data\data_with_image_and_text.xlsx"

print("Inisialisasi model YOLO11x dan EasyOCR...")
yolo_model = YOLO("yolo11x.pt")
reader = easyocr.Reader(["en", "id"], gpu=False)
print("Model berhasil diinisialisasi.\n")

def extract_number_from_filename(filename):
    match = re.search(r"(\d+)", filename)
    return int(match.group(1)) if match else None

def unique_preserve_order(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def detect_objects_yolo(image_path):
    try:
        results = yolo_model(image_path)
        objects = []
        for r in results:
            if hasattr(r, "boxes") and hasattr(r.boxes, "cls"):
                # pastikan objek diubah ke list python
                cls_list = r.boxes.cls.cpu().numpy().tolist() if hasattr(r.boxes.cls, "cpu") else list(r.boxes.cls)
                for cls_idx in cls_list:
                    class_name = yolo_model.names[int(cls_idx)]
                    objects.append(class_name)
        return unique_preserve_order(objects)
    except Exception as e:
        print(f"[YOLO ERROR] {image_path}: {e}")
        return []

def extract_text_ocr(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Gagal membaca gambar.")
        results = reader.readtext(img)  # list of (bbox, text, conf)
        def bbox_top_left(bbox):
            ys = [pt[1] for pt in bbox]
            xs = [pt[0] for pt in bbox]
            return (min(ys), min(xs))
        sorted_results = sorted(results, key=lambda r: bbox_top_left(r[0]))
        texts = [text for _, text, _ in sorted_results]
        return unique_preserve_order(texts)
    except Exception as e:
        print(f"[OCR ERROR] {image_path}: {e}")
        return []

def link_to_knowledge_graph(yolo_entities):
    linked = []
    for ent in yolo_entities:
        norm = ent.lower().strip().replace(" ", "_")
        linked.append(f"local::{norm}")
    return unique_preserve_order(linked)

def build_image_index(image_dir):
    files = [f for f in os.listdir(image_dir) if f.lower().endswith((".jpg", ".png", ".jpeg", ".webp"))]
    index_by_number = {}
    no_number = []
    for f in files:
        num = extract_number_from_filename(f)
        if num is not None:
            index_by_number.setdefault(num, []).append(f)
        else:
            no_number.append(f)
    sorted_by_num = []
    for num in sorted(index_by_number.keys()):
        sorted_by_num.extend(index_by_number[num])
    return {
        "files": files,
        "sorted_by_num": sorted_by_num,
        "index_by_number": index_by_number,
        "no_number": no_number
    }

def load_input(input_path):
    ext = os.path.splitext(input_path)[1].lower()
    if ext in (".xlsx", ".xls"):
        # baca Excel -> DataFrame -> list of dicts
        df = pd.read_excel(input_path, engine="openpyxl")  # openpyxl umum digunakan
        # convert NaN ke None untuk JSON
        df = df.where(pd.notnull(df), None)
        data = df.to_dict(orient="records")
        return data, df
    elif ext == ".json":
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, None
    else:
        raise ValueError(f"Unsupported input file type: {ext}")

def process_images(input_path, image_dir, output_json_path, output_xlsx_path=None):
    try:
        data, df_original = load_input(input_path)
    except Exception as e:
        print(f"[ERROR] Gagal membaca input: {e}")
        return

    img_idx = build_image_index(image_dir)
    image_files_sorted = img_idx["sorted_by_num"] if img_idx["sorted_by_num"] else img_idx["files"]

    print(f"Jumlah entri input: {len(data)}")
    print(f"Jumlah gambar ditemukan: {len(image_files_sorted)}\n")

    # Coba mapping berdasarkan kolom 'id' jika numeric
    use_mapping_by_id = True
    for entry in data:
        pid = entry.get("id") or entry.get("post_id")  # coba dua kemungkinan nama kolom
        try:
            if pid is None:
                raise ValueError("None id")
            int(pid)
        except:
            use_mapping_by_id = False
            break

    mapping = {}
    if use_mapping_by_id:
        for entry in data:
            pid = int(entry.get("id") or entry.get("post_id"))
            candidates = img_idx["index_by_number"].get(pid)
            if candidates:
                chosen = None
                for c in candidates:
                    if c not in mapping.values():
                        chosen = c
                        break
                if chosen is None:
                    chosen = candidates[0]
                mapping[pid] = chosen

    # Untuk menyimpan result dan (opsional) tulis kembali ke DataFrame
    results_list = []
    for i, entry in enumerate(data):
        entry_result = dict(entry)  # salin supaya tidak merusak input asli
        entry_result["detected_objects"] = []
        entry_result["extracted_text_ocr"] = []
        entry_result["linked_image_entities"] = []
        entry_result["image_filename"] = None

        image_filename = None
        if use_mapping_by_id:
            pid = int(entry.get("id") or entry.get("post_id"))
            image_filename = mapping.get(pid)
        else:
            if i < len(image_files_sorted):
                image_filename = image_files_sorted[i]
            else:
                image_filename = None

        image_path = os.path.join(image_dir, image_filename) if image_filename else None
        entry_result["image_filename"] = image_filename

        if image_path and os.path.exists(image_path):
            print(f"Memproses {image_filename} (id/post_id: {entry.get('id') or entry.get('post_id', '?')})")

            objects = detect_objects_yolo(image_path)
            entry_result["detected_objects"] = objects
            print(f"  Objek YOLO: {objects}")

            texts = extract_text_ocr(image_path)
            entry_result["extracted_text_ocr"] = texts
            print(f"  OCR: {texts}")

            linked = link_to_knowledge_graph(objects)
            entry_result["linked_image_entities"] = linked
            print(f"  Entitas KG: {linked}\n")
        else:
            print(f"Gambar tidak ditemukan untuk entri ke-{i+1} (id: {entry.get('id') or entry.get('post_id')})")

        results_list.append(entry_result)

    # simpan JSON output
    try:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(results_list, f, ensure_ascii=False, indent=2)
        print(f"\nData disimpan ke: {output_json_path}")
    except Exception as e:
        print(f"[ERROR] Gagal menyimpan JSON: {e}")

    # juga simpan ke excel jika diminta (berguna untuk review)
    if output_xlsx_path:
        try:
            df_out = pd.DataFrame(results_list)
            df_out.to_excel(output_xlsx_path, index=False)
            print(f"Data juga disimpan ke Excel: {output_xlsx_path}")
        except Exception as e:
            print(f"[ERROR] Gagal menyimpan XLSX: {e}")

if __name__ == "__main__":
    process_images(INPUT_PATH, IMAGE_DIR, OUTPUT_JSON_PATH, OUTPUT_XLSX_PATH)
