import streamlit as st
import pandas as pd

st.set_page_config(page_title="NBA Oracle PRO", layout="wide")

# CSS per rendere l'app più scura e professionale
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stDataFrame { border: 1px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏀 NBA Oracle v2.0 - Betting Intelligence")

# Dati potenziati
data = {
    "Giocatore": ["G. Antetokounmpo", "L. Doncic", "J. Tatum", "V. Wembanyama", "T. Haliburton"],
    "Media Punti": [30.8, 33.9, 27.1, 21.4, 20.1],
    "Linea Scommessa": [29.5, 34.5, 26.5, 23.5, 18.5],
    "Probabilità (%)": [78, 52, 65, 45, 71]
}

df = pd.DataFrame(data)

# CALCOLO DEL MARGINE: Differenza tra media e linea
df['Differenza'] = df['Media Punti'] - df['Linea Scommessa']

# LOGICA DI CONSIGLIO
def segnale(row):
    if row['Differenza'] > 1 and row['Probabilità (%)'] > 70:
        return "🔥 OVER FORTE"
    elif row['Differenza'] > 0:
        return "✅ OVER"
    else:
        return "⚠️ UNDER/RISCHIO"

df['Consiglio'] = df.apply(segnale, axis=1)

# Visualizzazione Tabella Principale
st.subheader("📊 Analisi Performance e Target")
st.dataframe(df.style.background_gradient(subset=['Probabilità (%)'], cmap='RdYlGn'), use_container_width=True)

st.divider()

# NUOVA SEZIONE: I 3 "BOOM" DELLA NOTTE
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Miglior Over", value="Antetokounmpo", delta="+1.3 punti vs linea")
with col2:
    st.metric(label="Rischio Alto", value="Wembanyama", delta="-2.1 punti", delta_color="inverse")
with col3:
    st.metric(label="Value Bet", value="Haliburton", delta="Quota 1.85")

st.info("💡 La colonna 'Differenza' indica di quanto il giocatore supera solitamente la linea proposta dai bookmakers.")
