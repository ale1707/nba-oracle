import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, scoreboardv2

# --- 1. CONFIGURAZIONE E STILE ---
st.set_page_config(page_title="NBA Oracle ULTIMATE", layout="wide", page_icon="🏀", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    div[data-testid="stStatusWidget"] {display:none;}
    .team-logo { width: 45px; vertical-align: middle; margin: 0 10px; }
    .team-logo-small { width: 30px; vertical-align: middle; margin-right: 10px; }
    .match-header { font-size: 24px; font-weight: 800; text-align: center; margin-bottom: 5px; }
    .time-text { font-size: 14px; color: #888; text-align: center; margin-bottom: 20px; }
    .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem; }
    .injury-alert { color: #ff4b4b; font-weight: bold; font-size: 14px; margin-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

# Mappatura Abbreviazioni -> Nomi Completi
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

# --- 2. MOTORE DI RICERCA DATI ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_nba_data():
    try:
        # A. Database Stagione
        season = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame').get_data_frames()[0]
        df_sea = season[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']]
        
        # B. Database Ultime 10 Partite
        l10 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=10).get_data_frames()[0]
        df_l10 = l10[['PLAYER_ID', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']]
        
        # C. Unione Database
        df = pd.merge(df_sea, df_l10, on='PLAYER_ID', suffixes=('', '_L10'), how='left').fillna(0)
        df = df.rename(columns={'PLAYER_NAME': 'Giocatore', 'TEAM_ABBREVIATION': 'Abbr'})
        
        # Aggiunta Nome Completo
        df['Squadra'] = df['Abbr'].map(TEAM_NAMES)
        
        df = df[df['MIN'] > 15.0]

        # Logica Infortuni
        def calcola_stato(r):
            if r['GP_L10'] == 0 and r['GP'] > 5: return "❌ OUT"
            elif r['GP_L10'] < 4 and r['GP'] > 15: return "🚑 DUBBIO"
            else: return "✅ OK"
        df['Stato'] = df.apply(calcola_stato, axis=1)

        # Logica Pronostico Trend
        def calcola_pronostico(r):
            if "OUT" in r['Stato'] or "DUBBIO" in r['Stato']: return "⛔ Evitare"
            diff = r['PTS_L10'] - r['PTS']
            if diff >= 4.0: return "🔥 OVER Punti"
            elif diff <= -4.0: return "❄️ UNDER Punti"
            elif r['AST_L10'] >= 7.5: return "🎯 OVER Assist"
            else: return "⚖️ Stabile"
        df['Trend'] = df.apply(calcola_pronostico, axis=1)

        # Logica Safe Pick
        def giocata_sicura(r):
            if "OUT" in r['Stato'] or "DUBBIO" in r['Stato']: return "---"
            safe_val = int(r['PTS_L10'] * 0.7) if r['PTS_L10'] > 0 else int(r['PTS'] * 0.7)
            return f"🟢 OVER {safe_val}.5 P" if safe_val > 8 else "---"
        df['Safe Pick'] = df.apply(giocata_sicura, axis=1)

        # Partite
        games = scoreboardv2.ScoreboardV2().get_data_frames()[0]
        partite_oggi = []
        for _, row in games.iterrows():
            gamecode = row['GAMECODE']
            away_abbr, home_abbr = gamecode.split('/')[1][:3], gamecode.split('/')[1][3:]
            partite_oggi.append({
                'Casa': TEAM_NAMES.get(home_abbr, home_abbr), 'CasaAbbr': home_abbr,
                'Trasferta': TEAM_NAMES.get(away_abbr, away_abbr), 'TrasfertaAbbr': away_abbr,
                'Orario': row['GAME_STATUS_TEXT']
            })

        return df, partite_oggi
    except:
        return None, None

df_totale, partite = get_nba_data()

if df_totale is None:
    st.error("Errore connessione NBA. Ricarica.")
    st.stop()

# --- 3. INTERFACCIA ---
tab_match, tab_db_sea, tab_db_l10, tab_calc = st.tabs(["🔥 Match", "🗄️ Stagione", "📈 Forma L10", "🧮 Calcolatore"])

with tab_match:
    if not partite:
        st.info("Nessun match oggi.")
    else:
        for p in partite:
            st.markdown(f"""
            <div class="match-header">
                <img src="{get_logo(p['CasaAbbr'])}" class="team-logo">{p['Casa']} vs {p['Trasferta']}<img src="{get_logo(p['TrasfertaAbbr'])}" class="team-logo">
            </div>
            <p style="text-align:center; color:gray;">{p['Orario']}</p>
            """, unsafe_allow_html=True)
            
            # Radar Infortuni
            for side in [p['Casa'], p['Trasferta']]:
                inf = df_totale[(df_totale['Squadra'] == side) & (df_totale['Stato'] != "✅ OK")]['Giocatore'].tolist()
                if inf: st.markdown(f"<div class='injury-alert'>🚑 {side} Assenze: {', '.join(inf[:3])}</div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            cols = ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'Safe Pick']
            with c1: st.dataframe(df_totale[df_totale['Squadra'] == p['Casa']][cols].head(6), hide_index=True)
            with c2: st.dataframe(df_totale[df_totale['Squadra'] == p['Trasferta']][cols].head(6), hide_index=True)
            st.divider()

# Funzione Database con Loghi e Nomi Lunghi
def render_full_db(df, columns, order_by):
    squadre_ordinate = sorted(df['Squadra'].unique())
    for s in squadre_ordinate:
        abbr = df[df['Squadra'] == s]['Abbr'].iloc[0]
        with st.expander(f"🏀 {s}"):
            st.markdown(f"<img src='{get_logo(abbr)}' class='team-logo-small'> **{s}**", unsafe_allow_html=True)
            st.dataframe(df[df['Squadra'] == s][columns].sort_values(order_by, ascending=False), hide_index=True, use_container_width=True)

with tab_db_sea:
    render_full_db(df_totale, ['Giocatore', 'Stato', 'PTS', 'AST', 'REB', 'FG3M'], 'PTS')

with tab_db_l10:
    render_full_db(df_totale, ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'FG3M_L10'], 'PTS_L10')

with tab_calc:
    p_sel = st.selectbox("Giocatore:", sorted(df_totale['Giocatore'].tolist()))
    stat_val = df_totale[df_totale['Giocatore'] == p_sel]['PTS_L10'].values[0]
    st.metric(f"Media Punti Recente {p_sel}", f"{stat_val:.1f}")
    linea = st.number_input("Linea Bookmaker:", step=0.5)
    if linea > 0:
        if stat_val > linea + 1.5: st.success("🔥 VALORE OVER")
        elif stat_val < linea - 1.5: st.error("❄️ VALORE UNDER")
