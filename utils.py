import pandas as pd
import unicodedata
import re
from thefuzz import process, fuzz

def remove_accents(input_str):
    """Xóa dấu tiếng Việt và chuyển sang in thường."""
    if not isinstance(input_str, str):
        return ""
    s1 = unicodedata.normalize('NFD', input_str)
    s2 = s1.encode('ascii', 'ignore').decode('utf-8')
    return s2.lower().strip()

def load_data(dm_path='DM.xlsx', th_path='Bang TH.xlsx'):
    """Nạp dữ liệu từ 2 file Excel."""
    # Đọc DM.xlsx không có header
    df_dm = pd.read_excel(dm_path, header=None)
    # Giữ 4 cột đầu tiên và đổi tên
    df_dm = df_dm.iloc[:, :4]
    df_dm.columns = ['ma_loai', 'ma_dinh_muc', 'ten_cong_viec', 'don_vi_tinh']
    
    # Chuẩn hóa để search
    df_dm['ten_cong_viec_norm'] = df_dm['ten_cong_viec'].apply(remove_accents)
    
    # Fill NaN bằng chuỗi rỗng
    df_dm = df_dm.fillna('')

    # Đọc Bang TH.xlsx
    df_th = pd.read_excel(th_path)
    df_th = df_th.fillna('')
    
    return df_dm, df_th

def search_dm(query, df_dm, limit=10):
    """Tìm kiếm mã định mức gần đúng nhất với query."""
    if not query or not isinstance(query, str):
        return pd.DataFrame()
        
    query_norm = remove_accents(query)
    
    # Lọc ban đầu nếu query có trong chuỗi (chính xác hơn)
    mask = df_dm['ten_cong_viec_norm'].str.contains(query_norm, regex=False)
    exact_matches = df_dm[mask].copy()
    
    # Nếu không tìm thấy exact matches thì dùng fuzzy search
    choices_dict = df_dm['ten_cong_viec_norm'].to_dict()
    
    # Dùng thefuzz để extract best matches
    results = process.extract(query_norm, choices_dict, limit=limit, scorer=fuzz.token_set_ratio)
    
    # Lấy ra các index tương ứng
    matched_indices = [idx for (_, _, idx) in results]
    
    # Kết hợp exact matches và fuzzy (ưu tiên exact)
    fuzzy_matches = df_dm.iloc[matched_indices].copy()
    
    if not exact_matches.empty:
        # Hợp nhất và loại bỏ trùng lặp
        combined = pd.concat([exact_matches, fuzzy_matches]).drop_duplicates(subset=['ma_dinh_muc'])
        return combined.head(limit)
    
    return fuzzy_matches.head(limit)
