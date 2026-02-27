import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, scoreboardv2

# --- 1. CONFIGURAZIONE E STILE ---
st.set_page_config(page_title="NBA Oracle ULTIMATE", layout="wide", page_icon="🏀", initial_sidebar_state="collapsed")

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
    .injury-alert { color: #ff4b4b; font-weight: bold; font-size: 14px; margin-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

def get_logo(abbr):
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{abbr.lower()}.png"

# --- 2. MOTORE DI RICERCA DATI (Aggiornamento ogni 60 min) ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_nba_data():
    try:
        # A. Database Stagione
        season = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame').get_data_frames()[0]
        df_sea = season[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']]
        
        # B. Database Ultime 10 Partite
        l10 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=10).get_data_frames()[0]
        df_l10 = l10[['PLAYER_ID', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']]
        
        # C. Unione Database
        df = pd.merge(df_sea, df_l10, on='PLAYER_ID', suffixes=('', '_L10'), how='left').fillna(0)
        df = df.rename(columns={'PLAYER_NAME': 'Giocatore', 'TEAM_ABBREVIATION': 'Squadra'})
        
        # Filtro base per escludere panchinari inutili
        df = df[df['MIN'] > 15.0]

        # --- LOGICA SICUREZZA INFORTUNI ---
        def calcola_stato(r):
            if r['GP_L10'] == 0 and r['GP'] > 5: return "❌ OUT (0 Min. Recenti)"
            elif r['GP_L10'] < 4 and r['GP'] > 15: return "🚑 DUBBIO / Rischio"
            else: return "✅ OK"
        df['Stato'] = df.apply(calcola_stato, axis=1)

        # --- LOGICA PRONOSTICO TREND ---
        def calcola_pronostico(r):
            if "OUT" in r['Stato'] or "DUBBIO" in r['Stato']: return "⛔ Evitare Bet"
            diff = r['PTS_L10'] - r['PTS']
            if diff >= 4.0: return "🔥 OVER Punti"
            elif diff <= -4.0: return "❄️ UNDER Punti"
            elif r['AST_L10'] >= 7.5: return "🎯 OVER Assist"
            elif r['REB_L10'] >= 9.0: return "🧱 OVER Rimbalzi"
            elif r['FG3M_L10'] >= 3.0: return "💦 OVER Triple"
            else: return "⚖️ Affidabile (Medie fisse)"
        df['Trend'] = df.apply(calcola_pronostico, axis=1)

        # --- LOGICA SAFE PICK (Quota Cassaforte) ---
        def giocata_sicura(r):
            if "OUT" in r['Stato'] or "DUBBIO" in r['Stato']: return "---"
            pts_ref = r['PTS_L10'] if r['PTS_L10'] > 0 else r['PTS']
            safe_val = int(pts_ref * 0.7)
            if safe_val >= 10: return f"🟢 OVER {safe_val}.5 P"
            elif r['AST_L10'] >= 6.0: return f"🟢 OVER {int(r['AST_L10']*0.7)}.5 A"
            elif r['REB_L10'] >= 8.0: return f"🟢 OVER {int(r['REB_L10']*0.7)}.5 R"
            else: return "---"
        df['Safe Pick'] = df.apply(giocata_sicura, axis=1)

        # Partite della Notte
        games = scoreboardv2.ScoreboardV2().get_data_frames()[0]
        partite_oggi = []
        for _, row in games.iterrows():
            gamecode = row['GAMECODE']
            away, home = gamecode.split('/')[1][:3], gamecode.split('/')[1][3:]
            partite_oggi.append({'Casa': home, 'Trasferta': away, 'Orario': row['GAME_STATUS_TEXT']})

        return df, partite_oggi
    except Exception as e:
        return None, None

with st.spinner("🔄 Connessione server NBA ed elaborazione dati in corso..."):
    df_totale, partite = get_nba_data()

if df_totale is None:
    st.error("⚠️ Errore di connessione ai server NBA. Ricarica la pagina tra un istante.")
    st.stop()

# --- 3. INTERFACCIA APP ---
st.title("🏀 NBA Oracle ULTIMATE")
st.caption("⚡ Auto-Update 60 min | Database Completo | Rilevamento Assenze Statistiche")

tab_match, tab_db_sea, tab_db_l10, tab_calc = st.tabs([
    "🔥 Match & Pronostici", "🗄️ Database Stagione", "📈 Forma (Last 10)", "🧮 Calcolatore Valore"
])

# ==========================================
# SCHEDA 1: MATCH E PRONOSTICI LIVE
# ==========================================
with tab_match:
    if not partite:
        st.info("Nessuna partita in programma trovata sui server NBA per la giornata odierna.")
    else:
        for p in partite:
            h, a = p['Casa'], p['Trasferta']
            st.markdown(f"""
            <div class="match-header"><img src="{get_logo(h)}" class="team-logo">{h} vs {a}<img src="{get_logo(a)}" class="team-logo"></div>
            <div class="time-text">🕒 Orario USA/Status: {p['Orario']}</div>
            """, unsafe_allow_html=True)
            
            # --- RADAR INFORTUNI ---
            outs_h = df_totale[(df_totale['Squadra'] == h) & (df_totale['Stato'] != "✅ OK")]['Giocatore'].tolist()
            outs_a = df_totale[(df_totale['Squadra'] == a) & (df_totale['Stato'] != "✅ OK")]['Giocatore'].tolist()
            
            if outs_h or outs_a:
                allarme = "🚑 **RADAR ASSENZE/RISCHIO:** "
                if outs_h: allarme += f"**{h}** ({', '.join(outs_h[:4])}) | "
                if outs_a: allarme += f"**{a}** ({', '.join(outs_a[:4])})"
                st.markdown(f'<div class="injury-alert">{allarme}</div>', unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            col_view = ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'Trend', 'Safe Pick']
            
            with c1:
                st.markdown(f"**🏠 {h} (Padroni di Casa)**")
                st.dataframe(df_totale[df_totale['Squadra'] == h][col_view].sort_values('PTS_L10', ascending=False).head(7), hide_index=True)
            with c2:
                st.markdown(f"**✈️ {a} (In Trasferta)**")
                st.dataframe(df_totale[df_totale['Squadra'] == a][col_view].sort_values('PTS_L10', ascending=False).head(7), hide_index=True)
            
            st.divider()

# ==========================================
# FUNZIONE PER RENDERIZZARE I DATABASE A TENDINA
# ==========================================
def render_grouped_db(df, cols, order_col):
    squadre = sorted(df['Squadra'].unique())
    for s in squadre:
        with st.expander(f"🏀 {s} - Espandi per vedere i giocatori"):
            df_s = df[df['Squadra'] == s][cols].sort_values(by=order_col, ascending=False)
            st.dataframe(df_s, hide_index=True, use_container_width=True)

# ==========================================
# SCHEDA 2 E 3: DATABASE CON SQUADRE A TENDINA
# ==========================================
with tab_db_sea:
    st.subheader("🗄️ Statistiche Medie Stagionali (Per Squadra)")
    st.write("Dati calcolati su tutte le partite giocate da inizio anno ad oggi.")
    col_sea = ['Giocatore', 'Stato', 'PTS', 'AST', 'REB', 'FG3M']
    render_grouped_db(df_totale, col_sea, 'PTS')

with tab_db_l10:
    st.subheader("📈 Stato di Forma (Ultime 10 Partite)")
    st.write("Dati calcolati SOLO sulle ultime 10 prestazioni. Ideale per capire chi è 'on fire'.")
    col_l10 = ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'FG3M_L10']
    render_grouped_db(df_totale, col_l10, 'PTS_L10')

# ==========================================
# SCHEDA 4: CALCOLATORE VALORE
# ==========================================
with tab_calc:
    st.subheader("🧮 Calcolatore Vantaggio Matematico vs Bookmaker")
    
    cA, cB = st.columns(2)
    p_sel = cA.selectbox("1. Seleziona Giocatore:", sorted(df_totale['Giocatore'].tolist()))
    stat_type = cB.radio("2. Mercato da analizzare:", ["Punti", "Assist", "Rimbalzi"])
    
    col_map = {"Punti": "PTS_L10", "Assist": "AST_L10", "Rimbalzi": "REB_L10"}
    val_form = df_totale[df_totale['Giocatore'] == p_sel][col_map[stat_type]].values[0]
    stato_p = df_totale[df_totale['Giocatore'] == p_sel]['Stato'].values[0]
    
    st.metric(f"Media {stat_type} (Ultime 10)", f"{val_form:.1f}", delta=stato_p, delta_color="off")
    
    linea = st.number_input("3. Inserisci Linea proposta dal Bookmaker:", step=0.5)
    
    if linea > 0:
        st.divider()
        if "OUT" in stato_p or "DUBBIO" in stato_p:
            st.error("⚠️ **ATTENZIONE:** Il giocatore risulta a rischio assenza. Sconsigliato scommettere.")
        else:
            margine = val_form - linea
            if margine > 1.5: st.success(f"🔥 **SUPER VALORE!** La media è superiore alla linea di **{margine:.1f}**. 👉 **Gioca OVER**")
            elif margine < -1.5: st.error(f"❄️ **SOTTO MEDIA!** La media è inferiore alla linea di **{abs(margine):.1f}**. 👉 **Gioca UNDER**")
            else: st.warning("⚖️ **LINEA PERFETTA.** Il bookmaker ha centrato la quota. Scommessa sconsigliata a livello matematico.")
