import streamlit as st
import pandas as pd
import io
from utils import load_data, search_dm

st.set_page_config(page_title="Hỗ Trợ Tra Mã Định Mức", layout="wide")

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .task-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #F3F4F6;
        border-left: 5px solid #3B82F6;
        margin-bottom: 1rem;
    }
    .highlight-text {
        color: #D97706;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Ứng Dụng Hỗ Trợ Tra Mã Định Mức Dự Toán</div>', unsafe_allow_html=True)

# Khởi tạo state
if 'selected_task_idx' not in st.session_state:
    st.session_state.selected_task_idx = None

def go_to_next_task():
    """Chuyển sang công việc kế tiếp"""
    if st.session_state.selected_task_idx is not None:
        if st.session_state.selected_task_idx < len(st.session_state.df_th) - 1:
            st.session_state.selected_task_idx += 1

# --- Sidebar Nạp dữ liệu ---
st.sidebar.header("📂 Nạp Dữ Liệu")
uploaded_dm = st.sidebar.file_uploader("1. Chọn file Từ điển (DM.xlsx)", type=['xlsx'])
uploaded_th = st.sidebar.file_uploader("2. Chọn file cần tra mã (Bang TH.xlsx)", type=['xlsx'])

if uploaded_dm and uploaded_th:
    if st.sidebar.button("Nạp dữ liệu", type="primary"):
        with st.spinner("Đang xử lý dữ liệu..."):
            try:
                df_dm, df_th = load_data(uploaded_dm, uploaded_th)
                st.session_state.df_dm = df_dm
                st.session_state.df_th = df_th
                
                if 'Ma_Dinh_Muc_Ket_Qua' not in st.session_state.df_th.columns:
                    st.session_state.df_th['Ma_Dinh_Muc_Ket_Qua'] = ''
                if 'Ten_Dinh_Muc_Ket_Qua' not in st.session_state.df_th.columns:
                    st.session_state.df_th['Ten_Dinh_Muc_Ket_Qua'] = ''
                
                st.session_state.selected_task_idx = 0
                st.sidebar.success("Nạp dữ liệu thành công!")
            except Exception as e:
                st.sidebar.error(f"Lỗi nạp dữ liệu: {e}")

if 'df_dm' not in st.session_state or 'df_th' not in st.session_state:
    st.info("👈 Vui lòng tải lên 2 file Excel ở thanh bên trái (Sidebar) để bắt đầu.")
    st.stop()


# --- Giao diện chia cột ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📋 Danh sách công việc cần tra mã")
    st.caption("Danh sách các công việc. Dòng màu vàng là công việc đang được chọn.")
    
    # Chuẩn bị dữ liệu hiển thị (Thêm cột trạng thái)
    display_df = st.session_state.df_th[['STT', 'Mô tả công việc mời thầu', 'Ma_Dinh_Muc_Ket_Qua']].copy()
    display_df['Trạng thái'] = display_df['Ma_Dinh_Muc_Ket_Qua'].apply(lambda x: "✅ Đã gán" if str(x).strip() else "⏳ Chờ")
    display_df.insert(0, 'Đang chọn', ['👉' if i == st.session_state.selected_task_idx else '' for i in display_df.index])
    display_df = display_df[['Đang chọn', 'STT', 'Mô tả công việc mời thầu', 'Trạng thái']]
    
    # Cho phép người dùng chuyển dòng bằng Selectbox
    task_options = []
    for idx, row in st.session_state.df_th.iterrows():
        status = "✅" if str(row['Ma_Dinh_Muc_Ket_Qua']).strip() != "" else "⏳"
        task_str = f"[{row['STT']}] {str(row['Mô tả công việc mời thầu'])[:60]}... {status}"
        task_options.append((idx, task_str))
        
    selected_option = st.selectbox(
        "Nhảy đến công việc cụ thể (hoặc click vào dòng trong bảng bên dưới):", 
        options=task_options, 
        format_func=lambda x: x[1],
        index=0 if st.session_state.selected_task_idx is None else st.session_state.selected_task_idx
    )
    
    if selected_option and selected_option[0] != st.session_state.selected_task_idx:
        st.session_state.selected_task_idx = selected_option[0]
        st.rerun()
        
    event = st.dataframe(
        display_df, 
        use_container_width=True, 
        height=500,
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True
    )
    
    if len(event.selection.rows) > 0:
        clicked_idx = event.selection.rows[0]
        actual_idx = display_df.index[clicked_idx]
        if actual_idx != st.session_state.selected_task_idx:
            st.session_state.selected_task_idx = actual_idx
            st.rerun()
    
with col2:
    st.subheader("🔍 Tìm kiếm và Ghép Mã")
    
    if st.session_state.selected_task_idx is not None:
        idx = st.session_state.selected_task_idx
        current_task = st.session_state.df_th.iloc[idx]
        
        st.markdown(f"""
        <div class="task-card">
            <strong>Đang chọn STT:</strong> <span class="highlight-text">{current_task['STT']}</span> <br/>
            <strong>Mô tả:</strong> <span class="highlight-text">{current_task['Mô tả công việc mời thầu']}</span> <br/>
            <strong>Mã đã chọn (hiện tại):</strong> <span style="color:#DC2626; font-weight:bold;">{current_task['Ma_Dinh_Muc_Ket_Qua']}</span>
            - {current_task['Ten_Dinh_Muc_Ket_Qua']}
        </div>
        """, unsafe_allow_html=True)
        
        # Nhập thủ công
        st.write("---")
        st.write("**Nhập mã thủ công (nếu đã biết mã):**")
        col_man1, col_man2 = st.columns([3, 1])
        with col_man1:
            manual_code = st.text_input("Gõ mã định mức (ví dụ: AE.11111):", key=f"manual_{idx}")
        with col_man2:
            st.write("") # padding
            st.write("") # padding
            if st.button("Lưu mã này", key=f"btn_manual_{idx}"):
                if manual_code.strip():
                    st.session_state.df_th.at[idx, 'Ma_Dinh_Muc_Ket_Qua'] = manual_code.strip()
                    st.session_state.df_th.at[idx, 'Ten_Dinh_Muc_Ket_Qua'] = "(Nhập thủ công)"
                    go_to_next_task()
                    st.rerun()
                else:
                    st.warning("Vui lòng nhập mã!")
        
        st.write("---")
        st.write("**Hoặc Tìm kiếm gợi ý (từ file DM.xlsx):**")
        # Khung tìm kiếm, mặc định lấy mô tả công việc
        search_query = st.text_input("Sửa từ khóa để tìm kiếm sát hơn:", value=str(current_task['Mô tả công việc mời thầu']), key=f"search_{idx}")
        
        if search_query:
            with st.spinner("Đang tìm..."):
                results = search_dm(search_query, st.session_state.df_dm)
                
            if not results.empty:
                for r_idx, r_row in results.iterrows():
                    with st.container(border=True):
                        ccol1, ccol2 = st.columns([4, 1])
                        with ccol1:
                            st.write(f"**Mã ĐM:** `{r_row['ma_dinh_muc']}` | **ĐVT:** {r_row['don_vi_tinh']}")
                            st.write(f"**Tên:** {r_row['ten_cong_viec']}")
                        with ccol2:
                            if st.button("Chọn mã này", key=f"btn_{idx}_{r_row['ma_dinh_muc']}"):
                                st.session_state.df_th.at[idx, 'Ma_Dinh_Muc_Ket_Qua'] = r_row['ma_dinh_muc']
                                st.session_state.df_th.at[idx, 'Ten_Dinh_Muc_Ket_Qua'] = r_row['ten_cong_viec']
                                # Chuyển sang task tiếp theo
                                go_to_next_task()
                                st.rerun()
            else:
                st.info("Không tìm thấy mã định mức nào phù hợp với từ khóa này.")
    else:
        st.info("Vui lòng chọn một công việc bên trái để bắt đầu tra mã.")

st.divider()

# --- Xuất kết quả ---
st.subheader("📥 Xuất dữ liệu")
st.write("Sau khi hoàn tất việc ghép mã, bạn có thể tải xuống file Excel chứa kết quả.")

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Ket_Qua')
    return output.getvalue()

if 'df_th' in st.session_state:
    excel_data = convert_df_to_excel(st.session_state.df_th)
    st.download_button(
        label="Tải xuống File Excel",
        data=excel_data,
        file_name='Ket_Qua_Ap_Ma_Du_Toan.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
