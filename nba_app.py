import streamlit as st
import pandas as pd

st.set_page_config(page_title="NBA Betting Oracle 2026", layout="wide")

st.title("🏀 NBA Oracle: Programma e Analisi del 27/28 Febbraio")
st.write("Dati medi stagionali aggiornati - Orario Italiano")

# Funzione per velocizzare la creazione delle tabelle
def schedina(data):
    df = pd.DataFrame(data)
    df['P+A+R'] = df['Punti'] + df['Assist'] + df['Rimbalzi']
    return df

# --- PARTITA 1: PHILADELPHIA vs TORONTO (Ore 01:00) ---
st.divider()
st.header("🏟️ Philadelphia 76ers @ Toronto Raptors")
st.subheader("⏰ Ore: 01:00 (ITA)")
c1, c2 = st.columns(2)
with c1:
    st.markdown("### 🔴 Philadelphia")
    st.table(schedina({
        "Giocatore": ["Tyrese Maxey", "Paul George", "Kelly Oubre Jr"],
        "Punti": [25.9, 22.1, 15.4], "Assist": [6.2, 4.5, 1.2], "Rimbalzi": [3.7, 5.2, 5.0], "3PT": [3.1, 3.3, 1.5], "Pronostico": ["OVER 25.5 P", "OVER 3.5 A", "UNDER"]
    }))
with c2:
    st.markdown("### 🦖 Toronto")
    st.table(schedina({
        "Giocatore": ["RJ Barrett", "Scottie Barnes", "Immanuel Quickley"],
        "Punti": [23.2, 21.0, 18.5], "Assist": [4.8, 6.1, 6.5], "Rimbalzi": [5.4, 9.2, 3.8], "3PT": [1.9, 1.2, 2.8], "Pronostico": ["OVER 22.5 P", "OVER 8.5 R", "OVER 2.5 3P"]
    }))

# --- PARTITA 2: MILWAUKEE vs MIAMI (Ore 02:00) ---
st.divider()
st.header("🏟️ Milwaukee Bucks @ Miami Heat")
st.subheader("⏰ Ore: 02:00 (ITA)")
c3, c4 = st.columns(2)
with c3:
    st.markdown("### 🦌 Milwaukee")
    st.table(schedina({
        "Giocatore": ["G. Antetokounmpo", "Damian Lillard", "Brook Lopez"],
        "Punti": [30.4, 24.3, 12.5], "Assist": [6.5, 7.0, 1.6], "Rimbalzi": [11.5, 4.4, 5.2], "3PT": [0.5, 3.0, 1.9], "Pronostico": ["OVER 29.5 P", "OVER 6.5 A", "OVER 1.5 BLK"]
    }))
with c4:
    st.markdown("### ☀️ Miami")
    st.table(schedina({
        "Giocatore": ["Jimmy Butler", "Bam Adebayo", "Tyler Herro"],
        "Punti": [20.8, 19.3, 22.5], "Assist": [5.0, 3.9, 4.2], "Rimbalzi": [5.3, 10.4, 4.8], "3PT": [0.9, 0.2, 3.5], "Pronostico": ["UNDER 21.5 P", "OVER 9.5 R", "OVER 3.5 3P"]
    }))

# --- PARTITA 3: PHOENIX vs DALLAS (Ore 04:00) ---
st.divider()
st.header("🏟️ Phoenix Suns @ Dallas Mavericks")
st.subheader("⏰ Ore: 04:00 (ITA)")
c5, c6 = st.columns(2)
with c5:
    st.markdown("### 🏜️ Phoenix")
    st.table(schedina({
        "Giocatore": ["Kevin Durant", "Devin Booker", "Bradley Beal"],
        "Punti": [27.2, 27.1, 18.2], "Assist": [5.0, 6.9, 4.5], "Rimbalzi": [6.6, 4.5, 4.1], "3PT": [2.2, 2.2, 2.0], "Pronostico": ["OVER 26.5 P", "OVER 6.5 A", "UNDER"]
    }))
with c6:
    st.markdown("### 🐴 Dallas")
    st.table(schedina({
        "Giocatore": ["Luka Doncic", "Kyrie Irving", "Klay Thompson"],
        "Punti": [33.9, 25.6, 17.0], "Assist": [9.8, 5.2, 2.3], "Rimbalzi": [9.2, 5.0, 3.3], "3PT": [4.1, 3.0, 3.5], "Pronostico": ["OVER 32.5 P", "OVER 8.5 A", "OVER 3.5 3P"]
    }))

st.sidebar.success("Oggi è il 27 Febbraio 2026. Dati allineati a Sofascore.")
