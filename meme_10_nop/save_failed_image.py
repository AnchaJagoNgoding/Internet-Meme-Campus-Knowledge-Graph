import os
import re
from collections import Counter

# ---------- konfigurasi ----------
image_folder = r"C:\TA KG Baru\data modelling\meme_10_nop\data\images"
# pola: img_001.jpg, img-001.JPG, img001.png, dll.
pattern = re.compile(r"img[_\-]?0*?(\d+)\.(jpg|jpeg|png|webp)$", re.IGNORECASE)
# ----------------------------------

all_files = os.listdir(image_folder)

# kumpulkan nomor yang ada dan panjang padding
nums = []
paddings = []
for fn in all_files:
    fn_stripped = fn.strip()
    m = pattern.search(fn_stripped)
    if m:
        num_str = m.group(1)
        nums.append(int(num_str))
        # hitung panjang sebenarnya (group 1 bisa tanpa leading zeros karena regex uses 0*?)
        # kita hitung full digits part by finding digits after 'img_' before dot
        m2 = re.search(r"img[_\-]?(\d+)\.(?:jpg|jpeg|png|webp)$", fn_stripped, re.IGNORECASE)
        if m2:
            paddings.append(len(m2.group(1)))

if not nums:
    print("Tidak ditemukan file gambar yang cocok pola 'img_<angka>.<ext>' di folder.")
else:
    nums_sorted = sorted(set(nums))
    min_n, max_n = nums_sorted[0], nums_sorted[-1]
    # padding paling umum untuk suggested filename
    padding = Counter(paddings).most_common(1)[0][0] if paddings else max(3, len(str(max_n)))

    # cari missing angka di rentang min..max
    missing = [i for i in range(min_n, max_n + 1) if i not in nums_sorted]

    print(f"Ditemukan nomor dari {min_n} sampai {max_n} (total unique present: {len(nums_sorted)})")
    print(f"Padding suggested: {padding} digit (contoh: img_{min_n:0{padding}d}.jpg)\n")

    print("=== DAFTAR INDEKS YANG MISSING ===")
    if missing:
        for i in missing:
            suggested = f"img_{i:0{padding}d}.jpg"
            print(i)  # hanya tampilkan indeks (sesuai permintaan)
        print(f"\nTotal missing: {len(missing)}")
    else:
        print("Tidak ada indeks yang missing — rentang penuh.")
