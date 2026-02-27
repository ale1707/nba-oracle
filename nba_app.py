import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, scoreboardv2
from datetime import datetime, timedelta

# --- 1. CONFIGURAZIONE E STILE INTEGRALE (TUTTO RIPRISTINATO) ---
st.set_page_config(page_title="NBA Oracle ULTIMATE", layout="wide", page_icon="🏀", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    div[data-testid="stStatusWidget"] {display:none;}
    .team-logo { width: 60px; vertical-align: middle; margin: 0 15px; }
    .team-logo-small { width: 40px; vertical-align: middle; margin-right: 15px; }
    .match-header { font-size: 28px; font-weight: 800; text-align: center; margin-bottom: 5px; color: #1E1E1E; }
    .injury-alert { 
        background-color: #fff1f1; 
        color: #d9534f; 
        font-weight: bold; 
        font-size: 15px; 
        margin-bottom: 15px; 
        border: 2px solid #d9534f; 
        padding: 12px; 
        border-radius: 8px;
        text-align: center;
    }
    .result-box {
        display: flex; justify-content: center; align-items: center; background: #fdfdfd; 
        padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #eee; border-left: 5px solid #1E1E1E;
    }
    </style>
""", unsafe_allow_html=True)

TEAM_NAMES = {
    'ATL': 'Atlanta Hawks', 'BOS': 'Boston Celtics', 'BKN': 'Brooklyn Nets', 'CHA': 'Charlotte Hornets',
    'CHI': 'Chicago Bulls', 'CLE': 'Cleveland Cavaliers', 'DAL': 'Dallas Mavericks', 'DEN': 'Denver Nuggets',
    'DET': 'Detroit Pistons', 'GSW': 'Golden State Warriors', 'HOU': 'Houston Rockets', 'IND': 'Indiana Pacers',
    'LAC': 'LA Clippers', 'LAL': 'Los Angeles Lakers', 'MEM': 'Memphis Grizzlies', 'MIA': 'Miami Heat',
    'MIL': 'Milwaukee Bucks', 'MIN': 'Minnesota Timberwolves', 'NOP': 'New Orleans Pelicans', 'NYK': 'New York Knicks',
    'OKC': 'Oklahoma City Thunder', 'ORL': 'Orlando Magic', 'PHI': 'Philadelphia 76ers', 'PHX': 'Phoenix Suns',
    'POR': 'Portland Trail Blazers', 'SAC': 'Sacramento Kings', 'SAS': 'San Antonio Spurs', 'TOR': 'Toronto Raptors',
    'UTA': 'Utah Jazz', 'WAS': 'Washington Wizards'
}

def get_logo(abbr):
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{abbr.lower()}.png"

# --- 2. MOTORE DI ELABORAZIONE DATI POTENZIATO ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_nba_data():
    try:
        season = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame').get_data_frames()[0]
        l10 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=10).get_data_frames()[0]
        l3 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=3).get_data_frames()[0]
        
        df = pd.merge(season[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']], 
                      l10[['PLAYER_ID', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']], 
                      on='PLAYER_ID', suffixes=('', '_L10'))
        df = pd.merge(df, l3[['PLAYER_ID', 'GP']], on='PLAYER_ID', suffixes=('', '_L3')).fillna(0)
        
        df = df.rename(columns={'PLAYER_NAME': 'Giocatore', 'TEAM_ABBREVIATION': 'Abbr'})
        df['Squadra'] = df['Abbr'].map(TEAM_NAMES)
        df = df[df['MIN'] > 14.0]

        def check_status(r):
            if r['GP_L3'] == 0 and r['GP'] > 5: return "❌ OUT"
            elif r['GP_L3'] < 2: return "🚑 RISCHIO/DUBBIO"
            elif r['GP_L10'] < 5: return "🚑 DUBBIO"
            else: return "✅ OK"
        df['Stato'] = df.apply(check_status, axis=1)

        def get_trend(r):
            if "OUT" in r['Stato'] or "RISCHIO" in r['Stato']: return "⛔ EVITARE"
            diff = r['PTS_L10'] - r['PTS']
            if diff >= 4.5: return "🔥 OVER Punti"
            elif diff <= -4.5: return "❄️ UNDER Punti"
            elif r['AST_L10'] > r['AST'] + 2: return "🎯 OVER Assist"
            elif r['REB_L10'] > r['REB'] + 2: return "🧱 OVER Rimbalzi"
            else: return "⚖️ STABILE"
        df['Analisi'] = df.apply(get_trend, axis=1)

        def get_safe(r):
            if r['Stato'] != "✅ OK": return "---"
            pts_ref = r['PTS_L10'] if r['PTS_L10'] > 0 else r['PTS']
            val = int(pts_ref * 0.72)
            return f"🟢 OVER {val}.5 P" if val > 8 else "---"
        df['Safe Pick'] = df.apply(get_safe, axis=1)

        # Partite del giorno
        games = scoreboardv2.ScoreboardV2().get_data_frames()[0]
        partite_oggi = []
        for _, row in games.iterrows():
            gc = row['GAMECODE']
            away_a, home_a = gc.split('/')[1][:3], gc.split('/')[1][3:]
            partite_oggi.append({'Casa': TEAM_NAMES.get(home_a, home_a), 'CasaAbbr': home_a, 'Trasferta': TEAM_NAMES.get(away_a, away_a), 'TrasfertaAbbr': away_a, 'Status': row['GAME_STATUS_TEXT']})

        # RISULTATI IERI (NUOVA AGGIUNTA SENZA TOGLIERE ALTRO)
        yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
        sb_yesterday = scoreboardv2.ScoreboardV2(game_date=yesterday).get_data_frames()
        res_yesterday = []
        if not sb_yesterday[0].empty:
            header, linescore = sb_yesterday[0], sb_yesterday[1]
            for _, row in header.iterrows():
                h_id, a_id = row['HOME_TEAM_ID'], row['VISITOR_TEAM_ID']
                h_score = linescore[linescore['TEAM_ID'] == h_id]['PTS'].values[0]
                a_score = linescore[linescore['TEAM_ID'] == a_id]['PTS'].values[0]
                gc_parts = row['GAMECODE'].split('/')[1]
                res_yesterday.append({
                    'Casa': TEAM_NAMES.get(gc_parts[3:], "Home"), 'CasaAbbr': gc_parts[3:], 'CasaPts': h_score,
                    'Trasferta': TEAM_NAMES.get(gc_parts[:3], "Away"), 'TrasfertaAbbr': gc_parts[:3], 'TrasfertaPts': a_score
                })

        return df, partite_oggi, res_yesterday
    except:
        return None, None, None

df_totale, partite, risultati = get_nba_data()

if df_totale is None:
    st.error("Connessione NBA fallita. Ricarica la pagina.")
    st.stop()

# --- 3. INTERFACCIA TABS (ORA 5 TABS) ---
t1, t2, t3, t4, t5 = st.tabs
