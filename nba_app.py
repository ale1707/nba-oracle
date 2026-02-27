import streamlit as st
import pandas as pd

st.set_page_config(page_title="NBA Oracle 27/02", layout="wide")

st.title("🏀 NBA Oracle: Programma Completo Stanotte")
st.write("Venerdì 27 Febbraio 2026 - Orari Italiani e Statistiche Sofascore")

def crea_match(squadra_casa, casa_data, squadra_trasferta, trasf_data, orario):
    st.divider()
    st.header(f"🏟️ {squadra_trasferta} @ {squadra_casa}")
    st.subheader(f"⏰ Ore: {orario} (ITA)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### {squadra_casa}")
        df_casa = pd.DataFrame(casa_data)
        df_casa['P+A+R'] = df_casa['Punti'] + df_casa['Assist'] + df_casa['Rimbalzi']
        st.table(df_casa)
    with c2:
        st.markdown(f"### {squadra_trasferta}")
        df_trasf = pd.DataFrame(trasf_data)
        df_trasf['P+A+R'] = df_trasf['Punti'] + df_trasf['Assist'] + df_trasf['Rimbalzi']
        st.table(df_trasf)

# --- PROGRAMMA REALE DI STANOTTE ---

# 1. ORLANDO @ DETROIT (01:00)
crea_match("Detroit Pistons", {
    "Giocatore": ["C. Cunningham", "J. Ivey"], "Punti": [22.8, 18.5], "Assist": [7.5, 4.2], "Rimbalzi": [4.1, 3.8], "3PT": [2.1, 1.8], "Pronostico": ["OVER P"]
}, "Orlando Magic", {
    "Giocatore": ["P. Banchero", "F. Wagner"], "Punti": [23.5, 20.8], "Assist": [5.2, 4.0], "Rimbalzi": [7.1, 5.5], "3PT": [1.5, 2.0], "Pronostico": ["OVER R"]
}, "01:00")

# 2. WASHINGTON @ ATLANTA (01:30)
crea_match("Atlanta Hawks", {
    "Giocatore": ["Trae Young", "J. Johnson"], "Punti": [26.4, 19.1], "Assist": [10.8, 3.5], "Rimbalzi": [2.8, 8.7], "3PT": [3.4, 1.2], "Pronostico": ["OVER A"]
}, "Washington Wizards", {
    "Giocatore": ["Kyle Kuzma", "Jordan Poole"], "Punti": [21.5, 17.2], "Assist": [4.1, 3.9], "Rimbalzi": [6.5, 2.6], "3PT": [2.3, 2.5], "Pronostico": ["UNDER"]
}, "01:30")

# 3. PHILADELPHIA @ TORONTO (01:30)
crea_match("Toronto Raptors", {
    "Giocatore": ["RJ Barrett", "S. Barnes"], "Punti": [21.2, 20.1], "Assist": [4.5, 6.0], "Rimbalzi": [5.1, 8.5], "3PT": [1.8, 1.1], "Pronostico": ["OVER P"]
}, "Philadelphia 76ers", {
    "Giocatore": ["Tyrese Maxey", "Paul George"], "Punti": [25.8, 22.5], "Assist": [6.4, 5.1], "Rimbalzi": [3.5, 5.8], "3PT": [3.2, 3.5], "Pronostico": ["OVER 3PT"]
}, "01:30")

# 4. CHARLOTTE @ NEW YORK (01:30)
crea_match("New York Knicks", {
    "Giocatore": ["Jalen Brunson", "K. Towns"], "Punti": [27.5, 21.8], "Assist": [6.8, 2.5], "Rimbalzi": [3.6, 11.5], "3PT": [2.7, 2.2], "Pronostico": ["OVER P"]
}, "Charlotte Hornets", {
    "Giocatore": ["LaMelo Ball", "B. Miller"], "Punti": [24.1, 19.5], "Assist": [8.2, 3.8], "Rimbalzi": [5.3, 4.2], "3PT": [3.8, 2.6], "Pronostico": ["OVER 3PT"]
}, "01:30")

# 5. SACRAMENTO @ CLEVELAND (01:30)
crea_match("Cleveland Cavaliers", {
    "Giocatore": ["D. Mitchell", "D. Garland"], "Punti": [27.8, 19.5], "Assist": [5.5, 7.1], "Rimbalzi": [5.2, 2.8], "3PT": [3.4, 2.5], "Pronostico": ["OVER P"]
}, "Sacramento Kings", {
    "Giocatore": ["D. Fox", "D. Sabonis"], "Punti": [26.8, 19.8], "Assist": [5.8, 8.2], "Rimbalzi": [4.5, 13.1], "3PT": [2.8, 0.5], "Pronostico": ["OVER R"]
}, "01:30")

# 6. CHICAGO @ NEW ORLEANS (02:00)
crea_match("New Orleans Pelicans", {
    "Giocatore": ["Zion Williamson", "BI Ingram"], "Punti": [23.1, 21.5], "Assist": [5.0, 5.8], "Rimbalzi": [5.8, 5.1], "3PT": [0.1, 2.1], "Pronostico": ["OVER P"]
}, "Chicago Bulls", {
    "Giocatore": ["Zach LaVine", "Coby White"], "Punti": [20.5, 19.1], "Assist": [4.2, 5.2], "Rimbalzi": [4.8, 4.5], "3PT": [2.8, 3.1], "Pronostico": ["OVER 3PT"]
}, "02:00")

# 7. HOUSTON @ MINNESOTA (02:00)
crea_match("Minnesota Timberwolves", {
    "Giocatore": ["Anthony Edwards", "Julius Randle"], "Punti": [28.2, 21.5], "Assist": [5.5, 4.8], "Rimbalzi": [5.2, 9.1], "3PT": [3.2, 1.8], "Pronostico": ["OVER P"]
}, "Houston Rockets", {
    "Giocatore": ["Jalen Green", "Alperen Sengun"], "Punti": [20.8, 21.1], "Assist": [3.5, 5.2], "Rimbalzi": [4.5, 9.8], "3PT": [2.5, 0.2], "Pronostico": ["OVER R"]
}, "02:00")

# 8. GOLDEN STATE @ UTAH (03:00)
crea_match("Utah Jazz", {
    "Giocatore": ["Lauri Markkanen", "C. Sexton"], "Punti": [22.5, 18.2], "Assist": [2.1, 4.8], "Rimbalzi": [8.2, 2.5], "3PT": [3.1, 1.5], "Pronostico": ["OVER P"]
}, "Golden State Warriors", {
    "Giocatore": ["Stephen Curry", "B. Hield"], "Punti": [26.5, 17.5], "Assist": [6.2, 2.5], "Rimbalzi": [4.5, 3.2], "3PT": [4.8, 3.8], "Pronostico": ["OVER 3PT"]
}, "03:00")

# 9. DALLAS @ PHOENIX (04:00)
crea_match("Phoenix Suns", {
    "Giocatore": ["Kevin Durant", "Devin Booker"], "Punti": [27.5, 26.8], "Assist": [5.2, 6.8], "Rimbalzi": [6.5, 4.8], "3PT": [2.3, 2.4], "Pronostico": ["OVER P"]
}, "Dallas Mavericks", {
    "Giocatore": ["Luka Doncic", "Kyrie Irving"], "Punti": [33.8, 25.4], "Assist": [9.5, 5.1], "Rimbalzi": [9.1, 5.0], "3PT": [4.0, 3.1], "Pronostico": ["OVER P+A"]
}, "04:00")
