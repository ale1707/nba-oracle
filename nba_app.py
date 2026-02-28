import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, scoreboardv2
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- 1. CONFIGURAZIONE E STILE PROFESSIONALE (No-AI Look) ---
st.set_page_config(page_title="NBA Oracle Pro", layout="wide", page_icon="🏀", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Nascondi elementi di default di Streamlit per sembrare un'app nativa */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Tipografia e Layout puliti */
    body { font-family: 'Inter', -apple-system, sans-serif; background-color: #f4f5f7; }
    
    .match-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 30px;
        border: 1px solid #e2e8f0;
    }
    .team-logo { width: 45px; vertical-align: middle; margin: 0 12px; }
    .team-logo-large { width: 70px; margin-bottom: 10px; display: block; }
    .match-header { font-size: 24px; font-weight: 700; text-align: center; margin-bottom: 20px; color: #0f172a; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px;}
    
    /* Box Infortuni Professionale */
    .injury-alert { 
        background-color: #fef2f2; color: #991b1b; font-weight: 600; font-size: 13px; 
        margin-bottom: 20px; border-left: 4px solid #ef4444; padding: 12px; border-radius: 4px;
    }
    
    /* Fix per il problema del testo bianco (Tema Scuro vs Tema Chiaro) */
    .bet-box { 
        background-color: #ffffff; 
        color: #0f172a !important; /* Forza il testo scuro sempre */
        border-left: 5px solid #10b981; 
        padding: 16px; 
        margin-bottom: 12px; 
        border-radius: 6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        border: 1px solid #e2e8f0;
    }
    .bet-box-medium { border-left-color: #f59e0b; }
    .bet-box-high { border-left-color: #ef4444; }
    .bet-title { font-weight: 800; font-size: 15px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;}
    .bet-leg { font-size: 14px; margin-bottom: 4px; border-bottom: 1px dashed #e2e8f0; padding-bottom: 4px;}
    
    .result-box {
        display: flex; justify-content: space-between; align-items: center; background: #ffffff; 
        padding: 15px 25px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #e2e8f0; border-left: 5px solid #3b82f6; color: #0f172a;
    }
    .score-text { font-size: 22px; font-weight: 800; color: #0f172a; }
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

def get_logo(abbr):
    espn_abbr = { 'GSW': 'gs', 'NOP': 'no', 'NYK': 'ny', 'SAS': 'sa', 'UTA': 'utah', 'WAS': 'wsh', 'LAL': 'lal', 'LAC': 'lac' }.get(abbr.upper(), abbr.lower())
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{espn_abbr}.png"

# --- 2. MOTORE DATI (Auto-Aggiornamento ogni 15 Minuti in Background) ---
@st.cache_data(ttl=900, show_spinner=False)
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
            if r['GP_L3'] == 0 and r['GP_L10'] == 0 and r['GP'] > 2: return "OUT"
            elif r['GP_L3'] == 0 and r['GP_L10'] > 0: return "DUBBIO"
            else: return "ATTIVO"
        df['Stato'] = df.apply(check_status, axis=1)

        def get_motivation(r):
            if r['Stato'] == "OUT": return "Assente."
            if r['Stato'] == "DUBBIO": return "Da monitorare (Game Time Decision)."
            diff = r['PTS_L10'] - r['PTS']
            if diff >= 4.0: return f"Forma top: {r['PTS_L10']:.1f} pt nelle ultime 10."
            elif diff <= -4.0: return f"In flessione: solo {r['PTS_L10']:.1f} pt di recente."
            elif r['AST_L10'] > r['AST'] + 1.5: return f"Playmaking attivo: {r['AST_L10']:.1f} assist (L10)."
            elif r['REB_L10'] > r['REB'] + 1.5: return f"Solido a rimbalzo: {r['REB_L10']:.1f} rimb (L10)."
            else: return f"Rendimento costante. Media: {r['PTS_L10']:.1f} pt."
        df['Motivazione'] = df.apply(get_motivation, axis=1)
        
        def get_prediction(r):
            if r['Stato'] != "ATTIVO": return "-"
            val = int(r['PTS_L10'] * 0.75) if r['PTS_L10'] > 0 else int(r['PTS'] * 0.75)
            return f"Over {val}.5 Punti" if val > 8 else "No Bet"
        df['Pronostico'] = df.apply(get_prediction, axis=1)

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
                risultati_ieri.append({'CasaAbbr': gc_parts[3:], 'CasaPts': h_score, 'TrasfertaAbbr': gc_parts[:3], 'TrasfertaPts': a_score})
        return df, partite_oggi, risultati_ieri
    except Exception as e: return None, None, None

df_totale, partite, risultati = get_nba_data()

if df_totale is None:
    st.error("Connessione ai server NBA in corso... Ricarica tra qualche secondo."); st.stop()

# --- GENERATORE SCHEDINE SISAL ---
def genera_schedine(df_match):
    df_ok = df_match[(df_match['Stato'] == 'ATTIVO') & (df_match['PTS_L10'] > 10)].sort_values('PTS_L10', ascending=False)
    if len(df_ok) < 3: return None, None, None
    p1, p2, p3 = df_ok.iloc[0], df_ok.iloc[1], df_ok.iloc[2]
    
    b_sic = f"<div class='bet-leg'><b>{p1['Giocatore']}</b>: Over {int(p1['PTS_L10']*0.65)}.5 Punti</div><div class='bet-leg'><b>{p2['Giocatore']}</b>: Over {int(p2['PTS_L10']*0.65)}.5 Punti</div>"
    b_med = f"<div class='bet-leg'><b>{p1['Giocatore']}</b>: Over {int(p1['PTS_L10']*0.8)}.5 Punti</div><div class='bet-leg'><b>{p3['Giocatore']}</b>: Over {int(p3['PTS_L10']*0.8)}.5 Punti</div><div class='bet-leg'><b>{p2['Giocatore']}</b>: Over {int(p2['AST_L10']*0.8)}.5 Assist</div>"
    b_alt = f"<div class='bet-leg'><b>{p1['Giocatore']}</b>: Over {int(p1['PTS_L10'])}.5 Punti</div><div class='bet-leg'><b>{p2['Giocatore']}</b>: Over {int(p2['PTS_L10'])}.5 Punti</div><div class='bet-leg'><b>{p1['Giocatore']}</b>: Over {int(p1['FG3M_L10'])}.5 Triple</div>"
    return b_sic, b_med, b_alt

# --- 3. INTERFACCIA DASHBOARD PROFESSIONALE ---
st.markdown("<h2 style='text-align: center; color: #0f172a; font-weight: 800; margin-bottom: 30px;'>NBA ORACLE PRO DASHBOARD</h2>", unsafe_allow_html=True)

t1, t_res, t2, t3, t4 = st.tabs(["PARTITE IN PROGRAMMA", "RISULTATI NOTTE", "STATISTICHE SQUADRE", "FORMA L10", "ANALISI QUOTE"])

with t1:
    if not partite: st.info("Il tabellone ufficiale per la prossima notte è in fase di aggiornamento sui server NBA.")
    else:
        for p in partite:
            st.markdown(f'<div class="match-card"><div class="match-header"><img src="{get_logo(p["CasaAbbr"])}" class="team-logo">{p["CasaAbbr"]} vs {p["TrasfertaAbbr"]}<img src="{get_logo(p["TrasfertaAbbr"])}" class="team-logo"></div>', unsafe_allow_html=True)
            
            df_match = df_totale[(df_totale['Squadra'] == p['Casa']) | (df_totale['Squadra'] == p['Trasferta'])]
            out = df_match[df_match['Stato'] != "ATTIVO"]['Giocatore'].tolist()
            if out: st.markdown(f'<div class="injury-alert">⚠️ INDISPONIBILI / DUBBI: {", ".join(out[:8])}</div>', unsafe_allow_html=True)
            
            # --- TABELLA 1: LE STATISTICHE ---
            st.markdown("<h4 style='color: #334155; font-size: 16px; margin-top: 10px;'>📊 Statistiche Giocatori (Ultime 10)</h4>", unsafe_allow_html=True)
            cfg_stats = { "Giocatore": st.column_config.TextColumn("Giocatore", width="medium"), "PTS_L10": st.column_config.NumberColumn("PTS", format="%.1f"), "AST_L10": st.column_config.NumberColumn("AST", format="%.1f"), "REB_L10": st.column_config.NumberColumn("REB", format="%.1f"), "FG3M_L10": st.column_config.NumberColumn("3PM", format="%.1f") }
            col_s = ['Giocatore', 'PTS_L10', 'AST_L10', 'REB_L10', 'FG3M_L10']
            c1, c2 = st.columns(2)
            with c1: st.dataframe(df_totale[(df_totale['Squadra'] == p['Casa']) & (df_totale['Stato'] == 'ATTIVO')][col_s].sort_values('PTS_L10', ascending=False).head(6), hide_index=True, use_container_width=True, column_config=cfg_stats)
            with c2: st.dataframe(df_totale[(df_totale['Squadra'] == p['Trasferta']) & (df_totale['Stato'] == 'ATTIVO')][col_s].sort_values('PTS_L10', ascending=False).head(6), hide_index=True, use_container_width=True, column_config=cfg_stats)
            
            # --- TABELLA 2: PRONOSTICI E MOTIVAZIONI ---
            st.markdown("<h4 style='color: #334155; font-size: 16px; margin-top: 20px;'>💡 Analisi e Motivazioni</h4>", unsafe_allow_html=True)
            cfg_mot = { "Giocatore": st.column_config.TextColumn("Giocatore", width="medium"), "Pronostico": st.column_config.TextColumn("Consiglio", width="small"), "Motivazione": st.column_config.TextColumn("Motivazione Tecnica", width="large") }
            col_m = ['Giocatore', 'Pronostico', 'Motivazione']
            st.dataframe(df_match[(df_match['Stato'] == 'ATTIVO') & (df_match['PTS_L10'] > 12)][col_m].sort_values(by="Giocatore").head(8), hide_index=True, use_container_width=True, column_config=cfg_mot)
            
            # --- SEZIONE 3: SCHEDINE PRONTE ---
            with st.expander("🎫 MOSTRA SCHEDINE CONSIGLIATE (Generazione Automatica)"):
                sic, med, alt = genera_schedine(df_match)
                if sic:
                    st.markdown(f'<div class="bet-box"><div class="bet-title" style="color:#059669;">Quota Bassa (Sicura)</div>{sic}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="bet-box bet-box-medium"><div class="bet-title" style="color:#d97706;">Quota Media (Bilanciata)</div>{med}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="bet-box bet-box-high"><div class="bet-title" style="color:#dc2626;">Quota Alta (Rischio)</div>{alt}</div>', unsafe_allow_html=True)
                else: st.write("Dati insufficienti per questo match.")
            
            st.markdown("</div>", unsafe_allow_html=True) # Chiude la match-card

with t_res:
    if not risultati: st.info("In attesa dei referti ufficiali della notte.")
    for r in risultati: st.markdown(f'<div class="result-box"><div style="display:flex; align-items:center;"><b>{r["CasaAbbr"]}</b><img src="{get_logo(r["CasaAbbr"])}" width="35" style="margin-left:10px;"></div><div class="score-text">{r["CasaPts"]} - {r["TrasfertaPts"]}</div><div style="display:flex; align-items:center;"><img src="{get_logo(r["TrasfertaAbbr"])}" width="35" style="margin-right:10px;"><b>{r["TrasfertaAbbr"]}</b></div></div>', unsafe_allow_html=True)

def render_db(df, cols, sort_col, cfg=None):
    for s in sorted(df['Squadra'].dropna().unique()):
        with st.expander(f"{s}"):
            abbr = df[df['Squadra'] == s]['Abbr'].iloc[0]
            st.markdown(f"<img src='{get_logo(abbr)}' class='team-logo-large'>", unsafe_allow_html=True)
            st.dataframe(df[df['Squadra'] == s][cols].sort_values(sort_col, ascending=False), hide_index=True, use_container_width=True, column_config=cfg)

with t2: render_db(df_totale, ['Giocatore', 'Stato', 'PTS', 'AST', 'REB', 'FG3M', 'GP'], 'PTS')
with t3: render_db(df_totale, ['Giocatore', 'Stato', 'PTS_L10', 'AST_L10', 'REB_L10', 'FG3M_L10', 'GP_L10'], 'PTS_L10', {"PTS_L10": "PTS", "AST_L10": "AST", "REB_L10": "REB", "FG3M_L10": "3PM"})
with t4:
    st.markdown("### Verifica Valore Quota Sisal/Snai")
    p_sel = st.selectbox("Cerca Giocatore:", sorted(df_totale['Giocatore'].dropna().tolist()))
    stat = df_totale[df_totale['Giocatore'] == p_sel].iloc[0]
    st.metric(f"Media Ultime 10: {p_sel}", f"{stat['PTS_L10']:.1f} Punti", delta=f"Stato: {stat['Stato']}")
    linea = st.number_input("Inserisci Linea Bookmaker (es. 22.5):", step=0.5)
    if linea > 0:
        if stat['PTS_L10'] > linea + 1.5: st.success("VANTAGGIO MATEMATICO: Consigliato OVER")
        elif stat['PTS_L10'] < linea - 1.5: st.error("VANTAGGIO MATEMATICO: Consigliato UNDER")
