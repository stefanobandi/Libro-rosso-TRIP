import streamlit as st
import pandas as pd
import calendar
import os
from datetime import datetime
from fpdf import FPDF

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

DB_FILE = "database.csv"

# --- CARICAMENTO DATI ---
def load_data():
    cols = ["Giorno"] + [f"H{i:02d}" for i in range(1, 25)] + ["Commenti"]
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=cols)
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

if 'db_memoria' not in st.session_state:
    st.session_state.db_memoria = load_data()

def save_to_disk():
    st.session_state.db_memoria.to_csv(DB_FILE, index=False)

# --- CSS (Stili per violazioni e tabella) ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem !important; }
    .header-box { background-color: #f2f2f2; border: 1px solid #999; text-align: center; font-weight: bold; font-size: 10px; height: 40px; display: flex; align-items: center; justify-content: center; }
    .data-cell { height: 35px; border: 1px solid #ccc; font-size: 12px; display: flex; align-items: center; justify-content: center; background-color: white; }
    .violation { background-color: #ff4b4b !important; color: white !important; font-weight: bold; }
    .promemoria-tab { width: 100%; border-collapse: collapse; margin-top: 30px; border: 2px solid #333; }
    .promemoria-tab td, .promemoria-tab th { border: 1px solid #999; padding: 10px; font-size: 14px; }
    .promemoria-header { background-color: #333; color: white; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- INTESTAZIONE FISSA ---
oggi = datetime.now()
mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
mese_attuale = mesi_ita[oggi.month-1]
anno_attuale = oggi.year

st.title(f"🚢 Registro Ore di Lavoro e Riposo - {mese_attuale} {anno_attuale}")
st.info("⚡ Istruzioni: Compila le ore e premi 'CALCOLA E SALVA' in fondo per aggiornare i calcoli e verificare la conformità.")

# --- FORM REGISTRO ---
with st.form("registro_form"):
    num_giorni = calendar.monthrange(anno_attuale, oggi.month)[1]
    
    # Header Tabella
    col_w = [0.8] + [0.5]*24 + [1, 2, 1, 1.2]
    h = st.columns(col_w)
    labels = ["GG"] + [f"{i:02d}" for i in range(1, 25)] + ["RIP", "Commenti", "LAV", "LAV 7g"]
    for i, l in enumerate(labels):
        h[i].markdown(f"<div class='header-box'>{l}</div>", unsafe_allow_html=True)

    temp_dati = {}
    temp_comm = {}
    ore_mensili_totali = [] # Per calcolo 7 giorni

    # Loop Giorni
    for g in range(1, num_giorni + 1):
        r = st.columns(col_w)
        r[0].markdown(f"<div class='data-cell'><b>{g:02d}</b></div>", unsafe_allow_html=True)
        
        row_db = st.session_state.db_memoria[st.session_state.db_memoria['Giorno'] == g]
        
        # 24 Ore Checkbox
        ore_giorno = []
        for ora in range(1, 25):
            with r[ora]:
                def_v = bool(row_db[f"H{ora:02d}"].values[0]) if not row_db.empty else False
                val = st.checkbox("", value=def_v, key=f"f_{g}_{ora}", label_visibility="collapsed")
                ore_giorno.append(val)
        temp_dati[g] = ore_giorno
        
        # Commenti
        with r[26]:
            def_c = str(row_db['Commenti'].values[0]) if not row_db.empty and str(row_db['Commenti'].values[0]) != 'nan' else ""
            temp_comm[g] = st.text_input("", value=def_c, key=f"c_{g}", label_visibility="collapsed")

        # --- CALCOLI E REGOLE (Visualizzazione istantanea caricata da DB) ---
        lav_24 = sum(ore_giorno)
        rip_24 = 24 - lav_24
        
        # Test Riposo Continuo (6 ore)
        rip_bin = "".join(['0' if x else '1' for x in ore_giorno])
        violazione_rip = "111111" not in rip_bin
        
        # Calcolo 7 giorni (Mobile)
        ore_mensili_totali.append(lav_24)
        lav_7g = sum(ore_mensili_totali[max(0, g-7):g])

        # Classi CSS Violazioni
        c_lav = "violation" if lav_24 > 14 else ""
        c_rip = "violation" if violazione_rip else ""
        c_7g = "violation" if lav_7g > 72 else ""

        r[25].markdown(f"<div class='data-cell {c_rip}'>{rip_24}</div>", unsafe_allow_html=True)
        r[27].markdown(f"<div class='data-cell {c_lav}'>{lav_24}</div>", unsafe_allow_html=True)
        r[28].markdown(f"<div class='data-cell {c_7g}'>{lav_7g}</div>", unsafe_allow_html=True)

    submit = st.form_submit_button("💾 CALCOLA E SALVA TUTTO IL MESE", use_container_width=True)

# --- LOGICA SALVATAGGIO ---
if submit:
    new_rows = []
    for g in range(1, num_giorni + 1):
        riga = {"Giorno": g, "Commenti": temp_comm[g]}
        for i, v in enumerate(temp_dati[g]):
            riga[f"H{i+1:02d}"] = v
        new_rows.append(riga)
    
    st.session_state.db_memoria = pd.DataFrame(new_rows)
    save_to_disk()
    st.success("✅ Dati salvati e calcoli aggiornati!")
    st.rerun()

# --- TABELLA REGOLE FISSA IN FONDO ---
st.markdown("""
<table class="promemoria-tab">
    <tr class="promemoria-header"><th colspan="2">TEST DI CONFORMITÀ (D.Lgs 271/99 - 108/05)</th></tr>
    <tr><td><b>1) Max Lavoro / 7 Giorni</b></td><td>Non deve superare le <b>72 ore</b> (Evidenziato in rosso nell'ultima colonna)</td></tr>
    <tr><td><b>2) Max Lavoro / 24 Ore</b></td><td>Non deve superare le <b>14 ore</b> (Evidenziato in rosso nella colonna LAV)</td></tr>
    <tr><td><b>3) Riposo Continuato</b></td><td>Almeno un blocco da <b>6 ore</b> consecutive (Evidenziato in rosso nella colonna RIP)</td></tr>
</table>
""", unsafe_allow_html=True)
