import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

# --- CSS CUSTOM PER STILE E VELOCITÀ ---
st.markdown("""
    <style>
    /* Forza il colore nero e grassetto per le X tramite selettore di attributo */
    button[kind="secondary"] p {
        font-size: 18px !important;
    }
    
    /* Rimpiccioliamo i bottoni per la griglia */
    div.stButton > button {
        width: 100% !important;
        height: 38px !important;
        padding: 0px !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 0px !important;
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
        height: 38px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #dee2e6;
        font-weight: bold;
        font-size: 13px;
        background-color: #ffffff;
    }
    
    /* Nasconde i margini eccessivi per compattare la tabella */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
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

# Inizializzazione session_state per evitare reset al click
if 'registro' not in st.session_state:
    st.session_state.registro = {g: [False]*24 for g in range(1, 32)}
if 'commenti' not in st.session_state:
    st.session_state.commenti = {g: "" for g in range(1, 32)}

# --- HEADER TABELLA ---
col_widths = [1] + [0.8]*24 + [1.2, 2, 1.2, 1.2]
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
    
    # 1. Colonna Giorno
    c[0].markdown(f"<div class='calc-cell'>{giorno:02d}</div>", unsafe_allow_html=True)
    
    # 2. 24 Ore (Pulsanti)
    for ora_index in range(24):
        with c[ora_index + 1]:
            is_lavoro = st.session_state.registro[giorno][ora_index]
            # Formattazione orario per il tooltip (finestra che si apre)
            fascia_oraria = f"Ore: {ora_index+1:02d}:00"
            
            # Etichetta e stile
            if is_lavoro:
                label = "**X**" # Grassetto Markdown
                btn_key = f"x_{giorno}_{ora_index}"
            else:
                label = "R"
                btn_key = f"r_{giorno}_{ora_index}"
            
            # Pulsante con 'help' per ripristinare il tooltip
            if st.button(label, key=btn_key, help=fascia_oraria):
                st.session_state.registro[giorno][ora_index] = not is_lavoro
                st.rerun()

    # 3. Calcoli di riga
    ore_l = sum(st.session_state.registro[giorno])
    ore_r = 24 - ore_l
    
    lav_7gg = 0
    for g_prec in range(max(1, giorno-6), giorno + 1):
        lav_7gg += sum(st.session_state.registro[g_prec])

    # 4. Colonne Risultati
    c[25].markdown(f"<div class='calc-cell'>{ore_r}</div>", unsafe_allow_html=True)
    with c[26]:
        st.session_state.commenti[giorno] = st.text_input("", value=st.session_state.commenti[giorno], key=f"cmt_{giorno}", label_visibility="collapsed")
    c[27].markdown(f"<div class='calc-cell'>{ore_l}</div>", unsafe_allow_html=True)
    c[28].markdown(f"<div class='calc-cell'>{lav_7gg}</div>", unsafe_allow_html=True)

# --- CSS FINALE PER COLORE NERO ---
st.markdown("""
    <style>
    /* Seleziona i bottoni che contengono la X (tramite grassetto markdown) */
    button:has(strong) p {
        color: black !important;
        font-weight: 900 !important;
    }
    </style>
    """, unsafe_allow_html=True)
