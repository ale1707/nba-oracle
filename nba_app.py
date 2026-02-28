import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, scoreboardv2
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- 1. CONFIGURAZIONE E STILE (UI MOBILE FRIENDLY) ---
st.set_page_config(page_title="NBA Oracle ULTIMATE", layout="wide", page_icon="🏀", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
    .team-logo { width: 45px; vertical-align: middle; margin: 0 10px; }
    .team-logo-large { width: 80px; margin-bottom: 10px; display: block; }
    .match-header { font-size: 22px; font-weight: 800; text-align: center; margin-bottom: 5px; color: #1E1E1E; }
    .injury-alert { background-color: #fff1f1; color: #d9534f; font-weight: bold; font-size: 14px; margin-bottom: 15px; border: 2px solid #d9534f; padding: 10px; border-radius: 8px; text-align: center; }
    .result-box { display: flex; justify-content: center; align-items: center; background: #fdfdfd; padding: 12px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #eee; border-left: 5px solid #ff4b4b; }
    [data-testid="stDataFrame"] { width: 100%; overflow-x: auto; }
    .bet-box { background-color: #f8f9fa; border-left: 4px solid #00C853; padding: 10px; margin-bottom: 10px; border-radius: 5px;}
    .bet-box-medium { border-left-color: #FFD600; }
    .bet-box-high { border-left-color: #D50000; }
    </style>
""", unsafe_allow_html=True)

TEAM_NAMES = {
    'ATL': 'Atlanta Hawks', 'BOS': 'Boston Celtics', 'BKN': 'Brooklyn Nets', 'CHA': 'Charlotte Hornets',
    'CHI': 'Chicago Bulls', 'CLE': 'Cleveland Cavaliers', 'DAL': 'Dallas Mavericks', 'DEN': 'Denver Nuggets',
    'DET': 'Detroit Pistons', 'GSW': 'Golden State Warriors', 'HOU': 'Houston Rockets', 'IND': 'Indiana Pacers',
    'LAC': 'LA Clippers', 'LAL': 'Los Angeles Lakers', 'MEM': 'Memphis Grizzlies', 'MIA': 'Miami Heat',
    'MIL': 'Milwaukee Bucks', 'MIN': 'Minnesota Timberwolves', 'NOP': 'New Orleans Pelicans', 'NYK': 'New York Knicks',
    'OKC': 'Oklahoma City Thunder', 'ORL': 'Orlando Magic', 'PHI': 'Philadelphia 76ers', 'PHX': 'Phoenix Suns',
    'POR': 'Portland Trail Blazers', 'SAC': 'Sacramento Kings', 'SAS': 'San Antonio Spurs', 'TOR': 'Toronto Raptors',
    'UTA': 'Utah Jazz', 'WAS': 'Washington Wizards'
}

# FIX LOGHI: Traduttore per le discrepanze tra NBA API e ESPN
def get_logo(abbr):
    espn_abbr = { 'GSW': 'gs', 'NOP': 'no', 'NYK': 'ny', 'SAS': 'sa', 'UTA': 'utah', 'WAS': 'wsh', 'LAL': 'lal', 'LAC': 'lac' }.get(abbr.upper(), abbr.lower())
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{espn_abbr}.png"

# PULSANTE DI AGGIORNAMENTO FORZATO E CONTROLLO ORARIO
c_title, c_btn = st.columns([7, 3])
with c_title: st.title("🏀 NBA Oracle ULTIMATE")
with c_btn:
    if st.button("🔄 Forza Aggiornamento Dati", use_container_width=True):
        st.cache_data.clear(); st.rerun()

# --- 2. MOTORE DATI (FUSO ORARIO US + FIX INFORTUNI + MOTIVAZIONI) ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_nba_data():
    try:
        now_est = datetime.now(ZoneInfo("America/New_York"))
        today_str = now_est.strftime('%Y-%m-%d')
        yesterday_str = (now_est - timedelta(1)).strftime('%Y-%m-%d')

        season = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame').get_data_frames()[0]
        l10 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=10).get_data_frames()[0]
        l3 = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame', last_n_games=3).get_data_frames()[0]
        
        df = pd.merge(season[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'MIN', 'PTS', 'AST', 'REB', 'FG3M', 'GP']], l10[['PLAYER_ID', 'PTS', 'AST', 'REB', 'FG3M', 'GP']], on='PLAYER_ID', how='left', suffixes=('', '_L10'))
        df = pd.merge(df, l3[['PLAYER_ID', 'GP']], on='PLAYER_ID', how='left', suffixes=('', '_L3')).fillna(0)
        df = df.rename(columns={'PLAYER_NAME': 'Giocatore', 'TEAM_ABBREVIATION': 'Abbr'})
        df['Squadra'] = df['Abbr'].map(TEAM_NAMES)
        df = df[df['MIN'] > 8.0]

        def check_status(r):
            if r['GP_L3'] == 0 and r['GP_L10'] == 0 and r['GP'] > 2: return "❌ OUT"
            elif r['GP_L3'] == 0 and r['GP_L10'] > 0: return "🚑 DUBBIO"
            else: return "✅ OK"
        df['Stato'] = df.apply(check_status, axis=1)

        # GENERATORE MOTIVAZIONI E PRONOSTICI
        def get_motivation(r):
            if "OUT" in r['Stato']: return f"❌ Assenza pesante."
            if "DUBBIO" in r['Stato']: return f"⚠️ In dubbio per stasera. Da monitorare."
            diff = r['PTS_L10'] - r['PTS']
            if diff >= 4.0: return f"🔥 Forma pazzesca: {r['PTS_L10']:.1f} pt nelle ultime 10 (Media stagionale {r['PTS']:.1f}). Ottimo da Over."
            elif diff <= -4.0: return f"❄️ Sotto tono: solo {r['PTS_L10']:.1f} pt di recente ({r['PTS']:.1f} stagionali)."
            elif r['AST_L10'] > r['AST'] + 1.5: return f"🎯 Focus Assist: sta smazzando {r['AST_L10']:.1f} assist a partita nelle ultime 10."
            elif r['REB_L10'] > r['REB'] + 1.5: return f"🧱 Dominio a rimbalzo: {r['REB_L10']:.1f} rimb nelle ultime 10."
            else: return f"⚖️ Costante e in linea con le sue medie ({r['PTS_L10']:.1f} pt)."
        df['Motivazione'] = df.apply(get_motivation, axis=1)
        df['Safe Pick'] = df.apply(lambda r: f"🟢 OV {int(r['PTS_L10'] * 0.72)}.5" if r['Stato'] == "✅ OK" and r['PTS_L10']>8 else "-", axis=1)

        games = scoreboardv2.ScoreboardV2(game_date=today_str).get_data_frames()[0]
        partite_oggi = []
        for _, row in games.iterrows():
            gc = row['GAMECODE']
            away_a, home_a = gc.split('/')[1][:3], gc.split('/')[1][3:]
            partite_oggi.append({'Casa': TEAM_NAMES.get(home_a, home_a), 'CasaAbbr': home_a, 'Trasferta': TEAM_NAMES.get(away_a, away_a), 'TrasfertaAbbr': away_a, 'Status': row['GAME_STATUS_TEXT']})

        sb_yesterday = scoreboardv2.ScoreboardV2(game_date=yesterday_str).get_data_frames()
        risultati_ieri = []
        if not sb_yesterday[0].empty:
            header, linescore = sb_yesterday[0], sb_yesterday[1]
            for _, row in header.iterrows():
                h_id, a_id = row['HOME_TEAM_ID'], row['VISITOR_TEAM_ID']
                h_score = linescore[linescore['TEAM_ID'] == h_id]['PTS'].values[0] if not linescore[linescore['TEAM_ID'] == h_id].empty else 0
                a_score = linescore[linescore['TEAM_ID'] == a_id]['PTS'].values[0] if not linescore[linescore['TEAM_ID'] == a_id].empty else 0
                gc_parts = row['GAMECODE'].split('/')[1]
                risultati_ieri.append({ 'Casa': TEAM_NAMES.get(gc_parts[3:], "Home"), 'CasaAbbr': gc_parts[3:], 'CasaPts': h_score, 'Trasferta': TEAM_NAMES.get(gc_parts[:3], "Away"), 'TrasfertaAbbr': gc_parts[:3], 'TrasfertaPts': a_score })
        return df, partite_oggi, risultati_ieri
    except Exception as e: return None, None, None

df_totale, partite, risultati = get_nba_data()

if df_totale is None:
    st.error("Errore API NBA. Clicca 'Forza Aggiornamento' in alto."); st.stop()

# --- GENERATORE SCHEDINE (Sisal Style) ---
def genera_schedine(df_match):
    df_ok = df_match[df_match['Stato'] == '✅ OK'].sort_values('PTS_L10', ascending=False)
    if len(df_ok) < 4: return None, None, None
    p1, p2, p3, p4 = df_ok.iloc[0], df_ok.iloc[1], df_ok.iloc[2], df_ok.iloc[3]
    
    b_sic = f"**{p1['Giocatore']}** OVER {int(p1['PTS_L10']*0.7)}.5 Punti\n<br>**{p2['Giocatore']}** OVER {int(p2['PTS_L10']*0.7)}.5 Punti"
    b_med = f"**{p1['Giocatore']}** OVER {int(p1['PTS_L10']*0.85)}.5 Punti\n<br>**{p3['Giocatore']}** OVER {int(p3['PTS_L10']*0.85)}.5 Punti\n<br>**{p2['Giocatore']}** OVER {int(p2['AST_L10']*0.8)}.5 Assist"
    b_alt = f"**{p1['Giocatore']}** OVER {int(p1['PTS_L10'])}.5 Punti\n<br>**{p2['Giocatore']}** OVER {int(p2['PTS_L10'])}.5 Punti\n<br>**{p4['Giocatore']}** OVER {int(p4['PTS_L10']*0.9)}.5 Punti\n<br>**{p1['Giocatore']}** OVER {int(p1['FG3M_L10'])}.5 Triple"
    return b_sic, b_med, b_alt

# --- 3. INTERFACCIA ---
t1, t_res, t2, t3, t4 = st.tabs(["🔥 MATCH DAY", "📅 IERI", "📊 STAGIONE", "📈 L10", "🧮 VANTAGGIO"])

with t1:
    if not partite: st.info("Nessuna partita in programma oggi (in base al fuso orario americano).")
    else:
        for p in partite:
            st.markdown(f'<div class="match-header"><img src="{get_logo(p["CasaAbbr"])}" class="team-logo">{p["CasaAbbr"]} vs {p["TrasfertaAbbr"]}<img src="{get_logo(p["TrasfertaAbbr"])}" class="team-logo"></div>', unsafe_allow_html=True)
            df_match = df_totale[(df_totale['Squadra'] == p['Casa']) | (df_totale['Squadra'] == p['Trasferta'])]
            out = df_match[df_match['Stato'] != "✅ OK"]['Giocatore'].tolist()
            if out: st.markdown(f'<div class="injury-alert">🚑 ASSENZE RILEVATE: {", ".join(out[:6])}</div>', unsafe_allow_html=True)
            
            # TABELLA 1: STATISTICHE (Tornate Punti, Assist, Rimb, Triple)
            cfg_mobile = { "Giocatore": st.column_config.TextColumn("Giocatore", width="medium"), "Stato": st.column_config.TextColumn("St", width="small"), "PTS_L10": st.column_config.NumberColumn("PTS", format="%.1f"), "AST_L10": st.column_config.NumberColumn("AST", format="%.1f"), "REB_L10": st.column_config.NumberColumn("REB", format="%.1f"), "FG3M_L10": st.column_config.NumberColumn("3PM", format="%.1f"), "Safe Pick": st.column_config.TextColumn("Pick", width="medium") }
            col_m = ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'FG3M_L10', 'Safe Pick']
            c1, c2 = st.columns(2)
            with c1: st.markdown(f"**🏠 {p['Casa']}**"); st.dataframe(df_totale[df_totale['Squadra'] == p['Casa']][col_m].sort_values('PTS_L10', ascending=False).head(8), hide_index=True, use_container_width=True, column_config=cfg_mobile)
            with c2: st.markdown(f"**✈️ {p['Trasferta']}**"); st.dataframe(df_totale[df_totale['Squadra'] == p['Trasferta']][col_m].sort_values('PTS_L10', ascending=False).head(8), hide_index=True, use_container_width=True, column_config=cfg_mobile)
            
            # TENDINA 1: MOTIVAZIONI
            with st.expander("💡 Pronostici Dettagliati e Motivazioni"):
                for _, row in df_match[df_match['PTS_L10'] > 12].sort_values('PTS_L10', ascending=False).head(6).iterrows():
                    st.markdown(f"**{row['Giocatore']} ({row['Squadra']})**: {row['Motivazione']}")

            # TENDINA 2: SCHEDINE PRONTE
            with st.expander("🎟️ Schedine Pronte (Quote stile Sisal)"):
                sic, med, alt = genera_schedine(df_match)
                if sic:
                    st.markdown(f'<div class="bet-box">🟢 <b>SCHEDINA SICURA (Raddoppio facile)</b><br>{sic}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="bet-box bet-box-medium">🟡 <b>SCHEDINA MEDIA (Buon Profitto)</b><br>{med}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="bet-box bet-box-high">🔴 <b>SCHEDINA ALTA (Rischio/Premio)</b><br>{alt}</div>', unsafe_allow_html=True)
                else: st.warning("Dati insufficienti per generare le schedine.")
            st.divider()

with t_res:
    if not risultati: st.info("Risultati di ieri non disponibili.")
    for r in risultati: st.markdown(f'<div class="result-box"><div style="flex:1;text-align:right;"><b>{r["CasaAbbr"]}</b> <img src="{get_logo(r["CasaAbbr"])}" width="35"></div><div style="flex:0.6;text-align:center;font-size:20px;font-weight:bold;color:#1E1E1E;">{r["CasaPts"]} - {r["TrasfertaPts"]}</div><div style="flex:1;text-align:left;"><img src="{get_logo(r["TrasfertaAbbr"])}" width="35"> <b>{r["TrasfertaAbbr"]}</b></div></div>', unsafe_allow_html=True)

def render_db(df, cols, sort_col, cfg=None):
    for s in sorted(df['Squadra'].dropna().unique()):
        with st.expander(f"{s}"): # Nessuna emoji, apro e c'è il logo
            abbr = df[df['Squadra'] == s]['Abbr'].iloc[0]
            st.markdown(f"<img src='{get_logo(abbr)}' class='team-logo-large'>", unsafe_allow_html=True)
            st.dataframe(df[df['Squadra'] == s][cols].sort_values(sort_col, ascending=False), hide_index=True, use_container_width=True, column_config=cfg)

with t2: render_db(df_totale, ['Giocatore', 'Stato', 'PTS', 'AST', 'REB', 'FG3M', 'GP'], 'PTS')
with t3: render_db(df_totale, ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'FG3M_L10', 'GP_L10'], 'PTS_L10', {"PTS_L10": "PTS", "AST_L10": "AST", "REB_L10": "REB", "FG3M_L10": "3PM"})
with t4:
    st.subheader("Calcolatore Valore Bookmaker")
    p_sel = st.selectbox("Giocatore:", sorted(df_totale['Giocatore'].dropna().tolist()))
    stat = df_totale[df_totale['Giocatore'] == p_sel].iloc[0]
    st.metric(f"Media L10 {p_sel}", f"{stat['PTS_L10']:.1f}", delta=f"Stato: {stat['Stato']}")
    linea = st.number_input("Linea Sisal/Snai:", step=0.5)
    if linea > 0:
        if stat['PTS_L10'] > linea + 1.5: st.success("🔥 OVER CONSIGLIATO")
        elif stat['PTS_L10'] < linea - 1.5: st.error("❄️ UNDER CONSIGLIATO")
