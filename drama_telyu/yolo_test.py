import os
import cv2
import numpy as np
import easyocr

# ====== KONFIGURASI ======
IMAGE_DIR = r"C:\TA KG Baru\data modelling\drama_telyu\data\images"
OUT_DIR = os.path.join(IMAGE_DIR, "imagesbounding")   # hasil disimpan di sini
GPU_FOR_OCR = False        # ubah ke True jika ada GPU dan EasyOCR dikonfigurasi
CONF_THRESHOLD = 0.3       # hanya tampilkan box OCR dengan confidence >= ambang ini (ubah ke 0.0 untuk semua)
DRAW_CONF = True           # tampilkan nilai confidence pada label
DRAW_TEXT = True           # tampilkan teks OCR pada label (potong bila panjang)

os.makedirs(OUT_DIR, exist_ok=True)

# Inisialisasi EasyOCR reader
print("Inisialisasi EasyOCR...")
reader = easyocr.Reader(["en", "id"], gpu=GPU_FOR_OCR)
print("Reader siap.\n")

def list_images(folder):
    files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
    files.sort()
    return files

def draw_ocr_boxes(image_path, ocr_results, out_path):
    """
    Menggambar polygon bounding box dari hasil OCR (bbox 4 titik),
    menambahkan label teks + confidence, lalu menyimpan output.
    ocr_results: list of tuples (bbox, text, conf)
      bbox: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Gagal membaca gambar: {image_path}")

    for bbox, text, conf in ocr_results:
        # skip jika conf di bawah threshold (jika conf tersedia)
        if conf is not None and conf < CONF_THRESHOLD:
            continue

        # konversi titik bbox ke numpy array (untuk cv2.polylines)
        pts = [(int(pt[0]), int(pt[1])) for pt in bbox]
        pts_np = np.array(pts, dtype=np.int32).reshape((-1,1,2))

        # gambar polygon bounding box (hijau)
        cv2.polylines(img, [pts_np], isClosed=True, color=(0,255,0), thickness=2)

        # label teks + confidence (letakkan di atas titik pertama)
        tx, ty = pts[0]
        ty = max(0, ty - 10)

        label_parts = []
        if DRAW_TEXT:
            # potong teks bila terlalu panjang agar label tidak memakan ruang berlebih
            short_text = text if len(text) <= 40 else text[:37] + "..."
            label_parts.append(short_text)
        if DRAW_CONF and conf is not None:
            label_parts.append(f"{conf:.2f}")
        label = " | ".join(label_parts) if label_parts else None

        if label:
            # hitung ukuran label
            (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            # tentukan background label (jangan keluar gambar)
            lx1 = tx
            ly2 = ty + 2
            ly1 = max(0, ly2 - th - 4)
            lx2 = min(img.shape[1], tx + tw + 6)
            # gambar latar label
            cv2.rectangle(img, (lx1, ly1), (lx2, ly2), (0,255,0), -1)
            # tulis label
            cv2.putText(img, label, (lx1 + 3, ly2 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)

    # simpan output
    base = os.path.basename(image_path)
    out_filepath = os.path.join(out_path, f"ocr_bbox_{base}")
    cv2.imwrite(out_filepath, img)
    return out_filepath

def main():
    files = list_images(IMAGE_DIR)
    if not files:
        print("Tidak ada gambar di folder:", IMAGE_DIR)
        return

    image_filename = files[0]   # hanya proses satu gambar (pertama)
    image_path = os.path.join(IMAGE_DIR, image_filename)
    print("Memproses gambar:", image_filename)

    try:
        # jalankan OCR
        results = reader.readtext(image_path)  # [(bbox, text, conf), ...]
    except Exception as e:
        print("Error saat menjalankan EasyOCR:", e)
        return

    print(f"Jumlah region teks terdeteksi: {len(results)} (sebelum threshold)")

    # sortir berdasarkan posisi top-left agar label muncul rapi (opsional)
    def bbox_top_left(bbox):
        ys = [pt[1] for pt in bbox]
        xs = [pt[0] for pt in bbox]
        return (min(ys), min(xs))
    results_sorted = sorted(results, key=lambda r: bbox_top_left(r[0]))

    # gambar bounding box dan simpan
    try:
        out_file = draw_ocr_boxes(image_path, results_sorted, OUT_DIR)
        print("Gambar hasil OCR bounding box disimpan di:", out_file)
    except Exception as e:
        print("Gagal menggambar/simpan bounding box:", e)

if __name__ == "__main__":
    main()
