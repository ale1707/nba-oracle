import streamlit as st
import pandas as pd

st.set_page_config(page_title="NBA Oracle Gold", layout="wide")
st.title("🏀 NBA Oracle: Database Statistiche Complete")

# --- DATABASE ESTESO (Esempio con i principali per categoria) ---
# Nota: Puoi espandere ogni lista aggiungendo nomi e numeri tra le parentesi [ ]
nba_data = {
    "Giocatore": [
        "Luka Doncic", "Kyrie Irving", "Nikola Jokic", "Jamal Murray", 
        "Jayson Tatum", "Jaylen Brown", "D. Mitchell", "D. Garland",
        "S. Gilgeous-Alexander", "Chet Holmgren", "Anthony Edwards", "Rudy Gobert",
        "Jalen Brunson", "OG Anunoby", "Giannis Antetokounmpo", "Damian Lillard",
        "LeBron James", "Anthony Davis", "Stephen Curry", "Klay Thompson",
        "Kevin Durant", "Devin Booker", "Victor Wembanyama", "Tyrese Maxey"
    ],
    "Squadra": [
        "DAL", "DAL", "DEN", "DEN", 
        "BOS", "BOS", "CLE", "CLE", 
        "OKC", "OKC", "MIN", "MIN",
        "NYK", "NYK", "MIL", "MIL",
        "LAL", "LAL", "GSW", "GSW",
        "PHX", "PHX", "SAS", "PHI"
    ],
    "Media Punti": [33.9, 25.6, 26.1, 21.2, 27.1, 23.0, 26.6, 18.0, 31.1, 16.5, 25.9, 13.7, 27.2, 15.0, 30.4, 24.3, 24.8, 24.9, 26.4, 17.0, 27.2, 27.1, 21.4, 25.9],
    "Media Assist": [9.8, 5.2, 9.0, 6.5, 4.9, 3.6, 6.1, 6.5, 6.4, 2.4, 5.1, 1.3, 6.7, 2.2, 6.5, 7.0, 7.8, 3.5, 5.1, 2.3, 5.0, 6.9, 3.8, 6.2],
    "Media Rimbalzi": [9.2, 5.0, 12.3, 4.1, 8.1, 5.5, 5.1, 2.7, 5.5, 7.9, 5.4, 12.9, 3.6, 5.0, 11.5, 4.4, 7.2, 12.2, 4.5, 3.3, 6.6, 4.5, 10.6, 3.7],
    "Media 3pt Segnati": [4.1, 3.0, 1.1, 2.4, 3.1, 2.1, 3.3, 2.3, 1.3, 1.6, 2.4, 0.0, 2.8, 2.2, 0.5, 3.0, 2.1, 0.5, 4.8, 3.5, 2.2, 2.2, 1.8, 3.0],
}

df = pd.DataFrame(nba_data)

# --- CALCOLO COMBO ---
df['P+A+R'] = df['Media Punti'] + df['Media Assist'] + df['Media Rimbalzi']
df['P+A'] = df['Media Punti'] + df['Media Assist']
df['P+R'] = df['Media Punti'] + df['Media Rimbalzi']

# --- SIDEBAR FILTRI ---
st.sidebar.header("Strumenti di Ricerca")
search = st.sidebar.text_input("Cerca Giocatore (es. Curry):")
squadra_filter = st.sidebar.multiselect("Seleziona Squadre:", options=sorted(df['Squadra'].unique()), default=sorted(df['Squadra'].unique()))

# Applicazione Filtri
filtered_df = df[df['Squadra'].isin(squadra_filter)]
if search:
    filtered_df = filtered_df[filtered_df['Giocatore'].str.contains(search, case=False)]

# --- VISUALIZZAZIONE ---
st.subheader("📈 Tabella Analisi Giocatori")
st.write("Dati medi pronti per il confronto con le linee dei bookmakers.")
st.dataframe(filtered_df.style.format(precision=1), use_container_width=True)

st.divider()

# --- ANALISI SPECIFICA CATEGORIE ---
st.subheader("🎯 Top della Notte per Categoria")
c1, c2, c3, c4 = st.columns(4)

with c1:
    top_p = df.nlargest(1, 'Media Punti')
    st.metric("Punti (AVG)", f"{top_p['Giocatore'].values[0]}", f"{top_p['Media Punti'].values[0]}")
with c2:
    top_a = df.nlargest(1, 'Media Assist')
    st.metric("Assist (AVG)", f"{top_a['Giocatore'].values[0]}", f"{top_a['Media Assist'].values[0]}")
with c3:
    top_r = df.nlargest(1, 'Media Rimbalzi')
    st.metric("Rimbalzi (AVG)", f"{top_r['Giocatore'].values[0]}", f"{top_r['Media Rimbalzi'].values[0]}")
with c4:
    top_3 = df.nlargest(1, 'Media 3pt Segnati')
    st.metric("Triple (AVG)", f"{top_3['Giocatore'].values[0]}", f"{top_3['Media 3pt Segnati'].values[0]}")
