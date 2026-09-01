import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials

# 1. Panggil Rahasia dari GitHub Secrets
API_KEY = os.environ['API_FOOTBALL_KEY']
TELE_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
GCP_JSON = os.environ['GCP_CREDENTIALS']

# Konfigurasi Target Liga (Tier 1 & Tier 2 Saja)
TARGET_LEAGUES = [78, 88, 144, 39, 203, 94, 179] # ID API-Football utk Jerman, Belanda, Belgia, Inggris, Turki, Portugal, Skotlandia

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def tulis_ke_sheets(data_row):
    creds_dict = json.loads(GCP_JSON)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    # Ganti dengan ID Google Sheets Anda (kombinasi huruf/angka panjang dari URL)
    sheet = gc.open_by_key("1TNC3m3T_n8ggl_S9uk8EHSJbzSE88c0rI5fbcVYgj2U").sheet1 
    sheet.append_row(data_row)

def cek_pemicu_hari_ini():
    # Di sinilah kita akan menyedot data API Football untuk mencari: 
    # Tuan Rumah Kalah vs Tim Peringkat Bawah
    
    # [SIMULASI SEMENTARA UNTUK TEST KONEKSI]
    pesan_alert = "🚨 *ALERT CUT-LOSS M2!*\n\nLiga: Bundesliga 🇩🇪\nPemicu: Bayern Munich 0-1 Augsburg\n\n*Siapkan Base Bet Anda di Match Berikutnya!*"
    kirim_telegram(pesan_alert)
    
    # Mencatat Log ke Google Sheets
    tulis_ke_sheets(["02-09-2026", "Bundesliga", "Bayern Munich", "Augsburg", "TRIGGERED"])

if __name__ == "__main__":
    print("Memulai pemindaian data pertandingan...")
    cek_pemicu_hari_ini()
    print("Selesai!")
