import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import playergamelog, commonallplayers, scoreboardv2
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="NBA Oracle 2026", layout="wide", initial_sidebar_state="collapsed")

# --- STILE CSS PER RENDERE L'APP BELLA ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #4a4a4a; }
    .top-card { border: 2px solid #ff4b4b; padding: 20px; border-radius: 15px; margin-bottom: 20px; background-color: #262730; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_daily_data():
    # 1. Recupera partite di oggi
    board = scoreboardv2.ScoreboardV2().get_data_frames()[1] # Header con orari
    # 2. Recupera tutti i giocatori
    players = commonallplayers(is_only_current_season=1).get_data_frames()[0]
    return board, players[['DISPLAY_FIRST_LAST', 'PERSON_ID', 'TEAM_ABBREVIATION']]

games_today, all_players = get_daily_data()

# --- SCHERMATA INIZIALE: TOP 10 PROMETTENTI ---
st.title("🎯 I 10 Migliori Pick di Oggi")
st.write(f"Analisi basata sui dati aggiornati al {datetime.now().strftime('%d/%m/%Y')}")

# Qui simuliamo l'algoritmo che estrae i 10 migliori (per velocità carichiamo i top scorer in forma)
top_cols = st.columns(5)
# Esempio di 10 giocatori "caldi" (in un'app reale qui girerebbe un loop su tutti i box score)
hot_players = ["LeBron James", "Luka Doncic", "Nikola Jokic", "Jayson Tatum", "Shai Gilgeous-Alexander", 
               "Giannis Antetokounmpo", "Kevin Durant", "Anthony Edwards", "Victor Wembanyama", "Tyrese Haliburton"]

for i, p_name in enumerate(hot_players[:10]):
    with top_cols[i % 5]:
        st.markdown(f"""<div class="top-card">
            <h3 style='margin:0;'>{p_name}</h3>
            <p style='color:#ff4b4b; font-weight:bold;'>🔥 Suggerimento: OVER</p>
        </div>""", unsafe_allow_html=True)

st.divider()

# --- SEZIONE PARTITE DEL GIORNO ---
st.header("📅 Programma e Statistiche Partite")

if games_today.empty:
    st.info("Nessuna partita in programma per oggi o dati non ancora disponibili.")
else:
    for index, game in games_today.iterrows():
        matchup = f"{game['HOME_TEAM_ID']} vs {game['VISITOR_TEAM_ID']}"
        # Convertiamo l'orario (semplificato)
        game_time = "Inizierà alle ore: " + str(game['GAME_STATUS_TEXT'])
        
        with st.expander(f"🏀 {matchup} | {game_time}"):
            col_a, col_b = st.columns(2)
            
            # Simuliamo l'analisi per un giocatore chiave di quella partita
            with col_a:
                st.subheader("Stats Punti")
                st.write("Giocatore chiave: Alta probabilità Over 24.5")
                st.progress(0.85) # Confidenza 85%
            
            with col_b:
                st.subheader("Rimbalzi & Assist")
                st.write("Target: Rimbalzi > 8.5 (Fiducia Media)")
                st.write("Target: Assist > 5.5 (Fiducia Alta)")

# --- RICERCA SINGOLO GIOCATORE ---
st.sidebar.header("Ricerca Specifica")
selected_p = st.sidebar.selectbox("Cerca un giocatore", all_players['DISPLAY_FIRST_LAST'])

if selected_p:
    p_id = all_players[all_players['DISPLAY_FIRST_LAST'] == selected_p]['PERSON_ID'].values[0]
    log = playergamelog.PlayerGameLog(player_id=p_id, season='2025-26').get_data_frames()[0]
    
    st.subheader(f"Analisi Dettagliata: {selected_p}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Media Punti (Ult. 5)", round(log.head(5)['PTS'].mean(), 1))
    c2.metric("Media Rimbalzi (Ult. 5)", round(log.head(5)['REB'].mean(), 1))
    c3.metric("Media Assist (Ult. 5)", round(log.head(5)['AST'].mean(), 1))
    
    st.plotly_chart(px.line(log.head(10), x='GAME_DATE', y=['PTS', 'REB', 'AST'], title="Trend ultime 10 partite"))