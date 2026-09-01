import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# Kredensial dari GitHub Secrets
API_KEY = os.environ['API_FOOTBALL_KEY']
TELE_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
GCP_JSON = os.environ['GCP_CREDENTIALS']

# ID Liga Target (Berdasarkan Backtesting 11 Tahun: Tier 1 & 2)
# 39: Premier League, 78: Bundesliga, 88: Eredivisie, 144: Pro League, 203: Super Lig, 94: Primeira Liga, 179: Premiership
TARGET_LEAGUES = [39, 78, 88, 144, 203, 94, 179]
# Target Musim (Otomatis menggunakan tahun berjalan)
CURRENT_SEASON = datetime.now().year

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def tulis_ke_sheets(data_row):
    try:
        creds_dict = json.loads(GCP_JSON)
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        # ID Google Sheets Anda
        sheet = gc.open_by_key("1TNC3m3T_n8ggl_S9uk8EHSJbzSE88c0rI5fbcVYgj2U").sheet1 
        sheet.append_row(data_row)
    except Exception as e:
        print(f"Gagal menulis ke Sheets: {e}")

def ambil_klasemen(league_id):
    """Menarik data klasemen sementara untuk melihat posisi (rank) tim."""
    url = "https://v3.football.api-sports.io/standings"
    headers = {"x-apisports-key": API_KEY}
    params = {"league": league_id, "season": CURRENT_SEASON}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['results'] > 0:
            standings = data['response'][0]['league']['standings'][0]
            # Buat dictionary pemetaan: ID Tim -> Peringkat (Rank)
            rank_map = {team['team']['id']: team['rank'] for team in standings}
            return rank_map
    return {}

def cek_pemicu_kemarin():
    """Mencari pertandingan H-1 di mana Tuan Rumah kalah dari Tim Peringkat Lebih Rendah."""
    kemarin = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    hari_ini = datetime.now().strftime('%d-%m-%Y')
    
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_KEY}
    
    laga_ditemukan = 0
    
    for league_id in TARGET_LEAGUES:
        # 1. Ambil klasemen liga ini
        klasemen = ambil_klasemen(league_id)
        if not klasemen:
            continue
            
        # 2. Ambil jadwal pertandingan H-1 di liga ini
        params = {"league": league_id, "season": CURRENT_SEASON, "date": kemarin}
        res = requests.get(url, headers=headers, params=params)
        
        if res.status_code == 200:
            fixtures = res.json().get('response', [])
            
            for match in fixtures:
                # Pastikan pertandingan sudah selesai (Match Finished)
                if match['fixture']['status']['short'] == 'FT':
                    home_team_id = match['teams']['home']['id']
                    away_team_id = match['teams']['away']['id']
                    home_name = match['teams']['home']['name']
                    away_name = match['teams']['away']['name']
                    home_goals = match['goals']['home']
                    away_goals = match['goals']['away']
                    league_name = match['league']['name']
                    
                    # Logika Pemicu: Tuan Rumah Kalah
                    if home_goals < away_goals:
                        home_rank = klasemen.get(home_team_id, 99)
                        away_rank = klasemen.get(away_team_id, 99)
                        
                        # Syarat Utama: Peringkat Tuan Rumah lebih tinggi (angka rank lebih kecil) dari Tamu
                        if home_rank < away_rank:
                            pesan_alert = (f"🚨 *ALGORITMA TRIGGERED!* 🚨\n\n"
                                           f"🏆 *Liga:* {league_name}\n"
                                           f"📉 *Pemicu:* {home_name} (Rank {home_rank}) KALA di kandang vs {away_name} (Rank {away_rank})\n"
                                           f"⚽ *Skor Akhir:* {home_goals} - {away_goals}\n\n"
                                           f"⚠️ *TINDAKAN:* Pantau pertandingan `{home_name}` berikutnya untuk M1 (Over Gol). "
                                           f"Ingat aturan Cut-Loss M2!")
                            
                            print(f"Pemicu ditemukan: {home_name} vs {away_name}")
                            kirim_telegram(pesan_alert)
                            
                            # Catat ke Database Sheets
                            tulis_ke_sheets([hari_ini, league_name, home_name, away_name, f"{home_goals}-{away_goals}", "MENUNGGU M1", "-"])
                            laga_ditemukan += 1

    if laga_ditemukan == 0:
        print("Tidak ada tim pemicu target hari ini.")
        # Opsional: Bisa diaktifkan jika ingin bot selalu laporan tiap pagi meski tidak ada pemicu
        # kirim_telegram("✅ *Laporan Harian:* Tidak ada tim tuan rumah favorit yang kalah kemarin. Modal aman!")

if __name__ == "__main__":
    print(f"Memulai pemindaian data pertandingan tanggal {(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}...")
    cek_pemicu_kemarin()
    print("Pemindaian Selesai!")
