import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, scoreboardv2

# --- 1. CONFIGURAZIONE E STILE ---
st.set_page_config(page_title="NBA Oracle ELITE", layout="wide", page_icon="🏀", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    div[data-testid="stStatusWidget"] {display:none;}
    .team-logo { width: 45px; vertical-align: middle; margin: 0 10px; }
    .match-header { font-size: 24px; font-weight: 800; text-align: center; margin-bottom: 5px; }
    .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem; }
    </style>
""", unsafe_allow_html=True)

def get_logo(abbr):
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{abbr.lower()}.png"

# --- 2. MOTORE DI RICERCA DATI ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_nba_data():
    try:
        # A. Database Stagione
        season = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame').get_data_frames()[0]
        df_sea = season[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']]
        
        # B. Database Ultime 10
        l10 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=10).get_data_frames()[0]
        df_l10 = l10[['PLAYER_ID', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']]
        
        # C. Unione
        df = pd.merge(df_sea, df_l10, on='PLAYER_ID', suffixes=('', '_L10'), how='left').fillna(0)
        df = df.rename(columns={'PLAYER_NAME': 'Giocatore', 'TEAM_ABBREVIATION': 'Squadra'})
        df = df[df['MIN'] > 15.0]

        # Infortuni
        df['Stato'] = df.apply(lambda r: "🚑 OUT/Risk" if (r['GP_L10'] < 3 and r['GP'] > 10) else "✅ OK", axis=1)

        # Safe Pick
        def giocata_sicura(r):
            if r['Stato'] == "🚑 OUT/Risk": return "---"
            pts_ref = r['PTS_L10'] if r['PTS_L10'] > 0 else r['PTS']
            safe_val = int(pts_ref * 0.7)
            return f"🟢 OVER {safe_val}.5 P" if safe_val > 8 else "🟢 OVER 5.5 P"
        df['Safe Pick'] = df.apply(giocata_sicura, axis=1)

        # Partite
        games = scoreboardv2.ScoreboardV2().get_data_frames()[0]
        partite_oggi = []
        for _, row in games.iterrows():
            gamecode = row['GAMECODE']
            away, home = gamecode.split('/')[1][:3], gamecode.split('/')[1][3:]
            partite_oggi.append({'Casa': home, 'Trasferta': away, 'Orario': row['GAME_STATUS_TEXT']})

        return df, partite_oggi
    except Exception as e:
        return None, None

with st.spinner("🔄 Caricamento dati NBA..."):
    df_totale, partite = get_nba_data()

if df_totale is None:
    st.error("Errore server. Ricarica.")
    st.stop()

# --- 3. INTERFACCIA ---
tab_match, tab_db_sea, tab_db_l10, tab_calc = st.tabs(["🔥 Match", "🗄️ Stagione per Squadra", "📈 Forma L10 per Squadra", "🧮 Calcolatore"])

with tab_match:
    if not partite:
        st.info("Nessuna partita oggi.")
    else:
        for p in partite:
            h, a = p['Casa'], p['Trasferta']
            st.markdown(f'<div class="match-header"><img src="{get_logo(h)}" class="team-logo">{h} vs {a}<img src="{get_logo(a)}" class="team-logo"></div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            col_match = ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'Safe Pick']
            with c1: st.dataframe(df_totale[df_totale['Squadra'] == h][col_match].head(6), hide_index=True)
            with c2: st.dataframe(df_totale[df_totale['Squadra'] == a][col_match].head(6), hide_index=True)
            st.divider()

# FUNZIONE PER RENDERE IL DB DIVISO PER SQUADRE
def render_grouped_db(df, cols, key_prefix):
    squadre = sorted(df['Squadra'].unique())
    for s in squadre:
        with st.expander(f"🏀 {s}"):
            df_s = df[df['Squadra'] == s][cols].sort_values(by=cols[2], ascending=False)
            st.dataframe(df_s, hide_index=True, use_container_width=True)

with tab_db_sea:
    st.subheader("Database Stagione (Diviso per Squadra)")
    render_grouped_db(df_totale, ['Giocatore', 'Stato', 'PTS', 'AST', 'REB', 'FG3M'], "sea")

with tab_db_l10:
    st.subheader("Database Forma L10 (Diviso per Squadra)")
    render_grouped_db(df_totale, ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'FG3M_L10'], "l10")

with tab_calc:
    st.subheader("Calcolatore")
    p_sel = st.selectbox("Giocatore:", sorted(df_totale['Giocatore'].tolist()))
    val_form = df_totale[df_totale['Giocatore'] == p_sel]['PTS_L10'].values[0]
    st.metric("Media Punti Recente", f"{val_form:.1f}")
    linea = st.number_input("Linea:", step=0.5)
    if linea > 0:
        if val_form > linea + 1: st.success("🔥 OVER")
        elif val_form < linea - 1: st.error("❄️ UNDER")
