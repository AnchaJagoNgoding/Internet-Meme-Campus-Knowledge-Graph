import pandas as pd
import json
import os

def convert_json_to_excel(json_file_path, excel_file_path):
  
    try:
        
        output_dir = os.path.dirname(excel_file_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Direktori output '{output_dir}' dibuat.")

        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        df = pd.DataFrame(data)

       
        df.to_excel(excel_file_path, index=False, engine='xlsxwriter')

        print(f"\nBerhasil mengonversi '{json_file_path}' menjadi '{excel_file_path}'")
        print(f"Total {len(df)} baris data telah ditulis ke Excel.")

    except FileNotFoundError:
        print(f"Error: File JSON tidak ditemukan di '{json_file_path}'.")
    except json.JSONDecodeError:
        print(f"Error: Gagal membaca file JSON di '{json_file_path}'. Pastikan formatnya valid.")
    except Exception as e:
        print(f"Terjadi kesalahan lain saat konversi: {e}")


if __name__ == "__main__":
    data_directory = r"C:\TA KG Baru\data modelling\drama_telyu\data"
    json_filename = "data_with_image_and_text.json" 
    excel_filename = "data_with_image_and_text.xlsx" 

    json_full_path = os.path.join(data_directory, json_filename)
    excel_full_path = os.path.join(data_directory, excel_filename)

    convert_json_to_excel(json_full_path, excel_full_path)