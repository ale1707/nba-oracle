import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, scoreboardv2
import time

# --- 1. CONFIGURAZIONE APP ---
st.set_page_config(page_title="NBA Oracle Ultimate", layout="wide", initial_sidebar_state="expanded")

# --- 2. MOTORE DI RICERCA DATI (Aggiornamento automatico ogni ora) ---
# Il parametro ttl=3600 fa aggiornare l'app da sola ogni 60 minuti
@st.cache_data(ttl=3600, show_spinner=False)
def get_nba_data():
    try:
        # A. Scarica TUTTI i giocatori della stagione (Medie a partita)
        player_stats = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame').get_data_frames()[0]
        
        # Pulizia e traduzione colonne
        df_players = player_stats[['PLAYER_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION', 'MIN', 'PTS', 'AST', 'REB', 'FG3M']]
        df_players = df_players.rename(columns={
            'PLAYER_NAME': 'Giocatore', 'TEAM_ABBREVIATION': 'Squadra', 
            'MIN': 'Minuti', 'PTS': 'Punti', 'AST': 'Assist', 'REB': 'Rimbalzi', 'FG3M': 'Triple'
        })
        # Teniamo solo chi gioca in media più di 10 minuti (via le riserve inutili)
        df_players = df_players[df_players['Minuti'] > 10.0].sort_values(by='Punti', ascending=False)
        
        # Algoritmo Base per i Pronostici Automatici
        def genera_pronostico(row):
            if row['Punti'] > 25: return "🔥 OVER Punti"
            elif row['Assist'] > 8: return "🎯 OVER Assist"
            elif row['Rimbalzi'] > 10: return "🧱 OVER Rimbalzi"
            elif row['Triple'] >= 3: return "💦 OVER Triple"
            else: return "⚖️ Linea Neutra"
            
        df_players['Pronostico'] = df_players.apply(genera_pronostico, axis=1)

        # B. Scarica le partite di OGGI
        games = scoreboardv2.ScoreboardV2().get_data_frames()[0]
        
        # Estrae l'abbreviazione della squadra dal GAMECODE (es. 20260227/LALDEN -> LAL e DEN)
        def get_teams(gamecode):
            teams_part = gamecode.split('/')[1]
            return teams_part[:3], teams_part[3:]

        partite_oggi = []
        for index, row in games.iterrows():
            away, home = get_teams(row['GAMECODE'])
            orario_usa = row['GAME_STATUS_TEXT'] # La NBA fornisce l'orario USA qui
            partite_oggi.append({'Casa': home, 'Trasferta': away, 'Orario_USA': orario_usa})
            
        return df_players, partite_oggi
    except Exception as e:
        return None, None

# --- CARICAMENTO DATI ---
with st.spinner("Connessione ai server NBA in corso... (potrebbe richiedere 1 minuto al primo avvio)"):
    df_totale, partite = get_nba_data()

# --- 3. NAVIGAZIONE LATERALE ---
st.sidebar.image("https://cdn.nba.com/logos/leagues/logo-nba.svg", width=150)
st.sidebar.title("Navigazione")
sezione = st.sidebar.radio("Scegli la pagina:", ["🔥 Partite di Oggi", "📊 Database Completo Stagione"])

st.sidebar.divider()
st.sidebar.info("🔄 Dati live ufficiali NBA. Si aggiornano automaticamente ogni 60 minuti.")
if st.sidebar.button("Forza Aggiornamento Ora"):
    get_nba_data.clear()
    st.rerun()

# =====================================================================
# PAGINA 1: PARTITE DI OGGI E SQUADRE
# =====================================================================
if sezione == "🔥 Partite di Oggi":
    st.title("🏀 Programma e Matchup di Stanotte")
    
    if df_totale is None or partite is None:
        st.error("I server NBA sono temporaneamente irraggiungibili o l'API è in blocco protettivo. Clicca 'Forza Aggiornamento Ora' nella barra laterale tra un paio di minuti.")
    elif len(partite) == 0:
        st.warning("Nessuna partita in programma per oggi secondo i server NBA.")
    else:
        st.write("Le tabelle mostrano i migliori 6 giocatori per squadra in base ai punti medi.")
        
        for p in partite:
            st.divider()
            st.header(f"🏟️ {p['Trasferta']} @ {p['Casa']}")
            st.subheader(f"Status/Orario USA: {p['Orario_USA']}")
            
            c1, c2 = st.columns(2)
            
            # Tabella Squadra in Trasferta
            with c1:
                st.markdown(f"### ✈️ {p['Trasferta']}")
                df_trasf = df_totale[df_totale['Squadra'] == p['Trasferta']].head(6) # Prende i top 6
                # Mostriamo una versione pulita della tabella
                st.dataframe(df_trasf[['Giocatore', 'Punti', 'Assist', 'Rimbalzi', 'Triple', 'Pronostico']], hide_index=True)
                
            # Tabella Squadra in Casa
            with c2:
                st.markdown(f"### 🏠 {p['Casa']}")
                df_casa = df_totale[df_totale['Squadra'] == p['Casa']].head(6)
                st.dataframe(df_casa[['Giocatore', 'Punti', 'Assist', 'Rimbalzi', 'Triple', 'Pronostico']], hide_index=True)

# =====================================================================
# PAGINA 2: DATABASE COMPLETO
# =====================================================================
elif sezione == "📊 Database Completo Stagione":
    st.title("🗄️ Database Analitico Stagionale")
    st.write("Esplora e filtra TUTTI i giocatori della NBA della stagione in corso.")
    
    if df_totale is not None:
        # Filtri dinamici
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            squadra_cercata = st.selectbox("Filtra per Squadra:", ["Tutte"] + sorted(df_totale['Squadra'].unique().tolist()))
        with col_f2:
            min_punti = st.slider("Punti minimi a partita:", 0.0, 35.0, 0.0, 0.5)
        with col_f3:
            cerca_nome = st.text_input("Cerca Giocatore (es. Curry):")
            
        # Applicazione Filtri
        df_filtrato = df_totale.copy()
        if squadra_cercata != "Tutte":
            df_filtrato = df_filtrato[df_filtrato['Squadra'] == squadra_cercata]
        if min_punti > 0:
            df_filtrato = df_filtrato[df_filtrato['Punti'] >= min_punti]
        if cerca_nome:
            df_filtrato = df_filtrato[df_filtrato['Giocatore'].str.contains(cerca_nome, case=False)]
            
        # Mostra tabella gigante
        st.dataframe(df_filtrato, use_container_width=True, height=600)
    else:
        st.error("Dati non disponibili. I server NBA non rispondono.")
