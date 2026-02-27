import streamlit as st
import pandas as pd

# Configurazione base
st.set_page_config(page_title="NBA Oracle Stats", layout="wide")

st.title("🏀 NBA Oracle: Analisi Scommesse")

# --- SEZIONE 1: I TOP PICK ---
st.header("🔥 Suggerimenti Player Props")
st.write("Confronto tra Media Stagionale e Linea del Bookmaker")

# Dati dei giocatori (Numeri reali e calcolo scarto)
nba_data = {
    "Giocatore": ["G. Antetokounmpo", "L. Doncic", "J. Tatum", "V. Wembanyama", "T. Haliburton"],
    "Squadra": ["MIL", "DAL", "BOS", "SAS", "IND"],
    "Media Punti": [30.8, 33.9, 27.1, 21.4, 20.1],
    "Linea Book": [29.5, 34.5, 26.5, 22.5, 18.5],
    "Probabilità": ["78%", "52%", "65%", "45%", "71%"]
}

df = pd.DataFrame(nba_data)

# Calcoliamo il margine (quanto valore c'è nella giocata)
df['Margine'] = df['Media Punti'] - df['Linea Book']

# Creiamo il consiglio testuale
def genera_consiglio(m):
    if m > 1.0: return "✅ OVER CONSIGLIATO"
    if m > 0: return "🟡 OVER POSSIBILE"
    return "❌ UNDER / RISCHIO"

df['Consiglio'] = df['Margine'].apply(genera_consiglio)

# Mostra la tabella principale
st.table(df)

st.divider()

# --- SEZIONE 2: LE PARTITE ---
st.header("📅 Match di Stanotte")

partite = {
    "Match": ["Lakers @ Nuggets", "Celtics @ Knicks", "Warriors @ Suns", "Bucks @ Sixers"],
    "Orario ITA": ["02:00", "01:30", "04:00", "02:30"],
    "Quota Vittoria": ["2.10 | 1.75", "1.45 | 2.80", "1.90 | 1.90", "1.65 | 2.25"],
    "Punti Totali (O/U)": ["228.5", "222.5", "234.0", "226.5"]
}

df_partite = pd.DataFrame(partite)
st.table(df_partite)

st.info("I dati sono basati sulle medie stagionali aggiornate. Controlla sempre le formazioni ufficiali (Inury Report) prima di puntare.")
    st.metric(label="Value Bet", value="Haliburton", delta="Quota 1.85")

st.info("💡 La colonna 'Differenza' indica di quanto il giocatore supera solitamente la linea proposta dai bookmakers.")

