import streamlit as st
import pandas as pd

# 1. Configurazione Pagina
st.set_page_config(page_title="NBA Oracle Stats", layout="wide")

# 2. Titolo
st.title("🏀 NBA Oracle: Analisi Giocatori")

# 3. Creazione Dati (Tabella Giocatori)
# Questi sono i numeri che volevi per confrontare media e linea
giocatori_data = {
    "Giocatore": ["G. Antetokounmpo", "L. Doncic", "J. Tatum", "V. Wembanyama", "T. Haliburton"],
    "Media Punti": [30.8, 33.9, 27.1, 21.4, 20.1],
    "Linea Scommessa": [29.5, 34.5, 26.5, 22.5, 18.5],
    "Differenza": [1.3, -0.6, 0.6, -1.1, 1.6],
    "Suggerimento": ["OVER ✅", "UNDER ❌", "OVER ✅", "UNDER ❌", "OVER ✅"]
}

df_giocatori = pd.DataFrame(giocatori_data)

# 4. Visualizzazione Tabella
st.header("🔥 Player Props di Oggi")
st.table(df_giocatori)

st.divider()

# 5. Tabella Partite
st.header("📅 Match in Programma")
partite_data = {
    "Partita": ["Lakers @ Nuggets", "Celtics @ Knicks", "Warriors @ Suns", "Bucks @ Sixers"],
    "Orario ITA": ["02:00", "01:30", "04:00", "02:30"],
    "Totale (O/U)": ["228.5", "222.5", "234.0", "226.5"]
}
df_partite = pd.DataFrame(partite_data)
st.table(df_partite)

st.success("App caricata correttamente! Se vedi questa scritta, il sistema è stabile.")
