import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

# CSS per simulare il registro e gestire i colori delle righe
st.markdown("""
    <style>
    /* Rimpiccioliamo i bottoni per farli sembrare quadratini */
    div.stButton > button {
        width: 100%;
        height: 30px;
        padding: 0px;
        border: 1px solid #ddd;
        border-radius: 2px;
        font-weight: bold;
    }
    /* Stile per la "X" (Lavoro) */
    .stButton > button:active, .stButton > button:focus, .stButton > button:hover {
        border-color: #ff4b4b;
    }
    /* Intestazioni tabella */
    .header-text {
        font-size: 12px;
        font-weight: bold;
        text-align: center;
    }
    /* Colonna ore calcolate */
    .calc-col {
        background-color: #f0f2f6;
        text-align: center;
        font-weight: bold;
        border-radius: 5px;
        padding: 5px 0px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚢 Libro-rosso-TRIP")
st.subheader("Registro Mensile delle Ore di Lavoro e Riposo")

# --- SIDEBAR: Dati Marittimo ---
with st.sidebar:
    st.header("Anagrafica & Periodo")
    nome = st.text_input("Nome e Cognome Marittimo", "Mario Rossi")
    qualifica = st.text_input("Qualifica", "Ufficiale di Coperta")
    
    oggi = datetime.now()
    anno_sel = st.selectbox("Anno", range(oggi.year - 1, oggi.year + 2), index=1)
    mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    mese_sel_nome = st.selectbox("Mese di Registro", mesi_ita, index=oggi.month - 1)
    mese_num = mesi_ita.index(mese_sel_nome) + 1

# --- LOGICA DATI ---
num_giorni = calendar.monthrange(anno_sel, mese_num)[1]

# Inizializzazione Stato del Registro (se non esiste)
# Struttura: { 'giorno': [False, True, ...] } dove True = Lavoro (X)
if 'registro' not in st.session_state:
    st.session_state.registro = {g: [False]*24 for g in range(1, 32)}

# --- HEADER TABELLA ---
# Spazio per Giorno (1.5), 24 ore (1 ciascuna), Totali (1.5 + 1.5)
col_widths = [1.5] + [1]*24 + [1.5, 1.5]
cols_h = st.columns(col_widths)
cols_h[0].markdown("<div class='header-text'>GIORNO</div>", unsafe_allow_html=True)
for i in range(24):
    cols_h[i+1].markdown(f"<div class='header-text'>{i:02d}</div>", unsafe_allow_html=True)
cols_h[25].markdown("<div class='header-text'>LAVORO</div>", unsafe_allow_html=True)
cols_h[26].markdown("<div class='header-text'>RIPOSO</div>", unsafe_allow_html=True)

st.divider()

# --- GRIGLIA GIORNALIERA ---
totale_mese_lavoro = 0
totale_mese_riposo = 0

for giorno in range(1, num_giorni + 1):
    c = st.columns(col_widths)
    
    # 1. Colonna Giorno
    c[0].write(f"**{giorno:02d}/{mese_num:02d}**")
    
    # 2. 24 Ore (Quadratini)
    for ora in range(24):
        with c[ora+1]:
            # Recuperiamo lo stato attuale
            is_lavoro = st.session_state.registro[giorno][ora]
            label = "X" if is_lavoro else "R"
            color = "#ff4b4b" if is_lavoro else "#d3d3d3"
            
            # Pulsante che agisce come toggle
            if st.button(label, key=f"btn_{giorno}_{ora}", help=f"Ora {ora:02d}"):
                st.session_state.registro[giorno][ora] = not is_lavoro
                st.rerun()

    # 3. Calcoli di riga
    ore_lavoro_giorno = sum(st.session_state.registro[giorno])
    ore_riposo_giorno = 24 - ore_lavoro_giorno
    
    totale_mese_lavoro += ore_lavoro_giorno
    totale_mese_riposo += ore_riposo_giorno
    
    # Visualizzazione Totali Giornalieri
    c[25].markdown(f"<div class='calc-col' style='color:blue'>{ore_lavoro_giorno}</div>", unsafe_allow_html=True)
    c[26].markdown(f"<div class='calc-col'>{ore_riposo_giorno}</div>", unsafe_allow_html=True)

st.divider()

# --- TOTALI MENSILI ---
m1, m2, m3, m4 = st.columns([10, 3, 3, 3])
with m2:
    st.metric("Totale Lavoro Mese", f"{totale_mese_lavoro} h")
with m3:
    st.metric("Totale Riposo Mese", f"{totale_mese_riposo} h")

# --- AZIONI ---
st.sidebar.divider()
if st.sidebar.button("🗑️ Reset Mese"):
    st.session_state.registro = {g: [False]*24 for g in range(1, 32)}
    st.rerun()

st.sidebar.download_button(
    label="📥 Scarica Registro (.csv)",
    data=pd.DataFrame(st.session_state.registro).T.to_csv(),
    file_name=f"Registro_{nome}_{mese_sel_nome}.csv",
    mime="text/csv"
)
