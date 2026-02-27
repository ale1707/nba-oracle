import streamlit as st
import pandas as pd

st.set_page_config(page_title="NBA Match-Day Oracle", layout="wide")

st.title("🏀 NBA Match-Day: Analisi e Pronostici")
st.write("Analisi dettagliata per ogni scontro di stanotte (Orari Italiani)")

# --- FUNZIONE PER CREARE LE TABELLE SQUADRA ---
def crea_tabella_squadra(data):
    df = pd.DataFrame(data)
    # Calcolo Combo
    df['P+A+R'] = df['Punti'] + df['Assist'] + df['Rimbalzi']
    return df

# =========================================================
# PARTITA 1: LAKERS vs NUGGETS (Ore 02:00)
# =========================================================
st.divider()
st.header("🏟️ L.A. Lakers @ Denver Nuggets")
st.subheader("⏰ Ore: 02:00 (ITA)")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🟡 L.A. Lakers")
    lakers_data = {
        "Giocatore": ["LeBron James", "Anthony Davis", "Austin Reaves"],
        "Punti": [24.8, 25.1, 15.9],
        "Assist": [7.8, 3.5, 5.5],
        "Rimbalzi": [7.2, 12.2, 4.3],
        "Triple": [2.1, 0.5, 1.9],
        "Pronostico": ["OVER P+A", "OVER Rimbalzi", "UNDER Punti"]
    }
    st.table(crea_tabella_squadra(lakers_data))

with col2:
    st.markdown("### 🔵 Denver Nuggets")
    nuggets_data = {
        "Giocatore": ["Nikola Jokic", "Jamal Murray", "Michael Porter Jr"],
        "Punti": [26.1, 21.2, 16.7],
        "Assist": [9.0, 6.5, 1.5],
        "Rimbalzi": [12.3, 4.1, 7.0],
        "Triple": [1.1, 2.4, 2.8],
        "Pronostico": ["OVER Assist", "OVER Punti", "OVER Triple"]
    }
    st.table(crea_tabella_squadra(nuggets_data))

# =========================================================
# PARTITA 2: CELTICS vs KNICKS (Ore 01:30)
# =========================================================
st.divider()
st.header("🏟️ Boston Celtics @ New York Knicks")
st.subheader("⏰ Ore: 01:30 (ITA)")

col3, col4 = st.columns(2)

with col3:
    st.markdown("### 🟢 Boston Celtics")
    celtics_data = {
        "Giocatore": ["Jayson Tatum", "Jaylen Brown", "D. White"],
        "Punti": [27.1, 23.0, 15.2],
        "Assist": [4.9, 3.6, 5.2],
        "Rimbalzi": [8.1, 5.5, 4.2],
        "Triple": [3.1, 2.1, 2.7],
        "Pronostico": ["OVER P+R", "OVER Punti", "OVER Triple"]
    }
    st.table(crea_tabella_squadra(celtics_data))

with col4:
    st.markdown("### 🟠 New York Knicks")
    knicks_data = {
        "Giocatore": ["Jalen Brunson", "Julius Randle", "OG Anunoby"],
        "Punti": [27.2, 24.0, 15.1],
        "Assist": [6.7, 4.8, 2.2],
        "Rimbalzi": [3.6, 9.2, 5.0],
        "Triple": [2.8, 1.7, 2.3],
        "Pronostico": ["OVER Punti", "OVER Rimbalzi", "UNDER Punti"]
    }
    st.table(crea_tabella_squadra(knicks_data))

st.sidebar.info("Aggiorna i dati ogni pomeriggio guardando Sofascore per avere la precisione massima.")
