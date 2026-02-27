import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, scoreboardv2
import time

# --- 1. CONFIGURAZIONE APP E STILE MODERNO ---
st.set_page_config(
    page_title="NBA Oracle PRO", 
    layout="wide", 
    page_icon="🏀",
    initial_sidebar_state="collapsed"
)

# Iniezione di CSS per rendere l'app "nativa" e pulita
st.markdown("""
    <style>
    /* Nasconde il menu Streamlit, il footer e il pulsante in basso */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    div[data-testid="stStatusWidget"] {display:none;}
    
    /* Migliora l'aspetto su mobile */
    .team-logo { width: 45px; vertical-align: middle; margin: 0 10px; }
    .match-header { font-size: 24px; font-weight: 800; text-align: center; margin-bottom: 5px; }
    .time-text { font-size: 14px; color: #888; text-align: center; margin-bottom: 20px; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #1f77b4; }
    
    /* Elimina spazi bianchi inutili in alto */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Helper per estrarre i loghi delle squadre ufficiali
def get_logo(abbr):
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{abbr.lower()}.png"

# --- 2. MOTORE DI RICERCA DATI (Auto-Aggiornamento 60 min) ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_nba_data():
    try:
        # Dati Stagionali
        player_stats = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame').get_data_frames()[0]
        df = player_stats[['PLAYER_NAME', 'TEAM_ABBREVIATION', 'MIN', 'PTS', 'AST', 'REB', 'FG3M']]
        df = df.rename(columns={
            'PLAYER_NAME': 'Giocatore', 'TEAM_ABBREVIATION': 'Squadra',
            'MIN': 'Min', 'PTS': 'Punti', 'AST': 'Assist', 'REB': 'Rimb', 'FG3M': '3PT'
        })
        df = df[df['Min'] > 12.0].sort_values(by='Punti', ascending=False) # Solo giocatori rilevanti

        # Generatore Pronostici Smart
        def genera_pronostico(row):
            if row['Punti'] > 25: return "🔥 OVER Punti"
            elif row['Assist'] > 8: return "🎯 OVER Assist"
            elif row['Rimb'] > 10: return "🧱 OVER Rimb"
            elif row['3PT'] >= 3: return "💦 OVER Triple"
            else: return "⚖️ Neutro"
        df['Pronostico'] = df.apply(genera_pronostico, axis=1)

        # Partite della Notte
        games = scoreboardv2.ScoreboardV2().get_data_frames()[0]
        partite_oggi = []
        for _, row in games.iterrows():
            gamecode = row['GAMECODE'] # Es. 20260227/LALDEN
            away = gamecode.split('/')[1][:3]
            home = gamecode.split('/')[1][3:]
            orario = row['GAME_STATUS_TEXT']
            partite_oggi.append({'Casa': home, 'Trasferta': away, 'Orario': orario})

        return df, partite_oggi
    except Exception as e:
        return None, None

# Caricamento Silenzioso
with st.spinner("🔄 Connessione server NBA in corso..."):
    df_totale, partite = get_nba_data()

# --- 3. INTERFACCIA A SCHEDE (Perfetta per Smartphone) ---
st.title("🏀 NBA Oracle PRO")
st.caption("⚡ Dati Ufficiali Live | Aggiornamento Automatico | Stile Sofascore")

if df_totale is None:
    st.error("⚠️ I server NBA sono temporaneamente in manutenzione. Riprova tra 5 minuti.")
    st.stop()

# Creazione delle 3 sezioni principali
tab_partite, tab_database, tab_calcolatore = st.tabs(["🔥 Partite Oggi", "🗄️ Database", "🧮 Calcolatore Valore"])

# ==========================================
# SCHEDA 1: PARTITE (Stile Sofascore)
# ==========================================
with tab_partite:
    if not partite:
        st.info("Nessuna partita trovata per stanotte secondo il calendario ufficiale NBA.")
    else:
        # Impostazione colonne per tabelle moderne
        cfg = {
            "Giocatore": st.column_config.TextColumn("Nome"),
            "Punti": st.column_config.NumberColumn("PTS", format="%.1f"),
            "Assist": st.column_config.NumberColumn("AST", format="%.1f"),
            "Rimb": st.column_config.NumberColumn("REB", format="%.1f"),
            "3PT": st.column_config.NumberColumn("3PT", format="%.1f"),
            "Pronostico": st.column_config.TextColumn("Consiglio")
        }

        for p in partite:
            home = p['Casa']
            away = p['Trasferta']

            # Intestazione Match con Loghi 
            st.markdown(f"""
            <div class="match-header">
                <img src="{get_logo(home)}" class="team-logo"> {home} <span style="color:#555; font-size:18px;">vs</span> {away} <img src="{get_logo(away)}" class="team-logo">
            </div>
            <div class="time-text">🕒 Orario USA/Status: {p['Orario']}</div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            
            # Squadra in Casa
            with c1:
                st.markdown(f"**🏠 {home}**")
                df_home = df_totale[df_totale['Squadra'] == home].head(6)
                st.dataframe(df_home[['Giocatore', 'Punti', 'Assist', 'Rimb', '3PT', 'Pronostico']],
                             column_config=cfg, hide_index=True, use_container_width=True)

            # Squadra in Trasferta
            with c2:
                st.markdown(f"**✈️ {away}**")
                df_away = df_totale[df_totale['Squadra'] == away].head(6)
                st.dataframe(df_away[['Giocatore', 'Punti', 'Assist', 'Rimb', '3PT', 'Pronostico']],
                             column_config=cfg, hide_index=True, use_container_width=True)

            st.divider()

# ==========================================
# SCHEDA 2: DATABASE AVANZATO
# ==========================================
with tab_database:
    st.subheader("🔍 Filtri Avanzati Giocatori")
    
    # Barra di ricerca mobile-friendly
    col_cerca, col_team = st.columns(2)
    cerca = col_cerca.text_input("Cerca Nome (es. Curry):")
    squadra = col_team.selectbox("Scegli Squadra:", ["Tutte"] + sorted(df_totale['Squadra'].unique().tolist()))

    st.write("**Filtra per Statistiche Minime:**")
    f1, f2, f3, f4 = st.columns(4)
    min_p = f1.number_input("PTS", 0.0, 40.0, 0.0, 1.0)
    min_a = f2.number_input("AST", 0.0, 15.0, 0.0, 1.0)
    min_r = f3.number_input("REB", 0.0, 20.0, 0.0, 1.0)
    min_3 = f4.number_input("3PT", 0.0, 6.0, 0.0, 0.5)

    # Applicazione filtri multipli
    df_fil = df_totale.copy()
    if squadra != "Tutte": df_fil = df_fil[df_fil['Squadra'] == squadra]
    if cerca: df_fil = df_fil[df_fil['Giocatore'].str.contains(cerca, case=False)]
    df_fil = df_fil[(df_fil['Punti'] >= min_p) & (df_fil['Assist'] >= min_a) & 
                    (df_fil['Rimb'] >= min_r) & (df_fil['3PT'] >= min_3)]

    st.dataframe(df_fil[['Giocatore', 'Squadra', 'Min', 'Punti', 'Assist', 'Rimb', '3PT']], 
                 hide_index=True, use_container_width=True, height=500)

# ==========================================
# SCHEDA 3: CALCOLATORE DEL VALORE QUOTE
# ==========================================
with tab_calcolatore:
    st.subheader("🧮 Trova il Vantaggio sul Bookmaker")
    st.write("Confronta matematicamente la linea del sito di scommesse con la media stagionale reale.")

    # Selettori compatti
    cA, cB = st.columns(2)
    player_calc = cA.selectbox("1. Seleziona Giocatore:", sorted(df_totale['Giocatore'].tolist()))
    stat_calc = cB.selectbox("2. Mercato Scommessa:", ["Punti", "Assist", "Rimb", "3PT"])

    media_reale = df_totale[df_totale['Giocatore'] == player_calc][stat_calc].values[0]
    
    # Mette in risalto la media reale
    st.metric(f"Media Stagionale Reale ({stat_calc})", f"{media_reale:.1f}")

    linea_book = st.number_input("3. Inserisci la Linea del Bookmaker (es. 25.5):", min_value=0.0, value=0.0, step=0.5)

    if linea_book > 0:
        margine = media_reale - linea_book
        st.divider()
        if margine > 1.5:
            st.success(f"🔥 **SUPER VALORE!** La media è più alta della linea di **{margine:.1f}**. \n\n👉 **Giocata Suggerita: OVER**")
        elif margine > 0:
            st.info(f"👍 **LEGGERO VANTAGGIO:** La media supera la linea di **{margine:.1f}**. \n\n👉 **Giocata Suggerita: OVER**")
        elif margine < -1.5:
            st.error(f"❄️ **SOTTO MEDIA:** La media è più bassa della linea di **{abs(margine):.1f}**. \n\n👉 **Giocata Suggerita: UNDER**")
        else:
            st.warning("⚖️ **LINEA PERFETTA:** Il bookmaker ha impostato la linea quasi esattamente sulla media. Scommessa molto rischiosa.")


