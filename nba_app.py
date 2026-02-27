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
    .time-text { font-size: 15px; color: #666; text-align: center; margin-bottom: 25px; font-style: italic; }
    .block-container { padding-top: 1.5rem; padding-bottom: 0rem; }
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
    /* Stile per la nuova sezione risultati */
    .result-box {
        display: flex; 
        justify-content: center; 
        align-items: center; 
        background: #fdfdfd; 
        padding: 15px; 
        border-radius: 10px; 
        margin-bottom: 10px; 
        border: 1px solid #eee; 
        border-left: 5px solid #ff4b4b;
    }
    </style>
""", unsafe_allow_html=True)

# Mappatura Completa Squadre NBA (Tutte le 30 squadre presenti)
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
        # A. Recupero Dati (Stagione, Last 10, Last 3 per infortuni lampo)
        season = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame').get_data_frames()[0]
        l10 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=10).get_data_frames()[0]
        l3 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=3).get_data_frames()[0]
        
        # B. Merge dei Database
        df = pd.merge(season[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']], 
                      l10[['PLAYER_ID', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']], 
                      on='PLAYER_ID', suffixes=('', '_L10'))
        
        df = pd.merge(df, l3[['PLAYER_ID', 'GP']], on='PLAYER_ID', suffixes=('', '_L3')).fillna(0)
        
        df = df.rename(columns={'PLAYER_NAME': 'Giocatore', 'TEAM_ABBREVIATION': 'Abbr'})
        df['Squadra'] = df['Abbr'].map(TEAM_NAMES)
        df = df[df['MIN'] > 14.0]

        # LOGICA INFORTUNI (Mitchell Safe)
        def check_status(r):
            if r['GP_L3'] == 0 and r['GP'] > 5: return "❌ OUT"
            elif r['GP_L3'] < 2: return "🚑 RISCHIO/DUBBIO"
            elif r['GP_L10'] < 5: return "🚑 DUBBIO"
            else: return "✅ OK"
        df['Stato'] = df.apply(check_status, axis=1)

        # ANALISI TREND
        def get_trend(r):
            if "OUT" in r['Stato'] or "RISCHIO" in r['Stato']: return "⛔ EVITARE"
            diff = r['PTS_L10'] - r['PTS']
            if diff >= 4.5: return "🔥 OVER Punti"
            elif diff <= -4.5: return "❄️ UNDER Punti"
            elif r['AST_L10'] > r['AST'] + 2: return "🎯 OVER Assist"
            elif r['REB_L10'] > r['REB'] + 2: return "🧱 OVER Rimbalzi"
            else: return "⚖️ STABILE"
        df['Analisi'] = df.apply(get_trend, axis=1)

        # SAFE PICK
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
            partite_oggi.append({
                'Casa': TEAM_NAMES.get(home_a, home_a), 'CasaAbbr': home_a,
                'Trasferta': TEAM_NAMES.get(away_a, away_a), 'TrasfertaAbbr': away_a,
                'Status': row['GAME_STATUS_TEXT']
            })

        # --- SEZIONE RISULTATI IERI (AGGIUNTA SENZA RIMUOVERE NULLA) ---
        yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
        sb_yesterday = scoreboardv2.ScoreboardV2(game_date=yesterday).get_data_frames()
        risultati_ieri = []
        if not sb_yesterday[0].empty:
            header, linescore = sb_yesterday[0], sb_yesterday[1]
            for _, row in header.iterrows():
                h_id, a_id = row['HOME_TEAM_ID'], row['VISITOR_TEAM_ID']
                h_score = linescore[linescore['TEAM_ID'] == h_id]['PTS'].values[0]
                a_score = linescore[linescore['TEAM_ID'] == a_id]['PTS'].values[0]
                gc_parts = row['GAMECODE'].split('/')[1]
                risultati_ieri.append({
                    'Casa': TEAM_NAMES.get(gc_parts[3:], "Home"), 'CasaAbbr': gc_parts[3:], 'CasaPts': h_score,
                    'Trasferta': TEAM_NAMES.get(gc_parts[:3], "Away"), 'TrasfertaAbbr': gc_parts[:3], 'TrasfertaPts': a_score
                })
        
        return df, partite_oggi, risultati_ieri
    except:
        return None, None, None

df_totale, partite, risultati = get_nba_data()

if df_totale is None:
    st.error("Connessione NBA fallita. Ricarica la pagina.")
    st.stop()

# --- 3. INTERFACCIA TABS ---
# Manteniamo esattamente i tuoi tab, aggiungendo quello dei Risultati
t1, t_res, t2, t3, t4 = st.tabs(["🔥 MATCH DAY", "📅 RISULTATI IERI", "📊 DB STAGIONE", "📈 FORMA L10", "🧮 CALCOLATORE"])

with t1:
    if not partite:
        st.info("Nessuna partita oggi.")
    else:
        for p in partite:
            st.markdown(f'<div class="match-header"><img src="{get_logo(p["CasaAbbr"])}" class="team-logo">{p["Casa"]} vs {p["Trasferta"]}<img src="{get_logo(p["TrasfertaAbbr"])}" class="team-logo"></div>', unsafe_allow_html=True)
            st.markdown(f'<p style="text-align:center; color:gray;">Status: {p["Status"]}</p>', unsafe_allow_html=True)
            
            # Radar Infortuni sotto il match
            for side in [p['Casa'], p['Trasferta']]:
                lista_out = df_totale[(df_totale['Squadra'] == side) & (df_totale['Stato'] != "✅ OK")]['Giocatore'].tolist()
                if lista_out:
                    st.markdown(f'<div class="injury-alert">🚑 ASSENZE/DUBBI {side.upper()}: {", ".join(lista_out[:5])}</div>', unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            col_match = ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'Analisi', 'Safe Pick']
            cfg = {"PTS_L10": "PTS", "AST_L10": "AST", "REB_L10": "REB", "Safe Pick": "SAFE 🟢"}
            with c1:
                st.markdown(f"**🏠 {p['Casa']}**")
                st.dataframe(df_totale[df_totale['Squadra'] == p['Casa']][col_match].sort_values('PTS_L10', ascending=False).head(8), hide_index=True, column_config=cfg)
            with c2:
                st.markdown(f"**✈️ {p['Trasferta']}**")
                st.dataframe(df_totale[df_totale['Squadra'] == p['Trasferta']][col_match].sort_values('PTS_L10', ascending=False).head(8), hide_index=True, column_config=cfg)
            st.divider()

with t_res:
    st.subheader("Risultati della notte")
    if not risultati:
        st.info("Nessun risultato disponibile.")
    else:
        for r in risultati:
            st.markdown(f'<div class="result-box"><div style="flex:1;text-align:right;"><b>{r["Casa"]}</b> <img src="{get_logo(r["CasaAbbr"])}" width="35"></div><div style="flex:0.6;text-align:center;font-size:22px;font-weight:bold;color:#ff4b4b;">{r["CasaPts"]} - {r["TrasfertaPts"]}</div><div style="flex:1;text-align:left;"><img src="{get_logo(r["TrasfertaAbbr"])}" width="35"> <b>{r["Trasferta"]}</b></div></div>', unsafe_allow_html=True)

# Funzione Database per Squadre (con LOGHI e NOMI LUNGHI)
def render_db(df, cols, sort_col, cfg=None):
    for s in sorted(df['Squadra'].unique()):
        abbr = df[df['Squadra'] == s]['Abbr'].iloc[0]
        with st.expander(f"🏀 {s}"):
            st.markdown(f"<img src='{get_logo(abbr)}' class='team-logo-small'> **{s}**", unsafe_allow_html=True)
            st.dataframe(df[df['Squadra'] == s][cols].sort_values(sort_col, ascending=False), hide_index=True, use_container_width=True, column_config=cfg)

with t2:
    st.subheader("Database Stagione Completa")
    render_db(df_totale, ['Giocatore', 'Stato', 'PTS', 'AST', 'REB', 'FG3M', 'GP'], 'PTS')

with t3:
    st.subheader("Analisi Forma Ultime 10 Partite")
    render_db(df_totale, ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'FG3M_L10', 'GP_L10'], 'PTS_L10', {"PTS_L10": "PTS", "AST_L10": "AST", "REB_L10": "REB", "FG3M_L10": "3PM"})

with t4:
    st.subheader("Calcolatore Valore")
    p_sel = st.selectbox("Seleziona Giocatore:", sorted(df_totale['Giocatore'].tolist()))
    stat = df_totale[df_totale['Giocatore'] == p_sel].iloc[0]
    st.metric(f"Media Recente {p_sel}", f"{stat['PTS_L10']:.1f}", delta=f"Stato: {stat['Stato']}")
    linea = st.number_input("Inserisci Linea Bookmaker:", step=0.5)
    if linea > 0:
        if stat['PTS_L10'] > linea + 1.5: st.success("🔥 OVER CONSIGLIATO")
        elif stat['PTS_L10'] < linea - 1.5: st.error("❄️ UNDER CONSIGLIATO")
