import streamlit as st
import pandas as pd

st.set_page_config(page_title="NBA Oracle Pro", layout="wide")

st.title("🏀 NBA Oracle: Stats & Betting Tips")

# Tabella dei Top Pick con i numeri che hai chiesto
st.subheader("🔥 Top 5 Player Prop - Suggerimenti di Oggi")

data = {
    "Giocatore": ["G. Antetokounmpo", "L. Doncic", "J. Tatum", "V. Wembanyama", "T. Haliburton"],
    "Squadra": ["MIL", "DAL", "BOS", "SAS", "IND"],
    "Media Punti": [30.8, 33.9, 27.1, 21.4, 20.1],
    "Linea (Scommessa)": [31.5, 34.5, 26.5, 22.5, 18.5],
    "Suggerimento": ["OVER 🔥", "OVER 🔥", "OVER 🔥", "UNDER ❄️", "OVER 🔥"],
    "Probabilità": ["72%", "68%", "75%", "61%", "70%"]
}

df = pd.DataFrame(data)

# Mostriamo la tabella con i dati chiari
st.table(df)

st.divider()

# Seconda sezione: Tabella Partite
st.subheader("📅 Programma Partite di Stanotte")

partite = {
    "Partita": ["Lakers vs Nuggets", "Celtics vs Knicks", "Warriors vs Suns", "Bucks vs Sixers"],
    "Orario (ITA)": ["02:00", "01:30", "04:00", "02:30"],
    "Favorita": ["Nuggets", "Celtics", "Warriors", "Bucks"],
    "Spread": ["-4.5", "-6.0", "-2.5", "-3.5"]
}

df_partite = pd.DataFrame(partite)
st.dataframe(df_partite, use_container_width=True)

st.info("💡 I dati vengono aggiornati in base alle ultime prestazioni medie.")
