import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, scoreboardv2
import time

# --- 1. CONFIGURAZIONE E STILE ---
st.set_page_config(page_title="NBA Oracle ELITE", layout="wide", page_icon="🏀", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    div[data-testid="stStatusWidget"] {display:none;}
    
    .team-logo { width: 45px; vertical-align: middle; margin: 0 10px; }
    .match-header { font-size: 24px; font-weight: 800; text-align: center; margin-bottom: 5px; }
    .time-text { font-size: 14px; color: #888; text-align: center; margin-bottom: 20px; }
    .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem; }
    </style>
""", unsafe_allow_html=True)

def get_logo(abbr):
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{abbr.lower()}.png"

# --- 2. MOTORE DI RICERCA DATI (Auto-Aggiornamento 60 min) ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_nba_data():
    try:
        # A. Database Stagione Completa
        season = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame').get_data_frames()[0]
        df_sea = season[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']]
        
        # B. Database Ultime 10 Partite (Forma Recente)
        l10 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=10).get_data_frames()[0]
        df_l10 = l10[['PLAYER_ID', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']]
        
        # C. Unione dei due Database
        df = pd.merge(df_sea, df_l10, on='PLAYER_ID', suffixes=('', '_L10'), how='left').fillna(0)
        df = df.rename(columns={'PLAYER_NAME': 'Giocatore', 'TEAM_ABBREVIATION': 'Squadra'})
        
        # Filtro: Teniamo solo giocatori rilevanti (almeno 15 min di media in stagione)
        df = df[df['MIN'] > 15.0]

        # --- LOGICA 1: Rilevatore Infortuni (Injury/Out Status) ---
        # Se ha giocato < 4 partite nelle ultime 10, ma ne ha giocate tante in stagione, è infortunato/fuori.
        df['Stato'] = df.apply(lambda r: "🚑 OUT/Risk" if (r['GP_L10'] < 4 and r['GP'] > 15) else "✅ OK", axis=1)

        # --- LOGICA 2: Generatore Pronostico (Basato sul Trend L10) ---
        def calcola_pronostico(r):
            if r['Stato'] == "🚑 OUT/Risk": return "⛔ Evitare Bet"
            diff_pts = r['PTS_L10'] - r['PTS']
            if diff_pts >= 4.0: return "🔥 OVER Punti (Super Forma)"
            elif diff_pts <= -4.0: return "❄️ UNDER Punti (In Calo)"
            elif r['AST_L10'] >= 7.5: return "🎯 OVER Assist"
            elif r['REB_L10'] >= 10.0: return "🧱 OVER Rimbalzi"
            elif r['FG3M_L10'] >= 3.0: return "💦 OVER Triple"
            else: return "⚖️ Giocare le Medie"
        df['Pronostico'] = df.apply(calcola_pronostico, axis=1)

        # --- LOGICA 3: Giocata "Sicura" (Safe Pick) ---
        # Prende le stats reali delle ultime 10, le abbassa del 30% per dare una quota cassaforte
        def giocata_sicura(r):
            if r['Stato'] == "🚑 OUT/Risk": return "---"
            safe_pts = int(r['PTS_L10'] * 0.7)
            safe_ast = int(r['AST_L10'] * 0.7)
            safe_reb = int(r['REB_L10'] * 0.7)
            
            # Cerca la statistica più affidabile per la safe pick
            if safe_pts >= 12: return f"🟢 OVER {safe_pts}.5 P"
            elif safe_ast >= 5: return f"🟢 OVER {safe_ast}.5 A"
            elif safe_reb >= 6: return f"🟢 OVER {safe_reb}.5 R"
            else: return f"🟢 OVER {int(r['PTS_L10'] * 0.6)}.5 P"
        df['Safe Pick'] = df.apply(giocata_sicura, axis=1)

        # D. Partite della Notte
        games = scoreboardv2.ScoreboardV2().get_data_frames()[0]
        partite_oggi = []
        for _, row in games.iterrows():
            gamecode = row['GAMECODE']
            away, home = gamecode.split('/')[1][:3], gamecode.split('/')[1][3:]
            partite_oggi.append({'Casa': home, 'Trasferta': away, 'Orario': row['GAME_STATUS_TEXT']})

        # Ordina per chi è in forma (Punti L10) decrescente per le tabelle
        df = df.sort_values(by='PTS_L10', ascending=False)
        return df, partite_oggi
    except Exception as e:
        return None, None

with st.spinner("🔄 Connessione server NBA & Calcolo Trend in corso..."):
    df_totale, partite = get_nba_data()

# --- 3. INTERFACCIA APP ---
st.title("🏀 NBA Oracle ELITE")
st.caption("⚡ Aggiornamento Automatico | Analisi Forma Ultime 10 Partite | Rilevamento Infortuni")

if df_totale is None:
    st.error("⚠️ Server NBA irraggiungibili o blocco temporaneo. Riprova più tardi.")
    st.stop()

# 4 Schede (Tabs)
tab_match, tab_db_sea, tab_db_l10, tab_calc = st.tabs([
    "🔥 Match & Sicure", "🗄️ DB Stagione", "📈 Forma (Last 10)", "🧮 Calcolatore"
])

# ==========================================
# SCHEDA 1: PARTITE (Con Safe Picks e Infortuni)
# ==========================================
with tab_match:
    if not partite:
        st.info("Nessuna partita programmata dai server NBA per stanotte.")
    else:
        st.write("Le tabelle mostrano i migliori 6 giocatori. L'app segnala chi rischia di non giocare (🚑).")
        
        cfg = {
            "Giocatore": st.column_config.TextColumn("Nome"),
            "Stato": st.column_config.TextColumn("Status"),
            "PTS_L10": st.column_config.NumberColumn("PTS (Ultime 10)", format="%.1f"),
            "Pronostico": st.column_config.TextColumn("Analisi Trend"),
            "Safe Pick": st.column_config.TextColumn("Giocata Sicura 🟢")
        }

        for p in partite:
            h, a = p['Casa'], p['Trasferta']
            st.markdown(f"""
            <div class="match-header"><img src="{get_logo(h)}" class="team-logo">{h} <span style="color:#555;font-size:18px;">vs</span> {a}<img src="{get_logo(a)}" class="team-logo"></div>
            <div class="time-text">🕒 Orario USA: {p['Orario']}</div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown(f"**🏠 {h}**")
                df_h = df_totale[df_totale['Squadra'] == h].head(6)
                st.dataframe(df_h[['Giocatore', 'Stato', 'PTS_L10', 'Pronostico', 'Safe Pick']], column_config=cfg, hide_index=True, use_container_width=True)

            with c2:
                st.markdown(f"**✈️ {a}**")
                df_a = df_totale[df_totale['Squadra'] == a].head(6)
                st.dataframe(df_a[['Giocatore', 'Stato', 'PTS_L10', 'Pronostico', 'Safe Pick']], column_config=cfg, hide_index=True, use_container_width=True)

            st.divider()

# ==========================================
# SCHEDA 2 & 3: DATABASE STAGIONE E FORMA
# ==========================================
def render_database(df, prefisso_colonne, titolo, desc):
    st.subheader(titolo)
    st.write(desc)
    c1, c2, c3, c4 = st.columns(4)
    team = c1.selectbox("Squadra:", ["Tutte"] + sorted(df['Squadra'].unique().tolist()), key=prefisso_colonne+"_t")
    min_p = c2.number_input("PTS Min:", 0.0, 40.0, 0.0, key=prefisso_colonne+"_p")
    min_a = c3.number_input("AST Min:", 0.0, 15.0, 0.0, key=prefisso_colonne+"_a")
    min_r = c4.number_input("REB Min:", 0.0, 20.0, 0.0, key=prefisso_colonne+"_r")
    
    df_f = df.copy()
    if team != "Tutte": df_f = df_f[df_f['Squadra'] == team]
    df_f = df_f[(df_f[prefisso_colonne+'PTS'] >= min_p) & (df_f[prefisso_colonne+'AST'] >= min_a) & (df_f[prefisso_colonne+'REB'] >= min_r)]
    
    col_da_mostrare = ['Giocatore', 'Squadra', 'Stato', prefisso_colonne+'PTS', prefisso_colonne+'AST', prefisso_colonne+'REB', prefisso_colonne+'FG3M']
    st.dataframe(df_f[col_da_mostrare], hide_index=True, use_container_width=True)

with tab_db_sea:
    render_database(df_totale, "", "🗄️ Database Stagione", "Medie calcolate sull'intero anno.")

with tab_db_l10:
    render_database(df_totale, "PTS_L10".replace("PTS",""), "📈 Database Forma (Last 10)", "Medie basate SOLO sulle ultime 10 partite giocate.")

# ==========================================
# SCHEDA 4: CALCOLATORE VALORE
# ==========================================
with tab_calc:
    st.subheader("🧮 Calcolatore Vantaggio vs Bookmaker")
    cA, cB = st.columns(2)
    player = cA.selectbox("1. Giocatore:", sorted(df_totale['Giocatore'].tolist()))
    stat = cB.selectbox("2. Mercato:", ["PTS_L10 (Punti Forma)", "AST_L10 (Assist Forma)", "REB_L10 (Rimb Forma)"])
    
    media = df_totale[df_totale['Giocatore'] == player][stat].values[0]
    st.metric(f"Media Recente Reale ({stat})", f"{media:.1f}")
    
    linea = st.number_input("3. Linea Bookmaker:", 0.0, step=0.5)
    if linea > 0:
        margine = media - linea
        st.divider()
        if margine > 1.5: st.success(f"🔥 **SUPER VALORE!** Media > Linea di **{margine:.1f}**. 👉 **Gioca OVER**")
        elif margine < -1.5: st.error(f"❄️ **SOTTO MEDIA!** Media < Linea di **{abs(margine):.1f}**. 👉 **Gioca UNDER**")
        else: st.warning("⚖️ **LINEA PERFETTA.** Troppo vicina alla media reale. Rischioso.")
