import streamlit as st
import pandas as pd

# 1. IMPOSTAZIONI PAGINA
st.set_page_config(page_title="NBA Oracle PRO", layout="wide")

st.title("🏀 NBA Oracle: Analisi Avanzata v4")

# --- SIDEBAR FILTRI ---
st.sidebar.header("Filtri Ricerca")
squadra_scelta = st.sidebar.multiselect(
    "Seleziona Squadre:",
    options=["Tutte", "DEN", "DAL", "OKC", "BOS", "MIN", "NYK"],
    default="Tutte"
)

# --- PASSO 1 POTENZIATO: DATABASE A 7+ COLONNE ---
# Qui abbiamo aggiunto: Squadra, Media Punti, Assist, Rimbalzi, Linea, Combo e Consiglio
nba_data = {
    "Giocatore": ["N. Jokic", "L. Doncic", "S. Gilgeous-Alexander", "J. Tatum", "A. Edwards", "J. Brunson"],
    "Squadra": ["DEN", "DAL", "OKC", "BOS", "MIN", "NYK"],
    "Media Punti": [26.1, 33.9, 31.1, 27.1, 26.3, 27.2],
    "Media Assist": [9.0, 9.8, 6.4, 4.9, 5.2, 6.5],
    "Media Rimbalzi": [12.3, 9.2, 5.5, 8.5, 5.4, 3.9],
    "Linea Bookmaker": [25.5, 34.5, 30.5, 27.5, 25.5, 26.5],
    "Consiglio": ["OVER ✅", "UNDER ❌", "OVER ✅", "OVER ✅", "OVER ✅", "⚖️ NEUTRO"]
}

df = pd.DataFrame(nba_data)

# CALCOLO COMBO (Punti + Assist + Rimbalzi) - Questa è la 7° colonna speciale
df['Combo (P+A+R)'] = df['Media Punti'] + df['Media Assist'] + df['Media Rimbalzi']

# Applichiamo il filtro squadra
if "Tutte" not in squadra_scelta:
    df = df[df['Squadra'].isin(squadra_scelta)]

# --- VISUALIZZAZIONE TABELLA ---
st.header("📊 Tabella Comparativa Completa")
# Usiamo dataframe per avere una tabella bella grande e scorrevole
st.dataframe(df, use_container_width=True)

st.divider()

# --- SEZIONE INFORTUNI ---
st.header("🚑 Situazione Infortuni")
col1, col2 = st.columns(2)
with col1:
    st.error("🔴 OUT")
    st.write("- **Joel Embiid**\n- **Kawhi Leonard**")
with col2:
    st.warning("🟡 IN DUBBIO")
    st.write("- **LeBron James**\n- **Kevin Durant**")
