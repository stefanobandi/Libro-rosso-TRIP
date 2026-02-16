import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

# --- CSS CUSTOM PER CONTRASTO MASSIMO X vs R ---
st.markdown("""
    <style>
    /* Rimpiccioliamo i bottoni della griglia */
    div.stButton > button {
        width: 100% !important;
        height: 40px !important;
        padding: 0px !important;
        border: 1px solid #eeeeee !important;
        border-radius: 0px !important;
        background-color: white !important;
    }
    
    /* Stile per la R (Riposo) - Piccolissima e quasi invisibile */
    button:has(span:contains("R")) p, 
    div.stButton > button p:not(:has(strong)) {
        color: #e0e0e0 !important;
        font-size: 10px !important;
        font-weight: 100 !important;
    }

    /* Stile per la X (Lavoro) - Enorme, nera e pesantissima */
    button:has(strong) p {
        color: #000000 !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        font-family: 'Arial Black', Gadget, sans-serif !important;
    }

    /* Header e Celle calcoli */
    .header-box {
        background-color: #f1f3f5;
        border: 1px solid #dee2e6;
        text-align: center;
        font-weight: bold;
        font-size: 10px;
        height: 45px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .calc-cell {
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #dee2e6;
        font-weight: bold;
        font-size: 14px;
        background-color: #ffffff;
    }
    
    /* Compattamento layout */
    .block-container {
        padding-top: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚢 Libro-rosso-TRIP")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Parametri")
    nome = st.text_input("Nome/Cognome", "ROSSI MARIO")
    qualifica = st.text_input("Qualifica", "UFFICIALE")
    
    oggi = datetime.now()
    anno_sel = st.number_input("Anno", 2024, 2030, oggi.year)
    mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    mese_sel = st.selectbox("Mese", mesi_ita, index=oggi.month - 1)
    mese_num = mesi_ita.index(mese_sel) + 1

# --- LOGICA DATI ---
num_giorni = calendar.monthrange(anno_sel, mese_num)[1]

if 'registro' not in st.session_state:
    st.session_state.registro = {g: [False]*24 for g in range(1, 32)}
if 'commenti' not in st.session_state:
    st.session_state.commenti = {g: "" for g in range(1, 32)}

# --- HEADER TABELLA ---
col_widths = [1] + [0.7]*24 + [1.2, 2, 1.2, 1.2]
cols_h = st.columns(col_widths)

with cols_h[0]: st.markdown("<div class='header-box'>GG</div>", unsafe_allow_html=True)
for i in range(1, 25):
    with cols_h[i]: st.markdown(f"<div class='header-box'>{i:02d}</div>", unsafe_allow_html=True)
with cols_h[25]: st.markdown("<div class='header-box'>Riposo<br>24h</div>", unsafe_allow_html=True)
with cols_h[26]: st.markdown("<div class='header-box'>Commenti</div>", unsafe_allow_html=True)
with cols_h[27]: st.markdown("<div class='header-box'>Lavoro<br>24h</div>", unsafe_allow_html=True)
with cols_h[28]: st.markdown("<div class='header-box'>Lavoro<br>7gg</div>", unsafe_allow_html=True)

# --- CORPO TABELLA ---
for giorno in range(1, num_giorni + 1):
    c = st.columns(col_widths)
    
    # Giorno
    c[0].markdown(f"<div class='calc-cell'>{giorno:02d}</div>", unsafe_allow_html=True)
    
    # 24 Ore
    for ora_index in range(24):
        with c[ora_index + 1]:
            is_lavoro = st.session_state.registro[giorno][ora_index]
            fascia_oraria = f"Giorno {giorno:02d} - Ore {ora_index+1:02d}:00"
            
            # Label differenziate per il CSS
            label = "**X**" if is_lavoro else "R"
            
            if st.button(label, key=f"btn_{giorno}_{ora_index}", help=fascia_oraria):
                st.session_state.registro[giorno][ora_index] = not is_lavoro
                st.rerun()

    # Calcoli
    ore_l = sum(st.session_state.registro[giorno])
    ore_r = 24 - ore_l
    
    lav_7gg = 0
    for g_prec in range(max(1, giorno-6), giorno + 1):
        lav_7gg += sum(st.session_state.registro[g_prec])

    # Colonne Finali
    c[25].markdown(f"<div class='calc-cell'>{ore_r}</div>", unsafe_allow_html=True)
    with c[26]:
        st.session_state.commenti[giorno] = st.text_input("", value=st.session_state.commenti[giorno], key=f"cmt_{giorno}", label_visibility="collapsed")
    c[27].markdown(f"<div class='calc-cell'>{ore_l}</div>", unsafe_allow_html=True)
    c[28].markdown(f"<div class='calc-cell'>{lav_7gg}</div>", unsafe_allow_html=True)
