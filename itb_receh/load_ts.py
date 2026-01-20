import pandas as pd

def load_and_prepare_data():
    
    file_path = r"C:\TA KG Baru\data modelling\drama_telyu\data\time_stamp_data_itbreceh.xlsx"
    df = pd.read_excel(file_path)
    print("Kolom tersedia:", df.columns.tolist())  
    
    
    df_preview = df[["likesCount", "timestamp"]].copy()
    return df_preview

if __name__ == "__main__":
    df = load_and_prepare_data()
    print(df.head())