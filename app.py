import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. Konfigurasi Tampilan Halaman
st.set_page_config(page_title="Mesin Cuan Bola", page_icon="⚽", layout="wide")
st.title("⚽ Dashboard Manajemen Over/Under")

# 2. Kunci Akses Database (Menggunakan Streamlit Secrets)
@st.cache_resource
def init_connection():
    # Menarik kunci JSON dari brankas rahasia Streamlit
    creds_dict = json.loads(st.secrets["GCP_CREDENTIALS"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

gc = init_connection()
# Membuka Google Sheets Anda (Jangan ubah ID ini)
sheet = gc.open_by_key("1TNC3m3T_n8ggl_S9uk8EHSJbzSE88c0rI5fbcVYgj2U").sheet1

# 3. Menarik Data dari Sheets
def get_data():
    # Mengambil semua data termasuk header
    data = sheet.get_all_records()
    return pd.DataFrame(data)

df = get_data()

# 4. Membangun Antarmuka Web
if not df.empty:
    # Mengamankan kolom profit agar terbaca sebagai angka
    df['Profit'] = pd.to_numeric(df['Profit'], errors='coerce').fillna(0)
    total_profit = df['Profit'].sum()
    total_trigger = len(df)
    
    # Menampilkan Papan Skor (Kartu Metrik)
    st.subheader("📊 Ringkasan Performa Sistem")
    col1, col2 = st.columns(2)
    col1.metric("🔥 Total Pemicu Ditemukan", total_trigger)
    col2.metric("💰 Total Net Profit", f"Rp {total_profit:,.0f}".replace(',', '.'))
    
    st.divider()
    
    # Menampilkan Tabel Utama (Interaktif)
    st.subheader("📋 Riwayat & Jadwal Pertandingan (Database)")
    st.dataframe(df, use_container_width=True)
    
    st.info("💡 **Tips:** Aplikasi ini saat ini berstatus Read-Only untuk memantau data otomatis dari Bot. Untuk mengubah 'Status' dan menginput 'Profit', silakan edit langsung di Google Sheets, dan otomatis akan ter-update di layar ini saat di-refresh.")

else:
    st.warning("Belum ada data pemicu. Bot akan mulai mencatat pertandingan besok pagi!")
