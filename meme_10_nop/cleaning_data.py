from load import load_and_prepare_data
import os

df_preview = load_and_prepare_data()

def filter_and_save_data(df, min_likes=499):
    output_dir = r"C:\TA KG Baru\data modelling\meme_10_nop\data"
    os.makedirs(output_dir, exist_ok=True)

    filtered_df = df[df["likesCount"] > min_likes].copy()

    excel_path = os.path.join(output_dir, "cleaned_timestamp_data_meme10nopember.xlsx")
    filtered_df.to_excel(excel_path, index=False)

    
    print(f"Data difilter dan disimpan ulang ke:\n{excel_path}")
    return filtered_df

filtered = filter_and_save_data(df_preview)
