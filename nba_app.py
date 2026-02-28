import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, scoreboardv2
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- 1. CONFIGURAZIONE E STILE (UI MOBILE FRIENDLY) ---
st.set_page_config(page_title="NBA Oracle ULTIMATE", layout="wide", page_icon="🏀", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
    .team-logo { width: 50px; vertical-align: middle; margin: 0 10px; }
    .team-logo-large { width: 80px; margin-bottom: 10px; display: block; }
    .match-header { font-size: 22px; font-weight: 800; text-align: center; margin-bottom: 5px; color: #1E1E1E; }
    .injury-alert { 
        background-color: #fff1f1; color: #d9534f; font-weight: bold; font-size: 14px; 
        margin-bottom: 15px; border: 2px solid #d9534f; padding: 10px; border-radius: 8px; text-align: center;
    }
    .result-box {
        display: flex; justify-content: center; align-items: center; background: #fdfdfd; 
        padding: 12px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #eee; border-left: 5px solid #ff4b4b;
    }
    /* Ottimizzazione per Mobile: forza la visualizzazione pulita delle tabelle */
    [data-testid="stDataFrame"] { width: 100%; overflow-x: auto; }
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

# --- PULSANTE DI AGGIORNAMENTO FORZATO ---
c_title, c_btn = st.columns([7, 3])
with c_title:
    st.title("🏀 NBA Oracle ULTIMATE")
with c_btn:
    if st.button("🔄 Forza Aggiornamento Dati", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- 2. MOTORE DATI (FUSO ORARIO US + FIX INFORTUNI) ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_nba_data():
    try:
        # Fuso orario di New York per allinearsi ai server NBA
        now_est = datetime.now(ZoneInfo("America/New_York"))
        today_str = now_est.strftime('%Y-%m-%d')
        yesterday_str = (now_est - timedelta(1)).strftime('%Y-%m-%d')

        # A. Recupero Database
        season = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame').get_data_frames()[0]
        l10 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=10).get_data_frames()[0]
        l3 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=3).get_data_frames()[0]
        
        # B. MERGE LEFT
        df = pd.merge(season[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']], 
                      l10[['PLAYER_ID', 'PTS', 'AST', 'REB', 'FG3M', 'GP']], 
                      on='PLAYER_ID', how='left', suffixes=('', '_L10'))
        
        df = pd.merge(df, l3[['PLAYER_ID', 'GP']], on='PLAYER_ID', how='left', suffixes=('', '_L3'))
        df = df.fillna(0)
        
        df = df.rename(columns={'PLAYER_NAME': 'Giocatore', 'TEAM_ABBREVIATION': 'Abbr'})
        df['Squadra'] = df['Abbr'].map(TEAM_NAMES)
        df = df[df['MIN'] > 8.0] # Mantiene i top player

        # C. LOGICA INFORTUNI (Calibrata per ridurre i falsi positivi)
        def check_status(r):
            if r['GP_L3'] == 0 and r['GP_L10'] == 0 and r['GP'] > 2: return "❌ OUT"
            elif r['GP_L3'] == 0 and r['GP_L10'] > 0: return "🚑 DUBBIO"
            else: return "✅ OK"
        df['Stato'] = df.apply(check_status, axis=1)

        # D. ANALISI TREND (Migliorata per tabelle strette)
        def get_trend(r):
            if "OUT" in r['Stato']: return "⛔ EVITARE"
            if "DUBBIO" in r['Stato']: return "⚠️ RISCHIO"
            diff = r['PTS_L10'] - r['PTS']
            if diff >= 4.0: return "🔥 OVER Punti"
            elif r['AST_L10'] > r['AST'] + 1.5: return "🎯 OVER Assist"
            elif r['REB_L10'] > r['REB'] + 1.5: return "🧱 OVER Rimb"
            else: return "⚖️ STABILE"
        df['Analisi'] = df.apply(get_trend, axis=1)

        # E. SAFE PICK
        def get_safe(r):
            if r['Stato'] != "✅ OK": return "-"
            val = int(r['PTS_L10'] * 0.72) if r['PTS_L10'] > 0 else int(r['PTS'] * 0.72)
            return f"🟢 OV {val}.5" if val > 8 else "-"
        df['Safe Pick'] = df.apply(get_safe, axis=1)

        # F. Partite Oggi (Forzate con la data US)
        games = scoreboardv2.ScoreboardV2(game_date=today_str).get_data_frames()[0]
        partite_oggi = []
        for _, row in games.iterrows():
            gc = row['GAMECODE']
            away_a, home_a = gc.split('/')[1][:3], gc.split('/')[1][3:]
            partite_oggi.append({'Casa': TEAM_NAMES.get(home_a, home_a), 'CasaAbbr': home_a, 'Trasferta': TEAM_NAMES.get(away_a, away_a), 'TrasfertaAbbr': away_a, 'Status': row['GAME_STATUS_TEXT']})

        # G. Risultati Ieri (Forzati con la data US ieri)
        sb_yesterday = scoreboardv2.ScoreboardV2(game_date=yesterday_str).get_data_frames()
        risultati_ieri = []
        if not sb_yesterday[0].empty:
            header, linescore = sb_yesterday[0], sb_yesterday[1]
            for _, row in header.iterrows():
                h_id, a_id = row['HOME_TEAM_ID'], row['VISITOR_TEAM_ID']
                h_score = linescore[linescore['TEAM_ID'] == h_id]['PTS'].values[0] if not linescore[linescore['TEAM_ID'] == h_id].empty else 0
                a_score = linescore[linescore['TEAM_ID'] == a_id]['PTS'].values[0] if not linescore[linescore['TEAM_ID'] == a_id].empty else 0
                gc_parts = row['GAMECODE'].split('/')[1]
                risultati_ieri.append({
                    'Casa': TEAM_NAMES.get(gc_parts[3:], "Home"), 'CasaAbbr': gc_parts[3:], 'CasaPts': h_score,
                    'Trasferta': TEAM_NAMES.get(gc_parts[:3], "Away"), 'TrasfertaAbbr': gc_parts[:3], 'TrasfertaPts': a_score
                })
        return df, partite_oggi, risultati_ieri
    except Exception as e: 
        return None, None, None

df_totale, partite, risultati = get_nba_data()

if df_totale is None:
    st.error("Errore API NBA. Clicca 'Forza Aggiornamento' in alto."); st.stop()

# --- 3. INTERFACCIA ---
t1, t_res, t2, t3, t4 = st.tabs(["🔥 MATCH DAY", "📅 IERI", "📊 STAGIONE", "📈 L10", "🧮 VANTAGGIO"])

with t1:
    if not partite: st.info("Nessuna partita in programma oggi (in base al fuso orario americano).")
    else:
        for p in partite:
            st.markdown(f'<div class="match-header"><img src="{get_logo(p["CasaAbbr"])}" class="team-logo">{p["CasaAbbr"]} vs {p["TrasfertaAbbr"]}<img src="{get_logo(p["TrasfertaAbbr"])}" class="team-logo"></div>', unsafe_allow_html=True)
            for side in [p['Casa'], p['Trasferta']]:
                lista_out = df_totale[(df_totale['Squadra'] == side) & (df_totale['Stato'] != "✅ OK")]['Giocatore'].tolist()
                if lista_out: st.markdown(f'<div class="injury-alert">🚑 {side.upper()}: {", ".join(lista_out[:5])}</div>', unsafe_allow_html=True)
            
            # Configurazione mobile-friendly per le colonne
            cfg_mobile = {
                "Giocatore": st.column_config.TextColumn("Giocatore", width="medium"),
                "Stato": st.column_config.TextColumn("St", width="small"),
                "PTS_L10": st.column_config.NumberColumn("PTS", format="%.1f"),
                "Analisi": st.column_config.TextColumn("Analisi", width="medium"),
                "Safe Pick": st.column_config.TextColumn("Pick", width="medium")
            }
            col_m = ['Giocatore', 'Stato', 'PTS_L10', 'Analisi', 'Safe Pick']
            
            c1, c2 = st.columns(2)
            with c1: 
                st.markdown(f"**🏠 {p['Casa']}**")
                st.dataframe(df_totale[df_totale['Squadra'] == p['Casa']][col_m].sort_values('PTS_L10', ascending=False).head(10), hide_index=True, use_container_width=True, column_config=cfg_mobile)
            with c2: 
                st.markdown(f"**✈️ {p['Trasferta']}**")
                st.dataframe(df_totale[df_totale['Squadra'] == p['Trasferta']][col_m].sort_values('PTS_L10', ascending=False).head(10), hide_index=True, use_container_width=True, column_config=cfg_mobile)
            st.divider()

with t_res:
    if not risultati: st.info("Risultati di ieri non disponibili.")
    for r in risultati: 
        st.markdown(f'<div class="result-box"><div style="flex:1;text-align:right;"><b>{r["CasaAbbr"]}</b> <img src="{get_logo(r["CasaAbbr"])}" width="35"></div><div style="flex:0.6;text-align:center;font-size:20px;font-weight:bold;color:#1E1E1E;">{r["CasaPts"]} - {r["TrasfertaPts"]}</div><div style="flex:1;text-align:left;"><img src="{get_logo(r["TrasfertaAbbr"])}" width="35"> <b>{r["TrasfertaAbbr"]}</b></div></div>', unsafe_allow_html=True)

def render_db(df, cols, sort_col, cfg=None):
    for s in sorted(df['Squadra'].dropna().unique()):
        # Niente emoji nel titolo dell'expander. Logo grande dentro.
        with st.expander(f"{s}"):
            abbr = df[df['Squadra'] == s]['Abbr'].iloc[0]
            st.markdown(f"<img src='{get_logo(abbr)}' class='team-logo-large'>", unsafe_allow_html=True)
            st.dataframe(df[df['Squadra'] == s][cols].sort_values(sort_col, ascending=False), hide_index=True, use_container_width=True, column_config=cfg)

with t2: render_db(df_totale, ['Giocatore', 'Stato', 'PTS', 'AST', 'REB', 'FG3M', 'GP'], 'PTS')
with t3: render_db(df_totale, ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'FG3M_L10', 'GP_L10'], 'PTS_L10', {"PTS_L10": "PTS", "AST_L10": "AST", "REB_L10": "REB", "FG3M_L10": "3PM"})
with t4:
    st.subheader("Calcolatore Valore Bookmaker")
    p_sel = st.selectbox("Giocatore:", sorted(df_totale['Giocatore'].dropna().tolist()))
    stat = df_totale[df_totale['Giocatore'] == p_sel].iloc[0]
    st.metric(f"Media L10 {p_sel}", f"{stat['PTS_L10']:.1f}", delta=f"Stato: {stat['Stato']}")
    linea = st.number_input("Linea:", step=0.5)
    if linea > 0:
        if stat['PTS_L10'] > linea + 1.5: st.success("🔥 OVER CONSIGLIATO")
        elif stat['PTS_L10'] < linea - 1.5: st.error("❄️ UNDER CONSIGLIATO")
