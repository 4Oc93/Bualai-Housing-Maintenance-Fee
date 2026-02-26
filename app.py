import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
import os
import io
import traceback
import requests
import base64

# --- 1. Page Configuration ---
st.set_page_config(page_title="ระบบเก็บเงินส่วนกลาง", layout="wide", initial_sidebar_state="expanded")

# ==========================================
#  ตั้งค่าลิงก์และ ID 
# ==========================================
DRIVE_FOLDER_ID = "1TBtWb9n8ju2cgBfiwOHJFKhktidxv7d-" 
SHEET_EDIT_URL = "https://docs.google.com/spreadsheets/d/1_1mz0yCDSXHHAYFiYPWGifugAJHwliD7iv8dtF-8Ohs/edit"
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT2YdRqtZKoB0M2vh_vYUPeps4_rb4zTP_r0hMBzsbMqqzKIhMQmNVH1e5sCyomfM6l92gCnpd3oqc3/pub?gid=922014835&single=true&output=csv"
# ==========================================

# Safe for Cloud
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap');
    
    /* 🌟 แก้ไขที่ 1: เปลี่ยนฟอนต์แบบปลอดภัย (ไม่ใช้ * !important เพื่อป้องกันไอคอนพัง) */
    html, body, div, span, p, h1, h2, h3, h4, h5, h6, li, a, button, input, select, textarea {
        font-family: '-apple-system', 'BlinkMacSystemFont', 'Prompt', sans-serif;
    }
    
    /* 🌟 แก้ไขที่ 2: คืนชีพฟอนต์ไอคอนให้กลับมาทำงาน 100% (แก้ปัญหาคำว่า keyboard_double...) */
    .material-symbols-rounded, .material-symbols-outlined, [class*="material-symbols"], .stIcon {
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    }

    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    
    /* 🌟 แก้ไขที่ 3: ยกเลิกการซ่อน stToolbar ตามที่ทีมแนะนำ ซ่อนเฉพาะ Deploy/Menu */
    [data-testid="stHeader"] { background-color: transparent !important; }
    .stAppDeployButton, [data-testid="stAppDeployButton"] { display: none !important; }
    #MainMenu { display: none !important; }
    
    /* 🌟 Apple Style KPI Cards: ล็อกขนาดตายตัว 145px */
    [data-testid="stMetric"] {
        background: rgba(130, 130, 130, 0.05) !important; 
        backdrop-filter: blur(10px) !important; 
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(130, 130, 130, 0.2) !important;
        border-radius: 16px !important; 
        padding: 16px 20px !important; 
        box-shadow: 0 4px 24px rgba(0,0,0,0.04) !important;
        
        height: 145px !important;
        min-height: 145px !important; 
        max-height: 145px !important;
        
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important; 
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
        overflow: hidden !important; 
        cursor: pointer !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: clamp(0.75rem, 1.2vw, 0.95rem) !important; 
        white-space: normal !important; 
        line-height: 1.2 !important;
        min-height: 35px !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: clamp(1.1rem, 2.2vw, 1.8rem) !important; 
        white-space: normal !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1) !important;
        border-color: #34C759 !important;
    }
    
    [data-testid="stHorizontalBlock"] > div { display: flex; }
    [data-testid="stHorizontalBlock"] > div > div { width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- 🚀 ฟังก์ชันอัปโหลดไฟล์ผ่าน GAS ---
def upload_via_gas(file_bytes, filename, mimetype):
    try:
        gas_url = st.secrets.get("gas_url")
        if not gas_url:
            return "ERROR: กรุณาตั้งค่า gas_url ใน secrets.toml"
        
        base64_data = base64.b64encode(file_bytes).decode('utf-8')
        payload = {
            "folderId": DRIVE_FOLDER_ID,
            "filename": filename,
            "mimetype": mimetype,
            "base64": base64_data
        }
        
        response = requests.post(gas_url, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                return result.get("url")
            else:
                return f"ERROR_GAS: {result.get('message')}"
        return f"ERROR_HTTP: {response.status_code}"
    except Exception as e:
        return f"ERROR_EXCEPTION: {str(e)}"

# --- 2. ฟังก์ชันโหลดข้อมูล ---
@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        df['ยอดเรียกเก็บ (บาท)'] = pd.to_numeric(df['ยอดเรียกเก็บ (บาท)'], errors='coerce').fillna(0)
        df['ห้องที่'] = df['ห้องที่'].astype(str)
        return df
    except Exception as e:
        st.error(f"⚠️ โหลดข้อมูลไม่สำเร็จ: {e}")
        return pd.DataFrame()

if 'df' not in st.session_state:
    st.session_state.df = load_data()

df = st.session_state.df

# --- 3. Sidebar ---
with st.sidebar:
    if os.path.exists("logo1.png"):
        st.image("logo1.png", use_container_width=True)
    else:
        st.markdown("<h3 style='text-align:center;'>🏢 ระบบเก็บเงินส่วนกลาง</h3>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("<p style='font-weight:600;font-size:14px;'>🏦 บัญชีสำหรับโอนเงิน</p>", unsafe_allow_html=True)
    if os.path.exists("logo2.png"):
        st.image("logo2.png", width=60)
    st.markdown("<b>ธนาคารออมสิน</b> สาขาบัวลาย<br>ชื่อบัญชี: บ้านพักโรงพยาบาลบัวลาย", unsafe_allow_html=True)
    st.code("020357340189", language="text")
    st.divider()
    
    if not df.empty:
        month_list = df['เดือน/ปี (Date)'].unique()
        selected_month = st.selectbox("📅 เลือกเดือน", month_list, index=len(month_list)-1 if len(month_list) > 0 else 0)
    
    st.markdown("#### 📤 แจ้งโอนเงิน")
    if not df.empty and selected_month:
        df_unpaid = df[(df['เดือน/ปี (Date)'] == selected_month) & (df['สถานะ'] == 'ยังไม่จ่าย')].copy()
        
        if not df_unpaid.empty:
            df_unpaid['label'] = df_unpaid['ชื่อผู้เข้าพัก'] + " (" + df_unpaid['บ้านพัก'] + " " + df_unpaid['ห้องที่'] + ")"
            room_map = dict(zip(df_unpaid['label'], df_unpaid['ห้องที่']))
            selected_display = st.selectbox("เลือกชื่อผู้เข้าพัก", list(room_map.keys()))
            
            with st.form("payment_form", clear_on_submit=True):
                pay_date = st.date_input("วันที่โอนเงิน")
                uploaded_file = st.file_uploader("แนบสลิป", type=['jpg', 'jpeg', 'png'])
                submitted = st.form_submit_button("บันทึกการแจ้งโอน", use_container_width=True)
                
                if submitted:
                    actual_room_id = room_map[selected_display]
                    slip_link = "แจ้งโอน (ไม่มีสลิป)"
                    
                    if uploaded_file:
                        with st.spinner("🚀 กำลังส่งสลิปผ่านสะพาน GAS..."):
                            fname = f"Slip_{actual_room_id}_{selected_month.replace('/','-')}.jpg"
                            upload_result = upload_via_gas(uploaded_file.getvalue(), fname, uploaded_file.type)
                            if upload_result and "ERROR" not in upload_result:
                                slip_link = upload_result
                            else:
                                st.error("❌ การอัปโหลดล้มเหลว ตรวจสอบ URL ของ GAS")
                                st.code(upload_result)
                                st.stop()
                    
                    idx = df[(df['เดือน/ปี (Date)'] == selected_month) & (df['ห้องที่'] == actual_room_id)].index
                    if not idx.empty:
                        st.session_state.df.loc[idx, 'สถานะ'] = 'จ่ายแล้ว'
                        st.session_state.df.loc[idx, 'วันที่ชำระเงิน'] = pay_date.strftime("%d/%m/%Y")
                        st.session_state.df.loc[idx, 'ลิงก์สลิปอ้างอิง'] = slip_link
                        
                        with st.spinner("💾 อัปเดต Google Sheets..."):
                            try:
                                from streamlit_gsheets import GSheetsConnection
                                conn = st.connection("gsheets", type=GSheetsConnection)
                                df_to_save = st.session_state.df.copy().fillna("")
                                conn.update(spreadsheet=SHEET_EDIT_URL, worksheet="Transaction", data=df_to_save)
                                st.cache_data.clear()
                                st.success(f"✅ บันทึกห้อง {actual_room_id} สำเร็จ!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ เขียนลง Sheets ล้มเหลว: {e}")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- 4. Main Content ---
if selected_month and not df.empty:
    def get_thai_month_year(m_y_str):
        try:
            m, y = m_y_str.split('/')
            thai_months = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
            return f"{thai_months[int(m) - 1]} {int(y) + 543}"
        except: return m_y_str

    display_month = get_thai_month_year(selected_month)
    st.markdown(f"### เรียกเก็บเงินส่วนกลางบ้านพักโรงพยาบาลบัวลาย ประจำเดือน {display_month}")

    df_filtered = df[df['เดือน/ปี (Date)'] == selected_month]
    df_active = df_filtered[df_filtered['สถานะ'] != 'ไม่เรียกเก็บ']
    df_exempt = df_filtered[df_filtered['สถานะ'] == 'ไม่เรียกเก็บ']

    target_amt = df_active['ยอดเรียกเก็บ (บาท)'].sum()
    paid_amt = df_active[df_active['status' if 'status' in df_active else 'สถานะ'] == 'จ่ายแล้ว']['ยอดเรียกเก็บ (บาท)'].sum()
    paid_n = len(df_active[df_active['สถานะ'] == 'จ่ายแล้ว'])
    unpaid_n = len(df_active[df_active['สถานะ'] == 'ยังไม่จ่าย'])
    exempt_n = len(df_exempt)

    # 🌟 KPI Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🎯 เป้าหมายรับเงิน", f"฿{target_amt:,.0f}")
    pct = (paid_amt/target_amt)*100 if target_amt > 0 else 0
    c2.metric("💰 เก็บได้แล้ว", f"฿{paid_amt:,.0f}", f"{pct:.1f}%")
    c3.metric("✅ จ่ายแล้ว (ห้อง)", paid_n)
    c4.metric("❌ ยังไม่จ่าย (ห้อง)", unpaid_n, "- ต้องตาม" if unpaid_n > 0 else None, delta_color="inverse")
    c5.metric("⚪ ห้องว่าง/ไม่เรียกเก็บ", exempt_n)

    st.markdown("<br>", unsafe_allow_html=True)
    ch_col, tb_col = st.columns([1.2, 2])

    with ch_col:
        st.markdown("##### ความคืบหน้าการชำระเงิน")
        if target_amt > 0:
            fig = go.Figure(go.Indicator(
                mode = "gauge+number", value = pct,
                number = {'suffix': "%", 'font': {'size': 56, 'color': '#34C759', 'weight': 'bold'}},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [0, 100], 'visible': False},
                    'bar': {'color': "#34C759", 'thickness': 0.85}, 
                    'bgcolor': "rgba(130,130,130,0.06)", 
                    'borderwidth': 0, # เอาเส้นขอบออก
                }
            ))
            fig.update_layout(margin=dict(t=20, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', height=280)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown(f"<p style='text-align:center; color:gray; font-size:14px; margin-top:-30px;'>สำเร็จแล้ว {paid_n} จาก {paid_n + unpaid_n} ห้อง</p>", unsafe_allow_html=True)

    with tb_col:
        t1, t2, t3 = st.tabs(["🔴 ยังไม่จ่าย", "🟢 จ่ายแล้ว", "⚪ ไม่เรียกเก็บ"])
        with t1: st.dataframe(df_active[df_active['สถานะ'] == 'ยังไม่จ่าย'][['บ้านพัก', 'ห้องที่', 'ชื่อผู้เข้าพัก', 'ยอดเรียกเก็บ (บาท)']], use_container_width=True, hide_index=True, height=350)
        with t2: st.dataframe(df_active[df_active['สถานะ'] == 'จ่ายแล้ว'][['บ้านพัก', 'ห้องที่', 'ชื่อผู้เข้าพัก', 'วันที่ชำระเงิน', 'ลิงก์สลิปอ้างอิง']], use_container_width=True, hide_index=True, height=350, column_config={"ลิงก์สลิปอ้างอิง": st.column_config.LinkColumn()})
        with t3: st.dataframe(df_exempt[['บ้านพัก', 'ห้องที่', 'ชื่อผู้เข้าพัก', 'สถานะ']], use_container_width=True, hide_index=True, height=350)

# JS สลับแท็บเมื่อคลิก KPI
components.html("""
    <script>
    function attachKpiListeners() {
        var metrics = window.parent.document.querySelectorAll('[data-testid="stMetric"]');
        var tabs = window.parent.document.querySelectorAll('button[role="tab"]');
        if(metrics.length >= 5 && tabs.length >= 3) {
            metrics[1].onclick = metrics[2].onclick = function() { tabs[1].click(); };
            metrics[3].onclick = function() { tabs[0].click(); };
            metrics[4].onclick = function() { tabs[2].click(); };
        } else { setTimeout(attachKpiListeners, 500); }
    } attachKpiListeners();
    </script>
    """, height=0)