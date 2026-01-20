import pandas as pd

def load_and_prepare_data():
    
    file_path = r"C:\TA KG Baru\data work\data modelling\drama_telyu\data\new_dataset_meme10nop.xlsx"
    df = pd.read_excel(file_path)
    print("Kolom tersedia:", df.columns.tolist())  
    
    
    df_preview = df[[ "id", "caption", "likesCount", "commentsCount", "displayUrl", "url"]].copy()
    return df_preview

if __name__ == "__main__":
    df = load_and_prepare_data()
    print(df.head())