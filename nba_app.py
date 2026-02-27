import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, scoreboardv2

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="NBA Oracle SAFETY", layout="wide", page_icon="🏀")

# CSS per alert infortuni
st.markdown("""
    <style>
    .stAlert { padding: 0.5rem; margin-bottom: 1rem; border-radius: 0.5rem; }
    .injury-banner { background-color: #ff4b4b; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

def get_logo(abbr):
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{abbr.lower()}.png"

@st.cache_data(ttl=1800) # Ridotto a 30 min per maggiore freschezza
def get_nba_data():
    try:
        # Dati Stagione e Last 10
        sea = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame').get_data_frames()[0]
        l10 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=10).get_data_frames()[0]
        
        df = pd.merge(sea[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'MIN', 'PTS', 'AST', 'REB', 'GP']], 
                      l10[['PLAYER_ID', 'MIN', 'PTS', 'AST', 'REB', 'GP']], 
                      on='PLAYER_ID', suffixes=('', '_L10')).fillna(0)
        
        df = df.rename(columns={'PLAYER_NAME': 'Giocatore', 'TEAM_ABBREVIATION': 'Squadra'})
        
        # LOGICA DI SICUREZZA INFORTUNI
        # Se un giocatore ha 0 minuti nelle ultime 10 o GP_L10 è troppo basso rispetto alla stagione
        df['Stato'] = df.apply(lambda r: "❌ OUT" if r['GP_L10'] == 0 else ("⚠️ DUBBIO" if r['GP_L10'] < 3 else "✅ OK"), axis=1)
        
        # Partite
        games = scoreboardv2.ScoreboardV2().get_data_frames()[0]
        partite_oggi = []
        for _, row in games.iterrows():
            gamecode = row['GAMECODE']
            away, home = gamecode.split('/')[1][:3], gamecode.split('/')[1][3:]
            partite_oggi.append({'Casa': home, 'Trasferta': away, 'Status': row['GAME_STATUS_TEXT']})
            
        return df, partite_oggi
    except:
        return None, None

df_totale, partite = get_nba_data()

st.title("🏀 NBA Oracle SAFETY")
st.warning("⚠️ ATTENZIONE: Donovan Mitchell e altri top player possono essere OUT. Controlla sempre lo 'Stato' prima di scommettere.")

# Visualizzazione Match con Alert Infortuni
if partite:
    for p in partite:
        h, a = p['Casa'], p['Trasferta']
        st.subheader(f"{h} vs {a} ({p['Status']})")
        
        # Alert se ci sono infortunati famosi nel team
        for team in [h, a]:
            outs = df_totale[(df_totale['Squadra'] == team) & (df_totale['Stato'] != "✅ OK")]['Giocatore'].tolist()
            if outs:
                st.write(f"🚑 **Assenze/Dubbi {team}:** {', '.join(outs[:5])}")

        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(df_totale[df_totale['Squadra'] == h][['Giocatore', 'Stato', 'PTS_L10', 'AST_L10']].head(8), hide_index=True)
        with c2:
            st.dataframe(df_totale[df_totale['Squadra'] == a][['Giocatore', 'Stato', 'PTS_L10', 'AST_L10']].head(8), hide_index=True)
        st.divider()

# Database a tendina (come chiesto)
st.header("🗄️ Database Squadre")
squadre = sorted(df_totale['Squadra'].unique())
for s in squadre:
    with st.expander(f"🏀 {s}"):
        st.dataframe(df_totale[df_totale['Squadra'] == s][['Giocatore', 'Stato', 'PTS', 'PTS_L10', 'AST', 'AST_L10']], hide_index=True)
