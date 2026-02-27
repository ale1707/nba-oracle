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
    .team-logo { width: 50px; vertical-align: middle; margin: 0 10px; }
    .team-logo-small { width: 35px; vertical-align: middle; margin-right: 12px; }
    .match-header { font-size: 26px; font-weight: 800; text-align: center; margin-bottom: 5px; }
    .time-text { font-size: 14px; color: #888; text-align: center; margin-bottom: 20px; }
    .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem; }
    .injury-alert { color: #ff4b4b; font-weight: bold; font-size: 15px; margin-bottom: 12px; border: 1px solid #ff4b4b; padding: 8px; border-radius: 5px;}
    </style>
""", unsafe_allow_html=True)

# Mappatura Squadre
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
        df['Squadra'] = df['Abbr'].map(TEAM_NAMES)
        df = df[df['MIN'] > 15.0]

        # Logica Infortuni
        df['Stato'] = df.apply(lambda r: "❌ OUT" if r['GP_L10'] == 0 else ("🚑 DUBBIO" if r['GP_L10'] < 4 else "✅ OK"), axis=1)

        # Logica Pronostico Trend
        def calcola_trend(r):
            if "OUT" in r['Stato'] or "DUBBIO" in r['Stato']: return "⛔ Evitare"
            diff = r['PTS_L10'] - r['PTS']
            if diff >= 4.0: return "🔥 OVER Punti"
            elif r['AST_L10'] >= 7.5: return "🎯 OVER Assist"
            elif r['REB_L10'] >= 9.5: return "🧱 OVER Rimbalzi"
            else: return "⚖️ Stabile"
        df['Trend'] = df.apply(calcola_trend, axis=1)

        # Logica Safe Pick
        def calcola_safe(r):
            if "OUT" in r['Stato'] or "DUBBIO" in r['Stato']: return "---"
            pts_ref = r['PTS_L10'] if r['PTS_L10'] > 0 else r['PTS']
            safe_p = int(pts_ref * 0.75)
            return f"🟢 OVER {safe_p}.5 P" if safe_p > 7 else "---"
        df['Safe Pick'] = df.apply(calcola_safe, axis=1)

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
    st.error("Connessione NBA fallita. Ricarica.")
    st.stop()

# --- 3. INTERFACCIA ---
tab_match, tab_db_sea, tab_db_l10, tab_calc = st.tabs(["🔥 Match & Safe", "🗄️ Database Stagione", "📈 Forma L10", "🧮 Calcolatore"])

with tab_match:
    if not partite:
        st.info("Nessuna partita oggi.")
    else:
        for p in partite:
            st.markdown(f'<div class="match-header"><img src="{get_logo(p["CasaAbbr"])}" class="team-logo">{p["Casa"]} vs {p["Trasferta"]}<img src="{get_logo(p["TrasfertaAbbr"])}" class="team-logo"></div>', unsafe_allow_html=True)
            st.markdown(f'<p style="text-align:center; color:gray;">Status: {p["Orario"]}</p>', unsafe_allow_html=True)
            
            # Radar Infortuni
            for team_name in [p['Casa'], p['Trasferta']]:
                inf = df_totale[(df_totale['Squadra'] == team_name) & (df_totale['Stato'] != "✅ OK")]['Giocatore'].tolist()
                if inf: st.markdown(f'<div class="injury-alert">🚑 {team_name} Assenze: {", ".join(inf[:4])}</div>', unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            # REB_L10 reinserito qui!
            cols_show = ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'Safe Pick']
            cfg = {"PTS_L10": "PTS", "AST_L10": "AST", "REB_L10": "REB", "Safe Pick": "Safe 🟢"}
            
            with c1:
                st.markdown(f"**🏠 {p['Casa']}**")
                st.dataframe(df_totale[df_totale['Squadra'] == p['Casa']][cols_show].sort_values('PTS_L10', ascending=False).head(7), hide_index=True, column_config=cfg)
            with c2:
                st.markdown(f"**✈️ {p['Trasferta']}**")
                st.dataframe(df_totale[df_totale['Squadra'] == p['Trasferta']][cols_show].sort_values('PTS_L10', ascending=False).head(7), hide_index=True, column_config=cfg)
            st.divider()

# Funzione Database con LOGHI e Nomi Lunghi
def render_full_db(df, columns, order_by, col_cfg):
    squadre = sorted(df['Squadra'].unique())
    for s in squadre:
        abbr = df[df['Squadra'] == s]['Abbr'].iloc[0]
        with st.expander(f"🏀 {s}"):
            st.markdown(f"<img src='{get_logo(abbr)}' class='team-logo-small'> **{s}**", unsafe_allow_html=True)
            st.dataframe(df[df['Squadra'] == s][columns].sort_values(order_by, ascending=False), hide_index=True, use_container_width=True, column_config=col_cfg)

with tab_db_sea:
    st.subheader("Database Medie Stagionali")
    render_full_db(df_totale, ['Giocatore', 'Stato', 'PTS', 'AST', 'REB', 'FG3M'], 'PTS', {})

with tab_db_l10:
    st.subheader("Database Forma Recente (Ultime 10)")
    render_full_db(df_totale, ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'FG3M_L10'], 'PTS_L10', {"PTS_L10": "PTS", "AST_L10": "AST", "REB_L10": "REB", "FG3M_L10": "3PM"})

with tab_calc:
    p_sel = st.selectbox("Seleziona Giocatore:", sorted(df_totale['Giocatore'].tolist()))
    val = df_totale[df_totale['Giocatore'] == p_sel]['PTS_L10'].values[0]
    st.metric(f"Media Punti Recente ({p_sel})", f"{val:.1f}")
    linea = st.number_input("Quota Bookmaker:", step=0.5)
    if linea > 0:
        if val > linea + 1.5: st.success("🔥 OVER")
        elif val < linea - 1.5: st.error("❄️ UNDER")
