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
        padding-bottom: 1rem;
        border-bottom: 2px solid #e5e7eb;
    }
    .task-card {
        padding: 1.5rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border-left: 6px solid #2563eb;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
    .task-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #111827;
        margin: 0.5rem 0;
        line-height: 1.4;
    }
    .task-status { margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px dashed #93c5fd; }
    .highlight-text {
        color: #D97706;
        font-weight: bold;
    }
    /* Tweak st.tabs slightly */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3.5rem;
        white-space: pre-wrap;
        font-size: 1.1rem;
        font-weight: 600;
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
col1, col2 = st.columns([1, 1.8])

with col1:
    st.subheader("📋 Danh sách công việc cần tra mã")
    st.caption("Danh sách các công việc. Dòng màu vàng là công việc đang được chọn.")
    
    focus_mode = st.checkbox("🔍 Tập trung hiển thị công việc hiện tại (Tự động cuộn)", value=True)
    
    # Chuẩn bị dữ liệu hiển thị (Thêm cột trạng thái)
    display_df = st.session_state.df_th[['STT', 'Mô tả công việc mời thầu', 'Ma_Dinh_Muc_Ket_Qua']].copy()
    display_df['Trạng thái'] = display_df['Ma_Dinh_Muc_Ket_Qua'].apply(lambda x: "✅ Đã gán" if str(x).strip() else "⏳ Chờ")
    display_df.insert(0, '👉', ['👉' if i == st.session_state.selected_task_idx else '' for i in display_df.index])
    display_df = display_df[['👉', 'STT', 'Mô tả công việc mời thầu', 'Trạng thái']]
    display_df = display_df.rename(columns={'Mô tả công việc mời thầu': 'Nội dung công việc'})
    
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

    if focus_mode and st.session_state.selected_task_idx is not None:
        start_idx = max(0, st.session_state.selected_task_idx - 5)
        end_idx = min(len(display_df), st.session_state.selected_task_idx + 15)
        display_df = display_df.iloc[start_idx:end_idx]

    def highlight_row(row):
        if row.name == st.session_state.selected_task_idx:
            return ['background-color: #FEF08A; font-weight: bold; color: #b91c1c'] * len(row)
        return [''] * len(row)

    styled_df = display_df.style.apply(highlight_row, axis=1)
        
    event = st.dataframe(
        styled_df, 
        use_container_width=True, 
        height=500,
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True,
        column_config={
            "👉": st.column_config.TextColumn("👉", width="small"),
            "STT": st.column_config.TextColumn("STT", width="small"),
            "Trạng thái": st.column_config.TextColumn("Trạng thái", width="small"),
            "Nội dung công việc": st.column_config.TextColumn("Nội dung công việc", width="large")
        }
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
            <div><span style="background:#2563eb;color:white;padding:2px 8px;border-radius:12px;font-size:0.8rem;font-weight:bold;">STT: {current_task['STT']}</span></div>
            <div class="task-title">{current_task['Mô tả công việc mời thầu']}</div>
            <div class="task-status">
                <strong>Mã đã chọn:</strong> 
                <span style="color:#dc2626; font-weight:bold; font-size:1.1rem; background:#fee2e2; padding:2px 8px; border-radius:4px; margin-left:4px;">
                    {current_task['Ma_Dinh_Muc_Ket_Qua'] if str(current_task['Ma_Dinh_Muc_Ket_Qua']).strip() else 'Chưa có'}
                </span>
                <span style="margin-left:8px; color:#4b5563; font-style:italic;">{current_task['Ten_Dinh_Muc_Ket_Qua']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔍 Tìm kiếm thuật toán thông minh", "✍️ Nhập mã định mức thủ công"])
        
        with tab1:
            st.caption("Hệ thống sẽ tự động gợi ý mã dựa trên mô tả công việc. Bạn có thể sửa đổi từ khóa để tìm chính xác hơn.")
            search_query = st.text_input("Từ khóa tìm kiếm:", value=str(current_task['Mô tả công việc mời thầu']), key=f"search_{idx}")
            
            if search_query:
                with st.spinner("Đang tìm kết quả phù hợp nhất..."):
                    results = search_dm(search_query, st.session_state.df_dm)
                    
                if not results.empty:
                    st.success(f"Tìm thấy **{len(results)}** kết quả liên quan:", icon="✅")
                    for r_idx, r_row in results.iterrows():
                        with st.container(border=True):
                            ccol1, ccol2 = st.columns([4, 1])
                            with ccol1:
                                st.markdown(f"""
                                    <div style="font-size:1.05rem; font-weight:600; color:#1f2937;">{r_row['ten_cong_viec']}</div>
                                    <div style="color:#4b5563; margin-top:0.4rem;">
                                        <span style="display:inline-block; background:#f3f4f6; padding:2px 8px; border-radius:4px; border:1px solid #d1d5db; margin-right:8px; font-family:monospace; color:#1d4ed8; font-weight:bold;">Mã: {r_row['ma_dinh_muc']}</span>
                                        <span style="display:inline-block; background:#f3f4f6; padding:2px 8px; border-radius:4px; border:1px solid #d1d5db; color:#047857; font-weight:500;">ĐVT: {r_row['don_vi_tinh']}</span>
                                    </div>
                                """, unsafe_allow_html=True)
                            with ccol2:
                                st.write("") # padding vertical
                                if st.button("Chọn mã này", key=f"btn_{idx}_{r_row['ma_dinh_muc']}", use_container_width=True, type="primary"):
                                    st.session_state.df_th.at[idx, 'Ma_Dinh_Muc_Ket_Qua'] = r_row['ma_dinh_muc']
                                    st.session_state.df_th.at[idx, 'Ten_Dinh_Muc_Ket_Qua'] = r_row['ten_cong_viec']
                                    go_to_next_task()
                                    st.rerun()
                else:
                    st.info("Không tìm thấy mã định mức nào phù hợp. Hãy thử rút gọn từ khóa tìm kiếm.", icon="ℹ️")
                    
        with tab2:
            st.info("Sử dụng tính năng này khi bạn đã biết chắc chắn mã định mức cần điền (VD: lấy từ file excel cũ, từ trí nhớ...).", icon="💡")
            col_man1, col_man2 = st.columns([3, 1])
            with col_man1:
                manual_code = st.text_input("Gõ chính xác mã định mức (ví dụ: AE.11111):", key=f"manual_{idx}")
            with col_man2:
                st.write("") # padding
                st.write("") # padding
                if st.button("Lưu mã này", key=f"btn_manual_{idx}", use_container_width=True, type="primary"):
                    if manual_code.strip():
                        st.session_state.df_th.at[idx, 'Ma_Dinh_Muc_Ket_Qua'] = manual_code.strip()
                        st.session_state.df_th.at[idx, 'Ten_Dinh_Muc_Ket_Qua'] = "(Nhập thủ công)"
                        go_to_next_task()
                        st.rerun()
                    else:
                        st.warning("Vui lòng nhập mã trước khi lưu!")
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
