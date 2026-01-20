import pandas as pd
import os

# --- Konfigurasi Jalur ---
# Jalur ke file Excel awal yang berisi data lengkap
excel_source_path = r"C:\Users\Ancha\OneDrive\Desktop\TA KG Baru\itb_receh\data_with_300plus_likes.xlsx"
# Jalur dan nama file output untuk data yang sudah difilter
output_excel_path = r"C:\Users\Ancha\OneDrive\Desktop\TA KG Baru\itb_receh\data_filtered_itbreceh.xlsx"
output_json_path = r"C:\Users\Ancha\OneDrive\Desktop\TA KG Baru\itb_receh\data_filtered_itbreceh.json"

# --- Konfigurasi Indeks Gambar ---
# Nomor awal yang Anda gunakan saat memberi nama gambar
# Ini harus sama dengan 'start_image_number' di skrip pengunduh gambar Anda
start_image_number = 1482

# --- Daftar Nomor Gambar yang Gagal ---
# PENTING: Anda perlu mengisi list ini dengan nomor-nomor gambar yang gagal
# yang Anda dapatkan dari file 'failed_image_downloads.txt' Anda.
# Contoh: Jika img_1727.jpg dan img_1800.jpg gagal, maka list-nya adalah [1727, 1800]
failed_image_numbers = [
    # Contoh:
    1504,
    1523,
    1568,
    1592,
    1606,
    1624,
    1631,
    1684,
    1687,
    1700,
    1765,
    1824,
    1892,
    1900,
    1901,
    1978,
    1983,
    1990,
    2007,
    2011,
    2022,
    2045,
    2046,
    2055,
    2058,
    2110,
    2115,
    2137,
    2160,
    2176,
    2181,
    2200,
    2228,
    2232,
    2235,
    2298,
    2318,
    2400,
    2422,
    2440,
    2466,
    2531,
    2547,
    2573,
    2630,
    2652,
    2681,
    2791,
    # ... tambahkan nomor-nomor gambar yang gagal di sini
]

# --- Opsional: Muat nomor gambar yang gagal dari file TXT ---
# Anda bisa menggunakan kode ini jika Anda ingin otomatis membaca dari file log
# log_file_path = r"C:\Users\Ancha\OneDrive\Desktop\TA KG Baru\itb_receh\images\failed_image_downloads.txt"
# if os.path.exists(log_file_path):
#     with open(log_file_path, 'r') as f:
#         lines = f.readlines()
#         for line in lines:
#             if "Nomor urut:" in line:
#                 try:
#                     # Ekstrak angka setelah "Nomor urut:"
#                     num_str = line.split("Nomor urut:")[1].strip().split(')')[0].strip()
#                     failed_image_numbers.append(int(num_str))
#                 except ValueError:
#                     print(f"Peringatan: Tidak dapat mengekstrak nomor dari baris log: {line.strip()}")
#     failed_image_numbers = sorted(list(set(failed_image_numbers))) # Hapus duplikat dan urutkan
#     print(f"Nomor gambar gagal yang dimuat dari log: {failed_image_numbers}")
# else:
#     print("File log 'failed_image_downloads.txt' tidak ditemukan. Menggunakan daftar manual.")

# --- Load Data Excel ---
try:
    df = pd.read_excel(excel_source_path)
    print(f"Data berhasil dimuat dari: {excel_source_path}. Jumlah baris: {len(df)}")
except FileNotFoundError:
    print(f"ERROR: File Excel tidak ditemukan di: {excel_source_path}")
    exit()
except Exception as e:
    print(f"ERROR: Terjadi kesalahan saat memuat Excel: {e}")
    exit()

# --- Hitung Indeks Baris yang Perlu Dihapus ---
# Konversi nomor gambar (yang dimulai dari start_image_number) ke indeks DataFrame (dimulai dari 0)
indices_to_drop = []
for failed_num in failed_image_numbers:
    df_index = failed_num - start_image_number
    # Pastikan indeks yang dihitung valid (tidak negatif dan tidak melebihi jumlah baris DataFrame)
    if 0 <= df_index < len(df):
        indices_to_drop.append(df_index)
    else:
        print(f"Peringatan: Nomor gambar {failed_num} menghasilkan indeks di luar batas DataFrame. Melewati.")

# Hapus duplikat indeks jika ada dan urutkan
indices_to_drop = sorted(list(set(indices_to_drop)))

print(f"Indeks baris yang akan dihapus dari DataFrame: {indices_to_drop}")

# --- Hapus Baris dari DataFrame ---
if indices_to_drop:
    df_filtered = df.drop(indices_to_drop).reset_index(drop=True)
    print(f"Berhasil menghapus {len(indices_to_drop)} baris data.")
else:
    df_filtered = df.copy() # Jika tidak ada yang dihapus, buat salinan saja
    print("Tidak ada baris yang perlu dihapus (daftar gambar gagal kosong atau tidak valid).")

print(f"Jumlah baris data setelah difilter: {len(df_filtered)}")

# --- Simpan Data yang Sudah Difilter ---
try:
    df_filtered.to_excel(output_excel_path, index=False)
    print(f"Data yang sudah difilter berhasil disimpan ke: {output_excel_path}")
    df_filtered.to_json(output_json_path, orient="records", force_ascii=False, indent=2)
    print(f"Data yang sudah difilter berhasil disimpan ke: {output_json_path}")
except Exception as e:
    print(f"ERROR: Terjadi kesalahan saat menyimpan data yang difilter: {e}")

