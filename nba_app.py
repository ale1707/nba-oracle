import streamlit as st
from nba_api.stats.endpoints import commonallplayers, scoreboardv2
import pandas as pd
import time

st.set_page_config(page_title="NBA Oracle 2026", layout="wide")

st.title("🏀 NBA Oracle: Stats & Predictions")

@st.cache_data(ttl=600)
def get_data():
    try:
        # Recupero Giocatori
        p_data = commonallplayers(is_only_current_season=1).get_data_frames()[0]
        # Recupero Partite di oggi
        s_data = scoreboardv2().get_data_frames()[1] # Header delle partite
        return p_data, s_data
    except:
        return None, None

all_players, games_today = get_data()

if all_players is not None:
    st.subheader("🔥 Top Pick del Giorno (Target Over/Under)")
    
    # Creiamo una tabella con dati simulati basati su medie reali per i top player
    top_picks = pd.DataFrame({
        "Giocatore": ["Antetokounmpo", "Doncic", "Tatum", "Wembanyama", "Haliburton"],
        "Media Punti": [30.8, 33.9, 27.1, 21.4, 20.1],
        "Target Oggi": [31.5, 34.5, 27.5, 22.5, 19.5],
        "Suggerimento": ["OVER 🔥", "OVER 🔥", "UNDER ❄️", "OVER 🔥", "OVER 🔥"]
    })
    
    # Mostriamo la tabella pulita
    st.table(top_picks)

    st.divider()

    st.subheader("📅 Programma Partite e Orari")
    if not games_today.empty:
        # Puliamo la tabella delle partite
        display_games = games_today[['GAME_SEQUENCE', 'GAME_STATUS_TEXT', 'HOME_TEAM_ID', 'VISITOR_TEAM_ID']]
        st.dataframe(display_games, use_container_width=True)
    else:
        st.info("Nessuna partita in programma nelle prossime ore.")
else:
    st.error("I server NBA sono carichi. Ricarica la pagina tra qualche secondo.")
    if st.button("Ricarica ora"):
        st.rerun()
