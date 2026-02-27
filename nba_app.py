import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, scoreboardv2
import time

# --- 1. CONFIGURAZIONE E STILE AVANZATO ---
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
    .stExpander { border: 1px solid #e6e6e6; border-radius: 8px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# Mappatura Completa Squadre NBA
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

# --- 2. MOTORE DI ELABORAZIONE DATI ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_nba_data():
    try:
        # A. Recupero Dati Stagione Completa
        season = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame').get_data_frames()[0]
        df_sea = season[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']]
        
        # B. Recupero Dati Ultime 10 Partite (Last 10)
        l10 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=10).get_data_frames()[0]
        df_l10 = l10[['PLAYER_ID', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']]
        
        # C. Merge e Calcoli Avanzati
        df = pd.merge(df_sea, df_l10, on='PLAYER_ID', suffixes=('', '_L10'), how='left').fillna(0)
        df = df.rename(columns={'PLAYER_NAME': 'Giocatore', 'TEAM_ABBREVIATION': 'Abbr'})
        df['Squadra'] = df['Abbr'].map(TEAM_NAMES)
        
        # Filtro Minutaggio (solo giocatori attivi)
        df = df[df['MIN'] > 14.0]

        # LOGICA 1: STATUS INFORTUNI / ASSENZE (Radar Mitchell)
        def check_status(r):
            if r['GP_L10'] == 0 and r['GP'] > 8: return "❌ OUT (Assente)"
            elif r['GP_L10'] < 3 and r['GP'] > 15: return "🚑 DUBBIO (Rischio)"
            elif r['MIN_L10'] < (r['MIN'] * 0.5): return "⚠️ MINUTI LIMITATI"
            else: return "✅ DISPONIBILE"
        df['Stato'] = df.apply(check_status, axis=1)

        # LOGICA 2: ANALISI DEL TREND (PRONOSTICO)
        def get_trend(r):
            if "OUT" in r['Stato'] or "DUBBIO" in r['Stato']: return "⛔ SALTARE"
            diff_pts = r['PTS_L10'] - r['PTS']
            if diff_pts >= 4.5: return "🔥 OVER Punti (Hot)"
            elif diff_pts <= -4.5: return "❄️ UNDER Punti (Cold)"
            elif r['AST_L10'] > r['AST'] + 2: return "🎯 OVER Assist"
            elif r['REB_L10'] > r['REB'] + 2.5: return "🧱 OVER Rimbalzi"
            elif r['FG3M_L10'] >= 3.5: return "💦 BOMBER (Triple)"
            else: return "⚖️ LINEA STABILE"
        df['Analisi'] = df.apply(get_trend, axis=1)

        # LOGICA 3: SAFE PICK (GIOCATA SICURA)
        def get_safe_pick(r):
            if "OUT" in r['Stato'] or "DUBBIO" in r['Stato']: return "---"
            ref = r['PTS_L10'] if r['PTS_L10'] > 5 else r['PTS']
            safe_val = int(ref * 0.72)
            if safe_val > 8: return f"🟢 OVER {safe_val}.5 P"
            elif r['AST_L10'] >= 6.5: return f"🟢 OVER {int(r['AST_L10']*0.6)}.5 A"
            else: return "🟢 OVER 5.5 P"
        df['Safe Pick'] = df.apply(get_safe_pick, axis=1)

        # D. Recupero Partite Odierne
        games = scoreboardv2.ScoreboardV2().get_data_frames()[0]
        partite_oggi = []
        for _, row in games.iterrows():
            gc = row['GAMECODE']
            away_a, home_a = gc.split('/')[1][:3], gc.split('/')[1][3:]
            partite_oggi.append({
                'Casa': TEAM_NAMES.get(home_abbr := home_a, home_a), 'CasaAbbr': home_a,
                'Trasferta': TEAM_NAMES.get(away_abbr := away_a, away_a), 'TrasfertaAbbr': away_a,
                'Status': row['GAME_STATUS_TEXT']
            })

        return df, partite_oggi
    except Exception as e:
        return None, None

with st.spinner("🚀 Sincronizzazione Database NBA Ultimate in corso..."):
    df_totale, partite = get_nba_data()

if df_totale is None:
    st.error("❌ Connessione fallita. Ricarica la pagina.")
    st.stop()

# --- 3. INTERFACCIA UTENTE (TABS) ---
t1, t2, t3, t4 = st.tabs(["🏀 MATCH DAY", "📊 DATABASE STAGIONE", "📈 TREND RECENTE (L10)", "🧮 CALCOLATORE"])

# TAB 1: MATCH LIVE E PRONOSTICI
with t1:
    if not partite:
        st.info("Nessuna partita in programma per oggi.")
    else:
        for p in partite:
            st.markdown(f"""
            <div class="match-header">
                <img src="{get_logo(p['CasaAbbr'])}" class="team-logo">{p['Casa']} VS {p['Trasferta']}<img src="{get_logo(p['TrasfertaAbbr'])}" class="team-logo">
            </div>
            <div class="time-text">Status Partita: {p['Status']}</div>
            """, unsafe_allow_html=True)

            # RILEVATORE ASSENZE PER IL MATCH (Radar Mitchell)
            for team_name in [p['Casa'], p['Trasferta']]:
                lista_out = df_totale[(df_totale['Squadra'] == team_name) & (df_totale['Stato'] != "✅ DISPONIBILE")]['Giocatore'].tolist()
                if lista_out:
                    st.markdown(f'<div class="injury-alert">🚑 ASSENZE {team_name.upper()}: {", ".join(lista_out[:5])}</div>', unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            # COLONNE COMPLETE: PTS, AST, REB, ANALISI, SAFE
            cols_disp = ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'Analisi', 'Safe Pick']
            cfg_table = {"PTS_L10": "Punti", "AST_L10": "Ass", "REB_L10": "Rimb", "Safe Pick": "GIOCATA SICURA 🟢"}
            
            with c1:
                st.markdown(f"**🏠 {p['Casa']}**")
                st.dataframe(df_totale[df_totale['Squadra'] == p['Casa']][cols_disp].sort_values('PTS_L10', ascending=False).head(8), hide_index=True, column_config=cfg_table)
            with c2:
                st.markdown(f"**✈️ {p['Trasferta']}**")
                st.dataframe(df_totale[df_totale['Squadra'] == p['Trasferta']][cols_disp].sort_values('PTS_L10', ascending=False).head(8), hide_index=True, column_config=cfg_table)
            st.divider()

# FUNZIONE PER I DATABASE A TENDINA CON LOGHI
def build_db(df, columns, sort_col, config=None):
    squadre = sorted(df['Squadra'].dropna().unique())
    for s in squadre:
        abbr = df[df['Squadra'] == s]['Abbr'].iloc[0]
        with st.expander(f"🏀 {s.upper()}"):
            st.markdown(f"<img src='{get_logo(abbr)}' class='team-logo-small'> **{s} - Roster & Statistiche**", unsafe_allow_html=True)
            st.dataframe(df[df['Squadra'] == s][columns].sort_values(sort_col, ascending=False), hide_index=True, use_container_width=True, column_config=config)

with t2:
    st.subheader("🗄️ Database Statistiche Stagione Completa")
    build_db(df_totale, ['Giocatore', 'Stato', 'PTS', 'AST', 'REB', 'FG3M', 'GP'], 'PTS')

with t3:
    st.subheader("📈 Analisi della Forma (Ultime 10 Partite)")
    cfg_l10 = {"PTS_L10": "PTS", "AST_L10": "AST", "REB_L10": "REB", "FG3M_L10": "3PM", "GP_L10": "Partite Giocate"}
    build_db(df_totale, ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'FG3M_L10', 'GP_L10'], 'PTS_L10', cfg_l10)

with t4:
    st.subheader("🧮 Calcolatore Vantaggio Matematico")
    sel_p = st.selectbox("Seleziona Giocatore:", sorted(df_totale['Giocatore'].tolist()))
    row_p = df_totale[df_totale['Giocatore'] == sel_p].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Media Stagione", f"{row_p['PTS']:.1f}")
    col2.metric("Forma (L10)", f"{row_p['PTS_L10']:.1f}", delta=round(row_p['PTS_L10']-row_p['PTS'], 1))
    col3.metric("Stato", row_p['Stato'])
    
    linea = st.number_input("Quota offerta dal Bookmaker (es. 22.5):", step=0.5)
    if linea > 0:
        diff = row_p['PTS_L10'] - linea
        if diff > 1.5: st.success(f"✅ VALORE TROVATO: La media recente è superiore di {diff:.1f}. Consigliato OVER.")
        elif diff < -1.5: st.error(f"❌ SOTTO MEDIA: La media recente è inferiore di {abs(diff):.1f}. Consigliato UNDER.")
        else: st.warning("⚖️ LINEA EQUILIBRATA: Nessun vantaggio chiaro.")
